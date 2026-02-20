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
            st.session_state['current_view'] = 'student_management'
            st.rerun()
    with col2:
        st.markdown(f"## 📋 学生ポートフォリオ: {student['name']}")

    days_val = student.get('days_since_active', 99)
    days_text = f"{days_val}日前" if days_val < 99 else "未ログイン"
    st.caption(f"学籍番号: {student.get('student_id', 'N/A')} | 最終活動: {days_text}")
    st.markdown("---")

    tab0, tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs([
        "👤 プロフィール", "📊 サマリー", "📝 学習履歴",
        "💬 提出物・フィードバック", "📈 成長記録", "📓 授業外学習", "📓 教員メモ"
    ])
    sid = student.get('user_id', student.get('id', ''))
    with tab0:
        show_student_profile_readonly(student, sid)
    with tab1:
        show_portfolio_summary(student, sid)
    with tab2:
        show_learning_history(sid)
    with tab3:
        show_submissions_and_feedback(sid)
    with tab4:
        show_growth_record(sid)
    with tab5:
        show_extracurricular_logs(sid)
    with tab6:
        show_teacher_notes(student)


MODULE_LABELS = {
    'speaking': '🎤 スピーキング',
    'speaking_pronunciation': '🎤 発音練習',
    'speaking_chat': '💬 会話練習',
    'speaking_read_aloud': '🎤 音読練習',
    'writing': '✍️ ライティング',
    'writing_practice': '✍️ ライティング練習',
    'writing_submission': '✍️ ライティング提出',
    'reading': '📖 リーディング',
    'reading_practice': '📖 リーディング練習',
    'listening': '👂 リスニング',
    'listening_practice': '👂 リスニング練習',
    'listening_dictation': '👂 ディクテーション',
    'listening_youtube': '👂 YouTube学習',
    'vocabulary': '📚 語彙学習',
    'vocabulary_quiz': '📚 語彙クイズ',
    'vocabulary_flashcard': '📚 フラッシュカード',
    'vocabulary_exercise': '📚 語彙練習',
    'exam_practice': '📝 検定練習',
}


def show_student_profile_readonly(student, student_id):
    """教員用：学生プロフィール閲覧（読み取り専用）"""
    st.markdown("### 👤 学生プロフィール")

    # selected_studentに渡されたprofileを優先、なければDBから取得
    profile = student.get('profile') or {}
    if not profile:
        try:
            from utils.database import get_student_profile
            profile = get_student_profile(student_id) or {}
        except Exception:
            profile = {}

    if not profile:
        st.info("この学生はまだプロフィールを入力していません。")
        return

    # 基本情報
    st.markdown("#### 📋 基本情報")
    col1, col2, col3 = st.columns(3)
    with col1:
        st.markdown(f"**学籍番号:** {profile.get('student_number', '未入力')}")
    with col2:
        st.markdown(f"**学部:** {profile.get('faculty', '未入力')}")
    with col3:
        st.markdown(f"**出身地:** {profile.get('hometown') or '未入力'}")

    if profile.get('hobbies'):
        st.markdown(f"**趣味:** {profile['hobbies']}")

    # 自己紹介
    if profile.get('self_intro_ja') or profile.get('self_intro_en'):
        st.markdown("---")
        st.markdown("#### ✍️ 自己紹介")
        if profile.get('self_intro_ja'):
            st.markdown(f"**日本語:** {profile['self_intro_ja']}")
        if profile.get('self_intro_en'):
            st.markdown(f"**English:** {profile['self_intro_en']}")

    # 検定スコア
    test_scores = profile.get('test_scores') or {}
    if test_scores:
        st.markdown("---")
        st.markdown("#### 📊 検定スコア")
        score_cols = st.columns(min(len(test_scores), 5))
        score_labels = {
            'toefl_itp': 'TOEFL ITP',
            'toeic': 'TOEIC',
            'ielts': 'IELTS',
            'eiken': '英検',
            'toefl_ibt': 'TOEFL iBT',
        }
        for idx, (key, val) in enumerate(test_scores.items()):
            if val:
                with score_cols[idx % len(score_cols)]:
                    label = score_labels.get(key, key)
                    st.metric(label, str(val))
    elif profile.get('toefl_itp_score'):
        st.markdown("---")
        st.markdown("#### 📊 検定スコア")
        st.metric("TOEFL ITP", str(profile['toefl_itp_score']))

    # 学習目標
    if profile.get('english_weakness') or profile.get('english_goals'):
        st.markdown("---")
        st.markdown("#### 🎯 学習目標")
        if profile.get('english_weakness'):
            st.markdown(f"**苦手な部分:** {profile['english_weakness']}")
        if profile.get('english_goals'):
            st.markdown(f"**目標:** {profile['english_goals']}")


