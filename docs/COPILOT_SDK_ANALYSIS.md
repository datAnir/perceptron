# GitHub Copilot SDK — Analysis for Arcon

Source analyzed: `/home/anirband/perceptron/copilot-sdk` (git HEAD `d3755535`, Java release tag `java/v1.0.13`).
All claims below come from reading the actual source in that tree. Where I could not verify something, I say so.

---

## 1. Overview

**What it is.** `github/copilot-sdk` — "Agents for every app." It is *not* an agent implementation. It is a **thin multi-language client for the Copilot CLI runtime**, which is a separately shipped binary that contains the actual agent loop, planner, built-in tools, and permission engine. The SDK's whole job is to spawn/connect to that runtime and speak JSON-RPC to it.

| Property | Value |
|---|---|
| Publisher | GitHub, Inc. |
| License | MIT (`LICENSE`) |
| Wire protocol version | `sdk-protocol-version.json` → `{"version": 3}` |
| Python package | `github-copilot-sdk` on PyPI, `requires-python >=3.11`, deps `pydantic>=2`, `httpx`, `python-dateutil` |
| Python maturity | `Development Status :: 3 - Alpha`; version is `0.0.0.dev0` in-tree and injected at publish time |
| Language SDKs | **six**: `nodejs/` (TS), `python/`, `go/`, `dotnet/`, `java/`, `rust/` |

**CORRECTION to Arcon's roadmap.** The roadmap assumed this was a Java/Maven codebase. That is **wrong**. `java/` is one of six peer SDKs (with Maven tooling, hence the `[maven-release-plugin]` commits at HEAD). The `session.py` / `client.py` / `tools.py` the roadmap wants to port from are **real Python**, at `python/copilot/`. Arcon can read them directly.

**Multi-language story.** All six SDKs are hand-written façades over a **code-generated** RPC/event layer. In Python that generated layer is `python/copilot/generated/rpc.py` (~44k lines) and `generated/session_events.py` (~13k lines), produced by `scripts/codegen/` from a shared schema. Practical consequence for Arcon: the *hand-written* files are small and readable (`session.py` 3,276 lines, `client.py` 5,001, `tools.py` 470); the generated files are machine noise you should not imitate.

Layout of significant parts:

```
copilot-sdk/
├── sdk-protocol-version.json      # wire protocol v3
├── scripts/codegen/               # generates the rpc/event layer for all 6 SDKs
├── docs/                          # cross-language feature docs (hooks/, features/, setup/, auth/)
├── python/
│   ├── pyproject.toml
│   ├── README.md                  # 45 KB — the real API reference
│   └── copilot/
│       ├── client.py              # CopilotClient, RuntimeConnection, transports
│       ├── session.py             # CopilotSession, permissions, hooks, elicitation
│       ├── tools.py               # define_tool, Tool, ToolResult, ToolInvocation
│       ├── _jsonrpc.py            # JSON-RPC framing
│       ├── _cli_download.py       # downloads/caches the CLI runtime per-platform
│       ├── _mode.py               # ToolSet builder, BUILTIN_TOOLS_ISOLATED, mode="empty"
│       ├── copilot_request_handler.py  # intercept model-layer HTTP/WS
│       ├── canvas.py, session_fs_provider.py, _telemetry.py, _ffi_runtime_host.py
│       └── generated/{rpc.py, session_events.py}
└── nodejs/ go/ dotnet/ java/ rust/  # peer SDKs, same shape
```

---

## 2. Architecture

```
Your app  →  CopilotClient  →(JSON-RPC)→  Copilot CLI runtime (server mode)  →  Copilot backend
```

Four transports, selected via `RuntimeConnection` static factories in `client.py`:

| Factory | Class | Behavior |
|---|---|---|
| `RuntimeConnection.for_stdio(...)` | `StdioRuntimeConnection` | spawn CLI as child, JSON-RPC over stdin/stdout (**default**) |
| `RuntimeConnection.for_tcp(...)` | `TcpRuntimeConnection` | spawn CLI, connect over local TCP |
| `RuntimeConnection.for_uri(url, connection_token=...)` | `UriRuntimeConnection` | attach to an already-running external CLI server |
| `RuntimeConnection.for_inprocess()` | `InProcessRuntimeConnection` | load the native runtime via FFI (`_ffi_runtime_host.py`) — no child process |

