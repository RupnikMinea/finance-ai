import streamlit as st
import pandas as pd

st.set_page_config(page_title='Live Screener', page_icon='📈', layout='wide')

# ── Run Scan ──────────────────────────────────────────────────────────────────
col_title, col_btn = st.columns([4, 1])
col_title.title('📈 Live Screener')

with col_btn:
    st.markdown('<div style="margin-top:14px"></div>', unsafe_allow_html=True)
    run_clicked = st.button('▶ Run Live Scan', type='primary', use_container_width=True)

if run_clicked:
    from engine.predictor import run_scan
    progress_bar = st.progress(0)
    status_text  = st.empty()

    def progress_cb(step: str, pct: int):
        progress_bar.progress(pct / 100)
        status_text.markdown(f'`{step}`')

    try:
        result = run_scan(progress_cb=progress_cb)
        st.session_state['scan_result'] = result
        progress_bar.progress(1.0)
        status_text.success(f'Done in {result.runtime_sec:.0f}s · {result.n_tickers} tickers')
    except Exception as e:
        status_text.error(f'Scan failed: {e}')
        st.stop()

result = st.session_state.get('scan_result')
if result is None:
    st.info('Click **▶ Run Live Scan** to start.')
    st.stop()

# ── Filters ───────────────────────────────────────────────────────────────────
with st.expander('Filters', expanded=False):
    fc1, fc2, fc3, fc4 = st.columns(4)
    min_conf    = fc1.slider('Min Confidence', 0, 100, 0)
    min_stable  = fc2.slider('Min Stable Score', 0, 100, 0)
    min_growth  = fc3.slider('Min Growth Score', 0, 100, 0)
    max_crash   = fc4.slider('Max Crash Risk', 0, 100, 100)
    selected_sectors = st.multiselect(
        'Sectors', sorted({s.sector for s in result.stocks}), default=[]
    )

stocks = result.stocks
stocks = [s for s in stocks if s.confidence >= min_conf]
stocks = [s for s in stocks if s.stable_score >= min_stable]
stocks = [s for s in stocks if s.growth_score >= min_growth]
stocks = [s for s in stocks if s.crash_prob <= max_crash]
if selected_sectors:
    stocks = [s for s in stocks if s.sector in selected_sectors]

st.caption(f'Showing {len(stocks)} of {result.n_tickers} tickers · '
           f'Last update: {result.last_update.strftime("%d %b %H:%M")}')

# ── Screener Table ─────────────────────────────────────────────────────────────
RATING_ORDER = {'A+': 0, 'A': 1, 'A-': 2, 'B+': 3, 'B': 4, 'B-': 5, 'C+': 6}

rows = []
for s in stocks:
    rows.append({
        'Ticker':   s.ticker,
        'Rating':   s.rating,
        'Sector':   s.sector,
        'Conf':     s.confidence,
        'Stable':   s.stable_score,
        'Growth':   s.growth_score,
        'Crash%':   s.crash_prob,
        'Exp Ret':  s.expected_return,
        'Exp DD':   s.expected_dd,
        'CI':       f'{s.ci_low:.0f}–{s.ci_high:.0f}%',
        'Kelly':    s.kelly,
        'Agree':    s.agreement,
        'Portfolio':'★' if s.in_portfolio else '',
    })

df_show = pd.DataFrame(rows)

# Style
def color_rating(val):
    colors = {'A+': '#00e676', 'A': '#69f0ae', 'A-': '#b9f6ca',
              'B+': '#ffeb3b', 'B': '#ffc107', 'B-': '#ff9800', 'C+': '#ef5350'}
    c = colors.get(val, '#aaa')
    return f'color: {c}; font-weight: 700'

def color_return(val):
    if isinstance(val, (int, float)):
        return f'color: {"#00e676" if val > 0 else "#ef5350"}'
    return ''

