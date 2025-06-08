import osmnx as ox
from shapely.geometry import Point, LineString

def get_pois_for_route(route_coords: list[list[float]]) -> list[dict]:
    """
    Finds points of interest within 100 meters of a given route.

    Args:
        route_coords: A list of [longitude, latitude] coordinates.

    Returns:
        A list of POIs with their name, type, and location.
    """
    if not route_coords:
        return []

    # Define the tags for points of interest we want to find
    tags = {
        "amenity": ["cafe", "pub", "restaurant", "bench"],
        "historic": True,
        "tourism": ["viewpoint", "artwork", "attraction"],
        "natural": ["tree", "peak", "spring"]
    }

    # Create a LineString geometry from the route coordinates
    # Note: osmnx expects (longitude, latitude)
    line = LineString(route_coords)

    # Use osmnx to fetch POIs from OpenStreetMap within the bounding box of the route
    pois_gdf = ox.features_from_geometry(line.buffer(0.001), tags) # 0.001 degrees is ~111 meters

    # Filter the results to be within 100 meters of the actual route line
    nearby_pois = []
    # Project the geometry to a local UTM CRS for accurate distance measurement
    pois_gdf_proj = ox.project_gdf(pois_gdf)
    route_proj = ox.project_gdf(pois_gdf.set_geometry([line])).iloc[0].geometry

    for idx, poi in pois_gdf_proj.iterrows():
        point = poi.geometry
        if point.distance(route_proj) <= 100: # Distance in meters
            # Get original unprojected coordinates
            original_poi = pois_gdf.loc[idx]
            poi_point = original_poi.geometry.centroid

            # Identify the type of POI
            poi_type = "Interesting Point"
            if 'amenity' in original_poi and original_poi['amenity']:
                poi_type = str(original_poi['amenity']).replace('_', ' ').title()
            elif 'historic' in original_poi and original_poi['historic']:
                poi_type = 'Historic Site'
            elif 'tourism' in original_poi and original_poi['tourism']:
                poi_type = str(original_poi['tourism']).replace('_', ' ').title()

            nearby_pois.append({
                "name": original_poi.get("name", "N/A"),
                "type": poi_type,
                "coords": [poi_point.y, poi_point.x] # Return as [lat, lon]
            })

    return nearby_pois