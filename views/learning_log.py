import streamlit as st
from utils.auth import get_current_user, require_auth
from datetime import datetime, timedelta

# 学習活動のカテゴリ
ACTIVITY_CATEGORIES = {
    "movie": {"name": "🎬 映画・ドラマ視聴", "points_per_hour": 10},
    "reading": {"name": "📖 読書（本・漫画・記事）", "points_per_hour": 12},
    "podcast": {"name": "🎧 ポッドキャスト・音声", "points_per_hour": 10},
    "conversation": {"name": "💬 会話・言語交換", "points_per_hour": 15},
    "app": {"name": "📱 アプリ学習（Duolingoなど）", "points_per_hour": 8},
    "video": {"name": "📺 YouTube・動画学習", "points_per_hour": 10},
    "writing": {"name": "✍️ ライティング・日記", "points_per_hour": 12},
    "music": {"name": "🎵 音楽・歌詞学習", "points_per_hour": 6},
    "game": {"name": "🎮 ゲーム（外国語）", "points_per_hour": 8},
    "class": {"name": "📚 他の授業・講座", "points_per_hour": 12},
    "other": {"name": "📝 その他", "points_per_hour": 8},
}

# 言語
LANGUAGES = {
    "english": "🇬🇧 英語",
    "spanish": "🇪🇸 スペイン語",
    "french": "🇫🇷 フランス語",
    "german": "🇩🇪 ドイツ語",
    "chinese": "🇨🇳 中国語",
    "korean": "🇰🇷 韓国語",
    "other": "🌐 その他",
}

@require_auth
def show():
    user = get_current_user()
    
    st.markdown("## 📝 授業外学習ログ")
    
    if user['role'] == 'teacher':
        st.info("教員として閲覧中。学生のポートフォリオから個別の学習ログを確認できます。")
        if st.button("← 教員ホームに戻る"):
            st.session_state['current_view'] = 'teacher_home'
            st.rerun()
        return
    
    if st.button("← ホームに戻る"):
        st.session_state['current_view'] = 'student_home'
        st.rerun()
    
    st.markdown("---")
    
    # 初期化
    if 'learning_logs' not in st.session_state:
        st.session_state.learning_logs = {}
    
    user_email = user.get('email', user.get('name', 'default'))
    
    if user_email not in st.session_state.learning_logs:
        st.session_state.learning_logs[user_email] = []
    
    user_logs = st.session_state.learning_logs[user_email]
    
    # タブ
    tab1, tab2, tab3, tab4 = st.tabs([
        "➕ 学習を記録",
        "📊 学習サマリー",
        "📋 学習履歴",
        "🏆 ポイント・成績"
    ])
    
    with tab1:
        show_add_log(user, user_email)
    with tab2:
        show_learning_summary(user_logs)
    with tab3:
        show_learning_history(user_logs, user_email)
    with tab4:
        show_points_and_grades(user_logs)


