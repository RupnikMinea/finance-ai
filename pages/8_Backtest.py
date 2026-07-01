import gc
import itertools
import numpy as np
import pandas as pd
import plotly.graph_objects as go
import streamlit as st
from datetime import datetime

from config import ALL_FEATS, FEAT_DISPLAY, TRAIN_START, HORIZON, ENS_W, SAFE_DD

st.set_page_config(page_title='AI Backtest', page_icon='📊', layout='wide')

BACKTEST_TICKERS = [
    'AAPL', 'MSFT', 'NVDA', 'AMZN', 'META', 'GOOGL', 'TSLA', 'AVGO', 'COST', 'NFLX',
    'AMD',  'ADBE', 'CRWD', 'PANW', 'QCOM', 'INTU',  'MU',   'ISRG', 'LRCX', 'PYPL',
]

st.markdown("## 📊 AI Backtest & Model Performance")

st.markdown("""
<div style="border-left:3px solid #29b6f6;padding:10px 16px;background:#0a0f1a;
            border-radius:0 8px 8px 0;margin-bottom:20px;font-size:13px;color:#aaa;line-height:1.6">
  See how the AI engine is built, what each model predicts, which price features it uses most,
  and how a quarterly rebalancing strategy based on AI ratings would have performed historically.
</div>
""", unsafe_allow_html=True)

# ── Section 1: Architecture ────────────────────────────────────────────────────
st.markdown("### 🧠 AI Engine — Architecture")

c1, c2 = st.columns([3, 2])

with c1:
    st.markdown("""
**Pipeline:** Price data → 43 price features → 4 LightGBM models → Ensemble score → Rankings

The AI trains 4 gradient-boosting models. Each predicts a different aspect of performance
over the next **{} trading days (~6 months)**.
""".format(HORIZON))

    for name, color, icon, typ, pred, weight, detail in [
        ('Expected Return', '#69f0ae', '📈', 'Regressor',
         'Average price gain in {} days (%)'.format(HORIZON), '40%',
         'Core model. Trained on actual 6-month returns since {}. Highest ensemble weight.'.format(TRAIN_START)),
        ('Max Upside', '#b39ddb', '🚀', 'Regressor',
         'Peak gain in {} days (%)'.format(HORIZON), '10%',
         'Optimistic model. Predicts the highest price reached at any point within the 6-month window.'),
        ('P(Safe)', '#29b6f6', '🛡️', 'Classifier',
         'P(max drawdown < {}%) in {} days'.format(int(SAFE_DD), HORIZON), '15%',
         'Safety model. Outputs probability the stock will NOT drop more than {}% from today.'.format(int(SAFE_DD))),
        ('Expected DD', '#ef9a9a', '📉', 'Regressor',
         'Max drawdown in {} days (%)'.format(HORIZON), 'Kelly sizing',
         'Risk model. Predicts worst dip from current price. Used in Dynamic Kelly: Kelly = ER / |EDD|.'),
    ]:
        st.markdown(f"""
<div style="background:#0d0d1a;border:1px solid #1e1e3a;border-radius:10px;
            padding:14px 16px;margin-bottom:8px">
  <div style="margin-bottom:6px">
    <span style="font-size:15px;font-weight:700;color:{color}">{icon} {name}</span>
    <span style="background:#1a1a3a;border-radius:4px;padding:2px 8px;
                 font-size:11px;color:#aaa;margin-left:8px">{typ}</span>
    <span style="background:#1a1a3a;border-radius:4px;padding:2px 8px;
                 font-size:11px;color:#ffd700;margin-left:4px">Weight: {weight}</span>
  </div>
  <div style="color:#aaa;font-size:13px">Predicts: <b style="color:white">{pred}</b></div>
  <div style="color:#666;font-size:12px;margin-top:4px">{detail}</div>
</div>
""", unsafe_allow_html=True)

