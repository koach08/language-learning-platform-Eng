import streamlit as st
from utils.auth import get_current_user, require_auth
from utils.gamification import (
    get_gamification_data, update_streak, get_current_level,
    get_next_level, get_xp_progress, get_weekly_challenges,
    show_gamification_dashboard, BADGES
)
from datetime import datetime, timedelta


@require_auth
def show():
    user = get_current_user()
    if user['role'] != 'student':
        st.session_state['current_view'] = 'teacher_home'
        st.rerun()
        return

    # ストリーク更新
    update_streak()

    st.markdown(f"## 🎓 学習ダッシュボード")
    st.markdown(f"ようこそ、{user['name']} さん")

    # --- コース登録状態を確認（ただし表示はブロックしない） ---
    class_key = user.get('class_key')
    class_name = user.get('class_name')
    is_enrolled = True

    if not class_key and not st.session_state.get('student_registered_classes'):
        # DBからenrollments確認
        enrolled_courses = []
        try:
            from utils.database import get_student_enrollments
            enrollments = get_student_enrollments(user['id'])
            enrolled_courses = [e['courses'] for e in enrollments if e.get('courses')]
        except Exception:
            pass

        if enrolled_courses:
            # DB上でコースに登録済み
            st.session_state.student_registered_classes = [
                {'class_key': c['id'], 'name': c['name'],
                 'display_name': f"{c['name']}（{c.get('year', '')}{c.get('semester', '')}）"}
                for c in enrolled_courses
            ]
        else:
            is_enrolled = False

    # コース表示（登録済みの場合）
    if class_name:
        st.info(f"📚 **{class_name}**")
    elif st.session_state.get('student_registered_classes'):
        classes = st.session_state.student_registered_classes
        if len(classes) > 1:
            selected = st.selectbox(
                "クラスを選択",
                classes,
                format_func=lambda x: x.get('display_name', x.get('name', ''))
            )
            class_key = selected.get('class_key')
            st.info(f"📚 **{selected.get('display_name', '')}**")
        else:
            class_key = classes[0].get('class_key')
            st.info(f"📚 **{classes[0].get('display_name', '')}**")

    st.markdown("---")

    # --- ★ 学習モジュールを最上部に配置 ---
    enabled_modules = get_enabled_modules(class_key)
    show_learning_modules(enabled_modules)

    # --- 未登録の場合: クラスコード登録（折りたたみ） ---
    if not is_enrolled:
        st.info("💡 **クラスに登録すると、課題の受け取りや成績の記録ができます。** 登録前でも各モジュールは自由に使えます。")
        with st.expander("📥 クラスコードを入力して登録する"):
            with st.form("enroll_form"):
                code_input = st.text_input("クラスコード", placeholder="例: ENG1A2025")
                enroll_btn = st.form_submit_button("📥 登録する", type="primary")

                if enroll_btn and code_input.strip():
                    try:
                        from utils.database import get_course_by_class_code, enroll_student
                        course = get_course_by_class_code(code_input.strip())
                        if course:
                            enroll_student(user['id'], course['id'])
                            st.success(f"✅ 「{course['name']}」に登録しました！")
                            st.cache_data.clear()
                            import time
                            time.sleep(1)
                            st.rerun()
                        else:
                            st.error("❌ そのクラスコードは見つかりません。先生に確認してください。")
                    except Exception as e:
                        if 'duplicate' in str(e).lower():
                            st.warning("すでにこのクラスに登録済みです")
                        else:
                            st.error(f"登録エラー: {e}")

    # プロフィール概要
    show_profile_summary(user)

    # ゲーミフィケーション ステータスバー
    show_gamification_status_bar()

    # 学習状況
    show_learning_summary()

    # 授業外学習サマリー
    show_extracurricular_summary(user)

    # 今日のおすすめ
    show_recommendations(enabled_modules)

    # 週間チャレンジ
    show_weekly_challenges()

    # 課題
    show_assignments_summary()

    # 最近の学習
    show_recent_activity()

    # 詳細ステータス（展開式）
    with st.expander("🎮 学習ステータス詳細 / Full Status"):
        show_gamification_dashboard()


