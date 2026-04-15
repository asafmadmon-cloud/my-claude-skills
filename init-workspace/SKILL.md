---
name: init-workspace
description: >
  Sets up a Claude Code project workspace from scratch — use this skill any time a user wants
  Claude to understand a project folder, create CLAUDE.md files, or build the memory system.
  ALWAYS use this skill when the user says anything like: "init workspace", "onboard this project",
  "set up claude for this project", "create CLAUDE.md", "create project memory files",
  "create memory files", "set up memory", "create project context", "I just opened this project",
  "I just started a new project", "scaffold a new repo", or any variation of wanting Claude to
  learn and remember the current project. Also triggers when user asks to create project_context.md,
  decisions.md, or feedback_preferences.md from scratch. Do NOT use for editing an existing
  CLAUDE.md, reading existing memory files, or explaining what memory files are.
  Produces: root CLAUDE.md, sub-folder CLAUDE.md files for major directories, the four
  standard memory files (MEMORY.md, project_context.md, decisions.md, feedback_preferences.md),
  a KB overview file at ~/Documents/Claude Code/knowledge base/projects/<name>/overview.md,
  and an update to the global ~/.claude/projects/C--Users-User/memory/MEMORY.md.
---

# init-workspace

You are initializing a Claude Code project workspace. Your job is to explore the current folder,
understand what this project is, and write the files that will give every future Claude session
instant context — without the user needing to re-explain things.

## What you produce

1. **Root `CLAUDE.md`** — the single most important file. Loaded automatically whenever Claude
   opens this folder. Should contain everything a knowledgeable developer needs at a glance:
   workspace map, tech stack, entry points, key file paths, health check command.

2. **Sub-folder `CLAUDE.md` files** — one per major sub-directory (skip vendor folders, node_modules,
   .git, build outputs, and any folder that has only static assets or generated files). Each one
   should give scoped context for that area only — not repeat what the root already says.

3. **Memory files** — stored in `~/.claude/projects/<slug>/memory/`. These persist across sessions
   even when the project isn't open. Four standard files + one optional:
   - `MEMORY.md` — index file listing all memory files. No frontmatter, keep under 200 lines.
   - `project_context.md` — project facts: name, purpose, tech stack, current status
   - `decisions.md` — key architectural/methodology decisions already made
   - `feedback_preferences.md` — how Claude should behave in this specific project
   - `current_focus.md` *(optional)* — what's actively being worked on right now; create only if
     the user has active in-progress work (inferred from code or Q6 answer)

4. **KB overview file** — `~/Documents/Claude Code/knowledge base/projects/<project-slug>/overview.md`
   Stable reference for the project. Sections: What, Tech Stack (include folder path), Status,
   Health Check, Key Decisions (empty placeholder), Related (empty placeholder).
   Use kebab-case for the folder name (e.g. "my-claude-skills", "stock-analysis").
   Format must match the existing overview files in that folder.

5. **Global MEMORY.md update** — `~/.claude/projects/C--Users-User/memory/MEMORY.md`
   Append one entry to `## Active Projects` (numbered, matching existing format):
   `N. **Project Name** — <one-liner>. Path: \`<folder path>\`. See: KB \`projects/<slug>/overview.md\``
   Append one entry to `## Project Memory Files`:
   `- Project Name: .claude/projects/<slug>/memory/MEMORY.md`

## Workflow

### Step 1: Explore

Before exploring, check whether any workspace files already exist:
- Root `CLAUDE.md` at the project root
- Sub-folder `CLAUDE.md` files in major directories
- Memory files at `~/.claude/projects/<slug>/memory/`

If any exist, tell the user what you found and ask:
"I found existing workspace files: [list them]. Do you want me to replace them, merge new info in, or skip the ones that already exist?"
Wait for their answer before proceeding.

