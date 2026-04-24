"""
Realistic road network generator for the Smart Path Finder.

Generates a directed weighted graph with:
- ~2,000 nodes placed in clustered neighborhoods (not a grid)
- ~5,000-6,000 directed edges (k-NN backbone + regional + highway links)
- Real-world-style names from configurable street/place pools
- Haversine distances from lat/lon coordinates
- 24-hour travel time profiles with congestion patterns

The generated graph satisfies:
- Triangle inequality (inherent from Euclidean/Haversine geometry)
- No collapsed coordinates (minimum spacing enforced)
- Connectivity (all nodes reachable via BFS verification + repair)

All randomness uses a seeded RNG for reproducibility.
"""

import math
import random

from graph import Node, Edge, Graph, haversine


# =============================================================================
# Configuration
# =============================================================================

LAT_MIN, LAT_MAX = 10.720, 10.860
LON_MIN, LON_MAX = 106.620, 106.760

NUM_NODES = 2000
NUM_NEIGHBORHOODS = 20
NODES_PER_NEIGHBORHOOD_MIN = 70
NODES_PER_NEIGHBORHOOD_MAX = 130
MIN_NODE_SPACING_METERS = 50  

KNN_K = 4                     
REGIONAL_RADIUS_M = 1500      
REGIONAL_PROBABILITY = 0.008  
HIGHWAY_COUNT_RATIO = 0.04    
HIGHWAY_MIN_DIST_M = 5000     
HIGHWAY_MAX_DIST_M = 15000    
BIDIRECTIONAL_RATIO = 0.70    

SPEED_LOCAL, SPEED_CITY, SPEED_HIGHWAY = 30, 50, 90 

CONGESTION_PROFILE = [
    0.82, 0.80, 0.80, 0.82, 0.85, 0.90,  
    1.10, 1.80, 2.20, 1.30, 1.10, 1.15,  
    1.30, 1.10, 1.05, 1.10, 1.20, 1.90,  
    2.30, 1.50, 1.20, 1.10, 0.95, 0.88,  
]
CONGESTION_VARIATION = 0.12
SEED = 42

STREET_NAMES = [
    "Nguyen Hue", "Le Loi", "Tran Hung Dao", "Pasteur", "Hai Ba Trung",
    "Dong Khoi", "Nam Ky Khoi Nghia", "Nguyen Thi Minh Khai", "Le Duan",
    "Vo Van Tan", "Nguyen Dinh Chieu", "Ly Tu Trong", "Ton Duc Thang",
    "Pham Ngu Lao", "Bui Vien", "De Tham", "Le Thanh Ton", "Mac Thi Buoi",
    "Nguyen Trai", "Cach Mang Thang Tam", "Ly Chinh Thang", "Ba Thang Hai",
    "Nguyen Van Cu", "Tran Quang Khai", "Phan Dang Luu", "Hoang Sa",
    "Truong Sa", "Dien Bien Phu", "Vo Thi Sau", "Nguyen Thi Dieu",
    "Le Van Sy", "Nguyen Van Troi", "Phan Xich Long", "Huynh Van Banh",
    "Ngo Duc Ke", "Nguyen Cong Tru", "Ho Tung Mau", "Pham Viet Chanh",
    "Tran Quoc Thao", "Nguyen Phi Khanh", "Le Quy Don", "Nguyen Binh Khiem",
    "Xo Viet Nghe Tinh", "Phan Van Tri", "Nguyen Thai Hoc", "Pham Hong Thai",
    "Le Lai", "Yersin", "Co Bac", "Co Giang",
    "Ben Van Don", "Nguyen Tat Thanh", "Hoang Dieu", "Ton That Thuyet",
    "Le Hong Phong", "Hung Vuong", "Tran Phu", "An Duong Vuong",
    "Lac Long Quan", "Au Co", "Luy Ban Bich", "Tan Hoa Dong",
    "Quang Trung", "Phan Van Han", "Bui Dinh Tuy", "Nguyen Xien",
    "Le Van Viet", "Do Xuan Hop", "Pham Van Dong", "Nguyen Van Linh",
    "Truong Chinh", "Cong Hoa", "Hoang Van Thu", "Ut Tich",
    "Tan Son Nhi", "Au Co", "Le Trong Tan", "Tay Thanh",
    "Nguyen Son", "Tan Ky Tan Quy", "Bau Cat", "Hong Bang",
]

