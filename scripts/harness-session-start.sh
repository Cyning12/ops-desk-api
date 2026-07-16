#!/usr/bin/env bash
# harness-session-start.sh
# SessionStart hook：每次新会话启动时扫描 active task 与分支状态

set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "${ROOT_DIR}"

branch=$(git branch --show-current 2>/dev/null || echo "unknown")
tasks=$(find docs/tasks/active -maxdepth 1 -name "task_*.md" -print 2>/dev/null | sort | head -5)

msg="Harness Session Start\nBranch: ${branch}\n"

if [ -n "${tasks}" ]; then
    msg+="Active tasks:\\n"
    while IFS= read -r t; do
        title=$(grep "^# Task:" "${t}" 2>/dev/null | head -1 | sed 's/^# Task: *//' || basename "${t}")
        status=$(grep "^> \\*\\*状态\\*\\*" "${t}" 2>/dev/null | sed 's/.*: *//' | tr -d '\\*' | tr -d ' ' || echo "unknown")
        msg+="  - ${title} (${status})\\n"
    done <<<"${tasks}"
else
    msg+="No active task. Create one in docs/tasks/active/ before coding.\\n"
fi

# 输出 JSON systemMessage
cat <<EOF
{"systemMessage": "${msg}"}
EOF
