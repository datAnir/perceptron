# Superpowers (obra/superpowers) — Analysis for Arcon

Analysis of the local checkout at `/home/anirband/perceptron/superpowers`, HEAD
`b36e082` ("Release v6.3.0", 2026-08-12). Written to inform Arcon's design at
`/home/anirband/perceptron/arcon`.

---

## 1. Overview

| Field | Value |
|---|---|
| Repo | `obra/superpowers` |
| Author | Jesse Vincent (`jesse@fsck.com`) / Prime Radiant |
| License | MIT (`LICENSE`, © 2025 Jesse Vincent) |
| Version | `6.3.0` (`package.json`, all plugin manifests) |
| Stack | Markdown + Bash. `type: module` JS for the OpenCode plugin, TypeScript for the Pi extension, one Python `__init__.py` for Hermes. **Zero runtime dependencies by design** (`CLAUDE.md`: "Superpowers is a zero-dependency plugin by design") |
| Maturity | High. Version 6.x, 94 KB of `RELEASE-NOTES.md`, 16 test suites under `tests/`, an external eval harness (`superpowers-evals`, "drill"), a version-bump manifest (`.version-bump.json`) that keeps 9 manifests in sync, and an explicit contributor policy with a stated 94% PR rejection rate |

It is **not a program**. It is a methodology distributed as content: 14 skill
directories plus a per-harness bootstrap shim. The product claim is that the
skills auto-trigger, so the user does nothing special.

---

## 2. Architecture

Three components, and the split is stated explicitly in
`docs/porting-to-a-new-harness.md` Part 1:

1. **Skills (harness-agnostic).** `skills/` is the single source of truth,
   shared verbatim by every harness. Skills describe *actions* — "invoke a
   skill", "dispatch a subagent", "create a todo" — never concrete tool names.
2. **Tool mapping (per-harness).** Action vocabulary → real tool names, in
   `skills/using-superpowers/references/<harness>-tools.md` and/or inline in
   the harness's bootstrap injector.
3. **Bootstrap (per-harness).** At session start, the *full text* of
   `skills/using-superpowers/SKILL.md` is injected into context wrapped in
   `<EXTREMELY_IMPORTANT>` tags. The doc is blunt about this:
   **"The bootstrap is the entire integration. Without it, the skill files are
   inert — present on disk, never invoked."**

### The hook

`hooks/hooks.json` registers one Claude Code hook with matcher
`startup|clear|compact` — i.e. it fires at session start **and after
compaction**, which is the key context-lifecycle move:

```json
{ "hooks": { "SessionStart": [ { "matcher": "startup|clear|compact",
  "hooks": [ { "type": "command",
    "command": "\"${CLAUDE_PLUGIN_ROOT}/hooks/run-hook.cmd\" session-start",
    "shell": "bash", "async": false } ] } ] } }
```

`hooks/session-start` reads the bootstrap skill, JSON-escapes it with pure bash
parameter substitution (no `jq` — zero deps), and emits the right key for the
detected platform: `additional_context` for Cursor,
`hookSpecificOutput.additionalContext` for Claude Code, top-level
`additionalContext` for Copilot CLI / SDK-standard. The comment notes Claude
Code reads *both* without dedup, so it must emit only one.

