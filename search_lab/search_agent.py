"""
search_agent.py
===============

Laboratory: Search and A*  --  Warehouse Robot Navigation.

A goal-based search agent that finds a path from S to G on an ASCII warehouse
map.  The robot moves Up, Down, Left or Right; every move costs 1.

Search problem  P = (S, A, T, s0, G, c)
  S  : states       -> (row, col) grid positions that are not obstacles
  A  : actions      -> Up, Down, Left, Right
  T  : transition   -> result(state, action) = neighbouring cell
  s0 : initial state-> position of 'S'
  G  : goal states  -> { position of 'G' }
  c  : cost         -> 1 per move

Algorithms implemented
  * astar(...)  A* search,   f(n) = g(n) + h(n)
  * bfs(...)    Breadth-First Search (blind / uninformed)

Heuristics (for Task 6)
  * manhattan   |x - xG| + |y - yG|        (default, admissible)
  * zero        h(n) = 0                   (A* behaves like uniform-cost search)
  * euclidean   sqrt((x-xG)^2 + (y-yG)^2)  (admissible, but less informed)
  * double      2 * manhattan              (NOT admissible)

Usage
  python search_agent.py                       # A* with Manhattan on the lab map
  python search_agent.py --algo bfs            # BFS on the lab map
  python search_agent.py --heuristic zero      # A* with h = 0
  python search_agent.py --compare             # all experiments in one table
  python search_agent.py --map mymap.txt       # use your own map file
"""

from __future__ import annotations

import argparse
import heapq
import math
from collections import deque
from typing import Callable, Dict, List, Optional, Tuple

# ---------------------------------------------------------------------------
# Maps
# ---------------------------------------------------------------------------

LAB_MAP = """\
#################
#S....#.........#
#.###.#.#######.#
#...#.#.......#.#
###.#.#######.#.#
#...#.........#.#
#.###########.#.#
#.............#G#
#################"""

State = Tuple[int, int]          # STATE: (row, col)

# ACTIONS: name -> (row change, col change)
ACTIONS: Dict[str, Tuple[int, int]] = {
    "Up": (-1, 0),
    "Down": (1, 0),
    "Left": (0, -1),
    "Right": (0, 1),
}

STEP_COST = 1                    # COST c: every move costs 1


class Warehouse:
    """The environment: an ASCII grid with obstacles, a start and a goal."""

    def __init__(self, text: str):
        self.grid: List[str] = [line for line in text.strip("\n").splitlines()]
        self.start: State = self._find("S")      # INITIAL STATE s0
        self.goal: State = self._find("G")       # GOAL G

    def _find(self, symbol: str) -> State:
        for r, row in enumerate(self.grid):
            c = row.find(symbol)
            if c != -1:
                return (r, c)
        raise ValueError(f"Map has no '{symbol}'")

    def is_free(self, s: State) -> bool:
        """A cell is valid if it is inside the map and is not an obstacle."""
        r, c = s
        return 0 <= r < len(self.grid) and 0 <= c < len(self.grid[r]) and self.grid[r][c] != "#"

    def result(self, s: State, action: str) -> State:
        """TRANSITION T(s, a): the cell reached by applying the action."""
        dr, dc = ACTIONS[action]
        return (s[0] + dr, s[1] + dc)

    def successors(self, s: State) -> List[Tuple[str, State]]:
        """Valid (action, next_state) pairs: invalid actions hit '#' or leave the map."""
        return [(a, self.result(s, a)) for a in ACTIONS if self.is_free(self.result(s, a))]

    def is_goal(self, s: State) -> bool:
        """GOAL TEST."""
        return s == self.goal

    def draw(self, path: Optional[List[State]]) -> str:
        rows = [list(r) for r in self.grid]
        for (r, c) in path or []:
            if rows[r][c] == ".":
                rows[r][c] = "*"
        return "\n".join("".join(r) for r in rows)


# ---------------------------------------------------------------------------
# Heuristics  h(n)
# ---------------------------------------------------------------------------

def h_manhattan(s: State, g: State) -> float:
    return abs(s[0] - g[0]) + abs(s[1] - g[1])


def h_zero(s: State, g: State) -> float:
    return 0


def h_euclidean(s: State, g: State) -> float:
    return math.hypot(s[0] - g[0], s[1] - g[1])


def h_double(s: State, g: State) -> float:
    return 2 * h_manhattan(s, g)


HEURISTICS: Dict[str, Callable[[State, State], float]] = {
    "manhattan": h_manhattan,
    "zero": h_zero,
    "euclidean": h_euclidean,
    "double": h_double,
}


# ---------------------------------------------------------------------------
# Search result and path reconstruction
# ---------------------------------------------------------------------------

class Result:
    def __init__(self, found: bool, path: Optional[List[State]], expanded: int):
        self.found = found
        self.path = path
        self.length = len(path) - 1 if path else None     # number of moves
        self.expanded = expanded


