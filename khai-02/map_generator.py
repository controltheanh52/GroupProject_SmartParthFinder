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

# Region bounds (roughly a city-sized area, ~15km x 15km)
LAT_MIN = 10.720
LAT_MAX = 10.860
LON_MIN = 106.620
LON_MAX = 106.760

# Node generation
NUM_NODES = 2000
NUM_NEIGHBORHOODS = 20
NODES_PER_NEIGHBORHOOD_MIN = 70
NODES_PER_NEIGHBORHOOD_MAX = 130
MIN_NODE_SPACING_METERS = 50  # minimum distance between any two nodes

# Edge generation
KNN_K = 4                     # each node connects to k nearest neighbors
REGIONAL_RADIUS_M = 1500      # connect nodes within this radius with some probability
REGIONAL_PROBABILITY = 0.008  # probability of regional connection per pair in radius
HIGHWAY_COUNT_RATIO = 0.04    # fraction of nodes that get highway links
HIGHWAY_MIN_DIST_M = 5000     # minimum distance for highway edges
HIGHWAY_MAX_DIST_M = 15000    # maximum distance for highway edges
BIDIRECTIONAL_RATIO = 0.70    # fraction of edges that are two-way

# Speed profiles (km/h) by road type
SPEED_LOCAL = 30       # short edges (< 1 km)
SPEED_CITY = 50        # medium edges (1-5 km)
SPEED_HIGHWAY = 90     # long edges (> 5 km)

# Congestion multipliers per hour (index = hour 0-23)
CONGESTION_PROFILE = [
    0.82, 0.80, 0.80, 0.82, 0.85, 0.90,  # 0-5:  night (low traffic)
    1.10, 1.80, 2.20, 1.30, 1.10, 1.15,  # 6-11: morning rush peaks at 7-8
    1.30, 1.10, 1.05, 1.10, 1.20, 1.90,  # 12-17: afternoon, evening rush starts
    2.30, 1.50, 1.20, 1.10, 0.95, 0.88,  # 18-23: evening rush peaks at 18, tapers
]

# Congestion variation range (±)
CONGESTION_VARIATION = 0.12

# Random seed for reproducibility
SEED = 42

# =============================================================================
# Street name pools for realistic naming
# =============================================================================

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
# Helper functions
# =============================================================================

def _generate_node_name(index, rng):
    """Generate a meaningful node name."""
    # Roughly 40% intersection names, 30% place names, 30% street + suffix
    roll = rng.random()

    if roll < 0.40:
        # Street intersection: "Street A / Street B"
        s1 = rng.choice(STREET_NAMES)
        s2 = rng.choice(STREET_NAMES)
        while s2 == s1:
            s2 = rng.choice(STREET_NAMES)
        return f"{s1} / {s2}"
    elif roll < 0.70:
        # Place name: use from pool with index to guarantee uniqueness
        if index < len(PLACE_NAMES):
            return PLACE_NAMES[index]
        else:
            base = rng.choice(PLACE_NAMES).split()[0]
            suffix = rng.choice(PLACE_SUFFIXES)
            return f"{base} {suffix} {index}"
    else:
        # Street + suffix
        street = rng.choice(STREET_NAMES)
        suffix = rng.choice(PLACE_SUFFIXES)
        return f"{street} {suffix}"


def _enforce_unique_names(nodes):
    """Ensure all node names are unique by appending small suffixes where needed."""
    seen = {}
    for node in nodes:
        if node.name in seen:
            seen[node.name] += 1
            node.name = f"{node.name} #{seen[node.name]}"
        else:
            seen[node.name] = 0


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
        """
        Args:
            cell_size_deg: Cell size in degrees. Should be >= the minimum
                           spacing converted to degrees.
                           At lat ~10.8: 50m ≈ 0.00045 deg.
        """
        self._cell_size = cell_size_deg
        self._grid = {}  # dict[(row, col)] -> list of (lat, lon, node)

    def _cell(self, lat, lon):
        """Get the grid cell indices for a coordinate."""
        row = int(lat / self._cell_size)
        col = int(lon / self._cell_size)
        return row, col

    def insert(self, lat, lon, node):
        """Insert a node into the grid."""
        cell = self._cell(lat, lon)
        if cell not in self._grid:
            self._grid[cell] = []
        self._grid[cell].append((lat, lon, node))

    def check_min_spacing(self, lat, lon, min_dist_m):
        """
        Check if (lat, lon) is at least min_dist_m away from ALL existing
        nodes in the grid. Only examines the 9 neighboring cells.

        Returns:
            True if the point is far enough from all neighbors (safe to place).
            False if any existing node is too close.
        """
        row, col = self._cell(lat, lon)

        # Check 9 neighboring cells (the cell itself + 8 surrounding)
        for dr in (-1, 0, 1):
            for dc in (-1, 0, 1):
                cell = (row + dr, col + dc)
                if cell in self._grid:
                    for other_lat, other_lon, _ in self._grid[cell]:
                        dist = haversine(lat, lon, other_lat, other_lon)
                        if dist < min_dist_m:
                            return False
        return True


