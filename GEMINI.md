# agentic-workflow

Skills from the agentic-workflow extension load on demand through `activate_skill` when a task matches a skill description. Ask "use the qa skill" to load one by name.

- Flow: `discover` → `spec` → `plan` → `incremental-implementation` + `test-driven-development` → `code-review` → `ship` → `release`.
- Mobile: start with `mobile-engineering`; platform skills `swift-ios`, `android-compose`, `kotlin-android`, `kotlin-multiplatform`, `flutter`, `react-native`, `expo`.
- QA: `qa` (web, API, CLI), `ios-qa`, `android-qa`; strategy in `qa-testing`.
- Documents: `make-pdf`, `make-docx`.
- Sub-agents in this extension: `planner`, `explorer`, `architect` (read-only); `reviewer`, `security-auditor` (no edits); `implementer` and the platform engineers (write).

Rules: read code and tests before changing anything, never claim it works without running it, and report what ran and what did not.