def _get_all_stats(student_id: str, days: int = 7):
    """practice_logs / reading_logs / listening_logs を統合して集計"""
    from utils.database import get_student_practice_stats, get_student_reading_logs, get_student_listening_logs
    # practice_logs
    stats = get_student_practice_stats(student_id, days=days) or {}
    total_count = sum(d.get('count', 0) for d in stats.values())
    total_sec = sum(d.get('total_seconds', 0) for d in stats.values())
    all_scores = []
    for d in stats.values():
        all_scores.extend(d.get('scores', []))

    # reading_logs
    reading_rows = get_student_reading_logs(student_id, days=days) or []
    for r in reading_rows:
        total_count += 1
        total_sec += r.get('time_spent_seconds') or 0
        qs = r.get('quiz_score')
        if qs is not None:
            all_scores.append(float(qs))
    if reading_rows:
        reading_count = len(reading_rows)
        reading_sec = sum(r.get('time_spent_seconds') or 0 for r in reading_rows)
        reading_scores = [float(r['quiz_score']) for r in reading_rows if r.get('quiz_score') is not None]
        stats['reading_logs'] = {'count': reading_count, 'total_seconds': reading_sec, 'scores': reading_scores}

    # listening_logs
    listening_rows = get_student_listening_logs(student_id, days=days) or []
    for l in listening_rows:
        total_count += 1
        total_sec += l.get('time_spent_seconds') or 0
        qs = l.get('quiz_score')
        if qs is not None:
            all_scores.append(float(qs))
    if listening_rows:
        listening_count = len(listening_rows)
        listening_sec = sum(l.get('time_spent_seconds') or 0 for l in listening_rows)
        listening_scores = [float(l['quiz_score']) for l in listening_rows if l.get('quiz_score') is not None]
        stats['listening_logs'] = {'count': listening_count, 'total_seconds': listening_sec, 'scores': listening_scores}

    avg = round(sum(all_scores) / len(all_scores), 1) if all_scores else 0
    return stats, total_count, round(total_sec / 60), avg


