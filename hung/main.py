from grid_generator import grid_generator, display_grid
from eagerDijkstra.DijkstraAlgo import eager_dijkstra
from lazyDijkstra.DijkstraAlgo import lazy_dijkstra
from bidirectDijkstra.DijkstraAlgo import bidirectional_dijkstra, build_reverse_graph
import os
import time

def process_avoid_nodes(graph, node_names):
    return {graph.vertices[name] for name in node_names}

def process_avoid_edges(graph, edge_pairs):
    avoid_e = set()
    for u_name, v_name in edge_pairs:
        u_obj = graph.vertices[u_name]
        v_obj = graph.vertices[v_name]
        avoid_e.add(graph.adjList[u_obj][v_obj])
    return avoid_e

def time_test(algo, graph, start_vertex, end_vertex, avoid_nodes, avoid_edges):
    times = []
    iterations = 100
    for _ in range(iterations):
        graph.reset() 
        
        start = time.perf_counter()
        algo(graph, start_vertex, end_vertex, avoid_nodes, avoid_edges)
        end = time.perf_counter()
        
        times.append(end - start)
        
    avg_time = (sum(times) / iterations) * 1000
    print(f"Average Runtime over {iterations} runs: {avg_time:.4f} ms")
    
# main
# initialize the graph and display it
rows, cols = 100, 100
graph = grid_generator(rows, cols)
reverseList = build_reverse_graph(graph.adjList)
while True:
    os.system('cls')
    # display_grid(graph, rows, cols)

    # Get Start and End
    while True:
        start = input("Enter Start Node: ").strip()
        if start in graph.vertices:
            start_vertex = graph.vertices[start]
            break
        print("This node doesn't exist") 

    while True:
        end = input("Enter End Node: ").strip()
        if end in graph.vertices:
            end_vertex = graph.vertices[end]
            break
        print("This node doesn't exist") 

    # Avoid Nodes
    avoid_nodes = []
    print("\n[OPTIONAL] Enter nodes to avoid. Press ENTER when done.")
    while True:
        node = input("Avoid Node: ").strip()
        if not node: break
        
        if node in graph.vertices:
            avoid_nodes.append(node)
        else:
            print(f"Node '{node}' not found. Try again.")

    avoid_nodes = process_avoid_nodes(graph, avoid_nodes)

    # Avoid Edges
    avoid_edges = []
    print("\n[OPTIONAL] Enter edges to avoid (Format: Start-End). Press ENTER when done.")
    while True:
        edge_input = input("Avoid Edge: ").strip()
        if not edge_input: break
        
        if "-" in edge_input:
            u_name, v_name = [x.strip() for x in edge_input.split("-")]
            
            # Validation: Do both nodes exist?
            if u_name in graph.vertices and v_name in graph.vertices:
                u_obj = graph.vertices[u_name]
                v_obj = graph.vertices[v_name]
                
                # Validation: Is there a road between them?
                if v_obj in graph.adjList.get(u_obj, {}):
                    avoid_edges.append((u_name, v_name))
                else:
                    print(f"No direct road exists from {u_name} to {v_name}.")
            else:
                print("One or both nodes do not exist.")
        else:
            print("Use 'Start-End' format.")

    avoid_edges = process_avoid_edges(graph, avoid_edges)

    # Algorithm execution
    # time_test(lazy_dijkstra, graph, start_vertex, end_vertex, avoid_nodes, avoid_edges)
    # time_test(bidirectional_dijkstra, graph, start_vertex, end_vertex, avoid_nodes, avoid_edges)
    
    # times = []
    # iterations = 100
    # for _ in range(iterations):
    #     graph.reset() 
        
    #     start = time.perf_counter()
    #     bidirectional_dijkstra(graph, start_vertex, end_vertex, avoid_nodes, avoid_edges, reverseList)
    #     end = time.perf_counter()
        
    #     times.append(end - start)
        
    # avg_time = (sum(times) / iterations) * 1000
    # print(f"Average Runtime over {iterations} runs: {avg_time:.4f} ms")
    
    shortest_path, distance = eager_dijkstra(graph, start_vertex, end_vertex, avoid_nodes, avoid_edges)
    
    if distance != float("inf"):
        print(f'Shortest path: {shortest_path}')
        print(f'Distance: {distance}')
    else:
        print("Unreachable!")
   
    input("Press Enter to continue...")
    # Reset graph
    graph.reset()