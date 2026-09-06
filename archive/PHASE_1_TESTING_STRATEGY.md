# Phase 1 Testing Strategy for Arcon v0.1.0 Enhancement

**Purpose:** Comprehensive testing plan for Phase 1 enhancements (Middleware, Permissions, Cost Tracking)  
**Scope:** Unit tests, integration tests, CLI tests for Phase 1 features  
**Target Coverage:** >85% for all Phase 1 code

---

## Phase 1 Implementation Overview

### Phase 1.1: Middleware Pipeline Architecture
- **Location:** `src/arcon/middleware/`
- **Components:** Base middleware, middleware pipeline, hooks system
- **Files:** `base.py`, `pipeline.py`, `hooks.py`

### Phase 1.2: Permission System (3-state model)
- **Location:** `src/arcon/permissions/`
- **Components:** Permission engine, state machine, decision logic
- **Files:** `engine.py`, `models.py`, `prompter.py`

### Phase 1.3: Cost Tracking Framework
- **Location:** `src/arcon/cost/`
- **Components:** Cost calculator, budget manager, token counter
- **Files:** `calculator.py`, `budget.py`, `tracker.py`

---

## Test File Structure

```
tests/
├── test_middleware.py          (NEW - 30-40 tests)
├── test_permissions.py          (NEW - 25-35 tests)
├── test_cost_tracking.py        (NEW - 20-30 tests)
├── integration/
│   └── test_phase1_features.py  (NEW - 15-25 tests)
├── cli/
│   └── test_cli_commands.py     (NEW - 20-30 tests)
└── [existing test files]
```

---

## 1. Middleware System Tests

### 1.1 Base Middleware Class Tests (5-6 tests)

**File:** `tests/test_middleware.py::TestMiddlewareBase`

**Tests:**

```python
def test_middleware_creation():
    """Test basic middleware instantiation."""
    # Create a simple middleware instance
    # Verify name, description, enabled flag
    
def test_middleware_metadata():
    """Test middleware metadata attributes."""
    # Verify all required metadata fields present
    # Check metadata serialization
    
def test_middleware_hooks_interface():
    """Test middleware hook interface."""
    # Verify input_hook, tool_call_hook, output_hook methods exist
    # Check method signatures
    
def test_custom_middleware_creation():
    """Test creating custom middleware subclass."""
    # Extend Middleware base class
    # Override specific hooks
    # Verify inheritance and method override
    
def test_middleware_error_handling():
    """Test error handling in middleware."""
    # Verify exceptions propagate correctly
    # Check error context preservation
    
def test_middleware_context_passing():
    """Test context passing through middleware."""
    # Verify context dict available in hooks
    # Check context mutation and preservation
```

### 1.2 Middleware Pipeline Tests (10-12 tests)

**File:** `tests/test_middleware.py::TestMiddlewarePipeline`

**Tests:**

```python
def test_pipeline_creation_empty():
    """Test creating empty pipeline."""
    # Verify empty pipeline initializes
    # Check pipeline statistics
    
def test_pipeline_register_middleware():
    """Test registering middleware in pipeline."""
    # Register single middleware
    # Register multiple middleware
    # Verify registration order
    
def test_pipeline_duplicate_middleware():
    """Test handling duplicate middleware names."""
    # Try to register same middleware twice
    # Verify error handling
    # Test override flag
    
def test_pipeline_execute_hooks():
    """Test executing pipeline hooks."""
    # Create pipeline with 2-3 middleware
    # Execute input_hook through all middleware
    # Verify hook execution order
    
def test_pipeline_hook_modifications():
    """Test middleware modifying data in pipeline."""
    # First middleware adds field to context
    # Second middleware modifies field
    # Verify modifications cascade
    
def test_pipeline_hook_abort():
    """Test middleware aborting pipeline execution."""
    # Middleware returns abort signal
    # Verify subsequent middleware skipped
    # Verify abort reason preserved
    
def test_pipeline_error_in_middleware():
    """Test error in one middleware."""
    # Second middleware throws exception
    # Verify exception contains middleware info
    # Check error recovery options
    
def test_pipeline_disabled_middleware():
    """Test disabled middleware skipped."""
    # Register middleware with enabled=False
    # Execute pipeline
    # Verify disabled middleware not called
    
def test_pipeline_middleware_timeout():
    """Test middleware execution timeout."""
    # Middleware takes too long
    # Verify timeout enforcement
    # Check timeout error handling
    
def test_pipeline_parallel_execution():
    """Test middleware supporting parallel execution."""
    # Execute multiple hooks in parallel
    # Verify thread safety
    
def test_pipeline_statistics():
    """Test pipeline execution statistics."""
    # Track middleware execution times
    # Track hook execution counts
    # Verify statistics accuracy
    
def test_pipeline_clear():
    """Test clearing middleware pipeline."""
    # Register middleware
    # Clear pipeline
    # Verify empty after clear
```

