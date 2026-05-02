SMART PATH FINDER

GROUP NUMBER: 12

   STUDENT NAME         STUDENT-ID  
 Nguyen Nhat Khoi        s4126564
   La Tran Hung          s4123461
  Ngo Quang Khai         s3975831
  Nguyen The Anh         s3975844

PROJECT OVERVIEW
========================================

This project simulates a real-world road network and implements
shortest path algorithms with dynamic traffic conditions.

Main features:
    (+) Synthetic map generation (nodes + edges)
    (+) Time dependent travel costs (24-hour congestion model)
    (+) Dijkstra algorithm (original & optimized)
    (+) Avoid nodes and edges functionality
    (+) Interactive command-line interface

ENVIRONMENT SETUP
========================================
Requirements:
Python 3.8 or higher

Required libraries:

No external libraries.

Steps:

Install and run python

Install Python from: https://www.python.org/downloads/
Verify installation:
python --version

Place all files in the same directory:
 _new_map.py
|_solution.py
|_queries.json
|_data
  |_edges.csv
  |_nodes.csv

RUN THE PROGRAM
========================================
***Step 1: Generate map data

Run:
    (+) Windows: python new_map.py
    (+) MacOS: python3 new_map.py

Description:

This will generate a synthetic road network
Output files will be created:
data/nodes.csv
data/edges.csv

Warning: waiting 1 to 2 minutes to finish the generate a new map

(Reference: see new_map.py)

***Step 2: Run the routing system

Run:
    (+) Windows: python solution.py
    (+) MacOS: python3 solution.py
Description:

Loads generated map data
Starts an interactive CLI menu
Allows querying shortest paths

DESCRIPT OF INPUT FORMAT
========================================
The program uses a JSON file named:
queries.json

{
  "queries": [
    {
      "id": "case_1",
      "name": "Source & Destination Only",
      "source": 0,
      "destination": 4999,
      "departure_hour": 8,
      "avoid_nodes": [],
      "avoid_edges": []
    },
    {
      "id": "case_2",
      "name": "Source, Dest, and Avoid Nodes",
      "source": 0,
      "destination": 4999,
      "departure_hour": 8,
      "avoid_nodes": [90, 88],
      "avoid_edges": []
    },
    {
      "id": "case_3",
      "name": "Source, Dest, and Avoid Edges",
      "source": 0,
      "destination": 4999,
      "departure_hour": 8,
      "avoid_nodes": [],
      "avoid_edges": [
        [5, 3],
        [3509, 4449]
      ]
    },
    {
      "id": "case_4",
      "name": "Source, Dest, Avoid Nodes, and Avoid Edges",
      "source": 0,
      "destination": 4999,
      "departure_hour": 8,
      "avoid_nodes": [5, 1067],
      "avoid_edges": [
        [4449, 4561]
      ]
    }
  ]
}

Explanation:
    - id: id of the case
    - name: title of the case

    - source: starting node ID
    - destination: target node ID

    - departure_hour: hour of travel (affects traffic)

    - avoid_nodes: nodes to avoid [list of nodes](optional)
                -> create avoid node(s) by using the node IDs
                ex1:[5, 1067]
                ex2:[1, 3, 5, 7, 8]

    - avoid_edges: edges to avoid [list of lists node](optional)
                -> create avoid edge(s) by using "from node id" to "end node id" 
                ex1: [
                        [1, 9]
                    ]

                ex2: [
                        [5, 3],
                        [3509, 4449]
                    ]


DESCRIPT OF OUTPUT
========================================
The system outputs:

1. Path Results:
    - Path: display a path with node IDs
    - Path: display a path with location names

2. Metrics:
    - Total distance: float number with kilometer unit (km)
    - Total travel time: float number with minutes unit (mins/minutes)

3. Algorithm Performance:
    - Nodes explored: The number of nodes visited during the algorithm excecute.
    - Edges relaxed: The number of times the algorithm updates the best-known cost to reach a node.
    - Runtime (ms): The total excecution time of the algorithm in miliseconds unit (ms)
    - Heap operations (optimized version): The number of operations performed on the MinHeap (insertions and extractions).

5. Algorithm Comparisons:
    - Original Dijkstra (distance): The standard Dijkstra algorithm optimizing for shortest distance.
    - Optimized Dijkstra (distance): An improved version using a MinHeap (priority queue).
    
    - Original Dijkstra (time): The standard Dijkstra algorithm optimizing for travel time instead of distance.
    - Optimized Dijkstra (time): the optimized Dijkstra algorithm optimizing for travel time instead of distance.

(Reference implementation: solution.py)


#LINK TO THE DEMO VIDEO 
========================================
Demo video link: https://youtu.be/v8rps85Unvo?si=KLzk1saSBnvWsdav


