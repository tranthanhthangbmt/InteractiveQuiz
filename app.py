import streamlit as st
from services.db_service import QuizDatabase
from views.teacher_view import teacher_view
from views.student_view import student_view

# Page Config
st.set_page_config(page_title="Classroom Quiz", page_icon="📝", layout="wide")

# Initialize DB
# We cache the resource to prevent reloading connection on every rerun
@st.cache_resource
def get_db():
    return QuizDatabase()

db = get_db()

# Navigation
# We can use a query param to separate views or a simple sidebar choice.
# For a real class, URLs like `app?role=student` are user friendly.
# But for MVP, a sidebar selector is fine.

params = st.query_params
role = params.get("role", None)

if role == "teacher":
    if "admin_authenticated" not in st.session_state:
        st.session_state.admin_authenticated = False

    if st.session_state.admin_authenticated:
        teacher_view(db)
    else:
        st.title("🔒 Admin Login")
        password = st.text_input("Enter Admin Password", type="password")
        if st.button("Login"):
            if password == "admin123":  # Simple hardcoded password for prototype
                st.session_state.admin_authenticated = True
                st.rerun()
            else:
                st.error("Incorrect password")
elif role == "student":
    student_view(db)
else:
    # Landing Page
    st.title("Interactive Classroom Quiz")
    
    col1, col2 = st.columns(2)
    with col1:
        if st.button("👨‍🏫 Giảng viên", use_container_width=True):
            st.query_params["role"] = "teacher"
            st.rerun()
            
    with col2:
        if st.button("🎓 Sinh viên", use_container_width=True):
            st.query_params["role"] = "student"
            st.rerun()
            
    st.info("Select your role to continue.")
