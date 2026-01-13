"""
Six Degrees of Kendrick Lamar - Streamlit Web App

Find the shortest collaboration path between any artist and Kendrick Lamar.
"""

import streamlit as st
from pathlib import Path
import sys

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent / "src"))

from database import CollaborationDatabase
from path_finder_sqlite import PathFinder, KENDRICK_ID
from data_fetcher import SpotifyAPIClient, AuthenticationError


# Page configuration
st.set_page_config(
    page_title="Six Degrees of Kendrick Lamar",
    page_icon="🎤",
    layout="centered"
)


@st.cache_resource
def load_database():
    """Load the database (cached to avoid reloading on every interaction)."""
    db_path = Path(__file__).parent / "data" / "collaboration_network.db"
    if not db_path.exists():
        return None
    return CollaborationDatabase(str(db_path))


@st.cache_resource
def load_path_finder(_db):
    """Load the path finder (cached)."""
    return PathFinder(_db)


@st.cache_resource
def load_spotify_client():
    """Load Spotify API client (cached). Returns None if credentials not available."""
    try:
        return SpotifyAPIClient()
    except AuthenticationError:
        return None


def search_track_preview(song_name: str, artist_names: list, spotify_client) -> str:
    """
    Search for a track on Spotify and return its preview URL.

    Args:
        song_name: Name of the song
        artist_names: List of artist names involved
        spotify_client: SpotifyAPIClient instance

    Returns:
        Preview URL string or None if not found
    """
    if not spotify_client:
        return None

    try:
        # Build search query with song and artists
        query = f"{song_name} {' '.join(artist_names)}"

        params = {
            "q": query,
            "type": "track",
            "limit": 1
        }

        response = spotify_client._make_request("/search", params)
        tracks = response.get("tracks", {}).get("items", [])

        if tracks:
            track = tracks[0]
            return track.get("preview_url")

    except Exception as e:
        # Silently fail if preview not available
        return None

    return None


def get_artist_image_url(artist_name: str) -> str:
    """Generate a placeholder image URL for an artist using UI Avatars."""
    # Use initials for the avatar
    import urllib.parse
    name_parts = artist_name.split()
    initials = ''.join([part[0].upper() for part in name_parts[:2]])
    # UI Avatars with custom colors (Kendrick red theme)
    bg_color = "DC143C"  # Crimson red
    text_color = "FFFFFF"  # White
    return f"https://ui-avatars.com/api/?name={urllib.parse.quote(artist_name)}&size=200&background={bg_color}&color={text_color}&bold=true&font-size=0.4"


def display_artist_card(artist_name: str, artist_id: str):
    """Display an artist card with image and name."""
    image_url = get_artist_image_url(artist_name)

    st.markdown(f"""
        <div style="text-align: center; padding: 1rem;">
            <img src="{image_url}"
                 style="border-radius: 12px; width: 120px; height: 120px; object-fit: cover; box-shadow: 0 4px 6px rgba(0,0,0,0.3);"
                 alt="{artist_name}">
            <div style="margin-top: 0.75rem; font-weight: 600; font-size: 1.1rem;">
                {artist_name}
            </div>
        </div>
    """, unsafe_allow_html=True)


def display_path(connection: dict, spotify_client=None):
    """Display the connection path with artist cards and songs."""
    degrees = connection['degrees']

    # Degrees header
    if degrees == 0:
        st.success("🎤 That's Kendrick Lamar himself!")
    elif degrees == 1:
        st.success(f"🔥 **{degrees} degree** of separation!")
    else:
        st.success(f"🔥 **{degrees} degrees** of separation!")

    st.markdown("")
    st.markdown("---")
    st.markdown("")

    # Path visualization with cards
    path_artists = connection['path']
    connections = connection['connections']

    for i, artist in enumerate(path_artists):
        # Display artist card
        display_artist_card(artist['name'], artist['id'])

        # If not the last artist, show the connecting songs
        if i < len(path_artists) - 1:
            # Find the connection between this artist and the next
            conn = connections[i]
            songs = conn['songs']
            from_artist = conn['from']['name']
            to_artist = conn['to']['name']

            # Arrow and songs container
            st.markdown(f"""
                <div style="text-align: center; margin: 1.5rem 0;">
                    <div style="font-size: 2rem; color: #DC143C; margin-bottom: 0.5rem;">↓</div>
                    <div style="background: #1A1A1A; padding: 1rem; border-radius: 8px; border-left: 3px solid #DC143C;">
                        <div style="font-weight: 600; margin-bottom: 0.5rem; color: #DC143C;">
                            🎵 Connecting Song{"s" if len(songs) > 1 else ""}
                        </div>
            """, unsafe_allow_html=True)

            # Display songs with preview players
            songs_to_show = songs[:3]  # Show first 3 songs

            for song in songs_to_show:
                # Try to get preview URL if Spotify client is available
                preview_url = None
                if spotify_client:
                    preview_url = search_track_preview(song, [from_artist, to_artist], spotify_client)

                # Display song name
                st.markdown(f"**•** {song}")

                # Add preview player if available
                if preview_url:
                    st.markdown(f"""
                        <audio controls style="width: 100%; margin: 0.5rem 0 1rem 0;">
                            <source src="{preview_url}" type="audio/mpeg">
                            Your browser does not support the audio element.
                        </audio>
                    """, unsafe_allow_html=True)

            if len(songs) > 3:
                st.markdown(f"*...and {len(songs) - 3} more*")

            st.markdown("</div></div>", unsafe_allow_html=True)


