import streamlit as st
from utils.auth import get_current_user, require_auth
from utils.listening import (
    generate_audio_with_openai,
    generate_dialogue_audio_with_speakers,
    check_dictation,
    check_youtube_dictation,
    generate_listening_from_prompt
)
from utils.materials_loader import load_materials
from utils.listening_youtube import (
    extract_youtube_id,
    get_youtube_transcript,
    get_transcript_auto,
    generate_exercises_from_transcript,
    analyze_video_difficulty,
    generate_learning_from_topic,
    CURATED_VIDEO_LIST
)
import time


@require_auth
def show():
    user = get_current_user()
    
    st.markdown("## 🎧 リスニング / Listening")
    
    if st.button("← ホームに戻る / Back"):
        st.session_state['current_view'] = 'teacher_home' if user['role'] == 'teacher' else 'student_home'
        st.rerun()
    
    st.markdown("---")
    
    if user['role'] == 'teacher':
        show_teacher_view()
    else:
        show_student_view()


# ==================== 教員用 ====================
def show_teacher_view():
    tab1, tab2, tab3, tab4, tab5 = st.tabs([
        "🤖 AI素材生成", "📺 YouTube（自動字幕）", "📋 動画リスト管理", "📚 素材一覧", "📊 学習状況"
    ])
    with tab1:
        show_ai_listening_generator()
    with tab2:
        show_youtube_with_whisper_teacher()
    with tab3:
        show_video_list_management()
    with tab4:
        show_material_management()
    with tab5:
        show_class_listening_progress()


def show_youtube_with_whisper_teacher():
    st.markdown("### 📺 YouTube動画から学習素材を作成")
    st.markdown("**字幕がない動画も対応！** Whisper AIで自動文字起こし（10分≒10円）")
    url = st.text_input("YouTube URL", placeholder="https://www.youtube.com/watch?v=...", key="t_yt_url_input")
    video_title = st.text_input("動画タイトル（任意）", key="t_yt_title_input")
    level = st.select_slider("対象レベル", ["A2", "B1", "B2", "C1"], value="B1", key="t_yt_level")
    if url:
        video_id = extract_youtube_id(url)
        if video_id:
            st.video(url)
            if st.button("🎓 字幕を取得して素材を生成", type="primary", key="t_yt_generate"):
                with st.spinner("字幕を取得中..."):
                    transcript_result = get_transcript_auto(video_id)
                if not transcript_result.get("success"):
                    st.error(f"❌ {transcript_result.get('error')}")
                else:
                    method = transcript_result.get("method", "")
                    st.success(f"✅ {'Whisper AIで文字起こし' if method == 'whisper' else 'YouTube字幕を取得'}完了！")
                    transcript = transcript_result.get("transcript", "")
                    with st.spinner("学習素材を生成中..."):
                        difficulty = analyze_video_difficulty(transcript, level)
                        exercises = generate_exercises_from_transcript(
                            transcript, video_title or transcript_result.get("title", ""), level
                        )
                    if exercises.get("success"):
                        st.session_state['t_yt_exercises'] = exercises
                        st.session_state['t_yt_difficulty'] = difficulty
                        st.session_state['t_yt_transcript'] = transcript
                        st.session_state['t_yt_video_url'] = url
                        st.success("✅ 素材生成完了！")
                        st.rerun()
        else:
            st.warning("有効なYouTube URLを入力してください")
    if 't_yt_exercises' in st.session_state:
        show_teacher_youtube_preview()


def show_teacher_youtube_preview():
    exercises = st.session_state.get('t_yt_exercises', {})
    difficulty = st.session_state.get('t_yt_difficulty', {})
    st.markdown("---")
    st.markdown("### 📋 生成された素材")
    if difficulty.get("success"):
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("推定レベル", difficulty.get('estimated_cefr', 'N/A'))
        with col2:
            st.metric("適合度", f"{difficulty.get('suitability_score', 'N/A')}/10")
        with col3:
            factors = difficulty.get('difficulty_factors', {})
            st.metric("話速", factors.get('speech_speed', 'N/A'))
    summary = exercises.get('summary', {})
    if summary:
        st.markdown("#### 📝 要約")
        st.markdown(f"**EN:** {summary.get('english', '')}")
        st.markdown(f"**JP:** {summary.get('japanese', '')}")
    if st.button("🗑️ クリア", key="t_yt_clear"):
        for key in ['t_yt_exercises', 't_yt_difficulty', 't_yt_transcript', 't_yt_video_url']:
            if key in st.session_state:
                del st.session_state[key]
        st.rerun()


