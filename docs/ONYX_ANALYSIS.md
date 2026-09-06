# Onyx (onyx-dot-app/onyx) — Analysis for Arcon

Scope: only the subsystems transferable to a coding agent — agent/chat loop, tool running & merging, deep research, context compression, KG, MCP, LLM provider abstraction, observability. Everything below was read from source at `/home/anirband/perceptron/onyx`. Where I could not verify a claim, I say so.

---

## 1. Overview

Onyx (formerly Danswer) is an enterprise Gen-AI chat + search platform over company knowledge: connectors ingest documents, an indexing pipeline embeds/chunks them, and an agentic chat loop answers with citations.

**License** — `/home/anirband/perceptron/onyx/LICENSE` is **MIT Expat**, with a carve-out: everything under an `ee/` directory is under the *Onyx Enterprise License*. The three enterprise trees are `backend/ee/`, `web/src/app/ee/`, `web/src/ee/`. **All subsystems in this analysis are in the MIT portion** (`backend/onyx/...`) — no license blocker for porting patterns into Arcon, subject to MIT attribution.

**Stack** (from `pyproject.toml`, `CLAUDE.md`):

| Layer | Tech |
|---|---|
| API | FastAPI 0.133, Python 3.11, uvicorn |
| Relational | PostgreSQL + SQLAlchemy + Alembic |
| Cache/coord | Redis |
| Search | Vespa **and** OpenSearch (`backend/onyx/document_index/{vespa,opensearch}/`) |
| Async | Celery (9 worker classes: primary, docfetching, docprocessing, light, heavy, kg_processing, monitoring, user_file_processing, beat) |
| LLM | LiteLLM 1.81 (single abstraction over all providers) |
| MCP | FastMCP 3.2 |
| Metrics | `prometheus_fastapi_instrumentator`, `prometheus_client` |
| Frontend | Next.js 15 / React / TS / Tailwind |

**Maturity** — high. Real design docs live next to the code (`chat/README.md` is a 16 KB context-engineering essay; `chat/COMPRESSION.md`; `mcp_server/README.md`), four distinct test tiers (unit / external-dependency-unit / integration / Playwright), strict typing enforced, tracing to Braintrust and Langfuse. The chat loop alone is ~19k lines across `chat/`, `tools/`, `deep_research/`.

**Monorepo layout** — `backend/` (onyx CE + ee), `web/` (Next.js), `desktop/`, `widget/`, `extensions/chrome/`, `cli/`, `deployment/`, `docs/`, `examples/`, `profiling/`. ~62 connector packages under `backend/onyx/connectors/` — *mentioned once, out of scope.*

---

## 2. Relevant architecture map

```
backend/onyx/
├── chat/
│   ├── process_message.py      # turn setup, validation, multi-model thread pool, save, compression trigger
│   ├── llm_loop.py             # run_llm_loop: the agent while-loop (max 6 cycles) + construct_message_history
│   ├── llm_step.py             # run_llm_step: ONE inference; streaming→packet translation, history→LLM format
│   ├── chat_state.py           # ChatStateContainer (accumulate-only) + ChatTurnSetup
│   ├── emitter.py              # Emitter: push packets to shared queue, tagged with model_index
│   ├── compression.py          # branch-aware progressive history summarization
│   ├── citation_processor.py   # DynamicCitationProcessor — streaming citation rewriting
│   ├── chat_utils.py           # history building, create_tool_call_failure_messages
│   ├── prompt_utils.py         # build_system_prompt / build_reminder_message
│   ├── README.md, COMPRESSION.md  # ← read these first
├── tools/
│   ├── interface.py            # abstract Tool[TOverride] (id/name/description/tool_definition/emit_start/run)
│   ├── tool_runner.py          # _merge_tool_calls + run_tool_calls (parallel threadpool exec)
│   ├── built_in_tools.py       # BUILT_IN_TOOL_MAP registry, STOPPING_TOOLS_NAMES, CITEABLE_TOOLS_NAMES
│   ├── tool_constructor.py     # per-turn tool instantiation from DB config
│   ├── tool_implementations/   # search, web_search, open_url, python, images, file_reader, memory, mcp, custom, knowledge_graph
│   └── fake_tools/research_agent.py  # the DR sub-agent, implemented as a pseudo-tool
├── deep_research/
│   ├── dr_loop.py              # orchestrator: clarify → plan → N research cycles → report
│   ├── dr_mock_tools.py        # think_tool / research_agent / generate_report / generate_plan schemas
│   └── utils.py                # think-tool streaming token processor, special-tool-call detection
├── kg/                         # entity/relationship extraction, normalization, clustering (Celery-driven)
├── mcp_server/                 # FastMCP server exposing Onyx search over HTTP (port 8090)
├── llm/
│   ├── interfaces.py           # LLM ABC + LLMConfig; auto-wraps invoke/stream with tracing
│   ├── multi_llm.py            # LitellmLLM — the one concrete impl; per-provider quirk handling
│   ├── factory.py, cost.py, model_name_parser.py, prompt_cache/
├── tracing/                    # own span framework + Braintrust/Langfuse processors + masking
└── server/
    ├── query_and_chat/streaming_models.py  # ~60 Packet obj types
    ├── query_and_chat/placement.py          # Placement(turn/tab/sub_turn/model_index)
    └── metrics/                             # ~14 Prometheus collector modules
```

---

## 3. The chat/agent loop

Three layers, documented in `chat/README.md`. Vocabulary: a **turn** = user message → final answer; a **step/cycle** = one LLM inference.

**Layer 1 — `process_message.py`** validates the request, builds branch-aware history, loads files/images, constructs tools, then calls `_run_models(setup, user, db_session)`. Each model runs in its own `ThreadPoolExecutor` worker with its own DB session and its own `Emitter`; workers push `(model_idx, packet)` onto an unbounded `merged_queue`; the main thread drains and yields in arrival order. N=1 and N=3 (multi-model comparison) use the identical path. Stop: the drain loop polls `check_is_connected()` on a 50 ms queue timeout, and a `drain_done: threading.Event` lets emitters stop blocking so workers exit fast. If a worker raises, the main thread yields a `StreamingError` for that model and keeps the others alive.

