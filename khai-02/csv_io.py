"""
CSV I/O module for the Smart Path Finder.

Handles loading and saving of node and edge data to CSV files.
Uses Python's built-in csv module only (no external libraries).

CSV Formats:
  nodes.csv: id,name,lat,lon
  edges.csv: from_id,to_id,distance,t0,t1,t2,...,t23
"""

import csv
import os

from graph import Node, Edge, Graph


def save_nodes(nodes, filepath):
    """
    Save nodes to a CSV file.

    Args:
        nodes: dict[int, Node] or list[Node]
        filepath: Path to the output CSV file.
    """
    os.makedirs(os.path.dirname(filepath), exist_ok=True)

    if isinstance(nodes, dict):
        node_list = sorted(nodes.values(), key=lambda n: n.id)
    else:
        node_list = sorted(nodes, key=lambda n: n.id)

    with open(filepath, 'w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerow(['id', 'name', 'lat', 'lon'])
        for node in node_list:
            writer.writerow([node.id, node.name, f"{node.lat:.6f}", f"{node.lon:.6f}"])

    print(f"  Saved {len(node_list)} nodes to {filepath}")


def save_edges(edges, filepath):
    """
    Save edges to a CSV file.

    Args:
        edges: list[Edge]
        filepath: Path to the output CSV file.
    """
    os.makedirs(os.path.dirname(filepath), exist_ok=True)

    with open(filepath, 'w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        header = ['from_id', 'to_id', 'distance'] + [f't{h}' for h in range(24)]
        writer.writerow(header)
        for edge in edges:
            row = [edge.from_id, edge.to_id, f"{edge.distance:.2f}"]
            row.extend([f"{t:.2f}" for t in edge.travel_times])
            writer.writerow(row)

    print(f"  Saved {len(edges)} edges to {filepath}")


def load_nodes(filepath):
    """
    Load nodes from a CSV file.

    Args:
        filepath: Path to the CSV file.

    Returns:
        dict[int, Node]
    """
    nodes = {}
    with open(filepath, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            node_id = int(row['id'])
            name = row['name']
            lat = float(row['lat'])
            lon = float(row['lon'])
            node = Node(node_id, name, lat, lon)
            nodes[node_id] = node

    print(f"  Loaded {len(nodes)} nodes from {filepath}")
    return nodes


def load_edges(filepath):
    """
    Load edges from a CSV file.

    Args:
        filepath: Path to the CSV file.

    Returns:
        list[Edge]
    """
    edges = []
    with open(filepath, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            from_id = int(row['from_id'])
            to_id = int(row['to_id'])
            distance = float(row['distance'])
            travel_times = [float(row[f't{h}']) for h in range(24)]
            edge = Edge(from_id, to_id, distance, travel_times)
            edges.append(edge)

    print(f"  Loaded {len(edges)} edges from {filepath}")
    return edges


def load_graph(nodes_path, edges_path):
    """
    Load a complete graph from CSV files.

    Args:
        nodes_path: Path to nodes CSV.
        edges_path: Path to edges CSV.

    Returns:
        Graph object with all nodes and edges loaded.
    """
    graph = Graph()

    nodes = load_nodes(nodes_path)
    for node in nodes.values():
        graph.add_node(node)

    edges = load_edges(edges_path)
    for edge in edges:
        graph.add_edge(edge)

    return graph


def save_graph(graph, nodes_path, edges_path):
    """
    Save a complete graph to CSV files.

    Args:
        graph: Graph object.
        nodes_path: Path to output nodes CSV.
        edges_path: Path to output edges CSV.
    """
    # Collect all edges from adjacency list
    all_edges = []
    for node_id in sorted(graph.adjacency.keys()):
        for _, edge in graph.adjacency[node_id]:
            all_edges.append(edge)

    save_nodes(graph.nodes, nodes_path)
    save_edges(all_edges, edges_path)


def data_exists(nodes_path, edges_path):
    """Check if both CSV data files exist."""
    return os.path.isfile(nodes_path) and os.path.isfile(edges_path)
