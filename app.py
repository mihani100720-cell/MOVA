"""
MOVA — Multimodal Spatial Gaming & Movement Intelligence Platform
Main Application Entry Point (Streamlit)
MOVE. PLAY. IMPROVE.
"""

import streamlit as st
import time
import uuid

# Must be the very first Streamlit command
st.set_page_config(
    page_title="MOVA — Multimodal Spatial Gaming",
    page_icon="🌌",
    layout="wide",
    initial_sidebar_state="expanded"
)

from config.settings import settings
from vision.camera import camera_manager
from games.game_manager import GameRegistry, game_manager
from database.sqlite import init_db
from database.repository import repo

# Import UI screens
from ui.dashboard import render_home_screen
from ui.game_library import render_game_library
from ui.game_manual import render_game_manual
from ui.session import render_session_screen
from ui.movement_lab import render_movement_lab
from ui.progress import render_progress_screen
from ui.ai_coach_view import render_ai_coach_screen
from ui.reports_view import render_reports_screen
from ui.settings_view import render_settings_screen
from ui.calibration import render_calibration_screen

# Global Futuristic Spatial Theme CSS
CUSTOM_CSS = """
<style>
    @import url('https://fonts.googleapis.com/css2?family=Outfit:wght@300;400;500;600;700;800;900&family=Inter:wght@400;500;600;700&display=swap');

    /* Global Dark Spatial Styling */
    html, body, [class*="css"] {
        font-family: 'Outfit', 'Inter', -apple-system, sans-serif;
    }

    .stApp {
        background-color: #080811;
        background-image: 
            radial-gradient(at 0% 0%, rgba(121, 40, 202, 0.12) 0px, transparent 50%),
            radial-gradient(at 100% 0%, rgba(0, 229, 255, 0.08) 0px, transparent 50%),
            radial-gradient(at 50% 100%, rgba(255, 0, 128, 0.08) 0px, transparent 50%);
        color: #F1F5F9;
    }

    /* Custom Scrollbar */
    ::-webkit-scrollbar {
        width: 6px;
        height: 6px;
    }
    ::-webkit-scrollbar-track {
        background: #080811;
    }
    ::-webkit-scrollbar-thumb {
        background: #1E1E38;
        border-radius: 3px;
    }
    ::-webkit-scrollbar-thumb:hover {
        background: #00E5FF;
    }

    /* Sidebar Styling */
    section[data-testid="stSidebar"] {
        background-color: #0D0D1A !important;
        border-right: 1px solid rgba(255, 255, 255, 0.07);
    }
    section[data-testid="stSidebar"] div.stButton > button {
        text-align: left;
        border-radius: 10px;
        font-weight: 600;
        letter-spacing: 0.3px;
        transition: all 0.2s ease-in-out;
    }

    /* Button Primary Glow */
    button[kind="primary"] {
        background: linear-gradient(135deg, #00E5FF 0%, #7928CA 100%) !important;
        border: none !important;
        color: #FFFFFF !important;
        font-weight: 700 !important;
        box-shadow: 0 4px 14px rgba(0, 229, 255, 0.3) !important;
        transition: all 0.25s ease !important;
    }
    button[kind="primary"]:hover {
        transform: translateY(-1px);
        box-shadow: 0 6px 20px rgba(0, 229, 255, 0.5) !important;
    }

    /* Cards & Containers */
    .mova-glass-card {
        background: rgba(19, 19, 32, 0.7);
        backdrop-filter: blur(12px);
        border: 1px solid rgba(255, 255, 255, 0.08);
        border-radius: 16px;
        padding: 20px;
    }

    /* Hide default Streamlit top header line */
    header[data-testid="stHeader"] {
        background-color: transparent !important;
    }
    footer {
        display: none !important;
    }
</style>
"""

st.markdown(CUSTOM_CSS, unsafe_allow_html=True)

