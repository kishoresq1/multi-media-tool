# Multi-Agent Architecture

## Supervisor / Orchestrator Agent

### Purpose
Acts as the central coordinator.

Responsibilities:
- Understand user intent
- Break complex tasks into subtasks
- Route work to specialized agents
- Aggregate outputs
- Validate final response
- Decide when to invoke expensive models

### Model
GPT-5 / Claude Opus / Gemini 2.5 Pro

Reason:
- Strong planning
- Better task decomposition
- Better agent routing decisions
- Higher reliability for complex workflows

---

## Agent 1: Repository Analyst

### Purpose
Understand codebase structure.

Responsibilities:
- Dependency analysis
- Architecture mapping
- Folder structure analysis
- Dead code detection
- Service relationship discovery

### Model
GPT-5 Mini / Claude Sonnet

### Input
Repository snapshot

### Output
Architecture report

---

## Agent 2: Code Reviewer

### Purpose
Review implementation quality.

Responsibilities:
- Code smells
- Design issues
- Security concerns
- Performance bottlenecks

### Model
GPT-5 Mini

### Output
Review findings

---

## Agent 3: Bug Hunter

### Purpose
Find defects.

Responsibilities:
- Logic errors
- Edge cases
- Missing validations
- Race conditions

### Model
GPT-5 Mini

### Output
Bug report

---

## Agent 4: API Analyzer

### Purpose
Investigate API behavior.

Responsibilities:
- Endpoint mapping
- Request flow tracing
- Excessive API calls
- Circular requests
- Rate limit risks

### Model
GPT-5 Mini

### Output
API analysis report

---

## Agent 5: Database Analyst

### Purpose
Analyze database interactions.

Responsibilities:
- Query optimization
- N+1 detection
- Missing indexes
- Data flow tracing

### Model
GPT-5 Mini

### Output
Database findings

---

## Agent 6: Python Performance Specialist

### Purpose
Investigate Python-specific issues.

Responsibilities:
- Sync vs Async problems
- Threading issues
- Memory leaks
- Slow imports
- Blocking operations

### Model
GPT-5 Mini

### Output
Performance report

---

## Agent 7: Security Auditor

### Purpose
Security assessment.

Responsibilities:
- Authentication flaws
- Authorization issues
- Secret leakage
- Injection vulnerabilities

### Model
GPT-5 Mini

### Output
Security report

---

## Agent 8: Documentation Writer

### Purpose
Generate documentation.

Responsibilities:
- Architecture docs
- API docs
- README generation
- Deployment guides

### Model
GPT-5 Nano

### Output
Markdown documents

---

## Agent 9: Test Engineer

### Purpose
Testing recommendations.

Responsibilities:
- Unit test generation
- Integration tests
- Coverage gaps

### Model
GPT-5 Nano

### Output
Test plan

---

# Workflow

User Request
        │
        ▼
┌─────────────────┐
│ Orchestrator    │
│ GPT-5           │
└────────┬────────┘
         │
 ┌───────┼────────┬─────────┬──────────┐
 ▼       ▼        ▼         ▼          ▼
Repo   Code     API      DB       Security
Agent  Review   Agent    Agent     Agent
         │
         ▼
    Bug Hunter
         │
         ▼
 Python Specialist
         │
         ▼
 Documentation
         │
         ▼
 Test Engineer
         │
         ▼
 Orchestrator
         │
         ▼
 Final Response

---

# Model Allocation Strategy

| Agent | Model Tier |
|---------|---------|
| Orchestrator | GPT-5 |
| Repository Analyst | GPT-5 Mini |
| Code Reviewer | GPT-5 Mini |
| Bug Hunter | GPT-5 Mini |
| API Analyzer | GPT-5 Mini |
| Database Analyst | GPT-5 Mini |
| Python Specialist | GPT-5 Mini |
| Security Auditor | GPT-5 Mini |
| Documentation Writer | GPT-5 Nano |
| Test Engineer | GPT-5 Nano |

---

# Design Principles

1. Only the Orchestrator uses the expensive model.
2. Specialist agents use smaller models.
3. Documentation and testing use the cheapest models.
4. Agents never talk directly to each other.
5. All communication goes through the Orchestrator.
6. Fan-out/Fan-in execution for parallelism.
7. Shared state stored in a central memory store.
8. Orchestrator performs final validation before responding.