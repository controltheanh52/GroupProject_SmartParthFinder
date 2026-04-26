"""
Smart Path Finder - Solution (Core Logic & Routing)
"""

import csv
import os
import random
import time
import math

# =============================================================================
# Core Solution & Data Structures
# =============================================================================

# =============================================================================
# Node (Location)
# =============================================================================

# Represents a location in the map
class Node:

    # Initialize the node/location
    def __init__(self, node_id, name, lat, lon):

        # Parameters:
        #     node_id: Unique identifier for the node.
        #     name: Name of the location.
        #     lat: Latitude of the location.
        #     lon: Longitude of the location.

        self.id = node_id
        self.name = name
        self.lat = lat
        self.lon = lon
        
    # Format a string output upon being called by print()
    def __repr__(self):
        return f"Node({self.id}, '{self.name}')"

# =============================================================================
# Edge (Road)
# =============================================================================

# Represents a directed road between two nodes
class Edge:

    # Initialize the edge/road
    def __init__(self, from_id, to_id, distance, travel_times):

        # Parameters:
        #     from_id: Source node ID.
        #     to_id: Destination node ID.
        #     distance: Distance in meters.
        #     travel_times: List of 24 floats, travel time in minutes per hour (index 0-23).

        self.from_id = from_id
        self.to_id = to_id
        self.distance = distance
        self.travel_times = travel_times
    
    # Format a string output upon being called by print()
    def __repr__(self):
        return f"Edge({self.from_id}->{self.to_id}, d={self.distance})"

# =============================================================================
# Graph (Map)
# =============================================================================

# Represents the map containing all the nodes with its connecting edges
class Graph:

    # Initialize the graph
    def __init__(self):

        # Parameters:
        #     nodes: Dictionary of nodes which each key is node_id and the value is node object.
        #     adjacency: Dictionary of edges which each key is node_id and the value is a list of (neighbor_id, edge) tuples.

        self.nodes = {}
        self.adjacency = {}
        
    # Add a node to the graph
    def add_node(self, node):
        self.nodes[node.id] = node
        if node.id not in self.adjacency:
            self.adjacency[node.id] = []
            
    # Add an edge to the graph
    def add_edge(self, edge):
        # Because this graph is an directed graph so  we only have one edge from standing node to the other node.
        # Therefore, each pair of from_id + to_id is used an unique indentifier.
        self.adjacency[edge.from_id].append((edge.to_id, edge)) 
        
    # Get a node by ID
    def get_node(self, node_id):
        return self.nodes.get(node_id)
        
    # Get neighbors from current standing node.
    def get_neighbors(self, from_id, avoid_nodes=None, avoid_edges=None):
        if from_id not in self.adjacency:
            return []
        
        neighbors = []
        for to_id, edge in self.adjacency[from_id]:
            if avoid_nodes and to_id in avoid_nodes:
                continue
            if avoid_edges and (from_id, to_id) in avoid_edges:
                continue
            neighbors.append((to_id, edge))
        return neighbors

# =============================================================================
# Custom MinHeap
# =============================================================================

class MinHeap:
    def __init__(self):
        self.heap = []

    def is_empty(self):
        return len(self.heap) == 0
    
    def peek(self):
        if len(self.heap) == 0:
            return None
        return self.heap[0]

    def insert_node(self, reach_cost, reach_node_id):
        # Parameters:
        #   reach_cost: The cost to reach the node.
        #   reach_node_id: The ID of the node to reach.
        self.heap.append((reach_cost, reach_node_id))
        self.heapify_up(len(self.heap) - 1)

    def heapify_up(self, index):
        while index > 0:
            parent_index = self.parent(index)
            if self.heap[index][0] < self.heap[parent_index][0]:
                # swap
                self.heap[index], self.heap[parent_index] = self.heap[parent_index], self.heap[index]
                index = parent_index
            else:
                break

    def extract_min(self):
        if self.is_empty():
            return None, None
        
        # swap the item at first index and last index to each other
        self.heap[0], self.heap[len(self.heap) - 1] = self.heap[len(self.heap) - 1], self.heap[0]
        item = self.heap.pop()
        if self.heap:
            self.heapify_down(0)
        return item[0], item[1]

    def heapify_down(self, index):
        smallest = index
        left_index = self.left_child(index)
        right_index = self.right_child(index)

        if left_index < len(self.heap) and self.heap[left_index][0] < self.heap[smallest][0]:
            smallest = left_index
        if right_index < len(self.heap) and self.heap[right_index][0] < self.heap[smallest][0]:
            smallest = right_index

        if smallest != index:
            # swap
            self.heap[index], self.heap[smallest] = self.heap[smallest], self.heap[index]
            self.heapify_down(smallest)

    def parent(self, index): 
        return (index - 1) // 2
    
    def left_child(self, index):
        return 2 * index + 1
    
    def right_child(self, index):
        return 2 * index + 2


