import streamlit as st

st.set_page_config(page_title='Growth AI', page_icon='🚀', layout='wide')

st.markdown("## 🚀 Growth AI — High-Growth Opportunities")

st.markdown("""
<div style="background:#1a1200;border:1px solid #3a2a00;border-radius:10px;padding:14px 18px;margin-bottom:16px">
  <b style="color:#ffd700">What this page shows</b><br>
  <span style="color:#aaa;font-size:13px">
  Stocks with a <b>high Growth Score</b> — AI sees potential for <b>explosive growth >60%</b> within
  126 trading days. Best for aggressive investors who accept higher risk in exchange for higher upside.
  Note: a high Growth Score often comes with higher Crash Risk.
  </span>
</div>
""", unsafe_allow_html=True)

result = st.session_state.get('scan_result')
if result is None:
    st.warning('Run a scan first in **Live Screener**.')
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
          <div style="color:#ffd700;font-size:28px;font-weight:800">{sig.growth_score:.0f}</div>
          <div style="color:#888;font-size:11px;margin-bottom:10px;text-transform:uppercase">Growth Score</div>
          <div style="color:#aaa;font-size:12px;line-height:1.8">
            Max potential <b style="color:#ffd700">+{sig.max_upside:.0f}%</b><br>
            Exp Return <b style="color:#69f0ae">+{sig.expected_return:.0f}%</b><br>
            Crash Risk <b style="color:#ef9a9a">{sig.crash_prob:.0f}%</b><br>
            Kelly Size <b style="color:#b39ddb">{sig.kelly:.0f}%</b><br>
            Agreement <b style="color:#ccc">{sig.agreement}/4</b>
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
        c1.metric('Max Upside',    f'+{sig.max_upside:.1f}%')
        c1.metric('Exp Return',    f'+{sig.expected_return:.1f}%')
        c1.metric('Crash Risk',    f'{sig.crash_prob:.0f}%')
        c2.metric('Growth Score',  f'{sig.growth_score:.0f}')
        c2.metric('Kelly Size',    f'{sig.kelly:.1f}%')
        c2.metric('Agreement',     f'{sig.agreement}/4')
        if sig.reasons_pos:
            st.markdown('**Reasons:** ' + ' · '.join(f'✓ {r}' for r in sig.reasons_pos))

with st.expander('📖 Parameter Legend', expanded=True):
    st.markdown("""
| Parameter | Meaning |
|---|---|
| **Growth Score** | Composite growth score 0–100. Formula: 50% Max Upside + 30% ER + 20% Kelly |
| **Max Upside** | Best-case scenario prediction — max gain under favorable conditions |
| **Expected Return (ER)** | Average predicted return over 126 days — more realistic than Max Upside |
| **Crash Risk** | Probability of a >30% crash. Growth stocks typically have higher Crash Risk — that's the trade-off |
| **Kelly Size** | Recommended position size (max 25%). Smaller Kelly = more model uncertainty |
| **Agreement** | How many of 4 AI models agree on this opportunity (0–4). 4/4 = full consensus |
    """)
