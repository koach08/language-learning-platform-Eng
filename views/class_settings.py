import streamlit as st
from utils.auth import get_current_user, require_auth
from utils.database import (
    get_teacher_courses, create_course, update_course,
    get_course_settings, upsert_course_settings,
)
from datetime import datetime
import random
import string


@require_auth
def show():
    user = get_current_user()

    if user['role'] != 'teacher':
        st.error("教員のみアクセス可能です")
        return

    st.markdown("## 🎓 クラス設定")

    if st.button("← 教員ホームに戻る"):
        st.session_state['current_view'] = 'teacher_home'
        st.rerun()

    tab1, tab2, tab3 = st.tabs(["📋 クラス一覧", "➕ 新規作成", "⚙️ モジュール設定"])

    with tab1:
        show_class_list(user)
    with tab2:
        show_create_class(user)
    with tab3:
        show_module_settings(user)


def show_class_list(user):
    """クラス一覧（DB連携版）"""
    st.markdown("### 📋 クラス一覧")

    try:
        courses = get_teacher_courses(user['id'])
    except Exception as e:
        st.error(f"コース読み込みエラー: {e}")
        courses = []

    if not courses:
        st.info("まだクラスがありません。「➕ 新規作成」タブからクラスを作成してください。")
        return

    for c in courses:
        with st.expander(f"📚 {c['name']}（{c.get('year', '')}{c.get('semester', '')}）"):
            col1, col2 = st.columns(2)
            with col1:
                st.write(f"**クラスコード:** `{c.get('class_code', 'なし')}`")
                st.write(f"**作成日:** {c.get('created_at', '')[:10]}")
                st.write(f"**テンプレート:** {c.get('template_type', 'custom')}")
            with col2:
                st.write(f"**ステータス:** {'✅ アクティブ' if c.get('is_active') else '❌ 非アクティブ'}")
                st.write(f"**ID:** `{c['id'][:8]}...`")

            # 有効モジュール
            modules = c.get('active_modules', {})
            enabled = [k for k, v in modules.items() if v]
            st.write(f"**有効モジュール:** {', '.join(enabled) if enabled else 'なし'}")


def show_create_class(user):
    """クラス新規作成（DB保存版）"""
    st.markdown("### ➕ 新しいクラスを作成")

    with st.form("create_class_form"):
        class_name = st.text_input("クラス名 *", placeholder="例: 英語コミュニケーションI（月2）")

        col1, col2 = st.columns(2)
        with col1:
            year = st.selectbox("年度", [2026, 2025, 2024])
        with col2:
            semester = st.selectbox("学期", ["前期", "後期", "通年"])

        class_code = st.text_input(
            "クラスコード（任意）",
            placeholder="空欄なら自動生成（例: ENG1A2026）",
        )

        description = st.text_area("説明（任意）", placeholder="クラスの説明...")

        submitted = st.form_submit_button("✅ 作成", type="primary", use_container_width=True)

        if submitted:
            if not class_name:
                st.error("クラス名を入力してください")
            else:
                # クラスコード自動生成
                if not class_code.strip():
                    class_code = ''.join(random.choices(string.ascii_uppercase + string.digits, k=8))

                try:
                    course = create_course(
                        teacher_id=user['id'],
                        name=class_name,
                        year=year,
                        semester=semester,
                        template_type='custom',
                        class_code=class_code.strip(),
                        description=description or None,
                    )
                    if course:
                        # デフォルトモジュール設定も保存
                        try:
                            upsert_course_settings(course['id'], {
                                'modules': {
                                    'speaking': True, 'writing': True,
                                    'vocabulary': True, 'reading': True,
                                    'listening': True, 'test_prep': False,
                                }
                            })
                        except Exception:
                            pass
                        st.success(f"✅ クラスを作成しました！")
                        st.info(f"📋 **クラスコード:** `{class_code}`\n\nこのコードを学生に共有してください。")
                        st.cache_data.clear()
                        st.rerun()
                    else:
                        st.error("作成に失敗しました")
                except Exception as e:
                    st.error(f"作成エラー: {e}")
                    st.code(str(e))


def show_module_settings(user):
    """モジュール設定（DB連携版）"""
    st.markdown("### ⚙️ モジュール設定")

    try:
        courses = get_teacher_courses(user['id'])
    except Exception:
        courses = []

    if not courses:
        st.info("先にクラスを作成してください")
        return

    selected_course = st.selectbox(
        "クラスを選択",
        courses,
        format_func=lambda c: f"{c['name']}（{c.get('year', '')}{c.get('semester', '')}）"
    )

    if selected_course:
        # course_settingsからモジュール取得、なければactive_modulesを使用
        settings = None
        try:
            settings = get_course_settings(selected_course['id'])
        except Exception:
            pass

        modules = {}
        if settings and settings.get('modules'):
            modules = settings['modules']
        elif selected_course.get('active_modules'):
            modules = selected_course['active_modules']
        else:
            modules = {
                'speaking': True, 'writing': True, 'vocabulary': True,
                'reading': True, 'listening': True, 'test_prep': False,
            }

        st.markdown("---")
        st.markdown("#### 有効にするモジュール")

        col1, col2 = st.columns(2)
        with col1:
            speaking = st.checkbox("🗣️ Speaking", value=modules.get('speaking', True), key="ms_spk")
            writing = st.checkbox("✍️ Writing", value=modules.get('writing', True), key="ms_wrt")
            vocabulary = st.checkbox("📚 Vocabulary", value=modules.get('vocabulary', True), key="ms_voc")
        with col2:
            reading = st.checkbox("📖 Reading", value=modules.get('reading', True), key="ms_read")
            listening = st.checkbox("🎧 Listening", value=modules.get('listening', True), key="ms_lst")
            test_prep = st.checkbox("📝 検定対策", value=modules.get('test_prep', False), key="ms_test")

        if st.button("💾 保存", type="primary"):
            new_modules = {
                'speaking': speaking, 'writing': writing,
                'vocabulary': vocabulary, 'reading': reading,
                'listening': listening, 'test_prep': test_prep,
            }
            try:
                upsert_course_settings(selected_course['id'], {'modules': new_modules})
                st.success("✅ 設定を保存しました！")
                st.cache_data.clear()
                st.rerun()
            except Exception as e:
                st.error(f"保存エラー: {e}")
