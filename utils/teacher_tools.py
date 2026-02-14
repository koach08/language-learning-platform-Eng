import streamlit as st
from datetime import datetime, timedelta


# ===== フィードバックテンプレート =====

FEEDBACK_TEMPLATES = {
    'speaking': {
        'excellent': [
            "Excellent pronunciation and fluency! Keep up the great work. 発音も流暢さも素晴らしいです。",
            "Very natural delivery. Your intonation patterns are improving significantly. とても自然な話し方です。",
            "Great job! Your confidence in speaking English is clearly growing. 英語で話す自信がついてきていますね。",
        ],
        'good': [
            "Good effort! Pay attention to the pronunciation of [specific sounds]. Try practicing with slower speed first. よく頑張りました。[特定の音]の発音に注意しましょう。",
            "Nice progress! Focus on connecting words more smoothly for better fluency. 進歩しています。単語の繋がりをもう少し滑らかにしましょう。",
            "Well done! Try to vary your intonation more to sound more natural. イントネーションにもう少し変化をつけると自然に聞こえます。",
        ],
        'needs_work': [
            "I can see you're working hard. Let's focus on basic pronunciation patterns first. Practice reading aloud for 10 minutes daily. 頑張っていますね。まず基本的な発音パターンに集中しましょう。毎日10分の音読を。",
            "Don't give up! Try listening to the model audio several times before recording. Keep practicing! 諦めずに。録音前にお手本の音声を何度か聞いてみてください。",
            "Good attempt! I recommend starting with shorter sentences and gradually increasing length. 短い文から始めて、徐々に長くしていくことをお勧めします。",
        ]
    },
    'writing': {
        'excellent': [
            "Excellent essay! Your arguments are well-structured and clearly expressed. 素晴らしいエッセイです。論旨が明確で構成もしっかりしています。",
            "Very impressive writing. Your vocabulary usage is varied and appropriate. 語彙の使い方が豊かで適切です。",
            "Great work! Your writing shows clear logical flow and good use of transitions. 論理的な流れが明確で、つなぎ言葉も上手に使えています。",
        ],
        'good': [
            "Good essay! Try to use more varied sentence structures. Also check your use of articles (a/the). 良いエッセイです。文構造をもう少し多様にし、冠詞の使い方を確認しましょう。",
            "Nice work! Your ideas are interesting. Pay attention to paragraph organization - each paragraph should have one main idea. 段落構成に注意。各段落に一つの主張を。",
            "Well written! Consider adding more specific examples to support your arguments. 具体的な例を追加すると、論旨がより強くなります。",
        ],
        'needs_work': [
            "I can see your ideas are developing. Focus on writing clear topic sentences for each paragraph. Practice the basic essay structure: introduction, body, conclusion. 段落ごとのトピックセンテンスを明確にしましょう。",
            "Good effort! Let's work on basic grammar: subject-verb agreement and tense consistency. Try writing shorter, simpler sentences first. 基本文法に集中しましょう。まず短くシンプルな文から。",
            "Keep trying! I recommend reading English articles and noting how they organize ideas. Then try to follow similar patterns. 英語の記事を読んで、構成のパターンを学びましょう。",
        ]
    },
    'general': {
        'encouragement': [
            "Great progress this week! 今週はよく頑張りました！",
            "I can see your improvement. Keep it up! 上達が見えます。この調子で！",
            "Your effort is paying off. Don't stop now! 努力が実を結んでいます。",
        ],
        'reminder': [
            "Don't forget to submit your assignment by the deadline. 締切までに課題を提出してください。",
            "Please try to practice at least 3 times this week. 今週は最低3回練習しましょう。",
            "Remember to review your vocabulary regularly. 語彙の定期的な復習を忘れずに。",
        ]
    }
}


def get_feedback_suggestion(module, score):
    """スコアに基づいてフィードバックテンプレートを提案"""
    templates = FEEDBACK_TEMPLATES.get(module, FEEDBACK_TEMPLATES['general'])
    
    if score >= 85:
        category = 'excellent'
    elif score >= 65:
        category = 'good'
    else:
        category = 'needs_work'
    
    suggestions = templates.get(category, templates.get('encouragement', []))
    return suggestions


# ===== 自動アラート =====