Map the project structure. Use Glob and Read tools — don't spawn subagents for this.
Look for:
- Language/framework indicators (package.json, requirements.txt, build.gradle, Cargo.toml, etc.)
- Entry points (main.py, index.ts, App.kt, generate_pdf.py, etc.)
- Configuration files that reveal architecture
- Folder purposes based on naming conventions and contents
- Existing documentation (README.md, docs/, any existing CLAUDE.md)
- Test setup, CI config, output directories

Read the README if it exists — it's the fastest way to understand intent.
Read 2-3 source files from the main directories to confirm what you see.

Don't over-read. Skim enough to understand purpose, not internals.

**Empty workspace:** If the folder has no meaningful files (empty or only contains an empty README),
skip exploration entirely and go straight to Step 2.5. Tell the user:
"This looks like a blank workspace — I'll set things up as a starting point rather than a reflection
of existing code. Answer the questions and I'll create the full context structure for you."
All Q1–Q10 answers start blank; none are pre-filled.

### Step 2: Detect slug

The memory folder path requires the Windows project slug. Compute it from the current working
directory:
- Replace all backslashes with dashes: `C:\Users\User\Documents\App design` → `C--Users-User-Documents-App-design`
- Keep original casing of path segments

Example slugs:
- `C:\Users\User` → `C--Users-User`
- `C:\Users\User\Documents\App design` → `C--Users-User-Documents-App-design`
- `C:\Users\User\Documents\Claude Code\Stock Analysis` → `C--Users-User-Documents-Claude-Code-Stock-Analysis`

Memory path: `C:/Users/User/.claude/projects/<slug>/memory/`

### Step 2.5: Ask Questions

Before writing anything, ask the user 10 questions in a single message. Pre-fill any answer you can
confidently infer from exploration — the user confirms or corrects. Ask all 10 at once, not one at a time.

Format:

```
Before I write the files, a few questions. I've pre-filled what I could from the code — correct anything
that's wrong, skip optional ones.

1. Project name: [inferred or blank]
2. What does it do? (1-2 sentences): [inferred from README or blank]
3. Project type: [inferred: Android app / Python CLI / web app / Node.js / other]
4. Tech stack — language, frameworks, key libraries: [inferred from package.json / requirements.txt or blank]
5. Main entry point or key file(s): [inferred or blank]
6. Current status: [planning / early dev / active dev / maintenance]
7. Any hard rules I must always follow in this project? (e.g. "never edit X", "always run Y first")
8. Any key decisions already made I should remember? (optional — skip to leave blank)
9. GitHub repo URL? (optional)
10. Solo project or collaborators?
```

Wait for answers before proceeding to Step 3.

Answer → file mapping:
- Q1, Q2, Q3, Q4, Q5, Q6, Q9, Q10 → `project_context.md`
- Q7 (hard rules) → `feedback_preferences.md` > Project-Specific Rules
- Q8 (decisions) → `decisions.md` (populate if answered; placeholder comment if skipped)

---

### Step 3: Draft all files and show for approval

Using the exploration findings and the user's answers from Step 2.5, draft all files in your response.
**Do not write any files to disk yet.**

Show every file as a markdown code block with its target path as a header. Present them all in one message:

```
Here are the files I'll create. Let me know if anything needs to change before I write them.

---
**Root `CLAUDE.md`** → `<project-root>/CLAUDE.md`
[content]

---
**`src/CLAUDE.md`** → `<project-root>/src/CLAUDE.md`
[content]

---
**`memory/MEMORY.md`** → `~/.claude/projects/<slug>/memory/MEMORY.md`
[content]

---
**`memory/project_context.md`** → `~/.claude/projects/<slug>/memory/project_context.md`
[content]

---
**`memory/decisions.md`** → `~/.claude/projects/<slug>/memory/decisions.md`
[content]

---
**`memory/feedback_preferences.md`** → `~/.claude/projects/<slug>/memory/feedback_preferences.md`
[content]

---
**`KB overview`** → `~/Documents/Claude Code/knowledge base/projects/<slug>/overview.md`
[content]

---
**Global `MEMORY.md` update** → `~/.claude/projects/C--Users-User/memory/MEMORY.md`
Show only the two lines being added (not the full file):
- New Active Projects entry: [line]
- New Project Memory Files entry: [line]
```

