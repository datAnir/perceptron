# Arcon Master Plan — Synthesis of Eight Reference Repos

**Date:** 2026-09-06
**Inputs:** the eight `*_ANALYSIS.md` docs in this directory (~41,000 words), each written from real source reading
**Supersedes:** `archive/ARCON_FRAMEWORK_CONTRIBUTION_MAP.md` and `archive/ARCON_ENHANCED_PLAN_v0.3.md` (April 2026)

---

## 0. Why the old plan must be retired

The April roadmap was written from architecture summaries, not source. Eight parallel source-level analyses falsified **nine** of its load-bearing premises:

| Old plan assumed | Source says |
| --- | --- |
| copilot-sdk is Java/Maven | Python at `python/copilot/`; Java is 1 of 6 peer SDKs |
| Permissions = `ElicitationHandler` | Separate channel; permissions are `on_permission_request` + a 12-variant `PermissionRequest` union |
| deepagents ships planning/todo middleware | Ships none — `write_todos` comes from LangChain's `TodoListMiddleware` |
| `deepagents/middleware/permissions.py` holds the logic | 5-line re-export; real logic in `filesystem.py::_check_fs_permission` + `_fs_interrupt.py` |
| Onyx merges tool calls semantically | `_merge_tool_calls()` is an allowlist single-field concat — no similarity, no dedupe |
| Onyx KG scopes context (8–49× win) | Query side literally `raise NotImplementedError` in the MIT tree |
| Onyx has "deep research replay" | Generic packet replay for chat history; `dr_loop.py`'s own TODO admits plan-replay is unbuilt |
| ECC has 48 agents / 156 skills | 68 agents / 286 skills / 94 commands / 23 hooks |
| openclaude `QueryEngine.ts` = provider abstraction | It's a turn orchestrator; providers live in `services/api/providerConfig.ts`. Reusable pattern is "one normalizer + gateways-as-**data** (`defineGateway` descriptors)", not "a better `LLMProvider` base class" |
| openclaude cost tracking lives in `cost-tracker.ts` | Pricing/math is in `utils/modelCost.ts`; `cost-tracker.ts` only accumulates + displays. Also: **no daily/monthly aggregation exists anywhere** — it is per-model-per-session only, persisted as one session-id-guarded snapshot |

**Two legal findings that constrain everything:**

1. **openclaude is not clean MIT.** Its `LICENSE` is a NOTICE stating the repo derives from Anthropic's proprietary Claude Code CLI without authorization, and that only *modifications* are MIT. The derived/modified boundary is unmarked in-tree. → **Design reference only. Never copy code.**
2. **autoskills is CC-BY-NC-4.0** (non-commercial). Arcon intends to compete commercially. → **Clean-room pattern port only**; do not reuse its code *or* its skills-map data tables.

Clean licenses: deepagents (MIT), Onyx (MIT, enterprise carve-outs only under `ee/`), ECC (MIT), superpowers (MIT), graphify (verify — dual LICENSE/LICENSE-MIT).

---

## 1. The one architectural decision that gates everything

> **The agent core emits a single typed NDJSON event stream. Every surface is a client of it.**

This is openclaude's most reusable idea and it answers Arcon's "CLI **and** a UI" requirement directly. Its VS Code extension does *not* reimplement the agent — it spawns `openclaude --print --input-format=stream-json --output-format=stream-json` and speaks NDJSON over stdin/stdout. TUI, `--print`, gRPC, SDK, and MCP are all subscribers to the same stream. Permission prompts travel over that same channel.

**Consequence for sequencing:** define the event schema as Pydantic models *before* writing either UI. Retrofitting a second surface onto a print-directly-to-stdout loop costs far more than doing it once. Arcon's `cli/chat.py` currently prints straight to stdout, so this is a refactor, not a greenfield build.

Message kinds to define: `assistant`, `user`, `result`, `system`, `stream_event`, `partial`, `compact_boundary`, `status`, `tool_progress`, `permission_request`, `hook_started/progress/response`, `task_notification`.

**Do not** fork a TUI framework. openclaude's `src/ink/` is ~70 files of reconciler + Yoga layout + termio + cell-diffing plus a native binding. Use Textual or Rich and stay upstream.

---

