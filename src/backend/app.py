import os
import time
from flask import Flask, request, jsonify, redirect, session, url_for
from dotenv import load_dotenv
from functools import wraps

from strava_client import get_strava_client
from poi_service import get_pois_for_route

# Load environment variables
load_dotenv()

app = Flask(__name__)
app.secret_key = os.getenv("FLASK_SECRET_KEY")

strava_api = get_strava_client()

# --- Helpers & Decorators ---

def auth_required(f):
    """Decorator to protect endpoints that require authentication."""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'strava_token' not in session:
            return jsonify({"error": "Unauthorized"}), 401

        # Check if the token is expired and refresh if necessary
        token_info = session['strava_token']
        if token_info['expires_at'] < time.time():
            try:
                new_token_info = strava_api.refresh_access_token(token_info['refresh_token'])
                session['strava_token'] = new_token_info
                session.modified = True
            except Exception as e:
                print(f"Error refreshing token: {e}")
                session.clear()
                return jsonify({"error": "Failed to refresh token, please re-authenticate"}), 401

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


# --- Authentication Endpoints ---

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
        return "Error: No code provided.", 400

    try:
        token_info = strava_api.exchange_code_for_token(code)
        session['strava_token'] = token_info
        # Redirect to frontend authenticated route
        return redirect("http://localhost:5173/activities")
    except Exception as e:
        print(e)
        return "Error: Could not exchange code for token.", 500


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


# --- API Endpoints ---

@app.route("/api/activities")
@auth_required
def get_activities():
    """Fetches user activities from Strava."""
    access_token = session['strava_token']['access_token']
    try:
        activities = strava_api.get_activities(access_token, per_page=50)
        # Simplify the data for the frontend
        filtered_activities = [
            {
                "id": act["id"],
                "name": act["name"],
                "distance": act["distance"],
                "type": act["type"],
                "start_date": act["start_date_local"],
            }
            for act in activities if act.get("map", {}).get("summary_polyline")
        ]
        return jsonify(filtered_activities)
    except Exception as e:
        print(e)
        return jsonify({"error": "Failed to fetch activities"}), 500


@app.route("/api/activities/<int:activity_id>/gpx")
@auth_required
def get_activity_gpx(activity_id):
    """Fetches GPX data for a specific activity."""
    access_token = session['strava_token']['access_token']
    try:
        latlng_stream = strava_api.get_activity_stream(activity_id, access_token)
        if not latlng_stream:
            return jsonify({"error": "No latitude/longitude data found for this activity."}), 404

        gpx_data = create_gpx_string(f"Activity {activity_id}", latlng_stream)
        return jsonify({"gpx": gpx_data})
    except Exception as e:
        print(e)
        return jsonify({"error": "Failed to fetch activity stream"}), 500


@app.route("/api/pois", methods=['POST'])
def get_nearby_pois():
    """Finds points of interest near a given route."""
    data = request.get_json()
    if not data or 'route' not in data:
        return jsonify({"error": "Missing route data"}), 400

    # The frontend sends [lat, lng], but osmnx wants [lng, lat]
    route_coords = [[coord[1], coord[0]] for coord in data['route']]

    try:
        pois = get_pois_for_route(route_coords)
        return jsonify(pois)
    except Exception as e:
        print(f"Error fetching POIs: {e}")
        return jsonify({"error": "Failed to retrieve points of interest"}), 500


if __name__ == "__main__":
    app.run(port=5000, debug=True)