"""
Path Finder Module

This module finds the shortest path between two artists in the collaboration network
and extracts detailed connection information including songs.
"""

import networkx as nx
from typing import Dict, List, Optional, Tuple
from network_builder import CollaborationNetwork


class PathFinder:
    """
    Finds paths between artists in the collaboration network.

    Uses NetworkX's shortest path algorithms to find connections
    between artists and extracts collaboration details.
    """

    def __init__(self, network: CollaborationNetwork):
        """
        Initialize the path finder with a collaboration network.

        Args:
            network: CollaborationNetwork instance with built graph
        """
        self.network = network

    def find_shortest_path(self, from_artist_id: str, to_artist_id: str) -> Optional[List[str]]:
        """
        Find the shortest path between two artists.

        Uses breadth-first search (BFS) to find the shortest path.

        Args:
            from_artist_id: Starting artist's Spotify ID
            to_artist_id: Target artist's Spotify ID

        Returns:
            List of artist IDs representing the path, or None if no path exists
        """
        # Check if both artists are in the network
        if not self.network.artist_in_network(from_artist_id):
            return None
        if not self.network.artist_in_network(to_artist_id):
            return None

        try:
            # Use NetworkX's shortest_path function (uses BFS for unweighted graphs)
            path = nx.shortest_path(self.network.graph, from_artist_id, to_artist_id)
            return path
        except nx.NetworkXNoPath:
            # No path exists between the artists
            return None

    def get_path_details(self, path: List[str]) -> Dict:
        """
        Get detailed information about a path including songs at each connection.

        Args:
            path: List of artist IDs representing the path

        Returns:
            Dictionary with path details:
            {
                "degrees": int,
                "path": [{"id": str, "name": str}, ...],
                "connections": [
                    {
                        "from": {"id": str, "name": str},
                        "to": {"id": str, "name": str},
                        "songs": [str, ...]
                    },
                    ...
                ]
            }
        """
        if not path or len(path) < 2:
            return {
                "degrees": 0,
                "path": [],
                "connections": []
            }

        # Calculate degrees (number of edges/connections)
        degrees = len(path) - 1

        # Build path with artist names
        path_details = []
        for artist_id in path:
            artist_info = self.network.get_artist_info(artist_id)
            path_details.append({
                "id": artist_id,
                "name": artist_info.get("name", "Unknown Artist") if artist_info else "Unknown Artist"
            })

        # Build connections with songs
        connections = []
        for i in range(len(path) - 1):
            from_id = path[i]
            to_id = path[i + 1]

            from_info = self.network.get_artist_info(from_id)
            to_info = self.network.get_artist_info(to_id)

            songs = self.network.get_collaboration_songs(from_id, to_id)

            connections.append({
                "from": {
                    "id": from_id,
                    "name": from_info.get("name", "Unknown") if from_info else "Unknown"
                },
                "to": {
                    "id": to_id,
                    "name": to_info.get("name", "Unknown") if to_info else "Unknown"
                },
                "songs": songs
            })

        return {
            "degrees": degrees,
            "path": path_details,
            "connections": connections
        }

    def find_connection(self, from_artist_id: str, to_artist_id: str) -> Optional[Dict]:
        """
        Find the connection between two artists with full details.

        This is the main function that combines path finding and detail extraction.

        Args:
            from_artist_id: Starting artist's Spotify ID
            to_artist_id: Target artist's Spotify ID

        Returns:
            Dictionary with connection details, or None if no path exists
        """
        # Find shortest path
        path = self.find_shortest_path(from_artist_id, to_artist_id)

        if path is None:
            return None

        # Get detailed information
        return self.get_path_details(path)

    def format_path_output(self, path_info: Dict) -> str:
        """
        Format path information into a readable string.

        Args:
            path_info: Dictionary from get_path_details()

        Returns:
            Formatted string representation of the path
        """
        if not path_info or path_info["degrees"] == 0:
            return "No path found."

        output = []

        # Header - clean and simple
        degree_text = "degree" if path_info['degrees'] == 1 else "degrees"
        output.append(f"\n⚡ {path_info['degrees']} {degree_text} of separation\n")

        # Path visualization
        path_names = [artist["name"] for artist in path_info["path"]]
        output.append("PATH:")
        output.append(" → ".join(path_names))
        output.append("")

        # Detailed connections
        output.append("CONNECTIONS:")
        for i, conn in enumerate(path_info["connections"], 1):
            output.append(f"{i}. {conn['from']['name']} & {conn['to']['name']}")

            if conn["songs"]:
                # Show up to 3 songs, each on its own line
                songs_to_show = conn["songs"][:3]
                for song in songs_to_show:
                    output.append(f"   • {song}")

                remaining = len(conn["songs"]) - 3
                if remaining > 0:
                    output.append(f"   ... and {remaining} more")
            else:
                output.append("   • (Collaboration details unavailable)")

            output.append("")

        return "\n".join(output)


def find_path_to_kendrick(artist_id: str, network: CollaborationNetwork,
                          kendrick_id: str = "2YZyLoL8N0Wb9xBt1NhZWg") -> Optional[Dict]:
    """
    Convenience function to find path from any artist to Kendrick Lamar.

    Args:
        artist_id: Starting artist's Spotify ID
        network: CollaborationNetwork instance
        kendrick_id: Kendrick Lamar's Spotify ID (default provided)

    Returns:
        Path details dictionary or None if no path exists
    """
    finder = PathFinder(network)
    return finder.find_connection(artist_id, kendrick_id)


if __name__ == "__main__":
    """
    Example usage: Test path finding with a loaded network
    """
    print("Testing Path Finder with saved network...\n")

    # Load the saved network
    network = CollaborationNetwork()

    if not network.load_network("data/collaboration_network.pkl"):
        print("Error: Could not load network. Please run network_builder.py first.")
        exit(1)

    print("\nNetwork loaded successfully!")
    stats = network.get_network_stats()
    print(f"Network contains {stats['total_artists']} artists and {stats['total_collaborations']} collaborations\n")

    # Create path finder
    finder = PathFinder(network)

    # Test with some artists
    from data_fetcher import get_spotify_client

    client = get_spotify_client()

    # Get Kendrick's ID
    kendrick = client.search_artist("Kendrick Lamar")
    kendrick_id = kendrick["id"]

    # Test artists to search for
    test_artists = ["SZA", "Travis Scott", "Jay Rock"]

    for artist_name in test_artists:
        print(f"\n{'='*80}")
        print(f"Searching for connection: {artist_name} → Kendrick Lamar")
        print('='*80)

        # Search for the artist
        artist_info = client.search_artist(artist_name)

        if not artist_info:
            print(f"Could not find artist: {artist_name}")
            continue

        artist_id = artist_info["id"]

        # Check if artist is in network
        if not network.artist_in_network(artist_id):
            print(f"{artist_name} is not in the current network.")
            continue

        # Find path
        path_info = finder.find_connection(artist_id, kendrick_id)

        if path_info:
            print(finder.format_path_output(path_info))
        else:
            print("No path found.")

    print("\n" + "="*80)
    print("Path finder test complete!")
    print("="*80)
