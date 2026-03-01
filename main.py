


# """
# main.py — FocusGuardian AI
# Main monitoring engine with FocusEngine, session tracking, CLI configuration,
# adaptive countdown escalation, level-up celebrations, and graceful shutdown.
# """

# import os
# import sys
# import time
# import argparse
# import signal
# from datetime import datetime

# from openai_client        import analyze_screenshot, analyze_batch
# from procrastination_event import ProcrastinationEvent, show_popup, _play_sound
# from utils                import (
#     take_screenshots, log_event, send_notification,
#     format_duration, cleanup_screenshots, load_config, save_config,
#     screenshots_disk_mb,
# )
# from analytics            import (
#     start_session, end_session, tick_session,
#     get_today_summary, export_report_txt,
# )

# # ──────────────────────────────────────────────────────────────────────────────
# #  FOCUS ENGINE
# # ──────────────────────────────────────────────────────────────────────────────
# class FocusEngine:
#     """
#     Tracks score, XP, level, streak, and time-based stats.
#     Score: 0–100.  XP grows infinitely.  Level = xp // (level * 100).
#     """

#     # Tunable constants
#     SCORE_FOCUSED_GAIN  =  3
#     SCORE_DISTRACT_LOSS =  8
#     XP_PER_FOCUSED_TICK =  10
#     SCORE_DECAY_INTERVAL= 5   # distraction ticks before extra score penalty kicks in

#     def __init__(self, start_score: int = 100):
#         self.focus_score        = start_score
#         self.level              = 1
#         self.xp                 = 0
#         self.streak             = 0          # consecutive focused ticks
#         self.distraction_streak = 0
#         self.total_focused      = 0          # ticks
#         self.total_distracted   = 0          # ticks
#         self._xp_for_next       = 100

#     # ── Tick updates ──────────────────────────────────────────────────────────
#     def update_focused(self) -> bool:
#         """Returns True if a level-up occurred."""
#         self.focus_score       = min(100, self.focus_score + self.SCORE_FOCUSED_GAIN)
#         self.streak            += 1
#         self.distraction_streak = 0
#         self.total_focused     += 1

#         # Streak bonus XP
#         bonus    = min(self.streak // 3, 5)   # up to +5 extra xp per tick
#         self.xp += self.XP_PER_FOCUSED_TICK + bonus

#         return self._check_level_up()

#     def update_distracted(self) -> None:
#         loss = self.SCORE_DISTRACT_LOSS
#         # Extra penalty for repeat distractions
#         if self.distraction_streak >= self.SCORE_DECAY_INTERVAL:
#             loss += 2
#         self.focus_score       = max(0, self.focus_score - loss)
#         self.distraction_streak += 1
#         self.streak             = 0
#         self.total_distracted  += 1

#     def _check_level_up(self) -> bool:
#         if self.xp >= self._xp_for_next:
#             self.level          += 1
#             self._xp_for_next    = self.level * 100
#             return True
#         return False

#     # ── Derived properties ────────────────────────────────────────────────────
#     @property
#     def focus_pct(self) -> float:
#         total = self.total_focused + self.total_distracted
#         return (self.total_focused / total * 100) if total else 100.0

#     @property
#     def level_progress_pct(self) -> float:
#         base  = (self.level - 1) * 100
#         chunk = self._xp_for_next - base
#         earned= self.xp - base
#         return min(earned / chunk * 100, 100)

#     def snapshot(self, status: str, category: str, reason: str, confidence: float) -> dict:
#         return {
#             "timestamp":   datetime.now().isoformat(timespec="seconds"),
#             "status":      status,
#             "reason":      reason,
#             "confidence":  round(confidence, 3),
#             "category":    category,
#             "focus_score": self.focus_score,
#             "level":       self.level,
#             "xp":          self.xp,
#             "streak":      self.streak,
#         }


