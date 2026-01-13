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
                display_path(connection)
            else:
                st.error("No connection found.")
                st.markdown(f"*{artist['name']} doesn't have a path to Kendrick Lamar in the current network.*")


if __name__ == "__main__":
    main()
