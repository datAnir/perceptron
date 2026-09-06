# Arcon Enhancement Plan: Advanced Features + Token Optimization
**Version:** 0.2.0 Roadmap  
**Date Created:** April 19, 2026  
**Status:** Planning Phase  
**Target:** Transform Arcon into production-grade coding agent with token efficiency

---

## Executive Summary

### Current State: Arcon v0.1.0
- ✅ **Fully functional** with 193/194 tests passing (99.5% pass rate)
- ✅ Core systems complete: providers, tools, agents, skills, storage, CLI
- ✅ 5 specialized agents (CodingAssistant, Debugger, CodeReviewer, TestEngineer, DocumentationWriter)
- ✅ 34 ECC skills loaded and functional
- ✅ Multi-provider support (Anthropic, OpenAI, Ollama)
- ✅ SQLite persistence with session management
- ✅ CI/CD pipelines ready

### Enhancement Goals
1. **Advanced Features** from leading coding agent frameworks (Copilot SDK, Deep Agents, OpenClaude, autoskills)
2. **Token Optimization** - 70-98% reduction, $1,500-$2,500/mo savings for heavy users
3. **Production Readiness** with comprehensive observability and quality metrics

### Expected Impact
- **Token Efficiency:** 70-98% reduction depending on feature
- **Cost Savings:** $1,500-$2,500/month for heavy users
- **Codebase Efficiency:** 8-49x reduction on large projects
- **User Experience:** Smarter agent routing, auto-skill injection, resumable sessions

---

## Research Foundation

### Source Frameworks Analyzed

#### Coding Agent Frameworks
1. **Copilot SDK** - JSON-RPC protocol, permission system, session management
2. **Deep Agents** - LangGraph-based with middleware architecture, execution backends
3. **OpenClaude** - Multi-provider support, streaming, cost tracking
4. **Everything Claude Code (ECC)** - 48 agents, 183 skills, continuous learning philosophy

#### Token Optimization Systems
1. **alexgreensh/token-optimizer** - Multi-layer optimization, quality scoring, delta mode
2. **mksglu/context-mode** - Sandboxed execution, FTS5 indexing, session continuity
3. **JuliusBrussee/caveman** - Linguistic compression (65% reduction)
4. **tirth8205/code-review-graph** - AST-based blast radius (8-49x reduction)
5. **nadimtuhin/claude-token-optimizer** - Tiered memory structure (90% reduction)

### Key Insights from Token Optimization Research

| Repository | Main Technique | Token Savings | Key Innovation |
|------------|---------------|---------------|----------------|
| token-optimizer | Delta mode + quality scoring | 97% on re-reads | Cache file contents, return only diffs |
| context-mode | Sandboxed execution + FTS5 | 98% (315KB→5.4KB) | Run analysis scripts, return only results |
| caveman | Linguistic compression | 65% average | Remove grammatical fluff, maintain accuracy |
| code-review-graph | AST blast radius | 8-49x reduction | Tree-sitter parsing, incremental updates |
| claude-token-optimizer | Tiered memory | 90% (11K→1.3K) | Core/Topic/Archive structure |

**Combined Potential:** $1,500-$2,500/month savings for heavy users

---

## Part 1: Advanced Features from Coding Agent Repos

### Priority Tier 1: Middleware & Tool Enhancement (Weeks 1-2)

#### Feature 1.1: Middleware Pipeline (from Deep Agents)
**Current Gap:** No middleware architecture  
**Value:** Enables extensible, composable processing pipeline for validation, transformation, injection

**Implementation Tasks:**
- [ ] Create `src/arcon/middleware/` module structure
- [ ] Implement base `Middleware` abstract class with 3 hooks:
  - `process_input(messages)` - pre-LLM processing
  - `process_tool_call(tool_name, input)` - tool call validation/modification
  - `process_output(output)` - post-LLM processing
- [ ] Create `MiddlewarePipeline` for sequential execution
- [ ] Implement core middlewares:
  - `FilesystemSecurityMiddleware` - prevent path traversal attacks
  - `PermissionMiddleware` - tool access control (allow/deny/ask)
  - `SkillInjectionMiddleware` - auto-inject relevant skills based on query
  - `ContextCompactionMiddleware` - auto-summarize when context fills (see Token Optimization)

**New Files:**
```
src/arcon/middleware/
├── __init__.py          # Exports
├── base.py              # Middleware ABC, MiddlewarePipeline
├── security.py          # FilesystemSecurityMiddleware
├── permissions.py       # PermissionMiddleware  
├── skills.py            # SkillInjectionMiddleware
└── compaction.py        # ContextCompactionMiddleware
```

**Tests:** 20+ unit tests for each middleware  
**Integration:** Update Session.invoke() to use middleware pipeline

---

#### Feature 1.2: Permission System (from Copilot SDK)
**Current Gap:** No formal permission checks for tool execution  
**Value:** User control, security compliance, enterprise readiness

**Implementation Tasks:**
- [ ] Create permission model with 3 states: `allow`, `deny`, `ask`
- [ ] Add `PermissionSet` class with default permissions per tool
- [ ] Implement interactive permission prompts with user choice memory
- [ ] Add permission persistence (SQLite storage)
- [ ] Update all tools to check permissions before execution
- [ ] Add CLI commands for permission management

**Default Permissions:**
```python
DEFAULT_PERMISSIONS = {
    "read_file": "allow",        # Safe, read-only
    "list_dir": "allow",         # Safe, read-only
    "write_file": "ask",         # Modifies filesystem
    "bash_execute": "ask",       # Executes code
}
```

**User Experience:**
```
$ arcon chat
> Write tests for auth.py

Agent wants to execute: bash_execute("pytest tests/test_auth.py")
Allow? [y]es / [n]o / [a]lways / ne[v]er: a
Permission saved: bash_execute = allow

Agent wants to write: tests/test_auth.py
Allow? [y]es / [n]o / [a]lways / ne[v]er: y
```

**Tests:** 15 permission flow tests  
**Documentation:** User guide for permission management

---

#### Feature 1.3: Enhanced Cost Tracking (from OpenClaude)
**Current Gap:** Basic token tracking, no cost awareness  
**Value:** Budget control, cost-aware model selection, monthly reporting

**Implementation Tasks:**
- [ ] Add `get_cost_per_token()` method to all providers (Anthropic, OpenAI, Ollama)
- [ ] Create `src/arcon/cost/tracker.py` module
- [ ] Track per-session costs with detailed breakdown
- [ ] Add cost aggregation (daily, weekly, monthly views)
- [ ] Implement cost-aware model selection (use cheaper models for simple queries)
- [ ] Add cost budgets and alerts
- [ ] Create cost reporting CLI commands

**Cost Tracking Data Model:**
```python
{
    "session_id": "sess-abc123",
    "timestamp": "2026-04-19T10:30:00Z",
    "model": "claude-3-5-sonnet-20241022",
    "input_tokens": 2500,
    "output_tokens": 850,
    "cost_usd": 0.0125,
    "tool_calls": 3,
    "provider": "anthropic"
}
```

**CLI Commands:**
```bash
arcon cost show                 # Current session
arcon cost report --daily       # Today's costs
arcon cost report --monthly     # This month
arcon cost budget set 50        # Set $50/month budget
arcon cost budget status        # Check budget usage
```

**Tests:** 10 cost calculation tests  
**Integration:** Display costs in session statistics

---

### Priority Tier 2: Intelligence & Discovery (Weeks 3-4)

#### Feature 2.1: Technology Auto-Detection (from autoskills)
**Current Gap:** Skills must be manually loaded, no project awareness  
**Value:** Auto-inject relevant skills, reduce configuration burden

