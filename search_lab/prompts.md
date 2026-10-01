# LLM Prompts Used (Appendix)

LLM used: Claude (Anthropic).

## Prompt 1: Generate A*

> I am implementing a simple goal-based search agent in Python.
> The environment is a grid represented by an ASCII map (map below). The agent starts at S and must reach G. The symbols # represent obstacles and . represents free cells. The agent can move up, down, left, or right, and every movement has cost 1.
> Implement A* search. Use Manhattan distance as the heuristic: h(n) = |x − xG| + |y − yG|.
> The program should:
> - represent grid positions as states (row, col) tuples;
> - represent the warehouse as a list of strings;
> - maintain a frontier as a priority queue ordered by f(n);
> - calculate g(n), h(n) and f(n) explicitly;
> - avoid repeatedly expanding the same state (use a closed set);
> - reconstruct the path using parent pointers when the goal is reached;
> - report whether a solution was found, the path, its length, and the number of states expanded;
> - report failure (not loop forever) if no path exists.
> Keep the implementation simple and explain the main components of the code.
>
> ```
> #################
> #S....#.........#
> #.###.#.#######.#
> #...#.#.......#.#
> ###.#.#######.#.#
> #...#.........#.#
> #.###########.#.#
> #.............#G#
> #################
> ```

## Prompt 2: Add BFS for comparison (Task 5)

> Add a Breadth-First Search function to the same program that uses the same Warehouse class and returns the same result object (found, path, length, states expanded), so that BFS and A* can be compared on the same map.

## Prompt 3: Heuristic variants (Task 6)

> Explain why Manhattan distance is an appropriate heuristic when the robot can only move horizontally and vertically. Then add three alternative heuristics that can be selected from the command line: h(n) = 0, Euclidean distance, and 2 × Manhattan distance. Add a --compare option that prints found / path length / states expanded for BFS and every heuristic.

## Prompt 4: Tests (Task 3)

> Write unittest tests for: (1) the original map, (2) a trivial map where G is next to S, (3) a map where G is unreachable, which must report failure, and (4) a map with several paths, checking that the returned path is a shortest one by comparing with BFS. Load the test maps from text files in a maps/ folder.
