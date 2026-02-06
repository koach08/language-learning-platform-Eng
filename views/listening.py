import streamlit as st
from utils.auth import get_current_user, require_auth
from utils.listening import (
    DEMO_LISTENING,
    generate_audio_with_openai,
    generate_dialogue_audio_with_speakers,
    check_dictation,
    generate_listening_from_prompt
)
from utils.listening_youtube import (
    extract_youtube_id,
    get_youtube_transcript,
    get_transcript_auto,
    generate_exercises_from_transcript,
    analyze_video_difficulty,
    generate_learning_from_topic,
    CURATED_VIDEO_LIST
)

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
        "🤖 AI素材生成",
        "📺 YouTube（自動字幕）",
        "📋 動画リスト管理",
        "📚 素材一覧",
        "📊 学習状況"
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
                st.success(f"「{new_title}」を追加しました！（※デモ）")
    
    st.markdown("---")
    for category_key, category in CURATED_VIDEO_LIST.items():
        with st.expander(f"📁 {category['name']} ({len(category['videos'])}本)"):
            st.caption(category['description'])
            for video in category['videos']:
                st.markdown(f"**{video['title']}** ({video['level']})")


def show_ai_listening_generator():
    st.markdown("### 🤖 AIでリスニング素材を生成")
    
    prompt = st.text_area("トピック", placeholder="例: カフェでの注文", height=80, key="t_ai_prompt")
    col1, col2 = st.columns(2)
    with col1:
        level = st.select_slider("レベル", ["A2", "B1", "B2", "C1"], value="B1", key="t_ai_level")
    with col2:
        duration = st.selectbox("長さ", ["short", "medium", "long"],
                               format_func=lambda x: {"short": "短い", "medium": "中程度", "long": "長い"}[x], key="t_ai_dur")
    
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
    for key, material in DEMO_LISTENING.items():
        with st.expander(f"🎧 {material['title']} ({material['level']})"):
            st.markdown(material['script'][:200] + "...")


def show_class_listening_progress():
    st.markdown("### 📊 学習状況")
    st.info("データベース接続後に表示されます")


# ==================== 学生用 ====================

def show_student_view():
    tab1, tab2, tab3, tab4, tab5 = st.tabs([
        "📺 YouTube学習",
        "💡 トピック予習",
        "🎧 リスニング練習",
        "🤖 AI素材生成",
        "📊 学習記録"
    ])
    
    with tab1:
        show_youtube_learning_student()
    with tab2:
        show_topic_preparation()
    with tab3:
        show_listening_practice()
    with tab4:
        show_student_ai_generator()
    with tab5:
        show_listening_progress()


def show_youtube_learning_student():
    st.markdown("### 📺 YouTube動画で学習")
    
    method = st.radio(
        "学習方法を選択",
        ["url", "curated"],
        format_func=lambda x: {"url": "🔗 URLを入力", "curated": "📚 おすすめから選ぶ"}[x],
        horizontal=True,
        key="yt_method"
    )
    
    if method == "url":
        show_youtube_url_input()
    else:
        show_curated_video_list()


def show_youtube_url_input():
    st.markdown("💡 **ヒント:** 日本語で知っているテーマの英語動画を選ぶと効果的！")
    
    url = st.text_input("YouTube URL", placeholder="https://www.youtube.com/watch?v=...", key="s_yt_url_input")
    col1, col2 = st.columns(2)
    with col1:
        video_title = st.text_input("動画タイトル（任意）", key="s_yt_title_input")
    with col2:
        level = st.select_slider("あなたのレベル", ["A2", "B1", "B2", "C1"], value="B1", key="s_yt_level_input")
    
    if url:
        video_id = extract_youtube_id(url)
        if video_id:
            st.video(url)
            
            if st.button("🎓 この動画で学習を開始", type="primary", key="s_yt_start"):
                with st.spinner("字幕を取得中..."):
                    transcript_result = get_transcript_auto(video_id)
                
                if not transcript_result.get("success"):
                    st.error(f"❌ {transcript_result.get('error')}")
                else:
                    if transcript_result.get("method") == "whisper":
                        st.info("🎤 AIで音声認識しました")
                    
                    transcript = transcript_result.get("transcript", "")
                    with st.spinner("学習素材を生成中..."):
                        difficulty = analyze_video_difficulty(transcript, level)
                        exercises = generate_exercises_from_transcript(
                            transcript, video_title or transcript_result.get("title", ""), level
                        )
                    
                    if exercises.get("success"):
                        st.session_state['s_yt_exercises'] = exercises
                        st.session_state['s_yt_difficulty'] = difficulty
                        st.session_state['s_yt_video_url'] = url
                        st.success("✅ 準備完了！")
                        st.rerun()
        else:
            st.warning("有効なYouTube URLを入力してください")
    
    if 's_yt_exercises' in st.session_state:
        show_student_youtube_content()


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
    
    topic = st.text_input("動画のトピック", placeholder="例: ゲーム実況、料理レシピ...", key="topic_input")
    video_desc = st.text_area("動画の説明（任意）", height=80, key="topic_desc")
    level = st.select_slider("レベル", ["A2", "B1", "B2", "C1"], value="B1", key="topic_level")
    
    if topic and st.button("🎓 予習素材を生成", type="primary", key="topic_gen"):
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
            st.metric("正確さ", f"{result.get('accuracy_percentage', 0)}%")
            with st.expander("正解"):
                st.markdown(original)


def show_listening_practice():
    st.markdown("### 🎧 リスニング練習")
    options = {key: f"{data['title']} ({data['level']})" for key, data in DEMO_LISTENING.items()}
    selected = st.selectbox("素材", list(options.keys()), format_func=lambda x: options[x], key="listen_select")
    
    if selected:
        material = DEMO_LISTENING[selected]
        st.markdown(f"### {material['title']}")
        
        key = f"audio_{selected}"
        if key not in st.session_state:
            if st.button("🔊 再生", type="primary", key="listen_play"):
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
            if st.checkbox("📜 スクリプト", key="listen_script"):
                st.markdown(material['script'])


def show_student_ai_generator():
    st.markdown("### 🤖 AI素材生成")
    prompt = st.text_area("トピック", placeholder="例: 友人との会話", height=80, key="s_ai_prompt")
    level = st.select_slider("レベル", ["A2", "B1", "B2"], value="B1", key="s_ai_level")
    
    if st.button("🚀 生成", type="primary", disabled=not prompt, key="s_ai_gen"):
        with st.spinner("生成中..."):
            result = generate_listening_from_prompt(prompt, level, "short")
        if result.get("success"):
            st.session_state['s_listening'] = result
            st.success("完了！")
    
    if 's_listening' in st.session_state:
        data = st.session_state['s_listening']
        st.markdown(f"### {data.get('title', '')}")
        with st.expander("📜 スクリプト"):
            st.markdown(data.get('script', ''))


def show_listening_progress():
    st.markdown("### 📊 学習記録")
    st.info("データベース接続後に表示されます")