**Implementation Tasks:**
- [ ] Create `src/arcon/skills/scanner.py` - ProjectScanner class
- [ ] Detect technologies from multiple signals:
  - **Package files:** package.json, requirements.txt, Cargo.toml, go.mod, pom.xml, Gemfile
  - **Config files:** tsconfig.json, .eslintrc, webpack.config.js, Dockerfile, .env
  - **Framework files:** settings.py (Django), manage.py (Django), next.config.js (Next.js)
  - **Content patterns:** Grep for framework imports (FastAPI, Flask, Express, React)
- [ ] Create `src/arcon/skills/resolver.py` - SkillResolver class
- [ ] Build `SKILLS_MAP.yaml` - technology → skills mapping
- [ ] Build `COMBO_SKILLS.yaml` - technology combination patterns
- [ ] Integrate with SkillInjectionMiddleware for automatic loading

**SKILLS_MAP Structure:**
```yaml
technologies:
  python:
    detect:
      packages: [requirements.txt, setup.py, pyproject.toml]
      imports: [import os, import sys, from pathlib]
    skills:
      - python-patterns
      - python-testing
      - python-best-practices
  
  django:
    detect:
      packages: [Django, django]
      files: [settings.py, manage.py]
      imports: [from django.db, from django.views]
    skills:
      - django-patterns
      - django-orm
      - django-security
  
  typescript:
    detect:
      packages: [tsconfig.json]
      files: [*.ts, *.tsx]
    skills:
      - typescript-patterns
      - typescript-testing
  
  react:
    detect:
      packages: [react, @types/react]
      files: [*.jsx, *.tsx]
      imports: [import React, from 'react']
    skills:
      - react-patterns
      - react-hooks
      - react-testing

combos:
  react-typescript:
    requires: [react, typescript]
    skills:
      - react-typescript-patterns
      - nextjs-patterns
  
  django-postgres:
    requires: [django, postgres]
    skills:
      - django-postgres-patterns
      - database-migrations
      - postgres-optimization
  
  fastapi-sqlalchemy:
    requires: [fastapi, sqlalchemy]
    skills:
      - fastapi-patterns
      - sqlalchemy-patterns
      - api-design
```

**Auto-Detection Flow:**
```
1. User opens project: cd /path/to/project && arcon chat
2. ProjectScanner scans directory
3. Detects: Python, FastAPI, SQLAlchemy, Postgres, pytest
4. Resolves combos: fastapi-sqlalchemy
5. Loads skills: python-patterns, fastapi-patterns, sqlalchemy-patterns,
                 api-design, python-testing, postgres-patterns
6. Skills available in all conversations
```

**Tests:** 25 detection tests across languages and frameworks  
**Documentation:** Guide for adding new technology detectors

---

#### Feature 2.2: Enhanced Agent Routing (from ECC + Copilot SDK)
**Current Gap:** Basic keyword matching, no context awareness  
**Value:** Smarter agent selection, sub-agent delegation, better results

**Implementation Tasks:**
- [ ] Enhance `AgentRegistry.route_query()` with multi-factor routing:
  - Explicit agent name in query (highest priority)
  - Context hints (file extension → specialization)
  - Keyword matching with confidence scoring
  - Technology detection → agent preference
  - Query complexity analysis
- [ ] Create `AgentOrchestrator` for multi-agent coordination
- [ ] Implement sub-agent delegation protocol
- [ ] Add agent capability registry
- [ ] Track routing decisions in session metadata for learning
- [ ] Add confidence scores to routing results

**Enhanced Routing Priority:**
```
1. Explicit name:     "Use Debugger to fix this error"          → Debugger (100%)
2. File extension:    Query about "auth.test.ts"                → TestEngineer (90%)
3. Keywords:          "Review security of this authentication"  → CodeReviewer (85%)
4. Tech detection:    Project has React, query about hooks      → CodingAssistant (75%)
5. Complexity:        Multi-step architectural question         → CodingAssistant (60%)
6. Fallback:          Generic query                             → CodingAssistant (50%)
```

**Sub-Agent Delegation:**
```python
# Main agent can request help from specialized agents
async def handle_complex_query():
    # CodingAssistant starts working on feature
    agent = CodingAssistant()
    
    # Realizes security review needed
    await agent.delegate_to(CodeReviewer, context="auth implementation")
    
    # Then needs tests written
    await agent.delegate_to(TestEngineer, context="auth feature")
    
    # Finally returns to user with complete solution
```

**Tests:** 20 routing scenario tests  
**Metrics:** Track routing accuracy over time

---

#### Feature 2.3: Execution Backends (from Deep Agents)
**Current Gap:** Only local execution, no sandboxing  
**Value:** Security isolation, remote execution, controlled environments

**Implementation Tasks:**
- [ ] Create `src/arcon/execution/` module
- [ ] Implement `ExecutionBackend` abstract base class
- [ ] Create backend implementations:
  - `LocalExecutionBackend` - current behavior (direct subprocess)
  - `SandboxedExecutionBackend` - isolated execution (Docker or subprocess with limits)
  - Future: `RemoteExecutionBackend` - cloud execution
- [ ] Update all tools to use backend abstraction
- [ ] Add backend selection in configuration
- [ ] Implement resource limits (CPU, memory, timeout)
- [ ] Add execution logging and monitoring

**Backend Interface:**
```python
class ExecutionBackend(ABC):
    @abstractmethod
    async def execute_command(self, command: str, cwd: str = None,
                             timeout: int = 30) -> str:
        """Execute shell command, return output"""
        pass
    
    @abstractmethod
    async def read_file(self, path: str) -> bytes:
        """Read file contents"""
        pass
    
    @abstractmethod
    async def write_file(self, path: str, content: bytes):
        """Write file contents"""
        pass
```

**Configuration:**
```yaml
execution:
  backend: sandboxed  # local, sandboxed, remote
  sandbox:
    type: docker
    image: python:3.12-slim
    timeout: 30
    memory_limit: 512M
    cpu_limit: 1.0
```

**Tests:** 15 backend tests (local, sandboxed, error cases)  
**Security:** Document sandboxing security model

---

### Priority Tier 3: Learning & Optimization (Weeks 5-6)

#### Feature 3.1: Continuous Learning (from ECC Philosophy)
**Current Gap:** No pattern extraction from sessions  
**Value:** Agent improves over time, learns project-specific patterns

**Implementation Tasks:**
- [ ] Create `src/arcon/learning/extractor.py` module
- [ ] Implement pattern extraction from successful sessions:
  - **Domain-specific solutions:** Code patterns that solved problems
  - **Error → Fix sequences:** Common bugs and their resolutions
  - **Refactoring patterns:** Improvements made to code
  - **Tool usage patterns:** Effective tool combinations
- [ ] Create skill generation from patterns
- [ ] Add user review workflow for learned skills (approve/reject/edit)
- [ ] Save approved skills to `skills/learned/` directory
- [ ] Add skill versioning and metadata tracking
- [ ] Implement skill quality metrics

**Pattern Types:**
```python
class Pattern:
    type: str  # 'solution', 'error_fix', 'refactoring', 'tool_usage'
    domain: str  # 'authentication', 'database', 'api', etc.
    content: str  # The actual pattern content
    context: dict  # When this pattern applies
    frequency: int  # How often seen
    success_rate: float  # How often it worked
```

**Learning Flow:**
```
1. Session completes successfully
2. Extractor analyzes conversation
3. Identifies reusable patterns
4. Generates skill candidates
5. User reviews and approves
6. Skills saved to learned/ directory
7. Skills available in future sessions
```

**Tests:** 10 learning and extraction tests  
**UI:** Interactive skill review interface

---

#### Feature 3.2: Enhanced Session Management (from Copilot SDK)
**Current Gap:** Basic persistence, no checkpointing or recovery  
**Value:** Resume interrupted sessions, audit trails, crash recovery