with c2:
    ew = ENS_W
    fig_pie = go.Figure(go.Pie(
        labels=[
            f'ER rank ({ew[0]*100:.0f}%)',
            f'Dynamic Kelly ({ew[1]*100:.0f}%)',
            f'P(Safe) ({ew[2]*100:.0f}%)',
            f'Max Upside ({ew[3]*100:.0f}%)',
        ],
        values=[ew[0]*100, ew[1]*100, ew[2]*100, ew[3]*100],
        hole=0.55,
        marker_colors=['#69f0ae', '#b39ddb', '#29b6f6', '#ef9a9a'],
        textinfo='percent',
        hovertemplate='%{label}<extra></extra>',
    ))
    fig_pie.update_layout(
        title=dict(text='Confidence Score Weights', font=dict(color='#aaa', size=13)),
        paper_bgcolor='#0a0a1a', font=dict(color='#aaa', size=11),
        legend=dict(font=dict(size=10), bgcolor='#0a0a1a'),
        height=280, margin=dict(t=40, b=5, l=5, r=5),
    )
    st.plotly_chart(fig_pie, use_container_width=True)

    st.markdown(f"""
<div style="background:#0d0d1a;border:1px solid #1e1e3a;border-radius:10px;padding:14px 16px">
  <b style="color:#ffd700">Training Setup</b>
  <table style="width:100%;margin-top:8px;font-size:12px;border-collapse:collapse">
    <tr><td style="color:#777;padding:3px 0">Algorithm</td>
        <td style="color:#aaa;text-align:right">LightGBM (GBDT)</td></tr>
    <tr><td style="color:#777;padding:3px 0">Training from</td>
        <td style="color:#aaa;text-align:right">{TRAIN_START}</td></tr>
    <tr><td style="color:#777;padding:3px 0">Prediction horizon</td>
        <td style="color:#aaa;text-align:right">{HORIZON} days (~6 months)</td></tr>
    <tr><td style="color:#777;padding:3px 0">Training universe</td>
        <td style="color:#aaa;text-align:right">NASDAQ-100 (~90 stocks)</td></tr>
    <tr><td style="color:#777;padding:3px 0">Features</td>
        <td style="color:#aaa;text-align:right">{len(ALL_FEATS)} price features</td></tr>
    <tr><td style="color:#777;padding:3px 0">Safe DD threshold</td>
        <td style="color:#aaa;text-align:right">{int(SAFE_DD)}% max drawdown</td></tr>
    <tr><td style="color:#777;padding:3px 0">Retrain interval</td>
        <td style="color:#aaa;text-align:right">every 7 days</td></tr>
    <tr><td style="color:#777;padding:3px 0">Sample weighting</td>
        <td style="color:#aaa;text-align:right">recent data weighted 4× higher</td></tr>
  </table>
</div>
""", unsafe_allow_html=True)

# ── Section 2: Feature Importance ─────────────────────────────────────────────
st.markdown("---")
st.markdown("### 🔬 Feature Importance")
st.caption("Top-15 features each model relies on most (LightGBM split count — how often the feature is used to make a decision).")

@st.cache_data(show_spinner=False)
def _load_fi():
    from engine.models import load_models
    models, _ = load_models()
    out = {}
    for name, model in models.items():
        if not hasattr(model, 'feature_importances_'):
            continue
        fi = pd.Series(model.feature_importances_, index=ALL_FEATS)
        fi = fi[fi > 0].sort_values(ascending=True).tail(15)
        out[name] = ([FEAT_DISPLAY.get(f, f) for f in fi.index], fi.values.tolist())
    return out

MODEL_META = {
    'expected_return': ('📈 Expected Return', '#69f0ae'),
    'max_upside':      ('🚀 Max Upside',      '#b39ddb'),
    'prob_safe':       ('🛡️ P(Safe)',          '#29b6f6'),
    'expected_dd':     ('📉 Expected DD',      '#ef9a9a'),
}

