

"""
procrastination_event.py — FocusGuardian AI
Full-screen distraction intervention popup.
Fixed for Windows — tkinter runs on the MAIN thread via a queue-based approach.
"""

import threading
import platform
import os
import random
import queue
from datetime import datetime

# ── Motivational lines ─────────────────────────────────────────────────────────
_HECKLER_LINES = [
    "Eyes on the prize. Back to work.",
    "Your competition isn't resting.",
    "Every second counts. FOCUS.",
    "You set a goal. Honor it.",
    "Champions don't get distracted.",
    "This moment matters. Choose wisely.",
    "Stop scrolling. Start winning.",
    "Discipline beats motivation every time.",
]

_PLEDGE_OPTIONS = [
    "✊  I will refocus RIGHT NOW",
    "⚡  Back to work — let's go!",
    "🎯  Locking in. No excuses.",
    "🔥  I'm focused. Watch me.",
    "💪  Closing distractions NOW",
]


def show_popup(user_name="User", reason="Distraction detected",
               advice="Close distractions and get back to work.",
               countdown=15):
    """
    Show a fullscreen distraction popup and BLOCK until dismissed or timed out.
    This function must be called from the MAIN thread (which main.py does).
    Returns True if user clicked pledge, False if timed out.
    """
    try:
        import tkinter as tk
    except ImportError:
        print("[popup] tkinter not available — skipping popup.")
        return False

    _play_sound("distracted")

    dismissed = [False]  # use list so inner functions can modify it

    root = tk.Tk()
    root.title("⚠ FOCUSGUARDIAN — DISTRACTION DETECTED")
    root.attributes("-fullscreen", True)
    root.attributes("-topmost",    True)
    root.configure(bg="#030712")
    root.bind("<Alt-F4>", lambda e: "break")
    root.bind("<Escape>", lambda e: "break")
    root.protocol("WM_DELETE_WINDOW", lambda: None)

    canvas = tk.Canvas(root, bg="#030712", highlightthickness=0)
    canvas.pack(fill="both", expand=True)

    sw = root.winfo_screenwidth()
    sh = root.winfo_screenheight()

    # Background grid
    for i in range(0, sw, 60):
        canvas.create_line(i, 0, i, sh, fill="#0a1628", width=1)
    for j in range(0, sh, 60):
        canvas.create_line(0, j, sw, j, fill="#0a1628", width=1)

    # Card dimensions
    cx     = sw // 2
    cy     = sh // 2
    card_w = min(860, sw - 80)
    card_h = min(580, sh - 80)
    x0     = cx - card_w // 2
    y0     = cy - card_h // 2

    # Glow layers
    for off, col in [(22, "#3d0012"), (14, "#5a0018"), (7, "#7a0022"), (3, "#ff2d55")]:
        canvas.create_rectangle(
            x0 - off, y0 - off,
            x0 + card_w + off, y0 + card_h + off,
            outline=col, width=1, fill=""
        )

    # Card body
    canvas.create_rectangle(
        x0, y0, x0 + card_w, y0 + card_h,
        fill="#0d1117", outline="#ff2d55", width=2
    )

    # Red header strip
    canvas.create_rectangle(
        x0, y0, x0 + card_w, y0 + 60,
        fill="#1c0a10", outline=""
    )
    canvas.create_text(
        cx, y0 + 30,
        text="⚠   DISTRACTION DETECTED  —  FOCUSGUARDIAN AI",
        fill="#ff2d55",
        font=("Courier", 13, "bold"),
        anchor="center"
    )

    # Main warning
    canvas.create_text(
        cx, y0 + 110,
        text=f"HEY {user_name.upper()}, GET BACK TO WORK!",
        fill="#ffffff",
        font=("Courier", 22, "bold"),
        anchor="center",
        width=card_w - 60
    )

    # Reason
    canvas.create_text(
        cx, y0 + 178,
        text=f"Reason:  {reason}",
        fill="#94a3b8",
        font=("Courier", 13),
        anchor="center",
        width=card_w - 80
    )

    # Advice
    canvas.create_text(
        cx, y0 + 228,
        text=f"Advice:  {advice}",
        fill="#38bdf8",
        font=("Courier", 13),
        anchor="center",
        width=card_w - 80
    )

    # Heckler quote
    canvas.create_text(
        cx, y0 + 285,
        text=f'"{random.choice(_HECKLER_LINES)}"',
        fill="#ff6b6b",
        font=("Courier", 14, "italic"),
        anchor="center"
    )

    # Divider
    canvas.create_line(
        x0 + 40, y0 + 315,
        x0 + card_w - 40, y0 + 315,
        fill="#1e293b", width=1
    )

    # Countdown label
    cd_var = tk.StringVar(value=str(countdown))
    cd_label = tk.Label(
        root,
        textvariable=cd_var,
        bg="#0d1117", fg="#00f5ff",
        font=("Courier", 52, "bold"),
    )
    cd_label.place(x=cx, y=y0 + card_h - 190, anchor="center")

    tk.Label(
        root,
        text="seconds remaining — close distractions before time runs out",
        bg="#0d1117", fg="#475569",
        font=("Courier", 9),
    ).place(x=cx, y=y0 + card_h - 140, anchor="center")

    # Progress bar background
    bar_bg_x0 = x0 + 40
    bar_bg_x1 = x0 + card_w - 40
    bar_y0    = y0 + card_h - 112
    bar_y1    = y0 + card_h - 97
    bar_full  = bar_bg_x1 - bar_bg_x0

    canvas.create_rectangle(
        bar_bg_x0, bar_y0, bar_bg_x1, bar_y1,
        fill="#1e293b", outline=""
    )
    bar_rect = canvas.create_rectangle(
        bar_bg_x0, bar_y0, bar_bg_x1, bar_y1,
        fill="#ff2d55", outline=""
    )

    # Pledge button
    def on_pledge():
        dismissed[0] = True
        _play_sound("dismiss")
        try:
            import tkinter.messagebox as mb
            mb.showinfo(
                "✅  Good Choice!",
                "Every focused minute builds momentum.\nFocusGuardian is watching — make it count!",
                parent=root
            )
        except Exception:
            pass
        root.destroy()

    btn = tk.Button(
        root,
        text=random.choice(_PLEDGE_OPTIONS),
        command=on_pledge,
        bg="#00f5ff", fg="#030712",
        font=("Courier", 14, "bold"),
        relief="flat",
        padx=28, pady=11,
        cursor="hand2",
        activebackground="#38bdf8",
        activeforeground="#030712",
        bd=0,
    )
    btn.place(x=cx, y=y0 + card_h - 50, anchor="center")

    # Timestamp
    canvas.create_text(
        sw - 16, 14,
        text=datetime.now().strftime("%H:%M:%S  ·  %d %b %Y"),
        fill="#1e293b",
        font=("Courier", 9),
        anchor="ne"
    )

    # ── Countdown tick (pure tkinter after — stays on main thread) ────────────
    total_cd = [countdown]

    def tick(remaining):
        if not root.winfo_exists():
            return

        cd_var.set(str(remaining))

        # Color shift
        if remaining <= 5:
            cd_label.configure(fg="#ff2d55")
        elif remaining <= 10:
            cd_label.configure(fg="#ffb800")
        else:
            cd_label.configure(fg="#00f5ff")

        # Shrink bar
        pct  = remaining / max(total_cd[0], 1)
        fill = int(bar_full * pct)
        canvas.coords(bar_rect, bar_bg_x0, bar_y0, bar_bg_x0 + fill, bar_y1)

        if remaining <= 0:
            root.destroy()
            return

        root.after(1000, tick, remaining - 1)

    root.after(1000, tick, countdown - 1)

    # Block here until window closes (stays on main thread — correct for Windows)
    root.mainloop()

    return dismissed[0]


