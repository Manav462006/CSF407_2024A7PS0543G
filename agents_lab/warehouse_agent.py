"""
warehouse_agent.py
==================

A goal-based intelligent agent for the Warehouse Navigation Problem.

The agent:
  1. PERCEIVES the environment (the warehouse grid),
  2. identifies its CURRENT STATE (position S) and GOAL (position G),
  3. uses a SEARCH algorithm (Breadth-First Search) to plan a sequence of
     actions that leads from the current state to the goal,
  4. EXECUTES the plan one action at a time, checking that each action
     moves it closer to the goal.

Why Breadth-First Search (BFS)?
-------------------------------
* Every move (Up, Down, Left, Right) has the same cost (1 square).
* BFS explores positions in order of distance from the start, so the first
  time it reaches G it has found a SHORTEST path (it is *optimal* for
  uniform step costs).
* BFS is *complete*: if a path exists it will find it; if none exists it
  terminates and reports failure.
* The grid is small (21 x 7 = 147 cells), so BFS's memory use is trivial.

An A* search (Manhattan-distance heuristic) is also provided for comparison,
because it scales better to much larger warehouses (see README).

Run:
    python warehouse_agent.py            # BFS (default)
    python warehouse_agent.py --astar    # A* search
"""

from __future__ import annotations

import heapq
import sys
from collections import deque
from typing import Dict, List, Optional, Tuple

# ---------------------------------------------------------------------------
# Environment definition
# ---------------------------------------------------------------------------

WAREHOUSE_MAP = """\
#####################
#S....#............G#
#.##....##########..#
#....##.............#
#.######.###.#.###..#
#........#..........#
#####################"""

Position = Tuple[int, int]  # (row, column)

# Actions available to the agent: name -> (row change, column change)
ACTIONS: Dict[str, Tuple[int, int]] = {
    "Up": (-1, 0),
    "Down": (1, 0),
    "Left": (0, -1),
    "Right": (0, 1),
}


class Warehouse:
    """The ENVIRONMENT: a 2-D grid of cells."""

    OBSTACLE = "#"
    FREE = "."
    START = "S"
    GOAL = "G"

    def __init__(self, map_text: str):
        self.grid: List[List[str]] = [list(line) for line in map_text.strip("\n").splitlines()]
        self.rows = len(self.grid)
        self.cols = max(len(r) for r in self.grid)
        self.start = self._find(self.START)
        self.goal = self._find(self.GOAL)

    def _find(self, symbol: str) -> Position:
        for r, row in enumerate(self.grid):
            for c, cell in enumerate(row):
                if cell == symbol:
                    return (r, c)
        raise ValueError(f"Map does not contain the symbol '{symbol}'.")

    def in_bounds(self, pos: Position) -> bool:
        r, c = pos
        return 0 <= r < self.rows and 0 <= c < len(self.grid[r])

    def is_free(self, pos: Position) -> bool:
        """A cell can be entered if it is inside the map and not a shelf."""
        return self.in_bounds(pos) and self.grid[pos[0]][pos[1]] != self.OBSTACLE

    def result(self, pos: Position, action: str) -> Position:
        """TRANSITION MODEL: the position reached by applying an action."""
        dr, dc = ACTIONS[action]
        return (pos[0] + dr, pos[1] + dc)

    def legal_actions(self, pos: Position) -> List[Tuple[str, Position]]:
        """All (action, next_position) pairs that do not cause a collision."""
        moves = []
        for action in ACTIONS:
            nxt = self.result(pos, action)
            if self.is_free(nxt):
                moves.append((action, nxt))
        return moves

    def render(self, path: Optional[List[Position]] = None, agent: Optional[Position] = None) -> str:
        """Return the map as text, optionally marking the path with '*'."""
        out = [row[:] for row in self.grid]
        for p in path or []:
            if out[p[0]][p[1]] == self.FREE:
                out[p[0]][p[1]] = "*"
        if agent and agent not in (self.start, self.goal):
            out[agent[0]][agent[1]] = "A"
        return "\n".join("".join(row) for row in out)


# ---------------------------------------------------------------------------
# Search algorithms (the agent's DECISION-MAKING component)
# ---------------------------------------------------------------------------

def reconstruct(parents: Dict[Position, Tuple[Optional[Position], Optional[str]]],
                goal: Position) -> Tuple[List[Position], List[str]]:
    """Follow parent links back from the goal to build the path and actions."""
    path, actions = [goal], []
    node = goal
    while parents[node][0] is not None:
        parent, action = parents[node]
        actions.append(action)
        path.append(parent)
        node = parent
    path.reverse()
    actions.reverse()
    return path, actions


