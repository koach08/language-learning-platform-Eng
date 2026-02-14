import streamlit as st
from utils.auth import get_current_user, require_auth
from datetime import datetime, timedelta


@require_auth
def show():
    """学生ポートフォリオ（電子カルテ）— 実データ版"""
    user = get_current_user()
    if user['role'] == 'teacher':
        if 'selected_student' not in st.session_state or not st.session_state.selected_student:
            st.warning("学生を選択してください")
            if st.button("← 学生管理に戻る"):
                st.session_state['current_view'] = 'student_management'
                st.rerun()
            return
        show_portfolio_teacher_view(st.session_state.selected_student)
    else:
        show_portfolio_student_view(user)


def show_portfolio_teacher_view(student):
    """教員用ポートフォリオビュー"""
    col1, col2 = st.columns([1, 4])
    with col1:
        if st.button("← 戻る"):
            st.session_state['current_view'] = 'teacher_dashboard'
            st.rerun()
    with col2:
        st.markdown(f"## 📋 学生ポートフォリオ: {student['name']}")

    days_val = student.get('days_since_active', 99)
    days_text = f"{days_val}日前" if days_val < 99 else "未ログイン"
    st.caption(f"学籍番号: {student.get('student_id', 'N/A')} | 最終活動: {days_text}")
    st.markdown("---")

    tab1, tab2, tab3, tab4, tab5 = st.tabs([
        "📊 サマリー", "📝 学習履歴", "💬 提出物・フィードバック",
        "📈 成長記録", "📓 教員メモ"
    ])
    sid = student.get('user_id', student.get('id', ''))
    with tab1:
        show_portfolio_summary(student, sid)
    with tab2:
        show_learning_history(sid)
    with tab3:
        show_submissions_and_feedback(sid)
    with tab4:
        show_growth_record(sid)
    with tab5:
        show_teacher_notes(student)


MODULE_LABELS = {
    'speaking_pronunciation': '🎤 発音練習',
    'speaking_chat': '💬 会話練習',
    'writing_practice': '✍️ ライティング',
    'listening_practice': '👂 リスニング',
    'reading_practice': '📖 リーディング',
    'vocabulary_review': '📚 語彙学習',
    'exam_practice': '📝 検定練習',
}


def show_portfolio_summary(student, student_id):
    """サマリータブ"""
    st.markdown("### 📊 学習サマリー")
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        avg = student.get('avg_score', 0)
        st.metric("平均スコア", f"{avg:.1f}点" if avg > 0 else "-")
    with col2:
        st.metric("練習回数（今週）", f"{student.get('practice_count', 0)}回")
    with col3:
        st.metric("今週の学習時間", f"{student.get('weekly_study_minutes', 0)}分")
    with col4:
        st.metric("課題提出", f"{student.get('submissions', 0)}/{student.get('total_assignments', 0)}")

    st.markdown("---")
    st.markdown("### 📊 モジュール別の練習状況（直近30日）")
    try:
        from utils.database import get_student_practice_stats
        stats = get_student_practice_stats(student_id, days=30)
        if stats:
            for module, data in stats.items():
                label = MODULE_LABELS.get(module, module)
                count = data.get('count', 0)
                minutes = round(data.get('total_seconds', 0) / 60)
                scores = data.get('scores', [])
                avg_s = round(sum(scores) / len(scores), 1) if scores else '-'
                col1, col2, col3, col4 = st.columns([3, 1, 1, 1])
                with col1:
                    st.markdown(f"**{label}**")
                with col2:
                    st.markdown(f"{count}回")
                with col3:
                    st.markdown(f"{minutes}分")
                with col4:
                    st.markdown(f"平均 {avg_s}" if avg_s != '-' else "-")
        else:
            st.info("まだ練習データがありません")
    except Exception as e:
        st.warning(f"練習統計の取得に失敗: {e}")

    st.markdown("---")
    st.markdown("### 🕐 最近の活動（直近7日）")
    _show_recent_activity(student_id, days=7)


