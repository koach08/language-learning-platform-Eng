import streamlit as st

st.set_page_config(
    page_title="English Learning Platform",
    page_icon="🎓",
    layout="wide",
    initial_sidebar_state="collapsed",
)

from utils.auth import (
    get_current_user, logout, handle_oauth_callback,
)

# OAuth callback handling
if handle_oauth_callback():
    st.rerun()

if "user" not in st.session_state:
    st.session_state.user = None
if "current_view" not in st.session_state:
    st.session_state.current_view = None

from views import login, teacher_home, student_home
from views import vocabulary, reading, listening
from views import writing_submit as writing

def safe_import(module_name):
    try:
        return __import__(f"views.{module_name}", fromlist=[module_name])
    except ImportError:
        return None

speaking = safe_import("speaking")
speaking_chat = safe_import("speaking_chat")
course_settings = safe_import("course_settings")
class_settings = safe_import("class_settings")
teacher_dashboard = safe_import("teacher_dashboard")
student_management = safe_import("student_management")
student_portfolio = safe_import("student_portfolio")
assignments = safe_import("assignments")
grades = safe_import("grades")
learning_log = safe_import("learning_log")
test_prep = safe_import("test_prep")
learning_resources = safe_import("learning_resources")

def get_student_enabled_modules(user):
    class_key = user.get("class_key")
    if not class_key:
        return ["speaking", "writing", "vocabulary", "reading", "listening", "test_prep"]
    teacher_classes = st.session_state.get("teacher_classes", {})
    if class_key in teacher_classes:
        modules = teacher_classes[class_key].get("modules", {})
        return [k for k, v in modules.items() if v]
    return ["speaking", "writing", "vocabulary", "reading", "listening", "test_prep"]

user = get_current_user()

