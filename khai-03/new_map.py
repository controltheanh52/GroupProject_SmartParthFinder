"""
Smart Path Finder - New Map Generator

Instructions:
1. Run this file independently using: `python new_map.py`
2. It will generate a realistic road network based on the parameters in the 'Generator Configuration' section.
3. The result is saved as 'nodes.csv' and 'edges.csv' in the data/ directory.
4. After generation, run 'python solution.py' to query shortest paths on this map.
"""

import math
import random
import csv
import os

from solution import Node, Edge

# =============================================================================
# Configuration
# =============================================================================

# --- Region Bounds Configuration ---
# What it is: 
#   These 4 variables create a geographical "bounding box" (a rectangle) on the Earth.
#   Currently set to coordinates near Ho Chi Minh City (~15.5km x 15km area).
# Mechanism:
#   Every generated map node is given a random coordinate uniformly distributed 
#   within these min and max bounds. 
# How to use/modify:
#   1. Change Cities: Replace these with bounding coordinates of New York, London, etc.
#   2. Expand Map Size: Increase the difference between MIN and MAX. 
#      (Rule of thumb: 1 degree of latitude is roughly 111 km). 
#      If you double the gap to 0.280, you get a ~30x30km map.
#      *IMPORTANT*: If you expand the map significantly, remember to increase 
#      `NUM_NODES` below so the intersections aren't spread too far apart!

LAT_MIN = 10.720                              # Southernmost latitude boundary of the map
LAT_MAX = 10.860                              # Northernmost latitude boundary of the map
LON_MIN = 106.620                             # Westernmost longitude boundary of the map
LON_MAX = 106.760                             # Easternmost longitude boundary of the map

# --- Node Generation Configuration ---
# What it is:
#   Controls how many intersections (nodes) exist and how they are clustered.
# Mechanism:
#   The script places neighborhood "centers". Then it scatters nodes around these 
#   centers using a Gaussian distribution, ensuring no two nodes are closer than MIN_NODE_SPACING_METERS.
# How to use/modify:
#   - Increase NUM_NODES for a denser map (more intersections/roads).
#   - Increase NUM_NEIGHBORHOODS to distribute the city into more distinct separate hubs.
#   - Tweak NODES_PER_NEIGHBORHOOD constraints to control the density of each hub vs the connecting areas.

NUM_NODES = 5000                              # Total number of nodes (intersections/locations) to generate
NUM_NEIGHBORHOODS = 20                        # Number of dense clusters (neighborhoods) in the map
NODES_PER_NEIGHBORHOOD_MIN = 70               # Minimum number of nodes clustered within a single neighborhood
NODES_PER_NEIGHBORHOOD_MAX = 130              # Maximum number of nodes clustered within a single neighborhood
MIN_NODE_SPACING_METERS = 50                  # Minimum distance between any two nodes (prevents overlapping)

# --- Edge (Road) Generation Configuration ---
# What it is:
#   Dictates how the roads (edges) connect the intersections together.
# Mechanism:
#   Builds a basic network where each node connects to geographically closest K neighbors (KNN_K).
#   Adds some random mid-range links (REGIONAL_RADIUS/PROBABILITY) and long-distance links for highways.
#   Randomly decides if roads are one-way or two-way based on BIDIRECTIONAL_RATIO.
# How to use/modify:
#   - Increase KNN_K (e.g. to 5 or 6) to make the map much more interconnected (less dead-ends).
#   - Adjust HIGHWAY_COUNT_RATIO to add more/fewer long fast roads across the city.
#   - Set BIDIRECTIONAL_RATIO = 1.0 if you want every single road to be two-way.

