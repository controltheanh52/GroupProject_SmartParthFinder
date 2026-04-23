"""
Smart Path Finder — Main Entry Point

Interactive CLI for computing shortest paths on a road network map.
- Loads graph from CSV files (or generates if not present)
- Accepts routing queries with source, destination, departure hour, avoid constraints
- Returns shortest distance and shortest travel time paths
- Displays evaluation metrics comparing Original vs Optimized Dijkstra

Usage:
    python main.py                     # Normal mode: load from CSV or generate
    python main.py --regenerate        # Force regenerate the map
    python main.py --regenerate-edges  # Keep nodes, regenerate edges only
"""

import sys
import os

from graph import Graph
from csv_io import load_graph, save_graph, data_exists
from map_generator import generate_map, generate_edges
from csv_io import load_nodes, save_nodes, save_edges
from query import Query, execute_query, format_comparison


# =============================================================================
# Configuration
# =============================================================================

DATA_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'data')
NODES_PATH = os.path.join(DATA_DIR, 'nodes.csv')
EDGES_PATH = os.path.join(DATA_DIR, 'edges.csv')

DEFAULT_DEPARTURE_HOUR = 8  # 8:00 AM


# =============================================================================
# Map loading / generation
# =============================================================================

def load_or_generate_map(force_regenerate=False, regenerate_edges=False):
    """
    Load the map from CSV files, or generate if not present.

    Args:
        force_regenerate: If True, regenerate entire map.
        regenerate_edges: If True, keep nodes but regenerate edges.

    Returns:
        Graph object.
    """
    if force_regenerate or not data_exists(NODES_PATH, EDGES_PATH):
        if force_regenerate:
            print("Force regenerating map...")
        else:
            print("No existing map data found. Generating new map...")

        graph = generate_map()
        save_graph(graph, NODES_PATH, EDGES_PATH)
        return graph

    if regenerate_edges:
        print("Regenerating edges (keeping existing nodes)...")
        nodes = load_nodes(NODES_PATH)
        node_list = sorted(nodes.values(), key=lambda n: n.id)
        edges = generate_edges(node_list)

        graph = Graph()
        for node in node_list:
            graph.add_node(node)
        for edge in edges:
            graph.add_edge(edge)

        save_edges(edges, EDGES_PATH)
        return graph

    print("Loading existing map from CSV...")
    graph = load_graph(NODES_PATH, EDGES_PATH)
    return graph


# =============================================================================
# Node search
# =============================================================================

def search_nodes(graph, search_term):
    """
    Search nodes by name (case-insensitive partial match).

    Returns:
        List of (node_id, node_name) tuples, max 15 results.
    """
    term = search_term.lower()
    results = []
    for node in graph.nodes.values():
        if term in node.name.lower():
            results.append((node.id, node.name))
    results.sort(key=lambda x: x[0])
    return results[:15]


# =============================================================================
# Interactive CLI
# =============================================================================

def print_banner(graph):
    """Print the application banner."""
    print()
    print("╔══════════════════════════════════════════════════════════════╗")
    print("║                 SMART PATH FINDER                            ║")
    print("║           Algorithms & Analysis 2026A                        ║")
    print("╠══════════════════════════════════════════════════════════════╣")
    print(f"║  Nodes: {graph.node_count():>6,}    Edges: {graph.edge_count():>6,}                              ║")
    print(f"║  Default departure: {DEFAULT_DEPARTURE_HOUR:02d}:00                                    ║")
    print("╠══════════════════════════════════════════════════════════════╣")
    print("║  Commands:                                                   ║")
    print("║    query    - Execute a routing query                        ║")
    print("║    search   - Search nodes by name                           ║")
    print("║    node     - Show node details by ID                        ║")
    print("║    stats    - Show graph statistics                          ║")
    print("║    help     - Show this help message                         ║")
    print("║    quit     - Exit the program                               ║")
    print("╚══════════════════════════════════════════════════════════════╝")
    print()


def prompt_int(prompt, default=None, min_val=None, max_val=None):
    """Prompt for an integer with optional default and range validation."""
    while True:
        suffix = f" [{default}]" if default is not None else ""
        raw = input(f"  {prompt}{suffix}: ").strip()

        if not raw and default is not None:
            return default
        try:
            val = int(raw)
            if min_val is not None and val < min_val:
                print(f"    Value must be >= {min_val}")
                continue
            if max_val is not None and val > max_val:
                print(f"    Value must be <= {max_val}")
                continue
            return val
        except ValueError:
            print(f"    Invalid integer.")


def prompt_node(graph, label):
    """
    Prompt the user for a node (by ID or name search).
    Returns node ID or None.
    """
    while True:
        raw = input(f"  {label} (ID or name): ").strip()
        if not raw:
            return None

        # Try as integer ID first
        try:
            node_id = int(raw)
            if node_id in graph.nodes:
                node = graph.nodes[node_id]
                print(f"    → [{node.id}] {node.name}")
                return node_id
            else:
                print(f"    Node ID {node_id} not found.")
                continue
        except ValueError:
            pass

        # Try as name search
        results = search_nodes(graph, raw)
        if not results:
            print(f"    No nodes matching '{raw}'.")
            continue

        if len(results) == 1:
            nid, name = results[0]
            print(f"    → [{nid}] {name}")
            return nid

        print(f"    Found {len(results)} matches:")
        for nid, name in results:
            print(f"      [{nid}] {name}")
        # Ask user to pick
        pick = prompt_int("Pick node ID", min_val=0)
        if pick in graph.nodes:
            return pick
        print(f"    Invalid node ID.")


