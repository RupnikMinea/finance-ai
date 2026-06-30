import streamlit as st

st.set_page_config(
    page_title='Finance AI Terminal',
    page_icon='📈',
    layout='wide',
    initial_sidebar_state='expanded',
)

# ── Custom CSS ────────────────────────────────────────────────────────────────
st.markdown("""
<style>
[data-testid="stSidebar"] { background: #0d0d1a; }
[data-testid="stSidebar"] * { color: #ccc !important; }
.main { background: #0a0a14; }
.stApp { background: #0a0a14; color: #e0e0e0; }

.metric-card {
    background: #12122a; border: 1px solid #1e1e3a;
    border-radius: 10px; padding: 14px 18px;
}
.rating-A\\+ { color: #00e676; font-weight: 700; font-size: 18px; }
.rating-A   { color: #69f0ae; font-weight: 700; }
.rating-A-  { color: #b9f6ca; font-weight: 600; }
.rating-B\\+ { color: #ffeb3b; font-weight: 600; }
.rating-B   { color: #ffc107; }
.rating-B-  { color: #ff9800; }
.rating-C\\+ { color: #ef5350; }

div[data-testid="stDataFrame"] table th {
    background: #1a1a2e !important; color: #b39ddb !important;
}
</style>
""", unsafe_allow_html=True)

# ── Session state init ────────────────────────────────────────────────────────
if 'scan_result' not in st.session_state:
    st.session_state['scan_result'] = None
if 'selected_ticker' not in st.session_state:
    st.session_state['selected_ticker'] = None

# ── Sidebar ───────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("## 📈 Finance AI Terminal")
    st.markdown("---")

    # Load cached result on startup
    if st.session_state['scan_result'] is None:
        from engine.predictor import get_last_results
        cached = get_last_results()
        if cached:
            st.session_state['scan_result'] = cached
            st.success(f"Cache loaded · {cached.last_update.strftime('%d %b %H:%M')}")

    result = st.session_state.get('scan_result')
    if result:
        age_min = round(((__import__('datetime').datetime.now()
                         - result.last_update).total_seconds()) / 60, 0)
        st.caption(f"Last update: {result.last_update.strftime('%d %b %H:%M')}  "
                   f"({int(age_min)}m ago)")
        cols = st.columns(3)
        cols[0].metric("Stable", result.n_stable_opp)
        cols[1].metric("Growth", result.n_growth_opp)
        cols[2].metric("Risk",   result.n_high_risk)

    st.markdown("---")
    st.markdown("**Navigation**")

# ── Home page ─────────────────────────────────────────────────────────────────
st.title("📈 Finance AI Terminal")
st.markdown("Use the sidebar navigation to access **Live Screener**, **Stable AI**, "
            "**Growth AI**, **Portfolio**, and more.")

if st.session_state['scan_result'] is None:
    st.info("No scan data yet. Open **Live Screener** and click **Run Live Scan**.")
else:
    result = st.session_state['scan_result']
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("QQQ", f"{result.market.qqq_price:.0f}",
              f"{result.market.qqq_ret:+.2f}%")
    c2.metric("SPY", f"{result.market.spy_price:.0f}",
              f"{result.market.spy_ret:+.2f}%")
    c3.metric("VIX", f"{result.market.vix:.1f}")
    c4.metric("Runtime", f"{result.runtime_sec:.0f}s")

    st.markdown("---")
    st.markdown("### Today's Top 5")
    cols = st.columns(5)
    for i, sig in enumerate(result.top(5)):
        with cols[i]:
            color = '#00e676' if sig.rating.startswith('A') else '#ffeb3b'
            st.markdown(f"""
            <div class="metric-card">
              <div style="font-size:20px;font-weight:700;color:#29b6f6">{sig.ticker}</div>
              <div style="color:{color};font-size:16px;font-weight:700">{sig.rating}</div>
              <div style="color:#aaa;font-size:12px">Conf: {sig.confidence:.0f}</div>
              <div style="color:#69f0ae;font-size:12px">ER: +{sig.expected_return:.0f}%</div>
              <div style="color:#ef9a9a;font-size:12px">DD: {sig.expected_dd:.0f}%</div>
            </div>""", unsafe_allow_html=True)
