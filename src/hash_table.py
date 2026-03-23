import math

from matplotlib.typing import CapStyleType

"""
Custom hash table with separate chaining.

This is the CORE data structure for the Mini Shazam project.
You must implement this from scratch — no built-in dicts or hashmaps allowed.

Refer to GUIDE.md, Milestone 1 for detailed instructions.
"""

class HashTable:
    """
    Hash table using separate chaining.

    Each bucket is a Python list of (key, value) pairs.
    When multiple entries hash to the same bucket, they form a "chain."

    You will implement:
      - _hash(key)       : Map an integer key to a bucket index
      - insert(key, value): Add a (key, value) pair to the table
      - lookup(key)       : Retrieve all values associated with a key
      - size()            : Return the total number of stored entries
      - capacity()        : Return the number of buckets
      - load_factor()     : Return entries / capacity
      - stats()           : Return collision statistics as a dict
      - _next_prime(n)    : Find the smallest prime >= n
      - _resize()         : Double capacity and rehash all entries
    """

    DEFAULT_CAPACITY = 10007  # A prime number — why prime? See GUIDE.md

    def __init__(self, capacity=None):
        self._capacity = capacity or self.DEFAULT_CAPACITY
        self._buckets = [[] for _ in range(self._capacity)]
        self._size = 0

    # ------------------------------------------------------------------ #
    # Hash function
    # ------------------------------------------------------------------ #

    def _hash(self, key):
        """
        Map an integer key to a bucket index in range [0, capacity).

        Requirements:
          - Must return an integer in [0, self._capacity)
          - Must be deterministic (same key always maps to same index)
          - Should distribute keys uniformly across buckets

        Hint: The Knuth multiplicative hash works well here.
              Multiply the key by a large constant, then take modulo capacity.
              The constant 2654435761 (a prime close to 2^32 * phi) is a
              classic choice from Knuth's "The Art of Computer Programming."

        Important: Use int(key) to convert the key to a Python int first.
                   This avoids integer overflow issues with numpy int64 values.

        Args:
            key: An integer hash key

        Returns:
            An integer bucket index in [0, self._capacity)
        """

        return int(key*2654435761) % self.capacity()

    # ------------------------------------------------------------------ #
    # Core operations
    # ------------------------------------------------------------------ #

    def insert(self, key, value):
        index = self._hash(key)
        self._buckets[index].append((key, value))
        self._size += 1

        if self.load_factor() > 0.75:
            self._resize()

    def lookup(self, key):
        index = self._hash(key)
        results = []

        for f_key, value in self._buckets[index]:
            if f_key == key:
                results.append(value)

        return results

    # ------------------------------------------------------------------ #
    # Size & statistics
    # ------------------------------------------------------------------ #

    def size(self):
        """Return the total number of stored entries."""
        return self._size

    def capacity(self):
        """Return the current number of buckets."""
        return self._capacity

    def load_factor(self):
        """
        Return the load factor: entries / capacity.

        The load factor tells you how "full" the table is.
        - 0.0 means empty
        - 0.5 means half the buckets have one entry (on average)
        - 1.0 means as many entries as buckets
        - > 1.0 means chains are getting long on average

        We resize when this exceeds 0.75 to keep lookups fast.
        """
        if self._capacity == 0:
            return 0
        return round(self._size/self._capacity, 4)

    def stats(self):
        """
        Return a dictionary of collision statistics.

        This is useful for analyzing how well your hash function distributes keys.

        Must return a dict with these keys:
          - "capacity": current number of buckets
          - "size": total number of stored entries
          - "load_factor": entries / capacity (rounded to 4 decimal places)
          - "empty_buckets": number of buckets with no entries
          - "max_chain_length": length of the longest chain
          - "avg_chain_length": average length of non-empty chains (rounded to 4 decimal places)

        Returns:
            dict with the keys described above
        """
        empty_buckets = 0
        max_chain_length = 0
        avg_chain_length = 0

        for bucket in self._buckets:
            if len(bucket) == 0:
                empty_buckets +=1
            max_chain_length = max(max_chain_length, len(bucket))
            avg_chain_length += len(bucket)
        

        return {
            "capacity": self._capacity,
            "size": self._size,
            "load_factor": self.load_factor(),
            "empty_buckets": empty_buckets,
            "max_chain_length": max_chain_length,
            "avg_chain_length": round(avg_chain_length/ self._capacity)
        }

    # ------------------------------------------------------------------ #
    # Resizing
    # ------------------------------------------------------------------ #

    @staticmethod
    def _next_prime(n):
        def is_prime(x):
            if x < 2:
                return False
            if x == 2:
                return True
            if x % 2 == 0:
                return False
            for i in range(3, int(x**0.5) + 1, 2):
                if x % i == 0:
                    return False
            return True

        while not is_prime(n):
            n += 1

        return n

    def _resize(self):
        
        new_capacity = self._next_prime(self._capacity*2)
        old_buckets = self._buckets

        self._capacity = new_capacity
        self._buckets = [[] for _ in range(self._capacity)]
        self._size = 0
        # [[(key1, value1), ()], ...., [(), ()]]
            
        for bucket in old_buckets:
            for key, value in bucket:
                index = self._hash(key)
                self._buckets[index].append((key, value))
                self._size += 1
