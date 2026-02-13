"""
Student Management (DB連携版)
==============================
教員が学生をコースに追加・管理する画面。
"""

import streamlit as st
from utils.auth import get_current_user, require_auth
from utils.database import (
    get_teacher_courses, get_course_students, get_all_students,
    enroll_student, unenroll_student, get_course_by_class_code,
)


@require_auth
def show():
    user = get_current_user()

    if user['role'] != 'teacher':
        st.error("教員のみアクセス可能です")
        return

    st.markdown("## 👥 学生管理")

    if st.button("← 教員ホームに戻る"):
        st.session_state['current_view'] = 'teacher_home'
        st.rerun()

    st.markdown("---")

    # コース選択
    try:
        courses = get_teacher_courses(user['id'])
    except Exception as e:
        st.error(f"コース読み込みエラー: {e}")
        return

    if not courses:
        st.info("まだコースがありません。先にクラス設定でコースを作成してください。")
        return

    selected_course = st.selectbox(
        "📚 コースを選択",
        courses,
        format_func=lambda c: f"{c['name']}（{c.get('class_code', '')}）"
    )

    if not selected_course:
        return

    st.markdown(f"**クラスコード:** `{selected_course.get('class_code', 'なし')}` — このコードを学生に共有してください")

    tab1, tab2, tab3 = st.tabs(["📋 登録学生一覧", "➕ 学生を追加", "📊 クラス情報"])

    with tab1:
        show_enrolled_students(selected_course)
    with tab2:
        show_add_student(selected_course)
    with tab3:
        show_class_info(selected_course)


def show_enrolled_students(course):
    """コースに登録済みの学生一覧"""
    st.markdown("### 📋 登録学生一覧")

    try:
        students = get_course_students(course['id'])
    except Exception as e:
        st.error(f"学生一覧の取得エラー: {e}")
        return

    if not students:
        st.info("まだ学生が登録されていません。「➕ 学生を追加」タブから追加するか、学生にクラスコードを共有してください。")
        return

    st.success(f"登録学生数: {len(students)}名")

    for i, s in enumerate(students):
        col1, col2, col3 = st.columns([3, 2, 1])
        with col1:
            st.markdown(f"**{s.get('name', '不明')}**")
        with col2:
            st.caption(f"{s.get('email', '')}")
        with col3:
            if st.button("❌ 削除", key=f"unenroll_{i}_{s.get('id', '')}"):
                try:
                    unenroll_student(s['id'], course['id'])
                    st.success(f"{s.get('name', '')} を削除しました")
                    st.cache_data.clear()
                    st.rerun()
                except Exception as e:
                    st.error(f"削除エラー: {e}")


def show_add_student(course):
    """学生をコースに追加"""
    st.markdown("### ➕ 学生を追加")

    # 方法1: 既存学生リストから選択
    st.markdown("#### 方法1: 登録済みの学生から選択")

    try:
        all_students = get_all_students()
    except Exception:
        all_students = []

    if all_students:
        # 既に登録済みの学生を除外
        try:
            enrolled = get_course_students(course['id'])
            enrolled_ids = {s['id'] for s in enrolled}
        except Exception:
            enrolled_ids = set()

        available = [s for s in all_students if s['id'] not in enrolled_ids]

        if available:
            selected_students = st.multiselect(
                "追加する学生を選択",
                available,
                format_func=lambda s: f"{s['name']} ({s.get('email', '')})",
            )

            if st.button("✅ 選択した学生を追加", type="primary") and selected_students:
                added = 0
                for s in selected_students:
                    try:
                        enroll_student(s['id'], course['id'])
                        added += 1
                    except Exception as e:
                        if 'duplicate' not in str(e).lower():
                            st.warning(f"{s['name']} の追加に失敗: {e}")
                if added > 0:
                    st.success(f"✅ {added}名を追加しました")
                    st.cache_data.clear()
                    st.rerun()
        else:
            st.info("追加できる学生がいません（全員登録済み）")
    else:
        st.info("まだ学生がシステムに登録されていません")

    st.markdown("---")

    # 方法2: クラスコード共有案内
    st.markdown("#### 方法2: クラスコードを共有")
    code = course.get('class_code', 'なし')
    st.markdown(f"""
    学生に以下のクラスコードを共有してください。
    学生はログイン後、ホーム画面でこのコードを入力して自分で登録できます。
    
    **クラスコード: `{code}`**
    """)


def show_class_info(course):
    """クラス情報"""
    st.markdown("### 📊 クラス情報")

    col1, col2 = st.columns(2)
    with col1:
        st.write(f"**コース名:** {course['name']}")
        st.write(f"**年度:** {course.get('year', '')}")
        st.write(f"**学期:** {course.get('semester', '')}")
    with col2:
        st.write(f"**クラスコード:** `{course.get('class_code', 'なし')}`")
        st.write(f"**テンプレート:** {course.get('template_type', 'custom')}")
        st.write(f"**ステータス:** {'✅ アクティブ' if course.get('is_active') else '❌ 非アクティブ'}")

    try:
        students = get_course_students(course['id'])
        st.metric("登録学生数", f"{len(students)}名")
    except Exception:
        st.metric("登録学生数", "取得エラー")
