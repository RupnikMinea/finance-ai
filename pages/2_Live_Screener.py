import streamlit as st
import pandas as pd

st.set_page_config(page_title='Live Screener', page_icon='📈', layout='wide')

# ── CSS ────────────────────────────────────────────────────────────────────────
st.markdown("""
<style>
.stApp { background: #0a0a14; color: #e0e0e0; }
.badge { display:inline-block; padding:3px 10px; border-radius:20px;
         font-weight:700; font-size:12px; }
.badge-Aplus  { background:#00e676; color:#000; }
.badge-A      { background:#69f0ae; color:#000; }
.badge-Aminus { background:#b9f6ca; color:#000; }
.badge-Bplus  { background:#ffeb3b; color:#000; }
.badge-B      { background:#ffc107; color:#000; }
.badge-Bminus { background:#ff9800; color:#000; }
.badge-Cplus  { background:#ef5350; color:#fff; }
.detail-card {
    background:#12122a; border:1px solid #1e1e3a; border-radius:12px; padding:20px;
}
.metric-row { display:flex; gap:12px; flex-wrap:wrap; margin:8px 0; }
.m-box { background:#0d0d1a; border:1px solid #1e1e3a; border-radius:8px;
         padding:8px 14px; text-align:center; flex:1; min-width:80px; }
.m-val { font-size:18px; font-weight:700; }
.m-lbl { font-size:10px; color:#666; text-transform:uppercase; margin-top:2px; }
.scan-summary {
    background:linear-gradient(135deg,#0a1a2e,#12122a);
    border:1px solid #1e3a5f; border-radius:12px; padding:16px 20px; margin-bottom:16px;
}
.filter-bar {
    background:#0d0d1a; border:1px solid #1e1e3a; border-radius:10px;
    padding:12px 16px; margin-bottom:12px;
}
div[data-testid="stDataFrame"] table th {
    background:#1a1a2e !important; color:#b39ddb !important;
}
</style>
""", unsafe_allow_html=True)


def badge(rating: str) -> str:
    cls = {'A+':'Aplus','A':'A','A-':'Aminus','B+':'Bplus',
           'B':'B','B-':'Bminus','C+':'Cplus'}.get(rating, 'Cplus')
    return f'<span class="badge badge-{cls}">{rating}</span>'


# ── Top bar: title + Quick Actions ────────────────────────────────────────────
col_title, col_actions = st.columns([3, 2])
col_title.markdown("## 📈 Live Screener")

with col_actions:
    st.markdown('<div style="margin-top:6px"></div>', unsafe_allow_html=True)
    qa1, qa2, qa3 = st.columns(3)
    run_clicked = qa1.button('▶ Run Scan', type='primary', use_container_width=True)
    go_portfolio = qa2.button('💼 Portfolio', use_container_width=True)
    export_btn   = qa3.button('📄 Export CSV', use_container_width=True)

# ── Universe selector ──────────────────────────────────────────────────────────
from config import ALL_UNIVERSES, get_universe, SP500_ADD, ETF_LIST, RUSSELL2000_TOP, NASDAQ100

_STATIC_UNIVERSES = ALL_UNIVERSES  # ['NASDAQ-100', 'S&P 500', 'ETFs', 'Russell 2000']
_ALL_OPTION       = 'All US Large & Mid Cap ($5B+)'

_universe_sizes = {
    'NASDAQ-100':   len(NASDAQ100),
    'S&P 500':      len(SP500_ADD),
    'ETFs':         len(ETF_LIST),
    'Russell 2000': len(RUSSELL2000_TOP),
}


def _get_largecap_tickers_cached():
    """Fetch S&P 500 + S&P 400 MidCap once per session (~900 tickers, all $5B+)."""
    if 'us_tickers_all' not in st.session_state:
        with st.spinner("Fetching S&P 500 + S&P 400 MidCap from Wikipedia (~900 stocks, $5B+)..."):
            from engine.universe import fetch_largecap_tickers
            st.session_state['us_tickers_all'] = fetch_largecap_tickers()
    return st.session_state['us_tickers_all']