### 1.3 Hook Integration Tests (8-10 tests)

**File:** `tests/test_middleware.py::TestHookIntegration`

**Tests:**

```python
def test_input_hook_modification():
    """Test input hook modifying query."""
    # Middleware adds prefix to user query
    # Verify modification in downstream
    
def test_tool_call_hook_filtering():
    """Test tool call hook filtering tools."""
    # Middleware filters specific tools
    # Verify filtered tools not available
    
def test_output_hook_formatting():
    """Test output hook formatting response."""
    # Middleware wraps response in formatted box
    # Verify formatting applied
    
def test_hook_error_recovery():
    """Test error recovery in hooks."""
    # Hook throws recoverable error
    # Handler catches and continues
    # Verify fallback applied
    
def test_hook_cancellation():
    """Test hook cancellation mechanism."""
    # Middleware signals cancellation
    # Verify operation cancelled
    
def test_hook_context_isolation():
    """Test context isolation between hooks."""
    # Middleware modifies context in input_hook
    # Second hook sees modifications
    # Modifications don't affect global state
    
def test_hook_async_execution():
    """Test async hook execution."""
    # Async middleware in pipeline
    # Verify async operations complete
    
def test_hook_concurrent_execution():
    """Test concurrent hook execution."""
    # Multiple threads executing pipeline
    # Verify thread safety
    
def test_hook_logging():
    """Test hook execution logging."""
    # Verify hook execution logged
    # Check log contains timing info
```

---

## 2. Permission System Tests

### 2.1 Permission State Machine Tests (8-10 tests)

**File:** `tests/test_permissions.py::TestPermissionStates`

**Tests:**

```python
def test_allow_state():
    """Test ALLOW permission state."""
    # Create ALLOW permission
    # Verify allowed status
    # Check cannot transition to DENY directly
    
def test_deny_state():
    """Test DENY permission state."""
    # Create DENY permission
    # Verify denied status
    # Check cannot be overridden without reset
    
def test_ask_state():
    """Test ASK permission state."""
    # Create ASK permission
    # Verify asking required
    # Check pending decision
    
def test_state_transitions():
    """Test valid state transitions."""
    # ALLOW -> ASK (user revokes)
    # ASK -> ALLOW (user grants)
    # ASK -> DENY (user rejects)
    # Verify invalid transitions raise error
    
def test_state_persistence():
    """Test permission state persistence."""
    # Grant permission
    # Save to database
    # Load and verify state preserved
    
def test_state_expiration():
    """Test permission state expiration."""
    # Grant permission for 1 hour
    # Wait/mock time passage
    # Verify expired permission
    
def test_state_scope():
    """Test permission scope (global, session, tool)."""
    # Grant tool-specific permission
    # Verify applies only to that tool
    # Verify other tools not affected
    
def test_conflicting_permissions():
    """Test handling conflicting permissions."""
    # Global DENY vs Tool-specific ALLOW
    # Verify precedence rules
    
def test_permission_reset():
    """Test resetting permissions."""
    # Grant permission
    # Reset all permissions
    # Verify back to initial state
    
def test_permission_inheritance():
    """Test permission inheritance."""
    # Parent tool has permission
    # Child tool inherits if not explicitly set
```

### 2.2 Permission Engine Tests (10-12 tests)

**File:** `tests/test_permissions.py::TestPermissionEngine`

**Tests:**

