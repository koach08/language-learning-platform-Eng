import streamlit as st
from utils.auth import get_current_user, require_auth
from utils.reading import (
    generate_comprehension_questions,
    generate_summary_and_vocabulary,
    generate_article_from_prompt,
    calculate_wpm,
    get_wpm_feedback
)
from utils.materials_loader import load_materials
import time
import json
from utils.tts_natural import show_tts_player, stop_audio


@require_auth
def show():
    user = get_current_user()
    
    st.markdown("## 📖 リーディング / Reading")
    
    if st.button("← ホームに戻る / Back"):
        st.session_state['current_view'] = 'teacher_home' if user['role'] == 'teacher' else 'student_home'
        st.rerun()
    
    st.markdown("---")
    
    if user['role'] == 'teacher':
        show_teacher_view()
    else:
        show_student_view()


def show_teacher_view():
    """教員用"""
    
    tab1, tab2, tab3 = st.tabs(["🤖 AI記事生成", "📋 記事管理", "📊 学習状況"])
    
    with tab1:
        show_ai_article_generator()
    
    with tab2:
        show_article_management()
    
    with tab3:
        show_class_reading_progress()


def show_ai_article_generator():
    """AI記事生成"""
    
    st.markdown("### 🤖 AIで記事を生成 / Generate Article with AI")
    
    with st.expander("💡 プロンプト例 / Example Prompts"):
        examples = [
            "日本の食文化について",
            "AIが仕事に与える影響",
            "大学生のメンタルヘルス",
            "持続可能なファッション",
            "宇宙探査の最新動向",
            "ソーシャルメディアの功罪",
        ]
        for ex in examples:
            st.markdown(f"- {ex}")
    
    prompt = st.text_area(
        "トピック / Topic",
        placeholder="例: 日本のポップカルチャーが世界に与える影響",
        height=80
    )
    
    col1, col2 = st.columns(2)
    with col1:
        level = st.select_slider("レベル / Level", ["A2", "B1", "B2", "C1"], value="B1")
    with col2:
        word_count = st.slider("語数 / Word count", 150, 500, 250)
    
    if st.button("🚀 記事を生成 / Generate", type="primary", disabled=not prompt):
        with st.spinner("記事を生成中... / Generating..."):
            result = generate_article_from_prompt(prompt, level, word_count)
        
        if result.get("success"):
            st.session_state['generated_article'] = result
            st.success("✅ 生成完了！")
        else:
            st.error(f"Error: {result.get('error')}")
    
    if 'generated_article' in st.session_state:
        article = st.session_state['generated_article']
        
        st.markdown("---")
        st.markdown(f"### 📰 {article.get('title', 'Generated Article')}")
        st.caption(f"Level: {article.get('level')} | Category: {article.get('category')} | Words: {article.get('word_count')}")
        
        st.markdown(article.get('text', ''))
        
        # 読み上げ機能
        show_tts_player(article.get('text', ''), key_prefix="tts_generated")
        
        col1, col2 = st.columns(2)
        with col1:
            if st.button("💾 保存 / Save"):
                st.success("記事を保存しました！ / Article saved!")
        with col2:
            if st.button("📝 問題を生成 / Generate Questions"):
                with st.spinner("問題を生成中..."):
                    questions = generate_comprehension_questions(
                        article.get('text', ''),
                        article.get('title', ''),
                        level=article.get('level', 'B1')
                    )
                if questions.get("success"):
                    st.session_state['generated_questions'] = questions
                    st.success("問題を生成しました！")
        
        if 'generated_questions' in st.session_state:
            show_questions_preview(st.session_state['generated_questions'])


def show_questions_preview(data):
    """生成された問題をプレビュー"""
    
    st.markdown("---")
    st.markdown("### 📝 生成された問題 / Generated Questions")
    
    for i, q in enumerate(data.get('questions', []), 1):
        with st.expander(f"Q{i}: {q.get('question', '')[:50]}..."):
            st.markdown(f"**{q.get('question', '')}**")
            st.caption(q.get('question_ja', ''))
            st.markdown(f"**Type:** {q.get('type', '')}")
            
            for opt in q.get('options', []):
                if opt == q.get('correct'):
                    st.markdown(f"- ✅ **{opt}**")
                else:
                    st.markdown(f"- {opt}")
            
            st.info(f"💡 {q.get('explanation', '')}")
            if q.get('text_evidence'):
                st.caption(f"📄 本文の根拠 / Text evidence: 『{q.get('text_evidence')}』")