class DijkstraResult:
    def __init__(self, algorithm_name):
        self.algorithm_name = algorithm_name
        self.found = False
        self.path = []
        self.total_distance = float('inf')
        self.total_time = float('inf')
        self.nodes_explored = 0
        self.edges_relaxed = 0
        self.runtime_ms = 0.0
        self.heap_operations = 0

# Helper method to convert the path from the prev dictionary to actual path 
# Because the original sequence is reversed
def reconstruct_path(prev, source, dest):
    path = []
    curr = dest
    while curr is not None:
        path.append(curr)
        curr = prev.get(curr)
    path.reverse()
    if path and path[0] == source:
        return path
    return []

# Helper method to calculate the total distance of the path
def compute_path_distance(graph, path):
    total = 0.0
    for i in range(len(path) - 1):
        u = path[i]
        v = path[i+1]
        for neighbor_id, edge in graph.adjacency.get(u, []):
            if neighbor_id == v:
                total += edge.distance
                break
    return total

# Helper method to calculate the total travel time of the path
def compute_path_time(graph, path, departure_hour):
    total = 0.0
    for i in range(len(path) - 1):
        u = path[i]
        v = path[i+1]
        current_hour = (departure_hour + int(total / 60)) % 24
        
        for neighbor_id, edge in graph.adjacency.get(u, []):
            if neighbor_id == v:
                total += edge.travel_times[current_hour]
                break
    return total

# Helper functions to return the edge cost based on distance(km)
def distance_weight(edge, accumulated_time, departure_hour):
    return edge.distance

# Helper functions to return the edge cost based on time(minutes)
def time_weight(edge, accumulated_time, departure_hour):
    current_hour = (departure_hour + int(accumulated_time / 60)) % 24
    return edge.travel_times[current_hour]


# =============================================================================
# Orignal Dijkstra Algorithms
# =============================================================================

def dijkstra_original(graph, source_id, dest_id, weight_func, departure_hour=8, avoid_nodes=None, avoid_edges=None):
    # Start the benchmark runtime
    start_time = time.perf_counter() 

    # Initialize the result object for later display
    result = DijkstraResult("Original Dijkstra") 
    
    # Initialize the cost to reach each node is infinity
    cost_val = {node_id: float('inf') for node_id in graph.nodes} 
    
    # Set the reach cost to the start/source node is 0
    cost_val[source_id] = 0.0 
    
    # ceate a dictionary to keep track the node sequences of the shortest path
    prev = {source_id: None}
    
    # Create a list that tell we have not visited all the nodes yet
    unvisited = set(graph.nodes.keys())
    
    if avoid_nodes:
        # Pre check the query if the start node in the avoid_nodes list
        if source_id in avoid_nodes:
            return result
            
        # Remove the avoid_nodes from the unvisited set
        for node in avoid_nodes:
            unvisited.discard(node)

    # How to score each node
    def get_known_score(node_id):
        return cost_val[node_id]
        
    while unvisited:
        # Scan all unvisited nodes and pick the one with the lowest distance score
        current_node_id = min(unvisited, key=get_known_score)
        current_cost = cost_val[current_node_id]
        
        if current_cost == float('inf'):
            break
            
        unvisited.remove(current_node_id)
        result.nodes_explored += 1      # Update the benchmark metrics
        
        
        if current_node_id == dest_id:
            break
            
        current_cost = cost_val[current_node_id] # accumulated time to reach current_node
        
        for neighbor_node_id, edge in graph.get_neighbors(current_node_id, avoid_nodes, avoid_edges):
            if neighbor_node_id not in unvisited:
                continue
                
            # calculate the cost of the edge based on the passing weighting function (distance-km or time-minutes) 
            edge_cost = weight_func(edge, current_cost, departure_hour) 
            new_cost = current_cost + edge_cost
            result.edges_relaxed += 1   # Update the benchmark metrics
            
            if new_cost < cost_val[neighbor_node_id]:
                cost_val[neighbor_node_id] = new_cost # Update the lowest cost to reach this same neighbor node
                prev[neighbor_node_id] = current_node_id # Add the current node in the node sequence

    if cost_val[dest_id] != float('inf'):
        result.found = True
        result.path = reconstruct_path(prev, source_id, dest_id)
        result.total_distance = compute_path_distance(graph, result.path)
        result.total_time = compute_path_time(graph, result.path, departure_hour)
        
    result.runtime_ms = (time.perf_counter() - start_time) * 1000
    return result

