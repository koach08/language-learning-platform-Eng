"""
Student Management (DB連携版)
==============================
教員が学生をコースに追加・管理する画面。
学習カルテ（ポートフォリオ）への遷移機能付き。
"""
import streamlit as st
from utils.auth import get_current_user, require_auth
from utils.database import (
    get_teacher_courses,
    get_course_students,
    get_all_students,
    enroll_student,
    unenroll_student,
    get_course_by_class_code,
    get_course_student_profiles,
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
        courses = []

    if not courses:
        st.info("まだコースがありません。先にクラス設定でコースを作成してください。")
        # コースがなくても全学生タブは表示
        tab_all = st.tabs(["👤 全登録ユーザー"])
        with tab_all[0]:
            show_all_students_list(courses)
        return

    selected_course = st.selectbox(
        "📚 コースを選択",
        courses,
        format_func=lambda c: f"{c['name']}（{c.get('class_code', '')}）"
    )

    if not selected_course:
        return

    st.markdown(f"**クラスコード:** `{selected_course.get('class_code', 'なし')}` — このコードを学生に共有してください")

    tab1, tab2, tab3, tab4 = st.tabs([
        "📋 学生一覧・カルテ",
        "➕ 学生を追加",
        "👤 全登録ユーザー",
        "📊 クラス情報",
    ])

    with tab1:
        show_student_list_with_profiles(selected_course)

    with tab2:
        show_add_student(selected_course)

    with tab3:
        show_all_students_list(courses)

    with tab4:
        show_class_info(selected_course)


def show_student_list_with_profiles(course):
    """コースの学生一覧 + プロフィール概要 + カルテ遷移"""
    st.markdown("### 📋 学生一覧")

    try:
        students_with_profiles = get_course_student_profiles(course['id'])
    except Exception as e:
        st.error(f"学生データの取得エラー: {e}")
        return

    if not students_with_profiles:
        st.info("まだ学生が登録されていません。「➕ 学生を追加」タブから追加するか、学生にクラスコードを共有してください。")
        return

    st.success(f"登録学生数: {len(students_with_profiles)}名")

    # 検索
    search = st.text_input("🔍 学生を検索（名前・学籍番号・学部）", key="student_search")

    for i, s in enumerate(students_with_profiles):
        profile = s.get('profile', {}) or {}
        name = s.get('name', '不明')
        email = s.get('email', '')
        student_number = profile.get('student_number', '')
        faculty = profile.get('faculty', '')

        # 検索フィルタ
        if search:
            search_lower = search.lower()
            searchable = f"{name} {student_number} {faculty} {email}".lower()
            if search_lower not in searchable:
                continue

        col1, col2, col3, col4 = st.columns([2.5, 2, 1.5, 1])

        with col1:
            if st.button(f"**{name}**", key=f"name_{i}_{s.get('id', '')}",
                         help="クリックでカルテを表示"):
                st.session_state['selected_student'] = {
                    'id': s.get('id', ''),
                    'user_id': s.get('id', ''),
                    'name': name,
                    'email': email,
                    'student_id': student_number,
                    'profile': profile,
                }
                st.session_state['current_view'] = 'student_portfolio'
                st.rerun()
            if student_number:
                st.caption(f"学籍番号: {student_number}")
            else:
                st.caption(f"{email}")

        with col2:
            info_parts = []
            if faculty:
                info_parts.append(faculty)
            test_scores = profile.get('test_scores') or {}
            if test_scores:
                score_parts = []
                if test_scores.get('toefl_itp'):
                    score_parts.append(f"TOEFL ITP: {test_scores['toefl_itp']}")
                if test_scores.get('toeic'):
                    score_parts.append(f"TOEIC: {test_scores['toeic']}")
                if test_scores.get('eiken'):
                    score_parts.append(f"英検: {test_scores['eiken']}")
                if score_parts:
                    info_parts.append(" / ".join(score_parts))
            if info_parts:
                st.caption(" | ".join(info_parts))
            else:
                st.caption("プロフィール未入力")

        with col3:
            if st.button("📋 カルテ", key=f"karte_{i}_{s.get('id', '')}",
                         use_container_width=True):
                st.session_state['selected_student'] = {
                    'id': s.get('id', ''),
                    'user_id': s.get('id', ''),
                    'name': name,
                    'email': email,
                    'student_id': student_number,
                    'profile': profile,
                }
                st.session_state['current_view'] = 'student_portfolio'
                st.rerun()

        with col4:
            if st.button("❌", key=f"unenroll_{i}_{s.get('id', '')}",
                         help="コースから削除"):
                try:
                    unenroll_student(s['id'], course['id'])
                    st.success(f"{name} を削除しました")
                    st.cache_data.clear()
                    st.rerun()
                except Exception as e:
                    st.error(f"削除エラー: {e}")

        st.markdown("---")


def show_all_students_list(courses):
    """全登録ユーザー一覧（クラス未登録の学生も含む）"""
    st.markdown("### 👤 全登録ユーザー")
    st.caption("Googleログイン済みの全学生を表示します（クラス未登録の学生も含む）")

    try:
        all_students = get_all_students()
    except Exception as e:
        st.error(f"学生データの取得エラー: {e}")
        return

    if not all_students:
        st.info("まだ学生がシステムに登録されていません。")
        return

    # 全コースの登録学生IDを収集
    enrolled_map = {}  # student_id -> [course_name, ...]
    for course in courses:
        try:
            enrolled = get_course_students(course['id'])
            for s in enrolled:
                sid = s.get('id', '')
                if sid not in enrolled_map:
                    enrolled_map[sid] = []
                enrolled_map[sid].append(course.get('name', ''))
        except Exception:
            pass

    # 未登録 / 登録済みに分類
    not_enrolled = [s for s in all_students if s['id'] not in enrolled_map]
    enrolled_students = [s for s in all_students if s['id'] in enrolled_map]

    st.markdown(f"**全学生: {len(all_students)}名** （クラス登録済み: {len(enrolled_students)}名 / 未登録: {len(not_enrolled)}名）")

    # 検索
    search = st.text_input("🔍 検索（名前・メール）", key="all_student_search")

    # フィルタ
    filter_opt = st.radio("表示フィルタ", ["全て", "クラス未登録のみ", "クラス登録済みのみ"],
                          horizontal=True, key="all_student_filter")

    if filter_opt == "クラス未登録のみ":
        display_list = not_enrolled
    elif filter_opt == "クラス登録済みのみ":
        display_list = enrolled_students
    else:
        display_list = all_students

    for i, s in enumerate(display_list):
        name = s.get('name', '不明')
        email = s.get('email', '')
        sid = s.get('id', '')

        # 検索フィルタ
        if search:
            if search.lower() not in f"{name} {email}".lower():
                continue

        student_courses = enrolled_map.get(sid, [])
        is_enrolled = len(student_courses) > 0

        col1, col2, col3 = st.columns([3, 2, 1.5])

        with col1:
            st.markdown(f"**{name}**")
            st.caption(email)

        with col2:
            if is_enrolled:
                st.success(f"✅ {', '.join(student_courses)}")
            else:
                st.warning("⚠️ クラス未登録")

        with col3:
            if not is_enrolled and courses:
                # 未登録の場合、コースに追加ボタン
                if st.button("➕ 追加", key=f"add_all_{i}_{sid}", use_container_width=True):
                    try:
                        enroll_student(sid, courses[0]['id'])
                        st.success(f"✅ {name} を {courses[0]['name']} に追加しました")
                        st.cache_data.clear()
                        st.rerun()
                    except Exception as e:
                        if 'duplicate' in str(e).lower():
                            st.warning("すでに登録済みです")
                        else:
                            st.error(f"追加エラー: {e}")
            elif is_enrolled:
                if st.button("📋 カルテ", key=f"karte_all_{i}_{sid}", use_container_width=True):
                    st.session_state['selected_student'] = {
                        'id': sid,
                        'user_id': sid,
                        'name': name,
                        'email': email,
                    }
                    st.session_state['current_view'] = 'student_portfolio'
                    st.rerun()

        if i < len(display_list) - 1:
            st.markdown("---")


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
