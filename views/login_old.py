import streamlit as st
from utils.auth import login_with_email

def show():
    st.markdown("<h1 style='text-align:center'>🎓 English Learning</h1>", unsafe_allow_html=True)
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        login_with_email()

def show_registration_form():
    with st.form("reg"):
        student_id = st.text_input("学籍番号")
        if st.form_submit_button("登録"):
            st.session_state['user']['student_id'] = student_id
            st.rerun()
