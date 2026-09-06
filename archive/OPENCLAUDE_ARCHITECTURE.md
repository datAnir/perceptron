# OpenClaude - Complete Architecture Reference

## Overview

**OpenClaude** is an open-source **coding-agent CLI** that provides a terminal-first workflow for AI-powered development using multiple LLM providers (OpenAI, Anthropic, Gemini, GitHub Models, Ollama, and others).

**Current Version:** Latest (main branch)  
**Language:** TypeScript/Bun  
**UI Framework:** React + Ink (terminal UI)  
**Key Strength:** Provider agnostic - works with any OpenAI-compatible API or Ollama

---

## Architecture Overview

### High-Level Architecture

```
┌─────────────────────────────────────┐
│  OpenClaude Terminal UI (Ink/React) │
│  ├─ Main REPL Loop                  │
│  ├─ Command Parser (/provider, etc) │
│  ├─ Streaming Renderer              │
│  └─ Multi-pane Display              │
└────────────┬────────────────────────┘
             │
             ▼
      ┌──────────────────┐
      │  Query Engine    │  ◄── Main orchestrator
      │  (query.ts)      │      - Message handling
      └────────┬─────────┘      - Tool calls
               │                - Streaming
               ▼
      ┌──────────────────┐
      │  Tool System     │
      │  (tools/)        │  ◄── Modular tools
      │  ├─ Bash         │      - Filesystem
      │  ├─ Grep         │      - Web search
      │  ├─ Glob         │      - Agents
      │  ├─ Web Search   │      - REPL
      │  ├─ Agents       │      - MCP servers
      │  └─ MCP Tools    │
      └────────┬─────────┘
               │
               ▼
      ┌──────────────────┐
      │  LLM Providers   │
      │  (QueryEngine)   │  ◄── Multiple backends
      │  ├─ OpenAI       │      - Stream parsing
      │  ├─ Anthropic    │      - Tool routing
      │  ├─ Gemini       │      - Cost tracking
      │  ├─ GitHub Models│
      │  ├─ Ollama       │
      │  └─ Custom APIs  │
      └──────────────────┘
```

### Project Structure

```
openclaude/
├── src/
│   ├── main.tsx              # Entry point & CLI bootstrapping
│   ├── commands.ts           # Slash command registry
│   ├── commands/             # Command implementations
│   │   ├── agents.ts         # Agent-related commands
│   │   ├── mcp.tsx           # MCP server management
│   │   └── ...
│   │
│   ├── query.ts              # Main query orchestration (1700+ lines)
│   ├── QueryEngine.ts        # Provider-specific logic
│   ├── Tool.ts               # Tool base class & invocation
│   │
│   ├── tools/                # Tool implementations (49 subdirs)
│   │   ├── BashTool/
│   │   ├── FileTool/
│   │   ├── GrepTool/
│   │   ├── AgentTool/        # Delegate to other agents
│   │   ├── WebSearchTool/
│   │   ├── TaskTool/
│   │   ├── MCPTool/          # Model Context Protocol
│   │   └── ...
│   │
│   ├── services/             # Business logic modules (26 subdirs)
│   │   ├── mcp/              # MCP integration
│   │   ├── compact/          # Context compaction
│   │   ├── cost-tracker.ts   # Usage cost tracking
│   │   ├── memory/           # Persistent memory
│   │   ├── shell/            # Shell command routing
│   │   └── ...
│   │
│   ├── components/           # React/Ink components (33 subdirs)
│   │   ├── PromptInput.tsx
│   │   ├── Spinner.tsx
│   │   ├── Message.tsx
│   │   └── ...
│   │
│   ├── memdir/               # Memory system
│   ├── context.ts            # Global app context
│   ├── setup.ts              # Configuration/initialization
│   ├── state/                # App state management
│   ├── utils/                # Utilities (26 subdirs)
│   │   ├── permissions/      # Permission system
│   │   ├── theme.ts
│   │   ├── cost-tracker.ts
│   │   └── ...
│   │
│   ├── hooks/                # React hooks
│   ├── keybindings/          # Keyboard shortcuts
│   ├── cli/                  # CLI-specific code
│   └── types/                # TypeScript types
│
├── docs/                     # Documentation
├── vscode-extension/         # VS Code integration
└── package.json
```

