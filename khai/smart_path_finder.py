"""
smart_path_finder.py
====================
Core module — Node, Edge, Graph, MinHeap, Dijkstra, A*, dataset generator.
No external libraries.
"""

import math
import time
import random


# =====================================================================
#  DATA STRUCTURES
# =====================================================================

class Node:
    def __init__(self, node_id, x, y, name=None):
        self.id = node_id
        self.x = x
        self.y = y
        self.name = name if name else f"N{node_id}"

    def __repr__(self):
        return f"Node({self.id}, '{self.name}')"


class Edge:
    def __init__(self, edge_id, source, destination, distance, travel_times):
        self.id = edge_id
        self.source = source
        self.destination = destination
        self.distance = distance
        self.travel_times = travel_times  # 24 hourly values (minutes)

    def get_travel_time(self, hour):
        return self.travel_times[int(hour) % 24]

    def __repr__(self):
        return f"Edge(e{self.id}: {self.source}->{self.destination})"


class MinHeap:
    """Binary min-heap with lazy deletion (no external libs)."""

    def __init__(self):
        self.heap = []
        self._counter = 0

    def __len__(self):
        return len(self.heap)

    def is_empty(self):
        return len(self.heap) == 0

    def insert(self, node_id, priority):
        entry = (priority, self._counter, node_id)
        self._counter += 1
        self.heap.append(entry)
        self._bubble_up(len(self.heap) - 1)

    def extract_min(self):
        if self.is_empty():
            return None, None
        self._swap(0, len(self.heap) - 1)
        priority, _, node_id = self.heap.pop()
        if self.heap:
            self._bubble_down(0)
        return node_id, priority

    def _swap(self, i, j):
        self.heap[i], self.heap[j] = self.heap[j], self.heap[i]

    def _bubble_up(self, i):
        while i > 0:
            p = (i - 1) // 2
            if self.heap[i][0] < self.heap[p][0]:
                self._swap(i, p)
                i = p
            else:
                break

    def _bubble_down(self, i):
        n = len(self.heap)
        while True:
            smallest = i
            left, right = 2 * i + 1, 2 * i + 2
            if left < n and self.heap[left][0] < self.heap[smallest][0]:
                smallest = left
            if right < n and self.heap[right][0] < self.heap[smallest][0]:
                smallest = right
            if smallest != i:
                self._swap(i, smallest)
                i = smallest
            else:
                break


class Graph:
    """Directed graph — adjacency list + edge dict."""

    def __init__(self):
        self.nodes = {}       # node_id -> Node
        self.adjacency = {}   # node_id -> [Edge, ...]
        self.edges = {}       # edge_id -> Edge

    def add_node(self, node_id, x, y, name=None):
        node = Node(node_id, x, y, name)
        self.nodes[node_id] = node
        self.adjacency[node_id] = []
        return node

    def add_edge(self, edge_id, source, destination, distance, travel_times):
        edge = Edge(edge_id, source, destination, distance, travel_times)
        self.adjacency[source].append(edge)
        self.edges[edge_id] = edge
        return edge

    def get_outgoing(self, node_id):
        return self.adjacency.get(node_id, [])

    def euclidean_distance(self, id_a, id_b):
        a, b = self.nodes[id_a], self.nodes[id_b]
        return math.sqrt((a.x - b.x) ** 2 + (a.y - b.y) ** 2)

    def update_edge_times(self, edge_id, new_times):
        if edge_id in self.edges:
            self.edges[edge_id].travel_times = new_times

    def node_count(self):
        return len(self.nodes)

    def edge_count(self):
        return len(self.edges)


# =====================================================================
#  WEIGHT FUNCTIONS
# =====================================================================

def distance_weight(edge, current_time=None):
    return edge.distance

def time_weight(edge, current_time=0):
    return edge.get_travel_time(int(current_time) % 24)


# =====================================================================
#  PATH RESULT
# =====================================================================

class PathResult:
    def __init__(self, path, total_distance, total_time, nodes_explored,
                 runtime_ms, algorithm, weight_mode):
        self.path = path
        self.total_distance = total_distance
        self.total_time = total_time
        self.nodes_explored = nodes_explored
        self.runtime_ms = runtime_ms
        self.algorithm = algorithm
        self.weight_mode = weight_mode

    @property
    def found(self):
        return self.path is not None and len(self.path) > 0

    def path_str(self, graph):
        if not self.found:
            return "No path found"
        return " -> ".join(graph.nodes[nid].name for nid in self.path)

    def summary(self, graph):
        lines = [f"  [{self.algorithm} / {self.weight_mode}]"]
        if self.found:
            lines.append(f"    Path     : {self.path_str(graph)}")
            lines.append(f"    Distance : {self.total_distance:.2f}")
            lines.append(f"    Time     : {self.total_time:.2f} min")
            lines.append(f"    Explored : {self.nodes_explored} nodes")
            lines.append(f"    Runtime  : {self.runtime_ms:.3f} ms")
        else:
            lines.append(f"    NO PATH FOUND  (explored {self.nodes_explored} nodes)")
        return "\n".join(lines)