if user:
    with st.sidebar:
        st.markdown(f"### 👤 {user['name']}")
        if user["role"] == "teacher":
            st.caption("👨‍🏫 教員")
        else:
            st.caption("🎓 学生")
            if user.get("class_name"):
                st.caption(f"📚 {user['class_name']}")
            try:
                from utils.gamification import get_gamification_data, update_streak, get_current_level
                update_streak()
                gdata = get_gamification_data()
                glevel = get_current_level(gdata["total_xp"])
                streak = gdata["current_streak"]
                st.markdown(f"**{glevel['icon']} Lv.{glevel['level']}** | ⭐{gdata['total_xp']} XP | 🔥{streak}日")
            except Exception:
                pass
        st.markdown("---")
        if user["role"] == "teacher":
            st.markdown("#### 📊 管理")
            if st.button("🏠 ホーム", use_container_width=True):
                st.session_state["current_view"] = "teacher_home"
                st.rerun()
            if st.button("📊 ダッシュボード", use_container_width=True):
                st.session_state["current_view"] = "teacher_dashboard"
                st.rerun()
            if st.button("👥 学生管理", use_container_width=True):
                st.session_state["current_view"] = "student_management"
                st.rerun()
            if st.button("📝 課題管理", use_container_width=True):
                st.session_state["current_view"] = "assignments"
                st.rerun()
            if st.button("📈 成績集計", use_container_width=True):
                st.session_state["current_view"] = "grades"
                st.rerun()
            if st.button("💬 メッセージ", use_container_width=True):
                st.session_state["current_view"] = "messaging"
                st.rerun()
            st.markdown("---")
            st.markdown("#### ⚙️ 設定")
            if st.button("🎓 クラス設定", use_container_width=True):
                st.session_state["current_view"] = "class_settings"
                st.rerun()
            if st.button("⚙️ 科目設定", use_container_width=True):
                st.session_state["current_view"] = "course_settings"
                st.rerun()
            st.markdown("---")
            st.markdown("#### 👁 プレビュー")
            st.caption("学生画面を確認")
            if st.button("🗣️ Speaking", use_container_width=True):
                st.session_state["current_view"] = "speaking"
                st.rerun()
            if st.button("✏️ Writing", use_container_width=True):
                st.session_state["current_view"] = "writing"
                st.rerun()
            if st.button("📚 Vocabulary", use_container_width=True):
                st.session_state["current_view"] = "vocabulary"
                st.rerun()
            if st.button("📖 Reading", use_container_width=True):
                st.session_state["current_view"] = "reading"
                st.rerun()
            if st.button("🎧 Listening", use_container_width=True):
                st.session_state["current_view"] = "listening"
                st.rerun()
            if st.button("📝 検定対策", use_container_width=True):
                st.session_state["current_view"] = "test_prep"
                st.rerun()
        else:
            st.markdown("#### 🎓 学習")
            if st.button("🏠 ホーム", use_container_width=True):
                st.session_state["current_view"] = "student_home"
                st.rerun()
            if st.button("📖 マイ単語帳", use_container_width=True):
                st.session_state["current_view"] = "word_book"
                st.rerun()
            if st.button("📊 学習分析", use_container_width=True):
                st.session_state["current_view"] = "analytics"
                st.rerun()
            if st.button("💬 メッセージ", use_container_width=True):
                st.session_state["current_view"] = "messaging"
                st.rerun()
            if st.button("📝 授業外学習ログ", use_container_width=True):
                st.session_state["current_view"] = "learning_log"
                st.rerun()
            if st.button("📋 マイポートフォリオ", use_container_width=True):
                st.session_state["current_view"] = "student_portfolio"
                st.rerun()
            st.markdown("---")
            st.markdown("#### 📚 モジュール")
            enabled = get_student_enabled_modules(user)
            if "speaking" in enabled:
                if st.button("🗣️ Speaking", use_container_width=True):
                    st.session_state["current_view"] = "speaking"
                    st.rerun()
            if "writing" in enabled:
                if st.button("✏️ Writing", use_container_width=True):
                    st.session_state["current_view"] = "writing"
                    st.rerun()
            if "reading" in enabled:
                if st.button("📖 Reading", use_container_width=True):
                    st.session_state["current_view"] = "reading"
                    st.rerun()
            if "listening" in enabled:
                if st.button("🎧 Listening", use_container_width=True):
                    st.session_state["current_view"] = "listening"
                    st.rerun()
            st.markdown("---")
            st.markdown("#### 📝 辞書")
            try:
                from utils.dictionary import show_dictionary_popup
                show_dictionary_popup(word_key="sidebar_dict")
            except Exception:
                st.info("辞書機能を読み込み中...")
            if "vocabulary" in enabled:
                if st.button("📚 Vocabulary", use_container_width=True):
                    st.session_state["current_view"] = "vocabulary"
                    st.rerun()
            if "test_prep" in enabled:
                if st.button("📝 検定対策", use_container_width=True):
                    st.session_state["current_view"] = "test_prep"
                    st.rerun()
            # --- 学習補助ページ ---
            st.markdown("---")
            st.markdown("#### 🚀 学習補助")
            if st.button("🤖 AIプロンプト集・学習リソース", use_container_width=True):
                st.session_state["current_view"] = "learning_resources"
                st.rerun()
        st.markdown("---")
        if st.button("📘 使い方ガイド / Help", use_container_width=True):
            st.session_state["current_view"] = "help"
            st.rerun()
        if st.button("🚪 ログアウト", use_container_width=True):
            logout()

