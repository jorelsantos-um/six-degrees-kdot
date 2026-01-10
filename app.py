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


def display_path(connection: dict):
    """Display the connection path with styling."""
    degrees = connection['degrees']

    # Degrees header
    if degrees == 0:
        st.success("🎤 That's Kendrick Lamar himself!")
    elif degrees == 1:
        st.success(f"🔥 **{degrees} degree** of separation!")
    else:
        st.success(f"🔥 **{degrees} degrees** of separation!")

    st.markdown("---")

    # Path visualization
    st.subheader("The Path")

    path_artists = [artist['name'] for artist in connection['path']]
    path_display = " → ".join(path_artists)
    st.markdown(f"**{path_display}**")

    st.markdown("---")

    # Collaboration details
    st.subheader("Collaborations")

    for conn in connection['connections']:
        from_artist = conn['from']['name']
        to_artist = conn['to']['name']
        songs = conn['songs']

        with st.expander(f"🎵 {from_artist} ↔ {to_artist} ({len(songs)} song{'s' if len(songs) != 1 else ''})"):
            for song in songs[:10]:  # Limit to 10 songs
                st.markdown(f"• {song}")
            if len(songs) > 10:
                st.markdown(f"*...and {len(songs) - 10} more*")


def main():
    # Title
    st.title("Six Degrees of Kendrick Lamar")
    st.markdown("*Find the collaboration path between any artist and Kendrick Lamar*")

    # Load database
    db = load_database()

    if db is None:
        st.error("Database not found. Please run the network builder first.")
        st.code("python3 src/build_network_sqlite.py", language="bash")
        return

    # Display network stats
    stats = db.get_stats()
    st.markdown(f"🎧 **Searching {stats['total_artists']:,} artists** in the network")

    st.markdown("---")

    # Search input
    artist_name = st.text_input(
        "Enter an artist name:",
        placeholder="e.g., Drake, SZA, Taylor Swift..."
    )

    # Search button
    if st.button("Find Connection", type="primary") or artist_name:
        if not artist_name:
            st.warning("Please enter an artist name.")
            return

        with st.spinner(f"Searching for {artist_name}..."):
            # Try exact match first
            artist = db.get_artist_by_name(artist_name)

            if not artist:
                # Try partial search
                similar_artists = db.search_artists(artist_name, limit=5)

                if similar_artists:
                    st.warning(f"Artist '{artist_name}' not found exactly. Did you mean:")

                    # Show suggestions as buttons
                    for similar in similar_artists:
                        if st.button(f"🎤 {similar['name']}", key=similar['id']):
                            artist = similar
                            break

                    if not artist:
                        st.info("Click on an artist above to find their connection.")
                        return
                else:
                    st.error(f"Artist '{artist_name}' not found in network.")
                    st.markdown("*This artist may not have collaborated with anyone in Kendrick's network.*")
                    return

            # Check if it's Kendrick himself
            if artist['id'] == KENDRICK_ID:
                st.balloons()
                st.success("🎤 That's Kendrick Lamar himself! 0 degrees of separation!")
                return

            # Find path
            path_finder = load_path_finder(db)
            connection = path_finder.find_connection(artist['id'], KENDRICK_ID)

            if connection:
                display_path(connection)
            else:
                st.error("No connection found.")
                st.markdown(f"*{artist['name']} doesn't have a path to Kendrick Lamar in the current network.*")


if __name__ == "__main__":
    main()