# ── Legacy class wrapper — so main.py import still works ──────────────────────
class ProcrastinationEvent:
    """
    Thin wrapper around show_popup() for backwards compatibility.
    Call trigger() then wait(), or just call show_popup() directly.
    """

    def __init__(self):
        self._result = False

    def trigger(self, user_name="User", reason="Distraction detected",
                advice="Close distractions and get back to work.", countdown=15):
        """Blocking call — shows popup on main thread and waits."""
        self._result = show_popup(
            user_name=user_name,
            reason=reason,
            advice=advice,
            countdown=countdown,
        )

    def wait(self, timeout=None):
        return self._result

    def is_showing(self):
        return False


# ── Sound helper ───────────────────────────────────────────────────────────────
def _play_sound(kind: str = "distracted") -> None:
    def _do():
        try:
            _os = platform.system()
            if _os == "Darwin":
                sounds = {"distracted": "Basso", "dismiss": "Hero", "levelup": "Hero"}
                os.system(f"afplay /System/Library/Sounds/{sounds.get(kind, 'Basso')}.aiff 2>/dev/null")
            elif _os == "Windows":
                import winsound
                freqs = {"distracted": 380, "dismiss": 880, "levelup": 1000}
                winsound.Beep(freqs.get(kind, 440), 350)
            else:
                os.system("paplay /usr/share/sounds/freedesktop/stereo/complete.oga 2>/dev/null || true")
        except Exception:
            pass
    threading.Thread(target=_do, daemon=True).start()


# ── Self-test ──────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    print("Showing test popup for 10 seconds...")
    result = show_popup(
        user_name="Dinesh",
        reason="Watching YouTube videos instead of coding.",
        advice="Close YouTube and return to your IDE.",
        countdown=10,
    )
    print("Dismissed by user!" if result else "Timed out.")
