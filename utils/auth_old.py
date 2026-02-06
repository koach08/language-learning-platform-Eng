import streamlit as st
from typing import Optional, Dict

def login_with_email():
    with st.form("login_form"):
        email = st.text_input("メールアドレス")
        name = st.text_input("名前")
        submitted = st.form_submit_button("ログイン", use_container_width=True)
        if submitted:
            if not email or not name:
                st.error("入力してください")
                return
            teacher_emails = st.secrets.get("app", {}).get("teacher_emails", "")
            if isinstance(teacher_emails, str):
                teacher_emails = [e.strip() for e in teacher_emails.split(',')]
            role = 'teacher' if email in teacher_emails else 'student'
            st.session_state['user'] = {'id': email, 'email': email, 'name': name, 'role': role, 'student_id': None}
            st.session_state['authenticated'] = True
            st.rerun()

def logout():
    for key in ['user', 'authenticated', 'current_course', 'current_view']:
        if key in st.session_state:
            del st.session_state[key]
    st.rerun()

def is_authenticated():
    return st.session_state.get('authenticated', False)

def get_current_user():
    return st.session_state.get('user')

def is_teacher():
    user = get_current_user()
    return user and user.get('role') == 'teacher'

def is_student():
    user = get_current_user()
    return user and user.get('role') == 'student'

def require_auth(func):
    def wrapper(*args, **kwargs):
        if not is_authenticated():
            login_with_email()
            st.stop()
        return func(*args, **kwargs)
    return wrapper

def require_teacher(func):
    def wrapper(*args, **kwargs):
        if not is_authenticated():
            login_with_email()
            st.stop()
        if not is_teacher():
            st.error("教員専用です")
            st.stop()
        return func(*args, **kwargs)
    return wrapper

def require_student(func):
    def wrapper(*args, **kwargs):
        if not is_authenticated():
            login_with_email()
            st.stop()
        if not is_student():
            st.error("学生専用です")
            st.stop()
        return func(*args, **kwargs)
    return wrapper

def handle_oauth_callback():
    return False

def inject_oauth_handler():
    pass

def login_with_google():
    login_with_email()


def init_session():
    """セッション初期化"""
    if 'user' not in st.session_state:
        st.session_state.user = None
    if 'current_view' not in st.session_state:
        st.session_state.current_view = None
