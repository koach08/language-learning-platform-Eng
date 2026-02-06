import streamlit as st
from utils.auth import get_current_user, require_auth
import random

@require_auth
def show():
    user = get_current_user()
    
    st.markdown("## 👥 学生管理")
    
    if st.button("← 教員ホームに戻る"):
        st.session_state['current_view'] = 'teacher_home'
        st.rerun()
    
    st.markdown("---")
    
    # デモ用学生データ
    if 'demo_students' not in st.session_state:
        from views.teacher_dashboard import generate_demo_students
        st.session_state.demo_students = generate_demo_students(50)
    
    students = st.session_state.demo_students
    
    # 特定の学生が選択されている場合は個別ビュー
    if 'selected_student' in st.session_state and st.session_state.selected_student:
        show_student_detail(st.session_state.selected_student)
        return
    
    # 学生一覧
    show_student_list(students)


def show_student_list(students):
    """学生一覧"""
    
    st.markdown("### 📋 学生一覧")
    
    selected_class = st.session_state.get('selected_class', 'english_specific_a')
    classes = st.session_state.get('teacher_classes', {})
    if selected_class in classes:
        st.info(f"📚 **{classes[selected_class]['name']}** ({len(students)}名)")
    
    col1, col2, col3 = st.columns(3)
    with col1:
        search = st.text_input("🔍 検索", placeholder="名前または学籍番号")
    with col2:
        sort_by = st.selectbox("ソート", ["学籍番号順", "スコア順（高→低）", "スコア順（低→高）", "練習回数順", "最終活動順"])
    with col3:
        filter_by = st.selectbox("フィルタ", ["全員", "要注意のみ", "今週練習なし", "高得点者"])
    
    filtered = students.copy()
    
    if search:
        filtered = [s for s in filtered if search.lower() in s['name'].lower() or search in s['student_id']]
    
    if filter_by == "要注意のみ":
        filtered = [s for s in filtered if s['days_since_active'] > 7 or s['avg_score'] < 50]
    elif filter_by == "今週練習なし":
        filtered = [s for s in filtered if s['days_since_active'] > 7]
    elif filter_by == "高得点者":
        filtered = [s for s in filtered if s['avg_score'] >= 80]
    
    if sort_by == "スコア順（高→低）":
        filtered.sort(key=lambda x: x['avg_score'], reverse=True)
    elif sort_by == "スコア順（低→高）":
        filtered.sort(key=lambda x: x['avg_score'])
    elif sort_by == "練習回数順":
        filtered.sort(key=lambda x: x['practice_count'], reverse=True)
    elif sort_by == "最終活動順":
        filtered.sort(key=lambda x: x['days_since_active'])
    
    st.markdown("---")
    st.caption(f"{len(filtered)}名表示中")
    
    col1, col2 = st.columns([3, 1])
    with col2:
        if st.button("📥 CSV出力"):
            st.success("CSVをダウンロードしました（※デモ）")
    
    for s in filtered:
        with st.container():
            col1, col2, col3, col4, col5 = st.columns([2, 1, 1, 1, 1])
            
            with col1:
                if s['days_since_active'] > 7 or s['avg_score'] < 50:
                    st.markdown(f"⚠️ **{s['name']}**")
                else:
                    st.markdown(f"**{s['name']}**")
                st.caption(s['student_id'])
            with col2:
                color = "🟢" if s['avg_score'] >= 70 else "🟡" if s['avg_score'] >= 50 else "🔴"
                st.metric("平均", f"{color} {s['avg_score']:.1f}")
            with col3:
                st.metric("練習", f"{s['practice_count']}回")
            with col4:
                if s['days_since_active'] == 0:
                    st.metric("最終活動", "今日")
                else:
                    st.metric("最終活動", f"{s['days_since_active']}日前")
            with col5:
                if st.button("詳細を見る", key=f"detail_{s['student_id']}"):
                    st.session_state.selected_student = s
                    st.rerun()
            
            st.markdown("---")