Canonical flow:

```python
from copilot import CopilotClient
from copilot.session import PermissionHandler

async with CopilotClient() as client:                # __aenter__ → start()
    session = await client.create_session(
        model="gpt-5",
        on_permission_request=PermissionHandler.approve_all,
        tools=[my_tool],
    )
    unsub = session.on(lambda e: print(e.type))      # streamed events
    await session.send("refactor foo.py")            # returns message id (str)
```

`CopilotClient.start()` resolves the runtime entrypoint, spawns/connects, then calls `_verify_protocol_version()` — a hard compatibility gate against `sdk-protocol-version.json`. Client-level RPCs: `ping`, `get_status`, `get_auth_status`, `list_models`, `list_sessions`, `get_session_metadata`, `delete_session`, `get_last_session_id`, `get_foreground_session_id` / `set_foreground_session_id`, `on_lifecycle`.

---

## 3. Session model — deep dive

`CopilotSession` (`python/copilot/session.py:1552`). Constructor is explicitly internal; you get instances from `client.create_session(...)` or `client.resume_session(...)`.

```python
def __init__(self, session_id: str, client: Any,
             workspace_path: os.PathLike[str] | str | None = None,
             managed_settings_enabled: bool = False,
             on_disconnect: Callable[[], None] | None = None)
```

**State.** Notably, the session holds **no conversation history**. It holds only handler registries, each behind a `threading.Lock`: `_event_handlers`, `_tool_handlers`, `_pending_external_tools`, `_permission_handler`, `_user_input_handler`, `_elicitation_handler`, `_mcp_auth_handler`, `_exit_plan_mode_handler`, `_auto_mode_switch_handler`, `_hooks`, `_transform_callbacks`, `_command_handlers`, `_bearer_token_providers`, `_canvas_handler`, plus `_capabilities` and `_destroyed`. **History lives in the runtime**, retrieved on demand via `await session.get_events()` → `session.getMessages` RPC → `list[SessionEvent]`.

Key methods:

```python
async def send(self, prompt: str, *, attachments=None,
               mode: Literal["enqueue","immediate"]|None = None,
               agent_mode: Literal["interactive","plan","autopilot","shell"]|None = None,
               request_headers: dict[str,str]|None = None,
               display_prompt: str|None = None) -> str
async def send_and_wait(self, prompt, *, ..., timeout: float = 60.0) -> SessionEvent | None
def on(self, handler: Callable[[SessionEvent], None]) -> Callable[[], None]   # returns unsubscribe
async def get_events(self) -> list[SessionEvent]
async def abort(self) -> None                     # session.abort — cancel current turn, session stays usable
async def disconnect(self) -> None                # session.detach — frees handlers, disk state survives
async def set_model(self, model: str, ...) -> None
async def set_auto_tier(self, ...) -> None
@property def rpc(self) -> SessionRpc; @property def capabilities(self) -> SessionCapabilities
@property def ui(self) -> SessionUiApi; @property def workspace_path -> pathlib.Path | None
```

**Cancellation** is two-tier and worth copying: `abort()` cancels the *turn* (idempotent, session reusable); `disconnect()` tears down the *client-side* session (cancels pending external tool tasks, clears every handler dict, sets `_destroyed`) while leaving durable state for `resume_session`. `delete_session` is the only destructive op.

**Streaming events.** `SessionEvent` carries a `type` (`SessionEventType` enum) and a `data` payload that is a **discriminated union of ~130 dataclasses** (`generated/session_events.py:12794`, `SessionEventData`). Consumers `match` on the data class. Selected families: `session.*` (start/resume/idle/error/usage_info/compaction_start/context_cleared/truncation/snapshot_rewind), `assistant.*` (turn_start/message_start/message_delta/reasoning_delta/tool_call_delta/usage/turn_end/idle), `tool.*` (execution_start/partial_result/progress/complete), `subagent.*` (started/configured/completed/failed/selected/deselected), `permission.requested`/`permission.completed`, `hook.*`, `elicitation.*`, `mcp.*`, `factory.*` (fleet). There is a deliberate `RawSessionEventData` fallback plus `test_event_forward_compatibility.py` — **unknown event types are tolerated, not fatal**.

