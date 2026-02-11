#!/bin/bash
# fb-bot Dev Team Monitor
# Run this to check the status of your dev team agents

echo "🚀 fb-bot Dev Team Status"
echo "========================="
echo ""

TEAM_DIR="/home/tk578/fb-bot/dev-team"

# Check each agent
check_agent() {
    local name=$1
    local dir=$2
    local output_file=$3
    
    echo "📋 Agent $name:"
    
    if [ -f "$dir/output/$output_file" ]; then
        echo "   ✅ Status: COMPLETE"
        echo "   📄 Output: $dir/output/$output_file"
        if [ -f "$dir/output/done" ]; then
            echo "   ✓ Marked as done"
        fi
    elif [ -f "$dir/task.txt" ]; then
        echo "   🔄 Status: IN PROGRESS"
        echo "   📝 Task assigned"
    else
        echo "   ⏳ Status: NOT STARTED"
    fi
    
    # Count output files
    if [ -d "$dir/output" ]; then
        file_count=$(ls -1 "$dir/output" 2>/dev/null | wc -l)
        if [ $file_count -gt 0 ]; then
            echo "   📁 Output files: $file_count"
            ls -1 "$dir/output" | sed 's/^/      - /'
        fi
    fi
    echo ""
}

check_agent "Alpha (Architect)" "$TEAM_DIR/alpha" "spec.md"
check_agent "Beta (Builder)" "$TEAM_DIR/beta" "code_changes.md"
check_agent "Gamma (Auditor)" "$TEAM_DIR/gamma" "audit.md"

# Show active sessions
echo "🔍 Active OpenClaw Sessions:"
sessions_list 2>/dev/null | grep -E "(fb-bot-alpha|fb-bot-beta|fb-bot-gamma)" | sed 's/^/   /' || echo "   (run 'sessions_list' to see details)"
echo ""

# Quick commands
echo "📌 Quick Commands:"
echo "   ./dev-team/orchestrator.sh status   - Check team status"
echo "   sessions_list                        - List all agent sessions"
echo "   sessions_history <session-key>       - View agent transcript"
echo ""
echo "💡 Tip: Agents are running in isolated sessions. Check their progress with sessions_history!"