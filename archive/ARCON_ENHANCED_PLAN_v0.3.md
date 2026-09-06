# Arcon Enhanced Plan v0.3.0
**Strategic Integration of Industry-Leading Frameworks**

**Version:** 0.3.0 Enhanced  
**Date Created:** April 26, 2026  
**Status:** Strategic Planning Phase  
**Target:** Transform Arcon into enterprise-grade coding agent platform by synthesizing best practices from leading frameworks

---

## Executive Summary

This plan synthesizes **proven patterns** from 6 industry frameworks into Arcon's enhancement roadmap:

| Framework | Contribution | Relevance |
|-----------|--------------|-----------|
| **Onyx** | MCP integration, knowledge graphs, tool merging, deep research | 🔴 CRITICAL |
| **Copilot SDK** | JSON-RPC protocol, permission system, session management | 🔴 CRITICAL |
| **Deep Agents** | Middleware architecture, execution backends, profile system | 🟡 HIGH |
| **ECC** | Agent specialization patterns, skill organization, multi-harness | 🟡 HIGH |
| **OpenClaude** | Provider agnosticism, terminal UI, streaming, cost tracking | 🟡 HIGH |
| **autoskills** | Tech stack auto-detection, skill auto-injection | 🟢 MEDIUM |

### Expected Impact by Phase

| Phase | Feature | Token Savings | Cost Impact |
|-------|---------|---------------|------------|
| Phase 1 (Weeks 1-4) | Middleware, Permissions, Cost Tracking | 15-20% | -$225-$500/mo |
| Phase 2 (Weeks 5-8) | Auto-detection, Agent Routing, Skill Injection | 30-40% | -$450-$1000/mo |
| Phase 3 (Weeks 9-12) | Knowledge Graphs, Tool Merging, Deep Research | 70-90% | -$1050-$2250/mo |
| Phase 4 (Weeks 13-16) | MCP Integration, Execution Backends | 10-15% | -$150-$375/mo |
| **TOTAL** | Full Platform | **70-98%** | **$1,500-$2,500/mo** |

---

## Architecture Evolution

### Current State (v0.1.0)
```
┌─────────────────────────────────┐
│  CLI Interface                  │
└────────────┬────────────────────┘
             │
             ▼
┌─────────────────────────────────┐
│  5 Agents (Router)              │
│  ├─ CodingAssistant             │
│  ├─ Debugger                    │
│  ├─ CodeReviewer                │
│  ├─ TestEngineer                │
│  └─ DocumentationWriter          │
└────────────┬────────────────────┘
             │
             ▼
┌─────────────────────────────────┐
│  Tools & Skills                 │
│  ├─ 34 ECC Skills (loaded)      │
│  └─ Basic Tools (file, bash)    │
└────────────┬────────────────────┘
             │
             ▼
┌─────────────────────────────────┐
│  Providers (Multi)              │
│  ├─ Anthropic                   │
│  ├─ OpenAI                      │
│  └─ Ollama                      │
└────────────┬────────────────────┘
             │
             ▼
┌─────────────────────────────────┐
│  SQLite Storage                 │
│  └─ Sessions, Skills            │
└─────────────────────────────────┘
```

### Target State (v0.4.0+)
```
┌──────────────────────────────────────────────────┐
│  Multi-Channel Interface Layer                   │
│  ├─ CLI (Terminal)  [OpenClaude pattern]         │
│  ├─ JSON-RPC        [Copilot SDK pattern]        │
│  ├─ MCP Server      [Onyx pattern]               │
│  └─ Web API         [FastAPI]                    │
└────────────┬─────────────────────────────────────┘
             │
             ▼
┌──────────────────────────────────────────────────┐
│  Middleware Pipeline Layer      [Deep Agents]    │
│  ├─ Filesystem Security         [Validate paths] │
│  ├─ Permission Middleware       [Allow/deny/ask] │
│  ├─ Skill Injection Middleware  [Auto-detect]   │
│  ├─ Tool Call Merging          [Onyx pattern]   │
│  ├─ Context Compaction         [Auto-summarize] │
│  └─ Tracing & Observability    [Telemetry]     │
└────────────┬─────────────────────────────────────┘
             │
             ▼
┌──────────────────────────────────────────────────┐
│  Enhanced Agent Orchestration       [ECC pattern]│
│  ├─ Intelligent Router             [Multi-factor]│
│  ├─ 10+ Specialized Agents         [Expand 5→10] │
│  ├─ Sub-agent Delegation          [Hierarchical]│
│  └─ Agent Capability Registry      [Metadata]   │
└────────────┬─────────────────────────────────────┘
             │
             ▼
┌──────────────────────────────────────────────────┐
│  Intelligence Layer         [Onyx + Deep Agents] │
│  ├─ Knowledge Graph         [Entity extraction]  │
│  ├─ Semantic Compression    [KG-based]          │
│  ├─ Deep Research           [Multi-step]        │
│  ├─ Execution Backends      [Local/Sandbox/etc] │
│  └─ Profile System          [Model-specific]    │
└────────────┬─────────────────────────────────────┘
             │
             ▼
┌──────────────────────────────────────────────────┐
│  Tool & Skill System              [autoskills]   │
│  ├─ Project Scanner               [Tech detect]  │
│  ├─ Skill Resolver                [Auto-inject]  │
│  ├─ Advanced Tools                [Code exec]    │
│  ├─ Tool Runner with Merging      [Onyx pattern]│
│  └─ 150+ Skills (Expand 34→150+)  [ECC-like]    │
└────────────┬─────────────────────────────────────┘
             │
             ▼
┌──────────────────────────────────────────────────┐
│  Multi-Provider Engine                           │
│  ├─ Anthropic   (Cost optimized)                 │
│  ├─ OpenAI      (GPT models)                     │
│  ├─ Ollama      (Local)                          │
│  └─ Provider Abstraction [OpenClaude pattern]    │
└────────────┬─────────────────────────────────────┘
             │
             ▼
┌──────────────────────────────────────────────────┐
│  Storage & Persistence Layer                     │
│  ├─ PostgreSQL  (Production upgrade)             │
│  ├─ Redis       (Caching/Sessions)               │
│  ├─ Vector DB   (Embeddings - optional)          │
│  └─ SQLite      (Local fallback)                 │
└──────────────────────────────────────────────────┘
```

---

## Phase 1: Foundation (Weeks 1-4)
**Goal:** Build core infrastructure for middleware, permissions, and cost tracking  
**Impact:** 15-20% token reduction, establish extension points

### 1.1 Middleware Pipeline Architecture [Deep Agents Pattern]

**Source:** Deep Agents middleware stack + Copilot SDK permission system