# =====================================================================
#  HELPERS
# =====================================================================

def _reconstruct(prev, source, destination):
    path, current = [], destination
    while current is not None:
        path.append(current)
        if current == source:
            break
        current = prev.get(current)
    if not path or path[-1] != source:
        return None
    path.reverse()
    return path


def _compute_path_costs(graph, path, departure_hour=8):
    total_dist, total_time = 0.0, 0.0
    current_time = float(departure_hour)
    for i in range(len(path) - 1):
        for edge in graph.get_outgoing(path[i]):
            if edge.destination == path[i + 1]:
                total_dist += edge.distance
                t = edge.get_travel_time(int(current_time) % 24)
                total_time += t
                current_time += t / 60.0
                break
    return total_dist, total_time


# =====================================================================
#  DIJKSTRA
# =====================================================================

def dijkstra(graph, source, destination, weight_fn,
             avoid_nodes=None, avoid_edges=None, departure_hour=8):
    avoid_nodes = avoid_nodes or set()
    avoid_edges = avoid_edges or set()
    weight_mode = "distance" if weight_fn is distance_weight else "time"

    t0 = time.perf_counter()
    dist = {source: 0.0}
    prev = {source: None}
    visited = set()
    nodes_explored = 0
    arrival = {source: float(departure_hour) * 60}

    heap = MinHeap()
    heap.insert(source, 0.0)

    while not heap.is_empty():
        current, cost = heap.extract_min()
        if current in visited:
            continue
        visited.add(current)
        nodes_explored += 1
        if current == destination:
            break

        curr_min = arrival.get(current, departure_hour * 60)
        for edge in graph.get_outgoing(current):
            if edge.id in avoid_edges:
                continue
            nb = edge.destination
            if nb in avoid_nodes or nb in visited:
                continue
            w = weight_fn(edge, curr_min / 60.0)
            new_cost = cost + w
            if nb not in dist or new_cost < dist[nb]:
                dist[nb] = new_cost
                prev[nb] = current
                arrival[nb] = curr_min + time_weight(edge, curr_min / 60.0)
                heap.insert(nb, new_cost)

    elapsed = (time.perf_counter() - t0) * 1000
    path = _reconstruct(prev, source, destination)
    td, tt = _compute_path_costs(graph, path, departure_hour) if path else (0, 0)
    return PathResult(path, td, tt, nodes_explored, elapsed, "Dijkstra", weight_mode)


# =====================================================================
#  A*
# =====================================================================

def astar(graph, source, destination, weight_fn,
          avoid_nodes=None, avoid_edges=None, departure_hour=8):
    avoid_nodes = avoid_nodes or set()
    avoid_edges = avoid_edges or set()
    weight_mode = "distance" if weight_fn is distance_weight else "time"

    t0 = time.perf_counter()

    # Admissible heuristic
    max_speed = 0.0
    for edge in graph.edges.values():
        for t in edge.travel_times:
            if t > 0:
                s = edge.distance / t
                if s > max_speed:
                    max_speed = s
    if max_speed == 0:
        max_speed = 1.0

    def h(nid):
        d = graph.euclidean_distance(nid, destination)
        return d / max_speed if weight_mode == "time" else d

    g_cost = {source: 0.0}
    prev = {source: None}
    visited = set()
    nodes_explored = 0
    arrival = {source: float(departure_hour) * 60}

    heap = MinHeap()
    heap.insert(source, h(source))

    while not heap.is_empty():
        current, _ = heap.extract_min()
        if current in visited:
            continue
        visited.add(current)
        nodes_explored += 1
        if current == destination:
            break

        curr_min = arrival.get(current, departure_hour * 60)
        for edge in graph.get_outgoing(current):
            if edge.id in avoid_edges:
                continue
            nb = edge.destination
            if nb in avoid_nodes or nb in visited:
                continue
            w = weight_fn(edge, curr_min / 60.0)
            new_g = g_cost[current] + w
            if nb not in g_cost or new_g < g_cost[nb]:
                g_cost[nb] = new_g
                prev[nb] = current
                arrival[nb] = curr_min + time_weight(edge, curr_min / 60.0)
                heap.insert(nb, new_g + h(nb))

    elapsed = (time.perf_counter() - t0) * 1000
    path = _reconstruct(prev, source, destination)
    td, tt = _compute_path_costs(graph, path, departure_hour) if path else (0, 0)
    return PathResult(path, td, tt, nodes_explored, elapsed, "A*", weight_mode)


# =====================================================================
#  QUERY RUNNER
# =====================================================================