---

## Core Concepts

### 1. Query-Driven Architecture

The **query** is the fundamental unit:
- User types a prompt → creates a query
- Query goes through agent loop (plan → tool call → result)
- Results streamed back to UI
- Saved to memory for future reference

### 2. Tool-Based Extensibility

Tools are the primary extension point:
- Each tool is a TypeScript class extending `Tool`
- Implements `execute(args, context)` method
- Can call other tools
- Can spawn sub-agents
- Return structured results or streaming output

### 3. Provider Agnostic

Supports multiple LLM providers:
- **OpenAI API** - GPT-4, GPT-4o
- **Anthropic** - Claude models
- **Gemini** - Google models
- **GitHub Models** - Hosted models
- **Ollama** - Local models
- **Custom OpenAI-compatible APIs**

---

## File Structure & Key Modules

### `main.tsx` (232KB - Entry Point & CLI)

**Purpose:** Application bootstrap and main REPL loop.

**Key Responsibilities:**
1. Parse CLI arguments and environment
2. Initialize providers (from env vars or interactive setup)
3. Launch Ink/React UI
4. Handle user input stream
5. Route commands and queries
6. Display responses and handle streaming

**Key Functions:**

```typescript
async function main() {
    // 1. Initialize config
    const config = loadConfig()  // From env/config file
    
    // 2. Get provider
    const provider = await getProvider(config)
    
    // 3. Load agent state
    const state = await loadAgentState()
    
    // 4. Launch UI
    return render(
        <App provider={provider} state={state} />
    )
}
```

**Configuration Sources (in order):**
1. Environment variables: `CLAUDE_CODE_*`
2. Config file: `~/.openclaude/config.json`
3. Interactive setup: `/provider` command
4. Defaults: OpenAI with bundled models

---

### `query.ts` (1700+ lines - Main Orchestrator)

**Purpose:** Core agent loop - coordinates message handling, tool calls, streaming.

**Key Concepts:**

#### Query State Machine

```
START → ASK_USER → GET_RESPONSE → HAS_TOOL_CALL?
                                    ├─ YES → EXECUTE_TOOL → GET_RESULT → LOOP_BACK
                                    └─ NO → STREAMING_RESPONSE → DONE
```

#### Main Invocation Flow

```typescript
async function executeQuery(
    query: string,
    context: QueryContext
): Promise<void> {
    // 1. Prepare messages with context
    const messages = buildMessages(query, context)
    
    // 2. Get LLM response
    const response = await provider.createMessage({
        model: config.model,
        messages: messages,
        tools: enabledTools,
        stream: true
    })
    
    // 3. Handle streaming response
    for await (const event of response) {
        if (event.type === "content_block_start") {
            if (event.content_block.type === "tool_use") {
                // Tool call incoming
            } else if (event.content_block.type === "text") {
                // Text content
            }
        }
        
        if (event.type === "tool_call") {
            // 4. Execute tool
            const result = await executeTool(
                event.tool_name,
                event.tool_input,
                context
            )
            
            // Add result to messages and continue loop
            messages.push({ role: "user", content: result })
        }
    }
}
```

#### Key Capabilities

1. **Message Management**
   - Builds message history
   - Injects context/skills
   - Manages token budget
   - Compacts old messages when needed

2. **Tool Invocation**
   - Parses tool calls from LLM response
   - Validates parameters
   - Handles parallel tool calls
   - Retries on failure

3. **Streaming**
   - Real-time text chunks
   - Streaming tool results
   - Progress indicators
   - Cost tracking

