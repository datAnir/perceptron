# Robust Coding Agent Implementation Guide
## Synthesizing Best Features from All Four Codebases

This document provides a synthesis of the best practices, patterns, and architectural decisions from four state-of-the-art coding agent systems, enabling you to build a high-quality, production-ready coding agent.

---

## Executive Summary

### Four Codebases Analyzed

1. **Copilot SDK** - Thin client for LLM orchestration via JSON-RPC
2. **Deep Agents** - LangGraph-based agent framework with middleware
3. **OpenClaude** - Multi-provider CLI with streaming and tools
4. **Everything Claude Code** - Agent + skill ecosystem with continuous learning

### Combined Best Practices

```
Copilot SDK    → JSON-RPC protocol, permission system
                
Deep Agents    → Middleware architecture, LangGraph base, backends
                
OpenClaude     → Multi-provider support, streaming, tool system
                
ECC            → Agent routing, skills, security-first, continuous learning
                
         ↓
         
Your Coding Agent
├─ LLM-agnostic (multiple providers)
├─ Modular (middleware, backends, tools)
├─ Learnable (skills from sessions)
├─ Secure (permissions, validation)
└─ Streaming (real-time feedback)
```

---

## Architectural Foundation

### Core Principles to Adopt

#### 1. **Plugin Architecture (Multiple Levels)**

```
Level 1: LLM Providers
├─ OpenAI-compatible endpoint
├─ Anthropic API
├─ Ollama local
├─ Google Gemini
└─ Custom providers via abstraction

Level 2: Tool System
├─ Tool registry
├─ Permission checks
├─ Custom tool extensions
├─ MCP server integration
└─ Dynamic MCP server management (start/stop based on queries)

Level 3: Agent System
├─ Specialized agents
├─ Agent orchestration
├─ Sub-agent delegation
└─ Multi-agent workflows

Level 4: Knowledge System
├─ Skills (Markdown files)
├─ Rules (per-language guidelines)
├─ Learned patterns
└─ Context injection
```

#### 2. **Message-Based Communication**

Like Copilot SDK's JSON-RPC:
```python
# Message protocol
{
    "type": "invoke",
    "session_id": "sess-123",
    "messages": [...],
    "tools": ["read_file", "bash", ...],
    "streaming": true
}
```

#### 3. **Streaming-First Architecture**

Like OpenClaude's query engine:
```python
for event in response_stream:
    if event.type == "text":
        display_streaming_text(event.text)
    elif event.type == "tool_call":
        execute_tool_and_continue(event)
    elif event.type == "completion":
        finalize_response()
```

#### 4. **Middleware Pipeline** (From Deep Agents)

```
Input → Filesystem MW → Permission MW → Skill Injection MW → LLM
  ↓
Output ← Result MW ← Tool Execution MW ← Tool Call Validation MW ← LLM
```

---

## Detailed Implementation Strategy

### 1. LLM Provider Abstraction

**Pattern from: OpenClaude + Copilot SDK**

```python
from abc import ABC, abstractmethod

class LLMProvider(ABC):
    """Abstraction for any LLM provider"""
    
    @abstractmethod
    async def create_message(
        self,
        model: str,
        messages: list[Message],
        tools: list[Tool],
        stream: bool = True,
    ) -> AsyncIterator[Event]:
        """Stream response from LLM"""
        pass
    
    @abstractmethod
    def validate_config(self) -> bool:
        """Validate provider configuration"""
        pass
    
    @abstractmethod
    def get_cost_per_token(self) -> tuple[float, float]:
        """Return (input_cost, output_cost) per 1M tokens"""
        pass

class OpenAIProvider(LLMProvider):
    async def create_message(self, ...):
        # OpenAI-compatible implementation
        pass

class AnthropicProvider(LLMProvider):
    async def create_message(self, ...):
        # Anthropic API implementation
        pass

class OllamaProvider(LLMProvider):
    async def create_message(self, ...):
        # Local Ollama implementation
        pass

class GeminiProvider(LLMProvider):
    async def create_message(self, ...):
        # Google Gemini implementation
        pass

# Provider resolution
def get_provider(config: ProviderConfig) -> LLMProvider:
    if config.type == "openai":
        return OpenAIProvider(config.api_key)
    elif config.type == "anthropic":
        return AnthropicProvider(config.api_key)
    elif config.type == "ollama":
        return OllamaProvider(config.base_url)
    # ... more providers
```

### 2. Tool System Architecture

**Pattern from: OpenClaude + Copilot SDK**