def show_profile_summary(user):
    """学生プロフィール概要をダッシュボード上部に表示"""
    profile = None
    try:
        from utils.database import get_student_profile
        profile = get_student_profile(user['id'])
    except Exception:
        pass

    if not profile:
        # プロフィール未登録
        col1, col2 = st.columns([3, 1])
        with col1:
            st.info("👤 プロフィールを登録すると、ここに表示されます")
        with col2:
            if st.button("✏️ 登録する", key="profile_register_btn", use_container_width=True):
                st.session_state['current_view'] = 'student_profile'
                st.rerun()
        return

    # --- プロフィール登録済み: コンパクト表示 ---
    # 1行目: 基本情報
    parts = []
    if profile.get('student_number'):
        parts.append(f"🆔 {profile['student_number']}")
    if profile.get('faculty'):
        parts.append(f"🏫 {profile['faculty']}")
    if profile.get('hometown'):
        parts.append(f"📍 {profile['hometown']}")

    # 2行目: スコア
    score_parts = []
    scores = profile.get('test_scores') or {}
    if scores.get('toefl_itp'):
        score_parts.append(f"TOEFL-ITP: {scores['toefl_itp']}")
    if scores.get('toeic'):
        score_parts.append(f"TOEIC: {scores['toeic']}")
    if scores.get('ielts'):
        score_parts.append(f"IELTS: {scores['ielts']}")
    if scores.get('eiken'):
        score_parts.append(f"英検: {scores['eiken']}")
    if scores.get('toefl_ibt'):
        score_parts.append(f"TOEFL iBT: {scores['toefl_ibt']}")

    # 表示
    info_line = " ｜ ".join(parts) if parts else ""
    score_line = " ｜ ".join(score_parts) if score_parts else ""

    col1, col2 = st.columns([5, 1])
    with col1:
        if info_line:
            st.markdown(f"**{info_line}**")
        if score_line:
            st.caption(f"📊 {score_line}")
        if profile.get('english_goals'):
            st.caption(f"🎯 {profile['english_goals']}")
    with col2:
        if st.button("✏️ 編集", key="profile_edit_btn", use_container_width=True):
            st.session_state['current_view'] = 'student_profile'
            st.rerun()

    st.markdown("---")


def show_gamification_status_bar():
    """ゲーミフィケーション ステータスバー（コンパクト版）"""
    data = get_gamification_data()
    total_xp = data['total_xp']
    current_level = get_current_level(total_xp)
    next_level = get_next_level(total_xp)
    progress = get_xp_progress(total_xp)
    streak = data['current_streak']
    badge_count = len(data['badges_earned'])

    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.markdown(f"**{current_level['icon']} Lv.{current_level['level']}** {current_level['name']}")
    with col2:
        st.markdown(f"**⭐ {total_xp:,} XP**")
    with col3:
        if streak > 0:
            st.markdown(f"**🔥 {streak}日連続**")
        else:
            st.markdown("🔥 今日から始めよう！")
    with col4:
        st.markdown(f"**🏅 {badge_count}個**")

    if next_level:
        st.progress(progress)
        st.caption(f"次のレベル ({next_level['icon']} {next_level['name']}) まであと {next_level['xp_required'] - total_xp} XP")
    else:
        st.progress(1.0)
        st.caption("🌟 最高レベル達成！")

    st.markdown("---")


def show_weekly_challenges():
    """週間チャレンジ表示"""
    st.markdown("### 🎯 今週のチャレンジ")

    challenges = get_weekly_challenges()
    if not challenges:
        st.info("チャレンジを読み込み中...")
        return

    cols = st.columns(len(challenges))
    for i, challenge in enumerate(challenges):
        with cols[i]:
            if challenge['completed']:
                st.success(f"✅ {challenge['name']}")
                st.caption(f"+{challenge['xp_reward']} XP 獲得！")
            else:
                st.info(f"🎯 {challenge['name']}")
                progress_val = min(challenge['current'] / challenge['target'], 1.0) if challenge['target'] > 0 else 0
                st.progress(progress_val)
                st.caption(f"{challenge['current']}/{challenge['target']}")

    st.markdown("---")


