import streamlit as st

st.set_page_config(page_title='Dashboard', page_icon='🏠', layout='wide')

result = st.session_state.get('scan_result')

st.title('🏠 Dashboard')

if result is None:
    st.warning('No scan data. Go to **Live Screener** and run a scan first.')
    st.stop()

# ── Market Row ────────────────────────────────────────────────────────────────
st.markdown('### Market Overview')
m = result.market
c1, c2, c3, c4, c5 = st.columns(5)
c1.metric('QQQ',  f'${m.qqq_price:.0f}',  f'{m.qqq_ret:+.2f}%')
c2.metric('SPY',  f'${m.spy_price:.0f}',  f'{m.spy_ret:+.2f}%')
c3.metric('VIX',  f'{m.vix:.1f}',
          delta_color='inverse')
c4.metric('Stable opp', result.n_stable_opp)
c5.metric('Growth opp', result.n_growth_opp)

st.markdown('---')

# ── AI Market Score ───────────────────────────────────────────────────────────
st.markdown('### AI Market Status')

# Simple market score from top stocks' average confidence
avg_conf = sum(s.confidence for s in result.stocks[:20]) / max(len(result.stocks[:20]), 1)
avg_stable = sum(s.stable_score for s in result.stocks[:20]) / max(len(result.stocks[:20]), 1)
avg_crash  = sum(s.crash_prob for s in result.stocks[:20]) / max(len(result.stocks[:20]), 1)

market_score = round(avg_conf * 0.5 + avg_stable * 0.3 + (100 - avg_crash) * 0.2)
mood = 'Bullish' if market_score >= 65 else ('Neutral' if market_score >= 45 else 'Bearish')
mood_color = '#00e676' if market_score >= 65 else ('#ffeb3b' if market_score >= 45 else '#ef5350')

col_score, col_dims = st.columns([1, 2])
with col_score:
    st.markdown(f"""
    <div style="background:#12122a;border:1px solid #1e1e3a;border-radius:14px;
                padding:28px;text-align:center">
      <div style="font-size:13px;color:#888;margin-bottom:4px">AI MARKET SCORE</div>
      <div style="font-size:64px;font-weight:700;color:{mood_color}">{market_score}</div>
      <div style="font-size:20px;color:{mood_color};margin-top:4px">{mood}</div>
    </div>""", unsafe_allow_html=True)

with col_dims:
    trend_score  = min(100, int(avg_conf))
    safety_score = min(100, int(avg_stable))
    risk_score   = min(100, int(100 - avg_crash))
    dims = [('Trend', trend_score), ('Safety', safety_score), ('Risk', risk_score)]
    for label, score in dims:
        filled = int(score / 20)
        stars  = '★' * filled + '☆' * (5 - filled)
        color  = '#00e676' if score >= 70 else ('#ffeb3b' if score >= 50 else '#ef5350')
        st.markdown(f"""
        <div style="margin:10px 0">
          <span style="color:#888;width:80px;display:inline-block">{label}</span>
          <span style="color:{color};font-size:18px;letter-spacing:2px">{stars}</span>
          <span style="color:#555;font-size:12px;margin-left:8px">{score}</span>
        </div>""", unsafe_allow_html=True)

st.markdown('---')

# ── Today's Best ─────────────────────────────────────────────────────────────
st.markdown('### Today\'s Best Picks')
top5 = result.top(5)
cols = st.columns(5)
for i, sig in enumerate(top5):
    c = cols[i]
    color = ('#00e676' if sig.rating in ('A+', 'A') else
             '#ffeb3b' if sig.rating in ('A-', 'B+') else '#ff9800')
    c.markdown(f"""
    <div style="background:#12122a;border:1px solid #1e1e3a;border-radius:10px;padding:14px">
      <div style="font-size:22px;font-weight:700;color:#29b6f6">{sig.ticker}</div>
      <div style="color:{color};font-size:18px;font-weight:700">{sig.rating}</div>
      <div style="color:#aaa;font-size:11px;margin-top:6px">
        Conf <b style="color:#ccc">{sig.confidence:.0f}</b><br>
        ER <b style="color:#69f0ae">+{sig.expected_return:.0f}%</b><br>
        DD <b style="color:#ef9a9a">{sig.expected_dd:.0f}%</b><br>
        Kelly <b style="color:#b39ddb">{sig.kelly:.0f}%</b>
      </div>
    </div>""", unsafe_allow_html=True)

st.markdown('---')

# ── High Risk Alert ───────────────────────────────────────────────────────────
if result.high_risk:
    st.markdown('### ⚠️ High Risk Alerts')
    risk_cols = st.columns(min(len(result.high_risk[:4]), 4))
    for i, sig in enumerate(result.high_risk[:4]):
        risk_cols[i].markdown(f"""
        <div style="background:#1a0a0a;border:1px solid #3a1a1a;border-radius:10px;padding:12px">
          <div style="color:#ef5350;font-weight:700">{sig.ticker}</div>
          <div style="color:#aaa;font-size:11px">
            Crash Risk <b style="color:#ef5350">{sig.crash_prob:.0f}%</b><br>
            ExpDD <b style="color:#ef5350">{sig.expected_dd:.0f}%</b>
          </div>
        </div>""", unsafe_allow_html=True)

st.caption(f"Last scan: {result.last_update.strftime('%d %b %Y %H:%M')} · "
           f"Runtime: {result.runtime_sec:.0f}s · {result.n_tickers} tickers")