PLACE_NAMES = [
    "Ben Thanh", "Saigon Central", "Cho Lon", "District 1 Hub",
    "Phu Nhuan Center", "Binh Thanh Gate", "Thu Duc North", "Go Vap Junction",
    "Tan Binh Plaza", "District 3 Park", "District 5 Market", "District 7 South",
    "District 10 Center", "Phu My Hung", "Thu Thiem", "Binh Tan West",
    "Tan Phu North", "District 4 Port", "An Phu East", "Thanh Da Island",
    "Saigon Zoo Area", "Reunification Palace", "Opera House", "City Hall",
    "Notre Dame Area", "War Museum Area", "Jade Emperor Area", "Turtle Lake",
    "Tao Dan Park", "Le Van Tam Park", "Gia Dinh Park", "Dam Sen Park",
    "Binh Quoi Village", "Starlight Bridge", "Saigon Pearl", "Landmark Tower",
    "Tan Son Nhat Gate", "Phu Lam Roundabout", "Hang Xanh Junction", "Bay Hien Junction",
]

PLACE_SUFFIXES = ["Junction", "Crossing", "Square", "Intersection", "Circle", "Corner", "Station", "Terminal", "Market", "Bridge", "Overpass", "Underpass"]

# =============================================================================
# Helper functions
# =============================================================================

def generate_node_name(index, rng):
    roll = rng.random()
    if roll < 0.40:
        s1, s2 = rng.choice(STREET_NAMES), rng.choice(STREET_NAMES)
        while s2 == s1:
            s2 = rng.choice(STREET_NAMES)
        return f"{s1} / {s2}"
    elif roll < 0.70:
        if index < len(PLACE_NAMES):
            return PLACE_NAMES[index]
        return f"{rng.choice(PLACE_NAMES).split()[0]} {rng.choice(PLACE_SUFFIXES)} {index}"
    else:
        return f"{rng.choice(STREET_NAMES)} {rng.choice(PLACE_SUFFIXES)}"


def enforce_unique_names(nodes):
    seen = {}
    for node in nodes:
        if node.name in seen:
            seen[node.name] += 1
            node.name = f"{node.name} #{seen[node.name]}"
        else:
            seen[node.name] = 0


class SpatialGrid:
    def __init__(self, cell_size_deg):
        self.cell_size = cell_size_deg
        self.grid = {} 

    def cell(self, lat, lon):
        return int(lat / self.cell_size), int(lon / self.cell_size)

    def insert(self, lat, lon, node):
        self.grid.setdefault(self.cell(lat, lon), []).append((lat, lon, node))

    def check_min_spacing(self, lat, lon, min_dist_m):
        row, col = self.cell(lat, lon)
        for dr in (-1, 0, 1):
            for dc in (-1, 0, 1):
                for other_lat, other_lon, _ in self.grid.get((row + dr, col + dc), []):
                    if haversine(lat, lon, other_lat, other_lon) < min_dist_m:
                        return False
        return True


def get_road_speed(distance_m):
    if distance_m < 1000: return SPEED_LOCAL
    if distance_m < 5000: return SPEED_CITY
    return SPEED_HIGHWAY


def generate_travel_times(distance_m, rng):
    base_time_min = (distance_m / 1000.0) / get_road_speed(distance_m) * 60.0
    return [round(base_time_min * max(0.5, f + rng.uniform(-CONGESTION_VARIATION, CONGESTION_VARIATION)), 2) 
            for f in CONGESTION_PROFILE]


# =============================================================================
# Edge Management Helpers (DRY approach)
# =============================================================================