**Resumption.** `client.resume_session(session_id, ...)` accepts the same ~85 kwargs as `create_session`, so handlers/tools/hooks are re-registered on resume. Session listing/metadata is a first-class client API (`SessionMetadata`, `SessionListFilter`). Forking exists as `session.rpc.sessions.fork(SessionsForkRequest(session_id, name=None, to_event_id=None))` → `SessionsForkResult(session_id, name)` — `to_event_id` is an exclusive event-ID boundary, i.e. **fork-at-a-point-in-history**.

**Versus Arcon.** `arcon/src/arcon/core/session.py` `Session` is ~150 lines: `id`, `working_dir`, `provider`, `messages: List[Message]`, a `metadata` dict, and `_total_input_tokens`/`_total_output_tokens`/`_total_cost_usd`. `Session.invoke(query, system_prompt=None, stream=True, **kwargs)` is an async generator that appends a user `Message`, forwards to `provider.create_message`, accumulates `chunk["content"]` for `type == "text"`, and appends one assistant `Message`. Structural gaps: (a) Arcon owns history in-process, Copilot delegates it — Arcon's model is fine for a single-process CLI but has no multi-client story; (b) Arcon has **no event bus** — `invoke` yields raw provider chunks with no typed union, so no UI can subscribe without re-parsing; (c) no `abort`, no fork, no `capabilities`; (d) `clear_context()` is a truncate, versus Copilot's compaction/truncation/rewind events. Arcon's token counters are actually *ahead* of the SDK's session object (the SDK reports usage as events instead).

---

## 4. The permission / elicitation system — deep dive (highest-value port)

Note upfront: the roadmap conflated two separate systems. **`ElicitationHandler` is not the permission system** — it's a generic "ask the user a structured question" channel (`SessionUiApi.confirm/select/input`, `session.py:746-897`). The permission system is separate and is what Arcon wants.

### Handler interface

```python
# session.py:444
class PermissionInvocation(TypedDict, total=False):
    session_id: Required[str]
    managed_settings_enabled: NotRequired[bool]

# session.py:449
_PermissionHandlerFn = Callable[
    [PermissionRequest, PermissionInvocation],
    PermissionRequestResult | AttributedPermissionResult
      | Awaitable[PermissionRequestResult | AttributedPermissionResult],
]

PermissionRequestResult = PermissionDecision | PermissionNoResult   # session.py:403
```

Registered as `create_session(on_permission_request=...)` / `resume_session(on_permission_request=...)`. Sync **or** async both work (`inspect.isawaitable` at `session.py:2742`).

### Granularity: 12 typed request variants, not "tool-level"

`PermissionRequest` is a discriminated union (`generated/session_events.py:11856`) — this is the single most valuable design idea in the repo. Permission is asked about the **semantic operation**, with the fields a human needs to judge it:

| Variant | Key fields |
|---|---|
| `PermissionRequestShell` | `full_command_text`, `commands`, `command_segments`, `possible_paths`, `possible_urls`, `has_write_file_redirection`, `intention`, `warning`, `can_offer_session_approval` |
| `PermissionRequestWrite` | `file_name`, **`diff`**, `new_file_contents`, `intention` |
| `PermissionRequestRead` | `path`, `intention` |
| `PermissionRequestCustomTool` | `tool_name`, `tool_description`, `args`, `skip_permission` |
| `PermissionRequestMcp` | `server_name`, `tool_name`, `tool_title`, `args`, `read_only`, `permission_recommendation` |
| `PermissionRequestUrl` | `url`, `redirected_from`, `intention` |
| `PermissionRequestMemory` | `action`, `direction`, `scope` |
| plus | `Hook`, `Factory`, `ExtensionManagement`, `ExtensionPermissionAccess`, `ExtensionEnvAccess` |

Every variant also carries `tool_call_id`, `managed_approval_required`, and `request_sandbox_bypass` / `request_sandbox_bypass_reason`. So: **path-scoped for reads/writes, command-text-and-segment-scoped for shell, argument-visible for tools/MCP.**

### Decision vocabulary and scope caching

Decisions are present-tense classes in `copilot.rpc` (`kind` is a `ClassVar`, never passed by the caller):

