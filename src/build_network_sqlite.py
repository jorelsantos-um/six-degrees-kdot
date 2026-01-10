"""
SQLite Network Builder for Six Degrees of Kendrick Lamar

This script builds the artist collaboration network and stores it in SQLite.
Run this once to populate the database, then use the Streamlit app to query it.
"""

import sys
from pathlib import Path
from typing import Set

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent))

from data_fetcher import SpotifyAPIClient
from database import CollaborationDatabase


# Kendrick Lamar's Spotify ID
KENDRICK_ID = "2YZyLoL8N0Wb9xBt1NhZWg"


def build_network(
    db: CollaborationDatabase,
    client: SpotifyAPIClient,
    starting_artist_id: str = KENDRICK_ID,
    depth: int = 2,
    max_albums: int = 15
) -> None:
    """
    Build the collaboration network using BFS from a starting artist.

    Args:
        db: CollaborationDatabase instance
        client: SpotifyAPIClient instance
        starting_artist_id: Artist ID to start from (default: Kendrick Lamar)
        depth: How many degrees of separation to build
        max_albums: Maximum albums to analyze per artist
    """
    print(f"\n{'='*70}")
    print(f"Building {depth}-degree network from starting artist...")
    print(f"{'='*70}")

    # Track processed artists
    processed: Set[str] = set()

    # Current level of artists to process
    current_level = {starting_artist_id}

    for level in range(depth):
        print(f"\n--- Processing Degree {level + 1} ({len(current_level)} artists) ---")

        next_level: Set[str] = set()

        for artist_id in current_level:
            if artist_id in processed:
                continue

            try:
                # Get artist info
                print(f"\nFetching artist {artist_id}...")
                artist_info = client._make_request(f"/artists/{artist_id}")
                artist_name = artist_info['name']
                print(f"Processing: {artist_name}")

                # Add artist to database
                db.add_artist(
                    artist_id=artist_id,
                    name=artist_name,
                    popularity=artist_info.get('popularity', 0),
                    genres=artist_info.get('genres', [])
                )

                # Get collaborators
                collaborators = client.get_artist_collaborators(artist_id, max_albums)
                print(f"  Found {len(collaborators)} collaborators")

                # Add each collaborator
                for collab_key, collab_info in collaborators.items():
                    collab_id = collab_info.get('id')
                    collab_name = collab_info['name']

                    # Skip collaborators without IDs
                    if not collab_id:
                        continue

                    # Add collaborator to database
                    db.add_artist(
                        artist_id=collab_id,
                        name=collab_name
                    )

                    # Add edges for each song
                    for song in collab_info['tracks']:
                        db.add_collaboration(artist_id, collab_id, song)

                    # Queue for next level
                    next_level.add(collab_id)

                processed.add(artist_id)

            except Exception as e:
                print(f"  Error processing artist {artist_id}: {e}")
                processed.add(artist_id)
                continue

        # Move to next level
        current_level = next_level - processed

    # Print final stats
    stats = db.get_stats()
    print(f"\n{'='*70}")
    print(f"Network built successfully!")
    print(f"  Total artists: {stats['total_artists']}")
    print(f"  Total collaborations: {stats['total_collaborations']}")
    print(f"  Total songs: {stats['total_songs']}")
    print(f"{'='*70}\n")


def main():
    """Main entry point for building the network."""
    print("=" * 70)
    print("Six Degrees of Kendrick Lamar - Network Builder")
    print("=" * 70)
    print("\nThis will build a collaboration network starting from Kendrick Lamar.")
    print("Estimated time: 10-15 minutes for a 2-degree network.\n")

    # Initialize database
    db_path = Path(__file__).parent.parent / "data" / "collaboration_network.db"
    print(f"Database: {db_path}")

    db = CollaborationDatabase(str(db_path))

    # Check existing data
    stats = db.get_stats()
    if stats['total_artists'] > 0:
        print(f"\nExisting database found:")
        print(f"  - {stats['total_artists']} artists")
        print(f"  - {stats['total_collaborations']} collaborations")
        response = input("\nRebuild from scratch? (y/n): ").strip().lower()
        if response != 'y':
            print("Keeping existing database. Exiting.")
            return

        # Clear existing data
        print("Clearing existing data...")
        with db._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM songs")
            cursor.execute("DELETE FROM collaborations")
            cursor.execute("DELETE FROM artists")

    # Initialize Spotify client
    print("\nInitializing Spotify client...")
    try:
        client = SpotifyAPIClient()
    except Exception as e:
        print(f"\nError: Could not initialize Spotify client.")
        print(f"Make sure you have a .env file with SPOTIFY_CLIENT_ID and SPOTIFY_CLIENT_SECRET")
        print(f"Error details: {e}")
        return

    # Verify Kendrick exists
    print("Verifying Kendrick Lamar...")
    kendrick = client.search_artist("Kendrick Lamar")
    if not kendrick:
        print("Error: Could not find Kendrick Lamar on Spotify!")
        return

    print(f"Found: {kendrick['name']} (ID: {kendrick['id']})")

    # Build the network
    build_network(
        db=db,
        client=client,
        starting_artist_id=kendrick['id'],
        depth=2,
        max_albums=15
    )

    print("Done! Your network is ready in the SQLite database.")
    print(f"Database location: {db_path}")


if __name__ == "__main__":
    main()
