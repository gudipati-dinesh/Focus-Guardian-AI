




"""
dashboard.py — FocusGuardian AI
Premium Streamlit dashboard: live metrics, trend charts, session history,
weekly analysis, lifetime stats, motivational system, and report export.

Run with:  streamlit run dashboard.py
"""

import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import os
import json
import random
from datetime import datetime, timedelta
from pathlib import Path

BASE_DIR   = os.path.dirname(os.path.abspath(__file__))
LOG_FILE   = os.path.join(BASE_DIR, "focus_log.csv")
SESS_FILE  = os.path.join(BASE_DIR, "sessions.json")
STATS_FILE = os.path.join(BASE_DIR, "lifetime_stats.json")

# ──────────────────────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="FocusGuardian AI",
    page_icon="🧠",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ──────────────────────────────────────────────────────────────────────────────
#  GLOBAL CSS
# ──────────────────────────────────────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Orbitron:wght@400;700;900&family=Rajdhani:wght@300;400;600;700&family=Share+Tech+Mono&display=swap');

:root {
    --cyan:    #00f5ff;
    --green:   #39ff14;
    --red:     #ff2d55;
    --amber:   #ffb800;
    --purple:  #a855f7;
    --bg:      #030712;
    --surface: #0d1117;
    --s2:      #111827;
    --border:  rgba(0,245,255,0.15);
    --glow:    0 0 20px rgba(0,245,255,0.35);
}

html, body, [data-testid="stAppViewContainer"], .main {
    background: var(--bg) !important;
    color: #e2e8f0 !important;
    font-family: 'Rajdhani', sans-serif !important;
}
[data-testid="stAppViewContainer"] {
    background:
        radial-gradient(ellipse 80% 50% at 50% -10%, rgba(0,245,255,0.07) 0%, transparent 55%),
        radial-gradient(ellipse 40% 40% at 90% 85%, rgba(57,255,20,0.05) 0%, transparent 50%),
        var(--bg);
}
[data-testid="stAppViewContainer"]::before {
    content:''; position:fixed; inset:0; pointer-events:none; z-index:999;
    background:repeating-linear-gradient(0deg,transparent,transparent 2px,rgba(0,0,0,0.025) 2px,rgba(0,0,0,0.025) 4px);
}

/* chrome */
#MainMenu,footer,header,[data-testid="stToolbar"],[data-testid="stDecoration"],.stDeployButton{display:none!important}
.block-container{padding:1.5rem 2rem 4rem!important;max-width:1600px!important}
::-webkit-scrollbar{width:4px}
::-webkit-scrollbar-track{background:var(--surface)}
::-webkit-scrollbar-thumb{background:var(--cyan);border-radius:2px}