| Decision | Scope / persistence |
|---|---|
| `PermissionDecisionApproveOnce()` | this request only |
| `PermissionDecisionApproveForSession(approval=…, domain=…)` | remembered for the session; `domain` for URL prompts |
| `PermissionDecisionApproveForLocation(approval=…, location_key=…)` | **persisted to a project location — `location_key` is the git root or cwd** |
| `PermissionDecisionApprovePermanently()` | persisted globally |
| `PermissionDecisionReject(feedback="…")` | denied; `feedback` string is fed back to the LLM |
| `PermissionDecisionUserNotAvailable()` | **the default/fail-closed outcome** |
| `PermissionNoResult()` | abstain — leave the request pending for another connected client |

`approval` sub-objects are themselves typed per operation class (`…ApprovalRead`, `…ApprovalWrite`, `…ApprovalCommands`, `…ApprovalCustomTool`, `…ApprovalMCP`, `…ApprovalMCPSampling`, `…ApprovalFactory`, `…ApprovalMemory`, …), so "always allow" is remembered *per operation class*, not per raw tool name. Persistence itself lives in the runtime — the SDK only transmits the scope.

### Two dispatch modes

1. **Direct callback** — `on_permission_request` supplied: `_handle_permission_request` (`session.py:2711`) runs it and replies.
2. **Event-based / pending** — handler omitted: the request is emitted as a `permission.requested` event (`PermissionRequestedData(permission_request, request_id, agent_mode, prompt_request, resolved_by_hook, risk_assessment)`) and left **pending**. Any connected client resolves it later via `session.rpc.permissions.handle_pending_permission_request(PermissionDecisionRequest(request_id, result, decision_context=None))`. Completion broadcasts `permission.completed` with a past-tense `PermissionResult` (`PermissionApproved`, `PermissionApprovedForSession`, `PermissionApprovedForLocation`, `PermissionDeniedByRules`, `PermissionDeniedInteractivelyByUser`, `PermissionDeniedByContentExclusionPolicy`, `PermissionDeniedByPermissionRequestHook`, `PermissionCancelled`, `PermissionDeniedNoApprovalRuleAndCouldNotRequestFromUser`). Note the deliberate **present-tense decision vs past-tense result** split.

### Safety posture — fail closed, three times

```python
if not handler:
    return PermissionDecisionUserNotAvailable()          # no handler → deny
...
except Exception:
    logger.error("Permission handler failed", ...)
    return PermissionDecisionUserNotAvailable()          # handler raised → deny
if isinstance(result, PermissionNoResult):
    return PermissionDecisionUserNotAvailable()          # abstain on direct callback → deny
```

Enterprise override layer: `ManagedSettings(permissions=ManagedSettingsPermissions(allow=[...], ask=[...], deny=[...], disable_bypass_permissions_mode=...))` (`client.py:329-368`) — rule strings like `"Read(**)"`, `"Shell(git push *)"`. Composition is restrictive: `deny` and `ask` are **unioned** across layers; `allow` must be admitted by **every** layer. `PermissionHandler.approve_all` *raises* under managed settings and returns `PermissionNoResult()` whenever `request.managed_approval_required` is true — auto-approval is blocked from silently overriding policy. Per-tool `skip_permission=True` is the only bypass.

`AttributedPermissionResult` / `create_attributed_permission_result(result, decision_context)` attach a `PermissionDecisionContext(outcome, source, surface, response_capability)` for telemetry only — explicitly documented as never changing behavior.

---

## 5. Tool definition & registration

`python/copilot/tools.py` (470 lines) — the cleanest file in the repo.

```python
@define_tool(description="Fetch issue details")
def lookup_issue(params: LookupIssueParams) -> str: ...     # LookupIssueParams is a pydantic BaseModel
```

**Schema derivation: pydantic, not hand-rolled.** `get_type_hints(fn)` finds the first parameter's type; if it's a `BaseModel` subclass, `ptype.model_json_schema()` becomes `Tool.parameters`. Four handler shapes are auto-detected by arity + hints: `()`, `(ToolInvocation)`, `(params)`, `(params, invocation)`.

`Tool` fields: `name`, `description`, `handler`, `parameters`, `overrides_built_in_tool`, `skip_permission`, `defer: "auto"|"never"`, `metadata`, `is_terminal` (a successful call **ends the turn**; a failed call keeps the loop running so the model can retry — a nice loop-engineering detail).