def show_video_list_management():
    st.markdown("### 📋 授業用動画リスト管理")
    with st.expander("➕ 新しい動画を追加"):
        new_url = st.text_input("YouTube URL", key="new_vid_url")
        new_title = st.text_input("タイトル", key="new_vid_title")
        col1, col2 = st.columns(2)
        with col1:
            new_level = st.selectbox("レベル", ["A2", "B1", "B2", "C1"], key="new_vid_level")
        with col2:
            new_topic = st.text_input("トピック", key="new_vid_topic")
        if st.button("➕ 追加", type="primary", key="add_new_vid"):
            if new_url and new_title:
                st.success(f"「{new_title}」を追加しました！")
                st.caption("※ 動画リスト管理の完全なDB対応は次回アップデートで実装予定です")
    st.markdown("---")
    for category_key, category in CURATED_VIDEO_LIST.items():
        with st.expander(f"📁 {category['name']} ({len(category['videos'])}本)"):
            st.caption(category['description'])
            for video in category['videos']:
                st.markdown(f"**{video['title']}** ({video['level']})")


def show_ai_listening_generator():
    st.markdown("### 🤖 AIでリスニング素材を生成")
    
    # text_areaの値をsession_stateで管理してボタンの有効/無効を制御
    if 't_ai_prompt_val' not in st.session_state:
        st.session_state['t_ai_prompt_val'] = ''
    
    prompt = st.text_area(
        "トピック",
        placeholder="例: カフェでの注文",
        height=80,
        key="t_ai_prompt",
        on_change=lambda: st.session_state.update({'t_ai_prompt_val': st.session_state.get('t_ai_prompt', '')})
    )
    
    col1, col2 = st.columns(2)
    with col1:
        level = st.select_slider("レベル", ["A2", "B1", "B2", "C1"], value="B1", key="t_ai_level")
    with col2:
        duration = st.selectbox(
            "長さ", ["short", "medium", "long"],
            format_func=lambda x: {"short": "短い", "medium": "中程度", "long": "長い"}[x],
            key="t_ai_dur"
        )
    
    if st.button("🚀 生成", type="primary", disabled=not prompt, key="t_ai_gen"):
        with st.spinner("生成中..."):
            result = generate_listening_from_prompt(prompt, level, duration)
        if result.get("success"):
            st.session_state['t_gen_listening'] = result
            st.success("✅ 生成完了！")
    
    if 't_gen_listening' in st.session_state:
        data = st.session_state['t_gen_listening']
        st.markdown(f"### {data.get('title', '')}")
        with st.expander("📜 スクリプト"):
            st.markdown(data.get('script', ''))


def show_material_management():
    st.markdown("### 📚 リスニング素材一覧")
    materials = load_materials('listening')
    for key, material in materials.items():
        with st.expander(f"🎧 {material['title']} ({material.get('level', '')})"):
            st.markdown((material.get('script', '') or '')[:200] + "...")


def show_class_listening_progress():
    st.markdown("### 📊 学習状況")
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
        from utils.database import get_listening_stats_for_course, get_course_students
        logs = get_listening_stats_for_course(course_id)
        students = get_course_students(course_id)
    except Exception:
        logs = []
        students = []
    if not logs:
        st.info("まだリスニング学習の記録がありません")
        return
    total_sessions = len(logs)
    quiz_scores = [l.get('quiz_score') for l in logs if l.get('quiz_score') is not None]
    avg_score = sum(quiz_scores) / len(quiz_scores) if quiz_scores else 0
    active_students = len(set(l.get('student_id') for l in logs))
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("総学習回数", f"{total_sessions}回")
    with col2:
        st.metric("平均スコア", f"{avg_score:.0f}%" if quiz_scores else "—")
    with col3:
        st.metric("アクティブ学生", f"{active_students}/{len(students)}人")


