import streamlit as st
from utils.auth import get_current_user, require_auth
import random
from datetime import datetime, timedelta

@require_auth
def show():
    """学生ポートフォリオ（電子カルテ）"""
    
    user = get_current_user()
    
    # 教員が学生を選択して見る場合
    if user['role'] == 'teacher':
        if 'selected_student' not in st.session_state or not st.session_state.selected_student:
            st.warning("学生を選択してください")
            if st.button("← 学生管理に戻る"):
                st.session_state['current_view'] = 'student_management'
                st.rerun()
            return
        
        student = st.session_state.selected_student
        show_portfolio_teacher_view(student)
    else:
        # 学生が自分のポートフォリオを見る場合
        show_portfolio_student_view(user)


def show_portfolio_teacher_view(student):
    """教員用ポートフォリオビュー（全て見える）"""
    
    col1, col2 = st.columns([1, 4])
    with col1:
        if st.button("← 戻る"):
            st.session_state['current_view'] = 'student_management'
            st.rerun()
    with col2:
        st.markdown(f"## 📋 学生ポートフォリオ: {student['name']}")
    
    st.caption(f"学籍番号: {student['student_id']} | 最終活動: {student['days_since_active']}日前")
    
    st.markdown("---")
    
    # タブ構成
    tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs([
        "📊 サマリー",
        "📝 学習履歴",
        "💬 フィードバック",
        "📧 やり取り",
        "📈 成長記録",
        "⚙️ 設定"
    ])
    
    with tab1:
        show_portfolio_summary(student)
    with tab2:
        show_learning_history_detail(student)
    with tab3:
        show_feedback_history(student)
    with tab4:
        show_messaging(student)
    with tab5:
        show_growth_record(student)
    with tab6:
        show_portfolio_settings(student)


def show_portfolio_summary(student):
    """ポートフォリオサマリー"""
    
    st.markdown("### 📊 学習サマリー")
    
    # 基本情報
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("現在レベル", "B1", "↑ A2+から")
    with col2:
        st.metric("総学習時間", "32.5時間")
    with col3:
        st.metric("総練習回数", f"{student['practice_count']}回")
    with col4:
        st.metric("平均スコア", f"{student['avg_score']:.1f}点", "+5.2")
    
    st.markdown("---")
    
    # 今週のハイライト
    st.markdown("### 📅 今週のハイライト")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("**よく取り組んだ活動:**")
        activities = [
            {"activity": "音読練習", "count": 8, "time": "45分"},
            {"activity": "YouTube学習", "count": 3, "time": "1.5時間"},
            {"activity": "単語学習", "count": 12, "time": "30分"},
        ]
        for a in activities:
            st.markdown(f"- {a['activity']}: {a['count']}回 ({a['time']})")
    
    with col2:
        st.markdown("**今週の成果:**")
        st.markdown("- 🎉 発音スコア +3.2点")
        st.markdown("- 📚 新規単語 45語習得")
        st.markdown("- ✅ 課題3 提出完了")
    
    st.markdown("---")
    
    # 最近の活動タイムライン
    st.markdown("### 🕐 最近の活動")
    
    recent_activities = generate_recent_activities()
    
    for activity in recent_activities[:10]:
        col1, col2, col3 = st.columns([1, 3, 1])
        with col1:
            st.caption(activity['datetime'])
        with col2:
            st.markdown(f"**{activity['module']}** - {activity['activity']}")
            if activity.get('detail'):
                st.caption(activity['detail'])
        with col3:
            if activity.get('score'):
                st.markdown(f"{activity['score']}点")


