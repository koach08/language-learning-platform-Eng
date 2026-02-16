import streamlit as st
from utils.auth import get_current_user, require_auth
from datetime import datetime


@require_auth
def show():
    user = get_current_user()
    st.markdown("## 📊 クラスダッシュボード")

    if st.button("← 教員ホームに戻る"):
        st.session_state['current_view'] = 'teacher_home'
        st.rerun()

    st.markdown("---")

    # クラス選択
    classes = st.session_state.get('teacher_classes', {})
    if not classes:
        st.warning("まだクラスが作成されていません")
        return

    selected_class = st.session_state.get('selected_class', list(classes.keys())[0])
    if selected_class not in classes:
        selected_class = list(classes.keys())[0]

    current_class = classes[selected_class]
    course_id = current_class.get('db_id') or current_class.get('course_id')

    # DBから学生データを取得（バッチクエリ版）
    class_students = _load_class_students_batch(course_id)
    student_count = len(class_students)

    st.info(f"📚 **{current_class['name']}**")
    st.caption(f"クラスコード: `{current_class.get('code', 'N/A')}` | 登録学生: {student_count}名")
    st.markdown("---")

    if not class_students:
        st.info("まだ学生が登録されていません。学生がクラスコードで登録するか、教員画面から追加してください。")
        return

    # サマリーメトリクス
    show_summary_metrics(class_students)

    # スコア分布
    show_score_distribution(class_students)

    # 課題状況（DB連携）
    show_assignment_status(course_id)

    # 要注意学生
    show_at_risk_students(class_students)

    # 学生一覧
    show_student_list(class_students)


def _load_class_students_batch(course_id: str) -> list:
    """DBからコースの学生活動サマリーを取得（バッチクエリ版 — APIコール削減）"""
    if not course_id:
        return []

    try:
        from utils.database import get_supabase_client
        from datetime import timedelta

        supabase = get_supabase_client()

        # 1. コースの学生一覧を取得（1クエリ）
        enrollments = supabase.table('enrollments')\
            .select('student_id, users(id, name, email, student_id, last_login)')\
            .eq('course_id', course_id)\
            .execute()

        if not enrollments.data:
            return []

        # 学生IDリストを作成
        student_map = {}
        for enrollment in enrollments.data:
            u = enrollment.get('users')
            if not u:
                continue
            sid = u['id']
            student_map[sid] = {
                'user_id': sid,
                'name': u.get('name', '不明'),
                'student_id': u.get('student_id', ''),
                'email': u.get('email', ''),
                'last_login': u.get('last_login'),
                'avg_score': 0,
                'practice_count': 0,
                'submissions': 0,
                'total_assignments': 0,
                'days_since_active': 99,
            }

        student_ids = list(student_map.keys())
        if not student_ids:
            return []

        # 2. コースの課題を一括取得（1クエリ）
        assignments = supabase.table('assignments')\
            .select('id')\
            .eq('course_id', course_id)\
            .execute()
        total_assignments = len(assignments.data) if assignments.data else 0
        assignment_ids = [a['id'] for a in (assignments.data or [])]

        # 3. 全学生の提出を一括取得（1クエリ）
        all_submissions = []
        if assignment_ids:
            for aid in assignment_ids:
                subs = supabase.table('submissions')\
                    .select('student_id, total_score, score')\
                    .eq('assignment_id', aid)\
                    .in_('student_id', student_ids)\
                    .execute()
                all_submissions.extend(subs.data or [])

        # 提出データを学生ごとに集計
        student_subs = {}
        for s in all_submissions:
            sid = s.get('student_id')
            if sid not in student_subs:
                student_subs[sid] = []
            student_subs[sid].append(s)

        # 4. 全学生の練習ログを一括取得（1クエリ）
        now = datetime.utcnow()
        week_ago = (now - timedelta(days=7)).isoformat()

        all_logs = supabase.table('practice_logs')\
            .select('student_id, score, practiced_at')\
            .eq('course_id', course_id)\
            .gte('practiced_at', week_ago)\
            .in_('student_id', student_ids)\
            .execute()

        # 練習ログを学生ごとに集計
        student_logs = {}
        for log in (all_logs.data or []):
            sid = log.get('student_id')
            if sid not in student_logs:
                student_logs[sid] = []
            student_logs[sid].append(log)

        # 5. 各学生のサマリーを構築
        for sid, info in student_map.items():
            # 提出集計
            subs = student_subs.get(sid, [])
            info['submissions'] = len(subs)
            info['total_assignments'] = total_assignments

            scores = []
            for s in subs:
                sc = s.get('total_score') or s.get('score') or 0
                if sc > 0:
                    scores.append(sc)
            info['avg_score'] = sum(scores) / len(scores) if scores else 0

            # 練習ログ集計
            logs = student_logs.get(sid, [])
            info['practice_count'] = len(logs)

            # 最終アクティブ日計算
            last_login = info.get('last_login')
            if last_login:
                try:
                    if isinstance(last_login, str):
                        # ISO形式をパース
                        lt = last_login.replace('Z', '+00:00')
                        from datetime import timezone
                        last_dt = datetime.fromisoformat(lt).replace(tzinfo=None)
                    else:
                        last_dt = last_login
                    info['days_since_active'] = (now - last_dt).days
                except Exception:
                    info['days_since_active'] = 99
            else:
                info['days_since_active'] = 99

        return list(student_map.values())

    except Exception as e:
        st.error(f"学生データの取得に失敗しました: {e}")
        return []


