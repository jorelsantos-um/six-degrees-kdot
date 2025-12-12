# Six Degrees of Kendrick Lamar: Music Collaboration Network Analyzer

## Project Overview
An interactive CLI application that finds the shortest path between any artist and Kendrick Lamar, showing their degrees of separation and the specific songs that connect them. Built with Python, NetworkX, and the Spotify API.

Inspired by "Six Degrees of Kevin Bacon," this project explores how artists in hip-hop and music are connected through their collaborations.

## How It Works
1. **Enter any artist name** (e.g., "Drake", "SZA", "Taylor Swift")
2. **Get instant results** showing:
   - Degrees of separation from Kendrick Lamar
   - The connection path (Artist A → Artist B → Kendrick)
   - Specific songs they collaborated on at each step

## Quick Start (TL;DR)

```bash
# 1. Install (~1 minute)
git clone https://github.com/jorelsantos-um/six-degrees-kdot.git
cd six-degrees-kdot
pip install -r requirements.txt

# 2. Get Spotify credentials (~2-3 minutes)
# Visit https://developer.spotify.com/dashboard
# Create app, copy Client ID and Client Secret

# 3. Create .env file
cp .env.example .env
# Edit .env with your credentials

# 4. Build network (⏱️ 10-15 minutes - ONLY FIRST TIME!)
python3 src/network_builder.py

# 5. Run!
python3 main.py
```

**Total setup time:** ~15-20 minutes (mostly waiting for network to build)

## Features

### Shortest Path Finding
- Uses breadth-first search to find the shortest connection between any two artists
- Shows exact collaboration songs at each step in the path
- Handles artists not in the network by dynamically expanding it

### Smart Network Building
- Pre-builds a 2-degree collaboration network from Kendrick Lamar
- Analyzes artists' albums to discover collaborations
- Caches data to minimize API calls and improve performance
- Automatically expands when searching for new artists

### Data Quality
- Includes both primary albums and guest features
- Smart track filtering for guest appearances
- Prioritizes studio albums over singles
- Eliminates duplicate collaborators (case-insensitive)
- Validates and caches all Spotify API responses

## Network Representation
- **Nodes**: Artists with metadata (name, ID, popularity, genres)
- **Edges**: Collaborations between artists
- **Edge Attributes**: List of songs they collaborated on

## Requirements
- Python 3.7+
- Spotify API credentials (free)
- Dependencies: `networkx`, `requests`, `python-dotenv`

## Getting Started

### 1. Clone and Install (⏱️ ~1 minute)
```bash
git clone https://github.com/jorelsantos-um/six-degrees-kdot.git
cd six-degrees-kdot
pip install -r requirements.txt  # Installs networkx, requests, python-dotenv
```

### 2. Get Spotify API Credentials (⏱️ ~2-3 minutes)
1. Go to https://developer.spotify.com/dashboard
2. Log in with your Spotify account (create one if needed)
3. Click **"Create App"**
4. Fill in:
   - App name: "Six Degrees of Kendrick Lamar" (or any name)
   - App description: "SI 507 Final Project"
   - Redirect URI: `http://localhost`
5. Click **"Create"**
6. Copy your **Client ID** and **Client Secret** (click "Show Client Secret")

### 3. Create .env File
```bash
cp .env.example .env
# Edit .env with your actual credentials:
SPOTIFY_CLIENT_ID=your_client_id_here
SPOTIFY_CLIENT_SECRET=your_client_secret_here
```

### 4. Build the Network (⏱️ 10-15 minutes - FIRST TIME ONLY)
```bash
python3 src/network_builder.py
```

⚠️ **IMPORTANT:** This step takes 10-15 minutes! The app makes many API calls to build a 2-degree collaboration network from Kendrick Lamar. This is **normal** and only needs to be done once. The network is saved and reused for all future searches.

### 5. Run the Application (⏱️ Instant if network already built)
```bash
python3 main.py
```

Once the network is built, the app starts instantly and searches are nearly immediate!

## Usage

