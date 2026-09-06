# Arcon Enhanced: Framework Contribution Map
**Quick Reference Guide - Which Framework Provides What**

**Date:** April 26, 2026  
**Version:** v0.3.0 Planning  
**Status:** Ready for Implementation

---

## 📊 Quick Reference: Framework → Arcon Feature Mapping

```
ARCON v0.3.0 ENHANCED FEATURES
│
├─ Phase 1: FOUNDATION (Weeks 1-4) ─────────────────────────────────────
│  │
│  ├─ 🟦 MIDDLEWARE PIPELINE [from Deep Agents + Onyx]
│  │  └─ Purpose: Extensible processing hooks (input → tool call → output)
│  │  └─ Source: Deep Agents middleware stack
│  │  └─ Additional: Tool call validation (Copilot SDK pattern)
│  │  └─ Token Savings: 5% (overhead reduction)
│  │
│  ├─ 🟦 PERMISSION SYSTEM [from Copilot SDK]
│  │  └─ Purpose: User-controlled tool access (allow/deny/ask)
│  │  └─ Source: Copilot SDK ElicitationHandler
│  │  └─ Storage: SQLite + CLI commands
│  │  └─ Token Savings: 5% (fail-fast on denied operations)
│  │
│  └─ 🟦 COST TRACKING [from OpenClaude]
│     └─ Purpose: Per-session, daily, monthly cost tracking
│     └─ Source: OpenClaude cost-tracker.ts
│     └─ Model-aware: Claude, GPT-4o, etc. pricing
│     └─ Token Savings: 5% (cheaper model selection)
│     └─ Total Phase 1: 15-20% reduction
│
├─ Phase 2: INTELLIGENCE (Weeks 5-8) ───────────────────────────────────
│  │
│  ├─ 🟩 TECH AUTO-DETECTION [from autoskills]
│  │  └─ Purpose: Scan project → detect technologies
│  │  └─ Source: autoskills ProjectScanner
│  │  └─ Detects: TypeScript, React, FastAPI, Django, Postgres, etc.
│  │  └─ Token Savings: 8% (relevant skills only)
│  │
│  ├─ 🟩 SKILL INJECTION [from ECC + autoskills]
│  │  └─ Purpose: Auto-load relevant skills from 150+ available
│  │  └─ Source: ECC skill organization + autoskills resolver
│  │  └─ Pattern: Technology combo → special skills (React+TS→NextJS)
│  │  └─ Token Savings: 7% (less noise in context)
│  │
│  ├─ 🟩 ENHANCED AGENT ROUTING [from ECC + Copilot SDK]
│  │  └─ Purpose: Smart multi-factor agent selection
│  │  └─ Source: ECC agent specialization + Copilot routing
│  │  └─ Factors: explicit name, file pattern, keywords, tech preference
│  │  └─ Token Savings: 5% (right agent first try)
│  │
│  └─ 🟩 TOOL CALL MERGING [from Onyx]
│     └─ Purpose: Merge similar tool calls (3 calls → 1)
│     └─ Source: Onyx tool_runner.py merge algorithm
│     └─ Example: 3 search queries merged into 1
│     └─ Token Savings: 10-15% (fewer LLM messages)
│     └─ Total Phase 2: +15-20% (35% cumulative)
│
├─ Phase 3: KNOWLEDGE (Weeks 9-12) ─────────────────────────────────────
│  │
│  ├─ 🟨 KNOWLEDGE GRAPH [from Onyx]
│  │  └─ Purpose: Entity extraction + relationship mapping
│  │  └─ Source: Onyx KG builder + entity extraction
│  │  └─ Builds: Classes, functions, imports, relationships
│  │  └─ Uses: For context filtering (only include relevant code)
│  │  └─ Token Savings: 8-49x (blast radius reduction)
│  │
│  ├─ 🟨 SEMANTIC COMPRESSION [from Onyx + caveman]
│  │  └─ Purpose: Compress context using KG + linguistic tricks
│  │  └─ Source: Onyx COMPRESSION.md + caveman linguistic compression
│  │  └─ Strategy: Remove non-essential words, keep meaning
│  │  └─ Token Savings: 40% on compressible text
│  │
│  ├─ 🟨 DEEP RESEARCH [from Onyx]
│  │  └─ Purpose: Multi-step reasoning for complex problems
│  │  └─ Source: Onyx deep_research module
│  │  └─ Process: Break query → research steps → synthesize
│  │  └─ Token Savings: 20% (more efficient reasoning)
│  │
│  └─ 🟨 EXECUTION BACKENDS [from Deep Agents]
│     └─ Purpose: Multiple execution environments (local, sandbox, custom)
│     └─ Source: Deep Agents backends/ module
│     └─ Enables: Safe code execution, isolated testing
│     └─ Token Savings: 5% (operational efficiency)
│     └─ Total Phase 3: +40-50% (75-80% cumulative)
│
└─ Phase 4: PRODUCTION (Weeks 13-16) ──────────────────────────────────
   │
   ├─ 🟪 MCP SERVER [from Onyx + Copilot SDK]
   │  └─ Purpose: Standard Model Context Protocol interface
   │  └─ Source: Onyx MCP server + FastMCP integration
   │  └─ Enables: Use Arcon as tool in Claude, other agents
   │  └─ Tools: search_codebase, generate_code, review_code, run_tests
   │  └─ Token Savings: 3% (external callers = shared context)
   │
   ├─ 🟪 OBSERVABILITY [from Onyx + OpenClaude]
   │  └─ Purpose: Tracing, metrics, logging
   │  └─ Source: Onyx tracing module + OpenClaude observability
   │  └─ Tracks: Token usage, latency, errors, tool calls
   │  └─ Token Savings: 2% (identify/remove inefficiencies)
   │
   └─ 🟪 PROFILE SYSTEM [from Deep Agents + OpenClaude]
      └─ Purpose: Model-specific configurations
      └─ Source: Deep Agents profiles/ + OpenClaude provider logic
      └─ Configs: Prompt format, token limits, model personality
      └─ Token Savings: 5% (optimized per model)
      └─ Total Phase 4: +10% (85-90% cumulative)

FINAL: 70-98% TOKEN REDUCTION (from baseline)
```