```python
def test_check_permission_allowed():
    """Test checking allowed permission."""
    # Grant permission
    # Engine checks permission
    # Verify decision: ALLOWED
    
def test_check_permission_denied():
    """Test checking denied permission."""
    # Deny permission
    # Engine checks permission
    # Verify decision: DENIED
    
def test_check_permission_ask():
    """Test checking ask permission."""
    # ASK state permission
    # Engine returns: REQUIRES_DECISION
    
def test_permission_decision_flow():
    """Test complete permission decision flow."""
    # Unknown permission -> ASK state
    # Prompt user -> ALLOW
    # Verify decision recorded
    
def test_permission_caching():
    """Test permission decision caching."""
    # First check: goes to database
    # Second check: from cache
    # Verify cache hit
    
def test_permission_context_aware():
    """Test context-aware permission."""
    # Different permission for different files
    # Verify correct permission used
    
def test_permission_scope_resolution():
    """Test permission scope resolution."""
    # Multiple overlapping scopes
    # Verify correct scope selected (most specific)
    
def test_permission_audit_log():
    """Test permission decision audit log."""
    # Grant permission
    # Verify decision logged
    # Check log contains user, tool, decision
    
def test_permission_bulk_decisions():
    """Test batch permission decisions."""
    # Multiple permission checks
    # Verify all processed correctly
    
def test_permission_error_handling():
    """Test permission engine error handling."""
    # Database error during check
    # Verify safe fallback (DENY)
    
def test_permission_concurrent_access():
    """Test concurrent permission checks."""
    # Multiple threads checking same permission
    # Verify thread-safe access
    
def test_permission_reporting():
    """Test permission reporting."""
    # Summarize all permissions
    # Generate permission report
```

### 2.3 Permission Prompter Tests (7-8 tests)

**File:** `tests/test_permissions.py::TestPermissionPrompter`

**Tests:**

```python
def test_prompt_for_permission():
    """Test prompting user for permission."""
    # Simulate user responding YES
    # Verify response captured
    
def test_prompt_deny_permission():
    """Test user denying permission."""
    # Simulate user responding NO
    # Verify denial recorded
    
def test_prompt_timeout():
    """Test prompt timeout."""
    # No user response within timeout
    # Verify timeout error
    
def test_prompt_remember_decision():
    """Test remember this decision checkbox."""
    # User checks "remember"
    # Verify decision persisted
    
def test_prompt_context_display():
    """Test permission context in prompt."""
    # Show what tool, why it needs permission
    # Verify clear context to user
    
def test_prompt_multiple_permissions():
    """Test prompting for multiple permissions."""
    # Tool requests 3 permissions
    # User grants some, denies others
    # Verify each decision recorded
    
def test_prompt_batch_approval():
    """Test approving multiple permissions at once."""
    # Show list of permissions
    # User approves all
    # Verify batch processing
    
def test_prompt_interactive_explanation():
    """Test interactive permission explanation."""
    # User asks why permission needed
    # System explains
    # Verify explanation provided
```

### 2.4 Permission Integration Tests (5-8 tests)

**File:** `tests/test_permissions.py::TestPermissionIntegration`

**Tests:**

```python
def test_permission_with_tool_execution():
    """Test permission system with tool execution."""
    # Tool requires file_read permission
    # User grants permission
    # Tool executes successfully
    
def test_permission_with_middleware():
    """Test permission middleware in pipeline."""
    # Tool call hook checks permissions
    # Denies tool execution if not allowed
    # Verify tool blocked
    
def test_permission_with_session():
    """Test permission persistence across session."""
    # Grant permission in session 1
    # Load session 2
    # Verify permission remembered
    
def test_permission_enforcement():
    """Test permission enforcement."""
    # Attempt to use denied tool
    # Verify tool execution blocked
    # Check error message
    
def test_permission_override():
    """Test admin override of permissions."""
    # Permission denied
    # Admin force approves
    # Verify tool executes
```

---

## 3. Cost Tracking Tests

### 3.1 Token Counter Tests (6-8 tests)

**File:** `tests/test_cost_tracking.py::TestTokenCounter`

**Tests:**

```python
def test_count_prompt_tokens():
    """Test counting prompt tokens."""
    # Send prompt to counter
    # Verify token count returned
    
def test_count_completion_tokens():
    """Test counting completion tokens."""
    # Send completion to counter
    # Verify token count
    
def test_count_tool_use_tokens():
    """Test counting tokens in tool calls."""
    # Tool call with parameters
    # Verify token count includes parameters
    
def test_count_vision_tokens():
    """Test counting tokens for vision (images)."""
    # Include image in prompt
    # Verify vision token count
    
def test_count_cached_tokens():
    """Test handling cached tokens."""
    # Prompt caching enabled
    # Verify cached tokens counted separately
    
def test_estimate_tokens():
    """Test token estimation."""
    # Estimate tokens for long text
    # Verify estimation within 5% accuracy
    
def test_token_overflow():
    """Test handling token count overflow."""
    # Very long text
    # Verify correct count even if > max
```

