# fb-bot + Dev Team Core Integration

## 🎯 Overview

fb-bot now uses the **centralized Dev Team Core** for Antigravity Kit agents and skills. This allows sharing the same AI infrastructure across all your projects.

## 📁 Architecture

```
Centralized Dev Team Core:
~/dev-team-core/
└── .agent/                    ← Shared by all projects
    ├── agents/               ← 20 specialist agents
    ├── skills/               ← 38 domain skills
    └── workflows/            ← 11 slash workflows

fb-bot Project:
~/fb-bot/
├── .agent -> ~/dev-team-core/.agent  ← Symlink (shared)
├── dev-team/                         ← Project-specific team
│   ├── alpha/                       (Architect - Claude)
│   ├── beta/                        (Builder - GLM)
│   └── gamma/                       (Auditor - DeepSeek)
└── src/                             ← Your code
```

## 🤖 Two-Layer AI Team

### Layer 1: Project-Specific Dev Team (fb-bot)

Your custom agents for the fb-bot project:

| Agent | Model | Role | Status |
|-------|-------|------|--------|
| **Alpha** | Claude 3.5 Sonnet | Architect | ✅ Complete (74KB spec) |
| **Beta** | GLM-4.6 | Builder | ✅ Complete (196KB code) |
| **Gamma** | DeepSeek Coder | Auditor | 🔄 In Progress |

**Purpose:** Handle fb-bot specific architecture, implementation, and auditing.

### Layer 2: Shared Antigravity Agents (Dev Team Core)

Available in ALL your projects:

| Agent | Best For |
|-------|----------|
| `security-auditor` | Deep security reviews |
| `backend-specialist` | FastAPI optimization |
| `performance-optimizer` | Rate limiter tuning |
| `qa-automation-engineer` | Automated testing |
| `devops-engineer` | Docker/deployment |
| `database-architect` | ChromaDB optimization |

**Purpose:** Specialized tasks that apply to any project.

## 🛠️ How to Use

### Using Project-Specific Team (Alpha/Beta/Gamma)

```bash
# Check status
cd ~/fb-bot
cat dev-team/alpha/output/spec.md        # View architecture
cat dev-team/beta/output/services/*.py   # View implementation
cat dev-team/gamma/output/audit.md       # View audit (when ready)
```

### Using Shared Antigravity Agents

```bash
# List available agents
~/dev-team-core/setup.sh list-agents

# Use an agent for specialized task
npx @vudovn/ag-kit agent security-auditor

# Or use slash commands in Cursor/Windsurf
/debug Facebook token expiration issue
/plan Add new webhook endpoint
/test --coverage
```

### Combining Both Teams

**Example: Security Audit**

1. **Gamma (Project)** does initial audit of Beta's code
2. **security-auditor (Shared)** does deep-dive penetration testing
3. **Compare results** and fix issues

```bash
# Gamma's audit (project-specific)
cat ~/fb-bot/dev-team/gamma/output/audit.md

# Additional audit with shared agent
npx @vudovn/ag-kit agent penetration-tester
```

**Example: Performance Optimization**

1. **Beta (Project)** implements rate limiter
2. **performance-optimizer (Shared)** tunes it further
3. **database-architect (Shared)** optimizes ChromaDB queries

```bash
# Beta's implementation
cat ~/fb-bot/dev-team/beta/output/services/enhanced_rate_limiter.py

# Additional optimization with shared agent
npx @vudovn/ag-kit agent performance-optimizer
```

## 📚 Key Files

### Project-Specific (fb-bot)

| File | Purpose |
|------|---------|
| `dev-team/alpha/output/spec.md` | Architecture specification |
| `dev-team/beta/output/services/*.py` | Implementation code |
| `dev-team/gamma/output/audit.md` | Security audit report |

### Shared (Dev Team Core)

| File | Purpose |
|------|---------|
| `~/dev-team-core/.agent/agents/*.md` | Agent definitions |
| `~/dev-team-core/.agent/skills/*/SKILL.md` | Skill documentation |
| `~/dev-team-core/.agent/workflows/*.md` | Workflow guides |
| `~/dev-team-core/README.md` | Dev Team Core docs |

## 🔄 Updating

**Update Dev Team Core (affects all projects):**
```bash
~/dev-team-core/setup.sh update
```

**Check status:**
```bash
~/dev-team-core/setup.sh status
```

## 🎯 Current Status

| Component | Status |
|-----------|--------|
| Alpha's Architecture Spec | ✅ Complete (85 pages) |
| Beta's Implementation | ✅ Complete (15 files, 196KB) |
| Gamma's Security Audit | 🔄 In Progress |
| Antigravity Integration | ✅ Linked |
| Available Shared Agents | ✅ 20 agents ready |

## 🚀 Next Steps

1. **Wait for Gamma's audit** to complete
2. **Review audit results** and fix any issues
3. **Deploy improvements** to production
4. **Use shared agents** for ongoing optimization:
   - `performance-optimizer` for rate limiter tuning
   - `qa-automation-engineer` for test automation
   - `security-auditor` for periodic security reviews

## 💡 Benefits of This Architecture

✅ **Centralized** - One Antigravity Kit for all projects  
✅ **Specialized** - Project-specific team (Alpha/Beta/Gamma) for deep domain knowledge  
✅ **Flexible** - Shared agents available in any project  
✅ **Scalable** - Add new projects by just running `setup.sh link`  
✅ **Updatable** - Update core once, all projects benefit  

---

Your fb-bot now has **two layers of AI power** working together! 🤖🤖