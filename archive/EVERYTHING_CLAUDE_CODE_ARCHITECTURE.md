# Everything Claude Code (ECC) - Complete Architecture Reference

## Overview

**Everything Claude Code (ECC)** is a **production-ready AI coding system** providing 48 specialized agents, 156+ skills, 72 legacy command shims, and continuous learning workflows. Built to work across multiple AI harnesses (Claude Code, Cursor, OpenCode, Codex, Gemini, etc.).

**Current Version:** 1.10.0  
**Stars:** 140K+  
**Contributors:** 170+  
**Language Ecosystems:** 12+ (TypeScript, Python, Go, Rust, Java, Kotlin, PHP, Perl, Dart, C++, Swift)  
**Previous Achievement:** Anthropic Hackathon Winner

---

## Core Philosophy

1. **Agent-First** — Delegate to specialized agents for domain tasks
2. **Test-Driven** — 80%+ coverage, tests before implementation
3. **Security-First** — Never compromise; validate all inputs
4. **Immutability** — Create new objects, never mutate
5. **Plan Before Execute** — Plan complex features before coding

---

## Architecture Overview

### System Layers

```
┌─────────────────────────────────────────────┐
│  User Harness (Claude Code, Cursor, etc.)   │
└────────────┬────────────────────────────────┘
             │
             ▼
┌─────────────────────────────────────────────┐
│  ECC Main Agent                             │
│  - Route to specialist agents               │
│  - Manage agent orchestration               │
│  - Handle skill injection                   │
└────────────┬────────────────────────────────┘
             │
             ▼
┌─────────────────────────────────────────────┐
│  48 Specialized Agents                      │
│  ├─ Architecture agents (architect, code-arch)
│  ├─ Review agents (code-reviewer, sec-rev)  │
│  ├─ Build agents (build-resolver, deploy)   │
│  ├─ Lang-specific (java-rev, rust-rev, etc) │
│  ├─ Domain agents (database-rev, api-design)│
│  └─ Operator agents (loop-operator, etc)    │
└────────────┬────────────────────────────────┘
             │
             ▼
┌─────────────────────────────────────────────┐
│  156+ Skills (Markdown-based knowledge)     │
│  ├─ Language patterns                       │
│  ├─ Architecture patterns                   │
│  ├─ Security guidelines                     │
│  ├─ Testing patterns                        │
│  ├─ Framework patterns                      │
│  └─ Domain knowledge                        │
└────────────┬────────────────────────────────┘
             │
             ▼
┌─────────────────────────────────────────────┐
│  Core Tools & Utilities                     │
│  ├─ File operations                         │
│  ├─ Testing framework                       │
│  ├─ Build/compilation                       │
│  ├─ Memory & learning                       │
│  └─ Hooks & automation                      │
└─────────────────────────────────────────────┘
```

### Directory Structure