# # ──────────────────────────────────────────────────────────────────────────────
# #  DISPLAY HELPERS
# # ──────────────────────────────────────────────────────────────────────────────
# _CYAN   = "\033[96m"
# _GREEN  = "\033[92m"
# _RED    = "\033[91m"
# _YELLOW = "\033[93m"
# _BOLD   = "\033[1m"
# _DIM    = "\033[2m"
# _RST    = "\033[0m"

# def _banner():
#     print(f"""
# {_CYAN}{_BOLD}
#  ███████╗ ██████╗  ██████╗██╗   ██╗███████╗
#  ██╔════╝██╔═══██╗██╔════╝██║   ██║██╔════╝
#  █████╗  ██║   ██║██║     ██║   ██║███████╗
#  ██╔══╝  ██║   ██║██║     ██║   ██║╚════██║
#  ██║     ╚██████╔╝╚██████╗╚██████╔╝███████║
#  ╚═╝      ╚═════╝  ╚═════╝ ╚═════╝ ╚══════╝
#  ██████╗ ██╗   ██╗ █████╗ ██████╗ ██████╗
# ██╔════╝ ██║   ██║██╔══██╗██╔══██╗██╔══██╗
# ██║  ███╗██║   ██║███████║██████╔╝██║  ██║
# ██║   ██║██║   ██║██╔══██║██╔══██╗██║  ██║
# ╚██████╔╝╚██████╔╝██║  ██║██║  ██║██████╔╝
#  ╚═════╝  ╚═════╝ ╚═╝  ╚═╝╚═╝  ╚═╝╚═════╝
# {_RST}{_DIM}  Neural Productivity Monitoring System  v2.0{_RST}
# """)


# def _print_status(engine: FocusEngine, status: str, result: dict, elapsed: str):
#     icon  = f"{_GREEN}●{_RST}" if status == "FOCUSED" else f"{_RED}●{_RST}"
#     score_color = _GREEN if engine.focus_score >= 70 else (_YELLOW if engine.focus_score >= 40 else _RED)

#     bar_filled = int(engine.focus_score / 5)
#     bar = f"{score_color}{'█' * bar_filled}{'░' * (20 - bar_filled)}{_RST}"

#     streak_str = (f" {_YELLOW}🔥×{engine.streak}{_RST}" if engine.streak >= 3 else "")

#     print(f"\n{'─'*60}")
#     print(f"  {icon}  {_BOLD}{status:<12}{_RST}  │  {result['category']:<14}│  conf: {result['confidence']:.0%}")
#     print(f"  Score [{bar}] {score_color}{_BOLD}{engine.focus_score:3d}{_RST}{streak_str}")
#     print(f"  LV {_CYAN}{engine.level}{_RST}  XP {engine.xp}  │  Focus {engine.focus_pct:.1f}%  │  {elapsed}")
#     if result.get("reason"):
#         print(f"  {_DIM}Reason: {result['reason'][:72]}{_RST}")
#     print(f"{'─'*60}")


# def _celebrate_levelup(level: int):
#     print(f"\n  {_YELLOW}{_BOLD}★  LEVEL UP!  You are now Level {level}  ★{_RST}")
#     print(f"  {_DIM}New XP target: {level * 100} XP{_RST}")
#     _play_sound("levelup")
#     send_notification("🔥 Level Up!", f"You've reached Level {level}! Keep it up.")


# # ──────────────────────────────────────────────────────────────────────────────
# #  MAIN LOOP
# # ──────────────────────────────────────────────────────────────────────────────
# def main(
#     delay_time:     int  = 45,
#     countdown_time: int  = 10,
#     user_name:      str  = "User",
#     all_monitors:   bool = False,
#     daily_goal_hrs: float= 4.0,
#     sound_enabled:  bool = True,
#     notify_enabled: bool = True,
# ):
#     _banner()

