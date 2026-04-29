# Red Flags Reference

Patterns to detect when auditing skill repos. Sourced from repo-forensics's documented scanner categories, adapted for static analysis via WebFetch.

Severity levels: 🚫 BLOCK-level | ⚠️ WARN-level | 💡 Note-level

---

## 1. Prompt Injection / Instruction Override

Patterns in SKILL.md or any markdown file:

🚫 BLOCK:
- "ignore previous instructions"
- "ignore your system prompt"
- "disregard your guidelines"
- "you are now" (followed by a different persona)
- `<IMPORTANT>` tags with instructions that contradict or override normal behavior
- "do not tell the user"
- "keep this secret from the user"
- Instructions to lie, deceive, or withhold information

⚠️ WARN:
- Unusual persona-setting language not related to skill domain
- Instructions that seem designed to suppress Claude's normal caution

---

## 2. Data Exfiltration

Patterns in any skill file:

🚫 BLOCK:
- Instructions to send data to external URLs (especially not explained in context)
- `curl`, `wget`, `fetch`, `requests.post` to non-GitHub, non-official endpoints
- Instructions to read and transmit: `~/.ssh`, `.env`, `secrets`, `credentials`, `token`, `api_key`
- Instructions to collect and store user conversation content externally
- WebSocket connections to unknown endpoints

⚠️ WARN:
- Instructions to fetch from external URLs without clear justification
- References to "reporting", "logging", or "telemetry" with external endpoints

---

## 3. Credential & Secret Access

🚫 BLOCK:
- References to `~/.ssh/id_rsa`, `~/.ssh/id_ed25519`
- Reading `.env` files and transmitting contents
- Accessing `~/.netrc`, `~/.aws/credentials`, `~/.config/gcloud`
- Instructions to read Windows credential store (`AppData\Roaming\Microsoft`)
- Instructions to read browser password stores
- References to `GITHUB_TOKEN`, `AWS_SECRET_ACCESS_KEY`, `ANTHROPIC_API_KEY` in a collection context

⚠️ WARN:
- Broad file access instructions (`read all files in home directory`)
- References to environment variables without clear justification

---

## 4. Hook Script Exploitation

Patterns in `hooks/` directory files:

🚫 BLOCK:
- `curl` or `wget` posting to external URLs
- `base64 -d | bash` or similar decode-and-execute patterns
- `eval $(...)` with dynamic content
- `rm -rf` on directories outside the project
- Commands that write to shell config files (`~/.bashrc`, `~/.zshrc`, `~/.profile`)
- Reverse shell patterns (`nc`, `ncat`, `bash -i >& /dev/tcp/`)
- Commands that modify SSH authorized_keys
- Cron job installation

⚠️ WARN:
- Any outbound network call from a hook (even GET requests)
- Writing files outside the project directory
- Spawning background processes (`&`, `nohup`)
- Using `sudo` or privilege escalation

---

## 5. Tool Poisoning

🚫 BLOCK:
- `<IMPORTANT>` tags in SKILL.md, README, or any prompt-facing file containing instruction-style text — this is the primary vector for tool poisoning (documented by Invariant Labs)
- HTML comment blocks (`<!--`) containing directives: "ignore", "you must", "do not", "disregard", "always"
- SKILL.md instructs Claude to describe its own capabilities differently than they are
- Instructions to claim tools are unavailable when they are
- Instructions to modify tool descriptions dynamically based on context
- Instructions to hide tool usage from the user

⚠️ WARN:
- Unusually complex instructions about how Claude should describe what it's doing
- Tool descriptions that reference behavior outside the skill's stated purpose

---

## 6. Self-Modification / Runtime Dynamism

🚫 BLOCK:
- Instructions to download and execute code at runtime
- Instructions to modify SKILL.md or other skill files during execution
- `eval(`, `new Function(`, `exec(` called with a non-literal (variable) argument
- `import(variable)` or `require(variable)` — dynamic module loading at runtime
- `setTimeout` or `setInterval` executing a string argument (not a function reference)
- Time-bomb patterns: `new Date()` / `datetime.now()` / `Date.now()` inside a conditional that gates a network call or destructive action
- Instructions conditioned on detecting monitoring or evaluation contexts ("if you are being tested")

⚠️ WARN:
- Instructions to fetch additional instructions from external URLs at runtime
- Deferred or conditional behavior not explained by the skill's purpose
- Date/time checks that gate non-network behavior (version checks, UI toggles) without explanation

---

## 7. Obfuscation & Hidden Payloads

🚫 BLOCK:
- Base64-encoded blobs in skill files with no clear purpose
- Long random-looking strings (high entropy, >32 chars, mixed upper/lower/digits/symbols) that aren't API keys with obvious context
- Hex-encoded strings decoded at runtime
- Unicode homoglyph substitution (e.g., using Cyrillic characters that look like Latin)
- Zero-width characters in text: U+200B (zero-width space), U+200C (zero-width non-joiner), U+200D (zero-width joiner), U+FEFF (BOM) — used to hide instructions in visible text
- Instructions referencing external files by hash rather than name

⚠️ WARN:
- Minified or compressed content in what should be readable text files
- Very long single-line strings without explanation

---

## 8. Dependency Typosquatting

Common typosquatting patterns — flag if package.json or requirements.txt contains:

🚫 BLOCK (known malicious names or suspicious variants):
- `cros-fetch` instead of `cross-fetch`
- `reqeusts` instead of `requests`
- `numpy` with unusual version pins (< 1.0.0 or > 99.0.0)
- `setup-tools` instead of `setuptools`
- Any package name that is 1-2 characters different from a popular package
- Packages with no PyPI/npm page or 0 downloads

