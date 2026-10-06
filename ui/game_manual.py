"""
MOVA UI: Visual 'How to Play' Manual
Implements Section 15:
Objective, Controls with icons (👀, 🖐️, 💪, 🧍, 🗣️), Step-by-Step, Scoring Rules,
What MOVA Tracks, Adaptive Difficulty Explanation, and [PRACTICE], [START GAME], [BACK] buttons.
"""

import streamlit as st
from games.game_manager import GameRegistry

# Dedicated manual content dictionary for each of the 10 crazy games
MANUAL_DETAILS = {
    "gravity_flip": {
        "objective": "Guide your glowing celestial orb into the cosmic portal while adapting to sudden gravitational shifts and dodging hazards.",
        "controls": ["🧍 Body: Lean torso laterally to steer against gravity", "💪 Arms: Balance body center", "😊 Head: Turn head for fine vertical trim", "👀 Gaze: Track incoming portal coordinates"],
        "steps": [
            "Stand centered inside the MOVA Zone with your torso clearly visible.",
            "Observe the active gravity direction indicator at the top of the HUD.",
            "Lean your torso in the opposite direction of gravity to counteract drift.",
            "Navigate your orb around red cosmic hazards and guide it safely into the portal."
        ],
        "scoring": "Earn 250 Base Points per portal reached, multiplied by current combo streak and adaptive difficulty level. Hazard collisions reset combo.",
        "tracks": ["Body displacement & lean angle", "Torso postural stability", "Directional reaction latency", "Movement trajectory smoothness"],
        "difficulty": "Higher difficulty increases gravitational acceleration, shortens switch timers, and adds erratic orbiting hazards."
    },
    "dragon_dash": {
        "objective": "Survive incoming dragon fire hazards by physically dodging with your body, while reaching out with hands to absorb dragon energy spheres.",
        "controls": ["🧍 Body: Shift laterally to dodge incoming fire", "👀 Eyes: Scan incoming trajectory lanes", "🖐️ Hands: Reach out to collect floating energy orbs", "💪 Arms: Coordinate dual-hand reach"],
        "steps": [
            "Keep your eyes locked on the upper boundary as dragon hazards descend.",
            "Step or lean your body sideways when a hazard falls toward your lane.",
            "Simultaneously reach your hands toward falling glowing energy spheres.",
            "Chain consecutive energy grabs to trigger combo multipliers."
        ],
        "scoring": "150 points for each energy orb collected; 80 points for each successful body dodge. Hazard hits reset combo.",
        "tracks": ["Visual reaction speed", "Dodge timing & evasion success", "Bilateral hand accuracy", "Whole-body coordination"],
        "difficulty": "Meteors descend with increasing velocity, spawn frequency tightens, and simultaneous left/right threats appear."
    },
    "galaxy_rescue": {
        "objective": "Locate stranded cosmic lifeforms across highlighted exoplanets using gaze fixation, then reach out with your hand to activate tractor beams.",
        "controls": ["👀 Gaze: Fixate gaze directly on the highlighted target planet", "🖐️ Hand: Reach toward target planet and hold position", "💪 Arm: Extend smoothly across space", "🧍 Body: Maintain steady posture"],
        "steps": [
            "Scan the starfield and visually locate the glowing highlighted planet.",
            "Lock your gaze onto the target planet for at least 0.2 seconds.",
            "Reach your hand over the planet to initiate the tractor beam charge.",
            "Hold steady until the beam charges to 100% to rescue the creature."
        ],
        "scoring": "200 points per creature beamed to safety. Fast gaze-to-reach latency awards high precision score multipliers.",
        "tracks": ["Gaze fixation accuracy", "Gaze-to-hand response latency", "Spatial reach precision", "Posture steadiness"],
        "difficulty": "Tractor beam charge times require faster alignment and planets disperse wider into peripheral zones."
    },
    "spellcaster": {
        "objective": "Channel arcane energy by drawing glowing magical glyph trajectories in the air with your hand and releasing spells with gestures or voice.",
        "controls": ["🖐️ Hand: Point or pinch to trace glowing glyph lines", "💪 Arm: Sweep through trajectory motions", "🗣️ Voice (Optional): Say 'Cast' or 'Ignite' to release spell"],
        "steps": [
            "Observe the target arcane pattern (Circle, Horizontal Strike, Zigzag, Triangle) shown on the HUD.",
            "Extend your hand and smoothly trace the shape in the air.",
            "Watch the Arcane Resonance meter fill as your trajectory matches the template.",
            "Once resonance exceeds 78%, the spell automatically bursts into magic (or say 'Cast'!)."
        ],
        "scoring": "220 points per spell cast. Smooth paths with low jerk and high geometric similarity earn bonus points.",
        "tracks": ["Trajectory curvature & jerk", "Gesture pattern fidelity", "Movement speed consistency", "Multimodal release timing"],
        "difficulty": "Requires tighter geometric tolerances and introduces multi-stroke intricate arcane sigils."
    },
    "bee_swarm": {
        "objective": "Identify the fluttering Golden Queen Bee among swarming worker hornets and catch her in flight using rapid hand movements.",
        "controls": ["👀 Eyes: Track the fast-moving Golden Queen", "🖐️ Hands: Rapidly intercept and catch the target", "💪 Arms: Rapid arm extension"],
        "steps": [
            "Visually distinguish the Golden Queen (glowing yellow aura) from red stinging hornets.",
            "Predict the queen's fluttering trajectory as she buzzes across the MOVA Zone.",
            "Quickly reach out your hand to intercept and grab her in mid-air.",
            "Avoid accidentally touching red hornets, which resets your combo."
        ],
        "scoring": "180 points per Queen Bee caught. Quick intercept speed and high accuracy increase combo score.",
        "tracks": ["Visual search speed", "Eye-hand coordination", "Hand interception velocity", "Movement precision"],
        "difficulty": "Bees flutter faster with randomized erratic trajectories and more hornets crowd the spatial zone."
    },
    "treasure_storm": {
        "objective": "Dodge rotating lightning storm hazard sectors with your body, reach sunken treasure chests, and unlock them with pinch gestures.",
        "controls": ["🧍 Body: Step and lean away from the electrified storm quadrant", "🖐️ Hands: Reach toward treasure chest and PINCH or GRAB to open", "💪 Arms: Coordinated lateral reach"],
        "steps": [
            "Check which quadrant of the MOVA Zone is flashing red with storm surge.",
            "Keep your body positioned in safe sectors away from the active hazard.",
            "Reach your hand directly over the treasure chest lock.",
            "Perform a pinch or closed fist gesture and hold until the lock circle fills."
        ],
        "scoring": "240 points per chest unlocked. Staying continuously clear of storm hazards maintains streak multipliers.",
        "tracks": ["Postural evasion accuracy", "Fine pinch / grasp detection", "Reach distance", "Spatial decision pacing"],
        "difficulty": "Storm rotation accelerates, leaving tighter windows to unlock chests before the surge shifts."
    },
    "robot_factory": {
        "objective": "Assemble cybernetic robots by following a strict 5-step multimodal sequence: Look -> Point -> Grab -> Move -> Release.",
        "controls": ["👀 Eyes: Look at component", "🖐️ Hand: Point, then Pinch/Grab, Move across screen, and Open Palm to release", "🗣️ Voice (Optional): Say 'Grab' or 'Attach'"],
        "steps": [
            "1. LOOK: Turn your gaze toward the glowing power core on the left.",
            "2. POINT: Extend your index finger toward the component.",
            "3. GRAB: Form a fist or pinch to secure the part.",
            "4. MOVE: Carry the part across space to the robot chassis on the right.",
            "5. RELEASE: Open your palm flat to lock the component in place."
        ],
        "scoring": "300 points per robot assembled. Flawless sequential execution awards maximum multimodal coordination score.",
        "tracks": ["Sequential state execution", "Gaze fixation", "Gesture transitions (Point -> Pinch -> Open)", "Movement continuity"],
        "difficulty": "Tighter time windows per assembly step and components must be precisely aligned."
    },
    "ocean_guardian": {
        "objective": "Steer an underwater research submarine through a deep ocean trench by leaning your body, collecting bioluminescent pearls while dodging mines.",
        "controls": ["🧍 Body: Lean torso left/right to steer submarine hull", "💪 Arms: Tilt arms to assist propulsion", "🖐️ Hands: Reach out to grab peripheral pearls"],
        "steps": [
            "Lean your torso to glide the submarine horizontally along the ocean floor.",
            "Guide the sub under descending glowing pearls to collect them.",
            "You can also reach out with either hand to snag pearls off to the sides.",
            "Steer clear of spiked red sea mines."
        ],
        "scoring": "160 points per pearl collected. Clean mine avoidance preserves combo multipliers.",
        "tracks": ["Lateral torso steering control", "Postural stability", "Bilateral hand reach", "Reaction latency"],
        "difficulty": "Ocean currents push the submarine faster, mine density increases, and pearls fall at varying speeds."
    },
    "mirror_mage": {
        "objective": "Reproduce progressive multimodal sequences of head turns, eye gazes, hand gestures, and body postures demonstrated by the Mirror Realm.",
        "controls": ["👀 Eyes: Look left/right", "😊 Face: Turn head left/right", "🖐️ Hands: Hand up, Open palms, Pinch", "🧍 Body: Lean left/right"],
        "steps": [
            "Observe the active action displayed in the Mirror Realm banner.",
            "Reproduce the exact action with your body, eyes, or hands.",
            "Hold the matching posture for 0.45 seconds until the confirmation ring fills.",
            "Advance through the sequence. Completing a round adds another step to the next sequence."
        ],
        "scoring": "180 points per action mirrored correctly. Tests sensorimotor working memory and synchronization.",
        "tracks": ["Multimodal synchronization", "Sequence working memory", "Gesture accuracy", "Postural fidelity"],
        "difficulty": "Sequences extend from 3 up to 5 consecutive actions combining rapid cross-modal shifts."
    },
    "neon_pulse": {
        "objective": "Strike spatial rhythm pads on beat as collapsing neon rings align with the tempo. Perfect timing yields maximum score.",
        "controls": ["🖐️ Hands: Strike left, right, or top pads with rhythmic arm reaches", "👀 Eyes: Scan incoming collapsing rings", "🧍 Body: Maintain rhythmic balance"],
        "steps": [
            "Listen and watch the rhythmic BPM pulse of the neon arena.",
            "Watch beat rings collapse toward the left, right, and top target pads.",
            "Reach and strike the corresponding pad with your hand exactly when the ring hits the center marker.",
            "Time strikes precisely to earn PERFECT or GOOD ratings."
        ],
        "scoring": "250 points for Perfect timing hits; 120 points for Good hits. Maintaining unbroken rhythm builds massive combos.",
        "tracks": ["Millisecond timing accuracy", "Bilateral hand synchronization", "Movement cadence consistency", "Visual-spatial rhythm"],
        "difficulty": "BPM tempo increases, beat rings collapse faster, and alternating dual-hand patterns emerge."
    }
}