/* sidebar */
[data-testid="stSidebar"]{background:var(--surface)!important;border-right:1px solid var(--border)!important}
[data-testid="stSidebar"] *{color:#94a3b8!important;font-family:'Rajdhani',sans-serif!important}
[data-testid="stSidebar"] .stSelectbox label,[data-testid="stSidebar"] .stRadio label{color:rgba(0,245,255,0.7)!important;font-family:'Share Tech Mono',monospace!important;font-size:.7rem!important;letter-spacing:2px!important}

/* header */
.hdr-wrap{display:flex;align-items:center;justify-content:space-between;padding:1.2rem 2rem;background:linear-gradient(135deg,rgba(0,245,255,0.06),rgba(0,0,0,0.3));border:1px solid var(--border);border-radius:16px;margin-bottom:1.5rem;position:relative;overflow:hidden}
.hdr-wrap::after{content:'';position:absolute;top:0;left:-100%;width:60%;height:2px;background:linear-gradient(90deg,transparent,var(--cyan),transparent);animation:scanH 3s linear infinite}
@keyframes scanH{to{left:200%}}
.hdr-logo{font-family:'Orbitron',monospace;font-size:1.9rem;font-weight:900;letter-spacing:2px;background:linear-gradient(90deg,var(--cyan),var(--green));-webkit-background-clip:text;-webkit-text-fill-color:transparent}
.hdr-sub{font-family:'Share Tech Mono',monospace;font-size:.7rem;color:rgba(0,245,255,0.5);letter-spacing:3px;text-transform:uppercase;margin-top:2px}
.live-badge{display:flex;align-items:center;gap:8px;padding:6px 16px;background:rgba(57,255,20,0.08);border:1px solid rgba(57,255,20,0.3);border-radius:50px;font-family:'Share Tech Mono',monospace;font-size:.7rem;color:var(--green);letter-spacing:2px}
.live-dot{width:8px;height:8px;border-radius:50%;background:var(--green);box-shadow:0 0 8px var(--green);animation:pulse 1.4s ease-in-out infinite}
@keyframes pulse{0%,100%{transform:scale(1);opacity:1}50%{transform:scale(1.4);opacity:.6}}

/* metric cards */
.metric-grid{display:grid;grid-template-columns:repeat(4,1fr);gap:1rem;margin-bottom:1.5rem}
.mcard{background:var(--surface);border:1px solid var(--border);border-radius:14px;padding:1.4rem 1.6rem;position:relative;overflow:hidden;transition:transform .2s,border-color .2s}
.mcard:hover{transform:translateY(-3px);border-color:rgba(0,245,255,0.4);box-shadow:var(--glow)}
.mcard::before{content:attr(data-icon);position:absolute;top:1rem;right:1.2rem;font-size:2rem;opacity:.12}
.mcard-label{font-family:'Share Tech Mono',monospace;font-size:.65rem;letter-spacing:3px;text-transform:uppercase;color:rgba(0,245,255,0.55);margin-bottom:.5rem}
.mcard-value{font-family:'Orbitron',monospace;font-size:2rem;font-weight:700;color:#fff;line-height:1}
.mcard-delta{font-family:'Share Tech Mono',monospace;font-size:.7rem;margin-top:.5rem}
.mcard-bar{height:3px;border-radius:2px;margin-top:.8rem;background:rgba(255,255,255,.06);overflow:hidden}
.mcard-bar-fill{height:100%;border-radius:2px;transition:width .6s ease}
.xp-bar-wrap{margin-top:.6rem;background:rgba(255,255,255,.05);border-radius:50px;height:6px;overflow:hidden}
.xp-bar-fill{height:100%;border-radius:50px;background:linear-gradient(90deg,var(--cyan),var(--green));transition:width .8s cubic-bezier(.4,0,.2,1)}

/* section label */
.section-label{font-family:'Orbitron',monospace;font-size:.7rem;font-weight:700;letter-spacing:4px;text-transform:uppercase;color:var(--cyan);margin:1.5rem 0 .8rem;display:flex;align-items:center;gap:10px}
.section-label::after{content:'';flex:1;height:1px;background:linear-gradient(90deg,var(--border),transparent)}

/* chart panel */
.chart-panel{background:var(--surface);border:1px solid var(--border);border-radius:14px;padding:1.4rem;margin-bottom:1rem}

/* motivation */
.motivation-wrap{background:linear-gradient(135deg,rgba(57,255,20,.08) 0%,rgba(0,245,255,.06) 100%);border:1px solid rgba(57,255,20,.25);border-radius:14px;padding:1.6rem 2rem;margin-bottom:1.5rem;position:relative;overflow:hidden}
.motivation-wrap::before{content:'';position:absolute;left:0;top:0;bottom:0;width:4px;background:linear-gradient(180deg,var(--green),var(--cyan));border-radius:4px 0 0 4px}
.motivation-quote{font-family:'Rajdhani',sans-serif;font-size:1.25rem;font-weight:600;color:#fff;line-height:1.4}
.motivation-author{font-family:'Share Tech Mono',monospace;font-size:.7rem;color:var(--green);letter-spacing:2px;margin-top:.5rem}

/* alert */
.alert-wrap{background:rgba(255,45,85,.08);border:1px solid rgba(255,45,85,.3);border-radius:14px;padding:1.2rem 1.6rem;margin-bottom:1.5rem;display:flex;align-items:center;gap:14px}
.alert-text{font-family:'Rajdhani',sans-serif;font-size:1rem;font-weight:600;color:var(--red)}

/* activity log */
.log-table{width:100%;border-collapse:collapse}
.log-table th{font-family:'Share Tech Mono',monospace;font-size:.62rem;letter-spacing:3px;color:rgba(0,245,255,.5);text-transform:uppercase;padding:8px 12px;border-bottom:1px solid var(--border);text-align:left}
.log-table td{font-family:'Rajdhani',sans-serif;font-size:.9rem;padding:8px 12px;border-bottom:1px solid rgba(255,255,255,.04)}
.log-table tr:hover td{background:rgba(0,245,255,.03)}
.badge{display:inline-block;padding:2px 10px;border-radius:50px;font-size:.7rem;font-weight:700;font-family:'Share Tech Mono',monospace;letter-spacing:1px}
.badge-focused{background:rgba(57,255,20,.12);color:var(--green);border:1px solid rgba(57,255,20,.3)}
.badge-dist{background:rgba(255,45,85,.12);color:var(--red);border:1px solid rgba(255,45,85,.3)}

/* stat box */
.stat-box{background:var(--surface);border:1px solid var(--border);border-radius:12px;padding:1rem 1.4rem;text-align:center}
.stat-box-val{font-family:'Orbitron',monospace;font-size:1.5rem;color:var(--cyan);font-weight:700}
.stat-box-lbl{font-family:'Share Tech Mono',monospace;font-size:.62rem;letter-spacing:2px;color:rgba(255,255,255,.35);margin-top:.3rem;text-transform:uppercase}

/* buttons */
.stButton>button{background:transparent!important;border:1px solid var(--cyan)!important;color:var(--cyan)!important;font-family:'Orbitron',monospace!important;font-size:.62rem!important;letter-spacing:3px!important;border-radius:8px!important;padding:8px 20px!important;transition:all .2s!important}
.stButton>button:hover{background:rgba(0,245,255,.08)!important;box-shadow:var(--glow)!important}

/* tabs */
button[data-baseweb="tab"]{font-family:'Share Tech Mono',monospace!important;letter-spacing:2px!important;font-size:.72rem!important;color:rgba(0,245,255,.5)!important;background:transparent!important;border:none!important}
button[data-baseweb="tab"][aria-selected="true"]{color:var(--cyan)!important;border-bottom:2px solid var(--cyan)!important}
[data-testid="stTabs"] [role="tablist"]{border-bottom:1px solid var(--border)!important;background:transparent!important;gap:16px!important}

.ring-label{font-family:'Orbitron',monospace;font-size:.62rem;letter-spacing:3px;color:rgba(0,245,255,.55);text-align:center;text-transform:uppercase;margin-top:-.5rem;margin-bottom:.5rem}
</style>
""", unsafe_allow_html=True)

# ──────────────────────────────────────────────────────────────────────────────
#  CONSTANTS
# ──────────────────────────────────────────────────────────────────────────────
DELAY_TIME = 45

QUOTES = [
    ("The secret of getting ahead is getting started.", "Mark Twain"),
    ("Focus is not about saying yes. It's about saying no.", "Steve Jobs"),
    ("Deep work is the superpower of the 21st century.", "Cal Newport"),
    ("Concentrate all your thoughts upon the work at hand.", "Alexander Graham Bell"),
    ("Your focus determines your reality.", "Qui-Gon Jinn"),
    ("It's not that I'm so smart — I just stay with problems longer.", "Einstein"),
    ("Energy flows where attention goes.", "Tony Robbins"),
    ("The successful warrior is the average man, with laser-like focus.", "Bruce Lee"),
]

DISTRACT_MSGS = [
    "Your future self is watching. Don't disappoint them.",
    "Every minute distracted is a minute behind your competition.",
    "Champions train. Legends stay focused.",
    "Reclaim your attention — it's your most valuable asset.",
]

CAT_COLORS = {
    "coding":       "#00f5ff",
    "writing":      "#a855f7",
    "research":     "#3b82f6",
    "design":       "#f97316",
    "social_media": "#ff2d55",
    "video":        "#ff6b6b",
    "messaging":    "#ffb800",
    "shopping":     "#ec4899",
    "gaming":       "#22c55e",
    "news":         "#64748b",
    "other":        "#475569",
}

# ──────────────────────────────────────────────────────────────────────────────
#  DATA HELPERS
# ──────────────────────────────────────────────────────────────────────────────
@st.cache_data(ttl=10)
def load_df() -> pd.DataFrame:
    if not os.path.exists(LOG_FILE):
        return pd.DataFrame()
    try:
        df = pd.read_csv(LOG_FILE)
        if df.empty:
            return df
        df["timestamp"] = pd.to_datetime(df["timestamp"], errors="coerce")
        df = df.dropna(subset=["timestamp"])
        df["focus_score"] = pd.to_numeric(df["focus_score"], errors="coerce").fillna(100)
        return df
    except Exception:
        return pd.DataFrame()


def load_json_safe(path: str, default):
    try:
        if os.path.exists(path):
            with open(path, "r", encoding="utf-8") as fh:
                return json.load(fh)
    except Exception:
        pass
    return default


def level_progress(xp: int, level: int) -> float:
    base   = (level - 1) * 100
    needed = level * 100 - base
    earned = xp - base
    return min(max(earned / needed * 100, 0), 100)


# ──────────────────────────────────────────────────────────────────────────────
#  SIDEBAR
# ──────────────────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("""
    <div style='font-family:"Orbitron",monospace;font-size:.9rem;color:#00f5ff;
                letter-spacing:3px;padding:.5rem 0 1rem;border-bottom:1px solid rgba(0,245,255,.1);
                margin-bottom:1rem'>
      ⬡ FOCUSGUARDIAN
    </div>
    """, unsafe_allow_html=True)

    page = st.radio(
        "NAVIGATION",
        ["Live Dashboard", "Session History", "Weekly Analysis", "Lifetime Stats"],
        label_visibility="visible",
    )

    st.markdown("<br>", unsafe_allow_html=True)
    daily_goal = st.slider("Daily Goal (hours)", 1, 10, 4, key="goal")
    st.markdown("<br>", unsafe_allow_html=True)

    if st.button("⟳  REFRESH DATA"):
        st.cache_data.clear()
        st.rerun()

    st.markdown("<br>", unsafe_allow_html=True)
    st.markdown("""
    <div style='font-family:"Share Tech Mono",monospace;font-size:.6rem;
                color:rgba(255,255,255,.2);letter-spacing:2px;line-height:2'>
      STACK<br>
      Google Gemini 2.5 Flash<br>
      Python · Streamlit · Plotly<br>
      MSS · Tkinter
    </div>
    """, unsafe_allow_html=True)


# ──────────────────────────────────────────────────────────────────────────────
#  HEADER
# ──────────────────────────────────────────────────────────────────────────────
now_str = datetime.now().strftime("%H:%M:%S  ·  %d %b %Y")
st.markdown(f"""
<div class="hdr-wrap">
  <div>
    <div class="hdr-logo">⬡ FOCUSGUARDIAN AI</div>
    <div class="hdr-sub">Neural Productivity Monitoring System · v2.0</div>
  </div>
  <div style="display:flex;gap:12px;align-items:center">
    <div style="font-family:'Share Tech Mono',monospace;font-size:.68rem;
                color:rgba(255,255,255,.3);letter-spacing:2px">{now_str}</div>
    <div class="live-badge"><div class="live-dot"></div>LIVE</div>
  </div>
</div>
""", unsafe_allow_html=True)


# ──────────────────────────────────────────────────────────────────────────────
#  LOAD DATA
# ──────────────────────────────────────────────────────────────────────────────
df = load_df()

if df.empty:
    st.markdown("""
    <div style="text-align:center;padding:6rem 2rem">
      <div style="font-family:'Orbitron',monospace;font-size:3rem;
                  color:rgba(0,245,255,.12);letter-spacing:8px;margin-bottom:1rem">NO SIGNAL</div>
      <div style="font-family:'Share Tech Mono',monospace;color:rgba(255,255,255,.3);
                  letter-spacing:3px;font-size:.78rem">
        Run <span style="color:#00f5ff">python main.py</span> to begin monitoring
      </div>
    </div>
    """, unsafe_allow_html=True)
    st.stop()


# ──────────────────────────────────────────────────────────────────────────────
#  PAGE: LIVE DASHBOARD
# ──────────────────────────────────────────────────────────────────────────────
if page == "Live Dashboard":

    latest   = df.iloc[-1]
    focus_sc = int(latest.get("focus_score", 100))
    level    = int(latest.get("level", 1))
    xp       = int(latest.get("xp", 0))
    streak   = int(latest.get("streak", 0))
    status   = str(latest.get("status", "FOCUSED"))

    focused_rows     = df[df["status"] == "FOCUSED"]
    dist_rows        = df[df["status"] == "DISTRACTED"]
    focused_time     = len(focused_rows) * DELAY_TIME
    distracted_time  = len(dist_rows) * DELAY_TIME
    total_time       = focused_time + distracted_time
    focus_pct        = (focused_time / total_time * 100) if total_time > 0 else 0
    lv_prog          = level_progress(xp, level)

    # Streak from end of log
    streak_live = 0
    for s in reversed(df["status"].tolist()):
        if s == "FOCUSED":
            streak_live += 1
        else:
            break

    # ── Motivation / Alert banner ──────────────────────────────────────────────
    if focus_pct >= 70 or status == "FOCUSED":
        q, a = random.choice(QUOTES)
        emoji = "🟢" if focus_pct >= 85 else "🟡"
        st.markdown(f"""
        <div class="motivation-wrap">
          <div style="font-size:1.4rem;margin-bottom:.4rem;font-family:'Orbitron',monospace;
                      font-size:.85rem;letter-spacing:2px;color:var(--green)">{emoji} YOU'RE IN THE ZONE</div>
          <div class="motivation-quote">"{q}"</div>
          <div class="motivation-author">— {a}</div>
        </div>
        """, unsafe_allow_html=True)
    else:
        warn = random.choice(DISTRACT_MSGS)
        st.markdown(f"""
        <div class="alert-wrap">
          <div style="font-size:1.8rem">⚠️</div>
          <div>
            <div class="alert-text">DISTRACTION PATTERN DETECTED</div>
            <div style="font-family:'Rajdhani';color:rgba(255,255,255,.45);font-size:.9rem;margin-top:2px">{warn}</div>
          </div>
        </div>
        """, unsafe_allow_html=True)

    # ── Metric cards ──────────────────────────────────────────────────────────
    sc_color  = "#39ff14" if focus_sc >= 70 else ("#ffb800" if focus_sc >= 40 else "#ff2d55")
    pct_color = "#39ff14" if focus_pct >= 70 else ("#ffb800" if focus_pct >= 40 else "#ff2d55")

    st.markdown(f"""
    <div class="metric-grid">

      <div class="mcard" data-icon="🧠">
        <div class="mcard-label">Focus Score</div>
        <div class="mcard-value" style="color:{sc_color}">{focus_sc}</div>
        <div class="mcard-delta" style="color:{sc_color}">{'▲ EXCELLENT' if focus_sc>=80 else '▲ ON TRACK' if focus_sc>=60 else '▼ RECOVER'}</div>
        <div class="mcard-bar"><div class="mcard-bar-fill"
          style="width:{focus_sc}%;background:{sc_color};box-shadow:0 0 8px {sc_color}"></div></div>
      </div>

      <div class="mcard" data-icon="🎯">
        <div class="mcard-label">Focus Efficiency</div>
        <div class="mcard-value" style="color:{pct_color}">{focus_pct:.1f}<span style="font-size:.9rem">%</span></div>
        <div class="mcard-delta" style="color:rgba(255,255,255,.4)">{focused_time//60}m focused · {distracted_time//60}m lost</div>
        <div class="mcard-bar"><div class="mcard-bar-fill"
          style="width:{focus_pct}%;background:{pct_color};box-shadow:0 0 8px {pct_color}"></div></div>
      </div>

      <div class="mcard" data-icon="🔥">
        <div class="mcard-label">Level · XP</div>
        <div class="mcard-value" style="color:#00f5ff">LV {level}</div>
        <div class="mcard-delta" style="color:rgba(0,245,255,.5)">{xp} XP  ·  {lv_prog:.0f}% to next</div>
        <div class="xp-bar-wrap"><div class="xp-bar-fill" style="width:{lv_prog:.0f}%"></div></div>
      </div>

      <div class="mcard" data-icon="⚡">
        <div class="mcard-label">Focus Streak</div>
        <div class="mcard-value" style="color:#ffb800">{streak_live}</div>
        <div class="mcard-delta" style="color:rgba(255,184,0,.6)">
          {'🔥 ON FIRE!' if streak_live>=5 else 'consecutive checks'}
        </div>
        <div class="mcard-bar"><div class="mcard-bar-fill"
          style="width:{min(streak_live*10,100)}%;background:#ffb800;box-shadow:0 0 8px #ffb800"></div></div>
      </div>

    </div>
    """, unsafe_allow_html=True)

    # ── Daily goal bar ────────────────────────────────────────────────────────
    goal_secs     = daily_goal * 3600
    goal_progress = min(focused_time / goal_secs * 100, 100)
    goal_color    = "#39ff14" if goal_progress >= 100 else "#00f5ff"
    st.markdown(f"""
    <div class="chart-panel" style="padding:1rem 1.6rem">
      <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:.6rem">
        <div style="font-family:'Share Tech Mono',monospace;font-size:.65rem;letter-spacing:3px;
                    color:rgba(0,245,255,.55);text-transform:uppercase">Daily Goal Progress</div>
        <div style="font-family:'Orbitron',monospace;font-size:.85rem;color:{goal_color}">
          {focused_time//3600}h {(focused_time%3600)//60}m / {daily_goal}h
        </div>
      </div>
      <div style="background:rgba(255,255,255,.05);border-radius:50px;height:8px;overflow:hidden">
        <div style="width:{goal_progress:.1f}%;height:100%;border-radius:50px;
             background:linear-gradient(90deg,{goal_color},{goal_color}88);
             box-shadow:0 0 12px {goal_color};transition:width .8s ease"></div>
      </div>
      <div style="font-family:'Share Tech Mono',monospace;font-size:.62rem;color:rgba(255,255,255,.25);
                  margin-top:.4rem;letter-spacing:2px">{goal_progress:.1f}% COMPLETE</div>
    </div>
    """, unsafe_allow_html=True)

    # ── Charts row 1 ──────────────────────────────────────────────────────────
    st.markdown('<div class="section-label">⬡ &nbsp;PERFORMANCE ANALYTICS</div>', unsafe_allow_html=True)
    c1, c2 = st.columns([1, 2])

    with c1:
        fig_gauge = go.Figure(go.Indicator(
            mode="gauge+number",
            value=focus_pct,
            number={'suffix': '%', 'font': {'family': 'Orbitron', 'size': 32, 'color': '#fff'}},
            gauge={
                'axis': {'range': [0, 100], 'tickfont': {'color': 'rgba(255,255,255,.3)', 'size': 9},
                         'tickcolor': 'rgba(255,255,255,.2)', 'nticks': 6},
                'bar': {'color': '#00f5ff', 'thickness': 0.22},
                'bgcolor': 'rgba(0,0,0,0)', 'borderwidth': 0,
                'steps': [
                    {'range': [0,  40],  'color': 'rgba(255,45,85,.1)'},
                    {'range': [40, 70],  'color': 'rgba(255,184,0,.09)'},
                    {'range': [70, 100], 'color': 'rgba(57,255,20,.09)'},
                ],
                'threshold': {'line': {'color': '#39ff14', 'width': 2},
                              'thickness': 0.8, 'value': 80}
            }
        ))
        fig_gauge.update_layout(
            paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)',
            margin=dict(t=30, b=10, l=30, r=30), height=250, font_color='white',
        )
        st.markdown('<div class="ring-label">Focus Efficiency Ring</div>', unsafe_allow_html=True)
        st.plotly_chart(fig_gauge, use_container_width=True, config={'displayModeBar': False})

    with c2:
        df_plot = df.copy()
        df_plot["color"] = df_plot["status"].apply(lambda x: "#39ff14" if x == "FOCUSED" else "#ff2d55")

        fig_trend = go.Figure()
        fig_trend.add_trace(go.Scatter(
            x=df_plot["timestamp"], y=df_plot["focus_score"],
            fill='tozeroy', fillcolor='rgba(0,245,255,.04)',
            line=dict(color='rgba(0,0,0,0)'), showlegend=False, hoverinfo='skip',
        ))
        fig_trend.add_trace(go.Scatter(
            x=df_plot["timestamp"], y=df_plot["focus_score"],
            mode='lines+markers',
            line=dict(color='#00f5ff', width=2.5, shape='spline'),
            marker=dict(color=df_plot["color"], size=7, line=dict(color='#030712', width=1.5)),
            hovertemplate='<b>%{y}</b> pts<br>%{x}<extra></extra>',
        ))
        fig_trend.add_hline(y=80, line_dash='dot', line_color='rgba(57,255,20,.3)',
                            annotation_text='TARGET', annotation_font_color='#39ff14',
                            annotation_font_size=9)
        fig_trend.update_layout(
            paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)',
            margin=dict(t=20, b=20, l=10, r=20), height=250,
            xaxis=dict(showgrid=False, color='rgba(255,255,255,.25)',
                       tickfont=dict(family='Share Tech Mono', size=9)),
            yaxis=dict(range=[0, 105], showgrid=True, gridcolor='rgba(255,255,255,.05)',
                       color='rgba(255,255,255,.25)', tickfont=dict(family='Share Tech Mono', size=9)),
            showlegend=False, font=dict(color='white'),
        )
        st.markdown('<div class="section-label" style="font-size:.6rem;margin-top:.2rem">Focus Score Over Time</div>', unsafe_allow_html=True)
        st.plotly_chart(fig_trend, use_container_width=True, config={'displayModeBar': False})

    # ── Charts row 2 ──────────────────────────────────────────────────────────
    c3, c4 = st.columns([1, 2])

    with c3:
        fig_pie = go.Figure(go.Pie(
            labels=['Focused', 'Distracted'],
            values=[max(focused_time, 1), max(distracted_time, 1)],
            hole=0.72,
            marker=dict(colors=['#39ff14', '#ff2d55'], line=dict(color='#030712', width=3)),
            textinfo='none',
            hovertemplate='%{label}: %{percent}<extra></extra>',
        ))
        fig_pie.add_annotation(
            text=f"{focus_pct:.0f}%", x=0.5, y=0.55,
            font=dict(family='Orbitron', color='white', size=26), showarrow=False,
        )
        fig_pie.add_annotation(
            text="focused", x=0.5, y=0.38,
            font=dict(family='Share Tech Mono', color='rgba(255,255,255,.35)', size=10), showarrow=False,
        )
        fig_pie.update_layout(
            paper_bgcolor='rgba(0,0,0,0)', margin=dict(t=10, b=10, l=10, r=10),
            height=220, showlegend=True,
            legend=dict(font=dict(family='Rajdhani', color='rgba(255,255,255,.5)', size=11),
                        bgcolor='rgba(0,0,0,0)'),
            font=dict(color='white'),
        )
        st.markdown('<div class="section-label" style="font-size:.6rem;margin-top:.2rem">Time Split</div>', unsafe_allow_html=True)
        st.plotly_chart(fig_pie, use_container_width=True, config={'displayModeBar': False})

    with c4:
        if "category" in df.columns:
            cat_counts = df["category"].value_counts().reset_index()
            cat_counts.columns = ["category", "count"]
            bar_colors = [CAT_COLORS.get(c, "#64748b") for c in cat_counts["category"]]
            fig_cat = go.Figure(go.Bar(
                x=cat_counts["count"], y=cat_counts["category"], orientation='h',
                marker=dict(color=bar_colors, line=dict(color='rgba(0,0,0,0)')),
                hovertemplate='%{y}: %{x} sessions<extra></extra>',
            ))
            fig_cat.update_layout(
                paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)',
                margin=dict(t=10, b=10, l=10, r=20), height=220,
                xaxis=dict(showgrid=True, gridcolor='rgba(255,255,255,.05)',
                           color='rgba(255,255,255,.25)', tickfont=dict(family='Share Tech Mono', size=9)),
                yaxis=dict(color='rgba(255,255,255,.6)', tickfont=dict(family='Rajdhani', size=12)),
                font=dict(color='white'),
            )
            st.markdown('<div class="section-label" style="font-size:.6rem;margin-top:.2rem">Activity Categories</div>', unsafe_allow_html=True)
            st.plotly_chart(fig_cat, use_container_width=True, config={'displayModeBar': False})

    # ── Recent activity log ───────────────────────────────────────────────────
    st.markdown('<div class="section-label">⬡ &nbsp;RECENT ACTIVITY LOG</div>', unsafe_allow_html=True)

    recent = df.tail(12).iloc[::-1].copy()
    rows_html = ""
    for _, row in recent.iterrows():
        s    = str(row.get("status", "FOCUSED")).strip()
        cls  = "badge-focused" if s == "FOCUSED" else "badge-dist"
        ts   = str(row.get("timestamp", ""))[:19]
        cat  = str(row.get("category", "other")).replace("_", " ").title()
        sc   = int(float(row.get("focus_score", 0)))
        sc_c = "#39ff14" if sc >= 70 else ("#ffb800" if sc >= 40 else "#ff2d55")
        # Sanitize reason to prevent breaking HTML rendering
        reason = (str(row.get("reason", ""))
                  .replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
                  .replace('"', "").replace("'", "")[:55])
        rows_html += (
            "<tr>"
            + '<td style="color:rgba(255,255,255,.35);font-size:.72rem">' + ts + "</td>"
            + "<td><span class=\"badge " + cls + "\">" + s + "</span></td>"
            + '<td style="color:rgba(255,255,255,.6)">' + cat + "</td>"
            + '<td style="color:rgba(255,255,255,.4);font-size:.8rem">' + reason + "</td>"
            + "<td><div style=\"display:flex;align-items:center;gap:8px\">"
            + "<div style=\"flex:1;height:4px;background:rgba(255,255,255,.06);border-radius:2px\">"
            + f'<div style="width:{sc}%;height:100%;background:{sc_c};border-radius:2px"></div>'
            + "</div>"
            + f'<span style="font-size:.72rem;color:white;min-width:26px">{sc}</span>'
            + "</div></td></tr>"
        )

    st.markdown(
        '<div class="chart-panel">'
        '<table class="log-table">'
        "<thead><tr>"
        "<th>Timestamp</th><th>Status</th><th>Category</th><th>Reason</th><th>Score</th>"
        "</tr></thead>"
        "<tbody>" + rows_html + "</tbody>"
        "</table></div>",
        unsafe_allow_html=True,
    )


# ──────────────────────────────────────────────────────────────────────────────
#  PAGE: SESSION HISTORY
# ──────────────────────────────────────────────────────────────────────────────
elif page == "Session History":
    st.markdown('<div class="section-label">⬡ &nbsp;SESSION HISTORY</div>', unsafe_allow_html=True)

    sessions_data = load_json_safe(SESS_FILE, {"sessions": []})
    sessions      = sessions_data.get("sessions", [])

    if not sessions:
        st.info("No session history yet. Start main.py to record sessions.")
    else:
        for s in reversed(sessions[-20:]):
            started  = s.get("started", "")[:19]
            ended    = s.get("ended",   "Not ended")
            if ended and ended != "Not ended":
                ended = ended[:19]
            task     = s.get("task",    "Unknown task")
            focused  = s.get("focused", 0)
            dist     = s.get("distracted", 0)
            total    = focused + dist
            pct      = round(focused / total * 100, 1) if total else 0
            score    = s.get("final_score", "—")
            pct_c    = "#39ff14" if pct >= 70 else ("#ffb800" if pct >= 40 else "#ff2d55")

            st.markdown(f"""
            <div class="chart-panel" style="margin-bottom:.8rem">
              <div style="display:flex;justify-content:space-between;align-items:flex-start">
                <div>
                  <div style="font-family:'Rajdhani';font-size:1.05rem;font-weight:600;
                              color:#fff;margin-bottom:.3rem">📋 {task}</div>
                  <div style="font-family:'Share Tech Mono';font-size:.65rem;
                              color:rgba(255,255,255,.3);letter-spacing:2px">
                    {started} → {ended}
                  </div>
                </div>
                <div style="text-align:right">
                  <div style="font-family:'Orbitron';font-size:1.2rem;color:{pct_c};font-weight:700">{pct}%</div>
                  <div style="font-family:'Share Tech Mono';font-size:.62rem;color:rgba(255,255,255,.3)">
                    Score: {score}
                  </div>
                </div>
              </div>
              <div style="display:flex;gap:1.5rem;margin-top:.8rem">
                <div style="font-family:'Rajdhani';font-size:.9rem;color:#39ff14">✓ {focused} focused</div>
                <div style="font-family:'Rajdhani';font-size:.9rem;color:#ff2d55">✗ {dist} distracted</div>
                <div style="font-family:'Rajdhani';font-size:.9rem;color:rgba(255,255,255,.4)">{total} total checks</div>
              </div>
            </div>
            """, unsafe_allow_html=True)


# ──────────────────────────────────────────────────────────────────────────────
#  PAGE: WEEKLY ANALYSIS
# ──────────────────────────────────────────────────────────────────────────────
elif page == "Weekly Analysis":
    st.markdown('<div class="section-label">⬡ &nbsp;7-DAY PERFORMANCE TREND</div>', unsafe_allow_html=True)

    today = datetime.now().date()
    days  = [today - timedelta(days=i) for i in range(6, -1, -1)]

    weekly = []
    for day in days:
        day_rows = df[df["timestamp"].dt.date == day]
        if len(day_rows):
            focused = (day_rows["status"] == "FOCUSED").sum()
            scores  = day_rows["focus_score"].tolist()
            weekly.append({
                "date":       str(day),
                "label":      day.strftime("%a %d"),
                "checks":     len(day_rows),
                "focus_pct":  round(focused / len(day_rows) * 100, 1),
                "avg_score":  round(sum(scores) / len(scores), 1),
            })
        else:
            weekly.append({"date": str(day), "label": day.strftime("%a %d"),
                           "checks": 0, "focus_pct": 0, "avg_score": 0})

    labels    = [d["label"]     for d in weekly]
    pcts      = [d["focus_pct"] for d in weekly]
    scores    = [d["avg_score"] for d in weekly]
    bar_colors= ["#39ff14" if p >= 70 else "#ffb800" if p >= 40 else "#ff2d55" for p in pcts]

    fig_week = go.Figure()
    fig_week.add_trace(go.Bar(
        x=labels, y=pcts, name="Focus %",
        marker=dict(color=bar_colors, line=dict(color='rgba(0,0,0,0)')),
        hovertemplate='%{x}<br>Focus: %{y:.1f}%<extra></extra>',
    ))
    fig_week.add_trace(go.Scatter(
        x=labels, y=scores, name="Avg Score",
        yaxis="y2", mode="lines+markers",
        line=dict(color="#00f5ff", width=2.5),
        marker=dict(size=8, color="#00f5ff"),
        hovertemplate='%{x}<br>Score: %{y:.1f}<extra></extra>',
    ))
    fig_week.update_layout(
        paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)',
        margin=dict(t=20, b=20, l=10, r=60), height=320,
        xaxis=dict(color='rgba(255,255,255,.4)', tickfont=dict(family='Rajdhani', size=12),
                   showgrid=False),
        yaxis=dict(title="Focus %", range=[0, 105],
                   color='rgba(255,255,255,.3)', tickfont=dict(family='Share Tech Mono', size=9),
                   showgrid=True, gridcolor='rgba(255,255,255,.05)'),
        yaxis2=dict(title="Avg Score", range=[0, 105], overlaying='y', side='right',
                    color='rgba(0,245,255,.4)', tickfont=dict(family='Share Tech Mono', size=9),
                    showgrid=False),
        legend=dict(bgcolor='rgba(0,0,0,0)', font=dict(family='Rajdhani', color='rgba(255,255,255,.5)')),
        font=dict(color='white'), barmode='group',
    )
    st.plotly_chart(fig_week, use_container_width=True, config={'displayModeBar': False})

    # Summary stats row
    total_checks = sum(d["checks"]    for d in weekly)
    avg_pct      = sum(pcts) / 7
    best_day     = max(weekly, key=lambda d: d["focus_pct"])["label"]
    worst_day    = min(weekly, key=lambda d: d["focus_pct"] if d["checks"] else 100)["label"]

    c1, c2, c3, c4 = st.columns(4)
    for col, val, lbl in [
        (c1, total_checks, "Total Checks"),
        (c2, f"{avg_pct:.1f}%", "Avg Focus"),
        (c3, best_day,    "Best Day"),
        (c4, worst_day,   "Toughest Day"),
    ]:
        col.markdown(f"""
        <div class="stat-box">
          <div class="stat-box-val">{val}</div>
          <div class="stat-box-lbl">{lbl}</div>
        </div>
        """, unsafe_allow_html=True)


# ──────────────────────────────────────────────────────────────────────────────
#  PAGE: LIFETIME STATS
# ──────────────────────────────────────────────────────────────────────────────
elif page == "Lifetime Stats":
    st.markdown('<div class="section-label">⬡ &nbsp;LIFETIME ACHIEVEMENTS</div>', unsafe_allow_html=True)

    stats     = load_json_safe(STATS_FILE, {})
    foc_h     = stats.get("total_focused_seconds",    0) // 3600
    dist_h    = stats.get("total_distracted_seconds", 0) // 3600
    sessions  = stats.get("total_sessions",           0)
    max_lv    = stats.get("max_level",                1)
    total_xp  = stats.get("total_xp",                0)
    top_cat   = stats.get("top_distraction_category", "N/A")
    max_score = stats.get("max_focus_score",          100)

    cols = st.columns(4)
    stat_items = [
        (f"{foc_h}h", "Total Focused Time", "#39ff14"),
        (f"{dist_h}h","Time Lost",          "#ff2d55"),
        (sessions,    "Sessions",           "#00f5ff"),
        (f"LV {max_lv}", "Peak Level",      "#ffb800"),
    ]
    for col, (val, lbl, color) in zip(cols, stat_items):
        col.markdown(f"""
        <div class="stat-box">
          <div class="stat-box-val" style="color:{color}">{val}</div>
          <div class="stat-box-lbl">{lbl}</div>
        </div>
        """, unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)

    cols2 = st.columns(3)
    for col, (val, lbl, color) in zip(cols2, [
        (total_xp,    "Total XP Earned",        "#a855f7"),
        (top_cat.replace("_"," ").title(), "Top Distraction", "#ff6b6b"),
        (max_score,   "Peak Focus Score",        "#00f5ff"),
    ]):
        col.markdown(f"""
        <div class="stat-box">
          <div class="stat-box-val" style="color:{color}">{val}</div>
          <div class="stat-box-lbl">{lbl}</div>
        </div>
        """, unsafe_allow_html=True)

    # Category all-time breakdown
    all_cats = stats.get("all_categories", {})
    if all_cats:
        st.markdown('<div class="section-label">⬡ &nbsp;ALL-TIME ACTIVITY BREAKDOWN</div>', unsafe_allow_html=True)
        cat_df = pd.DataFrame(list(all_cats.items()), columns=["category", "count"])
        cat_df = cat_df.sort_values("count", ascending=True)
        colors = [CAT_COLORS.get(c, "#64748b") for c in cat_df["category"]]

        fig_all = go.Figure(go.Bar(
            x=cat_df["count"], y=cat_df["category"], orientation='h',
            marker=dict(color=colors), hovertemplate='%{y}: %{x}<extra></extra>',
        ))
        fig_all.update_layout(
            paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)',
            margin=dict(t=10, b=10, l=10, r=20), height=280,
            xaxis=dict(showgrid=True, gridcolor='rgba(255,255,255,.05)',
                       color='rgba(255,255,255,.25)', tickfont=dict(family='Share Tech Mono', size=9)),
            yaxis=dict(color='rgba(255,255,255,.6)', tickfont=dict(family='Rajdhani', size=12)),
            font=dict(color='white'),
        )
        st.plotly_chart(fig_all, use_container_width=True, config={'displayModeBar': False})


# ──────────────────────────────────────────────────────────────────────────────
#  FOOTER
# ──────────────────────────────────────────────────────────────────────────────
st.markdown("""
<div style="margin-top:3rem;border-top:1px solid rgba(0,245,255,.07);
            padding-top:1rem;display:flex;justify-content:space-between;align-items:center">
  <div style="font-family:'Orbitron',monospace;font-size:.58rem;
              color:rgba(0,245,255,.2);letter-spacing:3px">
    ⬡ FOCUSGUARDIAN AI · NEURAL MONITORING SYSTEM · v2.0
  </div>
  <div style="font-family:'Share Tech Mono',monospace;font-size:.58rem;
              color:rgba(255,255,255,.12);letter-spacing:2px">
    POWERED BY GEMINI 2.5 FLASH · BUILT FOR HACKATHON
  </div>
</div>
""", unsafe_allow_html=True)