**Layer 2 — `run_llm_loop()`** (`chat/llm_loop.py:622`), `MAX_LLM_CYCLES = 6`. Per cycle:
1. Decide `tool_choice`: `REQUIRED` if a forced tool, `NONE` + empty tool list on the last cycle or after an image-gen (`STOPPING_TOOLS_NAMES`), else `AUTO`.
2. Rebuild the system prompt (`build_system_prompt`) — tool descriptions and the citation section are conditional on what ran this turn.
3. Build a **reminder** message appended at the very end of context (`build_reminder_message`, or `IMAGE_GEN_REMINDER` / `OPEN_URL_REMINDER`).
4. `construct_message_history(...)` → token-budgeted, structurally-aware history (see below).
5. `run_llm_step(...)` → `LlmStepResult(reasoning, answer, tool_calls, raw_answer)`.
6. `_try_fallback_tool_extraction(...)` — if the model emitted tool calls as text/XML instead of via the tool API, parse them out. Allowed **once** per turn to bound looping on weak models.
7. `run_tool_calls(...)`, then append **one** ASSISTANT message holding all `tool_calls` + one `TOOL_CALL_RESPONSE` per call (OpenAI parallel format).
8. Break when there are no tool calls (the model answered).

**`construct_message_history()`** (`llm_loop.py:311`) is the real context engineer. It subtracts system prompt + custom-agent prompt + project files + reminder tokens from `max_input_tokens`, hard-requires that the last user message and everything after it fits (else raises), then truncates *older* history from the top. Two nice details: `_drop_orphaned_tool_call_responses()` removes `TOOL_CALL_RESPONSE` messages whose parent assistant tool-call message got truncated away (Ollama rejects those); and dropped file messages are replaced by a compact **forgotten-files metadata message** so the `read_file` tool can re-fetch them by id.

**Layer 3 — `run_llm_step()`** / `run_llm_step_pkt_generator()` (`chat/llm_step.py`) is one inference. It translates the stream into typed packets (`ReasoningStart/Delta/Done`, `AgentResponseStart/Delta`, tool-specific starts/deltas, `SectionEnd`, `OverallStop`), accumulates reasoning/answer/tool-call fragments separately, and accepts a `custom_token_processor` hook `(Delta, state) -> (Delta|None, state)` used by deep research.

**Streaming/packet model** — every packet is `Packet(placement, obj)` with `Placement(turn_index, tab_index, sub_turn_index, model_index)`. `turn_index` is a *frontend render block*, not a backend turn — reasoning and the tool call from one inference are two `turn_index`es. `tab_index` disambiguates parallel tool calls; `sub_turn_index` handles tools-invoking-tools (DR sub-agents). `TopLevelBranching(num_parallel_branches=N)` is emitted before a parallel fan-out. Saved messages can be **replayed** as packet lists via `translate_assistant_message_to_packets` (`server/query_and_chat/chat_backend.py:348`) so the UI reconstructs history identically to live streaming.

**State** — `ChatStateContainer` (`chat/chat_state.py`) is accumulate-only by contract ("should not be used for logic"), holding answer tokens, reasoning, tool calls, citation mapping, search docs. It exists so any layer can contribute without threading returns up the stack, and so a partial save is possible on cancellation. Three message representations, deliberately separated: `ChatMessage` (DB) → `ChatMessageSimple` (canonical) → `LanguageModelInput` (LLM-facing, minimal).

---

## 4. Tool system & `tool_runner` — deep dive

**Definition** — `tools/interface.py`: `class Tool(abc.ABC, Generic[TOverride])` with abstract `id`, `name` (LLM-facing), `description`, `display_name`, `tool_definition() -> dict` (raw OpenAI function-schema dict, hand-written per tool — no decorator/introspection magic), `emit_start(placement)`, and `run(placement, override_kwargs: TOverride, **llm_kwargs)`. Plus `is_available(db_session)` for dynamic gating and `should_emit_argument_deltas()`.

The `TOverride` generic is the key idea: **arguments the LLM supplies** arrive as `**llm_kwargs`, while **arguments the host injects** (original user query, citation offsets, chat files, existing memories) arrive as a typed `override_kwargs` model. Clean separation of model-controlled vs. harness-controlled input.

**Registration** — `built_in_tools.py` is a static `BUILT_IN_TOOL_MAP: dict[str, Type[...]]` keyed by class name, plus a derived `TOOL_NAME_TO_CLASS` and two behavioral tag lists (`STOPPING_TOOLS_NAMES`, `CITEABLE_TOOLS_NAMES`). Per-turn instances are built by `tool_constructor.py` from DB config; MCP and OpenAPI "custom" tools are constructed dynamically.

### Tool-call merging — it exists, and here is the real algorithm

Arcon's roadmap cites a "merge similar tool calls" algorithm. **It is real**, at `tools/tool_runner.py:53`, `_merge_tool_calls()`. It is much simpler than the name suggests — there is no semantic similarity, no embedding, no dedup:

```python
MERGEABLE_TOOL_FIELDS: dict[str, str] = {
    SearchTool.NAME:    QUERIES_FIELD,  # "queries"
    WebSearchTool.NAME: QUERIES_FIELD,
    OpenURLTool.NAME:   URLS_FIELD,     # "urls"
}
```

1. Group incoming `ToolCallKickoff`s by `tool_name` (`defaultdict(list)`).
2. For a group whose tool is in the allowlist **and** `len(calls) > 1`: concatenate the list-valued merge field across all calls (`all_values.extend(...)`, coercing a bare string to `[str(v)]`), copy `calls[0].tool_args`, overwrite the merge field, and emit **one** `ToolCallKickoff` reusing `calls[0].tool_call_id` and `calls[0].placement`.
3. Everything else passes through untouched.

So: **allowlist-driven, single-field list concatenation, first-call-wins for id/placement.** No de-duplication of identical queries, no cross-tool merging. Note the consequence: the other tool-call ids are silently discarded, which is only safe because the LLM's assistant message is rebuilt from the *merged* calls afterwards.