**What to Build:**
```python
# src/arcon/middleware/base.py
from abc import ABC, abstractmethod
from typing import Any, Optional
from dataclasses import dataclass

@dataclass
class MiddlewareContext:
    """Execution context passed through middleware chain"""
    session_id: str
    agent_name: str
    provider: str
    messages: list[dict]
    metadata: dict[str, Any]

class Middleware(ABC):
    """Base class for all middleware"""
    
    @abstractmethod
    async def process_input(self, ctx: MiddlewareContext) -> MiddlewareContext:
        """Process messages before LLM call"""
        pass
    
    @abstractmethod
    async def process_tool_call(
        self, 
        ctx: MiddlewareContext,
        tool_name: str,
        args: dict[str, Any]
    ) -> tuple[str, dict[str, Any]]:
        """Process/validate tool calls"""
        pass
    
    @abstractmethod
    async def process_output(
        self,
        ctx: MiddlewareContext,
        output: str
    ) -> str:
        """Process LLM output before returning"""
        pass

class MiddlewarePipeline:
    """Execute middleware chain sequentially"""
    
    def __init__(self, middlewares: list[Middleware]):
        self.middlewares = middlewares
    
    async def process_input(self, ctx: MiddlewareContext) -> MiddlewareContext:
        for mw in self.middlewares:
            ctx = await mw.process_input(ctx)
        return ctx
    
    async def process_tool_call(
        self, ctx: MiddlewareContext, tool_name: str, args: dict
    ) -> tuple[str, dict]:
        for mw in self.middlewares:
            tool_name, args = await mw.process_tool_call(ctx, tool_name, args)
        return tool_name, args
    
    async def process_output(self, ctx: MiddlewareContext, output: str) -> str:
        for mw in self.middlewares:
            output = await mw.process_output(ctx, output)
        return output
```

**Middleware Implementations:**

1. **FilesystemSecurityMiddleware** - Prevent path traversal attacks
   ```python
   class FilesystemSecurityMiddleware(Middleware):
       """Prevent access outside workspace"""
       
       async def process_tool_call(self, ctx, tool_name, args):
           if tool_name in ["read_file", "write_file", "delete_file"]:
               file_path = args.get("path", "")
               if ".." in file_path or file_path.startswith("/"):
                   raise SecurityException(f"Access denied: {file_path}")
           return tool_name, args
   ```

2. **PermissionMiddleware** - Tool access control (from Copilot SDK)
   ```python
   class PermissionMiddleware(Middleware):
       """Control which tools agents can call"""
       
       def __init__(self, permission_store):
           self.store = permission_store
       
       async def process_tool_call(self, ctx, tool_name, args):
           perm = self.store.get_permission(tool_name, ctx.agent_name)
           
           if perm == "deny":
               raise PermissionDenied(f"{ctx.agent_name} cannot call {tool_name}")
           elif perm == "ask":
               allowed = await self.ask_user_permission(tool_name, args)
               if not allowed:
                   raise PermissionDenied("User denied permission")
           
           return tool_name, args
   ```

3. **ContextCompactionMiddleware** - Auto-summarize when context fills
   ```python
   class ContextCompactionMiddleware(Middleware):
       """Compress context when approaching token limits"""
       
       async def process_input(self, ctx: MiddlewareContext) -> MiddlewareContext:
           messages = ctx.messages
           total_tokens = sum(self.count_tokens(m) for m in messages)
           
           if total_tokens > 20000:  # Auto-compact at 20K tokens
               # Summarize older messages
               messages = await self.compress_messages(messages)
               ctx.messages = messages
           
           return ctx
   ```

**Integration Point:**
```python
# In src/arcon/core/session.py
class Session:
    def __init__(self, agent, middleware_pipeline):
        self.agent = agent
        self.middleware = middleware_pipeline
    
    async def invoke(self, messages: list[dict]) -> str:
        ctx = MiddlewareContext(
            session_id=self.id,
            agent_name=self.agent.name,
            provider=self.agent.provider,
            messages=messages,
            metadata={}
        )
        
        # Process input through middleware
        ctx = await self.middleware.process_input(ctx)
        
        # Invoke LLM
        response = await self.agent.invoke(ctx.messages)
        
        # Process output through middleware
        output = await self.middleware.process_output(ctx, response)
        
        return output
```

**Tests Required:**
- 20+ middleware tests (order, chaining, exceptions)
- 10+ security tests (path traversal, injection)
- 5+ integration tests (middleware + agent)

---

### 1.2 Permission System [Copilot SDK Pattern]

**Source:** Copilot SDK's ElicitationHandler + permission model

**What to Build:**
```python
# src/arcon/permissions/models.py
from enum import Enum
from dataclasses import dataclass
from typing import Optional

class PermissionState(str, Enum):
    """Permission can be: allow, deny, ask, not_set"""
    ALLOW = "allow"
    DENY = "deny"
    ASK = "ask"
    NOT_SET = "not_set"

@dataclass
class Permission:
    tool_name: str
    agent_name: str  # "*" for all agents
    state: PermissionState
    remember: bool = False  # Remember future decisions

class PermissionStore:
    """Persistent permission storage"""
    
    def __init__(self, db_path: str):
        self.db = SQLiteDB(db_path)
    
    def get_permission(self, tool_name: str, agent_name: str) -> PermissionState:
        """Get permission with fallback: specific → all agents → default"""
        perm = self.db.query(tool_name, agent_name)
        if perm:
            return perm.state
        
        # Fallback to wildcard agent
        perm = self.db.query(tool_name, "*")
        if perm:
            return perm.state
        
        # Use default
        return DEFAULT_PERMISSIONS.get(tool_name, PermissionState.ASK)
    
    def set_permission(
        self,
        tool_name: str,
        agent_name: str,
        state: PermissionState,
        remember: bool = False
    ) -> None:
        """Save permission decision"""
        perm = Permission(tool_name, agent_name, state, remember)
        self.db.save(perm)

# Default permission matrix
DEFAULT_PERMISSIONS = {
    # Read-only (safe) - allow by default
    "read_file": PermissionState.ALLOW,
    "list_dir": PermissionState.ALLOW,
    "grep": PermissionState.ALLOW,
    "glob": PermissionState.ALLOW,
    
    # Modifies filesystem (risky) - ask by default
    "write_file": PermissionState.ASK,
    "edit_file": PermissionState.ASK,
    "delete_file": PermissionState.ASK,
    "create_dir": PermissionState.ASK,
    
    # Executes code (dangerous) - ask by default
    "bash_execute": PermissionState.ASK,
    "python_execute": PermissionState.ASK,
    
    # Network (watch closely) - ask by default
    "web_search": PermissionState.ASK,
    "open_url": PermissionState.ASK,
}
```