def show_article_management():
    """記事管理"""
    
    st.markdown("### 📋 記事管理 / Manage Articles")
    
    articles = load_materials('reading')
    for key, article in articles.items():
        with st.expander(f"📰 {article['title']} ({article.get('level', '')})"):
            st.caption(f"Category: {article.get('category', '')} | Words: {article.get('word_count', '')}")
            st.markdown((article.get('text', '') or '')[:200] + "...")
            
            # 読み上げ機能
            if article.get('text'):
                show_tts_player(article['text'], key_prefix=f"tts_mgmt_{key}")


def show_class_reading_progress():
    """クラス学習状況"""
    
    st.markdown("### 📊 学習状況 / Reading Progress")
    
    from views.teacher_home import _load_classes
    user = get_current_user()
    if not user:
        return
    classes = _load_classes(user['id'])
    selected_class = st.session_state.get('selected_class')
    
    course_id = None
    if selected_class and selected_class in classes:
        course_id = classes[selected_class].get('db_id') or classes[selected_class].get('course_id')
    
    if not course_id:
        st.info("クラスを選択してください（教員ホームで選択後に戻ってください）")
        return
    
    try:
        from utils.database import get_supabase_client, get_course_students
        supabase = get_supabase_client()
        students = get_course_students(course_id)
        student_ids = [s['id'] for s in students]
        
        if student_ids:
            logs = supabase.table('reading_logs')\
                .select('student_id, quiz_score, time_spent_seconds, word_count')\
                .in_('student_id', student_ids)\
                .order('completed_at', desc=True)\
                .limit(200)\
                .execute()
            reading_data = logs.data if logs.data else []
        else:
            reading_data = []
    except Exception:
        reading_data = []
        students = []
    
    if not reading_data:
        st.info("まだリーディング学習の記録がありません")
        return
    
    quiz_scores = [d.get('quiz_score') for d in reading_data if d.get('quiz_score') is not None]
    avg_score = sum(quiz_scores) / len(quiz_scores) if quiz_scores else 0
    active_students = len(set(d.get('student_id') for d in reading_data))
    total_articles = len(reading_data)
    
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("平均正答率", f"{avg_score:.0f}%" if quiz_scores else "—")
    with col2:
        st.metric("総読了数", f"{total_articles} articles")
    with col3:
        st.metric("アクティブ学生", f"{active_students}/{len(students)}人")


def show_student_view():
    """学生用"""
    
    tab1, tab2, tab3 = st.tabs([
        "📖 記事を読む",
        "🤖 AI記事生成",
        "📊 学習記録"
    ])
    
    with tab1:
        show_reading_practice()
    
    with tab2:
        show_student_ai_generator()
    
    with tab3:
        show_reading_progress()