`ToolResult(text_result_for_llm, result_type: "success"|"failure"|"rejected"|"denied"|"timeout", error, binary_results_for_llm, session_log, tool_telemetry, tool_references)`. `_normalize_result` coerces `None`/`str`/`ToolResult`/anything-JSON-serializable (with pydantic, datetime, Decimal, UUID, Enum, set encoders).

**Error handling is security-conscious and worth stealing verbatim.** Pydantic `ValidationError` returns a *helpful* per-field message to the LLM. Any other exception returns the deliberately opaque `"Invoking this tool produced an error. Detailed information is not available."` with the real message in `ToolResult.error` for host-side debugging. Arcon currently has no equivalent split.

Registration/dispatch: tools are passed as `create_session(tools=[...])`; `_register_tools` stores handlers in `_tool_handlers`; the runtime issues `external_tool.requested`, and `_execute_tool_and_respond` (`session.py:2157`) runs the handler as an `asyncio.Task` tracked in `_pending_external_tools` and replies via `HandlePendingToolCall`. Built-ins live in the runtime, filtered by `available_tools` / `excluded_tools` accepting a `ToolSet` builder with source-qualified patterns (`builtin:bash`, `mcp:*`, `custom:my_tool`).

**Versus Arcon.** `tools/base.py` has an ABC `Tool` with `_create_metadata()`, `_create_parameters() -> List[ToolParameter]`, `async execute(**kwargs)`, and `tools/registry.py` `ToolRegistry` with `register/get/has/list_all/get_by_category/get_by_tag/to_dict()`. Arcon builds JSON schema by hand from `ToolParameter(name, type, description, required, default)`. Arcon's registry is *richer* on discovery (category/tag lookup — the SDK has nothing like it, useful for skills/routing) but weaker on authoring: every tool needs a class and a hand-written parameter list. Arcon already depends on pydantic (it's in `venv`), so a `@define_tool`-style decorator is a low-cost, high-leverage addition that can coexist with the ABC.

---

## 6. Subagents

**Sub-agents are runtime-side, not SDK-side.** You *declare* agents; the Copilot runtime decides to delegate and reports back. Declaration via `create_session(custom_agents=[CustomAgentConfig], default_agent=..., agent="name", excluded_builtin_agents=[...], custom_agents_local_only=...)`. A `CustomAgentConfig` is `{name, display_name, description, tools, prompt}` — i.e. **the same shape as Arcon's 5 YAML agents**.

Per `docs/features/custom-agents.md`, delegation runs the child "in an isolated context while streaming lifecycle events back to the parent session." What returns to the parent is the **event stream**, not shared history:

- `SubagentStartedData(agent_name, agent_display_name, agent_description, tool_call_id, agent_type, execution_mode, factory_run_id, model, parent_id, resumable)`
- `SubagentConfiguredData(model, multi_turn, context_tier, reasoning_effort)`
- `SubagentCompletedData(agent_name, tool_call_id, cancelled, duration, model, total_tokens, total_tool_calls, …model-override attribution fields)`
- `SubagentFailedData(…, error)`, plus `SubagentSelectedData` / `SubagentDeselectedData`

`create_session(include_sub_agent_streaming_events=True)` (default) forwards child deltas with `agentId` set; `False` gives lifecycle-only.

**On the "`isolated` mode rename."** The only `ISOLATED` identifier in the Python SDK is `BUILTIN_TOOLS_ISOLATED` in `_mode.py:96` — the built-in tool allowlist for `mode="empty"` (`["ask_user","task_complete","exit_plan_mode","task","read_agent","write_agent","list_agents","send_inbox","context_board","skill"]`). That is a **client-mode tool allowlist, not a subagent mode**. "Isolated" as a subagent property appears only as prose in `docs/features/custom-agents.md`. I did not find a subagent-scoped `isolated` enum; the prior skim's claim looks unconfirmed at this commit.

**Rubric/grader hooks: not present.** `grep -i "rubric|grader"` over `python/` returns zero hits (only `degraded_*` false positives). If those exist, they are not in the Python SDK at this commit.

**Fleet mode** (`docs/features/fleet-mode.md`) is the real parallel-orchestration surface: `session.rpc.fleet.start(FleetStartRequest(prompt=...))`, dispatching many sub-agents via a `task` tool with SQL todos as shared coordination state. It is backed by the `factory.*` RPC namespace (`run`, `resume`, `cancel`, `get_run_progress`, `journal.get/put`, `agent`) with declared limits `FactoryRunLimits(max_ai_credits, max_concurrent_subagents, max_total_subagents, timeout_seconds)` and consumption accounting `FactoryRunConsumed(active_ms, nano_aiu, subagents)`. The docs mark fleet mode **experimental** and advise pinning both SDK and CLI.