### 3.2 Cost Calculator Tests (8-10 tests)

**File:** `tests/test_cost_tracking.py::TestCostCalculator`

**Tests:**

```python
def test_calculate_anthropic_cost():
    """Test calculating Anthropic cost."""
    # Input: 1000 tokens, Output: 500 tokens
    # Verify cost calculated correctly
    
def test_calculate_openai_cost():
    """Test calculating OpenAI cost."""
    # Different pricing for GPT-4, GPT-3.5
    # Verify correct pricing used
    
def test_calculate_ollama_cost():
    """Test calculating Ollama cost."""
    # Local model, should be free or minimal
    
def test_calculate_batch_cost():
    """Test calculating cost for batch operations."""
    # 10 requests
    # Verify total cost
    
def test_cost_with_caching():
    """Test cost calculation with token caching."""
    # Cached tokens cost less
    # Verify discount applied
    
def test_cost_with_vision():
    """Test cost calculation with vision tokens."""
    # Image incurs vision token cost
    # Verify additional cost
    
def test_cost_currency_conversion():
    """Test currency conversion."""
    # Calculate cost in USD, EUR, GBP
    # Verify conversions correct
    
def test_cost_rounding():
    """Test cost rounding rules."""
    # Verify rounding to 2 decimal places
    
def test_cost_per_operation():
    """Test cost per operation type."""
    # Chat cost
    # Tool execution cost
    # Search cost
    
def test_cost_breakdown():
    """Test cost breakdown by component."""
    # Show cost contribution of each component
```

### 3.3 Budget Manager Tests (7-9 tests)

**File:** `tests/test_cost_tracking.py::TestBudgetManager`

**Tests:**

```python
def test_set_budget():
    """Test setting budget limits."""
    # Set daily budget: $5
    # Set monthly budget: $100
    # Verify limits stored
    
def test_check_budget_available():
    """Test checking available budget."""
    # Budget: $100/month
    # Used: $30
    # Verify available: $70
    
def test_budget_exceeded_alert():
    """Test alert when budget exceeded."""
    # Monthly budget: $100
    # Spending reaches $105
    # Verify alert triggered
    
def test_budget_hard_stop():
    """Test hard stop at budget limit."""
    # Enable hard stop
    # Budget exceeded
    # Verify new operations blocked
    
def test_budget_soft_warning():
    """Test soft warning at 80% budget."""
    # Budget: $100
    # Spending: $80
    # Verify warning issued
    
def test_budget_reset():
    """Test budget period reset."""
    # Daily budget resets at midnight
    # Verify reset works correctly
    
def test_budget_per_session():
    """Test per-session budget limits."""
    # Set session budget: $10
    # Verify enforced for this session
    
def test_budget_per_agent():
    """Test per-agent budget limits."""
    # CodeReviewer budget: $5
    # Debugger budget: $10
    # Verify each agent tracked separately
    
def test_budget_carryover():
    """Test unused budget carryover."""
    # Daily budget not fully used
    # Check if carryover to next day
```

### 3.4 Cost Tracker Tests (6-8 tests)

**File:** `tests/test_cost_tracking.py::TestCostTracker`

**Tests:**

```python
def test_track_session_cost():
    """Test tracking cost for session."""
    # Session with 5 queries
    # Verify total cost tracked
    
def test_track_cost_per_agent():
    """Test tracking cost by agent."""
    # CodingAssistant: 3 queries
    # Debugger: 2 queries
    # Verify costs separated by agent
    
def test_track_cost_per_provider():
    """Test tracking cost by provider."""
    # 2 queries with Anthropic
    # 1 query with OpenAI
    # Verify costs by provider
    
def test_track_daily_cost():
    """Test daily cost aggregation."""
    # Queries throughout day
    # Verify daily total
    
def test_track_monthly_cost():
    """Test monthly cost aggregation."""
    # Queries throughout month
    # Verify monthly total
    
def test_cost_history():
    """Test cost history tracking."""
    # Generate cost history for 30 days
    # Verify history complete
    
def test_cost_export():
    """Test exporting cost data."""
    # Export to CSV/JSON
    # Verify format and completeness
    
def test_cost_optimization_suggestions():
    """Test suggestions for cost optimization."""
    # Analyze usage patterns
    # Suggest cheaper provider/model
```