with st.expander("⚙️ Universe — which stocks to scan", expanded=False):
    # All large/mid cap option
    use_all_us = st.checkbox(
        f"🌍 {_ALL_OPTION}",
        value=st.session_state.get('use_all_us', False),
        help="S&P 500 + S&P 400 MidCap — ~900 US stocks with $5B+ market cap. "
             "Takes ~15–20 min on Railway. Best run locally.",
    )
    st.session_state['use_all_us'] = use_all_us

    if use_all_us:
        _us_tickers = _get_largecap_tickers_cached()
        n_us = len(_us_tickers)
        selected_universes = [_ALL_OPTION]
        st.info(
            f"📊 **{n_us} tickers** — S&P 500 + S&P 400 MidCap (vse $5B+ market cap). "
            "Scan traja ~15–20 min in potrebuje ~2–3 GB RAM.",
        )
        st.session_state['us_tickers_filtered'] = _us_tickers

    else:
        # Static curated universes
        select_all_static = st.checkbox(
            "✅ All curated universes (NASDAQ-100 + S&P 500 + ETFs + Russell 2000)",
            value=st.session_state.get('universe_all', False),
        )
        st.session_state['universe_all'] = select_all_static

        if select_all_static:
            selected_universes = _STATIC_UNIVERSES
        else:
            selected_universes = st.multiselect(
                "Pick universes",
                options=_STATIC_UNIVERSES,
                default=st.session_state.get('selected_universes', ['NASDAQ-100']),
                format_func=lambda u: f"{u}  ({_universe_sizes[u]} stocks)",
                label_visibility='collapsed',
            )
            if not selected_universes:
                selected_universes = ['NASDAQ-100']

        st.session_state['selected_universes'] = selected_universes
        n_total = len(get_universe(selected_universes))
        breakdown = '  +  '.join(f"{u} ({_universe_sizes.get(u, '?')})" for u in selected_universes)
        st.caption(f"**{n_total} tickers total** — {breakdown}")
        if n_total > 300:
            st.warning(f"⚠ {n_total} tickers — ~10–15 min, ~1.5 GB RAM. Run locally.")
        elif n_total > 150:
            st.warning(f"⚠ {n_total} tickers — ~5–8 min, may OOM on Railway.")
        elif n_total > 100:
            st.info(f"ℹ {n_total} tickers — ~3–5 min on Railway.")


def _resolve_tickers() -> list:
    """Return the final ticker list based on current UI state."""
    if st.session_state.get('use_all_us'):
        return st.session_state.get('us_tickers_filtered',
               st.session_state.get('us_tickers_all', []))
    return get_universe(st.session_state.get('selected_universes', ['NASDAQ-100']))


# ── Run Scan logic ─────────────────────────────────────────────────────────────
if run_clicked:
    from engine.predictor import run_scan
    pb = st.progress(0)
    st_txt = st.empty()

    def pcb(step, pct):
        pb.progress(pct / 100)
        st_txt.markdown(f'`{step}`')

    _tickers = _resolve_tickers()

    try:
        result = run_scan(progress_cb=pcb, tickers=_tickers)
        st.session_state['scan_result'] = result
        pb.progress(1.0)
        st_txt.success(f'✅ Scan complete — {result.n_tickers} tickers in {result.runtime_sec:.0f}s')
    except Exception as e:
        st_txt.error(f'Scan failed: {e}')
        st.stop()

result = st.session_state.get('scan_result')
if result is None:
    try:
        from engine.predictor import get_last_results
        result = get_last_results()
        if result is not None:
            st.session_state['scan_result'] = result
    except Exception:
        pass
if result is None:
    st.info('Click **▶ Run Scan** to start.')
    st.stop()

# ── Export ─────────────────────────────────────────────────────────────────────
if export_btn:
    rows_exp = [{'Ticker': s.ticker, 'Rating': s.rating, 'Sector': s.sector,
                 'Confidence': s.confidence, 'Exp Return': s.expected_return,
                 'Exp DD': s.expected_dd, 'Stable': s.stable_score,
                 'Growth': s.growth_score, 'Crash%': s.crash_prob, 'Kelly': s.kelly}
                for s in result.stocks]
    csv = pd.DataFrame(rows_exp).to_csv(index=False)
    st.download_button('⬇ Download CSV', csv, 'finance_ai_scan.csv', 'text/csv')

# ── AI Post-scan summary ───────────────────────────────────────────────────────
n_aplus = sum(1 for s in result.stocks if s.rating in ('A+', 'A'))
n_opp   = sum(1 for s in result.stocks if s.confidence >= 55)
top5    = [s.ticker for s in result.stocks[:6] if s.confidence >= 50][:5]
sector_scores: dict[str, list] = {}
for s in result.stocks:
    sector_scores.setdefault(s.sector, []).append(s.confidence)
top_sec = sorted(sector_scores, key=lambda k: sum(sector_scores[k])/len(sector_scores[k]), reverse=True)[:2]