def try_add_edge(from_id, to_id, dist, rng, edges, edge_set):
    """Helper to avoid duplicating edge creation code everywhere."""
    if (from_id, to_id) not in edge_set:
        times = generate_travel_times(dist, rng)
        edges.append(Edge(from_id, to_id, round(dist, 2), times))
        edge_set.add((from_id, to_id))
        return 1
    return 0


def try_add_bidirectional(from_id, to_id, dist, rng, edges, edge_set, force_bidi=False):
    """Helper for adding two-way paths if RNG allows it."""
    count = try_add_edge(from_id, to_id, dist, rng, edges, edge_set)
    if force_bidi or rng.random() < BIDIRECTIONAL_RATIO:
        count += try_add_edge(to_id, from_id, dist, rng, edges, edge_set)
    return count


# =============================================================================
# Main generation functions
# =============================================================================

def generate_nodes(num_nodes=NUM_NODES, seed=SEED):
    rng = random.Random(seed)
    nodes = []
    spatial_grid = SpatialGrid(cell_size_deg=0.0005)

    centers = [(LAT_MIN + rng.uniform(0.05, 0.95) * (LAT_MAX - LAT_MIN),
                LON_MIN + rng.uniform(0.05, 0.95) * (LON_MAX - LON_MIN)) 
               for _ in range(NUM_NEIGHBORHOODS)]

    nodes_per_hood = []
    remaining = num_nodes
    for i in range(NUM_NEIGHBORHOODS):
        count = remaining if i == NUM_NEIGHBORHOODS - 1 else min(rng.randint(NODES_PER_NEIGHBORHOOD_MIN, NODES_PER_NEIGHBORHOOD_MAX), remaining)
        nodes_per_hood.append(count)
        remaining -= count
        if remaining <= 0: break

    node_id = 0
    for hood_idx, count in enumerate(nodes_per_hood):
        c_lat, c_lon = centers[hood_idx]
        attempts, generated = 0, 0

        while generated < count and attempts < count * 20:
            attempts += 1
            lat = max(LAT_MIN, min(LAT_MAX, rng.gauss(c_lat, 0.008)))
            lon = max(LON_MIN, min(LON_MAX, rng.gauss(c_lon, 0.008)))

            if not spatial_grid.check_min_spacing(lat, lon, MIN_NODE_SPACING_METERS):
                continue

            node = Node(node_id, generate_node_name(node_id, rng), lat, lon)
            nodes.append(node)
            spatial_grid.insert(lat, lon, node)
            node_id += 1
            generated += 1

    enforce_unique_names(nodes)
    print(f"  Generated {len(nodes)} nodes across {len(nodes_per_hood)} neighborhoods")
    return nodes


def find_k_nearest(node_idx, all_nodes, k, rng):
    target = all_nodes[node_idx]
    distances = [(haversine(target.lat, target.lon, other.lat, other.lon), i) 
                 for i, other in enumerate(all_nodes) if i != node_idx]
    distances.sort(key=lambda x: x[0])
    return distances[:k]


