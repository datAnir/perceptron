# deepagents — Architecture Analysis for Arcon

Source analyzed: `/home/anirband/perceptron/deepagents` (github.com/langchain-ai/deepagents), package version **0.7.13**.
Scope note: the `libs/talon` messaging-bot feature was explicitly skipped per instruction.

---

## 1. Overview

| Property | Value |
|---|---|
| Package location | `/home/anirband/perceptron/deepagents/libs/deepagents/` (import root `deepagents/`) |
| Maintainer | LangChain (langchain-ai) |
| License | MIT (`pyproject.toml`: `license = { text = "MIT" }`) |
| Version / maturity | `0.7.13`, classifier `Development Status :: 4 - Beta`; public API stable-ish, `deepagents.profiles` explicitly marked beta, forked subagents emit `warn_beta` |
| Python | `>=3.11,<4.0` |
| Hard deps | `langchain>=1.4`, `langchain-core>=1.6.1`, `langchain-anthropic`, `langchain-google-genai`, `langsmith`, `packaging`, `wcmatch` |
| Total size | ~27.5k LOC across the package (excluding tests) |

deepagents self-describes as "the batteries-included agent harness." Its own README states the layering precisely: **LangGraph is the graph runtime; LangChain's `create_agent` is a minimal agent harness on top of it; deepagents is a more opinionated harness on top of `create_agent`.** deepagents does *not* implement its own agent loop — `create_deep_agent()` is fundamentally a large, careful *middleware-stack assembler* that ends in a single call to `langchain.agents.create_agent(...)`.

Other monorepo libs (not analyzed in depth): `libs/code` (Deep Agents Code — a shipped Claude-Code-like terminal agent), `libs/acp`, `libs/evals`, `libs/talon` (skipped).

Significant directory tree:

```
libs/deepagents/deepagents/
├── graph.py                     978  create_deep_agent() — stack assembly
├── _models.py                   211  resolve_model(), provider/identifier extraction
├── _excluded_middleware.py      225  profile-driven middleware filtering + validation
├── _messages_reducer.py          90  DeltaChannel reducer for messages
├── middleware/
│   ├── filesystem.py           3577  file tools, permissions, tool-result eviction
│   ├── summarization.py        2167  compaction, arg truncation, media offload
│   ├── rubric.py               1438  self-grading against a rubric
│   ├── skills.py               1058  SKILL.md discovery + prompt injection
│   ├── subagents.py             988  `task` tool, isolated + forked subagents
│   ├── async_subagents.py       931  background/remote subagents
│   ├── memory.py                417  AGENTS.md loading
│   ├── _overflow_clip.py        206  ContextOverflowError tail clipping
│   ├── _fs_interrupt.py         183  permissions → HITL `interrupt_on` bridge
│   ├── _message_eviction.py     162
│   ├── _tool_exclusion.py       101
│   ├── _prompt_caching.py        49  Anthropic/Bedrock/Fireworks cache middleware
│   ├── patch_tool_calls.py       49  repair dangling tool calls
│   └── permissions.py             5  ← re-export shim only
├── backends/
│   ├── sandbox.py              1989  BaseSandbox: file ops via remote `execute`
│   ├── filesystem.py           1576  FilesystemBackend (real local disk)
│   ├── utils.py                1067  path validation, glob anchors, overlap
│   ├── composite.py            1019  CompositeBackend (prefix routing)
│   ├── protocol.py              984  BackendProtocol / SandboxBackendProtocol
│   ├── store.py                 719  StoreBackend (LangGraph BaseStore)
│   ├── context_hub.py           713  ContextHubBackend (LangSmith Hub repo)
│   ├── state.py                 374  StateBackend (in-graph-state files, default)
│   ├── langsmith.py             353  LangSmithSandbox
│   └── local_shell.py           366  LocalShellBackend (host shell, no isolation)
└── profiles/
    ├── harness/harness_profiles.py  1325  HarnessProfile, registry, selection
    ├── harness/_nvidia_nemotron_3_ultra.py 1826  (largest built-in profile)
    ├── harness/_openai_codex.py, _anthropic_{opus_4_7,sonnet_4_6,haiku_4_5}.py
    ├── provider/provider_profiles.py 455  ProviderProfile
    └── provider/_openai.py, _openrouter.py, _nvidia.py
```

---

## 2. Core architecture

**Assembly, not a loop.** `create_deep_agent()` in `deepagents/graph.py` accepts `model, tools, system_prompt, middleware, subagents, skills, memory, permissions, backend, interrupt_on, response_format, state_schema, context_schema, checkpointer, store, ...` and returns a `CompiledStateGraph`. The loop itself (model call → tool node → repeat) is LangChain/LangGraph's; deepagents contributes the stack.

Documented base ordering (from the `middleware` docstring, verified against code at `graph.py:862-938`):