def show_summary_metrics(students):
    """サマリーメトリクス"""
    st.markdown("### 📈 クラスサマリー")

    col1, col2, col3, col4 = st.columns(4)
    with col1:
        if students:
            scored = [s for s in students if s.get('avg_score', 0) > 0]
            if scored:
                avg = sum(s['avg_score'] for s in scored) / len(scored)
                st.metric("クラス平均", f"{avg:.1f}点")
            else:
                st.metric("クラス平均", "-")
        else:
            st.metric("クラス平均", "-")

    with col2:
        if students:
            active = len([s for s in students if s.get('days_since_active', 99) <= 7])
            rate = (active / len(students) * 100) if students else 0
            st.metric("今週の練習率", f"{rate:.0f}%")
        else:
            st.metric("今週の練習率", "-")

    with col3:
        if students:
            total_a = students[0].get('total_assignments', 0) if students else 0
            if total_a > 0:
                with_subs = [s for s in students if s.get('submissions', 0) > 0]
                if with_subs:
                    submit_rate = sum(
                        min(s['submissions'] / total_a * 100, 100)
                        for s in with_subs
                    ) / len(students)
                    st.metric("課題提出率", f"{submit_rate:.0f}%")
                else:
                    st.metric("課題提出率", "0%")
            else:
                st.metric("課題提出率", "-")
        else:
            st.metric("課題提出率", "-")

    with col4:
        if students:
            at_risk = len([s for s in students
                          if s.get('days_since_active', 0) > 7
                          or (0 < s.get('avg_score', 100) < 50)])
            st.metric("要注意学生", f"{at_risk}名")
        else:
            st.metric("要注意学生", "0名")


def show_score_distribution(students):
    """スコア分布"""
    st.markdown("---")
    st.markdown("### 📊 スコア分布")

    if not students:
        st.info("学生データがありません")
        return

    scored = [s for s in students if s.get('avg_score', 0) > 0]
    if not scored:
        st.info("まだスコアデータがありません")
        return

    ranges = {"90-100": 0, "80-89": 0, "70-79": 0, "60-69": 0, "50-59": 0, "~49": 0}
    for s in scored:
        score = s.get('avg_score', 0)
        if score >= 90:
            ranges["90-100"] += 1
        elif score >= 80:
            ranges["80-89"] += 1
        elif score >= 70:
            ranges["70-79"] += 1
        elif score >= 60:
            ranges["60-69"] += 1
        elif score >= 50:
            ranges["50-59"] += 1
        else:
            ranges["~49"] += 1

    for range_name, count in ranges.items():
        col1, col2, col3 = st.columns([1, 3, 1])
        with col1:
            st.markdown(f"**{range_name}**")
        with col2:
            st.progress(count / max(len(scored), 1))
        with col3:
            st.markdown(f"{count}名")


def show_assignment_status(course_id: str):
    """課題状況（DB連携）"""
    st.markdown("---")
    st.markdown("### 📝 課題状況")

    if not course_id:
        st.info("コースが選択されていません")
        return

    try:
        from utils.database import get_course_assignments, get_assignment_submissions, get_course_students

        assignments = get_course_assignments(course_id)
        if not assignments:
            st.info("まだ課題が作成されていません")
            return

        students = get_course_students(course_id)
        total_students = len(students) if students else 0

        for a in assignments:
            subs = get_assignment_submissions(a['id'])
            submitted = len(subs) if subs else 0
            scores = [
                (s.get('total_score') or s.get('score') or 0)
                for s in (subs or [])
                if (s.get('total_score') or s.get('score'))
            ]
            avg = sum(scores) / len(scores) if scores else 0

            col1, col2, col3, col4 = st.columns([3, 1, 1, 1])
            with col1:
                st.markdown(f"**{a.get('title', '課題')}**")
                due = a.get('due_date', '')
                if due:
                    st.caption(f"締切: {due[:10]}")
            with col2:
                st.markdown(f"{submitted}/{total_students}")
            with col3:
                st.markdown(f"平均 {avg:.1f}点" if avg > 0 else "-")
            with col4:
                if st.button("詳細", key=f"assign_{a['id']}"):
                    st.session_state['current_view'] = 'assignments'
                    st.rerun()

    except Exception as e:
        st.error(f"課題データの取得に失敗しました: {e}")