def show_learning_history_detail(student):
    """詳細な学習履歴（使用素材含む）"""
    
    st.markdown("### 📝 学習履歴（詳細）")
    
    # フィルタ
    col1, col2, col3 = st.columns(3)
    with col1:
        module_filter = st.selectbox(
            "モジュール",
            ["全て", "Speaking", "Writing", "Vocabulary", "Reading", "Listening"]
        )
    with col2:
        date_filter = st.selectbox(
            "期間",
            ["今週", "今月", "過去3ヶ月", "全期間"]
        )
    with col3:
        if st.button("📥 CSV出力"):
            st.success("CSVをダウンロードしました（※デモ）")
    
    st.markdown("---")
    
    # 詳細履歴
    history = generate_detailed_history()
    
    for record in history:
        with st.expander(f"📌 {record['datetime']} - {record['module']}: {record['activity']}"):
            col1, col2 = st.columns([2, 1])
            
            with col1:
                st.markdown("**活動詳細:**")
                st.markdown(f"- モジュール: {record['module']}")
                st.markdown(f"- 活動タイプ: {record['activity']}")
                st.markdown(f"- 所要時間: {record['duration']}")
                
                if record.get('material'):
                    st.markdown("---")
                    st.markdown("**使用した素材:**")
                    
                    material = record['material']
                    if material['type'] == 'script':
                        st.markdown(f"📜 **スクリプト:** {material['title']}")
                        with st.expander("スクリプト内容を見る"):
                            st.text(material['content'])
                    
                    elif material['type'] == 'youtube':
                        st.markdown(f"📺 **YouTube:** {material['title']}")
                        st.markdown(f"URL: {material['url']}")
                        st.caption(f"視聴部分: {material.get('watched_range', '全体')}")
                    
                    elif material['type'] == 'article':
                        st.markdown(f"📖 **記事:** {material['title']}")
                        st.caption(f"レベル: {material.get('level', 'B1')} | {material.get('word_count', 200)}語")
                    
                    elif material['type'] == 'essay':
                        st.markdown(f"✍️ **エッセイ:** {material['title']}")
                        with st.expander("提出内容を見る"):
                            st.text(material['content'])
                    
                    elif material['type'] == 'vocabulary':
                        st.markdown(f"📚 **単語リスト:** {material['title']}")
                        st.markdown(f"学習単語数: {material.get('word_count', 10)}語")
            
            with col2:
                st.markdown("**結果:**")
                if record.get('score'):
                    st.metric("スコア", f"{record['score']}点")
                if record.get('accuracy'):
                    st.metric("正答率", f"{record['accuracy']}%")
                if record.get('wpm'):
                    st.metric("WPM", record['wpm'])
            
            # AIフィードバック
            if record.get('ai_feedback'):
                st.markdown("---")
                st.markdown("**AIフィードバック:**")
                st.info(record['ai_feedback'])


def show_feedback_history(student):
    """フィードバック履歴"""
    
    st.markdown("### 💬 フィードバック履歴")
    
    # フィルタ
    col1, col2 = st.columns(2)
    with col1:
        feedback_type = st.selectbox(
            "タイプ",
            ["全て", "発音評価", "ライティング添削", "会話フィードバック", "教員コメント"]
        )
    with col2:
        skill_filter = st.selectbox(
            "スキル",
            ["全て", "発音", "文法", "語彙", "流暢さ", "内容"]
        )
    
    st.markdown("---")
    
    feedbacks = generate_feedback_history()
    
    for fb in feedbacks:
        with st.expander(f"💬 {fb['datetime']} - {fb['type']} ({fb['module']})"):
            st.markdown(f"**活動:** {fb['activity']}")
            
            st.markdown("---")
            st.markdown("**詳細フィードバック:**")
            st.markdown(fb['feedback'])
            
            if fb.get('scores'):
                st.markdown("---")
                st.markdown("**評価スコア:**")
                cols = st.columns(len(fb['scores']))
                for i, (criterion, score) in enumerate(fb['scores'].items()):
                    with cols[i]:
                        st.metric(criterion, f"{score}点")
            
            if fb.get('improvements'):
                st.markdown("---")
                st.markdown("**改善ポイント:**")
                for imp in fb['improvements']:
                    st.markdown(f"- {imp}")
            
            if fb.get('audio_available'):
                col1, col2 = st.columns(2)
                with col1:
                    if st.button("🔊 録音を再生", key=f"play_fb_{fb['datetime']}"):
                        st.info("音声再生（※デモ）")
                with col2:
                    if st.button("📊 詳細分析", key=f"analysis_fb_{fb['datetime']}"):
                        st.info("詳細分析（※デモ）")


