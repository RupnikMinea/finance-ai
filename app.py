import streamlit as st
from datetime import datetime

st.set_page_config(
    page_title='Finance AI Terminal',
    page_icon='📈',
    layout='wide',
    initial_sidebar_state='expanded',
)

# ── CSS ───────────────────────────────────────────────────────────────────────
st.markdown("""
<style>
[data-testid="stSidebar"] { background: #0d0d1a; }
[data-testid="stSidebar"] * { color: #ccc !important; }
.stApp { background: #0a0a14; color: #e0e0e0; }
.main { background: #0a0a14; }

/* KPI cards */
.kpi-card {
    background: #12122a; border: 1px solid #1e1e3a;
    border-radius: 12px; padding: 16px 20px; text-align: center;
}
.kpi-value { font-size: 32px; font-weight: 800; line-height: 1.1; }
.kpi-label { font-size: 12px; color: #888; margin-top: 4px; letter-spacing: .5px; text-transform: uppercase; }

/* Rating badges */
.badge { display:inline-block; padding:3px 10px; border-radius:20px;
         font-weight:700; font-size:13px; letter-spacing:.3px; }
.badge-Aplus  { background:#00e676; color:#000; }
.badge-A      { background:#69f0ae; color:#000; }
.badge-Aminus { background:#b9f6ca; color:#000; }
.badge-Bplus  { background:#ffeb3b; color:#000; }
.badge-B      { background:#ffc107; color:#000; }
.badge-Bminus { background:#ff9800; color:#000; }
.badge-Cplus  { background:#ef5350; color:#fff; }

/* Stock mini cards */
.stock-card {
    background:#12122a; border:1px solid #1e1e3a; border-radius:10px;
    padding:14px 16px; margin-bottom:6px; cursor:pointer;
    transition: border-color .2s;
}
.stock-card:hover { border-color:#29b6f6; }

/* AI Action Center */
.ai-summary {
    background: linear-gradient(135deg, #0d1a2e 0%, #12122a 100%);
    border: 1px solid #1e3a5f; border-radius: 14px;
    padding: 20px 24px; margin-bottom: 20px;
}

/* Market banner */
.market-bull { background:#0a2a1a; border:1px solid #00e676;
               border-radius:10px; padding:10px 18px; display:inline-block; }
.market-bear { background:#2a0a0a; border:1px solid #ef5350;
               border-radius:10px; padding:10px 18px; display:inline-block; }
.market-neut { background:#1a1a1a; border:1px solid #666;
               border-radius:10px; padding:10px 18px; display:inline-block; }

/* Engine bar */
.engine-bar {
    background:#0d0d1a; border:1px solid #1e1e3a; border-radius:8px;
    padding:8px 16px; display:flex; gap:24px; font-size:12px; color:#666;
}
.engine-val { color:#b39ddb; font-weight:600; }

div[data-testid="stDataFrame"] table th {
    background: #1a1a2e !important; color: #b39ddb !important;
}
</style>
""", unsafe_allow_html=True)


# ── Helpers ───────────────────────────────────────────────────────────────────
def badge(rating: str) -> str:
    cls = {'A+':'Aplus','A':'A','A-':'Aminus','B+':'Bplus',
           'B':'B','B-':'Bminus','C+':'Cplus'}.get(rating, 'Cplus')
    return f'<span class="badge badge-{cls}">{rating}</span>'


def generate_ai_summary(result) -> str:
    n_opp      = sum(1 for s in result.stocks if s.confidence >= 60)
    n_high     = sum(1 for s in result.stocks if s.rating in ('A+', 'A'))
    top_picks  = [s.ticker for s in result.stocks[:8] if s.confidence >= 55][:5]
    safe_count = sum(1 for s in result.stocks if s.stable_score >= 65)

    sector_scores: dict[str, list] = {}
    for s in result.stocks:
        sector_scores.setdefault(s.sector, []).append(s.confidence)
    top_sec = sorted(sector_scores, key=lambda k: sum(sector_scores[k])/len(sector_scores[k]), reverse=True)[:2]

    qqq_dir = result.market.qqq_ret
    if qqq_dir > 0.5:
        mood = f'Market is <b style="color:#69f0ae">bullish</b> today (QQQ +{qqq_dir:.1f}%).'
    elif qqq_dir < -0.5:
        mood = f'Market is <b style="color:#ef5350">bearish</b> today (QQQ {qqq_dir:.1f}%).'
    else:
        mood = f'Market is <b style="color:#ffc107">neutral</b> today (QQQ {qqq_dir:+.1f}%).'

    parts = [mood]
    parts.append(f'AI found <b style="color:#29b6f6">{n_opp} opportunities</b>, '
                 f'of which <b style="color:#00e676">{n_high} rated A or A+</b>.')
    if top_sec:
        parts.append(f'Strongest sectors: <b style="color:#b39ddb">{", ".join(top_sec)}</b>.')
    if safe_count:
        parts.append(f'<b style="color:#69f0ae">{safe_count} stocks</b> have a stable profile '
                     f'(low risk + solid return).')
    if top_picks:
        tickers_html = ', '.join(f'<b style="color:#29b6f6">{t}</b>' for t in top_picks)
        parts.append(f"Today's best opportunities: {tickers_html}.")
    return '&nbsp;&nbsp;·&nbsp;&nbsp;'.join(parts)


