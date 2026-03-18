"""
Unit tests for YOUR custom hash table implementation.

Run with:
    python -m pytest tests/student/test_hash_table.py -v

These tests are designed to guide you through Milestone 1.
Start by making the basic tests pass, then work your way down.
"""

import pytest

from src.hash_table import HashTable

# ================================================================== #
# PART A: Basic operations (implement _hash, insert, lookup, size first)
# ================================================================== #


class TestHashTableBasics:
    def test_empty_table(self):
        """A fresh table should have size 0 and return [] for any lookup."""
        ht = HashTable()
        assert ht.size() == 0
        assert ht.load_factor() == 0.0
        assert ht.lookup(42) == []

    def test_insert_and_lookup(self):
        """Insert one item, look it up."""
        ht = HashTable()
        ht.insert(100, "hello")
        assert ht.size() == 1
        assert ht.lookup(100) == ["hello"]

    def test_multiple_values_same_key(self):
        """Multiple values under the same key should all be returned."""
        ht = HashTable()
        ht.insert(100, ("song_a", 10))
        ht.insert(100, ("song_b", 20))
        ht.insert(100, ("song_c", 30))
        results = ht.lookup(100)
        assert len(results) == 3
        assert ("song_a", 10) in results
        assert ("song_b", 20) in results
        assert ("song_c", 30) in results

    def test_different_keys(self):
        """Different keys should store and retrieve independently."""
        ht = HashTable()
        ht.insert(1, "a")
        ht.insert(2, "b")
        ht.insert(3, "c")
        assert ht.lookup(1) == ["a"]
        assert ht.lookup(2) == ["b"]
        assert ht.lookup(3) == ["c"]
        assert ht.size() == 3

    def test_lookup_nonexistent(self):
        """Looking up a key that doesn't exist should return []."""
        ht = HashTable()
        ht.insert(1, "a")
        assert ht.lookup(999) == []


# ================================================================== #
# PART B: Resizing (implement _next_prime and _resize)
# ================================================================== #


class TestHashTableResize:
    def test_resize_triggers(self):
        """When load factor exceeds 0.75, table should resize."""
        small_ht = HashTable(capacity=7)
        for i in range(10):
            small_ht.insert(i, f"val_{i}")
        # After inserting 10 items into capacity=7, resize should have happened
        assert small_ht.capacity() > 7
        # All values should still be retrievable after resize!
        for i in range(10):
            assert small_ht.lookup(i) == [f"val_{i}"]

    def test_load_factor(self):
        """Load factor should be entries / capacity."""
        ht = HashTable(capacity=100)
        for i in range(50):
            ht.insert(i, i)
        assert ht.load_factor() == pytest.approx(0.5)


# ================================================================== #
# PART C: Statistics (implement stats)
# ================================================================== #


class TestHashTableStats:
    def test_stats_structure(self):
        """stats() should return a dict with the expected keys."""
        ht = HashTable(capacity=101)
        for i in range(50):
            ht.insert(i * 7, i)
        s = ht.stats()
        assert "capacity" in s
        assert "size" in s
        assert "load_factor" in s
        assert "empty_buckets" in s
        assert "max_chain_length" in s
        assert "avg_chain_length" in s
        assert s["size"] == 50

    def test_collision_stats(self):
        """Inserting many entries with the same key should create a long chain."""
        ht = HashTable(capacity=101)
        for i in range(20):
            ht.insert(42, i)
        s = ht.stats()
        assert s["max_chain_length"] >= 20


# ================================================================== #
# PART D: Stress test
# ================================================================== #


class TestHashTableLargeScale:
    def test_many_inserts(self):
        """The table should handle 50,000 inserts correctly."""
        ht = HashTable()
        n = 50000
        for i in range(n):
            ht.insert(i, i * 2)
        assert ht.size() == n
        # Spot check a few values
        assert ht.lookup(0) == [0]
        assert ht.lookup(12345) == [24690]
        assert ht.lookup(n - 1) == [(n - 1) * 2]


# ================================================================== #
# PART E: Prime helper
# ================================================================== #


class TestNextPrime:
    def test_small_primes(self):
        assert HashTable._next_prime(2) == 2
        assert HashTable._next_prime(3) == 3
        assert HashTable._next_prime(4) == 5
        assert HashTable._next_prime(10) == 11

    def test_already_prime(self):
        assert HashTable._next_prime(17) == 17
