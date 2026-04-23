"""
Custom Binary Min-Heap implementation.

This module provides a MinHeap data structure built from scratch (no heapq).
Used by the optimized Dijkstra algorithm with a lazy deletion strategy:
  - push() inserts (priority, item) pairs
  - pop() extracts the minimum-priority pair
  - Stale entries are detected and skipped by the Dijkstra caller

Time Complexity:
  - push: O(log n)
  - pop:  O(log n)
  - is_empty / len: O(1)

Space Complexity: O(n) where n is the number of entries in the heap.
"""


class MinHeap:
    """
    A binary min-heap that stores (priority, item) tuples.

    The heap is a complete binary tree stored as a flat list.
    Parent of index i is at (i - 1) // 2.
    Children of index i are at 2*i + 1 (left) and 2*i + 2 (right).
    """

    def __init__(self):
        self._data = []  # list of (priority, insertion_order, item)
        self._counter = 0  # tie-breaker for equal priorities

    def push(self, priority, item):
        """Insert an item with the given priority. O(log n)."""
        entry = (priority, self._counter, item)
        self._counter += 1
        self._data.append(entry)
        self._sift_up(len(self._data) - 1)

    def pop(self):
        """
        Remove and return (priority, item) with the smallest priority.
        Raises IndexError if the heap is empty.
        O(log n).
        """
        if not self._data:
            raise IndexError("pop from empty heap")

        # Swap root with last element, then sift down
        self._swap(0, len(self._data) - 1)
        priority, _, item = self._data.pop()

        if self._data:
            self._sift_down(0)

        return priority, item

    def peek(self):
        """Return (priority, item) with the smallest priority without removing. O(1)."""
        if not self._data:
            raise IndexError("peek at empty heap")
        priority, _, item = self._data[0]
        return priority, item

    def is_empty(self):
        """Check if the heap is empty. O(1)."""
        return len(self._data) == 0

    def __len__(self):
        """Return the number of entries in the heap. O(1)."""
        return len(self._data)

    def __bool__(self):
        """Return True if the heap is non-empty."""
        return len(self._data) > 0

    # -------------------------------------------------------------------------
    # Internal heap operations
    # -------------------------------------------------------------------------

    def _sift_up(self, index):
        """
        Move element at 'index' up until the heap property is restored.
        Called after insertion at the bottom of the heap.
        """
        while index > 0:
            parent = (index - 1) // 2
            if self._data[index] < self._data[parent]:
                self._swap(index, parent)
                index = parent
            else:
                break

    def _sift_down(self, index):
        """
        Move element at 'index' down until the heap property is restored.
        Called after replacing the root during pop.
        """
        size = len(self._data)
        while True:
            smallest = index
            left = 2 * index + 1
            right = 2 * index + 2

            if left < size and self._data[left] < self._data[smallest]:
                smallest = left
            if right < size and self._data[right] < self._data[smallest]:
                smallest = right

            if smallest != index:
                self._swap(index, smallest)
                index = smallest
            else:
                break

    def _swap(self, i, j):
        """Swap elements at indices i and j."""
        self._data[i], self._data[j] = self._data[j], self._data[i]