def show_reading_practice():
    """読解練習"""
    
    st.markdown("### 📖 記事を読む / Read Articles")
    
    # 記事選択
    articles = load_materials('reading')
    if not articles:
        st.info("リーディング教材がありません")
        return
    article_options = {key: f"{data['title']} ({data.get('level', '')})" for key, data in articles.items()}
    selected = st.selectbox(
        "記事を選択 / Select Article",
        options=list(article_options.keys()),
        format_func=lambda x: article_options[x]
    )
    
    if selected:
        article = articles[selected]
        
        st.markdown("---")
        st.markdown(f"### 📰 {article['title']}")
        st.caption(f"Level: {article['level']} | Category: {article['category']} | Words: {article['word_count']}")
        
        # 読解モード選択
        mode = st.radio(
            "モード / Mode",
            ["timed", "untimed"],
            format_func=lambda x: {
                "timed": "⏱️ タイム計測 / Timed (measure WPM)",
                "untimed": "📖 じっくり読む / Untimed"
            }[x],
            horizontal=True
        )
        
        # セッション状態
        if 'reading_started' not in st.session_state:
            st.session_state.reading_started = False
        if 'reading_start_time' not in st.session_state:
            st.session_state.reading_start_time = None
        if 'reading_finished' not in st.session_state:
            st.session_state.reading_finished = False
        
        st.markdown("---")
        
        if not st.session_state.reading_started:
            st.info("「読み始める」をクリックすると記事が表示されます / Click 'Start Reading' to see the article")
            if st.button("📖 読み始める / Start Reading", type="primary"):
                st.session_state.reading_started = True
                st.session_state.reading_start_time = time.time()
                st.session_state.reading_finished = False
                st.session_state.current_article = selected
                st.rerun()
        
        elif not st.session_state.reading_finished:
            # 記事を表示
            st.markdown(article['text'])
            
            # 読み上げ機能
            st.markdown("---")
            show_tts_player(article['text'], key_prefix=f"tts_{selected}")
            
            st.markdown("---")
            
            if mode == "timed":
                elapsed = int(time.time() - st.session_state.reading_start_time)
                st.caption(f"⏱️ 経過時間 / Elapsed: {elapsed} seconds")
            
            if st.button("✅ 読み終わった / Finished Reading", type="primary"):
                st.session_state.reading_finished = True
                st.session_state.reading_end_time = time.time()
                st.rerun()
        
        else:
            # 読了後
            if mode == "timed":
                reading_time = st.session_state.reading_end_time - st.session_state.reading_start_time
                wpm = calculate_wpm(article['word_count'], reading_time)
                feedback = get_wpm_feedback(wpm, article['level'])
                
                st.markdown("### ⏱️ 読解速度 / Reading Speed")
                col1, col2, col3 = st.columns(3)
                with col1:
                    st.metric("WPM", wpm)
                with col2:
                    st.metric("時間 / Time", f"{int(reading_time)}秒")
                with col3:
                    st.metric("評価", feedback['rating'])
                
                st.info(feedback['message'])
            
            st.markdown("---")
            
            # 次のアクション
            col1, col2, col3 = st.columns(3)
            
            with col1:
                if st.button("📝 理解度クイズ / Comprehension Quiz", type="primary"):
                    with st.spinner("問題を生成中..."):
                        questions = generate_comprehension_questions(
                            article['text'],
                            article['title'],
                            level=article['level']
                        )
                    if questions.get("success"):
                        st.session_state.reading_questions = questions
                        st.session_state.quiz_mode = True
                        st.rerun()
            
            with col2:
                if st.button("📋 要約・語彙 / Summary & Vocab"):
                    with st.spinner("分析中..."):
                        analysis = generate_summary_and_vocabulary(
                            article['text'],
                            article['title'],
                            level=article['level']
                        )
                    if analysis.get("success"):
                        st.session_state.reading_analysis = analysis
                        st.rerun()
            
            with col3:
                if st.button("🔄 別の記事 / Another Article"):
                    st.session_state.reading_started = False
                    st.session_state.reading_finished = False
                    if 'reading_questions' in st.session_state:
                        del st.session_state.reading_questions
                    if 'reading_analysis' in st.session_state:
                        del st.session_state.reading_analysis
                    st.rerun()
            
            # クイズ表示
            if 'reading_questions' in st.session_state and st.session_state.get('quiz_mode'):
                show_comprehension_quiz(st.session_state.reading_questions)
            
            # 要約・語彙表示
            if 'reading_analysis' in st.session_state:
                show_reading_analysis(st.session_state.reading_analysis)


