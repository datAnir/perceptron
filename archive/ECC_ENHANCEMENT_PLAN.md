# ECC Enhancement Plan
## Augmenting Everything Claude Code with Best Features from Adjacent Frameworks

**Approach:** Evolutionary Enhancement, Not Greenfield  
**Base:** ECC (Python, proven in production, 10+ months of daily use)  
**Augmentation Sources:** Copilot SDK, Deep Agents, OpenClaude, autoskills  
**Philosophy:** Keep what works in ECC, adopt/adapt better implementations from other repos

---

## Current ECC Capabilities (Solid Foundation)

### ✅ What ECC Already Has (Keep As-Is)

| Capability | ECC Implementation | Status |
|------------|------------------|--------|
| **Specialized Agents** | 48 production-ready agents in `/agents` | ✅ Strong, keep |
| **Skills Catalog** | 183 domain skills in `/skills` | ✅ Comprehensive, keep |
| **Legacy Commands** | 79 slash commands, migration path | ✅ Mature, keep |
| **Git Hook Automation** | Pre-commit, post-merge, pre-push | ✅ Proven, keep |
| **Multi-Harness Support** | Claude Code, Codex, Cursor, OpenCode, Gemini | ✅ Flexible, keep |
| **Security-First Philosophy** | Built-in validation, sanitization, permission checks | ✅ Foundational, keep |
| **Continuous Learning** | Session extraction → skill learning | ✅ Innovative, keep |
| **Dashboard GUI** | Tkinter-based desktop app (`ecc_dashboard.py`) | ✅ Modern, keep |
| **Python Implementation** | Production-grade Python 3.11+ codebase | ✅ Maintainable, keep |

---

## Enhancement Opportunities by Feature Category

### 1. **LLM Provider Abstraction** 
**Status:** Exists in ECC but limited  
**Enhancement:** Adopt OpenClaude + Copilot SDK patterns

#### Current ECC Situation
- Has basic provider routing in `src/llm/providers/`
- Supports Anthropic, OpenAI via API
- Single-provider focus during session

#### Enhancement from OpenClaude
```python
# From OpenClaude: Cost tracking per provider
class LLMProvider:
    async def create_message(self, messages, tools, stream=True):
        pass
    
    def get_cost_per_token(self) -> tuple[float, float]:
        """Return (input_cost, output_cost) per 1M tokens"""
        pass

# From Copilot SDK: Config validation
@property
def is_valid(self) -> bool:
    """Validate provider configuration before use"""
    pass
```

#### Enhancement from autoskills (in `/autoskills/main.ts`)
```python
# Model preference hierarchy
preferred_model = config.get("model_preference")
fallback_models = config.get("fallback_models", [])

# Cost-aware model selection
async def select_best_model(query_complexity: int) -> str:
    if complexity < 3:
        return fallback_models[0]  # Cheaper
    return preferred_model  # Better quality
```

#### Action Items
- [ ] Add cost tracking to `src/llm/providers/`
- [ ] Add `get_cost_per_token()` method to each provider
- [ ] Implement model selection hierarchy (preferred + fallbacks)
- [ ] Add cost aggregation to session metadata
- [ ] Document provider selection per agent type

---

### 2. **Tool System & Execution**
**Status:** Exists in ECC, basic implementation  
**Enhancement:** Adopt Deep Agents middleware + Copilot SDK permission model + OpenClaude streaming

#### Current ECC Situation
- Tools exist but invocation is agent-specific
- No unified tool registry
- Limited streaming support

#### Enhancement from Deep Agents
```python
# Middleware pipeline for tool execution
class Middleware:
    async def process_tool_call(self, tool_name, tool_input) -> tuple[str, dict]:
        """Intercept/validate/modify tool call"""
        pass

class ToolRegistry:
    def get_enabled_tools(self, context) -> list[Tool]:
        """Return only allowed tools for current context"""
        pass
```

#### Enhancement from Copilot SDK
```python
# Permission-aware tool execution
class ToolExecutionContext:
    permissions: PermissionSet  # Grant/deny/ask for each tool
    
    async def can_execute(self, tool_name: str) -> bool:
        perm = self.permissions.get(tool_name)
        if perm == "ask":
            return await self._prompt_user(tool_name)
        return perm == "allow"
```