def _get_road_type(distance_m):
    """Classify road type by edge distance."""
    if distance_m < 1000:
        return 'local'
    elif distance_m < 5000:
        return 'city'
    else:
        return 'highway'


def _get_base_speed(road_type):
    """Get base speed in km/h for a road type."""
    if road_type == 'local':
        return SPEED_LOCAL
    elif road_type == 'city':
        return SPEED_CITY
    else:
        return SPEED_HIGHWAY


def _generate_travel_times(distance_m, rng):
    """
    Generate 24 hourly travel times for an edge (in minutes).

    Base time = distance / speed, then scaled by congestion profile per hour.
    """
    road_type = _get_road_type(distance_m)
    base_speed_kmh = _get_base_speed(road_type)

    # Base travel time in minutes
    base_time_min = (distance_m / 1000.0) / base_speed_kmh * 60.0

    times = []
    for hour in range(24):
        factor = CONGESTION_PROFILE[hour]
        # Add random variation
        variation = rng.uniform(-CONGESTION_VARIATION, CONGESTION_VARIATION)
        actual_factor = max(0.5, factor + variation)  # floor at 0.5x
        travel_time = base_time_min * actual_factor
        # Round to 2 decimal places
        times.append(round(travel_time, 2))

    return times


# =============================================================================
# Main generation functions
# =============================================================================

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

    # Spatial grid for guaranteed proximity checking.
    # Cell size: 50m ≈ 0.00045 degrees at this latitude.
    # Using 0.0005 deg (~55m) as cell size so each cell is slightly
    # larger than the minimum spacing — ensures the 9-cell neighborhood
    # check catches all possible violations.
    spatial_grid = SpatialGrid(cell_size_deg=0.0005)

    # Generate neighborhood centers
    lat_range = LAT_MAX - LAT_MIN
    lon_range = LON_MAX - LON_MIN

    centers = []
    for _ in range(NUM_NEIGHBORHOODS):
        c_lat = LAT_MIN + rng.uniform(0.05, 0.95) * lat_range
        c_lon = LON_MIN + rng.uniform(0.05, 0.95) * lon_range
        centers.append((c_lat, c_lon))

    # Distribute nodes among neighborhoods
    nodes_per_hood = []
    remaining = num_nodes
    for i in range(NUM_NEIGHBORHOODS):
        if i == NUM_NEIGHBORHOODS - 1:
            count = remaining
        else:
            count = rng.randint(NODES_PER_NEIGHBORHOOD_MIN, NODES_PER_NEIGHBORHOOD_MAX)
            count = min(count, remaining)
        nodes_per_hood.append(count)
        remaining -= count
        if remaining <= 0:
            break

    node_id = 0
    # Gaussian spread (in degrees, roughly 0.005 deg ≈ 500m)
    lat_spread = 0.008
    lon_spread = 0.008

    for hood_idx, count in enumerate(nodes_per_hood):
        c_lat, c_lon = centers[hood_idx]
        attempts = 0
        generated = 0

        while generated < count and attempts < count * 20:
            attempts += 1
            # Gaussian placement around center
            lat = rng.gauss(c_lat, lat_spread)
            lon = rng.gauss(c_lon, lon_spread)

            # Clamp to region bounds
            lat = max(LAT_MIN, min(LAT_MAX, lat))
            lon = max(LON_MIN, min(LON_MAX, lon))

            # Guaranteed spacing check via spatial grid (checks ALL nearby nodes)
            if not spatial_grid.check_min_spacing(lat, lon, MIN_NODE_SPACING_METERS):
                continue

            name = _generate_node_name(node_id, rng)
            node = Node(node_id, name, lat, lon)
            nodes.append(node)
            spatial_grid.insert(lat, lon, node)
            node_id += 1
            generated += 1

    _enforce_unique_names(nodes)
    print(f"  Generated {len(nodes)} nodes across {len(nodes_per_hood)} neighborhoods")
    return nodes