4. **Error Handling**
   - Recovers from tool failures
   - Retries with context
   - User-friendly error messages

---

### `Tool.ts` (29KB - Base Tool Class)

**Purpose:** Abstract base class for all tools.

**Key Structure:**

```typescript
export abstract class Tool {
    // Metadata
    name: string
    description: string
    category: string
    
    // Configuration
    permissions: PermissionMode[]
    requires: string[]  // Dependent tools
    
    // Validation
    validateInput(input: unknown): ValidationResult
    
    // Main execution
    abstract execute(
        input: ToolInput,
        context: ToolExecutionContext
    ): Promise<ToolResult>
    
    // Optional hooks
    onBeforeExecute?(input: ToolInput): Promise<void>
    onAfterExecute?(result: ToolResult): Promise<void>
}
```

#### Tool Result

```typescript
type ToolResult = 
    | { success: true; output: string }
    | { success: false; error: string }
    | { stream: AsyncIterable<string> }
    | { tool_calls: ToolCall[] }
```

#### Tool Execution Context

```typescript
interface ToolExecutionContext {
    workingDirectory: string
    queryId: string
    agentId: string
    
    // Sub-tool access
    callTool(name: string, input: unknown): Promise<ToolResult>
    
    // State
    getState(): AppState
    
    // Memory
    memory: MemoryService
    
    // Permissions
    requestPermission(tool: string): Promise<boolean>
}
```

---

### `tools/` Directory - Core Tools Implementation

#### 1. **BashTool**
```typescript
// Execute shell commands with safety checks
// - Path validation
// - Command auditing
// - Output streaming
// - Exit code handling
```

#### 2. **FileTool** (read/write/edit)
```typescript
// Filesystem operations
// - File reading
// - File creation/modification
// - Inline editing (replace line ranges)
// - Binary file handling
```

#### 3. **GrepTool**
```typescript
// Pattern searching with ripgrep
// - Multi-file search
// - Regex patterns
// - Context lines
// - Performance optimized
```

#### 4. **GlobTool**
```typescript
// File finding
// - Glob patterns
// - Recursive search
// - Filtering
```

#### 5. **WebSearchTool**
```typescript
// Web search via Exa or similar
// - Query formatting
// - Result ranking
// - Context extraction
// - Rate limiting
```

#### 6. **AgentTool**
```typescript
// Delegate to specialized agents
// - Load agent definitions from AGENTS.md
// - Isolated context window
// - Result summarization
```

#### 7. **MCPTool**
```typescript
// Model Context Protocol servers
// - Server discovery
// - Tool registration
// - Request/response handling
```

#### 8. **REPLTool** (if available)
```typescript
// Interactive code execution
// - Language support (Python, Node, etc.)
// - State persistence
// - Output capture
```

---

### `QueryEngine.ts` (47KB - Provider Integration)

**Purpose:** Handle provider-specific logic for API calls, streaming, tool parsing.

**Key Responsibilities:**

1. **Message Formatting**
   - Convert OpenClaude messages → Provider format
   - Handle system prompts correctly
   - Inject tool definitions

2. **Streaming Response Parsing**
   - Parse delta events
   - Identify tool calls
   - Track content blocks
   - Handle stop reasons

3. **Tool Definition Conversion**
   - OpenClaude tools → JSON schema
   - Provider-specific format adjustments

4. **Error Recovery**
   - API errors → user-friendly messages
   - Rate limiting → backoff
   - Malformed responses → retry

**Multi-Provider Pattern:**

```typescript
export async function createQueryEngine(provider: Provider) {
    if (provider.type === "openai") {
        return new OpenAIQueryEngine(provider)
    } else if (provider.type === "anthropic") {
        return new AnthropicQueryEngine(provider)
    } else if (provider.type === "ollama") {
        return new OllamaQueryEngine(provider)
    }
    // ...
}

class OpenAIQueryEngine implements QueryEngine {
    async invoke(request: InvokeRequest) {
        // OpenAI-specific implementation
        const response = await this.client.messages.create({
            model: request.model,
            messages: request.messages,
            tools: request.tools?.map(convertTool),
            stream: true
        })
        
        for await (const chunk of response) {
            if (chunk.type === "content_block_delta") {
                yield { type: "text", text: chunk.delta.text }
            }
        }
    }
}
```