---

## 7. Hooks & extensibility

`SessionHooks` TypedDict (`session.py:1156`), passed as `create_session(hooks={...})`. Ten hooks, each `Callable[[Input, dict[str,str]], Output | None | Awaitable[...]]`:

`on_pre_tool_use`, `on_pre_mcp_tool_call`, `on_post_tool_use`, `on_post_tool_use_failure`, `on_user_prompt_submitted`, `on_user_prompt_transformed`, `on_session_start`, `on_session_end`, `on_error_occurred`, `on_agent_stop`.

The one Arcon should note is `PreToolUseHookOutput`:

```python
class PreToolUseHookOutput(TypedDict, total=False):
    permissionDecision: Literal["allow", "deny", "ask"]
    permissionDecisionReason: str
    modifiedArgs: Any
    additionalContext: str
    suppressOutput: bool
```

**This is where the literal `allow`/`deny`/`ask` triple lives** — a *policy* layer that can pre-empt or defer to the interactive permission handler, and can also rewrite tool args. `PostToolUseHookOutput` can rewrite results (`modifiedResult`, `additionalContext`). Denial through this path surfaces as `PermissionDeniedByPermissionRequestHook`.

Other extension surfaces: system-message `append` / `replace` / `customize` (with per-`SectionOverride` transform callbacks); `commands=[CommandDefinition]` for host slash-commands; `on_elicitation_request` + `session.ui.{confirm,select,input,elicitation}`; `canvases` / `CanvasHandler` for host-rendered UI; `session_fs` provider; `CopilotRequestHandler` to intercept every model-layer HTTP/WS request; skills (`enable_skills`, `skill_directories`, `included_builtin_skills`, `disabled_skills`) and `plugin_directories` / `instruction_directories`.

**MCP: full support.** `mcp_servers: dict[str, MCPStdioServerConfig | MCPHTTPServerConfig]`, per-server tool allowlists, OAuth via `on_mcp_auth_request` with `mcp_oauth_token_storage: "persistent"|"in-memory"`, MCP Apps (`enable_mcp_apps`), and `convert_mcp_call_tool_result()` in `tools.py`.

---

## 8. Model selection / routing

- **Listing:** `await client.list_models() -> list[ModelInfo]`, where `ModelInfo(id, name, capabilities, policy, billing, supported_reasoning_efforts, default_reasoning_effort)`. Hosts can *supply* the list via `CopilotClient(on_list_models=...)`.
- **Selection:** `create_session(model=..., reasoning_effort=..., reasoning_summary=..., context_tier=...)`, plus mid-session `await session.set_model(model, ...)`. Per-agent `model` in `CustomAgentConfig`.
- **Routing:** `capi=CapiSessionOptions(auto_tier="efficiency"|"balance"|"intelligence")` and `session.set_auto_tier(...)` — Arcon-relevant, but it selects a *server-side* Auto router; the routing logic itself is not in the SDK. `fusion.*` events hint at further server-side routing.
- **BYOK / local models:** `provider=ProviderConfig` (single, Azure/custom endpoint) or additive `providers=[NamedProviderConfig]` + `models=[ProviderModelConfig]`, each with a `bearer_token_provider` callback. `CopilotRequestHandler` can service *every* model request in-process. This is the closest analogue to Arcon's Ollama path, and it means an OpenAI-compatible local endpoint is expressible.
- **Usage/token reporting:** event-based, and richer than Arcon's counters. `AssistantUsageData(model, cache_read_tokens, cache_write_tokens, cache_expires_at, cost, duration, finish_reason, api_endpoint, copilot_usage, …)` per model call; `SessionUsageInfoData(current_tokens, token_limit, conversation_tokens, system_tokens, tool_definitions_tokens, messages_length)` for context-window pressure — note the **breakdown by system vs tools vs conversation**. Also `session.usage_checkpoint`, `session.completion_receipt`, `session_limits` config and `session.limits_exhausted` requests.

---

## 9. Cross-platform & packaging