KNN_K = 4                     # each node connects to k nearest neighbors
REGIONAL_RADIUS_M = 1500      # connect nodes within this radius with some probability
REGIONAL_PROBABILITY = 0.008  # probability of regional connection per pair in radius
HIGHWAY_COUNT_RATIO = 0.04    # fraction of nodes that get highway links
HIGHWAY_MIN_DIST_M = 5000     # minimum distance for highway edges
HIGHWAY_MAX_DIST_M = 15000    # maximum distance for highway edges
BIDIRECTIONAL_RATIO = 0.70    # fraction of edges that are two-way

# --- Speed Profiles Configuration ---
# What it is:
#   Specifies the base speed limits for roads depending on their length.
# Mechanism:
#   Short roads are deemed 'local' (slower), medium are 'city', long ones are 'highways'.
# How to use/modify:
#   - Adjust speeds to see how shortest-time path algorithms alter routes.

SPEED_LOCAL = 30       # short edges (< 1 km)
SPEED_CITY = 50        # medium edges (1-5 km)
SPEED_HIGHWAY = 90     # long edges (> 5 km)

# --- Congestion Multipliers Configuration ---
# What it is:
#   Simulates the 24-hour traffic conditions using multipliers.
# Mechanism:
#   The base travel time is multiplied by the factor for the respective hour (0-23).
#   Values > 1.0 mean traffic (slower), values < 1.0 mean clear roads.
#   CONGESTION_VARIATION adds random noise (±) to make it more realistic so not every road is identical.
# How to use/modify:
#   - Change the multipliers to create different rush hours (e.g. a massive spike at element 8 for 8 AM).

CONGESTION_PROFILE = [
    0.82, 0.80, 0.80, 0.82, 0.85, 0.90,  # 0-5:  night (low traffic)
    1.10, 1.80, 2.20, 1.30, 1.10, 1.15,  # 6-11: morning rush peaks at 7-8
    1.30, 1.10, 1.05, 1.10, 1.20, 1.90,  # 12-17: afternoon, evening rush starts
    2.30, 1.50, 1.20, 1.10, 0.95, 0.88,  # 18-23: evening rush peaks at 18, tapers
]

# Congestion variation range (±)
CONGESTION_VARIATION = 0.12

# --- Random Seed Configuration ---
# What it is/Mechanism: 
#   Fixes the RNG (Random Number Generator) so multiple runs produce the EXACT SAME map instead of randomizing every time.
# How to use/modify:
#   - Change this integer to any other number to generate a completely new, differently shaped but equally sized city.
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
PLACE_SUFFIXES = [
    "Junction", "Crossing", "Square", "Intersection",
    "Circle", "Corner", "Station", "Terminal",
    "Market", "Bridge", "Overpass", "Underpass",
]

# =============================================================================
# Spatial Grid & Handlers
# =============================================================================

class SpatialGrid:
    """
    Spatial hash grid for O(1) proximity checks.

    Divides the coordinate space into cells. To check if a new point is
    too close to any existing point, only the 9 neighboring cells need
    to be examined — guaranteeing correctness across ALL nodes, not just
    a heuristic subset.

    This is an internal data structure used only during generation.
    It does NOT affect the map layout — nodes remain randomly scattered.
    """
    def __init__(self, cell_size_deg):
        self.cell_size = cell_size_deg
        self.grid = {}

    def cell(self, lat, lon):
        return int(lat / self.cell_size), int(lon / self.cell_size)

    def insert(self, lat, lon, node):
        c = self.cell(lat, lon)
        if c not in self.grid:
            self.grid[c] = []
        self.grid[c].append((lat, lon, node))

    def check_min_spacing(self, lat, lon, min_dist_m):
        row, col = self.cell(lat, lon)
        for dr in (-1, 0, 1):
            for dc in (-1, 0, 1):
                c = (row + dr, col + dc)
                if c in self.grid:
                    for other_lat, other_lon, _ in self.grid[c]:
                        if haversine(lat, lon, other_lat, other_lon) < min_dist_m:
                            return False
        return True