---

### `components/` - UI Layer (React + Ink)

#### Key Components

1. **PromptInput.tsx** (73 lines of changes)
   - User input handling
   - Command suggestions
   - History navigation

2. **Spinner.tsx** (14+ lines of changes)
   - Visual progress indicator
   - Animated output
   - State tracking

3. **Message.tsx**
   - Display agent responses
   - Format tool calls
   - Render streaming output

4. **ThemePicker.tsx** (522 lines - refactored)
   - Color scheme selection
   - Theme persistence
   - Dark/light mode

5. **ProviderManager.tsx** (1553 lines - new)
   - Provider setup UI
   - Configuration dialog
   - Credential management

---

### `services/` - Business Logic

#### 1. **mcp/** - Model Context Protocol
- MCP server discovery and connection
- Tool registration from MCP servers
- Request routing

#### 2. **compact/** - Context Compaction
- Token counting
- Message summarization
- Old conversation archival
- Smart truncation

#### 3. **cost-tracker.ts**
- Track API costs per query
- Cost by provider
- Daily/monthly summaries
- Budget alerts

#### 4. **memory/** - Persistent Memory
- Session history storage
- Query summaries
- Context retrieval
- File-based or database storage

#### 5. **shell/** - Shell Integration
- Command history
- Environment setup
- Working directory tracking

#### 6. **permissions/** - Access Control
- Tool blacklist/whitelist
- Permission requests
- Audit logging

---

### `utils/` - Utilities

#### Key Utilities

1. **permissions/permissions.ts**
   - Permission checking logic
   - Permission models
   - Validation rules

2. **theme.ts**
   - Color definitions
   - Theme application
   - Terminal capability detection

3. **thinking.ts**
   - Extended thinking support (Claude)
   - Budget management

4. **cost-tracker.ts**
   - Token calculation
   - Cost estimation
   - Billing integration

5. **fileStateCache.ts**
   - File metadata caching
   - Modification detection
   - Performance optimization

6. **systemPromptType.ts**
   - System prompt construction
   - Context injection
   - Prompt optimization

---

### `memdir/` - Memory System

```typescript
class MemoryDirectory {
    // Persistent memory storage
    // - Session history
    // - Summaries
    // - Learned patterns
    // - Cost history
    
    async saveSession(id: string, data: SessionData)
    async loadSession(id: string): Promise<SessionData>
    async querySessions(pattern: string): Promise<SessionData[]>
    async summarizeSessions(count: number): Promise<Summary>
}
```

---

## Configuration & Setup

### Environment Variables

```bash
# Provider selection
export CLAUDE_CODE_USE_OPENAI=1           # Use OpenAI
export CLAUDE_CODE_USE_ANTHROPIC=1        # Use Anthropic
export CLAUDE_CODE_USE_OLLAMA=1           # Use Ollama

# Credentials
export OPENAI_API_KEY=sk-...
export ANTHROPIC_API_KEY=sk-ant-...
export OLLAMA_BASE_URL=http://localhost:11434

# Model selection
export OPENAI_MODEL=gpt-4o
export ANTHROPIC_MODEL=claude-opus-4-6
export OLLAMA_MODEL=qwen2.5-coder:7b

# Configuration
export CLAUDE_CODE_WORK_DIR=/path/to/project
export CLAUDE_CODE_THEME=dark
export CLAUDE_CODE_TIMEOUT=30
```

### Provider Setup (Interactive)

```
openclaude
> /provider
? Select provider: OpenAI
? API Key: sk-...
? Model: gpt-4o
✓ Provider configured
```

---

## Streaming Architecture