# ── Session init ──────────────────────────────────────────────────────────────
if 'scan_result' not in st.session_state:
    st.session_state['scan_result'] = None

with st.sidebar:
    st.markdown("## 📈 Finance AI Terminal")
    st.markdown("---")
    if st.session_state['scan_result'] is None:
        from engine.predictor import get_last_results
        cached = get_last_results()
        if cached:
            st.session_state['scan_result'] = cached
            st.success(f"Cache · {cached.last_update.strftime('%d %b %H:%M')}")
    result = st.session_state.get('scan_result')
    if result:
        age_min = int((datetime.now() - result.last_update).total_seconds() / 60)
        st.caption(f"Last scan: {result.last_update.strftime('%d %b %H:%M')} ({age_min}m ago)")
        c1, c2, c3 = st.columns(3)
        c1.metric("Stable", result.n_stable_opp)
        c2.metric("Growth", result.n_growth_opp)
        c3.metric("Risk",   result.n_high_risk)
    st.markdown("---")
    st.markdown("**Navigation**")


# ── No data state ─────────────────────────────────────────────────────────────
if st.session_state['scan_result'] is None:
    st.title("📈 Finance AI Terminal")
    st.info("Ni podatkov. Odpri **Live Screener** in klikni **▶ Run Live Scan**.")
    st.stop()

result = st.session_state['scan_result']

# ── AI Action Center ──────────────────────────────────────────────────────────
summary_text = generate_ai_summary(result)
st.markdown(f"""
<div class="ai-summary">
  <div style="color:#29b6f6;font-size:13px;font-weight:700;letter-spacing:1px;
              margin-bottom:10px">📊 AI ACTION CENTER</div>
  <div style="color:#e0e0e0;font-size:15px;line-height:1.9">{summary_text}</div>
  <div style="color:#555;font-size:11px;margin-top:10px">
    Last scan: {result.last_update.strftime('%d %b %Y · %H:%M')} · {result.n_tickers} tickers · {result.runtime_sec:.0f}s
  </div>
</div>
""", unsafe_allow_html=True)

# ── Market status + KPI cards ─────────────────────────────────────────────────
qqq_r = result.market.qqq_ret
market_cls   = 'market-bull' if qqq_r > 0.3 else ('market-bear' if qqq_r < -0.3 else 'market-neut')
market_emoji = '🟢' if qqq_r > 0.3 else ('🔴' if qqq_r < -0.3 else '🟡')
market_label = 'Bullish' if qqq_r > 0.3 else ('Bearish' if qqq_r < -0.3 else 'Neutral')

n_aplus = sum(1 for s in result.stocks if s.rating in ('A+','A'))
last_scan_str = result.last_update.strftime('%H:%M')

col_mkt, col_opp, col_stable, col_growth, col_risk, col_scan = st.columns(6)

with col_mkt:
    st.markdown(f"""<div class="kpi-card">
      <div class="kpi-value" style="font-size:22px">{market_emoji} {market_label}</div>
      <div class="kpi-label">Today's Market</div>
      <div style="color:#666;font-size:11px;margin-top:4px">QQQ {qqq_r:+.2f}%</div>
    </div>""", unsafe_allow_html=True)

with col_opp:
    st.markdown(f"""<div class="kpi-card">
      <div class="kpi-value" style="color:#29b6f6">{n_aplus}</div>
      <div class="kpi-label">AI A/A+ Picks</div>
      <div style="color:#666;font-size:11px;margin-top:4px">High confidence</div>
    </div>""", unsafe_allow_html=True)