## 2. Verified state of Arcon today

Confirmed by direct source reading, not docs:

| Fact | Location | Implication |
| --- | --- | --- |
| `format_for_prompt()` returns `f"### Skill: {name}\n\n{content}"` — the **full body** | `skills/base.py:154` | Zero progressive disclosure |
| `select_skills(max_auto_skills=3)` | `skills/manager.py:25` | Up to 3 complete skill bodies per prompt |
| Chat loop never calls `update_session_usage`; `add_message` gets no token counts | `cli/chat.py:195-201` | **Cost columns always read zero** |
| `provider_type`/`model` on `SessionRecord`, not `MessageRecord` | `storage/models.py:19-20` | No per-model attribution across a model switch |
| `ProviderResolver` is a dict-lookup factory | `providers/resolver.py` | Zero routing logic — greenfield |
| `get_cost_per_token() -> (in, out)` 2-tuple | `core/interface.py:90` | **Cannot express cache pricing** — under-reports 2–10× on cached workloads |
| Ollama returns `(0.0, 0.0)` | `providers/ollama.py:155` | "Free" is a lie for hardware you paid for |
| `Agent.invoke(query, context=[Message], ...)` is an async generator | `agents/base.py` | **This is the subagent seam** |
| `tools/executor.py` has no tool-result invariant | `tools/executor.py` | Orphaned tool calls will 400 on strict providers |
| Agent YAML has no `tools:` field, no capability tier | `agents/*.yaml` | Blocks read-only-reviewer safety and cost routing |
| No hooks, no slash commands, no permissions, no subagents, no graph | — | All greenfield |

Baseline: 193/194 tests pass, 64% coverage (96–99% core, **0% CLI**).

---

## 3. Cross-repo convergence: what the sources agree on

**Nobody measures tokens.** superpowers makes no quantified claims. autoskills *deleted* its benchmark script. Onyx's compression claims no measured savings. deepagents has **no cost/token accounting at all**. graphify's 71.5× is corpus-size-dependent by construction (`chars/4` estimation, whole-corpus vs one subgraph, ~1× at 6 files). openclaude tracks cost well but **deliberately excludes** its permission-classifier tokens from accounting.

→ **Token economics is Arcon's clearest differentiator.** There is essentially no prior art to beat. Corollary: count *every* token Arcon spends, including internal classifier/summarizer/title calls, labeled separately rather than hidden.

**Context isolation is achieved by replacement, not filtering.** deepagents `_validate_and_prepare_state`: pass shared non-private state (notably the filesystem), **replace `messages` with a single `HumanMessage(description)`**, return only the last non-empty assistant message. Parent history costs the subagent zero tokens. superpowers reaches the same end differently — **artifacts-by-path**: briefs and diffs cross agent boundaries as *files*, never as pasted text, because anything pasted into a dispatch prompt stays resident and is re-read every subsequent turn.

**Permissions should ask about operations, not tool names.** copilot-sdk's `PermissionRequest` is a 12-variant discriminated union over *semantic* operations — shell command text + `possible_paths`, write + **diff**, read + path — with scope-carrying decisions (`ApproveOnce` / `ForSession` / `ForLocation(location_key=git_root)` / `Permanently` / `Reject(feedback)`), fail-closed to `UserNotAvailable` on missing handler, handler exception, or abstain.

**Every mature harness has a hook system.** ECC's contract, fully documented: JSON on stdin, exit `0`=allow / `2`=block with stderr fed back to the model, stdout `{"hookSpecificOutput": {"hookEventName", "additionalContext"}}` for context injection. 7 events, 23 hooks. Hard-won lessons: consolidate dispatchers (~50–100ms per spawn), split sync/async, cap SessionStart injection at 8000 chars, ship env kill-switches.

---

## 4. Dependency-ordered roadmap

Ordering rule: **measurement before optimization, protocol before surfaces, correctness before features.**

### Phase 0 — Foundations (2–3 weeks)

Nothing here is user-visible; everything after depends on it.

