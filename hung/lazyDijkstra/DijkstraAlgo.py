from lazyDijkstra.lazyMinHeap import MinHeap

# current best
def lazy_dijkstra(graph, start_vertex, end_vertex, avoid_nodes, avoid_edges):

    # shorten
    adjList = graph.adjList
    
    # main section
    heap = MinHeap()
    start_vertex.min_distance = 0
    heap.insert(start_vertex)
    
    while not heap.is_empty():
        
        curr_vertex = heap.pop()
        # Early exit
        if curr_vertex == end_vertex:
            break
        if curr_vertex.visited == True:
            continue

        curr_vertex.visited = True
        
        for neighbor, edge in adjList[curr_vertex].items():
            if neighbor.visited == True or neighbor in avoid_nodes \
                or edge in avoid_edges:
                continue
            
            curr_dist = curr_vertex.min_distance + edge.distance
            if curr_dist < neighbor.min_distance:
                neighbor.min_distance = curr_dist
                neighbor.predecessor = curr_vertex
                heap.insert(neighbor)    
    
    vertex = end_vertex
    path = []
    while vertex:
        path.append(vertex.name)
        vertex = vertex.predecessor
            
    return path[::-1], end_vertex.min_distance        
    