def color_crash(val):
    if isinstance(val, (int, float)):
        if val >= 70: return 'color: #ef5350; font-weight: 700'
        if val >= 50: return 'color: #ff9800'
    return ''

styled = (df_show.style
          .map(color_rating, subset=['Rating'])
          .map(color_return, subset=['Exp Ret'])
          .map(color_crash,  subset=['Crash%'])
          .format({'Conf': '{:.0f}', 'Stable': '{:.0f}', 'Growth': '{:.0f}',
                   'Crash%': '{:.0f}', 'Exp Ret': '{:+.1f}%',
                   'Exp DD': '{:.1f}%', 'Kelly': '{:.1f}%', 'Agree': '{}/4'}))

st.dataframe(styled, use_container_width=True, height=500,
             column_config={
                 'Ticker':   st.column_config.TextColumn('Ticker', width=70),
                 'Rating':   st.column_config.TextColumn('Rating', width=60),
                 'Conf':     st.column_config.NumberColumn('Conf', format='%.0f', width=55),
                 'Stable':   st.column_config.ProgressColumn('Stable', min_value=0, max_value=100, width=90),
                 'Growth':   st.column_config.ProgressColumn('Growth', min_value=0, max_value=100, width=90),
                 'Crash%':   st.column_config.NumberColumn('Crash%', format='%.0f%%', width=70),
                 'Exp Ret':  st.column_config.NumberColumn('Exp Ret', format='%+.1f%%', width=75),
                 'Kelly':    st.column_config.NumberColumn('Kelly', format='%.1f%%', width=60),
                 'Portfolio':st.column_config.TextColumn('Ptf', width=35),
             })

# ── Stock Detail ──────────────────────────────────────────────────────────────
st.markdown('---')
st.markdown('### Stock Details')

tickers_available = [s.ticker for s in stocks]
selected = st.selectbox('Select ticker', [''] + tickers_available,
                        index=0, label_visibility='collapsed')

