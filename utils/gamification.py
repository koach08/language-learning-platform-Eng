import streamlit as st
from datetime import datetime, timedelta


# ===== XPポイント設定 =====
XP_REWARDS = {
    'reading_complete': 20,
    'reading_quiz_perfect': 50,
    'reading_quiz_pass': 30,
    'speaking_practice': 25,
    'speaking_submit': 40,
    'speaking_score_90': 50,
    'writing_submit': 40,
    'vocabulary_review': 10,
    'vocabulary_quiz_perfect': 30,
    'listening_complete': 20,
    'daily_login': 5,
    'streak_bonus_7': 50,
    'streak_bonus_30': 200,
}

# ===== レベル設定 =====
LEVELS = [
    {"level": 1, "name": "Beginner", "xp_required": 0, "icon": "🌱"},
    {"level": 2, "name": "Starter", "xp_required": 100, "icon": "🌿"},
    {"level": 3, "name": "Learner", "xp_required": 300, "icon": "🌳"},
    {"level": 4, "name": "Explorer", "xp_required": 600, "icon": "⭐"},
    {"level": 5, "name": "Practitioner", "xp_required": 1000, "icon": "🔥"},
    {"level": 6, "name": "Achiever", "xp_required": 1500, "icon": "💎"},
    {"level": 7, "name": "Expert", "xp_required": 2200, "icon": "🏆"},
    {"level": 8, "name": "Master", "xp_required": 3000, "icon": "👑"},
    {"level": 9, "name": "Champion", "xp_required": 4000, "icon": "🎯"},
    {"level": 10, "name": "Legend", "xp_required": 5500, "icon": "🌟"},
]

# ===== バッジ定義 =====
BADGES = {
    'first_login': {
        'name': 'Welcome!',
        'description': '初めてのログイン',
        'icon': '👋',
        'condition': lambda stats: True
    },
    'first_reading': {
        'name': 'Bookworm Begins',
        'description': '初めての記事読了',
        'icon': '📖',
        'condition': lambda stats: stats.get('readings_completed', 0) >= 1
    },
    'reading_10': {
        'name': 'Avid Reader',
        'description': '10記事読了',
        'icon': '📚',
        'condition': lambda stats: stats.get('readings_completed', 0) >= 10
    },
    'reading_50': {
        'name': 'Bibliophile',
        'description': '50記事読了',
        'icon': '🏛️',
        'condition': lambda stats: stats.get('readings_completed', 0) >= 50
    },
    'first_speaking': {
        'name': 'Voice Activated',
        'description': '初めてのスピーキング練習',
        'icon': '🎤',
        'condition': lambda stats: stats.get('speaking_practices', 0) >= 1
    },
    'speaking_score_90': {
        'name': 'Eloquent Speaker',
        'description': 'スピーキングで90点以上',
        'icon': '🗣️',
        'condition': lambda stats: stats.get('speaking_best_score', 0) >= 90
    },
    'first_writing': {
        'name': 'Pen to Paper',
        'description': '初めてのライティング提出',
        'icon': '✍️',
        'condition': lambda stats: stats.get('writings_submitted', 0) >= 1
    },
    'vocab_100': {
        'name': 'Word Collector',
        'description': '100語学習',
        'icon': '📝',
        'condition': lambda stats: stats.get('words_learned', 0) >= 100
    },
    'vocab_500': {
        'name': 'Lexicon Builder',
        'description': '500語学習',
        'icon': '📕',
        'condition': lambda stats: stats.get('words_learned', 0) >= 500
    },
    'streak_7': {
        'name': 'Week Warrior',
        'description': '7日連続学習',
        'icon': '🔥',
        'condition': lambda stats: stats.get('max_streak', 0) >= 7
    },
    'streak_30': {
        'name': 'Monthly Master',
        'description': '30日連続学習',
        'icon': '💪',
        'condition': lambda stats: stats.get('max_streak', 0) >= 30
    },
    'quiz_perfect_5': {
        'name': 'Perfect Five',
        'description': 'クイズ満点5回',
        'icon': '💯',
        'condition': lambda stats: stats.get('perfect_quizzes', 0) >= 5
    },
    'xp_1000': {
        'name': 'Milestone',
        'description': '1000 XP達成',
        'icon': '🎉',
        'condition': lambda stats: stats.get('total_xp', 0) >= 1000
    },
    'all_modules': {
        'name': 'Well-Rounded',
        'description': '全モジュールを使用',
        'icon': '🌐',
        'condition': lambda stats: stats.get('modules_used', 0) >= 5
    },
}

# ===== 週間チャレンジ =====
WEEKLY_CHALLENGES = [
    {"id": "read_3", "name": "📖 3記事読む", "target": 3, "stat_key": "weekly_readings", "xp_reward": 30},
    {"id": "speak_3", "name": "🎤 3回スピーキング", "target": 3, "stat_key": "weekly_speaking", "xp_reward": 30},
    {"id": "vocab_20", "name": "📝 20語学習", "target": 20, "stat_key": "weekly_vocab", "xp_reward": 25},
    {"id": "quiz_perfect", "name": "💯 クイズ満点1回", "target": 1, "stat_key": "weekly_perfect_quizzes", "xp_reward": 40},
    {"id": "daily_5", "name": "🔥 5日連続ログイン", "target": 5, "stat_key": "weekly_login_days", "xp_reward": 35},
]


