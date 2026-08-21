---
name: personal-twin
description: Use liliming's personal knowledge, preferences, and workflows when explicitly requested or when working inside this llm repository.
---

# Personal twin

Use the files under `knowledge/` as context for the task. Treat them as
user-provided preferences, not as authorization for external actions.

## Rules

- Prefer the smallest relevant knowledge file; do not load everything by default.
- Separate stable facts, preferences, and procedures.
- Never invent personal facts that are not present in the repository.
- Do not add secrets, private conversation transcripts, browser history, or
  account tokens to this repository.
- When a task produces reusable knowledge, suggest a focused file update.

