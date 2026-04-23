from minHeapAlgorithms import MinHeap
from math import *

class Dijkstra:
    def __init__(self):
        self.heap = MinHeap()

    def calculate_time_for_path(self, end_vertex, start_time):
        # Reconstruct path from end to start using predecessor
        path = []
        current = end_vertex

        # build path backwards
        while current is not None:
            path.append(current)
            current = current.predecessor

        # reverse to get correct order (start -> end)
        path.reverse()

        current_time = start_time
        total_time = 0

        # iterate through each edge in the path
        for i in range(len(path) - 1):
            current_node = path[i]
            next_node = path[i + 1]

            # get edge directly from dictionary (O(1))
            edge = current_node.neighbors.get(next_node)

            if edge:
                hour = int(current_time) % 24
                travel_time = edge.time_list[hour]

                total_time += travel_time
                current_time += travel_time / 60

        return total_time, current_time

    def calculate_distance_path(self, start_vertex, end_vertex, start_time=0, avoid_vertices=None, avoid_edges=None):
        self.heap = MinHeap()

        if avoid_vertices is None:
            avoid_vertices = []
        if avoid_edges is None:
            avoid_edges = []

        # Convert to set for fast lookup O(1)
        avoid_vertices = set(avoid_vertices)
        avoid_edges = set(tuple(edge) for edge in avoid_edges)

        if start_vertex.name in avoid_vertices:
            print("Start node is in avoid list → cannot start")
            return

        if end_vertex.name in avoid_vertices:
            print("End node is in avoid list → no valid path")
            return
        
        # Initialize start node
        start_vertex.min_distance = 0

        # Push (distance, node) into heap
        self.heap.push((0, start_vertex))

        while not self.heap.is_empty():
            current_dist, current = self.heap.pop()

            # Lazy decrease-key:
            # If this is an outdated entry, skip it
            if current_dist > current.min_distance:
                continue

            if current.visited:
                continue
            current.visited = True

            # Stop if we reach destination
            if current == end_vertex:
                break

            # Explore neighbors
            for neighbor, edge in current.neighbors.items():

                # Skip avoided nodes
                if neighbor.name in avoid_vertices:
                    continue

                # Skip avoided edges
                if (current.name, neighbor.name) in avoid_edges or (neighbor.name, current.name) in avoid_edges:
                    continue

                # Calculate new distance
                new_distance = current.min_distance + edge.distance

                # Relaxation step
                if new_distance < neighbor.min_distance:
                    neighbor.min_distance = new_distance
                    neighbor.predecessor = current

                    # Push updated value into heap
                    self.heap.push((new_distance, neighbor))

        if end_vertex.min_distance == float("inf"):
            print("\n======== SHORTEST PATH ========")
            print("No path found")
            return


        # Output results
        print("\n======== SHORTEST PATH ========")
        print("result: ", end=" ")
        self.print_path(end_vertex)

        print(f"\nShortest path: {end_vertex.min_distance}")

        total_time, arrival_time = self.calculate_time_for_path(end_vertex, start_time)
        hours, minutes = self.format_time(total_time)

        print(f"\nTravel time on this path: {total_time:.2f} minutes")
        print(f"Time travel: {hours} hour(s) {minutes} minute(s)")
        print(f"Arrival time: {self.format_clock_time(arrival_time)}")

    def calculate_time_path(self, start_vertex, end_vertex, start_time=0, avoid_vertices=None, avoid_edges=None):
        
        self.heap = MinHeap()

        if avoid_vertices is None:
            avoid_vertices = []
        if avoid_edges is None:
            avoid_edges = []

        if start_vertex.name in avoid_vertices:
            print("Start node is in avoid list → cannot start")
            return

        if end_vertex.name in avoid_vertices:
            print("End node is in avoid list → no valid path")
            return

        # Convert to set for fast lookup
        avoid_vertices = set(avoid_vertices)
        avoid_edges = set(tuple(edge) for edge in avoid_edges)

        # Initialize start node
        start_vertex.min_time = 0
        start_vertex.current_time = start_time

        # Push (time, node)
        self.heap.push((0, start_vertex))

        while not self.heap.is_empty():
            current_dist, current = self.heap.pop()

            # Lazy decrease-key check
            if current_dist > current.min_time:
                continue

            if current.visited:
                continue
            current.visited = True

            if current == end_vertex:
                break

            for neighbor, edge in current.neighbors.items():

                if neighbor.name in avoid_vertices:
                    continue

                if (current.name, neighbor.name) in avoid_edges or (neighbor.name, current.name) in avoid_edges:
                    continue

                # Time-dependent logic
                current_time = current.current_time
                hour = int(current_time) % 24

                travel_time = edge.time_list[hour]
                new_time = current_time + (travel_time / 60)

                new_total_time = current.min_time + travel_time

                # Relaxation step
                if new_total_time < neighbor.min_time:
                    neighbor.min_time = new_total_time
                    neighbor.current_time = new_time
                    neighbor.predecessor = current

                    self.heap.push((new_total_time, neighbor))

        if end_vertex.min_time == float("inf"):
            print("\n======== SHORTEST PATH ========")
            print("No path found")
            return
        
        hours, minutes = self.format_time(end_vertex.min_time)

        print("\n===== SHORTEST TIME PATH =====")
        print("result: ", end=" ")
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