from grid_generator import grid_generator
from minHeap import MinHeap
def dijkstra(graph, start, end, avoid_nodes, avoid_edges):
    
    heap = MinHeap()
    visited = []
    heap.insert(graph.adjList[start])
    