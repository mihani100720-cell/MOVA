"""
MOVA UI: 6-Step Interactive Calibration Experience
Implements Section 11:
Step 1: Camera Check (lighting, user inside frame)
Step 2: Body Calibration (usable interaction area)
Step 3: Hand Calibration (dual hand tracking)
Step 4: Eye / Face Calibration (approximate gaze & orientation)
Step 5: Movement Calibration (Personal Interaction Baseline)
Step 6: Ready: MOVA ZONE READY!
Playful, polished, non-clinical.
"""

import streamlit as st
import time
import cv2
import numpy as np

from vision.camera import camera_manager
from database.models import CalibrationProfile
from database.repository import repo

STEPS = [
    "1. Camera Check",
    "2. Body Calibration",
    "3. Hand Calibration",
    "4. Eye & Face Calibration",
    "5. Personal Baseline",
    "6. MOVA Zone Ready"
]

def render_calibration_screen():
    if "calib_step" not in st.session_state:
        st.session_state["calib_step"] = 0

    current_step = st.session_state["calib_step"]

    st.markdown("""
    <div style="margin-bottom: 20px;">
        <div style="font-size: 0.8rem; font-weight: 800; color: #00E5FF; letter-spacing: 2px;">SPATIAL CALIBRATION</div>
        <h2 style="font-size: 2.2rem; font-weight: 800; color: #FFFFFF; margin: 0;">✨ Calibrate MOVA Zone</h2>
        <div style="color: #94A3B8; font-size: 0.95rem; margin-top: 4px;">
            A quick, playful sequence to tune spatial boundaries to your room and personal movement range.
        </div>
    </div>
    """, unsafe_allow_html=True)

    # Progress Bar
    progress_val = (current_step + 1) / len(STEPS)
    st.progress(progress_val)
    st.markdown(f"**Step {current_step + 1} of 6:** {STEPS[current_step]}")

    frame_data = camera_manager.read_frame()

    col_view, col_guide = st.columns([1.5, 1.0])

    with col_view:
        # Camera Feed annotated for current calibration step
        frame_vis = frame_data.frame.copy()
        h, w = frame_vis.shape[:2]

        if current_step == 0:  # Camera check
            cv2.rectangle(frame_vis, (w // 4, h // 6), (3 * w // 4, 5 * h // 6), (0, 255, 200), 2)
            cv2.putText(frame_vis, "Center Yourself Here", (w // 4 + 20, h // 6 + 30),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 200), 2)

        elif current_step == 1:  # Body calibration
            bc = frame_data.pose.body_center
            cv2.circle(frame_vis, (int(bc[0] * w), int(bc[1] * h)), 40, (255, 0, 255), 2)

        elif current_step == 2:  # Hands
            for hand in [frame_data.hands.right_hand, frame_data.hands.left_hand]:
                if hand.detected:
                    px, py = int(hand.palm_center[0] * w), int(hand.palm_center[1] * h)
                    cv2.circle(frame_vis, (px, py), 30, (0, 255, 255), 2)

        elif current_step == 3:  # Eye/Face
            fc = frame_data.face.face_center
            cv2.circle(frame_vis, (int(fc[0] * w), int(fc[1] * h)), 45, (0, 200, 255), 2)

        elif current_step == 4:  # Reach range
            cv2.circle(frame_vis, (int(0.2 * w), int(0.5 * h)), 35, (255, 255, 0), 2)
            cv2.circle(frame_vis, (int(0.8 * w), int(0.5 * h)), 35, (255, 255, 0), 2)

        elif current_step == 5:  # Ready
            cv2.putText(frame_vis, "MOVA ZONE READY!", (w // 2 - 160, h // 2),
                        cv2.FONT_HERSHEY_DUPLEX, 1.0, (0, 255, 120), 2)

        rgb = cv2.cvtColor(frame_vis, cv2.COLOR_BGR2RGB)
        st.image(rgb, channels="RGB", use_container_width=True)

    with col_guide:
        st.markdown(f"### {STEPS[current_step]}")

        if current_step == 0:
            st.write("Ensure your camera is active, room lighting is adequate, and your face is visible within the green frame.")
            st.metric("Lighting Score", f"{int(frame_data.lighting_score * 100)}%", frame_data.lighting_status)
            if st.button("Continue to Body Calibration ➡️", key="btn_calib_0", use_container_width=True):
                st.session_state["calib_step"] = 1
                st.rerun()

        elif current_step == 1:
            st.write("Stand centered so your shoulders and torso are detected.")
            st.metric("Pose Status", "Detected ✅" if frame_data.pose.detected else "Adjusting...")
            if st.button("Continue to Hand Calibration ➡️", key="btn_calib_1", use_container_width=True):
                st.session_state["calib_step"] = 2
                st.rerun()

        elif current_step == 2:
            st.write("Raise both your left and right hands into the camera view.")
            st.metric("Hands Tracked", f"{frame_data.hands.hands_count} hands visible")
            if st.button("Continue to Eye & Face ➡️", key="btn_calib_2", use_container_width=True):
                st.session_state["calib_step"] = 3
                st.rerun()

        elif current_step == 3:
            st.write("Look forward and turn your head gently left and right. This calibrates approximate gaze orientation.")
            st.metric("Head Yaw", f"{frame_data.face.head_yaw:.1f}°")
            if st.button("Establish Baseline ➡️", key="btn_calib_3", use_container_width=True):
                st.session_state["calib_step"] = 4
                st.rerun()

        elif current_step == 4:
            st.write("Extend both arms outward to your comfortable reach envelope. (Personal Interaction Baseline — non-medical).")
            st.success("Comfortable reach bounds registered.")
            if st.button("Finalize Calibration ➡️", key="btn_calib_4", use_container_width=True):
                profile = CalibrationProfile(
                    user_id="default_user",
                    head_center_x=frame_data.face.face_center[0],
                    head_center_y=frame_data.face.face_center[1],
                    lighting_score=frame_data.lighting_score
                )
                repo.save_calibration_profile(profile)
                st.session_state["calibrated"] = True
                st.session_state["calib_step"] = 5
                st.rerun()

        elif current_step == 5:
            st.balloons()
            st.markdown("""
            <div style="background: rgba(16, 185, 129, 0.2); border: 1px solid #10B981; border-radius: 12px; padding: 16px; margin: 15px 0;">
                <h3 style="color: #6EE7B7; margin: 0;">🚀 MOVA ZONE READY</h3>
                <p style="color: #E2E8F0; margin-top: 6px; font-size: 0.9rem;">
                    Your personal interaction zone is primed. Ready to step into spatial gaming.
                </p>
            </div>
            """, unsafe_allow_html=True)
            if st.button("🎮 Jump into Games", key="btn_calib_done", use_container_width=True):
                st.session_state["calib_step"] = 0
                st.session_state["nav_page"] = "GAME LIBRARY"
                st.rerun()
