import logging
import os
import time
from flask import Flask, request, jsonify, redirect, session, url_for
from dotenv import load_dotenv
from functools import wraps
from typing import List, Dict

from config import Config
from strava_client import get_strava_client, StravaAPIError
from poi_service import get_pois_for_route

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Validate configuration
try:
    Config.validate()
except ValueError as e:
    logger.error(f"Configuration error: {e}")
    raise

app = Flask(__name__)
app.secret_key = Config.FLASK_SECRET_KEY

strava_api = get_strava_client()

def auth_required(f):
    """Decorator to protect endpoints that require authentication."""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'strava_token' not in session:
            return jsonify({"error": "Authentication required"}), 401

        # Check if the token is expired and refresh if necessary
        token_info = session['strava_token']
        if token_info['expires_at'] < time.time():
            try:
                new_token_info = strava_api.refresh_access_token(token_info['refresh_token'])
                session['strava_token'] = new_token_info
                session.modified = True
                logger.info("Token refreshed for user")
            except StravaAPIError as e:
                logger.error(f"Token refresh failed: {e}")
                session.clear()
                return jsonify({"error": "Authentication expired, please re-authenticate"}), 401

        return f(*args, **kwargs)
    return decorated_function


def create_gpx_string(activity_name: str, coords: list) -> str:
    """Creates a GPX XML string from a list of lat/lng coordinates."""
    gpx_points = ""
    for lat, lng in coords:
        gpx_points += f"  <trkpt lat=\"{lat}\" lon=\"{lng}\"></trkpt>\n"

    return f"""<?xml version="1.0" encoding="UTF-8"?>
<gpx version="1.1" creator="Strava Route Discovery App" xmlns="http://www.topografix.com/GPX/1/1">
  <trk>
    <name>{activity_name}</name>
    <trkseg>
{gpx_points}
    </trkseg>
  </trk>
</gpx>
"""

@app.route("/api/activities/<int:activity_id>/stream")
@auth_required
def get_activity_stream_data(activity_id):
    """Fetches the lat/lng stream for a specific activity."""
    access_token = session['strava_token']['access_token']
    try:
        latlng_stream = strava_api.get_activity_stream(activity_id, access_token)
        if not latlng_stream:
            return jsonify({"error": "No GPS data found for this activity"}), 404
        
        # The frontend expects [latitude, longitude], but the stream is [lat, lng]. It's already correct.
        return jsonify({"stream": latlng_stream})
    except StravaAPIError as e:
        logger.error(f"Failed to fetch stream for activity {activity_id}: {e}")
        return jsonify({"error": "Failed to fetch activity data"}), 500
    

@app.route("/auth/strava")
def strava_auth():
    """Redirects user to Strava for authentication."""
    redirect_uri = url_for('strava_callback', _external=True)
    auth_url = strava_api.get_authorization_url(redirect_uri)
    return redirect(auth_url)


@app.route("/auth/strava/callback")
def strava_callback():
    """Handles the callback from Strava after authentication."""
    code = request.args.get('code')
    if not code:
        logger.warning("Auth callback received without code")
        return jsonify({"error": "Authorization code not provided"}), 400

    try:
        token_info = strava_api.exchange_code_for_token(code)
        session['strava_token'] = token_info
        logger.info("User successfully authenticated with Strava")
        return redirect("http://localhost:5173/activities")
    except StravaAPIError as e:
        logger.error(f"Authentication failed: {e}")
        return jsonify({"error": "Authentication failed"}), 500


@app.route("/auth/status")
def auth_status():
    """Checks if the user is currently authenticated."""
    if 'strava_token' in session and session['strava_token']['expires_at'] > time.time():
        return jsonify({"authenticated": True})
    return jsonify({"authenticated": False})


@app.route("/auth/logout", methods=['POST'])
def logout():
    """Logs the user out by clearing the session."""
    session.clear()
    return jsonify({"message": "Successfully logged out"}), 200

@app.route("/api/activities")
@auth_required
def get_activities():
    """Fetches user activities from Strava."""
    access_token = session['strava_token']['access_token']
    try:
        activities = strava_api.get_activities(access_token, per_page=50)
        # Filter activities with GPS data
        filtered_activities = [
            {
                "id": act["id"],
                "name": act["name"],
                "distance": round(act["distance"], 2),
                "type": act["type"],
                "start_date": act["start_date_local"],
            }
            for act in activities if act.get("map", {}).get("summary_polyline")
        ]
        logger.info(f"Fetched {len(filtered_activities)} activities for user")
        return jsonify(filtered_activities)
    except StravaAPIError as e:
        logger.error(f"Failed to fetch activities: {e}")
        return jsonify({"error": "Failed to fetch activities"}), 500


@app.route("/api/activities/<int:activity_id>/gpx")
@auth_required
def get_activity_gpx(activity_id):
    """Fetches GPX data for a specific activity."""
    access_token = session['strava_token']['access_token']
    try:
        latlng_stream = strava_api.get_activity_stream(activity_id, access_token)
        if not latlng_stream:
            return jsonify({"error": "No GPS data found for this activity"}), 404

        gpx_data = create_gpx_string(f"Activity {activity_id}", latlng_stream)
        return jsonify({"gpx": gpx_data})
    except StravaAPIError as e:
        logger.error(f"Failed to fetch GPX for activity {activity_id}: {e}")
        return jsonify({"error": "Failed to fetch activity data"}), 500


@app.route("/api/pois", methods=['POST'])
def get_nearby_pois():
    """Finds points of interest near a given route."""
    data = request.get_json()
    if not data or 'route' not in data:
        return jsonify({"error": "Route data is required"}), 400
    
    route = data['route']
    if not isinstance(route, list) or len(route) < 2:
        return jsonify({"error": "Route must be a list with at least 2 coordinates"}), 400

    # Convert [lat, lng] to [lng, lat] for Google Maps API
    try:
        route_coords = [[coord[1], coord[0]] for coord in route]
        pois = get_pois_for_route(route_coords)
        logger.info(f"Found {len(pois)} POIs for route")
        return jsonify(pois)
    except (IndexError, TypeError) as e:
        logger.error(f"Invalid route format: {e}")
        return jsonify({"error": "Invalid route coordinate format"}), 400
    except Exception as e:
        logger.error(f"Error fetching POIs: {e}")
        return jsonify({"error": "Failed to retrieve points of interest"}), 500

if __name__ == "__main__":
    app.run(port=5000, debug=Config.FLASK_DEBUG)