```python
from abc import ABC, abstractmethod
from pydantic import BaseModel

class ToolInput(BaseModel):
    """Base class for tool parameters (with validation)"""
    pass

class ToolResult:
    """Standardized tool result"""
    def __init__(
        self,
        success: bool,
        output: str = "",
        error: str = "",
        tool_calls: list = None,
        stream: AsyncIterator = None
    ):
        self.success = success
        self.output = output
        self.error = error
        self.tool_calls = tool_calls or []
        self.stream = stream

class Tool(ABC):
    """Base class for all tools"""
    
    name: str
    description: str
    category: str  # "filesystem", "execution", "search", etc.
    
    @abstractmethod
    async def execute(
        self,
        input: ToolInput,
        context: ToolExecutionContext
    ) -> ToolResult:
        pass
    
    def get_json_schema(self) -> dict:
        """Return JSON schema for parameters"""
        return ToolInput.model_json_schema()

# Specialized tool implementations
class ReadFileTool(Tool):
    name = "read_file"
    description = "Read contents of a file"
    
    class Input(ToolInput):
        path: str
        start_line: int = 1
        end_line: int | None = None
    
    async def execute(self, input: Input, context) -> ToolResult:
        try:
            content = await context.filesystem.read(
                input.path,
                input.start_line,
                input.end_line
            )
            return ToolResult(success=True, output=content)
        except Exception as e:
            return ToolResult(success=False, error=str(e))

class BashTool(Tool):
    name = "bash"
    description = "Execute shell command"
    
    class Input(ToolInput):
        command: str
        working_directory: str | None = None
    
    async def execute(self, input: Input, context) -> ToolResult:
        # Validate command (security)
        if not context.permissions.can_execute(input.command):
            return ToolResult(
                success=False,
                error="Permission denied for this command"
            )
        
        # Execute with streaming
        process = await context.shell.execute(input.command)
        return ToolResult(
            success=True,
            stream=process.stream_output()
        )

# Tool registry
class ToolRegistry:
    def __init__(self):
        self.tools = {}
    
    def register(self, tool: Tool):
        self.tools[tool.name] = tool
    
    def get_tool(self, name: str) -> Tool:
        return self.tools.get(name)
    
    def get_enabled_tools(self, context) -> list[Tool]:
        return [
            tool for tool in self.tools.values()
            if context.permissions.can_use(tool.name)
        ]
```

### 3. Agent System

**Pattern from: ECC + Deep Agents**

```python
from enum import Enum

class AgentType(Enum):
    PLANNER = "planner"
    CODE_REVIEWER = "code_reviewer"
    SECURITY_REVIEWER = "security_reviewer"
    BUILD_ERROR_RESOLVER = "build_error_resolver"
    ARCHITECT = "architect"
    # ... more agents

class Agent:
    """Represents a specialized agent"""
    
    def __init__(
        self,
        agent_type: AgentType,
        system_prompt: str,
        available_tools: list[str],
        skills: list[str],
        model_preference: str = None
    ):
        self.type = agent_type
        self.system_prompt = system_prompt
        self.available_tools = available_tools
        self.skills = skills
        self.model_preference = model_preference
    
    async def invoke(
        self,
        query: str,
        context: AgentContext,
        stream: bool = True
    ) -> AsyncIterator[str]:
        """Invoke agent and stream results"""
        
        # 1. Inject skills into context
        skill_context = self._inject_skills(context)
        
        # 2. Prepare messages
        messages = [
            {"role": "system", "content": self.system_prompt},
            *skill_context,
            {"role": "user", "content": query}
        ]
        
        # 3. Call LLM
        response = await context.provider.create_message(
            model=self.model_preference or context.default_model,
            messages=messages,
            tools=self.available_tools,
            stream=True
        )
        
        # 4. Handle tool calls and stream response
        async for event in response:
            if event.type == "text":
                yield event.text
            elif event.type == "tool_call":
                result = await context.execute_tool(
                    event.tool_name,
                    event.tool_input
                )
                # Continue agent loop with result
                messages.append({"role": "assistant", "content": result})
    
    def _inject_skills(self, context) -> list[dict]:
        """Inject relevant skills into message context"""
        injected = []
        for skill_name in self.skills:
            skill_content = context.skills.load(skill_name)
            injected.append({
                "role": "system",
                "content": f"Relevant skill: {skill_content}"
            })
        return injected

# Agent router
class AgentRouter:
    def __init__(self, agents: dict[AgentType, Agent]):
        self.agents = agents
    
    def route(self, request: str) -> AgentType:
        """Determine which agent should handle request"""
        request_lower = request.lower()
        
        if any(w in request_lower for w in ["plan", "break down"]):
            return AgentType.PLANNER
        elif any(w in request_lower for w in ["review code", "quality"]):
            return AgentType.CODE_REVIEWER
        elif any(w in request_lower for w in ["security", "vulnerable"]):
            return AgentType.SECURITY_REVIEWER
        elif any(w in request_lower for w in ["build fail", "compile error"]):
            return AgentType.BUILD_ERROR_RESOLVER
        elif any(w in request_lower for w in ["design", "architecture"]):
            return AgentType.ARCHITECT
        # Default to general agent
        return AgentType.PLANNER
```

### 4. Middleware Pipeline

**Pattern from: Deep Agents**

