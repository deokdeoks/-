#!/bin/sh
# rate_limits 데이터를 캡처한 뒤 오르카로 전달
tee /tmp/piplup_rate.json | /bin/sh "${HOME}/.orca/agent-hooks/claude-statusline.sh"