def generate_node_name(index, rng):
    roll = rng.random()
    if roll < 0.40:
        s1 = rng.choice(STREET_NAMES)
        s2 = rng.choice(STREET_NAMES)
        while s2 == s1: 
            s2 = rng.choice(STREET_NAMES)
        return f"{s1} / {s2}"
    elif roll < 0.70:
        return f"{rng.choice(PLACE_NAMES)} {rng.choice(PLACE_SUFFIXES)} {index}"
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

def get_road_type(distance_m):
    if distance_m < 1000:
        return 'local'
    elif distance_m < 5000:
        return 'city'
    return 'highway'

def get_base_speed(road_type):
    if road_type == 'local': return SPEED_LOCAL
    if road_type == 'city': return SPEED_CITY
    return SPEED_HIGHWAY

def haversine(lat1, lon1, lat2, lon2):
    """
    Calculate the great-circle distance between two points on the Earth surface.
    
    Parameters:
        lat1, lon1: Latitude and longitude of the first point in decimal degrees.
        lat2, lon2: Latitude and longitude of the second point in decimal degrees.
        
    Returns:
        The distance between the two points in meters.
    """
    R = 6371000.0  # Earth radius in meters
    
    # Convert coordinates from degrees to radians for trigonometric functions
    phi1 = math.radians(lat1)
    phi2 = math.radians(lat2)
    delta_phi = math.radians(lat2 - lat1)
    delta_lambda = math.radians(lon2 - lon1)

    # Apply the Haversine formula
    a = math.sin(delta_phi / 2.0)**2 + \
        math.cos(phi1) * math.cos(phi2) * \
        math.sin(delta_lambda / 2.0)**2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    
    return R * c

def generate_travel_times(distance_m, rng):
    """
    Generate 24 hourly travel times for an edge (in minutes).

    Base time = distance / speed, then scaled by congestion profile per hour.
    """
    base_speed_kmh = get_base_speed(get_road_type(distance_m))
    base_time_min = (distance_m / 1000.0) / base_speed_kmh * 60.0
    times = []
    for hour in range(24):
        factor = max(0.5, CONGESTION_PROFILE[hour] + rng.uniform(-CONGESTION_VARIATION, CONGESTION_VARIATION))
        times.append(round(base_time_min * factor, 2))
    return times

def generate_nodes(num_nodes=NUM_NODES, seed=SEED):
    """
    Generate nodes in clustered neighborhoods with realistic coordinates.

    Uses a SpatialGrid for O(1) proximity checks that are GUARANTEED
    correct across all nodes (not a heuristic). The spatial grid is an
    internal lookup structure — it does not affect the map layout.

    The nodes are placed using a Gaussian cluster model:
    1. Create neighborhood centers spread across the region
    2. Each neighborhood gets a random number of nodes scattered around its center
    3. Minimum spacing (50m) is enforced via SpatialGrid — guaranteed no collisions

    Args:
        num_nodes: Target number of nodes.
        seed: Random seed.

    Returns:
        list[Node]
    """
    rng = random.Random(seed)
    nodes = []
    spatial_grid = SpatialGrid(cell_size_deg=0.0005)
    
    # 1. Establish neighborhood hubs
    centers = []
    for _ in range(NUM_NEIGHBORHOODS):
        c_lat = LAT_MIN + rng.uniform(0.05, 0.95) * (LAT_MAX - LAT_MIN)
        c_lon = LON_MIN + rng.uniform(0.05, 0.95) * (LON_MAX - LON_MIN)
        centers.append((c_lat, c_lon))
    
    nodes_per_hood = []
    remaining = num_nodes
    for i in range(NUM_NEIGHBORHOODS):
        count = remaining if i == NUM_NEIGHBORHOODS - 1 else min(rng.randint(NODES_PER_NEIGHBORHOOD_MIN, NODES_PER_NEIGHBORHOOD_MAX), remaining)
        nodes_per_hood.append(count)
        remaining -= count

    node_id = 0
    for hood_idx, count in enumerate(nodes_per_hood):
        c_lat, c_lon = centers[hood_idx]
        attempts, generated = 0, 0
        
        # Max attempts to prevent infinite loop if area is over-saturated
        while generated < count and attempts < count * 20:
            attempts += 1
            lat = max(LAT_MIN, min(LAT_MAX, rng.gauss(c_lat, 0.008)))
            lon = max(LON_MIN, min(LON_MAX, rng.gauss(c_lon, 0.008)))
            
            if not spatial_grid.check_min_spacing(lat, lon, MIN_NODE_SPACING_METERS):
                continue
                
            name = generate_node_name(node_id, rng)
            node = Node(node_id, name, lat, lon)
            nodes.append(node)
            spatial_grid.insert(lat, lon, node)
            node_id += 1
            generated += 1
            
        if generated < count:
            print(f"Warning: Saturated space! Capped neighborhood {hood_idx} at {generated}/{count} nodes due to 50m spacing.")
            
    enforce_unique_names(nodes)
    print(f"Generated {len(nodes)} nodes.")
    return nodes