# ==================== 学生用 ====================
def show_student_view():
    tab1, tab2, tab3, tab4 = st.tabs([
        "📺 YouTube学習", "🎧 リスニング練習", "🤖 AI素材生成", "📊 学習記録"
    ])
    with tab1:
        show_youtube_learning_student()
    with tab2:
        show_listening_practice()
    with tab3:
        show_student_ai_generator()
    with tab4:
        show_listening_progress()


def show_youtube_learning_student():
    st.markdown("### 📺 YouTube動画でディクテーション練習")
    st.caption("好きな動画を見ながら、聞こえた英語を書き取ろう")

    url = st.text_input("YouTube URL", placeholder="https://www.youtube.com/watch?v=...", key="s_yt_url_input")

    if url:
        video_id = extract_youtube_id(url)
        if video_id:
            st.video(url)
            st.markdown("---")
            st.info("💡 ① 動画を再生 → ② 聞こえた英語を入力 → ③「チェック」ボタンを押す")

            user_input = st.text_area(
                "聞こえた英語を入力してください（1文ずつでもOK）",
                height=120,
                placeholder="例: The human brain is an amazing organ...",
                key="s_yt_dictation_input"
            )

            if st.button("✅ チェック", type="primary", key="s_yt_dictation_check"):
                if not user_input.strip():
                    st.warning("テキストを入力してからチェックしてください")
                else:
                    with st.spinner("AIが添削中..."):
                        result = check_youtube_dictation(user_input)
                    if result.get("success"):
                        feedback = result.get("feedback", {})
                        score = feedback.get("score", 0)
                        st.metric("スコア", f"{score}/100")
                        if score >= 80:
                            st.success("✅ よく書けています！")
                        elif score >= 60:
                            st.info("💪 もう少しです！")
                        else:
                            st.warning("🔄 もう一度聞いてみましょう")

                        if feedback.get("corrections"):
                            st.markdown("**修正箇所:**")
                            for c in feedback["corrections"]:
                                st.markdown(f"- ~~{c.get('original')}~~ → **{c.get('corrected')}** （{c.get('reason')}）")

                        if feedback.get("good_points"):
                            st.markdown(f"**良い点:** {feedback.get('good_points')}")

                        if feedback.get("tip"):
                            st.markdown(f"**💡 アドバイス:** {feedback.get('tip')}")
        else:
            st.warning("有効なYouTube URLを入力してください")


def show_curated_video_list():
    st.markdown("### 📚 おすすめ動画リスト")
    for category_key, category in CURATED_VIDEO_LIST.items():
        if not category['videos']:
            continue
        with st.expander(f"📁 {category['name']}"):
            for video in category['videos']:
                col1, col2 = st.columns([4, 1])
                with col1:
                    st.markdown(f"**{video['title']}** ({video['level']})")
                with col2:
                    if st.button("学習", key=f"learn_{video['id']}"):
                        st.session_state['selected_curated_video'] = video
                        st.rerun()
    if 'selected_curated_video' in st.session_state:
        video = st.session_state['selected_curated_video']
        url = f"https://www.youtube.com/watch?v={video['id']}"
        st.markdown("---")
        st.markdown(f"### 🎬 {video['title']}")
        st.video(url)
        if st.button("🎓 学習素材を生成", type="primary", key="curated_gen"):
            with st.spinner("処理中..."):
                transcript_result = get_transcript_auto(video['id'])
                if transcript_result.get("success"):
                    transcript = transcript_result.get("transcript", "")
                    exercises = generate_exercises_from_transcript(transcript, video['title'], video['level'])
                    difficulty = analyze_video_difficulty(transcript, video['level'])
                    if exercises.get("success"):
                        st.session_state['s_yt_exercises'] = exercises
                        st.session_state['s_yt_difficulty'] = difficulty
                        st.session_state['s_yt_video_url'] = url
                        del st.session_state['selected_curated_video']
                        st.rerun()