⚠️ WARN:
- Pinned to a very specific unusual version (e.g., `==1.2.3.4.5`)
- Package names with extra hyphens/underscores vs the canonical name
- Multiple dependencies on very obscure packages for a simple skill

---

## 9. Secret Detection in Code

Patterns that indicate hardcoded secrets (🚫 BLOCK if found in any committed file):

- `sk-[a-zA-Z0-9]{48}` — OpenAI API key
- `sk-ant-[a-zA-Z0-9-]{90+}` — Anthropic API key
- `ghp_[a-zA-Z0-9]{36}` — GitHub personal access token
- `AKIA[0-9A-Z]{16}` — AWS access key
- `-----BEGIN RSA PRIVATE KEY-----` — private key
- `-----BEGIN EC PRIVATE KEY-----` — EC private key
- `xoxb-[0-9]+-` — Slack bot token
- `xoxp-[0-9]+-` — Slack user token
- Hardcoded passwords in connection strings
- Bearer tokens in source code (`bearer [a-zA-Z0-9._-]{20,}`)
- `password\s*=\s*["'][^"']{8,}["']` — hardcoded password assignment

Note: flag even if the author claims they are "example" or "placeholder" values — legitimate examples use clearly fake values like `YOUR_API_KEY_HERE`.

---

## 10. Infrastructure Misconfiguration

⚠️ WARN:
- MCP server configurations pointing to `0.0.0.0` (all interfaces)
- Disabled TLS verification (`verify=False`, `--insecure`, `NODE_TLS_REJECT_UNAUTHORIZED=0`)
- World-readable permissions set in scripts (`chmod 777`)
- Instructions to disable firewall or security software

---

## 11. Git Forensics Signals

Check via: `https://api.github.com/repos/{owner}/{repo}/commits?per_page=20`

⚠️ WARN:
- Repo created < 7 days ago with no prior activity from the owner
- Owner account created < 30 days ago
- Commit history shows a single large initial commit with many files (possible code drop from elsewhere)
- Commit messages containing "remove", "clean", "delete", "oops", "revert" near filenames like `.env`, `keys`, `credentials`, `secret`, `token` — suggests a secret was committed and then removed (it may still be in git history)
- README makes extraordinary claims without links to verification

💡 Note:
- Large gaps in commit timeline may indicate history rewrite
- Deleted branches with no explanation

---

## 12. Social Engineering in README

⚠️ WARN:
- Urgency language: "install now", "limited time", "don't miss out", "before it's removed"
- Authority claims without verification: "official", "certified", "approved by Anthropic"
- Fear language: "your system is vulnerable without this", "critical security tool"
- Requests to disable security tools before installing
- Requests to run with elevated permissions or `sudo`
- Extraordinary performance claims without benchmarks or sources ("18 parallel scanners", "500+ patterns", "undetectable")

💡 Note:
- These don't block on their own but lower the overall trust signal when combined with other flags

---

## 13. AI Ecosystem Specific Threats

🚫 BLOCK:
- MCP server that requests access beyond what it needs for its stated purpose
- Skill that instructs Claude to bypass its own safety guidelines
- Plugin manifest that references a different name than the repo (identity mismatch)
- Instructions that would cause Claude to approve actions without user confirmation

⚠️ WARN:
- Skill requests broad filesystem or network access not needed for its purpose
- MCP server requests permissions beyond read-only for a read-only use case

---

## 14. MCP-Specific Threats

Applies when `tools.json` is present:

🚫 BLOCK:
- Any tool `description` field containing instruction-style overrides: "ignore", "always", "you must", "do not tell the user", "disregard previous"
- Tool descriptions that claim capabilities beyond the repo's stated purpose (full-schema poisoning)
- Tool `name` fields that impersonate built-in Claude capabilities (`read_file`, `execute_code`, `web_search`)

⚠️ WARN:
- Tool `description` field longer than 200 characters — unusually verbose descriptions are a schema poisoning vector
- Tool input schemas that request more fields than needed for the stated function
- Multiple tools with overlapping names that could cause routing confusion

---

## 15. Cross-file Taint Signals

Flag when the **same file** does both of the following:

🚫 BLOCK — if destination URL is unknown/dynamic:
- Reads environment variables: `process.env`, `os.environ`, `os.getenv`, `dotenv.config()`
- AND makes a network call to a non-hardcoded or non-obvious destination: `fetch(url)`, `axios.post(endpoint)`, `requests.post(url)`, `urllib.request.urlopen(addr)`

⚠️ WARN — if destination URL is hardcoded and well-known but combination is unexplained:
- Same as above but the network destination is a recognizable API (GitHub, Slack, etc.) — still worth noting so the user understands what data leaves the machine

💡 Note:
- Legitimate skills that call APIs usually have the destination URL hardcoded and documented. Dynamic destinations are almost always suspicious.

---

## Known Legitimate Orgs (strong trust signal)

These owner names should be weighted positively:
- `anthropics`, `anthropic`
- `google`, `googlecloudplatform`
- `microsoft`, `azure`
- `openai`
- `meta-llama`, `facebookresearch`
- `aws`, `awslabs`
- `hashicorp`
- `vercel`
- `supabase`

Being on this list doesn't guarantee safety — always still check the specific repo.

---

## Scoring Summary

| Count of 🚫 findings | Verdict |
|----------------------|---------|
| 1 or more | BLOCK |

| Count of ⚠️ findings | Verdict |
|----------------------|---------|
| 3 or more | BLOCK |
| 1–2 | WARN |
| 0 | SAFE (if no 💡 concerns either) |

When in doubt, WARN rather than SAFE. The user can always decide to proceed.