**CLI Commands:**
```bash
# View permissions
arcon perms list
arcon perms list --tool read_file
arcon perms list --agent CodingAssistant

# Set permissions
arcon perms set read_file allow --agent "*"
arcon perms set bash_execute ask --agent "Debugger"
arcon perms set write_file deny --agent "CodeReviewer"

# Reset to defaults
arcon perms reset
```

**User Interaction:**
```
Agent wants to call: bash_execute("pytest tests/")

╭─ Permission Required ─────────────────────────╮
│                                               │
│ Tool:  bash_execute                           │
│ Agent: Debugger                               │
│ Cmd:   pytest tests/                          │
│                                               │
│ [Y]es  [N]o  [A]lways  Ne[V]er  [?]Help       │
│                                               │
╰───────────────────────────────────────────────╯
```

**Tests:**
- 15 permission flow tests
- 8 persistence tests
- 6 default permission tests

---

### 1.3 Enhanced Cost Tracking [OpenClaude Pattern]

**Source:** OpenClaude's cost-tracker + OpenAI/Anthropic pricing

**What to Build:**
```python
# src/arcon/cost/tracker.py
from dataclasses import dataclass
from datetime import datetime
import json

@dataclass
class TokenCount:
    input_tokens: int
    output_tokens: int
    
    @property
    def total(self) -> int:
        return self.input_tokens + self.output_tokens

@dataclass
class CostEntry:
    """Single API call cost"""
    timestamp: datetime
    session_id: str
    agent_name: str
    model: str
    provider: str  # "anthropic", "openai", "ollama"
    tokens: TokenCount
    cost_usd: float
    tool_calls: int = 0
    metadata: dict = None

class CostCalculator:
    """Calculate costs per provider and model"""
    
    PRICING = {
        "anthropic": {
            "claude-3-5-sonnet-20241022": {
                "input": 3.0 / 1_000_000,      # $3 per M input tokens
                "output": 15.0 / 1_000_000,    # $15 per M output tokens
            },
            "claude-3-opus-20250219": {
                "input": 15.0 / 1_000_000,
                "output": 75.0 / 1_000_000,
            },
        },
        "openai": {
            "gpt-4o": {
                "input": 5.0 / 1_000_000,      # $5 per M input tokens
                "output": 15.0 / 1_000_000,
            },
            "gpt-4-turbo": {
                "input": 10.0 / 1_000_000,
                "output": 30.0 / 1_000_000,
            },
        },
        "ollama": {
            "*": {
                "input": 0,   # Local = free
                "output": 0,
            }
        }
    }
    
    @staticmethod
    def calculate(
        provider: str,
        model: str,
        input_tokens: int,
        output_tokens: int
    ) -> float:
        """Calculate cost in USD"""
        pricing = CostCalculator.PRICING.get(provider, {}).get(model)
        if not pricing:
            return 0.0
        
        cost = (
            input_tokens * pricing["input"] +
            output_tokens * pricing["output"]
        )
        return cost

class CostTracker:
    """Track costs per session, agent, and time period"""
    
    def __init__(self, db_path: str):
        self.db = SQLiteDB(db_path)
        self.session_cache = {}
    
    def record(self, entry: CostEntry) -> None:
        """Record a cost entry"""
        self.db.save("cost_entries", entry)
        
        # Update session cache
        if entry.session_id not in self.session_cache:
            self.session_cache[entry.session_id] = {"total": 0.0, "entries": 0}
        
        self.session_cache[entry.session_id]["total"] += entry.cost_usd
        self.session_cache[entry.session_id]["entries"] += 1
    
    def get_session_cost(self, session_id: str) -> float:
        """Get total cost for a session"""
        return self.db.query_sum(
            "SELECT cost_usd FROM cost_entries WHERE session_id = ?",
            (session_id,)
        )
    
    def get_daily_cost(self, date: datetime) -> float:
        """Get cost for a specific day"""
        start = date.replace(hour=0, minute=0, second=0, microsecond=0)
        end = date.replace(hour=23, minute=59, second=59, microsecond=999999)
        
        return self.db.query_sum(
            "SELECT cost_usd FROM cost_entries WHERE timestamp BETWEEN ? AND ?",
            (start, end)
        )
    
    def get_monthly_cost(self, year: int, month: int) -> float:
        """Get cost for a month"""
        from calendar import monthrange
        days = monthrange(year, month)[1]
        
        total = 0.0
        for day in range(1, days + 1):
            date = datetime(year, month, day)
            total += self.get_daily_cost(date)
        
        return total
    
    def get_agent_cost(self, agent_name: str, start: datetime, end: datetime) -> dict:
        """Get cost breakdown by agent"""
        results = self.db.query_all(
            """SELECT agent_name, COUNT(*) as calls, SUM(cost_usd) as total
               FROM cost_entries
               WHERE agent_name = ? AND timestamp BETWEEN ? AND ?
               GROUP BY agent_name""",
            (agent_name, start, end)
        )
        return results[0] if results else {"calls": 0, "total": 0.0}
    
    def get_model_cost(self, start: datetime, end: datetime) -> dict:
        """Get cost breakdown by model"""
        results = self.db.query_all(
            """SELECT model, COUNT(*) as calls, SUM(cost_usd) as total
               FROM cost_entries
               WHERE timestamp BETWEEN ? AND ?
               GROUP BY model
               ORDER BY total DESC""",
            (start, end)
        )
        return results
```

**CLI Commands:**
```bash
# Show current session costs
arcon cost show

# Show daily costs
arcon cost daily
arcon cost daily 2026-04-25

# Show monthly costs
arcon cost monthly
arcon cost monthly 2026-04-01

# Show breakdown by agent
arcon cost agent
arcon cost agent --date 2026-04-01

# Show breakdown by model
arcon cost model
arcon cost model --start 2026-04-01 --end 2026-04-30

# Budget management
arcon budget set 100                 # $100/month
arcon budget status                  # Show usage
arcon budget alert --threshold 0.8   # Alert at 80% ($80)

# Cost comparison
arcon cost compare --model claude-3.5-sonnet gpt-4o
```

**Session Display:**
```
╭─ Session Summary ─────────────────────────────────────╮
│                                                       │
│ Session:       sess-abc123                            │
│ Duration:      15 minutes                             │
│ Provider:      anthropic                              │
│ Model:         claude-3-5-sonnet-20241022             │
│                                                       │
│ Input Tokens:  2,500                                  │
│ Output Tokens: 850                                    │
│ Total Tokens:  3,350                                  │
│ Cost:          $0.0149                                │
│                                                       │
│ Tool Calls:    3                                      │
│ ├─ read_file:  2                                      │
│ ├─ bash_exec:  1                                      │
│ └─ write_file: 0                                      │
│                                                       │
╰───────────────────────────────────────────────────────╯

Monthly Budget: $100.00
Used This Month: $8.45 (8.5%)
Estimated Total: $11.27
Status: ✅ On Track
```