```python
from abc import ABC, abstractmethod
from typing import Any

class Middleware(ABC):
    """Base class for middleware in the pipeline"""
    
    @abstractmethod
    async def process_input(self, messages: list[dict]) -> list[dict]:
        """Process input before sending to LLM"""
        pass
    
    @abstractmethod
    async def process_tool_call(
        self,
        tool_name: str,
        tool_input: dict
    ) -> tuple[str, dict]:
        """Process tool call (can modify or intercept)"""
        pass
    
    @abstractmethod
    async def process_output(self, output: str) -> str:
        """Process LLM output before returning"""
        pass

class FilesystemSecurityMiddleware(Middleware):
    """Validate file operations against allowed paths"""
    
    def __init__(self, allowed_root: str):
        self.allowed_root = allowed_root
    
    async def process_tool_call(self, tool_name, tool_input):
        if tool_name in ["read_file", "write_file", "edit_file"]:
            path = tool_input.get("path", "")
            if not self._is_allowed(path):
                # Block operation
                return tool_name, {"error": "Path not allowed"}
        return tool_name, tool_input
    
    def _is_allowed(self, path: str) -> bool:
        # Check if path is within allowed root
        abs_path = os.path.abspath(path)
        return abs_path.startswith(self.allowed_root)
    
    async def process_input(self, messages):
        return messages  # No input processing
    
    async def process_output(self, output):
        return output  # No output processing

class PermissionMiddleware(Middleware):
    """Check permissions for tool usage"""
    
    def __init__(self, permissions: dict[str, str]):
        self.permissions = permissions  # tool_name -> "allow"|"deny"|"ask"
    
    async def process_tool_call(self, tool_name, tool_input):
        perm = self.permissions.get(tool_name, "ask")
        
        if perm == "deny":
            return tool_name, {"error": f"Tool {tool_name} is disabled"}
        elif perm == "ask":
            # In interactive mode, ask user
            allowed = await self._ask_user(tool_name, tool_input)
            if not allowed:
                return tool_name, {"error": "Permission denied by user"}
        
        return tool_name, tool_input
    
    async def _ask_user(self, tool_name, tool_input) -> bool:
        # Interactive permission request
        print(f"Allow tool '{tool_name}' with input: {tool_input}? (y/n)")
        return input().lower() == 'y'
    
    async def process_input(self, messages):
        return messages
    
    async def process_output(self, output):
        return output

class SkillInjectionMiddleware(Middleware):
    """Inject relevant skills based on query"""
    
    def __init__(self, skills_loader):
        self.skills_loader = skills_loader
    
    async def process_input(self, messages):
        # Extract query from last user message
        last_message = messages[-1]["content"] if messages else ""
        
        # Find relevant skills
        relevant_skills = self.skills_loader.find_relevant(last_message)
        
        # Inject skills after system prompt
        if relevant_skills:
            skill_message = {
                "role": "system",
                "content": f"Relevant skills:\n" + "\n".join(relevant_skills)
            }
            # Insert after first system message
            if messages[0]["role"] == "system":
                messages.insert(1, skill_message)
            else:
                messages.insert(0, skill_message)
        
        return messages
    
    async def process_tool_call(self, tool_name, tool_input):
        return tool_name, tool_input
    
    async def process_output(self, output):
        return output

class ContextCompactionMiddleware(Middleware):
    """Auto-summarize old context when tokens exceed limit"""
    
    def __init__(self, token_limit: int = 8000, summarizer=None):
        self.token_limit = token_limit
        self.summarizer = summarizer
    
    async def process_input(self, messages):
        token_count = self._count_tokens(messages)
        
        if token_count > self.token_limit:
            # Summarize old messages
            old_messages = messages[:-3]  # Keep last 3 messages
            summary = await self.summarizer.summarize(old_messages)
            
            messages = [
                {"role": "system", "content": f"Summary of previous context:\n{summary}"},
                *messages[-3:]  # Keep recent context
            ]
        
        return messages
    
    def _count_tokens(self, messages) -> int:
        # Rough token counting (actual impl would use tokenizer)
        total = sum(len(m["content"].split()) for m in messages)
        return int(total / 0.75)  # Rough estimate
    
    async def process_tool_call(self, tool_name, tool_input):
        return tool_name, tool_input
    
    async def process_output(self, output):
        return output

class MiddlewarePipeline:
    """Execute middlewares in sequence"""
    
    def __init__(self, middlewares: list[Middleware]):
        self.middlewares = middlewares
    
    async def process_input(self, messages):
        for middleware in self.middlewares:
            messages = await middleware.process_input(messages)
        return messages
    
    async def process_tool_call(self, tool_name, tool_input):
        for middleware in self.middlewares:
            tool_name, tool_input = await middleware.process_tool_call(
                tool_name, tool_input
            )
        return tool_name, tool_input
    
    async def process_output(self, output):
        for middleware in self.middlewares:
            output = await middleware.process_output(output)
        return output
```

### 5. Session Management

**Pattern from: Copilot SDK**

