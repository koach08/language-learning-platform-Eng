import streamlit as st
from utils.auth import get_current_user, require_auth
from utils.database import (
    get_teacher_courses, create_course, get_course,
    get_course_students, get_course_settings, update_course,
)

# ============================================================
# デフォルトクラス（DB未登録時のフォールバック / マイグレーション元）
# ============================================================
DEFAULT_CLASSES = {
    "english_specific_a": {
        "name": "英語特定技能演習A（発信）",
        "term": "2025前期",
        "code": "ESA2025A",
        "year": 2025,
        "semester": "前期",
        "modules": {
            "speaking": True, "writing": True, "vocabulary": True,
            "reading": False, "listening": False, "test_prep": False,
        }
    },
    "english_specific_b": {
        "name": "英語特定技能演習B（受信）",
        "term": "2025前期",
        "code": "ESB2025B",
        "year": 2025,
        "semester": "前期",
        "modules": {
            "speaking": False, "writing": False, "vocabulary": True,
            "reading": True, "listening": True, "test_prep": False,
        }
    },
    "english_1_a": {
        "name": "英語I Aクラス",
        "term": "2025前期",
        "code": "ENG1A2025",
        "year": 2025,
        "semester": "前期",
        "modules": {
            "speaking": True, "writing": True, "vocabulary": True,
            "reading": True, "listening": True, "test_prep": False,
        }
    },
    "english_seminar": {
        "name": "英語演習",
        "term": "2025前期",
        "code": "ENGSEM2025",
        "year": 2025,
        "semester": "前期",
        "modules": {
            "speaking": True, "writing": True, "vocabulary": True,
            "reading": True, "listening": True, "test_prep": False,
        }
    }
}


def _load_classes(user_id: str) -> dict:
    """DBからコース一覧を取得。なければDEFAULT_CLASSESをフォールバック。
    
    Returns:
        dict: {class_key: class_data} 形式。
              DBコースの場合 class_data に 'db_id' キーが入る。
    """
    try:
        db_courses = get_teacher_courses(user_id)
    except Exception:
        db_courses = []

    if db_courses:
        classes = {}
        for c in db_courses:
            # course_settingsからモジュール設定を取得
            settings = None
            try:
                settings = get_course_settings(c['id'])
            except Exception:
                pass

            modules = (settings or {}).get('modules', {
                "speaking": True, "writing": True, "vocabulary": True,
                "reading": True, "listening": True, "test_prep": False,
            })

            key = c['id']  # UUIDをキーに使用
            classes[key] = {
                "db_id": c['id'],
                "name": c['name'],
                "term": f"{c.get('year', '')}{c.get('semester', '')}",
                "code": c.get('class_code', c['id'][:8]),
                "year": c.get('year', 2025),
                "semester": c.get('semester', ''),
                "modules": modules,
                "is_active": c.get('is_active', True),
            }
        return classes

    # フォールバック: DEFAULT_CLASSES
    return DEFAULT_CLASSES.copy()


def _migrate_default_to_db(user_id: str) -> int:
    """DEFAULT_CLASSESをDBに一括登録する（初回マイグレーション用）"""
    created = 0
    errors = []
    for key, cls in DEFAULT_CLASSES.items():
        try:
            course = create_course(
                teacher_id=user_id,
                name=cls['name'],
                year=cls.get('year', 2025),
                semester=cls.get('semester', '前期'),
                template_type='custom',
                class_code=cls.get('code', key),
            )
            if course:
                # course_settingsにモジュール設定を保存
                try:
                    from utils.database import upsert_course_settings
                    upsert_course_settings(course['id'], {
                        'modules': cls['modules'],
                    })
                except Exception as e2:
                    errors.append(f"設定保存エラー ({cls['name']}): {e2}")
                created += 1
        except Exception as e:
            errors.append(f"コース作成エラー ({cls['name']}): {e}")

    # エラーがあれば表示（消えないようにする）
    for err in errors:
        st.error(err)

    return created