---

## 🎯 Feature-by-Framework Breakdown

### Onyx (Full AI Platform) → 5 Key Features

| Feature | Source Module | Arcon Integration | Phase | Impact |
|---------|---------------|------------------|-------|--------|
| **MCP Server** | `mcp_server/` | FastMCP wrapper | P4 | Extensibility |
| **Knowledge Graph** | `kg/` | Entity extraction | P3 | 8-49x reduction |
| **Tool Merging** | `tool_runner.py` | Batch execution | P2 | 10-15% reduction |
| **Deep Research** | `deep_research/` | Multi-step reasoning | P3 | 20% reduction |
| **Compression** | `chat/compression.py` | Context optimization | P3 | 40% reduction |

**Onyx Contribution:** 40% of total token reduction  
**Critical for:** Achieving 70-98% savings goal

---

### Copilot SDK (Session Management) → 3 Key Features

| Feature | Source Module | Arcon Integration | Phase | Impact |
|---------|---------------|------------------|-------|--------|
| **Permission System** | `session.py` | Allow/deny/ask model | P1 | Security + UX |
| **Session Architecture** | `client.py` | Session lifecycle | P1 | Foundation |
| **Tool Definition** | `tools.py` | Decorator-based tools | P2 | Developer UX |

**Copilot Contribution:** Foundation + 15% of total reduction  
**Critical for:** Permission model, extensibility

---

### Deep Agents (Elegant Architecture) → 3 Key Features

| Feature | Source Module | Arcon Integration | Phase | Impact |
|---------|---------------|------------------|-------|--------|
| **Middleware Pipeline** | `middleware/` | Processing hooks | P1 | Extensibility |
| **Execution Backends** | `backends/` | Multi-environment support | P3 | Flexibility |
| **Profile System** | `profiles/` | Model-specific configs | P4 | Optimization |

**Deep Agents Contribution:** Architecture pattern + 5% of total reduction  
**Critical for:** Extensibility without code changes

---

### ECC (Scale & Specialization) → 2 Key Features

| Feature | Source Module | Arcon Integration | Phase | Impact |
|---------|---------------|------------------|-------|--------|
| **Agent Specialization** | `agents/` (48 agents) | Expand 5→10 agents | P2 | Quality |
| **Skill Organization** | `skills/` (156+ skills) | Tech-based skills | P2 | 8% reduction |

**ECC Contribution:** Blueprint for 150+ skill system + 8% of total reduction  
**Critical for:** Scaling agents from 5→10+, skill coverage