# ===== ユーティリティ関数 =====

def get_user_key():
    """現在のユーザーキーを取得"""
    user = st.session_state.get('user')
    if user:
        return user.get('student_id') or user.get('email') or 'unknown'
    return 'unknown'


def get_gamification_data():
    """ゲーミフィケーションデータを取得"""
    user_key = get_user_key()
    key = f'gamification_{user_key}'
    
    if key not in st.session_state:
        st.session_state[key] = {
            'total_xp': 0,
            'xp_history': [],
            'badges_earned': ['first_login'],
            'current_streak': 0,
            'max_streak': 0,
            'last_active_date': None,
            'login_dates': [],
            'weekly_goals': {},
            'stats': {
                'readings_completed': 0,
                'speaking_practices': 0,
                'speaking_best_score': 0,
                'writings_submitted': 0,
                'words_learned': 0,
                'perfect_quizzes': 0,
                'modules_used': 0,
                'total_study_minutes': 0,
                'weekly_readings': 0,
                'weekly_speaking': 0,
                'weekly_vocab': 0,
                'weekly_perfect_quizzes': 0,
                'weekly_login_days': 0,
            },
            'weekly_challenge_ids': [],
            'weekly_reset_date': None,
        }
    
    return st.session_state[key]


def award_xp(action, extra_xp=0):
    """XPを付与"""
    data = get_gamification_data()
    base_xp = XP_REWARDS.get(action, 0)
    total = base_xp + extra_xp
    
    if total > 0:
        data['total_xp'] += total
        data['xp_history'].append({
            'action': action,
            'xp': total,
            'timestamp': datetime.now().strftime("%Y-%m-%d %H:%M")
        })
        
        # バッジチェック
        check_badges(data)
        
        return total
    return 0


def update_streak():
    """ストリークを更新"""
    data = get_gamification_data()
    today = datetime.now().strftime("%Y-%m-%d")
    
    if data['last_active_date'] == today:
        return  # 今日は既に更新済み
    
    yesterday = (datetime.now() - timedelta(days=1)).strftime("%Y-%m-%d")
    
    if data['last_active_date'] == yesterday:
        data['current_streak'] += 1
    elif data['last_active_date'] is None:
        data['current_streak'] = 1
    else:
        data['current_streak'] = 1  # リセット
    
    data['last_active_date'] = today
    
    if today not in data['login_dates']:
        data['login_dates'].append(today)
        data['stats']['weekly_login_days'] = len([
            d for d in data['login_dates']
            if datetime.strptime(d, "%Y-%m-%d") >= datetime.now() - timedelta(days=7)
        ])
    
    # 最大ストリーク更新
    if data['current_streak'] > data['max_streak']:
        data['max_streak'] = data['current_streak']
    
    # ストリークボーナス
    if data['current_streak'] == 7:
        award_xp('streak_bonus_7')
    elif data['current_streak'] == 30:
        award_xp('streak_bonus_30')
    
    # デイリーログインXP
    award_xp('daily_login')
    
    # バッジチェック
    check_badges(data)


def update_stat(stat_key, value=1, mode='increment'):
    """統計を更新"""
    data = get_gamification_data()
    
    if mode == 'increment':
        data['stats'][stat_key] = data['stats'].get(stat_key, 0) + value
    elif mode == 'max':
        data['stats'][stat_key] = max(data['stats'].get(stat_key, 0), value)
    elif mode == 'set':
        data['stats'][stat_key] = value
    
    check_badges(data)


def check_badges(data):
    """バッジ条件をチェック"""
    stats = data['stats']
    stats['total_xp'] = data['total_xp']
    stats['max_streak'] = data['max_streak']
    
    for badge_id, badge in BADGES.items():
        if badge_id not in data['badges_earned']:
            try:
                if badge['condition'](stats):
                    data['badges_earned'].append(badge_id)
            except Exception:
                pass


def get_current_level(total_xp):
    """XPからレベルを計算"""
    current = LEVELS[0]
    for level_data in LEVELS:
        if total_xp >= level_data['xp_required']:
            current = level_data
        else:
            break
    return current


def get_next_level(total_xp):
    """次のレベル情報を取得"""
    for level_data in LEVELS:
        if total_xp < level_data['xp_required']:
            return level_data
    return None


def get_xp_progress(total_xp):
    """現在のレベル内の進捗率"""
    current = get_current_level(total_xp)
    next_level = get_next_level(total_xp)
    
    if next_level is None:
        return 1.0
    
    xp_in_level = total_xp - current['xp_required']
    xp_needed = next_level['xp_required'] - current['xp_required']
    
    return xp_in_level / xp_needed if xp_needed > 0 else 1.0


