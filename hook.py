"""
Claude Code Stop 훅
Claude Code가 응답할 때마다 실행됨.
토큰 사용량을 추적하고 팽도리 알림을 띄움.
"""
import json
import sys
import os
import subprocess

DIR = os.path.dirname(os.path.abspath(__file__))
WIDGET = os.path.join(DIR, "widget.py")
PYTHON = "/opt/homebrew/bin/python3"
MAX_TOKENS = 200000
RATE_FILE = "/tmp/piplup_rate.json"
STATE_FILE = os.path.expanduser("~/.piplup_state.json")

# 구간별 GIF 매핑: (최소 사용량%, gif 파일명)
THRESHOLDS = [
    (0,   "piplup1.gif"),
    (25,  "piplup2.gif"),
    (50,  "piplup3.gif"),
    (75,  "piplup4.gif"),
    (100, "piplup5.gif"),
]


def get_bracket(percent):
    """현재 사용량이 속하는 구간 반환"""
    for threshold, gif in reversed(THRESHOLDS):
        if percent >= threshold:
            return threshold, gif
    return THRESHOLDS[0]


def load_state():
    try:
        with open(STATE_FILE) as f:
            d = json.load(f)
        # 옛날 포맷 호환
        if "session_id" not in d:
            return {"session_id": "", "shown": []}
        return d
    except Exception:
        return {"session_id": "", "shown": []}


def save_state(state):
    with open(STATE_FILE, "w") as f:
        json.dump(state, f)


def main():
    try:
        data = json.loads(sys.stdin.read())
    except Exception:
        data = {}

    used_percent = 0
    used_tokens = 0
    max_tokens = MAX_TOKENS

    # statusLine이 캡처한 rate_limits 파일에서 읽기 (같은 세션일 때만 사용)
    rate_ok = False
    try:
        with open(RATE_FILE) as f:
            rate_data = json.load(f)
        if rate_data.get("session_id") == data.get("session_id", ""):
            used_percent = rate_data["rate_limits"]["five_hour"]["used_percentage"]
            ctx = rate_data.get("context_window", {})
            max_tokens = ctx.get("context_window_size", MAX_TOKENS)
            cur = ctx.get("current_usage", {})
            used_tokens = (
                cur.get("input_tokens", 0)
                + cur.get("output_tokens", 0)
                + cur.get("cache_creation_input_tokens", 0)
                + cur.get("cache_read_input_tokens", 0)
            )
            rate_ok = True
    except Exception:
        pass

    if not rate_ok:
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

    # 세션별 구간 추적
    session_id = data.get("session_id", "")
    state = load_state()

    # 새 세션이면 초기화
    if state["session_id"] != session_id:
        state = {"session_id": session_id, "shown": []}

    bracket, gif_name = get_bracket(used_percent)

    # 이미 보여준 구간이면 패스
    if bracket in state["shown"]:
        save_state(state)
        return

    # 처음 진입한 구간이면 표시
    state["shown"].append(bracket)
    save_state(state)

    gif_path = os.path.join(DIR, gif_name)
    subprocess.Popen(
        [PYTHON, WIDGET, str(used_percent), str(used_tokens), str(max_tokens), gif_path],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL
    )


if __name__ == "__main__":
    main()
