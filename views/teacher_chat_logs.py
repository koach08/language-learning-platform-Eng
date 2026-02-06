import streamlit as st
from utils.auth import get_current_user, require_teacher

@require_teacher
def show():
    user = get_current_user()
    
    st.markdown("## 📋 AI対話ログ確認")
    
    if st.button("← ホームに戻る"):
        st.session_state['current_view'] = 'teacher_home'
        st.rerun()
    
    st.markdown("---")
    
    # フィルター
    col1, col2, col3 = st.columns(3)
    with col1:
        course = st.selectbox("コース", ["すべて", "英語I（前期）", "英語II（後期）"])
    with col2:
        date_range = st.selectbox("期間", ["今週", "今月", "すべて"])
    with col3:
        student_filter = st.text_input("学生検索", placeholder="名前または学籍番号")
    
    st.markdown("---")
    
    # サマリー統計
    st.markdown("### 📊 サマリー")
    
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("総セッション数", "156", "+23 今週")
    with col2:
        st.metric("アクティブ学生", "45/50", "90%")
    with col3:
        st.metric("平均スコア", "72/100", "+3")
    with col4:
        st.metric("平均セッション時間", "4.2分")
    
    st.markdown("---")
    
    # 頻出エラーパターン
    st.markdown("### ⚠️ 頻出エラーパターン（クラス全体）")
    
    error_data = [
        {"パターン": "冠詞の欠落（a/the）", "頻度": "78%", "例": "I am student → I am a student"},
        {"パターン": "三単現のs忘れ", "頻度": "65%", "例": "He go → He goes"},
        {"パターン": "不自然な表現（直訳）", "頻度": "52%", "例": "My hobby is → I enjoy"},
        {"パターン": "時制の不一致", "頻度": "41%", "例": "Yesterday I go → Yesterday I went"},
        {"パターン": "前置詞の誤用", "頻度": "38%", "例": "arrive to → arrive at"},
    ]
    
    for error in error_data:
        with st.expander(f"**{error['パターン']}** - {error['頻度']}の学生に見られる"):
            st.markdown(f"例: ❌ `{error['例'].split(' → ')[0]}` → ✅ `{error['例'].split(' → ')[1]}`")
            st.caption("💡 次回の授業で取り上げることを検討してください")
    
    st.markdown("---")
    
    # 学生別ログ
    st.markdown("### 👥 学生別ログ")
    
    # デモデータ
    students = [
        {"name": "山田太郎", "id": "2024001", "sessions": 8, "avg_score": 75, "last_active": "2時間前", "trend": "↑"},
        {"name": "佐藤花子", "id": "2024002", "sessions": 12, "avg_score": 82, "last_active": "1日前", "trend": "→"},
        {"name": "鈴木一郎", "id": "2024003", "sessions": 3, "avg_score": 58, "last_active": "5日前", "trend": "↓"},
        {"name": "田中美咲", "id": "2024004", "sessions": 15, "avg_score": 88, "last_active": "30分前", "trend": "↑"},
        {"name": "高橋健太", "id": "2024005", "sessions": 0, "avg_score": 0, "last_active": "未使用", "trend": "-"},
    ]
    
    for student in students:
        trend_icon = {"↑": "🟢", "→": "🟡", "↓": "🔴", "-": "⚪"}.get(student["trend"], "")
        
        with st.expander(f"{trend_icon} **{student['name']}** ({student['id']}) - {student['sessions']}セッション"):
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("平均スコア", f"{student['avg_score']}/100")
            with col2:
                st.metric("セッション数", student['sessions'])
            with col3:
                st.caption(f"最終アクティブ: {student['last_active']}")
            
            if student['sessions'] > 0:
                st.markdown("**最近のセッション:**")
                
                # セッション詳細（デモ）
                session_demo = {
                    "日時": "2024/2/5 14:30",
                    "シチュエーション": "レストランでの注文",
                    "スコア": "78/100",
                    "発話数": "6回",
                }
                
                st.markdown(f"📅 {session_demo['日時']} | 🎭 {session_demo['シチュエーション']} | 📊 {session_demo['スコア']}")
                
                if st.button(f"詳細を見る", key=f"detail_{student['id']}"):
                    show_session_detail(student['name'])
            else:
                st.warning("まだ対話練習を行っていません")
                st.caption("💡 個別に声かけを検討してください")
    
    st.markdown("---")
    
    # CSV出力
    st.markdown("### 📥 データ出力")
    col1, col2 = st.columns(2)
    with col1:
        if st.button("📊 サマリーCSV出力", use_container_width=True):
            st.success("ダウンロードリンクを生成しました（デモ）")
    with col2:
        if st.button("📋 詳細ログCSV出力", use_container_width=True):
            st.success("ダウンロードリンクを生成しました（デモ）")


def show_session_detail(student_name):
    """セッション詳細を表示"""
    
    st.markdown(f"#### 💬 {student_name}さんの対話詳細")
    
    # デモの会話ログ
    messages = [
        {"role": "AI", "content": "Hi there! Welcome to Ocean View Cafe. Can I get you something to drink?"},
        {"role": "学生", "content": "Yes, I want coffee please."},
        {"role": "AI", "content": "Sure! Would you like that hot or iced?"},
        {"role": "学生", "content": "Hot coffee. And I want see menu."},
        {"role": "AI", "content": "Of course! Here's the menu. Take your time."},
        {"role": "学生", "content": "Thank you. What is recommend?"},
    ]
    
    for msg in messages:
        if msg["role"] == "AI":
            st.markdown(f"🤖 **AI:** {msg['content']}")
        else:
            st.markdown(f"👤 **学生:** {msg['content']}")
    
    st.markdown("---")
    st.markdown("**AIからのフィードバック:**")
    st.info("""
    良かった点：積極的に会話を続けようとしている
    
    改善点：
    - "I want see menu" → "Could I see the menu?" が自然
    - "What is recommend?" → "What do you recommend?" が正しい
    """)