def show_add_log(user, user_email):
    """学習を記録"""
    
    st.markdown("### ➕ 新しい学習を記録")
    st.caption("授業外で行った外国語学習を記録しましょう。記録はポイントとして成績に加算されます。")
    
    with st.form("add_learning_log"):
        col1, col2 = st.columns(2)
        
        with col1:
            # 日付
            log_date = st.date_input("📅 日付", value=datetime.now().date())
            
            # カテゴリ
            category = st.selectbox(
                "📂 活動カテゴリ",
                list(ACTIVITY_CATEGORIES.keys()),
                format_func=lambda x: ACTIVITY_CATEGORIES[x]['name']
            )
            
            # 言語
            language = st.selectbox(
                "🌍 言語",
                list(LANGUAGES.keys()),
                format_func=lambda x: LANGUAGES[x]
            )
        
        with col2:
            # 時間
            hours = st.number_input("⏱️ 学習時間（時間）", 0, 12, 1)
            minutes = st.number_input("⏱️ 学習時間（分）", 0, 59, 0, step=15)
            
            total_minutes = hours * 60 + minutes
            
            # ポイント計算プレビュー
            points_per_hour = ACTIVITY_CATEGORIES[category]['points_per_hour']
            estimated_points = int(total_minutes / 60 * points_per_hour)
            st.info(f"💰 獲得予定ポイント: **{estimated_points}点**")
        
        # 活動内容
        st.markdown("---")
        title = st.text_input("📌 タイトル *", placeholder="例: Netflix「フレンズ」シーズン1エピソード3")
        description = st.text_area(
            "📝 詳細（任意）",
            placeholder="何を学んだか、感想、新しく覚えた単語など...",
            height=100
        )
        
        # 証拠添付（任意）
        st.markdown("---")
        st.markdown("📎 **証拠を添付（任意）**")
        st.caption("スクリーンショット、写真、学習アプリの記録などを添付できます")
        
        uploaded_file = st.file_uploader(
            "画像をアップロード",
            type=['png', 'jpg', 'jpeg', 'gif'],
            help="学習の証拠となる画像をアップロードしてください"
        )
        
        evidence_url = st.text_input(
            "または URL を入力（任意）",
            placeholder="例: https://www.duolingo.com/profile/username"
        )
        
        # 送信
        submitted = st.form_submit_button("📤 記録を保存", type="primary")
        
        if submitted:
            if not title:
                st.error("タイトルを入力してください")
            elif total_minutes == 0:
                st.error("学習時間を入力してください")
            else:
                # 新しいログを作成
                new_log = {
                    "id": f"log_{datetime.now().timestamp()}",
                    "date": log_date.strftime("%Y-%m-%d"),
                    "category": category,
                    "category_name": ACTIVITY_CATEGORIES[category]['name'],
                    "language": language,
                    "language_name": LANGUAGES[language],
                    "title": title,
                    "description": description,
                    "duration_minutes": total_minutes,
                    "points": estimated_points,
                    "evidence_file": uploaded_file.name if uploaded_file else None,
                    "evidence_url": evidence_url if evidence_url else None,
                    "status": "pending",  # pending, approved, rejected
                    "created_at": datetime.now().strftime("%Y-%m-%d %H:%M"),
                }
                
                st.session_state.learning_logs[user_email].insert(0, new_log)
                
                st.success(f"✅ 学習を記録しました！ +{estimated_points}ポイント")
                st.balloons()
    
    # 最近の記録
    st.markdown("---")
    st.markdown("### 📋 最近の記録")
    
    recent_logs = st.session_state.learning_logs.get(user_email, [])[:3]
    
    if recent_logs:
        for log in recent_logs:
            col1, col2, col3 = st.columns([1, 3, 1])
            with col1:
                st.caption(log['date'])
            with col2:
                st.markdown(f"**{log['title']}**")
                st.caption(f"{log['category_name']} | {log['language_name']} | {log['duration_minutes']}分")
            with col3:
                st.markdown(f"+{log['points']}pt")
    else:
        st.info("まだ記録がありません")


def show_learning_summary(logs):
    """学習サマリー"""
    
    st.markdown("### 📊 学習サマリー")
    
    if not logs:
        st.info("まだ学習記録がありません。「➕ 学習を記録」から記録を始めましょう！")
        return
    
    # 期間選択
    period = st.radio(
        "期間",
        ["week", "month", "semester", "all"],
        format_func=lambda x: {"week": "今週", "month": "今月", "semester": "今学期", "all": "全期間"}[x],
        horizontal=True
    )
    
    # 期間でフィルタ
    filtered_logs = filter_logs_by_period(logs, period)
    
    st.markdown("---")
    
    # メトリクス
    total_minutes = sum(log['duration_minutes'] for log in filtered_logs)
    total_points = sum(log['points'] for log in filtered_logs)
    total_days = len(set(log['date'] for log in filtered_logs))
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        hours = total_minutes // 60
        mins = total_minutes % 60
        st.metric("総学習時間", f"{hours}時間{mins}分")
    
    with col2:
        st.metric("総ポイント", f"{total_points}pt")
    
    with col3:
        st.metric("学習日数", f"{total_days}日")
    
    with col4:
        avg_per_day = total_minutes / max(total_days, 1)
        st.metric("1日平均", f"{avg_per_day:.0f}分")
    
    st.markdown("---")
    
    # カテゴリ別集計
    st.markdown("#### 📂 カテゴリ別")
    
    category_stats = {}
    for log in filtered_logs:
        cat = log['category']
        if cat not in category_stats:
            category_stats[cat] = {"minutes": 0, "points": 0, "count": 0}
        category_stats[cat]['minutes'] += log['duration_minutes']
        category_stats[cat]['points'] += log['points']
        category_stats[cat]['count'] += 1
    
    for cat, stats in sorted(category_stats.items(), key=lambda x: x[1]['minutes'], reverse=True):
        col1, col2, col3 = st.columns([3, 1, 1])
        with col1:
            st.markdown(f"**{ACTIVITY_CATEGORIES[cat]['name']}**")
            st.progress(stats['minutes'] / max(total_minutes, 1))
        with col2:
            st.caption(f"{stats['minutes']}分")
        with col3:
            st.caption(f"+{stats['points']}pt")
    
    st.markdown("---")
    
    # 言語別集計
    st.markdown("#### 🌍 言語別")
    
    language_stats = {}
    for log in filtered_logs:
        lang = log['language']
        if lang not in language_stats:
            language_stats[lang] = {"minutes": 0, "count": 0}
        language_stats[lang]['minutes'] += log['duration_minutes']
        language_stats[lang]['count'] += 1
    
    for lang, stats in sorted(language_stats.items(), key=lambda x: x[1]['minutes'], reverse=True):
        col1, col2 = st.columns([3, 1])
        with col1:
            st.markdown(f"**{LANGUAGES[lang]}**")
            st.progress(stats['minutes'] / max(total_minutes, 1))
        with col2:
            hours = stats['minutes'] // 60
            mins = stats['minutes'] % 60
            st.caption(f"{hours}h {mins}m")