def find_k_nearest(node_idx, all_nodes, k):
    """Helper to find the geographically closest K nodes using Haversine calculation."""
    target = all_nodes[node_idx]
    dist_list = []
    for i, other in enumerate(all_nodes):
        if i != node_idx:
            dist_list.append((haversine(target.lat, target.lon, other.lat, other.lon), i))
    dist_list.sort(key=lambda x: x[0])
    return dist_list[:k]

def generate_edges(nodes, seed=SEED):
    """
    Generate directed edges connecting the given nodes.

    Strategy:
    1. K-nearest-neighbor backbone (k=4): each node connects to its nearest neighbors
    2. Regional connections: random edges within a radius with low probability
    3. Highway links: long-distance edges between distant nodes (~4%)
    4. ~70% bidirectional, ~30% unidirectional

    The graph is checked for connectivity and repaired if needed using BFS 
    to guarantee there are no stranded neighborhoods.

    Args:
        nodes: list[Node]
        seed: Random seed.

    Returns:
        list[Edge]
    """
    rng = random.Random(seed)
    n = len(nodes)
    edge_set = set()
    edges = []

    print("Phase 1: KNN Backbone...")
    for i in range(n):
        for dist, j in find_k_nearest(i, nodes, KNN_K):
            if (nodes[i].id, nodes[j].id) not in edge_set:
                edges.append(Edge(nodes[i].id, nodes[j].id, round(dist, 2), generate_travel_times(dist, rng)))
                edge_set.add((nodes[i].id, nodes[j].id))
            if rng.random() < BIDIRECTIONAL_RATIO and (nodes[j].id, nodes[i].id) not in edge_set:
                edges.append(Edge(nodes[j].id, nodes[i].id, round(dist, 2), generate_travel_times(dist, rng)))
                edge_set.add((nodes[j].id, nodes[i].id))

    print("Phase 2: Regional links...")
    for i in range(n):
        for j in range(i+1, n):
            dist = haversine(nodes[i].lat, nodes[i].lon, nodes[j].lat, nodes[j].lon)
            if dist < REGIONAL_RADIUS_M and rng.random() < REGIONAL_PROBABILITY:
                if (nodes[i].id, nodes[j].id) not in edge_set:
                    edges.append(Edge(nodes[i].id, nodes[j].id, round(dist, 2), generate_travel_times(dist, rng)))
                    edge_set.add((nodes[i].id, nodes[j].id))
                if rng.random() < BIDIRECTIONAL_RATIO and (nodes[j].id, nodes[i].id) not in edge_set:
                    edges.append(Edge(nodes[j].id, nodes[i].id, round(dist, 2), generate_travel_times(dist, rng)))
                    edge_set.add((nodes[j].id, nodes[i].id))

    print("Phase 3: Highway links...")
    candidates = rng.sample(range(n), min(int(n * HIGHWAY_COUNT_RATIO), n))
    for i in candidates:
        farways = [(haversine(nodes[i].lat, nodes[i].lon, nodes[j].lat, nodes[j].lon), j) for j in range(n) if i != j]
        farways = [x for x in farways if HIGHWAY_MIN_DIST_M <= x[0] <= HIGHWAY_MAX_DIST_M]
        if farways:
            rng.shuffle(farways)
            for dist, j in farways[:rng.randint(1, 2)]:
                if (nodes[i].id, nodes[j].id) not in edge_set:
                    edges.append(Edge(nodes[i].id, nodes[j].id, round(dist, 2), generate_travel_times(dist, rng)))
                    edge_set.add((nodes[i].id, nodes[j].id))
                if (nodes[j].id, nodes[i].id) not in edge_set:
                    edges.append(Edge(nodes[j].id, nodes[i].id, round(dist, 2), generate_travel_times(dist, rng)))
                    edge_set.add((nodes[j].id, nodes[i].id))

    print("Phase 4: Ensure Connectivity...")
    adj = {n.id: [] for n in nodes}
    for e in edges: 
        adj[e.from_id].append(e.to_id)
        
    visited = set()
    comps = []
    
    for n_obj in nodes:
        if n_obj.id not in visited:
            comp, q = [], [n_obj.id]
            visited.add(n_obj.id)
            while q:
                curr = q.pop(0)
                comp.append(curr)
                for nbr in adj[curr]:
                    if nbr not in visited:
                        visited.add(nbr)
                        q.append(nbr)
            comps.append(comp)

    if len(comps) > 1:
        comps.sort(key=len, reverse=True)
        main_comp = set(comps[0])
        node_map = {n_obj.id: n_obj for n_obj in nodes}
        
        for i in range(1, len(comps)):
            best_dist, best_pair = float('inf'), None
            for a_id in comps[i]:
                na = node_map[a_id]
                for b_id in main_comp:
                    nb = node_map[b_id]
                    dist = haversine(na.lat, na.lon, nb.lat, nb.lon)
                    if dist < best_dist:
                        best_dist, best_pair = dist, (a_id, b_id)
            if best_pair:
                a_id, b_id = best_pair
                for fid, tid in [(a_id, b_id), (b_id, a_id)]:
                    if (fid, tid) not in edge_set:
                        edges.append(Edge(fid, tid, round(best_dist, 2), generate_travel_times(best_dist, rng)))
                        edge_set.add((fid, tid))
                main_comp.update(comps[i])

    print(f"Generated {len(edges)} edges.")
    return edges

