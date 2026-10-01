"""Tests for the logical planner (Task 3).   Run:  python -m unittest -v"""

import unittest

from planner import (GOAL, INITIAL, applicable, apply, bfs_plan, irrelevant_actions,
                     make_action, move_actions, pickup_actions, drop_actions,
                     validate_plan, warehouse_actions)


def act(name):
    """Look up a grounded action by name."""
    return {a.name: a for a in warehouse_actions()}[name]


class TestPlanner(unittest.TestCase):

    # Task 0: applicability in the initial state
    def test_initial_applicability(self):
        s0 = frozenset(INITIAL)
        self.assertTrue(applicable(s0, act("PickUp(Package,A)")))
        self.assertFalse(applicable(s0, act("Drop(Package,C)")))   # robot not at C, not holding
        self.assertTrue(applicable(s0, act("Move(A,B)")))
        self.assertFalse(applicable(s0, act("Move(B,C)")))          # robot is not at B

    def test_apply_effects(self):
        s1 = apply(frozenset(INITIAL), act("PickUp(Package,A)"))
        self.assertEqual(s1, frozenset({"At(Robot,A)", "Holding(Package)"}))

    # Task 1: hand-made plan is valid; the lab's example ordering is not
    def test_manual_plan_valid(self):
        plan = [act(n) for n in ("PickUp(Package,A)", "Move(A,B)", "Move(B,C)", "Drop(Package,C)")]
        ok, _ = validate_plan(INITIAL, GOAL, plan)
        self.assertTrue(ok)

    def test_lab_example_plan_invalid(self):
        plan = [act(n) for n in ("Move(A,B)", "PickUp(Package,B)", "Move(B,C)", "Drop(Package,C)")]
        ok, log = validate_plan(INITIAL, GOAL, plan)
        self.assertFalse(ok)
        self.assertIn("PickUp(Package,B) NOT applicable", log[-1])

    # Test A: solvable problem
    def test_A_solvable(self):
        plan, _ = bfs_plan(INITIAL, GOAL, warehouse_actions())
        self.assertIsNotNone(plan)
        self.assertEqual(len(plan), 4)                     # shortest possible plan
        ok, _ = validate_plan(INITIAL, GOAL, plan)         # verify every action
        self.assertTrue(ok)

    # Test B: impossible problem
    def test_B_no_pickup_no_plan(self):
        plan, _ = bfs_plan(INITIAL, GOAL, warehouse_actions(include_pickup=False))
        self.assertIsNone(plan)

    def test_B_disconnected_no_plan(self):
        acts = move_actions([("A", "B"), ("B", "A")]) + pickup_actions() + drop_actions()
        plan, _ = bfs_plan(INITIAL, GOAL, acts)            # C is unreachable
        self.assertIsNone(plan)

    # Test C: irrelevant actions; robot at C is not the package at C
    def test_C_irrelevant_actions(self):
        plan, _ = bfs_plan(INITIAL, GOAL, warehouse_actions() + irrelevant_actions())
        names = [a.name for a in plan]
        self.assertEqual(len(plan), 4)
        self.assertNotIn("Wait(Robot)", names)
        self.assertNotIn("Recharge(Robot,B)", names)
        ok, _ = validate_plan(INITIAL, GOAL, plan)
        self.assertTrue(ok)

    def test_C_robot_at_C_is_not_goal(self):
        plan = [act("Move(A,B)"), act("Move(B,C)")]
        ok, _ = validate_plan(INITIAL, GOAL, plan)
        self.assertFalse(ok)

    # Negative preconditions are respected
    def test_negative_precondition(self):
        a = make_action("Test", pre_neg=["Holding(Package)"])
        self.assertFalse(applicable(frozenset({"Holding(Package)"}), a))
        self.assertTrue(applicable(frozenset(), a))


if __name__ == "__main__":
    unittest.main()