st.markdown(f"""
<div class="scan-summary">
  <span style="color:#29b6f6;font-weight:700;font-size:13px">📊 AI SUMMARY</span>
  &nbsp;&nbsp;
  <span style="color:#ccc;font-size:14px">
    Najdenih <b style="color:#69f0ae">{n_opp} priložnosti</b>,
    od tega <b style="color:#00e676">{n_aplus} z oceno A/A+</b>.
    {'Sektorji: <b>' + ', '.join(top_sec) + '</b>.' if top_sec else ''}
    {'Top picks: <b style="color:#29b6f6">' + ', '.join(top5) + '</b>.' if top5 else ''}
  </span>
  <span style="color:#555;font-size:11px;float:right">
    {result.last_update.strftime('%d %b · %H:%M')} · {result.n_tickers} tickers
  </span>
</div>
""", unsafe_allow_html=True)

# ── Filter bar (always visible) ───────────────────────────────────────────────
st.markdown('<div class="filter-bar">', unsafe_allow_html=True)
f1, f2, f3, f4, f5, f6 = st.columns([2, 2, 2, 1, 1, 1])
search_q        = f1.text_input('🔍 Search', placeholder='AAPL, NVDA...', label_visibility='collapsed')
sectors_all     = sorted({s.sector for s in result.stocks})
sel_sectors     = f2.multiselect('Sector', sectors_all, placeholder='Sector', label_visibility='collapsed')
rating_filter   = f3.multiselect('Rating', ['A+','A','A-','B+','B','B-','C+'], placeholder='Rating', label_visibility='collapsed')
min_stable      = f4.number_input('Min Stable', 0, 100, 0, step=10, label_visibility='collapsed')
min_growth      = f5.number_input('Min Growth', 0, 100, 0, step=10, label_visibility='collapsed')
ptf_only        = f6.checkbox('Portfolio only')
st.markdown('</div>', unsafe_allow_html=True)

# ── Apply filters ──────────────────────────────────────────────────────────────
stocks = result.stocks
if search_q:
    q = search_q.upper()
    stocks = [s for s in stocks if q in s.ticker or q in s.sector.upper()]
if sel_sectors:
    stocks = [s for s in stocks if s.sector in sel_sectors]
if rating_filter:
    stocks = [s for s in stocks if s.rating in rating_filter]
if min_stable:
    stocks = [s for s in stocks if s.stable_score >= min_stable]
if min_growth:
    stocks = [s for s in stocks if s.growth_score >= min_growth]
if ptf_only:
    stocks = [s for s in stocks if s.in_portfolio]

st.caption(f'Showing {len(stocks)} / {result.n_tickers} · Click a row for details')

# ── Screener table ─────────────────────────────────────────────────────────────
RATING_ORDER = {'A+':0,'A':1,'A-':2,'B+':3,'B':4,'B-':5,'C+':6}

rows = []
for s in stocks:
    stars = '★' * max(0, 5 - RATING_ORDER.get(s.rating, 6))
    rows.append({
        'Stars':  stars,
        'Ticker': s.ticker,
        'Rating': s.rating,
        'Sector': s.sector,
        'Conf':   round(s.confidence),
        'Stable': round(s.stable_score),
        'Growth': round(s.growth_score),
        'Crash%': round(s.crash_prob),
        'ER%':    round(s.expected_return, 1),
        'DD%':    round(s.expected_dd, 1),
        'Kelly':  round(s.kelly, 1),
        'Agree':  s.agreement,
        '💼':     '●' if s.in_portfolio else '',
    })

df = pd.DataFrame(rows)

def color_rating(v):
    c = {'A+':'#00e676','A':'#69f0ae','A-':'#b9f6ca',
         'B+':'#ffeb3b','B':'#ffc107','B-':'#ff9800','C+':'#ef5350'}.get(v,'#aaa')
    return f'color:{c};font-weight:700'

def color_er(v):
    if isinstance(v, float): return f'color:{"#69f0ae" if v>0 else "#ef5350"}'
    return ''

def color_crash(v):
    if isinstance(v, (int,float)):
        if v >= 70: return 'color:#ef5350;font-weight:700'
        if v >= 50: return 'color:#ff9800'
        if v <= 25: return 'color:#69f0ae'
    return ''

styled = (df.style
          .map(color_rating, subset=['Rating'])
          .map(color_er,     subset=['ER%'])
          .map(color_crash,  subset=['Crash%'])
          .format({'ER%': '{:+.1f}%', 'DD%': '{:.1f}%',
                   'Kelly': '{:.1f}%', 'Agree': '{}/4',
                   'Conf': '{:.0f}', 'Stable': '{:.0f}',
                   'Growth': '{:.0f}', 'Crash%': '{:.0f}'}))