---

### OpenClaude (Provider Agnosticism) → 2 Key Features

| Feature | Source Module | Arcon Integration | Phase | Impact |
|---------|---------------|------------------|-------|--------|
| **Cost Tracking** | `services/cost-tracker.ts` | Per-session tracking | P1 | 5% reduction |
| **Provider Abstraction** | `QueryEngine.ts` | Multi-provider support | P2 | Flexibility |

**OpenClaude Contribution:** Cost awareness pattern + 5% of total reduction  
**Critical for:** User-facing cost control

---

### autoskills (Auto-Detection) → 1 Key Feature

| Feature | Source Module | Arcon Integration | Phase | Impact |
|---------|---------------|------------------|-------|--------|
| **Tech Auto-Detection** | Root scanner logic | ProjectScanner | P2 | 8% reduction |

**autoskills Contribution:** Zero-config detection + 8% of total reduction  
**Critical for:** User friction reduction

---

## 📈 Token Savings Mechanism Breakdown

```
Starting Baseline: $200/month (500 interactions at current efficiency)

Phase 1: FOUNDATION (+15-20%)
├─ Middleware overhead reduction: 5%
├─ Permission-based fail-fast: 5%
├─ Cost-aware model selection: 5%
└─ Subtotal: $150/month (-25%)

Phase 2: INTELLIGENCE (+15-20%)
├─ Tech auto-detection (skill filtering): 8%
├─ Smart agent routing: 5%
├─ Tool call merging: 10-15%
└─ Subtotal: $100/month (-50% cumulative)

Phase 3: KNOWLEDGE (+40-50%)
├─ Knowledge graph (blast radius): 8-49x!
├─ Semantic compression: 40%
├─ Deep research efficiency: 20%
├─ Execution optimization: 5%
└─ Subtotal: $25-60/month (-75% cumulative)

Phase 4: PRODUCTION (+10%)
├─ MCP integration efficiency: 3%
├─ Observability-based tuning: 2%
├─ Profile optimization: 5%
└─ Subtotal: $10-50/month (-97.5% cumulative)

TOTAL REDUCTION: 70-98%
```

---

## 🔄 Implementation Order (Why Each Depends on Previous)

```
P1.1: Middleware Pipeline (foundation)
  ↓
P1.2: Permission System (uses middleware)
  ↓
P1.3: Cost Tracking (tracks all calls)
  ↓
P2.1: Tech Auto-Detection (independent, no deps)
  ↓
P2.2: Skill Injection Middleware (needs P1.1 + P2.1)
  ↓
P2.3: Agent Routing (uses skill context)
  ↓
P2.4: Tool Merging (independent)
  ↓
P3.1: Knowledge Graph (independent)
  ↓
P3.2: Semantic Compression (uses KG from P3.1)
  ↓
P3.3: Deep Research (uses agents + tools)
  ↓
P3.4: Execution Backends (independent)
  ↓
P4.1: MCP Server (all previous components)
  ↓
P4.2: Observability (all previous components)
  ↓
P4.3: Profile System (all previous components)
```

---

## 📚 Code Reference Mapping

For each Arcon component, where to look in source frameworks:

### Middleware & Permissions
- **Architecture:** `deepagents/libs/deepagents/middleware/`
- **Permission Model:** `copilot-sdk/python/copilot_sdk/session.py`
- **Validation:** `onyx/tools/interface.py`

### Cost Tracking & Routing
- **Cost Calculation:** `openclaude/src/services/cost-tracker.ts`
- **Agent Router:** `everything-claude-code/agents/` (48 agent examples)
- **Tool Calling:** `onyx/tools/tool_runner.py`

### Auto-Detection & Skills
- **Tech Detection:** `autoskills/README.md` (algorithm description)
- **Skill System:** `everything-claude-code/skills/` (156+ examples)
- **Combo Skills:** `everything-claude-code/EVERYTHING_CLAUDE_CODE_ARCHITECTURE.md`

### Knowledge Graphs & Compression
- **KG Building:** `onyx/kg/extractions/` + `onyx/kg/clustering/`
- **Compression:** `onyx/chat/compression.py`
- **Linguistic:** (caveman repo - conceptual only)

### MCP & Backends
- **MCP Server:** `onyx/mcp_server/api.py`
- **Backends:** `deepagents/libs/deepagents/backends/`
- **Profiles:** `deepagents/libs/deepagents/profiles/`