def show_comprehension_quiz(data):
    """理解度クイズ"""
    
    st.markdown("---")
    st.markdown("### 📝 理解度クイズ / Comprehension Quiz")
    
    questions = data.get('questions', [])
    
    if 'quiz_answers' not in st.session_state:
        st.session_state.quiz_answers = {}
    if 'quiz_submitted' not in st.session_state:
        st.session_state.quiz_submitted = False
    
    if not st.session_state.quiz_submitted:
        for i, q in enumerate(questions):
            st.markdown(f"**Q{i+1}. {q.get('question', '')}**")
            st.caption(q.get('question_ja', ''))
            
            answer = st.radio(
                f"選択 / Choose",
                q.get('options', []),
                key=f"reading_q_{i}",
                label_visibility="collapsed"
            )
            st.session_state.quiz_answers[i] = answer
            st.markdown("---")
        
        if st.button("📤 回答を送信 / Submit Answers", type="primary"):
            st.session_state.quiz_submitted = True
            st.rerun()
    
    else:
        # 結果表示
        correct_count = 0
        for i, q in enumerate(questions):
            user_answer = st.session_state.quiz_answers.get(i)
            is_correct = user_answer == q.get('correct')
            if is_correct:
                correct_count += 1
            
            if is_correct:
                st.success(f"**Q{i+1}. ✅ Correct!**")
            else:
                st.error(f"**Q{i+1}. ❌ Incorrect**")
            
            st.markdown(f"Your answer: {user_answer}")
            st.markdown(f"Correct answer: {q.get('correct')}")
            st.info(f"💡 {q.get('explanation', '')}")
            if q.get('text_evidence'):
                st.caption(f"📄 本文の根拠 / Text evidence: 『{q.get('text_evidence')}』")
            st.markdown("---")
        
        # スコア
        score_pct = (correct_count / len(questions)) * 100
        st.markdown(f"### 🎯 Score: {correct_count}/{len(questions)} ({score_pct:.0f}%)")
        
        # DB保存（1回だけ実行）
        if not st.session_state.get('quiz_saved'):
            _save_reading_quiz_to_db(questions, score_pct)
            st.session_state.quiz_saved = True
        
        if st.button("🔄 もう一度 / Try Again"):
            st.session_state.quiz_submitted = False
            st.session_state.quiz_answers = {}
            st.session_state.quiz_mode = False
            st.session_state.quiz_saved = False
            st.rerun()


def _save_reading_quiz_to_db(questions, score_pct):
    """クイズ結果をreading_logsに保存"""
    try:
        from utils.auth import get_current_user
        from utils.database import log_reading, log_practice
        
        user = get_current_user()
        if not user or user.get('role') == 'teacher':
            return
        
        student_id = user['id']
        
        # コースIDを取得
        course_id = None
        registered = st.session_state.get('student_registered_classes', [])
        if registered:
            first = registered[0]
            if isinstance(first, dict):
                course_id = first.get('class_key') or first.get('id') or first.get('course_id')
            else:
                course_id = None
        
        # 記事情報を取得
        article = st.session_state.get('current_article') or st.session_state.get('student_article', {})
        title = article.get('title', 'Unknown')
        level = article.get('level', 'B1')
        word_count = article.get('word_count', 0)
        
        # 各問題の正誤を記録
        quiz_results = []
        for i, q in enumerate(questions):
            user_answer = st.session_state.quiz_answers.get(i)
            quiz_results.append({
                'question': q.get('question', ''),
                'type': q.get('type', ''),
                'user_answer': user_answer,
                'correct_answer': q.get('correct', ''),
                'is_correct': user_answer == q.get('correct')
            })
        
        # 読解時間（reading_start_timeがあれば）
        time_spent = 0
        if st.session_state.get('reading_start_time'):
            time_spent = int(time.time() - st.session_state.reading_start_time)
        
        # reading_logsに記録
        log_reading(
            student_id=student_id,
            course_id=course_id,
            source_title=title,
            word_count=word_count,
            estimated_level=level,
            activity_type='intensive',
            quiz_results=quiz_results,
            quiz_score=round(score_pct, 1),
            time_spent_seconds=time_spent
        )
        
        # practice_logsにも記録（ダッシュボード集計用）
        log_practice(
            student_id=student_id,
            course_id=course_id,
            module_type='reading_practice',
            score=round(score_pct, 1),
            duration_seconds=time_spent,
            activity_details={
                'activity': 'comprehension_quiz',
                'title': title,
                'level': level,
                'questions': len(questions),
                'correct': sum(1 for r in quiz_results if r['is_correct'])
            }
        )
        
    except Exception as e:
        st.error(f"Reading保存エラー: {e}")


def show_reading_analysis(data):
    """要約・語彙分析"""
    
    st.markdown("---")
    st.markdown("### 📋 要約・語彙 / Summary & Vocabulary")
    
    # 要約
    st.markdown("#### 📝 Summary / 要約")
    st.markdown(f"**English:** {data.get('summary_en', '')}")
    st.markdown(f"**日本語:** {data.get('summary_ja', '')}")
    
    # 要点
    st.markdown("#### 🎯 Main Points / 要点")
    for point in data.get('main_points', []):
        st.markdown(f"- {point}")
    
    # 重要語彙
    st.markdown("#### 📚 Key Vocabulary / 重要語彙")
    for vocab in data.get('key_vocabulary', []):
        with st.expander(f"**{vocab.get('word', '')}** - {vocab.get('meaning', '')}"):
            st.markdown(f"*Context:* {vocab.get('context', '')}")
    
    # ディスカッション質問
    if data.get('discussion_questions'):
        st.markdown("#### 💬 Discussion Questions")
        for q in data.get('discussion_questions', []):
            st.markdown(f"- {q}")