event = st.dataframe(
    styled,
    use_container_width=True,
    height=420,
    on_select='rerun',
    selection_mode='single-row',
    column_config={
        'Stars':  st.column_config.TextColumn('★', width=60),
        'Ticker': st.column_config.TextColumn('Ticker', width=70),
        'Rating': st.column_config.TextColumn('Rating', width=65),
        'Conf':   st.column_config.ProgressColumn('Conf', min_value=0, max_value=100, width=85),
        'Stable': st.column_config.ProgressColumn('Stable', min_value=0, max_value=100, width=85),
        'Growth': st.column_config.ProgressColumn('Growth', min_value=0, max_value=100, width=85),
        'Crash%': st.column_config.NumberColumn('Crash%', format='%.0f%%', width=70),
        'ER%':    st.column_config.NumberColumn('ER 6m', format='%+.1f%%', width=80),
        'Kelly':  st.column_config.NumberColumn('Kelly', format='%.1f%%', width=65),
        'Agree':  st.column_config.NumberColumn('Agree', format='%d/4', width=60, help='Koliko modelov se strinja (0–4)'),
        '💼':     st.column_config.TextColumn('Ptf', width=35, help='Del priporočenega portfelja'),
    }
)

# ── Stock detail panel (click on row) ─────────────────────────────────────────
selected_ticker = None
if event and event.selection and event.selection.rows:
    idx = event.selection.rows[0]
    if idx < len(stocks):
        selected_ticker = stocks[idx].ticker

# Fallback: selectbox
if not selected_ticker:
    sel_sb = st.selectbox(
        'Ali izberi ročno:', [''] + [s.ticker for s in stocks],
        index=0, label_visibility='visible'
    )
    if sel_sb:
        selected_ticker = sel_sb

# ── Column glossary ────────────────────────────────────────────────────────────
with st.expander('📖 Column Legend', expanded=True):
    st.markdown("""
| Column | Meaning |
|---|---|
| **★** | AI stars: ★★★★★ = A+, ★★★★ = A, ★★★ = A−, ★★ = B+, ★ = B |
| **Rating** | AI composite grade: A+ (strongest) → C+ (weakest) |
| **Conf** | Overall AI confidence 0–100. NOT a probability of profit — measures model consensus |
| **Stable** | Score for stable, low-risk return profile. >60 = good stable candidate |
| **Growth** | Score for explosive upside potential. >60 = high-growth candidate |
| **Crash%** | Probability of a >30% crash within 126 trading days |
| **ER 6m** | Average predicted return over 126 trading days (~6 months) |
| **DD%** | Expected maximum drawdown from peak before horizon end |
| **Kelly** | Recommended position size as % of portfolio (capped at 25%) |
| **Agree** | How many of 4 AI models agree on this signal (0 = none, 4 = all) |
| **Ptf** | ● = included in AI recommended portfolio |
    """)

