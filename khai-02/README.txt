Smart Path Finder — README
==========================

A Python program that computes routes between locations on a road network map.
Supports shortest distance and shortest travel time routing with time-dependent edges.

---------------------------------------------------------------------
Environment Setup
---------------------------------------------------------------------

Requirements:
  - Python 3.8 or later
  - No external libraries needed (all implementations are built from scratch)

No installation steps required. Clone or extract the project files.

---------------------------------------------------------------------
How to Run
---------------------------------------------------------------------

1. First run (generates the map and saves to CSV):
   python main.py

   This creates data/nodes.csv and data/edges.csv.
   Subsequent runs will load from these files (map stays the same).

2. Force regenerate the map:
   python main.py --regenerate

3. Regenerate edges only (keep existing nodes):
   python main.py --regenerate-edges

4. Interactive commands once running:
   query    - Execute a routing query (shortest distance + shortest time)
   search   - Search nodes by name
   node     - Show details for a specific node
   stats    - Show graph statistics
   quit     - Exit

---------------------------------------------------------------------
Input Format
---------------------------------------------------------------------

Each query requires:
  - Source node: Enter node ID (integer) or type a name to search
  - Destination node: Same as above
  - Departure hour: 0-23, default is 8 (8:00 AM)
  - Avoid nodes: Comma-separated node IDs (optional)
  - Avoid edges: Pairs like 1-2,3-4 meaning edge from node 1 to 2, etc. (optional)

---------------------------------------------------------------------
Output Format
---------------------------------------------------------------------

For each query, the system returns:

1. Shortest Distance Path (optimized Dijkstra):
   - Node sequence with names
   - Total distance (meters and km)
   - Total travel time (minutes)

2. Shortest Travel Time Path (optimized Dijkstra):
   - Node sequence with names
   - Total distance
   - Total travel time

3. Algorithm Comparison Table:
   - Nodes explored, edges relaxed, runtime (ms), heap operations
   - Comparison between Original O(V^2) and Optimized O((V+E)log V) Dijkstra
   - Speedup factor

---------------------------------------------------------------------
Project Structure
---------------------------------------------------------------------

main.py            Entry point and interactive CLI
graph.py           Graph data structure (Node, Edge, adjacency list)
heap.py            Custom binary min-heap implementation
dijkstra.py        Original and Optimized Dijkstra algorithms
map_generator.py   Road network map generator (nodes + edges)
csv_io.py          CSV import/export
query.py           Query processing and result formatting
data/nodes.csv     Persisted node data
data/edges.csv     Persisted edge data

---------------------------------------------------------------------
Demo Video
---------------------------------------------------------------------

Link: [To be added]
