"""
Map Visualizer for the Smart Path Finder.

Standalone script that draws the entire road network map:
- Nodes colored by neighborhood cluster
- Edges drawn as lines (local=thin gray, highway=thick blue)
- Optional: highlight a specific path on top

Usage:
    python visualize.py                      # Draw full map
    python visualize.py --path 0 1999 8      # Draw map + shortest path (src dst hour)
    python visualize.py --no-edges           # Draw nodes only (faster)
    python visualize.py --save map.png       # Save to file instead of showing

Requires: matplotlib (pip install matplotlib)
This is a visualization tool only — not part of the main program.
"""

import sys
import os
import math

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import matplotlib.pyplot as plt
import matplotlib.collections as mc
import matplotlib.patches as mpatches

from csv_io import load_graph, data_exists
from graph import Graph, haversine
from dijkstra import dijkstra_optimized, distance_weight, time_weight


# =============================================================================
# Configuration
# =============================================================================

DATA_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'data')
NODES_PATH = os.path.join(DATA_DIR, 'nodes.csv')
EDGES_PATH = os.path.join(DATA_DIR, 'edges.csv')

# Visual settings
FIGURE_SIZE = (16, 14)
DPI = 120
BG_COLOR = '#1a1a2e'
EDGE_COLOR_LOCAL = '#2a2a4a'
EDGE_COLOR_CITY = '#3a3a6a'
EDGE_COLOR_HIGHWAY = '#4a7af5'
NODE_SIZE_DEFAULT = 4
NODE_SIZE_HIGHLIGHT = 80
PATH_COLOR = '#ff4757'
PATH_WIDTH = 2.5
FONT_SIZE_TITLE = 14
FONT_SIZE_LABEL = 6


def classify_edge_color(distance_m):
    """Return color and linewidth based on edge distance."""
    if distance_m > 5000:
        return EDGE_COLOR_HIGHWAY, 1.0, 0.6  # highway: blue, thick
    elif distance_m > 1000:
        return EDGE_COLOR_CITY, 0.5, 0.3     # city: medium
    else:
        return EDGE_COLOR_LOCAL, 0.3, 0.15    # local: thin, faint


def assign_cluster_colors(graph, num_clusters=20):
    """
    Assign colors to nodes based on spatial clustering (simple grid-based).
    Returns dict[node_id] -> color string.
    """
    if not graph.nodes:
        return {}

    # Find bounds
    lats = [n.lat for n in graph.nodes.values()]
    lons = [n.lon for n in graph.nodes.values()]
    lat_min, lat_max = min(lats), max(lats)
    lon_min, lon_max = min(lons), max(lons)

    lat_range = lat_max - lat_min or 1
    lon_range = lon_max - lon_min or 1

    grid_size = int(math.sqrt(num_clusters))

    # Color palette (20 distinct colors)
    palette = [
        '#ff6b6b', '#ffa502', '#ffd43b', '#51cf66', '#20c997',
        '#38d9a9', '#22b8cf', '#4dabf7', '#5c7cfa', '#845ef7',
        '#cc5de8', '#f06595', '#ff8787', '#ffa94d', '#ffe066',
        '#69db7c', '#63e6be', '#66d9e8', '#74c0fc', '#91a7ff',
    ]

    colors = {}
    for node in graph.nodes.values():
        row = min(int((node.lat - lat_min) / lat_range * grid_size), grid_size - 1)
        col = min(int((node.lon - lon_min) / lon_range * grid_size), grid_size - 1)
        idx = (row * grid_size + col) % len(palette)
        colors[node.id] = palette[idx]

    return colors