#### Enhancement from OpenClaude
```python
# Streaming tool results
async def execute_tool_with_streaming(tool_name, input):
    tool = registry.get(tool_name)
    async for chunk in tool.execute_streaming(input):
        yield {"type": "tool_output", "chunk": chunk}
```

#### Action Items
- [ ] Create unified `ToolRegistry` in `src/llm/tools/registry.py`
- [ ] Add `Middleware` base class to `src/llm/middleware/`
- [ ] Implement `PermissionMiddleware` for tool access control
- [ ] Add streaming support to tool execution pipeline
- [ ] Refactor agent tools to use central registry
- [ ] Document tool permission matrix per agent type

---

### 3. **Middleware Pipeline**
**Status:** Not currently in ECC (significant gap)  
**Enhancement:** Adopt Deep Agents middleware architecture

#### New Architecture
```python
# src/llm/middleware/pipeline.py
class MiddlewarePipeline:
    def __init__(self, middlewares: list[Middleware]):
        self.middlewares = middlewares
    
    async def process_input(self, messages: list[dict]) -> list[dict]:
        """Run middlewares in sequence on input"""
        for middleware in self.middlewares:
            messages = await middleware.process_input(messages)
        return messages
    
    async def process_tool_call(self, tool_name: str, input: dict):
        """Validate tool call through middleware stack"""
        for middleware in self.middlewares:
            tool_name, input = await middleware.process_tool_call(tool_name, input)
        return tool_name, input
    
    async def process_output(self, output: str) -> str:
        """Post-process LLM output"""
        for middleware in self.middlewares:
            output = await middleware.process_output(output)
        return output

# Concrete implementations
class FilesystemSecurityMiddleware(Middleware):
    """Validate file operations against allowed paths"""
    pass

class PermissionMiddleware(Middleware):
    """Check permissions for tool usage"""
    pass

class SkillInjectionMiddleware(Middleware):
    """Inject relevant skills based on query"""
    pass

class ContextCompactionMiddleware(Middleware):
    """Auto-summarize old context when tokens exceed limit"""
    pass
```

