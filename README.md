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
- Filters to only primary artist albums (not guest appearances)
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

### 1. Clone and Install
```bash
git clone https://github.com/jorelsantos-um/six-degrees-kdot.git
cd six-degrees-kdot
pip install -r requirements.txt
```

### 2. Get Spotify API Credentials
1. Go to https://developer.spotify.com/dashboard
2. Log in and click "Create App"
3. Copy your Client ID and Client Secret

### 3. Create .env File
```bash
cp .env.example .env
# Edit .env with your credentials:
SPOTIFY_CLIENT_ID=your_client_id_here
SPOTIFY_CLIENT_SECRET=your_client_secret_here
```

### 4. Build the Network (First Time Only)
```bash
python3 src/network_builder.py
```
This builds a 2-degree collaboration network from Kendrick Lamar.
**Note**: Takes 10-15 minutes due to API calls. Only needs to be done once!

### 5. Run the Application
```bash
python3 main.py
```

## Usage

Once the app is running:
```
Enter artist name: Drake

Searching for 'Drake'...
✓ Found: Drake

Finding connection to Kendrick Lamar...

================================================================================
CONNECTION FOUND: 1 degree(s) of separation
================================================================================

PATH:
Drake → Kendrick Lamar

CONNECTIONS:
--------------------------------------------------------------------------------

1. Drake → Kendrick Lamar
   Collaborated on:
      • Poetic Justice

================================================================================
```

Type `quit` or `exit` to leave the application.

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
