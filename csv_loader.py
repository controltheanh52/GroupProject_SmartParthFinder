import csv
from graph import Node

# load vertices
def load_vertices(vertices_file):
    nodes = {}

    with open(vertices_file, newline='') as f:
        reader = csv.reader(f)
        next(reader)
        for row in reader:
            name = row[0].strip()
            nodes[name] = Node(name)

    return nodes

# read the edge node
def load_edges(edges_file, nodes):
    with open(edges_file, newline='') as f:
        reader = csv.reader(f)
        next(reader)

        for row in reader:
            start, end, weight, bi, road_type = row

            start = start.strip()
            end = end.strip()
            weight = float(weight)

            bidirectional = bi.strip().lower() == "true"

            road_type = road_type.strip().lower()

            nodes[start].add_edge(weight, nodes[end], bidirectional, road_type)