try:
    fi_data = _load_fi()
    if fi_data:
        tab_labels = [MODEL_META.get(k, (k, '#aaa'))[0] for k in fi_data]
        fi_tabs = st.tabs(tab_labels)
        for tab, (mk, (labels, vals)) in zip(fi_tabs, fi_data.items()):
            with tab:
                _, col = MODEL_META.get(mk, (mk, '#b39ddb'))
                fig_fi = go.Figure(go.Bar(
                    x=vals, y=labels, orientation='h',
                    marker_color=col,
                    hovertemplate='%{y}: %{x:,.0f}<extra></extra>',
                ))
                fig_fi.update_layout(
                    paper_bgcolor='#0a0a1a', plot_bgcolor='#12122a',
                    font=dict(color='#aaa'), height=430,
                    margin=dict(t=10, b=20, l=200, r=20),
                    xaxis=dict(title='Feature importance (split count)',
                               gridcolor='#1a1a3a', color='#aaa'),
                    yaxis=dict(color='#aaa', tickfont=dict(size=11)),
                )
                st.plotly_chart(fig_fi, use_container_width=True)
    else:
        st.info("No trained models found on disk. Run a scan first to train the models.")
except Exception as e:
    st.info(f"Run a scan first to train the models. ({e})")

# ── Section 3: Walk-Forward Backtest ──────────────────────────────────────────
st.markdown("---")
st.markdown("### 📈 Walk-Forward Portfolio Backtest")

st.markdown("""
<div style="border-left:3px solid #ffd700;padding:10px 16px;background:#1a1200;
            border-radius:0 8px 8px 0;margin-bottom:16px;font-size:12px;color:#aaa;line-height:1.6">
  <b style="color:#ffd700">How it works</b><br>
  At the start of each quarter, the AI scores <b>20 liquid NASDAQ stocks</b> using only price data
  available at that moment (no future leakage in features). The top-N stocks are bought equally
  and held for one quarter. Performance is compared to QQQ buy-and-hold.<br>
  <span style="color:#555">⚠ Models were trained on the full dataset — this is pseudo-out-of-sample.
  Feature values (SMAs, momentum, etc.) use no future data.</span>
</div>
""", unsafe_allow_html=True)

col_a, col_b = st.columns(2)
top_n       = col_a.slider("Stocks selected per quarter", min_value=3, max_value=10, value=5)
start_year  = col_b.selectbox("Backtest start", options=[2022, 2023, 2024], index=0)

# ── Cached data loading ────────────────────────────────────────────────────────

def _load_backtest_data(prog):
    from engine.data     import download_all
    from engine.features import build_cache

    prog.progress(5, "Downloading 20 NASDAQ stocks + QQQ...")
    end_date = (datetime.today()).strftime('%Y-%m-%d')

    tickers_all = BACKTEST_TICKERS + ['QQQ']
    price_dict  = download_all(tickers_all, end_date)

    if 'QQQ' not in price_dict or len(price_dict) < 5:
        return None, None, "Download returned too little data — check internet connection."

    prog.progress(35, "Building price features for 20 stocks...")
    qqq_c    = price_dict['QQQ']['Close']
    qqq_rets = {
        '1m':  qqq_c.pct_change(21)  * 100,
        '3m':  qqq_c.pct_change(63)  * 100,
        '6m':  qqq_c.pct_change(126) * 100,
        '12m': qqq_c.pct_change(252) * 100,
    }
    stock_dict = {t: df for t, df in price_dict.items() if t != 'QQQ'}

    try:
        full_cache = build_cache(stock_dict, qqq_rets)
    except Exception as e:
        return None, None, f"Feature build error: {e}"

    prog.progress(70, "Data ready.")
    close_prices = {t: df['Close'] for t, df in price_dict.items()}
    return full_cache, close_prices, None


