import time
from csv_loader import load_vertices, load_edges
from queries_loader import load_queries
from DijkstraAlgorithm import Dijkstra
#Main file

nodes = load_vertices("Data/vertices.csv")
load_edges("data/edges.csv", nodes)
queries = load_queries("queries.json")

def reset_graph(nodes):
    for node in nodes.values():
        node.visited = False
        node.predecessor = None
        node.min_distance = float("inf")
        node.min_time = float("inf")
        node.current_time = float("inf")
        node.f = float("inf")

for q in queries:
    print("\n======================================================")

    start_node = nodes[q["source"]]
    end_node = nodes[q["destination"]]
    start_time = q.get("start_time", 8)

    avoid_nodes = q["avoid_nodes"]
    avoid_edges = [tuple(edge) for edge in q.get("avoid_edges", [])]

    # reset graph before run next query
    reset_graph(nodes)

    algorithm = Dijkstra()

    print(f"Start time: {q['start_time']}")
    print(f"Source node: {q['source']}")
    print(f"Destination node: {q['destination']}")
    if avoid_nodes == []:
        print(f"Avoid nodes: EMPTY!!!")
    else:
        print(f"Avoid nodes: {avoid_nodes}")

    if avoid_edges == []:
        print(f"Avoid edges: EMPTY!!!")
    else:
        print(f"Avoid edges: {avoid_edges}")

    # caculate the A*
    start_1 = time.time()
    algorithm.calculate_distance_path(start_node, end_node, start_time, avoid_nodes, avoid_edges)
    end_1 = time.time()
    print("\nRuntime (shortest path algorithm):", (end_1 - start_1) * 1000, "ms")
    
    reset_graph(nodes)

    # time
    start = time.time()
    algorithm.calculate_time_path(start_node, end_node, start_time, avoid_nodes, avoid_edges)
    end = time.time()
    print("Runtime (fastest time algorithm):", (end - start) * 1000, "ms")