In-process harnesses do it differently. `.pi/extensions/superpowers.ts`
subscribes to `session_start`, `session_compact`, `agent_end`, and `context`,
and injects the bootstrap as a **user message** placed after any
`compactionSummary` messages. `.opencode/plugins/superpowers.js` hooks
`experimental.chat.messages.transform` and unshifts the bootstrap into the
first user message — with two documented reasons for user-message-over-system:
"Token bloat from system messages repeated every turn (#750)" and "Multiple
system messages breaking Qwen and other models (#894)". Both cache the
bootstrap at module level and guard against double injection by scanning for a
marker string.

`hooks/run-hook.cmd` is a bash/batch polyglot so the same file works on Windows
(Git Bash discovery) and Unix — relevant to Arcon's cross-platform goal.

### Directory structure (significant parts)

```
superpowers/
├── CLAUDE.md              # contributor rules; AGENTS.md is a symlink to it
├── GEMINI.md              # 2 lines: @-includes bootstrap + gemini tool map
├── package.json           # v6.3.0, "pi" block declares extensions + skills
├── .version-bump.json     # 9 manifests kept version-synced
├── .claude-plugin/        # plugin.json + marketplace.json
├── .codex-plugin/  .cursor-plugin/  .devin-plugin/
├── .kimi-plugin/          # plugin.json carries a "skillInstructions" tool map
├── .hermes-plugin/        # plugin.yaml (provides_hooks: pre_llm_call) + __init__.py
├── .opencode/plugins/superpowers.js
├── .pi/extensions/superpowers.ts
├── .agents/plugins/marketplace.json
├── hooks/
│   ├── hooks.json  hooks-cursor.json
│   ├── session-start          # the bootstrap injector
│   └── run-hook.cmd           # bash/batch polyglot wrapper
├── skills/<name>/SKILL.md     # 14 skills + reference/script sidecars
├── docs/
│   ├── porting-to-a-new-harness.md
│   ├── superpowers/specs/     # 17 design docs, dated
│   └── superpowers/plans/     # 15 implementation plans, dated
├── scripts/ (bump-version, lint-shell, sync/package-codex-plugin)
└── tests/   (16 dirs: claude-code, codex, pi, opencode, kimi, hooks, …)
```

Note the repo dogfoods its own conventions: `docs/superpowers/specs/` and
`docs/superpowers/plans/` are exactly the paths the `brainstorming` and
`writing-plans` skills write to.

---

## 3. The skills system in detail

**Format.** One directory per skill, `SKILL.md` required, sidecar files
optional. YAML frontmatter with exactly two fields, max 1024 chars total.
Verbatim from `skills/subagent-driven-development/SKILL.md`:

```markdown
---
name: subagent-driven-development
description: Use when executing implementation plans with independent tasks in the current session
---
```

And from `skills/brainstorming/SKILL.md`, showing the imperative style used for
the always-on gate skill:

```markdown
---
name: brainstorming
description: "You MUST use this before any creative work - creating features, building components, adding functionality, or modifying behavior. Explores user intent, requirements and design before implementation."
---
```

**Progressive disclosure.** Frontmatter is resident (harnesses index
name+description into the system prompt); the body loads only when the skill is
invoked. `skills/writing-skills/SKILL.md` makes a subtle and empirically-derived
rule out of this, in its "Skill Discovery Optimization (SDO)" section:

> **CRITICAL: Description = When to Use, NOT What the Skill Does** … Testing
> revealed that when a description summarizes the skill's workflow, an agent may
> follow the description instead of reading the full skill content. A
> description saying "code review between tasks" caused an agent to do ONE
> review, even though the skill's flowchart clearly showed TWO reviews.

So the description is deliberately *information-poor about process* to force
the body to be read. That is a real, non-obvious lesson.

**Discovery** is delegated to the harness: Claude Code / Cursor / Codex / Kimi
manifests point `"skills": "./skills/"`; Pi's `resources_discover` event returns
`skillPaths`; OpenCode's `config` hook pushes the dir onto `config.skills.paths`
to avoid symlinks. Nothing in the repo builds its own index.

**Conventions:** flat namespace, verb-first hyphenated names
(`creating-skills` not `skill-creation`), heavy reference (100+ lines) split to
sidecars, principles and <50-line code patterns kept inline. Target word
counts are stated: <150 words for getting-started workflows, <200 for
frequently-loaded skills, <500 for others.

**Inventory — 14 skills** (actual, from `skills/*/SKILL.md`; body sizes by
`wc -w`):

| Category | Skills |
|---|---|
| Meta / bootstrap | `using-superpowers` (485w), `writing-skills` (3779w) |
| Design | `brainstorming` (2324w), `writing-plans` (1059w) |
| Execution | `executing-plans` (344w), `subagent-driven-development` (4823w), `dispatching-parallel-agents` (865w) |
| Quality | `test-driven-development` (1375w), `verification-before-completion` (580w), `systematic-debugging` (1440w) |
| Review | `requesting-code-review` (421w), `receiving-code-review` (913w) |
| Git flow | `using-git-worktrees` (1069w), `finishing-a-development-branch` (1269w) |

Total ~20.7k words of skill bodies — but only the ~485-word bootstrap plus 14
descriptions are ever resident.

---

## 4. Key workflows / methodology

**The chain** (README "Basic Workflow"): `brainstorming` →
`using-git-worktrees` → `writing-plans` → `subagent-driven-development` *or*
`executing-plans` → `test-driven-development` → `requesting-code-review` →
`finishing-a-development-branch`. Skills name their successors explicitly
("**REQUIRED SUB-SKILL:** Use superpowers:finishing-a-development-branch"), so
the chain is encoded in the content, not in a scheduler.

**brainstorming** — as of 6.3.0, a three-path router the agent must classify and
announce out loud: **spike** (feasibility probe, output is an answer, code is
labeled throwaway), **bounded** (scoped change to code that already exists;
short design in chat, no documents), **architectural** (questions → 2-3
approaches with trade-offs → sectioned design approved section-by-section →
spec written to `docs/superpowers/specs/YYYY-MM-DD-<topic>-design.md` →
self-review → human review gate → hand off to `writing-plans`). Two invariants:
"the ceremony scales with the task; the approval gate never does", and the
ratchet is one-way — hidden complexity upgrades the path mid-task, nothing
downgrades. The skill body embeds a Graphviz `dot` state machine and a Red
Flags table mapping rationalizations to rebuttals.

**writing-plans** — writes plans "assuming the engineer has zero context for
our codebase and questionable taste". Bite-sized steps of 2-5 minutes, each one
action, in a fixed RED/GREEN/commit shape. Mandatory plan header carrying
**Goal / Architecture / Tech Stack / `Spec:` pointer / Global Constraints**.
Each task block declares `Files:` (create/modify with line ranges/test) and an
`Interfaces:` block — Consumes/Produces with exact signatures — because "a
task's implementer sees only their own task; this block is how they learn the
names and types neighboring tasks use." An explicit "No Placeholders" list
("TBD", "add appropriate error handling", "Similar to Task N") declares those
*plan failures*. Ends with a self-review pass: spec coverage, placeholder scan,
type consistency across tasks.

**subagent-driven-development (SDD)** — the most developed skill (4823 words)
and the most interesting engineering. Controller loop, per task:

1. Record `BASE = git rev-parse HEAD`.
2. Run `scripts/task-brief PLAN_FILE N` — an awk script that extracts *just
   that task's* text (fence-aware) to `task-N-brief.md` and prints the path.
   "Never make a subagent read the whole plan file."
3. Dispatch the implementer with only: one line of project placement, the brief
   path, interfaces/decisions from earlier tasks, resolutions of ambiguity, and
   the report-file path. Explicitly forbidden: pasting accumulated history —
   "a real session's dispatch hit 42k chars of which 99% was pasted history."
4. Implementer writes its full report to `task-N-report.md` and returns only
   status, commits, a one-line test summary, and concerns. Four statuses:
   `DONE`, `DONE_WITH_CONCERNS`, `NEEDS_CONTEXT`, `BLOCKED`, each with a
   prescribed controller response.
5. `scripts/review-package PLAN_FILE BASE HEAD` writes commit list + `--stat` +
   `git diff -U10` to a file; the reviewer gets the *path*. "The output never
   enters your own context."
6. Two verdicts required — spec compliance AND task quality. Reviewers may not
   be pre-judged ("if the prompt you are writing contains 'do not flag' … stop").
7. Fix loop, max 5 rounds: rounds ≤3 resume the same implementer agent, rounds
   ≥4 use a fresh implementer on a more capable model; at round 5 a circuit
   breaker trips and the controller adjudicates each open finding.
8. Ledger append, then next task. One broad whole-branch review at the end on
   the most capable model.

Two structural details worth stealing. **The ledger:**
`scripts/sdd-workspace PLAN_FILE` creates
`<repo-root>/.superpowers/sdd/<plan-basename>/` with a self-ignoring
`.gitignore`, one directory per plan. `progress.md`'s first line is
`# SDD ledger — plan: <path>`; tasks with a `Task <N>: complete` line are done.
The rationale is stated: "Conversation memory does not survive compaction. In
real sessions, controllers that lost their place have re-dispatched entire
completed task sequences — the single most expensive failure observed." Plan
scoping exists because a stale ledger misread as current progress made
controllers skip task sequences.

**Rulings, not stalls:** "A running plan does not wait on a human." Conflicts
and ambiguities get decided and recorded as
`Ruling: <what> — <why> — <what it costs if wrong>`. Only four things stop the
loop (irreversible/destructive action, a publish, a cap, a plan broken beyond
guessing). Justification: one donated session sat blocked nine hours on a
question the controller could have decided.

**dispatching-parallel-agents** — one agent per independent problem domain,
all dispatches issued in the *same response* ("Multiple dispatch calls in one
response = parallel execution. One per response = sequential"). Explicit
non-use conditions: related failures, need for full system state.

**test-driven-development** — "The Iron Law: NO PRODUCTION CODE WITHOUT A
FAILING TEST FIRST. Write code before the test? Delete it. Start over." Not
"adapt", not keep as reference.

**verification-before-completion** — a 5-step gate function
(IDENTIFY → RUN → READ → VERIFY → claim) and a table of
claim → required-evidence → not-sufficient rows, including
"Agent completed | VCS diff shows changes | Agent reports 'success'".

**writing-skills** — skill authoring *is* TDD applied to prose: run a pressure
scenario against a subagent with no skill (RED, documenting the exact
rationalizations), write the skill addressing those rationalizations, re-run
(GREEN), then close loopholes (REFACTOR). This is why the Red Flags tables
exist — each row is a captured, observed rationalization.

---

## 5. Token-efficiency mechanisms

**The repo makes no quantified savings claims.** There is no benchmark, no
"reduces tokens by N%", no measurement tooling in this checkout. The one
numeric claim I found is a cross-reference example in
`skills/writing-skills/SKILL.md` — "Always use subagents (50-100x context
savings)" — presented as sample skill prose, not as a measured result. What
follows is therefore **structural**: design choices whose token effect is real
and derivable, but emergent rather than advertised.

| Mechanism | Where | How it saves |
|---|---|---|
| Progressive disclosure | all `SKILL.md` frontmatter | ~485-word bootstrap + 14 descriptions resident vs. 20.7k words of bodies. Bodies load only when invoked. |
| Description-as-trigger-only | SDO section, `writing-skills` | Short descriptions; also prevents the agent short-circuiting on the description (a correctness win that happens to keep descriptions small). |
| Sidecar splitting | e.g. `systematic-debugging/root-cause-tracing.md`, `test-driven-development/writing-good-tests.md` | Heavy reference never enters context unless the specific technique is needed. |
| Artifacts by path, not by paste | SDD §"Everything you paste into a dispatch prompt — and everything a subagent prints back — stays resident in your context for the rest of the session and is re-read on every later turn. Hand artifacts over as files." | The single sharpest insight here. `task-brief`, `review-package`, and report files mean diffs and task text cross agent boundaries through the filesystem, never through the controller's context. |
| Task-scoped briefs | `scripts/task-brief` | Implementer reads one task, not the whole plan. |
| Report contract | implementer returns status + commits + one-line test summary + concerns; full report goes to a file | Bounds what re-enters the controller's context per task. |
| Fresh subagent per task | SDD core principle | No accumulation across tasks; controller context stays coordination-only. |
| No-history dispatches | "Do not paste accumulated prior-task summaries … a real session's dispatch hit 42k chars of which 99% was pasted history" | Kills quadratic prompt growth across a plan. |
| Batching same-shape tasks | SDD "Batch small same-shape work" | One dispatch + one review instead of N of each. |
| No worker-spawned reviewers | `implementer-prompt.md` + `docs/…/2026-07-30-codex-efficiency-fixes-design.md` T1: "9/9 depth-2 spawns across 4 corpora were implementer-issued reviewers; all 9 were same-task duplicates" | Eliminates a whole duplicate review seat per task. |
| Model tiering | SDD "Model Selection" | Cheapest tier for transcription-style tasks, mid-tier floor for reviewers, most capable only for architecture + final review. Caveat stated: "Turn count beats token price" — cheap models take 2-3× turns on multi-step work and cost more overall. **"Always specify the model explicitly when dispatching a subagent"**, since omission inherits the session's (expensive) model. |
| Bootstrap as user message, cached | `.opencode/plugins/superpowers.js` (#750, #894) | Avoids a system block repeated every turn; module-level cache avoids per-step disk+regex work (#1202). |
| Event-driven waiting | 6.3.0 Codex fixes, #2060 | "60–78% of `wait_agent` calls time out in every corpus" — each timeout is a wasted turn. |
| Narration cap | SDD: "between tool calls, narrate at most one short line — the ledger and the tool results carry the record" | Cuts assistant-side token production; also removes "should I continue?" check-ins. |

---

## 6. Harness / context / loop engineering lessons

- **Context lifecycle is a first-class concern.** The hook matcher is
  `startup|clear|compact`, not just `startup`. Compaction is treated as a
  context-loss event that must re-establish the agent's operating instructions.
  Pi re-arms on `session_compact` and inserts the bootstrap *after* the
  compaction summary. Hermes is called out in the README as having no
  post-compaction hook, so a long first turn loses the bootstrap — a documented
  limitation, not hidden.
- **Durable state beats conversational memory.** The ledger exists because
  memory dies at compaction, and the failure mode was expensive and observed.
  The instruction is explicit: "After compaction, trust the ledger and
  `git log` over your own recollection."
- **Subagent isolation is a context-budget instrument, not just modularity.**
  "They should never inherit your session's context or history — you construct
  exactly what they need. This also preserves your own context for coordination
  work." The controller's job is context curation.
- **Filesystem as the inter-agent bus.** Anything large moves as a path.
- **Loops need bounded rounds and a circuit breaker.** 5 fix rounds, escalate
  model at round 4, adjudicate at round 5. Unbounded retry loops are the
  default failure mode of agent harnesses, and this repo names the bound.
- **Autonomy needs an explicit stop list.** Four named stop conditions, plus
  "rulings, not stalls" for everything else, plus a recorded reversible
  decision trail. That is how you get multi-hour unattended runs without
  either stalling or going rogue.
- **Verification must be evidenced in the same message.** "If you haven't run
  the verification command in this message, you cannot claim it passes."
  Notably: an agent's own "success" report is *not* sufficient evidence — a VCS
  diff is.
- **Self-correction is designed in at three layers:** the implementer's own
  diff read, the controller-dispatched two-verdict task review, and one broad
  whole-branch review. Reviews are never pre-judged, and reviewer findings that
  conflict with plan text escalate to a controller ruling rather than silent
  compliance.
- **Behavior-shaping content is code, tested like code.** Red Flags tables are
  captured rationalizations from real failed baselines; the repo requires eval
  evidence before rewording them.

---

## 7. Multi-agent / platform support

Fourteen install paths are documented in the README (Claude Code, Antigravity,
Codex App, Codex CLI, Cursor, Devin CLI, Factory Droid, Gemini CLI, GitHub
Copilot CLI, Grok Build CLI, Kimi Code, OpenCode, Pi, Hermes) — plus a Claude
plugin marketplace and the Superpowers marketplace, and `tests/` has suites for
most of them.

The abstraction collapses to **three integration shapes**, per
`docs/porting-to-a-new-harness.md` Part 4, distinguished only by *how the
bootstrap reaches the model*:

- **A — shell hook**: harness runs a command at session start and reads stdout
  JSON (Claude Code, Cursor, Copilot CLI).
- **B — in-process plugin/extension**: a lifecycle callback mutates the message
  array (OpenCode, Pi, Hermes `pre_llm_call`).
- **C — extension-shipped instructions file**: the harness loads a context file
  the *extension itself* declares (Gemini's `contextFileName` → `GEMINI.md`,
  which is literally two `@`-include lines).

The **hard requirement** is stated as non-negotiable: automatic session-start
injection with **no per-session opt-in**. If the only way in is the user
pasting a prompt or enabling a mode, the harness "cannot be properly
supported." Everything else is a degradation table: subagents degrade to inline
work, todos degrade to a `TODO.md` or plan file, web fetch degrades away — and
skills contain the fallback wording, so the tool mapping just points at the
real tool when it exists. Read/write/edit and shell are non-negotiable.

Two more rules with real teeth: **skills name actions, not tools** (porting
never edits `skills/*/SKILL.md`), and **never edit the user's files** — ship
everything inside the install artifact. And the acceptance test is a single
user message, "Let's make a react todo list", which must auto-trigger
`brainstorming` before any code is written.

Implication for Arcon: harness-agnosticism is achievable if and only if the
content layer is written in an action vocabulary and the per-harness layer is
kept thin (one injector + one tool-map file). The variability is almost
entirely in injection plumbing and tool names — 14 harnesses, three shapes.

---

## 8. What Arcon should adopt

Arcon already has the right bones: `src/arcon/skills/{loader,manager,registry,base}.py`
parses `--- ... ---` frontmatter into `SkillMetadata(name, description, …)` plus
`content`, and `Agent.invoke(query, context=[Message], …)` in
`src/arcon/agents/base.py` is an async generator that takes context explicitly.
Ordered by value-per-effort:

| # | Adopt | From | Where in Arcon | Effort |
|---|---|---|---|---|
| 1 | **Two-tier skill loading.** Today `SkillManager.select_skills()` picks up to 3 skills and `Skill.format_for_prompt()` splices *full bodies* into the prompt. Instead: make all 34 skills' `name + description` resident as a compact index, and add a `load_skill(name)` **tool** so the model pulls a body on demand. | Progressive disclosure; `skills/*/SKILL.md` frontmatter contract | `skills/manager.py`, `skills/base.py`, new builtin tool alongside read/write/list/bash in `tools/builtin.py` | S — the parsing already separates metadata from content |
| 2 | **Subagent runner** on the existing `Agent.invoke(query, context=...)` seam. A `SubagentRunner` that constructs a *fresh* context list (never the parent's history), passes only a brief path + interfaces + a report path, and returns a structured `{DONE, DONE_WITH_CONCERNS, NEEDS_CONTEXT, BLOCKED}` result. | `subagent-driven-development`, `dispatching-parallel-agents` | new `src/arcon/agents/subagent.py`; `invoke`'s explicit `context` param is exactly the right boundary | M |
| 3 | **Artifacts-by-path discipline** as a harness rule, not advice: a workspace helper (Python port of `sdd-workspace`) at `.arcon/sdd/<plan>/`, plus `task_brief(plan, n)` and `review_package(base, head)` helpers that write files and return paths. Nothing large crosses an agent boundary in-context. | `scripts/{sdd-workspace,task-brief,review-package}` | new `src/arcon/workspace/` | S–M (the shell versions are ~40 lines each) |
| 4 | **Ledger / plan persistence.** A `progress.md` (or a `ledger` table beside the existing SQLite `sessions`/`messages`) whose first line identifies the plan, with `Task N: complete` markers and `Ruling:` lines. Resume logic reads the ledger, not the transcript. | SDD Setup section | `src/arcon/storage/` — you already have SQLite + token/cost columns; a ledger table is natural, but keep a human-readable file too | S |
| 5 | **Compaction-aware re-injection.** When Arcon adds compaction, re-inject the bootstrap/skill index *after* the compaction summary, and mark the ledger as the source of truth. Do this before you need it — retrofitting is how the "re-dispatched completed tasks" failure happens. | `hooks.json` matcher `startup\|clear\|compact`; Pi's `session_compact` + `firstNonCompactionSummaryIndex` | `core/session.py`, `cli/chat.py` | S if done early |
| 6 | **Explicit model per dispatch, with a tier policy.** Arcon has a provider resolver (`providers/resolver.py`) and Ollama — perfect fit. Rule: never inherit the parent's model; cheap/local for transcription-shaped tasks, mid-tier floor for reviewers, top tier for architecture and the final review. Encode the "turn count beats token price" caveat. | SDD "Model Selection" | `providers/resolver.py` + subagent runner | M — this is Arcon's differentiator, since you own routing and token accounting |
| 7 | **Bounded fix loop with escalation + circuit breaker.** Max 5 rounds; ≤3 resume the same agent, ≥4 fresh agent one tier up; at 5, adjudicate and record. | SDD §4 fix loop | subagent runner | S once #2 exists |
| 8 | **Ship the methodology skills.** Arcon's 34 skills are mostly domain skills (`frontend-design`, `investor-outreach`, `x-api`) plus a few process ones (`tdd-workflow`, `verification-loop`, `strategic-compact`). It has no brainstorm→plan→execute spine. Write Arcon-native `brainstorming` / `writing-plans` / `executing-plans` / `subagent-driven-development` in the same action vocabulary (MIT license permits adapting these directly, with attribution). | the whole chain | `skills/` | M for good versions; L to actually tune them |
| 9 | **Description-as-trigger-only lint.** A check in `skills/loader.py` (or CI) that descriptions start with "Use when"/state triggers and do **not** summarize workflow, and are <500 chars. Cheap, and it prevents the observed short-circuit bug. | SDO section of `writing-skills` | `skills/loader.py` validation, next to the existing required-fields check | XS |
| 10 | **Skill-authoring-as-TDD + an eval harness.** Pressure-test a skill against an agent *without* it to capture baseline rationalizations, then write the skill against them. Arcon has an `eval-harness` skill already; wire it to real runs. | `writing-skills`, `testing-skills-with-subagents.md`, `superpowers-evals` | `tests/` + new evals dir | L |
| 11 | **Verification gate as a harness feature, not just prose.** Arcon controls the loop, so it can *enforce* it: block a "done" claim unless a verification command ran in the current turn with exit code captured. This is strictly better than Superpowers' prompt-only version. | `verification-before-completion` | tool executor + loop in `core/session.py` | M |
| 12 | **Plan-header contract with `Spec:` and `Global Constraints`, plus `Interfaces: Consumes/Produces` per task.** Machine-checkable, and it is what makes single-task briefs viable. | `writing-plans` | plan template + a validator | S |
| 13 | **Three-shape harness abstraction, inverted.** Arcon is the harness — but the same shape catalog tells you what *your* plugin surface must expose: a session-start injection point, a post-compaction injection point, a skill-load tool, and a subagent dispatch API. Design those four as the public extension API. | `docs/porting-to-a-new-harness.md` | new `src/arcon/hooks/` (currently absent) | M |
| 14 | **Cross-platform hook execution.** The polyglot `run-hook.cmd` trick matters for Windows. Arcon should prefer in-process Python hooks (shape B) precisely because it "sidesteps this entirely", per the porting doc. | `hooks/run-hook.cmd`, `docs/windows/polyglot-hooks.md` | hooks design | S (as a decision) |

Graphify/knowledge-graph has **no analogue** in Superpowers — there is nothing
to borrow there. The nearest adjacent idea is that SDD's `Interfaces:`
Consumes/Produces blocks are a hand-written, plan-scoped dependency graph; a
real code graph could generate those automatically, which is a genuine Arcon
differentiator rather than an adoption.

---

## 9. What Arcon should NOT copy / caveats

- **The all-caps coercion register.** `<EXTREMELY-IMPORTANT>`, "YOU DO NOT HAVE
  A CHOICE", "This is not negotiable. You cannot rationalize your way out of
  this." This is tuned against specific models under specific harnesses, and the
  repo says so ("Our internal skill philosophy differs from Anthropic's
  published guidance… extensively tested and tuned"). It is not portable to
  Ollama-hosted local models, and Arcon has a better lever: enforce in the
  harness (gate the tool call) rather than shout in the prompt. Copy the
  *gates*, not the volume.
- **Prompt-only enforcement generally.** Superpowers can't intercept tool calls,
  so everything is exhortation. Arcon owns the loop — the Iron Law, the
  verification gate, the no-subagent-spawning contract, and the "always specify
  the model" rule should all be code-enforced invariants, not skill prose.
- **Zero-dependency purity.** A defensible policy for a plugin shipped into
  someone else's runtime; wrong for a Python product where `pydantic`,
  `rich`/`textual`, and `pyyaml` earn their keep.
- **Bash-script tooling.** `task-brief` (awk), `review-package`, `sdd-workspace`,
  `lint-shell.sh`, the polyglot `.cmd` — port the *semantics* to Python.
  Shipping bash breaks the Windows target and duplicates work.
- **Skills-as-the-only-abstraction.** Superpowers has no code because it can't
  have code. Arcon shouldn't express plan parsing, ledger management, or
  routing as markdown instructions when a function is available and testable.
- **Claude-Code-specific plumbing**: `CLAUDE_PLUGIN_ROOT`, the
  `hookSpecificOutput.additionalContext` vs `additional_context` dance,
  `${CLAUDE_PLUGIN_ROOT}` interpolation, marketplace manifests, and the `Skill`
  tool name. Relevant only if Arcon later ships *into* those harnesses.
- **Nine parallel manifests kept in sync by `.version-bump.json`.** That's the
  tax of 14 harnesses. Arcon has one artifact; don't pre-build the machinery.
- **The visual companion** (`skills/brainstorming/scripts/server.cjs`, a Node
  browser server, plus logo telemetry). Arcon plans a real UI — a
  bolted-on browser tab is a workaround for harnesses that lack one, and the
  telemetry-in-a-logo pattern is a trust liability.
- **The 94%-rejection contributor posture** and the "we don't accept new
  skills" policy. Correct for a tuned methodology repo with an eval budget;
  hostile for a young project that needs contributors.
- **Mandatory heavyweight ceremony for everything.** Note that 6.3.0 itself
  retreated here — the three-path brainstorming router exists because the
  two-document ritual was too heavy for small tasks. Arcon should ship the
  scaled version from day one: the approval gate never scales, the artifacts
  always do.
- **Unquantified efficiency claims.** Do not repeat "50-100x context savings"
  as fact. Arcon has token/cost columns in SQLite already — measure your own
  numbers and publish those. That is a competitive advantage Superpowers
  structurally cannot claim.