# ── Detail panel ───────────────────────────────────────────────────────────────
if selected_ticker:
    sig = result.get(selected_ticker)
    if sig is None:
        st.warning('Ticker ne najdem v rezultatih.')
        st.stop()

    st.markdown('---')

    # Header
    badge_html = badge(sig.rating)
    r_color = ('#00e676' if sig.rating in ('A+','A') else
               '#ffeb3b' if sig.rating in ('A-','B+') else
               '#ff9800' if sig.rating == 'B' else '#ef5350')

    st.markdown(f"""
    <div style="display:flex;align-items:center;gap:16px;margin-bottom:16px">
      <span style="font-size:32px;font-weight:800;color:#29b6f6">{sig.ticker}</span>
      {badge_html}
      <span style="color:#888;font-size:14px">{sig.sector}</span>
      {'<span style="color:#69f0ae;font-size:12px;background:#0a2a1a;padding:3px 10px;border-radius:20px">💼 In Portfolio</span>' if sig.in_portfolio else ''}
    </div>
    """, unsafe_allow_html=True)

    col_left, col_mid, col_right = st.columns([1, 1, 1])

    # Metrics
    with col_left:
        st.markdown('<div class="detail-card">', unsafe_allow_html=True)
        st.markdown(f"""
        <div class="metric-row">
          <div class="m-box">
            <div class="m-val" style="color:#29b6f6">{sig.confidence:.0f}</div>
            <div class="m-lbl">Confidence</div>
          </div>
          <div class="m-box">
            <div class="m-val" style="color:#69f0ae">+{sig.expected_return:.0f}%</div>
            <div class="m-lbl">Exp Return</div>
          </div>
          <div class="m-box">
            <div class="m-val" style="color:#ef9a9a">{sig.expected_dd:.0f}%</div>
            <div class="m-lbl">Exp DD</div>
          </div>
        </div>
        <div class="metric-row">
          <div class="m-box">
            <div class="m-val" style="color:#b39ddb">{sig.kelly:.0f}%</div>
            <div class="m-lbl">Kelly</div>
          </div>
          <div class="m-box">
            <div class="m-val" style="color:#ffd700">{sig.max_upside:.0f}%</div>
            <div class="m-lbl">Max Upside</div>
          </div>
          <div class="m-box">
            <div class="m-val" style="color:#ccc">{sig.rr:.1f}x</div>
            <div class="m-lbl">R/R</div>
          </div>
        </div>
        <div class="metric-row">
          <div class="m-box">
            <div class="m-val" style="color:#69f0ae">{sig.stable_score:.0f}</div>
            <div class="m-lbl">Stable</div>
          </div>
          <div class="m-box">
            <div class="m-val" style="color:#ffd700">{sig.growth_score:.0f}</div>
            <div class="m-lbl">Growth</div>
          </div>
          <div class="m-box">
            <div class="m-val" style="color:#ef5350">{sig.crash_prob:.0f}%</div>
            <div class="m-lbl">Crash%</div>
          </div>
        </div>
        <div style="color:#555;font-size:12px;margin-top:8px">
          Model agreement: <b style="color:#ccc">{sig.agreement}/4</b> &nbsp;·&nbsp;
          CI: <b style="color:#ccc">{sig.ci_low:.0f}%–{sig.ci_high:.0f}%</b>
        </div>
        """, unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)

    # Why AI likes it
    with col_mid:
        pos_html = ''.join(
            f'<div style="color:#69f0ae;padding:5px 0;border-bottom:1px solid #1a1a2e">✓ {r}</div>'
            for r in sig.reasons_pos
        )
        neg_html = ''.join(
            f'<div style="color:#ef9a9a;padding:5px 0;border-bottom:1px solid #1a1a2e">✗ {r}</div>'
            for r in sig.reasons_neg
        )
        st.markdown(f"""
        <div class="detail-card">
          <div style="color:#b39ddb;font-weight:700;margin-bottom:12px;font-size:14px">
            🤖 Why AI {'rates' if sig.confidence >= 60 else 'flags'} {sig.ticker}
          </div>
          {pos_html or '<div style="color:#555;font-size:12px">No positive signals</div>'}
          {neg_html}
        </div>
        """, unsafe_allow_html=True)

    # Prediction range
    with col_right:
        total = sig.ci_high - sig.ci_low
        med_pct = (sig.expected_return - sig.ci_low) / max(total, 1) * 100
        st.markdown(f"""
        <div class="detail-card">
          <div style="color:#b39ddb;font-weight:700;margin-bottom:16px;font-size:14px">
            📊 Prediction Range (6M)
          </div>
          <div style="display:flex;justify-content:space-between;color:#888;font-size:12px;margin-bottom:8px">
            <span>Q10: {sig.ci_low:.0f}%</span>
            <span style="color:#69f0ae;font-weight:700">⟨ {sig.expected_return:.0f}% ⟩</span>
            <span>Q90: {sig.ci_high:.0f}%</span>
          </div>
          <div style="background:#1a1a2e;border-radius:6px;height:12px;margin:8px 0;position:relative">
            <div style="background:linear-gradient(to right,#1a1a3a,#29b6f6,#69f0ae);
                        height:12px;border-radius:6px;opacity:0.5;width:100%"></div>
            <div style="position:absolute;left:{min(max(med_pct,2),98):.0f}%;
                        transform:translateX(-50%);top:-4px;
                        background:#69f0ae;width:4px;height:20px;border-radius:2px"></div>
          </div>
          <div style="margin-top:20px">
            <div style="color:#888;font-size:11px;margin-bottom:6px">DAILY METRICS</div>
            <div style="display:flex;gap:12px;font-size:12px">
              <div><span style="color:#666">RS 1M</span><br>
                   <b style="color:{'#69f0ae' if sig.rs_1m > 0 else '#ef5350'}">{sig.rs_1m:+.1f}%</b></div>
              <div><span style="color:#666">RS 3M</span><br>
                   <b style="color:{'#69f0ae' if sig.rs_3m > 0 else '#ef5350'}">{sig.rs_3m:+.1f}%</b></div>
              <div><span style="color:#666">Vol 20d $</span><br>
                   <b style="color:#ccc">{sig.dollar_vol_20d/1e6:.0f}M</b></div>
              <div><span style="color:#666">Days∆ATH</span><br>
                   <b style="color:#ccc">{sig.days_since_ath:.0f}</b></div>
            </div>
          </div>
        </div>
        """, unsafe_allow_html=True)