| # | Item | Source | Effort |
| --- | --- | --- | --- |
| 0.1 | **Neutral `Usage` dataclass + normalization at the provider boundary.** Three providers, three usage shapes (Anthropic `cache_read_input_tokens`; OpenAI `prompt_tokens_details.cached_tokens`; Ollama `prompt_eval_count`/`eval_count`) → one canonical type. Honest-N/A rule: Ollama reports no cache data → `supported=False`, render "N/A", never a fabricated 0%. Define Arcon's **own** neutral types — do not adopt a vendor shape as canonical (openclaude's coupling to `BetaUsage` forced shim gymnastics). | openclaude §3.3 | 1–2 d |
| 0.2 | **Tiered pricing model.** Replace the 2-tuple with `ModelCosts(input_per_1m, output_per_1m, cache_write_per_1m, cache_read_per_1m, web_search_per_req)`; shared `COST_TIER_*` constants; canonicalize model name before lookup. Ship as a **data file with a version stamp**, not a hardcoded constant. Unknown model → default tier **plus** a flag that makes `/cost` say so. User pricing overrides readable only from user/local config, never project/repo config. | openclaude §3.1 | 2 d |
| 0.3 | **Close the accounting loop.** One `add_to_session_cost(cost, usage, model)` chokepoint at the single place provider responses are consumed. Add `cache_read_tokens`/`cache_write_tokens` columns and `model`/`provider_type` to `MessageRecord`. | verified gap | 1 d |
| 0.4 | **NDJSON event schema** (§1). Pydantic models + emitter; refactor `cli/chat.py` to be a *subscriber*. | openclaude §9 | 3–4 d |
| 0.5 | **Tool-result invariant.** Every assistant tool-call id must get a matching result or strict providers (Bedrock Converse) hard-fail 400. Synthesize failure results; contain per-tool exceptions; drop orphaned responses. | Onyx `dr_loop.py:731` | 1–2 d |
| 0.6 | **Explicit config object.** Credentials and routing in an immutable config, not `os.environ`. openclaude needed to clear ~25 env vars before an override and 30+ follow-up credential-isolation fixes. Touch `os.environ` only when spawning subprocesses. | openclaude §12.4 | 2 d |
| 0.7 | **CLI test coverage** from 0%. | baseline gap | 3 d |

**Exit criteria:** `arcon costs` reports real non-zero numbers with cache lines itemized; every surface consumes the event stream; CLI coverage >70%.

### Phase 1 — Token economics + progressive disclosure (2 weeks)

First user-visible wins, and the differentiator.

| # | Item | Source | Effort |
| --- | --- | --- | --- |
| 1.1 | **Progressive skill disclosure.** Make the 34 *descriptions* resident; bodies load via a `load_skill(name)` tool. Listing budget = `max(1% of context window, 8000 chars)`, per-entry description cap 250 chars, degradation ladder full→truncate→names-only, subagent budget 4000, announce only newly-loaded skills. Add **conditional skills** via `paths` frontmatter — zero tokens until a matching file is touched. | superpowers + openclaude §7.3 | 3 d |
| 1.2 | **`arcon costs` command + per-turn footer.** Per-session / per-model / per-agent, plus **daily / monthly rollups — which are Arcon-original**: openclaude has no time-based aggregation at all (per-model-per-session snapshot only), so this is net-new design, not a port. Arcon's SQLite `created_at` columns make it a straightforward `GROUP BY`. Label internal (classifier, summarizer, title) tokens separately — never hide them. | openclaude §3.4/§3.6 + Arcon-original | 3 d |
| 1.3 | **USD budget ceiling.** `max_budget_usd` checked between turns → structured `error_max_budget_usd`. | openclaude | 0.5 d |
| 1.4 | **Benchmark harness.** Fixed task suite, measured token deltas per feature. Every later claim must cite it. | none — Arcon's own | 3 d |
| 1.5 | **Tool metadata for parallelism + cache stability.** `is_read_only` / `is_concurrency_safe` / `is_destructive`, **fail-closed defaults**. Keep tool ordering stable (builtins as a contiguous sorted prefix) — unstable ordering silently destroys prompt-cache hit rate and therefore the numbers Arcon reports. | openclaude §8 | 1–2 d |

### Phase 2 — Permissions + hooks (3 weeks)

Safety and extensibility. Both are prerequisites for autonomous subagents.

