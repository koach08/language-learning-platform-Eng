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
    
    # --- DBからログを読み込み ---
    user_logs = _load_user_logs(user['id'])
    
    # タブ
    tab1, tab2, tab3, tab4 = st.tabs([
        "➕ 学習を記録",
        "📊 学習サマリー",
        "📋 学習履歴",
        "🏆 ポイント・成績"
    ])
    
    with tab1:
        show_add_log(user, user_logs)
    with tab2:
        show_learning_summary(user_logs)
    with tab3:
        show_learning_history(user_logs, user['id'])
    with tab4:
        show_points_and_grades(user_logs)


def _load_user_logs(user_id: str) -> list:
    """DBから学習ログを読み込み、失敗時はsession_stateにフォールバック"""
    cache_key = f'_learning_logs_{user_id}'
    
    # キャッシュがあれば使う（同一セッション内の高速化）
    if cache_key in st.session_state and not st.session_state.get('_learning_logs_refresh'):
        return st.session_state[cache_key]
    
    try:
        from utils.database import get_student_learning_logs
        db_logs = get_student_learning_logs(user_id, limit=200)
        # DB形式 → 表示用形式に変換
        logs = []
        for row in db_logs:
            cat = row.get('category', 'other')
            lang = row.get('language', 'english')
            logs.append({
                'id': row['id'],
                'date': row.get('log_date', ''),
                'category': cat,
                'category_name': ACTIVITY_CATEGORIES.get(cat, {}).get('name', cat),
                'language': lang,
                'language_name': LANGUAGES.get(lang, lang),
                'title': row.get('title', ''),
                'description': row.get('description', ''),
                'duration_minutes': row.get('duration_minutes', 0),
                'points': row.get('points', 0),
                'evidence_file': row.get('evidence_file_name'),
                'evidence_url': row.get('evidence_url'),
                'status': row.get('status', 'pending'),
                'created_at': row.get('created_at', ''),
                'from_db': True,
            })
        st.session_state[cache_key] = logs
        st.session_state['_learning_logs_refresh'] = False
        return logs
    except Exception:
        # DB接続失敗時はsession_stateフォールバック
        return st.session_state.get(cache_key, [])


def _refresh_logs():
    """ログのキャッシュをクリアして再読み込みを促す"""
    st.session_state['_learning_logs_refresh'] = True


def show_add_log(user, user_logs):
    """学習を記録"""
    
    st.markdown("### ➕ 新しい学習を記録")
    st.caption("授業外で行った外国語学習を記録しましょう。記録はポイントとして成績に加算されます。")
    
    with st.form("add_learning_log"):
        col1, col2 = st.columns(2)
        
        with col1:
            log_date = st.date_input("📅 日付", value=datetime.now().date())
            category = st.selectbox(
                "📂 活動カテゴリ",
                list(ACTIVITY_CATEGORIES.keys()),
                format_func=lambda x: ACTIVITY_CATEGORIES[x]['name']
            )
            language = st.selectbox(
                "🌍 言語",
                list(LANGUAGES.keys()),
                format_func=lambda x: LANGUAGES[x]
            )
        
        with col2:
            hours = st.number_input("⏱️ 学習時間（時間）", 0, 12, 1)
            minutes = st.number_input("⏱️ 学習時間（分）", 0, 59, 0, step=15)
            total_minutes = hours * 60 + minutes
            points_per_hour = ACTIVITY_CATEGORIES[category]['points_per_hour']
            estimated_points = int(total_minutes / 60 * points_per_hour)
            st.info(f"💰 獲得予定ポイント: **{estimated_points}点**")
        
        st.markdown("---")
        title = st.text_input("📌 タイトル *", placeholder="例: Netflix「フレンズ」シーズン1エピソード3")
        description = st.text_area(
            "📝 詳細（任意）",
            placeholder="何を学んだか、感想、新しく覚えた単語など...",
            height=100
        )
        
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
        
        submitted = st.form_submit_button("📤 記録を保存", type="primary")
        
        if submitted:
            if not title:
                st.error("タイトルを入力してください")
            elif total_minutes == 0:
                st.error("学習時間を入力してください")
            else:
                log_data = {
                    'date': log_date.strftime("%Y-%m-%d"),
                    'category': category,
                    'language': language,
                    'title': title,
                    'description': description,
                    'duration_minutes': total_minutes,
                    'points': estimated_points,
                    'evidence_file': uploaded_file.name if uploaded_file else None,
                    'evidence_url': evidence_url if evidence_url else None,
                    'status': 'pending',
                }
                
                # --- DB保存 ---
                saved = False
                try:
                    from utils.database import save_learning_log
                    result = save_learning_log(user['id'], log_data)
                    if result:
                        saved = True
                        _refresh_logs()
                except Exception as e:
                    st.warning(f"DB保存に問題がありましたが、ローカルに記録しました: {e}")
                
                if not saved:
                    # フォールバック: session_stateに保存
                    cache_key = f'_learning_logs_{user["id"]}'
                    if cache_key not in st.session_state:
                        st.session_state[cache_key] = []
                    log_data['id'] = f"local_{datetime.now().timestamp()}"
                    log_data['category_name'] = ACTIVITY_CATEGORIES[category]['name']
                    log_data['language_name'] = LANGUAGES[language]
                    log_data['created_at'] = datetime.now().strftime("%Y-%m-%d %H:%M")
                    st.session_state[cache_key].insert(0, log_data)
                
                st.success(f"✅ 学習を記録しました！ +{estimated_points}ポイント")
                st.balloons()
                st.rerun()
    
    # 最近の記録
    st.markdown("---")
    st.markdown("### 📋 最近の記録")
    
    recent_logs = user_logs[:3]
    
    if recent_logs:
        for log in recent_logs:
            col1, col2, col3 = st.columns([1, 3, 1])
            with col1:
                st.caption(log.get('date', ''))
            with col2:
                st.markdown(f"**{log.get('title', '')}**")
                st.caption(f"{log.get('category_name', '')} | {log.get('language_name', '')} | {log.get('duration_minutes', 0)}分")
            with col3:
                st.markdown(f"+{log.get('points', 0)}pt")
    else:
        st.info("まだ記録がありません")


