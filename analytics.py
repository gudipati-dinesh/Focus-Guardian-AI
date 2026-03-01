


"""
analytics.py — FocusGuardian AI
Handles all data logging, session summaries, trend analysis, and export.
"""

import csv
import os
import json
from datetime import datetime, timedelta
from collections import Counter

# ── Paths ──────────────────────────────────────────────────────────────────────
BASE_DIR  = os.path.dirname(os.path.abspath(__file__))
LOG_FILE  = os.path.join(BASE_DIR, "focus_log.csv")
SESS_FILE = os.path.join(BASE_DIR, "sessions.json")       # one record per run
STATS_FILE= os.path.join(BASE_DIR, "lifetime_stats.json") # cumulative counters

# ── CSV columns ────────────────────────────────────────────────────────────────
CSV_FIELDS = [
    "timestamp", "status", "reason", "confidence",
    "category", "focus_score", "level", "xp", "streak",
]

# ── Bootstrap files ────────────────────────────────────────────────────────────
def _ensure_csv():
    if not os.path.exists(LOG_FILE):
        with open(LOG_FILE, "w", newline="", encoding="utf-8") as fh:
            csv.DictWriter(fh, fieldnames=CSV_FIELDS).writeheader()

def _ensure_json(path, default):
    if not os.path.exists(path):
        with open(path, "w", encoding="utf-8") as fh:
            json.dump(default, fh, indent=2)

_ensure_csv()
_ensure_json(SESS_FILE,  {"sessions": []})
_ensure_json(STATS_FILE, {
    "total_focused_seconds":    0,
    "total_distracted_seconds": 0,
    "total_xp":                 0,
    "max_level":                1,
    "max_focus_score":          100,
    "total_sessions":           0,
    "top_distraction_category": "none",
    "all_categories":           {},
})