# Initialize Session State
if "nav_page" not in st.session_state:
    st.session_state["nav_page"] = "HOME"
if "demo_mode" not in st.session_state:
    # .env has MOVA_DEMO_MODE=false so default to False (use real camera)
    st.session_state["demo_mode"] = settings.DEMO_MODE_DEFAULT
if "selected_game_id" not in st.session_state:
    st.session_state["selected_game_id"] = "gravity_flip"
if "game_mode" not in st.session_state:
    st.session_state["game_mode"] = "CHALLENGE"
if "session_id" not in st.session_state:
    st.session_state["session_id"] = f"SES-{uuid.uuid4().hex[:8].upper()}"
if "calibrated" not in st.session_state:
    st.session_state["calibrated"] = False
if "camera_started" not in st.session_state:
    st.session_state["camera_started"] = False

# Synchronize demo mode with CameraManager singleton
camera_manager.is_demo_mode = st.session_state["demo_mode"]

# Start the physical camera on first load (if not in demo mode)
if not st.session_state["demo_mode"] and not st.session_state["camera_started"]:
    cam_ok = camera_manager.start_camera()
    st.session_state["camera_started"] = cam_ok
    if not cam_ok:
        # Camera failed — fall back to demo mode gracefully
        st.session_state["demo_mode"] = True
        camera_manager.is_demo_mode = True