1. `SkillsMiddleware` (only if `skills=`)
2. `FilesystemMiddleware` — **required scaffolding**
3. `SubAgentMiddleware` — **required scaffolding**
4. `SummarizationMiddleware` (via `create_summarization_middleware(model, backend)`)
5. `PatchToolCallsMiddleware`
6. `AsyncSubAgentMiddleware` (if async subagents)
7. *— user middleware spliced in here —*
8. Tail: profile `extra_middleware` → `_ToolExclusionMiddleware` → prompt-caching middlewares → `MemoryMiddleware` → `HumanInTheLoopMiddleware`

**State model.** `DeepAgentState(AgentState)` overrides only `messages`:

```python
class DeepAgentState(AgentState):
    """AgentState with `DeltaChannel` on messages to reduce checkpoint growth from O(N²) to O(N)."""
    messages: Required[Annotated[list[AnyMessage], DeltaChannel(_messages_delta_reducer, snapshot_frequency=50)]]
```

Middleware contribute *additional* state via a class-level `state_schema` TypedDict; `graph.py` collects `mw.state_schema` from every middleware and computes `private_state_field_names(*state_schemas)` — fields annotated `PrivateStateAttr` are stripped from subagent inputs/outputs.

**Planning/todo.** Notable negative finding: **deepagents ships no planning/todo middleware of its own.** The only `write_todos` tool comes from LangChain's `TodoListMiddleware`, registered by exactly one profile (`profiles/harness/_openai_codex.py:77`), because the Codex system prompt references reconciling TODOs. `"todos"` otherwise appears only in `subagents.py`'s `_EXCLUDED_STATE_KEYS`. Planning is treated as a per-model prompt concern, not core harness machinery.

**Filesystem abstraction.** Two layers: `BackendProtocol` (storage/exec) and `FilesystemMiddleware` (the model-facing tools `ls, read_file, write_file, edit_file, glob, grep, delete, execute`). Permissions, line-number gutters, and eviction all live in the middleware, *not* the backend — the docstring is explicit: "Direct backend usage does not currently incorporate `permissions`."

**Subagents** are a tool, not a graph edge: `SubAgentMiddleware` injects one `task(description, subagent_type)` tool that `invoke()`s a fully separate compiled graph.

---

## 3. The middleware system — deep dive

### 3.1 Base class and hooks

