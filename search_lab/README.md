# Lab 2: Search and A*: Warehouse Robot Navigation

A goal-based search agent that finds a path from `S` to `G` in a warehouse using **A\* search** with the Manhattan-distance heuristic. For comparison it also includes **Breadth-First Search** and three alternative heuristics.

## How to run (reproducing every experiment)

Python 3.8+ only; no external libraries are needed.

```bash
python search_agent.py                                   # Test 1: A* (Manhattan) on the lab map
python search_agent.py --algo bfs                        # BFS on the lab map
python search_agent.py --map maps/test2_trivial.txt      # Test 2
python search_agent.py --map maps/test3_no_solution.txt  # Test 3
python search_agent.py --map maps/test4_alternative_paths.txt   # Test 4
python search_agent.py --compare                         # Task 5 + 6 table on the lab map
python search_agent.py --map maps/open_warehouse.txt --compare  # Task 6 on an open map
python search_agent.py --heuristic double                # one specific heuristic
python -m unittest -v                                    # run all automated tests
```

| File | Contents |
|---|---|
| `search_agent.py` | Environment, A\*, BFS, heuristics, reporting |
| `test_search_agent.py` | Automated tests (Tests 1–4, plus Task 5/6 checks) |
| `maps/` | Test maps used in the experiments |
| `prompts.md` | Appendix: the prompts given to the LLM |

The warehouse map used in the lab:

```
#################
#S....#.........#
#.###.#.#######.#
#...#.#.......#.#
###.#.#######.#.#
#...#.........#.#
#.###########.#.#
#.............#G#
#################
```

---

## Task 0: The Search Problem

| Component | Specification |
|---|---|
| **State S** | The robot's position as a pair `(row, col)`; the set of states is every cell that is not `#` |
| **Actions A** | `{Up, Down, Left, Right}` |
| **Transition T** | `T((r,c), Up) = (r-1,c)`, `Down → (r+1,c)`, `Left → (r,c-1)`, `Right → (r,c+1)`. This applies only if the new cell is inside the map and is not `#` |
| **Initial state s₀** | Position of `S`: `(1, 1)` |
| **Goal G** | `{ (7, 15) }`, the position of `G` |
| **Cost c** | `c(s, a, s') = 1` for every move, so the path cost is the number of moves |

**(a) What information is needed to specify a state?**
Only the robot's position `(row, col)`. The map is fixed and doesn't change, so it is part of the problem definition rather than the state.

**(b) What makes an action invalid?**
An action is invalid if the resulting cell is an obstacle (`#`) or lies outside the grid.

**(c) Is this a deterministic search problem?**
Yes. Each action from a given state always leads to exactly one known next state. The environment is also fully observable, static and discrete.

**(d) What would constitute a solution?**
A sequence of valid actions that leads from `s₀` to the goal state. An **optimal** solution is one with the lowest total cost, which here means the fewest moves.

---

## Task 1: Design of the Agent

1. **State representation:** a tuple `(row, col)`. Tuples are hashable, so they can be used as dictionary keys and set members.
2. **Warehouse representation:** a list of strings, one per map row; `grid[r][c]` gives the symbol in a cell.
3. **Valid actions:** for each of the 4 moves, compute the neighbouring cell and keep it only if `is_free()` (inside the map and not `#`).
4. **Goal recognition:** `is_goal(s)` checks `s == goal`. In A\* the test is done when a state is **expanded** (removed from the frontier), not when it is generated, which is required for A\* to be optimal.
5. **Frontier contents:** for each entry, `(f(n), h(n), tie-breaker, state)`. `g(n)` and the parent pointer are kept in dictionaries `g` and `came_from`.
6. **Path reconstruction:** `came_from[n]` stores the parent of each state. When the goal is reached, follow parents from the goal back to the start and reverse the list.

**Reported on termination:** whether a solution was found, the path, the path length (number of moves) and the number of states expanded. The map is also printed with the path marked `*`.

---

## Task 2: LLM-generated A\*

The LLM (Claude) was given a prompt based on the design above. The exact prompts are in [`prompts.md`](prompts.md). The generated program was run on the lab map and then tested systematically (Task 3) rather than assumed to be correct.

---

## Task 3: Testing