#     # ── Task input ─────────────────────────────────────────────────────────────
#     print(f"  {_CYAN}Hello, {user_name}!{_RST}  Let's lock in.\n")
#     user_spec = input(f"  {_BOLD}What are you working on today?{_RST}\n  › ").strip()
#     if not user_spec:
#         user_spec = "my task"

#     daily_goal_secs = int(daily_goal_hrs * 3600)

#     # ── Session start ──────────────────────────────────────────────────────────
#     session_id  = start_session(user_spec, user_name)
#     engine      = FocusEngine()
#     start_time  = time.time()
#     tick_count  = 0

#     print(f"\n  {_GREEN}Monitoring started.{_RST}  Press Ctrl+C to stop.\n")
#     if notify_enabled:
#         send_notification("FocusGuardian AI", f"Monitoring started for: {user_spec}")

#     # ── Graceful shutdown on Ctrl+C / SIGTERM ─────────────────────────────────
#     def _shutdown(signum=None, frame=None):
#         elapsed_secs = int(time.time() - start_time)
#         print(f"\n\n  {_YELLOW}Stopping…{_RST}")

#         summary = end_session(session_id, engine.focus_score)
#         today   = get_today_summary()

#         print(f"\n{'═'*60}")
#         print(f"  SESSION SUMMARY")
#         print(f"{'═'*60}")
#         print(f"  Task        : {user_spec}")
#         print(f"  Duration    : {format_duration(elapsed_secs)}")
#         print(f"  Focus score : {engine.focus_score}/100")
#         print(f"  Level       : {engine.level}  │  XP: {engine.xp}")
#         print(f"  Ticks       : {engine.total_focused} focused / {engine.total_distracted} distracted")
#         print(f"  Focus %%    : {engine.focus_pct:.1f}%%")
#         if isinstance(today, dict) and "avg_focus_score" in today:
#             print(f"  Today avg   : {today['avg_focus_score']} / today focus: {today['focus_pct']}%%")

#         # Export report
#         try:
#             rpt = export_report_txt()
#             print(f"\n  Report saved → {rpt}")
#         except Exception:
#             pass

#         deleted = cleanup_screenshots()
#         if deleted:
#             print(f"  Cleaned {deleted} old screenshots.")

#         print(f"\n{'═'*60}")
#         print(f"  {_GREEN}Great session! Keep building the habit.{_RST}")
#         print(f"{'═'*60}\n")

#         sys.exit(0)

#     # signal.signal(signal.SIGINT,  _shutdown)
#     # signal.signal(signal.SIGTERM, _shutdown)

#     import threading

#     if threading.current_thread() is threading.main_thread():
#     signal.signal(signal.SIGINT, _shutdown)
#     signal.signal(signal.SIGTERM, _shutdown)

#     # ── Main monitoring loop ───────────────────────────────────────────────────
#     while True:
#         tick_count   += 1
#         elapsed_secs  = int(time.time() - start_time)
#         elapsed_str   = format_duration(elapsed_secs)

#         # ── Capture screenshot(s) ──────────────────────────────────────────────
#         paths = take_screenshots(all_monitors=all_monitors)
#         if not paths:
#             print(f"  {_YELLOW}[tick {tick_count}] No screenshot captured — skipping.{_RST}")
#             time.sleep(delay_time)
#             continue

#         # ── AI Analysis ────────────────────────────────────────────────────────
#         if len(paths) > 1:
#             result = analyze_batch(paths, user_spec)
#         else:
#             result = analyze_screenshot(paths[0], user_spec)

#         status = result["status"]

#         # ── Update engine ──────────────────────────────────────────────────────
#         if status == "DISTRACTED":
#             engine.update_distracted()
#             tick_session(session_id, "DISTRACTED")

#             # Adaptive countdown: longer if repeated distraction
#             adaptive_cd = countdown_time + (engine.distraction_streak * 5)
#             adaptive_cd = min(adaptive_cd, 120)   # cap at 2 minutes

#             if sound_enabled:
#                 _play_sound("distracted")

