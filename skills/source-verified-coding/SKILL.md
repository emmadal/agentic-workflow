---
name: source-verified-coding
description: "Use when writing code against a library, framework, SDK, CLI or API whose version matters: check current official docs before coding, cite the source, flag anything unverified."
---
# Source-verified coding

Training data is stale. Versions change APIs.

1. Read the installed version from the lockfile or manifest (`package.json`, `Package.resolved`, `libs.versions.toml`).
2. Fetch current official docs for that version: a docs MCP (Context7), the vendor site, or the changelog. Prefer official over blogs.
3. Check for the deprecation or migration note on every API you are about to use.
4. Write code from the documented signature and example, not from memory.
5. Cite the doc URL or section in a short comment for non-obvious usage or in the PR.
6. If you cannot verify, say `UNVERIFIED: <what>` and tell the user what to check.

Skip for stable language basics and APIs you just read in this repo.

## Red flags
| Thought | Reality |
|---|---|
| "I know this API" | Major versions rename and remove things. Check. |
| "Docs are too long" | Query the one concept you need. |
| "It compiled, so it's right" | Deprecated or insecure usage still compiles. |

## Verify
Every external API call matches the documented version; sources are cited; unverified items are listed.
