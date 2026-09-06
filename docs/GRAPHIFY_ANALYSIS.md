# Graphify — Technical Analysis for Arcon Integration

Source analysed: `/home/anirband/perceptron/graphify` (Graphify-Labs/graphify), git HEAD `c9f9901` = release 0.9.55.

## 1. Overview

Graphify turns a folder of code, docs, SQL schemas, configs, PDFs, images and video into a queryable knowledge graph. It is a Python library plus a CLI plus an MCP server, and it ships itself as a *skill* for ~18 coding-agent hosts (Claude Code, Codex, OpenCode, Kilo, Cursor, Gemini CLI, Aider, Kiro, Devin, …) — the `graphify/skill-*.md` files and `graphify install` machinery.

| Field | Value |
|---|---|
| PyPI name | `graphifyy` (imports as `graphify`) |
| Version | 0.9.55 (unreleased in-tree; 0.9.54 dated 2026-09-05) |
| Python | `>=3.10` (`tool.pyright` pins 3.10, ruff `target-version = py310`) |
| License | **Apache-2.0** — `pyproject.toml` declares `license = "Apache-2.0"`. `LICENSE-MIT` is retained for historical reasons: `NOTICE` states portions contributed under MIT *prior to relicensing* remain available under those terms. Practically: consume it as Apache-2.0, keep the `NOTICE`. |
| Core stack | tree-sitter (AST), NetworkX (in-memory graph), numpy + rapidfuzz (scoring/similarity), no database required |
| Build backend | setuptools>=77; three packages shipped: `graphify`, `graphify.extractors`, `graphify.exporters` |
| Maturity | Pre-1.0 but heavy: 198 changelog sections, ~200 test files, 7,645-line `extract.py`, CI parity checks, `SECURITY.md` threat model, pre-commit, bandit, pyright, pip-audit |

Graph construction over code costs **zero LLM tokens** — tree-sitter is deterministic and local. LLM calls appear only in the optional semantic pass over docs/PDFs/images/transcripts, community *naming*, and `--dedup-llm`.

## 2. Architecture

`ARCHITECTURE.md` documents the pipeline, and `tests/test_architecture_doc.py` imports every symbol named in it, so that table cannot drift from code.

```
detect() → extract() → build() → cluster() → analyze helpers → report.generate() → export.to_*()
```

Stages are pure functions communicating via plain dicts and `nx.Graph` — no shared state, no side effects outside `graphify-out/`.

**tree-sitter parsing.** Most languages are *config-driven*: `graphify/extractors/models.py` defines a `LanguageConfig` dataclass naming the tree-sitter module (`ts_module: str`, e.g. `"tree_sitter_python"`), plus node-type frozensets (`class_types`, `function_types`, `import_types`, `call_types`), field names (`name_field`, `body_field`, `call_function_field`), and optional hooks (`import_handler`, `resolve_function_name_fn`, `extra_walk_fn`). A shared `_extract_generic` core (~1,300 lines, in `extractors/engine.py`) walks the tree against that config. `extract_python` is a thin wrapper over it. Extraction is **two-pass**: (1) per-file structure, (2) cross-file import/member-call resolution, which turns file-level imports into symbol-level `INFERRED` edges. Language-specific resolvers exist for Python, TypeScript, Swift, C++, C#, Java, Objective-C, Kotlin, Ruby, Pascal.

**Adding a language** (from `ARCHITECTURE.md` + `extractors/MIGRATION.md`): write `extract_<lang>(path: Path) -> dict` in a new `graphify/extractors/<lang>.py`; register the suffix in `extract()`'s dispatch table *and* `collect_files()` (both `extract.py`); add it to `CODE_EXTENSIONS` in `detect.py` and `_WATCHED_EXTENSIONS` in `watch.py`; add the grammar to `pyproject.toml`; add a fixture + test. `graphify/extractors/__init__.py` exposes `LANGUAGE_EXTRACTORS: dict[str, Callable[[Path], dict]]` — but its own docstring says this is only "the registry seed; wiring dispatch through it is a later, separate step." **Dispatch today still flows through `extract.py`'s hard-coded `_get_extractor()`, not the registry.** That matters: it is not yet a true plugin system for third parties.

**In-memory representation** is `networkx.Graph` (undirected by default; `directed=True` opt-in). Hyperedges (3+ node group relations) ride in `G.graph["hyperedges"]`.

**On disk**, everything lives under `graphify-out/` (overridable via `GRAPHIFY_OUT`, honoured centrally by `graphify/paths.py:out_path()` / `default_graph_json()`):

