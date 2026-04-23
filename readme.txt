==============================
SMART PATH FINDER - README
==============================

1. ENVIRONMENT SETUP
------------------------------
- Programming language: Python 3.11
- No external libraries are required

Make sure Python is installed on your system.

All project files should be placed in the same directory:
- main.py
- graph.py
- DijkstraAlgorithm.py
- csv_loader.py
- queries.json
- Data
  |_ vertices.csv
  |_ edges.csv


2. HOW TO RUN THE PROGRAM
------------------------------
Step 1: Open terminal / command prompt

Step 2: Navigate to the project folder

Step 3: Run the program:

    python main.py

Step 4: The results will be displayed in the console


3. INPUT FORMAT
------------------------------

The system uses three input files:

1. vertices.csv
Format:
    node_name, x_coordinate, y_coordinate

Example:
    A,0,0
    B,1,0


2. edges.csv
Format:
    start_vertex, end_vertex, distance, bidirectional, road_type

Example:
    A,B,40,True,city
    A,E,60,True,highway

Description:
- start_vertex: starting node
- end_vertex: destination node
- distance: distance between nodes
- bidirectional: True or False
- road_type: city / highway / normal


3. queries.json
Format:
    [
        {
            "source": "A",
            "destination": "J",
            "start_time": 6
        },
        {
            "source": "A",
            "destination": "J",
            "start_time": 6,
            "avoid_nodes": ["C"]
        },
        {
            "source": "A",
            "destination": "J",
            "start_time": 6,
            "avoid_edges": [["E","F"], ["F","G"]]
        },
        {
            "source": "A",
            "destination": "J",
            "start_time": 8,
            "avoid_nodes": ["C"],
            "avoid_edges": [["E","F"]]
        }
    ]

Description:
- source: starting node
- destination: target node
- start_time: hour (0–23)
- avoid_nodes: list of nodes to avoid (optional)
- avoid_edges: list of edges to avoid (optional)


4. OUTPUT FORMAT
------------------------------
For each query, the program outputs:

1. Shortest path (by distance)
- Path (sequence of nodes)
- Total distance
- Travel time for this path
- Arrival time

2. Shortest time path (by travel time)
- Path (sequence of nodes)
- Total travel time
- Arrival time


Example Output:

===== SHORTEST PATH =====
result: A B C D J
Shortest path: 160

Travel time on this path: 320 minutes
Time travel: 5 hour(s) 20 minute(s)
Arrival time: 13:20


===== SHORTEST TIME PATH =====
result: A E F G H I J
Total time: 288 minutes
Time travel: 4 hour(s) 48 minute(s)
Arrival: 12:48


5. DEMO VIDEO
------------------------------
Link:
(Paste your demo video link here)


==============================
END OF README
==============================