def show_at_risk_students(students):
    """要注意学生"""
    st.markdown("---")
    st.markdown("### ⚠️ 要注意学生")

    if not students:
        st.info("学生データがありません")
        return

    at_risk = [s for s in students
               if s.get('days_since_active', 0) > 7
               or (0 < s.get('avg_score', 100) < 50)]

    if not at_risk:
        st.success("✅ 要注意学生はいません")
        return

    at_risk.sort(key=lambda x: (x.get('days_since_active', 0), -x.get('avg_score', 0)), reverse=True)

    for s in at_risk[:5]:
        issues = []
        if s.get('days_since_active', 0) > 7:
            issues.append(f"🔴 {s.get('days_since_active', 0)}日間活動なし")
        if 0 < s.get('avg_score', 100) < 50:
            issues.append(f"🔴 平均スコア {s.get('avg_score', 0):.1f}点")

        col1, col2, col3 = st.columns([2, 2, 1])
        with col1:
            st.markdown(f"**{s['name']}**")
            st.caption(s.get('student_id', ''))
        with col2:
            st.markdown(", ".join(issues) if issues else "")
        with col3:
            if st.button("詳細", key=f"risk_{s.get('user_id', s['name'])}"):
                st.session_state.selected_student = s
                st.session_state['current_view'] = 'student_portfolio'
                st.rerun()


def show_student_list(students):
    """学生一覧"""
    st.markdown("---")
    st.markdown("### 👥 学生一覧")

    if not students:
        st.info("学生データがありません")
        return

    col1, col2, col3 = st.columns(3)
    with col1:
        sort_by = st.selectbox("ソート", ["学籍番号順", "スコア順", "活動順"], key="dash_sort")
    with col2:
        filter_by = st.selectbox("フィルタ", ["全員", "要注意のみ", "高得点者"], key="dash_filter")
    with col3:
        search_text = st.text_input("🔍 検索", placeholder="名前または学籍番号", key="dash_search")

    filtered = students.copy()
    if filter_by == "要注意のみ":
        filtered = [s for s in filtered
                    if s.get('days_since_active', 0) > 7
                    or (0 < s.get('avg_score', 100) < 50)]
    elif filter_by == "高得点者":
        filtered = [s for s in filtered if s.get('avg_score', 0) >= 80]

    if search_text:
        search_lower = search_text.lower()
        filtered = [s for s in filtered
                    if search_lower in s.get('name', '').lower()
                    or search_text in s.get('student_id', '')]

    if sort_by == "スコア順":
        filtered.sort(key=lambda x: x.get('avg_score', 0), reverse=True)
    elif sort_by == "活動順":
        filtered.sort(key=lambda x: x.get('days_since_active', 99))

    st.caption(f"{len(filtered)}名表示中")

    for s in filtered[:20]:
        col1, col2, col3, col4, col5 = st.columns([2, 1, 1, 1, 1])
        with col1:
            if s.get('days_since_active', 0) > 7 or (0 < s.get('avg_score', 100) < 50):
                st.markdown(f"⚠️ **{s['name']}**")
            else:
                st.markdown(f"**{s['name']}**")
            st.caption(s.get('student_id', ''))
        with col2:
            score = s.get('avg_score', 0)
            color = "🟢" if score >= 70 else "🟡" if score >= 50 else "🔴"
            st.markdown(f"{color} {score:.1f}" if score > 0 else "-")
        with col3:
            st.markdown(f"{s.get('practice_count', 0)}回")
        with col4:
            days = s.get('days_since_active', 99)
            if days == 0:
                st.markdown("今日")
            elif days <= 3:
                st.markdown(f"{days}日前")
            elif days < 99:
                st.markdown(f"🔴 {days}日前")
            else:
                st.markdown("未ログイン")
        with col5:
            if st.button("👤", key=f"dash_detail_{s.get('user_id', s['name'])}"):
                st.session_state.selected_student = s
                st.session_state['current_view'] = 'student_portfolio'
                st.rerun()

    if len(filtered) > 20:
        st.caption(f"... 他 {len(filtered) - 20}名")
        if st.button("全学生を見る"):
            st.session_state['current_view'] = 'student_management'
            st.rerun()