`pip install github-copilot-sdk` (py3.11–3.14). **The CLI runtime is a hard dependency.** For Node/Python/.NET it is auto-bundled; `_cli_download.py` fetches a platform-specific GitHub Release asset, SHA-verifies it, and materializes it into an OS-appropriate cache:

| OS | Cache path |
|---|---|
| Linux | `~/.cache/github-copilot-sdk/cli/{version}/prebuilds/{platform}/copilot` |
| macOS | `~/Library/Caches/github-copilot-sdk/cli/{version}/prebuilds/{platform}/copilot` |
| Windows | `%LOCALAPPDATA%/github-copilot-sdk/cli/{version}/prebuilds/{platform}/copilot.exe` |

Escape hatches: `COPILOT_SKIP_CLI_DOWNLOAD`, `COPILOT_CLI_EXTRACT_DIR`, `COPILOT_CLI_DOWNLOAD_BASE_URL`. Go/Java/Rust require a manual CLI install on `PATH`.

**Auth** is GitHub-centric: `CopilotClient(github_token=..., use_logged_in_user=...)`, per-session `github_token` / `github_token_provider` (for multi-tenant servers), `COPILOT_HOME` via `base_directory`, and `await client.get_auth_status() -> GetAuthStatusResponse(isAuthenticated, authType, host, login, statusMessage)`. Docs cover device OAuth, server-to-server tokens, Azure managed identity, and BYOK.

---

## 10. What Arcon should adopt

| # | What to build | Where it comes from | Effort | Priority |
|---|---|---|---|---|
| 1 | **Permission system** | §4 | 3–5 d | **Highest** |
| 2 | Typed session event union + event bus | §3 | 3–4 d | High |
| 3 | `@define_tool` pydantic decorator + tool error split | `tools.py` | 1–2 d | High |
| 4 | Subagent runner on `Agent.invoke` | §6 | 2–3 d | High |
| 5 | `PreToolUse`/`PostToolUse` hooks with `allow/deny/ask` | §7 | 1–2 d | Medium |
| 6 | Usage events with system/tool/conversation split | §8 | 1 d | Medium |
| 7 | `abort()` / `fork()` on `Session` | §3 | 1–2 d | Medium |

**1. Permission system — the single highest-value port.** Copy the *shape*, not the code. New `arcon/src/arcon/permissions/`:
- A `PermissionRequest` discriminated union of dataclasses — start with `ShellRequest(full_command_text, possible_paths, has_write_redirection, intention)`, `WriteRequest(file_name, diff, new_file_contents)`, `ReadRequest(path)`, `CustomToolRequest(tool_name, tool_description, args)`. The **`diff` on writes** and **`possible_paths` on shell** are what make a prompt reviewable; do not collapse to `(tool_name, args)`.
- Decisions: `ApproveOnce`, `ApproveForSession(approval)`, `ApproveForLocation(approval, location_key=git_root_or_cwd)`, `ApprovePermanently`, `Reject(feedback)`, `UserNotAvailable`.
- `PermissionHandlerFn = Callable[[PermissionRequest, PermissionInvocation], Result | Awaitable[Result]]`, awaited via `inspect.isawaitable`.
- **Fail closed** exactly as `session.py:2711` does: no handler → deny, handler raises → deny (log with `exc_info`).
- Persistence: Arcon already has SQLite (`storage/sqlite.py`) — session-scoped approvals in memory, `ApproveForLocation` in a table keyed by git-root, `ApprovePermanently` in `~/.arcon/permissions.json`.
- Wiring: enforce in `tools/executor.py` before dispatch, since both CLI and future UI go through it. Both dispatch modes matter for Arcon's CLI+UI goal — a direct callback for the CLI, and a pending-request queue keyed by `request_id` so the UI can resolve asynchronously.

**2. Typed events.** `Session.invoke` currently yields raw provider dicts, so every consumer re-parses. Define `SessionEvent(type, data)` with a dataclass union (`AssistantMessageDelta`, `ToolExecutionStart/Complete`, `PermissionRequested`, `SubagentStarted/Completed`, `Usage`, …), add `Session.on(handler) -> unsubscribe`, and **include a `RawEvent` fallback** so a new event type never crashes an older consumer. This is the prerequisite for the UI and for token economics.

