"""
planner.py
==========

Laboratory: Logical Reasoning for Planning  --  Warehouse Robot.

A simple STRIPS-style planning agent.

  * A STATE is a frozenset of logical propositions (strings), e.g.
        {"At(Robot,A)", "At(Package,A)"}
    Anything not in the set is false (closed-world assumption).

  * An ACTION has a name, positive and negative preconditions,
    and positive and negative effects.

  * LOGIC   : applicable(S, a)  <=>  S |= Preconditions(a)
              apply(S, a) = (S - negative_effects) | positive_effects
  * SEARCH  : breadth-first search over states, using only applicable actions.

Logic decides what is possible; search decides what to try.

Run:
    python planner.py              # original warehouse problem (Test A)
    python planner.py --all        # Tests A, B and C
"""

from __future__ import annotations

import sys
from collections import deque
from dataclasses import dataclass, field
from typing import FrozenSet, Iterable, List, Optional, Tuple

State = FrozenSet[str]


# ---------------------------------------------------------------------------
# Actions
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class Action:
    name: str
    pre_pos: FrozenSet[str] = field(default_factory=frozenset)   # must be TRUE
    pre_neg: FrozenSet[str] = field(default_factory=frozenset)   # must be FALSE
    add: FrozenSet[str] = field(default_factory=frozenset)       # positive effects
    delete: FrozenSet[str] = field(default_factory=frozenset)    # negative effects

    def __str__(self) -> str:
        return self.name


def make_action(name, pre_pos=(), pre_neg=(), add=(), delete=()) -> Action:
    return Action(name, frozenset(pre_pos), frozenset(pre_neg), frozenset(add), frozenset(delete))


# ---------------------------------------------------------------------------
# Logical component
# ---------------------------------------------------------------------------

def applicable(state: State, action: Action) -> bool:
    """PRECONDITIONS: S |= Preconditions(a).
    Every positive precondition is in S and no negative precondition is in S."""
    return action.pre_pos <= state and not (action.pre_neg & state)


def apply(state: State, action: Action) -> State:
    """EFFECTS: S' = (S - negative effects) U positive effects."""
    return frozenset((state - action.delete) | action.add)


def satisfies(state: State, goal: Iterable[str]) -> bool:
    """GOAL TEST: S |= G  (every goal proposition is true in S)."""
    return frozenset(goal) <= state


# ---------------------------------------------------------------------------
# Search component: breadth-first search
# ---------------------------------------------------------------------------

def bfs_plan(initial: Iterable[str], goal: Iterable[str],
             actions: List[Action]) -> Tuple[Optional[List[Action]], int]:
    """Return (plan, states_explored). plan is None if no plan exists."""
    start = frozenset(initial)
    goal = frozenset(goal)
    frontier = deque([start])                                  # FIFO queue -> BFS
    parent = {start: None}                                     # also the visited set
    explored = 0

    while frontier:
        state = frontier.popleft()
        explored += 1
        if satisfies(state, goal):                             # planning terminates
            plan = []
            while parent[state] is not None:
                prev, act = parent[state]
                plan.append(act)
                state = prev
            return list(reversed(plan)), explored

        for action in actions:                                 # alternatives explored
            if applicable(state, action):                      # logic: is it possible?
                nxt = apply(state, action)
                if nxt not in parent:                          # do not revisit states
                    parent[nxt] = (state, action)
                    frontier.append(nxt)

    return None, explored                                      # no plan exists


# ---------------------------------------------------------------------------
# Independent plan validator (does not use the search at all)
# ---------------------------------------------------------------------------

def validate_plan(initial: Iterable[str], goal: Iterable[str],
                  plan: List[Action]) -> Tuple[bool, List[str]]:
    """Execute the plan step by step, checking every precondition and the goal."""
    state = frozenset(initial)
    log = []
    for i, a in enumerate(plan, 1):
        if not applicable(state, a):
            missing = sorted(a.pre_pos - state)
            forbidden = sorted(a.pre_neg & state)
            log.append(f"step {i}: {a} NOT applicable (missing {missing}, forbidden {forbidden})")
            return False, log
        state = apply(state, a)
        log.append(f"step {i}: {a} OK")
    ok = satisfies(state, goal)
    log.append("goal satisfied" if ok else f"goal NOT satisfied, final state {sorted(state)}")
    return ok, log


