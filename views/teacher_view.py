import streamlit as st
import altair as alt
from streamlit_autorefresh import st_autorefresh

def teacher_view(db):
    st_autorefresh(interval=2000, key="teacher_refresh")

    st.title("👨‍🏫 Teacher Dashboard")

    # Get current state
    room_state = db.get_room_state()
    current_q_id = room_state['current_question_id']
    is_active = room_state['is_active']
    
    # Create main columns: Left for Controls (1/3), Right for Display (2/3)
    col_controls, col_display = st.columns([1, 2])
    
    # --- Control Panel (Left Column) ---
    with col_controls:
        st.header("Control Panel")
        
        st.subheader("Question Controls")
        
        # Navigation
        subcol1, subcol2, subcol3 = st.columns([1, 2, 1])
        with subcol1:
            if st.button("⬅️", help="Previous Question"):
                new_id = max(1, current_q_id - 1)
                db.update_room_state(current_question_id=new_id, is_active=False, correct_answer=None, start_time=None)
                st.rerun()
        
        with subcol2:
             st.markdown(f"<h3 style='text-align: center; margin: 0;'>Q: {current_q_id}</h3>", unsafe_allow_html=True)

        with subcol3:
            if st.button("➡️", help="Next Question"):
                new_id = current_q_id + 1
                db.update_room_state(current_question_id=new_id, is_active=False, correct_answer=None, start_time=None)
                st.rerun()

        # Timer Settings
        duration = st.number_input("Time Limit (seconds)", min_value=10, value=60, step=10, disabled=is_active)
        
        # Actions
        if not is_active:
            if st.button("🚀 START VOTING", type="primary", use_container_width=True):
                from datetime import datetime
                import pytz
                # Storing naive timestamp for simplicity or UTC
                now_iso = datetime.now().isoformat()
                db.update_room_state(is_active=True, start_time=now_iso, duration_seconds=duration)
                st.rerun()
        else:
            st.button("Voting acts...", disabled=True, use_container_width=True)

        st.write("---")
        st.subheader("Close & Revealing Answer")

        # Custom CSS for Big Colorful Buttons
        st.markdown("""
        <style>
        div.stButton > button {
            width: 100%;
            height: 80px;
            font-size: 24px;
            font-weight: bold;
            color: white;
            border: none;
        }
        /* Target buttons by approximate index if key is not stable, or simpler: just colors */
        /* Since we can't easily target specific buttons by key in pure CSS without stable IDs, 
           we rely on the order or wrap them. 
           However, Streamlit creates unique IDs. 
           Let's use a simpler approach: 4 columns, closely packed. */
        
        [data-testid="column"] {
            padding: 0px !important;
        }
        </style>
        """, unsafe_allow_html=True)

        cols = st.columns(4, gap="small")
        
        # A - Red
        with cols[0]:
            if st.button("A", disabled=not is_active, key="btn_A", use_container_width=True):
                finish_question(db, current_q_id, "A")
        
        # B - Blue
        with cols[1]:
            if st.button("B", disabled=not is_active, key="btn_B", use_container_width=True):
                finish_question(db, current_q_id, "B")
                
        # C - Yellow (Dark Text for contrast)
        with cols[2]:
            if st.button("C", disabled=not is_active, key="btn_C", use_container_width=True):
                finish_question(db, current_q_id, "C")
        
        # D - Green
        with cols[3]:
            if st.button("D", disabled=not is_active, key="btn_D", use_container_width=True):
                finish_question(db, current_q_id, "D")
        
        # Inject Javascript or very specific CSS to color keys? 
        # Streamlit doesn't expose keys to CSS.
        # Workaround: Use primary/secondary is not enough.
        # Valid Workaround: Use st.markdown buttons with callback (hard in Streamlit) 
        # OR use :nth-of-type selectors on the specific row of buttons.
        # Assuming these are the last 4 buttons in the control panel.
        
        st.markdown("""
        <style>
        /* Base Button Style */
        div.stButton > button {
            width: 100%;
            height: 100px;
            font-size: 30px !important;
            font-weight: 900 !important;
            color: black !important;
            background-color: #2196F3 !important; /* Default Blue as requested */
            border: 2px solid #333 !important;
            border-radius: 12px !important;
            box-shadow: 0 4px 6px rgba(0,0,0,0.1);
            transition: transform 0.1s;
        }
        div.stButton > button:hover {
            transform: scale(1.02);
            box-shadow: 0 6px 8px rgba(0,0,0,0.2);
            border: 2px solid black !important;
        }
        div.stButton > button:active {
            transform: scale(0.98);
        }

        /* Target ONLY rows with 4 columns (The Answer Buttons) */
        /* Re-introducing :has() to ensure we don't color the navigation buttons */
        [data-testid="stHorizontalBlock"]:has([data-testid="column"]:nth-child(4)) [data-testid="column"]:nth-child(1) div.stButton > button {
            background-color: #4CAF50 !important; /* Green */
        }
        [data-testid="stHorizontalBlock"]:has([data-testid="column"]:nth-child(4)) [data-testid="column"]:nth-child(2) div.stButton > button {
             background-color: #FF9800 !important; /* Orange */
        }
        [data-testid="stHorizontalBlock"]:has([data-testid="column"]:nth-child(4)) [data-testid="column"]:nth-child(3) div.stButton > button {
             background-color: #FFC107 !important; /* Yellow */
        }
        [data-testid="stHorizontalBlock"]:has([data-testid="column"]:nth-child(4)) [data-testid="column"]:nth-child(4) div.stButton > button {
             background-color: #2196F3 !important; /* Blue */
        }
        
        /* Remove padding for tight fit */
        [data-testid="stHorizontalBlock"]:has([data-testid="column"]:nth-child(4)) [data-testid="column"] {
             padding-left: 2px !important;
             padding-right: 2px !important;
        }
        </style>
        """, unsafe_allow_html=True)
        
        # To strictly target these 4 columns, we'd need them to be the ONLY 4 columns in a container.
        # But we are inside `col_controls`.
        # Taking a risk with nth-of-type, user can verify.
        
        st.write("---")
        if st.button("🚨 RESET SYSTEM", type="secondary"):
            db.reset_game()
            st.rerun()

    # --- Main Projector View (Right Column) ---
    with col_display:
        st.header("Projector View")
        
        # Timer Logic for Display (Keep calculation here or in controls, need variable for both)
        remaining_time = 0
        if is_active and room_state.get('start_time'):
            from datetime import datetime
            start_dt = datetime.fromisoformat(room_state['start_time'])
            elapsed = (datetime.now() - start_dt).total_seconds()
            remaining_time = max(0, room_state['duration_seconds'] - elapsed)
            
            # Show small timer in controls too? Or just big usage
            with col_controls:
                 st.markdown(f"### ⏳ Time: {int(remaining_time)}s")
                 st.progress(min(1.0, max(0.0, remaining_time / room_state['duration_seconds'])))
            
            if remaining_time == 0:
               with col_controls:
                   st.error("Time's up!")

        # Common Chart Config
        color_scale = alt.Scale(
            domain=['A', 'B', 'C', 'D'],
            range=['#4CAF50', '#FF9800', '#FFC107', '#2196F3'] # Green, Orange, Yellow, Blue
        )

        if is_active:
            st.info(f"📢 **Question {current_q_id} is LIVE!** Students are voting...")
            
            # Big Timer on Projector
            if remaining_time > 0:
                st.markdown(f"<h1 style='text-align: center; font-size: 80px; color: #D32F2F;'>{int(remaining_time)}</h1>", unsafe_allow_html=True)
            else:
                 st.markdown(f"<h1 style='text-align: center; font-size: 80px; color: gray;'>TIME'S UP</h1>", unsafe_allow_html=True)
            
            # Live Chart
            data = db.get_response_counts(current_q_id)
            
            chart = alt.Chart(data).mark_bar().encode(
                x=alt.X('selected_option', title='Option'),
                y=alt.Y('count', title='Votes'),
                color=alt.Color('selected_option', scale=color_scale, legend=None),
                tooltip=['selected_option', 'count']
            ).properties(
                height=400,
                title='Live Responses'
            )
            
            st.altair_chart(chart, use_container_width=True)
            
            total_votes = data['count'].sum()
            st.metric("Total Votes", int(total_votes))
            
        else:
            st.info(f"⏸️ **Ready for Question {current_q_id}**")
            
            # Display Previous Question Results if available
            if room_state['correct_answer']:
                prev_q_id = max(1, current_q_id - 1)
                st.write(f"### Previous Result (Q{prev_q_id}): **{room_state['correct_answer']}**")
                
                # Show Chart for Previous Question
                data = db.get_response_counts(prev_q_id)
                
                # Highlight logic: Keep colors but maybe dim incorrect ones? 
                # Or just show the colors as is, and user knows which is correct.
                # User asked to match buttons. So we stick to scale.
                
                chart = alt.Chart(data).mark_bar().encode(
                    x=alt.X('selected_option', title='Option'),
                    y=alt.Y('count', title='Votes'),
                    color=alt.Color('selected_option', scale=color_scale, legend=None),
                    tooltip=['selected_option', 'count']
                ).properties(
                    height=300,
                    title=f'Results for Q{prev_q_id}'
                )
                st.altair_chart(chart, use_container_width=True)
            
            # Leaderboard
            st.subheader("🏆 Leaderboard")
            leaderboard = db.get_leaderboard()
            st.dataframe(leaderboard, use_container_width=True)

def finish_question(db, q_id, answer):
    # Calculate scores for the CURRENT question (before incrementing)
    count = db.calculate_scores(q_id, answer)
    
    # Auto-advance: Increment ID, Stop Active, Set Answer
    db.update_room_state(current_question_id=q_id + 1, is_active=False, correct_answer=answer)
    
    st.toast(f"Q{q_id} Closed! {count} correct. Move to Q{q_id+1}.")
    st.rerun()