**Tests:**
- 10 cost calculation tests (all providers)
- 8 time-range queries
- 6 budget tracking tests
- 5 reporting tests

---

## Phase 2: Intelligence & Discovery (Weeks 5-8)
**Goal:** Auto-detect tech stacks, inject skills, route agents intelligently  
**Impact:** 30-40% additional token reduction via semantic understanding

### 2.1 Technology Auto-Detection [autoskills Pattern]

**Source:** autoskills + Onyx connector detection

**What to Build:**
```python
# src/arcon/scanner/project_scanner.py
from pathlib import Path
from typing import Set, Dict, List
import json
import re

class ProjectScanner:
    """Detect project technologies and frameworks"""
    
    PACKAGE_PATTERNS = {
        "typescript": {
            "files": ["tsconfig.json"],
            "packages": ["typescript", "ts-node"],
        },
        "react": {
            "packages": ["react", "@types/react"],
            "imports": [r"import.*React.*from.*['\"]react"],
        },
        "fastapi": {
            "packages": ["fastapi", "uvicorn"],
            "imports": [r"from fastapi import"],
        },
        "django": {
            "files": ["manage.py"],
            "packages": ["django"],
            "imports": [r"from django"],
        },
        "python": {
            "files": ["requirements.txt", "pyproject.toml", "setup.py"],
            "packages": ["python"],
        },
        "java": {
            "files": ["pom.xml", "build.gradle"],
            "packages": ["maven", "gradle"],
        },
        "rust": {
            "files": ["Cargo.toml"],
            "packages": ["cargo"],
        },
        "go": {
            "files": ["go.mod", "go.sum"],
            "packages": ["go"],
        },
        "postgres": {
            "files": ["docker-compose.yml", "Dockerfile"],
            "imports": [r"psycopg2|sqlalchemy.*postgresql"],
            "packages": ["psycopg2", "sqlalchemy[postgresql]"],
        },
    }
    
    def __init__(self, project_root: Path):
        self.project_root = project_root
        self.detected: Dict[str, bool] = {}
    
    def scan(self) -> Set[str]:
        """Detect all technologies in project"""
        techs = set()
        
        # Check files
        for tech, patterns in self.PACKAGE_PATTERNS.items():
            if self._check_files(patterns.get("files", [])):
                techs.add(tech)
                self.detected[tech] = True
        
        # Check package.json/requirements.txt
        techs.update(self._check_packages())
        
        # Check imports in code
        techs.update(self._check_imports())
        
        return techs
    
    def _check_files(self, files: List[str]) -> bool:
        """Check if any files exist"""
        return any((self.project_root / f).exists() for f in files)
    
    def _check_packages(self) -> Set[str]:
        """Check package files for dependencies"""
        techs = set()
        
        # Check package.json
        pkg_json = self.project_root / "package.json"
        if pkg_json.exists():
            deps = json.load(pkg_json.open()).get("dependencies", {})
            if "react" in deps:
                techs.add("react")
            if "fastapi" in deps:
                techs.add("fastapi")
        
        # Check requirements.txt
        req_txt = self.project_root / "requirements.txt"
        if req_txt.exists():
            for line in req_txt.read_text().split("\n"):
                line = line.strip()
                if line.startswith("fastapi"):
                    techs.add("fastapi")
                elif line.startswith("django"):
                    techs.add("django")
                elif line.startswith("psycopg2") or "postgresql" in line:
                    techs.add("postgres")
        
        return techs
    
    def _check_imports(self) -> Set[str]:
        """Grep for framework imports in code"""
        techs = set()
        
        # Search for imports in source files
        src_files = list(self.project_root.glob("**/*.py")) + \
                    list(self.project_root.glob("**/*.ts")) + \
                    list(self.project_root.glob("**/*.tsx"))
        
        for file in src_files[:100]:  # Limit scan
            try:
                content = file.read_text(errors="ignore")
                for tech, patterns in self.PACKAGE_PATTERNS.items():
                    for pattern in patterns.get("imports", []):
                        if re.search(pattern, content):
                            techs.add(tech)
            except:
                pass
        
        return techs

# src/arcon/skills/resolver.py
class SkillResolver:
    """Map detected technologies to skills"""
    
    SKILLS_MAP = {
        "typescript": [
            "typescript-patterns",
            "typescript-best-practices",
            "typescript-testing",
        ],
        "react": [
            "react-patterns",
            "react-hooks",
            "react-testing",
        ],
        "fastapi": [
            "fastapi-patterns",
            "fastapi-security",
            "api-design",
        ],
        "django": [
            "django-patterns",
            "django-orm",
            "django-security",
            "django-testing",
        ],
        "python": [
            "python-patterns",
            "python-best-practices",
            "python-testing",
        ],
        "postgres": [
            "postgres-patterns",
            "database-optimization",
            "sql-best-practices",
        ],
        "rust": [
            "rust-patterns",
            "rust-best-practices",
            "rust-safety",
        ],
        "java": [
            "java-patterns",
            "java-best-practices",
            "spring-boot-patterns",
        ],
    }
    
    COMBO_SKILLS = {
        "react-typescript": {
            "requires": ["react", "typescript"],
            "skills": [
                "react-typescript-patterns",
                "nextjs-patterns",
            ]
        },
        "fastapi-postgres": {
            "requires": ["fastapi", "postgres"],
            "skills": [
                "fastapi-postgres-patterns",
                "sqlalchemy-patterns",
                "database-migrations",
            ]
        },
        "django-postgres": {
            "requires": ["django", "postgres"],
            "skills": [
                "django-postgres-patterns",
                "django-orm-optimization",
                "migration-strategies",
            ]
        },
    }
    
    def resolve(self, technologies: Set[str]) -> List[str]:
        """Map technologies to skills"""
        skills = set()
        
        # Add skills for each technology
        for tech in technologies:
            skills.update(self.SKILLS_MAP.get(tech, []))
        
        # Add combo skills
        for combo, config in self.COMBO_SKILLS.items():
            if all(t in technologies for t in config["requires"]):
                skills.update(config["skills"])
        
        return sorted(list(skills))
```

**Integration Flow:**
```
1. User: cd /my/project && arcon chat
2. ProjectScanner scans directory
   └─ Detects: TypeScript, React, Postgres
3. SkillResolver maps to skills
   └─ Resolves: typescript-patterns, react-patterns, react-typescript-patterns, postgres-patterns
4. SkillManager loads from ~/.arcon/skills/
5. SkillInjectionMiddleware auto-injects into prompts
6. All subsequent agent calls have context
```