def show_student_youtube_content():
    exercises = st.session_state.get('s_yt_exercises', {})
    difficulty = st.session_state.get('s_yt_difficulty', {})
    st.markdown("---")
    if difficulty.get("success"):
        col1, col2 = st.columns(2)
        with col1:
            st.metric("動画レベル", difficulty.get('estimated_cefr', 'N/A'))
        with col2:
            st.metric("適合度", f"{difficulty.get('suitability_score', 'N/A')}/10")
        if difficulty.get('recommendations'):
            st.info(f"💡 {difficulty.get('recommendations')}")
    mode = st.radio(
        "学習モード",
        ["summary", "vocabulary", "quiz", "dictation"],
        format_func=lambda x: {"summary": "📝 要約", "vocabulary": "📚 語彙", "quiz": "❓ クイズ", "dictation": "✏️ ディクテーション"}[x],
        horizontal=True,
        key="yt_mode"
    )
    st.markdown("---")
    if mode == "summary":
        summary = exercises.get('summary', {})
        st.markdown(f"**English:** {summary.get('english', '')}")
        st.markdown(f"**日本語:** {summary.get('japanese', '')}")
    elif mode == "vocabulary":
        for i, v in enumerate(exercises.get('key_vocabulary', []), 1):
            with st.expander(f"{i}. **{v.get('word')}** - {v.get('meaning')}"):
                st.markdown(f"*例:* {v.get('example_from_video', '')}")
    elif mode == "quiz":
        show_youtube_quiz(exercises)
    elif mode == "dictation":
        show_youtube_dictation(exercises)
    st.markdown("---")
    if st.button("🔄 別の動画", key="s_yt_clear"):
        for key in ['s_yt_exercises', 's_yt_difficulty', 's_yt_video_url', 'selected_curated_video', 'yt_quiz_done', 'yt_answers']:
            if key in st.session_state:
                del st.session_state[key]
        st.rerun()


def show_topic_preparation():
    st.markdown("### 💡 トピック予習")
    st.markdown("動画を見る前に語彙やフレーズを準備しよう！")
    st.caption("トピックを入力してボタンを押すと、その話題に関連する重要語彙・フレーズを事前学習できます")
    
    topic = st.text_input("動画のトピック", placeholder="例: ゲーム実況、料理レシピ...", key="topic_input")
    video_desc = st.text_area("動画の説明（任意）", height=80, key="topic_desc")
    level = st.select_slider("レベル", ["A2", "B1", "B2", "C1"], value="B1", key="topic_level")
    
    if st.button("🎓 予習素材を生成", type="primary", disabled=not topic, key="topic_gen"):
        with st.spinner("生成中..."):
            result = generate_learning_from_topic(topic, video_desc, level)
        if result.get("success"):
            st.session_state['topic_materials'] = result
            st.rerun()
    
    if 'topic_materials' in st.session_state:
        materials = st.session_state['topic_materials']
        st.markdown("---")
        topic_summary = materials.get('topic_summary', {})
        if topic_summary:
            st.markdown("### 📝 概要")
            st.markdown(f"**EN:** {topic_summary.get('english', '')}")
            st.markdown(f"**JP:** {topic_summary.get('japanese', '')}")
        vocab = materials.get('key_vocabulary', [])
        if vocab:
            st.markdown("### 📚 覚えておきたい語彙")
            for v in vocab[:10]:
                with st.expander(f"**{v.get('word')}** - {v.get('meaning')}"):
                    st.markdown(f"*例:* {v.get('example', '')}")
        if st.button("🗑️ クリア", key="topic_clear"):
            del st.session_state['topic_materials']
            st.rerun()


