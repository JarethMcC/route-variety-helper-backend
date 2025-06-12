import logging
from typing import List, Dict, Tuple
import googlemaps
from config import Config

logger = logging.getLogger(__name__)

# Initialize Google Maps client
gmaps = googlemaps.Client(key=Config.GOOGLE_MAPS_API_KEY) if Config.GOOGLE_MAPS_API_KEY else None

# Types of POIs to search for
POI_TYPES = [
    "cafe", "restaurant", "bar", "tourist_attraction", 
    "museum", "park", "art_gallery", "viewpoint"
]

def _sample_route_points(route_coords: List[List[float]], sample_distance: int = 500) -> List[Tuple[float, float]]:
    """Sample points along route to reduce API calls while maintaining coverage"""
    if len(route_coords) <= 2:
        return [(lat, lng) for lng, lat in route_coords]
    
    # For now, simple sampling - could be improved with actual distance calculation
    step = max(1, len(route_coords) // (len(route_coords) * 100 // sample_distance))
    return [(lat, lng) for lng, lat in route_coords[::step]]

def get_pois_for_route(route_coords: List[List[float]]) -> List[Dict]:
    """
    Finds points of interest within specified radius of a given route using Google Maps Places API.
    
    Args:
        route_coords: A list of [longitude, latitude] coordinates.
    
    Returns:
        A list of POIs with their name, type, and location.
    """
    if not route_coords:
        logger.warning("Empty route coordinates provided")
        return []
    
    if not gmaps:
        logger.error("Google Maps client not initialized - check API key")
        return []
    
    # Sample route points to reduce API calls
    sample_points = _sample_route_points(route_coords, Config.POI_ROUTE_SAMPLING_DISTANCE)
    logger.info(f"Searching POIs for {len(sample_points)} sample points along route")
    
    found_pois = {}
    
    for lat, lng in sample_points:
        location = (lat, lng)
        
        try:
            # Use nearby search with multiple types in one call
            results = gmaps.places_nearby(
                location=location,
                radius=Config.POI_SEARCH_RADIUS,
                type="|".join(POI_TYPES)  # Multiple types in one request
            ).get("results", [])
            
            for poi in results:
                place_id = poi["place_id"]
                if place_id not in found_pois:
                    poi_types = poi.get("types", [])
                    poi_type = next((t for t in poi_types if t in POI_TYPES), "point_of_interest")
                    
                    found_pois[place_id] = {
                        "name": poi.get("name", "Unknown"),
                        "type": poi_type.replace('_', ' ').title(),
                        "coords": [
                            poi["geometry"]["location"]["lat"],
                            poi["geometry"]["location"]["lng"]
                        ],
                        "rating": poi.get("rating"),
                        "price_level": poi.get("price_level")
                    }
                    
        except googlemaps.ApiError as e:
            logger.error(f"Google Maps API error at location {location}: {e}")
            continue
        except Exception as e:
            logger.error(f"Unexpected error searching POIs at {location}: {e}")
            continue
    
    logger.info(f"Found {len(found_pois)} unique POIs")
    return list(found_pois.values())