```python
class Session:
    """Represents one agent session"""
    
    def __init__(
        self,
        session_id: str,
        working_directory: str,
        provider: LLMProvider,
        tools: ToolRegistry,
        middleware: MiddlewarePipeline,
        storage: SessionStorage = None
    ):
        self.id = session_id
        self.working_directory = working_directory
        self.provider = provider
        self.tools = tools
        self.middleware = middleware
        self.storage = storage or MemorySessionStorage()
        
        self.messages = []
        self.metadata = {}
    
    async def invoke(
        self,
        query: str,
        agent_type: AgentType = None,
        stream: bool = True
    ) -> AsyncIterator[str]:
        """Invoke agent with query"""
        
        # 1. Route to appropriate agent
        if agent_type is None:
            agent_type = self.router.route(query)
        agent = self.agents[agent_type]
        
        # 2. Add user message
        self.messages.append({
            "role": "user",
            "content": query
        })
        
        # 3. Process through middleware
        processed_messages = await self.middleware.process_input(self.messages)
        
        # 4. Invoke agent
        async for chunk in agent.invoke(
            query,
            AgentContext(
                provider=self.provider,
                tools=self.tools,
                middleware=self.middleware,
                storage=self.storage,
                working_directory=self.working_directory,
                session_id=self.id
            ),
            stream=stream
        ):
            yield chunk
        
        # 5. Save to memory
        await self._save_to_memory(query)
    
    async def _save_to_memory(self, query: str):
        """Save successful interaction to memory"""
        if self.storage:
            await self.storage.save(
                self.id,
                SessionData(
                    timestamp=datetime.now(),
                    query=query,
                    messages=self.messages,
                    metadata=self.metadata
                )
            )
    
    async def resume_from_checkpoint(self, checkpoint_id: str):
        """Resume session from saved state"""
        data = await self.storage.load(checkpoint_id)
        self.messages = data.messages
        self.metadata = data.metadata
    
    async def close(self):
        """Close session and save state"""
        await self.storage.finalize(self.id)
```

### 6. Skill Discovery, Catalog, and Learning

**Pattern from: autoskills + ECC + Deep Agents**

This section upgrades the prior skill manager design into a concrete skill discovery and enablement layer.

```python
from dataclasses import dataclass
from pathlib import Path
from typing import Any
import re
import yaml

class SkillDefinition:
    def __init__(
        self,
        id: str,
        name: str,
        description: str,
        content: str,
        tags: list[str],
        category: str = "general",
        harnesses: list[str] = None,
        version: str = "1.0.0",
        source: str = "internal",
    ):
        self.id = id
        self.name = name
        self.description = description
        self.content = content
        self.tags = tags or []
        self.category = category
        self.harnesses = harnesses or []
        self.version = version
        self.source = source

class TechnologyDetectRule:
    def __init__(
        self,
        packages: list[str] = None,
        package_patterns: list[str] = None,
        config_files: list[str] = None,
        config_content_patterns: list[str] = None,
    ):
        self.packages = packages or []
        self.package_patterns = package_patterns or []
        self.config_files = config_files or []
        self.config_content_patterns = config_content_patterns or []

class TechnologyDefinition:
    def __init__(self, id: str, name: str, detect: TechnologyDetectRule, skills: list[str]):
        self.id = id
        self.name = name
        self.detect = detect
        self.skills = skills

class ComboSkillDefinition:
    def __init__(self, id: str, name: str, requires: list[str], skills: list[str]):
        self.id = id
        self.name = name
        self.requires = requires
        self.skills = skills
```

### 6.1 Skill Registry and Catalog

```python
class SkillRegistry:
    def __init__(self, skills_dir: str, catalog_path: str | None = None):
        self.skills_dir = Path(skills_dir)
        self.catalog_path = Path(catalog_path) if catalog_path else None
        self.skills: dict[str, SkillDefinition] = {}
        self._load_catalog()
        self._load_skills_from_files()

    def _load_catalog(self):
        if not self.catalog_path or not self.catalog_path.exists():
            return
        raw = yaml.safe_load(self.catalog_path.read_text())
        for entry in raw.get("skills", []):
            skill = SkillDefinition(**entry)
            self.skills[skill.id] = skill

    def _load_skills_from_files(self):
        for path in self.skills_dir.rglob("*.md"):
            skill = self._parse_skill_file(path)
            self.skills[skill.id] = skill

    def _parse_skill_file(self, path: Path) -> SkillDefinition:
        text = path.read_text()
        title = re.search(r"^#\s+(.+)$", text, re.MULTILINE)
        name = title.group(1).strip() if title else path.stem
        description = self._extract_description(text)
        tags = self._extract_tags(text)
        category = self._determine_category(name, text)
        return SkillDefinition(
            id=path.stem,
            name=name,
            description=description,
            content=text,
            tags=tags,
            category=category,
            source="markdown",
        )

    def _extract_description(self, text: str) -> str:
        lines = [line.strip() for line in text.splitlines() if line.strip()]
        return lines[1] if len(lines) > 1 else ""

    def _extract_tags(self, text: str) -> list[str]:
        matches = re.findall(r"^tags:\s*(.+)$", text, re.MULTILINE)
        tags = []
        for line in matches:
            tags.extend([tag.strip() for tag in line.split(",") if tag.strip()])
        return tags

    def _determine_category(self, name: str, text: str) -> str:
        lower = (name + " " + text).lower()
        if "security" in lower or "vulnerability" in lower:
            return "security"
        if "testing" in lower or "ci" in lower:
            return "best_practices"
        if any(lang in lower for lang in ["python", "javascript", "rust", "go", "java"]):
            return "programming_languages"
        return "general"

    def get_skills(self, harness: str | None = None) -> list[SkillDefinition]:
        return [skill for skill in self.skills.values() if not harness or harness in skill.harnesses]

    def find_relevant(self, query: str, categories: list[str]) -> list[SkillDefinition]:
        lowered = query.lower()
        results = []
        for skill in self.skills.values():
            if any(tag in lowered for tag in skill.tags):
                results.append(skill)
                continue
            if skill.category in categories:
                results.append(skill)
        return results
```