#### Action Items
- [ ] Create `src/llm/middleware/` directory structure
- [ ] Implement middleware base class and pipeline
- [ ] Port existing ECC validations into middleware
- [ ] Add filesystem security middleware
- [ ] Add permission enforcement middleware
- [ ] Add skill injection middleware (see #5 below)
- [ ] Add context compaction for long conversations

---

### 4. **Session Management & Persistence**
**Status:** Exists in ECC, basic session tracking  
**Enhancement:** Adopt Copilot SDK session state management

#### Current ECC Situation
- Sessions tracked but limited persistence
- State stored per-harness
- No session resumption capabilities

#### Enhancement from Copilot SDK
```python
# src/llm/session/manager.py
class Session:
    def __init__(self, session_id: str, working_directory: str):
        self.id = session_id
        self.working_directory = working_directory
        self.messages = []
        self.metadata = {}  # Track agent choices, tool calls, costs
    
    async def invoke(self, query: str, agent_type: AgentType = None, stream: bool = True):
        """Invoke with agent routing and state tracking"""
        agent = self.router.route(query, agent_type)
        self.messages.append({"role": "user", "content": query})
        
        # Process through middleware
        processed = await self.middleware.process_input(self.messages)
        
        # Invoke agent and stream results
        async for chunk in agent.invoke(query, context, stream):
            yield chunk
        
        # Save state
        await self._save_to_memory(query)
    
    async def resume_from_checkpoint(self, checkpoint_id: str):
        """Resume from saved state"""
        data = await self.storage.load(checkpoint_id)
        self.messages = data.messages
        self.metadata = data.metadata
    
    async def close(self):
        """Save final state"""
        await self.storage.finalize(self.id)
```

#### Action Items
- [ ] Enhance `Session` class with checkpoint/resume capabilities
- [ ] Add `SessionStorage` (SQLite backend from ECC 1.9)
- [ ] Track agent choices and routing decisions in metadata
- [ ] Track tool execution times and costs
- [ ] Implement session recovery from crashes
- [ ] Add session export for analysis/audit

---

### 5. **Skill Discovery & Dynamic Loading**
**Status:** Exists in ECC (foundational), can be greatly enhanced  
**Enhancement:** Adopt autoskills detection + combo logic

#### Current ECC Situation
- Skills are manually curated in `/skills/`
- Loaded per-agent
- No automatic technology detection
- No skill composition (combos)

#### Enhancement from autoskills
```python
# src/llm/skills/discovery.py

class ProjectScanner:
    """Auto-detect project technologies"""
    
    async def detect_technologies(self, project_dir: str) -> list[str]:
        # Strategy 1: package.json, requirements.txt, go.mod
        # Strategy 2: config files (tsconfig.json, webpack.config.js, .eslintrc, Dockerfile)
        # Strategy 3: file presence (Django has settings.py, Spring has pom.xml)
        # Strategy 4: content patterns (grep for framework signatures)
        pass

class SkillResolver:
    """Map technologies to available skills"""
    
    def resolve(self, technologies: list[str], query: str = None) -> list[str]:
        # Look up SKILLS_MAP: Python → [python-patterns, python-testing, ...]
        # Look up COMBO_SKILLS: (React, TypeScript) → [react-ts-patterns]
        # Rank by relevance to query
        pass

class ComboDetector:
    """Identify technology combinations"""
    
    def detect(self, technologies: list[str]) -> list[str]:
        combos = []
        if "react" in technologies and "typescript" in technologies:
            combos.append("react-typescript-patterns")
        if "django" in technologies and "postgres" in technologies:
            combos.append("django-postgres-patterns")
        return combos

class SkillsManager:
    """Orchestrate skill loading and injection"""
    
    async def enable_project_skills(self, project_dir: str):
        """Auto-load skills based on detected technologies"""
        detector = ProjectScanner()
        techs = await detector.detect_technologies(project_dir)
        combos = ComboDetector().detect(techs)
        
        skills = []
        for tech in techs:
            skills.extend(self.skill_registry.get_by_tag(tech))
        for combo in combos:
            skills.extend(self.skill_registry.get_by_tag(combo))
        
        self.active_skills = deduplicate(skills)
    
    async def resolve_for_query(self, query: str) -> list[str]:
        """Find relevant skills for specific query"""
        categories = analyze_query(query)
        return [s for s in self.active_skills if s.category in categories]
```

#### SKILLS_MAP Structure (from autoskills)
```yaml
# Technology-to-skill mapping
technologies:
  python:
    skills:
      - python-patterns
      - python-testing
      - django-patterns
      - flask-patterns
      - fastapi-patterns
  
  typescript:
    skills:
      - typescript-patterns
      - react-patterns
      - nextjs-patterns
      - nodejs-patterns
  
  rust:
    skills:
      - rust-patterns
      - rust-testing
      - cargo-optimization

# Technology combinations
combos:
  react-typescript:
    requires: [react, typescript]
    skills:
      - react-typescript-patterns
      - nextjs-patterns
  
  django-postgres:
    requires: [django, postgres]
    skills:
      - django-patterns
      - postgres-patterns
      - database-migrations
```

#### Action Items
- [ ] Create `src/llm/skills/scanner.py` for technology detection
- [ ] Create `src/llm/skills/resolver.py` for tech-to-skill mapping
- [ ] Create `SKILLS_MAP.yaml` defining technology catalog
- [ ] Create `COMBO_SKILLS.yaml` for technology combinations
- [ ] Enhance middleware to auto-inject detected skills (see #3)
- [ ] Add skill caching to avoid repeated detection
- [ ] Update agent invocation to use auto-loaded skills
- [ ] Document how to add skills for new technologies

---

### 6. **Execution Backends**
**Status:** Not currently in ECC (local execution only)  
**Enhancement:** Adopt Deep Agents backend abstraction

#### Current ECC Situation
- Executes only on local machine
- No isolation/sandboxing
- No remote execution support

#### Enhancement from Deep Agents
```python
# src/llm/execution/backends.py

class ExecutionBackend(ABC):
    """Abstract execution environment"""
    
    @abstractmethod
    async def execute_command(self, command: str, cwd: str = None) -> str:
        pass
    
    @abstractmethod
    async def read_file(self, path: str) -> bytes:
        pass
    
    @abstractmethod
    async def write_file(self, path: str, content: bytes):
        pass

class LocalExecutionBackend(ExecutionBackend):
    """Local machine execution"""
    pass

class SandboxedExecutionBackend(ExecutionBackend):
    """Isolated sandbox (e2b, Docker)"""
    pass

class RemoteExecutionBackend(ExecutionBackend):
    """Execute on remote server"""
    pass
```

#### Action Items
- [ ] Create backend abstraction in `src/llm/execution/`
- [ ] Implement `LocalExecutionBackend` (current behavior)
- [ ] Add `SandboxedExecutionBackend` for untrusted code
- [ ] Add configuration to select execution backend
- [ ] Update tools to use backend abstraction
- [ ] Document security implications of each backend

---

### 7. **Agent System & Routing**
**Status:** Exists in ECC with 48 agents, needs infrastructure  
**Enhancement:** Adopt Copilot SDK agent routing + Deep Agents orchestration

#### Current ECC Situation
- 48 agents defined as markdown in `/agents/`
- Manual invocation per request
- Limited agent orchestration
- No sub-agent delegation

#### Enhancement from Copilot SDK + ECC
```python
# src/llm/agents/router.py

class AgentRouter:
    def route(self, request: str, agents: dict[str, Agent]) -> str:
        """Determine which agent(s) should handle request"""
        # Pattern matching
        if any(w in request.lower() for w in ["security", "vulnerable"]):
            return "security-reviewer"
        
        # Technology detection
        if "react" in request.lower() or "jsx" in request.lower():
            return "typescript-reviewer"
        
        # Build/error keywords
        if "build fail" in request.lower() or "compile error" in request:
            return "build-error-resolver"
        
        # Default
        return "code-reviewer"

class AgentOrchestrator:
    """Manage multiple agents and sub-agent delegation"""
    
    async def invoke(self, query: str, main_agent: str = None):
        if main_agent is None:
            main_agent = self.router.route(query)
        
        agent = self.agents[main_agent]
        
        # Let agent optionally request sub-agents
        async for chunk in agent.invoke(query):
            yield chunk
            
            # If agent requests help, delegate to sub-agent
            if chunk.get("request_subagent"):
                subagent_name = chunk["subagent"]
                subagent = self.agents[subagent_name]
                
                async for subchunk in subagent.invoke(chunk["context"]):
                    yield subchunk
```

#### Action Items
- [ ] Create `src/llm/agents/router.py` with routing logic
- [ ] Create `src/llm/agents/orchestrator.py` for coordination
- [ ] Map all 48 agents to their keywords and specializations
- [ ] Implement agent capability registry
- [ ] Add sub-agent request/response protocol
- [ ] Document agent interdependencies
- [ ] Add parallel agent execution for independent queries

---

### 8. **Streaming & Real-Time Response**
**Status:** Partially in ECC, can be enhanced  
**Enhancement:** Full streaming from OpenClaude

#### Current ECC Situation
- Some streaming support
- Not consistent across all code paths

#### Enhancement from OpenClaude
```python
# Full streaming pipeline
async def invoke_with_streaming(agent, query: str):
    # 1. Stream LLM response
    async for event in provider.create_message(messages, tools, stream=True):
        if event.type == "text":
            yield {"type": "text", "content": event.text}
        
        elif event.type == "tool_call":
            # 2. Stream tool execution
            tool = registry.get(event.tool_name)
            async for tool_chunk in tool.execute_streaming(event.input):
                yield {"type": "tool_output", "chunk": tool_chunk}
        
        elif event.type == "completion":
            yield {"type": "completion", "reason": event.reason}
```

#### Action Items
- [ ] Ensure all providers support streaming
- [ ] Add streaming support to all tool executions
- [ ] Document streaming event protocol
- [ ] Test with large outputs (files, logs, etc.)
- [ ] Add progress indication for long-running tools

---

### 9. **Security & Validation**
**Status:** Strong in ECC, can be formalized  
**Enhancement:** Formal middleware + Copilot SDK permission model

#### Current ECC Situation
- Good security guidelines in `AGENTS.md`
- Ad-hoc validation scattered in code

#### Enhancement from Copilot SDK
```python
# Formal validation middleware
class InputValidationMiddleware(Middleware):
    async def process_input(self, messages):
        for msg in messages:
            if msg["role"] == "user":
                validate_no_injection(msg["content"])
        return messages

# Tool-specific validation
async def validate_tool_input(tool_name: str, input: dict) -> bool:
    if tool_name == "bash":
        cmd = input.get("command", "")
        if any(bad in cmd for bad in [";", "|", "&", "$", "`"]):
            raise SecurityError("Potentially dangerous command")
    
    if tool_name in ["read_file", "write_file"]:
        if ".." in input.get("path", "") or input["path"].startswith("/"):
            raise SecurityError("Path traversal detected")
    
    return True
```

#### Action Items
- [ ] Formalize security guidelines into middleware
- [ ] Create `src/llm/security/validator.py`
- [ ] Document attack vectors per tool type
- [ ] Add rate limiting middleware
- [ ] Add audit logging middleware
- [ ] Implement sandbox enforcement

---

### 10. **Cost Tracking & Optimization**
**Status:** Partially in ECC, can be enhanced  
**Enhancement:** Full cost tracking from OpenClaude

#### Current ECC Situation
- Token tracking exists
- No cost aggregation
- No cost-aware model selection

#### Enhancement from OpenClaude
```python
# src/llm/cost/tracker.py

class CostTracker:
    async def track_invocation(self, 
        model: str, 
        input_tokens: int, 
        output_tokens: int
    ):
        provider = self.get_provider(model)
        in_cost, out_cost = provider.get_cost_per_token()
        
        total_cost = (input_tokens * in_cost + output_tokens * out_cost) / 1_000_000
        
        self.costs.append({
            "timestamp": datetime.now(),
            "model": model,
            "input_tokens": input_tokens,
            "output_tokens": output_tokens,
            "cost_usd": total_cost,
            "session_id": self.session_id,
        })
    
    def get_session_cost(self, session_id: str) -> float:
        return sum(c["cost_usd"] for c in self.costs if c["session_id"] == session_id)
    
    def get_daily_cost(self) -> float:
        today = date.today()
        return sum(c["cost_usd"] for c in self.costs if c["timestamp"].date() == today)
```

#### Action Items
- [ ] Create `src/llm/cost/tracker.py`
- [ ] Add cost tracking to each provider
- [ ] Create cost reporting in session metadata
- [ ] Add cost-aware model selection
- [ ] Create `cost-audit` skill for monthly review
- [ ] Add cost alerts/budgets

---

### 11. **Continuous Learning & Auto-Skill Generation**
**Status:** Exists in ECC as concept, needs implementation  
**Enhancement:** Formalize pattern extraction

#### Current ECC Situation
- Mentioned in `AGENTS.md` as philosophy
- Not yet fully implemented

#### Enhancement from ECC Philosophy
```python
# src/llm/learning/extractor.py

class SkillLearner:
    async def extract_patterns_from_session(self, session: Session) -> list[Pattern]:
        """Extract reusable patterns from successful interactions"""
        messages = session.messages
        
        patterns = []
        
        # Pattern 1: Domain-specific solutions
        for msg in messages:
            if msg["role"] == "assistant" and "solution:" in msg["content"].lower():
                patterns.append(Pattern(
                    type="solution",
                    domain=extract_domain(msg),
                    content=extract_code_block(msg),
                ))
        
        # Pattern 2: Error → Fix sequences
        for i, msg in enumerate(messages):
            if "error" in msg.get("content", "").lower():
                if i + 1 < len(messages):
                    next_msg = messages[i+1]
                    if "fix" in next_msg.get("content", "").lower():
                        patterns.append(Pattern(
                            type="error_fix",
                            error=extract_error(msg),
                            fix=extract_code_block(next_msg),
                        ))
        
        return patterns
    
    async def create_skills_from_patterns(self, patterns: list[Pattern]):
        """Convert patterns into reusable skills"""
        for pattern in patterns:
            skill = SkillDefinition(
                id=generate_id(pattern),
                name=pattern.generate_name(),
                description=pattern.generate_description(),
                content=pattern.to_markdown(),
                tags=pattern.extract_tags(),
                source="learned",
            )
            
            # Save as markdown file in skills/
            self.skill_registry.save(skill)
```

#### Action Items
- [ ] Create `src/llm/learning/extractor.py`
- [ ] Implement pattern extraction from sessions
- [ ] Create skill generation from patterns
- [ ] Add user review/approval workflow
- [ ] Save learned skills to `/skills/` directory
- [ ] Document skill quality standards
- [ ] Add skill versioning

---

### 12. **Configuration & Plugin System**
**Status:** Exists, can be formalized  
**Enhancement:** Adopt Copilot SDK config patterns

#### Current ECC Situation
- Config in `agent.yaml`
- Per-harness configuration
- Limited extensibility

#### Enhancement from Copilot SDK
```python
# src/config/manager.py

class ConfigManager:
    def __init__(self, config_path: str = None):
        self.config_path = config_path or "~/.ecc/config.yaml"
        self.config = self._load_config()
    
    def _load_config(self) -> dict:
        # 1. Load from file
        config = yaml.load(self.config_path)
        
        # 2. Override with env vars
        for key, value in os.environ.items():
            if key.startswith("ECC_"):
                config[key[4:].lower()] = value
        
        return config
    
    def get_provider_config(self) -> ProviderConfig:
        return ProviderConfig(
            type=self.config.get("provider_type", "anthropic"),
            api_key=self.config.get("api_key"),
            model=self.config.get("model", "claude-opus-4-6"),
        )
    
    def get_middleware_config(self) -> list[str]:
        return self.config.get("middleware", [
            "permission",
            "security",
            "skill_injection",
            "context_compaction",
        ])

# Plugin system
class PluginRegistry:
    def register_middleware(self, name: str, cls: type[Middleware]):
        pass
    
    def register_tool(self, name: str, cls: type[Tool]):
        pass
    
    def register_backend(self, name: str, cls: type[ExecutionBackend]):
        pass
```

#### Action Items
- [ ] Create `src/config/manager.py`
- [ ] Support environment variable overrides
- [ ] Create `src/plugins/registry.py` for extensibility
- [ ] Document plugin development guide
- [ ] Add plugin discovery and loading
- [ ] Create official plugin templates

---

## Enhancement Priority & Roadmap

### Phase 1: Foundation (Week 1-2)
High-value, low-complexity enhancements that enable everything else.

- [ ] **Middleware Pipeline** (#3) — enables security, skill injection, context management
- [ ] **Tool Registry** (#2) — centralizes tool management
- [ ] **Enhanced Session Management** (#4) — enables resumption and auditing
- [ ] **Cost Tracking** (#10) — enables cost-aware decisions

**Why First:** These provide infrastructure for all other enhancements.

### Phase 2: Intelligence (Week 3-4)
Enhance agent capabilities and decision-making.

- [ ] **Agent Routing** (#7) — smarter agent selection
- [ ] **Skill Discovery** (#5) — auto-load skills based on project
- [ ] **Execution Backends** (#6) — sandboxing and security
- [ ] **Improved Provider Abstraction** (#1) — cost-aware model selection

**Why Second:** Builds on Phase 1 foundation, enables smarter routing.

### Phase 3: Polish (Week 5-6)
User experience and production readiness.

- [ ] **Full Streaming** (#8) — real-time feedback
- [ ] **Security Formalization** (#9) — middleware-based validation
- [ ] **Cost Optimization** (#10 continued) — budgets and alerts
- [ ] **Configuration System** (#12) — user customization

**Why Third:** Builds on agent intelligence from Phase 2.

### Phase 4: Advanced (Week 7+)
Learning and optimization.

- [ ] **Continuous Learning** (#11) — auto-skill generation
- [ ] **Advanced Orchestration** (#7 continued) — sub-agent delegation
- [ ] **Performance Optimization** — caching, batching
- [ ] **Observability** — dashboards, metrics

**Why Last:** Benefits from mature foundation and active usage.

---

## Feature Matrix: Who Has It

| Feature | ECC | Copilot SDK | Deep Agents | OpenClaude | autoskills | Where to Take From |
|---------|-----|-------------|-------------|------------|------------|-------------------|
| Provider Abstraction | ✓ Basic | ✓ Full | ✓ Via LangGraph | ✓ Full | ✗ | **OpenClaude** (cost tracking) |
| Tool Registry | ✗ | ✓ | ✓ | ✓ | ✗ | **Copilot SDK** (permissions) |
| Middleware Pipeline | ✗ | ✗ | ✓ Full | ✗ | ✗ | **Deep Agents** |
| Agent Routing | ✓ Manual | ✓ | ✓ | ✗ | ✗ | **ECC** (keep), enhance with **Copilot** |
| Session Management | ✓ Basic | ✓ Full | ✓ | ✗ | ✗ | **Copilot SDK** (checkpoints) |
| Skill System | ✓ Manual catalog | ✗ | ✗ | ✗ | ✓ Full | **autoskills** (auto-detection) |
| Tech Detection | ✗ | ✗ | ✗ | ✗ | ✓ Full | **autoskills** |
| Execution Backends | ✓ Local only | ✗ | ✓ Full | ✗ | ✗ | **Deep Agents** |
| Streaming | ✓ Partial | ✗ | ✗ | ✓ Full | ✗ | **OpenClaude** |
| Cost Tracking | ✓ Minimal | ✗ | ✗ | ✓ Full | ✗ | **OpenClaude** |
| Security | ✓ Strong | ✓ Full | ✓ | ✓ | ✓ | **ECC** (keep), formalize with **Copilot** |
| Git Hooks | ✓ Full | ✗ | ✗ | ✗ | ✗ | **ECC** (keep) |
| Multi-Harness | ✓ Full | ✓ | ✗ | ✗ | ✗ | **ECC** (keep) |
| Agents | ✓ 48 specialized | ✗ | ✗ | ✗ | ✗ | **ECC** (keep) |
| Continuous Learning | ✓ Conceptual | ✗ | ✗ | ✗ | ✗ | **ECC** (implement) |

---

## Implementation File Structure

```
src/llm/
├── core/
│   ├── agent.py           (enhance existing)
│   └── session.py         (enhance with checkpoints)
│
├── providers/
│   ├── base.py            (add cost tracking)
│   ├── anthropic.py       (enhance)
│   ├── openai.py          (enhance)
│   └── ollama.py          (add cost awareness)
│
├── middleware/            (NEW)
│   ├── base.py
│   ├── pipeline.py
│   ├── security.py
│   ├── permissions.py
│   ├── skill_injection.py
│   └── context_compaction.py
│
├── tools/                 (enhance)
│   ├── registry.py        (NEW - centralize)
│   └── ... existing tools
│
├── skills/               (enhance)
│   ├── scanner.py        (NEW - auto-detect)
│   ├── resolver.py       (NEW - tech mapping)
│   ├── manager.py        (NEW - orchestrate)
│   └── catalog.yaml      (NEW - SKILLS_MAP)
│
├── agents/               (enhance)
│   ├── router.py         (NEW - smarter routing)
│   └── orchestrator.py   (NEW - coordination)
│
├── execution/            (NEW)
│   ├── backends.py
│   ├── local.py
│   ├── sandboxed.py
│   └── remote.py
│
├── cost/                 (NEW)
│   └── tracker.py
│
├── learning/             (NEW)
│   └── extractor.py
│
├── config/               (NEW)
│   └── manager.py
│
└── plugins/              (NEW)
    └── registry.py
```

---

## Summary: What to Build

### Keep (No Changes Needed)
✅ 48 specialized agents  
✅ 183 domain skills  
✅ 79 legacy commands  
✅ Git hook automation  
✅ Multi-harness support  
✅ Security philosophy  
✅ Tkinter dashboard  
✅ Python codebase  

### Enhance (Add to Existing)
🔄 Provider abstraction → add cost tracking  
🔄 Session management → add checkpoints/resumption  
🔄 Tool system → add registry and middleware  
🔄 Agent system → add routing and orchestration  

### Introduce (New Capabilities)
⭐ Middleware pipeline (from Deep Agents)  
⭐ Technology detection (from autoskills)  
⭐ Execution backends (from Deep Agents)  
⭐ Skill auto-loading (from autoskills)  
⭐ Full streaming (from OpenClaude)  
⭐ Cost tracking (from OpenClaude)  
⭐ Formal security validation (from Copilot SDK)  
⭐ Continuous learning (formalize ECC concept)  

---

## Next Steps

1. **Review this plan** — Does it align with your vision?
2. **Prioritize Phase 1** — Shall we start with middleware, tool registry, sessions, and cost tracking?
3. **Create implementation tickets** — Break down each enhancement into concrete PRs
4. **Iterative enhancement** — Ship Phase 1, validate with real usage, then Phase 2

The beauty of this approach: **You get ECC's proven stability and 48 agents, plus the best infrastructure improvements from four adjacent frameworks, all in evolutionary steps.**