def show_student_detail(student):
    """学生個別ビュー"""
    
    if st.button("← 学生一覧に戻る"):
        st.session_state.selected_student = None
        st.rerun()
    
    st.markdown("---")
    
    col1, col2 = st.columns([3, 1])
    with col1:
        st.markdown(f"## 👤 {student['name']}")
        st.caption(f"学籍番号: {student['student_id']}")
    with col2:
        if student['days_since_active'] > 7 or student['avg_score'] < 50:
            st.error("⚠️ 要注意")
    
    # タブで詳細を分類
    tab1, tab2, tab3, tab4, tab5 = st.tabs([
        "📊 概要",
        "📈 学習進捗",
        "🎯 弱点分析",
        "📝 課題履歴",
        "💬 コメント"
    ])
    
    with tab1:
        show_student_overview(student)
    with tab2:
        show_learning_progress(student)
    with tab3:
        show_weakness_analysis(student)
    with tab4:
        show_assignment_history(student)
    with tab5:
        show_teacher_comments(student)


def show_student_overview(student):
    """概要タブ"""
    
    st.markdown("### 📊 概要")
    
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("現在のレベル", "CEFR B1")
    with col2:
        st.metric("課題平均", f"{student['avg_score']:.1f}点", "+3.2")
    with col3:
        st.metric("練習回数", f"{student['practice_count']}回")
    with col4:
        st.metric("推定TOEFL ITP", "480-500")
    
    st.markdown("---")
    
    # スキル別サマリー
    st.markdown("### 🎯 スキル別スコア")
    
    skills = {
        "Speaking": {"score": student['pronunciation_score'], "change": +3.2},
        "Writing": {"score": student['grammar_score'], "change": +1.5},
        "Listening": {"score": random.randint(60, 85), "change": +2.0},
        "Reading": {"score": random.randint(65, 90), "change": +1.8},
        "Vocabulary": {"score": random.randint(55, 80), "change": +4.5},
    }
    
    cols = st.columns(5)
    for i, (skill, data) in enumerate(skills.items()):
        with cols[i]:
            color = "🟢" if data['score'] >= 70 else "🟡" if data['score'] >= 50 else "🔴"
            st.metric(skill, f"{color} {data['score']:.0f}", f"+{data['change']:.1f}")
    
    st.markdown("---")
    
    # 今週の活動サマリー
    st.markdown("### 📅 今週の活動")
    
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("練習日数", "4/7日")
    with col2:
        st.metric("総学習時間", "2.5時間")
    with col3:
        st.metric("練習回数", "12回")
    with col4:
        st.metric("目標達成率", "80%")


