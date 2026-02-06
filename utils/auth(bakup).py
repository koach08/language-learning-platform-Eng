"""
Authentication Module
=====================
Supabase Auth with Google OAuth
"""

import streamlit as st
from typing import Optional, Dict
import urllib.parse


def get_auth_url() -> str:
    """Google OAuth認証URLを生成"""
    supabase_url = st.secrets["supabase"]["url"]
    redirect_url = _get_redirect_url()
    
    # Supabase OAuth URL
    auth_url = f"{supabase_url}/auth/v1/authorize"
    params = {
        "provider": "google",
        "redirect_to": redirect_url
    }
    return f"{auth_url}?{urllib.parse.urlencode(params)}"


def _get_redirect_url() -> str:
    """リダイレクトURLを取得"""
    # Streamlit Cloudの場合はそのURLを使用
    # ローカルの場合はlocalhost
    try:
        # Streamlit >= 1.30 では st.context.headers が使える場合がある
        # フォールバックとして設定値を使用
        return st.secrets.get("app", {}).get("redirect_url", "http://localhost:8501")
    except:
        return "http://localhost:8501"


def handle_oauth_callback():
    """OAuthコールバックを処理"""
    # URLからaccess_tokenとrefresh_tokenを取得
    query_params = st.query_params
    
    # Supabaseからのコールバックでフラグメントにトークンが含まれる場合
    # JavaScriptで処理する必要がある
    if 'access_token' in query_params:
        access_token = query_params['access_token']
        refresh_token = query_params.get('refresh_token', '')
        
        # セッションに保存
        st.session_state['access_token'] = access_token
        st.session_state['refresh_token'] = refresh_token
        
        # ユーザー情報を取得
        user_info = get_user_from_token(access_token)
        if user_info:
            st.session_state['user'] = user_info
            st.session_state['authenticated'] = True
        
        # クエリパラメータをクリア
        st.query_params.clear()
        return True
    
    return False


def get_user_from_token(access_token: str) -> Optional[Dict]:
    """アクセストークンからユーザー情報を取得"""
    from utils.database import get_supabase_client, get_or_create_user
    
    try:
        supabase = get_supabase_client()
        # トークンでユーザー情報を取得
        user_response = supabase.auth.get_user(access_token)
        
        if user_response and user_response.user:
            auth_user = user_response.user
            email = auth_user.email
            
            # user_metadataから名前とプロフィール画像を取得
            metadata = auth_user.user_metadata or {}
            name = metadata.get('full_name') or metadata.get('name') or email.split('@')[0]
            avatar_url = metadata.get('avatar_url') or metadata.get('picture')
            
            # データベースでユーザーを取得または作成
            db_user = get_or_create_user(email, name, avatar_url)
            
            return {
                'id': db_user['id'],
                'email': email,
                'name': db_user['name'],
                'role': db_user['role'],
                'student_id': db_user.get('student_id'),
                'profile_image_url': db_user.get('profile_image_url'),
                'auth_id': str(auth_user.id)
            }
    except Exception as e:
        st.error(f"ユーザー情報の取得に失敗しました: {e}")
        if st.secrets.get("app", {}).get("debug", False):
            st.exception(e)
    
    return None


def login_with_google():
    """Googleログインボタンを表示"""
    auth_url = get_auth_url()
    
    # カスタムスタイルのGoogleログインボタン
    st.markdown("""
    <style>
    .google-btn {
        display: inline-flex;
        align-items: center;
        justify-content: center;
        padding: 12px 24px;
        background-color: white;
        color: #444;
        border: 1px solid #ddd;
        border-radius: 8px;
        font-size: 16px;
        font-weight: 500;
        text-decoration: none;
        transition: all 0.2s;
        box-shadow: 0 1px 3px rgba(0,0,0,0.1);
    }
    .google-btn:hover {
        background-color: #f8f8f8;
        box-shadow: 0 2px 6px rgba(0,0,0,0.15);
        text-decoration: none;
        color: #333;
    }
    .google-btn img {
        margin-right: 12px;
    }
    </style>
    """, unsafe_allow_html=True)
    
    st.markdown(f"""
    <a href="{auth_url}" class="google-btn">
        <img src="https://www.google.com/favicon.ico" width="20" height="20">
        Googleアカウントでログイン
    </a>
    """, unsafe_allow_html=True)


def logout():
    """ログアウト"""
    # セッションをクリア
    keys_to_clear = ['user', 'authenticated', 'access_token', 'refresh_token', 
                     'current_course', 'current_view']
    for key in keys_to_clear:
        if key in st.session_state:
            del st.session_state[key]
    
    # Supabaseからもログアウト
    try:
        from utils.database import get_supabase_client
        supabase = get_supabase_client()
        supabase.auth.sign_out()
    except:
        pass
    
    st.rerun()


def is_authenticated() -> bool:
    """認証済みかどうか"""
    return st.session_state.get('authenticated', False)


def get_current_user() -> Optional[Dict]:
    """現在のユーザーを取得"""
    return st.session_state.get('user')


def is_teacher() -> bool:
    """教員かどうか"""
    user = get_current_user()
    return user and user.get('role') == 'teacher'


def is_student() -> bool:
    """学生かどうか"""
    user = get_current_user()
    return user and user.get('role') == 'student'


def require_auth(func):
    """認証が必要なページのデコレータ"""
    def wrapper(*args, **kwargs):
        if not is_authenticated():
            st.warning("このページにアクセスするにはログインが必要です。")
            login_with_google()
            st.stop()
        return func(*args, **kwargs)
    return wrapper


def require_teacher(func):
    """教員権限が必要なページのデコレータ"""
    def wrapper(*args, **kwargs):
        if not is_authenticated():
            st.warning("このページにアクセスするにはログインが必要です。")
            login_with_google()
            st.stop()
        if not is_teacher():
            st.error("このページは教員専用です。")
            st.stop()
        return func(*args, **kwargs)
    return wrapper


def require_student(func):
    """学生権限が必要なページのデコレータ"""
    def wrapper(*args, **kwargs):
        if not is_authenticated():
            st.warning("このページにアクセスするにはログインが必要です。")
            login_with_google()
            st.stop()
        if not is_student():
            st.error("このページは学生専用です。")
            st.stop()
        return func(*args, **kwargs)
    return wrapper


# ============================================================
# OAuth Callback Handler (JavaScript)
# ============================================================

def inject_oauth_handler():
    """OAuthコールバック用のJavaScriptを注入"""
    st.markdown("""
    <script>
    // URLフラグメントからトークンを取得してクエリパラメータに変換
    (function() {
        const hash = window.location.hash.substring(1);
        if (hash && hash.includes('access_token')) {
            const params = new URLSearchParams(hash);
            const accessToken = params.get('access_token');
            const refreshToken = params.get('refresh_token');
            
            if (accessToken) {
                // クエリパラメータとしてリダイレクト
                const newUrl = window.location.pathname + 
                    '?access_token=' + encodeURIComponent(accessToken) +
                    (refreshToken ? '&refresh_token=' + encodeURIComponent(refreshToken) : '');
                window.location.href = newUrl;
            }
        }
    })();
    </script>
    """, unsafe_allow_html=True)
