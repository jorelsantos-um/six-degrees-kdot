"""
Data Fetcher Module for Spotify API

This module handles fetching artist data from the Spotify API, including
artist search, album retrieval, and collaboration discovery. All API
responses are cached locally to minimize API calls and improve performance.
"""

import os
import json
import time
import hashlib
from pathlib import Path
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta

import requests
from dotenv import load_dotenv


# Custom Exceptions
class SpotifyAPIError(Exception):
    """Base exception for Spotify API errors"""
    pass


class AuthenticationError(SpotifyAPIError):
    """Exception raised for authentication failures"""
    pass


class SpotifyAPIClient:
    """
    Client for interacting with the Spotify Web API.

    Handles authentication, rate limiting, error handling, and caching
    of API responses to minimize redundant requests.
    """

    BASE_URL = "https://api.spotify.com/v1"
    TOKEN_URL = "https://accounts.spotify.com/api/token"
    CACHE_EXPIRY_DAYS = 7

    def __init__(self, cache_dir: str = "data"):
        """
        Initialize the Spotify API client.

        Args:
            cache_dir: Directory to store cached API responses

        Raises:
            AuthenticationError: If API credentials are missing
        """
        # Load environment variables
        load_dotenv()

        self.client_id = os.getenv("SPOTIFY_CLIENT_ID")
        self.client_secret = os.getenv("SPOTIFY_CLIENT_SECRET")

        # Validate credentials
        if not self.client_id or not self.client_secret:
            raise AuthenticationError(
                "Missing Spotify credentials. Please set SPOTIFY_CLIENT_ID "
                "and SPOTIFY_CLIENT_SECRET in your .env file."
            )

        # Set up cache directory
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(exist_ok=True)

        # Initialize access token
        self.access_token = None
        self.token_expiry = None

    def _get_access_token(self) -> str:
        """
        Obtain an access token using OAuth 2.0 Client Credentials flow.

        Returns:
            Valid access token string

        Raises:
            AuthenticationError: If authentication fails
        """
        # Return cached token if still valid
        if self.access_token and self.token_expiry and datetime.now() < self.token_expiry:
            return self.access_token

        # Request new token
        auth_response = requests.post(
            self.TOKEN_URL,
            data={"grant_type": "client_credentials"},
            auth=(self.client_id, self.client_secret)
        )

        if auth_response.status_code != 200:
            raise AuthenticationError(
                f"Authentication failed: {auth_response.status_code} - {auth_response.text}"
            )

        auth_data = auth_response.json()
        self.access_token = auth_data["access_token"]

        # Set token expiry (subtract 60 seconds for safety margin)
        expires_in = auth_data.get("expires_in", 3600)
        self.token_expiry = datetime.now() + timedelta(seconds=expires_in - 60)

        return self.access_token

    def _make_request(self, endpoint: str, params: Optional[Dict] = None,
                     retries: int = 3) -> Dict[str, Any]:
        """
        Make an authenticated request to the Spotify API with error handling.

        Args:
            endpoint: API endpoint (e.g., '/search')
            params: Query parameters
            retries: Number of retry attempts for rate limiting

        Returns:
            JSON response as dictionary

        Raises:
            SpotifyAPIError: If request fails after retries
        """
        url = f"{self.BASE_URL}{endpoint}"
        token = self._get_access_token()
        headers = {"Authorization": f"Bearer {token}"}

        for attempt in range(retries):
            try:
                response = requests.get(url, headers=headers, params=params)

                # Handle rate limiting (429)
                if response.status_code == 429:
                    retry_after = int(response.headers.get("Retry-After", 1))
                    print(f"Rate limited. Waiting {retry_after} seconds...")
                    time.sleep(retry_after)
                    continue

                # Handle authentication errors (401)
                if response.status_code == 401:
                    # Token may have expired, get a new one
                    self.access_token = None
                    token = self._get_access_token()
                    headers = {"Authorization": f"Bearer {token}"}
                    continue

                # Handle not found (404)
                if response.status_code == 404:
                    raise SpotifyAPIError(f"Resource not found: {endpoint}")

                # Raise error for other bad status codes
                response.raise_for_status()

                return response.json()

            except requests.exceptions.RequestException as e:
                if attempt == retries - 1:
                    raise SpotifyAPIError(f"Request failed after {retries} attempts: {str(e)}")

                # Exponential backoff
                wait_time = 2 ** attempt
                print(f"Request failed, retrying in {wait_time} seconds...")
                time.sleep(wait_time)

        raise SpotifyAPIError(f"Request failed after {retries} attempts")

    def _generate_cache_key(self, identifier: str) -> str:
        """
        Generate a cache key from an identifier.

        Args:
            identifier: String to hash (e.g., 'artist_kendrick_lamar')

        Returns:
            MD5 hash of the identifier
        """
        return hashlib.md5(identifier.encode()).hexdigest()

    def _get_cache_path(self, cache_key: str) -> Path:
        """
        Get the file path for a cache key.

        Args:
            cache_key: Cache key hash

        Returns:
            Path to cache file
        """
        return self.cache_dir / f"{cache_key}.json"

    def _load_from_cache(self, cache_key: str) -> Optional[Dict[str, Any]]:
        """
        Load data from cache if it exists and hasn't expired.

        Args:
            cache_key: Cache key hash

        Returns:
            Cached data if valid, None otherwise
        """
        cache_path = self._get_cache_path(cache_key)

        if not cache_path.exists():
            return None

        try:
            with open(cache_path, 'r') as f:
                cache_data = json.load(f)

            # Check expiry
            cached_time = datetime.fromisoformat(cache_data["cached_at"])
            expiry_time = cached_time + timedelta(days=self.CACHE_EXPIRY_DAYS)

            if datetime.now() > expiry_time:
                print(f"Cache expired for {cache_key}")
                return None

            print(f"Loading from cache: {cache_key}")
            return cache_data["data"]

        except (json.JSONDecodeError, KeyError, ValueError) as e:
            print(f"Error reading cache: {e}")
            return None

    def _save_to_cache(self, cache_key: str, data: Dict[str, Any]) -> None:
        """
        Save data to cache with timestamp.

        Args:
            cache_key: Cache key hash
            data: Data to cache
        """
        cache_path = self._get_cache_path(cache_key)

        cache_data = {
            "cached_at": datetime.now().isoformat(),
            "data": data
        }

        try:
            with open(cache_path, 'w') as f:
                json.dump(cache_data, f, indent=2)
            print(f"Saved to cache: {cache_key}")
        except IOError as e:
            print(f"Warning: Failed to save cache: {e}")

    def search_artist(self, artist_name: str) -> Optional[Dict[str, Any]]:
        """
        Search for an artist by name on Spotify.

        Args:
            artist_name: Name of the artist to search for

        Returns:
            Dictionary containing artist info (id, name, popularity, genres)
            or None if not found

        Raises:
            SpotifyAPIError: If the API request fails
        """
        # Check cache first
        cache_key = self._generate_cache_key(f"artist_search_{artist_name.lower()}")
        cached_data = self._load_from_cache(cache_key)
        if cached_data is not None:
            return cached_data

        # Make API request
        params = {
            "q": artist_name,
            "type": "artist",
            "limit": 1
        }

        response = self._make_request("/search", params)

        artists = response.get("artists", {}).get("items", [])

        if not artists:
            print(f"No artist found for: {artist_name}")
            return None

        artist = artists[0]
        artist_data = {
            "id": artist["id"],
            "name": artist["name"],
            "popularity": artist.get("popularity", 0),
            "genres": artist.get("genres", []),
            "followers": artist.get("followers", {}).get("total", 0),
            "uri": artist["uri"]
        }

        # Cache the result
        self._save_to_cache(cache_key, artist_data)

        return artist_data

    def get_artist_albums(self, artist_id: str, limit: int = 50) -> List[Dict[str, Any]]:
        """
        Get all albums for an artist.

        Args:
            artist_id: Spotify artist ID
            limit: Maximum number of albums to fetch

        Returns:
            List of album dictionaries with id, name, and release_date

        Raises:
            SpotifyAPIError: If the API request fails
        """
        # Check cache first
        cache_key = self._generate_cache_key(f"artist_albums_{artist_id}")
        cached_data = self._load_from_cache(cache_key)
        if cached_data is not None:
            return cached_data

        # Make API request
        params = {
            "include_groups": "album,single,appears_on",
            "limit": limit
        }

        response = self._make_request(f"/artists/{artist_id}/albums", params)

        albums = []
        for album in response.get("items", []):
            albums.append({
                "id": album["id"],
                "name": album["name"],
                "release_date": album.get("release_date", ""),
                "type": album.get("album_type", ""),
                "total_tracks": album.get("total_tracks", 0)
            })

        # Cache the result
        self._save_to_cache(cache_key, albums)

        return albums

    def get_album_tracks(self, album_id: str) -> List[Dict[str, Any]]:
        """
        Get all tracks from an album.

        Args:
            album_id: Spotify album ID

        Returns:
            List of track dictionaries with id, name, and artists

        Raises:
            SpotifyAPIError: If the API request fails
        """
        # Check cache first
        cache_key = self._generate_cache_key(f"album_tracks_{album_id}")
        cached_data = self._load_from_cache(cache_key)
        if cached_data is not None:
            return cached_data

        # Make API request
        response = self._make_request(f"/albums/{album_id}/tracks")

        tracks = []
        for track in response.get("items", []):
            tracks.append({
                "id": track["id"],
                "name": track["name"],
                "artists": [
                    {"id": artist["id"], "name": artist["name"]}
                    for artist in track.get("artists", [])
                ]
            })

        # Cache the result
        self._save_to_cache(cache_key, tracks)

        return tracks

    def _parse_featured_artists(self, track_name: str) -> List[str]:
        """
        Extract featured artists from track name.

        Looks for patterns like "(feat. Artist)" or "(with Artist)"

        Args:
            track_name: Name of the track

        Returns:
            List of featured artist names
        """
        import re

        featured = []

        # Patterns to match: (feat. X), (ft. X), (featuring X), (with X)
        patterns = [
            r'\(feat\.\s*([^)]+)\)',
            r'\(ft\.\s*([^)]+)\)',
            r'\(featuring\s+([^)]+)\)',
            r'\(with\s+([^)]+)\)'
        ]

        for pattern in patterns:
            matches = re.findall(pattern, track_name, re.IGNORECASE)
            for match in matches:
                # Split by common separators
                artists = re.split(r',|\&|and', match)
                featured.extend([a.strip() for a in artists if a.strip()])

        return featured

    def get_artist_collaborators(self, artist_id: str, max_albums: int = 20) -> Dict[str, Dict[str, Any]]:
        """
        Get all collaborators for an artist by analyzing their tracks.

        Finds collaborators from:
        - Featured artists on the main artist's tracks
        - Track credits showing multiple artists
        - Featured artist mentions in track titles

        Args:
            artist_id: Spotify artist ID
            max_albums: Maximum number of albums to analyze

        Returns:
            Dictionary mapping normalized artist names to their info and collaboration count
            Format: {artist_name: {"id": str, "name": str, "count": int, "tracks": [str]}}

        Raises:
            SpotifyAPIError: If API requests fail
        """
        # Check cache first
        cache_key = self._generate_cache_key(f"artist_collaborators_{artist_id}_{max_albums}")
        cached_data = self._load_from_cache(cache_key)
        if cached_data is not None:
            return cached_data

        print(f"Fetching collaborators for artist ID: {artist_id}")

        # Get the main artist's info to filter them out
        main_artist_info = self._make_request(f"/artists/{artist_id}")
        main_artist_name = main_artist_info["name"].lower()
        print(f"Main artist: {main_artist_info['name']}")

        # Get artist's albums
        albums = self.get_artist_albums(artist_id, limit=max_albums)
        print(f"Found {len(albums)} albums")

        # Use normalized names as keys to avoid duplicates
        collaborators = {}

        # Process each album
        for i, album in enumerate(albums[:max_albums], 1):
            print(f"Processing album {i}/{min(len(albums), max_albums)}: {album['name']}")

            try:
                tracks = self.get_album_tracks(album["id"])

                for track in tracks:
                    # Check all artists on the track
                    for artist in track["artists"]:
                        # Skip if it's the main artist (by ID or name)
                        artist_name_lower = artist["name"].lower()
                        if artist["id"] == artist_id or artist_name_lower == main_artist_name:
                            continue

                        # Use normalized name as key to avoid duplicates
                        if artist_name_lower not in collaborators:
                            collaborators[artist_name_lower] = {
                                "id": artist["id"],
                                "name": artist["name"],  # Keep original capitalization
                                "count": 0,
                                "tracks": []
                            }

                        collaborators[artist_name_lower]["count"] += 1
                        if track["name"] not in collaborators[artist_name_lower]["tracks"]:
                            collaborators[artist_name_lower]["tracks"].append(track["name"])

                    # Also parse featured artists from track name
                    featured_names = self._parse_featured_artists(track["name"])
                    for featured_name in featured_names:
                        featured_name_lower = featured_name.lower()

                        # Skip if it's the main artist
                        if featured_name_lower == main_artist_name:
                            continue

                        # Skip if already in collaborators (from artist credits)
                        if featured_name_lower in collaborators:
                            # Just increment count, don't add as duplicate
                            collaborators[featured_name_lower]["count"] += 1
                            if track["name"] not in collaborators[featured_name_lower]["tracks"]:
                                collaborators[featured_name_lower]["tracks"].append(track["name"])
                        else:
                            # Add new featured artist
                            collaborators[featured_name_lower] = {
                                "id": None,  # No ID available from track name parsing
                                "name": featured_name,
                                "count": 1,
                                "tracks": [track["name"]]
                            }

                # Rate limiting - be nice to the API
                time.sleep(0.1)

            except SpotifyAPIError as e:
                print(f"Error processing album {album['name']}: {e}")
                continue

        print(f"Found {len(collaborators)} unique collaborators")

        # Cache the result
        self._save_to_cache(cache_key, collaborators)

        return collaborators


