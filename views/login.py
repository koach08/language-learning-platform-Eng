import streamlit as st
from utils.auth import login_with_google, login_with_email


def show():
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
            if (refreshToken) { newUrl += '&refresh_token=' + encodeURIComponent(refreshToken); }
            window.location.replace(newUrl);
        }
    }
    </script>
    """, unsafe_allow_html=True)

    st.markdown("<h1 style='text-align:center'>🎓 English Learning Platform</h1>", unsafe_allow_html=True)
    st.markdown("<p style='text-align:center; color:#666;'>英語学習プラットフォーム</p>", unsafe_allow_html=True)
    st.markdown("")

    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        st.markdown("#### 🔐 ログイン")
        login_with_google()
        st.markdown("")
        with st.expander("👨‍🏫 教員として登録する", expanded=False):
            st.caption("教員用招待コードをお持ちの方はこちらから登録できます。")
            show_teacher_registration_form()
        with st.expander("開発用ログイン（ローカルテスト）", expanded=False):
            st.caption("⚠️ Supabase OAuth が使えない環境向けです")
            login_with_email()


def show_teacher_registration_form():
    user = st.session_state.get("user")
    with st.form("teacher_registration_form"):
        if user:
            st.info(f"ログイン中: {user['email']}")
            st.text_input("メールアドレス", value=user["email"], disabled=True)
            email_val = user["email"]
            name_val = user["name"]
        else:
            email_val = st.text_input("メールアドレス", placeholder="example@email.com")
            name_val = st.text_input("氏名")
        invite_code = st.text_input("教員招待コード", type="password", placeholder="管理者から共有されたコードを入力")
        submitted = st.form_submit_button("教員として登録", use_container_width=True, type="primary")
        if submitted:
            valid_code = st.secrets.get("app", {}).get("teacher_invite_code", "")
            if not invite_code:
                st.error("招待コードを入力してください")
                return
            if not valid_code:
                st.error("招待コードが設定されていません")
                return
            if invite_code != valid_code:
                st.error("招待コードが正しくありません")
                return
            target_email = user["email"] if user else email_val
            target_name = user["name"] if user else name_val
            if not target_email or not target_name:
                st.error("メールアドレスと氏名を入力してください")
                return
            try:
                from utils.database import get_or_create_user, update_user
                db_user = get_or_create_user(target_email, target_name)
                update_user(db_user["id"], {"role": "teacher"})
                if user and user["email"] == target_email:
                    st.session_state["user"]["role"] = "teacher"
                    st.success("✅ 教員として登録しました！")
                    import time; time.sleep(1)
                    st.rerun()
                else:
                    st.success("✅ 登録完了。Googleアカウントでログインしてください。")
            except Exception as e:
                st.error(f"登録エラー: {e}")


def show_registration_form():
    user = st.session_state.get("user")
    if not user or user.get("role") == "teacher" or user.get("student_id"):
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