def show_portfolio_summary(student, student_id):
    """サマリータブ"""
    st.markdown("### 📊 学習サマリー")
    # practice_logs + reading_logs + listening_logs を統合
    try:
        stats_7, practice_count, weekly_minutes, avg = _get_all_stats(student_id, days=7)
    except Exception:
        stats_7, practice_count, weekly_minutes, avg = {}, 0, 0, 0

    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("平均スコア", f"{avg:.1f}点" if avg > 0 else "-")
    with col2:
        st.metric("練習回数（今週）", f"{practice_count}回")
    with col3:
        st.metric("今週の学習時間", f"{weekly_minutes}分")
    with col4:
        st.metric("課題提出", f"{student.get('submissions', 0)}/{student.get('total_assignments', 0)}")

    st.markdown("---")
    st.markdown("### 📊 モジュール別の練習状況（直近30日）")
    try:
        stats_30, _, _, _ = _get_all_stats(student_id, days=30)
        MODULE_DISPLAY = {
            **MODULE_LABELS,
            'reading_logs': '📖 リーディング',
            'listening_logs': '👂 リスニング',
        }
        if stats_30:
            col1, col2, col3, col4 = st.columns([3, 1, 1, 1])
            with col1: st.caption("モジュール")
            with col2: st.caption("回数")
            with col3: st.caption("時間")
            with col4: st.caption("平均スコア")
            for module, data in stats_30.items():
                label = MODULE_DISPLAY.get(module, module)
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
            ["全て", "speaking", "writing", "vocabulary", "reading_practice", "listening_practice"],
            format_func=lambda x: {
                "全て": "全て",
                "speaking": "🎤 スピーキング",
                "writing": "✍️ ライティング",
                "vocabulary": "📚 語彙",
                "reading_practice": "📖 リーディング",
                "listening_practice": "👂 リスニング",
            }.get(x, x))
    with col2:
        days_map = {"今週": 7, "今月": 30, "過去3ヶ月": 90, "全期間": 365}
        period = st.selectbox("期間", list(days_map.keys()))
        days = days_map[period]

    st.markdown("---")
    module_type = module_filter if module_filter != "全て" else None
    # writing/vocabulary は複数のmodule_typeをまとめて検索
    MODULE_GROUPS = {
        'speaking': ['speaking', 'speaking_pronunciation', 'speaking_chat', 'speaking_read_aloud'],
        'writing': ['writing', 'writing_practice', 'writing_submission'],
        'vocabulary': ['vocabulary', 'vocabulary_quiz', 'vocabulary_flashcard', 'vocabulary_exercise'],
    }
    try:
        from utils.database import get_student_practice_details, get_student_listening_logs
        all_logs = []
        if module_type != "listening_practice":
            if module_type in MODULE_GROUPS:
                # グループ内の全module_typeを取得してマージ
                raw = []
                for mt in MODULE_GROUPS[module_type]:
                    raw.extend(get_student_practice_details(student_id, days=days, module_type=mt) or [])
            else:
                raw = get_student_practice_details(student_id, days=days, module_type=module_type) or []
            for log in raw:
                details = log.get("activity_details") or {}
                dt = log.get("practiced_at", "")[:16].replace("T", " ")
                module = MODULE_LABELS.get(log.get("module_type", ""), log.get("module_type", ""))
                title = details.get("title", "")
                all_logs.append({"dt": dt, "header": f"📌 {dt} — {module}" + (f": {title}" if title else ""), "module": module, "title": title, "score": log.get("score"), "duration": log.get("duration_seconds", 0), "details": details})
        if module_type in (None, "listening_practice"):
            for log in (get_student_listening_logs(student_id, days=days) or []):
                dt = log.get("completed_at", "")[:16].replace("T", " ")
                title = log.get("video_title", "") or ""
                score = log.get("quiz_score")
                atype = log.get("activity_type", "practice")
                type_label = {"extensive": "YouTube学習", "practice": "練習", "dictation": "ディクテーション"}.get(atype, atype)
                all_logs.append({"dt": dt, "header": f"👂 {dt} — リスニング ({type_label})" + (f": {title}" if title else ""), "module": "👂 リスニング", "title": title, "score": score, "duration": log.get("time_spent_seconds", 0), "details": {}})
        all_logs.sort(key=lambda x: x["dt"], reverse=True)
        if not all_logs:
            st.info("この条件の学習データはありません")
            return
        st.caption(f"{len(all_logs)}件のログ")
        for log in all_logs[:30]:
            details = log.get("details", {})
            title = log.get("title", "")
            with st.expander(log["header"]):
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
        if len(all_logs) > 30:
            st.caption(f"... 他 {len(all_logs) - 30}件")

        if st.button("📥 CSV出力"):
            import pandas as pd
            df = pd.DataFrame([{
                '日時': l.get('dt', ''),
                'モジュール': l.get('module', ''),
                'スコア': l.get('score', ''),
                '時間(秒)': l.get('title', ''),
            } for l in all_logs])
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
                'モジュール': l.get('module', ''),
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