```
everything-claude-code/
├── agents/                    # Agent definitions (48 agents)
│   ├── architect.md          # System design
│   ├── code-reviewer.md      # Code quality
│   ├── tdd-guide.md          # TDD workflow
│   ├── security-reviewer.md  # Vulnerability detection
│   ├── build-error-resolver.md
│   ├── planner.md
│   ├── *-reviewer.md         # Lang-specific reviewers
│   ├── *-build-resolver.md   # Lang-specific builders
│   ├── loop-operator.md      # Autonomous loop control
│   └── [37 more agents]
│
├── skills/                    # 156+ Markdown skill files
│   ├── agents/               # Agent design patterns
│   ├── api-design/           # REST API guidelines
│   ├── architecture/         # System design patterns
│   ├── testing/              # Testing strategies
│   ├── security/             # Security best practices
│   ├── python/               # Python-specific
│   ├── java/                 # Java-specific
│   ├── typescript/           # TypeScript-specific
│   ├── rust/                 # Rust-specific
│   ├── golang/               # Go-specific
│   ├── kotlin/               # Kotlin-specific
│   ├── [more language dirs]
│   └── [more domain dirs]
│
├── rules/                     # Language-specific rules (17 langs)
│   ├── python/
│   │   ├── patterns.md
│   │   ├── testing.md
│   │   ├── security.md
│   │   ├── performance.md
│   │   ├── coding-style.md
│   │   └── hooks.md
│   ├── typescript/
│   ├── java/
│   ├── rust/
│   ├── [14 more languages]
│   └── README.md
│
├── hooks/                     # Git hooks & automation
│   ├── pre-commit
│   ├── post-merge
│   └── ...
│
├── .claude/                   # Claude Code specific
│   ├── rules/
│   ├── skills/
│   ├── agents/
│   └── ...
│
├── .cursor/                   # Cursor IDE specific
│   ├── rules/
│   ├── skills/
│   ├── agents/
│   └── ...
│
├── .codex/                    # Codex specific
├── .gemini/                   # Gemini specific
├── mcp-configs/               # Model Context Protocol
│
├── commands/                  # Legacy command shims (72)
│   ├── agent-sort.sh
│   ├── build-fix.sh
│   └── [70 more commands]
│
├── scripts/                   # Utility scripts
│   ├── install-plan.js        # Manifest-driven install
│   ├── install-apply.js       # Apply installation
│   └── ...
│
├── ecc2/                      # ECC 2.0 Rust control plane (alpha)
│   ├── src/
│   ├── dashboard/             # Python dashboard UI
│   └── ...
│
├── examples/                  # Usage examples
├── contexts/                  # ECC context definitions
├── manifests/                 # Plugin manifests
├── schemas/                   # JSON schemas
│
├── agent.yaml                 # Main agent configuration
├── AGENTS.md                  # Agent reference
├── RULES.md                   # Rules reference
├── the-shortform-guide.md    # Quick start
├── the-longform-guide.md     # Deep dive
├── the-security-guide.md     # Security guidelines
├── EVALUATION.md              # Testing/evaluation
├── WORKING-CONTEXT.md         # Development context
└── ecc_dashboard.py           # Desktop dashboard (Tkinter)
```

---

## Agent System

### 48 Specialized Agents

Agents are defined in `agents/` as Markdown files with frontmatter:

```markdown
---
name: code-reviewer
description: Review code for quality and best practices
tags: [quality, review, continuous-improvement]
requires_tools: [read_file, write_file, web_search]
model_preference: claude-opus-4-6
---

# Code Review Agent

You are a senior code reviewer...

## Review Checklist
- [ ] Code follows style guidelines
- [ ] No code duplication
- [ ] Error handling present
- [ ] Tests included
- [ ] Performance acceptable
```

#### Agent Categories

**1. Core Workflow Agents**
- `planner` - Implementation planning
- `architect` - System design
- `tdd-guide` - Test-driven development
- `code-reviewer` - Code quality
- `security-reviewer` - Vulnerability detection
- `build-error-resolver` - Fix compilation errors

**2. Language-Specific Agents (10+ languages)**
- `python-reviewer`, `python-build-resolver`
- `java-reviewer`, `java-build-resolver`
- `typescript-reviewer`, `typescript-build-resolver`
- `rust-reviewer`, `rust-build-resolver`
- `cpp-reviewer`, `cpp-build-resolver`
- `go-reviewer`, `go-build-resolver`
- `kotlin-reviewer`, `kotlin-build-resolver`
- `php-reviewer`, `php-build-resolver`
- `dart-reviewer`, `dart-build-resolver`
- `csharp-reviewer`, `csharp-build-resolver`

**3. Domain-Specific Agents**
- `database-reviewer` - PostgreSQL/Supabase optimization
- `e2e-runner` - Playwright test execution
- `api-design` - REST API design patterns
- `healthcare-reviewer` - HIPAA/PHI compliance

**4. Framework Agents**
- `flutter-reviewer` - Flutter/Dart specific
- `springboot-reviewer` - Spring Boot patterns
- `django-reviewer` - Django patterns
- `nextjs-reviewer` - Next.js patterns

**5. Operator Agents**
- `loop-operator` - Autonomous loop control, monitoring, stall detection
- `harness-optimizer` - Config tuning for cost/reliability/throughput

**6. Specialized Agents**
- `chief-of-staff` - Multi-agent orchestration
- `architect` - Full system design
- `refactor-cleaner` - Dead code removal
- `doc-updater` - Documentation updates
- `conversation-analyzer` - Extract insights from conversations

#### Agent Routing (From AGENTS.md)

```
request → [agent decision logic]
    ├─ "Plan the feature" → planner
    ├─ "Design the system" → architect
    ├─ "Review this code" → code-reviewer
    ├─ "Why is build failing?" → build-error-resolver
    ├─ "Security audit" → security-reviewer
    ├─ "Any async patterns?" → [lang]-reviewer
    ├─ "Run tests" → e2e-runner
    ├─ "Check for dead code" → refactor-cleaner
    └─ "Manage autonomous loop" → loop-operator
```