def _run_walk_forward(full_cache, close_prices, top_n, start_year, prog):
    from engine.features import get_today_snapshot
    from engine.models   import load_models
    from engine.ranking  import predict_and_rank

    prog.progress(72, "Loading trained models...")
    models, _ = load_models()
    if not models:
        return None, None, "No trained models found. Run a scan first."

    prog.progress(78, "Running quarterly simulation...")
    today = pd.Timestamp.today().normalize()
    rebalance_dates = sorted([
        pd.Timestamp(y, m, 1)
        for y, m in itertools.product(range(start_year, today.year + 2), [1, 4, 7, 10])
        if pd.Timestamp(y, m, 1) < today
    ])

    if len(rebalance_dates) < 2:
        return None, None, "Not enough quarters for backtest."

    qqq_close = close_prices.get('QQQ')
    rows, log  = [], []
    n_periods  = len(rebalance_dates) - 1

    for i, d in enumerate(rebalance_dates[:-1]):
        next_d = rebalance_dates[i + 1]

        # Snapshot at date d
        truncated = {t: df[df.index <= d] for t, df in full_cache.items()
                     if len(df[df.index <= d]) >= 252}
        if len(truncated) < 3:
            continue

        try:
            snap   = get_today_snapshot(truncated)
            ranked = predict_and_rank(snap, models)
        except Exception:
            continue

        top_tickers = ranked.head(top_n)['ticker'].tolist()

        # Actual returns d → next_d
        actual_rets  = []
        stock_detail = []
        for t in top_tickers:
            if t not in close_prices:
                continue
            p = close_prices[t]
            p0_s = p[p.index >= d]
            p1_s = p[p.index >= next_d]
            if len(p0_s) == 0 or len(p1_s) == 0:
                continue
            ret = float((p1_s.iloc[0] / p0_s.iloc[0] - 1) * 100)
            actual_rets.append(ret)
            stock_detail.append(f"{t} ({ret:+.1f}%)")

        if qqq_close is not None:
            q0 = qqq_close[qqq_close.index >= d]
            q1 = qqq_close[qqq_close.index >= next_d]
            qqq_ret = float((q1.iloc[0] / q0.iloc[0] - 1) * 100) if len(q0) and len(q1) else 0.0
        else:
            qqq_ret = 0.0

        strat_ret = float(np.mean(actual_rets)) if actual_rets else 0.0
        qlabel    = f"{d.year} Q{(d.month-1)//3+1}"

        rows.append({'date': d, 'strategy': strat_ret, 'qqq': qqq_ret})
        log.append({
            'Quarter':         qlabel,
            'AI Top Picks':    ', '.join(top_tickers),
            'Actual Results':  ', '.join(stock_detail),
            'Strategy':        f'{strat_ret:+.1f}%',
            'QQQ':             f'{qqq_ret:+.1f}%',
            'Alpha':           f'{strat_ret - qqq_ret:+.1f}%',
            'Beat QQQ':        '✅' if strat_ret > qqq_ret else '❌',
        })

        prog.progress(78 + int((i + 1) / n_periods * 20),
                      f"Quarter {i+1}/{n_periods}: {qlabel}...")
        gc.collect()

    prog.progress(100, "Done!")
    if not rows:
        return None, None, "No data generated — try a later start year."
    return pd.DataFrame(rows), log, None


# ── Session state ──────────────────────────────────────────────────────────────
for k in ('bt_cache', 'bt_closes', 'bt_df', 'bt_log', 'bt_err'):
    if k not in st.session_state:
        st.session_state[k] = None

if st.button("▶  Run Backtest", type="primary", use_container_width=True):
    prog = st.progress(0, "Starting...")

    # Load data if not already cached
    if st.session_state['bt_cache'] is None:
        cache, closes, err = _load_backtest_data(prog)
        if err:
            st.session_state['bt_err'] = err
        else:
            st.session_state['bt_cache']  = cache
            st.session_state['bt_closes'] = closes
    else:
        prog.progress(70, "Using cached price data...")

    if st.session_state['bt_cache'] is not None:
        df, log, err = _run_walk_forward(
            st.session_state['bt_cache'],
            st.session_state['bt_closes'],
            top_n, start_year, prog,
        )
        st.session_state.update({'bt_df': df, 'bt_log': log, 'bt_err': err})

    prog.empty()

