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
        print("\n╔════════════════════════════════════════════════════════════╗")
        print("║         Six Degrees of Kendrick Lamar                      ║")
        print("╚════════════════════════════════════════════════════════════╝\n")

        # Initialize Spotify client (silently)
        try:
            self.client = get_spotify_client()
        except Exception as e:
            print(f"✗ Error: Could not connect to Spotify API")
            print("  Please check your .env file has valid credentials\n")
            return False

        # Load or build network
        self.network = CollaborationNetwork(self.client)

        if self.network.load_network(NETWORK_FILE):
            stats = self.network.get_network_stats()
            print(f"✓ Loaded network: {stats['total_artists']} artists, {stats['total_collaborations']} collaborations\n")
        else:
            print("⚠ No saved network found. Building new network...")
            print("  This will take 10-15 minutes.\n")

            response = input("Build network now? (yes/no): ").strip().lower()
            if response not in ['yes', 'y']:
                print("Cannot proceed without a network. Exiting.")
                return False

            try:
                # Build 2-degree network from Kendrick
                self.network.build_network(KENDRICK_ID, depth=2, max_albums=15)
                self.network.save_network(NETWORK_FILE)
                print("\n✓ Network built successfully\n")
            except Exception as e:
                print(f"\n✗ Error building network: {e}")
                return False

        # Initialize path finder
        self.path_finder = PathFinder(self.network)

        return True

    def search_artist(self, artist_name: str):
        """
        Search for an artist and return their info.

        Args:
            artist_name: Name of the artist to search for

        Returns:
            Artist info dictionary or None
        """
        artist_info = self.client.search_artist(artist_name)

        if not artist_info:
            print(f"✗ Could not find '{artist_name}' - check spelling and try again\n")
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
        # Check if artist is in network
        if not self.network.artist_in_network(artist_id):
            print(f"⚠ {artist_name} not in network - expanding (2-3 min)...\n")

            try:
                # Build a 2-degree network from the artist to find bridges
                initial_size = self.network.graph.number_of_nodes()
                self.network.build_network(artist_id, depth=2, max_albums=15)
                final_size = self.network.graph.number_of_nodes()
                new_artists = final_size - initial_size

                print(f"✓ Added {new_artists} artists to network\n")

                # Update saved network
                self.network.save_network(NETWORK_FILE)

            except Exception as e:
                print(f"✗ Error: {e}")
                print("No path that we know of.\n")
                return

        # Find path
        path_info = self.path_finder.find_connection(artist_id, KENDRICK_ID)

        if path_info:
            # Display formatted path
            print(self.path_finder.format_path_output(path_info))
        else:
            print("No path that we know of.\n")

    def run(self):
        """
        Main application loop.
        """
        # Initialize
        if not self.initialize():
            return

        # Main loop
        while True:
            # Get user input
            artist_name = input("Enter artist name (or 'quit' to exit): ").strip()

            # Check for exit
            if artist_name.lower() in ['quit', 'exit', 'q']:
                print("\nThanks for using Six Degrees of Kendrick Lamar!\n")
                break

            # Validate input
            if not artist_name:
                continue

            # Check if searching for Kendrick himself
            if artist_name.lower() in ['kendrick lamar', 'kendrick', 'k dot', 'k.dot', 'kdot']:
                print("⚠ Please search for a different artist\n")
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