def run_query(graph, source, destination, avoid_nodes=None, avoid_edges=None,
              departure_hour=8, algorithms=None, weight_mode="both"):
    """
    Run pathfinding query.
    
    weight_mode: "distance", "time", or "both"
    """
    if algorithms is None:
        algorithms = ["dijkstra", "astar"]

    if weight_mode == "distance":
        wfns = [distance_weight]
    elif weight_mode == "time":
        wfns = [time_weight]
    else:
        wfns = [distance_weight, time_weight]

    results = []
    for algo in algorithms:
        fn = dijkstra if algo == "dijkstra" else astar
        for wfn in wfns:
            results.append(fn(graph, source, destination, wfn,
                              avoid_nodes, avoid_edges, departure_hour))
    return results


# =====================================================================
#  DATASET GENERATOR
# =====================================================================

def _gen_travel_times(distance):
    """
    Generate 24 travel time values (minutes) for an edge.

    Each value = the total minutes to traverse this edge if you START
    during that hour.  e.g. travel_times[8] = 30 means starting any
    time between 8:00–8:59 costs 30 minutes.

    Longer roads naturally take more minutes.  Rush hours (7-9, 17-19)
    are slower; night hours (0-5) are faster.

    A random per-edge speed factor (0.6–1.4) ensures that some roads
    are fast relative to their distance and others are slow, so the
    shortest-distance path and shortest-time path can differ.
    """
    # Per-edge speed factor: some roads are congested, some are clear
    edge_factor = random.uniform(0.4, 1.6)

    # Base minutes-per-unit-distance at each hour
    hourly_rates = [
        0.35, 0.32, 0.30, 0.30, 0.32, 0.38,   # 0-5:  night, fast
        0.45, 0.70, 0.75, 0.60, 0.55, 0.52,    # 6-11: morning rush peak@8
        0.55, 0.52, 0.50, 0.52, 0.58, 0.72,    # 12-17: afternoon, peak@17
        0.70, 0.60, 0.52, 0.45, 0.40, 0.38,    # 18-23: evening taper
    ]
    times = []
    for rate in hourly_rates:
        t = distance * rate * edge_factor * random.uniform(0.90, 1.10)
        times.append(round(max(t, 1.0), 1))     # at least 1 minute
    return times


def generate_dataset(seed=42):
    random.seed(seed)
    g = Graph()

    names = [
        "Downtown",  "Market",    "University","Hospital",  "Airport",
        "Stadium",   "Mall",      "Library",   "Museum",    "Park",
        "Station",   "Harbor",    "Factory",   "School",    "Clinic",
        "Theater",   "Plaza",     "Church",    "Bridge",    "Tower",
    ]
    for idx in range(20):
        row, col = divmod(idx, 5)
        x = col * 25 + random.uniform(-8, 8)
        y = row * 25 + random.uniform(-8, 8)
        g.add_node(idx, x, y, names[idx])

    eid = [0]
    added = set()

    def bidi(s, d):
        if (s, d) in added:
            return
        dist = round(g.euclidean_distance(s, d), 1)
        g.add_edge(eid[0], s, d, dist, _gen_travel_times(dist)); added.add((s,d)); eid[0]+=1
        g.add_edge(eid[0], d, s, dist, _gen_travel_times(dist)); added.add((d,s)); eid[0]+=1

    def oneway(s, d):
        if (s, d) in added:
            return
        dist = round(g.euclidean_distance(s, d), 1)
        g.add_edge(eid[0], s, d, dist, _gen_travel_times(dist)); added.add((s,d)); eid[0]+=1

    # Horizontal links
    for s, d in [(0,1),(1,2),(2,3),(3,4),(5,6),(6,7),(7,8),
                 (10,11),(11,12),(13,14),(15,16),(16,17),(18,19)]:
        bidi(s, d)
    # Vertical links
    for s, d in [(0,5),(1,6),(3,8),(4,9),(5,10),(7,12),
                 (8,13),(9,14),(10,15),(12,17),(13,18),(14,19)]:
        bidi(s, d)
    # Diagonal shortcuts (longer distance but potentially faster travel)
    for s, d in [(0,6),(1,7),(2,8),(6,12),(7,13),(11,17),(12,18)]:
        bidi(s, d)
    # One-way shortcuts
    oneway(6, 12)
    oneway(8, 14)
    oneway(5, 16)

    return g


def get_demo_queries():
    return [
        {"name": "Q1: Basic (Downtown -> Tower)",
         "source": 0, "destination": 19,
         "avoid_nodes": None, "avoid_edges": None, "departure_hour": 8},
        {"name": "Q2: Avoid nodes (Downtown -> Tower, avoid Mall & Museum)",
         "source": 0, "destination": 19,
         "avoid_nodes": {6, 8}, "avoid_edges": None, "departure_hour": 8},
        {"name": "Q3: Avoid edges (Market -> Church, avoid edge 4,5)",
         "source": 1, "destination": 17,
         "avoid_nodes": None, "avoid_edges": {4, 5}, "departure_hour": 17},
        {"name": "Q4: Avoid both (Airport -> Plaza, avoid Hospital & edge 10,11)",
         "source": 4, "destination": 16,
         "avoid_nodes": {3}, "avoid_edges": {10, 11}, "departure_hour": 12},
    ]