# =============================================================================
# Optimized Dijkstra Algorithms
# =============================================================================

def dijkstra_optimized(graph, source_id, dest_id, weight_func, departure_hour=8, avoid_nodes=None, avoid_edges=None):
    start_time = time.perf_counter()

    # Intialize an instance to save the return result
    result = DijkstraResult("Optimized Dijkstra")
    
    # Set the reach cost to the start/source node is 0
    cost_val = {source_id: 0.0} 

    # ceate a dictionary to keep track the node sequences of the shortest path
    prev = {source_id: None}
    
    # Optimize Feature No.1: minHeap
    heap = MinHeap()

    # In this case, we add the source_id as reach_node_id because our intial step is standing at the source node
    heap.insert_node(0.0, source_id) 

    result.heap_operations += 1     # Update the benchmark metrics
    
    # Pre check the query if the start node in the avoid_nodes list
    if avoid_nodes and source_id in avoid_nodes:
        return result
        
    while not heap.is_empty():
        # Extract the top node from the minHeap (has lowest cost)
        current_cost, current_node_id = heap.extract_min()
        result.heap_operations += 1
        
        # Optimize Feature No.2: Lazy Deletion/Duplicate Insertion
        # Check if the pop node is already visited with a lower cost
        # If yes, ignored the new pop cost
        if current_node_id in cost_val and current_cost > cost_val[current_node_id]:
            continue
        
        result.nodes_explored += 1
        
        # If the extracted node is the destination node, break the loop
        if current_node_id == dest_id:
            break
        
        for neighbor_node, edge in graph.get_neighbors(current_node_id, avoid_nodes, avoid_edges):
            # calculate the cost of the edge based on the passing weighting function (distance-km or time-minutes)
            edge_cost = weight_func(edge, current_cost, departure_hour)
            new_cost = current_cost + edge_cost
            result.edges_relaxed += 1    # Update the benchmark metrics
            
            # If the new cost is lower than the current cost, update the cost and the previous node
            if neighbor_node not in cost_val or new_cost < cost_val[neighbor_node]:
                cost_val[neighbor_node] = new_cost
                prev[neighbor_node] = current_node_id
                
                heap.insert_node(new_cost, neighbor_node)
                result.heap_operations += 1     # Update the benchmark metrics


    if dest_id in cost_val:
        result.found = True
        result.path = reconstruct_path(prev, source_id, dest_id)
        result.total_distance = compute_path_distance(graph, result.path)
        result.total_time = compute_path_time(graph, result.path, departure_hour)
        
    result.runtime_ms = (time.perf_counter() - start_time) * 1000
    return result

# =============================================================================
# CSV File Loading & Execution
# =============================================================================