def _find_k_nearest(node_idx, all_nodes, k, rng):
    """Find the k nearest nodes to all_nodes[node_idx] by Haversine distance."""
    target = all_nodes[node_idx]
    distances = []

    for i, other in enumerate(all_nodes):
        if i == node_idx:
            continue
        dist = haversine(target.lat, target.lon, other.lat, other.lon)
        distances.append((dist, i))

    distances.sort(key=lambda x: x[0])
    return distances[:k]


def generate_edges(nodes, seed=SEED):
    """
    Generate directed edges connecting the given nodes.

    Strategy:
    1. K-nearest-neighbor backbone (k=4): each node connects to its nearest neighbors
    2. Regional connections: random edges within a radius with low probability
    3. Highway links: long-distance edges between distant nodes (~4%)
    4. ~70% bidirectional, ~30% unidirectional

    The graph is checked for connectivity and repaired if needed.

    Args:
        nodes: list[Node]
        seed: Random seed.

    Returns:
        list[Edge]
    """
    rng = random.Random(seed)
    n = len(nodes)
    edge_set = set()  # (from_id, to_id) to avoid duplicates
    edges = []

    print("  Phase 1: Building k-nearest-neighbor backbone...")

    # Phase 1: K-nearest-neighbor backbone
    for i in range(n):
        nearest = _find_k_nearest(i, nodes, KNN_K, rng)
        for dist, j in nearest:
            from_id = nodes[i].id
            to_id = nodes[j].id

            if (from_id, to_id) not in edge_set:
                times = _generate_travel_times(dist, rng)
                edge = Edge(from_id, to_id, round(dist, 2), times)
                edges.append(edge)
                edge_set.add((from_id, to_id))

            # Bidirectional?
            if rng.random() < BIDIRECTIONAL_RATIO and (to_id, from_id) not in edge_set:
                times_rev = _generate_travel_times(dist, rng)
                edge_rev = Edge(to_id, from_id, round(dist, 2), times_rev)
                edges.append(edge_rev)
                edge_set.add((to_id, from_id))

        if (i + 1) % 500 == 0:
            print(f"    Processed {i + 1}/{n} nodes...")

    print(f"  Phase 1 complete: {len(edges)} edges")

    # Phase 2: Regional connections (sparse random within radius)
    print("  Phase 2: Adding regional connections...")
    regional_count = 0
    # Use spatial bucketing for efficiency
    for i in range(n):
        for j in range(i + 1, n):
            dist = haversine(nodes[i].lat, nodes[i].lon, nodes[j].lat, nodes[j].lon)
            if dist < REGIONAL_RADIUS_M and rng.random() < REGIONAL_PROBABILITY:
                from_id = nodes[i].id
                to_id = nodes[j].id

                if (from_id, to_id) not in edge_set:
                    times = _generate_travel_times(dist, rng)
                    edge = Edge(from_id, to_id, round(dist, 2), times)
                    edges.append(edge)
                    edge_set.add((from_id, to_id))
                    regional_count += 1

                if rng.random() < BIDIRECTIONAL_RATIO and (to_id, from_id) not in edge_set:
                    times_rev = _generate_travel_times(dist, rng)
                    edge_rev = Edge(to_id, from_id, round(dist, 2), times_rev)
                    edges.append(edge_rev)
                    edge_set.add((to_id, from_id))
                    regional_count += 1

    print(f"  Phase 2 complete: +{regional_count} regional edges")

    # Phase 3: Highway links (long-distance)
    print("  Phase 3: Adding highway links...")
    highway_count = 0
    num_highway_nodes = int(n * HIGHWAY_COUNT_RATIO)
    highway_candidates = rng.sample(range(n), min(num_highway_nodes, n))

    for i in highway_candidates:
        # Find a distant node
        candidates = []
        for j in range(n):
            if i == j:
                continue
            dist = haversine(nodes[i].lat, nodes[i].lon, nodes[j].lat, nodes[j].lon)
            if HIGHWAY_MIN_DIST_M <= dist <= HIGHWAY_MAX_DIST_M:
                candidates.append((dist, j))

        if candidates:
            # Pick 1-2 highway connections
            num_links = rng.randint(1, 2)
            rng.shuffle(candidates)
            for dist, j in candidates[:num_links]:
                from_id = nodes[i].id
                to_id = nodes[j].id

                if (from_id, to_id) not in edge_set:
                    times = _generate_travel_times(dist, rng)
                    edge = Edge(from_id, to_id, round(dist, 2), times)
                    edges.append(edge)
                    edge_set.add((from_id, to_id))
                    highway_count += 1

                # Highways are almost always bidirectional
                if (to_id, from_id) not in edge_set:
                    times_rev = _generate_travel_times(dist, rng)
                    edge_rev = Edge(to_id, from_id, round(dist, 2), times_rev)
                    edges.append(edge_rev)
                    edge_set.add((to_id, from_id))
                    highway_count += 1

    print(f"  Phase 3 complete: +{highway_count} highway edges")

    # Phase 4: Connectivity repair
    print("  Phase 4: Verifying & repairing connectivity...")
    edges, edge_set = _ensure_connectivity(nodes, edges, edge_set, rng)

    print(f"  Total edges: {len(edges)}")
    return edges


