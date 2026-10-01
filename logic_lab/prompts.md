# LLM Prompts Used (Appendix)

LLM used: Claude (Anthropic).

## Prompt 1: Implement the planner (Task 2)

> I want to implement a simple planning agent in Python.
> Represent a state as a set of logical propositions.
> Each action should contain: a name; positive preconditions; negative preconditions; positive effects; negative effects.
> An action is applicable if all of its preconditions are satisfied by the current state. When an action is applied: (1) remove its negative effects from the state; (2) add its positive effects to the state.
> Use breadth-first search to find a sequence of actions that achieves a specified goal. The program should also: detect when no plan exists; print the resulting sequence of actions; print the states reached after each action.
> Explain the implementation and identify any assumptions you make.
>
> The domain: locations A, B, C, connected A–B and B–C in both directions. Initial state {At(Robot,A), At(Package,A)}; goal {At(Package,C)}. Actions Move(X,Y), PickUp(Package,L) and Drop(Package,L) with the preconditions and effects given in the lab sheet.

## Prompt 2: Independent validator and tests (Task 3)

> Add a function validate_plan(initial, goal, plan) that does not use the search. It executes the plan one action at a time, checks every action's preconditions in the state where it is executed, and checks the goal at the end. Then write unittest tests for: (A) the original problem; (B) an impossible problem with the PickUp action removed; (C) the same problem with extra irrelevant actions added, checking that the robot reaching C is not treated as the package reaching C.

## Prompt 3: Self-verification (Task 5)

> For every action in the plan PickUp(Package,A), Move(A,B), Move(B,C), Drop(Package,C), identify its preconditions and show that those preconditions are satisfied in the state in which the action is executed.

## Prompt 4: Prolog (Tasks 6–8)

> Write a SWI-Prolog file planner.pl with the facts connected(a,b), connected(b,a), connected(b,c), connected(c,b), the rules can_move(X,Y) :- connected(X,Y) and valid_move(X,Y) :- connected(X,Y), a rule valid_path/1 that checks a whole list of moves, and the wet_road / slippery / reduce_speed example.
