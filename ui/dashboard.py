"""
MOVA UI: Home Screen Dashboard
Implements Section 36:
Hero: MOVA — MOVE. PLAY. IMPROVE.
Continue Session, Play Now, Recommended Game, Last Session Snapshot.
Futuristic, playful, premium spatial design.
"""

import streamlit as st
from games.game_manager import GameRegistry
from database.repository import repo
from ml.recommendation_engine import RecommendationEngine

def render_home_screen():
    st.markdown("""
    <div style="text-align: center; padding: 25px 10px 15px 10px;">
        <div style="font-size: 0.9rem; font-weight: 700; letter-spacing: 3px; color: #00E5FF; text-transform: uppercase; margin-bottom: 6px;">
            ✦ MULTIMODAL SPATIAL GAMING & MOVEMENT INTELLIGENCE ✦
        </div>
        <h1 style="font-size: 3.6rem; font-weight: 900; background: linear-gradient(135deg, #00E5FF 0%, #7928CA 50%, #FF0080 100%); -webkit-background-clip: text; -webkit-text-fill-color: transparent; margin: 0; letter-spacing: -1px;">
            M O V A
        </h1>
        <div style="font-size: 1.35rem; font-weight: 600; color: #E2E8F0; margin-top: 6px; letter-spacing: 1px;">
            MOVE. PLAY. IMPROVE.
        </div>
        <p style="color: #94A3B8; max-width: 680px; margin: 12px auto 20px auto; font-size: 0.95rem; line-height: 1.5;">
            MOVA doesn't just watch your body. It understands how eyes, face, hands, arms, body, and voice interact together in space.
        </p>
    </div>
    """, unsafe_allow_html=True)

    # Fetch recent stats
    results = repo.get_recent_results(limit=10)
    sessions = repo.get_all_sessions()
    last_res = results[0] if results else None
    recommendation = RecommendationEngine.recommend_next_game(last_res, results)

    # Hero Action Cards
    c1, c2, c3 = st.columns([1.2, 1.2, 1.0])

    with c1:
        st.markdown(f"""
        <div style="background: linear-gradient(135deg, rgba(121, 40, 202, 0.25) 0%, rgba(0, 112, 243, 0.15) 100%); border: 1px solid rgba(121, 40, 202, 0.4); border-radius: 16px; padding: 22px; height: 100%;">
            <div style="font-size: 0.75rem; font-weight: 700; color: #00E5FF; letter-spacing: 2px;">AI RECOMMENDED NEXT</div>
            <h3 style="margin: 6px 0 10px 0; color: #FFFFFF; font-size: 1.4rem;">{recommendation['game_name']}</h3>
            <p style="color: #CBD5E1; font-size: 0.88rem; min-height: 48px;">{recommendation['reason']}</p>
            <div style="margin-top: 10px; font-size: 0.8rem; color: #A78BFA;"><b>Focus:</b> {recommendation['target_focus']}</div>
        </div>
        """, unsafe_allow_html=True)
        if st.button(f"🚀 Play {recommendation['game_name'].split()[0]}", key="btn_hero_rec", use_container_width=True):
            st.session_state["selected_game_id"] = recommendation["game_id"]
            st.session_state["nav_page"] = "HOW TO PLAY"
            st.rerun()

    with c2:
        last_score_str = f"{last_res['score']:,}" if last_res else "No games yet"
        last_game_str = last_res['game_name'] if last_res else "Ready for Round 1"
        st.markdown(f"""
        <div style="background: linear-gradient(135deg, rgba(0, 229, 255, 0.15) 0%, rgba(20, 20, 35, 0.4) 100%); border: 1px solid rgba(0, 229, 255, 0.35); border-radius: 16px; padding: 22px; height: 100%;">
            <div style="font-size: 0.75rem; font-weight: 700; color: #38BDF8; letter-spacing: 2px;">LAST ACTIVITY SNAPSHOT</div>
            <h3 style="margin: 6px 0 10px 0; color: #FFFFFF; font-size: 1.4rem;">{last_game_str}</h3>
            <div style="font-size: 1.6rem; font-weight: 800; color: #FACC15;">{last_score_str} <span style="font-size: 0.85rem; color: #94A3B8; font-weight: normal;">PTS</span></div>
            <div style="margin-top: 10px; font-size: 0.85rem; color: #94A3B8;">Personal comparison baseline active</div>
        </div>
        """, unsafe_allow_html=True)
        if st.button("🎮 Browse Game Library", key="btn_hero_lib", use_container_width=True):
            st.session_state["nav_page"] = "GAME LIBRARY"
            st.rerun()

    with c3:
        st.markdown(f"""
        <div style="background: rgba(30, 30, 50, 0.5); border: 1px solid rgba(255, 255, 255, 0.12); border-radius: 16px; padding: 22px; height: 100%;">
            <div style="font-size: 0.75rem; font-weight: 700; color: #E2E8F0; letter-spacing: 2px;">SYSTEM READINESS</div>
            <div style="margin-top: 12px; font-size: 0.9rem; color: #CBD5E1;">
                <div>● Camera: <b>{'Demo Mode' if st.session_state.get('demo_mode') else 'Active'}</b></div>
                <div style="margin-top: 6px;">● MediaPipe: <b>Loaded</b></div>
                <div style="margin-top: 6px;">● Calibration: <b>{'Calibrated' if st.session_state.get('calibrated') else 'Standard Baseline'}</b></div>
            </div>
        </div>
        """, unsafe_allow_html=True)
        if st.button("⚙️ Calibrate MOVA Zone", key="btn_hero_calib", use_container_width=True):
            st.session_state["nav_page"] = "CALIBRATION"
            st.rerun()

    st.markdown("<div style='margin-top: 35px;'></div>", unsafe_allow_html=True)

    # 10 Games Quick Grid preview
    st.markdown("### 🌟 Featured Spatial Experiences")
    cols = st.columns(5)
    games_list = list(GameRegistry.CATALOG.items())

    for idx, (gid, gdata) in enumerate(games_list[:10]):
        col = cols[idx % 5]
        with col:
            st.markdown(f"""
            <div style="background: #181826; border: 1px solid rgba(255,255,255,0.08); border-radius: 12px; padding: 14px; text-align: center; margin-bottom: 12px; transition: transform 0.2s;">
                <div style="font-size: 2.2rem; margin-bottom: 6px;">{gdata['icon']}</div>
                <div style="font-weight: 700; color: #FFFFFF; font-size: 0.95rem; white-space: nowrap; overflow: hidden; text-overflow: ellipsis;">{gdata['title']}</div>
                <div style="font-size: 0.75rem; color: {gdata['color']}; margin-top: 3px; font-weight: 600;">{gdata['category']}</div>
            </div>
            """, unsafe_allow_html=True)
            if st.button(f"View", key=f"btn_quick_view_{gid}", use_container_width=True):
                st.session_state["selected_game_id"] = gid
                st.session_state["nav_page"] = "HOW TO PLAY"
                st.rerun()