| # | Item | Source | Effort |
| --- | --- | --- | --- |
| 2.1 | **Permission system.** Semantic-operation requests (shell+paths, write+**diff**, read+path, tool+args), scope-carrying decisions (`Once`/`Session`/`Location(git_root)`/`Permanently`/`Reject(feedback)`), **fail-closed**. Requests travel over the event stream (§1). | copilot-sdk §4 | 5–7 d |
| 2.2 | **`permissions: {allow, deny, ask}` config** with `Tool(pattern)` syntax; settings layering (user vs project vs local). Ship ECC's security-guide deny-list as a default. | ECC §7 | 3–5 d |
| 2.3 | **Hook system.** 7 events; JSON stdin; exit 0=allow / 2=block-with-stderr-to-model; stdout `additionalContext` injection. One consolidated dispatcher (not one process per hook), sync/async split, 8000-char injection cap, env kill-switch. `tools/executor.py` is the dispatch point. | ECC §6 | 5–7 d |
| 2.4 | **Agent YAML gains `tools:` + capability tier.** Unblocks read-only reviewers and cost-based routing. | ECC §10 | 1 d |

### Phase 3 — Model routing + local LLMs (2–3 weeks)

| # | Item | Source | Effort |
| --- | --- | --- | --- |
| 3.1 | **`route_model()` as a pure function.** 9 ordered escalate-to-strong rules, `STRONG_KEYWORDS` (24 anchors), 160-char / 28-word defaults, always return a human-readable `reason`. Reads no env/global state. **Off by default.** Then the policy wrapper: pin per turn, enforce allowlist, disable-per-session on conflict, drop pin on provider swap. | openclaude §4.2 | 3 d |
| 3.2 | **Context-window precedence ladder:** exact-env > builtin-catalog > env-prefix > user-config pin > **discovered** > descriptor-default. Rationale: a gateway-advertised number has no provenance, so only explicit user intent may outrank it. | openclaude §5 | 1 d |
| 3.3 | **Escalation taxonomy** — three distinct mechanisms: routed-error escalation (400/401/403 propagate; everything else including 404/429 retries on strong), capacity fallback after N consecutive overloads, and the retry loop itself with **foreground-only** retry allowlist so background summarizers don't amplify an outage. | openclaude §4.3 | 2 d |
| 3.4 | **Local fast path.** On loopback/RFC1918: skip deterministic-JSON hashing, strict tool-schema rewriting, tool-history compression — these dominate multi-second local round-trips. Detection ladder + `/v1` retry + `localhost`→`127.0.0.1`. | openclaude §5 | 1–2 d |
| 3.5 | **Text tool-call rescue for small local models.** Brace-depth balanced-JSON walk (not regex), fenced + bare, dedupe, return ranges so JSON can be stripped from display. Detect at **stream level**, not from a static capability table — small models are inconsistent turn to turn. Also Onyx's Ollama history flattener (`[Tool Call] …` / `[Tool Result] …`) and `num_ctx=32768`. | openclaude §5 + Onyx `llm_step.py:727` | 2–3 d |
| 3.6 | **Per-agent routing.** `agent_routing` (name > subagent_type > "default") with normalized keys + collision warning; `max_steps` in frontmatter. Cheap local model for search agents, strong cloud model for the planner. | openclaude §4.4 | 2 d |
| 3.7 | **Honest Ollama cost.** Stop reporting `(0.0, 0.0)`. Report `None`/N-A, or let users set an electricity/amortization rate via the override path. | openclaude §3 | 0.5 d |

### Phase 4 — Subagents + loop engineering (3 weeks)

The stated top priority. Deliberately placed after measurement (Phase 1) and safety (Phase 2).

