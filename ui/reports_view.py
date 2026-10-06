"""
MOVA UI: Session Complete & Reports View
Implements Section 31:
Detailed post-session breakdown, multimodal contribution, YOU vs. YOUR PREVIOUS PERFORMANCE comparison,
AI Movement Coach insights, next-activity recommendations, and direct ReportLab PDF download.
"""

import streamlit as st
import time
from database.repository import repo
from database.models import StandardGameResult
from reports.session_report import SessionReportService
from ai.coach import ai_coach
from ml.recommendation_engine import RecommendationEngine

def render_reports_screen():
    st.markdown("""
    <div style="margin-bottom: 20px;">
        <div style="font-size: 0.8rem; font-weight: 800; color: #10B981; letter-spacing: 2px;">SESSION COMPLETED</div>
        <h2 style="font-size: 2.2rem; font-weight: 800; color: #FFFFFF; margin: 0;">🏆 Session Report</h2>
        <div style="color: #94A3B8; font-size: 0.95rem; margin-top: 4px;">
            Measurable results compared strictly against your own previous performance.
        </div>
    </div>
    """, unsafe_allow_html=True)

    results = repo.get_recent_results(limit=10)
    last_res = st.session_state.get("last_completed_game") or (results[0] if results else None)

    if not last_res:
        st.info("No completed activity in the current session. Play an activity to generate your session report!")
        if st.button("Browse Game Library", key="btn_no_rep_lib"):
            st.session_state["nav_page"] = "GAME LIBRARY"
            st.rerun()
        return

    # Personal Comparison Trend (Section 1 & 26)
    gid = last_res.get("game_id", "gravity_flip")
    dummy_obj = StandardGameResult(**{k: v for k, v in last_res.items() if k in StandardGameResult.__dataclass_fields__})
    trend = repo.get_comparison_trend("default_user", gid, dummy_obj)

    # 1. Overall Performance Top Metrics
    c1, c2, c3, c4, c5 = st.columns(5)
    c1.metric("Final Score", f"{last_res.get('score', 0):,} pts", delta=f"{trend.get('score_delta', 0):+} pts" if trend.get("has_previous") else None)
    c2.metric("Target Accuracy", f"{int(last_res.get('accuracy', 0.8) * 100)}%", delta=f"{int(trend.get('accuracy_delta', 0.0) * 100):+}%" if trend.get("has_previous") else None)
    c3.metric("Reaction Latency", f"{last_res.get('reaction_time', 0.7):.2f}s", delta=f"{trend.get('reaction_delta', 0.0):+.2f}s (faster)" if trend.get("has_previous") else None)
    c4.metric("Multimodal Coord", f"{last_res.get('multimodal_coordination', 85.0):.1f}%")
    c5.metric("Body Stability", f"{last_res.get('stability_score', 90.0):.1f}/100")

    st.markdown("<div style='margin-top: 20px;'></div>", unsafe_allow_html=True)

    # 2. AI Movement Coach & Personal Trend
    coach_text = ai_coach.get_coach_feedback(last_res, trend)
    recommendation = RecommendationEngine.recommend_next_game(last_res, results)

    col_coach, col_trend = st.columns([1.2, 1.0])

    with col_coach:
        st.markdown(f"""
        <div style="background: linear-gradient(135deg, rgba(121, 40, 202, 0.25) 0%, rgba(30, 25, 55, 0.7) 100%); border: 1px solid rgba(121, 40, 202, 0.45); border-radius: 14px; padding: 20px;">
            <div style="font-size: 0.75rem; font-weight: 800; color: #00E5FF; letter-spacing: 2px;">AI MOVEMENT COACH INSIGHT</div>
            <h4 style="margin: 6px 0 10px 0; color: #FFFFFF;">Performance Observation</h4>
            <p style="color: #E2E8F0; font-size: 0.95rem; line-height: 1.5;">{coach_text}</p>
            <hr style="border-color: rgba(255,255,255,0.1); margin: 12px 0;">
            <div style="font-size: 0.82rem; color: #A78BFA;">
                <b>Next Recommended Activity:</b> {recommendation['game_name']}<br>
                <span style="color: #94A3B8;">Reason: {recommendation['reason']}</span>
            </div>
        </div>
        """, unsafe_allow_html=True)

    with col_trend:
        st.markdown(f"""
        <div style="background: rgba(20, 20, 35, 0.7); border: 1px solid rgba(255, 255, 255, 0.1); border-radius: 14px; padding: 20px;">
            <div style="font-size: 0.75rem; font-weight: 800; color: #F59E0B; letter-spacing: 2px;">YOU vs. YOUR PREVIOUS PERFORMANCE</div>
            <h4 style="margin: 6px 0 10px 0; color: #FFFFFF;">{trend.get('trend_status', 'Personal Baseline Established')}</h4>
            <p style="color: #CBD5E1; font-size: 0.9rem;">{trend.get('summary', 'Great start! First recorded benchmark for this activity.')}</p>
            <div style="margin-top: 10px; font-size: 0.82rem; color: #94A3B8;">
                <div>● Total Rounds Completed: <b>{trend.get('sessions_completed', 1)}</b></div>
                <div>● Baseline Avg Reaction: <b>{trend.get('baseline_avg_reaction', last_res.get('reaction_time', 0.7)):.2f}s</b></div>
                <div>● Baseline Avg Accuracy: <b>{int(trend.get('baseline_avg_accuracy', last_res.get('accuracy', 0.8)) * 100)}%</b></div>
            </div>
        </div>
        """, unsafe_allow_html=True)

    st.markdown("<div style='margin-top: 20px;'></div>", unsafe_allow_html=True)

    # 3. Multimodal Breakdown Chips
    st.markdown("### 🧩 Multimodal Breakdown")
    m_cols = st.columns(6)
    m_cols[0].markdown(f"**👀 Gaze:** {int(last_res.get('gaze_accuracy', 0.85) * 100)}%")
    m_cols[1].markdown(f"**🖐️ Hands:** {int(last_res.get('accuracy', 0.8) * 100)}%")
    m_cols[2].markdown(f"**💪 Arms:** {last_res.get('movement_score', 75.0):.1f}")
    m_cols[3].markdown(f"**🧍 Body:** {last_res.get('stability_score', 90.0):.1f}")
    m_cols[4].markdown(f"**⚖️ Symmetry:** {int(last_res.get('left_right_balance', 0.85) * 100)}%")
    m_cols[5].markdown(f"**🗣️ Voice:** Cued")

    st.markdown("<hr style='border-color: rgba(255,255,255,0.1); margin: 25px 0 20px 0;'>", unsafe_allow_html=True)

    # PDF Export & Actions
    b1, b2, b3 = st.columns([1.2, 1.2, 1.0])

    with b1:
        # Generate PDF using ReportLab
        session_meta = {
            "session_id": last_res.get("session_id", "SES-001"),
            "timestamp": last_res.get("timestamp", ""),
            "duration": last_res.get("duration", 45.0),
            "total_score": last_res.get("score", 0),
            "games_completed": len(results)
        }
        pdf_data = SessionReportService.export_pdf(session_meta, results, trend, coach_text)

        st.download_button(
            label="📄 Download PDF Session Report",
            data=pdf_data,
            file_name=f"MOVA_Session_Report_{int(time.time())}.pdf",
            mime="application/pdf",
            use_container_width=True
        )

    with b2:
        if st.button(f"🚀 Play Recommended: {recommendation['game_name'].split()[0]}", key="btn_rep_next", use_container_width=True):
            st.session_state["selected_game_id"] = recommendation["game_id"]
            st.session_state["nav_page"] = "HOW TO PLAY"
            st.rerun()

    with b3:
        if st.button("📈 View Full Progress", key="btn_rep_prog", use_container_width=True):
            st.session_state["nav_page"] = "PROGRESS"
            st.rerun()