def show_youtube_quiz(exercises):
    questions = exercises.get('comprehension_questions', [])
    st.markdown("### ❓ 理解度クイズ")
    if 'yt_quiz_done' not in st.session_state:
        st.session_state.yt_quiz_done = False
    if 'yt_answers' not in st.session_state:
        st.session_state.yt_answers = {}
    if not st.session_state.yt_quiz_done:
        for i, q in enumerate(questions):
            st.markdown(f"**Q{i+1}. {q.get('question')}**")
            ans = st.radio("選択", q.get('options', []), key=f"ytq_{i}", label_visibility="collapsed")
            st.session_state.yt_answers[i] = ans
        if st.button("📤 送信", type="primary", key="yt_quiz_submit"):
            st.session_state.yt_quiz_done = True
            # --- DB保存 ---
            try:
                user = get_current_user()
                if user:
                    from utils.database import log_listening, log_practice
                    correct_count = sum(1 for i, q in enumerate(questions) if st.session_state.yt_answers.get(i) == q.get('correct'))
                    score = correct_count / max(len(questions), 1) * 100
                    video_url = st.session_state.get('s_yt_video_url', '')
                    log_listening(
                        student_id=user['id'],
                        video_url=video_url,
                        video_title=st.session_state.get('s_yt_exercises', {}).get('summary', {}).get('english', '')[:200],
                        activity_type='extensive',
                        quiz_score=score,
                        quiz_results=[{
                            'question': q.get('question', ''),
                            'user_answer': st.session_state.yt_answers.get(i, ''),
                            'correct_answer': q.get('correct', ''),
                            'is_correct': st.session_state.yt_answers.get(i) == q.get('correct')
                        } for i, q in enumerate(questions)],
                    )
                    log_practice(
                        student_id=user['id'],
                        module_type='listening',
                        activity_details={'type': 'youtube_quiz', 'score': score, 'video_url': video_url},
                        score=score,
                    )
            except Exception as e:
                st.error(f"Listening保存エラー: {e}")
            st.rerun()
    else:
        correct = sum(1 for i, q in enumerate(questions) if st.session_state.yt_answers.get(i) == q.get('correct'))
        for i, q in enumerate(questions):
            if st.session_state.yt_answers.get(i) == q.get('correct'):
                st.success(f"Q{i+1}. ✅")
            else:
                st.error(f"Q{i+1}. ❌ 正解: {q.get('correct')}")
        st.markdown(f"### 🎯 Score: {correct}/{len(questions)}")
        if st.button("🔄 もう一度", key="yt_quiz_retry"):
            st.session_state.yt_quiz_done = False
            st.session_state.yt_answers = {}
            st.rerun()


def show_youtube_dictation(exercises):
    segments = exercises.get('dictation_segments', [])
    st.markdown("### ✏️ ディクテーション")
    if not segments:
        st.warning("セグメントがありません")
        return
    idx = st.selectbox("セグメント", range(len(segments)), format_func=lambda i: f"Segment {i+1}", key="dict_seg")
    segment = segments[idx]
    original = segment.get('text', '')
    if st.button("🔊 再生", key="dict_play"):
        with st.spinner("生成中..."):
            audio = generate_audio_with_openai(original)
        if audio:
            st.session_state['yt_dict_audio'] = audio
            st.rerun()
    if 'yt_dict_audio' in st.session_state:
        st.audio(st.session_state['yt_dict_audio'], format='audio/mp3')
    user_input = st.text_area("書き取り", height=100, key="dict_input")
    if user_input and st.button("✅ チェック", type="primary", key="dict_check"):
        result = check_dictation(original, user_input)
        if result.get("success"):
            accuracy = result.get('accuracy_percentage', 0)
            st.metric("正確さ", f"{accuracy}%")
            with st.expander("正解"):
                st.markdown(original)
            try:
                user = get_current_user()
                if user:
                    from utils.database import log_listening, log_practice
                    log_listening(
                        student_id=user['id'],
                        video_url=st.session_state.get('s_yt_video_url', ''),
                        activity_type='practice',
                        quiz_score=accuracy,
                    )
                    log_practice(
                        student_id=user['id'],
                        module_type='listening',
                        activity_details={'type': 'dictation', 'accuracy': accuracy},
                        score=accuracy,
                    )
            except Exception:
                pass


