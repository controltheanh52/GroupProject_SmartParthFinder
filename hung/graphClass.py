class Edge:
    def __init__(self, distance, timeArr):
        self.distance = distance # km
        self.timeArr = timeArr # minutes

class Vertex:
    def __init__(self, name):
        self.name = name
        self.min_distance = float("inf")
        self.predecessor = None
        self.visited = False 
        
    def reset(self):
        self.min_distance = float("inf")
        self.predecessor = None
        self.visited = False 
        
    def __lt__(self, other_node):
        return self.min_distance < other_node.min_distance
    
class Graph:
    def __init__(self):
        self.vertices = {} # for vertex reference
        self.adjList = {} # Dictionary of dictionary { Vertex1: {Neighbor1: Edge, Neighbor2: Edge},
                            #                          Vertex2: {Neighbor1: Edge, Neighbor2: Edge}  }
        
    def add_vertex(self, name):
        if name not in self.vertices:
            new_vertex = Vertex(name)
            self.vertices[name] = new_vertex
            self.adjList[new_vertex] = {}
        return self.vertices[name]
    
    # accept vertex objects    
    def add_edge(self, u, v, distance, timeArr, bidirectional=False):
        # failsafe
        if self.adjList[u][v]: return
        if u not in self.adjList: self.adjList[u] = {}
        if v not in self.adjList: self.adjList[v] = {}
         
        self.adjList[u][v] = Edge(distance, timeArr)
        
        if bidirectional:
            if v not in self.adjList:
                self.adjList[v] = {}
            self.adjList[v][u] = Edge(distance, timeArr)
            
    def reset(self):
        for vertex in self.vertices.values():
            vertex.reset()
            
     