def generate_edges(nodes, seed=SEED):
    rng = random.Random(seed)
    n = len(nodes)
    edge_set = set()  
    edges = []

    print("  Phase 1: Building k-nearest-neighbor backbone...")
    for i in range(n):
        for dist, j in find_k_nearest(i, nodes, KNN_K, rng):
            try_add_bidirectional(nodes[i].id, nodes[j].id, dist, rng, edges, edge_set)
        if (i + 1) % 500 == 0:
            print(f"    Processed {i + 1}/{n} nodes...")

    print(f"  Phase 1 complete: {len(edges)} edges")

    print("  Phase 2: Adding regional connections...")
    regional_count = 0
    for i in range(n):
        for j in range(i + 1, n):
            dist = haversine(nodes[i].lat, nodes[i].lon, nodes[j].lat, nodes[j].lon)
            if dist < REGIONAL_RADIUS_M and rng.random() < REGIONAL_PROBABILITY:
                regional_count += try_add_bidirectional(nodes[i].id, nodes[j].id, dist, rng, edges, edge_set)

    print(f"  Phase 2 complete: +{regional_count} regional edges")

    print("  Phase 3: Adding highway links...")
    highway_count = 0
    highway_candidates = rng.sample(range(n), min(int(n * HIGHWAY_COUNT_RATIO), n))

    for i in highway_candidates:
        candidates = [(haversine(nodes[i].lat, nodes[i].lon, nodes[j].lat, nodes[j].lon), j) 
                      for j in range(n) if i != j]
        valid_cands = [c for c in candidates if HIGHWAY_MIN_DIST_M <= c[0] <= HIGHWAY_MAX_DIST_M]
        
        if valid_cands:
            rng.shuffle(valid_cands)
            for dist, j in valid_cands[:rng.randint(1, 2)]:
                # Highways are almost always bidirectional
                highway_count += try_add_bidirectional(nodes[i].id, nodes[j].id, dist, rng, edges, edge_set, force_bidi=True)

    print(f"  Phase 3 complete: +{highway_count} highway edges")

    print("  Phase 4: Verifying & repairing connectivity...")
    edges, edge_set = ensure_connectivity(nodes, edges, edge_set, rng)

    print(f"  Total edges: {len(edges)}")
    return edges


def ensure_connectivity(nodes, edges, edge_set, rng):
    n = len(nodes)
    node_map = {node.id: node for node in nodes}
    adj = {node.id: [] for node in nodes}
    for edge in edges:
        adj[edge.from_id].append(edge.to_id)

    visited = set()
    components = []

    for node in nodes:
        if node.id in visited:
            continue
        component = []
        queue = [node.id]
        head = 0  # O(1) queue iteration instead of O(N) list.pop(0)
        visited.add(node.id)
        
        while head < len(queue):
            current = queue[head]
            head += 1
            component.append(current)
            for neighbor in adj.get(current, []):
                if neighbor not in visited:
                    visited.add(neighbor)
                    queue.append(neighbor)
        components.append(component)

    if len(components) == 1:
        print(f"    Graph is connected (1 component)")
        return edges, edge_set

    print(f"    Found {len(components)} components, adding bridge edges...")
    repair_count = 0
    components.sort(key=len, reverse=True)
    main_component = set(components[0])

    for comp in components[1:]:
        best_dist, best_pair = float('inf'), None
        for node_id in comp:
            node_a = node_map[node_id]
            for main_id in main_component:
                node_b = node_map[main_id]
                dist = haversine(node_a.lat, node_a.lon, node_b.lat, node_b.lon)
                if dist < best_dist:
                    best_dist, best_pair = dist, (node_id, main_id)

        if best_pair:
            # Force bidirectional bridge connecting components
            repair_count += try_add_bidirectional(best_pair[0], best_pair[1], best_dist, rng, edges, edge_set, force_bidi=True)
            main_component.update(comp)

    print(f"    Added {repair_count} bridge edges")
    return edges, edge_set


def generate_map(num_nodes=NUM_NODES, seed=SEED):
    print("=" * 60)
    print("Generating road network map...")
    print("=" * 60)

    nodes = generate_nodes(num_nodes, seed)
    edges = generate_edges(nodes, seed)

    graph = Graph()
    for node in nodes: graph.add_node(node)
    for edge in edges: graph.add_edge(edge)

    if graph.is_connected():
        print(f"\n  Graph is connected.")
    else:
        print(f"\n  WARNING: Graph is not fully connected!")

    print(f"\n  Final graph: {graph.node_count()} nodes, {graph.edge_count()} edges")
    print(f"  Average out-degree: {graph.edge_count() / graph.node_count() if graph.node_count() > 0 else 0:.2f}")
    print("=" * 60)

    return graph


if __name__ == '__main__':
    import sys
    sys.path.insert(0, '.')
    from csv_io import save_graph

    graph = generate_map()
    save_graph(graph, 'data/nodes.csv', 'data/edges.csv')
    print("\nMap saved to data/nodes.csv and data/edges.csv")