def show_listening_practice():
    st.markdown("### 🎧 リスニング練習")
    materials = load_materials('listening')
    if not materials:
        st.info("リスニング教材がありません")
        return
    options = {key: f"{data['title']} ({data.get('level', '')})" for key, data in materials.items()}
    selected = st.selectbox("素材", list(options.keys()), format_func=lambda x: options[x], key="listen_select")
    if selected:
        material = materials[selected]
        st.markdown(f"### {material['title']}")
        
        key = f"audio_{selected}"
        if key not in st.session_state:
            if st.button("🔊 音声を生成・再生", type="primary", key="listen_play"):
                with st.spinner("生成中..."):
                    if material.get('speakers'):
                        audio = generate_dialogue_audio_with_speakers(material['script'], material.get('speakers'))
                    else:
                        audio = generate_audio_with_openai(material['script'])
                if audio:
                    st.session_state[key] = audio
                    st.rerun()
        else:
            st.audio(st.session_state[key], format='audio/mp3')
            
            # 音声再生後に練習メニューを表示
            st.markdown("---")
            st.markdown("#### 📝 練習メニュー")
            practice_mode = st.radio(
                "練習方法を選択",
                ["script", "quiz", "dictation"],
                format_func=lambda x: {
                    "script": "📜 スクリプトを確認",
                    "quiz": "❓ 理解度クイズ",
                    "dictation": "✏️ ディクテーション（聞き取り書き取り）"
                }[x],
                horizontal=True,
                key="practice_mode_select"
            )
            
            if practice_mode == "script":
                st.markdown(material['script'])
            
            elif practice_mode == "quiz":
                show_material_quiz(material, selected)
            
            elif practice_mode == "dictation":
                show_material_dictation(material, selected)
            
            # ログ保存（音声再生時に1回だけ）
            log_key = f"logged_{selected}"
            if log_key not in st.session_state:
                try:
                    user = get_current_user()
                    if user and user.get('role') != 'teacher':
                        from utils.database import log_listening, log_practice
                        log_listening(
                            student_id=user['id'],
                            video_title=material.get('title', ''),
                            estimated_level=material.get('level', ''),
                            activity_type='practice',
                        )
                        log_practice(
                            student_id=user['id'],
                            module_type='listening',
                            activity_details={'type': 'material_practice', 'title': material.get('title', '')},
                        )
                        st.session_state[log_key] = True
                except Exception:
                    pass


def show_material_quiz(material, material_key):
    """教材の理解度クイズ（AIで生成）"""
    quiz_key = f"material_quiz_{material_key}"
    
    if quiz_key not in st.session_state:
        if st.button("🤖 クイズを生成", type="primary", key=f"gen_quiz_{material_key}"):
            with st.spinner("クイズを生成中..."):
                from utils.listening import generate_quiz_from_script
                result = generate_quiz_from_script(material['script'], material.get('level', 'B1'))
            if result.get("success"):
                st.session_state[quiz_key] = result['questions']
                st.rerun()
            else:
                st.error("クイズの生成に失敗しました")
    else:
        questions = st.session_state[quiz_key]
        submitted_key = f"quiz_submitted_{material_key}"
        answers_key = f"quiz_answers_{material_key}"
        
        if answers_key not in st.session_state:
            st.session_state[answers_key] = {}
        
        if not st.session_state.get(submitted_key):
            for i, q in enumerate(questions):
                st.markdown(f"**Q{i+1}. {q.get('question')}**")
                ans = st.radio("選択", q.get('options', []), key=f"mq_{material_key}_{i}", label_visibility="collapsed")
                st.session_state[answers_key][i] = ans
                st.markdown("---")
            
            if st.button("📤 回答を送信", type="primary", key=f"submit_quiz_{material_key}"):
                st.session_state[submitted_key] = True
                # DB保存
                try:
                    user = get_current_user()
                    if user and user.get('role') != 'teacher':
                        from utils.database import log_listening, log_practice
                        correct = sum(1 for i, q in enumerate(questions) if st.session_state[answers_key].get(i) == q.get('correct'))
                        score = correct / max(len(questions), 1) * 100
                        log_listening(
                            student_id=user['id'],
                            video_title=material.get('title', ''),
                            activity_type='practice',
                            quiz_score=score,
                        )
                        log_practice(
                            student_id=user['id'],
                            module_type='listening',
                            activity_details={'type': 'material_quiz', 'title': material.get('title', ''), 'score': score},
                            score=score,
                        )
                except Exception as e:
                    st.error(f"保存エラー: {e}")
                st.rerun()
        else:
            correct = sum(1 for i, q in enumerate(questions) if st.session_state[answers_key].get(i) == q.get('correct'))
            score = correct / max(len(questions), 1) * 100
            st.markdown(f"### 🎯 Score: {correct}/{len(questions)} ({score:.0f}%)")
            for i, q in enumerate(questions):
                if st.session_state[answers_key].get(i) == q.get('correct'):
                    st.success(f"Q{i+1}. ✅ {q.get('question')}")
                else:
                    st.error(f"Q{i+1}. ❌ 正解: {q.get('correct')}")
                st.info(f"💡 {q.get('explanation', '')}")
                st.markdown("---")
            if st.button("🔄 もう一度", key=f"retry_quiz_{material_key}"):
                del st.session_state[quiz_key]
                del st.session_state[submitted_key]
                st.session_state[answers_key] = {}
                st.rerun()