def load_graph_csv(nodes_path, edges_path):
    if not os.path.exists(nodes_path) or not os.path.exists(edges_path):
        return None
        
    graph = Graph()
    
    with open(nodes_path, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            node = Node(int(row['id']), row['name'], float(row['lat']), float(row['lon']))
            graph.add_node(node)
            
    with open(edges_path, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            travel_times = [float(row[f't{h}']) for h in range(24)]
            edge = Edge(int(row['from_id']), int(row['to_id']), float(row['distance']), travel_times)
            graph.add_edge(edge)
            
    return graph

def update_travel_times_in_memory(graph):
    """
    Updates the travel times in memory to simulate weekly traffic updates.
    The changes are intentionally NOT saved back to CSV to preserve the original map.
    """
    rng = random.Random()
    update_count = 0
    
    for node_id in graph.adjacency:
        for i, (neighbor_id, edge) in enumerate(graph.adjacency[node_id]):
            # Random variation between 0.85x and 1.15x
            variation = rng.uniform(0.85, 1.15)
            # Apply to all hours
            edge.travel_times = [round(t * variation, 2) for t in edge.travel_times]
            update_count += 1
            
    print(f"Updated travel times for {update_count} edges (IN-MEMORY ONLY)!")
    print("These changes will revert to normal once you terminate the program.")


#Interactive Terminal for demonstration
def main():
    data_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'data')
    nodes_path = os.path.join(data_dir, 'nodes.csv')
    edges_path = os.path.join(data_dir, 'edges.csv')
    
    print("Loading graph data...")
    graph = load_graph_csv(nodes_path, edges_path)
    
    if graph is None:
        print(f"Error: map data not found in {data_dir}.")
        print("Please run 'python new_map.py' first to generate the map.")
        return
        
    print(f"Graph loaded successfully: {len(graph.nodes)} nodes, {sum(len(edges) for edges in graph.adjacency.values())} edges.")
    
    while True:
        print("\n--- Main Menu ---")
        print("1. Query Shortest Path")
        print("2. Search Node by Name")
        print("3. Update Travel Times (In-memory weekly update)")
        print("4. Quit")
        
        choice = input("Enter choice: ").strip()
        
        if choice == '1':
            try:
                print("\n--- Query Configuration ---")
                print("1. Case 1: Source & Destination Only")
                print("2. Case 2: Source, Dest, and Avoid Nodes")
                print("3. Case 3: Source, Dest, and Avoid Edges")
                print("4. Case 4: Source, Dest, Avoid Nodes, and Avoid Edges")
                print("5. Custom Query (Manual Input)")
                
                case_choice = input("Enter configuration (1-5): ").strip()
                
                if case_choice == '1':
                    src, dst, hour = 0, 4999, 8
                    avoid_nodes, avoid_edges = set(), set()
                    print(f"\n[Case 1] Running query from {src} to {dst} at {hour}:00...")
                    
                elif case_choice == '2':
                    src, dst, hour = 0, 4999, 8
                    avoid_nodes = {90, 88}  # Blocks nodes that appear in the original shortest path
                    avoid_edges = set()
                    print(f"\n[Case 2] Running query from {src} to {dst} avoiding nodes {avoid_nodes}...")
                    
                elif case_choice == '3':
                    src, dst, hour = 0, 4999, 8
                    avoid_nodes = set()
                    avoid_edges = {(5, 3), (3509, 4449)} # Blocks edges that appear in the original shortest path
                    print(f"\n[Case 3] Running query from {src} to {dst} avoiding edges {avoid_edges}...")
                    
                elif case_choice == '4':
                    src, dst, hour = 0, 4999, 8
                    avoid_nodes = {5, 1067}
                    avoid_edges = {(4449, 4561)}
                    print(f"\n[Case 4] Running query from {src} to {dst} avoiding nodes {avoid_nodes} and edges {avoid_edges}...")
                    
                else:
                    src_input = input("Enter source node ID: ").strip()
                    dst_input = input("Enter destination node ID: ").strip()
                    if not src_input or not dst_input: continue
                    
                    src = int(src_input)
                    dst = int(dst_input)
                    
                    hour_input = input("Enter departure hour (0-23) [8]: ").strip()
                    hour = int(hour_input) if hour_input else 8
                    
                    avoid_n_input = input("Avoid nodes (comma separated IDs) [none]: ").strip()
                    avoid_e_input = input("Avoid edges (pairs like 1-2, comma separated) [none]: ").strip()
                    
                    avoid_nodes = {int(x.strip()) for x in avoid_n_input.split(',')} if avoid_n_input else set()
                    avoid_edges = {tuple(map(int, x.split('-'))) for x in avoid_e_input.split(',')} if avoid_e_input else set()
                
                print("\n" + "="*50)
                print("1. ORIGINAL VERSION: Shortest Distance Path")
                res_dist_orig = dijkstra_original(graph, src, dst, distance_weight, hour, avoid_nodes, avoid_edges)
                if res_dist_orig.found:
                    path_str = ' -> '.join([f"{n_id}. {graph.get_node(n_id).name}" for n_id in res_dist_orig.path])
                    print(f"Path: {path_str}")
                    print(f"Distance: {res_dist_orig.total_distance/1000:.2f} km")
                    print(f"Time: {res_dist_orig.total_time:.1f} min")
                    print(f"Nodes Explored: {res_dist_orig.nodes_explored} | Edges Relaxed: {res_dist_orig.edges_relaxed} | Runtime: {res_dist_orig.runtime_ms:.2f} ms")
                else:
                    print("No path found.")

                print("\n" + "-"*50)
                print("2. OPTIMIZED VERSION: Shortest Distance Path")
                res_dist_opt = dijkstra_optimized(graph, src, dst, distance_weight, hour, avoid_nodes, avoid_edges)
                if res_dist_opt.found:
                    path_str = ' -> '.join([f"{n_id}. {graph.get_node(n_id).name}" for n_id in res_dist_opt.path])
                    print(f"Path: {path_str}")
                    print(f"Distance: {res_dist_opt.total_distance/1000:.2f} km")
                    print(f"Time: {res_dist_opt.total_time:.1f} min")
                    print(f"Nodes Explored: {res_dist_opt.nodes_explored} | Edges Relaxed: {res_dist_opt.edges_relaxed} | Heap Ops: {res_dist_opt.heap_operations} | Runtime: {res_dist_opt.runtime_ms:.2f} ms")
                else:
                    print("No path found.")
                    
                print("\n" + "="*50)
                print("3. ORIGINAL VERSION: Shortest Travel Time Path")
                res_time_orig = dijkstra_original(graph, src, dst, time_weight, hour, avoid_nodes, avoid_edges)
                if res_time_orig.found:
                    path_str = ' -> '.join([f"{n_id}. {graph.get_node(n_id).name}" for n_id in res_time_orig.path])
                    print(f"Path: {path_str}")
                    print(f"Distance: {res_time_orig.total_distance/1000:.2f} km")
                    print(f"Time: {res_time_orig.total_time:.1f} min")
                    print(f"Nodes Explored: {res_time_orig.nodes_explored} | Edges Relaxed: {res_time_orig.edges_relaxed} | Runtime: {res_time_orig.runtime_ms:.2f} ms")
                else:
                    print("No path found.")

                print("\n" + "-"*50)
                print("4. OPTIMIZED VERSION: Shortest Travel Time Path")
                res_time_opt = dijkstra_optimized(graph, src, dst, time_weight, hour, avoid_nodes, avoid_edges)
                if res_time_opt.found:
                    path_str = ' -> '.join([f"{n_id}. {graph.get_node(n_id).name}" for n_id in res_time_opt.path])
                    print(f"Path: {path_str}")
                    print(f"Distance: {res_time_opt.total_distance/1000:.2f} km")
                    print(f"Time: {res_time_opt.total_time:.1f} min")
                    print(f"Nodes Explored: {res_time_opt.nodes_explored} | Edges Relaxed: {res_time_opt.edges_relaxed} | Heap Ops: {res_time_opt.heap_operations} | Runtime: {res_time_opt.runtime_ms:.2f} ms")
                else:
                    print("No path found.")
            
            except ValueError:
                print("Invalid input.")
                
        elif choice == '2':
            term = input("Search term (name): ").strip().lower()
            found = []
            for n in graph.nodes.values():
                if term in n.name.lower():
                    found.append(n)
            
            if found:
                for n in found[:10]:
                    print(f"ID: {n.id}, Name: '{n.name}', Lat: {n.lat}, Lon: {n.lon}")
                if len(found) > 10:
                    print(f"... and {len(found)-10} more.")
            else:
                print("No nodes found.")
                
        elif choice == '3':
            update_travel_times_in_memory(graph)
            
        elif choice == '4':
            print("Goodbye!")
            break
        else:
            print("Invalid choice.")

if __name__ == '__main__':
    main()