**3. `@define_tool`.** Additive next to the existing ABC in `tools/base.py`; `ToolRegistry.register` already takes a `Tool`. Adopt the arity/type-hint detection, `model_json_schema()`, `_normalize_result`, and especially the two-tier error contract (verbose pydantic validation errors to the LLM; opaque message for unexpected exceptions with the real error kept host-side).

**4. Subagents.** `Agent.invoke(query, context=..., skills=..., stream=True)` in `agents/base.py` is already the right seam — an async generator taking explicit `context: list[Message]`. Build `agents/subagent.py` that: forks a child context (Copilot's `to_event_id` boundary → in Arcon, slice `parent.messages[:n]` or pass a summary), constructs the child from an existing YAML agent's `tools`/`prompt`, runs `child.invoke(...)`, re-emits child chunks upward tagged with `agent_id` behind an `include_subagent_streaming` flag, and returns **only a result summary + `total_tokens` + `total_tool_calls`** to the parent — mirror `SubagentCompletedData`. Enforce `max_concurrent_subagents` / `max_total_subagents` / `timeout_seconds` from the start (`FactoryRunLimits`); unbounded spawning is the classic failure mode. Reuse `Agent.allowed_tools` as the child's tool scope.

**5. Hooks.** Adopt the `PreToolUseHookOutput` contract as Arcon's *policy* layer above the interactive handler: `{"permission_decision": "allow"|"deny"|"ask", "reason": str, "modified_args": dict, "additional_context": str}`. `ask` deferring to the interactive handler is the key composition trick.

**6. Usage.** Extend Arcon's existing `_total_*_tokens` with cache read/write, cost, duration, and the `SessionUsageInfoData` split (`system_tokens` / `tool_definitions_tokens` / `conversation_tokens` / `token_limit`) — that breakdown is what makes context engineering measurable rather than guessed.

---

## 11. What Arcon should NOT copy / caveats

1. **The whole architecture.** This SDK is a client to a proprietary closed runtime; the agent loop, built-in tools, planner, compaction, and permission *engine* are in the CLI binary, not here. Arcon *is* the runtime. Copy data models and contracts; do not copy the JSON-RPC-to-a-binary topology.
2. **The generated layer.** ~57k lines of `from_dict`/`to_dict` in `generated/`. Do not hand-write that, and do not stand up a codegen pipeline for a single-language project. Use pydantic models or dataclasses directly.
3. **GitHub coupling.** `github_token`, `use_logged_in_user`, `COPILOT_HOME`, `GetAuthStatusResponse`, device OAuth, `github_mcp_tool_config`, and Release-asset CLI download are all GitHub infrastructure. Arcon's multi-provider key model is unrelated.
4. **Entitlement/billing assumptions.** `ModelPolicy`, `ModelBilling`, `AssistantUsageCopilotUsage`, "AI credits"/`nano_aiu`, `session_limits`, `session.limits_exhausted` presume Copilot quotas. Arcon's economics are per-token cost across providers — build that model natively.
5. **Enterprise managed settings.** `ManagedSettings` / `enable_managed_settings` / MDM policy layering is real engineering but wrong-priority for v0.1. **Do** keep the composition rule (deny/ask union, allow intersect) if Arcon ever adds team policy.
6. **API stability.** Every permission decision type is annotated *"Experimental: this type is part of an experimental API and may change or be removed."* Fleet mode is explicitly experimental and advises pinning SDK+CLI together. Python package is `Development Status :: 3 - Alpha`. `sdk-protocol-version.json` v3 is hard-gated at `start()`, meaning breaking wire changes are expected. Treat everything here as inspiration, not a stable contract — and don't inherit `_verify_protocol_version`-style hard version gates into Arcon, where there is no split binary to gate against.
7. **Copilot-runtime-only surfaces** with no Arcon analogue: `canvas.py`, `session_fs_provider.py`, `_ffi_runtime_host.py`, remote/cloud sessions, `factory.*` journaling, `mode="empty"` (a multi-tenancy affordance for hosting *someone else's* agent).
8. **Unverified prior claims.** Rubric/grader hooks: **absent** from the Python SDK at this commit. A subagent-scoped `isolated` mode: **not found** — `BUILTIN_TOOLS_ISOLATED` is a `mode="empty"` tool allowlist. Conversation forking: **confirmed**, as `sessions.fork` with a `to_event_id` boundary. Don't plan around the first two.
