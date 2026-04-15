from graph import Node
from queries_loader import load_queries
from SmartPathFinder.dijkstraAlgorithm import dijkstra

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

#Step 2 - add the edges and distance cost
#using distance with float(Kilometer) and time(minutes), at the end, convert the time to hours and minutes
nodeA.add_edge(60.0, nodeB)
nodeA.add_edge(9.5, nodeD)
nodeA.add_edge(10.0, nodeC)

nodeB.add_edge(5.0, nodeD)
nodeB.add_edge(16.0, nodeE)
nodeB.add_edge(13.0, nodeF)

nodeC.add_edge(6.0, nodeD)
nodeC.add_edge(5.0, nodeH)
nodeC.add_edge(21.0, nodeG)

nodeD.add_edge(8.0, nodeF)
nodeD.add_edge(7.0, nodeH)

nodeE.add_edge(10.0, nodeG)

nodeF.add_edge(4.0, nodeE)
nodeF.add_edge(12.0, nodeG)

nodeH.add_edge(2.0, nodeF)
nodeH.add_edge(14.0, nodeG)


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
    algorithm.caculate_path(start_node, avoid_nodes = avoid_nodes, avoid_edges = avoid_edges)
    
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

    #Add a new workflow to print out the fastest time path