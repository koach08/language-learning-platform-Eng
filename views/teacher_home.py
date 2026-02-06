import streamlit as st
from utils.auth import get_current_user, require_auth

# デフォルトクラス
DEFAULT_CLASSES = {
    "english_specific_a": {
        "name": "英語特定技能演習A（発信）",
        "term": "2025前期",
        "code": "ESA2025A",
        "modules": {
            "speaking": True,
            "writing": True,
            "vocabulary": True,
            "reading": False,
            "listening": False,
            "test_prep": False
        }
    },
    "english_specific_b": {
        "name": "英語特定技能演習B（受信）",
        "term": "2025前期",
        "code": "ESB2025B",
        "modules": {
            "speaking": False,
            "writing": False,
            "vocabulary": True,
            "reading": True,
            "listening": True,
            "test_prep": False
        }
    },
    "english_1_a": {
        "name": "英語I Aクラス",
        "term": "2025前期",
        "code": "ENG1A2025",
        "modules": {
            "speaking": True,
            "writing": True,
            "vocabulary": True,
            "reading": True,
            "listening": True,
            "test_prep": False
        }
    },
    "english_seminar": {
        "name": "英語演習",
        "term": "2025前期",
        "code": "ENGSEM2025",
        "modules": {
            "speaking": True,
            "writing": True,
            "vocabulary": True,
            "reading": True,
            "listening": True,
            "test_prep": False
        }
    }
}

@require_auth
def show():
    user = get_current_user()
    
    # 教員でない場合はリダイレクト
    if user['role'] != 'teacher':
        st.session_state['current_view'] = 'student_home'
        st.rerun()
        return
    
    st.markdown(f"## 👨‍🏫 教員ダッシュボード")
    st.markdown(f"ようこそ、{user['name']} 先生")
    
    # 初期化
    if 'teacher_classes' not in st.session_state or not st.session_state.teacher_classes:
        st.session_state.teacher_classes = DEFAULT_CLASSES.copy()
    
    if 'class_students' not in st.session_state:
        st.session_state.class_students = {}
    
    # アラート通知バー
    show_alert_summary_bar()
    
    st.markdown("---")
    
    # クラス選択
    classes = st.session_state.teacher_classes
    
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
    
    st.markdown("---")
    
    # クラスサマリー
    show_class_summary(selected_class_key, selected_class)
    
    # クイックアクション
    show_quick_actions(selected_class_key)
    
    # モジュール設定（オン/オフ）
    show_module_settings(selected_class_key, selected_class)
    
    # 教員ツール（アラート、フィードバック、成績ツール）
    show_teacher_tools_section()
    
    # 最近の活動
    show_recent_class_activity(selected_class_key)


def show_alert_summary_bar():
    """アラート通知バー（ページ上部）"""
    try:
        from utils.teacher_tools import get_student_alerts
        alerts = get_student_alerts()
        
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
    with col2:
        if st.button("📋 コードをコピー"):
            st.success("コピーしました！")
    
    # 学生数取得
    class_students = st.session_state.class_students.get(class_key, [])
    student_count = len(class_students)
    
    # 統計
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
    
    # 有効モジュール表示
    modules = class_data.get('modules', {})
    enabled_modules = [k for k, v in modules.items() if v]
    
    if enabled_modules:
        module_names = {
            "speaking": "🗣️ Speaking",
            "writing": "✍️ Writing",
            "vocabulary": "📚 Vocabulary",
            "reading": "📖 Reading",
            "listening": "🎧 Listening",
            "test_prep": "📝 検定対策"
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
    """モジュール設定（オン/オフ）"""
    
    st.markdown("---")
    st.markdown("### 🎛️ モジュール設定")
    st.caption("このクラスで学生が使用できるモジュールを設定します")
    
    # 現在のモジュール設定を取得
    current_modules = class_data.get('modules', {
        "speaking": True,
        "writing": True,
        "vocabulary": True,
        "reading": True,
        "listening": True,
        "test_prep": False
    })
    
    module_info = {
        "speaking": {"name": "🗣️ Speaking", "desc": "音読・会話・スピーチ練習"},
        "writing": {"name": "✍️ Writing", "desc": "エッセイ・メール作成、AI添削"},
        "vocabulary": {"name": "📚 Vocabulary", "desc": "単語学習、フラッシュカード"},
        "reading": {"name": "📖 Reading", "desc": "読解練習、速読"},
        "listening": {"name": "🎧 Listening", "desc": "YouTube学習、ディクテーション"},
        "test_prep": {"name": "📝 検定対策", "desc": "TOEFL/TOEIC対策"},
    }
    
    # 2列で表示
    col1, col2 = st.columns(2)
    
    updated_modules = {}
    module_keys = list(module_info.keys())
    
    for i, mod_key in enumerate(module_keys):
        info = module_info[mod_key]
        current_state = current_modules.get(mod_key, False)
        
        with col1 if i % 2 == 0 else col2:
            new_state = st.toggle(
                f"{info['name']}",
                value=current_state,
                key=f"module_toggle_{class_key}_{mod_key}",
                help=info['desc']
            )
            updated_modules[mod_key] = new_state
            
            if new_state:
                st.caption(f"✅ {info['desc']}")
            else:
                st.caption(f"⬜ オフ")
    
    # 変更があれば保存
    if updated_modules != current_modules:
        st.session_state.teacher_classes[class_key]['modules'] = updated_modules
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
    
    class_students = st.session_state.class_students.get(class_key, [])
    
    if not class_students:
        st.info("まだ学生が登録されていません。学生が登録すると、ここに活動状況が表示されます。")
        
        st.markdown("**学生の登録方法:**")
        st.markdown(f"1. 学生にクラスコードを共有: `{st.session_state.teacher_classes[class_key].get('code', 'N/A')}`")
        st.markdown("2. 学生は新規登録時にこのコードを入力")
        st.markdown("3. 自動的にこのクラスに登録されます")
        return
    
    # 最近の活動（デモデータ）
    activities = [
        {"time": "10分前", "student": "田中太郎", "action": "音読練習を完了", "score": 78},
        {"time": "30分前", "student": "鈴木花子", "action": "単語クイズを完了", "score": 85},
        {"time": "1時間前", "student": "佐藤一郎", "action": "エッセイを提出", "score": 72},
        {"time": "2時間前", "student": "山田美咲", "action": "リスニング練習を完了", "score": 80},
    ]
    
    for act in activities[:5]:
        col1, col2, col3 = st.columns([1, 3, 1])
        with col1:
            st.caption(act['time'])
        with col2:
            st.markdown(f"**{act['student']}** が {act['action']}")
        with col3:
            st.markdown(f"{act['score']}点")
    
    if st.button("すべての活動を見る"):
        st.session_state['current_view'] = 'teacher_dashboard'
        st.rerun()
    
    st.markdown("---")
    
    # 要注意学生
    at_risk = [s for s in class_students if s.get('days_since_active', 0) > 7 or s.get('avg_score', 100) < 50]
    
    if at_risk:
        st.markdown("### ⚠️ 要注意学生")
        for s in at_risk[:3]:
            issues = []
            if s.get('days_since_active', 0) > 7:
                issues.append(f"{s.get('days_since_active', 0)}日間活動なし")
            if s.get('avg_score', 100) < 50:
                issues.append(f"平均スコア {s.get('avg_score', 0):.1f}点")
            
            st.warning(f"**{s['name']}** ({s.get('student_id', '')}) - {', '.join(issues)}")
        
        if len(at_risk) > 3:
            st.caption(f"他 {len(at_risk) - 3}名")
