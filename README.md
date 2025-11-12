# Six Degrees of Kendrick Lamar: Music Collaboration Network Analyzer

## Project Overview
This project analyzes the collaboration network in hip-hop and music, centered around Kendrick Lamar. Using graph theory and network analysis, it explores how artists are connected through their musical collaborations, revealing the intricate web of relationships in the music industry.

## Network Representation
- **Nodes**: Artists and musicians
- **Edges**: Collaborations between artists (features, co-productions, co-writing credits)
- **Edge Weights**: Can represent collaboration frequency or song popularity

## Data Sources
- **Spotify API**: Artist information, discographies, and featured collaborations
- **MusicBrainz API**: Detailed relationship data, recording credits, and artist metadata

## Four Interaction Modes

### 1. Shortest Path Finder
Find the shortest connection chain between any two artists in the network. Implements a "Six Degrees of Kevin Bacon" style search to discover how artists are connected through collaborations.

### 2. Network Visualization
Generate interactive graph visualizations of the collaboration network. View the network structure, identify clusters of frequently collaborating artists, and explore the overall topology.

### 3. Artist Analysis
Analyze individual artists within the network:
- Degree centrality (number of collaborations)
- Most frequent collaborators
- Artist influence and reach within the network
- Collaboration patterns over time

### 4. Network Expansion
Dynamically expand the network by adding new artists and their collaborators. Start with Kendrick Lamar and explore outward to discover extended networks and unexpected connections.

## Requirements
- Python 3.7+
- See `requirements.txt` for package dependencies

## Project Structure
```
six-degrees-kdot/
├── src/          # Source code modules
├── data/         # Cached API responses and datasets
├── tests/        # Unit tests
└── README.md     # Project documentation
```

## Getting Started
1. Clone this repository
2. Install dependencies: `pip install -r requirements.txt`
3. Set up API credentials in a `.env` file
4. Run the main application (coming soon!)

## Course Information
SI 507 Final Project - University of Michigan School of Information