### 6.2 Project Technology Detection

```python
class ProjectScanner:
    def __init__(self, root: Path):
        self.root = root

    def detect_technologies(self) -> list[str]:
        pkg = self._read_json(self.root / "package.json")
        deps = set(self._get_dependencies(pkg))
        techs = []

        for tech in TECHNOLOGIES:
            if any(pkg_name in deps for pkg_name in tech.detect.packages):
                techs.append(tech.id)
                continue
            if any((self.root / cfg).exists() for cfg in tech.detect.config_files):
                techs.append(tech.id)
                continue
            if self._matches_config_content(tech.detect.config_content_patterns):
                techs.append(tech.id)
        return techs

    def _get_dependencies(self, pkg: dict[str, Any]) -> list[str]:
        return list(pkg.get("dependencies", {}).keys()) + list(pkg.get("devDependencies", {}).keys())

    def _matches_config_content(self, patterns: list[str]) -> bool:
        for path in self.root.rglob("*"):
            if not path.is_file():
                continue
            text = path.read_text(errors="ignore").lower()
            if any(pattern.lower() in text for pattern in patterns):
                return True
        return False

    def _read_json(self, path: Path) -> dict[str, Any]:
        try:
            return json.loads(path.read_text())
        except Exception:
            return {}
```

### 6.3 Combo Detection

```python
class ComboDetector:
    def detect(self, technologies: list[str]) -> list[str]:
        return [combo.id for combo in COMBO_SKILLS if all(req in technologies for req in combo.requires)]
```

### 6.4 Skill Resolution

```python
class SkillResolver:
    def __init__(self, registry: SkillRegistry, combo_detector: ComboDetector):
        self.registry = registry
        self.combo_detector = combo_detector

    def resolve(self, project_dir: Path, harness: str | None = None) -> list[SkillDefinition]:
        detector = ProjectScanner(project_dir)
        techs = detector.detect_technologies()
        combos = self.combo_detector.detect(techs)
        skills = []
        for tech in techs:
            skills.extend(self._skills_for_tech(tech, harness))
        for combo in combos:
            skills.extend(self._skills_for_combo(combo, harness))
        return self._dedupe(skills)

    def _skills_for_tech(self, tech: str, harness: str | None) -> list[SkillDefinition]:
        return [skill for skill in self.registry.get_skills(harness) if tech in skill.tags]

    def _skills_for_combo(self, combo: str, harness: str | None) -> list[SkillDefinition]:
        return [skill for skill in self.registry.get_skills(harness) if combo in skill.tags]

    def _dedupe(self, skills: list[SkillDefinition]) -> list[SkillDefinition]:
        seen = set()
        unique = []
        for skill in skills:
            if skill.id not in seen:
                seen.add(skill.id)
                unique.append(skill)
        return unique
```

### 6.5 Skills Manager and Runtime Injection

```python
class SkillsManager:
    def __init__(self, registry: SkillRegistry, resolver: SkillResolver):
        self.registry = registry
        self.resolver = resolver
        self.active_skills: list[SkillDefinition] = []

    def enable_project_skills(self, project_dir: Path, harness: str | None = None):
        self.active_skills = self.resolver.resolve(project_dir, harness)

    def get_active_skill_texts(self) -> list[str]:
        return [skill.content for skill in self.active_skills]

    def find_relevant(self, query: str) -> list[SkillDefinition]:
        categories = analyze_query_expertise(query)
        return self.registry.find_relevant(query, categories)

    def inject_skills(self, messages: list[dict]) -> list[dict]:
        relevant = self.find_relevant(messages[-1]["content"] if messages else "")
        if relevant:
            skill_message = {
                "role": "system",
                "content": "Relevant skills:
" + "

".join(skill.content for skill in relevant[:5])
            }
            messages.insert(1 if messages and messages[0]["role"] == "system" else 0, skill_message)
        return messages
```

### 6.6 Continuous Learning

