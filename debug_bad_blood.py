"""Debug script to check Taylor Swift Bad Blood issue"""
import sys
sys.path.insert(0, 'src')
from data_fetcher import get_spotify_client

client = get_spotify_client()

# Search for Kendrick Lamar
kendrick = client.search_artist("Kendrick Lamar")
print(f"Kendrick Lamar ID: {kendrick['id']}")
print()

# Get ALL albums including guest appearances
print("="*80)
print("CHECKING GUEST APPEARANCES FOR KENDRICK")
print("="*80)

all_albums = client.get_artist_albums(kendrick['id'], limit=50, own_albums_only=False)

# Filter for guest albums only
guest_albums = [album for album in all_albums if not album.get('is_primary_artist', False)]

print(f"\nFound {len(guest_albums)} guest appearance albums")
print("\nGuest Albums:")
print("-"*80)

for i, album in enumerate(guest_albums, 1):
    print(f"{i}. {album['name']} ({album['release_date']})")

    # Check if it's 1989
    if '1989' in album['name']:
        print(f"   ^^^ FOUND 1989! Album ID: {album['id']}")

        # Get tracks from this album
        print("\n   Checking tracks on this album:")
        tracks = client.get_album_tracks(album['id'])

        for track in tracks:
            artist_names = [a['name'] for a in track['artists']]
            print(f"   - {track['name']}")
            print(f"     Artists: {', '.join(artist_names)}")

            # Check if Kendrick is on this track
            kendrick_on_track = any(a['id'] == kendrick['id'] for a in track['artists'])
            if kendrick_on_track:
                print(f"     ✓ KENDRICK IS ON THIS TRACK!")

            # Check for Bad Blood specifically
            if 'bad blood' in track['name'].lower():
                print(f"     ^^^ THIS IS BAD BLOOD!")
                print(f"     Artists: {artist_names}")
                print(f"     Kendrick on track: {kendrick_on_track}")

print("\n" + "="*80)
print("CHECKING KENDRICK'S COLLABORATORS")
print("="*80)

# Now check what collaborators are found
collaborators = client.get_artist_collaborators(kendrick['id'], max_albums=15)

print(f"\nTotal collaborators found: {len(collaborators)}")

# Check for Taylor Swift
taylor_found = False
for key, info in collaborators.items():
    if 'taylor' in info['name'].lower() and 'swift' in info['name'].lower():
        taylor_found = True
        print(f"\n✓ TAYLOR SWIFT FOUND IN COLLABORATORS!")
        print(f"  Name: {info['name']}")
        print(f"  Collaboration count: {info['count']}")
        print(f"  Songs: {info['tracks']}")
        break

if not taylor_found:
    print("\n✗ TAYLOR SWIFT NOT FOUND IN COLLABORATORS")
    print("\nSearching for any artist with 'swift' in name:")
    for key, info in collaborators.items():
        if 'swift' in info['name'].lower():
            print(f"  - {info['name']}: {info['tracks']}")