def _show_recent_activity(student_id, days=7):
    """practice_logs + reading_logs + listening_logs から最近の活動を時系列表示"""
    activities = []
    try:
        from utils.database import get_student_practice_details
        for log in get_student_practice_details(student_id, days=days):
            details = log.get('activity_details') or {}
            dt = log.get('practiced_at', '')[:16].replace('T', ' ')
            module = MODULE_LABELS.get(log.get('module_type', ''), log.get('module_type', ''))
            parts = [details.get('activity', ''), details.get('title', '')]
            desc = ' — '.join(p for p in parts if p)
            activities.append({'datetime': dt, 'module': module, 'description': desc,
                               'score': log.get('score'), 'duration': log.get('duration_seconds', 0)})
    except Exception:
        pass

    try:
        from utils.database import get_student_reading_logs
        for log in get_student_reading_logs(student_id, days=days):
            dt = log.get('completed_at', '')[:16].replace('T', ' ')
            qs = log.get('quiz_score')
            score_text = f" (クイズ: {qs:.0f}%)" if qs else ""
            activities.append({'datetime': dt, 'module': '📖 リーディング',
                               'description': f"{log.get('source_title', '')}{score_text}",
                               'score': qs, 'duration': log.get('time_spent_seconds', 0)})
    except Exception:
        pass

    try:
        from utils.database import get_student_listening_logs
        for log in get_student_listening_logs(student_id, days=days):
            dt = log.get('completed_at', '')[:16].replace('T', ' ')
            activities.append({'datetime': dt, 'module': '👂 リスニング',
                               'description': log.get('video_title', ''),
                               'score': log.get('quiz_score'), 'duration': log.get('time_spent_seconds', 0)})
    except Exception:
        pass

    activities.sort(key=lambda x: x['datetime'], reverse=True)
    if not activities:
        st.info("この期間の活動データはありません")
        return
    for a in activities[:15]:
        col1, col2, col3 = st.columns([1.5, 3, 1])
        with col1:
            st.caption(a['datetime'])
        with col2:
            st.markdown(f"**{a['module']}**")
            if a['description']:
                st.caption(a['description'])
        with col3:
            if a['score'] is not None:
                st.markdown(f"{a['score']:.0f}点")
            elif a['duration']:
                st.markdown(f"{a['duration'] // 60}分")


def show_learning_history(student_id):
    """学習履歴タブ"""
    st.markdown("### 📝 学習履歴")
    col1, col2 = st.columns(2)
    with col1:
        module_filter = st.selectbox("モジュール",
            ["全て"] + list(MODULE_LABELS.keys()),
            format_func=lambda x: MODULE_LABELS.get(x, x))
    with col2:
        days_map = {"今週": 7, "今月": 30, "過去3ヶ月": 90, "全期間": 365}
        period = st.selectbox("期間", list(days_map.keys()))
        days = days_map[period]

    st.markdown("---")
    module_type = module_filter if module_filter != "全て" else None
    try:
        from utils.database import get_student_practice_details
        logs = get_student_practice_details(student_id, days=days, module_type=module_type)
        if not logs:
            st.info("この条件の学習データはありません")
            return
        st.caption(f"{len(logs)}件のログ")
        for log in logs[:30]:
            details = log.get('activity_details') or {}
            dt = log.get('practiced_at', '')[:16].replace('T', ' ')
            module = MODULE_LABELS.get(log.get('module_type', ''), log.get('module_type', ''))
            title = details.get('title', '')
            header = f"📌 {dt} — {module}"
            if title:
                header += f": {title}"
            with st.expander(header):
                col1, col2 = st.columns([2, 1])
                with col1:
                    if details.get('activity'):
                        st.markdown(f"**活動:** {details['activity']}")
                    if title:
                        st.markdown(f"**素材:** {title}")
                    duration = log.get('duration_seconds', 0)
                    if duration:
                        st.markdown(f"**所要時間:** {duration // 60}分{duration % 60}秒")
                    if details.get('recognized_text'):
                        with st.expander("📝 認識テキスト"):
                            st.text(details['recognized_text'])
                    if details.get('level'):
                        st.caption(f"レベル: {details['level']}")
                with col2:
                    score = log.get('score')
                    if score:
                        st.metric("スコア", f"{score:.1f}点")
                    for key, val in details.get('scores', {}).items():
                        if isinstance(val, (int, float)):
                            st.caption(f"{key}: {val}")
        if len(logs) > 30:
            st.caption(f"... 他 {len(logs) - 30}件")

        if st.button("📥 CSV出力"):
            import pandas as pd
            df = pd.DataFrame([{
                '日時': l.get('practiced_at', '')[:16],
                'モジュール': l.get('module_type', ''),
                'スコア': l.get('score', ''),
                '時間(秒)': l.get('duration_seconds', ''),
            } for l in logs])
            csv = df.to_csv(index=False).encode('utf-8-sig')
            st.download_button("📤 ダウンロード", csv,
                f"history_{student_id[:8]}_{datetime.now().strftime('%Y%m%d')}.csv", "text/csv")
    except Exception as e:
        st.error(f"学習履歴の取得に失敗: {e}")