def bfs(env: Warehouse, start: Position, goal: Position):
    """Breadth-First Search. Returns (path, actions, nodes_expanded) or (None, None, n)."""
    frontier = deque([start])
    parents = {start: (None, None)}          # also serves as the explored set
    expanded = 0
    while frontier:
        current = frontier.popleft()
        expanded += 1
        if current == goal:                  # GOAL TEST
            path, actions = reconstruct(parents, goal)
            return path, actions, expanded
        for action, nxt in env.legal_actions(current):
            if nxt not in parents:
                parents[nxt] = (current, action)
                frontier.append(nxt)
    return None, None, expanded


def manhattan(a: Position, b: Position) -> int:
    return abs(a[0] - b[0]) + abs(a[1] - b[1])


def astar(env: Warehouse, start: Position, goal: Position):
    """A* search with the (admissible) Manhattan-distance heuristic."""
    counter = 0                               # tie-breaker for the heap
    frontier = [(manhattan(start, goal), counter, start)]
    parents = {start: (None, None)}
    g_cost = {start: 0}
    expanded = 0
    closed = set()
    while frontier:
        _, _, current = heapq.heappop(frontier)
        if current in closed:
            continue
        closed.add(current)
        expanded += 1
        if current == goal:
            path, actions = reconstruct(parents, goal)
            return path, actions, expanded
        for action, nxt in env.legal_actions(current):
            new_g = g_cost[current] + 1
            if new_g < g_cost.get(nxt, float("inf")):
                g_cost[nxt] = new_g
                parents[nxt] = (current, action)
                counter += 1
                heapq.heappush(frontier, (new_g + manhattan(nxt, goal), counter, nxt))
    return None, None, expanded


# ---------------------------------------------------------------------------
# The goal-based agent
# ---------------------------------------------------------------------------

class GoalBasedAgent:
    """
    Goal-based agent architecture:

        Percepts -> [What the world is like now (state)]
                 -> [What it will be like if I do action A (transition model)]
                 -> [Goal]  -> [Search / planning] -> Action -> Environment
    """

    def __init__(self, env: Warehouse, algorithm: str = "bfs"):
        self.env = env
        self.state: Position = env.start      # internal state: current position
        self.goal: Position = env.goal        # explicit goal
        self.algorithm = algorithm
        self.plan: List[str] = []
        self.path: List[Position] = []
        self.nodes_expanded = 0

    def goal_reached(self) -> bool:
        return self.state == self.goal

    def formulate_plan(self) -> bool:
        """Use search to find a sequence of actions from the state to the goal."""
        search = astar if self.algorithm == "astar" else bfs
        path, actions, expanded = search(self.env, self.state, self.goal)
        self.nodes_expanded = expanded
        if path is None:
            return False
        self.path, self.plan = path, actions
        return True

    def act(self) -> str:
        """Execute the next planned action and update the internal state."""
        action = self.plan.pop(0)
        nxt = self.env.result(self.state, action)
        assert self.env.is_free(nxt), f"Collision! {action} from {self.state}"
        self.state = nxt
        return action

    def run(self, verbose: bool = True) -> bool:
        if verbose:
            print(f"Algorithm : {self.algorithm.upper()}")
            print(f"Start (S) : row {self.state[0]}, col {self.state[1]}")
            print(f"Goal  (G) : row {self.goal[0]}, col {self.goal[1]}\n")

        if not self.formulate_plan():
            print("No collision-free path exists from S to G.")
            return False

        if verbose:
            print(f"Path found: {len(self.plan)} moves, {self.nodes_expanded} nodes expanded.\n")
            print("Path as coordinates (row, col):")
            print(" -> ".join(str(p) for p in self.path), "\n")
            print("Action sequence:")
            print(", ".join(self.plan), "\n")

        while not self.goal_reached():       # execute the plan
            self.act()

        if verbose:
            print("Map with path marked '*':")
            print(self.env.render(self.path))
            print("\nGoal reached successfully.")
        return True


def main() -> None:
    algorithm = "astar" if "--astar" in sys.argv else "bfs"
    env = Warehouse(WAREHOUSE_MAP)
    agent = GoalBasedAgent(env, algorithm)
    agent.run()


if __name__ == "__main__":
    main()
