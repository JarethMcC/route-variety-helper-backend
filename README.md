# Route Variety Helper Backend

A Flask-based backend service that integrates with Strava and Google Maps APIs to help users discover points of interest (POIs) along their cycling and running routes.

## Features

- **Strava Integration**: OAuth authentication and activity data retrieval
- **Route Analysis**: Fetch GPS tracks from Strava activities
- **POI Discovery**: Find cafes, restaurants, tourist attractions, and other points of interest along routes
- **GPX Export**: Convert Strava activities to GPX format
- **Smart Route Sampling**: Optimized POI search to minimize API calls while maintaining coverage

## Architecture

- **Flask** web framework with session-based authentication
- **Strava API** for activity data and OAuth
- **Google Maps Places API** for POI discovery
- **Gunicorn** WSGI server for production deployment

## Prerequisites

- Python 3.8+
- Strava API credentials (Client ID and Secret)
- Google Maps API key with Places API enabled

## Setup

### 1. Clone and Install Dependencies

```bash
git clone <repository-url>
cd route-variety-helper-backend
cd src
pip install -r requirements.txt
```

### 2. Environment Configuration

Copy the example environment file and configure your API keys:

```bash
cp .env.example .env
```

Edit `.env` with your credentials:

```bash
STRAVA_CLIENT_ID="your_strava_client_id"
STRAVA_CLIENT_SECRET="your_strava_client_secret"
GOOGLE_MAPS_API_KEY="your_google_maps_api_key"
FLASK_SECRET_KEY="your-secure-secret-key"
FLASK_ENV="development"

# Optional: POI search optimization
POI_SEARCH_RADIUS=100
POI_ROUTE_SAMPLING_DISTANCE=500
```

### 3. Strava App Setup

1. Go to [Strava Developers](https://developers.strava.com/)
2. Create a new application
3. Set authorization callback domain to your domain (e.g., `localhost` for development)
4. Note your Client ID and Client Secret

### 4. Google Maps API Setup

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Enable the Places API
3. Create an API key
4. Restrict the key to Places API for security

## Running the Application

### Development

```bash
cd src
python app.py
```

The server will start on `http://localhost:5000`

### Production

```bash
cd src
gunicorn -c gunicorn_config.py app:app
```

## API Documentation

### Authentication Endpoints

#### GET `/auth/strava`
Redirects user to Strava for OAuth authentication.

#### GET `/auth/strava/callback`
Handles OAuth callback from Strava. Automatically redirects to frontend.

#### GET `/auth/status`
Check authentication status.

**Response:**
```json
{
  "authenticated": true
}
```

#### POST `/auth/logout`
Logs out the current user.

### Activity Endpoints

#### GET `/api/activities`
Fetch user's Strava activities (requires authentication).

**Response:**
```json
[
  {
    "id": 123456789,
    "name": "Morning Run",
    "distance": 5432.1,
    "type": "Run",
    "start_date": "2023-12-01T07:30:00Z"
  }
]
```

#### GET `/api/activities/<activity_id>/gpx`
Get GPX data for a specific activity.

**Response:**
```json
{
  "gpx": "<?xml version=\"1.0\"?>...</gpx>"
}
```

### POI Endpoints

#### POST `/api/pois`
Find points of interest along a route.

**Request:**
```json
{
  "route": [
    [latitude, longitude],
    [latitude, longitude]
  ]
}
```

**Response:**
```json
[
  {
    "name": "Local Cafe",
    "type": "Cafe",
    "coords": [lat, lng],
    "rating": 4.5,
    "price_level": 2
  }
]
```

## Configuration Options

| Variable | Default | Description |
|----------|---------|-------------|
| `POI_SEARCH_RADIUS` | 100 | Search radius in meters for POIs |
| `POI_ROUTE_SAMPLING_DISTANCE` | 500 | Distance between route sample points |
| `FLASK_SECRET_KEY` | Required | Secret key for session management |
| `FLASK_ENV` | production | Set to "development" for debug mode |

## Deployment

### Using Docker (Recommended)

Create a `Dockerfile`:

```dockerfile
FROM python:3.9-slim

WORKDIR /app
COPY src/ .
RUN pip install -r requirements.txt

EXPOSE 8000
CMD ["gunicorn", "-c", "gunicorn_config.py", "app:app"]
```

Build and run:

```bash
docker build -t route-variety-helper .
docker run -p 8000:8000 --env-file .env route-variety-helper
```

### Manual Deployment

1. Install dependencies on your server
2. Configure environment variables
3. Use a process manager like systemd or supervisor
4. Set up a reverse proxy (nginx/Apache) for HTTPS

## Troubleshooting

### Common Issues

**"Missing required environment variables"**
- Ensure all required variables are set in your `.env` file
- Check that the file is in the correct location (`src/.env`)

**"Authentication failed"**
- Verify Strava Client ID and Secret are correct
- Check that your callback URL is properly configured in Strava app settings

**"No GPS data found"**
- Some Strava activities don't have GPS tracks (treadmill runs, etc.)
- Only activities with `summary_polyline` data are supported

**"Google Maps API error"**
- Ensure Places API is enabled in Google Cloud Console
- Check that your API key has proper restrictions and permissions
- Verify you haven't exceeded API quotas

### Logging

The application logs to stdout/stderr. In production, configure your deployment to capture and rotate logs appropriately.

## Development

### Project Structure

```
src/
├── app.py              # Main Flask application
├── config.py           # Configuration management
├── strava_client.py    # Strava API client
├── poi_service.py      # Google Maps POI service
├── gunicorn_config.py  # Production server config
└── requirements.txt    # Python dependencies
```

### Adding New POI Types

Edit the `POI_TYPES` list in `poi_service.py` to include additional Google Places types.

## License

[Add your license information here]

## Contributing

[Add contribution guidelines here]