```python
class SkillLearner:
    def __init__(self, registry: SkillRegistry):
        self.registry = registry

    async def learn_from_session(self, session: Session):
        patterns = await self._extract_patterns(session.messages)
        for pattern in patterns:
            new_skill = SkillDefinition(
                id=pattern.id,
                name=pattern.name,
                description=pattern.description,
                content=pattern.content,
                tags=pattern.tags,
                category=pattern.category,
                source="learned",
            )
            self.registry.skills[new_skill.id] = new_skill
            self._save_skill(new_skill)

    async def _extract_patterns(self, messages: list[dict]) -> list[SkillDefinition]:
        pass

    def _save_skill(self, skill: SkillDefinition):
        path = self.registry.skills_dir / f"{skill.id}.md"
        path.write_text(skill.content)
```

### 6.7 Optional Git Hook Automation

ECC demonstrates strong value for Git hook automation, but it should remain optional and repository-scoped.

Recommended hooks:
- `pre-commit` — formatting, linting, selective unit tests, quick security checks
- `pre-push` — integration smoke tests, dependency audit, release validation
- `post-merge` — refresh skill registry, regenerate summaries, validate repo state

The hook layer should live outside the core agent runtime and act as a companion quality scaffold.

```bash
# scripts/pre-commit.sh
#!/usr/bin/env bash
set -e
npm run lint
npm run test:unit -- --changed
python -m security_scan
```

```bash
# scripts/post-merge.sh
#!/usr/bin/env bash
set -e
python -m agent_skill_refresh
npm install
```

```bash
# scripts/pre-push.sh
#!/usr/bin/env bash
set -e
npm run test:smoke
python -m dependency_audit
```

### When git hooks are needed
- yes for production and developer safety
- yes for AI-generated code quality gating
- no for the minimal runtime core; keep them optional
```
### 7. Execution Backends

**Pattern from: Deep Agents**

```python
class ExecutionBackend(ABC):
    """Backend for executing tools/commands"""
    
    @abstractmethod
    async def execute_command(self, command: str, cwd: str = None) -> str:
        """Execute shell command"""
        pass
    
    @abstractmethod
    async def read_file(self, path: str) -> bytes:
        """Read file contents"""
        pass
    
    @abstractmethod
    async def write_file(self, path: str, content: bytes):
        """Write file contents"""
        pass
    
    @abstractmethod
    async def list_directory(self, path: str) -> list[str]:
        """List directory contents"""
        pass

class LocalExecutionBackend(ExecutionBackend):
    """Execute on local machine"""
    
    async def execute_command(self, command: str, cwd: str = None) -> str:
        process = await asyncio.create_subprocess_shell(
            command,
            cwd=cwd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )
        stdout, stderr = await process.communicate()
        return stdout.decode() or stderr.decode()
    
    async def read_file(self, path: str) -> bytes:
        with open(path, 'rb') as f:
            return f.read()
    
    async def write_file(self, path: str, content: bytes):
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, 'wb') as f:
            f.write(content)
    
    async def list_directory(self, path: str) -> list[str]:
        return os.listdir(path)

class SandboxedExecutionBackend(ExecutionBackend):
    """Execute in isolated sandbox (e.g., e2b, Docker)"""
    
    def __init__(self, sandbox_config):
        self.config = sandbox_config
        # Initialize sandbox connection
    
    async def execute_command(self, command: str, cwd: str = None) -> str:
        # Execute via sandbox API
        result = await self.sandbox.run_command(command, cwd=cwd)
        return result.stdout or result.stderr
    
    async def read_file(self, path: str) -> bytes:
        return await self.sandbox.read_file(path)
    
    async def write_file(self, path: str, content: bytes):
        await self.sandbox.write_file(path, content)
    
    async def list_directory(self, path: str) -> list[str]:
        return await self.sandbox.list_directory(path)
```

### 8. Configuration System

**Pattern from: ECC**

```python
@dataclass
class AgentConfig:
    name: str
    type: AgentType
    system_prompt: str
    available_tools: list[str]
    skills: list[str]
    model_preference: str = None

@dataclass
class ProviderConfig:
    type: str  # "openai", "anthropic", "ollama", "gemini"
    api_key: str = None
    base_url: str = None
    model: str = None
    
    @property
    def is_valid(self) -> bool:
        if self.type == "ollama":
            return bool(self.base_url)
        return bool(self.api_key and self.model)

class Config:
    """Main configuration management"""
    
    def __init__(self, config_file: str = None):
        self.config_file = config_file or "~/.agent/config.yaml"
        self.data = self._load_config()
    
    def _load_config(self) -> dict:
        """Load config from file or env vars"""
        config = {}
        
        # 1. Try loading from file
        if os.path.exists(self.config_file):
            with open(self.config_file) as f:
                config = yaml.safe_load(f)
        
        # 2. Override with environment variables
        for key, value in os.environ.items():
            if key.startswith("AGENT_"):
                config_key = key[6:].lower()
                config[config_key] = value
        
        return config
    
    def get_provider_config(self) -> ProviderConfig:
        return ProviderConfig(
            type=self.data.get("provider_type", "openai"),
            api_key=self.data.get("api_key"),
            base_url=self.data.get("base_url"),
            model=self.data.get("model")
        )
    
    def get_agents_config(self) -> dict[str, AgentConfig]:
        # Load agent configurations
        pass
    
    def save(self):
        """Save config to file"""
        os.makedirs(os.path.dirname(self.config_file), exist_ok=True)
        with open(self.config_file, 'w') as f:
            yaml.dump(self.data, f)