#             if notify_enabled:
#                 send_notification(
#                     f"⚠ {user_name}, You're Distracted!",
#                     result.get("reason", "Get back to work.")[:80]
#                 )

#             # Show fullscreen intervention popup (blocks main thread — correct for Windows)
#             try:
#                 show_popup(
#                     user_name=user_name,
#                     reason=result.get("reason", "Distraction detected"),
#                     advice=result.get("advice", "Close distractions and refocus."),
#                     countdown=adaptive_cd,
#                 )
#             except Exception as e:
#                 print(f"  {_DIM}[popup error: {e}]{_RST}")

#         else:  # FOCUSED
#             leveled_up = engine.update_focused()
#             tick_session(session_id, "FOCUSED")

#             if leveled_up:
#                 _celebrate_levelup(engine.level)

#         # ── Log ────────────────────────────────────────────────────────────────
#         snap = engine.snapshot(status, result["category"], result["reason"], result["confidence"])
#         log_event(snap)

#         # ── Terminal output ────────────────────────────────────────────────────
#         _print_status(engine, status, result, elapsed_str)

#         # ── Daily goal check ───────────────────────────────────────────────────
#         focused_secs = engine.total_focused * delay_time
#         if focused_secs >= daily_goal_secs and engine.total_focused > 0:
#             goal_pct = min(focused_secs / daily_goal_secs * 100, 100)
#             if engine.total_focused % 10 == 0:   # remind every 10 focused ticks
#                 print(f"\n  {_GREEN}🎯 Daily Goal: {goal_pct:.0f}% complete  "
#                       f"({format_duration(focused_secs)} / {format_duration(daily_goal_secs)}){_RST}")

#         # ── Disk guard ─────────────────────────────────────────────────────────
#         if tick_count % 20 == 0:
#             mb = screenshots_disk_mb()
#             if mb > 200:
#                 cleanup_screenshots(keep_last=10)

#         time.sleep(delay_time)


# # ──────────────────────────────────────────────────────────────────────────────
# #  ENTRY POINT
# # ──────────────────────────────────────────────────────────────────────────────
# if __name__ == "__main__":
#     # Load saved config as defaults
#     cfg = load_config()

#     parser = argparse.ArgumentParser(
#         description="FocusGuardian AI — Neural Productivity Monitor",
#         formatter_class=argparse.ArgumentDefaultsHelpFormatter,
#     )
#     parser.add_argument("--delay_time",      type=int,   default=cfg["delay_time"],
#                         help="Seconds between each screenshot analysis")
#     parser.add_argument("--countdown_time",  type=int,   default=cfg["countdown_time"],
#                         help="Base seconds for distraction countdown")
#     parser.add_argument("--user_name",       type=str,   default=cfg["user_name"],
#                         help="Your name (shown in popups)")
#     parser.add_argument("--all_monitors",    action="store_true", default=cfg["all_monitors"],
#                         help="Capture all monitors instead of primary only")
#     parser.add_argument("--daily_goal_hours",type=float, default=cfg["daily_goal_hours"],
#                         help="Daily focused-time goal in hours")
#     parser.add_argument("--no_sound",        action="store_true",
#                         help="Disable sound effects")
#     parser.add_argument("--no_notify",       action="store_true",
#                         help="Disable desktop notifications")
#     parser.add_argument("--save_config",     action="store_true",
#                         help="Save these settings as defaults")

#     args = parser.parse_args()

#     if args.save_config:
#         save_config({
#             "delay_time":       args.delay_time,
#             "countdown_time":   args.countdown_time,
#             "user_name":        args.user_name,
#             "all_monitors":     args.all_monitors,
#             "daily_goal_hours": args.daily_goal_hours,
#             "sound_enabled":    not args.no_sound,
#             "notify_enabled":   not args.no_notify,
#         })
#         print(f"  {_GREEN}Config saved!{_RST}")