| Test | Map | Expected | Result | Path length | States expanded |
|---|---|---|---|---|---|
| 1. Original warehouse | lab map | path found | ✅ found | 40 | 64 |
| 2. Trivial case | `maps/test2_trivial.txt` | 1 move | ✅ found | 1 | 2 |
| 3. No solution | `maps/test3_no_solution.txt` | failure, no infinite loop | ✅ reports "no path" | n/a | 9 |
| 4. Alternative paths | `maps/test4_alternative_paths.txt` | a shortest path (8) | ✅ found, length 8 = BFS optimum | 8 | 9 |

**Test 1 output (A\*, Manhattan):**

```
Solution found : YES
Path length    : 40 moves
States expanded: 64
#################
#S****#*********#
#.###*#*#######*#
#...#*#*******#*#
###.#*#######*#*#
#...#*********#*#
#.###########.#*#
#.............#G#
#################
```

The robot must go down the left corridor, along row 5, back up through the middle, along the top row and then down the right-hand column to reach `G`. `G` can only be entered from the cell above it.

**Test 2** (`#SG##`): the path `(1,1) → (1,2)` is found in one move.

**Test 3**: the goal is completely enclosed by walls. All 9 reachable cells are expanded, the frontier becomes empty, and the program prints *"no path exists"* instead of looping.

**Test 4** map:
```
#######
#S....#
#.###.#
#.....#
#.###.#
#....G#
#######
```
There are several routes, along the left side, the right side, or through the middle row. The Manhattan distance from S to G is 8, so no path can be shorter than 8. A\* returns a path of exactly 8 moves, the same as BFS, which is guaranteed optimal for unit costs. So the returned path is a shortest path.

All of these are also checked automatically: `python -m unittest -v` gives **6 tests, all OK**.

---

## Task 4: Inspecting the A\* Code

| Concept | Where it appears in `search_agent.py` |
|---|---|
| State | `State = Tuple[int, int]` (line 59), a `(row, col)` tuple |
| Action | `ACTIONS` dictionary (line 62): Up/Down/Left/Right → (Δrow, Δcol) |
| Transition | `Warehouse.result()` (line 92) and `Warehouse.successors()` (line 97), which also filters out invalid moves using `is_free()` (line 87) |
| Goal test | `Warehouse.is_goal()` (line 101), called in `astar()` when a node is expanded |
| g(n) | Dictionary `g` (line 169); updated with `new_g = g[s] + STEP_COST` |
| h(n) | `h_manhattan()` (line 117); called as `heuristic(nxt, goal)` inside `astar()` |
| f(n) | `f_val = new_g + h_val` (line 195) |
| Frontier | `frontier` list used as a heap (line 173), with `heapq.heappush` / `heapq.heappop` |
| Visited states | `closed` set (line 174) |
| Path reconstruction | `reconstruct_path()` (line 153), which follows `came_from` parent pointers |

**(a) Frontier data structure:** a **binary heap (priority queue)** from Python's `heapq` module, holding tuples `(f, h, tie, state)`.

**(b) Choosing the next state:** `heapq.heappop` removes the entry with the **lowest f(n)**. Ties are broken by lower h(n), which prefers states closer to the goal, and then by insertion order.

**(c) Where the heuristic is calculated:** in the `heuristic(nxt, goal)` call each time a successor is generated. The default is `h_manhattan`; it is passed in as a function so it can be swapped for Task 6.

**(d) Is f(n) = g(n) + h(n) explicitly calculated?** Yes: `f_val = new_g + h_val`, and `f_val` is the first element of the heap entry, so it is the priority.

**(e) Preventing repeated exploration:** in two ways.
1. A **closed set** stores expanded states. A popped state that is already closed is skipped as a stale entry, and successors that are already closed are not pushed again.
2. A successor is only pushed if the new `g` is **better** than the best `g` known so far (`new_g < g.get(nxt, inf)`).

---

## Task 5: A\* vs Blind Search (BFS)

**Lab map:**

| Measure | BFS | A\* (Manhattan) |
|---|---|---|
| Solution found | Yes | Yes |
| Path length | 40 | 40 |
| States expanded | 64 | 64 |

Because this result was surprising, both algorithms were also run on two other maps:

| Map | BFS expanded | A\* expanded | Path length (both) |
|---|---|---|---|
| `test4_alternative_paths.txt` | 19 | **9** | 8 |
| `open_warehouse.txt` | 58 | **37** | 16 |

**(a) Did both find a solution?** Yes, on every map that has one.