def main():
    if not user:
        login.show()
        return
    if user["role"] == "student" and not user.get("student_id"):
        from views.login import show_registration_form
        show_registration_form()
    default_view = "teacher_home" if user["role"] == "teacher" else "student_home"
    view = st.session_state.get("current_view", default_view)
    teacher_only_views = ["teacher_home", "teacher_dashboard", "student_management",
                          "assignments", "grades", "class_settings", "course_settings"]
    if user["role"] == "student" and view in teacher_only_views:
        view = "student_home"
    if view == "word_book":
        show_word_book_view()
        return
    if view == "analytics":
        show_analytics_view()
        return
    if view == "messaging":
        show_messaging_view()
        return
    if view == "phonetics":
        show_phonetics_view()
        return
    if view == "help":
        show_help_view()
        return
    if view == "learning_resources":
        show_learning_resources_view()
        return
    views = {
        "teacher_home": teacher_home.show,
        "student_home": student_home.show,
        "speaking": speaking.show if speaking else student_home.show,
        "speaking_chat": speaking_chat.show if speaking_chat else student_home.show,
        "writing": writing.show,
        "vocabulary": vocabulary.show,
        "reading": reading.show,
        "listening": listening.show,
        "course_settings": course_settings.show if course_settings else teacher_home.show,
        "class_settings": class_settings.show if class_settings else teacher_home.show,
        "teacher_dashboard": teacher_dashboard.show if teacher_dashboard else teacher_home.show,
        "student_management": student_management.show if student_management else teacher_home.show,
        "student_portfolio": student_portfolio.show if student_portfolio else student_home.show,
        "assignments": assignments.show if assignments else teacher_home.show,
        "grades": grades.show if grades else teacher_home.show,
        "learning_log": learning_log.show if learning_log else student_home.show,
        "test_prep": test_prep.show if test_prep else student_home.show,
    }
    views.get(view, student_home.show if user["role"] == "student" else teacher_home.show)()

def show_word_book_view():
    st.markdown("## 📖 マイ単語帳 / My Word Book")
    if st.button("← ホームに戻る"):
        st.session_state["current_view"] = "student_home"
        st.rerun()
    st.markdown("---")
    tab1, tab2, tab3 = st.tabs(["🧠 復習 (SRS)", "📖 単語帳", "📝 辞書検索"])
    with tab1:
        try:
            from utils.srs import show_srs_review
            show_srs_review()
        except Exception as e:
            st.error(f"読み込みエラー: {e}")
    with tab2:
        try:
            from utils.dictionary import show_word_book_full
            show_word_book_full()
        except Exception as e:
            st.error(f"読み込みエラー: {e}")
    with tab3:
        try:
            from utils.dictionary import show_dictionary_popup
            show_dictionary_popup(word_key="wordbook_dict")
        except Exception as e:
            st.error(f"読み込みエラー: {e}")

def show_help_view():
    user = get_current_user()
    if user:
        try:
            from utils.help_guide import show_help_page
            show_help_page(user)
        except Exception as e:
            st.error(f"読み込みエラー: {e}")
    else:
        st.warning("ログインしてください")

def show_phonetics_view():
    st.markdown("## 🔊 発音ヘルパー / Pronunciation Helper")
    if st.button("← ホームに戻る"):
        st.session_state["current_view"] = "student_home"
        st.rerun()
    st.markdown("---")
    try:
        from utils.phonetics import show_phonetic_helper
        show_phonetic_helper()
    except Exception as e:
        st.error(f"読み込みエラー: {e}")

def show_messaging_view():
    user = get_current_user()
    if user:
        try:
            from utils.messaging import show_messaging_page
            show_messaging_page(user)
        except Exception as e:
            st.error(f"読み込みエラー: {e}")
    else:
        st.warning("ログインしてください")

def show_analytics_view():
    st.markdown("## 📊 学習分析 / Learning Analytics")
    if st.button("← ホームに戻る"):
        user = get_current_user()
        st.session_state["current_view"] = (
            "teacher_home" if user and user["role"] == "teacher" else "student_home"
        )
        st.rerun()
    st.markdown("---")
    user = get_current_user()
    if user and user["role"] == "teacher":
        try:
            from utils.analytics import show_teacher_analytics
            show_teacher_analytics()
        except Exception as e:
            st.error(f"読み込みエラー: {e}")
    else:
        try:
            from utils.analytics import show_analytics_dashboard
            show_analytics_dashboard()
        except Exception as e:
            st.error(f"読み込みエラー: {e}")

def show_learning_resources_view():
    """学習補助ページ表示"""
    if learning_resources:
        learning_resources.show()
    else:
        st.error("学習補助ページの読み込みに失敗しました")

if __name__ == "__main__":
    main()
