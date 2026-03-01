


"""
utils.py — FocusGuardian AI
Screenshot capture, file management, desktop notifications, sound alerts,
and CSV/JSON logging helpers.
"""

import os
import sys
import csv
import json
import shutil
import platform
import threading
from datetime import datetime, timedelta
from pathlib import Path

BASE_DIR      = os.path.dirname(os.path.abspath(__file__))
SCREENSHOT_DIR= os.path.join(BASE_DIR, "screenshots")
LOG_FILE      = os.path.join(BASE_DIR, "focus_log.csv")

os.makedirs(SCREENSHOT_DIR, exist_ok=True)

# ── Screenshot capture ─────────────────────────────────────────────────────────
def take_screenshots(all_monitors: bool = False) -> list[str]:
    """
    Capture one or all monitors using mss.
    Returns list of saved file paths.
    """
    try:
        import mss
        import mss.tools

        paths = []
        ts    = datetime.now().strftime("%Y%m%d_%H%M%S")

        with mss.mss() as sct:
            monitors = sct.monitors[1:] if all_monitors else [sct.monitors[1]]
            for idx, monitor in enumerate(monitors):
                filename = f"screenshot_{ts}_m{idx}.png"
                filepath = os.path.join(SCREENSHOT_DIR, filename)
                img = sct.grab(monitor)
                mss.tools.to_png(img.rgb, img.size, output=filepath)
                paths.append(filepath)

        return paths

    except ImportError:
        print("[utils] mss not installed — pip install mss")
        return []
    except Exception as e:
        print(f"[utils] Screenshot error: {e}")
        return []


def cleanup_screenshots(keep_last: int = 20) -> int:
    """Delete old screenshots, keep the N most recent. Returns deleted count."""
    pngs = sorted(
        Path(SCREENSHOT_DIR).glob("screenshot_*.png"),
        key=lambda p: p.stat().st_mtime
    )
    to_delete = pngs[:-keep_last] if len(pngs) > keep_last else []
    for p in to_delete:
        try:
            p.unlink()
        except Exception:
            pass
    return len(to_delete)


# ── CSV logging ────────────────────────────────────────────────────────────────
_CSV_FIELDS = [
    "timestamp", "status", "reason", "confidence",
    "category", "focus_score", "level", "xp", "streak",
]

def log_event(data: dict) -> None:
    """Append a monitoring tick dict to focus_log.csv."""
    file_exists = os.path.isfile(LOG_FILE)
    # Fill in any missing fields
    row = {f: data.get(f, "") for f in _CSV_FIELDS}
    if not row["timestamp"]:
        row["timestamp"] = datetime.now().isoformat(timespec="seconds")

    with open(LOG_FILE, "a", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(fh, fieldnames=_CSV_FIELDS)
        if not file_exists:
            writer.writeheader()
        writer.writerow(row)


def read_recent_events(n: int = 50) -> list[dict]:
    """Return the last N rows from the CSV as a list of dicts."""
    if not os.path.exists(LOG_FILE):
        return []
    with open(LOG_FILE, "r", encoding="utf-8") as fh:
        rows = list(csv.DictReader(fh))
    return rows[-n:]


# ── Desktop notifications ──────────────────────────────────────────────────────
def send_notification(title: str, message: str) -> None:
    """
    Fire a desktop notification (best-effort, no crash on failure).
    Supports Windows, macOS, and Linux (notify-send).
    """
    def _notify():
        try:
            _os = platform.system()
            if _os == "Darwin":
                os.system(
                    f'osascript -e \'display notification "{message}" '
                    f'with title "{title}"\''
                )
            elif _os == "Windows":
                try:
                    from win10toast import ToastNotifier  # type: ignore
                    ToastNotifier().show_toast(title, message, duration=4, threaded=True)
                except ImportError:
                    pass  # optional dependency
            else:
                os.system(f'notify-send "{title}" "{message}" 2>/dev/null')
        except Exception:
            pass
    threading.Thread(target=_notify, daemon=True).start()


# ── Sound alerts ───────────────────────────────────────────────────────────────
def play_alert_sound(kind: str = "distracted") -> None:
    """
    Play a short beep / system sound (best-effort).
    kind: 'distracted' | 'levelup' | 'focused'
    """
    def _play():
        try:
            _os = platform.system()
            if _os == "Darwin":
                sound = {"distracted": "Basso", "levelup": "Hero", "focused": "Ping"}.get(kind, "Basso")
                os.system(f"afplay /System/Library/Sounds/{sound}.aiff 2>/dev/null")
            elif _os == "Windows":
                import winsound  # type: ignore
                freq = {"distracted": 400, "levelup": 880, "focused": 660}.get(kind, 440)
                winsound.Beep(freq, 400)
            else:
                # Linux fallback — try paplay, then beep
                os.system("paplay /usr/share/sounds/freedesktop/stereo/complete.oga 2>/dev/null || "
                          "beep -f 500 -l 300 2>/dev/null || true")
        except Exception:
            pass
    threading.Thread(target=_play, daemon=True).start()


# ── Session timer helpers ──────────────────────────────────────────────────────
def format_duration(seconds: int) -> str:
    """Convert seconds to human-readable '1h 23m 45s'."""
    h  = seconds // 3600
    m  = (seconds % 3600) // 60
    s  = seconds % 60
    parts = []
    if h: parts.append(f"{h}h")
    if m: parts.append(f"{m}m")
    parts.append(f"{s}s")
    return " ".join(parts)


def time_since(iso_ts: str) -> str:
    """Return human delta like '5 min ago' from an ISO timestamp string."""
    try:
        then  = datetime.fromisoformat(iso_ts)
        delta = datetime.now() - then
        secs  = int(delta.total_seconds())
        if secs < 60:
            return f"{secs}s ago"
        elif secs < 3600:
            return f"{secs // 60}m ago"
        else:
            return f"{secs // 3600}h {(secs % 3600) // 60}m ago"
    except Exception:
        return "unknown"


# ── Config persistence ─────────────────────────────────────────────────────────
CONFIG_FILE = os.path.join(BASE_DIR, "config.json")

_DEFAULT_CONFIG = {
    "delay_time":       45,
    "countdown_time":   10,
    "user_name":        "User",
    "all_monitors":     False,
    "daily_goal_hours": 4,
    "sound_enabled":    True,
    "notify_enabled":   True,
    "keep_screenshots": 20,
}

def load_config() -> dict:
    if os.path.exists(CONFIG_FILE):
        try:
            with open(CONFIG_FILE, "r", encoding="utf-8") as fh:
                saved = json.load(fh)
            cfg = _DEFAULT_CONFIG.copy()
            cfg.update(saved)
            return cfg
        except Exception:
            pass
    return _DEFAULT_CONFIG.copy()


def save_config(cfg: dict) -> None:
    merged = _DEFAULT_CONFIG.copy()
    merged.update(cfg)
    with open(CONFIG_FILE, "w", encoding="utf-8") as fh:
        json.dump(merged, fh, indent=2)


# ── Disk usage guard ───────────────────────────────────────────────────────────
def screenshots_disk_mb() -> float:
    """Return total MB used by the screenshots directory."""
    total = sum(p.stat().st_size for p in Path(SCREENSHOT_DIR).glob("*.png"))
    return round(total / 1_048_576, 2)
