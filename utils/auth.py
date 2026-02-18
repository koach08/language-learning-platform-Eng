"""
Authentication Module - Google OAuth (implicit) + email fallback
招待コード方式教員登録・ロール切り替え対応版
"""
import streamlit as st
from typing import Optional, Dict
import urllib.parse


def get_auth_url() -> str:
    supabase_url = st.secrets["supabase"]["url"]
    redirect_url = _get_redirect_url()
    auth_url = f"{supabase_url}/auth/v1/authorize"
    params = {"provider": "google", "redirect_to": redirect_url}
    return f"{auth_url}?{urllib.parse.urlencode(params)}"


def _get_redirect_url() -> str:
    try:
        return st.secrets.get("app", {}).get("redirect_url", "http://localhost:8502/callback.html")
    except Exception:
        return "http://localhost:8501"


def handle_oauth_callback() -> bool:
    query_params = st.query_params
    if "access_token" in query_params:
        access_token = query_params["access_token"]
        st.session_state["access_token"] = access_token
        user_info = _get_user_from_token(access_token)
        if user_info:
            st.session_state["user"] = user_info
            st.session_state["authenticated"] = True
            st.query_params.clear()
            return True
    return False


def _get_user_from_token(access_token: str) -> Optional[Dict]:
    from utils.database import get_supabase_client, get_or_create_user
    try:
        supabase = get_supabase_client()
        user_response = supabase.auth.get_user(access_token)
        if not (user_response and user_response.user):
            return None
        auth_user = user_response.user
        email = auth_user.email
        metadata = auth_user.user_metadata or {}
        name = metadata.get("full_name") or metadata.get("name") or email.split("@")[0]
        avatar_url = metadata.get("avatar_url") or metadata.get("picture")
        teacher_emails = st.secrets.get("app", {}).get("teacher_emails", "")
        if isinstance(teacher_emails, str):
            teacher_emails = [e.strip() for e in teacher_emails.split(",") if e.strip()]
        db_user = get_or_create_user(email, name, avatar_url)
        db_role = db_user.get("role", "student")
        if email in teacher_emails and db_role != "teacher":
            from utils.database import update_user
            update_user(db_user["id"], {"role": "teacher"})
            db_role = "teacher"
        if db_role == "pending_teacher":
            from utils.database import update_user
            update_user(db_user["id"], {"role": "student"})
            db_role = "student"
        return {
            "id": db_user["id"],
            "email": email,
            "name": db_user["name"],
            "role": db_role,
            "student_id": db_user.get("student_id"),
            "profile_image_url": db_user.get("profile_image_url"),
            "auth_id": str(auth_user.id),
        }
    except Exception as e:
        st.error(f"User info error: {e}")
        return None


def switch_to_student_view(course_id: str = None):
    user = get_current_user()
    if not user or user["role"] != "teacher":
        return
    st.session_state["original_teacher_user"] = user.copy()
    st.session_state["user"] = {
        **user,
        "role": "student",
        "_is_preview_mode": True,
        "_preview_course_id": course_id,
    }
    st.session_state["current_view"] = "student_home"
    st.rerun()


def switch_back_to_teacher():
    original = st.session_state.get("original_teacher_user")
    if original:
        st.session_state["user"] = original
        del st.session_state["original_teacher_user"]
    st.session_state["current_view"] = "teacher_home"
    st.rerun()


def is_preview_mode() -> bool:
    user = get_current_user()
    return bool(user and user.get("_is_preview_mode"))


def login_with_google():
    auth_url = get_auth_url()
    st.markdown("""
    <style>
    .google-btn {
        display: inline-flex; align-items: center; justify-content: center;
        width: 100%; padding: 12px 24px; background-color: white; color: #444;
        border: 1px solid #ddd; border-radius: 8px; font-size: 16px;
        font-weight: 500; text-decoration: none; transition: all 0.2s;
        box-shadow: 0 1px 3px rgba(0,0,0,0.1);
    }
    .google-btn:hover { background-color: #f8f8f8; box-shadow: 0 2px 6px rgba(0,0,0,0.15); text-decoration: none; color: #333; }
    .google-btn img { margin-right: 12px; }
    </style>
    """, unsafe_allow_html=True)
    st.markdown(f'<a href="{auth_url}" class="google-btn"><img src="https://www.google.com/favicon.ico" width="20" height="20">Googleアカウントでログイン</a>', unsafe_allow_html=True)


