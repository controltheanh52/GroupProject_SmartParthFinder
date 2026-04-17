from minHeapAlgorithms import MinHeap

class dijkstra:
    def __init__(self):
        #using heap data structure (heap_distance)
        self.heap = MinHeap()
        
        #maybe we head heap_time

    def caculate_path(self, start_vertex, end_vertex, avoid_nodes = None, avoid_edges = None):
        if avoid_nodes is None:
            avoid_nodes = []
            
        if avoid_edges is None:
            avoid_edges = []
        
        start_vertex.min_distance = 0
        self.heap.push(start_vertex)
        
        
        while not self.heap.is_empty():
            #pop element wwith the lowest cost
            actual_vertex = self.heap.pop()

            if actual_vertex.visited:
                continue

            if actual_vertex == end_vertex:
                break

            #consider the neighbors
            for edge in actual_vertex.neighbors:
                start_node = edge.start_vertex
                target_node = edge.target_vertex

                # skip node
                if target_node.name in avoid_nodes:
                    continue

                # skip edge
                if (start_node.name, target_node.name) in avoid_edges or (target_node.name, start_node.name) in avoid_edges:
                    continue

                new_distance = start_node.min_distance + edge.distance

                if new_distance < target_node.min_distance:
                    target_node.min_distance = new_distance
                    target_node.predecessor = start_node

                    #update the heap
                    self.heap.push(target_node)

                    #update the heap cost value of one vertex (take the lower one)

            actual_vertex.visited = True

        print(f"Shortest path: {end_vertex.min_distance}")
        self.print_path(end_vertex)
        print()

    # this function is for caculate the time. For the fastest time path
    def caculate_time(self, start_vertex, start_time = 0, avoid_nodes = [], avoid_edges = []):
        start_vertex.min_distance = 0
        self.heap.push(start_vertex)
        
        
        while not self.heap.is_empty():
            #pop element wwith the lowest cost
            actual_vertex = self.heap.pop()
            

            if actual_vertex.visited:
                continue

            #consider the neighbors
            for edge in actual_vertex.neighbors:
                start_node = edge.start_vertex
                target_node = edge.target_vertex

                # skip node
                if target_node.name in avoid_nodes:
                    continue

                # skip edge
                if (start_node.name, target_node.name) in avoid_edges or (target_node.name, start_node.name) in avoid_edges:
                    continue
                
                ###Create a new algorithm for the time###
                # new_distance = start_node.min_distance + edge.distance

                # if new_distance < target_node.min_distance:
                #     target_node.min_distance = new_distance
                #     target_node.predecessor = start_node

                #     #update the heap
                #     self.heap.push(target_node)

                #     #update the heap cost value of one vertex (take the lower one)

            actual_vertex.visited = True

    #recursive function to to print out the path
    def print_path(self, vertex):
        if vertex is None:
            return

        self.print_path(vertex.predecessor)
        print(vertex.name, end=" ")