with col_stable:
    st.markdown(f"""<div class="kpi-card">
      <div class="kpi-value" style="color:#69f0ae">{result.n_stable_opp}</div>
      <div class="kpi-label">Stable Picks</div>
      <div style="color:#666;font-size:11px;margin-top:4px">Low risk</div>
    </div>""", unsafe_allow_html=True)

with col_growth:
    st.markdown(f"""<div class="kpi-card">
      <div class="kpi-value" style="color:#ffd700">{result.n_growth_opp}</div>
      <div class="kpi-label">Growth Picks</div>
      <div style="color:#666;font-size:11px;margin-top:4px">High upside</div>
    </div>""", unsafe_allow_html=True)

with col_risk:
    st.markdown(f"""<div class="kpi-card">
      <div class="kpi-value" style="color:#ef5350">{result.n_high_risk}</div>
      <div class="kpi-label">High Risk</div>
      <div style="color:#666;font-size:11px;margin-top:4px">Crash &gt;60%</div>
    </div>""", unsafe_allow_html=True)

with col_scan:
    st.markdown(f"""<div class="kpi-card">
      <div class="kpi-value" style="color:#b39ddb;font-size:24px">{last_scan_str}</div>
      <div class="kpi-label">Last Scan</div>
      <div style="color:#666;font-size:11px;margin-top:4px">{result.n_tickers} tickers</div>
    </div>""", unsafe_allow_html=True)

st.markdown("<div style='margin-top:20px'></div>", unsafe_allow_html=True)

# ── Top 5 stock cards ─────────────────────────────────────────────────────────
st.markdown("### 🏆 Today's Top Picks")
cols = st.columns(5)
for i, sig in enumerate(result.top(5)):
    with cols[i]:
        r_color = ('#00e676' if sig.rating in ('A+','A') else
                   '#ffeb3b' if sig.rating in ('A-','B+') else
                   '#ff9800' if sig.rating == 'B' else '#ef5350')
        st.markdown(f"""
        <div class="stock-card">
          <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:8px">
            <span style="font-size:18px;font-weight:800;color:#29b6f6">{sig.ticker}</span>
            {badge(sig.rating)}
          </div>
          <div style="display:grid;grid-template-columns:1fr 1fr;gap:4px;font-size:12px">
            <div><span style="color:#888">Conf</span><br><b style="color:#ccc">{sig.confidence:.0f}</b></div>
            <div><span style="color:#888">ER</span><br><b style="color:#69f0ae">+{sig.expected_return:.0f}%</b></div>
            <div><span style="color:#888">DD</span><br><b style="color:#ef9a9a">{sig.expected_dd:.0f}%</b></div>
            <div><span style="color:#888">Kelly</span><br><b style="color:#b39ddb">{sig.kelly:.0f}%</b></div>
          </div>
          <div style="color:#555;font-size:10px;margin-top:6px">{sig.sector}</div>
        </div>""", unsafe_allow_html=True)

st.markdown("<div style='margin-top:20px'></div>", unsafe_allow_html=True)

# ── Market metrics ────────────────────────────────────────────────────────────
st.markdown("### 📊 Market Overview")
m1, m2, m3, m4 = st.columns(4)
m1.metric("QQQ", f"${result.market.qqq_price:.0f}", f"{result.market.qqq_ret:+.2f}%")
m2.metric("SPY", f"${result.market.spy_price:.0f}", f"{result.market.spy_ret:+.2f}%")
m3.metric("VIX", f"{result.market.vix:.1f}")
m4.metric("Scan time", f"{result.runtime_sec:.0f}s")

st.markdown("<div style='margin-top:20px'></div>", unsafe_allow_html=True)

# ── AI Engine bar ─────────────────────────────────────────────────────────────
from config import ALL_FEATS, TRAIN_START
st.markdown(f"""
<div class="engine-bar">
  <span>🤖 AI Engine</span>
  <span>Models: <span class="engine-val">4 LGB</span></span>
  <span>Features: <span class="engine-val">{len(ALL_FEATS)}</span></span>
  <span>Train from: <span class="engine-val">{TRAIN_START}</span></span>
  <span>Tickers: <span class="engine-val">{result.n_tickers}</span></span>
  <span>Version: <span class="engine-val">v1.0</span></span>
</div>
""", unsafe_allow_html=True)
