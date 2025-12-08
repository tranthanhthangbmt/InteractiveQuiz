import streamlit as st
from streamlit_autorefresh import st_autorefresh

def student_view(db):
    st_autorefresh(interval=3000, key="student_refresh")
    
    st.header("🎓 Student Portal")

    # Login Logic
    if "username" not in st.session_state:
        with st.form("login_form"):
            username = st.text_input("Enter your Full Name")
            submitted = st.form_submit_button("Join Class")
            if submitted and username:
                db.register_user(username)
                st.session_state["username"] = username
                st.rerun()
        return

    # Logged In State
    username = st.session_state["username"]
    st.write(f"Logged in as: **{username}**")
    
    room_state = db.get_room_state()
    current_q_id = room_state['current_question_id']
    is_active = room_state['is_active']
    
    # Check if already voted for this question locally to disable buttons immediately
    # (Optional optimization, but good for UX)
    if "last_voted_q" not in st.session_state:
        st.session_state["last_voted_q"] = -1
        
    if is_active:
        st.subheader(f"❓ Question {current_q_id}")
        
        # Timer Logic
        import time
        from datetime import datetime
        
        remaining_time = 0
        is_expired = False
        
        if room_state.get('start_time'):
            start_dt = datetime.fromisoformat(room_state['start_time'])
            # Ensure timezones match or use naive (assuming same server for prototype)
            elapsed = (datetime.now() - start_dt).total_seconds()
            remaining_time = max(0, room_state['duration_seconds'] - elapsed)
            
            st.metric("⏳ Time Left", f"{int(remaining_time)}s")
            st.progress(min(1.0, max(0.0, remaining_time / room_state['duration_seconds'])))
            
            if remaining_time == 0:
                is_expired = True
                st.error("⏰ TIME'S UP!")
        
        if st.session_state["last_voted_q"] == current_q_id:
            st.info("✅ Answer submitted. Waiting for results...")
            st.write("Hang tight!")
        elif is_expired:
            st.warning("⛔ You can no longer vote for this question.")
        else:
            st.write("Choose your answer:")
            col1, col2 = st.columns(2)
            with col1:
                if st.button("A", use_container_width=True):
                    submit_answer(db, current_q_id, username, "A")
                if st.button("C", use_container_width=True):
                    submit_answer(db, current_q_id, username, "C")
            with col2:
                if st.button("B", use_container_width=True):
                    submit_answer(db, current_q_id, username, "B")
                if st.button("D", use_container_width=True):
                    submit_answer(db, current_q_id, username, "D")
                    
    else:
        st.warning("⏳ Waiting for the next question...")
        if room_state["correct_answer"]:
             # Check if user got it right
             prev_q_id = current_q_id - 1
             user_ans = db.get_user_response(prev_q_id, username)
             
             if user_ans == room_state["correct_answer"]:
                 st.balloons()
                 st.success(f"🎉 CORRECT! You chose **{user_ans}**")
             elif user_ans:
                 st.error(f"❌ Incorrect. You chose **{user_ans}**, but the answer was **{room_state['correct_answer']}**.")
             else:
                 st.info(f"The correct answer was **{room_state['correct_answer']}**")

             # Show User Score
             score = db.get_user_score(username)
             st.success(f"🏆 Your Total Score: **{score}**")

def submit_answer(db, q_id, username, option):
    db.submit_response(q_id, username, option)
    st.session_state["last_voted_q"] = q_id
    st.balloons()
    st.rerun()