def show_extracurricular_logs(student_id):
    """授業外学習ログタブ（教員閲覧用）"""
    st.markdown("### 📝 授業外学習ログ")
    st.caption("学生が記録した授業外の外国語学習活動")

    ACTIVITY_CATEGORIES = {
        "movie": "🎬 映画・ドラマ視聴",
        "reading": "📖 読書",
        "podcast": "🎧 ポッドキャスト",
        "conversation": "💬 会話・言語交換",
        "app": "📱 アプリ学習",
        "video": "📺 YouTube・動画",
        "writing": "✍️ ライティング・日記",
        "music": "🎵 音楽・歌詞",
        "game": "🎮 ゲーム",
        "class": "📚 他の授業・講座",
        "other": "📝 その他",
    }
    STATUS_LABELS = {
        "approved": "✅ 承認済み",
        "pending": "⏳ 確認待ち",
        "rejected": "❌ 却下",
    }

    try:
        from utils.database import get_student_learning_logs
        logs = get_student_learning_logs(student_id, limit=200)
    except Exception as e:
        st.error(f"授業外学習ログの取得に失敗: {e}")
        return

    if not logs:
        st.info("まだ授業外学習の記録がありません")
        return

    # サマリー
    total_minutes = sum(l.get("duration_minutes", 0) for l in logs)
    total_points = sum(l.get("points", 0) for l in logs)
    approved_points = sum(l.get("points", 0) for l in logs if l.get("status") == "approved")
    pending_count = sum(1 for l in logs if l.get("status", "pending") == "pending")

    col1, col2, col3, col4 = st.columns(4)
    with col1:
        h, m = total_minutes // 60, total_minutes % 60
        st.metric("累計学習時間", f"{h}h {m}m")
    with col2:
        st.metric("累計ポイント", f"{total_points}pt")
    with col3:
        st.metric("承認済みポイント", f"{approved_points}pt")
    with col4:
        st.metric("承認待ち", f"{pending_count}件")

    st.markdown("---")

    # 承認待ちを先に表示
    pending = [l for l in logs if l.get("status", "pending") == "pending"]
    if pending:
        st.markdown("#### ⏳ 承認待ち")
        for log in pending:
            cat = log.get("category", "other")
            cat_name = ACTIVITY_CATEGORIES.get(cat, cat)
            date = (log.get("log_date") or log.get("created_at") or "")[:10]
            title = log.get("title", "")
            pts = log.get("points", 0)
            mins = log.get("duration_minutes", 0)
            log_id = log.get("id", "")
            with st.expander(f"⏳ {date} — {title} (+{pts}pt)"):
                col1, col2 = st.columns([3, 1])
                with col1:
                    st.markdown(f"- **カテゴリ:** {cat_name}")
                    st.markdown(f"- **時間:** {mins}分")
                    if log.get("description"):
                        st.markdown(f"- **詳細:** {log['description']}")
                    if log.get("evidence_url"):
                        st.markdown(f"- **証拠URL:** {log['evidence_url']}")
                with col2:
                    st.metric("ポイント", f"+{pts}")
                    # 承認/却下ボタン
                    try:
                        from utils.database import update_learning_log
                        col_a, col_b = st.columns(2)
                        with col_a:
                            if st.button("✅", key=f"approve_{log_id}", help="承認"):
                                update_learning_log(log_id, {"status": "approved"})
                                st.success("承認しました")
                                st.rerun()
                        with col_b:
                            if st.button("❌", key=f"reject_{log_id}", help="却下"):
                                update_learning_log(log_id, {"status": "rejected"})
                                st.warning("却下しました")
                                st.rerun()
                    except Exception:
                        pass
        st.markdown("---")

    # 全ログ一覧
    st.markdown(f"#### 📋 全記録 ({len(logs)}件)")
    for log in logs:
        cat = log.get("category", "other")
        cat_name = ACTIVITY_CATEGORIES.get(cat, cat)
        date = (log.get("log_date") or log.get("created_at") or "")[:10]
        title = log.get("title", "")
        pts = log.get("points", 0)
        mins = log.get("duration_minutes", 0)
        status = log.get("status", "pending")
        status_label = STATUS_LABELS.get(status, status)
        with st.expander(f"{status_label} {date} — {title} (+{pts}pt)"):
            col1, col2 = st.columns([3, 1])
            with col1:
                st.markdown(f"- **カテゴリ:** {cat_name}")
                st.markdown(f"- **時間:** {mins}分")
                if log.get("description"):
                    st.markdown(f"- **詳細:** {log['description']}")
                if log.get("evidence_url"):
                    st.markdown(f"- **証拠URL:** {log['evidence_url']}")
            with col2:
                st.metric("ポイント", f"+{pts}")


def show_teacher_notes(student):
    """教員メモ（DB永続化）"""
    st.markdown("### 📓 教員メモ")
    st.caption("この学生に関するメモや個別目標を記録できます")

    sid = student.get('user_id', student.get('id', ''))
    teacher = get_current_user()
    teacher_id = teacher.get('id', '')

    # DBからメモを読み込み、失敗時はsession_stateにフォールバック
    existing_note = None
    db_available = False
    try:
        from utils.database import get_teacher_note
        existing_note = get_teacher_note(teacher_id, sid)
        db_available = True
    except Exception:
        pass

    memo_key = f"teacher_memo_{sid}"
    goal_key = f"teacher_goal_{sid}"

    if existing_note:
        default_goal = existing_note.get('goal', '')
        default_memo = existing_note.get('memo', '')
    else:
        default_goal = st.session_state.get(goal_key, '')
        default_memo = st.session_state.get(memo_key, '')

    new_goal = st.text_input("🎯 個別目標", value=default_goal,
                              placeholder="例: TOEFL ITP 500点達成")
    new_memo = st.text_area("📝 メモ", value=default_memo,
                             placeholder="この学生に関する観察メモ...", height=150)

    if st.button("💾 メモを保存", type="primary"):
        saved = False
        if db_available:
            try:
                from utils.database import upsert_teacher_note
                result = upsert_teacher_note(teacher_id, sid,
                                             memo=new_memo, goal=new_goal)
                if result:
                    saved = True
            except Exception:
                pass

        # session_stateにも保存（フォールバック）
        st.session_state[memo_key] = new_memo
        st.session_state[goal_key] = new_goal

        if saved:
            st.success("✅ メモを保存しました")
        else:
            st.warning("⚠️ セッション内に保存しました（DB保存は teacher_notes テーブル作成後に有効になります）")


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
