import streamlit as st

st.set_page_config(page_title='Stable AI', page_icon='🛡️', layout='wide')

st.markdown("## 🛡️ Stable AI — Low-Risk Opportunities")

st.markdown("""
<div style="background:#0d1a12;border:1px solid #1a3a1a;border-radius:10px;padding:14px 18px;margin-bottom:16px">
  <b style="color:#69f0ae">What this page shows</b><br>
  <span style="color:#aaa;font-size:13px">
  Stocks with a <b>high Stable Score</b> — the AI expects a gain of +15% to +40% over 126 trading days
  while keeping the max drawdown under 10%. Best suited for conservative investors who want steady
  returns without large swings.
  </span>
</div>
""", unsafe_allow_html=True)

result = st.session_state.get('scan_result')
if result is None:
    st.warning('Run a scan first in **Live Screener**.')
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
          <div style="color:#00e676;font-size:28px;font-weight:800">{sig.stable_score:.0f}</div>
          <div style="color:#888;font-size:11px;margin-bottom:10px;text-transform:uppercase">Stable Score</div>
          <div style="color:#aaa;font-size:12px;line-height:1.8">
            Rating <b style="color:#00e676">{sig.rating}</b><br>
            Exp Return <b style="color:#69f0ae">+{sig.expected_return:.0f}%</b><br>
            Exp DD <b style="color:#ef9a9a">{sig.expected_dd:.0f}%</b><br>
            R/R ratio <b style="color:#b39ddb">{sig.rr:.1f}x</b><br>
            Kelly size <b style="color:#b39ddb">{sig.kelly:.0f}%</b>
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
        c1.metric('Kelly Size',      f'{sig.kelly:.1f}%')
        c2.metric('Stable Score',    f'{sig.stable_score:.0f}')
        c2.metric('AI Confidence',   f'{sig.confidence:.0f}')
        c2.metric('Crash Risk',      f'{sig.crash_prob:.0f}%')
        if sig.reasons_pos:
            st.markdown('**Reasons:** ' + ' · '.join(f'✓ {r}' for r in sig.reasons_pos))

with st.expander('📖 Parameter Legend', expanded=False):
    st.markdown("""
| Parameter | Meaning |
|---|---|
| **Stable Score** | Composite stability score 0–100. Formula: 50% P(safe) + 30% (−DD) + 20% ER |
| **Expected Return (ER)** | Predicted return over the next 126 trading days (~6 months) |
| **Expected DD** | Expected maximum drawdown from peak before horizon end. −8% = stock may dip 8% temporarily |
| **R/R Ratio** | Expected Return / |Expected DD|. 2.0x = double the reward vs risk |
| **Kelly Size** | Recommended position size as % of portfolio (capped at 25%) |
| **Crash Risk** | Probability of a >30% crash within 126 days. Stable stocks should be <30% |
| **AI Confidence** | Overall model confidence 0–100. NOT a probability of profit — measures model agreement |
    """)
