class MinHeap:
    def __init__(self):
        # Internal list to store heap elements
        # Each element will be a tuple: (priority, node)
        self.heap = []

    def peek(self):
        # Return smallest element without removing it
        if not self.heap:
            return None
        return self.heap[0]

    def push(self, item):
        # Add new item to heap and restore heap property
        self.heap.append(item)
        self._heapify_up(len(self.heap) - 1)

    def pop(self):
        # Remove and return smallest element (root)
        if len(self.heap) == 0:
            return None
        
        self._swap(0, len(self.heap) - 1)
        item = self.heap.pop()
        self._heapify_down(0)
        return item

    def is_empty(self):
        return len(self.heap) == 0

    def _heapify_up(self, index):
        # Move element up until heap property is restored
        parent = (index - 1) // 2

        # Compare based on priority (item[0])
        while index > 0 and self.heap[index][0] < self.heap[parent][0]:
            self._swap(index, parent)
            index = parent
            parent = (index - 1) // 2

    def _heapify_down(self, index):
        # Move element down until heap property is restored
        smallest = index
        left = 2 * index + 1
        right = 2 * index + 2

        # Compare based on priority (item[0])
        if left < len(self.heap) and self.heap[left][0] < self.heap[smallest][0]:
            smallest = left

        if right < len(self.heap) and self.heap[right][0] < self.heap[smallest][0]:
            smallest = right

        if smallest != index:
            self._swap(index, smallest)
            self._heapify_down(smallest)

    def _swap(self, i, j):
        self.heap[i], self.heap[j] = self.heap[j], self.heap[i]