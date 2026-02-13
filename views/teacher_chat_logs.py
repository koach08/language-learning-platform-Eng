import streamlit as st
from utils.auth import get_current_user, require_teacher
from datetime import datetime


@require_teacher
def show():
    user = get_current_user()
    
    st.markdown("## 📋 AI対話ログ確認")
    
    if st.button("← ホームに戻る"):
        st.session_state['current_view'] = 'teacher_home'
        st.rerun()
    
    st.markdown("---")
    
    # コースID取得
    selected_class = st.session_state.get('selected_class')
    classes = st.session_state.get('teacher_classes', {})
    course_id = None
    if selected_class and selected_class in classes:
        course_id = classes[selected_class].get('course_id')
    
    if not course_id:
        st.warning("クラスが選択されていません")
        return
    
    # フィルター
    col1, col2 = st.columns(2)
    with col1:
        date_range = st.selectbox("期間", ["今週", "今月", "すべて"])
    with col2:
        student_filter = st.text_input("学生検索", placeholder="名前または学籍番号")
    
    st.markdown("---")
    
    # DBからチャットセッションサマリーを取得
    summary = _load_chat_summary(course_id)
    
    if not summary or summary['total_sessions'] == 0:
        st.info("まだAI対話セッションがありません。学生がAI対話練習を行うとここに表示されます。")
        return
    
    # サマリー統計
    st.markdown("### 📊 サマリー")
    
    total_students = len(st.session_state.get('class_students', {}).get(selected_class, []))
    if total_students == 0:
        # fallback: summary内の学生数を使う
        total_students = summary['active_students']
    
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("総セッション数", f"{summary['total_sessions']}")
    with col2:
        st.metric("アクティブ学生", f"{summary['active_students']}/{total_students}" if total_students > 0 else f"{summary['active_students']}")
    with col3:
        avg_score = summary['avg_score']
        st.metric("平均スコア", f"{avg_score}/100" if avg_score > 0 else "-")
    with col4:
        st.metric("学生数", f"{summary['active_students']}名")
    
    st.markdown("---")
    
    # 学生別ログ
    st.markdown("### 👥 学生別ログ")
    
    students = summary.get('students', [])
    
    # フィルタリング
    if student_filter:
        filter_lower = student_filter.lower()
        students = [
            s for s in students 
            if filter_lower in s.get('name', '').lower() or student_filter in s.get('id', '')
        ]
    
    if not students:
        st.info("該当する学生が見つかりません")
        return
    
    for student in students:
        trend_icon = {"↑": "🟢", "→": "🟡", "↓": "🔴", "-": "⚪"}.get(student.get("trend", "→"), "🟡")
        
        session_count = student.get('sessions', 0)
        avg = student.get('avg_score', 0)
        
        with st.expander(f"{trend_icon} **{student['name']}** ({student.get('id', '')}) - {session_count}セッション"):
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("平均スコア", f"{avg}/100" if avg > 0 else "-")
            with col2:
                st.metric("セッション数", session_count)
            with col3:
                last_active = student.get('last_active', '')
                if last_active:
                    # ISO format → 表示用に変換
                    try:
                        dt = datetime.fromisoformat(last_active.replace('Z', '+00:00'))
                        display_time = dt.strftime('%m/%d %H:%M')
                    except (ValueError, TypeError):
                        display_time = last_active[:16] if last_active else ''
                    st.caption(f"最終アクティブ: {display_time}")
                else:
                    st.caption("最終アクティブ: -")
            
            if session_count > 0:
                st.markdown("**最近のセッション:**")
                
                recent = student.get('recent_sessions', [])
                for session in recent[:3]:
                    started = session.get('started_at', '')
                    scenario = session.get('scenario') or session.get('situation') or ''
                    s_score = session.get('score') or session.get('total_score') or 0
                    
                    # 日時表示
                    try:
                        dt = datetime.fromisoformat(started.replace('Z', '+00:00'))
                        time_str = dt.strftime('%m/%d %H:%M')
                    except (ValueError, TypeError):
                        time_str = started[:16] if started else ''
                    
                    parts = [f"📅 {time_str}"]
                    if scenario:
                        parts.append(f"🎭 {scenario}")
                    if s_score:
                        parts.append(f"📊 {s_score}/100")
                    
                    st.markdown(" | ".join(parts))
                    
                    # 詳細ボタン
                    session_id = session.get('id', '')
                    if session_id and st.button(f"詳細を見る", key=f"detail_{session_id}"):
                        show_session_detail_from_db(session_id, student['name'])
            else:
                st.warning("まだ対話練習を行っていません")
                st.caption("💡 個別に声かけを検討してください")
    
    st.markdown("---")
    
    # CSV出力
    st.markdown("### 📥 データ出力")
    
    if st.button("📊 サマリーCSV出力", use_container_width=True):
        _export_chat_csv(summary)


def _load_chat_summary(course_id: str) -> dict:
    """DBからチャットセッションサマリーを取得"""
    try:
        from utils.database import get_course_chat_session_summary
        return get_course_chat_session_summary(course_id)
    except Exception as e:
        st.error(f"チャットデータの取得に失敗しました: {e}")
        return {'total_sessions': 0, 'active_students': 0, 'avg_score': 0, 'students': []}


def show_session_detail_from_db(session_id: str, student_name: str):
    """セッション詳細を表示（DB連携）"""
    
    st.markdown(f"#### 💬 {student_name}さんの対話詳細")
    
    try:
        from utils.database import get_supabase_client
        supabase = get_supabase_client()
        
        result = supabase.table('chat_sessions')\
            .select('*')\
            .eq('id', session_id)\
            .execute()
        
        if not result.data:
            st.info("セッションデータが見つかりません")
            return
        
        session = result.data[0]
        messages = session.get('messages') or []
        
        if not messages:
            st.info("会話データがありません")
            return
        
        for msg in messages:
            role = msg.get('role', '')
            content = msg.get('content', '')
            if role == 'assistant':
                st.markdown(f"🤖 **AI:** {content}")
            elif role == 'user':
                st.markdown(f"👤 **学生:** {content}")
        
        # フィードバック
        feedback = session.get('feedback') or session.get('ai_feedback')
        if feedback:
            st.markdown("---")
            st.markdown("**AIからのフィードバック:**")
            st.info(feedback)
    
    except Exception as e:
        st.error(f"セッション詳細の取得に失敗しました: {e}")


def _export_chat_csv(summary: dict):
    """チャットログCSV出力"""
    import pandas as pd
    
    students = summary.get('students', [])
    if not students:
        st.warning("エクスポートするデータがありません")
        return
    
    df = pd.DataFrame([{
        '名前': s.get('name', ''),
        '学籍番号': s.get('id', ''),
        'セッション数': s.get('sessions', 0),
        '平均スコア': s.get('avg_score', 0),
        'トレンド': s.get('trend', ''),
    } for s in students])
    
    csv = df.to_csv(index=False).encode('utf-8-sig')
    st.download_button(
        "📤 CSVダウンロード",
        csv,
        f"chat_logs_{datetime.now().strftime('%Y%m%d')}.csv",
        "text/csv"
    )
