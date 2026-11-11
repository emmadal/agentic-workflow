---
name: code-simplification
description: "Use when working code is hard to read and you want to simplify, clean up or refactor it: reduce nesting, duplication and needless abstraction without changing behavior, proven by tests."
---
# Code simplification

Behavior must not change. If tests do not cover it, add characterization tests first.

1. Run the tests. Green before you start.
2. Understand why it is shaped this way (git blame, comments) before removing anything. Respect intentional "weird" code.
3. One simplification per commit. Rerun tests after each.
4. Targets: deep nesting (use early returns), long functions, duplicated logic (extract after three uses, not two), dead code and unused parameters, clever one-liners, speculative generality, misleading names.
5. Prefer deleting over abstracting. Fewer concepts beats fewer lines.
6. Do not mix refactors with feature or bug changes.
7. Match the project's conventions, even where you disagree.

## Red flags
| Thought | Reality |
|---|---|
| "Shorter is simpler" | Dense code is harder to read. Optimize for the reader. |
| "I'll fix that bug while refactoring" | Separate commit, or you cannot tell what changed behavior. |
| "Tests are slow, skip them" | A refactor without tests is a rewrite. |

## Verify
Tests unchanged and green; the diff removes more complexity than it adds; a reviewer can read each commit in under a minute.
