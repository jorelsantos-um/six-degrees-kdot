"""
Network Builder Module

This module builds and manages the artist collaboration network graph.
Uses NetworkX to create a graph where artists are nodes and collaborations
are edges, with song names stored as edge attributes.
"""

import pickle
import networkx as nx
from pathlib import Path
from typing import Dict, List, Optional, Set
from data_fetcher import SpotifyAPIClient


class CollaborationNetwork:
    """
    Manages the artist collaboration network graph.

    The graph structure:
    - Nodes: Artist IDs with attributes (name, popularity, etc.)
    - Edges: Connections between collaborating artists
    - Edge attributes: List of song names they collaborated on
    """

    def __init__(self, spotify_client: Optional[SpotifyAPIClient] = None):
        """
        Initialize the collaboration network.

        Args:
            spotify_client: Optional SpotifyAPIClient instance. If None, creates one.
        """
        self.graph = nx.Graph()
        self.client = spotify_client if spotify_client else SpotifyAPIClient()

    def add_artist_node(self, artist_id: str, artist_name: str, **attributes) -> None:
        """
        Add an artist as a node in the network.

        Args:
            artist_id: Spotify artist ID
            artist_name: Artist's name
            **attributes: Additional artist attributes (popularity, genres, etc.)
        """
        if artist_id not in self.graph:
            self.graph.add_node(
                artist_id,
                name=artist_name,
                **attributes
            )

    def add_collaboration_edge(self, artist1_id: str, artist2_id: str,
                              song_name: str) -> None:
        """
        Add or update a collaboration edge between two artists.

        Args:
            artist1_id: First artist's Spotify ID
            artist2_id: Second artist's Spotify ID
            song_name: Name of the song they collaborated on
        """
        # Check if edge already exists
        if self.graph.has_edge(artist1_id, artist2_id):
            # Add song to existing collaboration
            songs = self.graph[artist1_id][artist2_id].get('songs', [])
            if song_name not in songs:
                songs.append(song_name)
                self.graph[artist1_id][artist2_id]['songs'] = songs
        else:
            # Create new edge with song list
            self.graph.add_edge(
                artist1_id,
                artist2_id,
                songs=[song_name]
            )

    def add_artist_and_collaborators(self, artist_id: str,
                                     max_albums: int = 15) -> int:
        """
        Add an artist and all their collaborators to the network.

        Args:
            artist_id: Spotify artist ID to add
            max_albums: Maximum number of albums to analyze for collaborations

        Returns:
            Number of new collaborators added

        Raises:
            Exception: If artist data cannot be fetched
        """
        print(f"\nAdding artist {artist_id} to network...")

        # Get artist info
        artist_info = self.client._make_request(f"/artists/{artist_id}")
        artist_name = artist_info['name']

        # Add main artist node
        self.add_artist_node(
            artist_id,
            artist_name,
            popularity=artist_info.get('popularity', 0),
            genres=artist_info.get('genres', [])
        )

        # Get collaborators
        collaborators = self.client.get_artist_collaborators(artist_id, max_albums)

        new_collaborators = 0

        # Add each collaborator
        for collab_key, collab_info in collaborators.items():
            collab_id = collab_info.get('id')
            collab_name = collab_info['name']

            # Skip collaborators without IDs (parsed from track names)
            if not collab_id:
                continue

            # Add collaborator node if not already in graph
            if collab_id not in self.graph:
                self.add_artist_node(collab_id, collab_name)
                new_collaborators += 1

            # Add edges for each song collaboration
            for song in collab_info['tracks']:
                self.add_collaboration_edge(artist_id, collab_id, song)

        print(f"Added {len(collaborators)} collaborators ({new_collaborators} new)")
        return new_collaborators

    def build_network(self, starting_artist_id: str, depth: int = 2,
                     max_albums: int = 15) -> None:
        """
        Build the collaboration network starting from an artist.

        This performs a breadth-first expansion:
        - Depth 1: Starting artist's collaborators
        - Depth 2: Their collaborators' collaborators
        - And so on...

        Args:
            starting_artist_id: Artist ID to start from (e.g., Kendrick Lamar)
            depth: How many degrees of separation to build (default: 2)
            max_albums: Maximum albums to analyze per artist
        """
        print(f"\n{'='*80}")
        print(f"Building {depth}-degree network from starting artist...")
        print(f"{'='*80}")

        # Track artists we've already processed
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
                    # Add artist and their collaborators
                    self.add_artist_and_collaborators(artist_id, max_albums)

                    # Get their collaborators for next level
                    collaborators = self.graph.neighbors(artist_id)
                    next_level.update(collaborators)

                    processed.add(artist_id)

                except Exception as e:
                    print(f"Error processing artist {artist_id}: {e}")
                    processed.add(artist_id)  # Mark as processed to avoid retry
                    continue

            # Move to next level
            current_level = next_level - processed

        print(f"\n{'='*80}")
        print(f"Network built successfully!")
        print(f"Total artists: {self.graph.number_of_nodes()}")
        print(f"Total collaborations: {self.graph.number_of_edges()}")
        print(f"{'='*80}\n")

    def get_artist_info(self, artist_id: str) -> Optional[Dict]:
        """
        Get artist information from the network.

        Args:
            artist_id: Spotify artist ID

        Returns:
            Dictionary of artist attributes or None if not in network
        """
        if artist_id in self.graph:
            return self.graph.nodes[artist_id]
        return None

    def get_collaboration_songs(self, artist1_id: str, artist2_id: str) -> List[str]:
        """
        Get list of songs two artists collaborated on.

        Args:
            artist1_id: First artist's Spotify ID
            artist2_id: Second artist's Spotify ID

        Returns:
            List of song names, or empty list if no collaboration
        """
        if self.graph.has_edge(artist1_id, artist2_id):
            return self.graph[artist1_id][artist2_id].get('songs', [])
        return []

    def artist_in_network(self, artist_id: str) -> bool:
        """
        Check if an artist is in the network.

        Args:
            artist_id: Spotify artist ID

        Returns:
            True if artist is in network, False otherwise
        """
        return artist_id in self.graph

    def get_network_stats(self) -> Dict:
        """
        Get statistics about the network.

        Returns:
            Dictionary with network statistics
        """
        return {
            'total_artists': self.graph.number_of_nodes(),
            'total_collaborations': self.graph.number_of_edges(),
            'average_collaborators': sum(dict(self.graph.degree()).values()) / self.graph.number_of_nodes() if self.graph.number_of_nodes() > 0 else 0
        }

    def save_network(self, filepath: str = "data/collaboration_network.pkl") -> None:
        """
        Save the network to a file.

        Args:
            filepath: Path to save the network (default: data/collaboration_network.pkl)
        """
        filepath_obj = Path(filepath)
        filepath_obj.parent.mkdir(exist_ok=True)

        with open(filepath, 'wb') as f:
            pickle.dump(self.graph, f)

        print(f"Network saved to {filepath}")
        print(f"  - {self.graph.number_of_nodes()} artists")
        print(f"  - {self.graph.number_of_edges()} collaborations")

    def load_network(self, filepath: str = "data/collaboration_network.pkl") -> bool:
        """
        Load the network from a file.

        Args:
            filepath: Path to load the network from

        Returns:
            True if loaded successfully, False otherwise
        """
        filepath_obj = Path(filepath)

        if not filepath_obj.exists():
            print(f"Network file not found: {filepath}")
            return False

        try:
            with open(filepath, 'rb') as f:
                self.graph = pickle.load(f)

            print(f"Network loaded from {filepath}")
            print(f"  - {self.graph.number_of_nodes()} artists")
            print(f"  - {self.graph.number_of_edges()} collaborations")
            return True

        except Exception as e:
            print(f"Error loading network: {e}")
            return False