def reconstruct_path(came_from: Dict[State, Optional[State]], goal: State) -> List[State]:
    """PATH RECONSTRUCTION: follow parent pointers from the goal back to the start."""
    path = [goal]
    while came_from[path[-1]] is not None:
        path.append(came_from[path[-1]])
    path.reverse()
    return path


# ---------------------------------------------------------------------------
# A* search
# ---------------------------------------------------------------------------

def astar(env: Warehouse, heuristic: Callable[[State, State], float] = h_manhattan) -> Result:
    start, goal = env.start, env.goal

    g: Dict[State, float] = {start: 0}                  # g(n): best known cost from start
    came_from: Dict[State, Optional[State]] = {start: None}
    tie = 0                                             # tie-breaker so the heap never compares states
    h0 = heuristic(start, goal)
    frontier = [(0 + h0, h0, tie, start)]               # FRONTIER: priority queue ordered by f(n)
    closed = set()                                      # VISITED (expanded) states
    expanded = 0

    while frontier:
        f, h, _, s = heapq.heappop(frontier)            # select the node with the lowest f(n)
        if s in closed:                                 # stale entry: already expanded more cheaply
            continue
        closed.add(s)
        expanded += 1

        if env.is_goal(s):                              # goal test when a node is EXPANDED
            return Result(True, reconstruct_path(came_from, s), expanded)

        for action, nxt in env.successors(s):
            if nxt in closed:
                continue
            new_g = g[s] + STEP_COST                    # g(n') = g(n) + c(n, a, n')
            if new_g < g.get(nxt, math.inf):            # found a better route to nxt
                g[nxt] = new_g
                came_from[nxt] = s
                h_val = heuristic(nxt, goal)            # h(n')
                f_val = new_g + h_val                   # f(n') = g(n') + h(n')
                tie += 1
                heapq.heappush(frontier, (f_val, h_val, tie, nxt))

    return Result(False, None, expanded)                # frontier empty -> no solution


# ---------------------------------------------------------------------------
# Breadth-First Search (blind search, for Task 5)
# ---------------------------------------------------------------------------

def bfs(env: Warehouse) -> Result:
    start = env.start
    frontier = deque([start])                           # FIFO queue
    came_from: Dict[State, Optional[State]] = {start: None}   # also the visited set
    expanded = 0

    while frontier:
        s = frontier.popleft()
        expanded += 1
        if env.is_goal(s):
            return Result(True, reconstruct_path(came_from, s), expanded)
        for action, nxt in env.successors(s):
            if nxt not in came_from:
                came_from[nxt] = s
                frontier.append(nxt)

    return Result(False, None, expanded)


# ---------------------------------------------------------------------------
# Reporting
# ---------------------------------------------------------------------------

def solve(env: Warehouse, algo: str = "astar", heuristic: str = "manhattan") -> Result:
    return bfs(env) if algo == "bfs" else astar(env, HEURISTICS[heuristic])


def report(env: Warehouse, res: Result, title: str) -> None:
    print(f"=== {title} ===")
    print(f"Start {env.start}  Goal {env.goal}")
    if not res.found:
        print(f"Solution found : NO  (no path exists)")
        print(f"States expanded: {res.expanded}\n")
        return
    print("Solution found : YES")
    print(f"Path length    : {res.length} moves")
    print(f"States expanded: {res.expanded}")
    print("Path           : " + " -> ".join(str(p) for p in res.path))
    print(env.draw(res.path) + "\n")


def compare(env: Warehouse) -> None:
    runs = [("BFS", "bfs", "manhattan")] + [
        (f"A* h={name}", "astar", name) for name in ("manhattan", "zero", "euclidean", "double")
    ]
    print(f"{'Algorithm':<18}{'Found':<8}{'Length':<8}{'Expanded':<8}")
    print("-" * 42)
    for label, algo, h in runs:
        r = solve(env, algo, h)
        print(f"{label:<18}{'yes' if r.found else 'no':<8}{str(r.length):<8}{r.expanded:<8}")


def main() -> None:
    p = argparse.ArgumentParser(description="Warehouse search agent (A* / BFS)")
    p.add_argument("--algo", choices=["astar", "bfs"], default="astar")
    p.add_argument("--heuristic", choices=list(HEURISTICS), default="manhattan")
    p.add_argument("--map", help="path to a text file containing an ASCII map")
    p.add_argument("--compare", action="store_true", help="run all algorithms/heuristics")
    args = p.parse_args()

    text = open(args.map).read() if args.map else LAB_MAP
    env = Warehouse(text)
    if args.compare:
        compare(env)
    else:
        title = "BFS" if args.algo == "bfs" else f"A* (h = {args.heuristic})"
        report(env, solve(env, args.algo, args.heuristic), title)


if __name__ == "__main__":
    main()
