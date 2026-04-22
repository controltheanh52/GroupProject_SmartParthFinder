"""
main.py — Smart Path Finder Terminal Dashboard
===============================================
Run:  python3 main.py

PNG export requires matplotlib:  pip install matplotlib
"""

import os
import sys
import math

from smart_path_finder import (
    Graph, generate_dataset, get_demo_queries,
    dijkstra, astar, distance_weight, time_weight, run_query,
)


# =====================================================================
#  TERMINAL COLOURS
# =====================================================================

RESET   = "\033[0m"
BOLD    = "\033[1m"
DIM     = "\033[2m"
RED     = "\033[91m"
GREEN   = "\033[92m"
YELLOW  = "\033[93m"
BLUE    = "\033[94m"
MAGENTA = "\033[95m"
CYAN    = "\033[96m"
WHITE   = "\033[97m"


def clear():
    os.system("cls" if os.name == "nt" else "clear")

def sep():
    print(f"{DIM}{'─' * 62}{RESET}")

def banner():
    print(f"""
{CYAN}{BOLD}  ╔══════════════════════════════════════════════════════════════╗
  ║              SMART PATH FINDER  v1.0                       ║
  ║       Dijkstra & A* on Directed Road Networks              ║
  ╚══════════════════════════════════════════════════════════════╝{RESET}
""")

def header(text):
    print(f"\n{YELLOW}{BOLD}  ▸ {text}{RESET}")
    sep()

def ok(text):
    print(f"  {GREEN}✓{RESET} {text}")

def err(text):
    print(f"  {RED}✗{RESET} {text}")

def info(text):
    print(f"  {CYAN}ℹ{RESET} {text}")

def ask(text):
    return input(f"  {MAGENTA}>{RESET} {text}: ").strip()


def ask_weight_mode():
    """Prompt user to choose distance, time, or both."""
    choice = ask("Optimise for  [1] Distance  [2] Travel time  [3] Both (default 3)")
    if choice == "1":
        return "distance"
    elif choice == "2":
        return "time"
    else:
        return "both"


def print_result(r, graph):
    ac = GREEN if r.algorithm == "Dijkstra" else BLUE
    mc = YELLOW if r.weight_mode == "distance" else CYAN
    print(f"    {ac}{BOLD}{r.algorithm:<10}{RESET} {mc}{r.weight_mode}{RESET}")
    if r.found:
        print(f"      Path     : {WHITE}{r.path_str(graph)}{RESET}")
        print(f"      Distance : {r.total_distance:.2f}")
        print(f"      Time     : {r.total_time:.2f} min")
        print(f"      Explored : {r.nodes_explored}  |  Runtime : {r.runtime_ms:.3f} ms")
    else:
        print(f"      {RED}No path found{RESET}  ({r.nodes_explored} explored, {r.runtime_ms:.3f} ms)")
    print()


# =====================================================================
#  PNG EXPORT  (requires matplotlib)
# =====================================================================

def _try_import_matplotlib():
    try:
        import matplotlib
        matplotlib.use("Agg")
        import matplotlib.pyplot as plt
        from matplotlib.lines import Line2D
        return plt, Line2D
    except ImportError:
        return None, None


def _get_edge_label(edge, weight_mode, departure_hour=8):
    """Return the label to display on an edge based on weight mode."""
    if weight_mode == "distance":
        return f"{edge.distance:.0f}"
    elif weight_mode == "time":
        t = edge.get_travel_time(departure_hour)
        return f"{t:.0f}m"
    else:
        t = edge.get_travel_time(departure_hour)
        return f"{edge.distance:.0f} | {t:.0f}m"


def _get_edge_label_title(weight_mode):
    if weight_mode == "distance":
        return "Edge weights: distance"
    elif weight_mode == "time":
        return "Edge weights: travel time (min)"
    else:
        return "Edge weights: distance | time (min)"