def prompt_avoid_nodes():
    """Prompt for nodes to avoid (comma-separated IDs)."""
    raw = input("  Avoid nodes (comma-separated IDs, or Enter to skip): ").strip()
    if not raw:
        return set()
    try:
        return {int(x.strip()) for x in raw.split(',') if x.strip()}
    except ValueError:
        print("    Invalid input, skipping avoid nodes.")
        return set()


def prompt_avoid_edges():
    """Prompt for edges to avoid (pairs like 1-2,3-4)."""
    raw = input("  Avoid edges (pairs like 1-2,3-4, or Enter to skip): ").strip()
    if not raw:
        return set()
    try:
        edges = set()
        for pair in raw.split(','):
            parts = pair.strip().split('-')
            if len(parts) == 2:
                edges.add((int(parts[0].strip()), int(parts[1].strip())))
        return edges
    except ValueError:
        print("    Invalid input, skipping avoid edges.")
        return set()


def handle_query(graph):
    """Handle a routing query from the user."""
    print("\n─── New Query ───")

    source = prompt_node(graph, "Source node")
    if source is None:
        print("  Cancelled.")
        return

    dest = prompt_node(graph, "Destination node")
    if dest is None:
        print("  Cancelled.")
        return

    if source == dest:
        print("  Source and destination are the same.")
        return

    departure_hour = prompt_int("Departure hour (0-23)", default=DEFAULT_DEPARTURE_HOUR,
                                min_val=0, max_val=23)
    avoid_nodes = prompt_avoid_nodes()
    avoid_edges = prompt_avoid_edges()

    # Validate avoid lists don't include source/dest
    if source in avoid_nodes:
        print("  Warning: source node is in avoid list, removing it.")
        avoid_nodes.discard(source)
    if dest in avoid_nodes:
        print("  Warning: destination node is in avoid list, removing it.")
        avoid_nodes.discard(dest)

    query = Query(source, dest, departure_hour, avoid_nodes, avoid_edges)
    print(f"\n  Running query: {query}")
    print("  Please wait...")

    qr = execute_query(graph, query)
    print(format_comparison(graph, qr))


def handle_search(graph):
    """Handle a node search."""
    term = input("  Search term: ").strip()
    if not term:
        return
    results = search_nodes(graph, term)
    if not results:
        print(f"  No nodes matching '{term}'.")
        return
    print(f"  Found {len(results)} results:")
    for nid, name in results:
        node = graph.nodes[nid]
        print(f"    [{nid}] {name}  (lat={node.lat:.6f}, lon={node.lon:.6f})")


def handle_node_detail(graph):
    """Show details for a specific node."""
    node_id = prompt_int("Node ID", min_val=0)
    node = graph.get_node(node_id)
    if not node:
        print(f"  Node {node_id} not found.")
        return
    print(f"  [{node.id}] {node.name}")
    print(f"  Coordinates: lat={node.lat:.6f}, lon={node.lon:.6f}")
    neighbors = graph.adjacency.get(node_id, [])
    print(f"  Outgoing edges: {len(neighbors)}")
    for nid, edge in neighbors[:10]:
        n = graph.get_node(nid)
        name = n.name if n else "?"
        print(f"    → [{nid}] {name}  (dist={edge.distance:.0f}m, "
              f"time@8h={edge.travel_times[8]:.1f}min)")
    if len(neighbors) > 10:
        print(f"    ... and {len(neighbors) - 10} more")


def handle_stats(graph):
    """Show graph statistics."""
    print(f"\n  Graph Statistics:")
    print(f"  {'─' * 35}")
    print(f"  Nodes:          {graph.node_count():>10,}")
    print(f"  Edges:          {graph.edge_count():>10,}")

    if graph.node_count() > 0:
        avg_deg = graph.edge_count() / graph.node_count()
        print(f"  Avg out-degree: {avg_deg:>10.2f}")

    # Degree distribution
    degrees = [len(graph.adjacency.get(nid, [])) for nid in graph.nodes]
    if degrees:
        print(f"  Min out-degree: {min(degrees):>10}")
        print(f"  Max out-degree: {max(degrees):>10}")

    # Connected check
    connected = graph.is_connected()
    print(f"  Connected:      {'Yes':>10}" if connected else f"  Connected:      {'No':>10}")
    print()


def interactive_loop(graph):
    """Main interactive command loop."""
    print_banner(graph)

    while True:
        try:
            cmd = input(">>> ").strip().lower()
        except (EOFError, KeyboardInterrupt):
            print("\nGoodbye!")
            break

        if not cmd:
            continue
        elif cmd in ('query', 'q'):
            handle_query(graph)
        elif cmd in ('search', 's'):
            handle_search(graph)
        elif cmd in ('node', 'n'):
            handle_node_detail(graph)
        elif cmd in ('stats', 'st'):
            handle_stats(graph)
        elif cmd in ('help', 'h', '?'):
            print_banner(graph)
        elif cmd in ('quit', 'exit', 'x'):
            print("Goodbye!")
            break
        else:
            print(f"  Unknown command: '{cmd}'. Type 'help' for available commands.")


# =============================================================================
# Main
# =============================================================================

def main():
    """Entry point."""
    args = sys.argv[1:]

    force_regenerate = '--regenerate' in args
    regenerate_edges = '--regenerate-edges' in args

    graph = load_or_generate_map(force_regenerate, regenerate_edges)
    interactive_loop(graph)


if __name__ == '__main__':
    main()
