import streamlit as st
from utils.auth import login_with_google, login_with_email

def show():
    # OAuthコールバック: #access_token を ?access_token に変換するJS
    st.markdown("""
    <script>
    const hash = window.location.hash;
    if (hash && hash.includes('access_token')) {
        const params = new URLSearchParams(hash.substring(1));
        const accessToken = params.get('access_token');
        const refreshToken = params.get('refresh_token');
        if (accessToken) {
            const base = window.location.pathname;
            let newUrl = base + '?access_token=' + encodeURIComponent(accessToken);
            if (refreshToken) {
                newUrl += '&refresh_token=' + encodeURIComponent(refreshToken);
            }
            window.location.replace(newUrl);
        }
    }
    </script>
    """, unsafe_allow_html=True)

    st.markdown("<h1 style='text-align:center'>🎓 English Learning Platform</h1>", unsafe_allow_html=True)
    st.markdown("<p style='text-align:center; color:#666;'>北海道大学 英語学習プラットフォーム</p>", unsafe_allow_html=True)
    st.markdown("")
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        st.markdown("#### 🔐 ログイン")
        login_with_google()
        with st.expander("開発用ログイン（ローカルテスト）", expanded=False):
            st.caption("⚠️ Supabase OAuth が使えない環境向けです")
            login_with_email()

def show_registration_form():
    user = st.session_state.get("user")
    if not user:
        return
    if user.get("role") == "teacher":
        return
    if user.get("student_id"):
        return
    st.info("📋 初回ログインです。学籍番号を登録してください。")
    with st.form("registration_form"):
        student_id = st.text_input("学籍番号", placeholder="例: 02241234")
        submitted = st.form_submit_button("登録", use_container_width=True)
        if submitted:
            if not student_id:
                st.error("学籍番号を入力してください")
                return
            try:
                from utils.database import update_user
                update_user(user["id"], {"student_id": student_id})
            except Exception:
                pass
            st.session_state["user"]["student_id"] = student_id
            st.success("登録しました！")
            st.rerun()