```
graphify-out/
├── graph.json              # NetworkX node-link format — the queryable artifact
├── GRAPH_REPORT.md         # god nodes, communities, surprises, suggested questions
├── graph.html / graph.svg / graph.canvas / cypher.txt   # optional exports
├── wiki/index.md           # optional agent-crawlable markdown wiki
├── converted/              # Office/Google-Workspace → markdown sidecars
├── memory/                 # save_query_result() Q&A docs
├── reflections/LESSONS.md  # reflect() output
├── .graphify_learning.json # work-memory overlay
└── cache/
    ├── ast/v{ver}-s{schema}/   # version+schema namespaced (extractor code changes invalidate)
    └── semantic[-deep]/[p{prompt_fp}/]  # NOT version-namespaced — re-extraction costs LLM $
```

**Incremental story.** `cache.py:file_hash()` keys on SHA256 of contents with a `_stat_index` (mtime+size) fast path to skip rehashing. `load_cached`/`save_cached` handle AST entries; `check_semantic_cache`/`save_semantic_cache` handle the LLM tier and return the files still needing extraction. Crucially `extract()` accepts `resolution_context_nodes`/`resolution_context_edges` — read-only AST from *unchanged* files — so a changed caller still binds `foo()` or `obj.method()` to an unchanged callee without reparsing the corpus. `build.py:build_merge()`/`merge_raw_extraction()` merge fresh extraction into an existing `graph.json` behind a **shrink guard** that refuses to drop untouched files' nodes unless forced. `graphify update .` is the entry point; `watch.watch(path, debounce=3.0)` and `check_update(path)` drive it on change. Ids and `source_file` are stored repo-relative with canonical separators, so graphs are byte-stable across machines. Extraction parallelises via `ProcessPoolExecutor` above `_PARALLEL_THRESHOLD` uncached files (`max_workers`/`GRAPHIFY_MAX_WORKERS`); `extract()`'s only disk side effect is `save_cached`.

## 3. The graph model

`graph.json` is NetworkX node-link: top-level `directed`, `multigraph`, `graph`, `nodes`, `links`. Real excerpt from `worked/httpx/graph.json`:

```json
{
  "directed": false, "multigraph": false, "graph": {},
  "nodes": [
    {"label": "BaseClient", "file_type": "code",
     "source_file": "worked/httpx/raw/client.py",
     "source_location": "L31", "id": "client_baseclient", "community": 2},
    {"label": "._build_request()", "file_type": "code",
     "source_file": "worked/httpx/raw/client.py",
     "source_location": "L54", "id": "client_baseclient_build_request", "community": 2}
  ],
  "links": [
    {"relation": "contains", "confidence": "EXTRACTED",
     "source_file": "worked/mixed-corpus/raw/analyze.py", "source_location": "L6",
     "weight": 1.0, "source": "analyze", "target": "analyze_node_community_map"}
  ]
}
```