# ---------------------------------------------------------------------------
# The warehouse domain
# ---------------------------------------------------------------------------

LOCATIONS = ["A", "B", "C"]
CONNECTIONS = [("A", "B"), ("B", "A"), ("B", "C"), ("C", "B")]

INITIAL = {"At(Robot,A)", "At(Package,A)"}
GOAL = {"At(Package,C)"}


def move_actions(connections=CONNECTIONS) -> List[Action]:
    return [make_action(f"Move({x},{y})",
                        pre_pos=[f"At(Robot,{x})"],
                        add=[f"At(Robot,{y})"],
                        delete=[f"At(Robot,{x})"])
            for x, y in connections]


def pickup_actions(locations=LOCATIONS) -> List[Action]:
    return [make_action(f"PickUp(Package,{l})",
                        pre_pos=[f"At(Robot,{l})", f"At(Package,{l})"],
                        pre_neg=["Holding(Package)"],
                        add=["Holding(Package)"],
                        delete=[f"At(Package,{l})"])
            for l in locations]


def drop_actions(locations=LOCATIONS) -> List[Action]:
    return [make_action(f"Drop(Package,{l})",
                        pre_pos=[f"At(Robot,{l})", "Holding(Package)"],
                        add=[f"At(Package,{l})"],
                        delete=["Holding(Package)"])
            for l in locations]


def warehouse_actions(include_pickup: bool = True) -> List[Action]:
    acts = move_actions() + drop_actions()
    if include_pickup:
        acts += pickup_actions()
    return acts


def irrelevant_actions() -> List[Action]:
    """Actions that change the robot's situation but never move the package (Test C)."""
    return [
        make_action("Recharge(Robot,B)", pre_pos=["At(Robot,B)"], add=["Charged(Robot)"]),
        make_action("Wait(Robot)", add=["Waited(Robot)"]),
    ]


# ---------------------------------------------------------------------------
# Reporting
# ---------------------------------------------------------------------------

def fmt(state: Iterable[str]) -> str:
    return "{" + ", ".join(sorted(state)) + "}"


def run(title: str, initial, goal, actions) -> Optional[List[Action]]:
    print(f"=== {title} ===")
    print(f"Initial state : {fmt(initial)}")
    print(f"Goal          : {fmt(goal)}")
    plan, explored = bfs_plan(initial, goal, actions)
    print(f"States explored: {explored}")
    if plan is None:
        print("Result        : No plan found\n")
        return None

    print(f"Result        : plan with {len(plan)} actions")
    state = frozenset(initial)
    print(f"  S0: {fmt(state)}")
    for i, a in enumerate(plan, 1):
        state = apply(state, a)
        print(f"  {a.name:<20} -> S{i}: {fmt(state)}")
    ok, _ = validate_plan(initial, goal, plan)
    print(f"Independent validation: {'VALID' if ok else 'INVALID'}\n")
    return plan


def main() -> None:
    run("Test A: original warehouse problem", INITIAL, GOAL, warehouse_actions())
    if "--all" in sys.argv:
        run("Test B: impossible problem (no PickUp action)", INITIAL, GOAL,
            warehouse_actions(include_pickup=False))
        run("Test C: irrelevant actions added (robot moves / recharges without the package)",
            INITIAL, GOAL, warehouse_actions() + irrelevant_actions())
        print("Check: the robot alone can reach C with Move(A,B), Move(B,C),")
        print("but that must NOT count as delivering the package:")
        robot_only = [a for a in move_actions() if a.name in ("Move(A,B)", "Move(B,C)")]
        ok, log = validate_plan(INITIAL, GOAL, robot_only)
        for line in log:
            print("  " + line)


if __name__ == "__main__":
    main()