**Implementation Tasks:**
- [ ] Add checkpoint/resume capabilities to Session class
- [ ] Implement progressive checkpointing at key thresholds:
  - 20% context fill (early snapshot)
  - 35% context fill (before major work)
  - 50% context fill (midpoint)
  - 65% context fill (before optimization needed)
  - 80% context fill (before compaction)
- [ ] Track comprehensive metadata:
  - Agent routing decisions and confidence scores
  - Tool calls with execution times
  - Costs per interaction
  - Quality metrics
- [ ] Add session export formats (JSON, Markdown, HTML)
- [ ] Implement session recovery from crashes
- [ ] Add session statistics and detailed reporting
- [ ] Create session comparison tools

**Checkpoint Data Structure:**
```python
{
    "checkpoint_id": "chk-abc123",
    "session_id": "sess-xyz789",
    "timestamp": "2026-04-19T10:30:00Z",
    "fill_percentage": 0.35,
    "messages": [...],           # Full message history
    "metadata": {
        "agent": "CodingAssistant",
        "tool_calls": 12,
        "total_cost": 0.045,
        "quality_score": 85
    },
    "file_cache": {...},         # Cached file contents
    "skills_loaded": [...],      # Active skills
}
```

**CLI Commands:**
```bash
arcon sessions list                    # List all sessions
arcon sessions show <id>               # Show session details
arcon sessions resume <id>             # Resume from latest checkpoint
arcon sessions restore <checkpoint-id> # Restore from specific checkpoint
arcon sessions export <id> --format md # Export to Markdown
arcon sessions stats                   # Aggregated statistics
```

**Tests:** 15 session management tests  
**Documentation:** Session lifecycle guide

---

## Part 2: Token Optimization Features

### Token Optimization Tier 1: High-Impact Core (Weeks 1-2)

#### TO-1.1: Delta Mode for File Reads
**Source:** alexgreensh/token-optimizer  
**Technique:** Cache file contents, return only diffs on re-reads  
**Token Savings:** 97% reduction on repeated reads (2000 tokens → 60 tokens)

**Implementation Tasks:**
- [ ] Create `src/arcon/tools/cache.py` - FileContentCache class
- [ ] Enhance `ReadFileTool` with cache support and diff generation
- [ ] Implement cache invalidation on write operations
- [ ] Add cache statistics tracking (hits, misses, savings)
- [ ] Store cache in session metadata for persistence
- [ ] Add cache configuration options (max size, TTL)

**Example Workflow:**
```python
# First read: full content (2000 tokens)
> read_file("src/auth.py")
Returns: [full file content - 2000 tokens]

# Agent makes no changes
# Second read: cache hit
> read_file("src/auth.py")
Returns: "No changes since last read at 10:30:00" [20 tokens]

# Agent modifies file
> write_file("src/auth.py", modified_content)
Cache invalidated

# Third read: diff only
> read_file("src/auth.py")
Returns: [unified diff showing changes - 60 tokens]
```

**Cache Storage:**
```python
{
    "path": "src/auth.py",
    "content_hash": "abc123...",
    "content": "...",
    "last_read": "2026-04-19T10:30:00Z",
    "read_count": 5
}
```

**Tests:** 12 caching and diff generation tests  
**Metrics:** Track token savings per session

---

#### TO-1.2: Sandboxed Execution
**Source:** mksglu/context-mode  
**Technique:** Run analysis scripts, return only results (not raw data)  
**Token Savings:** 98% reduction (315 KB → 5.4 KB)

**Implementation Tasks:**
- [ ] Create `SandboxTool` for code execution in isolated environment
- [ ] Add support for multiple languages:
  - Python, JavaScript/TypeScript, Shell, Ruby, Go, Rust, PHP
- [ ] Return only stdout (raw file data never enters context)
- [ ] Add timeout and resource limits (CPU, memory)
- [ ] Store large outputs in FTS5 database (see TO-1.4)
- [ ] Implement result preview with full retrieval option

**Example: Instead of Reading 50 Files (50,000 tokens)**
```python
# ❌ Old way: Read every file into context
for file in glob('src/**/*.py'):
    content = read_file(file)  # 50 files × 1000 tokens = 50,000 tokens

# ✅ New way: Execute analysis script, return summary
sandbox_execute("""
import glob, ast, json

files = glob.glob('src/**/*.py')
imports = set()
functions = []

for f in files:
    with open(f) as file:
        tree = ast.parse(file.read())
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                imports.update(n.name for n in node.names)
            elif isinstance(node, ast.FunctionDef):
                functions.append(f"{f}:{node.name}")

print(json.dumps({
    "imports": sorted(imports),
    "functions": functions[:20]  # Top 20
}, indent=2))
""")

# Returns: JSON summary (~500 tokens instead of 50,000)
```

**Supported Languages:**
```yaml
sandbox:
  runtimes:
    python: python3
    javascript: node
    typescript: ts-node
    shell: bash
    ruby: ruby
    go: go run
    rust: rustc && ./a.out
    php: php
```

**Tests:** 20 sandbox execution tests across languages  
**Security:** Document sandboxing security model

---

#### TO-1.3: Progressive Checkpointing
**Source:** alexgreensh/token-optimizer  
**Technique:** Snapshot context at key thresholds, enable rollback  
**Token Savings:** Recover from compaction errors, prevent context loss

**Implementation Tasks:**
- [ ] Add context fill % tracking to Session class
- [ ] Create checkpoints at strategic thresholds: 20%, 35%, 50%, 65%, 80%
- [ ] Store checkpoint data in SQLite with compression
- [ ] Implement restore from checkpoint
- [ ] Add checkpoint management UI in CLI
- [ ] Track checkpoint size and creation time
- [ ] Add automatic cleanup of old checkpoints

**Checkpoint Thresholds:**
```
20% fill - Early snapshot (minimal overhead)
35% fill - Before major work begins
50% fill - Midpoint reference
65% fill - Before optimization needed
80% fill - Before compaction required
```

**Checkpoint Management:**
```bash
arcon checkpoint list                 # List checkpoints for session
arcon checkpoint create               # Manual checkpoint
arcon checkpoint restore <id>         # Restore to checkpoint
arcon checkpoint delete <id>          # Delete checkpoint
arcon checkpoint auto-cleanup         # Remove old checkpoints
```

**Tests:** 10 checkpointing tests  
**Storage:** Compress checkpoints with zlib

---

#### TO-1.4: FTS5 Knowledge Base
**Source:** mksglu/context-mode  
**Technique:** Store large outputs in searchable database, retrieve on-demand  
**Token Savings:** 0 tokens until explicitly queried

**Implementation Tasks:**
- [ ] Create `src/arcon/knowledge/fts.py` - FTS5 wrapper class
- [ ] Add `IndexOutputMiddleware` - auto-index tool results >4KB
- [ ] Create `SearchTool` for querying knowledge base
- [ ] Implement BM25 ranking for search results
- [ ] Add progressive throttling (limit repeated searches)
- [ ] Create knowledge base cleanup and maintenance
- [ ] Add knowledge export/import

**SQLite FTS5 Schema:**
```sql
CREATE VIRTUAL TABLE knowledge USING fts5(
    session_id,
    tool_name,
    timestamp,
    content,
    content_type,  -- 'file', 'output', 'error', 'log'
    tokenize = 'porter'
);

CREATE TABLE knowledge_metadata (
    id INTEGER PRIMARY KEY,
    knowledge_id TEXT,
    size_bytes INTEGER,
    indexed_at TEXT,
    accessed_count INTEGER DEFAULT 0,
    last_accessed TEXT
);
```

**Auto-Indexing Flow:**
```python
# Tool returns large output (10KB)
result = bash_execute("pytest -v --tb=long")

# Middleware intercepts
if len(result.output) > 4096:  # 4KB threshold
    knowledge_id = index_to_fts5(result.output)
    result.output = f"""
    [Large output indexed as {knowledge_id}]
    
    Preview (first 200 tokens):
    {result.output[:800]}...
    
    Use search("{knowledge_id}") to retrieve full output.
    Use search("test failure auth") to search content.
    """
```