def export_graph_png(graph, weight_mode="distance", departure_hour=8,
                     filename=None):
    """Export the full graph as a PNG with edge labels matching weight_mode."""
    plt, Line2D = _try_import_matplotlib()
    if plt is None:
        err("matplotlib not installed.  Run: pip install matplotlib")
        return None

    if filename is None:
        filename = f"graph_{weight_mode}.png"

    fig, ax = plt.subplots(figsize=(14, 10))
    ax.set_facecolor("#0f0f1a")
    fig.patch.set_facecolor("#0f0f1a")

    for edge in graph.edges.values():
        s = graph.nodes[edge.source]
        d = graph.nodes[edge.destination]
        dx, dy = d.x - s.x, d.y - s.y
        length = math.sqrt(dx*dx + dy*dy) or 1
        ox, oy = -dy/length * 0.6, dx/length * 0.6
        ax.annotate("",
            xy=(d.x + ox, d.y + oy),
            xytext=(s.x + ox, s.y + oy),
            arrowprops=dict(arrowstyle="-|>", color="#3a3a5c",
                            lw=1.0, mutation_scale=10))
        mx, my = (s.x + d.x) / 2 + ox, (s.y + d.y) / 2 + oy
        label = _get_edge_label(edge, weight_mode, departure_hour)
        ax.text(mx, my, label, fontsize=5.5,
                color="#5a5a7a", ha="center", va="center")

    for n in graph.nodes.values():
        circle = plt.Circle((n.x, n.y), 2.2, color="#e94560",
                             ec="white", lw=1.2, zorder=5)
        ax.add_patch(circle)
        ax.text(n.x, n.y + 4.5, n.name, fontsize=7, color="#cccccc",
                ha="center", va="bottom", fontweight="bold", zorder=6)
        ax.text(n.x, n.y, str(n.id), fontsize=6, color="white",
                ha="center", va="center", fontweight="bold", zorder=7)

    ax.set_aspect("equal")
    ax.margins(0.08)
    ax.set_title(f"Smart Path Finder — {graph.node_count()} nodes, "
                 f"{graph.edge_count()} edges\n"
                 f"{_get_edge_label_title(weight_mode)}",
                 color="white", fontsize=12, pad=12)
    ax.axis("off")
    fig.tight_layout()
    fig.savefig(filename, dpi=180, bbox_inches="tight")
    plt.close(fig)
    return filename


