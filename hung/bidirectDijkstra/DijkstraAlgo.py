from bidirectDijkstra.lazyMinHeap import MinHeap

def build_reverse_graph(adjList):
    revAdj = {}
    for u, neighbors in adjList.items():
        for v, edge in neighbors.items():
            if v not in revAdj:
                revAdj[v] = {}
            revAdj[v][u] = edge
    return revAdj

# only for distance, testing conclusion: slightly faster (10-15%)
def bidirectional_dijkstra(graph, start_vertex, end_vertex, avoid_nodes, avoid_edges, reverseList = None):

    # shorten
    adjList = graph.adjList
    revAdjList = reverseList if reverseList else build_reverse_graph(graph.adjList)
    
    # main section
    forward_heap = MinHeap()
    backward_heap = MinHeap()
    start_vertex.min_distance = 0
    forward_heap.insert((0, start_vertex))
    backward_heap.insert((0, end_vertex))
    
    distances_f = {start_vertex: 0}
    distances_b = {end_vertex: 0}
    preds_f = {start_vertex: None}
    preds_b = {end_vertex: None}
    forward_visited = set()
    backward_visited = set()
    
    while not forward_heap.is_empty() and not backward_heap.is_empty():
        
        dist_f, fwd_vertex = forward_heap.pop()
        if fwd_vertex in forward_visited: continue
        if fwd_vertex in backward_visited: break
        
        forward_visited.add(fwd_vertex)
        for neighbor, edge in adjList[fwd_vertex].items():
            if neighbor in forward_visited or neighbor in avoid_nodes \
                or edge in avoid_edges:
                continue
            
            curr_dist = dist_f + edge.distance
            if curr_dist < distances_f.get(neighbor, float('inf')):
                distances_f[neighbor] = curr_dist
                preds_f[neighbor] = fwd_vertex
                forward_heap.insert((curr_dist, neighbor))    
                        
        dist_b, back_vertex = backward_heap.pop()
        if back_vertex in backward_visited: continue
        if back_vertex in forward_visited: break
        
        backward_visited.add(back_vertex)
        for neighbor, edge in revAdjList[back_vertex].items():
            if neighbor in backward_visited or neighbor in avoid_nodes \
                or edge in avoid_edges:
                continue
            
            curr_dist = dist_b + edge.distance
            if curr_dist < distances_b.get(neighbor, float('inf')):
                distances_b[neighbor] = curr_dist
                preds_b[neighbor] = back_vertex
                backward_heap.insert((curr_dist, neighbor))  
                
    meeting_node = fwd_vertex if fwd_vertex in backward_visited else back_vertex

    if not meeting_node:
        return [], float('inf')

    # Trace Forward Path (Meeting Node -> Start)
    path_f = []
    curr = meeting_node
    while curr is not None:
        path_f.append(curr.name)
        curr = preds_f.get(curr)
    path_f = path_f[::-1] # Reverse to get Start -> Meeting Node

    # 2. Trace Backward Path (Meeting Node -> End)
    path_b = []
    curr = preds_b.get(meeting_node) # Start from the neighbor to avoid doubling meeting_node
    while curr is not None:
        path_b.append(curr.name)
        curr = preds_b.get(curr)
    
    # 3. Combine them
    full_path = path_f + path_b
    total_dist = distances_f[meeting_node] + distances_b[meeting_node]
    
    return full_path, total_dist          
            
    