#     main(
#         delay_time     = args.delay_time,
#         countdown_time = args.countdown_time,
#         user_name      = args.user_name,
#         all_monitors   = args.all_monitors,
#         daily_goal_hrs = args.daily_goal_hours,
#         sound_enabled  = not args.no_sound,
#         notify_enabled = not args.no_notify,
#     )



"""
main.py — FocusGuardian AI
Main monitoring engine with FocusEngine, session tracking,
adaptive countdown escalation, level-up celebrations,
and graceful shutdown.
"""

import sys
import time
import argparse
import signal
from datetime import datetime

from openai_client import analyze_screenshot, analyze_batch
from procrastination_event import show_popup, _play_sound
from utils import (
    take_screenshots,
    log_event,
    send_notification,
    format_duration,
    cleanup_screenshots,
    load_config,
    save_config,
    screenshots_disk_mb,
)
from analytics import (
    start_session,
    end_session,
    tick_session,
    get_today_summary,
    export_report_txt,
)

# ──────────────────────────────────────────────────────────────────────────────
#  FOCUS ENGINE
# ──────────────────────────────────────────────────────────────────────────────
class FocusEngine:
    SCORE_FOCUSED_GAIN = 3
    SCORE_DISTRACT_LOSS = 8
    XP_PER_FOCUSED_TICK = 10
    SCORE_DECAY_INTERVAL = 5

    def __init__(self, start_score: int = 100):
        self.focus_score = start_score
        self.level = 1
        self.xp = 0
        self.streak = 0
        self.distraction_streak = 0
        self.total_focused = 0
        self.total_distracted = 0
        self._xp_for_next = 100

    def update_focused(self) -> bool:
        self.focus_score = min(100, self.focus_score + self.SCORE_FOCUSED_GAIN)
        self.streak += 1
        self.distraction_streak = 0
        self.total_focused += 1

        bonus = min(self.streak // 3, 5)
        self.xp += self.XP_PER_FOCUSED_TICK + bonus

        return self._check_level_up()

    def update_distracted(self):
        loss = self.SCORE_DISTRACT_LOSS
        if self.distraction_streak >= self.SCORE_DECAY_INTERVAL:
            loss += 2

        self.focus_score = max(0, self.focus_score - loss)
        self.distraction_streak += 1
        self.streak = 0
        self.total_distracted += 1

    def _check_level_up(self) -> bool:
        if self.xp >= self._xp_for_next:
            self.level += 1
            self._xp_for_next = self.level * 100
            return True
        return False

    @property
    def focus_pct(self):
        total = self.total_focused + self.total_distracted
        return (self.total_focused / total * 100) if total else 100.0

    def snapshot(self, status, category, reason, confidence):
        return {
            "timestamp": datetime.now().isoformat(timespec="seconds"),
            "status": status,
            "reason": reason,
            "confidence": round(confidence, 3),
            "category": category,
            "focus_score": self.focus_score,
            "level": self.level,
            "xp": self.xp,
            "streak": self.streak,
        }


# ──────────────────────────────────────────────────────────────────────────────
#  MAIN LOOP
# ──────────────────────────────────────────────────────────────────────────────
def main(
    delay_time=45,
    countdown_time=10,
    user_name="User",
    all_monitors=False,
    daily_goal_hrs=4.0,
    sound_enabled=True,
    notify_enabled=True,
):

    print("\nFocusGuardian AI Started\n")

    user_spec = input("What are you working on today?\n> ").strip()
    if not user_spec:
        user_spec = "my task"

    daily_goal_secs = int(daily_goal_hrs * 3600)

    session_id = start_session(user_spec, user_name)
    engine = FocusEngine()
    start_time = time.time()
    tick_count = 0

    print("Monitoring started. Press Ctrl+C to stop.\n")

    if notify_enabled:
        send_notification("FocusGuardian AI", f"Monitoring: {user_spec}")

    # ── Graceful Shutdown ─────────────────────────────────────────────────────
    def shutdown(signum=None, frame=None):
        elapsed_secs = int(time.time() - start_time)

        print("\nStopping session...\n")

        end_session(session_id, engine.focus_score)

        print("Session Summary")
        print("----------------")
        print("Task:", user_spec)
        print("Duration:", format_duration(elapsed_secs))
        print("Focus Score:", engine.focus_score)
        print("Level:", engine.level)
        print("XP:", engine.xp)
        print("Focus %:", round(engine.focus_pct, 1))

        try:
            rpt = export_report_txt()
            print("Report saved:", rpt)
        except:
            pass

        cleanup_screenshots()
        sys.exit(0)

    signal.signal(signal.SIGINT, shutdown)
    signal.signal(signal.SIGTERM, shutdown)

    # ── Monitoring Loop ───────────────────────────────────────────────────────
    while True:
        tick_count += 1
        elapsed_secs = int(time.time() - start_time)

        paths = take_screenshots(all_monitors=all_monitors)
        if not paths:
            time.sleep(delay_time)
            continue

        if len(paths) > 1:
            result = analyze_batch(paths, user_spec)
        else:
            result = analyze_screenshot(paths[0], user_spec)

        status = result["status"]

        if status == "DISTRACTED":
            engine.update_distracted()
            tick_session(session_id, "DISTRACTED")

            adaptive_cd = countdown_time + (engine.distraction_streak * 5)
            adaptive_cd = min(adaptive_cd, 120)

            if sound_enabled:
                _play_sound("distracted")

            if notify_enabled:
                send_notification("Distraction Detected", result.get("reason", ""))

            try:
                show_popup(
                    user_name=user_name,
                    reason=result.get("reason", ""),
                    advice=result.get("advice", ""),
                    countdown=adaptive_cd,
                )
            except:
                pass

        else:
            leveled_up = engine.update_focused()
            tick_session(session_id, "FOCUSED")

            if leveled_up:
                print(f"LEVEL UP! Now Level {engine.level}")
                if sound_enabled:
                    _play_sound("levelup")

        snap = engine.snapshot(
            status,
            result.get("category", "other"),
            result.get("reason", ""),
            result.get("confidence", 0.8),
        )
        log_event(snap)

        focused_secs = engine.total_focused * delay_time
        if focused_secs >= daily_goal_secs:
            print("Daily goal achieved!")

        if tick_count % 20 == 0:
            if screenshots_disk_mb() > 200:
                cleanup_screenshots(keep_last=10)

        time.sleep(delay_time)


# ──────────────────────────────────────────────────────────────────────────────
#  ENTRY POINT
# ──────────────────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    cfg = load_config()

    parser = argparse.ArgumentParser()
    parser.add_argument("--delay_time", type=int, default=cfg["delay_time"])
    parser.add_argument("--countdown_time", type=int, default=cfg["countdown_time"])
    parser.add_argument("--user_name", type=str, default=cfg["user_name"])
    parser.add_argument("--all_monitors", action="store_true", default=cfg["all_monitors"])
    parser.add_argument("--daily_goal_hours", type=float, default=cfg["daily_goal_hours"])
    parser.add_argument("--no_sound", action="store_true")
    parser.add_argument("--no_notify", action="store_true")
    parser.add_argument("--save_config", action="store_true")

    args = parser.parse_args()

    if args.save_config:
        save_config({
            "delay_time": args.delay_time,
            "countdown_time": args.countdown_time,
            "user_name": args.user_name,
            "all_monitors": args.all_monitors,
            "daily_goal_hours": args.daily_goal_hours,
        })

    main(
        delay_time=args.delay_time,
        countdown_time=args.countdown_time,
        user_name=args.user_name,
        all_monitors=args.all_monitors,
        daily_goal_hrs=args.daily_goal_hours,
        sound_enabled=not args.no_sound,
        notify_enabled=not args.no_notify,
    )