def export_query_png(graph, query, results, weight_mode, filename=None):
    """Export a query's paths overlaid on the graph as PNG.
    
    Edge labels reflect the chosen weight_mode.
    Filename includes weight_mode.
    """
    plt, Line2D = _try_import_matplotlib()
    if plt is None:
        err("matplotlib not installed.  Run: pip install matplotlib")
        return None

    if filename is None:
        src_name = graph.nodes[query["source"]].name
        dst_name = graph.nodes[query["destination"]].name
        safe = f"{src_name}_to_{dst_name}_{weight_mode}".replace(" ", "_")
        filename = f"{safe}.png"

    dep_hour = query.get("departure_hour", 8)

    fig, ax = plt.subplots(figsize=(14, 10))
    ax.set_facecolor("#0f0f1a")
    fig.patch.set_facecolor("#0f0f1a")

    avoid_n = query.get("avoid_nodes") or set()
    avoid_e = query.get("avoid_edges") or set()

    # Draw edges with weight labels
    for edge in graph.edges.values():
        s = graph.nodes[edge.source]
        d = graph.nodes[edge.destination]
        dx, dy = d.x - s.x, d.y - s.y
        length = math.sqrt(dx*dx + dy*dy) or 1
        ox, oy = -dy/length * 0.6, dx/length * 0.6

        edge_color = "#442222" if edge.id in avoid_e else "#252540"
        ax.annotate("",
            xy=(d.x + ox, d.y + oy),
            xytext=(s.x + ox, s.y + oy),
            arrowprops=dict(arrowstyle="-|>", color=edge_color,
                            lw=0.7, mutation_scale=8))
        mx, my = (s.x + d.x) / 2 + ox, (s.y + d.y) / 2 + oy
        label = _get_edge_label(edge, weight_mode, dep_hour)
        lbl_color = "#663333" if edge.id in avoid_e else "#444460"
        ax.text(mx, my, label, fontsize=5, color=lbl_color,
                ha="center", va="center")

    # Draw nodes
    for n in graph.nodes.values():
        colour = "#ff4444" if n.id in avoid_n else "#e94560"
        alpha = 0.35 if n.id in avoid_n else 1.0
        circle = plt.Circle((n.x, n.y), 2.2, color=colour, alpha=alpha,
                             ec="white", lw=1.0, zorder=5)
        ax.add_patch(circle)
        ax.text(n.x, n.y + 4.5, n.name, fontsize=6.5, color="#999999",
                ha="center", va="bottom", fontweight="bold", zorder=6)
        ax.text(n.x, n.y, str(n.id), fontsize=5.5, color="white",
                ha="center", va="center", fontweight="bold", zorder=7)

    # Mark avoided nodes
    for nid in avoid_n:
        n = graph.nodes[nid]
        ax.text(n.x, n.y, "✕", fontsize=14, color="#ff4444",
                ha="center", va="center", fontweight="bold", zorder=8)

    # Draw paths
    path_styles = [
        {"color": "#2ecc71", "lw": 3.0, "ls": "-",  "offset":  1.2},
        {"color": "#3498db", "lw": 2.5, "ls": "--", "offset": -1.2},
        {"color": "#f1c40f", "lw": 2.5, "ls": "-",  "offset":  2.8},
        {"color": "#e67e22", "lw": 2.0, "ls": "--", "offset": -2.8},
    ]
    legend_entries = []
    for ri, r in enumerate(results):
        if not r.found:
            continue
        st = path_styles[ri % len(path_styles)]
        label = (f"{r.algorithm} / {r.weight_mode} "
                 f"(d={r.total_distance:.0f}, t={r.total_time:.0f}m, "
                 f"explored={r.nodes_explored})")
        legend_entries.append((st["color"], st["ls"], label))

        for i in range(len(r.path) - 1):
            s = graph.nodes[r.path[i]]
            d = graph.nodes[r.path[i + 1]]
            dx, dy = d.x - s.x, d.y - s.y
            length = math.sqrt(dx*dx + dy*dy) or 1
            ox = -dy / length * st["offset"]
            oy = dx / length * st["offset"]
            ax.plot([s.x + ox, d.x + ox], [s.y + oy, d.y + oy],
                    color=st["color"], lw=st["lw"], ls=st["ls"],
                    alpha=0.85, zorder=4, solid_capstyle="round")

    # Legend
    handles = [Line2D([0], [0], color=c, ls=ls, lw=2.5, label=lb)
               for c, ls, lb in legend_entries]
    if handles:
        ax.legend(handles=handles, loc="upper left", fontsize=7,
                  facecolor="#1a1a2e", edgecolor="#333",
                  labelcolor="white", framealpha=0.9)

    # Title
    title = query.get("name", "Query")
    parts = [_get_edge_label_title(weight_mode)]
    if avoid_n:
        names = [graph.nodes[n].name for n in avoid_n]
        parts.append(f"avoid nodes: {names}")
    if avoid_e:
        parts.append(f"avoid edges: {avoid_e}")
    subtitle = "  |  ".join(parts)

    ax.set_title(f"{title}\n{subtitle}", color="white", fontsize=10, pad=12)
    ax.set_aspect("equal")
    ax.margins(0.08)
    ax.axis("off")
    fig.tight_layout()
    fig.savefig(filename, dpi=180, bbox_inches="tight")
    plt.close(fig)
    return filename


# =====================================================================
#  MENU ACTIONS
# =====================================================================