Wait for the user to approve or request changes. If they request changes, update only the affected files
and re-show them. Do not proceed to Step 3.5 until the user approves.

**Root CLAUDE.md sections** (adapt to what actually applies):

```
## Tech Stack
Language, framework, key libraries — version numbers where visible

## Running / Entry Point
How to run or build the project. Health check command if applicable.

## Architecture
How the major parts fit together. Data flow if relevant.

## Key File Paths
The files a developer would actually need to find quickly.

## Workspace Map
| Folder / File | Purpose |
|---|---|
| folder/ | what it contains |
```

Guidelines:
- Be concrete, not vague. "Entry point is `src/main.py`" beats "the project has Python code"
- Write for a developer who knows the language but hasn't seen this project
- Skip sections that don't apply (a simple script doesn't need Architecture)
- 50–150 lines is the target range. Longer is OK for complex projects.

**Sub-folder CLAUDE.md files** — for each major sub-directory (use judgment — 2-5 folders is typical):
- Skip: `node_modules/`, `.git/`, `build/`, `dist/`, `__pycache__/`, vendor folders
- Skip folders with only static assets or auto-generated files
- Include: source code folders, main feature areas, script directories, test suites

Each sub-folder CLAUDE.md covers only that directory. Don't repeat what root CLAUDE.md says.
Useful content: key files in that folder, what each script does, how components relate, gotchas.

**Planned-but-absent directories:** If a folder is referenced in code or config (e.g., a route import
points to `routes/auth.js` but the directory doesn't exist yet), include a sub-folder CLAUDE.md for
it anyway — document its intended structure and what files are expected there. This is often the most
useful context for an early-stage project.

### Step 3.5: Write files — only after approval

Once the user approves the drafts, write all files to disk exactly as shown in the approved drafts.

Create `~/.claude/projects/<slug>/memory/` if it doesn't exist.
If `current_focus.md` is needed, create it with a brief note on what's actively in progress.

Write the KB overview file to `~/Documents/Claude Code/knowledge base/projects/<slug>/overview.md`.
Create the folder if it doesn't exist.

For the global MEMORY.md: read the file first, then use Edit to insert:
- The new project line into `## Active Projects` (append after the last numbered entry)
- The new memory file path into `## Project Memory Files` (append after the last entry)
Do NOT rewrite the entire file — use targeted edits only.

### Step 4: Verify and report

List all files you created with one-line descriptions. Ask the user:
"Anything to update or add before we're done?"

## What good output looks like

A root CLAUDE.md that a developer (or Claude) can read in 60 seconds and understand:
- what this project is
- how to run it
- where the key files are

Memory files that will save 2-3 minutes of re-explaining context at the start of every future session.

## overview.md format

```markdown
# <Project Name>

## What
<One or two sentences from Q2>

## Tech Stack
<From Q4. If Python, include full exe path. Always include folder path.>
Located at: `<folder path>`

## Status
<From Q6: planning / early dev / active dev / maintenance>

## Health Check
```bash
# <health check command, or TODO placeholder>
```

## Key Decisions
<!-- Add architectural decisions, design choices, etc. as you work -->

## Related
<!-- Link to other KB files as the project grows -->
```

## What to avoid

- Don't write generic placeholder content that could apply to any project ("This project uses modern best practices...")
- Don't invent details you can't confirm from the code
- Don't repeat the same information in both root CLAUDE.md and sub-folder CLAUDE.md files
- Don't create sub-folder CLAUDE.md files for directories that don't need them
- Don't over-document — a focused 80-line CLAUDE.md beats a sprawling 300-line one
- Don't rewrite the global MEMORY.md from scratch — only append the two new lines
