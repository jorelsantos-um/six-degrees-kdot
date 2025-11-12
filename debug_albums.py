"""Debug script to see which albums are being analyzed"""
import sys
sys.path.insert(0, 'src')
from data_fetcher import get_spotify_client

client = get_spotify_client()

# Search for Kendrick Lamar
artist = client.search_artist("Kendrick Lamar")
print(f"Artist: {artist['name']} (ID: {artist['id']})")
print()

# Get albums
albums = client.get_artist_albums(artist['id'], limit=50)

print(f"Total albums found: {len(albums)}")
print("\nAll albums (in order returned by Spotify):")
print("=" * 80)

for i, album in enumerate(albums, 1):
    print(f"{i:2}. [{album['type']:10}] {album['name'][:50]:50} ({album['release_date']}) - {album['total_tracks']} tracks")

print("\n" + "=" * 80)
print("\nAlbum type counts:")
from collections import Counter
type_counts = Counter(album['type'] for album in albums)
for album_type, count in type_counts.items():
    print(f"  {album_type}: {count}")

# Show what the prioritization algorithm would select
print("\n" + "=" * 80)
print("\nTop 15 albums after prioritization (what get_artist_collaborators uses):")
print("=" * 80)

type_priority = {"album": 0, "single": 1, "compilation": 2, "appears_on": 3}
sorted_albums = sorted(
    albums,
    key=lambda x: (type_priority.get(x['type'], 4), -len(x.get('release_date', '')), x.get('release_date', ''))
)

for i, album in enumerate(sorted_albums[:15], 1):
    print(f"{i:2}. [{album['type']:10}] {album['name'][:50]:50} ({album['release_date']}) - {album['total_tracks']} tracks")