Note the edge key is `links` (NetworkX node-link default), **not** `edges` — except in `--no-cluster` raw graphs, which store `edges` (this caused issue #2212). Use `graphify.paths.load_node_link_graph()` rather than parsing yourself; it handles both, plus a size cap and hyperedge re-attachment.

**Node types.** `file_type` is a closed enum — `build.py` rewrites anything outside `code | document | paper | image | rationale | concept` to `"concept"`. Observed distributions: `worked/rsl-siege-manager` (1,886 nodes) is 1,268 `code` + 618 `rationale`; `worked/httpx` is 144 `code`. Markdown adds a secondary `node_kind` field (`"page"` / `"heading"`) precisely because `file_type` is a closed enum and headings dominate docs-heavy corpora. Nodes carry `id`, `label`, `source_file`, `source_location` (`"L42"`), optional `community`, `norm_label`, `definition_file`, `rationale`.

**Edge relations** actually emitted (verified by grepping emission sites and counting a real graph):

| Relation | Meaning |
|---|---|
| `contains` | file → symbol it defines (structural, dominant by count) |
| `method` | class → its method |
| `calls` | direct call (same-file `EXTRACTED`; cross-file resolved `INFERRED`) |
| `indirect_call` | callable passed as value / dispatched |
| `imports`, `imports_from`, `dynamic_import`, `re_exports`, `requires`, `includes` | module graph |
| `inherits`, `extends`, `implements`, `mixes_in`, `embeds` | type hierarchy |
| `uses`, `references` (with `context` ∈ field/parameter_type/return_type/generic_arg/attribute/value/type), `uses_static_prop`, `uses_component`, `references_constant`, `instantiates`, `binds_method`, `bound_to`, `listened_by` | usage |
| `rationale_for` | rationale node → the code it explains |
| `depends_on`, `crate_depends_on`, `requires_env` | manifests, MCP configs |
| `documents`, `cites`, `joins` | docs, doc-refs, SQL joins |
| `semantically_similar_to` | emitted by the LLM semantic pass only |
| `defines` | schema/DDL |

`affected.py:DEFAULT_AFFECTED_RELATIONS` is the curated blast-radius set: `calls, indirect_call, references, imports, imports_from, dynamic_import, re_exports, inherits, extends, implements, uses, mixes_in, embeds, requires`.

**Design rationale as first-class nodes.** `extract.py:_extract_python_rationale()` mines module/class/function docstrings (>20 chars) *and* comments prefixed with `_RATIONALE_PREFIXES = ("# NOTE:", "# IMPORTANT:", "# HACK:", "# WHY:", "# RATIONALE:", "# TODO:", "# FIXME:")` (JS/TS has `//`/`*` equivalents). Each becomes a `file_type: "rationale"` node with an 80-char label, linked by `rationale_for` to the enclosing symbol; auto-generated files (Alembic, Django migrations, protobuf) are skipped. Genuinely valuable for an agent — "why is this like this" becomes a traversal.

**Provenance tagging** is the trust story. Every edge carries `confidence`:

| Label | Meaning |
|---|---|
| `EXTRACTED` | Explicit in the source — an import statement, a direct call. Always `confidence_score` 1.0. |
| `INFERRED` | A deduction — cross-file resolution, co-occurrence. Carries a discrete `confidence_score`: 0.95 near-certain / 0.85 strong / 0.75 reasonable / 0.65 naming-only / 0.55 speculative. |
| `AMBIGUOUS` | Uncertain; surfaced in `GRAPH_REPORT.md` for human review. |

Real ratios: httpx 174 EXTRACTED / 156 INFERRED; rsl-siege-manager 3,483 / 393. **Nearly half the edges on a small corpus are inferences.** An agent treating an `INFERRED` `calls` edge as ground truth will confidently assert a call that doesn't exist, so Arcon must surface the tag in tool output. `validate.py:validate_extraction(data)` / `assert_valid(data)` enforce the schema before `build()`.

## 4. Language + content coverage

Base install ships **25 mandatory tree-sitter grammars** (python, javascript, typescript, go, rust, java, groovy, c, cpp, ruby, c-sharp, kotlin, scala, php, swift, lua, zig, powershell, elixir, objc, julia, verilog, fortran, bash, json). The README claims 37 grammars / ~40 languages — reconciled because suffixes share grammars (`.mts`/`.cts` → TypeScript; `.cc`/`.cxx`/`.cu`/`.cuh`/`.metal` → C++) and several extractors are regex- or parser-based rather than tree-sitter (Apex `.cls`/`.trigger`, `.csproj`/`.slnx`/`.xaml`/`.razor` via XML, Robot Framework via `robot.api`).

Optional-extra languages: `[sql]` (also required by `[postgres]`), `[terraform]` (`.tf/.tfvars/.hcl`), `[ocaml]`, `[commonlisp]`, `[pascal]` (regex fallback if absent), `[dm]` (BYOND), `[robot]`.

Non-code content:

| Content | Extensions | Extra needed |
|---|---|---|
| Markdown / docs | `.md .mdx .qmd .html .txt .rst .yaml .yml` — headings become nodes, `[x](./y.md)` and `[[wikilinks]]` become `references` edges | none |
| Package manifests | `apm.yml`, `pyproject.toml`, `go.mod`, `pom.xml`, `Cargo.toml` — one canonical package node + `depends_on` | `tomli` on 3.10 (a base dep) |
| MCP configs | `.mcp.json`, `mcp.json`, `claude_desktop_config.json` — server nodes, package refs, `requires_env` | none |
| SQL | `.sql` — tables, views, foreign keys, JOIN relations, deterministically | `[sql]` |
| Live PostgreSQL | `--postgres <dsn>` reconstructs DDL then feeds `extract_sql()` | `[postgres]` |
| PDFs | `.pdf` | `[pdf]` (pypdf, markdownify) |
| Office | `.docx .xlsx` | `[office]` |
| Google Workspace | `.gdoc .gsheet .gslides` | `[google]` + authenticated `gws` CLI + `--google-workspace` |
| Images | `.png .jpg .webp .gif` | none, but needs an LLM backend (vision) |
| Video / audio | `.mp4 .mov .mp3 .wav`, YouTube URLs | `[video]` (faster-whisper, yt-dlp; py>=3.11) |

Images and docs go through the **LLM semantic pass** — they are not free. Code files are never sent to the LLM in the normal pipeline; if a corpus is code-only, the semantic pass is skipped entirely. This is the key fact for Arcon: a code-only graph is free and offline.

## 5. Query & analysis capabilities

| Capability | CLI | Python |
|---|---|---|
| Natural-language subgraph | `graphify query "what connects auth to the db?" [--dfs] [--budget 1500] [--graph P]` | `serve._query_graph_text(G, question, mode="bfs", depth=3, token_budget=2000, context_filters=None, graph_path=None)` |
| Shortest path | `graphify path "A" "B"` | `serve._shortest_path_text(G, arguments)` |
| Explain one concept | `graphify explain "RateLimiter"` | via serve internals |
| Blast radius | `graphify affected "X" [--relation R] [--depth N] [--graph P]` | `affected.resolve_seed(graph, query, root)`, `affected.affected_nodes(graph, seed, *, relations=DEFAULT_AFFECTED_RELATIONS, depth=2) -> list[AffectedHit]`, `affected.format_affected(...) -> str`, `affected.load_graph(path)` |
| God nodes | `graphify god-nodes` | `analyze.god_nodes(G, top_n=10, exclude_hubs_percentile=None) -> list[dict]` |
| Surprising connections | in `GRAPH_REPORT.md` | `analyze.surprising_connections(G, communities=None, top_n=5)` |
| Suggested questions | in `GRAPH_REPORT.md` | `analyze.suggest_questions(G, communities, community_labels, top_n=7)` |
| Import cycles | — | `analyze.find_import_cycles(G, max_cycle_length=5, top_n=20)` |
| Graph diff | — | `analyze.graph_diff(G_old, G_new) -> dict` |
| Communities | `graphify cluster-only . [--resolution 1.5] [--exclude-hubs 99] [--no-label]` | `cluster.cluster(G, resolution=1.0, exclude_hubs_percentile=None) -> dict[int, list[str]]` (does not mutate G), `cluster.label_communities_by_hub(G, communities)`, `cluster.cohesion_score(G, nodes)`, `cluster.score_all(G, communities)` |
| MCP server | `python -m graphify.serve graph.json [--transport http --port 8080 --api-key K]` | `serve.serve(graph_path)`, `serve.serve_http(graph_path, *, host, port, ...)` |

`query` is the one Arcon leans on, so its pipeline matters: `_query_terms` tokenizes (diacritic stripping, optional jieba for Chinese) → `_score_query` makes one graph pass computing IDF-weighted label/rationale/source-path matches plus a trigram index for fuzzy hits → `_pick_seeds` picks roots via a gap window plus a per-term guarantee, dropping relational-intent verbs like "calls" so they can't seat a decoy root → BFS or DFS to `depth`, narrowed by optional `context_filters` → `_subgraph_to_text` renders to a **token budget** (default 2,000), seed-first so the queried symbol survives truncation. The header names the graph and its node count — a guard against confidently answering from the wrong corpus.

MCP tools exposed: `query_graph`, `get_node`, `get_neighbors`, `get_community`, `god_nodes`, `graph_stats`, `shortest_path`, `list_prs`, `get_pr_impact`, `triage_prs`.

## 6. Token efficiency — verifying the claims

**The 71.5x figure is not in `BENCHMARKS.md`.** `BENCHMARKS.md` (last updated 2026-07-05) is about *memory* benchmarks — LOCOMO, LongMemEval-S, and an ERPNext code-intelligence suite. The 71.5x claim lives in `docs/how-it-works.md` and the README/translations.

`docs/how-it-works.md` reports:

| Corpus | Files | Reduction |
|---|---|---|
| Karpathy repos + 5 papers + 4 images | 52 | 71.5x |
| graphify source + Transformer paper | 4 | 5.4x |
| httpx (synthetic Python library) | 6 | ~1x |

**Methodology** (`graphify/benchmark.py:run_benchmark(graph_path, corpus_words=None, questions=None)`):

- Numerator: `corpus_tokens = corpus_words * 100 // 75`. `corpus_words` should come from `detect()`'s real word count. **If it is `None`, it falls back to `G.number_of_nodes() * 50`** — a made-up 50-words-per-node constant. Any caller not passing real word counts gets a synthetic numerator.
- Denominator: for each of 5 hard-coded `_SAMPLE_QUESTIONS` ("how does authentication work", "what is the main entry point", …), `_query_subgraph_tokens` scores nodes by *plain substring count of query terms in the label*, takes the top 3 as seeds, BFS to `depth=3`, renders `NODE ...` / `EDGE ...` lines, and estimates tokens as `len(text) // 4`.
- Ratio = `corpus_tokens / avg_query_tokens`, printed after every run via `print_benchmark`.

**Honest assessment.** The comparison is *corpus-total vs one subgraph* — "read every file" vs "read a scoped answer." That measures the context-stuffing anti-pattern fairly, but it is the wrong baseline for a competent agent, which greps and reads 2–5 files. So 71.5x overstates the gain versus Arcon's realistic alternative. Further caveats: the estimator is `chars/4`, not a tokenizer; the benchmark's substring node-scoring is cruder than production `_score_query`, so measured query cost isn't what production emits; and if no sample question matches, it returns an error rather than a number.

The repo is candid about the load-bearing caveat: **~1x on 6 files, 5.4x on 4, 71.5x at 52**. Below a context window the value is structural clarity, not compression. `BENCHMARKS.md`'s ERPNext result is the more credible and more modest code-intelligence number: on a ~1M-LOC repo, one graphify tool lifted key-fact coverage from 70.8% (grep+read baseline) to 82.0% at ~140K tokens/query, while whole-repo stuffing cost ~20x the tokens for *lower* coverage — but n=6 questions, so directional only. **For Arcon: expect navigation and accuracy wins on large repos, treat 71.5x as marketing, and measure it with Arcon's own token accounting.**

## 7. Public Python API

`graphify/__init__.py` is a `__getattr__` lazy-import shim — nothing is imported until touched, so `import graphify` is cheap and works before heavy deps are installed. The exact map:

```python
extract               -> graphify.extract:extract
collect_files         -> graphify.extract:collect_files
build_from_json       -> graphify.build:build_from_json
cluster               -> graphify.cluster:cluster
score_all             -> graphify.cluster:score_all
cohesion_score        -> graphify.cluster:cohesion_score
god_nodes             -> graphify.analyze:god_nodes
surprising_connections-> graphify.analyze:surprising_connections
suggest_questions     -> graphify.analyze:suggest_questions
generate              -> graphify.report:generate
to_json               -> graphify.export:to_json
to_html               -> graphify.export:to_html
to_svg                -> graphify.export:to_svg
to_canvas             -> graphify.export:to_canvas
to_wiki               -> graphify.wiki:to_wiki
reflect               -> graphify.reflect:reflect
save_query_result     -> graphify.ingest:save_query_result
```

Real signatures (read from source):

```python
# graphify/extract.py
def extract(paths: list[Path], cache_root: Path | None = None, *,
            root: Path | None = None, parallel: bool = True,
            max_workers: int | None = None,
            resolution_context_nodes: list[dict] | None = None,
            resolution_context_edges: list[dict] | None = None) -> dict
def collect_files(target: Path, *, follow_symlinks: bool = False,
                  root: Path | None = None) -> list[Path]

# graphify/build.py
def build(extractions: list[dict], *, directed: bool = False, dedup: bool = True,
          dedup_llm_backend: str | None = None,
          root: str | Path | None = None) -> nx.Graph
def build_from_json(extraction: dict, *, directed: bool = False,
                    root: str | Path | None = None) -> nx.Graph
def edge_data(G, u, v) -> dict            # multigraph-safe edge accessor
def edge_datas(G, u, v) -> list[dict]

# graphify/cluster.py
def cluster(G, resolution: float = 1.0,
            exclude_hubs_percentile: float | None = None) -> dict[int, list[str]]
def cohesion_score(G, community_nodes: list[str]) -> float
def score_all(G, communities) -> dict[int, float]
def label_communities_by_hub(G, communities) -> dict[int, str]

# graphify/analyze.py
def god_nodes(G, top_n: int = 10, exclude_hubs_percentile: float | None = None) -> list[dict]
def surprising_connections(G, communities=None, top_n: int = 5) -> list[dict]
def suggest_questions(G, communities, community_labels, top_n: int = 7) -> list[dict]
def find_import_cycles(G, max_cycle_length: int = 5, top_n: int = 20) -> list[dict]
def graph_diff(G_old, G_new) -> dict

# graphify/export.py
def to_json(G, communities, output_path: str, *, force: bool = False,
            built_at_commit: str | None = None,
            community_labels: dict[int, str] | None = None) -> bool
def to_svg(G, communities, output_path, community_labels=None,
           figsize: tuple[int,int] = (20,14)) -> None
def to_canvas(G, communities, output_path, community_labels=None,
              node_filenames=None) -> None
def to_obsidian(G, communities, output_dir, community_labels=None, cohesion=None) -> int
def to_graphml(G, communities, output_path) -> None
def to_cypher(G, output_path) -> None

# graphify/wiki.py
def to_wiki(G, communities, output_dir: str | Path, community_labels=None,
            cohesion=None, god_nodes_data: list[dict] | None = None) -> int

# graphify/report.py — 14 params, all required except the last 6
def generate(G, communities, cohesion_scores, community_labels, god_node_list,
             surprise_list, detection_result, token_cost, root: str,
             suggested_questions=None, min_community_size: int = 3,
             built_at_commit=None, learning=None, obsidian: bool = False) -> str

# graphify/reflect.py
def reflect(memory_dir: Path, out_path: Path, graph_path: Path | None = None,
            analysis_path: Path | None = None, labels_path: Path | None = None, *,
            now=None, half_life_days: float = ..., min_corroboration: int = ...
            ) -> tuple[Path, dict[str, Any]]

# graphify/ingest.py
def save_query_result(question: str, answer: str, memory_dir: Path,
                      query_type: str = "query", source_nodes: list[str] | None = None,
                      outcome: str | None = None, correction: str | None = None) -> Path
```

`to_html` resolves correctly: it is defined in `graphify/exporters/html.py:396` and re-exported by `export.py:166`. **Absent from the lazy map but essential to Arcon**: `graphify.detect:detect`, all of `graphify.affected`, `graphify.paths:load_node_link_graph`, `graphify.serve:_query_graph_text` / `_shortest_path_text`, `graphify.validate`, `graphify.benchmark:run_benchmark`, `graphify.build:build` / `build_merge` / `edge_data`. Import those from their submodules directly.

**Critical gotcha:** `extract()` takes a **list** of `Path`, and `root` is keyword-only and optional. `ARCHITECTURE.md` is emphatic — *always pass `root` explicitly*, because node ids and `source_file` are derived relative to it; omitted, it infers the common parent of the passed list, so a single-file call anchors to that file's directory and machine-local path segments leak into ids.

## 8. Integration plan for Arcon

Arcon's tool system (`src/arcon/tools/`) uses an ABC `Tool` with `_create_metadata() -> ToolMetadata`, `_create_parameters() -> List[ToolParameter]`, and `async execute(**kwargs) -> str`, registered into `ToolRegistry.register(tool)` (raises `ToolError` on duplicate name) alongside `ReadFileTool`, `WriteFileTool`, `ListDirectoryTool`, `BashExecuteTool`.

### Proposed layout

```
src/arcon/graph/
├── __init__.py       # re-export GraphManager, GraphNotBuiltError
├── manager.py        # GraphManager: build/load/update/query, per-workspace
├── paths.py          # workspace → graph dir resolution
├── formatting.py     # subgraph → token-budgeted agent text, confidence-annotated
└── tools.py          # GraphQueryTool, GraphPathTool, AffectedTool, GraphBuildTool
```

`GraphManager` owns a lazily-loaded `nx.Graph` cached in-process (keyed by workspace + graph.json mtime) so repeated tool calls in one agent loop don't re-read a multi-MB JSON. Build path:

```python
from pathlib import Path
from graphify.detect import detect
from graphify.extract import extract, collect_files
from graphify.build import build, build_merge
from graphify.cluster import cluster, label_communities_by_hub
from graphify.export import to_json
from graphify.paths import load_node_link_graph
from graphify.affected import affected_nodes, resolve_seed, format_affected
from graphify.serve import _query_graph_text, _shortest_path_text
```

`_query_graph_text` and `_shortest_path_text` are underscore-private. Either vendor a thin reimplementation over the public scoring primitives, or wrap them behind a single adapter in `manager.py` with a version-pinned dependency and a smoke test — so an upstream rename breaks one file, not the tool layer.

### Dependencies

Depend on **base `graphifyy`** (no extras) as the default. That gets code + markdown + JSON/manifest + MCP-config extraction with zero LLM cost — exactly Arcon's core use case. Make optional, behind an `arcon[graph-full]` extra and a runtime capability check: `[sql]`, `[pdf]`, `[office]`, `[terraform]`, `[ocaml]`, `[leiden]`, `[svg]`, `[video]`. **Do not** depend on `[mcp]` — the decision is in-process, and pulling `mcp` + `starlette` is pure weight. Skip `[anthropic]`/`[openai]`/`[ollama]` too; Arcon already owns those providers, and graphify's semantic pass is not needed for a code-only graph.

**The 25 mandatory grammars are the real cost and cannot be avoided.** They are hard `dependencies`, not extras, so `pip install graphifyy` pulls all 25 regardless — compiled C extension wheels totalling roughly tens of MB and a noticeably slower cold install for every Arcon user, including someone who only writes Python. Options: (1) make graphify an **optional Arcon extra** (`pip install arcon[graph]`) with `GraphQueryTool` self-registering only when `import graphify` succeeds and otherwise emitting a clear install hint; (2) ship it by default and document the install size; (3) upstream a PR splitting grammars into per-language extras — the right fix, not a blocker. **Recommendation: option 1 for v0.2, revisit once graph tooling proves itself in Arcon's own token measurements.**

### Where graph.json lives

Do **not** write `graphify-out/` into the user's repo — it pollutes their tree and their `.gitignore`. Set `GRAPHIFY_OUT` to an Arcon-owned per-workspace dir before importing `graphify.paths` (the module reads the env var at import time — `GRAPHIFY_OUT = os.environ.get("GRAPHIFY_OUT", "graphify-out")` — so set it in `arcon.graph.paths` before any graphify import, or pass explicit paths everywhere):

```
~/.arcon/graphs/<sha256(abs_workspace_path)[:16]>/
├── graph.json
├── cache/ast/v{ver}-s{schema}/
└── meta.json     # arcon-side: workspace path, git HEAD, built_at, node/edge counts, graphify version
```

Content-addressing by workspace path keeps worktrees and monorepo subdirs separate and survives `git clean`. Offer a `--graph-in-repo` opt-out for teams wanting a committed shared graph.

### Cache invalidation / incremental rebuild

Layer Arcon's staleness check on top of graphify's SHA256 cache:

1. On workspace open read `meta.json`; if absent, mark the graph unbuilt and have tools return an actionable "no graph — run `arcon graph build`" instead of failing.
2. Otherwise compare stored `git HEAD` to current. On mismatch, `git diff --name-only <stored>..HEAD` gives the changed set — feed exactly those to `extract()` with `resolution_context_nodes`/`resolution_context_edges` loaded from the existing graph, then `build_merge()`. This is graphify's supported incremental path and what makes rebuilds cheap.
3. For uncommitted edits, have Arcon's `WriteFileTool` append paths to a dirty set and re-extract that set (debounced) at the start of the next graph query, not on every write. Reuse `watch.check_update(path)` semantics rather than reinventing them.
4. Force a clean rebuild when installed `graphify.__version__` changes: the AST cache is version-namespaced but the merged `graph.json` is not, so it can otherwise carry nodes from two extractor generations.
5. Honour the shrink guard — never pass `force=True` to `to_json` on an incremental path. A shrunken graph is the signature of partial extraction, and overwriting loses untouched files' nodes.

### Tool surface and prompting

| Tool | Params | Returns |
|---|---|---|
| `GraphQueryTool` | `question: str`, `mode: "bfs"\|"dfs" = "bfs"`, `depth: int = 3`, `token_budget: int = 2000` | Token-budgeted subgraph text: header (graph path, node count, seeds), then `NODE`/`EDGE` lines with `source_file:Lline` and confidence tags |
| `GraphPathTool` | `source: str`, `target: str` | Hop-by-hop path with relation + confidence per hop, or an explicit "no path" |
| `AffectedTool` | `symbol: str`, `depth: int = 2`, `relations: list[str] \| None = None` | Blast radius: `list[AffectedHit]` rendered as `label (depth N, via <relation>) — file:Lline`, using `via_file`/`via_location` (the call *site*, not the definition line) |

Two design rules matter more than the tools themselves:

**Every line must carry `source_file:Lline`.** The graph's job is to make `ReadFileTool` *targeted*, not to replace it. An agent that gets `BaseClient — client.py:L31` reads 40 lines instead of a 900-line file.

**Every inferred edge must be labelled.** Render `calls (inferred, 0.75)` inline. Roughly half the edges on small corpora are `INFERRED`; unlabelled, the model will assert them as fact.

Prompting (in Arcon's system prompt, plus a `graph` skill): *"Before reading source files to answer a structural question ('how does X work', 'what calls Y', 'what breaks if I change Z'), call `graph_query`/`graph_affected` first. Those tools return `file:line` anchors — use them to read specific ranges, never a whole file. Do not read more than 2 files without a graph query. Edges marked `inferred` are the tool's deductions, not facts; verify by reading the cited line before asserting a call relationship."* Enforce it with a soft nudge in the tool-selection layer (graphify's own strict mode blocks the *first* raw source read of a session and redirects to the graph, then reverts — a pattern worth copying, since it fires once and cannot deadlock). Also worth adopting: graphify's `save_query_result` + `reflect` loop as a cheap long-term memory for which graph answers proved useful.

## 9. Cross-platform considerations

**Wheels.** The 25 mandatory grammars ship prebuilt wheels for macOS (x86_64 + arm64), manylinux (glibc) and Windows — debian and redhat are both fine, no C toolchain needed for a default install. `pyproject.toml` comments confirm `tree-sitter-pascal`, `[ocaml]` and `[commonlisp]` ship wheels for every platform, while `tree-sitter-dm` ships **only a Windows wheel** and compiles from source elsewhere (C toolchain + `python3-dev`). Arcon should not depend on `[dm]`.

**musl/Alpine is the real gap.** manylinux wheels don't work on musl and there is no sign of musllinux wheels; an Alpine-based Arcon container would compile 25 grammars from source. Standardise on a glibc base image.

**tree-sitter version coupling.** `tree-sitter>=0.23,<0.26` with each grammar pinned to its own narrow range (`<0.25`/`<0.26`/`<0.27`), enforced at runtime by `extract.py:_check_tree_sitter_version()`. A brittle constraint web — if anything else in Arcon's tree needs a different `tree-sitter`, resolution fails. Real risk given how many tools now embed it.

**Windows.** The code shows genuine care: `benchmark.py:_safe()` degrades box-drawing/arrow glyphs to ASCII for cp1252 consoles; `paths.py:is_absolute_any_platform()` handles paths stored under the other OS's rules; `_cap_filename`/`stem_filename_budget` cap export filenames at 200 chars for MAX_PATH; 0.9.55 fixed MCP `prs` hanging the stdio transport on Windows. Remaining risks: (a) the test suite needs Developer Mode for symlinks and `LongPathsEnabled` for long paths — deep node-derived export paths can still exceed MAX_PATH, so prefer `graph.json` over Obsidian/wiki exports there; (b) `ProcessPoolExecutor` spawns on Windows and re-imports, so Arcon's imports must be spawn-safe when calling `extract(parallel=True)`, else pass `parallel=False`; (c) set `GRAPHIFY_OUT` to an absolute path so `Path(GRAPHIFY_OUT, ...)` can't resolve against a drive-relative cwd; (d) keep `[postgres]` (`psycopg[binary]`) and `[video]` (`faster-whisper`) optional.

Python 3.10 needs `tomli` (a base dep since 0.9.54, after its absence silently dropped every `pyproject.toml`). `[leiden]` (graspologic) is `python_version < '3.13'`, so on 3.13+ clustering falls back to graphify's own `_partition` and community shape may differ.

## 10. Risks & caveats

**Pre-1.0 with extreme release velocity.** 198 changelog sections; 0.9.36 → 0.9.55 spans 2026-08-07 to 2026-09-05 — roughly **one release every 1.5 days**. Nothing in `0.9.x` promises API stability. Mitigation: pin an exact version (`graphifyy==0.9.55`), not a range; upgrade deliberately with a smoke test; keep every graphify import behind `src/arcon/graph/manager.py` so the blast radius of an upstream change is one module.

**Private-API dependency is the sharpest risk.** The functions Arcon most needs — `serve._query_graph_text`, `serve._shortest_path_text`, `serve._query_terms`, `serve._score_query`, `serve._subgraph_to_text` — are all underscore-prefixed and absent from `__init__.py`'s lazy map. graphify's *own* `benchmark.py` imports `serve._query_terms`, which is mild reassurance, but these can be renamed in any patch release. Write a `tests/test_graphify_contract.py` in Arcon that asserts each imported symbol exists with the expected arity; it will fail loudly on upgrade instead of at runtime in front of a user.

**Public API is thinner than it looks.** `LANGUAGE_EXTRACTORS` is documented as a registry seed that dispatch does not yet use, so it is not a third-party plugin hook. `report.generate()` needs 9 positional arguments including `detection_result` and `token_cost` dicts whose shapes are undocumented outside the code. The 17-name lazy map omits most of what an integrator actually needs (§7). Treat it as *the shape upstream advertises*, not a stability contract.

**Dependency weight.** ~25 compiled grammar wheels in the base install, plus networkx, numpy and rapidfuzz. Non-negotiable upstream today, and a genuine tax on Arcon's install experience for users who never touch the graph.

**Correctness is a moving target.** The changelog is dominated by extraction-correctness fixes — phantom edges, ghost nodes, id collisions, dropped dynamic imports, fabricated `extends` edges from JSON arrays. That reads as a healthy, actively-hardened project, but it also means today's graph contains unknown false edges. Combined with ~50% `INFERRED` edges on small corpora, this is the strongest argument for surfacing confidence in every tool response and treating the graph as a *navigation index*, not a source of truth. It also compounds with the un-version-stamped `graph.json` (§8, point 4): after an upgrade, an incremental merge can silently mix two extractor generations.

**If upstream changes or stalls.** Apache-2.0 means Arcon can vendor or fork freely (retaining `NOTICE`). The interface Arcon depends on is small: `extract` → `build` → `cluster` → `to_json`, plus BFS/path/affected traversal over a NetworkX graph. If upstream diverges, Arcon can pin the last good version indefinitely and reimplement the ~200 lines of query/path/affected logic over `graph.json` — the expensive, hard-to-replace asset is the tree-sitter extractor corpus, and that is the part with the most stable interface (`extract_<lang>(path) -> {nodes, edges}`).