def show_learning_history(logs, user_email):
    """学習履歴"""
    
    st.markdown("### 📋 学習履歴")
    
    if not logs:
        st.info("まだ学習記録がありません")
        return
    
    # フィルタ
    col1, col2, col3 = st.columns(3)
    with col1:
        cat_filter = st.selectbox(
            "カテゴリ",
            ["all"] + list(ACTIVITY_CATEGORIES.keys()),
            format_func=lambda x: "すべて" if x == "all" else ACTIVITY_CATEGORIES[x]['name']
        )
    with col2:
        lang_filter = st.selectbox(
            "言語",
            ["all"] + list(LANGUAGES.keys()),
            format_func=lambda x: "すべて" if x == "all" else LANGUAGES[x]
        )
    with col3:
        status_filter = st.selectbox(
            "ステータス",
            ["all", "pending", "approved", "rejected"],
            format_func=lambda x: {
                "all": "すべて",
                "pending": "⏳ 確認待ち",
                "approved": "✅ 承認済み",
                "rejected": "❌ 却下"
            }[x]
        )
    
    # フィルタ適用
    filtered = logs.copy()
    if cat_filter != "all":
        filtered = [l for l in filtered if l['category'] == cat_filter]
    if lang_filter != "all":
        filtered = [l for l in filtered if l['language'] == lang_filter]
    if status_filter != "all":
        filtered = [l for l in filtered if l.get('status', 'pending') == status_filter]
    
    st.markdown("---")
    st.caption(f"{len(filtered)}件")
    
    # 履歴表示
    for log in filtered:
        with st.expander(f"📌 {log['date']} - {log['title']} (+{log['points']}pt)"):
            col1, col2 = st.columns([3, 1])
            
            with col1:
                st.markdown(f"**{log['title']}**")
                st.markdown(f"- カテゴリ: {log['category_name']}")
                st.markdown(f"- 言語: {log['language_name']}")
                st.markdown(f"- 時間: {log['duration_minutes']}分")
                
                if log.get('description'):
                    st.markdown("---")
                    st.markdown(f"**詳細:** {log['description']}")
                
                if log.get('evidence_file') or log.get('evidence_url'):
                    st.markdown("---")
                    st.markdown("**証拠:**")
                    if log.get('evidence_file'):
                        st.caption(f"📎 {log['evidence_file']}")
                    if log.get('evidence_url'):
                        st.caption(f"🔗 {log['evidence_url']}")
            
            with col2:
                status = log.get('status', 'pending')
                if status == 'approved':
                    st.success("✅ 承認済み")
                elif status == 'rejected':
                    st.error("❌ 却下")
                else:
                    st.warning("⏳ 確認待ち")
                
                st.metric("ポイント", f"+{log['points']}")
            
            # 編集・削除
            col1, col2 = st.columns(2)
            with col1:
                if st.button("✏️ 編集", key=f"edit_{log['id']}"):
                    st.session_state[f'editing_log_{log["id"]}'] = True
            with col2:
                if st.button("🗑️ 削除", key=f"delete_{log['id']}"):
                    st.session_state.learning_logs[user_email] = [
                        l for l in st.session_state.learning_logs[user_email] if l['id'] != log['id']
                    ]
                    st.success("削除しました")
                    st.rerun()
            
            if st.session_state.get(f'editing_log_{log["id"]}'):
                st.markdown("---")
                new_title = st.text_input("タイトル", value=log.get('title', ''), key=f"edit_title_{log['id']}")
                new_duration = st.number_input("学習時間（分）", min_value=1, value=log.get('duration_minutes', 30), key=f"edit_dur_{log['id']}")
                new_content = st.text_area("学習内容", value=log.get('content', ''), key=f"edit_content_{log['id']}")
                ecol1, ecol2 = st.columns(2)
                with ecol1:
                    if st.button("💾 保存", key=f"save_log_{log['id']}"):
                        log['title'] = new_title
                        log['duration_minutes'] = new_duration
                        log['content'] = new_content
                        del st.session_state[f'editing_log_{log["id"]}']
                        st.success("保存しました！")
                        st.rerun()
                with ecol2:
                    if st.button("❌ キャンセル", key=f"cancel_log_{log['id']}"):
                        del st.session_state[f'editing_log_{log["id"]}']
                        st.rerun()