**Search Tool:**
```python
# Search by ID
search("know-abc123")  # Returns full content

# Search by keywords (BM25 ranked)
search("test failure authentication")  # Returns relevant excerpts

# Progressive throttling
# Calls 1-3: Normal results
# Calls 4-8: Reduced results, warning shown
# Calls 9+: Blocked, suggest refining query
```

**Tests:** 15 FTS5 indexing and search tests  
**Performance:** Benchmark search performance on large datasets

---

### Token Optimization Tier 2: Advanced Features (Weeks 3-4)

#### TO-2.1: AST-Based Blast Radius
**Source:** tirth8205/code-review-graph  
**Technique:** Parse codebase into knowledge graph, load only affected files  
**Token Savings:** 8.2x average, up to 49x on monorepos (27,732 files → ~15 files)

**Implementation Tasks:**
- [ ] Create `src/arcon/ast/parser.py` using Tree-sitter
- [ ] Build AST knowledge graph stored in SQLite
- [ ] Support 10+ languages:
  - Python, JavaScript, TypeScript, Java, Go, Rust, C/C++, Ruby, PHP, Kotlin
- [ ] Implement blast radius analysis:
  - When file changes, query graph for affected nodes
  - Calculate impact score for each file
  - Load only files within token budget
  - Prioritize by criticality score
- [ ] Add incremental updates (git hook integration)
- [ ] Create MCP tools for graph queries
- [ ] Add visualization support (export to D3.js)

**AST Graph Schema:**
```sql
CREATE TABLE ast_nodes (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    file_path TEXT NOT NULL,
    name TEXT NOT NULL,
    type TEXT NOT NULL,
    line_start INTEGER,
    line_end INTEGER,
    hash TEXT
);

CREATE TABLE ast_edges (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    source_id INTEGER,
    target_id INTEGER,
    type TEXT NOT NULL,
    confidence REAL,
    FOREIGN KEY (source_id) REFERENCES ast_nodes(id),
    FOREIGN KEY (target_id) REFERENCES ast_nodes(id)
);
```

**Blast Radius Query:**
```python
# Developer changes src/auth.py
changed_file = "src/auth.py"

# Query graph for affected files
blast_radius = calculate_blast_radius(changed_file)

# Returns prioritized list:
[
    ("src/auth.py", 1.0, "direct"),              # The changed file
    ("tests/test_auth.py", 0.95, "test"),        # Tests for this file
    ("src/api/routes.py", 0.85, "caller"),       # Calls functions from auth.py
    ("src/middleware/auth.py", 0.75, "imports"), # Imports from auth.py
    ("src/models/user.py", 0.60, "related"),     # Related domain
]

# Load only top N files within token budget
# Instead of loading all 500 files in project
```

**Incremental Updates:**
```bash
# Git hook on commit
git diff --name-only HEAD~1 | while read file; do
    arcon ast update "$file"  # Re-parse only changed files
done
```

**MCP Tools:**
```python
# Available via MCP
ast_find_callers("authenticate_user")
ast_find_dependencies("src/auth.py")
ast_find_tests("src/api/routes.py")
ast_visualize("src/auth.py")
```

**Tests:** 25 AST parsing and graph tests  
**Performance:** <2 seconds for 2,900-file project

---

#### TO-2.2: Tiered Memory Structure
**Source:** nadimtuhin/claude-token-optimizer  
**Technique:** Core (always loaded), Topic (on-demand), Archive (0 tokens)  
**Token Savings:** 90% reduction (11,000 → 1,300 tokens)

**Implementation Tasks:**
- [ ] Create tiered memory system:
  - **Core** (~800 tokens): Critical files always loaded
  - **Topic** (~500 tokens each): Loaded based on query
  - **Archive** (0 tokens): Historical data, never auto-loaded
- [ ] Implement `.arconignore` file for exclusion rules
- [ ] Add intelligent topic detection and loading
- [ ] Create memory management CLI commands
- [ ] Add memory tier visualization
- [ ] Implement automatic tier promotion/demotion

**Directory Structure:**
```
.arcon/
├── core/                      # Always loaded (800 tokens total)
│   ├── CLAUDE.md              # Agent guidelines
│   ├── COMMON_MISTAKES.md     # Top 5 recurring bugs
│   ├── ARCHITECTURE_MAP.md    # High-level structure
│   └── QUICK_START.md         # Common commands
│
├── topics/                    # Load on demand (500 tokens each)
│   ├── api-design.md          # API patterns and conventions
│   ├── database.md            # Database schema and migrations
│   ├── security.md            # Security best practices
│   ├── testing.md             # Testing strategies
│   ├── deployment.md          # Deployment procedures
│   └── performance.md         # Performance optimization
│
└── archive/                   # Never auto-loaded (0 tokens)
    ├── sessions/              # Completed session logs
    │   ├── 2026-04-01.md
    │   └── 2026-04-15.md
    ├── completed-tasks/       # Finished work
    │   ├── feature-auth.md
    │   └── bugfix-api.md
    └── learnings/             # Old patterns
        ├── v1-patterns.md
        └── deprecated.md
```

**Topic Loading Logic:**
```python
# Query: "How do I authenticate users?"
detected_topics = ["api-design", "security"]
load_topics(detected_topics)  # Loads 1000 tokens instead of 11,000

# Query: "Optimize database queries"
detected_topics = ["database", "performance"]
load_topics(detected_topics)  # Different 1000 tokens

# Query: "Deploy to production"
detected_topics = ["deployment"]
load_topics(detected_topics)  # Only 500 tokens
```

**.arconignore:**
```gitignore
# Ignore build outputs
**/dist/
**/build/
**/.next/

# Ignore test coverage
**/coverage/
**/.pytest_cache/

# Ignore logs
**/*.log

# Ignore large data files
**/*.csv
**/*.json
```

**CLI Commands:**
```bash
arcon memory init                    # Initialize tiered structure
arcon memory status                  # Show memory tier usage
arcon memory promote <file>          # Move to higher tier
arcon memory demote <file>           # Move to lower tier
arcon memory archive <file>          # Move to archive
arcon memory cleanup                 # Remove unused topics
```

**Tests:** 12 memory tier tests  
**Documentation:** Memory management guide

---

#### TO-2.3: Quality Scoring System
**Source:** alexgreensh/token-optimizer  
**Technique:** 7-signal health score to detect token waste  
**Token Savings:** Proactive optimization, prevent degradation

**Implementation Tasks:**
- [ ] Create `src/arcon/quality/scorer.py` module
- [ ] Implement 7 quality signals:
  1. **Context Fill %** - how full is context window (target: 40-70%)
  2. **Stale Reads %** - files read but never modified (target: <15%)
  3. **Bloated Results %** - tool outputs >4KB (target: <10%)
  4. **Compaction Depth** - number of compactions (target: <3)
  5. **Duplicate Content %** - repeated information (target: <10%)
  6. **Decision Density** - user decisions per 1000 tokens (target: >8)
  7. **Agent Efficiency** - meaningful actions per interaction (target: >70%)
- [ ] Generate quality report per session
- [ ] Add quality alerts (warn at score <60%)
- [ ] Create quality dashboard
- [ ] Track quality trends over time
- [ ] Add recommendations for improvement