def login_with_email():
    with st.form("login_form"):
        email = st.text_input("メールアドレス")
        name = st.text_input("名前")
        submitted = st.form_submit_button("ログイン（開発用）", use_container_width=True)
        if submitted:
            if not email or not name:
                st.error("メールアドレスと名前を入力してください")
                return
            teacher_emails = st.secrets.get("app", {}).get("teacher_emails", "")
            if isinstance(teacher_emails, str):
                teacher_emails = [e.strip() for e in teacher_emails.split(",") if e.strip()]
            try:
                from utils.database import get_or_create_user, update_user
                db_user = get_or_create_user(email, name)
                db_role = db_user.get("role", "student")
                if email in teacher_emails:
                    if db_role != "teacher":
                        update_user(db_user["id"], {"role": "teacher"})
                    db_role = "teacher"
                if db_role == "pending_teacher":
                    update_user(db_user["id"], {"role": "student"})
                    db_role = "student"
                st.session_state["user"] = {
                    "id": db_user["id"], "email": email, "name": db_user["name"],
                    "role": db_role, "student_id": db_user.get("student_id"),
                    "profile_image_url": db_user.get("profile_image_url"),
                }
            except Exception:
                role = "teacher" if email in teacher_emails else "student"
                st.session_state["user"] = {"id": email, "email": email, "name": name, "role": role, "student_id": None}
            st.session_state["authenticated"] = True
            st.rerun()


def logout():
    keys_to_clear = ["user", "authenticated", "access_token", "refresh_token", "current_course", "current_view", "original_teacher_user"]
    for key in keys_to_clear:
        if key in st.session_state:
            del st.session_state[key]
    try:
        from utils.database import get_supabase_client
        supabase = get_supabase_client()
        supabase.auth.sign_out()
    except Exception:
        pass
    st.rerun()


def is_authenticated() -> bool:
    return st.session_state.get("authenticated", False)


def get_current_user() -> Optional[Dict]:
    return st.session_state.get("user")


def is_teacher() -> bool:
    user = get_current_user()
    return user is not None and user.get("role") == "teacher"


def is_student() -> bool:
    user = get_current_user()
    return user is not None and user.get("role") == "student"


def require_auth(func):
    def wrapper(*args, **kwargs):
        if not is_authenticated():
            st.warning("ログインが必要です。")
            login_with_google()
            st.stop()
        return func(*args, **kwargs)
    return wrapper


def require_teacher(func):
    def wrapper(*args, **kwargs):
        if not is_authenticated():
            st.warning("ログインが必要です。")
            login_with_google()
            st.stop()
        if not is_teacher():
            st.error("教員専用です。")
            st.stop()
        return func(*args, **kwargs)
    return wrapper


def require_student(func):
    def wrapper(*args, **kwargs):
        if not is_authenticated():
            st.warning("ログインが必要です。")
            login_with_google()
            st.stop()
        if not is_student():
            st.error("学生専用です。")
            st.stop()
        return func(*args, **kwargs)
    return wrapper


def init_session():
    if "user" not in st.session_state:
        st.session_state.user = None
    if "current_view" not in st.session_state:
        st.session_state.current_view = None


def get_pending_teachers() -> list:
    """pending_teacherロールのユーザー一覧を返す"""
    try:
        from utils.database import get_supabase_client
        supabase = get_supabase_client()
        result = supabase.table("users").select("*").eq("role", "pending_teacher").execute()
        return result.data or []
    except Exception as e:
        st.warning(f"教員申請一覧の取得に失敗しました: {e}")
        return []


def approve_teacher(user_id: str) -> bool:
    """ユーザーを教員として承認する"""
    try:
        from utils.database import get_supabase_client
        supabase = get_supabase_client()
        supabase.table("users").update({"role": "teacher"}).eq("id", user_id).execute()
        return True
    except Exception as e:
        st.error(f"承認エラー: {e}")
        return False


def reject_teacher(user_id: str) -> bool:
    """教員申請を却下してstudentに戻す"""
    try:
        from utils.database import get_supabase_client
        supabase = get_supabase_client()
        supabase.table("users").update({"role": "student"}).eq("id", user_id).execute()
        return True
    except Exception as e:
        st.error(f"却下エラー: {e}")
        return False
