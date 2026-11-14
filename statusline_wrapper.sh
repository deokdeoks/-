#!/bin/sh
# rate_limits 데이터를 세션별 파일로 캡처한 뒤 오르카로 전달
INPUT=$(cat)
SESSION_ID=$(printf '%s' "$INPUT" | /opt/homebrew/bin/python3 -c "import json,sys; print(json.load(sys.stdin).get('session_id','unknown'))" 2>/dev/null || echo "unknown")
printf '%s' "$INPUT" > "/tmp/piplup_rate_${SESSION_ID}.json"
printf '%s\n' "$INPUT" | /bin/sh "${HOME}/.orca/agent-hooks/claude-statusline.sh"