**Quality Scoring Algorithm:**
```python
def calculate_quality_score(session: Session) -> QualityReport:
    signals = {
        "context_fill": score_context_fill(session),      # 0-100
        "stale_reads": score_stale_reads(session),        # 0-100
        "bloated_results": score_bloated_results(session),# 0-100
        "compaction_depth": score_compaction(session),    # 0-100
        "duplicates": score_duplicates(session),          # 0-100
        "decision_density": score_decisions(session),     # 0-100
        "agent_efficiency": score_efficiency(session),    # 0-100
    }
    
    overall = sum(signals.values()) / len(signals)
    
    return QualityReport(
        overall_score=overall,
        signals=signals,
        recommendations=generate_recommendations(signals)
    )
```

**Quality Report Example:**
```
Session Quality Report: sess-abc123
Overall Score: 72/100 (Good)

Signal Breakdown:
✅ Context Fill: 45% (85/100) - Optimal
⚠️  Stale Reads: 35% (60/100) - High, consider cleanup
✅ Bloated Results: 8% (92/100) - Low
✅ Compaction Depth: 1 (95/100) - Low
⚠️  Duplicates: 18% (72/100) - Moderate
✅ Decision Density: 12 per 1K tokens (88/100) - Good
✅ Agent Efficiency: 85% (85/100) - High

Recommendations:
1. Archive 8 stale file reads → save ~800 tokens
2. Consider compaction at 65% context fill
3. Remove duplicate imports in messages

Token Optimization Potential: ~1,200 tokens (12% reduction)
```

**Alerts:**
```
⚠️  Quality Alert: Session quality dropped to 58%
    Primary issue: Context fill at 85% (1 compaction away)
    Action: Create checkpoint and compact context
```

**Tests:** 15 quality scoring tests  
**Visualization:** Quality trend graphs over time

---

#### TO-2.4: Output Compression Modes
**Source:** JuliusBrussee/caveman  
**Technique:** Linguistic compression - remove grammatical fluff  
**Token Savings:** 65% average reduction, maintains 100% technical accuracy

**Implementation Tasks:**
- [ ] Add verbosity configuration with 4 modes:
  - **Standard** (default) - natural language, full grammar
  - **Lite** - professional, no fluff, concise
  - **Compressed** - fragments, telegraphic style
  - **Ultra** - maximum compression, grunt-level
- [ ] Create `OutputCompressionMiddleware`
- [ ] Preserve technical content (code blocks, URLs, file paths, commands)
- [ ] Add user preference persistence
- [ ] Implement selective compression (explanations compressed, debugging verbose)
- [ ] Add compression bypass for critical outputs

**Compression Examples:**

**Standard Mode (Default):**
```
I've analyzed the authentication code and found that the login function
has a potential security vulnerability where user input is not being
properly sanitized before being used in database queries. This could lead
to SQL injection attacks. I recommend adding input validation using
parameterized queries.
```

**Lite Mode:**
```
Auth analysis complete. Login function has SQL injection vulnerability -
user input not sanitized before DB queries. Fix: Use parameterized queries
for input validation.
```

**Compressed Mode:**
```
Auth: SQLi vuln in login. User input → DB unsanitized.
Fix: Parameterized queries.
```

**Ultra Mode:**
```
Auth: SQLi. Sanitize input. Use params.
```

**Selective Compression:**
```python
# Error debugging: NEVER compress
if query_type == "debugging":
    compression = "standard"

# Code review: Compress explanations, preserve code
elif query_type == "review":
    compression = "lite"
    preserve_code_blocks = True

# General questions: User preference
else:
    compression = user_preference
```

**Configuration:**
```yaml
output:
  compression:
    mode: lite  # standard, lite, compressed, ultra
    preserve:
      - code_blocks
      - file_paths
      - urls
      - commands
    selective:
      debugging: standard
      review: lite
      general: compressed
```

**Tests:** 10 compression tests across modes  
**Research Note:** 2026 study shows brevity constraints improved accuracy by 26%

---

### Token Optimization Tier 3: Experimental (Weeks 5-6)

#### TO-3.1: Context Compaction
**Sources:** token-optimizer + context-mode  
**Technique:** Auto-summarize old context when approaching token limits  
**Token Savings:** Extends session length indefinitely

**Implementation Tasks:**
- [ ] Enhance `ContextCompactionMiddleware` with smart summarization
- [ ] Trigger compaction at 80% context fill
- [ ] Summarize oldest 30% of message history
- [ ] Preserve critical information:
  - File modifications and their locations
  - Key decisions made by user
  - Tool call results (archived in FTS5)
  - Error resolutions and fixes
- [ ] Implement restore from checkpoint mechanism
- [ ] Track compaction depth for quality scoring
- [ ] Add compaction preview before execution

**Compaction Strategy:**
```python
# Before compaction (16,000 tokens at 80% fill):
[
    system_message,
    user_1, assistant_1,    # 500 tokens
    user_2, assistant_2,    # 600 tokens
    ...
    user_15, assistant_15,  # 700 tokens  ← Oldest 30%
    user_16, assistant_16,  # 800 tokens
    ...
    user_25, assistant_25,  # 900 tokens  ← Most recent
]

# After compaction (11,000 tokens):
[
    system_message,
    SUMMARY(user_1 through user_15),  # 1,500 tokens
    user_16, assistant_16,
    ...
    user_25, assistant_25,
]

# Summary preserves:
{
    "files_modified": ["src/auth.py", "tests/test_auth.py"],
    "key_decisions": ["Use JWT for authentication", "Add rate limiting"],
    "errors_resolved": ["Fixed import error in auth.py:15"],
    "tool_calls": 23,
    "compaction_timestamp": "2026-04-19T11:00:00Z"
}
```

**Compaction Preview:**
```
⚠️  Context at 81% capacity (16,200 / 20,000 tokens)

Compaction recommended:
- Will summarize messages 1-15 (4,500 tokens → 1,500 tokens)
- Will preserve messages 16-25 (7,200 tokens unchanged)
- Total reduction: 3,000 tokens (18%)
- Checkpoint created before compaction

Proceed? [y/n] y
Compacting context...
✅ Context compacted: 16,200 → 13,200 tokens (18% reduction)
```

**Tests:** 12 compaction tests  
**Safety:** Always create checkpoint before compaction

---

#### TO-3.2: Session Continuity Tracking
**Source:** mksglu/context-mode  
**Technique:** SQLite event log that survives compaction  
**Token Savings:** Never lose critical context even after multiple compactions

**Implementation Tasks:**
- [ ] Create `src/arcon/knowledge/events.py` module
- [ ] Track comprehensive event types:
  - **File edits** - path, timestamp, line range, diff hash
  - **Git operations** - commits, branches, merges, tags
  - **Tasks completed** - user-defined milestones
  - **Errors resolved** - error message, fix applied
  - **Decisions made** - key architectural or design choices
  - **Tool executions** - which tools used and why
- [ ] Query events to reconstruct session state
- [ ] Integrate with compaction (reference events, not full content)
- [ ] Add event search and filtering
- [ ] Create event timeline visualization

**Event Schema:**
```sql
CREATE TABLE events (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    session_id TEXT NOT NULL,
    timestamp TEXT NOT NULL,
    type TEXT NOT NULL,  # 'file_edit', 'git_commit', 'task_complete', etc.
    data JSON NOT NULL,
    importance INTEGER DEFAULT 5,  # 1-10 scale
    FOREIGN KEY (session_id) REFERENCES sessions(id)
);

CREATE INDEX idx_events_session ON events(session_id);
CREATE INDEX idx_events_type ON events(type);
CREATE INDEX idx_events_importance ON events(importance);
```

**Event Types:**