def show_messaging(student):
    """教員と学生の個別やり取り"""
    
    st.markdown("### 📧 個別やり取り")
    st.caption("学習に関する質問・相談・アドバイス")
    
    # メッセージ履歴
    messages = [
        {
            "datetime": "2025/05/12 14:30",
            "sender": "student",
            "sender_name": student['name'],
            "content": "先生、th音の練習方法についてもう少し詳しく教えていただけますか？練習しているのですがなかなか改善しません。"
        },
        {
            "datetime": "2025/05/12 16:45",
            "sender": "teacher",
            "sender_name": "山田先生",
            "content": "th音は日本語にない音なので難しいですよね。舌先を上の前歯の裏側に軽く当てて、息を出しながら発音してみてください。\n\n以下の練習を毎日5分やってみましょう：\n1. 「the, this, that」をゆっくり10回\n2. 鏡を見ながら舌の位置を確認\n3. AIの発音評価で確認\n\n1週間後にまた確認しましょう！"
        },
        {
            "datetime": "2025/05/14 10:20",
            "sender": "student",
            "sender_name": student['name'],
            "content": "ありがとうございます！練習を続けています。少し良くなった気がします。"
        },
        {
            "datetime": "2025/05/14 11:00",
            "sender": "teacher",
            "sender_name": "山田先生",
            "content": "いいですね！練習履歴を見ましたが、毎日取り組んでいるのが見えます。スコアも68→72に上がっています。この調子で続けましょう！👍"
        },
    ]
    
    # メッセージ表示
    st.markdown("#### 💬 メッセージ履歴")
    
    for msg in messages:
        if msg['sender'] == 'teacher':
            st.markdown(f"""
            <div style="background-color: #e3f2fd; padding: 10px; border-radius: 10px; margin: 5px 0; margin-left: 20%;">
                <small><b>👨‍🏫 {msg['sender_name']}</b> - {msg['datetime']}</small><br>
                {msg['content'].replace(chr(10), '<br>')}
            </div>
            """, unsafe_allow_html=True)
        else:
            st.markdown(f"""
            <div style="background-color: #f5f5f5; padding: 10px; border-radius: 10px; margin: 5px 0; margin-right: 20%;">
                <small><b>👤 {msg['sender_name']}</b> - {msg['datetime']}</small><br>
                {msg['content'].replace(chr(10), '<br>')}
            </div>
            """, unsafe_allow_html=True)
    
    st.markdown("---")
    
    # 新規メッセージ
    st.markdown("#### ✏️ メッセージを送信")
    
    # クイック返信
    col1, col2, col3 = st.columns(3)
    with col1:
        if st.button("👍 頑張っていますね！"):
            st.success("送信しました")
    with col2:
        if st.button("📚 練習を増やしましょう"):
            st.success("送信しました")
    with col3:
        if st.button("📅 面談しましょう"):
            st.success("送信しました")
    
    new_message = st.text_area("メッセージを入力", placeholder="学生へのアドバイスやフィードバックを入力...")
    
    col1, col2 = st.columns([3, 1])
    with col1:
        attach_option = st.selectbox(
            "添付",
            ["なし", "練習素材を添付", "参考リンクを添付", "課題を添付"]
        )
    with col2:
        if st.button("📤 送信", type="primary"):
            if new_message:
                st.success("メッセージを送信しました！")
            else:
                st.warning("メッセージを入力してください")


def show_growth_record(student):
    """成長記録"""
    
    st.markdown("### 📈 成長記録")
    
    # レベル推移
    st.markdown("#### 🚀 レベル推移")
    
    level_history = [
        {"date": "2025/04/01", "level": "A2", "toefl": "400-420", "note": "学期開始"},
        {"date": "2025/04/15", "level": "A2+", "toefl": "420-440", "note": "基礎固め完了"},
        {"date": "2025/05/01", "level": "B1 (low)", "toefl": "450-470", "note": "発音改善"},
        {"date": "2025/05/15", "level": "B1 (mid)", "toefl": "470-490", "note": "流暢さ向上"},
        {"date": "現在", "level": "B1 (high)", "toefl": "480-500", "note": "語彙力向上中"},
    ]
    
    for lh in level_history:
        col1, col2, col3, col4 = st.columns([1, 1, 1, 2])
        with col1:
            st.markdown(f"**{lh['date']}**")
        with col2:
            st.markdown(f"🎯 {lh['level']}")
        with col3:
            st.caption(f"TOEFL: {lh['toefl']}")
        with col4:
            st.caption(lh['note'])
    
    st.markdown("---")
    
    # スキル別成長
    st.markdown("#### 📊 スキル別成長")
    
    skills = ["発音", "流暢さ", "文法", "語彙", "リスニング", "読解"]
    
    for skill in skills:
        start = random.randint(40, 55)
        current = random.randint(65, 85)
        change = current - start
        
        col1, col2, col3 = st.columns([2, 3, 1])
        with col1:
            st.markdown(f"**{skill}**")
        with col2:
            st.progress(current / 100)
        with col3:
            st.markdown(f"{start} → {current} (+{change})")
    
    st.markdown("---")
    
    # マイルストーン
    st.markdown("#### 🏆 達成したマイルストーン")
    
    milestones = [
        {"date": "2025/04/10", "milestone": "初めての音読練習完了", "badge": "🎤"},
        {"date": "2025/04/20", "milestone": "10日連続練習達成", "badge": "🔥"},
        {"date": "2025/05/01", "milestone": "発音スコア70点突破", "badge": "🎯"},
        {"date": "2025/05/10", "milestone": "100単語マスター", "badge": "📚"},
        {"date": "2025/05/15", "milestone": "初めてのスピーチ提出", "badge": "🎤"},
    ]
    
    for ms in milestones:
        st.markdown(f"{ms['badge']} **{ms['date']}** - {ms['milestone']}")