def _ensure_connectivity(nodes, edges, edge_set, rng):
    """
    Ensure the graph is connected by finding disconnected components
    and adding bridge edges between them.
    """
    n = len(nodes)
    node_map = {node.id: node for node in nodes}

    # Build adjacency for BFS
    adj = {node.id: [] for node in nodes}
    for edge in edges:
        adj[edge.from_id].append(edge.to_id)

    # Find connected components via BFS
    visited = set()
    components = []

    for node in nodes:
        if node.id in visited:
            continue
        component = []
        queue = [node.id]
        visited.add(node.id)
        while queue:
            current = queue.pop(0)
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

    # Connect each component to the largest one
    components.sort(key=len, reverse=True)
    main_component = set(components[0])

    for comp_idx in range(1, len(components)):
        comp = components[comp_idx]
        # Find closest pair between this component and main component
        best_dist = float('inf')
        best_pair = None

        for node_id in comp:
            node_a = node_map[node_id]
            for main_id in main_component:
                node_b = node_map[main_id]
                dist = haversine(node_a.lat, node_a.lon, node_b.lat, node_b.lon)
                if dist < best_dist:
                    best_dist = dist
                    best_pair = (node_id, main_id)

        if best_pair:
            a_id, b_id = best_pair
            # Add bidirectional bridge
            for from_id, to_id in [(a_id, b_id), (b_id, a_id)]:
                if (from_id, to_id) not in edge_set:
                    times = _generate_travel_times(best_dist, rng)
                    edge = Edge(from_id, to_id, round(best_dist, 2), times)
                    edges.append(edge)
                    edge_set.add((from_id, to_id))
                    repair_count += 1

            main_component.update(comp)

    print(f"    Added {repair_count} bridge edges")
    return edges, edge_set


def generate_map(num_nodes=NUM_NODES, seed=SEED):
    """
    Generate a complete road network map.

    Args:
        num_nodes: Number of nodes to generate.
        seed: Random seed for reproducibility.

    Returns:
        Graph object with all nodes and edges.
    """
    print("=" * 60)
    print("Generating road network map...")
    print("=" * 60)

    nodes = generate_nodes(num_nodes, seed)
    edges = generate_edges(nodes, seed)

    graph = Graph()
    for node in nodes:
        graph.add_node(node)
    for edge in edges:
        graph.add_edge(edge)

    # Verify connectivity
    if graph.is_connected():
        print(f"\n  Graph is connected.")
    else:
        print(f"\n  WARNING: Graph is not fully connected!")

    print(f"\n  Final graph: {graph.node_count()} nodes, {graph.edge_count()} edges")
    avg_degree = graph.edge_count() / graph.node_count() if graph.node_count() > 0 else 0
    print(f"  Average out-degree: {avg_degree:.2f}")
    print("=" * 60)

    return graph


# =============================================================================
# Entry point for standalone generation
# =============================================================================

if __name__ == '__main__':
    import sys
    sys.path.insert(0, '.')
    from csv_io import save_graph

    graph = generate_map()
    save_graph(graph, 'data/nodes.csv', 'data/edges.csv')
    print("\nMap saved to data/nodes.csv and data/edges.csv")
