"""
Query processing module for the Smart Path Finder.

Handles parsing, validating, and executing routing queries.
Each query runs both distance and time Dijkstra, with both original and optimized
algorithms, providing evaluation metrics for comparison.
"""

from dijkstra import (
    dijkstra_original,
    dijkstra_optimized,
    distance_weight,
    time_weight,
    DijkstraResult,
)
from graph import Graph


class Query:
    """Represents a routing query."""

    def __init__(self, source, destination, departure_hour=8,
                 avoid_nodes=None, avoid_edges=None):
        """
        Args:
            source: Source node ID.
            destination: Destination node ID.
            departure_hour: Hour of departure (0-23), default 8 (8:00 AM).
            avoid_nodes: Set of node IDs to avoid, or None.
            avoid_edges: Set of (from_id, to_id) tuples to avoid, or None.
        """
        self.source = source
        self.destination = destination
        self.departure_hour = departure_hour
        self.avoid_nodes = avoid_nodes if avoid_nodes else set()
        self.avoid_edges = avoid_edges if avoid_edges else set()

    def __repr__(self):
        parts = [f"Query({self.source} -> {self.destination}, depart={self.departure_hour}h"]
        if self.avoid_nodes:
            parts.append(f", avoid_nodes={self.avoid_nodes}")
        if self.avoid_edges:
            parts.append(f", avoid_edges={self.avoid_edges}")
        parts.append(")")
        return "".join(parts)


class QueryResult:
    """Stores all results for a single query (4 Dijkstra runs)."""

    def __init__(self, query):
        self.query = query
        # Optimized algorithm results (primary)
        self.opt_distance_result = None    # DijkstraResult — shortest distance, optimized
        self.opt_time_result = None        # DijkstraResult — shortest time, optimized
        # Original algorithm results (for comparison)
        self.orig_distance_result = None   # DijkstraResult — shortest distance, original
        self.orig_time_result = None       # DijkstraResult — shortest time, original


def execute_query(graph, query):
    """
    Execute a routing query: run all 4 Dijkstra variants.

    Args:
        graph: The Graph object.
        query: A Query object.

    Returns:
        QueryResult with all 4 results.
    """
    qr = QueryResult(query)

    src = query.source
    dst = query.destination
    dep = query.departure_hour
    an = query.avoid_nodes if query.avoid_nodes else None
    ae = query.avoid_edges if query.avoid_edges else None

    # 1. Optimized Dijkstra — shortest distance
    qr.opt_distance_result = dijkstra_optimized(
        graph, src, dst, distance_weight, dep, an, ae
    )

    # 2. Optimized Dijkstra — shortest travel time
    qr.opt_time_result = dijkstra_optimized(
        graph, src, dst, time_weight, dep, an, ae
    )

    # 3. Original Dijkstra — shortest distance (for comparison)
    qr.orig_distance_result = dijkstra_original(
        graph, src, dst, distance_weight, dep, an, ae
    )

    # 4. Original Dijkstra — shortest travel time (for comparison)
    qr.orig_time_result = dijkstra_original(
        graph, src, dst, time_weight, dep, an, ae
    )

    return qr


def format_path(graph, path, max_display=10):
    """
    Format a path as a readable string with node names.

    Args:
        graph: The Graph object.
        path: List of node IDs.
        max_display: Maximum number of nodes to display in the path string.

    Returns:
        Formatted string.
    """
    if not path:
        return "  No path found."

    names = []
    for nid in path:
        node = graph.get_node(nid)
        if node:
            names.append(f"[{nid}] {node.name}")
        else:
            names.append(f"[{nid}]")

    if len(names) <= max_display:
        return " -> ".join(names)
    else:
        # Show first few, ..., last few
        shown = max_display // 2
        start = " -> ".join(names[:shown])
        end = " -> ".join(names[-shown:])
        skipped = len(names) - max_display
        return f"{start} -> ... ({skipped} more) ... -> {end}"


