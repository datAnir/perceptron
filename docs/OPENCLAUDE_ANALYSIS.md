# OpenClaude — Deep Analysis for Arcon

Analysis target: `/home/anirband/perceptron/openclaude` @ `0abfca30` (`fix(sdk): preserve async generator session context`).
Purpose: extract portable patterns for **Arcon** (`/home/anirband/perceptron/arcon`, Python v0.1.0). Everything below was read from source; uncertainty is flagged explicitly.

---

## 1. Overview

| Field | Value |
| --- | --- |
| Package | `@gitlawb/openclaude` v**0.30.0** (`package.json`) |
| Org / repo | `github.com/Gitlawb/openclaude` |
| Stack | TypeScript, ESM (`"type": "module"`), **React-in-terminal** via a vendored Ink fork (`src/ink/`) |
| Runtime | **Node >= 22** for install/run (`engines`); **Bun 1.3.13** (`.bun-version`) for source builds + tests (`bun test`) |
| Build | `scripts/build.ts` → single bundle `dist/cli.mjs` (+ separate `dist/sdk.mjs`), `target: 'node'` |
| License | **Not clean MIT.** `LICENSE` is a NOTICE stating the repo "contains code derived from Anthropic's Claude Code CLI", that the original is proprietary, that only *modifications* are MIT, and that "This project does not have Anthropic's authorization to distribute their proprietary source." |
| Size | ~3,191 `.ts`/`.tsx` files under `src/` |

**Relation to Claude Code:** it is a **de-obfuscated/derived fork turned superset**, not an independent reimplementation. Evidence: it depends on `@anthropic-ai/sdk`, `@anthropic-ai/bedrock-sdk`, `@anthropic-ai/foundry-sdk`, `@anthropic-ai/sandbox-runtime`; internal analytics event names are Claude Code's (`tengu_unknown_model_cost`, `tengu_api_opus_fallback_triggered`); env vars are `CLAUDE_CODE_*`; and internal-only gates read `process.env.USER_TYPE === 'ant'`. The fork's own value-add is **provider breadth** (OpenAI-compatible, Gemini, Codex OAuth, GitHub Models/Copilot, Bedrock/Vertex/Foundry, Ollama, and ~20 named gateways), plus config re-homing to `~/.openclaude` (it deliberately does **not** read `~/.claude`).

> Legal caveat for Arcon: do **not** copy code from this repo. Read it as a design reference only. Arcon being Python makes this a natural boundary.

---

## 2. Architecture

Flow: `bin/openclaude` (Node shim, heap-relaunch at 8 GB default) → `src/entrypoints/cli.tsx` (arg parse, provider preflight) → `src/main.tsx` / `src/replLauncher.tsx` (Ink mount) → **`QueryEngine`** (`src/QueryEngine.ts`, 1,555 LOC) → **`query()`** (`src/query.ts`, 3,204 LOC — the agent loop) → `src/services/api/claude.ts` (3,963 LOC, request/stream/usage) → shim layer (`openaiShim/`, `codexShim.ts`) → tools (`src/Tool.ts` + `src/tools/`) → cost tracker + Ink renderer.

```
src/
├── entrypoints/cli.tsx        CLI entry: argv, provider preflight, bg/print/mcp modes
├── main.tsx, replLauncher.tsx Ink app mount + REPL bootstrap
├── QueryEngine.ts             Turn orchestrator: submitMessage() async generator, budget checks, SDK messages
├── query.ts                   The agent loop (tool calls, compaction hooks, retries)
├── Tool.ts / tools.ts         Tool interface + registry
├── tools/                     ~55 built-in tools (Bash, FileEdit, Agent, Skill, RepoMap, …)
├── cost-tracker.ts            Session cost aggregation + /cost rendering  ← §3
├── utils/modelCost.ts         Pricing table + USD math                    ← §3
├── services/api/
│   ├── claude.ts              Request execution, streaming, usage capture
│   ├── withRetry.ts           Retry/backoff, 529 handling, model fallback
│   ├── providerConfig.ts      Provider/transport/base-URL resolution (1,547 LOC)
│   ├── openaiShim/            OpenAI-compat + Ollama adapters, text tool-call parsing
│   ├── smartModelRouting.ts   Pure simple/strong turn classifier            ← §4
│   ├── smartRouting/          Config, allowlist enforcement, tally, /cost summary
│   ├── agentRouting.ts        Per-agent model/provider routing
│   ├── cacheMetrics.ts        Cross-provider cache-token normalizer
│   └── cacheStatsTracker.ts   Session cache hit-rate stats
├── integrations/              Descriptor-driven provider/gateway registry + discovery cache
├── services/compact/          auto/micro/snip/time-based compaction
├── skills/                    Skill discovery + bundled skills
├── cli/handlers/skillsInstall.ts  Skill registry install + revocation enforcement
├── ink/                       Vendored/forked Ink renderer
├── bootstrap/state.ts         Process-global session/cost STATE + async-context binding
└── utils/sessionStorage.ts    JSONL transcript persistence
web/                           Astro marketing site (NOT an app UI)
vscode-extension/              Launcher + theme integration
```

---

## 3. Cost tracking — DEEP DIVE

Two files own this: **`src/utils/modelCost.ts`** (pricing + math) and **`src/cost-tracker.ts`** (accumulation + display). State lives in **`src/bootstrap/state.ts`**.

### 3.1 Pricing data model

Prices are **per-million-token rates in a hardcoded, shared-tier table** — not per-model duplicated numbers. Five fields, including both cache directions and a per-request web-search rate:

```ts
export type ModelCosts = {
  inputTokens: number            // USD per 1M
  outputTokens: number
  promptCacheWriteTokens: number
  promptCacheReadTokens: number
  webSearchRequests: number      // USD per request (0.01)
}

export const COST_TIER_3_15 = {            // "Sonnet tier"
  inputTokens: 3, outputTokens: 15,
  promptCacheWriteTokens: 3.75,            // = 1.25 × input
  promptCacheReadTokens: 0.3,              // = 0.10 × input
  webSearchRequests: 0.01,
} as const satisfies ModelCosts

export const MODEL_COSTS: Record<ModelShortName, ModelCosts> = { /* short-name → tier */ }
export const DEFAULT_UNKNOWN_MODEL_COST = COST_TIER_5_25
```

Key design points worth porting:
- **Tiers, not rows.** `COST_TIER_3_15`, `COST_TIER_15_75`, `COST_TIER_5_25`, `COST_TIER_30_150`, `COST_HAIKU_35`, `COST_HAIKU_45`. Many model ids map to one tier object. Adding a model = one line.
- **Canonicalization before lookup.** `getCanonicalName(model)` collapses provider prefixes/aliases to a short name, so `openrouter/anthropic/claude-sonnet-4` and `claude-sonnet-4-20250514` hit the same tier.
- **No auto-update.** The table is a **hardcoded constant with a `// @[MODEL LAUNCH]:` comment** telling maintainers to add an entry manually. There is **no** pricing fetch, no LiteLLM-style JSON download, no cache-with-TTL. Prices ship with the release.
- **Unknown-model handling is explicit and surfaced.** Unknown → `DEFAULT_UNKNOWN_MODEL_COST` **and** sets a global flag; `/cost` then appends `"(costs may be inaccurate due to usage of unknown models)"`. This is the honest answer to "the user is on a random gateway model."
- **User pricing overrides** (`src/utils/settings/modelPricing.ts`) let a user pin real prices per exact model id:
  ```ts
  const TRUSTED_MODEL_PRICING_SOURCES = new Set<SettingSource>([
    'userSettings', 'localSettings', 'flagSettings', 'policySettings',
  ])
  ```
  **Project/shared settings are deliberately excluded** so a checked-in repo file cannot rewrite a user's USD accounting. Matching is on the **exact resolved model id** with no normalization — override precision beats override convenience.
- **Prototype-pollution hardening** appears twice: `Object.hasOwn(MODEL_COSTS, shortName)` instead of `MODEL_COSTS[shortName]`, and `Object.create(null)` for the per-model accumulator — because arbitrary gateway model ids can be `__proto__` or `constructor`.

### 3.2 The cost formula

```ts
function tokensToUSDCost(modelCosts: ModelCosts, usage: Usage): number {
  return (
    (usage.input_tokens / 1_000_000) * modelCosts.inputTokens +
    (usage.output_tokens / 1_000_000) * modelCosts.outputTokens +
    ((usage.cache_read_input_tokens ?? 0) / 1_000_000) * modelCosts.promptCacheReadTokens +
    ((usage.cache_creation_input_tokens ?? 0) / 1_000_000) * modelCosts.promptCacheWriteTokens +
    (usage.server_tool_use?.web_search_requests ?? 0) * modelCosts.webSearchRequests
  )
}
```
Cache reads/writes are **priced as separate line items at different rates** — not folded into input tokens. `input_tokens` is post-shim **fresh-only**; the shim subtracts cached tokens from raw `prompt_tokens` so `read + created ≤ total` holds (documented invariant in `cacheMetrics.ts`).

### 3.3 Usage capture and aggregation

Capture point: `src/services/api/claude.ts:2659` (streaming) and `:3366` (non-stream fallback):

```ts
const costUSDForPart = calculateUSDCost(resolvedModel, usage)
costUSD += addToTotalSessionCost(costUSDForPart, usage, resolvedModel)
```