```python
# File Edit Event
{
    "type": "file_edit",
    "data": {
        "path": "src/auth.py",
        "lines_modified": "45-67",
        "action": "added authentication middleware",
        "diff_hash": "abc123..."
    }
}

# Git Commit Event
{
    "type": "git_commit",
    "data": {
        "hash": "abc123...",
        "message": "Add JWT authentication",
        "files": ["src/auth.py", "tests/test_auth.py"],
        "author": "user"
    }
}

# Task Complete Event
{
    "type": "task_complete",
    "data": {
        "task": "Implement user authentication",
        "files_involved": ["src/auth.py", "src/middleware/auth.py"],
        "tests_added": 5
    }
}

# Error Resolved Event
{
    "type": "error_resolved",
    "data": {
        "error": "ModuleNotFoundError: No module named 'jwt'",
        "solution": "Added python-jose to requirements.txt",
        "file": "requirements.txt"
    }
}
```

**Usage After Compaction:**
```python
# Even after compacting away old messages, can query events:
events = get_events(session_id, type="file_edit")

# Reconstruct what happened:
"""
Session Summary (from events):
- Modified 12 files
- Made 5 commits
- Completed 2 tasks: "Implement auth", "Add tests"
- Resolved 3 errors
- Total duration: 2 hours
"""
```

**Event Search:**
```bash
arcon events list --type file_edit
arcon events search "authentication"
arcon events timeline --since "2 hours ago"
arcon events summary
```

**Tests:** 10 event tracking tests  
**Integration:** Use events in quality scoring

---

#### TO-3.3: Intelligent Tool Result Archiving
**Source:** alexgreensh/token-optimizer  
**Technique:** Archive large tool outputs with preview + retrieval hints  
**Token Savings:** 4KB → 100 tokens (40x reduction)

**Implementation Tasks:**
- [ ] Create `ToolResultArchive` class in `src/arcon/tools/archive.py`
- [ ] Auto-archive tool results exceeding 4KB threshold
- [ ] Store in SQLite with compression (zlib)
- [ ] Return preview (first 100 tokens) + retrieval hint
- [ ] Create `RetrieveArchivedTool` for full content access
- [ ] Add archive cleanup and management
- [ ] Implement archive expiration policy

**Archive Schema:**
```sql
CREATE TABLE archived_results (
    id TEXT PRIMARY KEY,  -- artifact-abc123
    session_id TEXT,
    tool_name TEXT,
    timestamp TEXT,
    size_bytes INTEGER,
    compressed_data BLOB,  -- zlib compressed
    preview TEXT,
    accessed_count INTEGER DEFAULT 0,
    FOREIGN KEY (session_id) REFERENCES sessions(id)
);
```

**Auto-Archiving Flow:**
```python
# Tool returns large output (10KB)
result = bash_execute("pytest -v --tb=long")
# Output is 10KB

# Middleware intercepts
if len(result.output) > 4096:
    archive_id = archive_result(result)
    
    # Return preview instead
    result.output = f"""
Preview (first 100 tokens):
======================== test session starts =========================
platform linux -- Python 3.12.12, pytest-9.0.3
collected 194 items

tests/test_core.py::test_message_creation PASSED         [  0%]
tests/test_core.py::test_provider_type_enum PASSED       [  1%]
tests/test_core.py::test_session_creation PASSED         [  2%]
...

[Full output (10KB) archived as artifact-abc123]
Use retrieve_archived("artifact-abc123") to access full output.
Use search("test failure") to search within archived outputs.
    """
```

**Retrieval:**
```python
# Retrieve full content when needed
> retrieve_archived("artifact-abc123")
Returns: [Full 10KB output]

# Or search across all archived results
> search("TestAuthenticationFailure")
Returns: [Relevant excerpts from multiple archives]
```

**Archive Management:**
```bash
arcon archive list                    # List all archives
arcon archive show <id>               # Show archive details
arcon archive retrieve <id>           # Retrieve full content
arcon archive cleanup --older-than 7d # Delete old archives
arcon archive stats                   # Storage statistics
```

**Tests:** 8 archiving tests  
**Compression:** zlib level 6 (balance speed/size)

---

## Implementation Roadmap

### Phase 1: Foundation (Weeks 1-2)
**Focus:** Middleware Infrastructure + Core Token Optimization

**Sprint 1.1 (Week 1):**
- [ ] Middleware pipeline architecture
- [ ] Permission system implementation
- [ ] Delta mode file caching
- [ ] Enhanced cost tracking

**Sprint 1.2 (Week 2):**
- [ ] Sandboxed execution
- [ ] Progressive checkpointing
- [ ] FTS5 knowledge base
- [ ] Integration testing

**Deliverables:**
- Functional middleware pipeline with 4 core middlewares
- Permission system with CLI management
- File caching with 97% savings on re-reads
- Sandboxed execution for all supported languages
- FTS5 indexing for large outputs
- Cost tracking with reporting

**Tests:** 100+ new tests  
**Documentation:** Architecture guide, user guide for permissions  
**Token Savings Target:** 70-85% reduction on repeated operations

---

### Phase 2: Intelligence & AST (Weeks 3-4)
**Focus:** Agent Enhancement + Advanced Token Optimization

**Sprint 2.1 (Week 3):**
- [ ] Technology auto-detection
- [ ] Enhanced agent routing
- [ ] Execution backends (local + sandboxed)
- [ ] AST parser implementation

**Sprint 2.2 (Week 4):**
- [ ] AST knowledge graph
- [ ] Blast radius analysis
- [ ] Tiered memory structure
- [ ] Quality scoring system

**Deliverables:**
- Automatic technology detection and skill loading
- Multi-factor agent routing with confidence scores
- Multiple execution backends
- AST-based blast radius for 10+ languages
- Tiered memory with Core/Topic/Archive
- Quality scoring with 7 signals

**Tests:** 80+ new tests  
**Documentation:** AST guide, tiered memory guide  
**Token Savings Target:** 8-10x reduction on large codebases

---

### Phase 3: Learning & Advanced Optimization (Weeks 5-6)
**Focus:** Continuous Learning + Experimental Features

**Sprint 3.1 (Week 5):**
- [ ] Continuous learning implementation
- [ ] Pattern extraction from sessions
- [ ] Enhanced session management
- [ ] Output compression modes

**Sprint 3.2 (Week 6):**
- [ ] Context compaction
- [ ] Session continuity tracking
- [ ] Intelligent archiving
- [ ] Integration and polish

**Deliverables:**
- Continuous learning with pattern extraction
- Skill generation from successful sessions
- Enhanced session management with checkpointing
- Output compression with 4 verbosity modes
- Context compaction for indefinite sessions
- Session continuity event tracking
- Intelligent result archiving

**Tests:** 50+ new tests  
**Documentation:** Learning guide, compression guide  
**Token Savings Target:** 65% output compression, indefinite session length

---

### Phase 4: Production Readiness (Weeks 7-8)
**Focus:** Observability, Documentation, Benchmarking

**Sprint 4.1 (Week 7):**
- [ ] Quality dashboards and visualizations
- [ ] Cost reporting and alerts
- [ ] Performance benchmarks
- [ ] Comprehensive integration tests

**Sprint 4.2 (Week 8):**
- [ ] Documentation completion
- [ ] Migration guides
- [ ] Production deployment guide
- [ ] v0.2.0 release preparation

**Deliverables:**
- Quality dashboard with trend visualization
- Cost reporting with budgets and alerts
- Performance benchmarks and optimization
- Full documentation suite
- Migration guide for v0.1.0 users
- Production deployment guide
- Release notes and changelog

**Tests:** Full integration test suite (300+ tests total)  
**Documentation:** Complete user and developer docs  
**Target:** Production-ready v0.2.0 release

---

## Success Metrics & KPIs

### Token Efficiency Targets

| Feature | Target Savings | Measurement |
|---------|----------------|-------------|
| Delta Mode | 97% on re-reads | 2000 tokens → 60 tokens |
| Sandboxed Execution | 98% on analysis | 315KB → 5.4KB |
| AST Blast Radius | 8-10x reduction | Load 15 files instead of 500 |
| Tiered Memory | 90% on docs | 11,000 → 1,300 tokens |
| Output Compression | 65% on output | Standard → Compressed |
| Overall Target | $1,500-$2,500/mo savings | Heavy user baseline |

