"""Unit tests for the warehouse goal-based agent.  Run:  python -m unittest -v"""

import unittest

from warehouse_agent import (ACTIONS, WAREHOUSE_MAP, GoalBasedAgent, Warehouse,
                             astar, bfs)

BLOCKED_MAP = """\
#######
#S.#.G#
#..#..#
#######"""


class TestWarehouseAgent(unittest.TestCase):

    def setUp(self):
        self.env = Warehouse(WAREHOUSE_MAP)

    def test_start_and_goal_located(self):
        self.assertEqual(self.env.start, (1, 1))
        self.assertEqual(self.env.goal, (1, 19))

    def test_bfs_finds_valid_collision_free_path(self):
        path, actions, _ = bfs(self.env, self.env.start, self.env.goal)
        self.assertIsNotNone(path)
        self.assertEqual(path[0], self.env.start)
        self.assertEqual(path[-1], self.env.goal)
        for a, b in zip(path, path[1:]):
            self.assertEqual(abs(a[0] - b[0]) + abs(a[1] - b[1]), 1)  # one square per move
            self.assertTrue(self.env.is_free(b))                     # never hits a shelf
        self.assertEqual(len(actions), len(path) - 1)
        self.assertTrue(all(a in ACTIONS for a in actions))

    def test_bfs_and_astar_agree_on_shortest_length(self):
        p1, _, _ = bfs(self.env, self.env.start, self.env.goal)
        p2, _, _ = astar(self.env, self.env.start, self.env.goal)
        self.assertEqual(len(p1), len(p2))

    def test_astar_expands_no_more_nodes_than_bfs(self):
        _, _, n_bfs = bfs(self.env, self.env.start, self.env.goal)
        _, _, n_astar = astar(self.env, self.env.start, self.env.goal)
        self.assertLessEqual(n_astar, n_bfs)

    def test_agent_reaches_goal(self):
        agent = GoalBasedAgent(self.env)
        self.assertTrue(agent.run(verbose=False))
        self.assertEqual(agent.state, self.env.goal)

    def test_no_path_reported(self):
        env = Warehouse(BLOCKED_MAP)
        path, actions, _ = bfs(env, env.start, env.goal)
        self.assertIsNone(path)
        self.assertFalse(GoalBasedAgent(env).run(verbose=False))


if __name__ == "__main__":
    unittest.main()
