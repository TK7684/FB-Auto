#!/bin/bash
# fb-bot Dev Team Orchestrator
# Manages the workflow between Agent Alpha, Beta, and Gamma

set -e

PROJECT_DIR="/home/tk578/fb-bot"
TEAM_DIR="$PROJECT_DIR/dev-team"
LOG_DIR="$TEAM_DIR/logs"

# API Keys (loaded from environment)
export KIMI_API_KEY="${KIMI_API_KEY:-sk-kimi-FIf9YQ5qyVCmJuWskGOrSzw78514WaPPoYi2KXi6oVLemvO9PS1jRPm2purlMVUy}"
export GEMINI_API_KEY="${GEMINI_API_KEY:-AIzaSyAL91mukHurUJYMkYcUxk5tWIZnmToCstk}"
export OPENROUTER_API_KEY="${OPENROUTER_API_KEY:-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}"
export GLM_API_KEY="${GLM_API_KEY:-db8adca3674a4b0fa8841f6970040db4.PXvMANbfwNcAQ9kP}"

mkdir -p "$LOG_DIR"

echo "🚀 fb-bot Dev Team Orchestrator"
echo "================================"
echo ""

# Phase 1: Architecture (Agent Alpha - Claude 3.5 Sonnet)
run_alpha() {
    echo "📐 Phase 1: Agent Alpha (Architect) - Designing system..."
    echo "   Model: Claude 3.5 Sonnet via OpenRouter"
    
    # Create task for Alpha
    cat > "$TEAM_DIR/alpha/task.txt" << 'EOF'
TASK: Review the current fb-bot codebase and design improvements for:
1. Better error handling for Facebook API failures
2. Enhanced rate limiting with circuit breaker pattern
3. Improved Thai language response quality

Current codebase location: /home/tk578/fb-bot
Key files to analyze:
- main.py (FastAPI app)
- services/facebook_service.py
- services/gemini_service.py
- services/rate_limiter.py

Read these files and produce a Technical Specification Document.
EOF

    echo "   Task created at: $TEAM_DIR/alpha/task.txt"
    echo "   ⚠️  Run Agent Alpha manually with this task"
    echo ""
}

# Phase 2: Implementation (Agent Beta - GLM-4.6)
run_beta() {
    echo "🔨 Phase 2: Agent Beta (Builder) - Implementing code..."
    echo "   Model: GLM-4.6 (Unlimited Plan)"
    
    if [ ! -f "$TEAM_DIR/alpha/output/spec.md" ]; then
        echo "   ❌ Error: Alpha spec not found. Run Phase 1 first."
        return 1
    fi
    
    cat > "$TEAM_DIR/beta/task.txt" << EOF
TASK: Implement the code based on Agent Alpha's specification.

Specification location: $TEAM_DIR/alpha/output/spec.md

Implement all changes as specified, ensuring:
- Production-ready code
- Comprehensive error handling
- Thai language support
- Facebook rate limit compliance
- Proper logging

Output: Modified Python files ready for deployment.
EOF

    echo "   Task created at: $TEAM_DIR/beta/task.txt"
    echo "   ⚠️  Run Agent Beta manually with this task"
    echo ""
}

# Phase 3: Audit (Agent Gamma - DeepSeek Coder)
run_gamma() {
    echo "🔍 Phase 3: Agent Gamma (Auditor) - Security review..."
    echo "   Model: DeepSeek Coder V2 via OpenRouter"
    
    if [ ! -f "$TEAM_DIR/beta/output/code_changes.md" ]; then
        echo "   ❌ Error: Beta code not found. Run Phase 2 first."
        return 1
    fi
    
    cat > "$TEAM_DIR/gamma/task.txt" << EOF
TASK: Perform security audit on the code changes from Agent Beta.

Code location: $TEAM_DIR/beta/output/

Review for:
- Security vulnerabilities (OWASP Top 10)
- Facebook API compliance
- Rate limiting correctness
- Error handling completeness
- Performance issues

Output: Audit report with APPROVED or REQUEST CHANGES status.
EOF

    echo "   Task created at: $TEAM_DIR/gamma/task.txt"
    echo "   ⚠️  Run Agent Gamma manually with this task"
    echo ""
}

# Main workflow
case "${1:-full}" in
    alpha|1)
        run_alpha
        ;;
    beta|2)
        run_beta
        ;;
    gamma|3)
        run_gamma
        ;;
    full|all)
        run_alpha
        echo "⏳ Complete Phase 1, then run: $0 beta"
        ;;
    status)
        echo "📊 Dev Team Status"
        echo "=================="
        for agent in alpha beta gamma; do
            if [ -f "$TEAM_DIR/$agent/output/done" ]; then
                echo "  ✅ Agent $agent: Complete"
            elif [ -f "$TEAM_DIR/$agent/task.txt" ]; then
                echo "  🔄 Agent $agent: In Progress"
            else
                echo "  ⏳ Agent $agent: Not Started"
            fi
        done
        ;;
    *)
        echo "Usage: $0 [alpha|beta|gamma|full|status]"
        echo ""
        echo "Workflow:"
        echo "  1. $0 alpha   - Run Agent Alpha (Architect)"
        echo "  2. $0 beta    - Run Agent Beta (Builder)"
        echo "  3. $0 gamma   - Run Agent Gamma (Auditor)"
        echo "  4. $0 status  - Check team status"
        exit 1
        ;;
esac