### Example 1: Direct Collaboration (1 Degree)
```
Enter artist name (or 'quit' to exit): Drake
✓ Found: Drake

⚡ 1 degree of separation

PATH:
Drake → Kendrick Lamar

CONNECTIONS:
1. Drake & Kendrick Lamar
   • Poetic Justice
   • Buried Alive Interlude
   ... and 1 more

Enter artist name (or 'quit' to exit):
```

### Example 2: Two Degrees of Separation
```
Enter artist name (or 'quit' to exit): Travis Scott
✓ Found: Travis Scott

⚡ 2 degrees of separation

PATH:
Travis Scott → SZA → Kendrick Lamar

CONNECTIONS:
1. Travis Scott & SZA
   • Love Galore

2. SZA & Kendrick Lamar
   • All The Stars
   • Doves in the Wind
   ... and 1 more

Enter artist name (or 'quit' to exit):
```

### No Connection Found
```
Enter artist name (or 'quit' to exit): Frank Sinatra
✓ Found: Frank Sinatra
No path that we know of.
```

Type `quit` or `exit` to leave the application.

## Troubleshooting

### "Authentication error" / "Could not connect to Spotify API"
**Problem:** Spotify API credentials are missing or invalid

**Solutions:**
1. Check that `.env` file exists in the project root directory
2. Verify credentials are correct (no extra spaces, quotes, or line breaks)
3. Make sure you copied BOTH `SPOTIFY_CLIENT_ID` and `SPOTIFY_CLIENT_SECRET`
4. Try regenerating credentials in the Spotify Developer Dashboard
5. Ensure your Spotify app is not in restricted/quota exceeded mode

### "No saved network found" message
**Problem:** Network hasn't been built yet

**Solutions:**
- Run `python3 src/network_builder.py` first (takes 10-15 minutes)
- Or type `yes` when the app prompts you to build the network
- Check that `data/collaboration_network.pkl` file exists after building

### Network building takes too long / times out / fails
**Problem:** Slow internet, API rate limiting, or connection issues

**Solutions:**
- Ensure you have a stable internet connection
- Wait a few minutes if you hit rate limits - the app will retry automatically
- If it fails partway through, you can restart - cached data is preserved
- Network building progress is saved in `data/` folder as JSON files

### "Could not find artist" / "Could not find '[artist name]'"
**Problem:** Artist name spelling, artist not on Spotify, or search issue

**Solutions:**
- Check spelling carefully (try the artist's full legal name)
- Try alternate spellings or stage names
- Verify the artist exists on Spotify by searching there first
- Some very obscure artists may not be in Spotify's database

### "No path that we know of"
**Problem:** Artist genuinely not connected to Kendrick within the network

**Solutions:**
- This is **expected behavior** for artists from very different eras or genres
- Example: Frank Sinatra (died 1998) has no connection to Kendrick
- Example: Classical composers or artists from completely different musical universes
- The app will attempt 2-degree network expansion, but some artists truly aren't connected
- This is a feature, not a bug - it correctly identifies when no path exists

### Python version errors / "SyntaxError" / Module not found
**Problem:** Using incompatible Python version or missing dependencies

**Solutions:**
- Ensure Python 3.7 or higher is installed: `python3 --version`
- Use `python3` command instead of `python`
- Reinstall dependencies: `pip install -r requirements.txt`
- On some systems, use `pip3` instead of `pip`

### "Permission denied" or file access errors
**Problem:** Insufficient permissions to create files in `data/` directory

**Solutions:**
- Make sure you have write permissions in the project directory
- Try running from your home directory or a location you own
- Check that `data/` folder exists and is writable

## Project Structure
```
six-degrees-kdot/
├── main.py                          # Main interactive application
├── src/
│   ├── data_fetcher.py             # Spotify API client & caching
│   ├── network_builder.py          # Graph building with NetworkX
│   └── path_finder.py              # Shortest path algorithms
├── data/
│   ├── collaboration_network.pkl   # Saved network graph
│   └── *.json                      # Cached API responses
├── requirements.txt                # Python dependencies
└── README.md                       # This file
```

## Data Sources
- **Spotify Web API**: Artist information, albums, tracks, and collaboration data

## Course Information
SI 507 Final Project - University of Michigan School of Information
