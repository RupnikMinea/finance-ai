import streamlit as st
import pandas as pd

st.set_page_config(page_title='Analytics', page_icon='🧠', layout='wide')
st.title('🧠 Analytics')
st.caption('Power-user view: SHAP, feature drift, correlations')

result = st.session_state.get('scan_result')
if result is None:
    st.warning('Run a scan first from **Live Screener**.')
    st.stop()

tab_drift, tab_corr, tab_dist = st.tabs(['Feature Drift', 'Correlations', 'Score Distribution'])

# ── Feature Drift ─────────────────────────────────────────────────────────────
with tab_drift:
    drift = result.drift
    if not drift:
        st.info('No drift data available.')
    else:
        alerts = [d for d in drift if d.get('alert')]
        if alerts:
            st.warning(f'⚠️ {len(alerts)} features with significant drift (z > 2.5)')
            for d in alerts[:5]:
                st.markdown(f'`{d["display"]}` — z={d["drift_z"]:.1f}  '
                            f'(train: {d["train_mean"]:.2f} → now: {d["now_mean"]:.2f})')
        else:
            st.success('No significant feature drift detected.')

        df_drift = pd.DataFrame(drift[:30])
        if 'display' in df_drift.columns:
            df_drift = df_drift.rename(columns={'display': 'Feature'})
        st.dataframe(
            df_drift[['Feature','train_mean','now_mean','drift_z','alert']],
            use_container_width=True,
        )

# ── Correlations ──────────────────────────────────────────────────────────────
with tab_corr:
    top10 = [s.ticker for s in result.stocks[:10]]
    st.markdown(f'Showing correlations for Top 10: **{", ".join(top10)}**')
    st.info('Full correlation heatmap requires price data — run scan with price_data cached. '
            'Coming in Sprint 2 with persistent price cache.')

# ── Score Distribution ────────────────────────────────────────────────────────
with tab_dist:
    import plotly.graph_objects as go
    stocks = result.stocks
    fig = go.Figure()
    fig.add_trace(go.Histogram(
        x=[s.confidence for s in stocks],
        name='Confidence', nbinsx=20,
        marker_color='#29b6f6', opacity=0.7,
    ))
    fig.add_trace(go.Histogram(
        x=[s.stable_score for s in stocks],
        name='Stable Score', nbinsx=20,
        marker_color='#69f0ae', opacity=0.7,
    ))
    fig.add_trace(go.Histogram(
        x=[s.growth_score for s in stocks],
        name='Growth Score', nbinsx=20,
        marker_color='#ffd700', opacity=0.7,
    ))
    fig.update_layout(
        template='plotly_dark', paper_bgcolor='#1a1a2e', plot_bgcolor='#16213e',
        barmode='overlay', height=380, margin=dict(l=10,r=10,t=30,b=10),
        title=dict(text='Score Distributions (all NASDAQ-100)',
                   font=dict(color='#b39ddb',size=13)),
        xaxis=dict(title='Score', gridcolor='#2a2a4a', color='#aaa'),
        yaxis=dict(title='Count',  gridcolor='#2a2a4a', color='#aaa'),
        legend=dict(orientation='h', y=1.08, font=dict(color='#ccc')),
    )
    st.plotly_chart(fig, use_container_width=True)

    # Summary table
    rows = []
    for s in stocks:
        rows.append({'Ticker': s.ticker, 'Rating': s.rating,
                     'Conf': s.confidence, 'Stable': s.stable_score,
                     'Growth': s.growth_score, 'Crash': s.crash_prob})
    st.dataframe(pd.DataFrame(rows), use_container_width=True, height=400)