def show_material_dictation(material, material_key):
    """教材のディクテーション練習"""
    script = material.get('script', '')
    sentences = [s.strip() for s in script.replace('\n', ' ').split('.') if len(s.strip()) > 10]
    
    if not sentences:
        st.warning("ディクテーション用のテキストがありません")
        return
    
    idx = st.selectbox(
        "練習する文を選択",
        range(min(len(sentences), 5)),
        format_func=lambda i: f"文 {i+1}",
        key=f"dict_sent_{material_key}"
    )
    
    sentence = sentences[idx]

    st.info("💡 ① 音声を再生 → ② テキストボックスに入力 → ③「✅ チェック」ボタンを押す")

    if st.button("🔊 音声を再生", type="primary", key=f"dict_play_{material_key}"):
        with st.spinner("生成中..."):
            audio = generate_audio_with_openai(sentence)
        if audio:
            st.session_state[f"dict_audio_{material_key}_{idx}"] = audio
            st.rerun()

    audio_key = f"dict_audio_{material_key}_{idx}"
    if audio_key in st.session_state:
        st.audio(st.session_state[audio_key], format='audio/mp3')
        st.caption("↑ 何度でも再生できます")

    user_input = st.text_area(
        "② 聞こえた通りに入力してください（Enterは改行になります）",
        height=80,
        key=f"dict_input_{material_key}_{idx}"
    )

    if st.button("✅ チェック", type="primary", key=f"dict_check_{material_key}_{idx}"):
        if not user_input.strip():
            st.warning("テキストを入力してからチェックしてください")
        else:
            result = check_dictation(sentence, user_input)
            if result.get("success"):
                accuracy = result.get('accuracy_percentage', 0)
                st.metric("正確さ", f"{accuracy}%")
                if accuracy == 100:
                    st.success("🎉 完璧です！")
                elif accuracy >= 80:
                    st.success("✅ よくできました！")
                else:
                    st.info("💪 もう一度聞いてみましょう")
                if result.get('feedback'):
                    st.info(f"💬 {result.get('feedback')}")
                with st.expander("正解を確認"):
                    st.markdown(f"**{sentence}**")


