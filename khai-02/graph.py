"""
Graph data structure for the Smart Path Finder.

Represents a directed weighted graph using an adjacency list.
- Nodes have: id, name, latitude, longitude
- Edges have: from_id, to_id, distance (meters), travel_times (24 hourly values in minutes)

Space Complexity: O(V + E) where V = nodes, E = edges.
"""

import math

# Represents a location (intersection) on the map.
class Node:
    
    __slots__ = ('id', 'name', 'lat', 'lon') # for faster lookup and less memory

    def __init__(self, node_id, name, lat, lon):
        self.id = node_id
        self.name = name
        self.lat = lat
        self.lon = lon

    def __repr__(self):
        return f"Node({self.id}, '{self.name}', lat={self.lat:.6f}, lon={self.lon:.6f})"

# Represents a directed road between two nodes.
class Edge:

    __slots__ = ('from_id', 'to_id', 'distance', 'travel_times') # for faster lookup and less memory

    def __init__(self, from_id, to_id, distance, travel_times):
        """
        Args:
            from_id: Source node ID.
            to_id: Destination node ID.
            distance: Distance in meters.
            travel_times: List of 24 floats, travel time in minutes per hour (index 0-23).
        """
        self.from_id = from_id
        self.to_id = to_id
        self.distance = distance
        self.travel_times = travel_times  # list of 24 floats

    def __repr__(self):
        return f"Edge({self.from_id} -> {self.to_id}, dist={self.distance:.1f}m)"


def haversine(lat1, lon1, lat2, lon2):
    """
    Calculate the great-circle distance between two points on Earth
    using the Haversine formula.

    Args:
        lat1, lon1: Latitude and longitude of point 1 (degrees).
        lat2, lon2: Latitude and longitude of point 2 (degrees).

    Returns:
        Distance in meters.
    """
    R = 6_371_000  # Earth radius in meters

    phi1 = math.radians(lat1)
    phi2 = math.radians(lat2)
    d_phi = math.radians(lat2 - lat1)
    d_lambda = math.radians(lon2 - lon1)

    a = (math.sin(d_phi / 2) ** 2 +
         math.cos(phi1) * math.cos(phi2) * math.sin(d_lambda / 2) ** 2)
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))

    return R * c


class Graph:
    """
    Directed weighted graph using adjacency list representation.

    The adjacency list maps each node_id to a list of (neighbor_id, Edge) tuples.
    """

    def __init__(self):
        self.nodes = {}       # dict[int, Node]
        self.adjacency = {}   # dict[int, list[tuple[int, Edge]]]
        self._edge_count = 0

    def add_node(self, node):
        """Add a node to the graph."""
        self.nodes[node.id] = node
        if node.id not in self.adjacency:
            self.adjacency[node.id] = []

    def add_edge(self, edge):
        """Add a directed edge to the graph."""
        if edge.from_id not in self.adjacency:
            self.adjacency[edge.from_id] = []
        self.adjacency[edge.from_id].append((edge.to_id, edge))
        self._edge_count += 1

    def get_neighbors(self, node_id, avoid_nodes=None, avoid_edges=None):
        """
        Get reachable neighbors of a node, respecting avoid constraints.

        Args:
            node_id: The node to get neighbors for.
            avoid_nodes: set of node IDs to exclude, or None.
            avoid_edges: set of (from_id, to_id) tuples to exclude, or None.

        Returns:
            List of (neighbor_id, Edge) tuples.
        """
        if node_id not in self.adjacency:
            return []

        neighbors = self.adjacency[node_id]

        if avoid_nodes is None and avoid_edges is None:
            return neighbors

        result = []
        for neighbor_id, edge in neighbors:
            if avoid_nodes and neighbor_id in avoid_nodes:
                continue
            if avoid_edges and (edge.from_id, edge.to_id) in avoid_edges:
                continue
            result.append((neighbor_id, edge))

        return result

    def get_node(self, node_id):
        """Get a node by ID. Returns None if not found."""
        return self.nodes.get(node_id)

    def node_count(self):
        """Return the number of nodes."""
        return len(self.nodes)

    def edge_count(self):
        """Return the number of directed edges."""
        return self._edge_count

    def compute_distance(self, id_a, id_b):
        """Compute Haversine distance between two nodes (meters)."""
        a = self.nodes[id_a]
        b = self.nodes[id_b]
        return haversine(a.lat, a.lon, b.lat, b.lon)

    def is_connected(self):
        """
        Check if the graph is strongly connected using BFS from node 0.
        Returns True if all nodes are reachable from node 0.
        """
        if not self.nodes:
            return True

        start = next(iter(self.nodes))
        visited = set()
        queue = [start]
        visited.add(start)

        while queue:
            current = queue.pop(0)
            for neighbor_id, _ in self.adjacency.get(current, []):
                if neighbor_id not in visited:
                    visited.add(neighbor_id)
                    queue.append(neighbor_id)

        return len(visited) == len(self.nodes)

    def __repr__(self):
        return f"Graph(nodes={self.node_count()}, edges={self.edge_count()})"
