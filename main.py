from graph import Node
from queries_loader import load_queries
from dijkstraDistanceAlgorithm import dijkstra

#Main file
#testing

#Step 1 - create vertex
nodeA = Node("A")
nodeB = Node("B")
nodeC = Node("C")
nodeD = Node("D")
nodeE = Node("E")
nodeF = Node("F")
nodeG = Node("G")
nodeH = Node("H")

nodes = {
    "A": nodeA,
    "B": nodeB,
    "C": nodeC,
    "D": nodeD,
    "E": nodeE,
    "F": nodeF,
    "G": nodeG,
    "H": nodeH
}

queries = load_queries("SmartPathFinder/queries.json")

#Step 2 - add the edges and weight
nodeA.add_edge(6, nodeB)
nodeA.add_edge(9, nodeD)
nodeA.add_edge(10, nodeC)

nodeB.add_edge(5, nodeD)
nodeB.add_edge(16, nodeE)
nodeB.add_edge(13, nodeF)

nodeC.add_edge(6, nodeD)
nodeC.add_edge(5, nodeH)
nodeC.add_edge(21, nodeG)

nodeD.add_edge(8, nodeF)
nodeD.add_edge(7, nodeH)

nodeE.add_edge(10, nodeG)

nodeF.add_edge(4, nodeE)
nodeF.add_edge(12, nodeG)

nodeH.add_edge(2, nodeF)
nodeH.add_edge(14, nodeG)


for q in queries:
    print("\n======================================================")

    start_node = nodes[q["source"]]
    end_node = nodes[q["destination"]]

    avoid_nodes = q["avoid_nodes"]
    avoid_edges = [tuple(edge) for edge in q.get("avoid_edges", [])]

    # reset graph before run
    for node in nodes.values():
        node.visited = False
        node.min_distance = float("inf")
        node.predecessor = None

    algorithm = dijkstra()

    # caculate the dijkstra
    algorithm.caculate(start_node, avoid_nodes = avoid_nodes, avoid_edges = avoid_edges)

    print(f"Source node: {q['source']}")
    print(f"Destination node: {q['destination']}")
    if avoid_nodes == []:
        print(f"Avoid nodes: EMPTY!!!")
    else:
        print(f"Avoid nodes: {avoid_nodes}")

    if avoid_edges == []:
        print(f"Avoid edges: EMPTY!!!")
    else:
        print(f"Avoid edges: {avoid_edges}")

    algorithm.get_shortest_path(end_node)