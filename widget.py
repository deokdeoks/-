"""
팽도리 토큰 알림 팝업
사용: python3 widget.py <percent>
예시: python3 widget.py 75.5
"""
import tkinter as tk
import sys
import os
from PIL import Image, ImageTk, ImageSequence

GIF_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "piplup.gif")
SHOW_MS = 3000  # 표시 시간 (ms)


def remove_shadow(root):
    """macOS 창 그림자 제거"""
    try:
        import ctypes, ctypes.util
        objc = ctypes.cdll.LoadLibrary(ctypes.util.find_library('objc'))
        objc.objc_getClass.restype = ctypes.c_void_p
        objc.sel_registerName.restype = ctypes.c_void_p
        objc.objc_msgSend.restype = ctypes.c_void_p
        objc.objc_msgSend.argtypes = [ctypes.c_void_p, ctypes.c_void_p]

        NSApp = objc.objc_msgSend(
            objc.objc_getClass(b'NSApplication'),
            objc.sel_registerName(b'sharedApplication')
        )
        win = objc.objc_msgSend(NSApp, objc.sel_registerName(b'keyWindow'))

        set_shadow = objc.sel_registerName(b'setHasShadow:')
        objc.objc_msgSend.argtypes = [ctypes.c_void_p, ctypes.c_void_p, ctypes.c_bool]
        objc.objc_msgSend(win, set_shadow, False)
    except Exception:
        pass


def show(percent: float, used: int = 0, max_tokens: int = 200000):
    root = tk.Tk()
    root.withdraw()  # 먼저 숨기기
    root.overrideredirect(True)
    root.attributes("-topmost", True)
    root.attributes("-transparent", True)
    root.configure(bg="systemTransparent")

    # GIF 로드
    frames, durations = [], []
    gif = Image.open(GIF_PATH)
    orig_w, orig_h = gif.size
    new_w, new_h = orig_w // 2, orig_h // 2
    for frame in ImageSequence.Iterator(gif):
        durations.append(max(frame.info.get("duration", 100), 50))
        resized = frame.convert("RGBA").resize((new_w, new_h), Image.LANCZOS)
        frames.append(ImageTk.PhotoImage(resized))

    w, h = new_w, new_h
    sw, sh = root.winfo_screenwidth(), root.winfo_screenheight()
    root.geometry(f"{w}x{h}+{(sw-w)//2}+{(sh-h)//2}")

    lbl = tk.Label(root, image=frames[0], bg="systemTransparent")
    lbl.pack()

    # color = "#ff4444" if percent > 70 else ("#ffcc00" if percent > 30 else "#00ff88")
    # tk.Label(root, text=f"{percent:.1f}% 사용",
    #          font=("Helvetica", 22, "bold"),
    #          fg=color, bg="systemTransparent").pack(pady=(6, 2))
    # tk.Label(root, text=f"{used:,} / {max_tokens:,} 토큰",
    #          font=("Helvetica", 12),
    #          fg="#cccccc", bg="systemTransparent").pack()

    idx = [0]
    def animate():
        if not root.winfo_exists():
            return
        lbl.config(image=frames[idx[0] % len(frames)])
        idx[0] += 1
        root.after(durations[idx[0] % len(durations)], animate)
    root.deiconify()  # 세팅 완료 후 표시
    animate()
    root.after(50, lambda: remove_shadow(root))

    root.after(SHOW_MS, root.destroy)
    root.mainloop()


if __name__ == "__main__":
    percent = float(sys.argv[1]) if len(sys.argv) > 1 else 100.0
    used = int(sys.argv[2]) if len(sys.argv) > 2 else 0
    max_tokens = int(sys.argv[3]) if len(sys.argv) > 3 else 200000
    show(percent, used, max_tokens)