---

## ✅ Validation Checklist

Before starting each phase, verify:

### Pre-Phase 1
- [ ] Middleware API finalized
- [ ] Permission states documented
- [ ] Cost calculation formulas validated
- [ ] Tests written (TDD)

### Pre-Phase 2
- [ ] Tech scanner works on 5+ projects
- [ ] Skill mappings comprehensive
- [ ] Agent routing tested on 20+ queries
- [ ] Tool merging algorithm proven

### Pre-Phase 3
- [ ] KG extracts 90%+ of entities
- [ ] Compression validates 95%+ accuracy
- [ ] Deep research produces coherent results
- [ ] Backend execution is sandboxed

### Pre-Phase 4
- [ ] MCP server passes OpenAI compatibility
- [ ] Observability tracks all key metrics
- [ ] Profiles optimize for 3+ model types
- [ ] Documentation complete

---

## 🚀 Quick Start: Framework Learning Path

**If you have 1 hour:**
- Read: This document + ARCON_STRATEGIC_ANALYSIS.md

**If you have 4 hours:**
- Read: ARCON_ENHANCED_PLAN_v0.3.md Phase 1
- Skim: Copilot SDK `session.py` + Deep Agents `middleware/`

**If you have 1 day:**
- Read: All planning documents
- Code review: Onyx `tool_runner.py` + `mcp_server/`
- Code review: Deep Agents middleware examples

**If you have 1 week:**
- In-depth study of each framework
- Create prototype middleware implementation
- Design permission schema
- Plan cost tracking database

---

## 💡 Key Insights from Each Framework

### Onyx
> "Use knowledge graphs to understand code relationships, enabling 8-49x reduction in context size."

### Copilot SDK
> "Permission system should be three states (allow/deny/ask), not complex RBAC."

### Deep Agents
> "Middleware is the most extensible pattern - not hooks, not inheritance, just middleware."

### ECC
> "Scale through specialization - 48 agents each good at one thing beats 1 agent doing everything."

### OpenClaude
> "Provider abstraction enables cost-aware model selection - cheaper models for simple queries."

### autoskills
> "Zero-config is achievable - dual-signal detection (files + imports) catches 95% of tech stacks."

---

## 🎓 Learning Objectives by Phase

### Phase 1 Learnings
- [ ] How middleware architecture enables extensibility
- [ ] Permission model best practices
- [ ] Cost calculation and tracking for multiple providers

### Phase 2 Learnings
- [ ] Tech stack detection patterns
- [ ] Skill organization at scale
- [ ] Agent specialization benefits
- [ ] Tool call merging algorithms

### Phase 3 Learnings
- [ ] Knowledge graph construction and traversal
- [ ] Semantic compression techniques
- [ ] Multi-step reasoning workflows
- [ ] Context optimization strategies

### Phase 4 Learnings
- [ ] MCP protocol and integration
- [ ] Execution backend abstraction
- [ ] Observability and metrics collection
- [ ] Model-specific optimization

---

## 📞 Framework Contact Points

If implementation hits questions:

- **Onyx questions:** Check `onyx/` folder in perceptron, MIT licensed, active community
- **Copilot SDK questions:** Check copilot-sdk docs, Python SDK is reference implementation
- **Deep Agents questions:** LangGraph integration, check `deepagents/libs/` examples
- **ECC questions:** 140K+ stars, check AGENTS.md and agents/ folder
- **OpenClaude questions:** Terminal-based, check src/main.tsx for CLI patterns
- **autoskills questions:** Zero-config philosophy, check README.md for algorithm

---

## 🎯 Success Looks Like

**At end of Phase 1:**
- Arcon v0.2.0 with middleware, permissions, cost tracking
- 15-20% token reduction proven
- All tests passing, no security issues

**At end of Phase 2:**
- Arcon v0.3.0 with auto-detection, smart routing, tool merging
- 35-40% cumulative token reduction
- Users report "just works" experience

**At end of Phase 3:**
- Arcon v0.4.0 with knowledge graphs, compression, research
- 75-80% cumulative token reduction
- Cost savings documented ($100→$25/month range)

**At end of Phase 4:**
- Arcon v0.5.0 production-ready platform
- 85-90% cumulative token reduction
- MCP integration enables use as Claude tool

**Target: 70-98% reduction, $10-50/month for heavy users**