@require_auth
def show():
    user = get_current_user()

    if user['role'] != 'teacher':
        st.session_state['current_view'] = 'student_home'
        st.rerun()
        return

    st.markdown("## 👨‍🏫 教員ダッシュボード")
    st.markdown(f"ようこそ、{user['name']} 先生")

    # --------------------------------------------------
    # クラス読み込み（DB優先 → DEFAULT_CLASSESフォールバック）
    # --------------------------------------------------
    classes = _load_classes(user['id'])

    # session_stateに反映（学生側のモジュール判定で使う）
    st.session_state.teacher_classes = classes

    if 'class_students' not in st.session_state:
        st.session_state.class_students = {}

    # DBにコースがない場合のマイグレーション提案
    is_fallback = all('db_id' not in v for v in classes.values())
    if is_fallback:
        st.warning("⚠️ コースがまだデータベースに登録されていません（現在はデフォルト設定を表示中）")
        col1, col2 = st.columns(2)
        with col1:
            if st.button("📥 デフォルトクラスをDBに一括登録", type="primary", use_container_width=True):
                with st.spinner("コースを登録中..."):
                    try:
                        count = _migrate_default_to_db(user['id'])
                        if count > 0:
                            st.success(f"✅ {count}件のコースをDBに登録しました")
                            st.cache_data.clear()
                            import time
                            time.sleep(2)  # 成功メッセージを見せる
                            st.rerun()
                        else:
                            st.error("❌ コースの登録に失敗しました。上のエラーメッセージを確認してください。")
                    except Exception as e:
                        st.error(f"❌ 一括登録エラー: {e}")
                        st.code(str(e))  # 詳細エラーを表示
        with col2:
            if st.button("➕ 新規コースを作成", use_container_width=True):
                st.session_state['current_view'] = 'class_settings'
                st.rerun()
        st.markdown("---")

    # アラート通知バー
    show_alert_summary_bar()

    st.markdown("---")

    # クラス選択
    if not classes:
        st.warning("まだクラスが作成されていません")
        if st.button("➕ クラスを作成"):
            st.session_state['current_view'] = 'class_settings'
            st.rerun()
        return

    selected_class_key = st.selectbox(
        "📚 クラスを選択",
        list(classes.keys()),
        format_func=lambda x: f"{classes[x]['name']} ({classes[x].get('term', '')})"
    )

    st.session_state['selected_class'] = selected_class_key
    selected_class = classes[selected_class_key]

    # DBコースの場合、学生一覧もDBから取得
    if selected_class.get('db_id'):
        try:
            db_students = get_course_students(selected_class['db_id'])
            st.session_state.class_students[selected_class_key] = [
                {
                    'id': s.get('id', ''),
                    'name': s.get('name', ''),
                    'email': s.get('email', ''),
                    'student_id': s.get('student_id', ''),
                }
                for s in db_students
            ]
        except Exception as e:
            st.warning(f"学生データ取得エラー: {e}")

    st.markdown("---")

    # クラスサマリー
    show_class_summary(selected_class_key, selected_class)

    # クイックアクション
    show_quick_actions(selected_class_key)

    # モジュール設定（オン/オフ）
    show_module_settings(selected_class_key, selected_class)

    # 教員ツール
    show_teacher_tools_section()

    # 最近の活動
    show_recent_class_activity(selected_class_key)


# ============================================================
# サブ関数（既存ロジックをほぼ維持）
# ============================================================

def show_alert_summary_bar():
    """アラート通知バー（ページ上部）"""
    try:
        # 選択中クラスのcourse_idを取得
        selected_class = st.session_state.get('selected_class')
        classes = st.session_state.get('teacher_classes', {})
        course_id = None
        if selected_class and selected_class in classes:
            course_id = classes[selected_class].get('db_id') or classes[selected_class].get('course_id')
        
        if not course_id:
            return
        
        from utils.teacher_tools import get_student_alerts
        alerts = get_student_alerts(course_id=course_id)
        high = len([a for a in alerts if a['severity'] == 'high'])
        medium = len([a for a in alerts if a['severity'] == 'medium'])
        if high > 0:
            st.error(f"🚨 重要アラート {high}件 | ⚠️ 注意 {medium}件 — 下の「教員ツール」セクションで詳細を確認")
        elif medium > 0:
            st.warning(f"⚠️ 注意アラート {medium}件 — 下の「教員ツール」セクションで詳細を確認")
    except Exception:
        pass