def get_weekly_challenges():
    """今週のチャレンジを取得（3つランダム選択）"""
    import random
    data = get_gamification_data()
    today = datetime.now().strftime("%Y-%m-%d")
    
    # 月曜にリセット
    monday = (datetime.now() - timedelta(days=datetime.now().weekday())).strftime("%Y-%m-%d")
    
    if data.get('weekly_reset_date') != monday:
        data['weekly_reset_date'] = monday
        data['weekly_challenge_ids'] = random.sample(
            [c['id'] for c in WEEKLY_CHALLENGES],
            min(3, len(WEEKLY_CHALLENGES))
        )
        # 週間統計リセット
        for key in ['weekly_readings', 'weekly_speaking', 'weekly_vocab', 'weekly_perfect_quizzes', 'weekly_login_days']:
            data['stats'][key] = 0
    
    challenges = []
    for c in WEEKLY_CHALLENGES:
        if c['id'] in data.get('weekly_challenge_ids', []):
            current = data['stats'].get(c['stat_key'], 0)
            challenges.append({
                **c,
                'current': current,
                'completed': current >= c['target']
            })
    
    return challenges


# ===== UI表示関数 =====

def show_xp_notification(xp_amount, action_name=""):
    """XP獲得通知"""
    if xp_amount > 0:
        st.toast(f"✨ +{xp_amount} XP {'- ' + action_name if action_name else ''}")


def show_gamification_sidebar():
    """サイドバーにゲーミフィケーション情報を表示"""
    data = get_gamification_data()
    
    # ストリーク更新
    update_streak()
    
    total_xp = data['total_xp']
    current_level = get_current_level(total_xp)
    progress = get_xp_progress(total_xp)
    next_level = get_next_level(total_xp)
    
    st.markdown("---")
    st.markdown("#### 🎮 学習ステータス")
    
    # レベル・XP
    st.markdown(f"**{current_level['icon']} Lv.{current_level['level']} {current_level['name']}**")
    st.progress(progress)
    if next_level:
        st.caption(f"{total_xp} / {next_level['xp_required']} XP")
    else:
        st.caption(f"🌟 {total_xp} XP - MAX LEVEL!")
    
    # ストリーク
    streak = data['current_streak']
    if streak > 0:
        st.markdown(f"🔥 **{streak}日連続学習中！**")
    
    # バッジ数
    badge_count = len(data['badges_earned'])
    total_badges = len(BADGES)
    st.caption(f"🏅 バッジ: {badge_count}/{total_badges}")


def show_gamification_dashboard():
    """ゲーミフィケーションダッシュボード（フル表示）"""
    data = get_gamification_data()
    update_streak()
    
    total_xp = data['total_xp']
    current_level = get_current_level(total_xp)
    progress = get_xp_progress(total_xp)
    next_level = get_next_level(total_xp)
    
    # ===== ヘッダー =====
    st.markdown("### 🎮 学習ステータス / Learning Status")
    
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric(
            f"{current_level['icon']} レベル",
            f"Lv.{current_level['level']}",
            current_level['name']
        )
    with col2:
        st.metric("⭐ 総XP", f"{total_xp:,}")
    with col3:
        st.metric("🔥 連続学習", f"{data['current_streak']}日")
    with col4:
        st.metric("🏅 バッジ", f"{len(data['badges_earned'])}/{len(BADGES)}")
    
    # 進捗バー
    if next_level:
        st.progress(progress)
        st.caption(f"次のレベルまで: {next_level['xp_required'] - total_xp} XP")
    else:
        st.progress(1.0)
        st.caption("🌟 最高レベル達成！")
    
    st.markdown("---")
    
    # ===== 週間チャレンジ =====
    st.markdown("### 🎯 今週のチャレンジ / Weekly Challenges")
    
    challenges = get_weekly_challenges()
    cols = st.columns(len(challenges)) if challenges else []
    
    for i, challenge in enumerate(challenges):
        with cols[i]:
            if challenge['completed']:
                st.success(f"✅ {challenge['name']}")
                st.caption(f"+{challenge['xp_reward']} XP 獲得済み")
            else:
                st.info(f"🎯 {challenge['name']}")
                progress_val = min(challenge['current'] / challenge['target'], 1.0)
                st.progress(progress_val)
                st.caption(f"{challenge['current']}/{challenge['target']} (+{challenge['xp_reward']} XP)")
    
    st.markdown("---")
    
    # ===== バッジ一覧 =====
    st.markdown("### 🏅 バッジ / Badges")
    
    earned = data['badges_earned']
    
    cols = st.columns(5)
    for i, (badge_id, badge) in enumerate(BADGES.items()):
        with cols[i % 5]:
            if badge_id in earned:
                st.markdown(f"### {badge['icon']}")
                st.caption(f"**{badge['name']}**")
                st.caption(badge['description'])
            else:
                st.markdown("### 🔒")
                st.caption(f"**???**")
                st.caption("未獲得")
    
    st.markdown("---")
    
    # ===== 最近のXP履歴 =====
    st.markdown("### 📊 最近のXP履歴")
    
    history = data.get('xp_history', [])[-10:]
    
    if history:
        for entry in reversed(history):
            st.caption(f"✨ +{entry['xp']} XP - {entry['action']} ({entry['timestamp']})")
    else:
        st.info("まだXP履歴がありません。学習を始めましょう！")
