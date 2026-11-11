"""
Claude Code Stop 훅
Claude Code가 응답할 때마다 실행됨.
토큰 사용량을 추적하고 팽도리 알림을 띄움.
"""
import json
import sys
import os
import subprocess

WIDGET = os.path.join(os.path.dirname(os.path.abspath(__file__)), "widget.py")
PYTHON = "/opt/homebrew/bin/python3"
MAX_TOKENS = 200000


LOG_FILE = "/tmp/piplup_debug.log"


def debug_log(msg):
    with open(LOG_FILE, "a") as f:
        import datetime
        f.write(f"[{datetime.datetime.now().isoformat()}] {msg}\n")


RATE_FILE = "/tmp/piplup_rate.json"


def main():
    try:
        data = json.loads(sys.stdin.read())
    except Exception:
        data = {}

    used_percent = 0
    used_tokens = 0
    max_tokens = MAX_TOKENS

    # statusLine이 캡처한 rate_limits 파일에서 읽기
    try:
        with open(RATE_FILE) as f:
            rate_data = json.load(f)
        ctx = rate_data.get("context_window", {})
        used_percent = ctx.get("used_percentage", 0)
        max_tokens = ctx.get("context_window_size", MAX_TOKENS)
        cur = ctx.get("current_usage", {})
        used_tokens = (
            cur.get("input_tokens", 0)
            + cur.get("output_tokens", 0)
            + cur.get("cache_creation_input_tokens", 0)
            + cur.get("cache_read_input_tokens", 0)
        )
    except Exception:
        # 파일 없으면 transcript 파싱으로 폴백
        transcript_path = data.get("transcript_path", "")
        if transcript_path:
            try:
                with open(transcript_path) as f:
                    lines = f.readlines()
                for line in reversed(lines):
                    try:
                        entry = json.loads(line)
                        msg = entry.get("message", {})
                        usage = msg.get("usage", {}) or entry.get("usage", {})
                        inp = usage.get("input_tokens", 0)
                        cr = usage.get("cache_read_input_tokens", 0)
                        cc = usage.get("cache_creation_input_tokens", 0)
                        total = inp + cr + cc
                        if total > 0:
                            used_tokens = total
                            break
                    except Exception:
                        continue
            except Exception:
                pass
        if used_tokens == 0:
            used_tokens = 2000
        used_percent = round((used_tokens / max_tokens) * 100, 1)

    # 팽도리 알림 실행 (백그라운드)
    subprocess.Popen(
        [PYTHON, WIDGET, str(used_percent), str(used_tokens), str(max_tokens)],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL
    )


if __name__ == "__main__":
    main()
