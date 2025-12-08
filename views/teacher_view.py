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
    
    # --- Sidebar Controls ---
    with st.sidebar:
        st.header("Control Panel")
        
        st.subheader("Question Controls")
        
        # Navigation
        col_nav1, col_nav2, col_nav3 = st.columns([1, 2, 1])
        with col_nav1:
            if st.button("⬅️", help="Previous Question"):
                new_id = max(1, current_q_id - 1)
                db.update_room_state(current_question_id=new_id, is_active=False, correct_answer=None, start_time=None)
                st.rerun()
        
        with col_nav2:
             st.markdown(f"<h3 style='text-align: center; margin: 0;'>Q: {current_q_id}</h3>", unsafe_allow_html=True)

        with col_nav3:
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

        # Timer Logic for Display
        remaining_time = 0
        if is_active and room_state.get('start_time'):
            from datetime import datetime
            start_dt = datetime.fromisoformat(room_state['start_time'])
            elapsed = (datetime.now() - start_dt).total_seconds()
            remaining_time = max(0, room_state['duration_seconds'] - elapsed)
            
            st.markdown(f"### ⏳ Time Left: {int(remaining_time)}s")
            st.progress(min(1.0, max(0.0, remaining_time / room_state['duration_seconds'])))

            if remaining_time == 0:
               st.error("Time's up! Finish question to close.")

        cols = st.columns(4)
        if cols[0].button("A", disabled=not is_active, type="primary"):
            finish_question(db, current_q_id, "A")
        if cols[1].button("B", disabled=not is_active, type="primary"):
            finish_question(db, current_q_id, "B")
        if cols[2].button("C", disabled=not is_active, type="primary"):
            finish_question(db, current_q_id, "C")
        if cols[3].button("D", disabled=not is_active, type="primary"):
            finish_question(db, current_q_id, "D")
            
        st.write("---")
        if st.button("🚨 RESET SYSTEM", type="secondary"):
            db.reset_game()
            st.rerun()

    # --- Main Projector View ---
    if is_active:
        st.info(f"📢 **Question {current_q_id} is LIVE!** Students are voting...")
        
        # Big Timer on Projector
        if remaining_time > 0:
            st.markdown(f"<h1 style='text-align: center; font-size: 80px; color: red;'>{int(remaining_time)}</h1>", unsafe_allow_html=True)
        else:
             st.markdown(f"<h1 style='text-align: center; font-size: 80px; color: gray;'>TIME'S UP</h1>", unsafe_allow_html=True)
        
        # Live Chart
        
        # Live Chart
        data = db.get_response_counts(current_q_id)
        
        chart = alt.Chart(data).mark_bar().encode(
            x=alt.X('selected_option', title='Option'),
            y=alt.Y('count', title='Votes'),
            color=alt.Color('selected_option', legend=None),
            tooltip=['selected_option', 'count']
        ).properties(
            width=600,
            height=400,
            title='Live Responses'
        )
        
        st.altair_chart(chart, use_container_width=True)
        
        total_votes = data['count'].sum()
        st.metric("Total Votes", int(total_votes))
        
    else:
        st.info(f"⏸️ **Ready for Question {current_q_id}**")
        if room_state['correct_answer']:
            st.write(f"### Previous Result: **{room_state['correct_answer']}**")
        
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