| # | Item | Source | Effort |
| --- | --- | --- | --- |
| 4.1 | **Subagent runner.** Seam: `Agent.invoke(query, context=...)`. Isolation by **replacement** — pass shared state (filesystem, graph) but construct a fresh context containing only a task brief; return only the final assistant message. Parent history costs the subagent zero tokens. | deepagents §5 | 5 d |
| 4.2 | **Artifacts-by-path discipline, code-enforced.** Briefs and diffs cross agent boundaries as files under a workspace dir, never as pasted text. superpowers can only *exhort* this in prose; Arcon owns its loop and can enforce it. | superpowers | 3 d |
| 4.3 | **Progress ledger.** Plan-scoped file, trusted over recollection after compaction. Exists because controllers that lost their place re-dispatched entire completed task sequences — "the single most expensive failure observed." | superpowers | 2 d |
| 4.4 | **Code-enforced loop invariants:** verification gate before completion; bounded fix loop (5 rounds) with model escalation; never inherit the parent's model; workers may not spawn reviewers. | superpowers §8 | 3 d |
| 4.5 | **Parallel dispatch** via `asyncio.gather` with concurrency guardrails (`max_concurrent_subagents`, `max_total_subagents`, `timeout_seconds`). deepagents delegates parallelism to the model's tool-call batching; Arcon's asyncio can do better. | copilot-sdk + deepagents | 2 d |
| 4.6 | **Tiered compaction.** Micro-compaction *first* (drop old tool-result bodies → marker; no model call, recovers most tokens), then LLM summarization. Evict >20k-token tool results to files and embed the path in the summary rather than dropping content. Fraction-based thresholds (0.85 trigger / 0.10 keep), clamped so a window increase can never trigger an *earlier* compact. `ContextOverflowError` → catch-compact-retry. 3-strike circuit breaker with cooldown. | deepagents §8 + openclaude | 4 d |

### Phase 5 — Codebase graph (2 weeks)

| # | Item | Source | Effort |
| --- | --- | --- | --- |
| 5.1 | **graphify behind an `arcon[graph]` extra.** 25 tree-sitter grammars are *hard* deps (tens of MB) — do not put them in the base install. Skip `[mcp]` (decision: in-process). Self-registering tools so base Arcon works without it. **musl wheels don't exist** → Alpine compiles all 25 from source; document or ship a Debian-based image. | graphify §2, §9 | 2 d |
| 5.2 | **Pin `graphifyy==0.9.55` exactly + contract test.** NL query and shortest-path exist only as **private** `serve._query_graph_text()` / `serve._shortest_path_text()`, absent from the 17-name public map; releases land every ~1.5 days. Test asserts each imported symbol exists with expected arity. | graphify §7 | 1 d |
| 5.3 | **`GraphQueryTool` / `GraphPathTool` / `AffectedTool`** in the existing `ToolRegistry`; `graph.json` cached per workspace with mtime/size-keyed invalidation. | graphify §8 | 4 d |
| 5.4 | **Prompt agents to query subgraphs instead of reading whole files.** The real win is targeted reads — every tool line carries `source_file:Lline`. Surface `EXTRACTED` vs `INFERRED` honestly: ~half the edges on small corpora are inferences an agent would otherwise assert as fact. | graphify §3, §6 | 2 d |
| 5.5 | **Do not repeat graphify's benchmark claim.** Report Arcon's own measured numbers from 1.4, with corpus size stated. | graphify §6 | — |

*Fallback if graphify's private-API risk proves unacceptable:* openclaude's `docs/repo-map.md` specifies a near-direct Python port — `git ls-files` → tree-sitter symbols → directed reference graph weighted by reference-count × IDF of symbol name → PageRank → render to a token budget, cached by (path, mtime, size). `tree_sitter` + `networkx` are already available. ~1 week.

### Phase 6 — Breadth (ongoing)