**Tests:**
- 25 detection tests (per technology)
- 10 combo detection tests
- 8 skill resolution tests

---

### 2.2 Tool Merging & Batching [Onyx Pattern]

**Source:** Onyx's tool call merging + parallel execution

**What to Build:**
```python
# src/arcon/tools/tool_merger.py
from typing import List, Dict, Any
from dataclasses import dataclass

@dataclass
class ToolCall:
    """Single tool invocation"""
    tool_id: str
    tool_name: str
    arguments: Dict[str, Any]
    priority: int = 0

class ToolMerger:
    """Merge similar tool calls to reduce LLM overhead"""
    
    # Tools that can be merged and their merge fields
    MERGEABLE = {
        "search": "queries",          # Merge multiple search queries
        "read_file": "file_paths",    # Merge multiple file reads
        "web_search": "queries",      # Merge web searches
    }
    
    def merge(self, tool_calls: List[ToolCall]) -> List[ToolCall]:
        """Merge similar tool calls"""
        merged = {}
        result = []
        
        for call in tool_calls:
            if call.tool_name not in self.MERGEABLE:
                # Can't merge - add as-is
                result.append(call)
                continue
            
            # Track by tool name
            if call.tool_name not in merged:
                merged[call.tool_name] = {
                    "id": call.tool_id,
                    "args": call.arguments.copy(),
                    "priority": call.priority,
                }
            else:
                # Merge arguments
                merge_field = self.MERGEABLE[call.tool_name]
                
                # Get existing and new values
                existing = merged[call.tool_name]["args"].get(merge_field, [])
                new = call.arguments.get(merge_field, [])
                
                # Ensure lists
                if not isinstance(existing, list):
                    existing = [existing]
                if not isinstance(new, list):
                    new = [new]
                
                # Merge and deduplicate
                merged[call.tool_name]["args"][merge_field] = list(
                    set(existing + new)
                )
        
        # Convert back to ToolCall objects
        for tool_name, data in merged.items():
            result.append(ToolCall(
                tool_id=data["id"],
                tool_name=tool_name,
                arguments=data["args"],
                priority=data["priority"],
            ))
        
        return result

# Example: Merge multiple searches
calls = [
    ToolCall("t1", "search", {"queries": ["authentication patterns"]}),
    ToolCall("t2", "search", {"queries": ["JWT best practices"]}),
    ToolCall("t3", "read_file", {"file_paths": ["auth.py"]}),
    ToolCall("t4", "read_file", {"file_paths": ["utils.py"]}),
]

merger = ToolMerger()
merged = merger.merge(calls)

# Result: 2 calls instead of 4
# [
#   ToolCall("t1", "search", {"queries": ["auth patterns", "JWT best practices"]}),
#   ToolCall("t3", "read_file", {"file_paths": ["auth.py", "utils.py"]}),
# ]

# Token Savings: ~40% reduction on tool calling overhead
```

**Parallel Execution:**
```python
# src/arcon/tools/tool_runner.py
import asyncio

class ToolRunner:
    """Execute tool calls (merged or parallel)"""
    
    async def run_batch(self, calls: List[ToolCall]) -> Dict[str, Any]:
        """Execute tool calls in parallel"""
        results = {}
        
        # Create coroutines for all calls
        tasks = [
            self._run_single(call)
            for call in calls
        ]
        
        # Execute in parallel with 10-minute timeout
        completed = await asyncio.wait_for(
            asyncio.gather(*tasks, return_exceptions=True),
            timeout=600
        )
        
        # Collect results
        for call, result in zip(calls, completed):
            if isinstance(result, Exception):
                results[call.tool_id] = {"error": str(result)}
            else:
                results[call.tool_id] = result
        
        return results
    
    async def _run_single(self, call: ToolCall) -> Any:
        """Run a single tool call"""
        tool = self.tools.get(call.tool_name)
        if not tool:
            raise ToolNotFound(call.tool_name)
        
        return await tool.execute(call.arguments)
```

**Tests:**
- 15 merging tests (various combinations)
- 8 parallel execution tests
- 5 error handling tests

---

### 2.3 Enhanced Agent Routing [ECC Pattern]

**Source:** ECC's 48-agent system + capability registry

**What to Build:**
```python
# src/arcon/agents/registry.py
from dataclasses import dataclass
from typing import Set

@dataclass
class AgentCapability:
    """What an agent is good at"""
    name: str
    specialization: str  # "architecture", "testing", "debugging", etc.
    keywords: Set[str]  # Search keywords
    file_patterns: Set[str]  # ".test.ts", "*.py", etc.
    tech_preferences: Set[str]  # "typescript", "react", etc.
    confidence_boost: float = 1.0  # Multiplier for routing score

class AgentRouter:
    """Intelligent multi-factor agent routing"""
    
    AGENTS = {
        # Tier 0: Existing agents (expand with metadata)
        "CodingAssistant": AgentCapability(
            name="CodingAssistant",
            specialization="general-coding",
            keywords={"implement", "write", "create", "code", "function", "class"},
            file_patterns={"*.py", "*.ts", "*.tsx", "*.java"},
            tech_preferences={"python", "typescript", "react"},
        ),
        "Debugger": AgentCapability(
            name="Debugger",
            specialization="debugging",
            keywords={"bug", "debug", "error", "crash", "fix", "fail"},
            file_patterns={"*.py", "*.ts"},
            tech_preferences=set(),
        ),
        "CodeReviewer": AgentCapability(
            name="CodeReviewer",
            specialization="code-review",
            keywords={"review", "improve", "optimize", "refactor", "style"},
            file_patterns={"*.py", "*.ts", "*.java"},
            tech_preferences=set(),
        ),
        "TestEngineer": AgentCapability(
            name="TestEngineer",
            specialization="testing",
            keywords={"test", "unit", "integration", "mock", "coverage"},
            file_patterns={"*.test.ts", "*_test.py", "test_*.py"},
            tech_preferences=set(),
        ),
        "DocumentationWriter": AgentCapability(
            name="DocumentationWriter",
            specialization="documentation",
            keywords={"document", "readme", "comment", "docstring", "explain"},
            file_patterns={"*.md", "*.rst"},
            tech_preferences=set(),
        ),
        
        # Tier 1: New specialized agents (add gradually)
        "ArchitectureReviewer": AgentCapability(
            name="ArchitectureReviewer",
            specialization="architecture",
            keywords={"architecture", "design", "pattern", "scalability"},
            file_patterns={"*.py", "*.ts", "*.java"},
            tech_preferences=set(),
        ),
        "SecurityReviewer": AgentCapability(
            name="SecurityReviewer",
            specialization="security",
            keywords={"security", "vulnerability", "auth", "crypto", "sql-injection"},
            file_patterns={"*.py", "*.ts", "*.java"},
            tech_preferences=set(),
        ),
        "PerformanceOptimizer": AgentCapability(
            name="PerformanceOptimizer",
            specialization="performance",
            keywords={"performance", "optimize", "slow", "efficiency", "cache"},
            file_patterns={"*.py", "*.ts"},
            tech_preferences=set(),
        ),
    }
    
    def route(self, query: str, context: dict) -> tuple[str, float]:
        """
        Route query to best agent.
        
        Returns: (agent_name, confidence_score)
        
        Routing Priority:
        1. Explicit agent mention (100%)
        2. File context (90%)
        3. Keyword match (70-80%)
        4. Tech detection (60-70%)
        """
        scores = {}
        
        # Factor 1: Explicit agent name in query (100%)
        for agent_name in self.AGENTS.keys():
            if agent_name.lower() in query.lower():
                return agent_name, 1.0
        
        # Factor 2: File pattern matching (90%)
        for agent_name, cap in self.AGENTS.items():
            if context.get("current_file"):
                for pattern in cap.file_patterns:
                    if self._matches_pattern(context["current_file"], pattern):
                        scores[agent_name] = 0.9
        
        # Factor 3: Keyword matching (70-80%)
        words = query.lower().split()
        for agent_name, cap in self.AGENTS.items():
            matches = sum(1 for w in words if w in cap.keywords)
            if matches > 0:
                score = min(0.8, 0.5 + (matches * 0.1))
                scores[agent_name] = max(scores.get(agent_name, 0), score)
        
        # Factor 4: Technology preference (60-70%)
        techs = context.get("detected_techs", set())
        for agent_name, cap in self.AGENTS.items():
            if any(t in cap.tech_preferences for t in techs):
                scores[agent_name] = max(
                    scores.get(agent_name, 0),
                    0.7 * cap.confidence_boost
                )
        
        # Return highest scoring agent
        if not scores:
            return "CodingAssistant", 0.5  # Default fallback
        
        best_agent = max(scores.items(), key=lambda x: x[1])
        return best_agent
    
    def _matches_pattern(self, filename: str, pattern: str) -> bool:
        """Check if filename matches pattern (e.g., *.test.ts)"""
        from fnmatch import fnmatch
        return fnmatch(filename, pattern)
```

