class Edge:
    #add a new parameter for the time list
    def __init__(self, distance, start_vertex, target_vertex, road_type = "normal"):
        #the cost between 2 vertex
        self.distance = distance

        self.road_type = road_type
        #Create a new variable for time
        self.time_list = self.generate_time_list(distance)

        #start vertex
        self.start_vertex = start_vertex

        #the end of vertex
        self.target_vertex = target_vertex
        print(f"[DEBUG] {start_vertex.name}->{target_vertex.name}: {road_type}")

    def generate_time_list(self, distance):
        time_list = []

        for hour in range(24):

            if self.road_type == "highway":
                if 7 <= hour <= 9 or 16 <= hour <= 19:
                    factor = 1.2   # little bit slow
                else:
                    factor = 0.8   # faster

            elif self.road_type == "city":
                if 7 <= hour <= 9 or 16 <= hour <= 19:
                    factor = 3.5   # very slow
                else:
                    factor = 1.5   # little bit slow

            else:
                if 7 <= hour <= 9 or 16 <= hour <= 19:
                    factor = 2     # little bit slow
                else:
                    factor = 1     # normal

            time_list.append(distance * factor)

        return time_list

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

        ## this variable for time
        self.min_time = float("inf")
        self.current_time = float("inf")

        #using for the A* ( f(n) = g(n) (distance) + h(n)(euclidean distancce of coordinate) )
        self.f = float("inf")

        #Create a self time for the node

    #compare 2 nodes
    def __lt__(self, other_node):
        return self.f < other_node.f
    
    #maybe we need to create a new function add_edge(time) or still using this one
    
    def add_edge(self, weight, destination_vertex, bidirectional = False , road_type = "normal"):
        #create an edge
        edge = Edge(weight, self, destination_vertex, road_type)
        #append to neighbor, edge between currrent vertex and destionation vertex 
        self.neighbors.append(edge)

        if bidirectional == True:
            # reversed edge
            reverse_edge = Edge(weight, destination_vertex, self, road_type)
            destination_vertex.neighbors.append(reverse_edge)