def show_learning_summary(logs):
    """学習サマリー"""
    
    st.markdown("### 📊 学習サマリー")
    
    if not logs:
        st.info("まだ学習記録がありません。「➕ 学習を記録」から記録を始めましょう！")
        return
    
    period = st.radio(
        "期間",
        ["week", "month", "semester", "all"],
        format_func=lambda x: {"week": "今週", "month": "今月", "semester": "今学期", "all": "全期間"}[x],
        horizontal=True
    )
    
    filtered_logs = filter_logs_by_period(logs, period)
    
    st.markdown("---")
    
    total_minutes = sum(log.get('duration_minutes', 0) for log in filtered_logs)
    total_points = sum(log.get('points', 0) for log in filtered_logs)
    total_days = len(set(log.get('date', '') for log in filtered_logs if log.get('date')))
    
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
        cat = log.get('category', 'other')
        if cat not in category_stats:
            category_stats[cat] = {'minutes': 0, 'points': 0, 'count': 0}
        category_stats[cat]['minutes'] += log.get('duration_minutes', 0)
        category_stats[cat]['points'] += log.get('points', 0)
        category_stats[cat]['count'] += 1
    
    for cat, stats in sorted(category_stats.items(), key=lambda x: x[1]['minutes'], reverse=True):
        col1, col2, col3 = st.columns([3, 1, 1])
        with col1:
            st.markdown(f"**{ACTIVITY_CATEGORIES.get(cat, {}).get('name', cat)}**")
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
        lang = log.get('language', 'english')
        if lang not in language_stats:
            language_stats[lang] = {"minutes": 0, "count": 0}
        language_stats[lang]['minutes'] += log.get('duration_minutes', 0)
        language_stats[lang]['count'] += 1
    
    for lang, stats in sorted(language_stats.items(), key=lambda x: x[1]['minutes'], reverse=True):
        col1, col2 = st.columns([3, 1])
        with col1:
            st.markdown(f"**{LANGUAGES.get(lang, lang)}**")
            st.progress(stats['minutes'] / max(total_minutes, 1))
        with col2:
            hours = stats['minutes'] // 60
            mins = stats['minutes'] % 60
            st.caption(f"{hours}h {mins}m")


def show_learning_history(logs, user_id):
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
        filtered = [l for l in filtered if l.get('category') == cat_filter]
    if lang_filter != "all":
        filtered = [l for l in filtered if l.get('language') == lang_filter]
    if status_filter != "all":
        filtered = [l for l in filtered if l.get('status', 'pending') == status_filter]
    
    st.markdown("---")
    st.caption(f"{len(filtered)}件")
    
    for log in filtered:
        with st.expander(f"📌 {log.get('date', '')} - {log.get('title', '')} (+{log.get('points', 0)}pt)"):
            col1, col2 = st.columns([3, 1])
            
            with col1:
                st.markdown(f"**{log.get('title', '')}**")
                st.markdown(f"- カテゴリ: {log.get('category_name', '')}")
                st.markdown(f"- 言語: {log.get('language_name', '')}")
                st.markdown(f"- 時間: {log.get('duration_minutes', 0)}分")
                
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
                
                st.metric("ポイント", f"+{log.get('points', 0)}")
            
            # 削除ボタン
            log_id = log.get('id', '')
            if log_id and st.button("🗑️ 削除", key=f"delete_{log_id}"):
                try:
                    from utils.database import delete_learning_log
                    delete_learning_log(log_id)
                    _refresh_logs()
                except Exception:
                    cache_key = f'_learning_logs_{user_id}'
                    if cache_key in st.session_state:
                        st.session_state[cache_key] = [
                            l for l in st.session_state[cache_key] if l.get('id') != log_id
                        ]
                st.success("削除しました")
                st.rerun()


def show_points_and_grades(logs):
    """ポイントと成績"""
    
    st.markdown("### 🏆 ポイント・成績への反映")
    
    total_points = sum(log.get('points', 0) for log in logs)
    approved_points = sum(log.get('points', 0) for log in logs if log.get('status') == 'approved')
    pending_points = sum(log.get('points', 0) for log in logs if log.get('status', 'pending') == 'pending')
    
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("総獲得ポイント", f"{total_points}pt")
    with col2:
        st.metric("承認済みポイント", f"{approved_points}pt", help="成績に反映されるポイント")
    with col3:
        st.metric("確認待ち", f"{pending_points}pt")
    
    st.markdown("---")
    
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
    
    if total_points >= 300:
        rank, bonus = "S", 10
    elif total_points >= 200:
        rank, bonus = "A", 6
    elif total_points >= 100:
        rank, bonus = "B", 4
    elif total_points >= 50:
        rank, bonus = "C", 2
    else:
        rank, bonus = "D", 0
    
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
        if today.month >= 4 and today.month < 10:
            start_date = today.replace(month=4, day=1)
        else:
            if today.month >= 10:
                start_date = today.replace(month=10, day=1)
            else:
                start_date = today.replace(year=today.year-1, month=10, day=1)
    else:
        return logs
    
    filtered = []
    for log in logs:
        date_str = log.get('date', '')
        if date_str:
            try:
                log_date = datetime.strptime(date_str[:10], "%Y-%m-%d").date()
                if log_date >= start_date:
                    filtered.append(log)
            except (ValueError, TypeError):
                pass
    return filtered
