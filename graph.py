class Edge:
    #add a new parameter for the time list
    def __init__(self, distance, start_vertex, target_vertex):
        #the cost between 2 vertex
        self.distance = distance

        #Create a new variable for time

        #start vertex
        self.start_vertex = start_vertex

        #the end of vertex
        self.target_vertex = target_vertex

#node class
class Node:
    def __init__(self, name):
        self.name = name
        self.visited = False

        #previous node that we come to this node
        self.predecessor = None

        #neighbors of the current node, need to know how many neighbor off currrent node
        self.neighbors = []

        #for other node, for the start node will be 0
        self.min_distance = float("inf")

        #Create a self time for the node

    #compare 2 nodes
    def __lt__(self, other_node):
        return self.min_distance < other_node.min_distance
    
    #maybe we need to create a new function add_edge(time) or still using this one
    
    def add_edge(self, weight, destination_vertex):
        #create an edge
        edge = Edge(weight, self, destination_vertex)
        #append to neighbor, edge between currrent vertex and destionation vertex 
        self.neighbors.append(edge)

        # reversed edge
        reverse_edge = Edge(weight, destination_vertex, self)
        destination_vertex.neighbors.append(reverse_edge)