def show_class_summary(class_key, class_data):
    """クラスサマリー"""
    st.markdown(f"### 📊 {class_data['name']}")

    col1, col2 = st.columns([3, 1])
    with col1:
        st.caption(f"クラスコード: `{class_data.get('code', 'N/A')}` | {class_data.get('term', '')}")
        if class_data.get('db_id'):
            st.caption("✅ DB連携済み")
        else:
            st.caption("⚠️ ローカル設定（DBに未登録）")
    with col2:
        if st.button("📋 コードをコピー"):
            st.success("コピーしました！")

    class_students = st.session_state.class_students.get(class_key, [])
    student_count = len(class_students)

    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("登録学生数", f"{student_count}名")
    with col2:
        if class_students:
            active = len([s for s in class_students if s.get('days_since_active', 99) <= 7])
            rate = (active / student_count * 100) if student_count > 0 else 0
            st.metric("今週アクティブ", f"{active}名 ({rate:.0f}%)")
        else:
            st.metric("今週アクティブ", "0名")
    with col3:
        if class_students:
            at_risk = len([s for s in class_students if s.get('days_since_active', 0) > 7 or s.get('avg_score', 100) < 50])
            st.metric("要注意", f"{at_risk}名", delta=None if at_risk == 0 else f"{at_risk}名", delta_color="inverse")
        else:
            st.metric("要注意", "0名")
    with col4:
        if class_students:
            avg = sum(s.get('avg_score', 0) for s in class_students) / student_count if student_count > 0 else 0
            st.metric("クラス平均", f"{avg:.1f}点")
        else:
            st.metric("クラス平均", "-")

    modules = class_data.get('modules', {})
    enabled_modules = [k for k, v in modules.items() if v]
    if enabled_modules:
        module_names = {
            "speaking": "🗣️ Speaking", "writing": "✍️ Writing",
            "vocabulary": "📚 Vocabulary", "reading": "📖 Reading",
            "listening": "🎧 Listening", "test_prep": "📝 検定対策",
        }
        enabled_str = " | ".join([module_names.get(m, m) for m in enabled_modules])
        st.caption(f"有効モジュール: {enabled_str}")


def show_quick_actions(class_key):
    """クイックアクション"""
    st.markdown("---")
    st.markdown("### ⚡ クイックアクション")

    col1, col2, col3, col4 = st.columns(4)
    with col1:
        if st.button("👥 学生一覧", use_container_width=True):
            st.session_state['current_view'] = 'student_management'
            st.rerun()
    with col2:
        if st.button("📝 課題管理", use_container_width=True):
            st.session_state['current_view'] = 'assignments'
            st.rerun()
    with col3:
        if st.button("📈 成績集計", use_container_width=True):
            st.session_state['current_view'] = 'grades'
            st.rerun()
    with col4:
        if st.button("⚙️ クラス設定", use_container_width=True):
            st.session_state['current_view'] = 'class_settings'
            st.rerun()

    col1, col2, col3, col4 = st.columns(4)
    with col1:
        if st.button("📊 詳細ダッシュボード", use_container_width=True):
            st.session_state['current_view'] = 'teacher_dashboard'
            st.rerun()
    with col2:
        if st.button("📊 学習分析", use_container_width=True):
            st.session_state['current_view'] = 'analytics'
            st.rerun()
    with col3:
        if st.button("📥 データ出力", use_container_width=True):
            st.success("CSVをダウンロードしました（※デモ）")
    with col4:
        if st.button("➕ 学生追加", use_container_width=True):
            st.session_state['current_view'] = 'student_management'
            st.rerun()


def show_module_settings(class_key, class_data):
    """モジュール設定（オン/オフ） — DB連携版"""
    st.markdown("---")
    st.markdown("### 🎛️ モジュール設定")
    st.caption("このクラスで学生が使用できるモジュールを設定します")

    current_modules = class_data.get('modules', {
        "speaking": True, "writing": True, "vocabulary": True,
        "reading": True, "listening": True, "test_prep": False,
    })

    module_info = {
        "speaking": {"name": "🗣️ Speaking", "desc": "音読・会話・スピーチ練習"},
        "writing": {"name": "✍️ Writing", "desc": "エッセイ・メール作成、AI添削"},
        "vocabulary": {"name": "📚 Vocabulary", "desc": "単語学習、フラッシュカード"},
        "reading": {"name": "📖 Reading", "desc": "読解練習、速読"},
        "listening": {"name": "🎧 Listening", "desc": "YouTube学習、ディクテーション"},
        "test_prep": {"name": "📝 検定対策", "desc": "TOEFL/TOEIC対策"},
    }

    col1, col2 = st.columns(2)
    updated_modules = {}
    module_keys = list(module_info.keys())

    for i, mod_key in enumerate(module_keys):
        info = module_info[mod_key]
        current_state = current_modules.get(mod_key, False)
        with col1 if i % 2 == 0 else col2:
            new_state = st.toggle(
                f"{info['name']}", value=current_state,
                key=f"module_toggle_{class_key}_{mod_key}",
                help=info['desc'],
            )
            updated_modules[mod_key] = new_state
            if new_state:
                st.caption(f"✅ {info['desc']}")
            else:
                st.caption("⬜ オフ")

    if updated_modules != current_modules:
        # session_state更新
        st.session_state.teacher_classes[class_key]['modules'] = updated_modules

        # DBコースならcourse_settingsにも保存
        db_id = class_data.get('db_id')
        if db_id:
            try:
                from utils.database import upsert_course_settings
                upsert_course_settings(db_id, {'modules': updated_modules})
            except Exception as e:
                st.warning(f"DB保存エラー: {e}")

        st.success("モジュール設定を更新しました！")
        st.rerun()