def get_enabled_modules(class_key):
    # 表示順序を固定（この順序でモジュールカードが並ぶ）
    MODULE_ORDER = ["speaking", "writing", "reading", "listening", "vocabulary", "test_prep"]

    teacher_classes = st.session_state.get('teacher_classes', {})
    if class_key and class_key in teacher_classes:
        class_data = teacher_classes[class_key]
        modules = class_data.get('modules', {})
        enabled = {k for k, v in modules.items() if v}
        return [m for m in MODULE_ORDER if m in enabled]
    return MODULE_ORDER


def show_learning_summary():
    st.markdown("### 📊 学習状況")

    try:
        from utils.analytics import get_analytics_data, estimate_cefr
        from utils.gamification import get_gamification_data
        adata = get_analytics_data()
        gdata = get_gamification_data()

        total_time = sum(adata['module_time'].values())
        hours = total_time // 60
        mins = total_time % 60

        all_scores = []
        for key in ['speaking_scores', 'writing_scores', 'reading_scores', 'vocabulary_scores', 'listening_scores']:
            all_scores.extend([s['score'] for s in adata.get(key, [])])

        avg_score = sum(all_scores) / len(all_scores) if all_scores else 0
        streak = gdata.get('current_streak', 0)
        cefr = estimate_cefr(avg_score) if all_scores else '-'

        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("総学習時間", f"{hours}h {mins}m")
        with col2:
            st.metric("平均スコア", f"{avg_score:.1f}" if all_scores else "-")
        with col3:
            st.metric("連続学習", f"{streak}日")
        with col4:
            st.metric("推定CEFR", cefr)
    except Exception:
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("今週の練習", "0回")
        with col2:
            st.metric("平均スコア", "-")
        with col3:
            st.metric("連続練習", "0日")
        with col4:
            st.metric("推定CEFR", "-")


def show_extracurricular_summary(user):
    """授業外学習サマリー"""
    st.markdown("---")
    st.markdown("### 📝 授業外学習")
    st.caption("映画、読書、アプリなど授業外で行った外国語学習を記録して成績に反映！")

    user_email = user.get('email', user.get('name', 'default'))
    logs = st.session_state.get('learning_logs', {}).get(user_email, [])

    # 今週
    today = datetime.now().date()
    start_of_week = today - timedelta(days=today.weekday())
    week_logs = [l for l in logs if datetime.strptime(l['date'], "%Y-%m-%d").date() >= start_of_week]

    total_minutes = sum(l['duration_minutes'] for l in week_logs)
    total_points = sum(l['points'] for l in week_logs)
    all_time_points = sum(l['points'] for l in logs)

    col1, col2, col3, col4 = st.columns(4)
    with col1:
        hours = total_minutes // 60
        mins = total_minutes % 60
        st.metric("今週の学習", f"{hours}h {mins}m")
    with col2:
        st.metric("今週のポイント", f"+{total_points}pt")
    with col3:
        st.metric("累計ポイント", f"{all_time_points}pt")
    with col4:
        if st.button("📝 記録する", use_container_width=True):
            st.session_state['current_view'] = 'learning_log'
            st.rerun()

    # 最近の記録
    if logs:
        with st.expander("最近の記録を見る"):
            for log in logs[:3]:
                col1, col2, col3 = st.columns([1, 3, 1])
                with col1:
                    st.caption(log['date'])
                with col2:
                    st.markdown(f"**{log['title']}**")
                    st.caption(f"{log['category_name']} | {log['duration_minutes']}分")
                with col3:
                    st.markdown(f"+{log['points']}pt")

            if st.button("すべての記録を見る"):
                st.session_state['current_view'] = 'learning_log'
                st.rerun()