def show_submissions_and_feedback(student_id):
    """提出物・フィードバックタブ"""
    st.markdown("### 💬 提出物・フィードバック")
    try:
        from utils.database import get_student_submissions
        submissions = get_student_submissions(student_id)
        if not submissions:
            st.info("まだ提出物がありません")
        else:
            st.caption(f"{len(submissions)}件の提出物")
            for sub in submissions:
                dt = (sub.get('submitted_at') or '')[:16].replace('T', ' ')
                score = sub.get('total_score') or sub.get('score', 0)
                content_type = sub.get('content_type', '')
                title = sub.get('title', f"提出物 ({content_type})")
                icon = "🟢" if score and score >= 70 else "🟡" if score and score >= 50 else "🔴" if score else "⬜"
                header = f"{icon} {dt} — {title} ({score:.1f}点)" if score else f"⬜ {dt} — {title}"
                with st.expander(header):
                    col1, col2 = st.columns([2, 1])
                    with col1:
                        if sub.get('text_content'):
                            with st.expander("📝 提出内容"):
                                st.text(sub['text_content'][:1000])
                        if sub.get('feedback'):
                            st.markdown("**AIフィードバック:**")
                            st.info(sub['feedback'])
                        if sub.get('teacher_comment'):
                            st.markdown("**👨‍🏫 教員コメント:**")
                            st.success(sub['teacher_comment'])
                    with col2:
                        if score:
                            st.metric("総合スコア", f"{score:.1f}点")
                        if sub.get('cefr_level'):
                            st.markdown(f"**CEFR:** {sub['cefr_level']}")
    except Exception as e:
        st.error(f"提出物の取得に失敗: {e}")

    st.markdown("---")
    st.markdown("### 💬 AI会話セッション")
    try:
        from utils.database import get_student_chat_sessions
        sessions = get_student_chat_sessions(student_id, limit=10)
        if sessions:
            for s in sessions:
                dt = (s.get('started_at') or '')[:16].replace('T', ' ')
                topic = s.get('topic', 'フリートーク')
                turns = s.get('message_count', 0)
                score = s.get('overall_score', 0)
                col1, col2, col3 = st.columns([2, 1, 1])
                with col1:
                    st.markdown(f"**{dt}** — {topic}")
                with col2:
                    st.caption(f"{turns}ターン")
                with col3:
                    if score:
                        st.caption(f"{score:.1f}点")
        else:
            st.info("まだ会話セッションがありません")
    except Exception as e:
        st.caption(f"会話データの取得に失敗: {e}")