`addToTotalSessionCost(cost, usage, model)` in `cost-tracker.ts` then:
1. `addToTotalModelUsage` → accumulates a per-model `ModelUsage` record `{inputTokens, outputTokens, cacheReadInputTokens, cacheCreationInputTokens, webSearchRequests, costUSD, contextWindow, maxOutputTokens}`.
2. `addToTotalCostState(cost, modelUsage, model)` → writes into process-global `STATE.modelUsage[model]` and `STATE.totalCostUSD += cost`.
3. Records normalized cache metrics via `recordCacheRequest(cacheMetrics, model)`.
4. Optional per-request NDJSON debug line on **stderr** gated by `OPENCLAUDE_LOG_TOKEN_USAGE` (tag `openclaude.tokenUsage`).
5. **Recurses** for sub-model "advisor" usage: `getAdvisorUsage(usage)` yields nested usages that are costed and added under their own model id.

**Aggregation granularity: per-model within a session only.** `getTotalInputTokens()` etc. are `sumBy(Object.values(STATE.modelUsage), 'inputTokens')` — derived, not separately counted. There is **no daily or monthly aggregation anywhere** in this repo (verified: no rollup store, no date-bucketed table). Historical/date-based spend is not a feature. Cross-session totals for gateways come from *provider-reported* quota endpoints (`clinepassUsage.ts`, `codexUsage.ts`, `minimaxUsage.ts`), not from local accumulation.

### 3.4 Persistence

Not a database — a **single "last session" snapshot in project config** (`saveCurrentSessionCosts()`), keyed by session id:

```ts
saveCurrentProjectConfig(current => ({ ...current,
  lastCost: getTotalCostUSD(),
  lastAPIDuration: ..., lastToolDuration: ..., lastLinesAdded: ...,
  lastTotalCacheCreationInputTokens: ..., lastTotalCacheReadInputTokens: ...,
  lastModelUsage: { /* per-model breakdown */ },
  lastSessionId: getSessionId(),
}))
```
Restore is guarded: `getStoredSessionCosts(sessionId)` returns `undefined` unless `projectConfig.lastSessionId === sessionId`, so resuming session A never inherits session B's spend. `restoreCostStateForSession()` → `setCostStateForRestore()`. `resetCostState()` (on `/clear`, `/compact`, session switch) zeroes cost **plus** the cache-stats tracker **plus** the routing tally, so `/cost` never mixes windows.

### 3.5 Budget enforcement

`QueryEngine` supports a hard USD ceiling (`src/QueryEngine.ts:1090`):

```ts
if (maxBudgetUsd !== undefined && getTotalCost() >= maxBudgetUsd) {
  // emits SDK result with subtype: 'error_max_budget_usd',
  // errors: [`Reached maximum budget ($${maxBudgetUsd})`]
}
```
Checked **between turns in the loop**, not mid-stream. Every SDK result message carries `total_cost_usd: getTotalCost()` and `usage: this.totalUsage`.

### 3.6 Surfacing to the user

`/cost` → `src/commands/cost/cost.ts` → `formatTotalCost()`. Output has four blocks: a dim stats block (total cost, API duration, wall duration, lines added/removed), an ASCII **token bar chart** (`formatTokenBar`, 20-cell `█`/`░`, blue input / green output / cyan cache-read / yellow cache-write, each scaled to the max of the four), a **per-short-name model breakdown** with cache and web-search columns, and the **smart-routing summary**. Formatting rule: `formatCost` uses 2 decimals above $0.50 and 4 below. The command self-hides for subscription users (`isHidden` → `isClaudeAISubscriber()`).

---

## 4. Provider abstraction & model routing — DEEP DIVE

### 4.1 There is no `Provider` interface

This is the most important finding and it **contradicts Arcon's roadmap assumption**. `QueryEngine.ts` contains no provider abstraction — it is a turn orchestrator (`async *submitMessage()`, `injectMessages`, `setModel`, `updateTools`, budget/interrupt handling). Providers are handled by **normalizing everything to the Anthropic Messages shape**:

1. `resolveProviderRequest()` in `src/services/api/providerConfig.ts` resolves `{baseURL, apiKey, model, transport, ...}` from env + saved profile + descriptor.
2. One transport enum decides the wire protocol: `type ProviderTransport = 'chat_completions' | 'responses' | 'responses_compat' | 'codex_responses'`.
3. **Shims translate inbound/outbound**: `openaiShim/` (with `ollamaAdapter.ts`, `geminiStreamConversion.ts`, `responseAdapters.ts`) and `codexShim.ts` convert requests to the provider format and convert responses/usage **back to Anthropic-shaped** objects. Downstream (`cost-tracker`, UI, compaction) only ever sees Anthropic shapes.
4. New providers are added **declaratively**, not by subclassing: `src/integrations/` uses `defineGateway`/`defineCatalog`/`defineModel` descriptors (`src/integrations/define.ts`) plus a generated manifest (`integrations/generated/integrationManifest.generated.ts`).

So the port for Arcon is: **keep `LLMProvider` for transport, add a normalizer that maps every provider's usage/response into one canonical shape, and make gateways data (descriptors) rather than classes.**

### 4.2 Smart routing — real, heuristic, opt-in

`src/services/api/smartModelRouting.ts` is a **pure function** (documented as "never reads env vars or state directly — caller supplies everything"):

```ts
export function routeModel(input: RoutingInput, config: SmartRoutingConfig): RoutingDecision
// RoutingInput  = { userText, hasNonTextContent?, recentToolUses?, turnNumber? }
// RoutingDecision = { model, complexity: 'simple'|'strong', reason }
```
Ordered escalate-to-strong rules (first match wins, each returns a human-readable `reason`):

| Order | Condition → strong | Note |
| --- | --- | --- |
| 1 | `!config.enabled` / role missing / `simpleModel === strongModel` | safe default |
| 2 | `hasNonTextContent` (image/doc blocks) | |
| 3 | *(empty text → **simple**)* | resuming a tool chain is cheap |
| 4 | `turnNumber === 1` | "first turn is task-setup" |
| 5 | contains code fence or inline backticks | `CODE_FENCE_RE` |
| 6 | matches `STRONG_KEYWORDS` | 24 anchors: plan, design, refactor, debug, investigate, analyze, implement, optimize, review, audit, root cause, "why does", … word-boundary, case-insensitive |
| 7 | multi-paragraph (`/\n\s*\n/`) | |
| 8 | `length > simpleMaxChars` (default **160**) | |
| 9 | `words > simpleMaxWords` (default **28**) | |
| — | else → **simple** | |

Wrapper `decideTurnModel()` in `smartRouting/index.ts` adds the policy layer: resolve config → classify → **enforce org allowlist unconditionally via `isModelAllowed`** (a disallowed routed model is coerced to strong; if strong is also disallowed, routing is **disabled for that session** via a session-id-keyed `Set` capped at 1024 entries, and one notice fires). Decisions are **pinned per user turn**; `shouldDropPinForProviderSwap()` drops a pin if the provider changed mid-turn, because a model-only route is keyed to the endpoint it resolved against.

Default: **off** (`settings.smartRouting.enabled`). Docs (`docs/smart-routing.md`) are unusually candid: the classifier is "not a perfect judge", the failure mode is "no savings on a turn that could have been cheap, never a silently degraded answer", and savings are labeled "first-party reference pricing" because OpenClaude does not know your gateway's real prices.

### 4.3 Escalation, fallback, retry

Three independent mechanisms:

- **Routed-error escalation** (simple→strong): `isRetryableRoutedModelError(err)` — `400/401/403` propagate (a different model won't fix a bad request/auth); **everything else retries on strong, including 404 and 429 by design**. Counted as `escalations` in the tally.
- **Capacity fallback**: `src/services/api/withRetry.ts` counts consecutive `529`s; at `MAX_529_RETRIES = 3` it throws `FallbackTriggeredError(originalModel, fallbackModel)` if a `fallbackModel` is configured. Gated on `FALLBACK_FOR_ALL_PRIMARY_MODELS` or (non-subscriber ∧ non-custom Opus).
- **Retry loop**: `withRetry` is itself an `async function*` yielding `SystemAPIErrorMessage` while retrying. `DEFAULT_MAX_RETRIES = 10` (configurable to 100), `BASE_DELAY_MS = 500`, `MAX_RETRY_DELAY_BASE_MS = 60_000`, plus a `FOREGROUND_529_RETRY_SOURCES` allowlist so background work (titles, summaries, classifiers) **bails immediately** on 529 rather than amplifying a capacity cascade 3–10×. Also: fast-mode rejection permanently disables fast mode and retries; credential caches (`clearAwsCredentialsCache`, etc.) are cleared on auth errors.

### 4.4 Per-agent routing (relevant to Arcon subagents)

`src/services/api/agentRouting.ts` routes *individual agents* to different models/providers:

```ts
export type ProviderOverride = { apiKey; baseURL; ... }
export type AgentModelOnly   = { model: string }
export type AgentRoute       = ProviderOverride | AgentModelOnly
```
Lookup priority in `resolveAgentProvider(name, subagentType, settings)`: **`name` > `subagentType` > `"default"` > null**, keyed through `settings.agentRouting` → `settings.agentModels`, with **normalized keys** (`explore-agent` and `explore_agent` collide → warn, first wins). A full `ProviderOverride` clears ~25 conflicting `CLAUDE_CODE_USE_*` / `*_BASE_URL` env vars before applying (`PROVIDER_ENV_VARS_TO_CLEAR_FOR_OVERRIDE`) — a real lesson about env-var-based provider config being stateful and leaky. Agents can also cap tool steps via `maxSteps` in frontmatter.

### 4.5 Command Code hybrid gateway

`src/integrations/gateways/commandcode.ts` (~204 LOC, added in `5b9daef6`). A descriptor-first OpenAI-compatible **aggregating** gateway at `https://api.commandcode.ai/provider/v1`, dedicated `CMD_API_KEY` (also `COMMANDCODE_API_KEY`/`COMMAND_CODE_API_KEY`), default `deepseek/deepseek-v4-flash`, model catalog auto-discovered from the public `/models` endpoint. "Hybrid" = it aggregates multiple upstream vendors behind one key. Its notable engineering content is **contract enforcement**: `getCommandcodeChatCompletionsModelError()` rejects any model matching `/^(claude-|anthropic\/)/i` or a known alias, because those need the Anthropic Messages protocol, not Chat Completions — enforced at CLI parse time, `/model` picker, profile write time, and request time. The 30+ follow-up fix commits are almost entirely about **credential isolation** (a leftover generic `OPENAI_API_KEY` winning over the dedicated key) — a strong argument for Arcon to keep per-provider credentials in an explicit config object rather than in `os.environ`.

---

## 5. Local LLM support

The most thorough local-model support of any of these subsystems, and directly reusable as a design spec.

**Detection ladder** (`providerConfig.ts`): `isLocalProviderUrl()` (loopback, RFC1918, `.local`, ULA/link-local) → `isLikelyOllamaEndpoint()` (port `11434`, or `ollama` in host/path) → `isDirectLocalOllamaEndpoint()` (strict: `http:` ∧ port 11434 ∧ localhost/`::1`/`127.x`, with bracketed-IPv6 unwrapping).

**Local fast path** — the standout idea. `getLocalFastPathConfig(baseUrl, env)` returns:
```ts
export type LocalFastPathConfig = {
  enabled: boolean
  skipStableStringify: boolean          // skip deterministic JSON hashing (no remote prompt cache to hit)
  skipStrictTools: boolean              // skip additionalProperties:false rewrite (llama.cpp/vLLM don't need it)
  skipToolHistoryCompression: boolean   // skip tool-result tiering (history is in local RAM)
}
```
Rationale in-code: issue #1016 traced client-side overhead as the dominant regression against ~45 tok/s local models — "against a 200ms cloud API the layers are invisible, but against multi-second local round-trips they multiply per-call." Override with `OPENCLAUDE_LOCAL_FAST_PATH=1|0|auto`.

**Endpoint self-healing**: `getLocalProviderRetryBaseUrls(baseUrl)` generates retry candidates — appending `/v1` if missing, and rewriting `localhost`/`::1` → `127.0.0.1` (fixes the classic IPv6-resolution hang).

**Tool-calling support detection / rescue**: `shouldAttemptLocalToollessRetry({baseUrl, hasTools})` retries without tools against a likely-Ollama endpoint. More importantly, when a local model *emits* tool calls as prose instead of structured `tool_calls`, `openaiShim/rawToolCallParsing.ts::parseTextToolCalls()` recovers them: it scans for fenced ```` ```json ```` blocks **and** bare `{"name": ...}` starts, uses `extractBalancedJson()` (brace-depth walk, not regex) to find the object end, dedupes, and returns `toolCallRanges` so `stripRanges()` can excise the JSON from the visible text. Wired into `streamConversion.ts:410` (`isOllamaStream && parseTextToolCalls(...).calls.length > 0`) — i.e. detected at **stream level**, not from a capability table. There's a dedicated test file `openaiShim.ollamaTextToolCalls.test.ts`.

**Native Ollama API**: for Ollama it uses `/api/chat` (`openaiShim/ollamaAdapter.ts`) rather than the OpenAI-compat shim, specifically to pass `num_ctx`; `MIN_RECOMMENDED_OLLAMA_CONTEXT_TOKENS = 32_768` is requested per chat request so same-session history isn't silently truncated. Overridable via `OPENCLAUDE_OLLAMA_NUM_CTX` / `OLLAMA_CONTEXT_LENGTH`. `src/utils/ollamaContext.ts` even **shells out to `ollama ps`** and parses the CONTEXT column (`parseOllamaPsContextWarning`, handling `k`/`m` suffixes) to warn the user their loaded model's window is below the recommended minimum.

**Model discovery**: `src/utils/model/ollamaModels.ts::fetchOllamaModels()` hits `/api/tags` with a 5s `AbortController` timeout, caches into a module-level `cachedOllamaOptions` so the synchronous `/model` picker can read it, and renders `parameter_size · quantization · sizeGB` as the description. Failure returns `[]` — never throws.

**The "explicit overrides beat discovered context windows" fix** (`3451187a`, `src/integrations/runtimeMetadata.ts::resolveModelRuntimeLimits`). Final precedence, high→low:

```
1. exact env override           (e.g. CLAUDE_CODE_OPENAI_<MODEL>_CONTEXT_WINDOW)
2. built-in route catalog       (so `:cloud` variants keep their catalog cap over a broad env *prefix*)
3. env *prefix* override
4. settings.json modelLimits    (explicit user pin)
5. discovery cache              (gateway-advertised context_length)
6. model descriptor default
```
The instructive part is what was **rejected**: the first attempt preferred a larger known descriptor over a generic advertised `128000`, and that was reverted because "a flat 128000 is indistinguishable from a real per-deployment or tenant cap" — the numeric value carries no provenance. Trading an early auto-compact for a late context-window API failure was judged worse. **Discovery stays authoritative over the descriptor; only *explicit user intent* outranks discovery.** Arcon should copy this precedence and this reasoning verbatim (in spirit).

---

## 6. Session & context management

**Persistence:** append-only **JSONL transcripts**, one file per session — `getTranscriptPath()` → `<projectDir>/<sessionId>.jsonl` (`src/utils/sessionStorage.ts`). Subagents get their own `agent-<agentId>.jsonl` plus a sibling `.meta.json` (`AgentMetadata`). `MAX_TRANSCRIPT_READ_BYTES = 50MB`. Deletion is via **tombstone lines + bounded rewrite** (`MAX_TOMBSTONE_REWRITE_BYTES = 50MB`, `TRANSCRIPT_COPY_CHUNK_BYTES = 64KB`) rather than in-place edits. Resume/fork: `--resume <id>`, `--continue`, `--fork-session` (conversation branching only — explicitly *not* filesystem/worktree isolation).

**Context-window resolution:** `getContextWindowForModel(model, sdkBetas, runtimeLimits)` in `src/utils/context.ts` (`MODEL_CONTEXT_WINDOW_DEFAULT = 200_000`), with a session-scoped override map (`setSessionContextWindowOverride`, `/set-context-window`) layered on the §5 precedence.

**Compaction** (`src/services/compact/`) is a **tiered family**, not one function:

| Mechanism | File | What it does |
| --- | --- | --- |
| Auto-compact | `autoCompact.ts` | Full LLM summarization at a token threshold |
| Micro-compact | `microCompact.ts` | Drops old **tool-result** bodies only (`COMPACTABLE_TOOLS` set), replacing with `'[Old tool result content cleared]'` |
| Cached micro-compact | `cachedMicrocompact.ts` | Same via cache-edit API so the prompt cache isn't busted |
| Time-based | `timeBasedMCConfig.ts` | Age-triggered clearing |
| Snip | `snipCompact.ts`, `snipProjection.ts` | Feature-flagged projection-based trimming |
| Session memory | `sessionMemoryCompact.ts` | Persists durable facts before dropping history |

Threshold math is worth porting:
```ts
getEffectiveContextWindowSize(model) = contextWindow − min(maxOutputTokens, 20_000 /* summary reserve */)
                                       // floored at reserve + 13k (AUTOCOMPACT_FLOOR_BUFFER_TOKENS)
getAutoCompactThreshold(model)       = effectiveWindow − clamp(effectiveWindow − 30_000, floor, 30_000)
```
`AUTOCOMPACT_BUFFER_TOKENS = 30_000`, warning/error headroom `20_000` each. The buffer is a **`min`/`max` clamp rather than a constant**, explicitly so the threshold stays monotonic (a one-token window increase must never cause an *earlier* compact) and so warning thresholds can't go negative on mid-sized windows — this was issue #635. Failures use a **circuit breaker**: `MAX_CONSECUTIVE_AUTOCOMPACT_FAILURES = 3`, `AUTOCOMPACT_FAILURE_COOLDOWN_MS = 5min` with a half-open state (`resolveAutoCompactCircuitBreakerState`).

**The async-generator session-context fix** (`0abfca30`). Session/cost state is a process-global `STATE` in `src/bootstrap/state.ts`, scoped per logical session by an async-context wrapper. The bug: `runWithSdkContext(ctx, () => asyncGenerator())` only bound the context during the *creation* of the generator, not during each `next()` resumption — so concurrent SDK sessions leaked each other's session id/cost state across yields. The fix replaced it with two primitives:

```ts
bindSdkContextToAsyncGenerator(sdkContext, generatorInstance)  // re-enters the context on every next()
runOutsideSdkContext(init)                                     // global init must NOT inherit a session's context
```
Applied in both `src/entrypoints/sdk/query.ts` and `sdk/v2.ts`, covered by `tests/sdk/sdk-context-isolation.test.ts` and `query-concurrency.test.ts`. **Direct lesson for Arcon:** if Arcon adopts a global/ambient session or cost object plus `async def`/async generators, use `contextvars` and be aware that a `ContextVar` set outside an async generator does **not** automatically follow it across suspension points — Python's `contextvars` + PEP 568 has the same class of pitfall. Prefer passing an explicit session object into the loop.

---

## 7. Skills system & registry security

### 7.1 Definition

A skill is a **directory containing `SKILL.md`** (`isSkillFile` matches `/^skill\.md$/i`, `src/skills/loadSkillsDir.ts:620`). Crucially, **the skill's invocable name comes from the directory name, not frontmatter** — nested dirs become `:`-namespaces (`a/b/SKILL.md` → `a:b`, `getSkillCommandName`/`buildNamespace` at :659-679); loose markdown in the root `skills/` dir is ignored. Frontmatter (`parseSkillFrontmatterFields`, :222-304) supplies `name`→`displayName`, `description` (falls back to `extractDescriptionFromMarkdown`, with `hasUserSpecifiedDescription` tracked separately), `when_to_use`, `version`, `model`, `effort`, `agent`, `allowed-tools`, `argument-hint`, `arguments`, `disable-model-invocation`, `user-invocable` (default **true**), `hooks` (validated against `HooksSchema()`), `context: fork`, `shell`, and `paths` (gitignore-style patterns for conditional skills). A sidecar `skill.json` carries only `trust` → `skillTrust`.

Skills are `Command` objects of `type: 'prompt'`, built by `createSkillCommand()`. `getPromptForCommand` prefixes `Base directory for this skill: ${baseDir}`, substitutes args, expands `${CLAUDE_SKILL_DIR}`/`${CLAUDE_SESSION_ID}`, and runs inline shell injection — **with one security carve-out**:

```ts
// Security: MCP skills are remote and untrusted — never execute inline
// shell commands (!`…` / ```! … ```) from their markdown body.
if (loadedFrom !== 'mcp') {
  finalContent = await executeShellCommandsInPrompt(...)
}
```

`LoadedFrom = 'commands_DEPRECATED' | 'skills' | 'plugin' | 'managed' | 'bundled' | 'mcp'`. Bundled skills are *code* (`BundledSkillDefinition` in `src/skills/bundledSkills.ts:16-44`, with `files?: Record<string,string>` extracted to disk on first invoke).

### 7.2 Discovery and precedence

`getSkillDirCommands = memoize(async cwd => ...)` (:776-941) merges roots in order **managed/policy → project → `--add-dir` → user → legacy `/commands/`**, then dedups **first-wins by `realpath` identity** — so managed/policy skills win. Within roots, `compareSkillDirPrecedence` puts **deeper paths first**, tie-broken toward `.openclaude` dirs. Policy gates: `isRestrictedToPluginOnly('skills')` disables user+project+legacy+dynamic (org can mandate vetted plugin skills only); `isBareMode()` loads only `--add-dir` paths.

Two mechanisms Arcon should note:
- **Dynamic discovery** walks up from touched files and **refuses gitignored dirs** — `isPathGitignored(currentDir, resolvedCwd)` blocks `node_modules/pkg/.openclaude/skills` from loading silently. The in-code comment is candid that "the invocation-time trust dialog is the actual security boundary."
- **Conditional skills** with `paths` frontmatter are withheld in a `conditionalSkills` map until `activateConditionalSkillsForPaths()` matches a touched file (via the `ignore` library). This is a token-economics feature: a Django skill costs nothing until you open a `.py` file.

### 7.3 Injection — two-stage progressive disclosure

**Stage 1 — names + descriptions only, as a system-reminder.** `src/utils/attachments.ts:~3061` emits `{type: 'skill_listing', content, skillCount, isInitial}`, rendered in `src/utils/messages.ts:2687`:

```ts
case 'skill_listing': {
  return wrapMessagesInSystemReminder([
    createUserMessage({
      content: `The following skills are available for use with the Skill tool:\n\n${attachment.content}`,
      isMeta: true,
    }),
  ])
}
```

Lines are `- <name>: <description> - <whenToUse>`. **Budgeting** (`src/tools/SkillTool/prompt.ts:20-31`) is the part Arcon needs with 34+ skills: `SKILL_BUDGET_CONTEXT_PERCENT = 0.01` of the context window in chars, `DEFAULT_CHAR_BUDGET = 8_000`, `SUBAGENT_SKILL_LISTING_CHAR_BUDGET = 4_000`, per-entry cap `MAX_LISTING_DESC_CHARS = 250`. Degradation ladder: full → per-entry truncation → **names-only**, with bundled skills never truncated. Listings are **deltas** — `sentSkillNames` per `agentId` means only newly-loaded skills are re-announced. Token accounting matches the model: `estimateSkillFrontmatterTokens` counts only name+description+whenToUse "since full content is only loaded on invocation".

**Stage 2 — body loaded on invoke.** `SkillTool` (`src/tools/SkillTool/SkillTool.ts:331`), input `{skill: string, args?: string}`. Its prompt is unusually forceful: *"this is a BLOCKING REQUIREMENT: invoke the relevant Skill tool BEFORE generating any other response"*, *"NEVER mention a skill without actually calling this tool"*. Output is a union of `inlineOutputSchema` and `forkedOutputSchema` — `context: fork` skills run in a **subagent** and return only the result, which is a direct pattern for Arcon's automated subagent spawning. Post-compact, the listing is deliberately dropped and reset (`services/compact/compact.ts:222,573`).

> `src/services/skillSearch/*` and `DiscoverSkillsTool` are **stubs in this snapshot** ("skillSearch not included in source snapshot (feature-gated)"), behind `feature('EXPERIMENTAL_SKILL_SEARCH')`. So semantic skill search is *designed* (shrink the static listing to bundled+MCP, search for the rest) but not readable here. My earlier assumption that `@orama/orama` backs skill search is **not verifiable** from this snapshot.

### 7.4 Registry install pipeline

CLI: `openclaude skills list|show|validate|install|remove` (`src/cli/handlers/skillsCli.ts`), flags `--registry`, `--sha256`, `--global`, `--force`. Registry resolution: `--registry` → `OPENCLAUDE_SKILLS_REGISTRY_URL` → default `https://raw.githubusercontent.com/Gitlawb/openclaude-skills/main/registry.json`. Entries (`SkillRegistryEntry`) carry `id, name, title, description, trust, version, license, source, repo, path, sha256, min_openclaude_version, tools_required, category, tags, author`. Remote reads are bounded: `REMOTE_SOURCE_TIMEOUT_MS = 30_000`, `MAX_REMOTE_SOURCE_BYTES = 1 MiB` (checked via both `content-length` **and** streaming byte count), schemes limited to `http:/https:/file:`.

**Install order** (`prepareInstallCandidate`, `src/cli/handlers/skillsInstall.ts:688-727`) — note revocations are checked *before* the body is even downloaded:

1. `requireRegistrySha256` — no pinned digest ⇒ `Refusing to install an unpinned skill.`
2. `assertCompatibleOpenClaudeVersion` — semver `min_openclaude_version`
3. `readRevocations(registrySource)` → **`assertNotRevoked(...)`**
4. fetch `entry.source`, then `assertSha256Matches(markdown, expectedSha256, spec)`
5. stage into a `mkdtemp` dir, write `SKILL.md` + generated `skill.json`
6. `validateSkillPath(tempDir, {requireRegistryMetadata})`, refuse to clobber without `--force`, print trust warning, `fs.cp` into `installRoot()`, `rm -rf` temp in `finally`

### 7.5 `revocations.json` — the kill switch

```ts
type SkillRevocation = {
  id?: unknown; version?: unknown; sha256?: unknown; reason?: unknown
}
```

A JSON **array** of these. `parseRevocation` (:235-275) requires `sha256` to match `/^[a-fA-F0-9]{64}$/` if present and enforces that each entry **"must pin at least an id or a sha256"** — an entry with neither matches nothing. Location: `OPENCLAUDE_SKILLS_REVOCATIONS_URL` env override, else a `revocations.json` **sibling of the registry** (URL-relative or `resolve(dirname(registrySource), ...)`).

**Matching** (`revocationApplies`, :398-424) is conjunctive over *specified* fields — three useful granularities:

| Entry | Revokes |
| --- | --- |
| `{id}` | all versions of that registry id |
| `{id, version}` | that one release |
| `{sha256}` | that exact content under **any** id — defeats republication under a new name |

**Fail-closed is the key design decision** (`readRevocations`, :282-308): only a *confirmed absence* (local `ENOENT` or HTTP **404**) returns `[]`. Any other read failure, non-JSON, or non-array **throws and aborts the install**. The comment states the threat directly: *"an unreachable kill switch must not read as an empty one."* An attacker who can block or poison the revocations fetch would otherwise get a free bypass. On match: `Skill "<spec>" is revoked in the registry. Refusing to install.` + optional reason → `exitCode = 1`, temp dir removed, nothing lands on disk. Tests (`src/cli/handlers/skills.test.ts:696-830`) cover revoke-by-id+version, revoke-by-digest-alone, and malformed-JSON-aborts, plus a negative case (revocation for `0.0.9` still allows `0.1.0`).

### 7.6 Integrity — hashing, no signatures

```ts
function sha256OfSkillSource(text: string): string {
  const normalized = text.replace(/\r\n/g, '\n')   // stable across platforms
  return createHash('sha256').update(normalized, 'utf8').digest('hex')
}
```
`assertSha256Matches` reports both expected and actual on mismatch. **There is no signature/keyring/provenance verification** — only SHA-256 pinning. Scope limits: the digest covers **only `SKILL.md`** (registry installs materialize just that file plus generated metadata, so there is no multi-file manifest to verify), and **local-directory installs are unverified** (recursive `fs.cp`, `trust: 'local'`). Direct `http(s)://` installs *require* `--sha256` but **bypass revocations entirely** — revocations apply only to registry-resolved installs.

Complementary content validation (`src/cli/handlers/skillsValidation.ts`): `REQUIRED_METADATA` (`name,title,description,version,category,author,license,trust`), `VALID_SKILL_NAME` regex, **no symlinks**, no binaries (NUL byte in first 4096 bytes), `UNSAFE_FILE_NAMES` (package.json, lockfiles — closes the dependency-install escape hatch), 1 MiB per-text-file cap, and `UNSAFE_TEXT_PATTERNS` flagging `curl … | sh`, `base64 … | sh|node|python`, `rm -rf /|$HOME|~|*`, embedded credential-like values, and credential-collection instructions.

### 7.7 Threat model

A `SKILL.md` is effectively **remote code**: it injects instructions into the agent's context, can pre-approve tools via `allowed-tools`, can register `hooks`, and (for non-MCP skills) can execute inline shell during prompt expansion. The chain **require-digest → check-revocations → verify-digest → validate-content** addresses distinct threats:

- **SHA-256 pinning** defeats tampering in transit and silent content swaps at a stable URL (compromised CDN, poisoned raw-GitHub path, MITM). Identity is content-based, not URL-trust-based.
- **`revocations.json`** covers what pinning cannot: content that was *legitimately published and correctly pinned* and later found malicious. Digest-level revocation is what makes it robust against republication.
- **Fail-closed** removes the network-suppression bypass.
- **Content validation + trust tiers + no-symlinks/binaries/lockfiles** bound the blast radius of anything that does pass.
- **Discovery-side** defenses target a different vector — skills smuggled in via a cloned repo or a dependency (gitignored-dir skip, MCP bodies never shell-execute, plugin-only lockdown).

**Residual gap Arcon should close:** revocations are consulted on **install only**. Already-installed skills are never re-validated, so a revocation published after install is inert until reinstall. Arcon should check revocations (and re-verify digests) **on load** as well as install.

---

## 8. Tools & permissions

### 8.1 The `Tool` type — and a correction

`src/Tool.ts` (827 LOC). It is a **generic object type alias, not an interface**, and tools are **not** classes:

```ts
export type Tool<
  Input extends AnyObject = AnyObject,   // AnyObject = z.ZodType<{[key:string]: unknown}>, zod/v4
  Output = unknown,
  P extends ToolProgressData = ToolProgressData,
> = { ... }
export type Tools = readonly Tool[]
```

**Important correction to a common assumption (including my own initial read): `call()` is NOT an async generator.** It returns a plain Promise and delivers progress through a callback:

```ts
call(
  args: z.infer<Input>,
  context: ToolUseContext,
  canUseTool: CanUseToolFn,
  parentMessage: AssistantMessage,
  onProgress?: ToolCallProgress<P>,
): Promise<ToolResult<Output>>
```
Async generators appear one layer *up*, in the hook/execution layer (`runPreToolUseHooks`, `runPostToolUseHooks` in `src/services/tools/toolHooks.ts` are `export async function*`). For Arcon: `async def call(...) -> ToolResult` **plus** an `on_progress` callback is a simpler Python port than an async generator, and keeps the yield-vs-return contract unambiguous.

**Behavior predicates** — the scheduling metadata worth porting wholesale:
```ts
isConcurrencySafe(input): boolean
isReadOnly(input): boolean
isDestructive?(input): boolean          // "Only set when the tool performs irreversible operations"
interruptBehavior?(): 'cancel' | 'block'   // defaults to 'block'
isOpenWorld?(input): boolean
requiresUserInteraction?(): boolean
```
BashTool derives one from the other: `isConcurrencySafe(input) { return this.isReadOnly?.(input) ?? false }`.

**Construction defaults fail closed** — `buildTool(def)` spreads `TOOL_DEFAULTS` under the definition, and every risk-bearing default is the safe value: `isConcurrencySafe: () => false`, `isReadOnly: () => false`, `isDestructive: () => false`, `checkPermissions: → {behavior:'allow', updatedInput}` (safe because the *pipeline* gates, not the tool). Arcon should mirror this: a tool that forgets to declare read-only-ness must be treated as mutating.

**Schema/metadata extras:** `inputJSONSchema?` (raw JSON Schema for MCP tools that don't use Zod), `outputSchema?`, lazy schema getters (`get inputSchema() { return inputSchema() }`) for startup time, `searchHint?`, `shouldDefer?` / `alwaysLoad?` (tool-search deferral), `maxResultSizeChars` (`Infinity` for Read, to avoid a Read→file→Read loop), `aliases?`. Permission surface on the tool itself: `validateInput?`, `checkPermissions`, `preparePermissionMatcher?`, `backfillObservableInput?` (mutates a **copy** so hooks/transcript see derived fields without busting the prompt cache on the API-bound input), `toAutoClassifierInput`.

**Renderers** are React nodes on the tool: `renderToolUseMessage` (takes `Partial<Input>` because it renders while args still stream in), `renderToolResultMessage?`, `renderToolUseProgressMessage?`, `renderToolUseRejectedMessage?`, `renderGroupedToolUse?` (groups parallel calls), `getActivityDescription?` ("Reading src/foo.ts"), and `extractSearchText?` for transcript search indexing.

### 8.2 Built-ins and assembly

~55 dirs under `src/tools/`. **Unconditionally core** (statically imported in `getAllBaseTools()`): `AgentTool`, `TaskOutputTool`, `BashTool`, `RepoMapTool`, `ExitPlanModeV2Tool`, `FileReadTool`, `FileEditTool`, `FileWriteTool`, `NotebookEditTool`, `WebFetchTool`, `TodoWriteTool`, `WebSearchTool`, `TaskStopTool`, `AskUserQuestionTool`, `SkillTool`, `EnterPlanModeTool`, `LSPTool`, `BriefTool`, `ListMcpResourcesTool`, `ReadMcpResourceTool`. `GlobTool`+`GrepTool` are conditional on `!hasEmbeddedSearchTools()`. Everything else is `feature()`-gated and dead-code-eliminated at build (worktrees, teams/swarms, cron, monitor, PowerShell, workflow scripts, ToolSearch…). `--bare` reduces to `[BashTool, FileReadTool, FileEditTool]`.

Two constraints in `assembleToolPool` that Arcon will eventually hit:
> "Sort each partition for prompt-cache stability, keeping built-ins as a contiguous prefix. The server's cache policy places a global cache breakpoint after the last prefix-matched built-in tool; a flat sort would interleave MCP tools into built-ins and invalidate all downstream cache keys."

i.e. **tool ordering is part of your cache key** — unstable tool ordering silently destroys prompt-cache hit rate, which is a direct token-economics concern. Deny rules also filter tools *before the model sees them* (`filterToolsByDenyRules`), not just at call time.

### 8.3 Permission modes

```ts
export const EXTERNAL_PERMISSION_MODES = [
  'acceptEdits', 'bypassPermissions', 'default', 'dontAsk', 'fullAccess', 'plan',
] as const
export type InternalPermissionMode = ExternalPermissionMode | 'auto' | 'bubble'
```
`'auto'` is gated behind `feature('TRANSCRIPT_CLASSIFIER')`; `'bubble'` is typecheck-only. Semantics: `default` (rule-driven, prompt otherwise), `acceptEdits` (auto-allow in-workdir edits), `plan` (mechanical read-only enforcement), `dontAsk` (every `ask` → `deny`), `bypassPermissions` (allow, but safety checks still bind), `fullAccess` (the "explicit second-level opt-in" that *also* skips safety checks), `auto` (LLM classifier replaces the prompt).

### 8.4 Rule model and matching

Three parallel buckets, each keyed by source: `alwaysAllowRules` / `alwaysDenyRules` / `alwaysAskRules`, all `{ [T in PermissionRuleSource]?: string[] }` with `PermissionRuleSource = 'userSettings'|'projectSettings'|'localSettings'|'flagSettings'|'policySettings'|'cliArg'|'command'|'session'` in fixed precedence order. Syntax is `"ToolName"` or `"ToolName(content)"`; `Bash` is blanket, `Bash(npm install)` is content-specific, `Bash()`/`Bash(*)` collapse to blanket. Parens inside content are escaped (`escapeRuleContent('psycopg2.connect()')` → `'psycopg2.connect\\(\\)'`), with `findFirstUnescapedChar`/`findLastUnescapedChar` counting backslash parity. MCP server-level rules work: `mcp__server1` or `mcp__server1__*` matches every tool from that server. Legacy names are normalized with the same prototype-pollution guard seen in the cost layer (`Object.hasOwn(LEGACY_TOOL_NAME_ALIASES, name)` — a rule literally named `constructor` would otherwise return an inherited function).

### 8.5 The decision pipeline

`hasPermissionsToUseTool` (the exported `CanUseToolFn`) → `hasPermissionsToUseToolWithModeHandling` → `hasPermissionsToUseToolInner` (`src/utils/permissions/permissions.ts`, 1,898 LOC). The inner function is explicitly step-numbered in comments:

| Step | Check |
| --- | --- |
| 1a | blanket **deny** rule → deny |
| 1b | blanket **ask** rule → ask (unless sandbox auto-allow / `fullAccess` / `plan`) |
| 1c | `inputSchema.parse(input)` then `tool.checkPermissions(...)` |
| 1d | tool-level **deny** wins |
| — | `checkPlanModePermissions(...)`; deferred blanket-ask re-fires after plan policy |
| 1e | `requiresUserInteraction()` + tool said ask → ask (**survives bypass**) |
| 1f | content-specific ask rules **beat `bypassPermissions`** |
| 1g | `safetyCheck` asks are **bypass-immune** (`.git/`, `.claude/`, `.vscode/`, shell configs) |
| 2a | `bypassPermissions`/`fullAccess` → allow |
| 2b | tool-always-allowed rule → allow |
| 3 | `'passthrough'` (tool has no opinion) → ask |

Results are a discriminated union `allow | ask | deny | passthrough`, each carrying a 12-arm `PermissionDecisionReason` (`rule`, `mode`, `subcommandResults`, `hook`, `sandboxOverride`, `classifier`, `safetyCheck` with `classifierApprovable: boolean`, …) used for UI copy, analytics, and re-decision. Mode transforms are applied **at the end, in the wrapper, "so it can't be bypassed by early returns"** — a structural lesson worth copying.

Auto mode is where the cost note lives: before spending a classifier call it runs an **`acceptEdits` fast-path probe** (re-invoking `tool.checkPermissions` with a spoofed context), deliberately skipped for AgentTool and REPLTool because "REPL code can contain VM escapes between inner tool calls; the classifier must see the glue JavaScript." Denial limits (`DENIAL_LIMITS.maxTotal`/consecutive) abort headless runs with `AbortError('Agent aborted: too many classifier denials in headless mode')`. And per `permissions.ts:848`, the classifier "does NOT call `addToTotalSessionCost`, so classifier tokens are excluded" from billing — a deliberate accounting choice Arcon should make consciously rather than inherit.

**Sandbox** (`SandboxManager`, `src/utils/sandbox/sandbox-adapter.ts`, wrapping `@anthropic-ai/sandbox-runtime`) hooks in at step 1b: a sandboxed Bash command may skip a blanket ask rule via `isSandboxingEnabled() && isAutoAllowBashIfSandboxedEnabled() && shouldUseSandbox(input)`. Escapes are recorded as `sandboxOverride: 'excludedCommand' | 'dangerouslyDisableSandbox'` and rendered as "Run outside of the sandbox."

**Hooks: 27 events** (`src/entrypoints/sdk/coreTypes.ts:25`) — `PreToolUse, PostToolUse, PostToolUseFailure, Notification, UserPromptSubmit, SessionStart, SessionEnd, Stop, StopFailure, SubagentStart, SubagentStop, PreCompact, PostCompact, PermissionRequest, PermissionDenied, Setup, TeammateIdle, TaskCreated, TaskCompleted, Elicitation, ElicitationResult, ConfigChange, WorktreeCreate, WorktreeRemove, InstructionsLoaded, CwdChanged, FileChanged`. `runPreToolUseHooks` yields `hookPermissionResult` / `hookUpdatedInput` / `preventContinuation` / `stop`, and `resolveHookPermissionDecision` reconciles the hook verdict with `canUseTool` — including the case where a hook satisfies an interactive tool's requirement by supplying `updatedInput`.

---

## 9. CLI/TUI implementation

**Two-stage entry, split for startup latency.** `src/entrypoints/cli.tsx` (827 LOC) is **not** the arg parser — it is a fast-path dispatcher that self-executes at module scope and deliberately avoids loading commander. It hand-rolls a flag scanner (`SKILLS_LEADING_BOOLEAN_FLAGS`, `_VALUE_FLAGS`, `_OPTIONAL_VALUE_FLAGS`, `_MULTI_VALUE_FLAGS`) to detect a `skills` subcommand, then `await import(...)`s only what a given invocation needs (`--dump-system-prompt`, chrome/computer-use MCP, daemon worker, remote-control, environment-runner, …), each wrapped in `profileCheckpoint('cli_..._path')`. Notable: `process.env.CLAUDE_CODE_DISABLE_EXPERIMENTAL_BETAS ??= 'true'` — OpenClaude disables tool-search/defer_loading and global-cache betas because they 500 on external accounts.

**Real arg parsing is `src/main.tsx` (4,475 LOC)** using **`@commander-js/extra-typings` 12.1.0**, with `.enablePositionalOptions()` plus root-flag pre-parsing so `openclaude -p "explain assistant"` isn't mistaken for the `assistant` subcommand; `--permission-mode` uses `.choices(PERMISSION_MODES)`. `src/replLauncher.tsx` is 22 lines of pure lazy import (`App` + `REPL`).

**The TUI is a heavily extended Ink fork — confirmed.** `package.json` has **no `ink` dependency**; it has `react` 19.2.4 + `react-reconciler` 0.33.0. `src/ink/` (~70 files) is a full renderer (`reconciler.ts` importing `react-reconciler`, `dom.ts`, `renderer.ts`, `output.ts`, `log-update.ts`, plus `components/Box.tsx`/`Text.tsx`/`Link.tsx`/…), with a leftover upstream reference (`// See https://github.com/vadimdemedes/ink/issues/384`). Extensions well beyond upstream Ink:
- **Own layout engine** `src/ink/layout/{engine,geometry,node,yoga}.ts` against a native Yoga binding in `src/native-ts/yoga-layout/`.
- **Own terminal I/O** `src/ink/termio/{ansi,csi,dec,esc,osc,sgr,tokenize,parser}.ts` — alt-screen, Kitty keyboard protocol, `modifyOtherKeys`, mouse tracking, OSC 52 clipboard, iTerm2 progress.
- **Cell-level virtual screen + diffing** — `screen.ts` (`Cell`, `CharPool`, `StylePool`, `HyperlinkPool`, `diffEach`, `shiftRows`), `log-update.ts` (`class LogUpdate`, `class VirtualScreen`).
- Features Ink lacks: `selection.ts` (mouse text selection, URL detection), `hit-test.ts` (`dispatchClick`/`dispatchHover`), a DOM-like `events/` model, `ScrollBox`, `bidi.ts`, `tabstops.ts`, `searchHighlight.ts`.
- `src/ink.ts` re-exports **themed** `Box`/`Text` from the design system instead of Ink's ("Ink itself is theme-agnostic").

**Streaming render: diff-based, throttled to ~60fps.** `FRAME_INTERVAL_MS = 16`; `scheduleRender = throttle(() => queueMicrotask(this.onRender), FRAME_INTERVAL_MS)` driven off the reconciler's `resetAfterCommit` (microtask defer so it runs after layout; tests bypass via `onImmediateRender`). Each frame: Yoga `calculateLayout(terminalColumns)` → `renderNodeToOutput` → styled-cell `Screen` → `optimize()` → `LogUpdate` diffs against `previousOutput` → minimal patch list. Optimizations include partial main-screen rewrites (`rewriteMainScreenFrame`/`rowsEqual`), **CSI scroll-region ops instead of redrawing scrolled content**, style/hyperlink transition diffing via `@alcalzone/ansi-tokenize`, a 4ms catch-up drain timer for fast streaming, and a pointedly-named fallback `fullResetSequence_CAUSES_FLICKER`. Overlays (search highlight, selection) composite onto the buffer *after* layout — which is why `Tool.extractSearchText` must match rendered text exactly.

**Slash commands: ~190 entries** in `src/commands/`, three kinds (`src/types/command.ts`):
- `PromptCommand` (`type: 'prompt'`) — expands into the conversation; this is what skills are.
- `LocalCommand` (`type: 'local'`) — `call(args, context)`, with **lazy `load: () => import('./cost.js')`** to protect startup.
- `LocalJSXCommand` (`type: 'local-jsx'`) — `call(onDone, context, args)` returning a full interactive Ink component, mounted via `ToolUseContext.setToolJSX`.

Shared metadata includes a distinction Arcon should copy verbatim:
> `availability` = who can use this (auth/provider requirement, **static**); `isEnabled()` = is this turned on right now (flags, platform, env vars)

`COMMANDS = memoize(() => [...])` is a function specifically because "underlying functions read from config, which can't be read at module initialization time" — and cache invalidation is layered (`clearCommandMemoizationCaches()` must also call `clearSkillIndexCache()`, since the skill index memoizes *on top*; "clearing only the inner caches is a no-op for the outer").

### The UI answer for Arcon: there is no GUI — but there *is* a protocol

- `web/` is an **Astro 6.4.6 static marketing + docs site** (`site: 'https://openclaude.gitlawb.com'`, plain CSS, no client framework, own lockfile, **zero imports from `src/`**). Its docs pages are driven by hand-maintained TS data files (`src/data/{cliFlags,commands,configuration,keybindings,skills,providers}.ts`) that mirror the CLI surface. Not an app UI.
- `vscode-extension/openclaude-vscode/` is **plain CommonJS JavaScript** (no TS, no bundler, no webview framework) — and critically, **it does not reimplement the agent**. Per `src/chat/protocol.js`:
  > "The extension spawns `openclaude --print --input-format=stream-json --output-format=stream-json` and speaks NDJSON over stdin/stdout."

  It declares the wire message types (`assistant`, `user`, `result`, `system`, `stream_event`, `partial`, `compact_boundary`, `status`, `api_retry`, `tool_progress`, `hook_started/progress/response`, `task_notification`, …), handles permission prompts over the same channel (`permissionResponse.js`), and surfaces edits in the editor (`diffController.js`).

**This is the single most reusable architectural idea for Arcon's dual CLI+UI requirement**, and it does not depend on TypeScript at all: the agent core emits **one typed NDJSON message stream**, and every surface — TUI, `--print`, VS Code, gRPC (`src/grpc/`, `docs/grpc-server.md`), the SDK (`dist/sdk.mjs`), MCP server (`src/entrypoints/mcp.ts`), background sessions (`src/cli/bg.ts`) — is a *client* of that stream. Arcon should define that event schema (Pydantic models + NDJSON) **before** building either UI, then implement the Textual/Rich TUI and the web UI as two independent subscribers. Do **not** copy the Ink fork.

---

## 10. Cross-platform story

| Concern | Reality |
| --- | --- |
| Install | `npm install -g @gitlawb/openclaude` (Node ≥22). Community AUR package for Arch. |
| Runtime | **Node ≥22 to run**; **Bun 1.3.13 only to build/test**. |
| Packaging | `files` ships `bin/`, `dist/cli.mjs`, `dist/sdk.mjs`, SDK `.d.ts`, a PowerShell alias script, and a `node-domexception-shim` vendored under `vendor/`. |
| External deps | `ripgrep` bundled via `@vscode/ripgrep`, but the CLI still warns "ripgrep not found" and asks for a system install; `git` is required for repo-map and worktrees. |
| Windows | First-class-ish: dedicated `PowerShellTool`, `scripts/windows/openclaude-aliases.ps1`, `docs/windows-aliases-and-launchers.md`, `docs/quick-start-windows.md`, all setup docs give PowerShell `$env:` variants. `process.platform === 'win32'` branches in ~54 source files. Known gap documented: POSIX signal names are not inferred on Windows for background sessions. |
| macOS/Linux | `docs/quick-start-mac-linux.md`; Debian-based Docker image (`node:22-slim` + `git` + `ripgrep`, runs as non-root `node`). No RPM/RedHat-specific packaging. |
| Android | `ANDROID_INSTALL.md` — Termux + `proot-distro` Ubuntu, because Bun has no native Android build. |
| Doctor | `scripts/system-check.ts` (`doctor:runtime`, `--json`, `--out`) for runtime diagnostics. |

Arcon (Python) has a structurally easier story here — but note the pattern of a **`doctor` command emitting machine-readable JSON**, and of shipping ripgrep as a dependency rather than assuming it.

---

## 11. What Arcon should adopt

**These are pattern ports, not code ports.** OpenClaude is TypeScript and legally encumbered (§1); Arcon is Python. Translate the data models and algorithms, write the code fresh.

| # | Port | Onto Arcon's real code | Effort |
| --- | --- | --- | --- |
| **P0** | **Tiered pricing table + 5-field cost model.** Replace `LLMProvider.get_cost_per_token(model) -> (in, out)` — a 2-tuple **cannot express cache-read/cache-write/web-search pricing** and will silently under-report by 2–10× on cached workloads. Define `@dataclass(frozen=True) ModelCosts(input_per_1m, output_per_1m, cache_write_per_1m, cache_read_per_1m, web_search_per_req)`, shared `COST_TIER_*` constants, and a `MODEL_COSTS: dict[str, ModelCosts]` keyed on a **canonicalized** model name. Keep `get_cost_per_token` as a thin back-compat shim. | new `src/arcon/core/pricing.py`; amend `providers/base.py` + all three providers | **1–2 days** |
| **P0** | **Actually populate the token columns.** Arcon's schema is already right (`sessions.total_input_tokens/total_output_tokens/total_cost`, `messages.input_tokens/output_tokens/cost`) but the chat loop never writes them, so cost always reads 0. Add a single `add_to_session_cost(cost, usage, model)` chokepoint called from the one place provider responses are consumed, mirroring `addToTotalSessionCost`. Add `cache_read_tokens`/`cache_write_tokens` columns while you're touching the schema. | `src/arcon/cli/chat.py`, `src/arcon/storage/`, `core/session.py` | **1 day** |
| **P0** | **Normalize provider usage into one canonical shape at the shim boundary**, exactly as `cacheMetrics.ts` documents. Arcon has three providers with three usage shapes; normalize once (Anthropic: `cache_read_input_tokens`; OpenAI: `prompt_tokens_details.cached_tokens`; Ollama: `prompt_eval_count`/`eval_count`) so pricing, display, and compaction see one type. Include the **honest-N/A rule**: Ollama reports no cache data → `supported=False`, render "N/A", never a fabricated 0%. | `providers/*.py` → new `core/usage.py` | **1–2 days** |
| **P1** | **Unknown-model policy + user pricing overrides.** Unknown model → a documented default tier **plus** a `has_unknown_model_cost` flag that makes `/cost` say so. Add `model_pricing` overrides readable only from **user/local** config, never from project/repo config (the `TRUSTED_MODEL_PRICING_SOURCES` rule) — otherwise a cloned repo can rewrite the user's spend numbers. Critically: **Ollama returning `(0.0, 0.0)` is a lie for a machine you paid for**; either report `None`/N-A or let the user set an electricity/amortization rate via the override path. | `core/pricing.py`, `config/manager.py` | **1 day** |
| **P1** | **`routeModel()` verbatim as an algorithm.** Arcon's `ProviderResolver` is a dict factory with **zero routing logic**. Port the pure classifier as `route_model(input: RoutingInput, config: RoutingConfig) -> RoutingDecision` with the 9 ordered rules, the `STRONG_KEYWORDS` list, the 160-char/28-word defaults, and the always-return-a-`reason` contract. Keep it a **pure function** that reads no env/global state, and keep it **off by default**. Then add the policy wrapper: pin per turn, enforce an allowlist, disable-per-session on conflict. This is the single highest-leverage feature for Arcon's local-LLM story: route trivial turns to `qwen2.5-coder:1.5b` locally, hard turns to Sonnet. | new `src/arcon/core/routing.py`; wire into `providers/resolver.py` (rename to a real router) | **2–3 days** |
| **P1** | **Escalation taxonomy.** Three separate concepts, don't conflate them: (a) routed-error escalation simple→strong where **400/401/403 propagate and everything else — including 404/429 — retries on strong**; (b) capacity fallback after N consecutive overloads; (c) the retry loop itself with exponential backoff and a **foreground-only** retry allowlist so background summarizers don't amplify an outage. | new `core/retry.py` | **2 days** |
| **P1** | **Context-window precedence.** Adopt the §5 ladder exactly: exact-env > builtin-catalog > env-prefix > user-config pin > **discovered** > descriptor-default, and adopt the *rationale* that a gateway-advertised number has no provenance so only explicit user intent may outrank it. Arcon needs this the moment it talks to Ollama or any gateway. | `core/types.py` + new `core/model_limits.py` | **1 day** |
| **P2** | **Local fast path.** `LocalFastPathConfig` — when the base URL is loopback/RFC1918, skip deterministic-JSON hashing, strict tool-schema rewriting, and tool-history compression. Against multi-second local round-trips these layers dominate. Also port `get_local_provider_retry_base_urls` (append `/v1`; `localhost`→`127.0.0.1`). | `providers/ollama.py` | **1–2 days** |
| **P2** | **Text tool-call rescue for local models.** `parse_text_tool_calls()` with a **brace-depth balanced-JSON walk** (not regex), fenced + bare detection, dedupe, and returned ranges so the JSON can be stripped from displayed text. Detect at **stream level** (did this response contain a parseable call?) rather than from a static capability table — small local models are inconsistent turn to turn. Plus `num_ctx=32768` on every Ollama request and the `ollama ps` context warning. | `providers/ollama.py` | **2–3 days** |
| **P2** | **Tiered compaction + monotonic thresholds.** Don't jump straight to LLM summarization. Add micro-compaction first (drop old tool-result bodies, replace with a marker) — it's cheap, needs no model call, and recovers most tokens. Port the clamped-buffer threshold formula (so a window increase can never trigger an *earlier* compact) and the 3-strike failure circuit breaker with cooldown. | new `services/compact/` | **3–4 days** |
| **P2** | **Per-agent routing for subagent spawning.** `agent_routing` (name > subagent_type > "default") → `agent_models`, with **normalized keys** and a duplicate-collision warning, plus `max_steps` in agent frontmatter. Arcon's 5 YAML agents can immediately gain per-agent model assignment — cheap local model for search agents, strong cloud model for the planner. | `agents/registry.py`, `agents/loader.py` | **2 days** |
| **P2** | **USD budget ceiling.** `max_budget_usd` checked between turns, terminating with a structured `error_max_budget_usd` result. Trivial once P0 lands, and a genuine differentiator. | `core/session.py`, `cli/chat.py` | **half day** |
| **P3** | **Repo map = Arcon's "graphify", already specified.** `docs/repo-map.md` describes exactly what Arcon wants: `git ls-files --cached --others --exclude-standard` → tree-sitter symbol extraction → directed reference graph with edges weighted by **reference count × IDF of the symbol name** (so `get`/`value` contribute less) → **PageRank** → render top-down until a token budget is hit, with an on-disk cache keyed by (path, mtime, size). Python has `tree_sitter` and `networkx`; this is a near-direct port and their Python grammar support already exists. | new `src/arcon/graph/` | **1 week** |
| **P1** | **One NDJSON event stream, many surfaces.** The answer to Arcon's "CLI *and* a UI" requirement (§9). Define the message schema as Pydantic models (`assistant`, `user`, `result`, `system`, `stream_event`, `partial`, `compact_boundary`, `status`, `tool_progress`, `permission_request`, …) and have the agent core emit only that. Then TUI, `--print`, and web UI are all subscribers, and permission prompts travel over the same channel. **Do this before writing either UI** — retrofitting is far more expensive. | new `core/events.py`; refactor `cli/chat.py` to consume | **3–4 days** |
| **P2** | **Skill listing budget + delta announcement.** With 34+ skills Arcon will burn real context on the listing alone. Port: budget = `max(1% of context window, 8000 chars)`, per-entry description cap **250 chars**, degradation ladder full→truncate→**names-only**, subagent budget **4000**, and **only announce newly-loaded skills** (`sent_skill_names` per agent id). Plus **conditional skills** via `paths` frontmatter — a skill costs zero tokens until a matching file is touched. | `skills/loader.py`, new `skills/listing.py` | **2 days** |
| **P2** | **Tool metadata for safe parallelism + cache stability.** Port `is_read_only` / `is_concurrency_safe` / `is_destructive` with **fail-closed defaults** (unset ⇒ mutating, unset ⇒ not concurrency-safe), letting Arcon run independent reads in parallel. And keep **tool ordering stable** (builtins as a contiguous sorted prefix, MCP/dynamic tools after) — unstable ordering silently destroys prompt-cache hit rate, which directly harms the token-economics numbers Arcon wants to report. | `tools/` | **1–2 days** |
| **P3** | **Descriptor-driven providers.** Make gateways **data** (`define_gateway`-style dataclasses + a discovery cache) rather than `LLMProvider` subclasses — that's how OpenClaude supports ~20 gateways without 20 classes. | `providers/`, `core/interface.py` | **4–5 days** |
| **P3** | **Registry security chain, if Arcon ships a skill registry.** Port the whole ordered chain: require a pinned SHA-256 (CRLF-normalized so digests are stable across Windows/Linux) → check revocations **before download** → verify digest → validate content. Copy the three revocation granularities (`{id}`, `{id,version}`, `{sha256}`-alone to defeat republication), the "must pin at least an id or a sha256" rule, and above all **fail closed**: only `ENOENT`/HTTP-404 means "no revocations"; any other fetch/parse failure aborts the install. Then **improve on it**: check revocations on **load** too, not just install (§7.7). Also port the content validators (no symlinks, no NUL-byte binaries, no lockfiles/package.json, `curl|sh` pattern flagging). | `skills/loader.py`, new `skills/registry.py` | **3–4 days** |

Suggested order: **P0 block first** (cost is broken today and is a 3-day fix), then routing (P1), then local-LLM hardening (P2), then graphify (P3).

---

## 12. What Arcon should NOT copy / caveats

1. **Do not copy code. Any code.** `LICENSE` states the repo derives from proprietary Claude Code without Anthropic's authorization and that only *modifications* are MIT — and the boundary between "derived" and "modification" is not marked in-tree. Read for patterns, write fresh Python. Do not vendor, transpile, or paste. Do not cite it as an upstream in Arcon's docs.
2. **Anthropic-shape-as-canonical is a defensible choice with a real cost.** OpenClaude normalizes every provider into `BetaUsage` from `@anthropic-ai/sdk` and imports Anthropic SDK types into `cost-tracker.ts` at the type level. That gave them one internal shape, but it hard-couples their cost layer to one vendor's evolving type and forces shim gymnastics (`thinkTagSanitizer`, `openaiSchemaSanitizer`, `markerEchoGuard`, `SYNTHETIC_OUTPUT_TOOL_NAME`). Arcon should define its **own** neutral `Usage`/`Message` dataclasses and map *into* them — same benefit, no vendor coupling.
3. **Don't inherit the process-global mutable `STATE`.** `bootstrap/state.ts` is a module-level singleton for session id, cost, and usage; the `0abfca30` fix exists precisely because that global leaked across concurrent async generators. Arcon should pass an explicit `Session`/`CostLedger` object through the loop. If Arcon uses `contextvars` for ambient state, know that the same async-generator suspension pitfall applies in Python.
4. **Don't copy env-vars-as-config.** Provider selection here is env-var-driven (`CLAUDE_CODE_USE_OPENAI`, `OPENAI_BASE_URL`, …), which is why `agentRouting.ts` must **clear ~25 env vars** before applying an override and why the Command Code PR needed 30+ credential-isolation fixes. Arcon should keep credentials and routing in an explicit immutable config object and touch `os.environ` only when spawning subprocesses.
5. **Don't fork your TUI framework.** `src/ink/` is ~70 files of reconciler + Yoga layout + termio + cell-diffing maintenance burden, plus a native Yoga binding in `src/native-ts/`. Arcon should use Textual or Rich and stay on upstream.
6. **Don't copy the hardcoded pricing table as a permanent design.** It requires a release to fix a price and it only covers first-party Claude models — every gateway model falls to `DEFAULT_UNKNOWN_MODEL_COST`. Arcon, whose whole pitch includes routing across providers, should ship the table as a **data file with a version stamp and an optional refresh**, keeping the tier structure but making the values updatable without a release.
7. **Don't copy the analytics/telemetry scaffolding.** `logEvent('tengu_*')`, GrowthBook feature flags, and the `AnalyticsMetadata_I_VERIFIED_THIS_IS_NOT_CODE_OR_FILEPATHS` type are inherited Anthropic infrastructure that this fork actively neuters (`scripts/no-telemetry-plugin.ts`, `verify:privacy`, `scripts/verify-no-phone-home.ts`). Arcon should start with no telemetry rather than build-time stripping.
8. **Don't treat `web/` as a UI reference** — it is an Astro marketing site (§9). Arcon's UI needs an independent design.
9. **API-stability warning.** Versioned 0.30.0 with `release-please`, but this is a fast-moving fork tracking a proprietary upstream: hardcoded model names (`glm-5.3-flash`, `gpt-5.6-sol`, `CLAUDE_OPUS_4_8_CONFIG`), gateway URLs, and pricing tiers churn per release, and features hide behind `bun:bundle feature()` flags that are dead-code-eliminated per build. Treat anything you read here as a **snapshot at `0abfca30`**, not a stable contract. Model ids and prices in particular should be re-verified against provider docs before Arcon ships them — do not transcribe the numbers in §3.1 as ground truth.
10. **Four specific gaps to fix rather than replicate:**
    - Revocations are checked on **install only** — already-installed compromised skills stay live (§7.7). Check on load too.
    - There is **no signature/provenance verification** for skills, only SHA-256 pinning; and the digest covers **only `SKILL.md`**, with local-directory installs entirely unverified and direct-URL installs bypassing revocations. Arcon should decide whether that's acceptable rather than inherit it silently.
    - The permission LLM classifier's tokens are deliberately **excluded** from cost accounting (`permissions.ts:848`). For a product whose selling point *is* token economics, Arcon should count every token it spends — including internal classifier, summarizer, and title-generation calls — and label them separately rather than hide them.
    - `CLAUDE_CODE_DISABLE_EXPERIMENTAL_BETAS` defaults to `'true'` here because tool-search and global prompt-cache betas **500 on external accounts** — a reminder that features Arcon reads about in Anthropic's docs may not be available on the account tier Arcon's users have.
11. **Don't build a `local-jsx`-style escape hatch early.** OpenClaude's third command kind renders a full interactive Ink component inside the loop. It's powerful and it's why `setToolJSX`, `shouldHidePromptInput`, and `clearLocalJSX` leak through `ToolUseContext`. In a Python/Textual app this coupling is worse, not better. Keep commands to "returns text" and "returns a prompt" until the event stream (§11, P1) is stable.

---

## Corrections to prior assumptions

Two things in Arcon's existing roadmap and in a reasonable first reading of this repo turn out to be wrong:

| Assumption | Reality |
| --- | --- |
| "Port cost tracking from `cost-tracker.ts` and provider abstraction from `QueryEngine.ts`" | Paths were already known to be flat under `src/` (correct). But **`QueryEngine.ts` contains no provider abstraction at all** (§4.1) — it is a turn orchestrator. Provider handling lives in `services/api/providerConfig.ts` + `openaiShim/` + `integrations/`. And the *pricing* half of cost tracking is in `utils/modelCost.ts`, not `cost-tracker.ts`. |
| "`Tool.call` is an async generator yielding progress" | It returns `Promise<ToolResult>` and takes an `onProgress` callback (§8.1). Async generators live in the hook layer above it. |
| "The VS Code extension / `web/` is a second UI to study" | `web/` is a static Astro marketing site with zero imports from `src/`. The VS Code extension is plain CommonJS JS that **spawns the CLI in `--print --input-format=stream-json` mode and speaks NDJSON** — the reusable artifact is the *protocol*, not the UI (§9). |
| "`revocations.json` matching key unknown" | Resolved: conjunctive over specified fields, supporting `{id}`, `{id,version}`, and `{sha256}`-alone; fail-closed on unreachable/malformed (§7.5). |

---

*Verified against source at `0abfca30`. Remaining unverified item: `src/services/skillSearch/*` and `DiscoverSkillsTool` are feature-gated **stubs** in this snapshot, so semantic skill search is designed but not readable here (§7.3) — including whether `@orama/orama` backs it.*