def show_portfolio_settings(student):
    """ポートフォリオ設定"""
    
    st.markdown("### ⚙️ ポートフォリオ設定")
    
    st.markdown("#### 🔔 通知設定")
    
    col1, col2 = st.columns(2)
    with col1:
        st.checkbox("練習がない日が続いたら通知", value=True)
        st.checkbox("スコアが大きく変動したら通知", value=True)
        st.checkbox("課題締切前にリマインド", value=True)
    with col2:
        st.number_input("練習なし通知の日数", 1, 14, 7)
        st.number_input("スコア変動の閾値（点）", 5, 20, 10)
    
    st.markdown("---")
    
    st.markdown("#### 🎯 個別目標設定")
    
    st.text_input("学期目標", value="TOEFL ITP 500点達成")
    st.text_area("メモ", placeholder="この学生に関するメモ...")
    
    if st.button("💾 設定を保存", type="primary"):
        st.success("設定を保存しました")


def show_portfolio_student_view(user):
    """学生用ポートフォリオビュー"""
    
    st.markdown(f"## 📋 マイポートフォリオ")
    st.caption(f"{user['name']} さんの学習記録")
    
    # 学生用は簡易版（詳細な分析は見れない）
    tab1, tab2, tab3 = st.tabs(["📊 サマリー", "📝 学習履歴", "📧 先生からのメッセージ"])
    
    with tab1:
        st.markdown("### 📊 学習状況")
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("総学習時間", "32.5時間")
        with col2:
            st.metric("練習回数", "45回")
        with col3:
            st.metric("現在レベル", "B1")
    
    with tab2:
        st.markdown("### 📝 最近の学習")
        activities = generate_recent_activities()
        for a in activities[:5]:
            st.markdown(f"- {a['datetime']}: {a['module']} - {a['activity']}")
    
    with tab3:
        st.markdown("### 📧 先生からのメッセージ")
        st.info("th音の練習、効果が出てきています。引き続きがんばりましょう！")


# ===== デモデータ生成関数 =====

def generate_recent_activities():
    """最近の活動を生成"""
    activities = []
    
    activity_types = [
        {"module": "Speaking", "activities": ["音読練習", "会話練習", "スピーチ練習", "シャドーイング"]},
        {"module": "Writing", "activities": ["エッセイ作成", "メール作成", "翻訳チェック"]},
        {"module": "Vocabulary", "activities": ["フラッシュカード", "単語クイズ", "単語検索"]},
        {"module": "Reading", "activities": ["記事読解", "速読練習", "クイズ"]},
        {"module": "Listening", "activities": ["YouTube学習", "ディクテーション", "リスニングクイズ"]},
    ]
    
    for i in range(20):
        days_ago = i // 3
        hour = random.randint(8, 22)
        minute = random.randint(0, 59)
        
        dt = datetime.now() - timedelta(days=days_ago)
        datetime_str = dt.strftime(f"%m/%d {hour:02d}:{minute:02d}")
        
        mod = random.choice(activity_types)
        act = random.choice(mod['activities'])
        
        activities.append({
            "datetime": datetime_str,
            "module": mod['module'],
            "activity": act,
            "score": random.randint(60, 95) if random.random() > 0.3 else None,
            "detail": f"練習時間: {random.randint(3, 15)}分" if random.random() > 0.5 else None
        })
    
    return activities


