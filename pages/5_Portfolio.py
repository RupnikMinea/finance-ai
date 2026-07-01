import streamlit as st

st.set_page_config(page_title='Portfolio Builder', page_icon='🎯', layout='wide')

st.markdown("## 🎯 Portfolio Builder")

st.markdown("""
<div style="background:#0d0d1a;border:1px solid #1e1e3a;border-radius:10px;padding:14px 18px;margin-bottom:16px">
  <b style="color:#b39ddb">What this page shows</b><br>
  <span style="color:#aaa;font-size:13px">
  AI builds an <b>optimal portfolio</b> from the top-ranked scan results. Constraints applied:
  max correlation 0.70 between positions (diversification),
  max 2 stocks per sector,
  Kelly criterion for position sizing,
  max 10 positions total.
  Below you can also build a <b>custom portfolio</b> and see its metrics.
  </span>
</div>
""", unsafe_allow_html=True)

result = st.session_state.get('scan_result')
if result is None:
    st.warning('Run a scan first in **Live Screener**.')
    st.stop()

p = result.portfolio

if not p.tickers:
    st.info('Portfolio not built. Re-run scan.')
    st.stop()

st.markdown('### AI Recommended Portfolio')
c1, c2, c3, c4, c5 = st.columns(5)
c1.metric('Expected Return', f'+{p.expected_return:.1f}%',
          help='Weighted average expected return of all positions over 126 days')
c2.metric('Expected DD',     f'{p.expected_dd:.1f}%',
          help='Weighted average expected drawdown of the portfolio')
c3.metric('Sharpe Est.',     f'{p.sharpe_est:.2f}',
          help='Estimated Sharpe ratio: return / risk. >1.5 = excellent')
c4.metric('Diversification', p.diversification,
          help='Diversification quality: Poor / Moderate / Good / Excellent')
c5.metric('Correlation',     p.correlation_level,
          help='Average pairwise correlation. Low = better diversification')

st.markdown(f'**{p.n_sectors} sectors** · Kelly Exposure: **{p.kelly_exposure:.0f}%**')

st.markdown('### Positions')
cols_per_row = 5
for batch_start in range(0, len(p.tickers), cols_per_row):
    batch = p.tickers[batch_start:batch_start + cols_per_row]
    cols  = st.columns(len(batch))
    for i, ticker in enumerate(batch):
        sig    = result.get(ticker)
        weight = p.weights.get(ticker, 0)
        with cols[i]:
            if sig:
                badge_color = ('#00e676' if sig.rating in ('A+','A') else
                               '#ffeb3b' if sig.rating in ('A-','B+') else '#ff9800')
                st.markdown(f"""
                <div style="background:#12122a;border:1px solid #1e1e3a;
                            border-radius:10px;padding:14px;text-align:center">
                  <div style="font-size:20px;font-weight:700;color:#29b6f6">{ticker}</div>
                  <div style="color:{badge_color};font-size:13px;font-weight:700">{sig.rating}</div>
                  <div style="color:#b39ddb;font-size:24px;font-weight:800">{weight:.0f}%</div>
                  <div style="color:#888;font-size:10px;text-transform:uppercase">Weight</div>
                  <div style="color:#aaa;font-size:11px;margin-top:8px;line-height:1.7">
                    {sig.sector}<br>
                    ER <b style="color:#69f0ae">+{sig.expected_return:.0f}%</b><br>
                    DD <b style="color:#ef9a9a">{sig.expected_dd:.0f}%</b><br>
                    Kelly <b style="color:#b39ddb">{sig.kelly:.0f}%</b>
                  </div>
                </div>""", unsafe_allow_html=True)

st.markdown('---')
st.markdown('### 🛠️ Custom Portfolio')
st.caption('Pick any stocks from scan results and see combined metrics.')

if 'custom_portfolio' not in st.session_state:
    st.session_state['custom_portfolio'] = []

all_tickers = [s.ticker for s in result.stocks]
c_add, c_btn = st.columns([3, 1])
add_ticker = c_add.selectbox('Add stock', [''] + all_tickers, label_visibility='collapsed')
if c_btn.button('+ Add', use_container_width=True):
    if add_ticker and add_ticker not in st.session_state['custom_portfolio']:
        st.session_state['custom_portfolio'].append(add_ticker)
        st.rerun()

custom = st.session_state['custom_portfolio']
if custom:
    st.markdown(f'**{len(custom)} positions** in custom portfolio:')
    rem_cols = st.columns(min(len(custom), 8))
    for i, t in enumerate(custom[:8]):
        if rem_cols[i].button(f'✕ {t}', key=f'rm_{t}'):
            st.session_state['custom_portfolio'].remove(t)
            st.rerun()

    sigs = [result.get(t) for t in custom if result.get(t)]
    if sigs:
        avg_er  = sum(s.expected_return for s in sigs) / len(sigs)
        avg_dd  = sum(s.expected_dd     for s in sigs) / len(sigs)
        avg_k   = sum(s.kelly           for s in sigs) / len(sigs)
        n_sec   = len({s.sector for s in sigs})
        sharpe  = abs(avg_er / avg_dd) if avg_dd != 0 else 0
        cc1, cc2, cc3, cc4 = st.columns(4)
        cc1.metric('Avg Return (ER)', f'+{avg_er:.1f}%')
        cc2.metric('Avg DD',          f'{avg_dd:.1f}%')
        cc3.metric('Sharpe Est.',     f'{sharpe:.2f}')
        cc4.metric('Sectors',         str(n_sec))
else:
    st.info('Select stocks above to build a custom portfolio.')

with st.expander('📖 Parameter Legend', expanded=True):
    st.markdown("""
| Parameter | Meaning |
|---|---|
| **Expected Return** | Weighted average predicted return of all positions over 126 trading days |
| **Expected DD** | Weighted average expected maximum drawdown across positions |
| **Sharpe Est.** | ER / |DD| — return-to-risk estimate. >1.5 = excellent, >1.0 = good |
| **Diversification** | Poor / Moderate / Good / Excellent — quality of sector spread |
| **Kelly Exposure** | Sum of all Kelly position sizes. Higher = more total market exposure |
| **Weight** | Recommended % of portfolio for this position (based on Kelly criterion) |
| **Correlation** | Average pairwise correlation. Low (<0.4) = better diversification |
    """)