def show_graph_info(graph):
    header("GRAPH INFORMATION")
    print(f"  Nodes: {graph.node_count()}   Edges: {graph.edge_count()}")
    print()
    for n in sorted(graph.nodes.values(), key=lambda n: n.id):
        deg = len(graph.get_outgoing(n.id))
        print(f"    [{n.id:2d}] {n.name:<14s}  ({n.x:6.1f}, {n.y:6.1f})  deg={deg}")
    print()
    print(f"  {BOLD}Edges:{RESET}")
    for e in sorted(graph.edges.values(), key=lambda e: e.id):
        sn = graph.nodes[e.source].name
        dn = graph.nodes[e.destination].name
        print(f"    e{e.id:<3d} {sn:<12s} -> {dn:<12s}  "
              f"dist={e.distance:6.1f}  t@8h={e.get_travel_time(8):.1f}m")


def show_adjacency(graph):
    header("ADJACENCY LIST")
    for nid in sorted(graph.adjacency.keys()):
        node = graph.nodes[nid]
        edges = graph.adjacency[nid]
        targets = ", ".join(
            f"{graph.nodes[e.destination].name}(e{e.id})" for e in edges)
        print(f"  {BOLD}{node.name:<14s}{RESET} -> {targets or '(none)'}")


def run_demo(graph):
    header("RUNNING 4 DEMO QUERIES")
    wm = ask_weight_mode()
    info(f"Weight mode: {wm}")
    print()

    queries = get_demo_queries()
    all_results = []

    for qi, q in enumerate(queries):
        print(f"\n  {YELLOW}{BOLD}{q['name']}{RESET}")
        if q.get("avoid_nodes"):
            nms = [graph.nodes[n].name for n in q["avoid_nodes"]]
            print(f"  Avoid nodes: {nms}")
        if q.get("avoid_edges"):
            print(f"  Avoid edges: {q['avoid_edges']}")
        print(f"  Departure  : {q.get('departure_hour',8)}:00")
        sep()

        results = run_query(graph, q["source"], q["destination"],
                            q.get("avoid_nodes"), q.get("avoid_edges"),
                            q.get("departure_hour", 8),
                            weight_mode=wm)
        for r in results:
            print_result(r, graph)
        all_results.append((q, results, wm))

        # Auto-export each query PNG
        fname = f"query_{qi+1}_{wm}.png"
        f = export_query_png(graph, q, results, wm, filename=fname)
        if f:
            ok(f"Exported -> {f}")

    return all_results


def custom_query(graph):
    header("CUSTOM QUERY")
    print(f"  {DIM}Nodes:{RESET}")
    for n in sorted(graph.nodes.values(), key=lambda n: n.id):
        print(f"    {n.id}: {n.name}", end="   ")
        if (n.id + 1) % 5 == 0:
            print()
    print("\n")

    try:
        src = int(ask("Source node ID"))
        dst = int(ask("Destination node ID"))
        if src not in graph.nodes or dst not in graph.nodes:
            err("Invalid node ID"); return None

        an = ask("Avoid node IDs (comma-sep, or empty)")
        avoid_n = set(int(x) for x in an.split(",")) if an else None

        ae = ask("Avoid edge IDs (comma-sep, or empty)")
        avoid_e = set(int(x) for x in ae.split(",")) if ae else None

        hr = ask("Departure hour 0-23 (default 8)")
        dep = int(hr) if hr else 8

        wm = ask_weight_mode()

        al = ask("Algorithm [1]Dijkstra [2]A* [3]Both (default 3)")
        algos = {"1": ["dijkstra"], "2": ["astar"]}.get(al, ["dijkstra","astar"])

        sep()
        src_name = graph.nodes[src].name
        dst_name = graph.nodes[dst].name
        query = {"name": f"Custom: {src_name} -> {dst_name}",
                 "source": src, "destination": dst,
                 "avoid_nodes": avoid_n, "avoid_edges": avoid_e,
                 "departure_hour": dep}

        results = run_query(graph, src, dst, avoid_n, avoid_e, dep, algos,
                            weight_mode=wm)
        for r in results:
            print_result(r, graph)

        # Auto-export PNG
        safe = f"{src_name}_to_{dst_name}_{wm}".replace(" ", "_")
        fname = f"{safe}.png"
        f = export_query_png(graph, query, results, wm, filename=fname)
        if f:
            ok(f"Auto-exported -> {f}")

        return (query, results, wm)

    except (ValueError, KeyError) as e:
        err(f"Invalid input: {e}"); return None