def show_teacher_tools_section():
    """教員ツールセクション"""
    st.markdown("---")
    st.markdown("### 🛠️ 教員ツール")

    tab1, tab2, tab3 = st.tabs(["🔔 学生アラート", "📨 フィードバック", "📊 成績ツール"])
    with tab1:
        try:
            from utils.teacher_tools import show_alert_dashboard
            show_alert_dashboard()
        except Exception as e:
            st.error(f"読み込みエラー: {e}")
    with tab2:
        try:
            from utils.teacher_tools import show_batch_feedback_ui
            show_batch_feedback_ui()
        except Exception as e:
            st.error(f"読み込みエラー: {e}")
    with tab3:
        try:
            from utils.teacher_tools import show_grade_tools
            show_grade_tools()
        except Exception as e:
            st.error(f"読み込みエラー: {e}")


def show_recent_class_activity(class_key):
    """クラスの最近の活動"""
    st.markdown("---")
    st.markdown("### 📈 最近の活動")

    classes = st.session_state.teacher_classes
    class_data = classes.get(class_key, {})
    class_students = st.session_state.class_students.get(class_key, [])

    if not class_students:
        st.info("まだ学生が登録されていません。学生が登録すると、ここに活動状況が表示されます。")
        code = class_data.get('code', 'N/A')
        st.markdown("**学生の登録方法:**")
        st.markdown(f"1. 学生にクラスコードを共有: `{code}`")
        st.markdown("2. 学生は新規登録時にこのコードを入力")
        st.markdown("3. 自動的にこのクラスに登録されます")
        return

    # 登録学生の名簿を表示
    st.markdown("#### 👥 登録学生一覧")
    for i, s in enumerate(class_students, 1):
        col1, col2, col3 = st.columns([1, 3, 3])
        with col1:
            st.caption(f"{i}")
        with col2:
            if s.get('id'):
                if st.button(f"**{s['name']}**", key=f"home_student_{i}_{s.get('id','')}",
                             help="クリックでカルテを表示"):
                    st.session_state['selected_student'] = {
                        'id': s['id'],
                        'user_id': s['id'],
                        'name': s['name'],
                        'email': s.get('email', ''),
                        'student_id': s.get('student_id', ''),
                    }
                    st.session_state['current_view'] = 'student_portfolio'
                    st.rerun()
            else:
                st.markdown(f"**{s['name']}**")
        with col3:
            st.caption(s.get('email', '') or s.get('student_id', ''))

    # 活動ログ（実データ）
    db_id = class_data.get('db_id')
    if db_id:
        try:
            from utils.database import get_course_submissions
            submissions = get_course_submissions(db_id, limit=5)
            if submissions:
                st.markdown("---")
                st.markdown("#### 📝 最近の提出")
                for j, s in enumerate(submissions):
                    u = s.get('users', {}) or {}
                    uid = u.get('id', '')
                    uname = u.get('name', '?')
                    module = s.get('module_type', '')
                    date = s.get('created_at', '')[:10]
                    col1, col2 = st.columns([2, 3])
                    with col1:
                        if uid:
                            if st.button(f"📋 {uname}", key=f"sub_student_{j}_{uid}",
                                         help="クリックでカルテを表示"):
                                st.session_state['selected_student'] = {
                                    'id': uid, 'user_id': uid,
                                    'name': uname, 'email': u.get('email', ''),
                                }
                                st.session_state['current_view'] = 'student_portfolio'
                                st.rerun()
                        else:
                            st.markdown(f"**{uname}**")
                    with col2:
                        st.caption(f"{module} ({date})")
            else:
                st.caption("まだ提出物はありません")
        except Exception:
            st.caption("まだ提出物はありません")