def show_recommendations(enabled_modules):
    st.markdown("### 🎯 今日のおすすめ練習")

    all_recommendations = [
        {"module": "speaking", "task": "音読練習 10分", "icon": "🗣️", "reason": "発音スコア向上"},
        {"module": "vocabulary", "task": "単語フラッシュカード", "icon": "📚", "reason": "語彙力強化"},
        {"module": "listening", "task": "YouTube学習 15分", "icon": "🎧", "reason": "リスニング力向上"},
        {"module": "writing", "task": "短文ライティング", "icon": "✍️", "reason": "表現力向上"},
        {"module": "reading", "task": "記事読解", "icon": "📖", "reason": "読解スピード向上"},
    ]

    recommendations = [r for r in all_recommendations if r['module'] in enabled_modules]
    for rec in recommendations[:3]:
        col1, col2 = st.columns([4, 1])
        with col1:
            st.markdown(f"{rec['icon']} **{rec['task']}**")
            st.caption(rec['reason'])
        with col2:
            if st.button("開始", key=f"start_{rec['module']}"):
                st.session_state['current_view'] = rec['module']
                st.rerun()


def show_learning_modules(enabled_modules):
    st.markdown("### 📚 学習モジュール")

    all_modules = [
        {"key": "speaking",   "icon": "🗣️", "name": "Speaking",   "desc": "発音・会話・音読練習",  "color": "#4F8EF7", "bg": "#EEF4FF"},
        {"key": "writing",    "icon": "✍️",  "name": "Writing",    "desc": "ライティング・作文",    "color": "#F76B4F", "bg": "#FFF2EF"},
        {"key": "reading",    "icon": "📖",  "name": "Reading",    "desc": "読解・速読トレーニング", "color": "#3DBD7D", "bg": "#EDFBF3"},
        {"key": "listening",  "icon": "🎧",  "name": "Listening",  "desc": "リスニング強化",         "color": "#F7B84F", "bg": "#FFFAEF"},
        {"key": "vocabulary", "icon": "📚",  "name": "Vocabulary", "desc": "語彙・単語帳",           "color": "#A04FF7", "bg": "#F5EFFF"},
        {"key": "test_prep",  "icon": "📝",  "name": "検定対策",    "desc": "TOEFL / TOEIC / 英検",  "color": "#F74F8E", "bg": "#FFEFF5"},
    ]

    modules = [m for m in all_modules if m['key'] in enabled_modules]

    if not modules:
        st.info("このクラスで有効なモジュールはまだ設定されていません")
        return

    # カードCSSを一度だけ注入
    st.markdown("""
    <style>
    .module-card {
        background: var(--card-bg);
        border: 1.5px solid transparent;
        border-radius: 16px;
        padding: 24px 16px 20px;
        text-align: center;
        cursor: pointer;
        transition: transform .18s ease, box-shadow .18s ease, border-color .18s ease;
        margin-bottom: 12px;
        user-select: none;
        position: relative;
        overflow: hidden;
    }
    .module-card::before {
        content: "";
        position: absolute;
        top: 0; left: 0; right: 0;
        height: 4px;
        background: var(--card-accent);
        border-radius: 16px 16px 0 0;
    }
    .module-card:hover {
        transform: translateY(-4px);
        box-shadow: 0 8px 24px rgba(0,0,0,0.10);
        border-color: var(--card-accent);
    }
    .module-card:active {
        transform: translateY(-1px);
    }
    .module-card .card-icon {
        font-size: 2.2rem;
        display: block;
        margin-bottom: 8px;
        line-height: 1;
    }
    .module-card .card-name {
        font-size: 1.05rem;
        font-weight: 700;
        color: #1a1a2e;
        margin: 0 0 4px;
    }
    .module-card .card-desc {
        font-size: 0.78rem;
        color: #6b7280;
        margin: 0;
    }
    </style>
    """, unsafe_allow_html=True)

    num_cols = min(len(modules), 3)
    cols = st.columns(num_cols)
    for i, mod in enumerate(modules):
        with cols[i % num_cols]:
            # クリック可能なカードをボタンで実装（Streamlit制約のため）
            st.markdown(f"""
            <div class="module-card"
                 style="--card-bg:{mod['bg']}; --card-accent:{mod['color']};">
                <span class="card-icon">{mod['icon']}</span>
                <p class="card-name">{mod['name']}</p>
                <p class="card-desc">{mod['desc']}</p>
            </div>
            """, unsafe_allow_html=True)
            # カード直下に透明ボタン（カードクリックの代替）
            if st.button(
                f"{mod['icon']} {mod['name']}に進む",
                key=f"mod_{mod['key']}",
                use_container_width=True,
                type="primary" if i == 0 else "secondary",
            ):
                st.session_state['current_view'] = mod['key']
                st.rerun()

    disabled_modules = [m for m in all_modules if m['key'] not in enabled_modules and m['key'] != 'test_prep']
    if disabled_modules:
        st.caption("※ このクラスでは一部のモジュールが無効になっています")

    st.markdown("---")