---

## Skills System

### 156+ Skills (Markdown-Based Knowledge)

Skills are **versioned knowledge packets** that agents can inject into their context. Each skill is a Markdown file in `skills/` describing patterns, best practices, or guidelines.

#### Skill File Structure

```markdown
# Skill: API Design

## Overview
RESTful API design guidelines for production systems.

## Key Principles
- Resource-oriented (nouns, not verbs)
- Standard HTTP methods (GET, POST, PUT, DELETE)
- Proper status codes (200, 201, 400, 404, 500)
- Consistent error responses

## Implementation Pattern
```python
# Example: FastAPI endpoint
@app.post("/api/users")
def create_user(user: UserCreate) -> User:
    """Create a new user."""
    # Validation
    if not user.email:
        raise HTTPException(400, "Email required")
    
    # Creation
    db_user = User(**user.dict())
    db.add(db_user)
    db.commit()
    
    return db_user
```

## Common Mistakes
1. Mixing verbs with nouns (/api/getUser - wrong)
2. Missing error handling
3. No input validation

## Related Skills
- database-design
- security-review
- testing-strategies
```

#### Skill Categories

| Category | Count | Examples |
|----------|-------|----------|
| **Language Patterns** | 40+ | Python, Java, TypeScript, Rust, Go, etc. |
| **Framework Patterns** | 35+ | Django, Spring Boot, Next.js, Flutter, etc. |
| **Architecture** | 15+ | Microservices, event-driven, DDD, etc. |
| **Testing** | 12+ | Unit, integration, E2E, mocking, etc. |
| **Security** | 10+ | Auth, encryption, SQL injection, XSS, etc. |
| **Performance** | 8+ | Caching, async, optimization, etc. |
| **DevOps** | 6+ | Docker, CI/CD, monitoring, etc. |
| **Domain Specific** | 18+ | Healthcare, Finance, E-commerce, etc. |

#### Skill Injection

Skills are automatically injected into agent context when relevant:

```python
# Agent pseudo-code
if "Python" in request:
    skills = load_skills(["python-patterns", "python-testing"])
    context.append(skills)

if "REST API" in request:
    context.append(load_skills(["api-design"]))

if domain == "healthcare":
    context.append(load_skills(["healthcare-compliance"]))
```

### Continuous Learning

ECC evolves skills through:

1. **Session Recording** - Capture all agent interactions
2. **Pattern Extraction** - Find successful patterns
3. **Skill Evolution** - Update skill files with new patterns
4. **Version Control** - Track skill changes over time

```
Session → Successful pattern detected
    ↓
Extract pattern from conversation
    ↓
Add to skill file
    ↓
Version and commit
    ↓
Next agent uses updated skill
```

---

## Rules System

### Language-Specific Rules (17 Languages)

Each language has rules covering:
- **patterns.md** - Design patterns and idioms
- **coding-style.md** - Style conventions
- **testing.md** - Testing strategies
- **security.md** - Language-specific vulnerabilities
- **performance.md** - Optimization techniques
- **hooks.md** - Pre-commit hooks and automation

#### Example: Python Rules

```markdown
# Python Rules

## Patterns

### Error Handling
Always use custom exceptions:
```python
class ValidationError(Exception):
    """Raised when validation fails."""
    pass

try:
    validate_input(data)
except ValidationError as e:
    logger.error(f"Validation failed: {e}")
    raise
```

## Coding Style

- Use type hints: `def func(x: int) -> str:`
- Docstrings on all public functions
- 4-space indentation
- Line length: 88 characters (Black formatter)

## Testing

- 80%+ coverage minimum
- Unit tests in `tests/unit_tests/`
- Integration tests in `tests/integration_tests/`
- Use pytest fixtures for setup

## Security

- Never use `eval()` or `exec()`
- SQL: Use parameterized queries (SQLAlchemy ORM)
- Validate all input at system boundaries
- No hardcoded secrets
```

---

## Configuration System

### `agent.yaml` - Main Configuration