def show_learning_progress(student):
    """学習進捗タブ"""
    
    st.markdown("### 📈 学習進捗")
    
    # ===== 総合スコア推移 =====
    st.markdown("#### 📊 スコア推移（過去3ヶ月）")
    
    import datetime
    dates = [(datetime.date.today() - datetime.timedelta(days=i*7)).strftime("%m/%d") for i in range(12)][::-1]
    
    base_score = student['avg_score'] - 15
    overall_scores = [min(100, max(20, base_score + i*1.2 + random.randint(-3, 5))) for i in range(12)]
    speaking_scores = [min(100, max(20, base_score + i*1.5 + random.randint(-5, 8))) for i in range(12)]
    writing_scores = [min(100, max(20, base_score - 5 + i*1.0 + random.randint(-3, 5))) for i in range(12)]
    
    chart_data = {
        "日付": dates,
        "総合": overall_scores,
        "Speaking": speaking_scores,
        "Writing": writing_scores,
    }
    st.line_chart(chart_data, x="日付", y=["総合", "Speaking", "Writing"])
    
    st.markdown("---")
    
    # ===== モジュール別進捗 =====
    st.markdown("#### 📚 モジュール別学習進捗")
    
    modules = [
        {
            "name": "🗣️ Speaking",
            "sessions": 25,
            "total_time": "4.5時間",
            "last_used": "今日",
            "score_start": 58,
            "score_now": student['pronunciation_score'],
            "activities": {"音読": 15, "会話": 8, "スピーチ": 2}
        },
        {
            "name": "✍️ Writing",
            "sessions": 18,
            "total_time": "3.2時間",
            "last_used": "2日前",
            "score_start": 52,
            "score_now": student['grammar_score'],
            "activities": {"エッセイ": 5, "メール": 8, "翻訳チェック": 5}
        },
        {
            "name": "📚 Vocabulary",
            "sessions": 32,
            "total_time": "2.8時間",
            "last_used": "昨日",
            "score_start": 45,
            "score_now": 72,
            "activities": {"フラッシュカード": 20, "クイズ": 10, "単語検索": 2}
        },
        {
            "name": "📖 Reading",
            "sessions": 12,
            "total_time": "2.0時間",
            "last_used": "3日前",
            "score_start": 55,
            "score_now": 68,
            "activities": {"記事読解": 8, "クイズ": 4}
        },
        {
            "name": "🎧 Listening",
            "sessions": 15,
            "total_time": "3.5時間",
            "last_used": "1日前",
            "score_start": 50,
            "score_now": 65,
            "activities": {"YouTube": 10, "ディクテーション": 5}
        },
    ]
    
    for mod in modules:
        with st.expander(f"{mod['name']} - {mod['sessions']}回 / {mod['total_time']}"):
            col1, col2, col3 = st.columns(3)
            
            with col1:
                st.markdown("**学習統計**")
                st.markdown(f"- セッション数: {mod['sessions']}回")
                st.markdown(f"- 総学習時間: {mod['total_time']}")
                st.markdown(f"- 最終利用: {mod['last_used']}")
            
            with col2:
                st.markdown("**スコア変化**")
                improvement = mod['score_now'] - mod['score_start']
                st.markdown(f"- 開始時: {mod['score_start']}点")
                st.markdown(f"- 現在: {mod['score_now']}点")
                st.markdown(f"- 向上: **+{improvement}点** 🎉" if improvement > 0 else f"- 変化: {improvement}点")
            
            with col3:
                st.markdown("**活動内訳**")
                for activity, count in mod['activities'].items():
                    st.markdown(f"- {activity}: {count}回")
    
    st.markdown("---")
    
    # ===== 週別学習パターン =====
    st.markdown("#### 📅 週別学習パターン")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("**曜日別学習時間**")
        days = ["月", "火", "水", "木", "金", "土", "日"]
        for day in days:
            time = random.randint(0, 45)
            bar = "█" * (time // 5) + "░" * (9 - time // 5)
            st.markdown(f"{day}: {bar} {time}分")
    
    with col2:
        st.markdown("**時間帯別学習**")
        times = ["朝(6-9)", "午前(9-12)", "午後(12-18)", "夜(18-24)"]
        percentages = [10, 15, 25, 50]
        for t, p in zip(times, percentages):
            st.markdown(f"{t}: {'█' * (p // 10)}{'░' * (10 - p // 10)} {p}%")
    
    st.markdown("---")
    
    # ===== 目標達成状況 =====
    st.markdown("#### 🎯 目標達成状況")
    
    goals = [
        {"goal": "週5日以上練習", "target": 5, "current": 4, "unit": "日"},
        {"goal": "Speaking 10回/週", "target": 10, "current": 8, "unit": "回"},
        {"goal": "単語 50語/週", "target": 50, "current": 42, "unit": "語"},
        {"goal": "リスニング 2時間/週", "target": 120, "current": 95, "unit": "分"},
    ]
    
    for g in goals:
        progress = min(100, g['current'] / g['target'] * 100)
        col1, col2, col3 = st.columns([3, 1, 1])
        with col1:
            st.markdown(f"**{g['goal']}**")
            st.progress(progress / 100)
        with col2:
            st.markdown(f"{g['current']}/{g['target']} {g['unit']}")
        with col3:
            if progress >= 100:
                st.success("達成！")
            elif progress >= 70:
                st.warning("あと少し")
            else:
                st.error("頑張ろう")
    
    st.markdown("---")
    
    # ===== レベル向上グラフ =====
    st.markdown("#### 🚀 レベル向上推移")
    
    st.markdown("""
    | 時期 | 推定レベル | TOEFL ITP相当 | 主な改善点 |
    |------|-----------|--------------|-----------|
    | 4月（開始時） | A2+ | 420-450 | - |
    | 5月 | B1 (low) | 450-470 | 発音の基礎 |
    | 6月 | B1 (mid) | 470-490 | 流暢さ向上 |
    | 現在 | B1 (high) | 480-500 | 語彙力向上 |
    """)
    
    st.info("💡 このペースで続けると、学期末には **B1+ (TOEFL ITP 500-520相当)** に到達見込み")


def show_weakness_analysis(student):
    """弱点分析タブ"""
    
    st.markdown("### 🎯 弱点分析")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("#### 🔴 繰り返し出ている問題")
        weaknesses = [
            {"issue": "\"th\" → /s/ 置換", "frequency": 85, "trend": "横ばい", "module": "Speaking"},
            {"issue": "語末の -ed 発音", "frequency": 60, "trend": "改善中", "module": "Speaking"},
            {"issue": "冠詞の誤用 (a/the)", "frequency": 55, "trend": "横ばい", "module": "Writing"},
            {"issue": "母音挿入 (world→worudo)", "frequency": 45, "trend": "改善中", "module": "Speaking"},
            {"issue": "時制の一致", "frequency": 40, "trend": "悪化", "module": "Writing"},
        ]
        
        for w in weaknesses:
            trend_icon = "→" if w['trend'] == "横ばい" else "↗️" if w['trend'] == "改善中" else "↘️"
            st.markdown(f"**{w['issue']}** ({w['module']})")
            col_a, col_b = st.columns([3, 1])
            with col_a:
                st.progress(w['frequency'] / 100)
            with col_b:
                st.caption(f"{w['frequency']}% {trend_icon}")
    
    with col2:
        st.markdown("#### 🟢 改善が見られる項目")
        improvements = [
            {"issue": "/r/ と /l/ の区別", "before": 50, "after": 75, "module": "Speaking"},
            {"issue": "文末イントネーション", "before": 55, "after": 70, "module": "Speaking"},
            {"issue": "基本語彙の定着", "before": 40, "after": 72, "module": "Vocabulary"},
        ]
        
        for imp in improvements:
            change = imp['after'] - imp['before']
            st.markdown(f"**{imp['issue']}** ({imp['module']})")
            st.markdown(f"  {imp['before']}% → {imp['after']}% (**+{change}%** 🎉)")
    
    st.markdown("---")
    
    st.markdown("#### 💡 AIからの学習アドバイス")
    
    st.info("""
    **この学生への推奨練習：**
    
    1. **th音の練習** - 毎日5分、舌の位置を意識した練習を推奨
       - おすすめ教材: 「the, this, that, think, three」の反復練習
    
    2. **冠詞の復習** - Writing練習時に特に注意
       - 推奨: 週2回のエッセイ添削で冠詞に焦点
    
    3. **語末の -ed** - 過去形の発音パターン（/t/, /d/, /ɪd/）の区別練習
    """)


def show_assignment_history(student):
    """課題履歴タブ"""
    
    st.markdown("### 📝 課題提出履歴")
    
    assignments = [
        {
            "name": "課題1: Self-Introduction",
            "type": "スピーチ",
            "score": 72,
            "date": "2025/04/15",
            "status": "提出済",
            "feedback": "Good introduction! Clear voice. Work on 'th' sounds in 'think' and 'the'.",
            "rubric": {"内容": 75, "発音": 68, "流暢さ": 72, "構成": 73}
        },
        {
            "name": "課題2: Reading Aloud",
            "type": "音読",
            "score": 68,
            "date": "2025/05/01",
            "status": "提出済",
            "feedback": "Fluency improved. Watch word stress on multi-syllable words.",
            "rubric": {"発音": 70, "流暢さ": 65, "イントネーション": 68, "完成度": 69}
        },
        {
            "name": "課題3: Speech (My Hobby)",
            "type": "スピーチ",
            "score": 75,
            "date": "2025/05/15",
            "status": "提出済",
            "feedback": "Great content and enthusiasm! Pronunciation getting better.",
            "rubric": {"内容": 80, "発音": 72, "流暢さ": 75, "構成": 73}
        },
        {
            "name": "課題4: Essay",
            "type": "エッセイ",
            "score": None,
            "date": None,
            "status": "未提出",
            "due": "2025/05/30",
            "feedback": None,
            "rubric": None
        },
    ]
    
    for a in assignments:
        if a['status'] == "提出済":
            with st.expander(f"✅ {a['name']} - **{a['score']}点** ({a['date']})"):
                col1, col2 = st.columns(2)
                
                with col1:
                    st.markdown("**評価詳細:**")
                    for criterion, score in a['rubric'].items():
                        st.markdown(f"- {criterion}: {score}点")
                
                with col2:
                    st.markdown("**AIフィードバック:**")
                    st.markdown(a['feedback'])
                
                col1, col2, col3 = st.columns(3)
                with col1:
                    if st.button("🔊 音声再生", key=f"play_{a['name']}"):
                        st.info("音声再生（※デモ）")
                with col2:
                    if st.button("📊 詳細分析", key=f"analysis_{a['name']}"):
                        st.info("詳細分析（※デモ）")
                with col3:
                    if st.button("📝 再提出を許可", key=f"resubmit_{a['name']}"):
                        st.success("再提出を許可しました（※デモ）")
        else:
            with st.expander(f"⏳ {a['name']} - **未提出** (締切: {a['due']})"):
                st.warning("この課題はまだ提出されていません")
                if st.button("📧 リマインダーを送信", key=f"remind_{a['name']}"):
                    st.success("リマインダーを送信しました（※デモ）")


def show_teacher_comments(student):
    """コメントタブ"""
    
    st.markdown("### 💬 教員コメント")
    
    past_comments = [
        {"date": "2025/05/10", "comment": "th音の練習、効果が出てきています。引き続きがんばりましょう。", "notified": True},
        {"date": "2025/04/20", "comment": "課題提出が遅れがちです。計画的に取り組みましょう。", "notified": True},
        {"date": "2025/04/05", "comment": "初回面談。目標：学期末までにTOEFL ITP 500点。", "notified": False},
    ]
    
    st.markdown("#### 📜 過去のコメント")
    
    for c in past_comments:
        col1, col2 = st.columns([4, 1])
        with col1:
            st.markdown(f"**{c['date']}**")
            st.markdown(c['comment'])
        with col2:
            if c['notified']:
                st.caption("📧 通知済")
            else:
                st.caption("（内部メモ）")
        st.markdown("---")
    
    st.markdown("#### ✏️ 新規コメント")
    
    new_comment = st.text_area("コメントを入力", placeholder="学生へのアドバイスやフィードバックを入力...")
    
    col1, col2 = st.columns(2)
    with col1:
        notify = st.checkbox("学生に通知する", value=True)
    with col2:
        comment_type = st.selectbox("種類", ["フィードバック", "アドバイス", "面談メモ", "その他"])
    
    if st.button("💾 コメントを保存", type="primary"):
        if new_comment:
            st.success("コメントを保存しました！")
            if notify:
                st.info("学生にメール通知を送信しました")
        else:
            st.warning("コメントを入力してください")