if st.button("🔄 Clear Cached Data", help="Re-download fresh price data on next run"):
    st.session_state['bt_cache']  = None
    st.session_state['bt_closes'] = None
    st.session_state['bt_df']     = None
    st.session_state['bt_log']    = None
    st.session_state['bt_err']    = None
    st.success("Cache cleared.")

# ── Display results ────────────────────────────────────────────────────────────
bt_err = st.session_state['bt_err']
bt_df  = st.session_state['bt_df']
bt_log = st.session_state['bt_log']

if bt_err:
    st.error(bt_err)

elif bt_df is not None and len(bt_df) > 0:
    bt_df = bt_df.copy()
    bt_df['cum_strat'] = ((1 + bt_df['strategy'] / 100).cumprod() - 1) * 100
    bt_df['cum_qqq']   = ((1 + bt_df['qqq']      / 100).cumprod() - 1) * 100

    # Summary metrics
    total_ret = float(bt_df['cum_strat'].iloc[-1])
    total_qqq = float(bt_df['cum_qqq'].iloc[-1])
    alpha     = total_ret - total_qqq
    win_rate  = float((bt_df['strategy'] > bt_df['qqq']).mean() * 100)
    n_q       = len(bt_df)
    years     = max(n_q / 4.0, 0.25)
    ann_ret   = ((1 + total_ret / 100) ** (1 / years) - 1) * 100 if total_ret > -100 else -100.0
    ann_qqq   = ((1 + total_qqq / 100) ** (1 / years) - 1) * 100 if total_qqq > -100 else -100.0

    q_rets = bt_df['strategy'].values
    sharpe = float(np.mean(q_rets) / np.std(q_rets) * 2) if np.std(q_rets) > 0 else 0.0

    cum_series  = (1 + bt_df['strategy'] / 100).cumprod()
    max_dd_val  = float(((cum_series / cum_series.cummax()) - 1).min() * 100)

    m1, m2, m3, m4, m5, m6 = st.columns(6)
    m1.metric("Strategy Total",  f"{total_ret:+.1f}%", f"Ann: {ann_ret:+.1f}%")
    m2.metric("QQQ Total",       f"{total_qqq:+.1f}%", f"Ann: {ann_qqq:+.1f}%")
    m3.metric("Alpha vs QQQ",    f"{alpha:+.1f}%")
    m4.metric("Win Rate vs QQQ", f"{win_rate:.0f}%",   f"{n_q} quarters")
    m5.metric("Sharpe (ann.)",   f"{sharpe:.2f}")
    m6.metric("Max Drawdown",    f"{max_dd_val:.1f}%")

    # Cumulative return chart
    fig1 = go.Figure()
    fig1.add_trace(go.Scatter(
        x=bt_df['date'], y=bt_df['cum_strat'], name='AI Strategy',
        line=dict(color='#69f0ae', width=2.5),
        fill='tozeroy', fillcolor='rgba(105,240,174,0.06)',
        hovertemplate='%{x|%Y-%m}: %{y:+.1f}%<extra>Strategy</extra>',
    ))
    fig1.add_trace(go.Scatter(
        x=bt_df['date'], y=bt_df['cum_qqq'], name='QQQ (benchmark)',
        line=dict(color='#29b6f6', width=2, dash='dash'),
        hovertemplate='%{x|%Y-%m}: %{y:+.1f}%<extra>QQQ</extra>',
    ))
    fig1.add_hline(y=0, line_color='#333', line_dash='dot')
    fig1.update_layout(
        title='Cumulative Return: AI Strategy vs QQQ',
        paper_bgcolor='#0a0a1a', plot_bgcolor='#12122a',
        font=dict(color='#aaa'), height=380,
        margin=dict(t=50, b=20, l=20, r=20),
        legend=dict(bgcolor='rgba(18,18,42,0.9)', bordercolor='#1e1e3a'),
        xaxis=dict(gridcolor='#1a1a3a', color='#aaa'),
        yaxis=dict(title='Cumulative Return (%)', gridcolor='#1a1a3a',
                   color='#aaa', ticksuffix='%', zeroline=True, zerolinecolor='#333'),
        hovermode='x unified',
    )
    st.plotly_chart(fig1, use_container_width=True)

    # Quarterly bar chart
    bar_colors = ['#69f0ae' if s > q else '#ef9a9a'
                  for s, q in zip(bt_df['strategy'], bt_df['qqq'])]
    fig2 = go.Figure()
    fig2.add_trace(go.Bar(
        x=bt_df['date'], y=bt_df['strategy'], name='AI Strategy',
        marker_color=bar_colors,
        hovertemplate='%{x|%Y-%m}: %{y:+.1f}%<extra>Strategy</extra>',
    ))
    fig2.add_trace(go.Scatter(
        x=bt_df['date'], y=bt_df['qqq'], name='QQQ',
        line=dict(color='#29b6f6', width=2),
        mode='lines+markers', marker=dict(size=5),
        hovertemplate='%{x|%Y-%m}: %{y:+.1f}%<extra>QQQ</extra>',
    ))
    fig2.add_hline(y=0, line_color='#333', line_dash='dot')
    fig2.update_layout(
        title='Quarterly Returns — green = beat QQQ',
        paper_bgcolor='#0a0a1a', plot_bgcolor='#12122a',
        font=dict(color='#aaa'), height=330,
        margin=dict(t=50, b=20, l=20, r=20),
        legend=dict(bgcolor='rgba(18,18,42,0.9)'),
        xaxis=dict(gridcolor='#1a1a3a', color='#aaa'),
        yaxis=dict(title='Return (%)', gridcolor='#1a1a3a', color='#aaa', ticksuffix='%'),
        hovermode='x unified',
    )
    st.plotly_chart(fig2, use_container_width=True)

    # Positions table
    if bt_log:
        with st.expander("📋 Quarter-by-Quarter Positions & Returns", expanded=True):
            log_df = pd.DataFrame(bt_log)
            st.dataframe(log_df, use_container_width=True, hide_index=True)

