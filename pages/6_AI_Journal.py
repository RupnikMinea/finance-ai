import streamlit as st
import pandas as pd
from engine.cache import load_journal

st.set_page_config(page_title='AI Journal', page_icon='📔', layout='wide')
st.title('📔 AI Journal')
st.caption('Signal trajectory — how AI confidence evolves for each stock over time')

journal = load_journal()
if not journal:
    st.info('No journal entries yet. Entries are saved automatically after each scan.')
    st.stop()

# ── Per-ticker trajectory ─────────────────────────────────────────────────────
all_tickers = sorted({entry['ticker'] for day in journal for entry in day['top10']})

selected = st.selectbox('Select ticker to view trajectory', [''] + all_tickers)
if selected:
    rows = []
    for day in journal:
        for entry in day['top10']:
            if entry['ticker'] == selected:
                rows.append({
                    'Date':       day['date'],
                    'Confidence': entry['confidence'],
                    'Exp Ret':    entry['expected_return'],
                    'Rating':     entry['rating'],
                })
    if rows:
        df_traj = pd.DataFrame(rows).sort_values('Date')
        st.markdown(f'#### {selected} — {len(rows)} appearances in Top 10')

        import plotly.graph_objects as go
        fig = go.Figure()
        fig.add_trace(go.Scatter(
            x=df_traj['Date'], y=df_traj['Confidence'],
            mode='lines+markers', name='Confidence',
            line=dict(color='#29b6f6', width=2),
            marker=dict(size=8),
        ))
        fig.update_layout(
            template='plotly_dark', paper_bgcolor='#1a1a2e', plot_bgcolor='#16213e',
            height=280, margin=dict(l=10, r=10, t=30, b=10),
            yaxis=dict(range=[0, 100], gridcolor='#2a2a4a', color='#aaa'),
            xaxis=dict(gridcolor='#2a2a4a', color='#aaa'),
            title=dict(text=f'{selected} — Confidence Trajectory',
                       font=dict(color='#29b6f6', size=13)),
        )
        st.plotly_chart(fig, use_container_width=True)
        st.dataframe(df_traj, use_container_width=True)
    else:
        st.info(f'{selected} not in any Top 10 yet.')

st.markdown('---')

# ── Latest journal entries ────────────────────────────────────────────────────
st.markdown('### Recent Scans')
for day in sorted(journal, key=lambda x: x['date'], reverse=True)[:10]:
    with st.expander(f"{day['date']}  ·  Top 10"):
        rows = [{'Rank': i+1, **e} for i, e in enumerate(day['top10'])]
        st.dataframe(pd.DataFrame(rows), use_container_width=True)