def compare_table(graph):
    header("ALGORITHM COMPARISON")
    wm = ask_weight_mode()
    queries = get_demo_queries()
    print(f"\n  {'Query':<48s} {'Algo':<9s} {'Mode':<9s} "
          f"{'Explored':>8s} {'ms':>8s}")
    sep()
    for q in queries:
        results = run_query(graph, q["source"], q["destination"],
                            q.get("avoid_nodes"), q.get("avoid_edges"),
                            q.get("departure_hour", 8),
                            weight_mode=wm)
        for r in results:
            ac = GREEN if r.algorithm == "Dijkstra" else BLUE
            print(f"  {q['name'][:47]:<48s} {ac}{r.algorithm:<9s}{RESET} "
                  f"{r.weight_mode:<9s} {r.nodes_explored:>8d} "
                  f"{r.runtime_ms:>8.3f}")


def update_edge(graph):
    header("UPDATE EDGE TRAVEL TIMES")
    try:
        eid = int(ask("Edge ID"))
        edge = graph.edges.get(eid)
        if not edge:
            err(f"Edge {eid} not found"); return
        sn = graph.nodes[edge.source].name
        dn = graph.nodes[edge.destination].name
        info(f"e{eid}: {sn} -> {dn}  |  t@8h={edge.get_travel_time(8):.1f}m  "
             f"t@17h={edge.get_travel_time(17):.1f}m")
        factor = float(ask("Multiply all times by factor (e.g. 1.5)"))
        new = [round(t * factor, 1) for t in edge.travel_times]
        graph.update_edge_times(eid, new)
        ok(f"Updated! t@8h={edge.get_travel_time(8):.1f}m  "
           f"t@17h={edge.get_travel_time(17):.1f}m")
    except (ValueError, TypeError) as e:
        err(f"Invalid input: {e}")


def export_graph_only(graph):
    header("EXPORT GRAPH PNG")
    wm = ask_weight_mode()
    hr = ask("Departure hour for time labels 0-23 (default 8)")
    dep = int(hr) if hr else 8
    fname = f"graph_{wm}.png"
    f = export_graph_png(graph, weight_mode=wm, departure_hour=dep,
                         filename=fname)
    if f:
        ok(f"Exported -> {f}")


# =====================================================================
#  MAIN LOOP
# =====================================================================

def main():
    clear()
    banner()
    info("Generating dataset: 20 nodes, ~50 edges...")
    graph = generate_dataset(seed=42)
    ok(f"Graph ready: {graph.node_count()} nodes, {graph.edge_count()} edges")

    all_results = []

    while True:
        print(f"""
  {BOLD}MENU{RESET}
    {CYAN}1{RESET}  Show graph info
    {CYAN}2{RESET}  Show adjacency list
    {CYAN}3{RESET}  Run 4 demo queries   (+ auto-export PNGs)
    {CYAN}4{RESET}  Custom query          (+ auto-export PNG)
    {CYAN}5{RESET}  Compare algorithms (table)
    {CYAN}6{RESET}  Update edge travel times
    {CYAN}7{RESET}  Export graph-only PNG
    {CYAN}0{RESET}  Exit
""")
        ch = ask("Choose")

        if   ch == "1": show_graph_info(graph)
        elif ch == "2": show_adjacency(graph)
        elif ch == "3": all_results = run_demo(graph)
        elif ch == "4":
            r = custom_query(graph)
            if r: all_results.append(r)
        elif ch == "5": compare_table(graph)
        elif ch == "6": update_edge(graph)
        elif ch == "7": export_graph_only(graph)
        elif ch == "0":
            info("Goodbye!"); break
        else:
            err("Invalid choice")

        print()
        ask("Press Enter to continue")


if __name__ == "__main__":
    main()
