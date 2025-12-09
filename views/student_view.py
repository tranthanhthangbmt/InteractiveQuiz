import streamlit as st
import extra_streamlit_components as stx
from streamlit_autorefresh import st_autorefresh

def get_cookie_manager():
    return stx.CookieManager()

def student_view(db):
    st_autorefresh(interval=3000, key="student_refresh")
    
    st.header("🎓 Student Portal")
    
    cookie_manager = get_cookie_manager()
    # It takes time to load cookies, so we might need to wait for reruns
    cookies = cookie_manager.get_all()
    
    # 1. Check Auth (Cookie -> Session -> Form)
    cookie_username = cookies.get("student_username")
    
    # If cookie exists but session doesn't, restore session
    if cookie_username and "username" not in st.session_state:
        st.session_state["username"] = cookie_username
        db.register_user(cookie_username)
        # Force rerun to update UI state if needed, though usually st triggers update
    
    # Login Logic
    if "username" not in st.session_state:
        with st.form("login_form"):
            username = st.text_input("Nhập Họ và Tên của bạn")
            submitted = st.form_submit_button("Tham gia")
            if submitted and username:
                db.register_user(username)
                st.session_state["username"] = username
                # Set Cookie (Expires in 30 days)
                cookie_manager.set("student_username", username, expires_at=None)
                st.rerun()
        return

    # 3. Logged In State
    username = st.session_state["username"]
    
    col_info, col_logout = st.columns([3, 1])
    with col_info:
        st.write(f"👤 Chào bạn: **{username}**")
    with col_logout:
        if st.button("Đăng xuất", type="secondary", use_container_width=True):
            # Logout Logic
            if "username" in st.session_state:
                del st.session_state["username"]
            cookie_manager.delete("student_username")
            st.rerun()
    
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
            
            # Custom CSS for Student Buttons
            st.markdown("""
            <style>
            /* Base Button Style */
            div.stButton > button {
                width: 100%;
                height: 100px;
                font-size: 30px !important;
                font-weight: 900 !important;
                color: black !important;
                background-color: #2196F3 !important; /* Default Blue */
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

            /* Target aligned columns */
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
            
            # 4 Columns for Student too (consistent with colors)
            cols = st.columns(4)
            
            with cols[0]:
                if st.button("A", use_container_width=True):
                    submit_answer(db, current_q_id, username, "A")
            with cols[1]:
                if st.button("B", use_container_width=True):
                    submit_answer(db, current_q_id, username, "B")
            with cols[2]:
                if st.button("C", use_container_width=True):
                    submit_answer(db, current_q_id, username, "C")
            with cols[3]:
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

             st.write("---")
             
             # 1. Poll Results (Bar Chart)
             st.subheader("📊 Class Results")
             data = db.get_response_counts(prev_q_id)
             if not data.empty:
                 total_votes = data['count'].sum()
                 if total_votes > 0:
                     data['percentage'] = (data['count'] / total_votes * 100).round(1)
                 else:
                     data['percentage'] = 0
                
                 import altair as alt
                 
                 color_scale = alt.Scale(
                    domain=['A', 'B', 'C', 'D'],
                    range=['#4CAF50', '#FF9800', '#FFC107', '#2196F3']
                 )
                 
                 chart = alt.Chart(data).mark_bar().encode(
                     x=alt.X('selected_option', title='Option'),
                     y=alt.Y('percentage', title='Percentage %'),
                     color=alt.Color('selected_option', scale=color_scale, legend=None),
                     tooltip=['selected_option', 'count', 'percentage']
                 ).properties(height=200)
                 
                 st.altair_chart(chart, use_container_width=True)
            
             # 2. Leaderboard & Position
             st.subheader("🥇 Leaderboard")
             # Fetch more users to find rank
             leaderboard_df = db.get_leaderboard(limit=100) 
             
             if not leaderboard_df.empty:
                 # Calculate Rank
                 # Sort by score desc (db does this, but ensure)
                 # reset_index to get 0-based rank, add 1
                 leaderboard_df['Rank'] = leaderboard_df.index + 1
                 
                 # Find current user
                 user_row = leaderboard_df[leaderboard_df['username'] == username]
                 
                 if not user_row.empty:
                     my_rank = user_row.iloc[0]['Rank']
                     st.info(f"You are currently **#{my_rank}** on the whiteboard.")
                     
                     # Highlight user in the table
                     def highlight_user(row):
                         return ['background-color: #ffeb3b; color: black'] * len(row) if row['username'] == username else [''] * len(row)
                     
                     st.dataframe(
                         leaderboard_df[['Rank', 'username', 'score']].style.apply(highlight_user, axis=1),
                         use_container_width=True,
                         hide_index=True
                     )
                 else:
                     st.write("You are not in the top 100 yet.")

def submit_answer(db, q_id, username, option):
    db.submit_response(q_id, username, option)
    st.session_state["last_voted_q"] = q_id
    st.balloons()
    st.rerun()
