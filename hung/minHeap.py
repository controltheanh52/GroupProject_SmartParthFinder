from math import log2, ceil

class MinHeap :
    def __init__(self):
        self.heap = []
        
    def is_empty(self):
        return len(self.heap) == 0
    
    def insert(self, obj):
        # uncomment this for debugging ( it uses O(n) )
        # if value in self.heap:
        #     return
        self.heap.append(obj)
        self.heapify_up(len(self.heap) - 1)
    
    def pop(self):
        if not self.heap: return None
        if len(self.heap) == 1: return self.heap.pop()

        root = self.heap[0]
        self.heap[0] = self.heap.pop() # Move last to top
        self.heapify_down(0)
        return root
    
    # def remove(self, obj):
    #     if obj not in self.heap:
    #         return
        
    #     nodeIndex = self.heap.index(obj)
    #     self.heap[nodeIndex] = self.heap[-1]
    #     self.heap.pop()
        
    #     parent = int((nodeIndex - 1) / 2)
    #     if self.heap[nodeIndex] >= self.heap[parent]:
    #         self.heapify_down(nodeIndex)
    #     else:
    #         self.heapify_up(nodeIndex)
        
    def heapify_up(self, index):
        
        parent = (index - 1) // 2
        while index > 0 and self.heap[parent] > self.heap[index]:
            self.swap(parent, index)
            index = parent
            parent = (index - 1) // 2
                
    def heapify_down(self, index):
        while True:
            swapIndex = index # assign swapIndex with index for easier check later
            left = 2*index + 1
            right = 2*index + 2
            
            if left < len(self.heap) and self.heap[left] < self.heap[swapIndex]:
                swapIndex = left
                
            # compared right with swapIndex because:
            # 1. swapIndex is the current smallest node
            # 2. if swapIndex is replaced with left, check if right < left
            # 3. otherwise, check if right < index 
            if right < len(self.heap) and self.heap[right] < self.heap[swapIndex]: 
                swapIndex = right                        
            
            if swapIndex != index: # if the swapIndex is replaced by left or right child, swap
                self.swap(swapIndex, index)
                index = swapIndex   
            else:
                break
                
    def swap(self, n1, n2):
        self.heap[n1], self.heap[n2] = self.heap[n2], self.heap[n1]
        
    def display(self):

        levels = ceil(log2(len(self.heap) + 1))
        max_nodes = 2 ** (levels - 1)
        width = max_nodes * 4

        index = 0

        for level in range(levels):
            nodes = 2 ** level
            gap = width // nodes
            line = ""

            for i in range(nodes):
                if index >= len(self.heap):
                    break

                obj = str(self.heap[index])
                pos = gap * i + gap // 2
                line = line.ljust(pos)
                line += obj
                index += 1

            print(line)
 
if __name__ == "__main__":
    minheap = MinHeap()

    # Insert test values
    values = [10, 4, 15, 2, 8, 20, 1, 6]

    print("Inserting values:")
    for value in values:
        print(f"insert({value})")
        minheap.insert(value)

    print("\nHeap array:")
    print(minheap.heap)

    print("\nTree view:")
    minheap.display()

    # Remove tests
    remove_values = [1, 4, 10, 20]

    for value in remove_values:
        print(f"\nremove({value})")
        minheap.remove(value)

        print("Heap array:")
        print(minheap.heap)

        print("Tree view:")
        minheap.display()

    # Edge cases
    print("\nremove(999)  # not in heap")
    minheap.remove(999)

    print("\nFinal heap:")
    print(minheap.heap)
    minheap.display()