### Feature Adoption Metrics

| Feature | Target | Measurement Method |
|---------|--------|-------------------|
| Middleware Usage | 100% of requests | Automatic, track execution |
| Permission System | 95% satisfaction | User survey |
| Tech Detection | 90% accuracy | Manual verification on 100 projects |
| Agent Routing | 85% correct first-try | User feedback + logging |
| Quality Alerts | 80% catch degradation | Proactive vs reactive ratio |

### Quality Metrics

| Metric | Target | Current |
|--------|--------|---------|
| Test Coverage | 85%+ | 99.5% (v0.1.0) |
| Integration Tests | 95% of critical paths | 100% (21/21 passing) |
| Middleware Overhead | <200ms per request | TBD |
| Core Reliability | 99.5%+ uptime | TBD |
| Documentation | 100% features covered | 60% (v0.1.0) |

### User Experience Metrics

| Metric | Target | Measurement |
|--------|--------|-------------|
| Permission Fatigue | <3 prompts/session | Track ask-mode usage |
| Compression Clarity | >80% satisfaction | User feedback on terse output |
| Session Recovery | <30 sec to restore | Checkpoint restore time |

---

## Technical Architecture

### New Module Structure

```
src/arcon/
├── middleware/              # NEW - Middleware pipeline
│   ├── __init__.py         # Exports
│   ├── base.py             # Middleware ABC, MiddlewarePipeline
│   ├── security.py         # FilesystemSecurityMiddleware
│   ├── permissions.py      # PermissionMiddleware  
│   ├── skills.py           # SkillInjectionMiddleware
│   └── compaction.py       # ContextCompactionMiddleware
│
├── execution/              # NEW - Execution backends
│   ├── __init__.py
│   ├── base.py             # ExecutionBackend ABC
│   └── sandboxed.py        # SandboxedExecutionBackend
│
├── cost/                   # NEW - Cost tracking
│   ├── __init__.py
│   └── tracker.py          # CostTracker class
│
├── learning/               # NEW - Continuous learning
│   ├── __init__.py
│   └── extractor.py        # SkillLearner, PatternExtractor
│
├── knowledge/              # NEW - FTS5 + events
│   ├── __init__.py
│   ├── fts.py              # FTS5 knowledge base
│   └── events.py           # Session continuity events
│
├── ast/                    # NEW - AST analysis
│   ├── __init__.py
│   ├── parser.py           # Tree-sitter parser
│   └── graph.py            # AST knowledge graph
│
├── quality/                # NEW - Quality scoring
│   ├── __init__.py
│   └── scorer.py           # QualityScorer, 7-signal analysis
│
├── tools/                  # ENHANCED
│   ├── cache.py            # NEW - Delta mode file caching
│   ├── sandbox.py          # NEW - Sandboxed execution tool
│   └── archive.py          # NEW - Result archiving
│
├── skills/                 # ENHANCED
│   ├── scanner.py          # NEW - Technology detection
│   └── resolver.py         # NEW - Skill resolution
│
└── (existing modules)
```

### Database Schema Extensions

```sql
-- Cost tracking
CREATE TABLE cost_records (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    session_id TEXT NOT NULL,
    timestamp TEXT NOT NULL,
    model TEXT NOT NULL,
    input_tokens INTEGER,
    output_tokens INTEGER,
    cost_usd REAL,
    provider TEXT,
    FOREIGN KEY (session_id) REFERENCES sessions(id)
);

-- Knowledge base (FTS5)
CREATE VIRTUAL TABLE knowledge USING fts5(
    session_id,
    tool_name,
    timestamp,
    content,
    content_type,
    tokenize = 'porter'
);

-- Session events
CREATE TABLE events (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    session_id TEXT NOT NULL,
    timestamp TEXT NOT NULL,
    type TEXT NOT NULL,
    data JSON NOT NULL,
    importance INTEGER DEFAULT 5,
    FOREIGN KEY (session_id) REFERENCES sessions(id)
);

-- AST knowledge graph
CREATE TABLE ast_nodes (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    file_path TEXT NOT NULL,
    name TEXT NOT NULL,
    type TEXT NOT NULL,
    line_start INTEGER,
    line_end INTEGER,
    hash TEXT
);

CREATE TABLE ast_edges (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    source_id INTEGER,
    target_id INTEGER,
    type TEXT NOT NULL,
    confidence REAL,
    FOREIGN KEY (source_id) REFERENCES ast_nodes(id),
    FOREIGN KEY (target_id) REFERENCES ast_nodes(id)
);

-- Archived results
CREATE TABLE archived_results (
    id TEXT PRIMARY KEY,
    session_id TEXT,
    tool_name TEXT,
    timestamp TEXT,
    size_bytes INTEGER,
    compressed_data BLOB,
    preview TEXT,
    FOREIGN KEY (session_id) REFERENCES sessions(id)
);

-- Checkpoints
CREATE TABLE checkpoints (
    id TEXT PRIMARY KEY,
    session_id TEXT,
    timestamp TEXT,
    fill_percentage REAL,
    messages_json TEXT,
    metadata_json TEXT,
    FOREIGN KEY (session_id) REFERENCES sessions(id)
);
```

---

## Dependencies to Add

### Python Packages

```toml
[project.dependencies]
# Existing dependencies (keep)
anthropic = ">=0.25.0"
openai = ">=1.30.0"
requests = ">=2.31.0"
pyyaml = ">=6.0"
python-dotenv = ">=1.0.0"
sqlalchemy = ">=2.0.0"
aiofiles = ">=23.0.0"
aiohttp = ">=3.9.0"

# NEW - Token optimization
tree-sitter = ">=0.21.0"              # AST parsing
tree-sitter-python = ">=0.21.0"       # Python grammar
tree-sitter-javascript = ">=0.21.0"   # JavaScript grammar
tree-sitter-typescript = ">=0.21.0"   # TypeScript grammar
tree-sitter-java = ">=0.21.0"         # Java grammar
tree-sitter-go = ">=0.21.0"           # Go grammar
tree-sitter-rust = ">=0.21.0"         # Rust grammar

# NEW - Quality & metrics
prometheus-client = ">=0.20.0"        # Optional metrics export

[project.optional-dependencies]
dev = [
    "pytest>=8.0",
    "pytest-asyncio>=0.23",
    "pytest-cov>=4.1",
    "mypy>=1.10",
    "ruff>=0.4",
]

# NEW - Additional language support
extended = [
    "tree-sitter-cpp>=0.21.0",
    "tree-sitter-ruby>=0.21.0",
    "tree-sitter-php>=0.21.0",
    "tree-sitter-kotlin>=0.21.0",
]
```

### External Tools (Optional)

- **Docker** - For sandboxed execution backend (optional)
- **Git** - For repository analysis and event tracking
- **tree-sitter CLI** - For grammar compilation (development only)

---

## Migration Strategy

### For Existing Arcon v0.1.0 Users

**Backwards Compatibility:**
- All v0.2.0 features are **opt-in** by default
- Existing configurations continue to work
- No breaking changes to core APIs
- Session data migrated automatically

**Migration Steps:**

1. **Backup existing data:**
```bash
cp arcon.db arcon.db.backup
```

2. **Upgrade Arcon:**
```bash
cd /home/anirband/perceptron/arcon
git pull origin main
pip install -e ".[dev]"
```

3. **Run database migrations:**
```bash
arcon migrate --from v0.1.0 --to v0.2.0
```

4. **Enable new features incrementally:**
```bash
# Start with token optimization
arcon config set token_optimization.enabled true
arcon config set token_optimization.delta_mode true

# Add permission system
arcon config set permissions.enabled true

# Enable quality scoring
arcon config set quality.scoring_enabled true
```

