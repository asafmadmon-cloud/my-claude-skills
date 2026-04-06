# Git Skill Audit

A Claude Code skill that automatically audits GitHub repositories — skills, plugins, and MCP servers — **before you install them**.

It performs static, read-only analysis using public GitHub data and flags security risks with a clear verdict: ✅ SAFE / ⚠️ WARN / 🚫 BLOCK.

> No code is ever executed. Everything is read-only.

---

## Auto-Trigger

This skill triggers **automatically** — no explicit "audit" command needed.

It activates whenever you share a GitHub URL alongside install intent:

- *"install this skill"*
- *"add this plugin"*
- *"npx skills add https://github.com/..."*
- *"is this safe to install?"*
- *"check this repo"*
- *"should I trust this?"*
- *"review this before I install it"*

---

## What It Checks

The skill runs 7 steps in sequence:

| Step | What It Does |
|------|--------------|
| 1 | Parse `owner/repo` from the URL |
| 2 | Fetch repo metadata from GitHub API (stars, age, license, owner type, archived status) |
| 3 | Read and scan `SKILL.md` for prompt injection, data exfiltration instructions, persona overrides |
| 4 | Read every file in the `hooks/` directory and scan for malicious shell commands |
| 5 | Check `.claude-plugin/plugin.json` for manifest anomalies |
| 6 | Scan root files: `package.json`, `requirements.txt`, `.sh` scripts, `README.md` |
| 7 | Output a structured verdict report |

### 13 Threat Categories

1. **Prompt Injection / Instruction Override** — instructions to ignore or override Claude's guidelines
2. **Data Exfiltration** — sending your files or conversation to external endpoints
3. **Credential & Secret Access** — reading SSH keys, `.env`, AWS/GCloud credentials, browser passwords
4. **Hook Script Exploitation** — malicious shell commands that run on your machine
5. **Tool Poisoning** — misrepresenting Claude's available tools or capabilities
6. **Self-Modification / Runtime Dynamism** — downloading and executing code at runtime, time bombs
7. **Obfuscation & Hidden Payloads** — base64 blobs, zero-width characters, homoglyph substitution
8. **Dependency Typosquatting** — packages with names 1–2 characters off from popular libraries
9. **Hardcoded Secrets** — API keys, private keys, bearer tokens committed to the repo
10. **Infrastructure Misconfiguration** — disabled TLS, world-readable permissions, `0.0.0.0` bindings
11. **Git Forensics Signals** — brand new repos, large initial commits, no gradual development history
12. **Social Engineering in README** — urgency language, fake authority claims, fear tactics
13. **AI Ecosystem Specific Threats** — skills that bypass Claude's safety guidelines or auto-approve actions

---

## Output Format

```
🔍 SKILL AUDIT: owner/repo
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
VERDICT: ✅ SAFE / ⚠️ REVIEW RECOMMENDED / 🚫 DO NOT INSTALL
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

📊 SOURCE REPUTATION
  Owner: name (Organization / User)
  Stars: N | Forks: N | Age: X months
  License: MIT / NONE
  → one-line summary

📄 SKILL.md ANALYSIS
  → CLEAN — no red flags found
  OR
  → ⚠️ finding: description
  → 🚫 finding: description

🪝 HOOKS
  → NONE FOUND / ⚠️ finding

🔌 PLUGIN MANIFEST
  → OK / NOT FOUND / ⚠️ issue

📦 DEPENDENCIES
  → CLEAN / ⚠️ suspicious package

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
RECOMMENDATION: one concrete sentence
```

---

## Verdict Logic

| Condition | Verdict |
|-----------|---------|
| Any 🚫 finding | BLOCK |
| 3 or more ⚠️ findings | BLOCK |
| 1–2 ⚠️ findings | WARN |
| No findings | SAFE |

---

## Installation

Copy this skill folder into your Claude Code project:

```
your-project/
└── .claude/
    └── skills/
        └── Git Skill Audit/
```

Or install from GitHub:

```bash
npx skills add https://github.com/asafmadmon-cloud/my-claude-skills --skill git-skill-audit --yes
```

---

## Author

Built by [Asaf Madmon](https://github.com/asafmadmon-cloud)
Part of [my-claude-skills](https://github.com/asafmadmon-cloud/my-claude-skills)
