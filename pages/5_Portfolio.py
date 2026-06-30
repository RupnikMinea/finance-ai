import streamlit as st

st.set_page_config(page_title='Portfolio Builder', page_icon='🎯', layout='wide')
st.title('🎯 Portfolio Builder')

result = st.session_state.get('scan_result')
if result is None:
    st.warning('Run a scan first from **Live Screener**.')
    st.stop()

p = result.portfolio

# ── AI Recommended Portfolio ──────────────────────────────────────────────────
st.markdown('### AI Recommended Portfolio')
st.caption('Selected by correlation filter + Kelly weighting. Max 10 positions, max 2/sector, corr < 0.70.')

if not p.tickers:
    st.info('Portfolio not built. Re-run scan.')
    st.stop()

# Portfolio metrics
c1, c2, c3, c4, c5 = st.columns(5)
c1.metric('Expected Return', f'+{p.expected_return:.1f}%')
c2.metric('Expected DD',     f'{p.expected_dd:.1f}%')
c3.metric('Sharpe Est.',     f'{p.sharpe_est:.2f}')
c4.metric('Diversification', p.diversification)
c5.metric('Correlation',     p.correlation_level)

st.markdown(f'**{p.n_sectors} sectors** · Kelly Exposure: **{p.kelly_exposure:.0f}%**')

# ── Position cards ────────────────────────────────────────────────────────────
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
                st.markdown(f"""
                <div style="background:#12122a;border:1px solid #1e1e3a;
                            border-radius:10px;padding:14px;text-align:center">
                  <div style="font-size:18px;font-weight:700;color:#29b6f6">{ticker}</div>
                  <div style="color:#b39ddb;font-size:22px;font-weight:700">{weight:.0f}%</div>
                  <div style="color:#888;font-size:11px">Weight</div>
                  <div style="color:#aaa;font-size:11px;margin-top:6px">
                    {sig.sector}<br>
                    ER <b style="color:#69f0ae">+{sig.expected_return:.0f}%</b><br>
                    Kelly <b style="color:#b39ddb">{sig.kelly:.0f}%</b>
                  </div>
                </div>""", unsafe_allow_html=True)

# ── Custom portfolio builder ───────────────────────────────────────────────────
st.markdown('---')
st.markdown('### Custom Portfolio')
st.caption('Build your own portfolio from scan results.')

if 'custom_portfolio' not in st.session_state:
    st.session_state['custom_portfolio'] = []

all_tickers = [s.ticker for s in result.stocks]
add_ticker  = st.selectbox('Add ticker', [''] + all_tickers, label_visibility='collapsed')
if add_ticker and add_ticker not in st.session_state['custom_portfolio']:
    if st.button(f'+ Add {add_ticker}'):
        st.session_state['custom_portfolio'].append(add_ticker)
        st.rerun()

custom = st.session_state['custom_portfolio']
if custom:
    st.markdown(f'**{len(custom)} positions selected**')
    remove_cols = st.columns(min(len(custom), 6))
    for i, t in enumerate(custom[:6]):
        if remove_cols[i].button(f'✕ {t}', key=f'rm_{t}'):
            st.session_state['custom_portfolio'].remove(t)
            st.rerun()

    # Custom portfolio metrics
    sigs = [result.get(t) for t in custom if result.get(t)]
    if sigs:
        avg_er  = sum(s.expected_return for s in sigs) / len(sigs)
        avg_dd  = sum(s.expected_dd     for s in sigs) / len(sigs)
        avg_k   = sum(s.kelly           for s in sigs) / len(sigs)
        sectors = len({s.sector for s in sigs})
        st.markdown(f"""
        **Custom Portfolio Metrics** (equal weight):
        Exp Return **+{avg_er:.1f}%** · Exp DD **{avg_dd:.1f}%** ·
        Avg Kelly **{avg_k:.1f}%** · Sectors **{sectors}**
        """)
else:
    st.info('Select tickers above to build a custom portfolio.')
