# init-workspace

A Claude Code skill that sets up your project workspace from scratch — creates `CLAUDE.md` files
and memory files so every future Claude session starts with full context.

Asks you 10 structured questions, shows you the file drafts for approval, then writes everything to disk.

> No guessing. Everything is grounded in what's actually in your codebase.

---

## How to Trigger

Say any of the following — Claude will invoke the skill automatically:

- *"init workspace"*
- *"onboard this project"*
- *"set up claude for this project"*
- *"create CLAUDE.md"*
- *"I just opened this project"*
- *"create project memory files"*
- *"create project context"*
- *"scaffold a new repo"*

Does **not** trigger for: editing an existing CLAUDE.md, reading memory files, or explaining what memory files are.

---

## What It Creates

**In the project folder:**

| File | Purpose |
|------|---------|
| `CLAUDE.md` (root) | Workspace map, tech stack, entry point, key paths, health check |
| `<folder>/CLAUDE.md` | Scoped context per major sub-directory (2–5 folders typical) |

**In `~/.claude/projects/<slug>/memory/`:**

| File | Purpose |
|------|---------|
| `MEMORY.md` | Index of all memory files |
| `project_context.md` | Project name, purpose, stack, status |
| `decisions.md` | Architectural decisions already made |
| `feedback_preferences.md` | How Claude should behave in this project |
| `current_focus.md` *(optional)* | Active in-progress work |

Memory files persist across sessions — even when the project isn't open.

---

## Workflow

1. **Explore** — reads dependency files, README, entry point, 2–3 source files
2. **Detect slug** — derives the memory folder path from the project's Windows path
3. **Ask 10 questions** — pre-fills what it can infer; you confirm or correct
4. **Draft for approval** — shows all file contents before writing anything
5. **Write** — only after you approve
6. **Verify** — lists all files created

---

## Installation

Copy this skill folder into your Claude Code project:

```
your-project/
└── .claude/
    └── skills/
        └── init-workspace/
```

Or install from GitHub:

```bash
npx skills add https://github.com/asafmadmon-cloud/my-claude-skills --skill init-workspace --yes
```

---

## Author

Built by [Asaf Madmon](https://github.com/asafmadmon-cloud)
Part of [my-claude-skills](https://github.com/asafmadmon-cloud/my-claude-skills)