def get_student_alerts(course_id: str = None):
    """学生の要注意アラートを生成（DB連携）"""
    alerts = []
    
    # コースIDの取得
    if not course_id:
        selected_class = st.session_state.get('selected_class')
        classes = st.session_state.get('teacher_classes', {})
        if selected_class and selected_class in classes:
            course_id = classes[selected_class].get('db_id') or classes[selected_class].get('course_id')
    
    if not course_id:
        return alerts
    
    # DBから学生の活動サマリーを取得
    try:
        from utils.database import get_students_with_activity_summary
        db_students = get_students_with_activity_summary(course_id)
    except Exception as e:
        st.warning(f"学生データの取得に失敗しました: {e}")
        return alerts
    
    if not db_students:
        return alerts
    
    for student in db_students:
        # 長期未ログイン
        days_inactive = student.get('days_since_active', 0)
        
        if days_inactive >= 14:
            alerts.append({
                'student': student['name'],
                'student_id': student['student_id'],
                'type': 'inactive',
                'severity': 'high',
                'icon': '🚨',
                'message': f'{days_inactive}日間ログインなし',
                'suggestion': '個別に声かけを推奨',
                'days_inactive': days_inactive,
            })
        elif days_inactive >= 7:
            alerts.append({
                'student': student['name'],
                'student_id': student['student_id'],
                'type': 'inactive',
                'severity': 'medium',
                'icon': '⚠️',
                'message': f'{days_inactive}日間ログインなし',
                'suggestion': 'リマインダーの送信を検討',
                'days_inactive': days_inactive,
            })
        
        # 課題未提出
        missing = student['total_assignments'] - student['submissions']
        if missing >= 2:
            alerts.append({
                'student': student['name'],
                'student_id': student['student_id'],
                'type': 'missing_assignments',
                'severity': 'high',
                'icon': '📝',
                'message': f'未提出課題が{missing}件',
                'suggestion': '締切の再通知と個別サポートを',
            })
        elif missing == 1:
            alerts.append({
                'student': student['name'],
                'student_id': student['student_id'],
                'type': 'missing_assignments',
                'severity': 'low',
                'icon': '📋',
                'message': f'未提出課題が1件',
                'suggestion': 'リマインダーを送信',
            })
        
        # スコア低下
        if student['score_trend'] <= -10 and student['avg_score'] > 0:
            alerts.append({
                'student': student['name'],
                'student_id': student['student_id'],
                'type': 'score_decline',
                'severity': 'medium',
                'icon': '📉',
                'message': f'スコアが{abs(student["score_trend"])}点低下（平均{student["avg_score"]}点）',
                'suggestion': '個別面談やサポートを検討',
            })
        
        # 低スコア
        if 0 < student['avg_score'] < 50:
            alerts.append({
                'student': student['name'],
                'student_id': student['student_id'],
                'type': 'low_score',
                'severity': 'high',
                'icon': '🔴',
                'message': f'平均スコアが{student["avg_score"]}点（要サポート）',
                'suggestion': '補助教材の提供と個別指導を推奨',
            })
        
        # 学習時間不足
        if student['weekly_study_minutes'] < 30 and days_inactive < 7:
            alerts.append({
                'student': student['name'],
                'student_id': student['student_id'],
                'type': 'low_study_time',
                'severity': 'low',
                'icon': '⏱️',
                'message': f'今週の学習時間が{student["weekly_study_minutes"]}分',
                'suggestion': '学習習慣の定着を支援',
            })
    
    # 重要度でソート
    severity_order = {'high': 0, 'medium': 1, 'low': 2}
    alerts.sort(key=lambda x: severity_order.get(x['severity'], 3))
    
    return alerts


# ===== 一括フィードバック =====

def show_batch_feedback_ui():
    """一括フィードバック送信UI"""
    
    st.markdown("### 📨 一括フィードバック")
    
    tab1, tab2 = st.tabs(["📋 テンプレートから", "✏️ カスタム"])
    
    with tab1:
        module = st.selectbox("モジュール", ["speaking", "writing", "general"])
        
        templates = FEEDBACK_TEMPLATES.get(module, {})
        category = st.selectbox("カテゴリ", list(templates.keys()))
        
        suggestions = templates.get(category, [])
        
        if suggestions:
            selected_template = st.selectbox(
                "テンプレートを選択",
                suggestions,
                key="batch_template"
            )
            
            # 編集可能
            final_message = st.text_area(
                "メッセージ（編集可）",
                value=selected_template,
                height=100,
                key="batch_message_template"
            )
        else:
            final_message = st.text_area("メッセージ", height=100)
    
    with tab2:
        final_message = st.text_area(
            "カスタムメッセージ",
            placeholder="学生へのメッセージを入力...",
            height=100,
            key="batch_message_custom"
        )
    
    # 送信対象
    st.markdown("#### 送信対象")
    target = st.radio(
        "対象",
        ["all", "score_below", "inactive", "missing"],
        format_func=lambda x: {
            "all": "📢 全員",
            "score_below": "📉 スコアが低い学生",
            "inactive": "😴 非アクティブな学生",
            "missing": "📝 課題未提出の学生"
        }[x],
        horizontal=True
    )
    
    if target == "score_below":
        threshold = st.slider("スコア閾値", 0, 100, 60)
        st.caption(f"平均スコアが{threshold}点未満の学生に送信")
    
    if st.button("📤 送信", type="primary"):
        st.success("フィードバックを送信しました！（※デモ）")
        st.balloons()