The base class `AgentMiddleware[StateT, ContextT, ResponseT]` lives **upstream** in `langchain.agents.middleware.types`, not in deepagents (langchain is not vendored here, so hook names below are enumerated from actual overrides across this repo rather than from the base class source — this is exhaustive for deepagents' usage but langchain may define more).

Hooks actually implemented in deepagents, with real signatures:

| Hook | Sync/async pair | Purpose | Example |
|---|---|---|---|
| `before_agent(self, state, runtime)` | `abefore_agent` | once per graph invocation, before any model call; returns a state-update dict | `PatchToolCallsMiddleware`, `SkillsMiddleware`, `MemoryMiddleware`, `RubricMiddleware` |
| `after_agent(...)` | — | once after the run completes | `RubricMiddleware`, nemotron profile |
| `before_model(self, state, runtime)` | `abefore_model` | per model step | nemotron profile only |
| `wrap_model_call(request, handler)` | `awrap_model_call` | **the workhorse** — full interception of each LLM request | filesystem, summarization, subagents, memory, skills, tool-exclusion |
| `wrap_tool_call(request, handler)` | `awrap_tool_call` | wraps each tool execution | filesystem (eviction), tool-exclusion, nemotron |

`wrap_*` hooks are **onion/decorator style**, not pre/post callbacks:

```python
def wrap_model_call(
    self,
    request: ModelRequest[ContextT],
    handler: Callable[[ModelRequest[ContextT]], ModelResponse[ResponseT]],
) -> ModelResponse[ResponseT]:
    request = request.override(system_message=new_system_message)
    return handler(request)
```

Composition semantics that follow from this shape:
- **Ordering** = nesting order. Earlier middleware in the list wraps outermost, so its `wrap_model_call` sees the request first and the response last.
- **Short-circuit** = simply not calling `handler`. `_ToolExclusionMiddleware.wrap_tool_call` returns an error `ToolMessage` without invoking the handler; `SummarizationMiddleware` catches `ContextOverflowError` from `handler(...)`, compacts, and **re-invokes** `handler` — retry is expressed naturally in this shape.
- `request.override(...)` returns a *new* request; middleware never mutate shared state in place.
- State flows two ways: read-only via `state`/`runtime.state`, written by returning update dicts from `before_*`/`after_*`, or via `Command(update={...})` from tools.

### 3.2 Stack assembly and profile-driven filtering

Three helpers in `graph.py` implement merge semantics:

- `_apply_custom_middleware(base, custom, *, core_names)` — a custom middleware whose `.name` matches an existing entry **replaces it in place** (preserving order); otherwise it's inserted right after the last core member, ahead of the tail.
- `_apply_excluded_middleware(...)` / `_validate_excluded_middleware_config(...)` / `_verify_excluded_middleware_coverage(...)` (in `_excluded_middleware.py`) — profiles may drop middleware by class or by `.name`. An exclusion matching *nothing* raises `ValueError` (catches typos/stale profiles).
- `_REQUIRED_MIDDLEWARE = ((FilesystemMiddleware, ()), (SubAgentMiddleware, ()))` — protected scaffolding; excluding either raises rather than silently degrading. `FilesystemMiddleware` is protected specifically because it enforces `permissions` (a security guarantee).

### 3.3 Shipped middleware catalog

| Middleware | File | Hooks | What it does |
|---|---|---|---|
| `FilesystemMiddleware` | `middleware/filesystem.py` | `wrap_model_call`, `wrap_tool_call`/`awrap_tool_call` | Registers all file tools; drops `execute` at call time when the backend isn't a sandbox; **enforces permission deny rules**; evicts oversized tool results to disk (§8) |
| `SummarizationMiddleware` (`_DeepAgentsSummarizationMiddleware`) | `middleware/summarization.py` | `wrap_model_call` | Compaction, tool-arg truncation, inline-media offload, `ContextOverflowError` retry (§8) |
| `SummarizationToolMiddleware` | same | tool only | Exposes a `compact_conversation` tool with an eligibility gate at ~50% of the auto trigger |
| `SubAgentMiddleware` | `middleware/subagents.py` | `wrap_model_call` | Injects `task` tool; appends available-agent list to system prompt (§5) |
| `AsyncSubAgentMiddleware` | `middleware/async_subagents.py` | `wrap_model_call` | Background/remote subagents via LangSmith deployments; tools to launch/check/update/cancel/list |
| `SkillsMiddleware` | `middleware/skills.py` | `before_agent`, `wrap_model_call` | Discovers `SKILL.md` files with YAML frontmatter under given source paths, injects a skill index into the system prompt. Caps: 10 MB/file, name ≤64, description ≤1024 chars |
| `MemoryMiddleware` | `middleware/memory.py` | `before_agent`, `wrap_model_call` | Loads `AGENTS.md` files at startup into the system prompt; sets an Anthropic `cache_control` breakpoint |
| `PatchToolCallsMiddleware` | `middleware/patch_tool_calls.py` | `before_agent` | Synthesizes `ToolMessage`s for dangling/invalid tool calls so history is well-formed after an interruption. Rewrites via `RemoveMessage(id=REMOVE_ALL_MESSAGES)` |
| `RubricMiddleware` | `middleware/rubric.py` | `before_agent`, `after_agent` | LLM-graded self-evaluation against pass/fail criteria |
| `_ToolExclusionMiddleware` | `middleware/_tool_exclusion.py` | `wrap_model_call`, `wrap_tool_call` | Filters profile-`excluded_tools` from the tool list *and* blocks execution — appended last so a custom `wrap_model_call` can't restore them |
| Prompt caching | `middleware/_prompt_caching.py` | (upstream) | `append_prompt_caching_middleware()` unconditionally adds `AnthropicPromptCachingMiddleware(unsupported_model_behavior="ignore")`, plus Bedrock/Fireworks equivalents if those packages are installed |
| `HumanInTheLoopMiddleware` | upstream langchain | interrupt | Approval gate; wired from permissions (§4) |

---

## 4. The permission system

**`middleware/permissions.py` is a 5-line backward-compat re-export.** The real implementation is in `middleware/filesystem.py` + `middleware/_fs_interrupt.py`.

```python
@dataclass
class FilesystemPermission:
    operations: list[FilesystemOperation]          # "read" | "write"
    paths: list[str]                                # POSIX glob patterns, must start with "/"
    mode: Literal["allow", "deny", "interrupt"] = "allow"
```

`__post_init__` rejects patterns not starting with `/`, containing `..` (ValueError), or containing `~` (NotImplementedError).

**Evaluation** — first match wins, default allow:

```python
def _check_fs_permission(rules, operation, path) -> Literal["allow", "deny", "interrupt"]:
    for rule in rules:
        if operation not in rule.operations:
            continue
        if any(wcglob.globmatch(path, pattern, flags=_FS_WCMATCH_FLAGS) for pattern in rule.paths):
            return rule.mode
    return "allow"
```

**Enforcement is split by mode:**

- **deny** — enforced *inside each tool*, pre-execution. `read_file`/`write_file`/`edit_file` return `Error: permission denied for write on {path} (matches deny rule(s): ...)`. Bulk tools instead *filter results*: `_apply_permissions_to_ls_results`, `_apply_permissions_to_glob_results`, `_filter_paths_by_permission` drop denied entries so denied paths aren't even disclosed.
- **interrupt** — deepagents' HITL. `FilesystemMiddleware` deliberately knows nothing about HITL; `graph.py` calls `_build_interrupt_on_from_permissions(rules)` which synthesizes an `interrupt_on` map, merged with the user's `interrupt_on` (user wins per tool name) by `_merge_fs_interrupt_on`, and installs `HumanInTheLoopMiddleware`.

**Argument-level granularity** is the sophisticated part. `_FS_TOOL_PATH_ARGS` maps each tool to `(operation, path-arg-name, scope, pattern-arg-name)` with `ToolScope = "exact" | "bulk"`, and a `when: Callable[[ToolCallRequest], bool]` predicate inspects the *actual argument values*:

```python
_FS_TOOL_PATH_ARGS = {
    "ls":         ("read",  "path",      "bulk",  None),
    "read_file":  ("read",  "file_path", "exact", None),
    "write_file": ("write", "file_path", "exact", None),
    "edit_file":  ("write", "file_path", "exact", None),
    "delete":     ("write", "file_path", "bulk",  None),
    "glob":       ("read",  "path",      "bulk",  "pattern"),
    "grep":       ("read",  "path",      "bulk",  None),
}
```

Bypass defenses worth stealing: `grep(path=None)` fires unconditionally (a pathless bulk call can touch anything); `path="."`/`""`/`"./"` normalizes to `/.` and is collapsed to `/` so it can't evade overlap checks; `glob`'s `pattern` is gated independently because an absolute pattern redirects the search root; relative patterns containing `..` fire unconditionally. Recursive `delete` gets a dedicated subtree-overlap analysis (`_find_delete_deny_patterns`, `_wildcard_delete_overlap`) that fails **closed** for directory-wildcard patterns.

Approver decision set is `["approve", "edit", "reject", "respond"]`; an `edit`ed call re-enters the tool and still hits the pre-execution deny check, so the human never becomes an authorization bypass.

**Persistence:** decisions are *not* persisted as a policy cache. There is no "always allow this" learning. Durability comes only from LangGraph checkpointing of the interrupted graph; rules themselves are static config passed to `create_deep_agent(permissions=[...])`.

---

## 5. Subagent spawning (highest-priority for Arcon)

Three spec forms, discriminated structurally in `graph.py`:

| Form | Detection | Runs via |
|---|---|---|
| `SubAgent` (TypedDict) | default | compiled by `create_sub_agent()` → `create_agent()` |
| `CompiledSubAgent` | `"runnable" in spec` | caller's pre-built runnable |
| `AsyncSubAgent` | `"graph_id" in spec` | `AsyncSubAgentMiddleware`, background/remote |

`SubAgent` fields: `name`, `description` (required); `system_prompt`, `mode`, `tools`, `model`, `middleware`, `interrupt_on`, `skills`, `permissions`, `response_format` (optional).

**Each subagent gets its own middleware stack**, built in `graph.py:689-703` — a full `FilesystemMiddleware` (with resolved permissions), its own `create_summarization_middleware(subagent_model, backend)`, and `PatchToolCallsMiddleware`. Because the model can differ per subagent, `_harness_profile_for_model` is re-run per subagent so a Haiku subagent gets Haiku's profile under an Opus parent. Permissions resolve as `spec.get("permissions", permissions)` — a subagent's own rules **replace** the parent's entirely, never merge.

**Context isolation** is the core mechanism, in `_validate_and_prepare_state`:

```python
subagent_state = {k: v for k, v in runtime.state.items()
                  if k not in _EXCLUDED_STATE_KEYS | private_state_keys}
subagent_state["messages"] = [HumanMessage(content=description)]
```

`_EXCLUDED_STATE_KEYS = {"messages", "todos", "structured_response", _FORKED_CONTEXT_KEY}`. So an isolated subagent inherits **shared non-private state (crucially the virtual filesystem) but a completely fresh single-message conversation.** That is the token-isolation win: the parent's 100k-token history costs the subagent nothing, and files are the shared channel.

**`mode="fork"`** (experimental, `warn_beta`) is the opposite trade: `_fork_messages()` replays the parent's *effective* (post-summarization) history plus a `_FORK_TASK_PREAMBLE`, pops a trailing tool-calling `AIMessage`, and inherits private channels so the fork's own middleware rebuilds the same system prompt. Forks are marked with `_FORKED_CONTEXT_KEY` and `task`/`atask` return `_FORK_RECURSION_REFUSAL` if a fork tries to delegate again — preventing unbounded recursion. Forks may not define `skills`.

**What returns to the parent** — `_return_command_with_state_update`:

```python
return Command(update={**state_update, "messages": [ToolMessage(content, tool_call_id=tool_call_id)]})
```

Content is `structured_response` JSON-serialized if present (handles pydantic `model_dump_json`, dataclasses, plain), else it **walks backwards to the last `AIMessage` with non-empty text** (defensive against Anthropic's trailing empty `end_turn` message). Only that one string crosses back — intermediate tool calls never enter the parent's context. The subagent's non-excluded state updates *do* merge back.

**Parallel dispatch** is not implemented by deepagents. It's delegated to the model: the `task` tool description says "Launch multiple agents concurrently when their tasks are independent, using a single message with multiple tool calls," and LangGraph's tool node executes that batch. `atask` provides the async path. Per-invocation summarization session IDs are scoped "so parallel sub-agents do not share one history file."

---

## 6. Execution backends

`BackendProtocol` (ABC, `backends/protocol.py`) defines file ops with a **sync + `a`-prefixed async pair each**, where the async default is `asyncio.to_thread(self.<sync>, ...)`:

`ls/als`, `read/aread`, `grep/agrep`, `glob/aglob`, `write/awrite`, `edit/aedit`, `delete/adelete`, `upload_files/aupload_files`, `download_files/adownload_files`.

Every method returns a **typed result dataclass carrying `error: str | None` rather than raising** — `ReadResult, WriteResult, EditResult, DeleteResult, LsResult, GrepResult, GlobResult` — plus `FileInfo`/`GrepMatch`/`FileData` TypedDicts. `ReadResult.__post_init__` aggressively validates pagination coherence (`next_offset == end_line`, `total_lines >= end_line`, etc.) to prevent silently skipping lines. Capability detection is duck-typed and cached: `_supports_delete()`, `execute_accepts_timeout()`, `_method_accepts_max_count()` via `inspect.signature` + `lru_cache`.

`SandboxBackendProtocol(BackendProtocol)` adds only `id`, `execute(command, *, timeout)`, `aexecute(...)` returning `ExecuteResponse(output, exit_code, truncated)`. `FilesystemMiddleware` exposes the `execute` tool only when `supports_execution(backend)`.

| Backend | File | Notes |
|---|---|---|
| `StateBackend` | `state.py` | **Default.** Files live in LangGraph state — no disk, no shell. Fully ephemeral/virtual. |
| `FilesystemBackend` | `filesystem.py` | Real local disk. `virtual_mode=True` maps `/x` → `{root_dir}/x` and blocks `..`/`~`. Uses ripgrep with a Python fallback. |
| `LocalShellBackend` | `local_shell.py` | `FilesystemBackend` + host shell. `subprocess.run(shell=True, capture_output=True, stdin=DEVNULL, timeout=..., env=self._env, cwd=self.cwd, start_new_session=(sys.platform != "win32"))`. Defaults: 120 s timeout, 100 KB output cap, **empty env unless `inherit_env=True`**. stderr lines prefixed `[stderr]`; timeout returns exit code 124. |
| `BaseSandbox` (ABC) | `sandbox.py` | Implements *all* inherited file ops by generating `python3 -c "..."` scripts and shipping them through the subclass's `execute()`. Subclass implements only `execute` + `id`. Bounds: `MAX_MATCHES=10000`, `TIME_BUDGET=5.0s`, `MAX_OUTPUT_BYTES=500 KB`, prunes `/proc,/sys,/dev`, heredoc transport for edits >50 KB, plus `execute_with_offload` writing full output to a capture path and returning only a 5-line/2 KB head+tail preview. |
| `LangSmithSandbox` | `langsmith.py` | Concrete remote sandbox. |
| `CompositeBackend` | `composite.py` | Routes path prefixes to different backends — the reason `virtual_mode` exists. |
| `StoreBackend` | `store.py` | LangGraph `BaseStore` (cross-session memory). |
| `ContextHubBackend` | `context_hub.py` | Files in a LangSmith Hub agent repo, with a batching `_MutationQueue`, conflict reload on `LangSmithConflictError`, and commit-hash tracking. |

**Sandboxing honesty:** deepagents provides *no* local isolation primitive. `LocalShellBackend` is documented as having "NO sandboxing or isolation," and notes `virtual_mode=True` "provide[s] NO security with shell access enabled." Real isolation means implementing `BaseSandbox` against a container/VM/remote host. Its recommended primary safeguard is HITL middleware.

**Cross-platform:** mostly POSIX-shaped. All paths are POSIX (`PurePosixPath`, `to_posix_path`); `start_new_session` is explicitly guarded on `sys.platform != "win32"`; `BaseSandbox` hard-assumes `python3` and POSIX shell semantics on the remote side.

---

## 7. Profiles

Two **orthogonal, differently-phased** registries — this split is the key idea:

| | `ProviderProfile` | `HarnessProfile` |
|---|---|---|
| File | `profiles/provider/provider_profiles.py` | `profiles/harness/harness_profiles.py` |
| Phase | **model construction** (`resolve_model`) | **runtime shaping** (`create_deep_agent`) |
| Configures | `init_kwargs` (forwarded to `init_chat_model`: `use_responses_api`, `temperature`, `base_url`, headers…), `pre_init` (side effects / min-version checks), `init_kwargs_factory` (env-var-derived kwargs) | `base_system_prompt`, `system_prompt_suffix`, `tool_description_overrides: Mapping[str, str]`, `excluded_tools: frozenset[str]`, `excluded_middleware: frozenset[type | str]`, `extra_middleware`, `general_purpose_subagent: GeneralPurposeSubagentProfile` |

Both are keyed registries accepting a `provider` (`"openai"`) or `provider:model` (`"openai:gpt-5.4"`) key. Registration is **additive**: re-registering merges on top rather than replacing. `HarnessProfileConfig` is the YAML/JSON-serializable subset (`from_dict`), for declarative profiles; the runtime `HarnessProfile` additionally accepts middleware classes/instances. Built-ins register lazily on first registry access (plus third-party plugins via `importlib.metadata` entry points) so importing the package stays cheap.

**Selection at runtime** — `_harness_profile_for_model(model, spec)`:
1. If the caller passed a string spec, look that up directly.
2. Otherwise derive `provider` (`_get_ls_params`) + `identifier` (`model_dump`) from the instance, try `provider:identifier`, then identifier-only (only when it already contains `:`), then provider-only.
3. Fall back to an empty `HarnessProfile()` null object.

A deliberate security-ish choice: a *bare* identifier is never consulted, so an in-house proxy whose `model_name` happens to be `"openai"` can't silently inherit OpenAI's profile.

Prompt assembly is a strict three-slot order — `USER` (caller `system_prompt=`) → `BASE` (`profile.base_system_prompt`) → `SUFFIX` (`profile.system_prompt_suffix`) — applied by `_apply_profile_prompt`, with `SystemMessage` inputs preserving existing `cache_control` markers. Note profiles do **not** carry token limits; `max_input_tokens` is read from LangChain's `model.profile` dict instead.

Built-in harness profiles: `_anthropic_opus_4_7`, `_anthropic_sonnet_4_6`, `_anthropic_haiku_4_5` (~50 lines each — mostly prompt suffixes), `_openai_codex` (88, adds `TodoListMiddleware`), `_nvidia_nemotron_3_ultra` (**1826 lines** — a heavy compatibility shim with its own `wrap_tool_call`/`before_model`/`after_agent` middleware, demonstrating how far the profile system stretches for a quirky open-weight model).

---

## 8. Context / token management

Five distinct, layered mechanisms — the most transferable part of the codebase.

**(1) Model-aware thresholds** (`compute_summarization_defaults`). If `model.profile["max_input_tokens"]` exists, use fraction-based defaults; otherwise conservative fixed counts:

```python
if has_profile:
    return {"trigger": ("fraction", 0.85), "keep": ("fraction", 0.10),
            "truncate_args_settings": {"trigger": ("fraction", 0.85), "keep": ("fraction", 0.10)}}
return {"trigger": ("tokens", 170000), "keep": ("messages", 6),
        "truncate_args_settings": {"trigger": ("messages", 20), "keep": ("messages", 20)}}
```

Triggers use a `ContextSize` tuple form `("tokens"|"messages"|"fraction", value)`; a `TriggerClause` dict combines them with **AND** semantics, and a list of clauses ORs them.

**(2) Tool-arg truncation — a cheaper pre-pass.** `TruncateArgsSettings` clips `args` values on `AIMessage.tool_calls` for messages *before* the keep window (`max_length` chars, then `truncation_text` after the first 20 chars). Targets exactly the fat args: `write_file` content, `edit_file` patches. Explicit goal: "often reclaiming enough context to skip summarizing."

**(3) Compaction with offload-not-drop.** Evicted history is appended to `/conversation_history/{session_id}.md` on the backend *before* the summary replaces it, and **the summary embeds that path** so the agent can `read_file` it back. The README-level contrast is stated in code comments: "LangChain drops evicted messages with no recovery path."

**(4) Non-mutating state.** deepagents tracks compaction in a private `_summarization_event` (`{cutoff_index, summary_message, file_path}`) applied at `wrap_model_call` time via `_get_effective_messages`/`_apply_event_to_messages`, leaving `state["messages"]` fully intact. LangChain instead rewrites history with `RemoveMessage(id=REMOVE_ALL_MESSAGES)` from `before_model`. Preserving the raw log enables replay, evals, forked subagents seeing compacted history, and a shared view with the `compact_conversation` tool. Session IDs are per-invocation so parallel subagents don't collide.

**(5) Tool-result eviction to the filesystem.** `FilesystemMiddleware.wrap_tool_call` with `tool_token_limit_before_evict: int | None = 20000`: any result over ~20k tokens (`NUM_CHARS_PER_TOKEN * limit` chars) is written to `/large_tool_results/{tool_call_id}` and replaced with a stub telling the model to `read_file` with pagination. `TOOLS_EXCLUDED_FROM_EVICTION = ("ls","glob","grep","read_file","edit_file","write_file","delete")` — `read_file` is excluded with a good reason in the comments: evicting a read's output would just make the agent re-read the same truncated file in a loop.

Plus: **inline-media offload** (data-URL image blocks written to the backend, replaced by `_media_reference_block`); **`ContextOverflowError` retry** — on a provider over-budget rejection, `wrap_model_call` summarizes, runs `_clip_overflow_tail` (`_overflow_clip.py`) to shrink the trailing `ToolMessage` batch, and retries instead of bubbling up; **prompt caching** applied unconditionally with `unsupported_model_behavior="ignore"`, with `MemoryMiddleware` and profile middleware deliberately ordered *after* the core stack so memory updates don't invalidate the cache prefix; and **`DeltaChannel`** on `messages` reducing checkpoint growth from O(N²) to O(N).

Notable gap for Arcon: deepagents has **no cost/token accounting or reporting surface** — no `$`-per-run, no per-model spend measurement. That's Arcon's "token economics" pillar and there is nothing here to port for it.

---

## 9. What Arcon should adopt

Arcon is plain-Python/asyncio with `LLMProvider`/`ProviderResolver`, `AgentRegistry.route_query()`, `ToolRegistry`, SQLite storage, and `Agent.invoke(query, context=..., skills=..., stream=...) -> async generator`. Verdict up front: **the middleware pattern, permission model, subagent isolation, and backend protocol are all pure-Python patterns Arcon can port without LangGraph.** What genuinely depends on LangGraph is only checkpoint/interrupt/resume durability and the reducer-based state channels.

Prioritized:

**P0 — Subagent runner via context isolation (Arcon's top feature).** Port the pattern wholesale; it needs no LangGraph. Add a `task(description, subagent_type)` builtin to `ToolRegistry` that constructs a fresh `Agent` (own provider/model, own tool subset, own skills) seeded with `messages=[user(description)]`, shares Arcon's workspace/file layer, and returns **only the final assistant text** to the parent. Copy `_EXCLUDED_STATE_KEYS`-style filtering, the backwards-walk to the last non-empty assistant message, the recursion refusal flag, and the "launch multiple concurrently in one message" tool-description line — with `asyncio.gather` over a tool-call batch, Arcon gets true parallel dispatch more easily than deepagents does. Arcon's 5 YAML agents + `AgentRegistry` are already ~the `SubAgent` spec registry; the missing piece is the runner. *Effort: medium (~3-5 days).* *Skip `mode="fork"` initially* — it depends on replaying private state channels and is beta even upstream.

**P1 — Middleware pipeline with `wrap_*` onion hooks.** Adopt the *shape*, not the API: an `AgentMiddleware` base with `async def wrap_model_call(self, request, handler)` and `async def wrap_tool_call(self, request, handler)` plus `before_agent`/`after_agent`. Compose by folding the list into nested closures around Arcon's provider call inside `Agent.invoke`. Use an immutable `request.override(...)`. Critically, also port the *assembly discipline*: name-based replacement (`_apply_custom_middleware`), a protected-required set, and exclusions that raise on no-match. This is the single highest-leverage refactor because permissions, summarization, skills injection, and subagents all become middleware rather than special cases inside `Agent.invoke`. *Effort: medium-high (~1 week), touches `core/`.* No LangGraph needed — the onion is plain function composition and maps cleanly onto async generators if `handler` is awaited rather than yielded through.

**P2 — Permission system.** Port `FilesystemPermission` + `_check_fs_permission` almost verbatim (it's ~12 lines plus `wcmatch`, already a dependency-light choice). Then port the **argument-level `when` predicate** design: an `_FS_TOOL_PATH_ARGS`-style table with `exact` vs `bulk` scope, and specifically the bypass defenses (pathless bulk → fire; `"."` → `/`; independent `glob` pattern gating; fail-closed recursive delete). Enforce deny inside tools; for `interrupt`, Arcon's CLI/UI can prompt directly and its **SQLite storage lets Arcon beat deepagents** by persisting session-scoped "always allow" decisions — deepagents has no such cache. *Effort: medium for the rule engine (~2-3 days); the delete-overlap analysis is genuinely subtle — port it rather than reinvent.*

**P3 — Backend protocol.** Adopt `BackendProtocol`'s two best decisions: **typed `*Result` dataclasses with `error: str | None` instead of exceptions** (LLM-friendly, and Arcon's tools can pass errors straight to the model), and **sync + `a`-prefixed async pairs**. Arcon is asyncio-native so define async-first and skip the `to_thread` shims. Start with `LocalShellBackend`-equivalent (Arcon is a local coding agent) and keep `SandboxBackendProtocol` as the seam for later container isolation. Note `ReadResult`'s pagination invariants — cheap to copy, prevents silent line-skipping. *Effort: medium (~3-4 days), replaces/extends `tools/executor.py`.*

**P4 — Context management, in this order (each independently shippable):**
1. Tool-result eviction at ~20k tokens to a file + stub message, with the `TOOLS_EXCLUDED_FROM_EVICTION` list and its read_file rationale. *Effort: low (~1 day). Highest token savings per hour invested.*
2. Model-aware fraction thresholds (`0.85` trigger / `0.10` keep) sourced from Arcon's provider metadata; fall back to fixed counts for Ollama models with unknown windows. *Effort: low.*
3. Tool-arg truncation pre-pass before full compaction. *Effort: low-medium.*
4. Compaction that **offloads to `conversation_history/{session}.md` and embeds the path in the summary**, and tracks compaction as a `summarization_event` rather than destroying history — Arcon's SQLite store makes the preserved-log version strictly easier than deepagents' state-channel version. *Effort: medium.*
5. `ContextOverflowError` catch-compact-retry around the provider call. *Effort: low, big robustness win.*

**P5 — Profiles, adopting the two-registry split.** Arcon's YAML config makes `HarnessProfileConfig` a natural fit. Keep the phases separate: a **provider profile** feeding `ProviderResolver` (init kwargs, `base_url`, pre-init version checks — directly useful for Ollama endpoints), and a **harness profile** consumed at agent-construction time (`base_system_prompt`, `system_prompt_suffix`, `tool_description_overrides`, `excluded_tools`, `excluded_middleware`, `extra_middleware`). Copy the `provider:model` → `provider` fallback lookup, additive re-registration merge, and the refuse-bare-identifier rule. This is also Arcon's **model-routing** substrate: profiles per model, selected by resolved spec. *Effort: low-medium (~2-3 days), fits Arcon's existing YAML/factory shape well.*

**P6 — Cheap high-value borrows.** `PatchToolCallsMiddleware` (~50 lines, repairs dangling tool calls after Ctrl-C — essential for an interactive CLI; *effort: hours*). Provider prompt-caching applied unconditionally with ignore-on-unsupported, plus the ordering rule that mutable prompt content (memory/skills) goes *after* the stable prefix. Arcon's 34 markdown skills should adopt `SkillsMiddleware`'s frontmatter validation caps (10 MB file, 64-char name, 1024-char description) and prompt-index injection via a middleware rather than an `invoke(skills=...)` parameter.

---

## 10. What Arcon should NOT copy

- **`create_agent`/LangGraph itself.** deepagents' value is the middleware stack, not the runtime. Adopting LangGraph to get it would import checkpointers, `Command`, `DeltaChannel`, `Runtime`, `InterruptOnConfig`, and reducer semantics into a codebase that has an async generator and SQLite — a huge dependency for patterns Arcon can express in a few hundred lines.
- **Reducer/channel-based state.** `DeepAgentState`'s `DeltaChannel(_messages_delta_reducer, snapshot_frequency=50)` solves O(N²) *checkpoint* growth — a LangGraph-specific problem Arcon doesn't have. Likewise `OmitFromSchema`, `PrivateStateAttr`, and `private_state_field_names` exist because middleware inject state into a shared graph schema; Arcon's subagents can just be objects with their own attributes.
- **`graph.py`'s assembly complexity.** ~980 lines to build one stack, with the exclusion filter applied *three times* (before custom, after custom, then coverage verification) and near-duplicated blocks for main agent / general-purpose subagent / declarative subagents. This is the cost of being a library that must let any consumer override any piece without forking. Arcon ships one product and should build the stack in one place declaratively.
- **`mode="fork"` subagents.** Beta upstream, needs private-channel inheritance, and its own docstring concedes "the tradeoff is cache misses." It also required a whole `_FORK_TASK_PREAMBLE` prompt hack and a recursion-refusal guard to stop the fork misreading the replayed history as a fresh request. Ship isolated subagents; revisit forks only if a concrete need appears.
- **`_nvidia_nemotron_3_ultra.py` (1826 lines).** A single-model compatibility shim larger than most of Arcon's modules. Valuable as *proof* the profile system is expressive enough; a terrible thing to maintain. Cap Arcon profiles at declarative config and refuse to let one model's quirks grow custom middleware.
- **LangSmith coupling.** `ContextHubBackend`, `LangSmithSandbox`, `AsyncSubAgentMiddleware` (which runs subagents "deployed via LangSmith deployments"), `backends/langsmith.py`, and `_subagent_tracing_context()` all assume LangSmith. Arcon needs local-first observability instead — and this is where Arcon's token-economics pillar lives, for which deepagents offers nothing.
- **`RubricMiddleware` (1438 lines)** as a core feature — LLM self-grading is an eval-harness concern, plausible later as an optional skill, not part of the main loop.
- **Trusting `virtual_mode` as a security boundary.** deepagents says so plainly. If Arcon claims sandboxing, it must be process/container-level; otherwise document honestly, as deepagents does, and lean on the permission + approval layer.
- **Not-actually-there features.** Don't plan to "port the planning/todo middleware" — deepagents has none of its own (only LangChain's `TodoListMiddleware`, used by one profile). And `middleware/permissions.py` is a 5-line re-export; the logic is in `filesystem.py`/`_fs_interrupt.py`. Arcon's roadmap should be corrected on both points.
