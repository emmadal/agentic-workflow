---
name: test-driven-development
description: "Use when implementing logic, fixing a bug or changing behavior with red-green-refactor: write the failing test first, watch it fail, make it pass, refactor. Bug fixes start with a reproduction test."
---
# Test-driven development

**Red, green, refactor.**

1. **Red**: write one test for one behavior. Run it. Confirm it fails for the right reason. A test that passes first time proves nothing.
2. **Green**: the minimum code to pass. No extras.
3. **Refactor**: only while green. Rerun after each change.
4. Bug: reproduce it in a test first, then fix, then keep the test.
5. Find the repo's real test command (`AGENTS.md`, CI config). Do not assume `npm test`.
6. Test behavior through the public interface. Name tests by behavior. Inject clocks, randomness and network; no sleeps.
7. Prefer real implementations over fakes, fakes over stubs, stubs over mocks. Mock only at slow or nondeterministic boundaries. Review every snapshot; never bulk-update them.

## Pitfalls
| Excuse | Reality |
|---|---|
| "Too simple to test" | Simple code grows. The test documents intent. |
| "I'll add tests after" | After-the-fact tests mirror the code, not the requirement. |
| "I tested it manually" | Manual checks do not persist. |
| "Rerun to be sure" | Repeating an unchanged run adds nothing. Rerun after edits. |

Skipping, weakening or deleting a test to get green is never a fix.

## Verify
New behavior has a test that failed before the change; bug fixes have a regression test; the full suite passes; you ran the tests and read the result.
