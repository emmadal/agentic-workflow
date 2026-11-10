# Interview rubrics

## Score scale
1 = not shown. 2 = partial, needs strong hints. 3 = solid, minor gaps. 4 = strong, unprompted.

## Coding
- Problem solving: clarifies input and edge cases, states brute force, finds the key insight.
- Correctness: working code, handles empty, one item, duplicates, overflow, negative values.
- Complexity: states time and space, justifies, knows the lower bound.
- Communication: thinks aloud, names variables well, explains trade-offs.
- Testing: walks an example, picks edge cases before being asked.

## System design
- Requirements: functional and non-functional, scale numbers (QPS, storage, latency target).
- Design: clear components, API and data model, sensible store choices.
- Depth: one area (caching, sharding, queue, consistency) explored with failure modes.
- Trade-offs: names the alternative and why not; CAP, cost, complexity.
- Operations: monitoring, rollout, rollback, data growth.

## Behavioral (STAR)
Situation in one sentence, Task owned by the user, Action in "I" not "we", Result with a number, Reflection on what changed. Prepare 6 stories that cover several themes each.

## Level signals
Junior: finishes with hints. Mid: finishes alone, tests. Senior: leads trade-offs, anticipates scale and failure. Staff: reframes the problem, weighs org and cost impact.
