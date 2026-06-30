import streamlit as st

st.set_page_config(page_title='Growth AI', page_icon='🚀', layout='wide')
st.title('🚀 Growth AI')
st.caption('Stocks with highest explosive growth potential (Max Upside > 60%)')

result = st.session_state.get('scan_result')
if result is None:
    st.warning('Run a scan first from **Live Screener**.')
    st.stop()

stocks = result.growth
if not stocks:
    st.info('No stocks meet the Growth criteria today.')
    st.stop()

st.markdown(f'**{len(stocks)} growth opportunities** found today')

cols = st.columns(min(len(stocks[:5]), 5))
for i, sig in enumerate(stocks[:5]):
    with cols[i]:
        st.markdown(f"""
        <div style="background:#1a1200;border:1px solid #3a2a00;border-radius:12px;padding:18px">
          <div style="font-size:22px;font-weight:700;color:#29b6f6">{sig.ticker}</div>
          <div style="color:#ffd700;font-size:26px;font-weight:700">{sig.growth_score:.0f}</div>
          <div style="color:#888;font-size:11px;margin-bottom:10px">Growth Score</div>
          <div style="color:#aaa;font-size:12px">
            Potential <b style="color:#ffd700">+{sig.max_upside:.0f}%</b><br>
            Exp Ret <b style="color:#69f0ae">+{sig.expected_return:.0f}%</b><br>
            Crash Risk <b style="color:#ef9a9a">{sig.crash_prob:.0f}%</b><br>
            Kelly <b style="color:#b39ddb">{sig.kelly:.0f}%</b>
          </div>
          <div style="margin-top:10px;font-size:11px">
            {''.join(f'<div style="color:#ffd700">✓ {r}</div>' for r in sig.reasons_pos)}
          </div>
        </div>""", unsafe_allow_html=True)

st.markdown('---')
st.markdown('### All Growth Stocks')
for sig in stocks:
    with st.expander(f'{sig.ticker}  ·  Growth {sig.growth_score:.0f}  ·  '
                     f'Potential +{sig.max_upside:.0f}%  ·  Crash {sig.crash_prob:.0f}%'):
        c1, c2 = st.columns(2)
        c1.metric('Max Upside',     f'+{sig.max_upside:.1f}%')
        c1.metric('Expected Return',f'+{sig.expected_return:.1f}%')
        c1.metric('Crash Risk',     f'{sig.crash_prob:.0f}%')
        c2.metric('Growth Score',   f'{sig.growth_score:.0f}')
        c2.metric('Kelly',          f'{sig.kelly:.1f}%')
        c2.metric('Agreement',      f'{sig.agreement}/4')