# ── Core log event ─────────────────────────────────────────────────────────────
def log_event(data: dict, delay_seconds: int = 45) -> None:
    """
    Append one monitoring tick to the CSV.
    `data` must contain at least: status, focus_score.
    Any missing CSV fields are filled with sensible defaults.
    """
    _ensure_csv()

    row = {
        "timestamp":   datetime.now().isoformat(timespec="seconds"),
        "status":      data.get("status",      "FOCUSED"),
        "reason":      data.get("reason",      ""),
        "confidence":  data.get("confidence",  1.0),
        "category":    data.get("category",    "other"),
        "focus_score": data.get("focus_score", 100),
        "level":       data.get("level",       1),
        "xp":          data.get("xp",          0),
        "streak":      data.get("streak",      0),
    }

    with open(LOG_FILE, "a", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(fh, fieldnames=CSV_FIELDS)
        writer.writerow(row)

    # ── Live lifetime stats update ─────────────────────────────────────────────
    stats = _load_json(STATS_FILE)
    if row["status"] == "FOCUSED":
        stats["total_focused_seconds"]    += delay_seconds
    else:
        stats["total_distracted_seconds"] += delay_seconds
    stats["total_xp"]         = max(stats["total_xp"],         int(row["xp"]))
    stats["max_level"]        = max(stats["max_level"],        int(row["level"]))
    stats["max_focus_score"]  = max(stats["max_focus_score"],  int(row["focus_score"]))

    cat = row["category"]
    stats["all_categories"][cat] = stats["all_categories"].get(cat, 0) + 1
    stats["top_distraction_category"] = max(
        stats["all_categories"], key=stats["all_categories"].get
    )
    _save_json(STATS_FILE, stats)


# ── Session management ─────────────────────────────────────────────────────────
def start_session(user_spec: str, user_name: str) -> str:
    """Record session start; return session_id (ISO timestamp string)."""
    session_id = datetime.now().isoformat(timespec="seconds")
    sessions   = _load_json(SESS_FILE)
    sessions["sessions"].append({
        "id":        session_id,
        "user":      user_name,
        "task":      user_spec,
        "started":   session_id,
        "ended":     None,
        "ticks":     0,
        "focused":   0,
        "distracted":0,
        "final_score": None,
    })
    _save_json(SESS_FILE, sessions)

    # bump counter
    stats = _load_json(STATS_FILE)
    stats["total_sessions"] += 1
    _save_json(STATS_FILE, stats)

    return session_id


def end_session(session_id: str, final_score: int) -> dict:
    """Mark session as ended; return summary dict."""
    sessions = _load_json(SESS_FILE)
    summary  = {}
    for s in sessions["sessions"]:
        if s["id"] == session_id:
            s["ended"]      = datetime.now().isoformat(timespec="seconds")
            s["final_score"]= final_score
            summary = s.copy()
            break
    _save_json(SESS_FILE, sessions)
    return summary


def tick_session(session_id: str, status: str) -> None:
    """Increment tick counters for the active session."""
    sessions = _load_json(SESS_FILE)
    for s in sessions["sessions"]:
        if s["id"] == session_id:
            s["ticks"] += 1
            if status == "FOCUSED":
                s["focused"]    += 1
            else:
                s["distracted"] += 1
            break
    _save_json(SESS_FILE, sessions)


# ── Analysis helpers ───────────────────────────────────────────────────────────
def get_today_summary() -> dict:
    """Return aggregated stats for today from the CSV."""
    rows = _read_csv_rows()
    today = datetime.now().date()
    today_rows = [r for r in rows if _parse_ts(r["timestamp"]).date() == today]

    if not today_rows:
        return {"message": "No data for today yet."}

    focused     = [r for r in today_rows if r["status"] == "FOCUSED"]
    distracted  = [r for r in today_rows if r["status"] == "DISTRACTED"]
    scores      = [float(r["focus_score"]) for r in today_rows]
    categories  = Counter(r["category"] for r in distracted)

    return {
        "date":                str(today),
        "total_checks":        len(today_rows),
        "focused_checks":      len(focused),
        "distracted_checks":   len(distracted),
        "focus_pct":           round(len(focused) / len(today_rows) * 100, 1),
        "avg_focus_score":     round(sum(scores) / len(scores), 1),
        "peak_focus_score":    max(scores),
        "min_focus_score":     min(scores),
        "top_distraction":     categories.most_common(1)[0][0] if categories else "none",
        "distraction_breakdown": dict(categories),
    }


def get_weekly_trend() -> list:
    """Return list of daily summaries for the past 7 days."""
    rows  = _read_csv_rows()
    today = datetime.now().date()
    trend = []
    for delta in range(6, -1, -1):
        day  = today - timedelta(days=delta)
        day_rows = [r for r in rows if _parse_ts(r["timestamp"]).date() == day]
        if day_rows:
            focused = sum(1 for r in day_rows if r["status"] == "FOCUSED")
            scores  = [float(r["focus_score"]) for r in day_rows]
            trend.append({
                "date":       str(day),
                "checks":     len(day_rows),
                "focus_pct":  round(focused / len(day_rows) * 100, 1),
                "avg_score":  round(sum(scores) / len(scores), 1),
            })
        else:
            trend.append({"date": str(day), "checks": 0, "focus_pct": 0, "avg_score": 0})
    return trend


def get_lifetime_stats() -> dict:
    return _load_json(STATS_FILE)


def get_best_focus_hour() -> str:
    """Return the hour-of-day (e.g. '14:00') where user is most focused."""
    rows = _read_csv_rows()
    if not rows:
        return "N/A"
    hour_focus: dict[int, list] = {}
    for r in rows:
        h = _parse_ts(r["timestamp"]).hour
        hour_focus.setdefault(h, []).append(1 if r["status"] == "FOCUSED" else 0)
    best = max(hour_focus, key=lambda h: sum(hour_focus[h]) / len(hour_focus[h]))
    return f"{best:02d}:00"


def export_report_txt() -> str:
    """Write a plain-text productivity report and return its path."""
    summary = get_today_summary()
    stats   = get_lifetime_stats()
    trend   = get_weekly_trend()
    path    = os.path.join(BASE_DIR, f"report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt")

    lines = [
        "=" * 60,
        "  FOCUSGUARDIAN AI — PRODUCTIVITY REPORT",
        f"  Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
        "=" * 60,
        "",
        "TODAY'S SUMMARY",
        "-" * 40,
    ]
    for k, v in summary.items():
        lines.append(f"  {k:<28} {v}")

    lines += ["", "LIFETIME STATS", "-" * 40]
    lines.append(f"  {'Total sessions':<28} {stats.get('total_sessions', 0)}")
    focused_h   = stats.get("total_focused_seconds",    0) // 3600
    dist_h      = stats.get("total_distracted_seconds", 0) // 3600
    lines.append(f"  {'Total focused time':<28} {focused_h}h")
    lines.append(f"  {'Total distracted time':<28} {dist_h}h")
    lines.append(f"  {'Max level reached':<28} {stats.get('max_level', 1)}")
    lines.append(f"  {'Total XP earned':<28} {stats.get('total_xp', 0)}")

    lines += ["", "7-DAY TREND", "-" * 40]
    for day in trend:
        lines.append(f"  {day['date']}  focus={day['focus_pct']:5.1f}%  avg_score={day['avg_score']}")

    lines += ["", "=" * 60, "  Keep it up — every focused minute compounds.", "=" * 60]

    with open(path, "w", encoding="utf-8") as fh:
        fh.write("\n".join(lines))

    return path


# ── Internal helpers ───────────────────────────────────────────────────────────
def _load_json(path: str) -> dict:
    with open(path, "r", encoding="utf-8") as fh:
        return json.load(fh)

def _save_json(path: str, data) -> None:
    with open(path, "w", encoding="utf-8") as fh:
        json.dump(data, fh, indent=2)

def _read_csv_rows() -> list:
    if not os.path.exists(LOG_FILE):
        return []
    with open(LOG_FILE, "r", encoding="utf-8") as fh:
        return list(csv.DictReader(fh))

def _parse_ts(ts_str: str) -> datetime:
    try:
        return datetime.fromisoformat(ts_str)
    except Exception:
        return datetime.now()