### 3.5 Cost Integration Tests (6-8 tests)

**File:** `tests/test_cost_tracking.py::TestCostIntegration`

**Tests:**

```python
def test_cost_tracking_with_session():
    """Test cost tracking within session."""
    # Create session
    # Execute queries
    # Verify cost tracked
    
def test_cost_display_in_cli():
    """Test cost display in CLI output."""
    # After chat interaction
    # Verify cost shown
    
def test_cost_persistence():
    """Test cost data persistence."""
    # Track cost
    # Reload from database
    # Verify cost preserved
    
def test_cost_with_budget_enforcement():
    """Test cost tracking with budget."""
    # Set budget
    # Track cost
    # Verify budget enforced
    
def test_cost_reporting():
    """Test cost reporting."""
    # Generate cost report
    # Verify accuracy
    
def test_cost_anomaly_detection():
    """Test detecting cost anomalies."""
    # Spike in usage
    # Verify anomaly detected
```

---

## 4. Integration Tests for Phase 1 Features

### 4.1 Feature Interaction Tests (8-12 tests)

**File:** `tests/integration/test_phase1_features.py`

**Tests:**

```python
@pytest.mark.asyncio
async def test_middleware_with_permissions():
    """Test middleware pipeline with permission checks."""
    # Create pipeline with permission middleware
    # Execute tool call
    # Verify permission checked before execution
    
@pytest.mark.asyncio
async def test_permissions_with_cost_tracking():
    """Test permission grants affecting cost."""
    # Permission required for expensive operation
    # Cost tracked correctly with permission
    
@pytest.mark.asyncio
async def test_cost_with_middleware():
    """Test cost tracking in middleware."""
    # Middleware tracks cost of operations
    # Verify cost accurate
    
@pytest.mark.asyncio
async def test_full_phase1_workflow():
    """Test complete Phase 1 workflow."""
    # User query -> Permission check -> Middleware -> Cost tracking -> Execution
    # Verify all components work together
    
@pytest.mark.asyncio
async def test_phase1_error_recovery():
    """Test error recovery in Phase 1 components."""
    # Permission error -> Fallback
    # Middleware error -> Skip middleware
    # Cost error -> Log and continue
    
@pytest.mark.asyncio
async def test_phase1_concurrent_requests():
    """Test Phase 1 with concurrent requests."""
    # Multiple concurrent queries
    # Verify costs tracked separately
    # Verify permissions enforced
    
@pytest.mark.asyncio
async def test_phase1_session_persistence():
    """Test Phase 1 data persists across sessions."""
    # Grant permissions
    # Track costs
    # End session
    # Start new session
    # Verify permissions and costs remembered
    
@pytest.mark.asyncio
async def test_phase1_cli_integration():
    """Test Phase 1 features in CLI."""
    # Run CLI commands
    # Verify cost displayed
    # Verify permission prompts work
    
@pytest.mark.asyncio
async def test_phase1_with_multiple_providers():
    """Test Phase 1 with multiple LLM providers."""
    # Switch between Anthropic, OpenAI, Ollama
    # Verify costs calculated per provider
    
@pytest.mark.asyncio
async def test_phase1_performance():
    """Test Phase 1 performance impact."""
    # Measure latency with Phase 1 features
    # Verify <5% overhead
    
@pytest.mark.asyncio
async def test_phase1_memory_usage():
    """Test Phase 1 memory efficiency."""
    # Long-running session
    # Monitor memory usage
    # Verify no memory leaks
```

---

## 5. CLI Tests for Phase 1 Features

### 5.1 CLI Cost Display Tests (6-8 tests)

**File:** `tests/cli/test_cli_commands.py`

**Tests:**