```

---

## Integration Architecture

### Complete System Diagram

```
┌─────────────────────────────────────────────────┐
│              User Interface                      │
│  (CLI / Web / IDE Extension)                     │
└────────────────┬────────────────────────────────┘
                 │
                 ▼
┌─────────────────────────────────────────────────┐
│         Message Handler                         │
│  Parses user input, routes to agent             │
└────────────────┬────────────────────────────────┘
                 │
                 ▼
┌─────────────────────────────────────────────────┐
│         Agent Router                            │
│  Determines which agent should handle request   │
└────────────────┬────────────────────────────────┘
                 │
         ┌───────┴───────┐
         ▼               ▼
    ┌────────┐      ┌────────┐
    │ Agent  │      │ Agent  │
    └───┬────┘      └───┬────┘
        │               │
        └───────┬───────┘
                ▼
┌─────────────────────────────────────────────────┐
│      Middleware Pipeline                        │
│  ├─ Permission Middleware                       │
│  ├─ Filesystem Security Middleware              │
│  ├─ Skill Injection Middleware                  │
│  ├─ Context Compaction Middleware               │
│  └─ Tool Call Validation Middleware             │
└────────────────┬────────────────────────────────┘
                 │
                 ▼
┌─────────────────────────────────────────────────┐
│      LLM Provider Abstraction                   │
│  ├─ OpenAI (GPT-4, GPT-4o)                      │
│  ├─ Anthropic (Claude models)                   │
│  ├─ Ollama (Local models)                       │
│  ├─ Gemini (Google models)                      │
│  └─ Custom OpenAI-compatible                    │
└────────────────┬────────────────────────────────┘
                 │
                 ▼
    ┌────────────────────────────┐
    │  LLM Response Stream        │
    │  ├─ Text chunks            │
    │  ├─ Tool calls             │
    │  └─ Completion events      │
    └────────────┬───────────────┘
                 │
        ┌────────┴────────┐
        ▼                 ▼
   ┌────────────┐    ┌──────────────┐
   │ Tool       │    │ Streaming    │
   │ Execution  │    │ Output       │
   └─────┬──────┘    └──────────────┘
         │
    ┌────┴──────────────────────────┐
    ▼                                ▼
┌──────────────┐          ┌─────────────────┐
│   Local      │          │  Sandboxed      │
│ Execution    │          │  Execution      │
│ Backend      │          │  Backend        │
└──────────────┘          └─────────────────┘
    │                          │
    ▼                          ▼
 Filesystem              Isolated
 Shell                   Container
 Execution               or Sandbox
```

---

## Implementation Roadmap

### Phase 1: Foundation (Week 1-2)
- [ ] Set up project structure
- [ ] Implement provider abstraction
- [ ] Create basic tool system
- [ ] Implement middleware pipeline
- [ ] Add dynamic MCP server management

### Phase 2: Core Agent (Week 3-4)
- [ ] Implement agent routing
- [ ] Create specialized agents (5 core)
- [ ] Add message handling
- [ ] Implement streaming

### Phase 3: Enhancement (Week 5-6)
- [ ] Add structured skills system (programming languages, cloud, DevOps, data, security)
- [ ] Implement memory/persistence
- [ ] Add permission system
- [ ] Create multiple backends
- [ ] Add vulnerability assessment and best practices skills

### Phase 4: Learning & Optimization (Week 7-8)
- [ ] Implement continuous learning
- [ ] Add cost tracking
- [ ] Optimization middleware
- [ ] Add more agents (15+)

### Phase 5: Production (Week 9+)
- [ ] Full test coverage (80%+)
- [ ] Security audit
- [ ] Performance optimization
- [ ] Documentation
- [ ] Multiple provider support

---

## Security Best Practices

### Input Validation
```python
def validate_tool_input(tool_name: str, input_dict: dict) -> tuple[bool, str]:
    """Validate tool input before execution"""
    
    # Check for command injection
    if tool_name == "bash":
        if any(dangerous in input_dict.get("command", "") 
               for dangerous in [";", "|", "&", "$", "`"]):
            return False, "Potentially dangerous command"
    
    # Check path traversal
    if tool_name in ["read_file", "write_file"]:
        path = input_dict.get("path", "")
        if ".." in path or path.startswith("/"):
            return False, "Invalid path"
    
    return True, ""
```

### Permission System
```python
DEFAULT_PERMISSIONS = {
    "read_file": "allow",
    "write_file": "ask",
    "bash": "ask",
    "web_search": "allow",
    "delete_file": "deny",
}
```

### Error Handling
```python
try:
    result = await tool.execute(input, context)
except Exception as e:
    # Log detailed error internally
    logger.error(f"Tool {tool_name} failed: {e}", exc_info=True)
    
    # Return safe error to user
    return ToolResult(
        success=False,
        error="Tool execution failed. Please try again or provide more details."
    )
