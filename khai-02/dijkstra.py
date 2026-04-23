"""
Dijkstra's algorithm implementations for the Smart Path Finder.

Provides two versions:
1. Original Dijkstra — O(V²) with array scan + early termination
2. Optimized Dijkstra — O((V+E) log V) with custom binary heap + lazy deletion + early termination

Both versions support:
- Distance-based shortest path (fixed edge weight)
- Time-based shortest path (time-dependent edge weight based on hour of day)
- Node avoidance (skip certain nodes)
- Edge avoidance (skip certain edges)
- Per-query evaluation metrics (runtime, nodes explored, edges relaxed, etc.)
"""

import time

from heap import MinHeap
from graph import Graph


class DijkstraResult:
    """Stores the result of a Dijkstra query including path and evaluation metrics."""

    __slots__ = (
        'path', 'total_distance', 'total_time',
        'nodes_explored', 'edges_relaxed', 'runtime_ms',
        'heap_operations', 'algorithm'
    )

    def __init__(self, algorithm_name):
        self.path = []               # list of node IDs
        self.total_distance = 0.0    # total distance in meters
        self.total_time = 0.0        # total travel time in minutes
        self.nodes_explored = 0      # nodes popped / processed
        self.edges_relaxed = 0       # edges where a shorter distance was found
        self.runtime_ms = 0.0        # wall-clock time in milliseconds
        self.heap_operations = 0     # push + pop count (optimized only)
        self.algorithm = algorithm_name

    @property
    def found(self):
        """True if a path was found."""
        return len(self.path) > 0

    def __repr__(self):
        if not self.found:
            return f"DijkstraResult({self.algorithm}: no path found)"
        return (
            f"DijkstraResult({self.algorithm}: "
            f"path_len={len(self.path)}, "
            f"dist={self.total_distance:.1f}m, "
            f"time={self.total_time:.2f}min, "
            f"explored={self.nodes_explored}, "
            f"relaxed={self.edges_relaxed}, "
            f"runtime={self.runtime_ms:.2f}ms)"
        )


def _reconstruct_path(previous_destionation, source, destination):
    """Reconstruct the path from source to dest using the prev dict."""
    
    if previous_destionation not in previous_destionation and destination != source:
        return []

    path = []
    current = previous_destionation

    while current is not None:
        path.append(current)
        if current == source:
            break
        current = previous_destionation.get(current)

    if not path or path[-1] != source:
        return []

    path.reverse()
    return path


def _compute_path_distance(graph, path):
    """Compute total distance along a path (sum of edge distances)."""
    total = 0.0
    for i in range(len(path) - 1):
        from_id = path[i]
        to_id = path[i + 1]

        for neighbor_id, edge in graph.adjacency.get(from_id, []):
            if neighbor_id == to_id:
                total += edge.distance
                break

    return total


def _compute_path_time(graph, path, departure_hour):
    """
    Compute total travel time along a path with time-dependent edges.

    Uses the time-dependent model:
    - Track accumulated time from departure
    - At each node, determine current hour based on departure + accumulated time
    - Use current hour to look up edge travel time
    """
    total_time = 0.0
    for i in range(len(path) - 1):
        from_id = path[i]
        to_id = path[i + 1]

        for neighbor_id, edge in graph.adjacency.get(from_id, []):
            if neighbor_id == to_id:
                current_minutes = departure_hour * 60 + total_time
                current_hour = int(current_minutes / 60) % 24
                total_time += edge.travel_times[current_hour]

                break

    return total_time


# =============================================================================
# Weight functions
# =============================================================================

def distance_weight(edge):
    """
    Weight function for shortest distance path.
    Returns the fixed distance of the edge.
    """
    return edge.distance


def time_weight(edge, accumulated_time, departure_hour):
    """
    Weight function for shortest travel time path (time-dependent).

    The travel time depends on what hour of the day you arrive at the edge's
    start node. This is computed from:
      current_time = departure_hour * 60 + accumulated_time (minutes since midnight)
      current_hour = floor(current_time / 60) % 24

    For example: depart at 8:00, accumulated 30 min → current time is 8:30 → hour 8
    Edge's travel_times[8] is used.
    """
    current_minutes = departure_hour * 60 + accumulated_time
    current_hour = int(current_minutes / 60) % 24
    return edge.travel_times[current_hour]


# =============================================================================
# Original Dijkstra — O(V²) with early termination
# =============================================================================

