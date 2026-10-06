"""
MOVA UI: Movement Lab Diagnostic Studio
Implements Section 38:
Developer & diagnostic experience displaying raw video feed, MediaPipe joint skeletons,
estimated gaze vectors, dual hand skeletal trees, real-time joint angles, kinematics, and FPS.
"""

import streamlit as st
import cv2
import numpy as np
import time

from vision.camera import camera_manager
from movement.metrics_engine import MovementMetricsEngine
from multimodal.fusion_engine import MultimodalFusionEngine
from utils.privacy import FPSCounter

def render_movement_lab():
    st.markdown("""
    <div style="margin-bottom: 16px;">
        <div style="font-size: 0.8rem; font-weight: 800; color: #38BDF8; letter-spacing: 2px;">DEVELOPER & DIAGNOSTIC STUDIO</div>
        <h2 style="font-size: 2.2rem; font-weight: 800; color: #FFFFFF; margin: 0;">🔬 Movement Lab</h2>
        <div style="color: #94A3B8; font-size: 0.95rem; margin-top: 4px;">
            Real-time OpenCV webcam stream with MediaPipe Pose, Hand & Face tracking, joint angles, and spatial telemetry.
        </div>
    </div>
    """, unsafe_allow_html=True)

    # Stream Controls
    c_ctrl1, c_ctrl2 = st.columns([1.5, 1.0])
    with c_ctrl1:
        is_streaming = st.toggle("🔴 Real-Time Camera Tracking", value=st.session_state.get("lab_streaming", True), key="lab_stream_toggle")
        st.session_state["lab_streaming"] = is_streaming
    with c_ctrl2:
        cam_source = "🟡 DEMO SIMULATOR" if camera_manager.is_demo_mode else "🟢 HARDWARE WEBCAM"
        st.markdown(f"""
        <div style="text-align: right; padding-top: 8px; font-size: 0.85rem; font-weight: 700; color: #00E5FF;">
            FEED SOURCE: {cam_source}
        </div>
        """, unsafe_allow_html=True)

    if "lab_fps" not in st.session_state:
        st.session_state["lab_fps"] = FPSCounter()
    if "lab_metrics" not in st.session_state:
        st.session_state["lab_metrics"] = MovementMetricsEngine()
    if "lab_fusion" not in st.session_state:
        st.session_state["lab_fusion"] = MultimodalFusionEngine()

    # Ensure camera is open
    if not camera_manager.is_demo_mode:
        if camera_manager.cap is None or not camera_manager.cap.isOpened():
            camera_manager.start_camera()

    fps_counter: FPSCounter = st.session_state["lab_fps"]
    metrics_engine: MovementMetricsEngine = st.session_state["lab_metrics"]
    fusion_engine: MultimodalFusionEngine = st.session_state["lab_fusion"]

    c_stream, c_telemetry = st.columns([1.6, 1.0])

    with c_stream:
        img_placeholder = st.empty()
        st.caption("Live video annotated with MediaPipe landmark skeleton, dual hands, and gaze vector.")

    with c_telemetry:
        tel_placeholder = st.empty()

    def process_and_draw():
        frame_data = camera_manager.read_frame()
        dt = frame_data.dt
        current_fps = fps_counter.tick()

        metrics = metrics_engine.process_frame(frame_data, dt)
        fusion = fusion_engine.fuse_frame(frame_data, metrics)

        # Annotate frame with diagnostic overlays
        vis_frame = frame_data.frame.copy() if frame_data.frame is not None else np.zeros((480, 640, 3), dtype=np.uint8)
        h, w = vis_frame.shape[:2]

        # Draw Pose Skeleton
        if frame_data.pose.detected:
            for lm_name, pt in frame_data.pose.landmarks.items():
                px, py = int(pt[0] * w), int(pt[1] * h)
                cv2.circle(vis_frame, (px, py), 5, (0, 255, 120), -1, cv2.LINE_AA)
                cv2.putText(vis_frame, lm_name.split("_")[-1], (px + 6, py - 4),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.35, (0, 255, 200), 1)

            # Draw Torso center
            bc = frame_data.pose.body_center
            cv2.circle(vis_frame, (int(bc[0] * w), int(bc[1] * h)), 8, (255, 0, 255), 2, cv2.LINE_AA)

        # Draw Hand Landmarks
        for hand, col in [(frame_data.hands.right_hand, (0, 255, 255)), (frame_data.hands.left_hand, (255, 150, 0))]:
            if hand.detected:
                px, py = int(hand.palm_center[0] * w), int(hand.palm_center[1] * h)
                cv2.circle(vis_frame, (px, py), 9, col, 2, cv2.LINE_AA)
                cv2.putText(vis_frame, f"{hand.label}: {hand.gesture}", (px - 25, py - 14),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.45, col, 1, cv2.LINE_AA)

        # Draw Gaze Vector
        gx, gy = frame_data.eyes.gaze_target_coords
        fc = frame_data.face.face_center
        cv2.arrowedLine(vis_frame, (int(fc[0] * w), int(fc[1] * h)),
                        (int(gx * w), int(gy * h)), (255, 255, 0), 2, cv2.LINE_AA, tipLength=0.2)
        cv2.circle(vis_frame, (int(gx * w), int(gy * h)), 10, (255, 255, 0), 1, cv2.LINE_AA)
        cv2.putText(vis_frame, f"GAZE: {frame_data.eyes.gaze_direction}", (int(gx * w) + 12, int(gy * h) + 4),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.4, (255, 255, 0), 1)

        # Status text on frame
        mode_text = "SIMULATED RIG" if frame_data.is_demo_mode else "LIVE WEBCAM"
        cv2.putText(vis_frame, f"{mode_text} | FPS: {current_fps:.1f}", (15, 30),
                    cv2.FONT_HERSHEY_DUPLEX, 0.65, (0, 255, 120), 2)

        # Display image
        rgb_vis = cv2.cvtColor(vis_frame, cv2.COLOR_BGR2RGB)
        img_placeholder.image(rgb_vis, channels="RGB", use_container_width=True)

        # Render Telemetry sidebar
        angles = metrics.get("angles", {})
        kin = metrics.get("kinematics", {})
        stab = metrics.get("stability", {})

        with tel_placeholder.container():
            st.markdown(f"""
            <div style="background: #151522; border-radius: 12px; padding: 14px; border: 1px solid rgba(255,255,255,0.08); font-size: 0.85rem;">
                <div style="font-weight: 700; color: #38BDF8; margin-bottom: 6px;">MEDIAPIPE TRACKING</div>
                <div>● Pose Detected: <b style="color: {'#00FF88' if frame_data.pose.detected else '#EF4444'}">{frame_data.pose.detected}</b> ({frame_data.pose.confidence*100:.0f}%)</div>
                <div>● Hands Count: <b>{frame_data.hands.hands_count}</b></div>
                <div>● Head Yaw / Pitch: <b>{frame_data.face.head_yaw:.1f}° / {frame_data.face.head_pitch:.1f}°</b></div>
                <div>● Lighting: <b>{frame_data.lighting_status} ({frame_data.lighting_score})</b></div>
                <hr style="margin: 8px 0; border-color: rgba(255,255,255,0.08);">
                <div style="font-weight: 700; color: #A78BFA; margin-bottom: 6px;">JOINT ANGLES</div>
                <div>● Left Elbow: <b>{angles.get('left_elbow', 0.0):.1f}°</b></div>
                <div>● Right Elbow: <b>{angles.get('right_elbow', 0.0):.1f}°</b></div>
                <div>● Left Shoulder: <b>{angles.get('left_shoulder', 0.0):.1f}°</b></div>
                <div>● Right Shoulder: <b>{angles.get('right_shoulder', 0.0):.1f}°</b></div>
                <hr style="margin: 8px 0; border-color: rgba(255,255,255,0.08);">
                <div style="font-weight: 700; color: #FBBF24; margin-bottom: 6px;">KINEMATICS & STABILITY</div>
                <div>● Right Hand Speed: <b>{kin.get('right_hand', {}).get('speed', 0.0):.2f}</b></div>
                <div>● Left Hand Speed: <b>{kin.get('left_hand', {}).get('speed', 0.0):.2f}</b></div>
                <div>● Stability Score: <b>{stab.get('stability_score', 95.0)}/100</b></div>
                <div>● Posture Status: <b>{stab.get('posture_status', 'Steady')}</b></div>
                <div>● Multimodal Sync: <b>{fusion.get('multimodal_sync_score', 90.0)}%</b></div>
            </div>
            """, unsafe_allow_html=True)

    if not is_streaming:
        process_and_draw()
        st.info("Stream paused. Click the toggle above to resume live camera tracking.")
    else:
        # Run smooth batch loop
        t_start = time.perf_counter()
        while time.perf_counter() - t_start < 0.8:
            process_and_draw()
            time.sleep(0.02)
        st.rerun()
