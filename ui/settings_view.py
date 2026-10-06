"""
MOVA UI: Settings & Accessibility Controls
Implements Section 39, 41, 43:
Camera configuration, Demo Mode toggle, API Key management, and accessibility preferences.
"""

import streamlit as st
import cv2
import os
from vision.camera import camera_manager
from config.settings import settings


def render_settings_screen():
    st.markdown("""
    <div style="margin-bottom: 20px;">
        <div style="font-size: 0.8rem; font-weight: 800; color: #E2E8F0; letter-spacing: 2px;">PLATFORM CONFIGURATION</div>
        <h2 style="font-size: 2.2rem; font-weight: 800; color: #FFFFFF; margin: 0;">⚙️ Settings & Accessibility</h2>
        <div style="color: #94A3B8; font-size: 0.95rem; margin-top: 4px;">
            Manage vision devices, simulation mode, API credentials, and accessibility features.
        </div>
    </div>
    """, unsafe_allow_html=True)

    tab_vis, tab_api, tab_access, tab_priv = st.tabs(["📷 Vision & Hardware", "🔑 AI & Voice APIs", "♿ Accessibility", "🔒 Privacy Architecture"])

    with tab_vis:
        st.markdown("### Camera & Hardware Pipeline")

        # ── Camera Status Banner ───────────────────────────────────────────────
        is_demo = camera_manager.is_demo_mode
        cap_open = camera_manager.cap is not None and camera_manager.cap.isOpened()

        if is_demo:
            st.markdown("""
            <div style="background: rgba(250,204,21,0.12); border: 1px solid rgba(250,204,21,0.45); border-radius: 10px; padding: 12px 18px; margin-bottom: 16px;">
                <div style="font-weight: 800; color: #FACC15; margin-bottom: 4px;">🟡 DEMO / SIMULATION MODE ACTIVE</div>
                <div style="font-size: 0.88rem; color: #CBD5E1;">
                    Synthetic kinematics are being generated. Uncheck "Use Demo Simulation" below and click
                    <strong>Activate Camera</strong> to switch to live webcam tracking.
                </div>
            </div>
            """, unsafe_allow_html=True)
        elif cap_open:
            ret, _ = camera_manager.cap.read()
            cam_ok = ret
            color = "#00FF88" if cam_ok else "#EF4444"
            label = "LIVE WEBCAM FEED ACTIVE" if cam_ok else "CAMERA OPENED BUT NO FRAMES"
            st.markdown(f"""
            <div style="background: rgba(0,229,255,0.1); border: 1px solid rgba(0,229,255,0.4); border-radius: 10px; padding: 12px 18px; margin-bottom: 16px;">
                <div style="font-weight: 800; color: {color}; margin-bottom: 4px;">🟢 {label}</div>
                <div style="font-size: 0.88rem; color: #CBD5E1;">
                    MediaPipe Pose, Hand & Face Landmarker pipelines are running on every captured frame.
                    Resolution: 640×480, Target FPS: 30.
                </div>
            </div>
            """, unsafe_allow_html=True)
        else:
            st.markdown("""
            <div style="background: rgba(239,68,68,0.1); border: 1px solid rgba(239,68,68,0.4); border-radius: 10px; padding: 12px 18px; margin-bottom: 16px;">
                <div style="font-weight: 800; color: #EF4444; margin-bottom: 4px;">⚫ CAMERA NOT STARTED</div>
                <div style="font-size: 0.88rem; color: #CBD5E1;">
                    Disable Demo Mode and click <strong>Activate Camera</strong> to open the webcam.
                </div>
            </div>
            """, unsafe_allow_html=True)

        # ── Demo Mode Toggle ───────────────────────────────────────────────────
        demo_active = st.checkbox(
            "🧪 Use Demo Simulation (no webcam needed)",
            value=is_demo,
            help="Simulates realistic dual-hand and body kinematics for presentations without a camera."
        )
        if demo_active != is_demo:
            if demo_active:
                camera_manager.stop_camera()
                camera_manager.is_demo_mode = True
                st.session_state["demo_mode"] = True
                st.session_state["camera_started"] = False
                st.success("Demo Mode activated. Synthetic spatial rig is now running.")
            else:
                camera_manager.is_demo_mode = False
                st.session_state["demo_mode"] = False
            st.rerun()

        # ── Camera Index Picker ────────────────────────────────────────────────
        cam_idx = st.number_input("Camera Device Index", min_value=0, max_value=9, value=camera_manager.camera_index,
                                  help="0 = built-in webcam, 1 = USB camera, etc.")

        col_btn1, col_btn2 = st.columns(2)
        with col_btn1:
            if st.button("🎥 Activate Camera", type="primary", use_container_width=True):
                camera_manager.camera_index = int(cam_idx)
                camera_manager.stop_camera()
                camera_manager.is_demo_mode = False
                st.session_state["demo_mode"] = False
                ok = camera_manager.start_camera()
                st.session_state["camera_started"] = ok
                if ok:
                    st.success(f"✅ Camera index {cam_idx} opened successfully — Live MOVA Zone active!")
                else:
                    camera_manager.is_demo_mode = True
                    st.session_state["demo_mode"] = True
                    st.error(f"❌ Could not open camera index {cam_idx}. Check device connection. Fallback: Demo Mode.")
                st.rerun()

        with col_btn2:
            if st.button("⏹ Stop Camera", use_container_width=True):
                camera_manager.stop_camera()
                st.session_state["camera_started"] = False
                st.info("Camera capture stopped.")
                st.rerun()

        # ── Camera Test Preview ────────────────────────────────────────────────
        if not is_demo and cap_open:
            st.markdown("#### Live Camera Preview (single frame)")
            if st.button("📸 Capture Test Frame", use_container_width=True):
                frame_data = camera_manager.read_frame()
                if frame_data.frame is not None:
                    import cv2, numpy as np
                    rgb = cv2.cvtColor(frame_data.frame, cv2.COLOR_BGR2RGB)
                    st.image(rgb, channels="RGB", use_container_width=True,
                             caption=f"Live Frame — Pose: {frame_data.pose.detected} | Hands: {frame_data.hands.hands_count} | Confidence: {frame_data.overall_confidence:.2f}")
                else:
                    st.warning("No frame captured — ensure camera is connected.")

        # ── MediaPipe Model Status ─────────────────────────────────────────────
        st.markdown("#### MediaPipe Vision Pipeline Status")
        pose_ok = camera_manager.pose_detector is not None
        hand_ok = camera_manager.hand_detector is not None
        face_ok = camera_manager.face_detector is not None
        st.markdown(f"""
        <div style="background: #13131F; border-radius: 10px; padding: 14px; font-size: 0.88rem; border: 1px solid rgba(255,255,255,0.07);">
            <div>{'✅' if pose_ok else '❌'} <b>PoseLandmarker</b> (33 body joints) — {'Loaded' if pose_ok else 'Not loaded'}</div>
            <div style="margin-top: 6px;">{'✅' if hand_ok else '❌'} <b>HandLandmarker</b> (21 pts × 2 hands) — {'Loaded' if hand_ok else 'Not loaded'}</div>
            <div style="margin-top: 6px;">{'✅' if face_ok else '❌'} <b>FaceLandmarker</b> (478 mesh pts + blendshapes) — {'Loaded' if face_ok else 'Not loaded'}</div>
        </div>
        """, unsafe_allow_html=True)

    with tab_api:
        st.markdown("### Cloud Intelligence Integrations (Optional)")
        st.caption("AI is an enhancement, not the foundation. MOVA runs with high precision offline.")

        gemini_k = st.text_input("Gemini API Key", value=settings.GEMINI_API_KEY, type="password")
        openai_k = st.text_input("OpenAI API Key", value=settings.OPENAI_API_KEY, type="password")
        eleven_k = st.text_input("ElevenLabs API Key", value=settings.ELEVENLABS_API_KEY, type="password")

        if st.button("Save API Configuration", key="btn_save_api"):
            settings.GEMINI_API_KEY = gemini_k
            settings.OPENAI_API_KEY = openai_k
            settings.ELEVENLABS_API_KEY = eleven_k
            st.success("API keys updated in memory.")

    with tab_access:
        st.markdown("### Accessibility Preferences")
        st.checkbox("High Contrast Game Overlays", value=False)
        st.checkbox("Reduced Motion / Disable Particle Trails", value=False)
        st.slider("Target Size Scaling", min_value=0.8, max_value=1.5, value=1.0, step=0.1)
        st.slider("Global Gameplay Speed Modifier", min_value=0.5, max_value=1.5, value=1.0, step=0.1)
        st.write("MOVA is designed for all ability envelopes. Games support seated, upper-body only, or one-handed modes.")

    with tab_priv:
        st.markdown("### Privacy Architecture")
        st.markdown("""
        ```
        Camera Feed
            ↓
        100% LOCAL COMPUTER VISION (MediaPipe / OpenCV)
            ↓
        Numerical Coordinates / Joint Angles / Scalars
            ↓
        Spatial Game Engine
        ```
        - **Zero Raw Video Uploaded:** Camera frames never leave your local machine.
        - **Structured Scalar Metrics Only:** If Gemini or OpenAI is used, only non-identifiable numbers are sent (e.g. `reaction: 0.72s, accuracy: 0.88`).
        - **No Facial Biometrics Saved:** No face meshes or voice recordings are persisted to disk or cloud.
        """)
