import streamlit as st

st.set_page_config(page_title='Stable AI', page_icon='🛡️', layout='wide')
st.title('🛡️ Stable AI')
st.caption('Stocks with high probability of 15–40% gain AND drawdown < 10%')

result = st.session_state.get('scan_result')
if result is None:
    st.warning('Run a scan first from **Live Screener**.')
    st.stop()

stocks = result.stable
if not stocks:
    st.info('No stocks meet the Stable criteria today.')
    st.stop()

st.markdown(f'**{len(stocks)} stable opportunities** found today')

cols = st.columns(min(len(stocks[:5]), 5))
for i, sig in enumerate(stocks[:5]):
    with cols[i]:
        st.markdown(f"""
        <div style="background:#0d1a12;border:1px solid #1a3a1a;border-radius:12px;padding:18px">
          <div style="font-size:22px;font-weight:700;color:#29b6f6">{sig.ticker}</div>
          <div style="color:#00e676;font-size:26px;font-weight:700">{sig.stable_score:.0f}</div>
          <div style="color:#888;font-size:11px;margin-bottom:10px">Stable Score</div>
          <div style="color:#aaa;font-size:12px">
            Rating <b style="color:#00e676">{sig.rating}</b><br>
            Exp Ret <b style="color:#69f0ae">+{sig.expected_return:.0f}%</b><br>
            Exp DD <b style="color:#ef9a9a">{sig.expected_dd:.0f}%</b><br>
            Sharpe est <b style="color:#b39ddb">{sig.rr:.1f}x</b><br>
            Kelly <b style="color:#b39ddb">{sig.kelly:.0f}%</b>
          </div>
          <div style="margin-top:10px;font-size:11px">
            {''.join(f'<div style="color:#69f0ae">✓ {r}</div>' for r in sig.reasons_pos)}
          </div>
        </div>""", unsafe_allow_html=True)

st.markdown('---')
st.markdown('### All Stable Stocks')
for sig in stocks:
    with st.expander(f'{sig.ticker}  ·  {sig.rating}  ·  Stable {sig.stable_score:.0f}  ·  '
                     f'ER +{sig.expected_return:.0f}%  ·  DD {sig.expected_dd:.0f}%'):
        c1, c2 = st.columns(2)
        c1.metric('Expected Return', f'+{sig.expected_return:.1f}%')
        c1.metric('Expected DD',     f'{sig.expected_dd:.1f}%')
        c1.metric('Kelly',           f'{sig.kelly:.1f}%')
        c2.metric('Stable Score',    f'{sig.stable_score:.0f}')
        c2.metric('Confidence',      f'{sig.confidence:.0f}')
        c2.metric('Crash Risk',      f'{sig.crash_prob:.0f}%')
        if sig.reasons_pos:
            st.markdown('**Why:** ' + ' · '.join(f'✓ {r}' for r in sig.reasons_pos))