```python
def test_cli_show_cost_after_query():
    """Test cost displayed after query."""
    # CLI query -> Response
    # Verify cost shown in output
    
def test_cli_cost_summary():
    """Test cost summary command."""
    # arcon cost summary
    # Verify session/daily/monthly costs
    
def test_cli_cost_breakdown():
    """Test cost breakdown by agent/provider."""
    # arcon cost breakdown
    # Verify costs by agent
    # Verify costs by provider
    
def test_cli_budget_settings():
    """Test budget configuration in CLI."""
    # arcon budget set --daily 5
    # Verify budget set
    
def test_cli_budget_warning():
    """Test budget warning in CLI."""
    # arcon chat (with low budget)
    # Verify warning when approaching limit
    
def test_cli_budget_exceeded():
    """Test exceeding budget in CLI."""
    # arcon chat (with exceeded budget)
    # Verify operation blocked or warned
    
def test_cli_cost_history():
    """Test viewing cost history."""
    # arcon cost history --days 30
    # Verify 30 days of costs shown
    
def test_cli_cost_export():
    """Test exporting costs."""
    # arcon cost export --format csv
    # Verify CSV generated
```

### 5.2 CLI Permission Tests (8-10 tests)

**File:** `tests/cli/test_cli_commands.py`

**Tests:**

```python
def test_cli_permission_prompt():
    """Test permission prompt in interactive chat."""
    # Chat requires permission
    # Mock user granting permission
    # Verify tool executes
    
def test_cli_permission_denied():
    """Test denied permission in CLI."""
    # Chat requires permission
    # Mock user denying permission
    # Verify operation blocked
    
def test_cli_permission_remember():
    """Test remembering permission decision."""
    # Grant permission with "remember"
    # Second query doesn't prompt
    
def test_cli_permissions_list():
    """Test listing granted permissions."""
    # arcon permissions list
    # Verify all permissions shown
    
def test_cli_revoke_permission():
    """Test revoking permission."""
    # arcon permissions revoke tool_name
    # Verify permission revoked
    
def test_cli_reset_permissions():
    """Test resetting all permissions."""
    # arcon permissions reset
    # Verify all permissions cleared
    
def test_cli_permission_scope():
    """Test permission scope display."""
    # Show which permissions apply globally vs per-tool
    
def test_cli_permission_timeout():
    """Test permission prompt timeout."""
    # arcon chat (with 5s timeout)
    # No user input
    # Verify timeout and fallback
    
def test_cli_batch_permissions():
    """Test batch permission approval."""
    # Multiple permissions needed
    # User approves all
    
def test_cli_interactive_permissions():
    """Test interactive permission explanation."""
    # User requests why permission needed
    # Verify explanation provided
```

### 5.3 CLI Integration Tests (6-8 tests)

**File:** `tests/cli/test_cli_commands.py`

**Tests:**

```python
def test_cli_full_workflow():
    """Test complete CLI workflow with Phase 1 features."""
    # arcon chat -> Query -> Permission check -> Execution -> Cost display
    
def test_cli_session_with_costs():
    """Test session tracking costs."""
    # arcon chat --session ID
    # Multiple queries
    # Session summary shows total cost
    
def test_cli_agent_selection_with_cost():
    """Test agent selection shows cost implications."""
    # arcon chat --agent CodingAssistant
    # Show cost per agent
    
def test_cli_error_messages():
    """Test helpful error messages."""
    # Permission denied -> "Grant permission with: arcon permissions allow tool_name"
    # Budget exceeded -> "Set new budget with: arcon budget set"
    
def test_cli_colored_output():
    """Test colored output for cost/permission info."""
    # Cost shown in green
    # Warnings in yellow
    # Errors in red
```

---

## Test Data & Fixtures

### Mock Data for Testing

```python
# Cost fixtures
ANTHROPIC_PRICING = {
    "input": 0.003,      # $0.003 per 1K tokens
    "output": 0.015,     # $0.015 per 1K tokens
}

OPENAI_PRICING = {
    "gpt-4": {"input": 0.03, "output": 0.06},
    "gpt-3.5": {"input": 0.0005, "output": 0.0015},
}

# Permission fixtures
SAMPLE_PERMISSIONS = {
    "file_read": {"scope": "global", "default": "ask"},
    "bash_execute": {"scope": "session", "default": "deny"},
    "internet_access": {"scope": "tool", "default": "ask"},
}

# Token fixtures
SAMPLE_QUERY = "What is the capital of France?"  # ~7 tokens
SAMPLE_RESPONSE = "The capital of France is Paris. It is a major city..."  # ~20 tokens
```

### Fixtures (conftest.py)