**Execution** — `run_tool_calls()` (`tool_runner.py:222`):
- merge → build `tools_by_name` → drop unknown tools with a warning (they don't count against the cap) → truncate to `max_concurrent_tools` (calls beyond the cap are **dropped, not queued**).
- Compute shared inputs once: `minimal_history` (`ChatMinimalTextMessage`), the last user message, and a reversed `url → citation_num` map.
- Per call, build the typed `override_kwargs` and **allocate a disjoint citation range by advancing `starting_citation_num += 100`** for each citeable tool — a neat trick to avoid citation-number collisions under parallelism without locking.
- `tool.emit_start(placement)` before dispatch.
- `run_functions_tuples_in_parallel(..., allow_failures=True, max_workers=max_concurrent_tools, timeout=TOOL_EXECUTION_TIMEOUT_SECONDS)` where the timeout is **10 minutes**.
- `_safe_run_single_tool()` wraps each call in a `function_span`, catches `ToolCallException` (expected — uses `e.llm_facing_message`), `ToolExecutionException`, and bare `Exception`, converting all into `ToolResponse(rich_response=None, llm_facing_response="Tool failed with error: ...")`, attaching a `SpanError` with args + stack trace, and **always** emitting `SectionEnd`. A failed tool therefore never breaks the loop — the model just reads the error.

Each `ToolResponse` carries both `llm_facing_response` (the string the model sees) and `rich_response` (typed object for UI/DB). That two-channel return is the single most portable idea in the tool layer.

**Memory tool** (`tool_implementations/memory/memory_tool.py`) — `NAME = "add_memory"`, one parameter `memory: str`. The interesting part is that it is **LLM-mediated**: `run()` calls `process_memory_update(new_memory, existing_memories, chat_history, llm, user_name, user_email, user_role)`, which uses a second LLM call to decide *add vs. replace-at-index*, returning `MemoryToolResponse(memory_text, index_to_replace: int | None)`. Persistence is deliberately **not** in the tool — `run_llm_loop` inspects the rich response and calls `add_memory()` / `update_memory_at_index()` (`llm_loop.py`, `MemoryToolResponseSnapshot`). Existing memories are also injected into the system prompt via `build_system_prompt(user_memory_context=...)`, with an `inject_memories_in_prompt` flag that can strip them from search-tool query expansion while still passing them to the memory tool.

**Image / file tools** — `ImageGenerationTool` is in `STOPPING_TOOLS_NAMES`: after it runs, the next cycle forces `tool_choice=NONE` plus an `IMAGE_GEN_REMINDER` so the model doesn't fabricate `attachment://` markdown links. Generated images are persisted as `GeneratedImage` objects on the tool call for replay (`db/models.py:2804`). `FileReaderTool` (`read_file`) takes a UUID `file_id` and pairs with the forgotten-files metadata message described above. `PythonTool` (code interpreter) receives `chat_files` via `PythonToolOverrideKwargs`, and search hits that carry raw source files are auto-staged into `chat_files` by `build_python_chat_files_from_search_docs` so the next code call already sees them.

---

## 5. Context compression

`chat/compression.py` (448 lines) + `chat/COMPRESSION.md`. Strategy: **summarize old messages, keep recent ones verbatim, branch-aware, progressive.**

**Trigger** — *after* the turn is saved, not mid-loop (`process_message.py:1713`): rebuild the history chain, `calculate_total_history_tokens()` (sums the persisted `token_count` per message — no re-tokenization), then `get_compression_params(max_input_tokens, current_history_tokens, reserved_tokens)`. Compress iff `history_tokens > (max_input_tokens - reserved_tokens) * COMPRESSION_TRIGGER_RATIO` (default **0.75**, env-overridable). Budget for verbatim tail = `current_history_tokens * RECENT_MESSAGES_RATIO` (**0.2**, a module constant).

**Branch-awareness** — the summary is stored as a *new* `ChatMessage` with two pointers: `parent_message_id` = last message at compression time (places it in the tree), and `last_summarized_message_id` = the cutoff. `find_summary_for_branch()` fetches all summaries for the session and returns the first whose `parent_message_id` is in the current history's id set (explicitly avoiding an `IN` clause for long histories). The rationale in COMPRESSION.md is sharp: embedding the summary *into* an existing message would leak post-fork context into sibling branches.

**Selection** — `get_messages_to_summarize()`: filter to messages after any prior cutoff, drop empty ones, walk backwards accumulating until the recent budget is exceeded, then **pop leading non-USER messages off the recent list so the cutoff always lands immediately before a user message**. Everything else is summarized.

**Prompt** — `generate_summary()` sends: system prompt (`SUMMARIZATION_PROMPT`, plus `PROGRESSIVE_SUMMARY_SYSTEM_PROMPT_BLOCK` with the previous summary if any) → older messages as real `UserMessage`/`AssistantMessage` objects → a `SUMMARIZATION_CUTOFF_MARKER` user message → recent messages (context only, not to be summarized) → a final reminder. Progressive: the previous summary is fed in so nothing is lost across repeated compressions.

**Aggressive tool-response handling** — `_build_llm_messages_for_summarization()` collapses an assistant message with tool calls to the literal string `"[Used tools: search, web_search]"` and **skips `TOOL_CALL_RESPONSE` messages entirely**. Separately and independently of compression, `chat/README.md` states that in the *live* history tool responses "are currently replaced with a hardcoded string saying it is no longer available" while the tool-call arguments are kept (information-dense, cheap). I read this in the README but did **not** locate the constant/code path implementing that replacement — treat it as documented intent I could not confirm in code.

**Savings** — no measured or claimed numbers anywhere in the module or the doc. COMPRESSION.md instead flags a *cost*: high `reserved_tokens` makes compression fire often, which is "costly, slow, and leads to a bad user experience."

---

## 6. Deep research

`deep_research/dr_loop.py:195`, `run_deep_research_llm_loop()`. Dispatched from `process_message.py:1167`. Hard precondition: `max_input_tokens >= 50_000`. This is the strongest loop-engineering reference in the repo.

**Four phases:**

1. **Clarification** (skippable via `SKIP_DEEP_RESEARCH_CLARIFICATION` or a param). System prompt = `CLARIFICATION_PROMPT`, single tool offered = `generate_plan` (zero-arg), `tool_choice=AUTO`, history limited to `last_n_user_messages=5`. If the model produces **no** tool call, that text *is* the clarifying question: set `state_container.set_is_clarification(True)`, emit `OverallStop`, return and wait for the user. Elegant — "call the tool to proceed, or just talk to ask" needs no extra schema.
2. **Plan** — `RESEARCH_PLAN_PROMPT`, no tools, `tool_choice=NONE`. Streamed through `run_llm_step_pkt_generator` and **re-typed on the fly**: `AgentResponseStart/Delta` packets are rewritten to `DeepResearchPlanStart/Delta` so the UI renders the plan in its own surface, while all other packet types (reasoning etc.) pass through. The plan string is threaded into every later prompt.
3. **Research execution** — `for cycle in range(max_orchestrator_cycles)` where the budget is **8 cycles for non-reasoning models, 4 for reasoning models** (`MAX_ORCHESTRATOR_CYCLES` / `_REASONING`), because non-reasoning models burn a cycle on each `think_tool` call. `tool_choice=REQUIRED`, `max_tokens=1024` (the orchestrator only emits tool calls — the cap explicitly guards against "an endless loop of null or bad tokens"), and the orchestrator prompt is re-formatted every cycle with the live `current_cycle_count` / `max_cycles` so the model knows its remaining budget. Three orchestrator tools (`dr_mock_tools.py`) — none of which is a real `Tool` subclass; they are schema dicts interpreted by the loop:
   - `research_agent(task: str)` — spawn a sub-agent on a 1–2 sentence task.
   - `think_tool(reasoning: str)` — for non-reasoning models only.
   - `generate_report()` — terminate.
4. **Report** — `generate_final_report()`: fresh `FINAL_REPORT_PROMPT` system message, `USER_FINAL_REPORT_QUERY.format(research_plan=...)` as a trailing reminder, no tools, `max_tokens=20_000`, `timeout_override=300`. Only **cited** documents are passed as `final_documents` ("the whole list would be too long").

**Sub-agents** — `tools/fake_tools/research_agent.py` (~700 lines). `run_research_agent_calls()` fans out via `run_functions_tuples_in_parallel`; each `run_research_agent_call()` is a nested agent loop up to `MAX_RESEARCH_CYCLES` with the real search tools (`internal_search`, `web_search`, `open_url` — the orchestrator's `allowed_tools` is filtered to exactly these three) plus its own `think_tool`/`generate_report`, and produces an *intermediate report* capped at `MAX_INTERMEDIATE_REPORT_LENGTH_TOKENS = 10_000` ("empirically reports of around 5,000 tokens are pretty good"). Sub-agent output is streamed as `IntermediateReportStart/Delta` with `sub_turn_index` set, so nested work renders without polluting the top-level transcript.

**Layered timeouts** — 30 min hard per sub-agent (`RESEARCH_AGENT_TIMEOUT_SECONDS`), 12 min soft before a sub-agent is forced to write its report (`RESEARCH_AGENT_FORCE_REPORT_SECONDS`), 30 min soft at the orchestrator (`DEEP_RESEARCH_FORCE_REPORT_SECONDS`) checked at the *top* of each cycle. On timeout or last cycle, skip the LLM entirely and go straight to the report — a deep research run **always** produces output.

**The think_tool → reasoning transform** — `create_think_tool_token_processor()` (`deep_research/utils.py`) is a streaming state machine that converts a `think_tool` tool call into reasoning tokens *while it streams*, so non-reasoning models get a reasoning UI for free. It finds `{"reasoning": "` (both spacing variants) in the accumulating argument buffer, strips it, unescapes JSON escapes with a placeholder trick so `\\n` survives correctly, holds back **3 characters** to avoid emitting the closing `"}` or splitting an escape sequence, and drops all other deltas once the think tool is detected. On flush (`delta=None`) it emits the reassembled complete tool call. The think tool is then written into history as a real assistant-tool-call + `THINK_TOOL_RESPONSE_MESSAGE = "Acknowledged, please continue."` pair (10 tokens) and the cycle `continue`s without consuming a research cycle.

**Parallel tool calls in history** — after a fan-out, exactly **one** ASSISTANT message is appended carrying all `ToolCallSimple`s, followed by one `TOOL_CALL_RESPONSE` per call. This is the OpenAI parallel-tool format and is applied uniformly in `dr_loop.py`, `run_llm_loop`, and `create_tool_call_failure_messages`.

**Synthetic `tool_result` on failure** — `dr_loop.py:731`, verbatim comment:

> Every tool_use id in the preceding assistant message must have a matching TOOL_CALL_RESPONSE or strict providers (e.g. AWS Bedrock Converse) reject the next request with 400 "Expected toolResult blocks at messages.N.content for the following Ids: ...". Emit a synthetic failure response so the invariant holds and the LLM knows the call failed.

When `intermediate_reports[tab_index] is None`, it appends `"Research agent call failed. Try a different approach or continue without this result."` bound to that `tool_call_id`. The same invariant is enforced generically by `create_tool_call_failure_messages()` (`chat/chat_utils.py:822`) — used in `run_llm_loop` when *all* tool calls fail, after which the loop `continue`s and lets the model retry. **This is the single highest-value pattern here for Arcon**: the assistant-tool-calls ↔ tool-results pairing is a provider-enforced invariant, and any harness that can drop a result must synthesize one.

**Replay** — I found **no** DR-specific replay engine. `dr_loop.py`'s own TODO says "3. Save the plan for replay" (not done). What exists is generic packet replay for chat history (§3) plus `db/models.py` storing search docs and generated images "for replay." The prior skim's "DR replay" appears to refer to that.

---

## 7. Knowledge graph — what Onyx does that graphify likely won't

`backend/onyx/kg/` targets a **document corpus with typed business entities**, not a codebase. Since Arcon has committed to `graphify`, the useful question is what's differently hard here.

- **Schema-first, not discovery-first.** `kg/models.py` defines `KGEntityTypeDefinition` with `grounding: GROUNDED | UNGROUNDED`, a `grounded_source_name: DocumentSource`, and `KGEntityTypeAttributes` carrying `metadata_attribute_conversion`, `entity_filter_attributes`, and `classification_attributes`. Defaults seeded in `kg/setup/kg_default_entity_definitions.py` (290 lines). Entity types are *declared and admin-tunable*, and extraction is validated against them — unlike a code graph where node types fall out of the AST.
- **Metadata → implied entities/relations.** `KGAttributeImplicationProperty` lets a metadata key mint an entity of an implied type and a named relationship back to the document. `KGAttributeEntityOption.FROM_EMAIL` even infers ACCOUNT-vs-EMPLOYEE from an email domain (`KG_VENDOR_DOMAINS`, `KG_IGNORE_EMAIL_DOMAINS`). Cheap structured extraction with no LLM call.
- **Two-tier extraction.** `kg_implied_extraction()` (metadata/owners, deterministic) vs. `kg_deep_extraction()` / `kg_deep_extract_chunks()` / `kg_classify_document()` (LLM over chunks, gated per entity type by `KGExtractionInstructions.deep_extraction`). Cost control is a first-class schema field.
- **Entity resolution / normalization is a whole module.** `kg/clustering/normalizations.py` does n-gram-based fuzzy matching (`_ngrams`, `_clean_name`, `_normalize_one_entity`) to collapse "Acme Corp" / "ACME, Inc." into one node, producing `NormalizedEntities.entity_normalization_map`. `kg/clustering/clustering.py` then promotes rows from `KGEntityExtractionStaging` into the live graph and builds parent-child relationships. Code graphs mostly get identity for free from FQNs, so this is where the two problems genuinely diverge — but Arcon *will* need the analogous problem for cross-language / cross-repo symbol identity.
- **Staging → normalized → transferred pipeline** with an explicit `KGStage` enum (`NOT_STARTED, EXTRACTING, EXTRACTED, NORMALIZED, FAILED, SKIPPED, DO_NOT_EXTRACT`) and a lock module (`kg/utils/lock_utils.py`). Incremental, resumable, per-document state. Worth stealing conceptually for incremental re-indexing of a working tree.
- **Time-scoped coverage** — `KG_COVERAGE_START`, `KG_MAX_COVERAGE_DAYS`, per-connector `kg_coverage_days`.
- **Storage** is Postgres tables (KG entities/relationships) with an embeddings path (`kg/utils/embeddings.py`) and Vespa interaction (`kg/vespa/vespa_interactions.py`). Runs on its own Celery `kg_processing` worker every 60 s.

**Important caveat: the query side is not implemented in CE.** `tools/tool_implementations/knowledge_graph/knowledge_graph_tool.py` declares a one-parameter `query: str` schema, is gated on `KG_ENABLED and KG_EXPOSED`, and both `emit_start()` and `run()` `raise NotImplementedError`. So I can document extraction/storage from source, but **"how the KG is queried and used to scope context" is not observable in the MIT code** — it presumably lives in EE or was removed. Do not model Arcon's retrieval on this.

---

## 8. MCP server

`backend/onyx/mcp_server/` + `mcp_server_main.py`. Onyx is an MCP **provider** here; it is separately a **consumer** via `tools/tool_implementations/mcp/`.

- **Transport** — FastMCP 3.2 streamable HTTP, mounted at `/` inside a FastAPI wrapper (`create_mcp_fastapi_app()`), port **8090** (`MCP_SERVER_PORT`), off by default (`MCP_SERVER_ENABLED`). No stdio, no OAuth ("may support OAuth and stdio in the future"). A middleware rewrites the `Accept` header to `application/json, text/event-stream` because clients often send `*/*` and FastMCP requires both.
- **Auth** — `OnyxTokenVerifier(TokenVerifier)` takes the bearer token and does an HTTP `GET /me` against the API server on **every request**; on 200 it returns `AccessToken(client_id="mcp", scopes=["mcp:use"])`, else `None`. Stateless, zero DB access in the MCP process, all ACLs enforced by the API server it proxies to. `/health` bypasses auth via middleware.
- **Tool surface** — three tools in `mcp_server/tools/search.py`: `search_indexed_documents(query, source_types, document_set_names, time_cutoff, limit=10)`, `search_web(...)`, `open_urls(...)`. Two resources: `resource://indexed_sources` (which connectors exist) and `resource://document_sets`.
- **Doc-set scoping** — this is the notable design bit. `document_set_names` filters to curated Document Sets, and the docstring says it's "useful for scoping queries to a curated subset of the knowledge base (**e.g. to isolate knowledge between agents**)". The `document_sets` resource exists purely so an agent can *discover* valid scope names before filtering. Resources-as-schema-discovery is the pattern.
- **Honest self-documentation** — the `search_indexed_documents` docstring warns that in CE it routes through the chat endpoint, "which invokes an LLM on every call, consuming tokens and adding latency," and returns a truncated blurb rather than a full chunk; EE uses a dedicated search endpoint. Good practice: tell the model about the tool's cost.
- **Consumer side** — `mcp/mcp_client.py` handles discovery (`discover_mcp_tools`, `discover_mcp_resources_sync`), sync-over-async bridging (`_call_mcp_client_function_sync`), `ExceptionGroup` flattening (`log_exception_group`), and `process_mcp_result(CallToolResult) -> str`. `mcp/mcp_tool.py` wraps each remote tool as an `MCPTool(Tool[None])` with `_normalize_parameters_schema()` to make third-party JSON schemas provider-acceptable, and a distinct `llm_name` vs `name` to namespace collisions.

---

## 9. LLM provider abstraction & model routing

- **One ABC, one impl.** `llm/interfaces.py` defines `LLM` with `invoke()` and `stream()` (both take `prompt, tools, tool_choice, structured_response_format, timeout_override, max_tokens, reasoning_effort, user_identity`) and an `LLMConfig` (provider, model, temperature, api_key/base/version, deployment_name, custom_config, `max_input_tokens`). The only real implementation is `LitellmLLM` in `llm/multi_llm.py` (894 lines) — **LiteLLM is the abstraction**; Onyx's layer exists for quirk-patching, not multi-SDK dispatch.
- **Auto-instrumentation via `__init_subclass__`.** Every `LLM` subclass gets `invoke`/`stream` wrapped with `wrap_invoke`/`wrap_stream` (`llm/tracing_wrap.py`) at class-creation time, and `_wrap_method_if_defined` skips inherited methods to avoid double-wrapping. No LLM call anywhere can escape tracing. **Directly stealable by Arcon** for its provider base class.
- **Provider quirks are explicit, not hidden.** `_strip_tool_content_from_messages`, `_fix_tool_user_message_ordering`, `_messages_contain_tool_content`, `_is_vertex_model_rejecting_output_config`, `_anthropic_uses_adaptive_thinking`, plus `is_ollama` / `is_claude_model` / `is_mistral` branches around parameter passing (one branch cites `ollama/ollama#11171`). Ollama also gets a dedicated **history formatter** (`_OllamaHistoryMessageFormatter`, `chat/llm_step.py:727`) that flattens tool calls into plain text — `[Tool Call] name=… id=… args={…}` on the assistant side and `[Tool Result] id=…\n…` as a *user* message — because Ollama's structured tool history is unreliable. Given Arcon's Ollama-first local-LLM goal, **this file is the single most directly relevant thing in the repo.**
- **Model routing: essentially none.** `llm/factory.py` has `get_llm_for_persona`, `get_default_llm`, `get_default_llm_with_vision`, `get_llm_for_contextual_rag`. Selection is *configuration* resolution — `LLMOverride(model_provider, model_version, temperature, display_name)` from the request, else persona override, else tenant default — plus an access check (`can_user_access_llm_provider`) that falls back to the default provider if denied. There is **no cost-, latency-, or difficulty-based router.** The only capability-driven routing is by *task*: a separate vision LLM, a separate contextual-RAG LLM, and behavioral branching on `model_is_reasoning_model()` (cycle budgets, prompt variants, think-tool inclusion). Arcon's router would be new work; Onyx offers no design to copy, only `model_name_parser.py` (`parse_litellm_model_name` → `ParsedModelName`, vendor/region inference, display-name generation) and a 120 KB `model_metadata_enrichments.json` as capability metadata.
- **Token counting** — `natural_language_processing/utils.get_tokenizer()` with an explicit fallback tokenizer when the model's is unknown (`chat/README.md` flags this as approximate); `llm/factory.get_llm_token_counter(llm) -> Callable[[str], int]` is passed down as `token_counter` everywhere. Token counts are computed **once at message-creation time** and persisted on `ChatMessage.token_count`, so budgeting is pure arithmetic on stored ints. Images get an assumed constant. `Usage` (`llm/model_response.py`) parses `prompt_tokens`, `completion_tokens`, `total_tokens`, `cache_creation_input_tokens`, `cache_read_input_tokens`.
- **Cost** — `llm/cost.calculate_llm_cost_cents(model, prompt_tokens, completion_tokens)` wraps `litellm.cost_per_token`, converts to cents, and **returns 0.0 on any error** ("unknown models or errors shouldn't block usage"). `LitellmLLM._track_llm_cost()` fires after every call but only persists when usage limits are enabled *and* the key is an Onyx-managed key, via `increment_usage(db, UsageType.LLM_COST, cents)`. Cost also lands in the Braintrust/Langfuse spans.
- **Prompt caching** — `llm/prompt_cache/` (`CacheManager`, `generate_cache_key_hash`, `prepare_messages_with_cacheable_transform`, `process_with_prompt_cache`) with metadata in a Postgres/Redis KV store. `construct_message_history` sets `should_cache = True` on the system prompt and on surviving older history so a stable prefix is marked cacheable.

---

## 10. Observability & telemetry

- **Custom span framework** — `onyx/tracing/framework/` (`create.py`, `spans.py`, `traces.py`, `scope.py`, `span_data.py`, `provider.py`, `processor_interface.py`, `_error_tracing.py`). Primitives: `trace(name, group_id=..., metadata=...)`, `ensure_trace(...)`, `function_span(name)` with mutable `span.span_data.input/output`, and `attach_error_to_current_span(SpanError(message, data))`. `group_id` is the chat session, so a whole conversation is one trace group. Usage is dense and deliberate: `run_llm_loop`, `run_deep_research_llm_loop`, `clarification_step`, `research_plan_step`, `research_execution_step`, `think_tool`, `generate_report`, `generate_intermediate_report`, `chat_history_compression`, and every individual tool run.
- **Pluggable backends** — `tracing/setup.py` wires `_setup_braintrust()` and/or `_setup_langfuse()` behind a `processor_interface`, plus `tracing/masking.py` for PII redaction. `tracing/llm_utils.py` provides `llm_generation_span(llm, flow, input_messages)`, `record_llm_response`, `record_llm_span_output`, and `_build_usage_dict` — so every generation span carries model config, `flow` label, and full token usage; the tracing processors compute cost per span.
- **Prometheus** — `server/metrics/` has ~14 collector modules registered by `setup_prometheus_metrics(app)` (`main.py:685`) plus a standalone `metrics_server.py` for Celery workers. `embedding.py` is the recent work referenced in the brief: `onyx_embedding_client_duration_seconds` (Histogram), `onyx_embedding_requests_total` (Counter, labeled by outcome), `onyx_embedding_texts_total`, `onyx_embedding_input_chars_total`. Others cover celery tasks, indexing pipeline, connector health, permission sync, pruning, deletion, OpenSearch search latency, Postgres pool, slow requests, and per-tenant labels. **Note: I found no Prometheus metric for LLM tokens or cost** — LLM economics live in span metadata and the `TenantUsage` table, not in Prometheus.
- **Product telemetry** — `utils/telemetry.py`: `optional_telemetry(RecordType, ...)` (opt-out anonymous usage), `mt_cloud_telemetry` / `mt_cloud_identify` / `mt_cloud_alias` for cloud milestones.
- **Timing** — `@log_function_time(print_only=True)` on `run_deep_research_llm_loop`; `pre_answer_processing_time` (monotonic clock from loop start to first answer token) is threaded through `run_llm_step` and persisted on the message. A real user-facing latency SLI baked into the data model.

---

## 11. What Arcon should adopt

Scale reality check: Onyx is a multi-tenant server platform (Postgres + Vespa/OpenSearch + Redis + 9 Celery workers) reasoning over a *document corpus*. Arcon is a local-first CLI+UI over SQLite reasoning over a *codebase*. Nothing infrastructural transfers. What transfers is loop, context, and tool-protocol engineering — which is exactly where Onyx is strong.

Priority order, mapped to Arcon's real tree (`src/arcon/{core,tools,providers,agents,storage,cli,skills}`):

| # | Item | Onyx source | Arcon target | Type | Effort |
|---|---|---|---|---|---|
| 1 | **Read `chat/README.md` + `COMPRESSION.md` end to end** before touching the loop. The empirical claims (reminder-at-the-end, section-locality raising instruction-following ~30%→~90%, custom prompt as a *moving user message* not a system prompt) are free calibration. | `chat/README.md` | design input | learn | 1 h |
| 2 | **Synthetic tool_result invariant.** Every emitted assistant tool-call id must get a matching tool result, even on crash/timeout/cancel — else strict providers 400. | `dr_loop.py:731`, `chat_utils.py:822` | `tools/executor.py` + `core/session.py` | direct port | 0.5 d |
| 3 | **`Tool[TOverride]` + two-channel `ToolResponse`.** Split model-supplied `**llm_kwargs` from harness-injected typed `override_kwargs`; return `llm_facing_response` (string for the model) *and* `rich_response` (typed, for UI/DB). Arcon's `tools/base.py` almost certainly conflates these today. | `tools/interface.py`, `tools/models.py` | `tools/base.py`, `tools/registry.py` | pattern (adapt) | 1–2 d |
| 4 | **Per-tool exception containment.** `_safe_run_single_tool`: catch expected vs. unexpected separately, always convert to an LLM-readable error string, always emit the terminator, never break the loop. | `tool_runner.py:108` | `tools/executor.py` | direct port | 0.5 d |
| 5 | **Ollama-specific history flattening.** Text-encode tool calls/results as `[Tool Call] …` / `[Tool Result] …` for Ollama, plus `_drop_orphaned_tool_call_responses()`. Arcon has `providers/ollama.py` and local LLMs are a headline feature — this is battle-tested work you'd otherwise rediscover painfully. | `llm_step.py:727`, `llm_loop.py:526` | `providers/ollama.py` | direct port | 1 d |
| 6 | **XML/text tool-call fallback extraction, attempted once per turn.** Weak local models emit tool calls in the content channel; recover them instead of failing, but bound the retries. | `llm_step.py:396–560`, `llm_loop.py:148` | `providers/base.py` | pattern | 1–2 d |
| 7 | **Cycle-budget-aware prompting + terminal cycle.** `MAX_LLM_CYCLES`, inject `current_cycle/max_cycles` into the prompt each iteration, and on the last cycle force `tool_choice=NONE` with an empty tool list so a final answer is guaranteed. | `llm_loop.py:622`, `dr_loop.py:432` | `core/session.py` | direct port | 0.5 d |
| 8 | **`Placement`-tagged typed packet stream** (`turn_index`/`tab_index`/`sub_turn_index`/`model_index`) with `Emitter` → shared queue, and *replay* of stored turns as the same packets. This is how you get one event model serving both the CLI renderer and the future UI, plus `--resume`. | `streaming_models.py`, `placement.py`, `emitter.py`, `chat_backend.py:348` | `core/interface.py`, `cli/chat.py` | pattern (high leverage) | 3–5 d |
| 9 | **Auto-wrap providers via `__init_subclass__`** so no LLM call can escape tracing/token accounting. | `llm/interfaces.py:50` | `providers/base.py` | direct port | 0.5 d |
| 10 | **Persist `token_count` per message at write time**; budget by summing stored ints, never re-tokenize. Foundation for Arcon's token economics. Add `Usage` capture incl. `cache_read_input_tokens` / `cache_creation_input_tokens`. | `compression.py:64`, `model_response.py` | `storage/models.py`, `storage/sqlite.py` | direct port | 1 d |
| 11 | **`function_span` + `group_id`-scoped traces**, with a pluggable processor. Even a local JSONL processor gives per-turn/per-tool/per-subagent cost and latency attribution — precisely Arcon's token-economics feature. | `tracing/framework/`, `tracing/llm_utils.py` | new `arcon/tracing/` | pattern | 2–3 d |
| 12 | **Progressive summarization with a cutoff marker.** Trigger at 0.75 of available budget, keep ~20% verbatim, **align the cutoff to a user-message boundary**, feed the prior summary back in, compact tool calls to `[Used tools: …]`. Arcon has no compression at all. Use a linear session (skip the branch tree) unless Arcon adds conversation forking. | `compression.py`, `COMPRESSION.md` | new `core/compression.py` | pattern (simplify) | 2–3 d |
| 13 | **Tool-call merging** — port the *mechanism* (allowlist `{tool_name: list_field}`, group, concat, first-call-wins) but re-target the allowlist to code tools: `read_file{paths}`, `grep{patterns}`, `glob{globs}`. Add the de-duplication Onyx lacks. Cheap, real token savings. | `tool_runner.py:53` | `tools/executor.py` | direct port + improve | 0.5 d |
| 14 | **Disjoint id-range allocation for parallel tools** (Onyx: `+= 100` citation slots per call) — the same trick works for Arcon's diff/hunk or artifact ids under parallel execution, no locks needed. | `tool_runner.py:310` | `tools/executor.py` | pattern | 0.25 d |
| 15 | **Deep-research architecture as Arcon's "deep mode" / subagent spawner:** clarify (no-tool-call *is* the question) → plan → bounded orchestrator cycles with only `spawn_subagent` / `think` / `finish` → parallel sub-agents with restricted toolsets → bounded-length intermediate reports → forced synthesis. Plus layered soft/hard timeouts so a run *always* produces output. Maps directly onto Arcon's `agents/` YAML agents. | `deep_research/`, `fake_tools/research_agent.py` | `agents/`, new `core/deep_mode.py` | pattern (flagship) | 1–2 wk |
| 16 | **Orchestrator tools as plain schema dicts** interpreted by the loop rather than registered `Tool`s, and `check_special_tool_calls()` to detect control-flow tools. Keeps control flow (`think`, `finish`, `spawn`) out of the real tool registry. | `dr_mock_tools.py`, `deep_research/utils.py:...` | `core/deep_mode.py` | pattern | 0.5 d |
| 17 | **`think_tool` → streaming reasoning transform** for models with no native reasoning channel. Non-trivial correctness work already solved (escape handling, 3-char holdback). Worth it for Ollama parity with Claude/GPT reasoning UX. | `deep_research/utils.py` | `providers/base.py` | direct port | 1 d |
| 18 | **`max_tokens` cap on planning/orchestration steps** (Onyx: 1024) to kill runaway degenerate generation from weak models. | `dr_loop.py:532` | `core/session.py` | direct port | 0.1 d |
| 19 | **LLM-mediated memory add-vs-update.** Second LLM call returns `(memory_text, index_to_replace)`; the *loop*, not the tool, persists. Prevents an ever-growing memory file. | `memory/memory_tool.py` | new `tools/memory.py` | pattern | 1 d |
| 20 | **Graceful truncation with a recovery handle.** When history eviction drops a file, inject a compact metadata stub so the model can `read_file(file_id)` again. In Arcon: evict large file contents but leave `path + line-range + digest` so it can re-read. | `llm_loop.py:401–470` | `core/compression.py` | pattern | 1 d |
| 21 | **MCP server: FastMCP + streamable HTTP + `TokenVerifier`, resources-as-schema-discovery, and "declare the tool's cost in its docstring."** Arcon's analogue of Document-Set scoping is *repo/path scoping* — expose a `resource://repos` so a remote agent can discover valid scopes. | `mcp_server/` | new `arcon/mcp_server/` | pattern | 3–5 d |
| 22 | **MCP consumption:** `_normalize_parameters_schema`, `llm_name` vs `name` namespacing, `ExceptionGroup` flattening, sync-over-async bridge. Saves real debugging. | `tool_implementations/mcp/` | new `tools/mcp_client.py` | direct port | 2–3 d |
| 23 | Behavioral flags on the tool registry (`STOPPING_TOOLS_NAMES`, `CITEABLE_TOOLS_NAMES`) driving loop policy. Arcon analogue: "mutating tools" (force a confirm/summarize cycle), "expensive tools". | `built_in_tools.py` | `tools/registry.py` | pattern | 0.25 d |
| 24 | `model_name_parser.py` + model-capability metadata JSON as the **input table** to Arcon's model router (context window, vision, reasoning, cost). Onyx has the data, not the router. | `llm/model_name_parser.py`, `model_metadata_enrichments.json` | `providers/resolver.py` | pattern (data only) | 0.5 d |
| — | KG extraction/normalization/clustering pipeline | `kg/` | — | **inapplicable** (using graphify); borrow only the `KGStage` staging-state idea for incremental indexing | — |

---

## 12. What Arcon should NOT copy

1. **Every service dependency.** Postgres/SQLAlchemy/Alembic, Redis, Vespa/OpenSearch, Celery's nine worker classes, Kubernetes/Helm deployment. Arcon is SQLite + a local process. Onyx's own `chat/README.md` complexity around branch trees and `parent_message_id` chains exists to serve a multi-user web app.
2. **Multi-tenancy.** `get_current_tenant_id()`, `shared_configs.contextvars`, `DynamicTenantScheduler`, per-tenant metric labels, `TenantUsage` — all threaded deep into the code. Strip it entirely; keep only the *shape* (a `session_id` group key for tracing).
3. **DB-backed tool registration.** `Tool.id` is an `int` FK into a Postgres `tool` table (`_get_research_agent_tool_id()` opens a session mid-loop just to look up an id, in the hot path of every DR cycle). Arcon should key tools by name/string.
4. **Compression's branch-aware summary tree.** `parent_message_id` + `last_summarized_message_id` + `find_summary_for_branch` scanning all summaries exists purely because the web UI supports message-edit branching. Unless Arcon ships conversation forking, use a single linear summary pointer — you get the progressive-summarization benefit for a fraction of the complexity.
5. **Citation machinery.** `DynamicCitationProcessor`, `CitationMode.HYPERLINK`, `collapse_citations`, the `{"documents": [{"document": 1, ...}]}` JSON envelope, the always-on citation reminder, the `+= 100` citation-range logic — all of it presupposes a retrieval corpus with per-document provenance. A coding agent cites `path:line`, which needs none of this. (Borrow only the disjoint-range allocation trick, item 14.)
6. **Document-corpus retrieval assumptions.** RRF fusion (`weighted_reciprocal_rank_fusion`), chunk merging (`merge_overlapping_sections`, `merge_individual_chunks`), query expansion, contextual-RAG enrichment, embedding-model management. Code retrieval is structural (AST/graph/grep), not chunk-and-embed; adopting this would be actively wrong.
7. **The `search_indexed_documents` CE implementation.** By its own docstring it routes through the chat endpoint and invokes an LLM per call. An LLM call inside a search tool is a latency and cost trap; don't replicate.
8. **The KG module as a port target.** Beyond the graphify decision: the query side literally `raise NotImplementedError` in the MIT code, and the entity model (ACCOUNT/EMPLOYEE, email-domain inference, `KG_COVERAGE_START` date windows) is business-CRM-shaped, not code-shaped.
9. **`llm/multi_llm.py`'s size, not its content.** 894 lines of provider quirk-patching is what happens when quirks accumulate un-refactored. Take the *specific* quirk fixes (§9, items 5/6/17) but keep them in per-provider adapter modules under `providers/`, not in one god-file.
10. **Braintrust/Langfuse as required infrastructure.** Adopt the span *framework* and its processor interface; ship a local JSONL/SQLite processor as the default. A local-first CLI must not need a SaaS observability account to report token spend.
11. **Onyx's absent model router.** Do not assume there's a routing design here to lift — there isn't (§9). Arcon's router is greenfield; Onyx contributes capability *data* and task-specialized-LLM *slots*, nothing more.