def show_student_ai_generator():
    """学生用AI記事生成"""
    
    st.markdown("### 🤖 興味のあるトピックで記事を生成 / Generate Article on Your Topic")
    
    prompt = st.text_area(
        "読みたいトピック / Topic you want to read about",
        placeholder="例: eスポーツの歴史と未来、日本のアニメ産業...",
        height=80
    )
    
    col1, col2 = st.columns(2)
    with col1:
        level = st.select_slider("レベル", ["A2", "B1", "B2", "C1"], value="B1", key="student_level")
    with col2:
        word_count = st.slider("語数", 150, 400, 200, key="student_wc")
    
    if st.button("🚀 生成 / Generate", type="primary", disabled=not prompt):
        with st.spinner("記事を生成中..."):
            result = generate_article_from_prompt(prompt, level, word_count)
        
        if result.get("success"):
            st.session_state['student_article'] = result
            st.success("✅ 生成完了！")
        else:
            st.error(f"Error: {result.get('error')}")
    
    if 'student_article' in st.session_state:
        article = st.session_state['student_article']
        
        st.markdown("---")
        st.markdown(f"### 📰 {article.get('title', '')}")
        st.caption(f"Level: {article.get('level')} | Words: {article.get('word_count')}")
        st.markdown(article.get('text', ''))
        
        # 読み上げ機能
        show_tts_player(article.get('text', ''), key_prefix="tts_student_gen")
        
        if st.button("📝 この記事でクイズ / Quiz on this article"):
            with st.spinner("問題を生成中..."):
                questions = generate_comprehension_questions(
                    article.get('text', ''),
                    article.get('title', ''),
                    level=article.get('level', 'B1')
                )
            if questions.get("success"):
                st.session_state.reading_questions = questions
                st.session_state.quiz_mode = True
                st.session_state.quiz_submitted = False
                st.session_state.quiz_answers = {}
                show_comprehension_quiz(questions)


def show_reading_progress():
    """学習記録"""
    
    st.markdown("### 📊 学習記録 / Reading Progress")
    
    user = get_current_user()
    if not user:
        return
    
    try:
        from utils.database import get_student_reading_logs, get_student_practice_details
        logs = get_student_reading_logs(user['id'], days=90)
        practice = get_student_practice_details(user['id'], days=90, module_type='reading')
    except Exception:
        logs = []
        practice = []
    
    if not logs and not practice:
        st.info("まだ学習記録がありません。リーディング練習を始めましょう！")
        return
    
    quiz_scores = [l.get('quiz_score') for l in logs if l.get('quiz_score') is not None]
    avg_score = sum(quiz_scores) / len(quiz_scores) if quiz_scores else 0
    total_articles = len(logs)
    total_words = sum(l.get('word_count', 0) or 0 for l in logs)
    
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("読んだ記事数", f"{total_articles}")
    with col2:
        st.metric("総語数", f"{total_words:,}")
    with col3:
        st.metric("平均正答率", f"{avg_score:.0f}%" if quiz_scores else "—")
    with col4:
        # 今週の記事数
        from datetime import datetime, timedelta
        week_ago = (datetime.utcnow() - timedelta(days=7)).isoformat()
        this_week = sum(1 for l in logs if (l.get('completed_at', '') or '') >= week_ago)
        st.metric("今週", f"{this_week} articles")
    
    # 最近の履歴
    if logs:
        st.markdown("---")
        st.markdown("#### 📋 最近の学習")
        for l in logs[:8]:
            date_str = (l.get('completed_at', '') or '')[:10]
            title = l.get('source_title', '') or '—'
            score_str = f" — 正答率: {l['quiz_score']:.0f}%" if l.get('quiz_score') is not None else ""
            st.caption(f"📖 {date_str} | {title}{score_str}")