**(b) Same path length?** Yes, 40 on the lab map. Both are optimal here: BFS because every step costs 1, and A\* because Manhattan distance is admissible.

**(c) Which expanded fewer states?** On the lab map, **neither**: both expanded 64. On the more open maps, A\* expanded far fewer (9 vs 19, and 37 vs 58).

**(d) Why might A\* expand fewer states?** A\* uses the heuristic to estimate how far each state is from the goal and expands the most promising states first, so it doesn't spread out evenly in all directions as BFS does.

**Why it doesn't help on the lab map:** the lab map is a maze in which the only route to `G` first leads **away** from the goal (down the left side and back along the top). Manhattan distance ignores walls, so it badly underestimates the remaining cost of many states. A\* must expand every state with `f(n) < 40` (the optimal cost), and in this maze that is almost every reachable cell, the same set BFS explores.

So, in answer to the "Think about it" question, *what information does the algorithm use to decide where to search next?*: BFS uses only the depth of a state. A\* uses depth plus an estimate of the remaining distance. That extra information only helps when the estimate is informative. In a twisting maze, straight-line-style estimates carry little information.

---

## Task 6: Investigating the Heuristic

**Why Manhattan distance is appropriate:** the robot can only move horizontally and vertically, one cell per move at cost 1. Even with no obstacles at all, getting from `(x, y)` to `(x_G, y_G)` takes at least `|x − x_G|` horizontal moves and `|y − y_G|` vertical moves. So Manhattan distance is the exact cost in an empty grid and can **never overestimate** the true cost when walls are added. It is **admissible** (h(n) ≤ h\*(n)) and also consistent, so A\* with it is optimal. It is the largest such simple estimate, so it is the most informed.

### Results

**Lab map** (`python search_agent.py --compare`):

| Heuristic | Found | Path length | States expanded |
|---|---|---|---|
| Manhattan | yes | 40 | 64 |
| h = 0 | yes | 40 | 64 |
| Euclidean | yes | 40 | 64 |
| 2 × Manhattan | yes | 40 | 64 |

On the lab map the maze has essentially one route, so every heuristic gives the same result. To see the effect of the heuristic, the experiment was repeated on an open warehouse, `maps/open_warehouse.txt`:

```
###############
#S............#
#.............#
#....#####....#
#........#....#
#........#...G#
###############
```

**Open warehouse** (`python search_agent.py --map maps/open_warehouse.txt --compare`):

| Heuristic | Admissible? | Found | Path length | States expanded |
|---|---|---|---|---|
| BFS (reference) | n/a | yes | 16 | 58 |
| h = 0 | yes | yes | 16 | 58 |
| Euclidean | yes | yes | 16 | 44 |
| **Manhattan** | yes | yes | **16** | **37** |
| 2 × Manhattan | **no** | yes | **18 (not optimal)** | 35 |

**1. h(n) = 0:** A\* becomes **uniform-cost search**. With unit costs this behaves like BFS: still optimal, but it expands the same number of states as BFS (58), because it has no information about where the goal is.

**2. Euclidean distance:** still admissible, because a straight line is never longer than a grid path, so the path is still optimal (16). It is **smaller** than Manhattan distance for most states, so it is less informed and A\* expands more states (44 vs 37).

**3. 2 × Manhattan:** this **overestimates** the true cost, so it is **not admissible**. A\* becomes greedier: it expanded slightly fewer states (35) but returned a **path of 18 moves instead of the optimal 16**:

```
2 × Manhattan (18 moves)      Manhattan (16 moves)
###############               ###############
#S............#               #S............#
#*..*******...#               #**********...#
#****#####*...#               #....#####*...#
#........#*...#               #........#*...#
#........#***G#               #........#***G#
###############               ###############
```

### What happens when the heuristic is too optimistic or too aggressive?

- **Too optimistic** (h too small, e.g. h = 0 or Euclidean): A\* is still **optimal**, but it explores more states and becomes less efficient. At h = 0 it is no better than blind search.
- **Too aggressive** (h > h\*, e.g. 2 × Manhattan): A\* may expand fewer states and run faster, but it **loses its optimality guarantee** and can return a longer path, as the experiment shows.
- **The best heuristic** is as large as possible **without** overestimating. Among the heuristics tested, Manhattan distance is the best for this 4-directional grid.

---

## Task 7: Evaluating the LLM-generated Agent

> **Note:** edit these answers so they describe your own experience with the LLM.

