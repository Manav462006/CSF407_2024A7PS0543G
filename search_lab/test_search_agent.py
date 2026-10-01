"""Tests for the A* / BFS warehouse search agent (Task 3).   Run:  python -m unittest -v"""

import unittest

from search_agent import (LAB_MAP, Warehouse, astar, bfs, h_double, h_euclidean,
                          h_zero)


def load(name):
    with open(f"maps/{name}") as f:
        return Warehouse(f.read())


class TestSearchAgent(unittest.TestCase):

    def check_valid_path(self, env, path):
        self.assertEqual(path[0], env.start)
        self.assertEqual(path[-1], env.goal)
        for a, b in zip(path, path[1:]):
            self.assertEqual(abs(a[0] - b[0]) + abs(a[1] - b[1]), 1)   # one step at a time
            self.assertTrue(env.is_free(b))                          # never enters an obstacle

    # Test 1: original warehouse
    def test1_original_warehouse(self):
        env = Warehouse(LAB_MAP)
        r = astar(env)
        self.assertTrue(r.found)
        self.check_valid_path(env, r.path)
        self.assertEqual(r.length, 40)

    # Test 2: trivial case (goal next to start)
    def test2_trivial(self):
        env = load("test2_trivial.txt")
        r = astar(env)
        self.assertTrue(r.found)
        self.assertEqual(r.length, 1)
        self.assertEqual(r.path, [env.start, env.goal])

    # Test 3: no solution -> reports failure, does not loop forever
    def test3_no_solution(self):
        env = load("test3_no_solution.txt")
        self.assertFalse(astar(env).found)
        self.assertFalse(bfs(env).found)

    # Test 4: alternative paths -> returned path must be a shortest one
    def test4_alternative_paths_shortest(self):
        env = load("test4_alternative_paths.txt")
        r = astar(env)
        self.assertTrue(r.found)
        self.check_valid_path(env, r.path)
        self.assertEqual(r.length, bfs(env).length)    # BFS is optimal for unit costs
        self.assertEqual(r.length, 8)

    # Task 5: A* and BFS agree on optimal length; A* never expands more on these maps
    def test_astar_matches_bfs(self):
        for env in (Warehouse(LAB_MAP), load("open_warehouse.txt"), load("test4_alternative_paths.txt")):
            a, b = astar(env), bfs(env)
            self.assertEqual(a.length, b.length)
            self.assertLessEqual(a.expanded, b.expanded)

    # Task 6: admissible heuristics stay optimal; 2x Manhattan may not
    def test_heuristic_variants(self):
        env = load("open_warehouse.txt")
        optimal = bfs(env).length
        self.assertEqual(astar(env, h_zero).length, optimal)
        self.assertEqual(astar(env, h_euclidean).length, optimal)
        self.assertGreater(astar(env, h_double).length, optimal)   # inadmissible -> suboptimal here


if __name__ == "__main__":
    unittest.main()