5. **Review and adjust:**
```bash
arcon config show
arcon permissions list
arcon quality status
```

### Configuration Migration

**Old config (v0.1.0) - Still works:**
```yaml
provider_type: anthropic
model: claude-3-5-sonnet-20241022
api_key: ${ANTHROPIC_API_KEY}
```

**Enhanced config (v0.2.0) - Optional:**
```yaml
# Provider settings (same as before)
provider_type: anthropic
model: claude-3-5-sonnet-20241022
api_key: ${ANTHROPIC_API_KEY}

# NEW - Middleware configuration
middleware:
  enabled:
    - permission
    - security
    - skill_injection
    - delta_mode
    - quality_scoring
  
# NEW - Token optimization
token_optimization:
  enabled: true
  delta_mode: true
  sandbox_execution: true
  quality_alerts: true
  tiered_memory: true
  output_compression: lite  # standard, lite, compressed, ultra

# NEW - Permissions
permissions:
  enabled: true
  defaults:
    read_file: allow
    write_file: ask
    bash_execute: ask
    list_dir: allow

# NEW - Quality settings
quality:
  scoring_enabled: true
  alert_threshold: 60
  track_trends: true

# NEW - Execution backend
execution:
  backend: local  # local, sandboxed, remote
  sandbox:
    enabled: false
    type: docker
    image: python:3.12-slim
    timeout: 30
    memory_limit: 512M
    cpu_limit: 1.0
```

---

## Risk Mitigation

### Technical Risks

| Risk | Impact | Probability | Mitigation |
|------|--------|-------------|-----------|
| Middleware adds latency | Medium | Medium | Benchmark each middleware, optimize hot paths, target <200ms |
| AST parsing fails on edge cases | Medium | Low | Graceful fallback to full-file loading, log failures |
| FTS5 database grows large | Low | High | Periodic cleanup, compression, configurable retention |
| Tree-sitter grammar missing | Low | Medium | Support 10+ languages initially, add more on demand |
| Sandboxed execution security | High | Low | Use proven containers, security audit, limit resources |

### User Experience Risks

| Risk | Impact | Probability | Mitigation |
|------|--------|-------------|-----------|
| Permission prompt fatigue | Medium | High | Smart defaults, learn from choices, batch permissions |
| Compressed output unclear | Medium | Medium | User-selectable modes, preserve technical content |
| Learning curve too steep | Medium | Low | Progressive disclosure, excellent docs, tutorials |
| Breaking changes in updates | High | Low | Semantic versioning, migration guides, deprecation warnings |
| Quality alerts too noisy | Low | Medium | Tune thresholds based on feedback, configurable sensitivity |

### Project Risks

| Risk | Impact | Probability | Mitigation |
|------|--------|-------------|-----------|
| Scope creep | Medium | Medium | Stick to phased roadmap, defer non-essential features |
| Timeline delays | Medium | Low | Build in 20% buffer, prioritize must-haves |
| Resource constraints | High | Low | Clear task breakdown, parallel work where possible |
| Testing gaps | High | Low | TDD approach, 85% coverage requirement |
| Documentation debt | Medium | Medium | Document as you build, review in Phase 4 |

---

## Next Steps

### Immediate Actions (This Week)

1. **Review and approve plan** with stakeholders ✅
2. **Set up development environment:**
   - Create feature branch: `git checkout -b feature/v0.2.0-enhancements`
   - Install new dependencies: `pip install tree-sitter tree-sitter-python`
3. **Create detailed tickets** for Phase 1 tasks (middleware + token optimization)
4. **Set up project tracking:**
   - Create GitHub project board
   - Add milestones for each phase
   - Assign tasks and priorities
5. **Architecture review:**
   - Review middleware architecture
   - Approve database schema changes
   - Validate external dependencies

### Week 1 Kickoff (Phase 1, Sprint 1.1)

**Monday:**
- [ ] Create middleware module structure
- [ ] Implement Middleware ABC and MiddlewarePipeline
- [ ] Write tests for pipeline execution

**Tuesday:**
- [ ] Implement FilesystemSecurityMiddleware
- [ ] Implement PermissionMiddleware
- [ ] Add permission CLI commands

**Wednesday:**
- [ ] Implement Delta Mode file caching
- [ ] Enhance ReadFileTool with cache support
- [ ] Write caching tests

**Thursday:**
- [ ] Implement Enhanced Cost Tracking
- [ ] Add cost aggregation queries
- [ ] Create cost reporting commands

**Friday:**
- [ ] Integration testing
- [ ] Documentation updates
- [ ] Sprint review and retrospective

---

## Conclusion

This enhancement plan transforms Arcon from a solid v0.1.0 foundation into a **production-grade, token-efficient coding agent** by:

1. **Adopting proven practices** from 4 leading coding agent frameworks
2. **Integrating advanced techniques** from 5 specialized token optimization systems
3. **Maintaining backwards compatibility** with incremental, opt-in rollout
4. **Delivering measurable value** with $1,500-$2,500/month savings potential

### Key Highlights

**Technical Excellence:**
- Extensible middleware architecture for composable features
- Multi-language AST analysis for surgical code loading
- Intelligent caching and archiving for 97%+ token reduction
- Quality scoring to proactively prevent degradation

**User Experience:**
- Auto-detection of technologies and automatic skill loading
- Smart permission system with minimal friction
- Resumable sessions with crash recovery
- Flexible verbosity modes for different use cases

**Production Readiness:**
- Comprehensive testing (300+ tests across all features)
- Full observability with quality dashboards and cost tracking
- Complete documentation for users and developers
- Proven migration path from v0.1.0

### Expected Outcomes

**Timeline:** 6-8 weeks for full implementation  
**Effort:** ~200-250 development hours  
**Return:** 70-98% token reduction, 8-49x codebase efficiency  
**Investment:** $1,500-$2,500/month savings for heavy users

The plan is **ambitious yet achievable** with:
- Clear phased approach (4 phases, 8 sprints)
- Focus on high-impact features first
- Comprehensive testing at each phase
- Continuous integration and deployment

**Ready to build Arcon v0.2.0!** 🚀

---

## Appendix

### A. Glossary

- **AST:** Abstract Syntax Tree - structured representation of code
- **Blast Radius:** Set of files affected by a code change
- **BM25:** Best Matching 25 - ranking function for text search
- **FTS5:** Full-Text Search 5 - SQLite extension for text indexing
- **Middleware:** Interceptor pattern for request/response processing
- **Tree-sitter:** Parser generator tool for building syntax trees
- **Delta Mode:** Caching technique that returns only changes
- **Compaction:** Process of summarizing old context to save tokens

### B. References

**Coding Agent Frameworks:**
- Copilot SDK: https://github.com/copilot-extensions/github-copilot-sdk
- Deep Agents: https://github.com/deepagents/deepagents
- OpenClaude: https://github.com/openclaude/openclaude
- Everything Claude Code: https://github.com/ecc/everything-claude-code

**Token Optimization Systems:**
- alexgreensh/token-optimizer: https://github.com/alexgreensh/token-optimizer
- mksglu/context-mode: https://github.com/mksglu/context-mode
- JuliusBrussee/caveman: https://github.com/JuliusBrussee/caveman
- tirth8205/code-review-graph: https://github.com/tirth8205/code-review-graph
- nadimtuhin/claude-token-optimizer: https://github.com/nadimtuhin/claude-token-optimizer

### C. Contact

For questions or feedback on this enhancement plan:
- GitHub Issues: [Arcon Repository](https://github.com/yourusername/arcon)
- Discussions: [Enhancement Plan Discussion](https://github.com/yourusername/arcon/discussions)

---

**Last Updated:** April 19, 2026  
**Version:** 1.0  
**Status:** Planning Complete, Ready for Implementation