if selected:
    sig = result.get(selected)
    if sig is None:
        st.warning('Ticker not found in scan results.')
        st.stop()

    col_left, col_right = st.columns([1, 1])

    with col_left:
        r_color = ('#00e676' if sig.rating in ('A+','A') else
                   '#ffeb3b' if sig.rating in ('A-','B+') else '#ff9800')
        st.markdown(f"""
        <div style="background:#12122a;border:1px solid #1e1e3a;border-radius:12px;padding:20px">
          <div style="display:flex;align-items:center;gap:16px;margin-bottom:16px">
            <span style="font-size:28px;font-weight:700;color:#29b6f6">{sig.ticker}</span>
            <span style="font-size:24px;color:{r_color};font-weight:700">{sig.rating}</span>
            <span style="font-size:13px;color:#888">{sig.sector}</span>
          </div>
          <table style="width:100%;border-collapse:collapse;font-size:14px">
            <tr><td style="color:#888;padding:5px 0">Confidence</td>
                <td style="color:#ccc;font-weight:600">{sig.confidence:.0f}/100</td></tr>
            <tr><td style="color:#888;padding:5px 0">Expected Return</td>
                <td style="color:#69f0ae;font-weight:600">+{sig.expected_return:.1f}%</td></tr>
            <tr><td style="color:#888;padding:5px 0">Range (CI)</td>
                <td style="color:#aaa">{sig.ci_low:.0f}% – {sig.ci_high:.0f}%</td></tr>
            <tr><td style="color:#888;padding:5px 0">Expected DD</td>
                <td style="color:#ef9a9a;font-weight:600">{sig.expected_dd:.1f}%</td></tr>
            <tr><td style="color:#888;padding:5px 0">Max Upside</td>
                <td style="color:#b39ddb">+{sig.max_upside:.1f}%</td></tr>
            <tr><td style="color:#888;padding:5px 0">Reward / Risk</td>
                <td style="color:#ccc">{sig.rr:.2f}x</td></tr>
            <tr><td style="color:#888;padding:5px 0">Kelly</td>
                <td style="color:#b39ddb">{sig.kelly:.1f}%</td></tr>
            <tr><td style="color:#888;padding:5px 0">Stable Score</td>
                <td style="color:#69f0ae">{sig.stable_score:.0f}</td></tr>
            <tr><td style="color:#888;padding:5px 0">Growth Score</td>
                <td style="color:#ffd700">{sig.growth_score:.0f}</td></tr>
            <tr><td style="color:#888;padding:5px 0">Crash Risk</td>
                <td style="color:#ef5350">{sig.crash_prob:.0f}%</td></tr>
            <tr><td style="color:#888;padding:5px 0">Model Agreement</td>
                <td style="color:#ccc">{sig.agreement}/4</td></tr>
          </table>
        </div>""", unsafe_allow_html=True)

    with col_right:
        # Why AI likes it
        pos_html = ''.join(f'<div style="color:#69f0ae;margin:4px 0">✓ {r}</div>'
                           for r in sig.reasons_pos)
        neg_html = ''.join(f'<div style="color:#ef9a9a;margin:4px 0">✗ {r}</div>'
                           for r in sig.reasons_neg)
        st.markdown(f"""
        <div style="background:#12122a;border:1px solid #1e1e3a;border-radius:12px;
                    padding:20px;margin-bottom:16px">
          <div style="color:#b39ddb;font-weight:700;margin-bottom:12px">
            Why AI {'likes' if sig.confidence >= 60 else 'flags'} {sig.ticker}
          </div>
          {pos_html}
          {neg_html if neg_html else ''}
        </div>""", unsafe_allow_html=True)

        # Prediction range bar
        total = sig.ci_high - sig.ci_low
        median_pct = (sig.expected_return - sig.ci_low) / max(total, 1) * 100
        st.markdown(f"""
        <div style="background:#12122a;border:1px solid #1e1e3a;border-radius:12px;padding:20px">
          <div style="color:#b39ddb;font-weight:700;margin-bottom:12px">Prediction Range</div>
          <div style="display:flex;justify-content:space-between;color:#888;font-size:12px">
            <span>Q10: {sig.ci_low:.0f}%</span>
            <span style="color:#69f0ae;font-weight:700">Median: {sig.expected_return:.0f}%</span>
            <span>Q90: {sig.ci_high:.0f}%</span>
          </div>
          <div style="background:#1a1a2e;border-radius:6px;height:10px;margin:8px 0;position:relative">
            <div style="position:absolute;left:{min(max(median_pct,0),100):.0f}%;
                        transform:translateX(-50%);top:-3px;
                        background:#69f0ae;width:4px;height:16px;border-radius:2px"></div>
            <div style="background:linear-gradient(to right,#1a1a3a,#29b6f6,#69f0ae);
                        height:10px;border-radius:6px;opacity:0.4;width:100%"></div>
          </div>
          <div style="color:#aaa;font-size:12px;margin-top:8px">
            Horizon: 126 trading days (~6 months)
          </div>
        </div>""", unsafe_allow_html=True)

# ── Tooltips legend ───────────────────────────────────────────────────────────
with st.expander('Column Glossary', expanded=False):
    st.markdown("""
| Column | Meaning |
|---|---|
| **Rating** | AI composite grade: A+ (strongest) → C+ |
| **Conf** | How confident the model is (not probability of gain) |
| **Stable** | Probability of >15% gain with <10% drawdown |
| **Growth** | Potential for explosive >60% gain |
| **Crash%** | Probability of >30% crash over 126 days |
| **Exp Ret** | Average predicted return over 126 trading days |
| **Exp DD** | Worst expected drawdown before peak |
| **CI** | Confidence interval (Q10–Q90) for Exp Ret |
| **Kelly** | Recommended position size (max 25%) |
| **Agree** | How many of 4 models agree (0–4) |
| **Ptf** | ★ = in recommended portfolio |
    """)