def save_csvs(nodes, edges):
    out_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'data')
    os.makedirs(out_dir, exist_ok=True)
    
    nodes_path = os.path.join(out_dir, 'nodes.csv')
    with open(nodes_path, 'w', newline='', encoding='utf-8') as f:
        w = csv.writer(f)
        w.writerow(['id', 'name', 'lat', 'lon'])
        for n in sorted(nodes, key=lambda x: x.id):
            w.writerow([n.id, n.name, f"{n.lat:.6f}", f"{n.lon:.6f}"])
            
    edges_path = os.path.join(out_dir, 'edges.csv')
    with open(edges_path, 'w', newline='', encoding='utf-8') as f:
        w = csv.writer(f)
        w.writerow(['from_id', 'to_id', 'distance'] + [f't{h}' for h in range(24)])
        for e in edges:
            w.writerow([e.from_id, e.to_id, f"{e.distance:.2f}"] + [f"{t:.2f}" for t in e.travel_times])

def main():
    print("========================================")
    print("Generating new map data...")
    print("========================================")
    nodes = generate_nodes()
    edges = generate_edges(nodes)
    save_csvs(nodes, edges)
    print("========================================")
    print("Success: data/nodes.csv and data/edges.csv generated.")
    print("You can now run 'python solution.py' to explore the map.")
    print("========================================")

if __name__ == '__main__':
    main()
