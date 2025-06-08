import requests
import time
import os
from urllib.parse import urlencode

class StravaAPI:
    """
    A client to interact with the Strava API, handling OAuth and token refreshes.
    """
    API_URL = "https://www.strava.com/api/v3"
    TOKEN_URL = "https://www.strava.com/oauth/token"
    AUTHORIZE_URL = "https://www.strava.com/oauth/authorize"

    def __init__(self, client_id: str, client_secret: str):
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

    def exchange_code_for_token(self, code: str) -> dict:
        """Exchanges an authorization code for an access token."""
        payload = {
            "client_id": self.client_id,
            "client_secret": self.client_secret,
            "code": code,
            "grant_type": "authorization_code"
        }
        response = requests.post(self.TOKEN_URL, data=payload)
        response.raise_for_status()
        return response.json()

    def refresh_access_token(self, refresh_token: str) -> dict:
        """Refreshes an expired access token."""
        print("Refreshing Strava access token...")
        payload = {
            "client_id": self.client_id,
            "client_secret": self.client_secret,
            "refresh_token": refresh_token,
            "grant_type": "refresh_token"
        }
        response = requests.post(self.TOKEN_URL, data=payload)
        response.raise_for_status()
        print("Token refreshed successfully.")
        return response.json()

    def get_api_headers(self, access_token: str) -> dict:
        """Returns the authorization headers for API requests."""
        return {'Authorization': f'Bearer {access_token}'}

    def get_activities(self, access_token: str, page: int = 1, per_page: int = 30) -> list:
        """Fetches a list of the authenticated athlete's activities."""
        headers = self.get_api_headers(access_token)
        params = {'page': page, 'per_page': per_page}
        response = requests.get(f"{self.API_URL}/athlete/activities", headers=headers, params=params)
        response.raise_for_status()
        return response.json()

    def get_activity_stream(self, activity_id: int, access_token: str) -> list:
        """Fetches the lat/lng stream for a given activity."""
        headers = self.get_api_headers(access_token)
        # Requesting only the latlng stream for efficiency
        params = {'keys': 'latlng', 'key_by_type': 'true'}
        response = requests.get(f"{self.API_URL}/activities/{activity_id}/streams", headers=headers, params=params)
        response.raise_for_status()
        data = response.json()
        return data.get('latlng', {}).get('data', [])

# Helper to create a singleton instance
def get_strava_client() -> StravaAPI:
    return StravaAPI(
        client_id=os.getenv("STRAVA_CLIENT_ID"),
        client_secret=os.getenv("STRAVA_CLIENT_SECRET")
    )