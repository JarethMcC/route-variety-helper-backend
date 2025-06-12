import requests
import time
import logging
from typing import List, Dict, Optional
from urllib.parse import urlencode
from config import Config

logger = logging.getLogger(__name__)

class StravaAPIError(Exception):
    """Custom exception for Strava API errors"""
    pass

class StravaAPI:
    """A client to interact with the Strava API, handling OAuth and token refreshes."""
    
    API_URL = "https://www.strava.com/api/v3"
    TOKEN_URL = "https://www.strava.com/oauth/token"
    AUTHORIZE_URL = "https://www.strava.com/oauth/authorize"

    def __init__(self, client_id: str, client_secret: str):
        if not client_id or not client_secret:
            raise ValueError("client_id and client_secret are required")
        self.client_id = client_id
        self.client_secret = client_secret

    def get_authorization_url(self, redirect_uri: str) -> str:
        """Generates the Strava authorization URL for the user to visit."""
        params = {
            "client_id": self.client_id,
            "redirect_uri": redirect_uri,
            "response_type": "code",
            "approval_prompt": "force",
            "scope": "read,activity:read_all"
        }
        return f"{self.AUTHORIZE_URL}?{urlencode(params)}"

    def exchange_code_for_token(self, code: str) -> Dict:
        """Exchanges an authorization code for an access token."""
        payload = {
            "client_id": self.client_id,
            "client_secret": self.client_secret,
            "code": code,
            "grant_type": "authorization_code"
        }
        try:
            response = requests.post(self.TOKEN_URL, data=payload, timeout=10)
            response.raise_for_status()
            return response.json()
        except requests.RequestException as e:
            logger.error(f"Failed to exchange code for token: {e}")
            raise StravaAPIError(f"Token exchange failed: {e}")

    def refresh_access_token(self, refresh_token: str) -> Dict:
        """Refreshes an expired access token."""
        logger.info("Refreshing Strava access token...")
        payload = {
            "client_id": self.client_id,
            "client_secret": self.client_secret,
            "refresh_token": refresh_token,
            "grant_type": "refresh_token"
        }
        try:
            response = requests.post(self.TOKEN_URL, data=payload, timeout=10)
            response.raise_for_status()
            logger.info("Token refreshed successfully")
            return response.json()
        except requests.RequestException as e:
            logger.error(f"Failed to refresh token: {e}")
            raise StravaAPIError(f"Token refresh failed: {e}")

    def get_api_headers(self, access_token: str) -> Dict[str, str]:
        """Returns the authorization headers for API requests."""
        return {'Authorization': f'Bearer {access_token}'}

    def get_activities(self, access_token: str, page: int = 1, per_page: int = 30) -> List[Dict]:
        """Fetches a list of the authenticated athlete's activities."""
        headers = self.get_api_headers(access_token)
        params = {'page': page, 'per_page': min(per_page, 200)}  # Strava limit is 200
        
        try:
            response = requests.get(
                f"{self.API_URL}/athlete/activities", 
                headers=headers, 
                params=params,
                timeout=10
            )
            response.raise_for_status()
            return response.json()
        except requests.RequestException as e:
            logger.error(f"Failed to fetch activities: {e}")
            raise StravaAPIError(f"Failed to fetch activities: {e}")

    def get_activity_stream(self, activity_id: int, access_token: str) -> List[List[float]]:
        """Fetches the lat/lng stream for a given activity."""
        headers = self.get_api_headers(access_token)
        params = {'keys': 'latlng', 'key_by_type': 'true'}
        
        try:
            response = requests.get(
                f"{self.API_URL}/activities/{activity_id}/streams", 
                headers=headers, 
                params=params,
                timeout=15
            )
            response.raise_for_status()
            data = response.json()
            return data.get('latlng', {}).get('data', [])
        except requests.RequestException as e:
            logger.error(f"Failed to fetch activity stream for {activity_id}: {e}")
            raise StravaAPIError(f"Failed to fetch activity stream: {e}")

def get_strava_client() -> StravaAPI:
    """Factory function to create a Strava client with configuration validation."""
    return StravaAPI(
        client_id=Config.STRAVA_CLIENT_ID,
        client_secret=Config.STRAVA_CLIENT_SECRET
    )