### Streaming Pipeline

```
Provider Stream
    ↓
QueryEngine Parser
    ├─ Text chunks → TextEvent
    ├─ Tool start → ToolStartEvent
    ├─ Tool input → ToolInputEvent
    └─ Stop reason → CompletionEvent
    ↓
Tool Executor
    ├─ Execute if tool call
    ├─ Stream result
    └─ Resume loop
    ↓
UI Renderer
    ├─ Display text
    ├─ Show spinner for tools
    └─ Update state
```

### Real-Time Display

```typescript
// As stream events arrive:
// 1. Display text in real-time
// 2. Show tool invocation with parameters
// 3. Execute tool in background
// 4. Display result streaming in
// 5. Resume agent loop if more iterations
// 6. Final summary with cost
```

---

## Extension Points

### 1. Custom Tools

```typescript
export class MyDatabaseTool extends Tool {
    name = "db_query"
    description = "Query our internal database"
    
    async execute(input: { sql: string }, context) {
        const result = await context.database.query(input.sql)
        return { success: true, output: JSON.stringify(result) }
    }
}

// Register
registerTool(new MyDatabaseTool())
```

### 2. Custom Providers

```typescript
export class MyLLMProvider extends Provider {
    async createMessage(request) {
        // Your API integration
        return streamResponse
    }
}
```

### 3. Custom Memory Backend

```typescript
export class PostgresMemory extends MemoryBackend {
    async save(id, data) { /* ... */ }
    async load(id) { /* ... */ }
}
```

### 4. Custom Permission Handler

```typescript
const permissions = {
    bash: "ask",           // Ask user
    read_file: "allow",    // Always allow
    web_search: "deny"     // Never allow
}
```

---

## Best Practices

### 1. Tool Design
- Single responsibility
- Clear input validation
- Streaming for long operations
- Error handling with context

### 2. Context Management
- Use working directory to scope file operations
- Remember file edits across queries
- Cache expensive operations

### 3. Error Handling
- Friendly error messages
- Suggest recovery actions
- Log errors for debugging

### 4. Performance
- Stream results for large outputs
- Lazy-load tools
- Cache provider connections

### 5. Security
- Validate all user input
- Enforce permission checks
- Audit sensitive operations
- Rate limit if needed

---

## Key Takeaways for Coding Agent Implementation

1. **Provider Abstraction** - Support multiple LLM backends via QueryEngine pattern
2. **Tool-Based Extensibility** - Tools as primary extension point
3. **Streaming Architecture** - Real-time output handling
4. **Message State Machine** - Clear message flow in agent loop
5. **Permission System** - Fine-grained access control
6. **Memory Persistence** - Session history and context
7. **Cost Tracking** - Monitor API usage and costs
8. **Interactive Setup** - User-friendly configuration

---

## Integration Recommendations for Your Coding Agent

✅ **From OpenClaude, adopt:**
- Tool-based architecture (extends Tool base class)
- QueryEngine pattern for multi-provider support
- Streaming response handling
- Message history management
- Permission/elicitation pattern
- Memory system for persistence
- Cost tracking
- Command-driven CLI with slash commands

✅ **Definitely use:**
- TypeScript for type safety
- Ink for terminal UI (if building TUI)
- Support multiple LLM providers

❌ **May skip:**
- Specific provider integrations (build your own as needed)
- React components (if not building TUI)
- Claude-specific features (support multiple models)

---

## File Reference

| File | Size | Purpose |
|------|------|---------|
| `main.tsx` | 232KB | Entry point & CLI bootstrap |
| `query.ts` | 74KB | Query orchestration & agent loop |
| `QueryEngine.ts` | 47KB | Provider-specific API integration |
| `Tool.ts` | 29KB | Base tool class |
| `commands.ts` | 25KB | Slash command registry |
| `cost-tracker.ts` | 10KB | Usage tracking |
| `setup.ts` | 18KB | Configuration initialization |
