from dotenv import load_dotenv
import os

load_dotenv(os.path.join(os.path.dirname(__file__), '.env'))

from typing import Optional

class Config:
    """Application configuration"""
    
    # Flask settings
    FLASK_SECRET_KEY: str = os.getenv("FLASK_SECRET_KEY", "dev-secret-key")
    FLASK_DEBUG: bool = os.getenv("FLASK_ENV") == "development"
    
    # Strava API settings
    STRAVA_CLIENT_ID: Optional[str] = os.getenv("STRAVA_CLIENT_ID")
    STRAVA_CLIENT_SECRET: Optional[str] = os.getenv("STRAVA_CLIENT_SECRET")
    
    # Google Maps API settings
    GOOGLE_MAPS_API_KEY: Optional[str] = os.getenv("GOOGLE_MAPS_API_KEY")
    
    # POI search settings
    POI_SEARCH_RADIUS: int = int(os.getenv("POI_SEARCH_RADIUS", "100"))
    POI_ROUTE_SAMPLING_DISTANCE: int = int(os.getenv("POI_ROUTE_SAMPLING_DISTANCE", "500"))
    
    @classmethod
    def validate(cls) -> None:
        """Validate required configuration"""
        missing = []
        if not cls.STRAVA_CLIENT_ID:
            missing.append("STRAVA_CLIENT_ID")
        if not cls.STRAVA_CLIENT_SECRET:
            missing.append("STRAVA_CLIENT_SECRET")
        if not cls.GOOGLE_MAPS_API_KEY:
            missing.append("GOOGLE_MAPS_API_KEY")
        
        if missing:
            raise ValueError(f"Missing required environment variables: {', '.join(missing)}")