**What I designed myself:** the problem formulation (Task 0), the state/frontier/path-reconstruction design (Task 1), the test cases, and the additional open-warehouse map used to make the heuristic effect visible.
**What the LLM suggested:** the code structure, the heap entry `(f, h, tie, state)` with tie-breaking, the closed set plus "better g" check, and the command-line options.
**What I accepted:** the A\* and BFS implementations and the Manhattan heuristic.
**What I changed/added:** the extra test maps, the `--compare` mode, and the automated unit tests.
**What I tested:** Tests 1–4, the BFS comparison and all four heuristics, as shown in the tables above.

1. **What parts were correct immediately?** The A\* loop, the Manhattan heuristic, the path reconstruction and the "no path" handling all worked on the first run.
2. **Any bugs or design problems?** The program ran correctly, but the original map produced a surprising result: A\* expanded exactly as many states as BFS. This was not a bug. It was a property of the maze, but it would be easy to wrongly conclude that A\* is "broken" or that the heuristic was ignored. It is also a design point that the goal test must happen when a node is expanded, not when it is generated; otherwise A\* can return non-optimal paths with some heuristics.
3. **How were problems found?** By comparing against a known-correct reference (BFS) and by building maps where the expected answer is known in advance: the trivial, no-solution and alternative-paths maps.
4. **Unfamiliar terminology or data structures?** `heapq` (a binary heap) and the use of a tie-breaker counter in heap entries, which is needed because Python cannot compare some entries directly when the f values are equal.
5. **Did I modify the code?** Yes: I added the heuristic variants, the comparison mode, map loading from files and the tests.
6. **Most useful tests?** The **no-solution** test, which checks termination, and the **alternative-paths** test compared against BFS, which checks optimality. The open-warehouse experiment was most useful for understanding the heuristic.
7. **Could I have trusted it without testing?** No. The output on the lab map looked plausible, but a plausible path does not prove it is the shortest. Only the comparison with BFS and the hand-checkable maps showed it is optimal.
8. **What I now understand about A\*:** A\* is only as good as its heuristic. On a maze where walls force detours, an admissible but uninformed heuristic gives no advantage over BFS. Making the heuristic larger speeds up the search but can break optimality once it overestimates.

---

## Final Reflection

**1. Why formulate the search problem before writing the algorithm?**
The formulation fixes what a state is, which actions are legal, what counts as success and what is being optimised. Without it, it is impossible to tell whether generated code is correct, because there is no specification to test against. For example, deciding that the cost is "number of moves" is what made it possible to check optimality against BFS. Asking an LLM for code before this is done just produces a program whose assumptions you haven't checked.

**2. In what sense is A\* an "informed" search algorithm?**
Blind searches such as BFS and DFS use only the structure of the search tree (depth or order of generation). A\* also uses **problem-specific knowledge** in the form of the heuristic h(n), an estimate of the remaining cost to the goal. It ranks states by `f(n) = g(n) + h(n)`, the estimated total cost of a solution through n, and so directs the search towards the goal.

**3. Why does the choice of heuristic matter?**
The heuristic controls both **efficiency** and **optimality**. A heuristic that is too weak (h = 0) wastes effort, and A\* degrades to uniform-cost search. A heuristic that overestimates (2 × Manhattan) can make A\* return a non-optimal path. An admissible, well-informed heuristic such as Manhattan distance gives optimal paths with the fewest expansions. The experiments also showed that even a good heuristic helps little when obstacles make it a poor estimate, as in the lab maze.

**4. What did the LLM contribute?**
It quickly turned the design into clean, working Python, suggested sensible implementation details (heap-based frontier, tie-breaking, closed set), explained why Manhattan distance is admissible, and helped generate the comparison and test code. It acted as a fast, knowledgeable assistant for implementation, but the problem formulation, the choice of tests and the interpretation of results had to come from me.

**5. What could go wrong if LLM code is accepted without testing?**
The code might look right but contain subtle errors: testing the goal when a node is generated instead of expanded, a missing visited set causing infinite loops on unreachable goals, an off-by-one in grid indexing, or an inadmissible heuristic silently producing non-optimal paths. These may not show up on a single example. In a real warehouse this could mean robots taking inefficient routes, freezing when no path exists, or colliding with shelves. **Working output ≠ validated algorithm**: the engineer remains responsible for testing and understanding the system.