```python
@pytest.fixture
def cost_calculator():
    """Provide cost calculator instance."""
    from arcon.cost import CostCalculator
    return CostCalculator()

@pytest.fixture
def permission_engine():
    """Provide permission engine instance."""
    from arcon.permissions import PermissionEngine
    return PermissionEngine()

@pytest.fixture
def middleware_pipeline():
    """Provide middleware pipeline instance."""
    from arcon.middleware import MiddlewarePipeline
    return MiddlewarePipeline()

@pytest.fixture
def test_session():
    """Provide test session."""
    from arcon.core import Session
    return Session()
```

---

## Coverage Goals by Module

| Module | Target | Rationale |
|--------|--------|-----------|
| `middleware/base.py` | 95%+ | Core infrastructure |
| `middleware/pipeline.py` | 95%+ | Critical execution path |
| `permissions/engine.py` | 90%+ | Core logic, complex state |
| `permissions/models.py` | 98%+ | Data structures |
| `cost/calculator.py` | 95%+ | Financial accuracy critical |
| `cost/budget.py` | 90%+ | Budget enforcement |
| `cli/` | 80%+ | Many code paths, less critical |
| Integration tests | 85%+ | Feature interaction |

---

## Performance Benchmarks (to be established)

```python
# Test middleware overhead
def test_middleware_performance():
    """Middleware should add <5ms per operation."""
    # Baseline: 100ms query
    # With middleware: <105ms
    
# Test permission overhead
def test_permission_check_performance():
    """Permission check should be <10ms."""
    # Cached: <1ms
    # Database: <10ms
    
# Test cost calculation overhead
def test_cost_calculation_performance():
    """Cost calculation should be <5ms."""
    # Single operation: <1ms
    # Batch: <5ms
```

---

## Continuous Integration Setup

### GitHub Actions Workflow

```yaml
# .github/workflows/phase1-tests.yml
name: Phase 1 Tests
on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - uses: actions/setup-python@v4
        with:
          python-version: "3.10"
      
      - name: Install dependencies
        run: |
          pip install -r requirements.txt
          pip install pytest pytest-cov pytest-asyncio
      
      - name: Run Phase 1 tests
        run: |
          pytest tests/test_middleware.py \
                 tests/test_permissions.py \
                 tests/test_cost_tracking.py \
                 tests/integration/test_phase1_features.py \
                 --cov=src/arcon/middleware \
                 --cov=src/arcon/permissions \
                 --cov=src/arcon/cost \
                 --cov-report=xml
      
      - name: Upload coverage
        uses: codecov/codecov-action@v3
        with:
          files: ./coverage.xml
```

---

## Test Execution Guide

### Run All Phase 1 Tests

```bash
pytest tests/test_middleware.py \
       tests/test_permissions.py \
       tests/test_cost_tracking.py \
       tests/integration/test_phase1_features.py \
       tests/cli/test_cli_commands.py \
       -v --cov=src/arcon/middleware,src/arcon/permissions,src/arcon/cost
```

### Run Specific Test Class

```bash
pytest tests/test_middleware.py::TestMiddlewarePipeline -v
```

### Run With Coverage Report

```bash
pytest tests/ --cov=src/arcon --cov-report=html
# Open htmlcov/index.html
```

### Run With Parallel Execution

```bash
pytest tests/ -n auto  # Requires pytest-xdist
```

---

## Success Criteria

- ✅ All Phase 1 tests pass (0 failures)
- ✅ Code coverage >85% for Phase 1 modules
- ✅ Performance overhead <5% for all operations
- ✅ All integration tests pass
- ✅ CLI tests cover 80%+ of new features
- ✅ Documentation matches implementation
- ✅ No memory leaks in long-running tests

---

## Timeline

| Week | Phase 1 Component | Tests to Write |
|------|-------------------|-----------------|
| 1 | Middleware | test_middleware.py (25 tests) |
| 2 | Permissions | test_permissions.py (35 tests) |
| 3 | Cost Tracking | test_cost_tracking.py (30 tests) |
| 4 | Integration & CLI | Integration tests (20 tests), CLI tests (30 tests) |

**Total New Tests:** ~140 tests for Phase 1

---

## Conclusion

This testing strategy ensures Phase 1 enhancements are:
- ✅ **Well-tested** (>85% coverage)
- ✅ **Well-integrated** (integration tests validate interactions)
- ✅ **Well-documented** (this strategy is comprehensive)
- ✅ **Well-performing** (performance tests validate overhead)
- ✅ **User-friendly** (CLI tests validate user experience)

Ready to begin Phase 1 implementation.