**Router Integration:**
```python
# In session
class Session:
    def invoke(self, query: str, context: dict = None) -> str:
        context = context or {}
        
        # Detect current context
        context["current_file"] = self.get_current_file()
        context["detected_techs"] = self.scanner.scan()
        
        # Route to best agent
        agent_name, confidence = self.router.route(query, context)
        
        # Log routing decision
        self.logger.info(f"Routed to {agent_name} (confidence: {confidence:.2f})")
        
        # Select agent and invoke
        agent = self.agents[agent_name]
        return agent.invoke(query)
```

**Tests:**
- 20 routing tests (explicit, file, keyword, tech)
- 10 confidence scoring tests
- 5 fallback tests

---

## Phase 3: Knowledge & Context Optimization (Weeks 9-12)
**Goal:** Implement knowledge graphs, semantic compression, deep research  
**Impact:** 70-90% token reduction via intelligent context selection

### 3.1 Knowledge Graph Construction [Onyx Pattern]

**Source:** Onyx's KG module + entity extraction

**What to Build:**
```python
# src/arcon/kg/extractor.py
from dataclasses import dataclass
from typing import Set, Dict, List
import re

@dataclass
class Entity:
    """Named entity in codebase"""
    name: str
    entity_type: str  # "class", "function", "module", "variable"
    location: str     # "file:line"
    definition: str   # Code snippet
    related: Set[str] = None  # Related entities

@dataclass
class Relationship:
    """Connection between entities"""
    from_entity: str
    to_entity: str
    rel_type: str  # "calls", "inherits", "imports", "uses"
    strength: float = 1.0  # 0.0-1.0 confidence

class KnowledgeGraphBuilder:
    """Build semantic knowledge graph of codebase"""
    
    def __init__(self, project_root: str):
        self.project_root = project_root
        self.entities: Dict[str, Entity] = {}
        self.relationships: List[Relationship] = []
    
    async def build(self) -> 'KnowledgeGraph':
        """Build KG from codebase"""
        # Extract entities from all source files
        await self._extract_entities()
        
        # Find relationships
        await self._find_relationships()
        
        # Build graph structure
        return KnowledgeGraph(self.entities, self.relationships)
    
    async def _extract_entities(self) -> None:
        """Extract named entities from source files"""
        import os
        
        for root, dirs, files in os.walk(self.project_root):
            # Skip common non-source directories
            dirs[:] = [d for d in dirs if d not in [".git", "node_modules", "venv", "__pycache__"]]
            
            for file in files:
                if file.endswith((".py", ".ts", ".tsx", ".java")):
                    filepath = os.path.join(root, file)
                    await self._extract_from_file(filepath)
    
    async def _extract_from_file(self, filepath: str) -> None:
        """Extract entities from a single file"""
        try:
            content = open(filepath).read()
            
            # Python patterns
            if filepath.endswith(".py"):
                self._extract_python(filepath, content)
            
            # TypeScript patterns
            elif filepath.endswith((".ts", ".tsx")):
                self._extract_typescript(filepath, content)
            
            # Java patterns
            elif filepath.endswith(".java"):
                self._extract_java(filepath, content)
        
        except Exception as e:
            print(f"Error extracting from {filepath}: {e}")
    
    def _extract_python(self, filepath: str, content: str) -> None:
        """Extract Python classes, functions, etc."""
        lines = content.split("\n")
        
        # Extract classes
        for i, line in enumerate(lines):
            match = re.match(r"class\s+(\w+)", line)
            if match:
                class_name = match.group(1)
                entity_key = f"{filepath}:class:{class_name}"
                self.entities[entity_key] = Entity(
                    name=class_name,
                    entity_type="class",
                    location=f"{filepath}:{i+1}",
                    definition=line.strip()
                )
            
            # Extract functions
            match = re.match(r"def\s+(\w+)", line)
            if match:
                func_name = match.group(1)
                entity_key = f"{filepath}:func:{func_name}"
                self.entities[entity_key] = Entity(
                    name=func_name,
                    entity_type="function",
                    location=f"{filepath}:{i+1}",
                    definition=line.strip()
                )
    
    def _extract_typescript(self, filepath: str, content: str) -> None:
        """Extract TypeScript classes, functions, interfaces"""
        # Similar pattern matching...
        pass
    
    def _extract_java(self, filepath: str, content: str) -> None:
        """Extract Java classes and methods"""
        # Similar pattern matching...
        pass
    
    async def _find_relationships(self) -> None:
        """Find relationships between entities (imports, calls, etc.)"""
        # Analyze which entities reference which others
        for entity_key, entity in self.entities.items():
            # Find entities that reference this one
            for other_key, other in self.entities.items():
                if entity_key == other_key:
                    continue
                
                # Check if other entity references this entity
                if self._entity_references(other.definition, entity.name):
                    self.relationships.append(Relationship(
                        from_entity=other_key,
                        to_entity=entity_key,
                        rel_type="uses",
                        strength=1.0
                    ))
    
    def _entity_references(self, code: str, entity_name: str) -> bool:
        """Check if code references an entity"""
        return entity_name in code

class KnowledgeGraph:
    """Query and navigate the knowledge graph"""
    
    def __init__(self, entities: Dict[str, Entity], relationships: List[Relationship]):
        self.entities = entities
        self.relationships = relationships
    
    def get_related(self, entity_key: str, depth: int = 2) -> Dict[str, Entity]:
        """Get all related entities (within depth)"""
        related = {entity_key: self.entities[entity_key]}
        
        if depth <= 0:
            return related
        
        # Find entities this one references
        for rel in self.relationships:
            if rel.from_entity == entity_key:
                related.update(
                    self.get_related(rel.to_entity, depth - 1)
                )
        
        return related
    
    def get_blast_radius(self, entity_key: str) -> Set[str]:
        """Get all entities affected by changing this entity"""
        affected = set()
        
        # Find all entities that depend on this one
        def traverse(key):
            for rel in self.relationships:
                if rel.to_entity == key:
                    affected.add(rel.from_entity)
                    traverse(rel.from_entity)
        
        traverse(entity_key)
        return affected
```