def _get_assignment_target_view(assignment_type: str) -> str:
    """課題タイプから遷移先ビューを判定"""
    if assignment_type and assignment_type.startswith('speaking'):
        return 'speaking'
    elif assignment_type and assignment_type.startswith('writing'):
        return 'writing'
    elif assignment_type and assignment_type.startswith('listening'):
        return 'listening'
    elif assignment_type and assignment_type.startswith('reading'):
        return 'reading'
    else:
        return 'writing'  # デフォルト


def _get_assignment_type_label(assignment_type: str) -> str:
    """課題タイプの日本語ラベル"""
    labels = {
        'speaking_read_aloud': '🗣️ 音読',
        'speaking_speech': '🗣️ スピーチ',
        'speaking_conversation': '🗣️ 会話',
        'writing_essay': '✍️ エッセイ',
        'writing_summary': '✍️ 要約',
        'writing_response': '✍️ レスポンス',
        'listening_comprehension': '🎧 リスニング',
        'reading_comprehension': '📖 リーディング',
    }
    return labels.get(assignment_type, f'📝 {assignment_type or "課題"}')


def show_assignments_summary():
    st.markdown("---")
    st.markdown("### 📝 課題")

    user = get_current_user()
    student_id = user.get('id')

    if not student_id:
        st.info("コースに登録されていないため課題を表示できません")
        return

    # 全コースのcourse_idを取得
    course_ids = []
    # 1. セッションの登録クラスから
    registered = st.session_state.get('student_registered_classes', [])
    if registered:
        course_ids = [c.get('class_key') for c in registered if c.get('class_key')]

    # 2. ユーザーのclass_keyから（フォールバック）
    if not course_ids:
        ck = user.get('class_key')
        if ck:
            course_ids = [ck]

    # 3. DBからenrollmentsを直接確認（フォールバック）
    if not course_ids:
        try:
            from utils.database import get_student_enrollments
            enrollments = get_student_enrollments(student_id)
            for e in enrollments:
                course = e.get('courses')
                if course and course.get('id'):
                    course_ids.append(course['id'])
        except Exception:
            pass

    if not course_ids:
        st.info("クラスに登録すると、課題がここに表示されます。")
        return

    # 全コースの課題を統合取得
    all_assignments = []
    try:
        from utils.database import get_student_assignment_status
        for cid in course_ids:
            try:
                assignments = get_student_assignment_status(student_id, cid)
                for a in assignments:
                    a['_course_id'] = cid  # 遷移時に使う
                all_assignments.extend(assignments)
            except Exception:
                pass
    except Exception as e:
        st.warning(f"課題データの取得に失敗しました: {e}")
        return

    if not all_assignments:
        st.info("まだ課題はありません。教員が課題を作成するとここに表示されます。")
        return

    # 未提出を先に、締切日順
    pending = [a for a in all_assignments if a.get('status') == '未提出']
    submitted = [a for a in all_assignments if a.get('status') == '提出済']
    graded = [a for a in all_assignments if a.get('status') == '採点済']

    # 未提出の課題
    if pending:
        st.markdown("#### ⏳ 未提出")
        for idx, a in enumerate(pending):
            due = a.get('due_date', '')
            due_display = due[:10] if due else ''
            a_type = a.get('type', '')  # get_student_assignment_status returns 'type'
            type_label = _get_assignment_type_label(a_type)

            col1, col2, col3 = st.columns([3, 1, 1])
            with col1:
                st.markdown(f"**{a['title']}**")
                st.caption(f"{type_label} {f'| 締切: {due_display}' if due_display else ''}")
            with col2:
                st.warning("⏳ 未提出")
            with col3:
                target_view = _get_assignment_target_view(a_type)
                if st.button("📤 提出する", key=f"submit_pending_{idx}_{a.get('assignment_id', '')}",
                             type="primary", use_container_width=True):
                    # 課題情報をセッションに保存して遷移
                    st.session_state['submit_assignment_id'] = a.get('assignment_id')
                    st.session_state['submit_assignment_title'] = a.get('title')
                    st.session_state['submit_assignment_type'] = a_type
                    st.session_state['submit_course_id'] = a.get('_course_id')
                    st.session_state['current_view'] = target_view
                    st.rerun()

    # 提出済の課題
    if submitted:
        st.markdown("#### 📤 提出済")
        for idx, a in enumerate(submitted):
            due = a.get('due_date', '')
            due_display = due[:10] if due else ''
            type_label = _get_assignment_type_label(a.get('type', ''))

            col1, col2 = st.columns([3, 1])
            with col1:
                st.markdown(f"**{a['title']}**")
                st.caption(f"{type_label} {f'| 締切: {due_display}' if due_display else ''}")
            with col2:
                st.info("📤 提出済")

    # 採点済の課題
    if graded:
        st.markdown("#### ✅ 採点済")
        for idx, a in enumerate(graded):
            due = a.get('due_date', '')
            due_display = due[:10] if due else ''
            score = a.get('score', 0)
            type_label = _get_assignment_type_label(a.get('type', ''))

            col1, col2 = st.columns([3, 1])
            with col1:
                st.markdown(f"**{a['title']}**")
                st.caption(f"{type_label} {f'| 締切: {due_display}' if due_display else ''}")
            with col2:
                st.success(f"✅ {score}点")


