# Health score (web targets)

Each category starts at 100. Subtract per open issue: critical 40, high 20, medium 8, low 3. Floor at 0. The score is the weighted sum, rounded.

| Category | Weight |
|---|---:|
| Functional | 30% |
| Console and network | 15% |
| Accessibility | 15% |
| UX | 10% |
| Performance | 10% |
| Visual | 10% |
| Content | 5% |
| Security | 5% |

Rules:
- Any open critical issue caps the total at 60, whatever the arithmetic says.
- Score before fixes (baseline) and after (final). Only verified fixes count as closed.
- Pages or flows you could not reach are listed as not tested; they do not count as 100.
- API and CLI targets do not get a score. Report contracts as pass, fail, blocked or not run.

Example: one high functional issue and two medium accessibility issues give Functional 80, Accessibility 84, the rest 100, total = 0.30*80 + 0.15*84 + 0.55*100 = 91.6, reported as 92.