**Token Savings: 8-49x reduction** by only including relevant code when discussing specific entities.

---

### 3.2 Semantic Context Compression [Onyx + caveman Pattern]

**Source:** Onyx COMPRESSION.md + caveman linguistic compression

**What to Build:**
```python
# src/arcon/compression/semantic_compressor.py
from typing import List, Dict

class SemanticCompressor:
    """Compress context using KG and semantic understanding"""
    
    def compress(
        self,
        messages: List[Dict],
        kg: KnowledgeGraph,
        context_limit: int = 20000
    ) -> List[Dict]:
        """
        Compress messages while preserving semantics.
        
        Strategy:
        1. Keep recent messages (important for task context)
        2. Summarize old messages using KG
        3. Use KG to identify minimal-but-sufficient code snippets
        """
        total_tokens = sum(self._count_tokens(m) for m in messages)
        
        if total_tokens < context_limit:
            return messages
        
        # Strategy: Keep recent + summarize old
        budget = context_limit
        compressed = []
        
        # Keep last 20% of messages (recent context)
        num_keep = max(1, len(messages) // 5)
        keep_from = len(messages) - num_keep
        
        # Add kept messages
        for msg in messages[keep_from:]:
            compressed.append(msg)
            budget -= self._count_tokens(msg)
        
        # Summarize old messages
        if keep_from > 0:
            summary = self._summarize_messages(
                messages[:keep_from],
                kg,
                budget * 0.3  # Use 30% of budget for summary
            )
            compressed.insert(0, {
                "role": "system",
                "content": f"Previous context summary:\n{summary}"
            })
        
        return compressed
    
    def _summarize_messages(
        self,
        messages: List[Dict],
        kg: KnowledgeGraph,
        token_budget: int
    ) -> str:
        """Summarize old messages using KG"""
        # Extract entities mentioned in messages
        entities_mentioned = set()
        for msg in messages:
            for entity_key in kg.entities:
                if entity_key.split(":")[-1] in msg.get("content", ""):
                    entities_mentioned.add(entity_key)
        
        # Build summary focusing on key entities
        summary_lines = [
            f"Discussed: {', '.join(e.split(':')[-1] for e in entities_mentioned[:5])}",
            f"Key entities: {len(entities_mentioned)} components analyzed"
        ]
        
        return "\n".join(summary_lines)
    
    def _count_tokens(self, message: Dict) -> int:
        """Estimate token count (rough: 1 token ≈ 4 chars)"""
        content = message.get("content", "")
        return len(content) // 4

# src/arcon/compression/linguistic_compressor.py
class LinguisticCompressor:
    """Remove non-essential words while preserving meaning (caveman style)"""
    
    # Words that can be removed without affecting meaning
    REMOVABLE_WORDS = {
        "the", "a", "an", "is", "are", "was", "were", "be",
        "have", "has", "do", "does", "did",
        "actually", "very", "really", "just", "quite",
        "would", "could", "should", "might", "may",
    }
    
    def compress(self, text: str) -> str:
        """Remove non-essential words (~65% reduction)"""
        words = text.split()
        
        # Remove articles, auxiliaries, intensifiers
        compressed = [w for w in words if w.lower() not in self.REMOVABLE_WORDS]
        
        # Keep key words, punctuation, numbers
        result = " ".join(compressed)
        
        # Collapse whitespace
        result = " ".join(result.split())
        
        return result

# Example
compressor = LinguisticCompressor()
original = "The authentication system is very important and should actually be implemented carefully."
compressed = compressor.compress(original)
# Result: "authentication system important should be implemented carefully"
# Reduction: ~40% on this snippet
```

**Tests:**
- 10 compression tests (various contexts)
- 8 KG-based compression tests
- 6 linguistic compression tests

---

### 3.3 Deep Research Capability [Onyx Pattern]

**Source:** Onyx's deep_research module

**What to Build:**
```python
# src/arcon/research/deep_research.py
from dataclasses import dataclass
from typing import List, Dict
import asyncio

@dataclass
class ResearchStep:
    """Single step in research process"""
    step_num: int
    query: str
    result: str
    entities_found: List[str] = None

class DeepResearch:
    """Multi-step research for complex problems"""
    
    async def research(
        self,
        query: str,
        max_steps: int = 5,
        agent = None
    ) -> Dict:
        """
        Break down complex query into research steps.
        
        Example:
        User: "How should we implement authentication in a FastAPI + React app?"
        
        Step 1: Research FastAPI authentication patterns
        Step 2: Research React auth state management
        Step 3: Find JWT best practices
        Step 4: Design system architecture
        Step 5: Generate implementation plan
        """
        
        plan = await self._create_research_plan(query, max_steps)
        steps = []
        
        for step in plan:
            result = await agent.invoke(step.query)
            step.result = result
            steps.append(step)
            
            # Each step informs the next
            if step.step_num < max_steps:
                plan = await self._refine_plan(query, steps, plan)
        
        return {
            "original_query": query,
            "steps": steps,
            "final_answer": self._synthesize(steps)
        }
    
    async def _create_research_plan(
        self,
        query: str,
        max_steps: int
    ) -> List[ResearchStep]:
        """Break query into research steps"""
        # Use an LLM to create breakdown
        step_plan = f"""
        Break down this query into {max_steps} research steps:
        {query}
        
        Format: Each step should be a specific, answerable question.
        """
        
        # This would call the LLM
        steps = []
        return steps
    
    def _synthesize(self, steps: List[ResearchStep]) -> str:
        """Combine step results into final answer"""
        # Combine insights from all steps
        return "\n".join(f"Step {s.step_num}: {s.result}" for s in steps)
```