def draw_map(graph, path=None, path_label="", show_edges=True,
             save_path=None, title="Smart Path Finder — Road Network Map"):
    """
    Draw the full road network map.

    Args:
        graph: Graph object with nodes and edges loaded.
        path: Optional list of node IDs to highlight as a path.
        path_label: Label for the highlighted path.
        show_edges: Whether to draw edges (False = nodes only, much faster).
        save_path: If set, save to file instead of showing interactively.
        title: Plot title.
    """
    fig, ax = plt.subplots(1, 1, figsize=FIGURE_SIZE, dpi=DPI)
    fig.patch.set_facecolor(BG_COLOR)
    ax.set_facecolor(BG_COLOR)

    # ── Draw edges ──
    if show_edges:
        # Group edges by type for batch drawing (much faster than individual lines)
        local_lines = []
        city_lines = []
        highway_lines = []

        for node_id in graph.adjacency:
            node = graph.nodes[node_id]
            for neighbor_id, edge in graph.adjacency[node_id]:
                neighbor = graph.nodes.get(neighbor_id)
                if neighbor is None:
                    continue
                segment = [(node.lon, node.lat), (neighbor.lon, neighbor.lat)]

                if edge.distance > 5000:
                    highway_lines.append(segment)
                elif edge.distance > 1000:
                    city_lines.append(segment)
                else:
                    local_lines.append(segment)

        # Draw as LineCollections (very fast)
        if local_lines:
            lc = mc.LineCollection(local_lines, colors=EDGE_COLOR_LOCAL,
                                   linewidths=0.3, alpha=0.15, zorder=1)
            ax.add_collection(lc)
        if city_lines:
            lc = mc.LineCollection(city_lines, colors=EDGE_COLOR_CITY,
                                   linewidths=0.5, alpha=0.3, zorder=2)
            ax.add_collection(lc)
        if highway_lines:
            lc = mc.LineCollection(highway_lines, colors=EDGE_COLOR_HIGHWAY,
                                   linewidths=1.0, alpha=0.6, zorder=3)
            ax.add_collection(lc)

    # ── Draw nodes ──
    node_colors = assign_cluster_colors(graph)
    lons = [n.lon for n in graph.nodes.values()]
    lats = [n.lat for n in graph.nodes.values()]
    colors = [node_colors.get(n.id, '#ffffff') for n in graph.nodes.values()]

    ax.scatter(lons, lats, s=NODE_SIZE_DEFAULT, c=colors, alpha=0.7,
               edgecolors='none', zorder=4)

    # ── Draw highlighted path ──
    if path and len(path) >= 2:
        path_lons = [graph.nodes[nid].lon for nid in path]
        path_lats = [graph.nodes[nid].lat for nid in path]

        # Path line
        ax.plot(path_lons, path_lats, color=PATH_COLOR, linewidth=PATH_WIDTH,
                alpha=0.9, zorder=6, label=path_label or "Path")

        # Path nodes (larger)
        ax.scatter(path_lons, path_lats, s=NODE_SIZE_HIGHLIGHT, c=PATH_COLOR,
                   edgecolors='white', linewidths=0.5, alpha=0.9, zorder=7)

        # Label start and end
        start_node = graph.nodes[path[0]]
        end_node = graph.nodes[path[-1]]
        ax.annotate(f"START: {start_node.name}",
                    (start_node.lon, start_node.lat),
                    textcoords="offset points", xytext=(10, 10),
                    fontsize=FONT_SIZE_LABEL + 2, color='#2ed573', fontweight='bold',
                    arrowprops=dict(arrowstyle='->', color='#2ed573', lw=1),
                    zorder=8)
        ax.annotate(f"END: {end_node.name}",
                    (end_node.lon, end_node.lat),
                    textcoords="offset points", xytext=(10, -15),
                    fontsize=FONT_SIZE_LABEL + 2, color='#ffa502', fontweight='bold',
                    arrowprops=dict(arrowstyle='->', color='#ffa502', lw=1),
                    zorder=8)

        ax.legend(loc='upper right', fontsize=9, facecolor='#16213e',
                  edgecolor='#444', labelcolor='white')

    # ── Styling ──
    ax.set_title(title, fontsize=FONT_SIZE_TITLE, color='white', fontweight='bold', pad=15)
    ax.set_xlabel('Longitude', fontsize=10, color='#888')
    ax.set_ylabel('Latitude', fontsize=10, color='#888')
    ax.tick_params(colors='#666', labelsize=8)
    for spine in ax.spines.values():
        spine.set_color('#333')

    # Stats box
    stats_text = (
        f"Nodes: {graph.node_count():,}\n"
        f"Edges: {graph.edge_count():,}\n"
        f"Avg degree: {graph.edge_count() / graph.node_count():.1f}"
    )
    ax.text(0.02, 0.98, stats_text, transform=ax.transAxes,
            fontsize=9, color='#aaa', verticalalignment='top',
            fontfamily='monospace',
            bbox=dict(boxstyle='round,pad=0.5', facecolor='#16213e',
                      edgecolor='#444', alpha=0.9))

    ax.set_aspect('equal')
    ax.autoscale_view()
    plt.tight_layout()

    if save_path:
        plt.savefig(save_path, dpi=DPI, facecolor=BG_COLOR, bbox_inches='tight')
        print(f"Map saved to {save_path}")
    else:
        plt.show()

    plt.close(fig)


# =============================================================================
# Main
# =============================================================================

def main():
    args = sys.argv[1:]

    if not data_exists(NODES_PATH, EDGES_PATH):
        print("Error: No map data found. Run 'python main.py' first to generate the map.")
        sys.exit(1)

    print("Loading map...")
    graph = load_graph(NODES_PATH, EDGES_PATH)

    show_edges = '--no-edges' not in args
    save_path = None
    path = None
    path_label = ""

    # Parse --save
    if '--save' in args:
        idx = args.index('--save')
        if idx + 1 < len(args):
            save_path = args[idx + 1]

    # Parse --path src dst [hour]
    if '--path' in args:
        idx = args.index('--path')
        if idx + 2 < len(args):
            src = int(args[idx + 1])
            dst = int(args[idx + 2])
            hour = int(args[idx + 3]) if idx + 3 < len(args) else 8

            print(f"Computing shortest path: {src} -> {dst} (departure {hour}:00)...")
            
            # Run distance Dijkstra
            result_dist = dijkstra_optimized(graph, src, dst, distance_weight, hour)
            # Run time Dijkstra
            result_time = dijkstra_optimized(graph, src, dst, time_weight, hour)

            if result_dist.found:
                path = result_dist.path
                path_label = (f"Shortest distance: {result_dist.total_distance / 1000:.2f} km, "
                              f"{result_dist.total_time:.1f} min")
                print(f"  Distance path: {len(path)} nodes, "
                      f"{result_dist.total_distance / 1000:.2f} km")
            else:
                print("  No path found!")

    title = "Smart Path Finder — Road Network Map"
    if path:
        src_name = graph.nodes[path[0]].name
        dst_name = graph.nodes[path[-1]].name
        title = f"Route: {src_name} → {dst_name}"

    draw_map(graph, path=path, path_label=path_label,
             show_edges=show_edges, save_path=save_path, title=title)


if __name__ == '__main__':
    main()