```yaml
spec_version: "0.1.0"
name: everything-claude-code
version: 1.10.0
description: "Complete AI coding system"
author: affaan-m
license: MIT

model:
  preferred: claude-opus-4-6
  fallback:
    - claude-sonnet-4-6
    - claude-haiku-4-6

skills:
  - agent-eval
  - api-design
  - architecture-decision-records
  - python-patterns
  - java-patterns
  - typescript-patterns
  - rust-patterns
  - golang-patterns
  - [150+ more skills]

agents:
  - architect
  - planner
  - code-reviewer
  - tdd-guide
  - security-reviewer
  - [44 more agents]

rules:
  - python
  - typescript
  - java
  - rust
  - golang
  - [12 more languages]

hooks:
  - pre-commit
  - post-merge
  - pre-push

commands:
  - agent-sort
  - build-fix
  - checkpoint
  - [69 more commands]
```

### Per-Harness Configuration

Each AI harness (Claude Code, Cursor, etc.) has its own `.{harness}/` directory:

```
.claude/           # Claude Code specific
.cursor/           # Cursor IDE specific
.codex/            # Codex specific
.gemini/           # Gemini specific
.opencode/         # OpenCode specific
```

Each contains customized:
- `rules/` - Harness-specific rules
- `skills/` - Harness-optimized skills
- `agents/` - Harness-specific agents
- `hooks/` - Harness integration hooks

---

## Hook System

### Git Hooks Automation

Hooks trigger automated checks and improvements:

```bash
# pre-commit hook
↓
│
├─ Run linter (ruff, eslint, etc.)
├─ Run tests
├─ Check security (bandit, etc.)
├─ Check coverage (≥80%)
├─ Run formatter
├─ Type check
└─ Commit if all pass

# post-merge hook
↓
│
├─ Update dependencies
├─ Run integration tests
├─ Check documentation
└─ Alert on schema changes

# pre-push hook
↓
│
├─ Run full test suite
├─ Security audit
├─ Performance regression check
└─ Only push if all pass
```

---

## Command System

### 72 Legacy Command Shims

Commands are shell scripts that delegate to agents:

```bash
# Commands are wrappers around agents
$ agent-sort                    # → planner agent
$ build-fix                     # → build-error-resolver agent
$ security-audit                # → security-reviewer agent
$ test-all                       # → e2e-runner agent
$ refactor-cleanup               # → refactor-cleaner agent
```

Benefits:
- Familiar shell interface
- Backward compatibility
- Quick invocation
- Scriptable

---

## ECC 2.0 (Alpha - Rust Control Plane)

Next-generation ECC with Rust-based control plane:

### Features

```bash
ecc2 dashboard          # Desktop GUI (Tkinter + Python)
ecc2 start [project]   # Initialize session
ecc2 sessions          # List active sessions
ecc2 status            # Check system status
ecc2 stop [session]    # Terminate session
ecc2 resume [id]       # Resume interrupted session
ecc2 daemon            # Run background daemon
```

### Architecture

```
Rust Control Plane
├─ Session management
├─ Resource pooling
├─ Cost optimization
├─ Parallel agent execution
└─ State persistence
        ↓
Python Dashboard (Tkinter)
├─ Dark/light theme
├─ Font customization
├─ Project logo display
├─ Real-time updates
└─ Session browser
```

---

## Testing & Evaluation

### Verification Loops (From EVALUATION.md)

**4 Testing Layers:**

1. **Layer 1 - TestContainers**
   - Spin up real services (Postgres, Redis, etc.)
   - Unit test with actual dependencies
   - Minimal setup overhead

2. **Layer 2 - Smoke Tests**
   - Critical paths only
   - Fast feedback (< 5 minutes)
   - Catch major regressions

3. **Layer 3 - Azure Integration Tests**
   - Full stack integration
   - Production-like environment
   - Slow but comprehensive (< 30 minutes)

4. **Layer 4 - Behavioral Comparison**
   - Pre-migration vs post-migration
   - Functional equivalence verification
   - Golden reference comparison

### Evaluation Strategy

```
Feature Complete
    ↓
Layer 1: Unit + Containers pass
    ↓
Layer 2: Smoke tests pass
    ↓
Layer 3: Integration tests pass
    ↓
Layer 4: Behavioral equivalence verified
    ↓
Safe to Release
```

---

## Security Guidelines

### Before ANY Commit

- ✅ No hardcoded secrets
- ✅ All inputs validated
- ✅ SQL injection prevention (parameterized queries)
- ✅ XSS prevention (sanitized HTML)
- ✅ CSRF protection enabled
- ✅ Auth/authorization verified
- ✅ Rate limiting on endpoints
- ✅ Error messages don't leak sensitive data

### Security Checklist