def render_game_manual():
    gid = st.session_state.get("selected_game_id", "gravity_flip")
    if gid not in GameRegistry.CATALOG:
        gid = "gravity_flip"

    gdata = GameRegistry.CATALOG[gid]
    manual = MANUAL_DETAILS.get(gid, MANUAL_DETAILS["gravity_flip"])

    # Header Card
    st.markdown(f"""
    <div style="background: linear-gradient(135deg, rgba(20,20,35,0.8) 0%, rgba(30,20,50,0.8) 100%); border: 1px solid rgba(255,255,255,0.15); border-left: 6px solid {gdata['color']}; border-radius: 16px; padding: 24px; margin-bottom: 20px;">
        <div style="display: flex; justify-content: space-between; align-items: center;">
            <div>
                <span style="font-size: 0.78rem; font-weight: 800; color: {gdata['color']}; letter-spacing: 2px;">HOW TO PLAY MANUAL</span>
                <h1 style="margin: 4px 0 6px 0; color: #FFFFFF; font-size: 2.2rem;">{gdata['title']}</h1>
                <div style="color: #94A3B8; font-size: 0.95rem;">Focus: <b style="color: #38BDF8;">{gdata['movement_focus']}</b> &bull; Duration: <b>{gdata['duration']}</b></div>
            </div>
            <div style="font-size: 3.5rem;">{gdata['icon']}</div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    # Manual Sections in clean columns
    col_left, col_right = st.columns([1.1, 1.0])

    with col_left:
        st.markdown("### 🎯 OBJECTIVE")
        st.info(manual["objective"])

        st.markdown("### 🕹️ CONTROLS & MODALITIES")
        for ctrl in manual["controls"]:
            st.markdown(f"- {ctrl}")

        st.markdown("### 📋 STEP-BY-STEP")
        for i, step in enumerate(manual["steps"]):
            st.markdown(f"**{i+1}.** {step}")

    with col_right:
        st.markdown("### 🏆 SCORING RULES")
        st.write(manual["scoring"])

        st.markdown("### 📊 WHAT MOVA TRACKS")
        for trk in manual["tracks"]:
            st.markdown(f"- {trk}")

        st.markdown("### ⚡ ADAPTIVE DIFFICULTY")
        st.write(manual["difficulty"])

    st.markdown("<hr style='border-color: rgba(255,255,255,0.1); margin: 25px 0 20px 0;'>", unsafe_allow_html=True)

    # Action Buttons: [ PRACTICE ] [ START GAME ] [ BACK ]
    b_col1, b_col2, b_col3, b_col4 = st.columns([1.2, 1.2, 1.0, 1.0])

    with b_col1:
        if st.button("▶ START GAME (Challenge)", key="manual_start_challenge", use_container_width=True):
            st.session_state["game_mode"] = "CHALLENGE"
            st.session_state["nav_page"] = "PLAY"
            st.rerun()

    with b_col2:
        if st.button("🛡️ PRACTICE MODE", key="manual_start_practice", use_container_width=True):
            st.session_state["game_mode"] = "PRACTICE"
            st.session_state["nav_page"] = "PLAY"
            st.rerun()

    with b_col3:
        mode_choice = st.selectbox("Other Modes:", ["EXPLORE", "EXTREME", "ASSESSMENT"], key="manual_other_modes", label_visibility="collapsed")
        if st.button(f"Launch {mode_choice}", key="manual_launch_other", use_container_width=True):
            st.session_state["game_mode"] = mode_choice
            st.session_state["nav_page"] = "PLAY"
            st.rerun()

    with b_col4:
        if st.button("⬅ Back to Library", key="manual_back", use_container_width=True):
            st.session_state["nav_page"] = "GAME LIBRARY"
            st.rerun()
