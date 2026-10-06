"""
MOVA UI: Game Library
Implements Section 37:
Category filtering (ALL, REACTION, COORDINATION, BALANCE, REACH, GESTURE, GAZE, RHYTHM, MEMORY, MULTIMODAL)
Rich game cards showing title, artwork, modalities, movement focus, duration, difficulty, and personal best.
"""

import streamlit as st
from games.game_manager import GameRegistry
from database.repository import repo

def render_game_library():
    st.markdown("""
    <div style="margin-bottom: 20px;">
        <h2 style="font-size: 2.2rem; font-weight: 800; color: #FFFFFF; margin: 0;">🎮 Game Library</h2>
        <p style="color: #94A3B8; font-size: 0.95rem; margin-top: 4px;">Select an experience to review its manual, practice moves, or launch directly into the MOVA Zone.</p>
    </div>
    """, unsafe_allow_html=True)

    # Filter chips
    categories = ["ALL", "REACTION", "COORDINATION", "STABILITY", "GESTURE", "MULTIMODAL", "RHYTHM"]
    sel_cat = st.radio("Category Filter:", categories, horizontal=True, label_visibility="collapsed")

    filtered = {}
    for gid, gdata in GameRegistry.CATALOG.items():
        if sel_cat == "ALL" or gdata["category"] == sel_cat:
            filtered[gid] = gdata

    st.markdown("<div style='margin-top: 15px;'></div>", unsafe_allow_html=True)

    # Render 2-column or 3-column game cards
    cols = st.columns(2)
    items = list(filtered.items())

    for idx, (gid, gdata) in enumerate(items):
        col = cols[idx % 2]
        with col:
            # Query personal baseline for best score
            baseline = repo.get_personal_baseline("default_user", gid)
            best_score_str = f"{baseline.best_score:,} pts" if baseline else "Unranked"
            sessions_count = baseline.sessions_count if baseline else 0

            modalities_str = " &bull; ".join(gdata["modalities"])

            st.markdown(f"""
            <div style="background: #151522; border: 1px solid rgba(255, 255, 255, 0.1); border-left: 5px solid {gdata['color']}; border-radius: 14px; padding: 20px; margin-bottom: 18px;">
                <div style="display: flex; justify-content: space-between; align-items: flex-start;">
                    <div>
                        <span style="font-size: 0.72rem; font-weight: 800; color: {gdata['color']}; letter-spacing: 1.5px; text-transform: uppercase;">{gdata['category']}</span>
                        <h3 style="margin: 4px 0 6px 0; color: #FFFFFF; font-size: 1.35rem;">{gdata['title']}</h3>
                    </div>
                    <div style="font-size: 2.2rem;">{gdata['icon']}</div>
                </div>
                <p style="color: #94A3B8; font-size: 0.88rem; min-height: 42px; margin-bottom: 12px;">{gdata['description']}</p>
                <div style="background: rgba(0, 0, 0, 0.25); border-radius: 8px; padding: 10px; margin-bottom: 14px; font-size: 0.8rem; color: #CBD5E1;">
                    <div><b>Modalities:</b> {modalities_str}</div>
                    <div style="margin-top: 4px;"><b>Movement Focus:</b> <span style="color: #38BDF8;">{gdata['movement_focus']}</span></div>
                    <div style="margin-top: 4px; display: flex; justify-content: space-between;">
                        <span><b>Duration:</b> {gdata['duration']}</span>
                        <span><b>Your Personal Best:</b> <span style="color: #FACC15; font-weight: bold;">{best_score_str}</span> ({sessions_count} rounds)</span>
                    </div>
                </div>
            </div>
            """, unsafe_allow_html=True)

            btn_col1, btn_col2 = st.columns(2)
            with btn_col1:
                if st.button("📖 How to Play", key=f"btn_manual_{gid}", use_container_width=True):
                    st.session_state["selected_game_id"] = gid
                    st.session_state["nav_page"] = "HOW TO PLAY"
                    st.rerun()
            with btn_col2:
                if st.button("▶ Start Game", key=f"btn_play_{gid}", use_container_width=True):
                    st.session_state["selected_game_id"] = gid
                    st.session_state["game_mode"] = "CHALLENGE"
                    st.session_state["nav_page"] = "PLAY"
                    st.rerun()