- **Tool-call merging** — port Onyx's `_merge_tool_calls()` allowlist field-concat retargeted at `read_file{paths}` / `grep{patterns}`, and *improve* it by adding the de-duplication Onyx lacks. Half a day.
- **Tech auto-detection** — clean-room Python `ProjectScanner`: six-signal detect DSL (`packages`, `packagePatterns`, `configFiles`, `fileExtensions`, `gems`, `configFileContent`) as pure data, one generic short-circuit-OR evaluator, per-directory cache, workspace-union pass. **Guard duplicate IDs at load** — autoskills' first-wins dedupe silently disabled its own Python/FastAPI/Django entries. 1 week.
- **Slash commands** — three kinds, but keep to "returns text" / "returns a prompt". Copy the `availability` (static, who *may*) vs `isEnabled()` (dynamic, is it *on now*) distinction verbatim. Defer interactive-component commands until the event stream is stable.
- **Agent + skill library** — expand from 5 agents toward ECC's taxonomy; **curate, don't bulk-import** (ECC's `validate-skills.js` downgrades frontmatter failures to WARN so CI won't break on pre-existing defects; the documented `references/`/`templates/`/`scripts/` layout is used by only 8/1/11 of 286 skills, `evals/` by zero). Drop the ~10 non-engineering marketing/investor skills already in Arcon's 34.
- **MCP** — both consume and expose. Onyx's `mcp_server/` is the reference.
- **Skill registry security** — only if Arcon accepts third-party skills. Ordered chain: pinned SHA-256 (CRLF-normalized for cross-platform digest stability) → check revocations **before download** → verify digest → validate content (no symlinks, no NUL bytes, no lockfiles, flag `curl|sh`). Three revocation granularities (`{id}`, `{id,version}`, `{sha256}` alone to defeat republication). **Fail closed** — only ENOENT/404 means "no revocations". **Improve on openclaude:** check revocations on *load*, not just install. Content-addressed cache keyed by bundle hash gives idempotency and cheap upgrades for free.
- **Cross-platform** — Python makes this structurally easier than Node. Adopt: a `doctor` command emitting machine-readable JSON; ship ripgrep as a dependency rather than assuming it; PowerShell-specific tooling and docs for Windows. Note no reference repo ships RPM/RedHat packaging — that's Arcon-original work.

---

## 5. Distinctive features (the competitive case)

Ordered by how defensible each is:

1. **Real token economics.** No reference repo measures its own savings; several deleted or omitted benchmarks; one excludes its own classifier's tokens; and **none has daily/monthly cost aggregation** (openclaude, the only one tracking cost properly, is per-session only). Arcon counting *every* token — internal calls labeled separately — with a per-turn footer, time-based rollups, a budget ceiling, and a reproducible benchmark harness is genuinely novel.
2. **Cost-aware routing to local models.** openclaude has the only real router found, and it's off by default and cloud-oriented. Arcon pairing the 9-rule classifier with first-class Ollama support (fast path, text tool-call rescue, honest local cost) targets a real unserved need: route trivial turns to a 1.5B local model, hard turns to Sonnet, and *show the user what that saved*.
3. **Code-enforced loop discipline.** superpowers must exhort in prose because it doesn't own the loop. Arcon owns it — verification gates, bounded fix loops, no-parent-model-inheritance, and artifacts-by-path become invariants instead of instructions.
4. **Graph-scoped context as a default.** Not novel alone, but combined with subagent isolation it multiplies: subagents receive subgraph slices, not file dumps.
5. **One protocol, many surfaces.** CLI + TUI + web UI + MCP + SDK as clients of one NDJSON stream — designed in from Phase 0 rather than retrofitted.

---

## 6. Risks

| Risk | Mitigation |
| --- | --- |
| openclaude license contamination | Design reference only; Python boundary; never cite as upstream |
| autoskills non-commercial license | Clean-room; no code, no data tables |
| graphify private APIs + ~1.5-day release cadence | Exact pin + contract test; repo-map fallback specified |
| 25 mandatory tree-sitter grammars | `arcon[graph]` extra; base install stays light |
| No musl wheels | Debian-based image; document Alpine cost |
| Scope: 6 phases ≈ 14–16 weeks | Phase 0+1 alone ships a defensible product; each phase is independently shippable |
| Reference repos churn | All findings are snapshots at 2026-09-06 HEAD; re-verify before porting |
| Model ids/prices in analyses | Do **not** transcribe as ground truth; re-verify against provider docs |

---

## 7. Immediate next actions

1. `docs/EVENT_SCHEMA.md` — the NDJSON contract (blocks the most).
2. Phase 0.1–0.3 as one PR: `core/usage.py`, `core/pricing.py`, close the accounting loop. Turns `arcon costs` from zeros into real numbers in ~4 days.
3. Phase 1.4 benchmark harness immediately after, so every later phase reports measured deltas.
4. Then Phase 1.1 progressive disclosure — the cheapest large win, and 1.4 will prove it.

---

*All findings sourced from the eight analysis docs in this directory, each written from direct source reading at 2026-09-06 HEAD. Where a source contradicted Arcon's April roadmap, the source won and the contradiction is recorded in §0.*