# Convenience functions for quick usage
def get_spotify_client() -> SpotifyAPIClient:
    """
    Create and return a Spotify API client instance.

    Returns:
        Configured SpotifyAPIClient

    Raises:
        AuthenticationError: If credentials are missing
    """
    return SpotifyAPIClient()


if __name__ == "__main__":
    # Example usage
    try:
        client = get_spotify_client()

        # Search for Kendrick Lamar
        artist = client.search_artist("Kendrick Lamar")
        if artist:
            print(f"\nFound artist: {artist['name']}")
            print(f"ID: {artist['id']}")
            print(f"Popularity: {artist['popularity']}")
            print(f"Genres: {', '.join(artist['genres'])}")

            # Get collaborators
            print("\nFetching collaborators...")
            collaborators = client.get_artist_collaborators(artist["id"], max_albums=10)

            # Show top 15 collaborators
            sorted_collabs = sorted(
                collaborators.items(),
                key=lambda x: x[1]["count"],
                reverse=True
            )

            print(f"\nTop 15 Collaborators:")
            for i, (artist_key, info) in enumerate(sorted_collabs[:15], 1):
                collab_id = info.get('id', 'N/A')
                print(f"{i}. {info['name']} - {info['count']} collaborations")
                if i <= 5:  # Show sample tracks for top 5
                    sample_tracks = info['tracks'][:2]
                    print(f"   Sample tracks: {', '.join(sample_tracks)}")

    except AuthenticationError as e:
        print(f"Authentication error: {e}")
        print("\nPlease create a .env file with your Spotify credentials:")
        print("SPOTIFY_CLIENT_ID=your_client_id")
        print("SPOTIFY_CLIENT_SECRET=your_client_secret")
    except SpotifyAPIError as e:
        print(f"API error: {e}")