def main():
    # Custom CSS for Kendrick aesthetic
    st.markdown("""
        <style>
        /* Main title styling */
        h1 {
            font-weight: 900;
            letter-spacing: -0.02em;
            margin-bottom: 0.5rem;
        }

        /* Clean input styling */
        .stTextInput input {
            border-radius: 8px;
            font-size: 1.1rem;
            padding: 0.75rem;
        }

        /* Button styling */
        .stButton button {
            border-radius: 8px;
            font-weight: 600;
            padding: 0.6rem 2rem;
            transition: all 0.2s;
        }

        /* Kendrick aesthetic accents */
        .stMarkdown {
            line-height: 1.6;
        }

        /* Clean card styling */
        .element-container {
            margin-bottom: 1rem;
        }
        </style>
    """, unsafe_allow_html=True)

    # Title
    st.title("Six Degrees of Kendrick Lamar")
    st.markdown("*Find the collaboration path between any artist and Kendrick Lamar*")
    st.markdown("")

    # Load database
    db = load_database()

    if db is None:
        st.error("Database not found. Please run the network builder first.")
        st.code("python3 src/build_network_sqlite.py", language="bash")
        return

    # Load Spotify client for preview players (optional)
    spotify_client = load_spotify_client()

    # Search input with autocomplete
    artist_name = st.text_input(
        "Enter an artist name:",
        placeholder="Start typing an artist name...",
        key="artist_search"
    )

    # Show autocomplete suggestions as user types
    selected_artist = None
    if artist_name and len(artist_name) >= 2:
        suggestions = db.search_artists(artist_name, limit=8)

        if suggestions:
            st.markdown("**Suggestions:**")
            cols = st.columns(2)
            for idx, suggestion in enumerate(suggestions):
                col = cols[idx % 2]
                with col:
                    if st.button(
                        f"🎤 {suggestion['name']}",
                        key=f"suggestion_{suggestion['id']}",
                        use_container_width=True
                    ):
                        selected_artist = suggestion

    st.markdown("")

    # Search button
    search_clicked = st.button("Find Connection", type="primary", use_container_width=True)

    if search_clicked or selected_artist:
        # Determine which artist to search for
        if selected_artist:
            artist = selected_artist
        elif artist_name:
            with st.spinner(f"Searching for {artist_name}..."):
                # Try exact match first
                artist = db.get_artist_by_name(artist_name)

                if not artist:
                    st.error(f"Artist '{artist_name}' not found.")
                    st.info("Please select an artist from the suggestions above, or try a different search.")
                    return
        else:
            st.warning("Please enter an artist name.")
            return

        with st.spinner(f"Finding connection to Kendrick..."):
            # Check if it's Kendrick himself
            if artist['id'] == KENDRICK_ID:
                st.balloons()
                st.success("🎤 That's Kendrick Lamar himself! 0 degrees of separation!")
                return

            # Find path
            path_finder = load_path_finder(db)
            connection = path_finder.find_connection(artist['id'], KENDRICK_ID)

            if connection:
                display_path(connection, spotify_client)
            else:
                st.error("No connection found.")
                st.markdown(f"*{artist['name']} doesn't have a path to Kendrick Lamar in the current network.*")


if __name__ == "__main__":
    main()
