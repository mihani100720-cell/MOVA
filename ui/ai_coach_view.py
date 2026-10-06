"""
MOVA UI: AI Coach Screen
Implements Section 35 & 41:
Dedicated AI Coach screen showing multimodal movement intelligence,
personal trend insights (YOU vs. YOUR PREVIOUS PERFORMANCE),
session summaries, and coaching recommendations.
"""

import streamlit as st
from database.repository import repo
from ai.coach import ai_coach
from games.game_manager import GameRegistry
from ml.recommendation_engine import RecommendationEngine

def render_ai_coach_screen():
    st.markdown("""
    <div style="padding: 10px 0 20px 0;">
        <div style="font-size: 0.85rem; font-weight: 700; letter-spacing: 2px; color: #00E5FF; text-transform: uppercase;">
            ✦ INTELLIGENCE ENGINE ✦
        </div>
        <h1 style="font-size: 2.6rem; font-weight: 800; background: linear-gradient(135deg, #00E5FF, #7928CA, #FF0080); -webkit-background-clip: text; -webkit-text-fill-color: transparent; margin: 4px 0 10px 0;">
            MOVA AI Movement Coach
        </h1>
        <p style="color: #94A3B8; font-size: 1rem; margin: 0;">
            Non-medical multimodal movement analysis and personalized performance guidance.
        </p>
    </div>
    """, unsafe_allow_html=True)

    # Mandatory Non-Medical Disclaimer
    st.markdown("""
    <div style="background: rgba(121, 40, 202, 0.1); border-left: 4px solid #7928CA; border-radius: 8px; padding: 12px 18px; margin-bottom: 24px; font-size: 0.88rem; color: #CBD5E1;">
        <strong style="color: #E2E8F0;">Privacy & Safety Notice:</strong>
        MOVA analyzes spatial telemetry strictly for gaming engagement and personal movement awareness.
        All comparisons are strictly <strong>YOU vs. YOUR PREVIOUS PERFORMANCE</strong>. MOVA does not diagnose, treat, or provide clinical advice.
    </div>
    """, unsafe_allow_html=True)

    results = repo.get_recent_results(limit=25)
    sessions = repo.get_all_sessions()

    if not results:
        st.info("No recorded movement sessions yet. Play any game to activate your AI Movement Coach!")
        c1, c2 = st.columns(2)
        with c1:
            if st.button("🚀 Explore Game Library", use_container_width=True):
                st.session_state["nav_page"] = "GAME LIBRARY"
                st.rerun()
        with c2:
            if st.button("⚙️ Calibrate Sensor Rig", use_container_width=True):
                st.session_state["nav_page"] = "CALIBRATION"
                st.rerun()
        return

    # Recent Stats Overview
    last_res = results[0]
    total_games = len(results)
    avg_accuracy = sum(r["accuracy"] for r in results) / total_games
    avg_reaction = sum(r["reaction_time"] for r in results) / total_games
    avg_stability = sum(r["stability_score"] for r in results) / total_games
    avg_coord = sum(r["multimodal_coordination"] for r in results) / total_games

    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.markdown(f"""
        <div style="background: #13131F; border: 1px solid rgba(255,255,255,0.08); border-radius: 12px; padding: 16px; text-align: center;">
            <div style="font-size: 0.75rem; color: #94A3B8; text-transform: uppercase;">Games Played</div>
            <div style="font-size: 1.8rem; font-weight: 800; color: #00E5FF; margin-top: 4px;">{total_games}</div>
        </div>
        """, unsafe_allow_html=True)
    with col2:
        st.markdown(f"""
        <div style="background: #13131F; border: 1px solid rgba(255,255,255,0.08); border-radius: 12px; padding: 16px; text-align: center;">
            <div style="font-size: 0.75rem; color: #94A3B8; text-transform: uppercase;">Average Precision</div>
            <div style="font-size: 1.8rem; font-weight: 800; color: #00FF88; margin-top: 4px;">{avg_accuracy*100:.1f}%</div>
        </div>
        """, unsafe_allow_html=True)
    with col3:
        st.markdown(f"""
        <div style="background: #13131F; border: 1px solid rgba(255,255,255,0.08); border-radius: 12px; padding: 16px; text-align: center;">
            <div style="font-size: 0.75rem; color: #94A3B8; text-transform: uppercase;">Avg Reaction Time</div>
            <div style="font-size: 1.8rem; font-weight: 800; color: #FFD600; margin-top: 4px;">{avg_reaction:.2f}s</div>
        </div>
        """, unsafe_allow_html=True)
    with col4:
        st.markdown(f"""
        <div style="background: #13131F; border: 1px solid rgba(255,255,255,0.08); border-radius: 12px; padding: 16px; text-align: center;">
            <div style="font-size: 0.75rem; color: #94A3B8; text-transform: uppercase;">Coordination Index</div>
            <div style="font-size: 1.8rem; font-weight: 800; color: #FF0080; margin-top: 4px;">{avg_coord*100:.0f}</div>
        </div>
        """, unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)

    # Coach Analysis Sections
    tab1, tab2, tab3 = st.tabs(["💡 Live Movement Insight", "🎯 Next Game Prescription", "📜 Session Archives"])

    with tab1:
        st.markdown("### Latest Performance Assessment")
        
        # Prepare structured data for AI Coach
        structured_metrics = {
            "game_id": last_res.get("game_id", "mova_game"),
            "game_name": last_res.get("game_name", "Game"),
            "score": last_res.get("score", 0),
            "accuracy": last_res.get("accuracy", 0.0),
            "reaction_time": last_res.get("reaction_time", 0.0),
            "stability_score": last_res.get("stability_score", 0.0),
            "multimodal_coordination": last_res.get("multimodal_coordination", 0.0),
            "left_right_balance": last_res.get("left_right_balance", 0.5)
        }
        trend_context = {
            "sessions_count": total_games,
            "avg_score": sum(r["score"] for r in results) / total_games,
            "avg_accuracy": avg_accuracy,
            "avg_reaction_time": avg_reaction,
            "avg_stability": avg_stability,
            "avg_coordination": avg_coord
        }

        # Dynamic AI coach generation with cache or fresh on click
        cache_key = f"coach_fb_{last_res.get('timestamp')}"
        if cache_key not in st.session_state:
            with st.spinner("AI Coach analyzing multimodal kinematics..."):
                st.session_state[cache_key] = ai_coach.get_coach_feedback(structured_metrics, trend_context)

        feedback_text = st.session_state.get(cache_key, "")

        st.markdown(f"""
        <div style="background: linear-gradient(135deg, rgba(0, 229, 255, 0.08) 0%, rgba(121, 40, 202, 0.15) 100%); border: 1px solid rgba(0, 229, 255, 0.3); border-radius: 16px; padding: 24px; margin-bottom: 20px;">
            <div style="display: flex; align-items: center; gap: 10px; margin-bottom: 12px;">
                <span style="font-size: 1.4rem;">🤖</span>
                <span style="font-weight: 700; color: #00E5FF; font-size: 1.1rem; letter-spacing: 0.5px;">MOVA COACHING DIRECTIVE</span>
            </div>
            <div style="font-size: 1rem; color: #F1F5F9; line-height: 1.7; white-space: pre-line;">
{feedback_text}
            </div>
        </div>
        """, unsafe_allow_html=True)

        if st.button("🔄 Refresh Coach Feedback", key="refresh_coach_btn"):
            st.session_state.pop(cache_key, None)
            st.rerun()

    with tab2:
        st.markdown("### Adaptive Movement Recommendation")
        recommendation = RecommendationEngine.recommend_next_game(last_res, results)
        
        st.markdown(f"""
        <div style="background: #141424; border: 1px solid #7928CA; border-radius: 16px; padding: 24px; margin-bottom: 20px;">
            <div style="font-size: 0.8rem; color: #00E5FF; font-weight: 700; letter-spacing: 1.5px;">AI PRESCRIBED CHALLENGE</div>
            <h2 style="color: #FFFFFF; margin: 8px 0 12px 0;">{recommendation['game_name']}</h2>
            <div style="font-size: 0.95rem; color: #CBD5E1; margin-bottom: 16px; line-height: 1.5;">
                <strong>Reason:</strong> {recommendation['reason']}
            </div>
            <div style="display: inline-block; background: rgba(0, 229, 255, 0.15); border: 1px solid #00E5FF; color: #00E5FF; border-radius: 6px; padding: 4px 12px; font-size: 0.85rem; font-weight: 600;">
                Focus Area: {recommendation.get('focus_area', 'Multimodal Integration')}
            </div>
        </div>
        """, unsafe_allow_html=True)

        if st.button(f"🎮 Play {recommendation['game_name']}", type="primary", use_container_width=True):
            st.session_state["selected_game_id"] = recommendation["game_id"]
            st.session_state["nav_page"] = "PLAY"
            st.rerun()

    with tab3:
        st.markdown("### Past Sessions & AI Syntheses")
        if not sessions:
            st.info("Completed sessions will be logged here.")
        else:
            for s in sessions[:5]:
                st.markdown(f"""
                <div style="background: #11111E; border: 1px solid rgba(255,255,255,0.06); border-radius: 12px; padding: 16px; margin-bottom: 12px;">
                    <div style="display: flex; justify-content: space-between; align-items: center;">
                        <span style="font-weight: 700; color: #00E5FF;">Session #{s.get('session_id', 'N/A')[:8]}</span>
                        <span style="font-size: 0.85rem; color: #94A3B8;">{s.get('timestamp', '')}</span>
                    </div>
                    <div style="margin-top: 8px; font-size: 0.9rem; color: #E2E8F0;">
                        Games: <strong>{s.get('games_completed', 0)}</strong> | Score: <strong>{s.get('total_score', 0)}</strong> | Reaction: <strong>{s.get('avg_reaction_time', 0.0):.2f}s</strong>
                    </div>
                    {f'<div style="margin-top: 8px; font-size: 0.85rem; color: #94A3B8; font-style: italic;">{s.get("ai_summary")}</div>' if s.get("ai_summary") else ''}
                </div>
                """, unsafe_allow_html=True)