def show_student_ai_generator():
    st.markdown("### 🤖 AI素材生成")
    st.caption("トピックを入力してボタンを押すと、リスニング素材を生成します")

    prompt = st.text_area("トピック", placeholder="例: 友人との会話", height=80, key="s_ai_prompt")
    level = st.select_slider("レベル", ["A2", "B1", "B2"], value="B1", key="s_ai_level")

    if st.button("🚀 生成", type="primary", disabled=not prompt, key="s_ai_gen"):
        with st.spinner("生成中..."):
            result = generate_listening_from_prompt(prompt, level, "short")
        if result.get("success"):
            st.session_state['s_listening'] = result
            # 音声・ディクテーションのキャッシュをクリア
            for k in ['s_ai_audio_data', 's_ai_dict_audio', 's_ai_dict_input']:
                if k in st.session_state:
                    del st.session_state[k]
            st.success("完了！")

    if 's_listening' in st.session_state:
        data = st.session_state['s_listening']
        st.markdown(f"### {data.get('title', '')}")

        # 練習モード選択
        practice_mode = st.radio(
            "練習方法",
            ["script", "audio", "dictation"],
            format_func=lambda x: {
                "script": "📜 スクリプトを確認",
                "audio": "🔊 音声を聞く",
                "dictation": "✏️ ディクテーション"
            }[x],
            horizontal=True,
            key="s_ai_mode"
        )

        if practice_mode == "script":
            st.markdown(data.get('script', ''))

        elif practice_mode == "audio":
            if st.button("🔊 音声を生成", key="s_ai_audio_btn"):
                with st.spinner("音声生成中..."):
                    audio = generate_audio_with_openai(data.get('script', ''))
                if audio:
                    st.session_state['s_ai_audio_data'] = audio
                    st.rerun()
            if 's_ai_audio_data' in st.session_state:
                st.audio(st.session_state['s_ai_audio_data'], format='audio/mp3')

        elif practice_mode == "dictation":
            script = data.get('script', '')
            sentences = [s.strip() for s in script.replace('\n', ' ').split('.') if len(s.strip()) > 10]

            if not sentences:
                st.warning("ディクテーション用のテキストがありません")
            else:
                idx = st.selectbox(
                    "練習する文を選択",
                    range(min(len(sentences), 5)),
                    format_func=lambda i: f"文 {i+1}",
                    key="s_ai_dict_sent"
                )
                sentence = sentences[idx]

                st.info("💡 ① 音声を再生 → ② テキストボックスに入力 → ③「✅ チェック」ボタンを押す")

                if st.button("🔊 音声を再生", type="primary", key="s_ai_dict_play"):
                    with st.spinner("生成中..."):
                        audio = generate_audio_with_openai(sentence)
                    if audio:
                        st.session_state[f's_ai_dict_audio_{idx}'] = audio
                        st.rerun()

                if f's_ai_dict_audio_{idx}' in st.session_state:
                    st.audio(st.session_state[f's_ai_dict_audio_{idx}'], format='audio/mp3')
                    st.caption("↑ 何度でも再生できます")

                user_input = st.text_area(
                    "② 聞こえた通りに入力してください（Enterは改行になります）",
                    height=80,
                    key=f"s_ai_dict_input_{idx}"
                )

                if st.button("✅ チェック", type="primary", key=f"s_ai_dict_check_{idx}"):
                    if not user_input.strip():
                        st.warning("テキストを入力してからチェックしてください")
                    else:
                        result = check_dictation(sentence, user_input)
                        if result.get("success"):
                            accuracy = result.get('accuracy_percentage', 0)
                            st.metric("正確さ", f"{accuracy}%")
                            if accuracy == 100:
                                st.success("🎉 完璧です！")
                            elif accuracy >= 80:
                                st.success("✅ よくできました！")
                            else:
                                st.info("💪 もう一度聞いてみましょう")
                            if result.get('feedback'):
                                st.info(f"💬 {result.get('feedback')}")
                            with st.expander("正解を確認"):
                                st.markdown(f"**{sentence}**")


def show_listening_progress():
    st.markdown("### 📊 学習記録")
    user = get_current_user()
    if not user:
        return
    try:
        from utils.database import get_student_listening_logs, get_student_practice_details
        logs = get_student_listening_logs(user['id'], days=90)
        practice = get_student_practice_details(user['id'], days=90, module_type='listening')
    except Exception:
        logs = []
        practice = []
    if not logs and not practice:
        st.info("まだ学習記録がありません。リスニング練習を始めましょう！")
        return
    total_sessions = len(logs)
    quiz_scores = [l.get('quiz_score') for l in logs if l.get('quiz_score') is not None]
    avg_score = sum(quiz_scores) / len(quiz_scores) if quiz_scores else 0
    total_practice = len(practice)
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("学習回数", f"{total_sessions + total_practice}回")
    with col2:
        st.metric("平均スコア", f"{avg_score:.0f}%" if quiz_scores else "—")
    with col3:
        types = {}
        for l in logs:
            t = l.get('activity_type', 'practice')
            types[t] = types.get(t, 0) + 1
        most_common = max(types, key=types.get) if types else "—"
        type_labels = {'extensive': 'YouTube学習', 'practice': 'リスニング練習', 'assigned': '課題'}
        st.metric("最多活動", type_labels.get(most_common, most_common))
    st.markdown("---")
    st.markdown("#### 📋 最近の学習")
    recent = sorted(logs, key=lambda x: x.get('completed_at', ''), reverse=True)[:10]
    for l in recent:
        date_str = (l.get('completed_at', '') or '')[:10]
        title = l.get('video_title', '') or l.get('activity_type', '')
        score_str = f" — スコア: {l['quiz_score']:.0f}%" if l.get('quiz_score') is not None else ""
        type_labels = {'extensive': '📺', 'practice': '🎧', 'assigned': '📋'}
        icon = type_labels.get(l.get('activity_type', ''), '🎧')
        st.caption(f"{icon} {date_str} | {title}{score_str}")