def dijkstra_original(graph, source, dest, weight_fn, departure_hour=8, avoid_nodes=None, avoid_edges=None):
    """
    Original Dijkstra's algorithm using O(V) array scan for minimum extraction.

    Time Complexity: O(V² + E)
      - Each iteration scans all V nodes to find minimum → O(V) per iteration
      - At most V iterations → O(V²) for min-extraction
      - Edge relaxation is O(E) total

    Space Complexity: O(V) for dist and prev arrays.

    Args:
        graph: The Graph object.
        source: Source node ID.
        dest: Destination node ID.
        weight_fn: Function(edge, accumulated, departure_hour) → weight.
        departure_hour: Hour of departure (0-23), default 8 AM.
        avoid_nodes: Set of node IDs to avoid, or None.
        avoid_edges: Set of (from_id, to_id) to avoid, or None.

    Returns:
        DijkstraResult with path, metrics, etc.
    """
    result = DijkstraResult("Original (O(V²))")
    start_time = time.perf_counter()

    # Initialize distances for ALL nodes (array-based approach)
    distance = {}
    previous_destination = {}
    visited = set()

    for node_id in graph.nodes:
        distance[node_id] = float('inf')
    distance[source] = 0

    while True:
        # O(V) scan: find unvisited node with minimum distance
        u = None
        min_dist = float('inf')
        for node_id in graph.nodes:
            if node_id not in visited and node_id not in (avoid_nodes or set()):
                if distance[node_id] < min_dist:
                    min_dist = distance[node_id]
                    u = node_id

        if u is None:
            break  # no reachable unvisited node

        if u == dest:
            result.nodes_explored += 1
            break  # EARLY TERMINATION

        visited.add(u)
        result.nodes_explored += 1

        # Relax neighbors
        for v, edge in graph.get_neighbors(u, avoid_nodes, avoid_edges):
            if v in visited:
                continue

            w = weight_fn(edge, distance[u], departure_hour)
            new_dist = distance[u] + w

            if new_dist < distance[v]:
                distance[v] = new_dist
                previous_destination[v] = u
                result.edges_relaxed += 1

    end_time = time.perf_counter()
    result.runtime_ms = (end_time - start_time) * 1000

    # Reconstruct path
    result.path = _reconstruct_path(previous_destination, source, dest)

    if result.found:
        result.total_distance = _compute_path_distance(graph, result.path)
        result.total_time = _compute_path_time(graph, result.path, departure_hour)

    return result


# =============================================================================
# Optimized Dijkstra — O((V+E) log V) with binary heap + lazy deletion
# =============================================================================

def dijkstra_optimized(graph, source, destination, weight_fn, departure_hour=8, avoid_nodes=None, avoid_edges=None):
    """
    Optimized Dijkstra's algorithm using a custom binary min-heap.

    Key optimizations over the original:
    1. Binary min-heap: O(log n) extract-min instead of O(V) scan
    2. Lazy deletion: push new entries, skip stale ones on pop
    3. Sparse dist dict: only store visited/discovered nodes, not all V
    4. Early termination: stop when destination is popped

    Time Complexity: O((V + E) log V)
      - Each node is popped at most once (stale entries skipped) → V pops → O(V log V)
      - Each edge relaxation may push to heap → E pushes → O(E log V)
      - Total: O((V + E) log V)

    Space Complexity: O(V + E) for dist, prev, and heap.

    Args:
        graph: The Graph object.
        source: Source node ID.
        dest: Destination node ID.
        weight_fn: Function(edge, accumulated, departure_hour) → weight.
        departure_hour: Hour of departure (0-23), default 8 AM.
        avoid_nodes: Set of node IDs to avoid, or None.
        avoid_edges: Set of (from_id, to_id) to avoid, or None.

    Returns:
        DijkstraResult with path, metrics, etc.
    """
    result = DijkstraResult("Optimized (Heap)")
    start_time = time.perf_counter()

    distance = {}    # node_id → best known distance (sparse — not all V)
    previous = {}    # node_id → previous node in shortest path tree
    heap = MinHeap()

    distance[source] = 0
    heap.push(0, source)
    result.heap_operations += 1

    while not heap.is_empty():
        d, u = heap.pop()
        result.heap_operations += 1

        # Lazy deletion: skip stale entries
        if d > distance.get(u, float('inf')):
            continue

        result.nodes_explored += 1

        # Early termination: destination reached
        if u == destination:
            break

        # Relax neighbors
        for v, edge in graph.get_neighbors(u, avoid_nodes, avoid_edges):
            w = weight_fn(edge, d, departure_hour)
            new_dist = d + w

            if new_dist < distance.get(v, float('inf')):
                distance[v] = new_dist
                previous[v] = u
                heap.push(new_dist, v)
                result.edges_relaxed += 1
                result.heap_operations += 1

    end_time = time.perf_counter()
    result.runtime_ms = (end_time - start_time) * 1000

    # Reconstruct path
    result.path = _reconstruct_path(previous, source, destination)

    if result.found:
        result.total_distance = _compute_path_distance(graph, result.path)
        result.total_time = _compute_path_time(graph, result.path, departure_hour)

    return result