**Tests:**
- 8 deep research tests
- 5 plan generation tests
- 4 synthesis tests

---

## Phase 4: Production Infrastructure (Weeks 13-16)
**Goal:** MCP integration, execution backends, observability  
**Impact:** 10-15% additional token reduction + operational excellence

### 4.1 MCP Server Integration [Onyx + Copilot SDK Pattern]

**Source:** Onyx's MCP server + FastMCP

**What to Build:**
```python
# src/arcon/mcp/server.py
from fastmcp import FastMCP
import json

mcp = FastMCP("arcon")  # MCP server

@mcp.tool()
async def search_codebase(query: str) -> str:
    """Search codebase using knowledge graph"""
    # Search in KG
    results = await kg.search(query)
    return json.dumps(results)

@mcp.tool()
async def generate_code(spec: str) -> str:
    """Generate code based on specification"""
    agent = agents["CodingAssistant"]
    return await agent.invoke(spec)

@mcp.tool()
async def review_code(code: str) -> str:
    """Review code for quality issues"""
    agent = agents["CodeReviewer"]
    return await agent.invoke(f"Review:\n{code}")

@mcp.tool()
async def run_tests(test_path: str = "tests") -> str:
    """Execute tests"""
    agent = agents["TestEngineer"]
    return await agent.invoke(f"Run tests in {test_path}")

@mcp.resource()
async def get_project_structure() -> str:
    """Get project structure and technologies"""
    scanner = ProjectScanner(project_root)
    techs = await scanner.scan()
    return json.dumps({
        "technologies": list(techs),
        "skills": resolver.resolve(techs)
    })

# Run server
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(mcp, host="localhost", port=8090)
```

**Config for Claude Desktop:**
```json
{
  "mcpServers": {
    "arcon": {
      "command": "python",
      "args": ["-m", "arcon.mcp.server"],
      "env": {
        "ARCON_PROJECT_ROOT": "/path/to/project"
      }
    }
  }
}
```

---

## Implementation Timeline & Milestones

### Phase 1 (Weeks 1-4): Foundation
- **Week 1:** Middleware pipeline + base classes (20 hours)
- **Week 2:** Permission system + storage (15 hours)
- **Week 3:** Cost tracking + CLI commands (15 hours)
- **Week 4:** Integration testing + documentation (10 hours)
- **Deliverable:** Arcon v0.2.0 (middleware, permissions, cost tracking)

### Phase 2 (Weeks 5-8): Intelligence
- **Week 5:** Tech scanner + skill resolver (20 hours)
- **Week 6:** Skill injection middleware (15 hours)
- **Week 7:** Agent routing enhancements (15 hours)
- **Week 8:** Tool merging + parallel execution (15 hours)
- **Deliverable:** Arcon v0.3.0 (auto-detection, routing, tool merging)

### Phase 3 (Weeks 9-12): Knowledge
- **Week 9:** KG builder (entity extraction) (20 hours)
- **Week 10:** KG relationships (20 hours)
- **Week 11:** Semantic + linguistic compression (15 hours)
- **Week 12:** Deep research implementation (20 hours)
- **Deliverable:** Arcon v0.4.0 (knowledge graphs, compression, research)

### Phase 4 (Weeks 13-16): Production
- **Week 13:** MCP server implementation (15 hours)
- **Week 14:** Execution backends (15 hours)
- **Week 15:** Observability + metrics (15 hours)
- **Week 16:** Performance tuning + docs (15 hours)
- **Deliverable:** Arcon v0.5.0 (production-ready)

---

## Technology Decisions

| Component | Choice | Rationale |
|-----------|--------|-----------|
| Middleware | Custom (Deep Agents pattern) | Simple, extensible, no external deps |
| Permission System | SQLite + custom classes (Copilot SDK pattern) | Light-weight, persistent, clear semantics |
| Cost Tracking | SQLite + pricing tables (OpenClaude pattern) | Accurate, offline-capable |
| KG Storage | In-memory dict (Onyx pattern) | Fast, suitable for codebases <100K lines |
| Database | SQLite (v0.2-0.3), PostgreSQL (v0.4+) | SQLite for dev, Postgres for production |
| MCP Framework | FastMCP (Onyx pattern) | Lightweight, FastAPI-integrated |
| LLM Calls | LiteLLM (multi-provider) | Keep OpenClaude compatibility |

---

## Success Metrics

### Token Efficiency
- Phase 1: 15-20% reduction (middleware + cost awareness)
- Phase 2: +15-20% reduction (smart routing + tool merging)
- Phase 3: +40-50% reduction (KG + compression + research)
- Phase 4: +10% reduction (execution optimization)
- **Total: 70-98% reduction**

### Cost Savings (for heavy users, 500 interactions/month)
- Baseline: ~$200/month (at current token usage)
- Phase 1: $150/month (-25%)
- Phase 2: $100/month (-50%)
- Phase 3: $25-60/month (-75%)
- **Target: $10-50/month (-97.5%)**

### Operational Excellence
- Error rate < 0.1% (robust middleware)
- P99 latency < 5 seconds (parallel execution)
- Coverage > 85% (comprehensive tests)
- Documentation: Every module has examples

---

## Risk Mitigation

| Risk | Mitigation |
|------|-----------|
| Middleware overhead | Profile early, optimize hot paths |
| KG memory usage | Implement trimming for large codebases |
| Compression quality | Validate against baselines, human review |
| MCP adoption slow | Provide clear examples, Discord support |
| Breaking changes | Semantic versioning, deprecation warnings |

---

## Next Steps

1. **Review & Refinement** (1 week)
   - Team review of architecture
   - Adjust priorities based on feedback
   - Estimate team capacity

2. **Phase 1 Kickoff** (Week 1)
   - Create middleware base classes
   - Set up project structure
   - Begin permission system

3. **Weekly Sync**
   - Monday: Planning
   - Friday: Demo + retrospective

---

## Reference Implementation Examples

Each phase will include:
- Reference implementations from source frameworks
- Minimal working examples
- Integration test suite
- Documentation with before/after comparisons

**Arcon becomes:** The most token-efficient, knowledge-aware coding agent platform.