def show_recent_activity():
    st.markdown("---")
    st.markdown("### 📈 最近の学習")

    user = get_current_user()
    student_id = user.get('id')

    if not student_id:
        st.info("まだ学習履歴はありません")
        return

    try:
        from utils.database import get_student_recent_activity
        activities = get_student_recent_activity(student_id, limit=5)
    except Exception as e:
        st.warning(f"学習履歴の取得に失敗しました: {e}")
        activities = []

    if not activities:
        st.info("まだ学習履歴はありません。学習を始めると実績がここに表示されます。")
    else:
        for h in activities:
            timestamp = h.get('timestamp', '')
            try:
                dt = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
                date_display = dt.strftime('%m/%d')
            except (ValueError, TypeError):
                date_display = timestamp[:10] if timestamp else ''

            col1, col2, col3 = st.columns([1, 3, 1])
            with col1:
                st.caption(date_display)
            with col2:
                module = h.get('module', '')
                desc = h.get('description', '')
                st.markdown(f"**{module}** - {desc}" if desc else f"**{module}**")
            with col3:
                score = h.get('score')
                if score:
                    st.markdown(f"**{score}点**")
                else:
                    st.markdown("-")

    st.markdown("---")

    col1, col2 = st.columns(2)
    with col1:
        if st.button("📋 マイポートフォリオ"):
            st.session_state['current_view'] = 'student_portfolio'
            st.rerun()
    with col2:
        if st.button("📝 授業外学習ログ"):
            st.session_state['current_view'] = 'learning_log'
            st.rerun()