def show_growth_record(student_id):
    """成長記録タブ"""
    st.markdown("### 📈 成長記録")
    st.markdown("#### 📊 スコア推移（直近90日）")
    try:
        from utils.database import get_student_practice_details
        logs = get_student_practice_details(student_id, days=90)
        scored = [l for l in (logs or []) if l.get('score')]
        if scored:
            import pandas as pd
            df = pd.DataFrame([{
                '日付': l.get('practiced_at', '')[:10],
                'モジュール': l.get('module_type', ''),
                'スコア': l.get('score', 0),
            } for l in scored])
            for module in df['モジュール'].unique():
                mod_df = df[df['モジュール'] == module].sort_values('日付')
                label = MODULE_LABELS.get(module, module)
                if len(mod_df) >= 2:
                    first_avg = mod_df.head(max(1, len(mod_df) // 3))['スコア'].mean()
                    last_avg = mod_df.tail(max(1, len(mod_df) // 3))['スコア'].mean()
                    change = last_avg - first_avg
                    col1, col2, col3 = st.columns([2, 3, 1])
                    with col1:
                        st.markdown(f"**{label}**")
                    with col2:
                        st.progress(min(100, int(last_avg)) / 100)
                    with col3:
                        arrow = "↑" if change > 0 else "↓" if change < 0 else "→"
                        st.markdown(f"{last_avg:.0f} ({arrow}{abs(change):.1f})")
                elif len(mod_df) == 1:
                    sc = mod_df.iloc[0]['スコア']
                    col1, col2, col3 = st.columns([2, 3, 1])
                    with col1:
                        st.markdown(f"**{label}**")
                    with col2:
                        st.progress(min(100, int(sc)) / 100)
                    with col3:
                        st.markdown(f"{sc:.0f}")
        else:
            st.info("スコアデータがまだありません")
    except Exception as e:
        st.warning(f"成長データの取得に失敗: {e}")

    st.markdown("---")
    st.markdown("#### 🏆 達成マイルストーン")
    try:
        from utils.database import get_student_practice_details
        all_logs = get_student_practice_details(student_id, days=365)
        if not all_logs:
            st.info("まだマイルストーンはありません")
            return
        milestones = []
        n = len(all_logs)
        first_log = min(all_logs, key=lambda x: x.get('practiced_at', ''))
        milestones.append(f"🎉 **{first_log.get('practiced_at', '')[:10]}** — 初めての練習完了")
        if n >= 10:
            milestones.append("🔟 練習10回達成")
        if n >= 50:
            milestones.append("🎯 練習50回達成")
        if n >= 100:
            milestones.append("💯 練習100回達成")
        high = [l for l in all_logs if (l.get('score') or 0) >= 90]
        if high:
            first90 = min(high, key=lambda x: x.get('practiced_at', ''))
            milestones.append(f"⭐ **{first90.get('practiced_at', '')[:10]}** — 初めて90点以上を達成")
        for m in milestones:
            st.markdown(m)
    except Exception:
        st.info("マイルストーンの判定に失敗しました")


def show_teacher_notes(student):
    """教員メモ"""
    st.markdown("### 📓 教員メモ")
    st.caption("この学生に関するメモや個別目標を記録できます（今後DB保存を実装予定）")
    sid = student.get('user_id', student.get('id', ''))
    memo_key = f"teacher_memo_{sid}"
    goal_key = f"teacher_goal_{sid}"
    new_goal = st.text_input("🎯 個別目標", value=st.session_state.get(goal_key, ""),
                              placeholder="例: TOEFL ITP 500点達成")
    new_memo = st.text_area("📝 メモ", value=st.session_state.get(memo_key, ""),
                             placeholder="この学生に関する観察メモ...", height=150)
    if st.button("💾 メモを保存", type="primary"):
        st.session_state[memo_key] = new_memo
        st.session_state[goal_key] = new_goal
        st.success("保存しました（※現在はセッション内のみ。DB永続化は今後実装）")


def show_portfolio_student_view(user):
    """学生用ポートフォリオビュー"""
    st.markdown("## 📋 マイポートフォリオ")
    st.caption(f"{user['name']} さんの学習記録")
    student_id = user['id']
    tab1, tab2, tab3 = st.tabs(["📊 サマリー", "📝 学習履歴", "📈 成長記録"])
    with tab1:
        st.markdown("### 📊 学習状況")
        try:
            from utils.database import get_student_practice_stats
            stats = get_student_practice_stats(student_id, days=30)
            total_count = sum(d.get('count', 0) for d in stats.values()) if stats else 0
            total_min = sum(d.get('total_seconds', 0) for d in stats.values()) / 60 if stats else 0
            all_sc = []
            for d in (stats or {}).values():
                all_sc.extend(d.get('scores', []))
            avg_sc = sum(all_sc) / len(all_sc) if all_sc else 0
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("練習回数（30日）", f"{total_count}回")
            with col2:
                st.metric("総学習時間", f"{total_min:.0f}分")
            with col3:
                st.metric("平均スコア", f"{avg_sc:.1f}点" if avg_sc > 0 else "-")
        except Exception:
            st.info("学習データの読み込みに失敗しました")
    with tab2:
        show_learning_history(student_id)
    with tab3:
        show_growth_record(student_id)