# Convenience function
def build_kendrick_network(depth: int = 2, max_albums: int = 15,
                          save_path: str = "data/collaboration_network.pkl") -> CollaborationNetwork:
    """
    Build and save a collaboration network centered on Kendrick Lamar.

    Args:
        depth: Degrees of separation to build (default: 2)
        max_albums: Maximum albums per artist to analyze
        save_path: Where to save the network

    Returns:
        CollaborationNetwork instance with built network
    """
    from data_fetcher import get_spotify_client

    # Get Kendrick Lamar's ID
    client = get_spotify_client()
    kendrick = client.search_artist("Kendrick Lamar")

    if not kendrick:
        raise ValueError("Could not find Kendrick Lamar on Spotify")

    kendrick_id = kendrick['id']

    # Build network
    network = CollaborationNetwork(client)
    network.build_network(kendrick_id, depth=depth, max_albums=max_albums)

    # Save network
    network.save_network(save_path)

    return network


if __name__ == "__main__":
    """
    Example usage: Build a 2-degree network from Kendrick Lamar
    """
    print("Building Kendrick Lamar collaboration network...")
    print("This may take several minutes...\n")

    try:
        network = build_kendrick_network(depth=2, max_albums=15)

        # Show some stats
        stats = network.get_network_stats()
        print("\nNetwork Statistics:")
        print(f"  Total Artists: {stats['total_artists']}")
        print(f"  Total Collaborations: {stats['total_collaborations']}")
        print(f"  Average Collaborators per Artist: {stats['average_collaborators']:.2f}")

    except Exception as e:
        print(f"Error building network: {e}")
