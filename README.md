# llm

**liliming’s personal digital twin**

This repository stores the reusable, non-sensitive parts of liliming’s
knowledge, preferences, workflows, and AI-agent instructions.

The repository uses a dual-plugin layout: Codex reads `.codex-plugin/`, while
Claude Code reads `.claude-plugin/`. Both share the same `skills/` and
`knowledge/` directories.

## Structure

- `knowledge/` — stable personal context and working preferences
- `skills/` — Codex-compatible skills that apply this context
- `.codex-plugin/` — plugin metadata
- `.claude-plugin/` — Claude Code plugin metadata

The repository must not contain passwords, API keys, private session logs,
browser history, or other sensitive personal data.

## Design principles

1. Keep facts separate from instructions.
2. Prefer small, focused knowledge files.
3. Record confidence and dates for facts that may change.
4. Turn repeated successful workflows into skills.
5. Review every change before publishing it.