```

---

## Testing Strategy

### Coverage Requirements
- **Unit Tests:** 80%+ coverage
- **Integration Tests:** Critical paths
- **E2E Tests:** Common workflows

### Test Categories
```python
# Unit tests - isolated tool logic
def test_read_file_tool():
    tool = ReadFileTool()
    result = tool.execute(ReadFileTool.Input(path="/tmp/test.txt"))
    assert result.success

# Integration tests - tool + filesystem
async def test_read_write_integration():
    backend = LocalExecutionBackend()
    
    # Write file
    await backend.write_file("/tmp/test.txt", b"content")
    
    # Read file
    content = await backend.read_file("/tmp/test.txt")
    assert content == b"content"

# E2E tests - full agent workflow
async def test_code_review_workflow():
    agent = create_agent()
    result = await agent.invoke("Review this code: def foo(): pass")
    assert "PEP 8" in result or "style" in result.lower()
```

---

## Monitoring & Observability

### Metrics to Track
```python
class AgentMetrics:
    total_invocations: int
    successful_invocations: int
    failed_invocations: int
    
    total_tokens_used: int
    total_cost: float
    
    tool_execution_times: dict[str, float]
    agent_response_times: dict[str, float]
    
    error_rates: dict[str, float]
```

### Logging
```python
import logging

logger = logging.getLogger("agent")

logger.info(f"Agent {agent.name} invoked with query: {query}")
logger.info(f"Tool {tool_name} executed successfully in {time_ms}ms")
logger.warning(f"Tool {tool_name} execution slow: {time_ms}ms")
logger.error(f"Tool {tool_name} failed: {error}")
```

---

## Deployment Considerations

### Local Development
```bash
# Use local LLM (Ollama)
export AGENT_PROVIDER_TYPE=ollama
export AGENT_BASE_URL=http://localhost:11434
export AGENT_MODEL=mistral:latest

python -m agent.cli
```

### Production
```bash
# Use cloud provider
export AGENT_PROVIDER_TYPE=openai
export AGENT_API_KEY=${OPENAI_API_KEY}
export AGENT_MODEL=gpt-4-turbo

# With logging and monitoring
export LOG_LEVEL=INFO
export SENTRY_DSN=${SENTRY_DSN}

gunicorn agent.api:app
```

---

## Summary: What to Build

✅ **MUST HAVE:**
1. Multi-provider LLM abstraction (OpenAI, Anthropic, Ollama, Gemini)
2. Modular tool system with permissions
3. Agent routing and specialization
4. Streaming response handling
5. Middleware pipeline for extensibility
6. Session management with persistence
7. Error handling and recovery
8. Cost tracking

✅ **SHOULD HAVE:**
1. Skill/knowledge injection system
2. Continuous learning from sessions
3. Multiple execution backends (local + sandboxed)
4. Security validation middleware
5. Context compaction for long conversations
6. Sub-agent delegation
7. Comprehensive logging

✅ **NICE TO HAVE:**
1. Web UI dashboard
2. Metric visualization
3. Advanced caching strategies
4. Custom LLM fine-tuning integration
5. Distributed execution
6. Plugin marketplace

---

## Key Insights from Four Codebases

| Feature | Source | Why Important |
|---------|--------|---------------|
| Provider Abstraction | OpenClaude | Works with any LLM |
| Tool Architecture | OpenClaude + Copilot | Extensible and safe |
| Middleware Pipeline | Deep Agents | Composable, modular |
| Agent Specialization | ECC | Better results per domain |
| Skills System | ECC | Continuous improvement |
| Permission System | Copilot SDK | Security & compliance |
| Streaming | OpenClaude | Better UX |
| Backends | Deep Agents | Flexible execution |
| Message Protocol | Copilot SDK | Interoperability |
| Session Persistence | All four | Resumable workflows |

---

## Final Recommendations

1. **Start with Provider + Tool foundation** (simplest, highest value)
2. **Add Agent routing next** (enables specialization)
3. **Build middleware pipeline early** (enables extensibility)
4. **Implement streaming throughout** (better UX)
5. **Add skills + memory later** (continuous improvement)
6. **Integrate security middlewares** (non-negotiable)
7. **Support multiple backends** (flexibility)
8. **Test everything thoroughly** (production readiness)

---

## Conclusion

By synthesizing the best practices from Copilot SDK (protocol + permissions), Deep Agents (middleware + backends), OpenClaude (multi-provider + streaming), and Everything Claude Code (agents + skills + learning), you have a blueprint for building a **world-class, production-ready coding agent** that is:

- ✅ **Flexible** (multiple LLM providers, tools, agents)
- ✅ **Extensible** (middleware, custom tools, skills)
- ✅ **Secure** (permissions, validation, sandboxing)
- ✅ **Learnable** (skills from sessions, continuous improvement)
- ✅ **Observable** (logging, metrics, tracing)
- ✅ **Maintainable** (clear architecture, testing)

Good luck building your coding agent! 🚀