# ===== アラートダッシュボード =====

def show_alert_dashboard():
    """アラートダッシュボード"""
    
    st.markdown("### 🔔 学生アラート")
    st.caption("自動検出された要注意事項")
    
    alerts = get_student_alerts()
    
    if not alerts:
        st.success("✅ 現在、注意が必要な学生はいません")
        return
    
    # サマリー
    high = len([a for a in alerts if a['severity'] == 'high'])
    medium = len([a for a in alerts if a['severity'] == 'medium'])
    low = len([a for a in alerts if a['severity'] == 'low'])
    
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("🚨 重要", f"{high}件")
    with col2:
        st.metric("⚠️ 注意", f"{medium}件")
    with col3:
        st.metric("💡 情報", f"{low}件")
    with col4:
        unique_students = len(set(a['student'] for a in alerts))
        st.metric("対象学生", f"{unique_students}名")
    
    st.markdown("---")
    
    # フィルター
    filter_severity = st.multiselect(
        "重要度フィルター",
        ["high", "medium", "low"],
        default=["high", "medium"],
        format_func=lambda x: {"high": "🚨 重要", "medium": "⚠️ 注意", "low": "💡 情報"}[x]
    )
    
    filtered = [a for a in alerts if a['severity'] in filter_severity]
    
    # アラート表示
    for alert in filtered:
        severity_colors = {
            'high': 'error',
            'medium': 'warning',
            'low': 'info'
        }
        
        with st.expander(f"{alert['icon']} {alert['student']} - {alert['message']}"):
            st.markdown(f"**学生:** {alert['student']} ({alert['student_id']})")
            st.markdown(f"**問題:** {alert['message']}")
            st.info(f"💡 **推奨アクション:** {alert['suggestion']}")
            
            # クイックアクション
            col1, col2, col3 = st.columns(3)
            with col1:
                if st.button("📨 メッセージ送信", key=f"msg_{alert['student_id']}_{alert['type']}"):
                    st.session_state['current_view'] = 'messaging'
                    st.rerun()
            with col2:
                if st.button("✅ 対応済み", key=f"done_{alert['student_id']}_{alert['type']}"):
                    st.success("対応済みにしました")
            with col3:
                if st.button("🔇 非表示", key=f"mute_{alert['student_id']}_{alert['type']}"):
                    st.success("非表示にしました")


# ===== 成績一括処理 =====

def show_grade_tools():
    """成績一括処理ツール"""
    
    st.markdown("### 📊 成績ツール")
    
    tab1, tab2 = st.tabs(["📥 一括インポート", "📤 一括エクスポート"])
    
    with tab1:
        st.markdown("#### CSVから成績をインポート")
        uploaded = st.file_uploader("CSVファイル", type=['csv'])
        if uploaded:
            import pandas as pd
            try:
                df = pd.read_csv(uploaded)
                st.dataframe(df, use_container_width=True)
                if st.button("📥 インポート実行"):
                    st.success(f"{len(df)}件のデータをインポートしました（※デモ）")
            except Exception as e:
                st.error(f"エラー: {e}")
    
    with tab2:
        st.markdown("#### 成績をCSVでエクスポート")
        
        import pandas as pd
        
        # DBから成績データを取得
        course_id = None
        selected_class = st.session_state.get('selected_class')
        classes = st.session_state.get('teacher_classes', {})
        if selected_class and selected_class in classes:
            course_id = classes[selected_class].get('db_id') or classes[selected_class].get('course_id')
        
        if course_id:
            try:
                from utils.database import get_students_with_activity_summary
                students_data = get_students_with_activity_summary(course_id)
                
                if students_data:
                    grades_df = pd.DataFrame([{
                        '学籍番号': s.get('student_id', ''),
                        '名前': s.get('name', ''),
                        '平均スコア': s.get('avg_score', 0),
                        '提出数': s.get('submissions', 0),
                        '総課題数': s.get('total_assignments', 0),
                        '練習回数': s.get('practice_count', 0),
                        '週間学習(分)': s.get('weekly_study_minutes', 0),
                    } for s in students_data])
                    
                    st.dataframe(grades_df, use_container_width=True, hide_index=True)
                    
                    csv = grades_df.to_csv(index=False).encode('utf-8-sig')
                    st.download_button(
                        "📤 CSVダウンロード",
                        csv,
                        f"grades_{datetime.now().strftime('%Y%m%d')}.csv",
                        "text/csv"
                    )
                else:
                    st.info("まだ成績データがありません。学生が課題を提出すると表示されます。")
            except Exception as e:
                st.error(f"成績データの取得に失敗しました: {e}")
        else:
            st.warning("コースが選択されていません")
