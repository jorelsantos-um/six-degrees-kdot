#!/usr/bin/env python3
"""
Six Degrees of Kendrick Lamar - Main Application

Interactive CLI application to find the shortest path between any artist
and Kendrick Lamar, showing degrees of separation and collaboration songs.
"""

import sys
import os

# Add src directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from data_fetcher import get_spotify_client, SpotifyAPIClient
from network_builder import CollaborationNetwork
from path_finder import PathFinder


# Kendrick Lamar's Spotify ID
KENDRICK_ID = "2YZyLoL8N0Wb9xBt1NhZWg"
KENDRICK_NAME = "Kendrick Lamar"
NETWORK_FILE = "data/collaboration_network.pkl"


class SixDegreesApp:
    """
    Main application for Six Degrees of Kendrick Lamar.
    """

    def __init__(self):
        """Initialize the application."""
        self.client = None
        self.network = None
        self.path_finder = None

    def initialize(self):
        """
        Initialize Spotify client and load/build network.
        """
        print("\n" + "="*80)
        print(" " * 20 + "SIX DEGREES OF KENDRICK LAMAR")
        print("="*80)
        print()

        # Initialize Spotify client
        print("Initializing Spotify client...")
        try:
            self.client = get_spotify_client()
            print("✓ Spotify client ready\n")
        except Exception as e:
            print(f"✗ Error initializing Spotify client: {e}")
            print("\nPlease ensure your .env file has valid credentials:")
            print("  SPOTIFY_CLIENT_ID=your_client_id")
            print("  SPOTIFY_CLIENT_SECRET=your_client_secret")
            return False

        # Load or build network
        print("Loading collaboration network...")
        self.network = CollaborationNetwork(self.client)

        if self.network.load_network(NETWORK_FILE):
            print("✓ Network loaded successfully\n")
            stats = self.network.get_network_stats()
            print(f"Network contains:")
            print(f"  • {stats['total_artists']} artists")
            print(f"  • {stats['total_collaborations']} collaborations")
            print()
        else:
            print("\n⚠ No saved network found. Building new network...")
            print("This will take 10-15 minutes. Please be patient.\n")

            response = input("Build network now? (yes/no): ").strip().lower()
            if response not in ['yes', 'y']:
                print("Cannot proceed without a network. Exiting.")
                return False

            try:
                # Build 2-degree network from Kendrick
                self.network.build_network(KENDRICK_ID, depth=2, max_albums=15)
                self.network.save_network(NETWORK_FILE)
                print("\n✓ Network built and saved successfully\n")
            except Exception as e:
                print(f"\n✗ Error building network: {e}")
                return False

        # Initialize path finder
        self.path_finder = PathFinder(self.network)
        print("✓ Path finder ready\n")

        return True

    def search_artist(self, artist_name: str):
        """
        Search for an artist and return their info.

        Args:
            artist_name: Name of the artist to search for

        Returns:
            Artist info dictionary or None
        """
        print(f"\nSearching for '{artist_name}'...")
        artist_info = self.client.search_artist(artist_name)

        if not artist_info:
            print(f"✗ Could not find artist: {artist_name}")
            print("  Please check the spelling and try again.")
            return None

        print(f"✓ Found: {artist_info['name']}")
        return artist_info

    def find_and_display_path(self, artist_id: str, artist_name: str):
        """
        Find path from artist to Kendrick and display results.

        Args:
            artist_id: Spotify artist ID
            artist_name: Artist's name
        """
        print(f"\nFinding connection to Kendrick Lamar...")

        # Check if artist is in network
        if not self.network.artist_in_network(artist_id):
            print(f"\n⚠ {artist_name} is not in the current network.")
            print("Attempting to expand network...")

            try:
                # Add the artist and their collaborators
                new_collabs = self.network.add_artist_and_collaborators(artist_id, max_albums=15)
                print(f"✓ Added {artist_name} and {new_collabs} collaborators to network")

                # Update saved network
                self.network.save_network(NETWORK_FILE)
                print("✓ Network updated and saved")

            except Exception as e:
                print(f"✗ Error expanding network: {e}")
                print("\nNo path that we know of.")
                return

        # Find path
        path_info = self.path_finder.find_connection(artist_id, KENDRICK_ID)

        if path_info:
            # Display formatted path
            print("\n" + self.path_finder.format_path_output(path_info))
        else:
            print("\nNo path that we know of.")

    def run(self):
        """
        Main application loop.
        """
        # Initialize
        if not self.initialize():
            return

        print("="*80)
        print("\nWelcome! Enter any artist name to find their connection to Kendrick Lamar.")
        print("Type 'quit' or 'exit' to leave.\n")
        print("="*80)

        # Main loop
        while True:
            # Get user input
            print("\n" + "-"*80)
            artist_name = input("\nEnter artist name: ").strip()

            # Check for exit
            if artist_name.lower() in ['quit', 'exit', 'q']:
                print("\nThanks for using Six Degrees of Kendrick Lamar!")
                print("="*80)
                break

            # Validate input
            if not artist_name:
                print("Please enter an artist name.")
                continue

            # Check if searching for Kendrick himself
            if artist_name.lower() in ['kendrick lamar', 'kendrick', 'k dot', 'k.dot', 'kdot']:
                print("\n⚠ You searched for Kendrick Lamar!")
                print("Please try searching for a different artist.")
                continue

            # Search for artist
            artist_info = self.search_artist(artist_name)
            if not artist_info:
                continue

            # Find and display path
            self.find_and_display_path(artist_info['id'], artist_info['name'])


def main():
    """
    Entry point for the application.
    """
    try:
        app = SixDegreesApp()
        app.run()
    except KeyboardInterrupt:
        print("\n\nInterrupted by user. Exiting...")
        print("="*80)
    except Exception as e:
        print(f"\n\nUnexpected error: {e}")
        print("="*80)
        sys.exit(1)


if __name__ == "__main__":
    main()