# --- SIDEBAR NAVIGATION ---
with st.sidebar:
    st.markdown("""
    <div style="padding: 10px 0 16px 0;">
        <div style="display: flex; align-items: center; gap: 10px;">
            <span style="font-size: 2.0rem;">🌌</span>
            <div>
                <div style="font-size: 1.6rem; font-weight: 900; background: linear-gradient(135deg, #00E5FF, #7928CA, #FF0080); -webkit-background-clip: text; -webkit-text-fill-color: transparent; letter-spacing: -0.5px;">
                    MOVA
                </div>
                <div style="font-size: 0.68rem; font-weight: 700; color: #94A3B8; letter-spacing: 1.5px; text-transform: uppercase;">
                    Move. Play. Improve.
                </div>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    # Live Mode Badge
    if st.session_state["demo_mode"]:
        st.markdown("""
        <div style="background: rgba(250, 204, 21, 0.15); border: 1px solid rgba(250, 204, 21, 0.4); border-radius: 8px; padding: 6px 12px; margin-bottom: 12px; font-size: 0.78rem; font-weight: 700; color: #FACC15; display: flex; align-items: center; gap: 8px;">
            <span style="display: inline-block; width: 8px; height: 8px; border-radius: 50%; background: #FACC15;"></span>
            DEMO MODE (Simulated Rig)
        </div>
        """, unsafe_allow_html=True)
    else:
        st.markdown("""
        <div style="background: rgba(0, 229, 255, 0.12); border: 1px solid rgba(0, 229, 255, 0.3); border-radius: 8px; padding: 6px 12px; margin-bottom: 12px; font-size: 0.78rem; font-weight: 700; color: #00E5FF; display: flex; align-items: center; gap: 8px;">
            <span style="display: inline-block; width: 8px; height: 8px; border-radius: 50%; background: #00FF88;"></span>
            CAMERA STREAM ACTIVE
        </div>
        """, unsafe_allow_html=True)

    # Demo Mode Quick Switch
    toggle_demo = st.checkbox("🧪 Use Demo Simulation", value=st.session_state["demo_mode"], help="Toggle between live webcam and synthetic spatial simulation")
    if toggle_demo != st.session_state["demo_mode"]:
        st.session_state["demo_mode"] = toggle_demo
        camera_manager.is_demo_mode = toggle_demo
        if not toggle_demo:
            # Switching TO live camera — open capture
            cam_ok = camera_manager.start_camera()
            st.session_state["camera_started"] = cam_ok
            if not cam_ok:
                st.session_state["demo_mode"] = True
                camera_manager.is_demo_mode = True
        else:
            camera_manager.stop_camera()
            st.session_state["camera_started"] = False
        st.rerun()

    st.markdown("<hr style='border: none; border-top: 1px solid rgba(255,255,255,0.08); margin: 8px 0 14px 0;'>", unsafe_allow_html=True)

    # Navigation Menu
    nav_items = [
        ("HOME", "🏠", "Home"),
        ("GAME LIBRARY", "🎮", "Game Library"),
        ("HOW TO PLAY", "📖", "How to Play"),
        ("PLAY", "🕹️", "Active Session"),
        ("MOVEMENT LAB", "🔬", "Movement Lab"),
        ("PROGRESS", "📈", "Progress Analytics"),
        ("AI COACH", "🤖", "AI Movement Coach"),
        ("REPORTS", "📄", "Session Reports"),
        ("CALIBRATION", "🎯", "Sensor Calibration"),
        ("SETTINGS", "⚙️", "Settings"),
    ]

    current_page = st.session_state["nav_page"]

    for page_key, icon, label in nav_items:
        is_active = (current_page == page_key)
        button_type = "primary" if is_active else "secondary"
        if st.sidebar.button(f"{icon}  {label}", key=f"nav_btn_{page_key}", type=button_type, use_container_width=True):
            if current_page != page_key:
                st.session_state["nav_page"] = page_key
                st.rerun()

    # Active Game Widget in Sidebar
    active_gid = st.session_state.get("selected_game_id", "gravity_flip")
    if active_gid in GameRegistry.CATALOG:
        ginfo = GameRegistry.CATALOG[active_gid]
        st.markdown(f"""
        <div style="margin-top: 16px; background: rgba(255,255,255,0.03); border: 1px solid rgba(255,255,255,0.06); border-radius: 10px; padding: 12px;">
            <div style="font-size: 0.68rem; font-weight: 700; color: #94A3B8; text-transform: uppercase; letter-spacing: 1px;">Selected Activity</div>
            <div style="font-weight: 800; color: #FFFFFF; font-size: 0.95rem; margin-top: 2px;">{ginfo['icon']} {ginfo['title']}</div>
            <div style="font-size: 0.75rem; color: #38BDF8; margin-top: 2px;">Focus: {ginfo['movement_focus']}</div>
        </div>
        """, unsafe_allow_html=True)

    # Sidebar Download & Footer Notice
    import os
    zip_path = r"C:\Users\HOME\OneDrive\Desktop\MOVA_Project.zip"
    if os.path.exists(zip_path):
        try:
            with open(zip_path, "rb") as zf:
                st.sidebar.download_button(
                    label="📦 Download Full Project (.zip)",
                    data=zf.read(),
                    file_name="MOVA_Project.zip",
                    mime="application/zip",
                    use_container_width=True
                )
        except Exception:
            pass

    st.markdown("""
    <div style="margin-top: 14px; padding-top: 10px; border-top: 1px solid rgba(255,255,255,0.06); font-size: 0.72rem; color: #64748B; line-height: 1.4;">
        MOVA v1.0.0 &bull; Non-medical spatial gaming and personal movement telemetry.
    </div>
    """, unsafe_allow_html=True)

# --- PAGE ROUTING ---
page = st.session_state.get("nav_page", "HOME")

if page == "HOME":
    render_home_screen()
elif page == "GAME LIBRARY":
    render_game_library()
elif page == "HOW TO PLAY":
    render_game_manual()
elif page == "PLAY":
    render_session_screen()
elif page == "MOVEMENT LAB":
    render_movement_lab()
elif page == "PROGRESS":
    render_progress_screen()
elif page == "AI COACH":
    render_ai_coach_screen()
elif page == "REPORTS":
    render_reports_screen()
elif page == "CALIBRATION":
    render_calibration_screen()
elif page == "SETTINGS":
    render_settings_screen()
else:
    render_home_screen()
