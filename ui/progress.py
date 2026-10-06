"""
MOVA UI: Personal Progress Dashboard
Implements Section 1 & 33:
Strictly compares YOU vs. YOUR PREVIOUS PERFORMANCE. Never compares to other people or normal standards.
Clean Plotly charts for reaction latency, accuracy, multimodal coordination, and posture stability.
"""

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from database.repository import repo

def render_progress_screen():
    st.markdown("""
    <div style="margin-bottom: 20px;">
        <div style="font-size: 0.8rem; font-weight: 800; color: #00E5FF; letter-spacing: 2px;">PERSONAL ANALYTICS</div>
        <h2 style="font-size: 2.2rem; font-weight: 800; color: #FFFFFF; margin: 0;">📈 Your Movement Progress</h2>
        <div style="color: #94A3B8; font-size: 0.95rem; margin-top: 4px;">
            <b>Core Principle:</b> YOU vs. YOUR PREVIOUS PERFORMANCE. MOVA tracks your personal trends across time.
        </div>
    </div>
    """, unsafe_allow_html=True)

    results = repo.get_recent_results(limit=50)

    if not results:
        st.info("No session history recorded yet. Complete your first activity in the MOVA Zone to begin tracking personal trends!")
        if st.button("🚀 Launch First Activity", key="btn_first_act"):
            st.session_state["nav_page"] = "GAME LIBRARY"
            st.rerun()
        return

    # Aggregate metrics
    total_rounds = len(results)
    best_score = max(r.get("score", 0) for r in results)
    avg_accuracy = sum(r.get("accuracy", 0.0) for r in results) / total_rounds
    avg_reaction = sum(r.get("reaction_time", 0.0) for r in results) / total_rounds
    avg_coord = sum(r.get("multimodal_coordination", 85.0) for r in results) / total_rounds

    # Metrics highlight bar
    m1, m2, m3, m4, m5 = st.columns(5)
    m1.metric("Rounds Played", f"{total_rounds}")
    m2.metric("Personal Best", f"{best_score:,} pts")
    m3.metric("Avg Accuracy", f"{int(avg_accuracy * 100)}%")
    m4.metric("Avg Reaction", f"{avg_reaction:.2f}s")
    m5.metric("Avg Coordination", f"{avg_coord:.1f}%")

    st.markdown("<div style='margin-top: 25px;'></div>", unsafe_allow_html=True)

    # Convert to DataFrame for Plotly
    df = pd.DataFrame(results)
    df["timestamp_clean"] = pd.to_datetime(df["timestamp"]).dt.strftime('%b %d, %H:%M')
    df = df.iloc[::-1].reset_index(drop=True)  # Chronological order
    df["Round"] = df.index + 1

    chart_c1, chart_c2 = st.columns(2)

    with chart_c1:
        # Reaction Time Trend (Lower is faster)
        fig_react = go.Figure()
        fig_react.add_trace(go.Scatter(
            x=df["Round"], y=df["reaction_time"],
            mode='lines+markers',
            name='Reaction Latency (s)',
            line=dict(color='#00E5FF', width=3),
            marker=dict(size=7, color='#7928CA')
        ))
        fig_react.update_layout(
            title="<b>Reaction Latency Trend (Lower is Faster)</b>",
            paper_bgcolor='rgba(20,20,35,0.7)',
            plot_bgcolor='rgba(15,15,25,0.7)',
            font=dict(color='#CBD5E1'),
            xaxis=dict(title="Activity Round", gridcolor='rgba(255,255,255,0.06)'),
            yaxis=dict(title="Seconds (s)", gridcolor='rgba(255,255,255,0.06)'),
            margin=dict(l=40, r=20, t=40, b=40),
            height=320
        )
        st.plotly_chart(fig_react, use_container_width=True)

    with chart_c2:
        # Accuracy & Multimodal Coordination Trend
        fig_acc = go.Figure()
        fig_acc.add_trace(go.Scatter(
            x=df["Round"], y=df["accuracy"] * 100,
            mode='lines+markers',
            name='Accuracy (%)',
            line=dict(color='#10B981', width=3),
            marker=dict(size=7)
        ))
        fig_acc.add_trace(go.Scatter(
            x=df["Round"], y=df["multimodal_coordination"],
            mode='lines+markers',
            name='Multimodal Coord (%)',
            line=dict(color='#F59E0B', width=2, dash='dot'),
            marker=dict(size=6)
        ))
        fig_acc.update_layout(
            title="<b>Accuracy & Multimodal Coordination (%)</b>",
            paper_bgcolor='rgba(20,20,35,0.7)',
            plot_bgcolor='rgba(15,15,25,0.7)',
            font=dict(color='#CBD5E1'),
            xaxis=dict(title="Activity Round", gridcolor='rgba(255,255,255,0.06)'),
            yaxis=dict(title="Percentage (%)", range=[30, 105], gridcolor='rgba(255,255,255,0.06)'),
            margin=dict(l=40, r=20, t=40, b=40),
            height=320,
            legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
        )
        st.plotly_chart(fig_acc, use_container_width=True)

    # Activity History Table
    st.markdown("### 📋 Activity History Log")
    display_cols = ["id", "game_name", "score", "accuracy", "reaction_time", "multimodal_coordination", "stability_score", "timestamp_clean"]
    renamed = {
        "id": "ID",
        "game_name": "Activity",
        "score": "Score",
        "accuracy": "Accuracy",
        "reaction_time": "Reaction (s)",
        "multimodal_coordination": "Coord (%)",
        "stability_score": "Stability",
        "timestamp_clean": "Recorded At"
    }
    st.dataframe(df[display_cols].rename(columns=renamed).sort_values("ID", ascending=False), use_container_width=True, hide_index=True)
