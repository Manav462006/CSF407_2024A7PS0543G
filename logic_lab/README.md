# Lab 3: Logical Reasoning for Planning

A simple **STRIPS-style planning agent** for a warehouse robot. **Logic** decides which actions are applicable and how they change the state; **breadth-first search** explores sequences of actions until the goal holds. An independent plan validator and a Prolog knowledge base are used to check the plans.

> **Logic + Search = Planning**

## How to run

Python 3.8+; no external libraries needed. The optional Prolog part needs [SWI-Prolog](https://www.swi-prolog.org/), or you can paste `planner.pl` into the online [SWISH](https://swish.swi-prolog.org/).

```bash
python planner.py           # Test A: solve the warehouse problem
python planner.py --all     # Tests A, B and C
python -m unittest -v       # 10 automated tests
swipl planner.pl            # then type queries such as  ?- can_move(a,b).
```

| File | Contents |
|---|---|
| `planner.py` | State/action representation, logic (`applicable`, `apply`, `satisfies`), BFS planner, independent validator |
| `test_planner.py` | Automated tests (Task 0 checks, manual plan, Tests A/B/C) |
| `planner.pl` | Prolog knowledge base for Tasks 6–8 |
| `prompts.md` | Appendix: prompts given to the LLM |

---

## Task 0: The Planning Problem

**(a) Initial state:** `I = { At(Robot,A), At(Package,A) }`

**(b) Goal:** `G = { At(Package,C) }`

**(c) Actions:**
`Move(A,B)`, `Move(B,A)`, `Move(B,C)`, `Move(C,B)`, `PickUp(Package,L)` and `Drop(Package,L)` for `L ∈ {A, B, C}`.

**(d) Preconditions and effects:**

| Action | Preconditions | Effects (add) | Effects (delete) |
|---|---|---|---|
| `Move(X,Y)` (X, Y connected) | `At(Robot,X)` | `At(Robot,Y)` | `At(Robot,X)` |
| `PickUp(Package,L)` | `At(Robot,L)`, `At(Package,L)`, ¬`Holding(Package)` | `Holding(Package)` | `At(Package,L)` |
| `Drop(Package,L)` | `At(Robot,L)`, `Holding(Package)` | `At(Package,L)` | `Holding(Package)` |

¬`Holding(Package)` is a negative precondition: the robot can't pick up a package it already holds. The sheet doesn't list it, but it is implied, and it was added in the design.

**Which actions are applicable in I?**

- **`PickUp(Package,A)`: applicable.** Both preconditions, `At(Robot,A)` and `At(Package,A)`, are in `I`, and `Holding(Package)` is not. So `I ⊨ Preconditions(PickUp(Package,A))`.
- **`Drop(Package,C)`: not applicable.** It needs `At(Robot,C)` and `Holding(Package)`, and **neither** is true in `I`. The robot is at A and is not holding anything.
- Also applicable in `I`: `Move(A,B)`, because `At(Robot,A)` holds. Every other action has at least one false precondition.

> An action is not applicable just because it appears in the action list. All of its preconditions must be satisfied in the current state.

---

## Task 1: Plan Constructed by Hand

Plan: **`PickUp(Package,A)`, `Move(A,B)`, `Move(B,C)`, `Drop(Package,C)`**

| State | Facts | Action that produced it |
|---|---|---|
| S₀ | At(Robot,A), At(Package,A) | (initial) |
| S₁ | At(Robot,A), Holding(Package) | PickUp(Package,A) |
| S₂ | At(Robot,B), Holding(Package) | Move(A,B) |
| S₃ | At(Robot,C), Holding(Package) | Move(B,C) |
| S₄ | At(Robot,C), **At(Package,C)** | Drop(Package,C) |

S₄ ⊨ G, so the plan is valid.

**Note:** the lab sheet's hint lists `Move(A,B)`, `PickUp(Package,B)`, … in that order. Followed literally, that sequence is **invalid**: after `Move(A,B)` the package is still at A, so `PickUp(Package,B)` fails its precondition `At(Package,B)`. The robot has to pick the package up **at A before** moving. The validator confirms this (see test `test_lab_example_plan_invalid`):

```
step 1: Move(A,B) OK
step 2: PickUp(Package,B) NOT applicable (missing ['At(Package,B)'], forbidden [])
```

---

## Task 2: LLM-generated planner

The prompt from the lab sheet was given to the LLM, along with the domain (see [`prompts.md`](prompts.md)). The generated program is `planner.py`.

**Assumptions in the implementation:**
- **Closed-world assumption:** any proposition not in the state set is false.
- States are stored as `frozenset`s so they can be put in the visited set.
- Actions are **grounded**: one action object for each concrete location or connection, generated from the templates.
- While the package is held it has **no** `At(Package, …)` fact. It is only located again when it is dropped.
- The goal test is subset inclusion: `G ⊆ S`.

**Where the specification appears in the code (Think About It):**

| Idea | Question | Where in `planner.py` |
|---|---|---|
| Preconditions | When is an action applicable? | `applicable(state, action)`: `pre_pos ⊆ state` and `pre_neg ∩ state = ∅` |
| Effects | How does the state change? | `apply(state, action)`: `(state − delete) ∪ add` |
| Goal | When does planning terminate? | `satisfies(state, goal)`, checked each time a state is taken from the frontier in `bfs_plan` |
| BFS | How are alternative plans explored? | `bfs_plan`: a FIFO `deque` frontier; every applicable action generates a successor; `parent` dict is the visited set and is used to rebuild the plan |

---

## Task 3: Testing

Output of `python planner.py --all`:

```
=== Test A: original warehouse problem ===
Initial state : {At(Package,A), At(Robot,A)}
Goal          : {At(Package,C)}
States explored: 8
Result        : plan with 4 actions
  S0: {At(Package,A), At(Robot,A)}
  PickUp(Package,A)    -> S1: {At(Robot,A), Holding(Package)}
  Move(A,B)            -> S2: {At(Robot,B), Holding(Package)}
  Move(B,C)            -> S3: {At(Robot,C), Holding(Package)}
  Drop(Package,C)      -> S4: {At(Package,C), At(Robot,C)}
Independent validation: VALID

=== Test B: impossible problem (no PickUp action) ===
States explored: 3
Result        : No plan found

=== Test C: irrelevant actions added (robot moves / recharges without the package) ===
States explored: 21
Result        : plan with 4 actions   (same plan as Test A)
Independent validation: VALID

Check: the robot alone can reach C with Move(A,B), Move(B,C),
but that must NOT count as delivering the package:
  step 1: Move(A,B) OK
  step 2: Move(B,C) OK
  goal NOT satisfied, final state ['At(Package,A)', 'At(Robot,C)']
```

### Results

| Test | Initial state | Goal | Plan found? | Plan | Actually valid? |
|---|---|---|---|---|---|
| **A** Solvable | At(Robot,A), At(Package,A) | At(Package,C) | Yes (4 actions) | PickUp(P,A), Move(A,B), Move(B,C), Drop(P,C) | **Yes**: every precondition was checked step by step by the independent validator |
| **B** Impossible (PickUp removed) | same | same | **No**: "No plan found" | n/a | Correct: the planner explored the 3 reachable states (robot at A, B, C) and stopped without inventing an action |
| **B2** Impossible (C disconnected) | same | same | No | n/a | Correct |
| **C** Irrelevant actions (`Wait`, `Recharge(Robot,B)`) | same | same | Yes (4 actions) | same as A; no irrelevant actions used | **Yes**. The robot-only plan `Move(A,B), Move(B,C)` is correctly **rejected**: the robot is at C but the package is still at A |

Notes:
- In Test C the planner explored 21 states instead of 8, because the irrelevant actions create extra states (charged or not, waited or not). BFS still returns the shortest plan, and the irrelevant actions are not included.
- **Bug found during testing:** the first version of the printing code crashed with `TypeError: unsupported format string passed to Action.__format__` because it formatted an `Action` object with `:<20`. The planning logic was correct; the fix was to format `a.name` instead. This only showed up when the program was actually run.

`python -m unittest -v`: **10 tests, all OK.**

---

## Task 4: Logic and Search

Completed flow:

```
Current state
     ↓
Check action preconditions        (logic: S ⊨ Preconditions(a)?)
     ↓
Select an applicable action       ← the missing step
     ↓
Generate successor state          (S' = Apply(S, a))
     ↓
Search over alternatives          (BFS frontier of states)
     ↓
Goal?                             (S ⊨ G?  yes → return plan, no → continue)
```

**How they work together:** **logical reasoning** answers local questions about a single state. Is this action allowed here, i.e. are its preconditions entailed by the current facts? What is true after applying it, i.e. its effects? And is the goal entailed by this state? On its own, logic doesn't say *which* of the allowed actions to take, or in what order. **Search** handles that global question: BFS systematically tries the applicable actions from each state, keeps a frontier of states still to explore, avoids revisiting states, and stops at the first state that satisfies the goal. Because BFS explores in order of plan length, the plan it returns is a shortest one.

> **Logic determines what is possible; search determines what to try.** This is the same graph search as the previous module, except that a node is a set of propositions instead of a grid cell, and the successor function is defined by preconditions and effects.

---

## Task 5 (Optional): Can the LLM verify its own plan?

When asked to justify the plan step by step, the LLM produced:

| Step | Action | Preconditions | Satisfied in |
|---|---|---|---|
| 1 | PickUp(Package,A) | At(Robot,A), At(Package,A), ¬Holding(Package) | S₀ ✔ |
| 2 | Move(A,B) | At(Robot,A) | S₁ ✔ (PickUp doesn't change the robot's location) |
| 3 | Move(B,C) | At(Robot,B) | S₂ ✔ |
| 4 | Drop(Package,C) | At(Robot,C), Holding(Package) | S₃ ✔ → S₄ contains At(Package,C) ✔ |

This matches the state transitions actually computed by `planner.py` and checked by `validate_plan`.

**Which should be trusted more?** **(b) the independently executed state transitions.** The LLM's explanation is generated text: it produces the kind of justification a correct answer would have, but nothing guarantees each claim was checked. It could say a precondition holds when it doesn't, and the explanation would read just as convincingly. The validator mechanically applies the action definitions to the actual state and checks set membership, so its result follows from the specification. The two agreed here, but only the executed check counts as evidence.

> A generated explanation is not the same as an independent verification.

---

## Task 6 (Optional): Prolog as a plan verifier

`planner.pl` contains the `connected/2` facts and the `can_move/2` rule. Results (SWI-Prolog 9):

```
?- can_move(a,b).    true.
?- can_move(a,c).    false.
```

**(a) Why `true` for `can_move(a,b)`?** Prolog tries the rule `can_move(X,Y) :- connected(X,Y)` with `X = a, Y = b`. Its body becomes the goal `connected(a,b)`, which matches a fact in the knowledge base. The body succeeds, so the head is proved.

**(b) Why can it not establish `can_move(a,c)`?** The body needs `connected(a,c)`, and there is no such fact or any rule that derives it. A and C are only linked **indirectly** via B, and `can_move` only describes a single direct step. Prolog uses the closed-world assumption (*negation as failure*), so what can't be proved is reported as `false`.

**(c) Relationship to `Connected(X,Y) → CanMove(X,Y)`:** the Prolog rule is that implication, universally quantified over X and Y and written backwards: `head :- body` means `body → head`. Prolog answers queries by using the implication with backward chaining: to prove `CanMove(a,b)` it tries to prove `Connected(a,b)`.

---

## Task 7 (Optional): Using Prolog to check a proposed plan

```
?- valid_move(a,b).    true.
?- valid_move(b,c).    true.
?- valid_move(a,c).    false.
```

**Challenge: the planner proposes `Move(a,c)`.** `?- valid_move(a,c).` returns **false**, so the action is **not supported** by the warehouse knowledge. There is no direct connection from A to C, and the robot must go through B. This independent check would catch an incorrect action even if the Python planner or an LLM proposed it.

**Extension:** `valid_path/1` checks a whole plan, requiring each move to be valid and to start where the previous one ended:

```
?- valid_path([move(a,b), move(b,c)]).    true.
?- valid_path([move(a,c)]).               false.
?- valid_path([move(a,b), move(c,b)]).    false.   % robot is at b, not c
```

This is the **Generate → Independent verification** architecture: Python (or an LLM) generates the candidate, and a separate logical system checks it.

---

## Task 8 (Optional): Connecting Prolog to logical reasoning

```
?- reduce_speed.    true.
```

**Why it succeeds:** to prove `reduce_speed`, Prolog uses the rule `reduce_speed :- slippery`, so it must prove `slippery`. Using `slippery :- wet_road`, it must prove `wet_road`, which is a **fact**. The chain succeeds, so the original query succeeds.

**As implications:**

> **WetRoad** (fact) ⇒ **Slippery** (rule: WetRoad → Slippery) ⇒ **ReduceSpeed** (rule: Slippery → ReduceSpeed) ⇒ conclusion: **ReduceSpeed is true**

This is repeated **modus ponens**. Prolog performs it **backwards**, starting from the query and working down to the fact.

---

## Reflection Questions

**1. Why specify preconditions and effects before asking the LLM?**
They are the specification of the problem. With them written down, the LLM's job is only to translate them into code, and the code can be checked against them. Without them, the LLM has to guess the domain rules. It might, for example, forget that the package must be held to be dropped, and there would be nothing to test the program against.

**2. Example error if preconditions were not checked:**
The planner could return `Drop(Package,C)` as a one-step plan from the initial state. It would "teleport" the package to C even though the robot is at A and not holding it. Similarly, `Move(A,C)` could be applied with no connection between A and C, or `PickUp(Package,B)` could pick up a package that isn't there, which is exactly the mistake in the lab sheet's example ordering.

**3. Why is a plan that "looks reasonable" not necessarily valid?**
Validity depends on the **order** and on the exact **state** in which each action is executed. `Move(A,B), PickUp(Package,B), Move(B,C), Drop(Package,C)` contains all the right kinds of actions and reads naturally, but step 2 fails because the package is still at A. A plan is only valid if every precondition holds at the moment its action is executed and the final state entails the goal, and this has to be checked, not judged by appearance.

**4. What did the LLM contribute?**
A clean implementation of the specification: the data structures (`frozenset` states, a frozen `Action` dataclass), the precondition and effect functions, BFS with plan reconstruction, the grounded action generators, the test scaffolding and the Prolog file. It also explained the implementation and listed its assumptions, such as the closed-world assumption.

**5. What had to be verified independently?**
That every action in the returned plan really is applicable in the state where it is executed, by running `validate_plan` separately from the search. Also: that the goal really holds at the end; that impossible problems report "No plan found"; that irrelevant actions are not used and that the robot at C isn't confused with the package at C; that the program actually runs, which revealed the formatting crash; and that the LLM's step-by-step explanation in Task 5 matched the computed transitions.

**6. Where is logical reasoning used?**
In `applicable()`, where `S ⊨ Preconditions(a)` is checked for positive and negative preconditions; in `apply()`, where the effects define the facts of the next state; in `satisfies()`, where `S ⊨ G` is the goal test; in the independent validator; and in the Prolog knowledge base, which derives `can_move`, `valid_move` and `reduce_speed` from facts and rules.

**7. How is planning related to the search algorithms in the previous module?**
Planning **is** state-space search. States are sets of propositions instead of grid positions, actions are defined by preconditions and effects instead of Up/Down/Left/Right, and the goal test is entailment instead of reaching a cell. The same BFS (or A\* with a planning heuristic) applies unchanged. Logic only supplies the successor function and the goal test.

### 7.2 Prolog reflection

**1. Fact vs rule:** a **fact** (`connected(a,b).`) is unconditionally true. A **rule** (`can_move(X,Y) :- connected(X,Y).`) states that the head is true **if** the body can be proved, i.e. an implication.

**2. Query and entailment:** `?- q.` asks whether `q` can be derived from the facts and rules, which roughly corresponds to asking whether `KB ⊨ q`. Prolog answers by trying to construct a proof with backward chaining. `false` means no proof was found under the closed-world assumption, not that `q` is proved false in classical logic.

**3. Why verify a Python plan with Prolog?**
Prolog checks the plan against an explicit, declarative statement of the domain rules that is **separate from the code that produced the plan**. A bug in the Python planner, such as a wrong precondition, would not be repeated in the Prolog knowledge base, so errors become visible instead of being silently confirmed.

**4. Advantage of an independent verifier when an LLM helped generate the plan:**
LLM output can be fluent and plausible but wrong, and if the same LLM explains its own output it can repeat the same mistake. An independent verifier based on formal rules gives a check that does not depend on trusting the generator. It either proves each step from the knowledge base or rejects it. This lets us use a fast but fallible generator safely.

> **An AI system can generate a candidate solution, while a separate logical system checks it.**

---

## Use of the LLM

> **Note:** edit this section so it describes your own work.

- **Designed by me:** the problem specification (Task 0), the hand-made plan (Task 1), and the choice of tests, including the extra disconnected-map test and the check of the lab's example plan.
- **Generated by the LLM:** the code in `planner.py`, `test_planner.py` and `planner.pl`, following the prompts in `prompts.md`.
- **Modified:** fixed the `Action.__format__` crash in the printing code; added the `¬Holding(Package)` negative precondition to `PickUp`.
- **Tested:** Tests A, B and C, the validator, the Task 0 applicability checks, and all the Prolog queries above.