```python
# GOOD
password = os.environ.get("DB_PASSWORD")
if not password:
    raise RuntimeError("DB_PASSWORD not set")

# BAD
password = "hardcoded_password_123"  # ❌ NEVER

# GOOD - Parameterized query
user = db.query("SELECT * FROM users WHERE id = ?", (user_id,))

# BAD - String concatenation
user = db.query(f"SELECT * FROM users WHERE id = {user_id}")  # ❌ SQL injection
```

### Agent Response

If security issue found:
1. **STOP** - Don't proceed
2. **security-reviewer** - Run specialized agent
3. **Fix CRITICAL issues** - Highest priority
4. **Rotate exposed secrets** - Immediately
5. **Codebase audit** - Look for similar issues

---

## Development Workflow (ECC-Recommended)

### Feature Development

```
Feature Request
    ↓
1. planner → Create detailed plan
    ↓
2. tdd-guide → Write test cases first
    ↓
3. Code implementation (80%+ coverage)
    ↓
4. code-reviewer → Quality audit
    ↓
5. security-reviewer → Vulnerability scan
    ↓
6. e2e-runner → End-to-end testing
    ↓
7. doc-updater → Update documentation
    ↓
Feature Complete
```

### Agent Parallelization

Independent operations can run in parallel:

```
Feature → planner
       ├─→ code-reviewer (on existing code)
       ├─→ security-reviewer (on new code)
       ├─→ database-reviewer (on schema)
       └─→ api-design (if REST endpoints)

# Wait for all, then merge results
```

---

## Coding Style Requirements

### Immutability (CRITICAL)

```python
# GOOD - Always create new objects
def add_item(items: list[str], new_item: str) -> list[str]:
    return items + [new_item]  # New list

# BAD - Mutating
def add_item(items: list[str], new_item: str):
    items.append(new_item)  # Modifies original
    return items
```

### File Organization

- Small files (200-400 lines typical)
- Maximum 800 lines per file
- Organize by feature/domain, not by type
- High cohesion, low coupling

### Naming

- Descriptive variable names
- Self-documenting code
- Prefer single-word names when possible
- Functions < 50 lines

### Error Handling

- Handle errors at every level
- User-friendly messages in UI
- Detailed logging server-side
- Never silently swallow errors

### Input Validation

- Validate all user input at boundaries
- Use schema-based validation
- Fail fast with clear messages
- Never trust external data

---

## Integration Recommendations for Your Coding Agent

✅ **From ECC, definitely adopt:**
- Agent-first architecture (specialized agents)
- Markdown-based skills system for knowledge injection
- Per-language rule system
- Security-first checklist approach
- Immutability principle
- Test-driven development enforcement (80%+ coverage)
- Multi-agent orchestration patterns
- Hook-based automation
- Continuous learning from sessions
- LLM model routing/fallback

✅ **Beneficial patterns:**
- Agent routing logic (request → which agent)
- Skills as versioned knowledge packets
- Language-specific agent variants
- Security-reviewer agent pattern
- Loop-operator pattern for autonomous execution
- ECC 2.0 control plane architecture (for future)

❌ **Not necessary to copy:**
- 48 specific agents (build your own domain agents)
- 156+ specific skills (create domain-specific ones)
- 72 legacy command shims (unless needed for compatibility)
- Specific language rules (adapt for your use case)

---

## Key Takeaways

1. **Agent-First System** - Agents delegate to specialist agents
2. **Markdown Skills** - Encapsulated, versioned knowledge
3. **Language Ecosystem** - Support 10+ languages with specialized rules
4. **Security-First** - Checklist before every commit
5. **Test-Driven** - 80%+ coverage mandatory
6. **Immutability** - Core principle (never mutate)
7. **Continuous Learning** - Evolve from successful sessions
8. **Multi-Harness Support** - Work with multiple AI platforms

---

## File Reference

| File | Purpose |
|------|---------|
| `agents/` | 48 agent definitions |
| `skills/` | 156+ knowledge packets |
| `rules/` | Language-specific rules |
| `hooks/` | Git automation |
| `commands/` | 72 CLI wrappers |
| `agent.yaml` | Master configuration |
| `AGENTS.md` | Agent reference |
| `RULES.md` | Rules reference |
| `.claude/`, `.cursor/`, etc. | Harness-specific configs |
| `ecc2/` | Next-gen control plane (alpha) |
| `ecc_dashboard.py` | Desktop UI |
