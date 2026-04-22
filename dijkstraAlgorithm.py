from minHeapAlgorithms import MinHeap
from math import *
class Dijkstra:
    def __init__(self):
        self.heap = MinHeap()

    
    
    def calculate_time_for_path(self, end_vertex, start_time):
        path = []
        current = end_vertex

        # lấy path từ end về start
        while current is not None:
            path.append(current)
            current = current.predecessor

        path.reverse()

        current_time = start_time
        total_time = 0

        for i in range(len(path) - 1):
            current_node = path[i]
            next_node = path[i + 1]

            # tìm edge
            for edge in current_node.neighbors:
                if edge.target_vertex == next_node:

                    hour = int(current_time) % 24
                    travel_time = edge.time_list[hour]

                    total_time += travel_time
                    current_time += travel_time / 60
                    break

        return total_time, current_time

    def calculate_distance_path(self, start_vertex, end_vertex, start_time = 0, avoid_vertices=None, avoid_edges=None):
        
        if avoid_vertices is None:
            avoid_vertices = []

        if avoid_edges is None:
            avoid_edges = []

        #start node with min_distance = 0
        start_vertex.min_distance = 0

        #find the heuristic between start and end vertex frist
        start_vertex.f = 0

        self.heap.push(start_vertex)

        while not self.heap.is_empty():
            current = self.heap.pop()

            # #debug
            # print(f"Visiting: {current.name}")

            if current.visited:
                continue
            
            #break if the current == to the end node
            if current == end_vertex:
                break
            
            for edge in current.neighbors:
                start = edge.start_vertex
                neighbor = edge.target_vertex

                # skip the avoid nodes
                if neighbor.name in avoid_vertices:
                    continue
                
                #skipe the avoide vertex
                if (start.name, neighbor.name) in avoid_edges or (neighbor.name, start.name) in avoid_edges:
                    continue
                
                #g cost of the distance
                g = start.min_distance + edge.distance
                
                #compare the f and neighbor of f 
                if g < neighbor.min_distance:
                    #update the min distance with g
                    neighbor.min_distance = g

                    #update the new f to the neighbor
                    neighbor.f = g

                    #set the predecessor of neighbor vertex is start node
                    neighbor.predecessor = start

                    self.heap.push(neighbor)

            current.visited = True

        print("\n======== SHORTEST PATH ========")
        print("result: ", end = " ")
        self.print_path(end_vertex)

        print(f"\nShortest path: {end_vertex.min_distance}")

        total_time, arrival_time = self.calculate_time_for_path(end_vertex, start_time)

        hours, minutes = self.format_time(total_time)

        print(f"\nTravel time on this path: {total_time:.2f} minutes")
        print(f"Time travel: {hours} hour(s) {minutes} minute(s)")
        print(f"Arrival time: {self.format_clock_time(arrival_time)}")

    def calculate_time_path(self, start_vertex, end_vertex, start_time = 0, avoid_vertices=None, avoid_edges=None):

        if avoid_vertices is None:
            avoid_vertices = []

        if avoid_edges is None:
            avoid_edges = []

        start_vertex.min_time = 0
        start_vertex.current_time = start_time
        start_vertex.f = 0

        self.heap.push(start_vertex)

        while not self.heap.is_empty():
            current = self.heap.pop()

            if current.visited:
                continue

            if current == end_vertex:
                break

            for edge in current.neighbors:
                neighbor = edge.target_vertex

                if neighbor.name in avoid_vertices:
                    continue

                if (current.name, neighbor.name) in avoid_edges or (neighbor.name, current.name) in avoid_edges:
                    continue

                # TIME LOGIC
                current_time = current.current_time
                hour = int(current_time) % 24

                travel_time = edge.time_list[hour] #minutes travel time
                new_time = current_time + (travel_time / 60)

                g = current.min_time + travel_time   #using min time

                if g < neighbor.min_time:
                    neighbor.min_time = g
                    neighbor.current_time = new_time
                    neighbor.f = g
                    neighbor.predecessor = current

                    self.heap.push(neighbor)

            current.visited = True

        hours, minutes = self.format_time(end_vertex.min_time)

        print("\n===== SHORTEST TIME PATH =====")
        print("result: ", end = " ")
        self.print_path(end_vertex)

        print(f"\nTotal time: {end_vertex.min_time:.2f} minutes")
        print(f"Time travel: {hours} hour(s) {minutes} minute(s)")
        print(f"Arrival: {self.format_clock_time(end_vertex.current_time)}")
        print()

    def format_time(self, total_minutes):
        hours = int(total_minutes // 60)
        minutes = int(total_minutes % 60)
        return hours, minutes
    def format_clock_time(self, time_float):
        hours = int(time_float)
        minutes = int((time_float - hours) * 60)
        return f"{hours}:{minutes:02d}"

    def print_path(self, vertex):
        if vertex is None:
            return

        self.print_path(vertex.predecessor)
        print(vertex.name, end=" ")