def show_points_and_grades(logs):
    """ポイントと成績"""
    
    st.markdown("### 🏆 ポイント・成績への反映")
    
    # 総ポイント計算
    total_points = sum(log['points'] for log in logs)
    approved_points = sum(log['points'] for log in logs if log.get('status') == 'approved')
    pending_points = sum(log['points'] for log in logs if log.get('status', 'pending') == 'pending')
    
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("総獲得ポイント", f"{total_points}pt")
    with col2:
        st.metric("承認済みポイント", f"{approved_points}pt", help="成績に反映されるポイント")
    with col3:
        st.metric("確認待ち", f"{pending_points}pt")
    
    st.markdown("---")
    
    # ポイントの成績換算
    st.markdown("#### 📊 成績への換算")
    
    st.markdown("""
    | ポイント | 評価 | 成績加算 |
    |---------|------|---------|
    | 0-49 | D | +0点 |
    | 50-99 | C | +2点 |
    | 100-199 | B | +4点 |
    | 200-299 | A | +6点 |
    | 300+ | S | +10点 |
    """)
    
    # 現在のランク
    if total_points >= 300:
        rank = "S"
        bonus = 10
    elif total_points >= 200:
        rank = "A"
        bonus = 6
    elif total_points >= 100:
        rank = "B"
        bonus = 4
    elif total_points >= 50:
        rank = "C"
        bonus = 2
    else:
        rank = "D"
        bonus = 0
    
    st.markdown("---")
    st.markdown(f"### 🎯 現在のランク: **{rank}** (+{bonus}点)")
    
    if rank != "S":
        next_thresholds = {"D": 50, "C": 100, "B": 200, "A": 300}
        next_rank = {"D": "C", "C": "B", "B": "A", "A": "S"}
        remaining = next_thresholds[rank] - total_points
        st.caption(f"次のランク「{next_rank[rank]}」まであと **{remaining}pt**")
        st.progress(total_points / next_thresholds[rank])
    else:
        st.success("🎉 最高ランク達成！")
    
    st.markdown("---")
    
    # ポイント獲得のヒント
    st.markdown("#### 💡 ポイントを増やすヒント")
    
    tips = [
        "🎬 映画1本（2時間）= 約20ポイント",
        "📖 本1章（30分）= 約6ポイント",
        "💬 言語交換（1時間）= 約15ポイント",
        "📱 Duolingo（15分）= 約2ポイント",
    ]
    
    for tip in tips:
        st.markdown(f"- {tip}")


def filter_logs_by_period(logs, period):
    """期間でログをフィルタ"""
    today = datetime.now().date()
    
    if period == "week":
        start_date = today - timedelta(days=today.weekday())
    elif period == "month":
        start_date = today.replace(day=1)
    elif period == "semester":
        # 学期の開始日（仮に4月1日または10月1日）
        if today.month >= 4 and today.month < 10:
            start_date = today.replace(month=4, day=1)
        else:
            if today.month >= 10:
                start_date = today.replace(month=10, day=1)
            else:
                start_date = today.replace(year=today.year-1, month=10, day=1)
    else:
        return logs
    
    return [log for log in logs if datetime.strptime(log['date'], "%Y-%m-%d").date() >= start_date]
