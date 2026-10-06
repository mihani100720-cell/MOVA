"""
MOVA UI: Active Game Session
Handles live camera stream / Demo Mode, frame-by-frame perception processing,
Universal HUD rendering, tracking status badges, and game completion handling.
"""

import streamlit as st
import time
import cv2
import numpy as np

from vision.camera import camera_manager
from movement.metrics_engine import MovementMetricsEngine
from multimodal.fusion_engine import MultimodalFusionEngine
from games.game_manager import game_manager, GameMode, GameState
from database.repository import repo
from database.models import StandardGameResult
from voice.speech_to_text import stt_service

def render_session_screen():
    gid = st.session_state.get("selected_game_id", "gravity_flip")
    mode_str = st.session_state.get("game_mode", "CHALLENGE")
    mode = GameMode[mode_str] if mode_str in GameMode.__members__ else GameMode.CHALLENGE

    # Initialize engines in session_state if needed
    if "metrics_engine" not in st.session_state:
        st.session_state["metrics_engine"] = MovementMetricsEngine()
    if "fusion_engine" not in st.session_state:
        st.session_state["fusion_engine"] = MultimodalFusionEngine()

    metrics_engine: MovementMetricsEngine = st.session_state["metrics_engine"]
    fusion_engine: MultimodalFusionEngine = st.session_state["fusion_engine"]

    # Ensure camera is open before running session (if not in demo mode)
    if not camera_manager.is_demo_mode:
        if camera_manager.cap is None or not camera_manager.cap.isOpened():
            ok = camera_manager.start_camera()
            st.session_state["camera_started"] = ok
            if not ok:
                st.warning("⚠️ Could not open camera. Switched to Demo Mode for this session.")
                camera_manager.is_demo_mode = True
                st.session_state["demo_mode"] = True

    # Ensure active game is selected
    if game_manager.active_game is None or game_manager.active_game_id != gid or game_manager.active_game.mode != mode:
        game = game_manager.select_game(gid, mode=mode)
        metrics_engine.reset_session()
        fusion_engine.reset_session()
    else:
        game = game_manager.active_game


    # Status Bar Header
    c_status, c_actions = st.columns([2.0, 1.0])
    with c_status:
        # Status indicators (Section 47)
        cam_active = not camera_manager.is_demo_mode
        demo_label = "🟡 DEMO MODE (Simulated)" if camera_manager.is_demo_mode else "🟢 CAMERA LIVE"
        hands_indicator = "🟢 HANDS" if st.session_state.get("last_hands_detected", True) else "⚪ HANDS"
        face_indicator = "🟢 FACE" if st.session_state.get("last_face_detected", True) else "⚪ FACE"

        st.markdown(f"""
        <div style="display: flex; gap: 12px; align-items: center; margin-bottom: 8px; font-size: 0.85rem; font-weight: 700;">
            <span style="color: #A78BFA;">TRACKING ●</span>
            <span>{demo_label}</span>
            <span>{hands_indicator}</span>
            <span>{face_indicator}</span>
            <span style="color: #6EE7B7;">MODE: [{mode.value}]</span>
        </div>
        """, unsafe_allow_html=True)

    with c_actions:
        btn_c1, btn_c2, btn_c3 = st.columns(3)
        with btn_c1:
            if game.state == GameState.PLAYING:
                if st.button("⏸ Pause", key="sess_pause", use_container_width=True):
                    game.pause()
                    st.rerun()
            elif game.state == GameState.PAUSED:
                if st.button("▶ Resume", key="sess_resume", use_container_width=True):
                    game.resume()
                    st.rerun()
            elif game.state == GameState.READY:
                if st.button("🚀 Start", key="sess_start", use_container_width=True):
                    game.start()
                    st.rerun()
        with btn_c2:
            if st.button("⏹ Stop", key="sess_stop", use_container_width=True):
                game.stop()
                st.session_state["nav_page"] = "REPORTS"
                st.rerun()
        with btn_c3:
            if st.button("📖 Manual", key="sess_manual", use_container_width=True):
                st.session_state["nav_page"] = "HOW TO PLAY"
                st.rerun()

    # Video & Spatial Zone Container
    frame_placeholder = st.empty()
    live_metrics_placeholder = st.empty()

    # Frame processing loop
    # In Streamlit, if game is PLAYING, we run a continuous burst of frames
    is_playing = (game.state == GameState.PLAYING)

    if not is_playing:
        # Read single preview frame
        frame_data = camera_manager.read_frame()
        metrics = metrics_engine.process_frame(frame_data, dt=0.033)
        fusion = fusion_engine.fuse_frame(frame_data, metrics, required_modalities=game.required_modalities)
        rendered = game_manager.render_game_view(frame_data.frame)
        rgb_preview = cv2.cvtColor(rendered, cv2.COLOR_BGR2RGB)
        frame_placeholder.image(rgb_preview, channels="RGB", use_container_width=True)

        if game.state == GameState.COMPLETED:
            st.success("🎉 Activity Completed! Saving your session data...")
            # Compile standard game result
            sess_id = st.session_state.get("session_id", f"SES-{int(time.time())}")
            movement_sum = metrics_engine.get_session_summary()
            fusion_sum = fusion_engine.get_session_summary()
            game_res = game.get_results(sess_id, movement_sum, fusion_sum)
            repo.save_game_result(game_res, user_id="default_user")

            try:
                from reports.report_recorder import record_game_session
                record_game_session(game_res.to_dict(), {"id": game.game_id, "title": game.game_name})
            except Exception as _e:
                pass

            st.session_state["last_completed_game"] = game_res.to_dict()
            st.session_state["nav_page"] = "REPORTS"
            time.sleep(1.0)
            st.rerun()

        elif game.state == GameState.READY:
            st.info("👆 Click **🚀 Start** above or say *'Start'* to begin the activity!")

    else:
        # Run active gameplay frame loop
        # Short burst per rerun ensures ultra-responsive UI without WebSocket choking
        loop_duration = 0.2
        t_start = time.perf_counter()

        while time.perf_counter() - t_start < loop_duration:
            frame_data = camera_manager.read_frame()
            dt = frame_data.dt

            # Update movement and multimodal intelligence
            metrics = metrics_engine.process_frame(frame_data, dt)
            fusion = fusion_engine.fuse_frame(frame_data, metrics, required_modalities=game.required_modalities)

            # Check for voice input
            voice_cmd = stt_service.consume_last_command()
            if voice_cmd:
                game_manager.handle_voice_input(voice_cmd)

            # Update game logic
            game_manager.update_frame(dt, frame_data, metrics, fusion)

            # Render augmented game frame
            rendered = game_manager.render_game_view(frame_data.frame)
            rgb_view = cv2.cvtColor(rendered, cv2.COLOR_BGR2RGB)
            frame_placeholder.image(rgb_view, channels="RGB", use_container_width=True)

            # Check if game reached end of duration
            if game.state == GameState.COMPLETED:
                break

        # Trigger reactive rerun to keep loop smooth
        st.rerun()