def generate_detailed_history():
    """詳細な学習履歴を生成"""
    history = []
    
    # Speaking - 音読
    history.append({
        "datetime": "2025/05/15 14:30",
        "module": "Speaking",
        "activity": "音読練習",
        "duration": "8分",
        "score": 78,
        "material": {
            "type": "script",
            "title": "The Power of Habits",
            "content": "Habits shape our lives far more than we realize. Every day, we perform countless actions automatically, from brushing our teeth to checking our phones. These habits, both good and bad, are powerful forces that can either help us achieve our goals or hold us back..."
        },
        "ai_feedback": "発音は全体的に良好です。'th'の音（the, that）で/s/への置換が見られます。語末の子音をより明確に発音しましょう。流暢さは向上しています。"
    })
    
    # Listening - YouTube
    history.append({
        "datetime": "2025/05/15 10:15",
        "module": "Listening",
        "activity": "YouTube学習",
        "duration": "12分",
        "accuracy": 75,
        "material": {
            "type": "youtube",
            "title": "TED Talk: The Power of Introverts",
            "url": "https://www.youtube.com/watch?v=c0KYU2j0TM4",
            "watched_range": "0:00 - 5:30"
        },
        "ai_feedback": "内容理解は良好です。話者のスピードについていけていますが、接続詞（however, therefore）の聞き取りに注意しましょう。"
    })
    
    # Writing
    history.append({
        "datetime": "2025/05/14 20:00",
        "module": "Writing",
        "activity": "エッセイ作成",
        "duration": "25分",
        "score": 72,
        "material": {
            "type": "essay",
            "title": "My Future Career",
            "content": "I want to become a software engineer in the future. There are several reasons why I chose this career path.\n\nFirst, I have been interested in computers since I was a child. I enjoy solving problems and creating things with technology.\n\nSecond, software engineers are in high demand nowadays. Many companies need people who can develop applications and websites.\n\nIn conclusion, I believe becoming a software engineer is the right choice for me."
        },
        "ai_feedback": "構成は明確です。冠詞（a/the）の使い分けに注意してください。'in the future'は文頭より文末がより自然です。具体的な例を追加するとさらに良くなります。"
    })
    
    # Vocabulary
    history.append({
        "datetime": "2025/05/14 15:30",
        "module": "Vocabulary",
        "activity": "フラッシュカード",
        "duration": "10分",
        "accuracy": 85,
        "material": {
            "type": "vocabulary",
            "title": "Academic Word List - Week 5",
            "word_count": 20
        },
        "ai_feedback": "20語中17語正解。'consequently'と'subsequent'の区別を復習しましょう。"
    })
    
    # Reading
    history.append({
        "datetime": "2025/05/13 19:00",
        "module": "Reading",
        "activity": "記事読解",
        "duration": "15分",
        "score": 80,
        "wpm": 145,
        "material": {
            "type": "article",
            "title": "Climate Change and Its Effects",
            "level": "B1",
            "word_count": 250
        },
        "ai_feedback": "読解スピードは目標範囲内です。内容理解も良好。推論問題での正答率向上を目指しましょう。"
    })
    
    return history


def generate_feedback_history():
    """フィードバック履歴を生成"""
    feedbacks = [
        {
            "datetime": "2025/05/15 14:35",
            "type": "発音評価",
            "module": "Speaking",
            "activity": "音読練習: The Power of Habits",
            "feedback": """
**総評:** 全体的に明瞭な発音で、リズムも安定しています。

**良かった点:**
- 文のイントネーションが自然
- 強勢の位置が適切
- ペースが聞きやすい

**改善点:**
- 'th'の音が/s/に置き換わっている箇所あり（the → /zə/）
- 語末の子音がやや弱い（habits → /hæbɪt/）
- 'automatically'の強勢位置を確認
            """,
            "scores": {"発音": 75, "流暢さ": 80, "イントネーション": 78},
            "improvements": ["th音の練習", "語末子音の強調", "多音節語の強勢"],
            "audio_available": True
        },
        {
            "datetime": "2025/05/14 20:30",
            "type": "ライティング添削",
            "module": "Writing",
            "activity": "エッセイ: My Future Career",
            "feedback": """
**総評:** 論理的な構成で、主張が明確です。

**良かった点:**
- 導入・本論・結論の構成が明確
- 理由が具体的
- 接続詞の使用が適切

**改善点:**
- 冠詞の誤用: "a software engineer" → "a software engineer"（OK）, "the future"の位置
- やや短い。具体的なエピソードを追加すると説得力UP
- 結論をより力強く
            """,
            "scores": {"内容": 70, "構成": 80, "文法": 68, "語彙": 72},
            "improvements": ["冠詞の復習", "具体例の追加", "結論の強化"],
            "audio_available": False
        },
    ]
    
    return feedbacks