def format_result(graph, result, label):
    """
    Format a DijkstraResult for display.

    Args:
        graph: The Graph object.
        result: DijkstraResult.
        label: Display label (e.g., "Shortest Distance").

    Returns:
        Multi-line formatted string.
    """
    lines = []
    lines.append(f"\n  [{label}] ({result.algorithm})")
    lines.append(f"  {'─' * 55}")

    if not result.found:
        lines.append(f"    No path found.")
    else:
        lines.append(f"    Path ({len(result.path)} nodes):")
        lines.append(f"      {format_path(graph, result.path)}")
        lines.append(f"    Distance:  {result.total_distance:,.1f} m ({result.total_distance / 1000:.2f} km)")
        lines.append(f"    Time:      {result.total_time:.2f} min")

    lines.append(f"    ── Evaluation Metrics ──")
    lines.append(f"    Nodes explored:  {result.nodes_explored:,}")
    lines.append(f"    Edges relaxed:   {result.edges_relaxed:,}")
    lines.append(f"    Runtime:         {result.runtime_ms:.2f} ms")
    if result.heap_operations > 0:
        lines.append(f"    Heap operations: {result.heap_operations:,}")

    return "\n".join(lines)


def format_comparison(graph, qr):
    """
    Format a full QueryResult with comparison between algorithms.

    Args:
        graph: The Graph object.
        qr: QueryResult.

    Returns:
        Multi-line formatted string.
    """
    lines = []
    src_node = graph.get_node(qr.query.source)
    dst_node = graph.get_node(qr.query.destination)
    src_name = f"[{qr.query.source}] {src_node.name}" if src_node else f"[{qr.query.source}]"
    dst_name = f"[{qr.query.destination}] {dst_node.name}" if dst_node else f"[{qr.query.destination}]"

    lines.append(f"\n{'═' * 65}")
    lines.append(f"  QUERY: {src_name}  →  {dst_name}")
    lines.append(f"  Departure hour: {qr.query.departure_hour}:00")
    if qr.query.avoid_nodes:
        lines.append(f"  Avoid nodes: {qr.query.avoid_nodes}")
    if qr.query.avoid_edges:
        lines.append(f"  Avoid edges: {qr.query.avoid_edges}")
    lines.append(f"{'═' * 65}")

    # Optimized results (primary)
    lines.append(format_result(graph, qr.opt_distance_result, "Shortest Distance"))
    lines.append(format_result(graph, qr.opt_time_result, "Shortest Travel Time"))

    # Comparison table
    lines.append(f"\n  {'─' * 55}")
    lines.append(f"  ALGORITHM COMPARISON")
    lines.append(f"  {'─' * 55}")
    lines.append(f"  {'Metric':<22} {'Original':>15} {'Optimized':>15}")
    lines.append(f"  {'─' * 22} {'─' * 15} {'─' * 15}")

    # Distance path comparison
    od = qr.orig_distance_result
    optd = qr.opt_distance_result
    lines.append(f"  Distance path:")
    lines.append(f"    {'Explored nodes':<20} {od.nodes_explored:>15,} {optd.nodes_explored:>15,}")
    lines.append(f"    {'Relaxed edges':<20} {od.edges_relaxed:>15,} {optd.edges_relaxed:>15,}")
    lines.append(f"    {'Runtime (ms)':<20} {od.runtime_ms:>15.2f} {optd.runtime_ms:>15.2f}")
    if optd.runtime_ms > 0:
        speedup_d = od.runtime_ms / optd.runtime_ms
        lines.append(f"    {'Speedup':<20} {'':>15} {speedup_d:>14.1f}x")

    # Time path comparison
    ot = qr.orig_time_result
    optt = qr.opt_time_result
    lines.append(f"  Time path:")
    lines.append(f"    {'Explored nodes':<20} {ot.nodes_explored:>15,} {optt.nodes_explored:>15,}")
    lines.append(f"    {'Relaxed edges':<20} {ot.edges_relaxed:>15,} {optt.edges_relaxed:>15,}")
    lines.append(f"    {'Runtime (ms)':<20} {ot.runtime_ms:>15.2f} {optt.runtime_ms:>15.2f}")
    if optt.runtime_ms > 0:
        speedup_t = ot.runtime_ms / optt.runtime_ms
        lines.append(f"    {'Speedup':<20} {'':>15} {speedup_t:>14.1f}x")

    lines.append(f"{'═' * 65}")

    return "\n".join(lines)