# ── Legend ─────────────────────────────────────────────────────────────────────
st.markdown("---")
with st.expander("📖 Metric & Model Legend", expanded=True):
    st.markdown("""
| Term | Meaning |
|---|---|
| **Expected Return (ER)** | Predicted average price change over 126 trading days (~6 months) |
| **Max Upside** | Predicted best-case peak — highest price within the 6-month window |
| **P(Safe)** | Probability the stock does NOT drop more than {}% from today (binary classifier) |
| **Expected DD (EDD)** | Predicted worst dip from current price within 6 months (negative %) |
| **Dynamic Kelly** | Position size = ER / |EDD|. Used as risk-adjusted sizing in the ensemble |
| **Confidence Score** | Ensemble of all 4 models + cross-sectional ranking (0–100) |
| **AI Rating** | A+ → C+ grade based on weighted Confidence + Stable + Growth + (100−Crash) |
| **Alpha** | Strategy quarterly return minus QQQ return. Positive = AI beat the benchmark |
| **Win Rate** | % of quarters where AI strategy outperformed QQQ buy-and-hold |
| **Sharpe (ann.)** | Annualized Sharpe ratio from quarterly returns. >1.0 = good, >2.0 = excellent |
| **Max Drawdown** | Largest peak-to-trough loss in the simulated equity curve |
| **Feature Importance** | LightGBM split count — how many tree splits used this feature. Higher = more influential |
| **Sample weighting** | Recent rows get up to 4× the training weight (time decay: 20%→100%) |
""".format(int(SAFE_DD)))
