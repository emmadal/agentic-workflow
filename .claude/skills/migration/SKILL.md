---
name: migration
description: "Use when removing, replacing or upgrading code, a legacy module, API, dependency, schema or platform: inventory consumers, migrate in steps, expand-migrate-contract, then delete the old path."
---
# Migration and deprecation

Code is a liability. Remove what you no longer need, safely.

1. **Decide** (`adr` if costly to reverse): why migrate, what replaces it, deadline.
2. **Inventory** every consumer: grep, dependency graph, logs and metrics showing real traffic, mobile versions in the field.
3. **Expand**: add the new path alongside the old. Both work.
4. **Migrate** consumers in small batches, each verified. Track the remaining count.
5. **Dual-run** when risk is high: compare old and new outputs in shadow mode.
6. **Contract**: when metrics show zero use for a full release cycle, delete the old path, its tests and docs.
7. **Data**: backfill in batches, idempotent and resumable, verify counts and checksums, keep a rollback until verified.
8. **Enforce**: advisory deprecation with no removal date never ends. Set the date, provide tooling, hold it.
9. **Communicate**: deprecation notice with date and migration guide. Mobile apps need a long window and a force-upgrade plan.
10. **Dependency or platform upgrade**: read the changelog for breaking changes, upgrade one major at a time, run the full suite, watch for behavior changes with no compile error.

## Red flags
| Thought | Reality |
|---|---|
| "Nobody uses it" | Prove it with traffic data. |
| "Big-bang cutover is faster" | It has no safe rollback. |
| "Leave the old code, it's harmless" | It rots, confuses and hides bugs. |

## Verify
Old path has zero traffic before deletion; rollback tested during the migration; docs and tests for the old path are gone.
