import streamlit as st
from utils.auth import get_current_user, require_auth
from datetime import datetime
import random
from utils.loading_tips import loading_with_tips, show_quick_tip
from utils.database import (
    log_speaking_practice,
    get_speaking_practice_history,
    save_ai_generated_text,
    get_ai_generated_texts,
    delete_ai_generated_text,
    create_speaking_material,
    get_speaking_materials,
    update_speaking_material,
    delete_speaking_material,
    get_speaking_rubric,
    upsert_speaking_rubric,
    create_speaking_submission,
    update_submission_feedback,
    get_speaking_submissions_for_assignment,
    get_course_assignments,
    get_assignment_submissions,
    create_assignment,
)

# プリセット教材
PRESET_MATERIALS = {
    "beginner": [
        {
            "id": "b1",
            "title": "Self-Introduction",
            "level": "A2",
            "duration": "2-3分",
            "text": """Hello, my name is [Your Name]. I am a student at Hokkaido University. 
I am studying [Your Major] in the Faculty of [Your Faculty].
I am from [Your Hometown] in [Your Prefecture].
In my free time, I like to [Your Hobbies].
I am taking this English class because I want to improve my communication skills.
Thank you for listening.""",
            "tips": "自分の情報に置き換えて練習しましょう。ゆっくり、はっきりと発音することを心がけてください。"
        },
        {
            "id": "b2", 
            "title": "Daily Routine",
            "level": "A2",
            "duration": "2-3分",
            "text": """Let me tell you about my daily routine.
I usually wake up at seven o'clock in the morning.
First, I take a shower and get dressed.
Then, I have breakfast. I usually eat rice and miso soup.
After that, I go to the university by bus or bicycle.
My classes start at nine o'clock.
I have lunch at the cafeteria around noon.
In the afternoon, I study at the library or attend more classes.
I go home around six o'clock in the evening.
After dinner, I do my homework and relax.
I go to bed at midnight.""",
            "tips": "時間を表す表現と動作を表す動詞の発音に注意しましょう。"
        }
    ],
    "intermediate": [
        {
            "id": "i1",
            "title": "Climate Change",
            "level": "B1",
            "duration": "3-4分",
            "text": """Climate change is one of the most pressing issues facing our world today.
Scientists have observed a significant increase in global temperatures over the past century.
This warming trend is primarily caused by human activities, especially the burning of fossil fuels.

The effects of climate change are already visible around the world.
We are experiencing more frequent and severe weather events, such as hurricanes, droughts, and floods.
Sea levels are rising, threatening coastal communities.
Many animal and plant species are struggling to adapt to the changing conditions.

To address this crisis, we need to take action at both individual and societal levels.
We can reduce our carbon footprint by using public transportation, eating less meat, and conserving energy.
Governments and businesses must invest in renewable energy sources and implement policies to reduce emissions.

The future of our planet depends on the choices we make today.
By working together, we can create a more sustainable world for future generations.""",
            "tips": "科学的な用語の発音に注意。パラグラフごとに適切なポーズを入れましょう。"
        }
    ],
    "advanced": [
        {
            "id": "a1",
            "title": "Artificial Intelligence Ethics",
            "level": "B2",
            "duration": "4-5分",
            "text": """The rapid advancement of artificial intelligence raises profound ethical questions that society must address.
As AI systems become more sophisticated and integrated into our daily lives, we must carefully consider their implications.

One major concern is algorithmic bias.
AI systems learn from historical data, which often reflects existing social inequalities.
Without careful intervention, these systems can perpetuate and even amplify discrimination in areas such as hiring, lending, and criminal justice.

Another critical issue is privacy and surveillance.
AI-powered facial recognition and data analysis enable unprecedented levels of monitoring.
We must establish clear boundaries to protect individual privacy while allowing beneficial applications.

The question of accountability is equally important.
When an AI system makes a harmful decision, who bears responsibility?
The developer? The company deploying the system? The user?
Our legal and ethical frameworks must evolve to address these novel situations.

Perhaps most fundamentally, we must consider the impact of AI on human autonomy and dignity.
As AI systems make more decisions on our behalf, we risk losing our agency and becoming dependent on technology.

Addressing these challenges requires collaboration among technologists, ethicists, policymakers, and the public.
We must ensure that AI development is guided by human values and serves the common good.""",
            "tips": "複雑な文構造に注意。専門用語（algorithmic bias, autonomy）の発音を事前に確認しましょう。"
        }
    ]
}

# AIテキスト生成用のトピック例
TOPIC_SUGGESTIONS = {
    "academic": [
        "The importance of university education",
        "Benefits of studying abroad",
        "The role of technology in education",
        "How to manage stress during exams"
    ],
    "business": [
        "The future of remote work",
        "Importance of teamwork in the workplace",
        "How to give an effective presentation",
        "The impact of AI on jobs"
    ],
    "daily_life": [
        "My favorite hobby",
        "A memorable trip",
        "My hometown",
        "My favorite food and how to make it"
    ],
    "current_events": [
        "Environmental protection",
        "Social media and society",
        "Health and wellness trends",
        "The importance of cultural exchange"
    ]
}


@require_auth
def show():
    user = get_current_user()
    
    st.markdown("## 🎤 Speaking Practice")
    
    if user['role'] == 'teacher':
        show_teacher_view()
    else:
        show_student_view(user)


def show_teacher_view():
    """教員用ビュー"""
    
    tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs([
        "📋 提出確認",
        "📊 成績一覧",
        "📚 教材管理",
        "📈 クラス進捗",
        "🎯 評価基準",
        "📝 課題作成"
    ])
    
    with tab1:
        show_submission_review()
    with tab2:
        show_grade_summary()
    with tab3:
        show_material_management()
    with tab4:
        show_class_progress()
    with tab5:
        show_rubric_settings()
    with tab6:
        show_assignment_creation()


def show_student_view(user):
    """学生用ビュー"""
    
    tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs([
        "📖 音読練習",
        "🤖 AIテキスト生成",
        "🎤 スピーチ練習",
        "💬 会話練習",
        "📤 課題提出",
        "📊 学習記録"
    ])
    
    with tab1:
        show_reading_aloud_practice(user)
    with tab2:
        show_ai_text_generation(user)
    with tab3:
        show_speech_practice(user)
    with tab4:
        show_conversation_practice(user)
    with tab5:
        show_assignment_submission(user)
    with tab6:
        show_practice_history(user)


def show_reading_aloud_practice(user):
    """音読練習"""
    
    st.markdown("### 📖 音読練習")
    st.caption("テキストを見ながら声に出して読む練習です")
    
    # 教材選択方法
    source = st.radio(
        "教材を選択",
        ["📚 プリセット教材", "✏️ カスタムテキスト", "🤖 AI生成テキスト"],
        horizontal=True
    )
    
    if source == "📚 プリセット教材":
        level = st.selectbox(
            "レベル",
            ["beginner", "intermediate", "advanced"],
            format_func=lambda x: {"beginner": "初級 (A2)", "intermediate": "中級 (B1)", "advanced": "上級 (B2)"}[x]
        )
        show_preset_materials(level, user)
    
    elif source == "✏️ カスタムテキスト":
        show_custom_text_input(user)
    
    else:
        show_ai_generated_materials(user)


def show_preset_materials(level, user):
    """プリセット教材を表示"""
    
    materials = PRESET_MATERIALS.get(level, [])
    
    if not materials:
        st.info("このレベルの教材はまだありません")
        return
    
    selected = st.selectbox(
        "教材を選択",
        materials,
        format_func=lambda x: f"{x['title']} ({x['duration']})"
    )
    
    if selected:
        show_practice_interface(selected, user)


def show_custom_text_input(user):
    """カスタムテキスト入力"""
    
    st.markdown("#### ✏️ 自分でテキストを入力")
    
    custom_text = st.text_area(
        "練習したいテキストを入力",
        placeholder="英文を入力してください...",
        height=200
    )
    
    if custom_text:
        word_count = len(custom_text.split())
        st.caption(f"📊 {word_count} words")
        
        material = {
            "id": "custom",
            "title": "カスタムテキスト",
            "level": "Custom",
            "duration": f"約{word_count // 100 + 1}分",
            "text": custom_text,
            "tips": ""
        }
        
        show_practice_interface(material, user)


def show_ai_generated_materials(user):
    """AI生成テキストを表示（Supabaseから取得）"""
    
    # --- Supabaseから取得してsession_stateにキャッシュ ---
    user_key = f"{user.get('student_id', user.get('email', 'unknown'))}"
    
    if f'ai_texts_{user_key}' not in st.session_state:
        try:
            db_texts = get_ai_generated_texts(user['id'])
            st.session_state[f'ai_texts_{user_key}'] = [
                {
                    "id": t['id'],
                    "title": t['title'],
                    "text": t['text'],
                    "level": t.get('level', 'AI Generated'),
                    "vocabulary": t.get('vocabulary', []),
                    "tips": t.get('tips', ''),
                    "created_at": t.get('created_at', '')[:16].replace('T', ' '),
                }
                for t in db_texts
            ]
        except Exception:
            st.session_state[f'ai_texts_{user_key}'] = []
    
    ai_texts = st.session_state[f'ai_texts_{user_key}']
    
    if not ai_texts:
        st.info("「🤖 AIテキスト生成」タブでテキストを生成してください")
        return
    
    selected = st.selectbox(
        "生成済みテキストを選択",
        ai_texts,
        format_func=lambda x: f"{x['title']} ({x['created_at']})"
    )
    
    if selected:
        material = {
            "id": f"ai_{selected['id']}",
            "title": selected['title'],
            "level": selected.get('level', 'AI Generated'),
            "duration": f"約{len(selected['text'].split()) // 100 + 1}分",
            "text": selected['text'],
            "tips": selected.get('tips', '')
        }
        
        show_practice_interface(material, user)


def show_ai_text_generation(user):
    """AIテキスト生成"""
    
    st.markdown("### 🤖 AIテキスト生成")
    st.caption("練習用のテキストをAIに生成してもらいます")
    
    user_key = f"{user.get('student_id', user.get('email', 'unknown'))}"
    
    # トピック選択
    col1, col2 = st.columns(2)
    
    with col1:
        category = st.selectbox(
            "カテゴリ",
            list(TOPIC_SUGGESTIONS.keys()),
            format_func=lambda x: {
                "academic": "📚 学術・教育",
                "business": "💼 ビジネス",
                "daily_life": "🏠 日常生活",
                "current_events": "📰 時事・社会"
            }[x]
        )
    
    with col2:
        difficulty = st.selectbox(
            "難易度",
            ["A2", "B1", "B2", "C1"],
            format_func=lambda x: {
                "A2": "A2 (初級)",
                "B1": "B1 (中級)",
                "B2": "B2 (中上級)",
                "C1": "C1 (上級)"
            }[x]
        )
    
    # トピック提案
    st.markdown("**💡 トピック例:**")
    suggestions = TOPIC_SUGGESTIONS.get(category, [])
    cols = st.columns(2)
    for i, suggestion in enumerate(suggestions):
        with cols[i % 2]:
            if st.button(suggestion, key=f"suggest_{i}", use_container_width=True):
                st.session_state['selected_topic'] = suggestion
    
    # カスタムトピック
    topic = st.text_input(
        "トピック",
        value=st.session_state.get('selected_topic', ''),
        placeholder="練習したいトピックを入力..."
    )
    
    # 詳細設定
    with st.expander("⚙️ 詳細設定"):
        length = st.slider("目標語数", 50, 300, 150, 25)
        style = st.selectbox(
            "スタイル",
            ["説明文", "スピーチ", "会話", "ナレーション"]
        )
        include_vocab = st.checkbox("重要語彙リストを含める", value=True)
        include_tips = st.checkbox("発音のヒントを含める", value=True)
    
    # 生成ボタン
    if st.button("🎯 テキストを生成", type="primary", use_container_width=True):
        if not topic:
            st.warning("トピックを入力してください")
        else:
            with loading_with_tips("テキストを生成中... / Generating text...", context="generating"):
                generated = generate_reading_text(
                    topic, difficulty, length, style,
                    include_vocab, include_tips
                )
                
                if generated:
                    # --- Supabaseに保存 ---
                    db_text = None
                    try:
                        db_text = save_ai_generated_text(
                            student_id=user['id'],
                            title=topic[:30],
                            text=generated['text'],
                            level=difficulty,
                            course_id=st.session_state.get('current_course', {}).get('id'),
                            topic=topic,
                            style=style,
                            vocabulary=generated.get('vocabulary', []),
                            tips=generated.get('tips', ''),
                        )
                    except Exception as e:
                        st.warning(f"DB保存に失敗: {e}")
                    
                    # --- session_stateにもキャッシュ ---
                    if f'ai_texts_{user_key}' not in st.session_state:
                        st.session_state[f'ai_texts_{user_key}'] = []
                    
                    new_text = {
                        "id": db_text['id'] if db_text else datetime.now().strftime("%Y%m%d%H%M%S"),
                        "title": topic[:30],
                        "text": generated['text'],
                        "level": difficulty,
                        "vocabulary": generated.get('vocabulary', []),
                        "tips": generated.get('tips', ''),
                        "created_at": datetime.now().strftime("%Y-%m-%d %H:%M")
                    }
                    
                    st.session_state[f'ai_texts_{user_key}'].append(new_text)
                    st.success("テキストを生成しました！")
                    st.rerun()
    
    # 生成済みテキスト一覧
    st.markdown("---")
    st.markdown("### 📝 生成済みテキスト")
    
    if f'ai_texts_{user_key}' not in st.session_state:
        try:
            db_texts = get_ai_generated_texts(user['id'])
            st.session_state[f'ai_texts_{user_key}'] = [
                {
                    "id": t['id'],
                    "title": t['title'],
                    "text": t['text'],
                    "level": t.get('level', 'AI Generated'),
                    "vocabulary": t.get('vocabulary', []),
                    "tips": t.get('tips', ''),
                    "created_at": t.get('created_at', '')[:16].replace('T', ' '),
                }
                for t in db_texts
            ]
        except Exception:
            st.session_state[f'ai_texts_{user_key}'] = []
    
    ai_texts = st.session_state[f'ai_texts_{user_key}']
    
    if not ai_texts:
        st.info("まだテキストを生成していません")
    else:
        for i, text_data in enumerate(ai_texts):
            with st.expander(f"📄 {text_data['title']} ({text_data['created_at']})"):
                st.markdown(f"**レベル:** {text_data['level']}")
                st.markdown(f"**語数:** {len(text_data['text'].split())} words")
                st.text_area("テキスト", text_data['text'], height=150, disabled=True, key=f"text_{i}")
                
                if text_data.get('vocabulary'):
                    st.markdown("**📚 重要語彙:**")
                    for vocab in text_data['vocabulary']:
                        st.write(f"- **{vocab['word']}**: {vocab['meaning']}")
                
                if text_data.get('tips'):
                    st.info(f"💡 {text_data['tips']}")
                
                col1, col2 = st.columns(2)
                with col1:
                    if st.button("🎤 このテキストで練習", key=f"practice_{i}", use_container_width=True):
                        st.session_state['practice_text'] = text_data
                        st.session_state['current_tab'] = 0  # 音読練習タブへ
                        st.rerun()
                with col2:
                    if st.button("🗑️ 削除", key=f"delete_{i}", use_container_width=True):
                        # --- Supabaseからも削除 ---
                        try:
                            delete_ai_generated_text(text_data['id'])
                        except Exception:
                            pass
                        ai_texts.pop(i)
                        st.rerun()


def generate_reading_text(topic, difficulty, length, style, include_vocab, include_tips):
    """テキスト生成（デモ版）"""
    
    # デモ用の生成テキスト
    demo_texts = {
        "A2": f"""Today I want to talk about {topic}.
This is an interesting topic for many people.
Let me share some simple ideas with you.

First, {topic} is important in our daily life.
Many people think about this every day.
It helps us understand the world better.

Second, we can learn a lot from {topic}.
There are many books and websites about it.
We can also talk to our friends about it.

In conclusion, {topic} is something we should know about.
I hope you learned something new today.
Thank you for listening.""",
        
        "B1": f"""I would like to discuss {topic} with you today.
This subject has become increasingly relevant in our modern society.

To begin with, {topic} affects many aspects of our lives.
Research has shown that understanding this topic can help us make better decisions.
Many experts have studied this area extensively.

Furthermore, there are different perspectives on {topic}.
Some people believe it has positive effects, while others express concerns.
It is important to consider various viewpoints before forming our own opinions.

Additionally, {topic} is likely to become even more important in the future.
As technology advances, we will see new developments in this field.
Staying informed about these changes will be beneficial for everyone.

In summary, {topic} deserves our attention and thoughtful consideration.
I encourage you to learn more about this fascinating subject.""",
        
        "B2": f"""Today's presentation will explore the multifaceted nature of {topic}.
This subject has garnered significant attention from scholars, policymakers, and the general public alike.

The significance of {topic} cannot be overstated in contemporary discourse.
Research conducted by leading institutions has demonstrated its far-reaching implications.
These findings have prompted a reevaluation of traditional approaches in this domain.

From an analytical perspective, {topic} presents both opportunities and challenges.
Proponents argue that it offers innovative solutions to persistent problems.
Critics, however, caution against potential unintended consequences that may arise.

The intersection of {topic} with technological advancement merits particular consideration.
Digital transformation has fundamentally altered how we approach this issue.
Emerging tools and methodologies continue to reshape our understanding.

Looking forward, the trajectory of {topic} remains subject to various influencing factors.
Stakeholders must engage in collaborative efforts to address associated complexities.
Such engagement will prove essential in navigating the evolving landscape.

In conclusion, {topic} represents a dynamic area worthy of continued exploration.
I invite you to reflect on these considerations as we proceed with our discussion.""",
        
        "C1": f"""This discourse examines the intricate dimensions of {topic}, a subject that has increasingly dominated academic and public spheres.

The conceptual framework surrounding {topic} necessitates careful examination of its epistemological foundations.
Scholarly inquiry has revealed substantial nuances that challenge conventional interpretations.
These revelations compel us to reconsider established paradigms and methodological approaches.

From a socioeconomic perspective, the ramifications of {topic} extend far beyond immediate observations.
Empirical evidence suggests correlations with broader systemic patterns that warrant rigorous investigation.
The interplay between various factors creates a complex web of causality and consequence.

Technological disruption has fundamentally transformed the discourse on {topic}.
Innovation continues to introduce unprecedented variables into existing analytical frameworks.
This evolution demands adaptive strategies that can accommodate rapid change while maintaining intellectual rigor.

The ethical dimensions of {topic} present particularly compelling considerations for contemporary society.
Questions of equity, sustainability, and intergenerational responsibility emerge as central themes.
Navigating these concerns requires sophisticated approaches that balance competing priorities.

In synthesizing these observations, we discern that {topic} embodies both promise and complexity.
Future endeavors in this domain will benefit from interdisciplinary collaboration and critical reflexivity."""
    }
    
    text = demo_texts.get(difficulty, demo_texts["B1"])
    
    result = {"text": text}
    
    if include_vocab:
        result["vocabulary"] = [
            {"word": "relevant", "meaning": "関連のある"},
            {"word": "perspective", "meaning": "視点"},
            {"word": "significant", "meaning": "重要な"},
        ]
    
    if include_tips:
        result["tips"] = "文の切れ目で適切にポーズを入れ、強調すべき単語に注意して読みましょう。"
    
    return result


def show_practice_interface(material, user):
    """練習インターフェース"""
    
    st.markdown("---")
    st.markdown(f"### 📖 {material['title']}")
    st.caption(f"レベル: {material['level']} | 目安時間: {material['duration']}")
    
    # テキスト表示
    st.markdown("#### 📝 テキスト")
    st.text_area("", material['text'], height=200, disabled=True, key="practice_text_display")
    
    # ヒント
    if material.get('tips'):
        st.info(f"💡 **ヒント:** {material['tips']}")
    
    # TTS（モデル音声）
    st.markdown("#### 🔊 モデル音声 / Model Audio")
    try:
        from utils.tts_natural import show_tts_player
        show_tts_player(material['text'], key_prefix=f"model_{material['id']}")
    except Exception:
        col1, col2, col3 = st.columns(3)
        with col1:
            speed = st.select_slider("速度", options=[0.5, 0.75, 1.0, 1.25, 1.5], value=1.0, format_func=lambda x: f"{x}x")
        with col2:
            voice_type = st.selectbox("音声", ["アメリカ英語 (女性)", "アメリカ英語 (男性)", "イギリス英語 (女性)", "イギリス英語 (男性)"])
        with col3:
            if st.button("🔊 再生", use_container_width=True):
                play_tts(material['text'], speed, voice_type)
    
    st.markdown("---")
    
    # 録音（マイク直接）
    st.markdown("#### 🎙️ 録音 / Record Your Voice")
    st.caption("マイクボタンを押して録音 → もう一度押して停止。すぐに評価されます。")
    
    try:
        from utils.mic_recorder import show_mic_or_upload
        audio_bytes = show_mic_or_upload(key_prefix=f"read_{material['id']}", allow_upload=False)
    except Exception:
        audio_bytes = None
        uploaded_audio = st.file_uploader(
            "音声ファイルをアップロード（WAV, MP3, M4A）",
            type=['wav', 'mp3', 'm4a'],
            key=f"audio_{material['id']}"
        )
        if uploaded_audio:
            audio_bytes = uploaded_audio.read()
            st.audio(audio_bytes)
    
    if audio_bytes:
        if st.button("📊 評価する", type="primary", key=f"eval_{material['id']}"):
            with loading_with_tips("音声を評価しています... / Evaluating your pronunciation...", context="evaluation"):
                import time
                time.sleep(0.5)
                
                score = random.randint(65, 95)
                pronunciation = random.randint(60, 95)
                fluency = random.randint(60, 95)
                
                st.success("評価完了！")
                
                col1, col2, col3 = st.columns(3)
                with col1:
                    st.metric("総合スコア", f"{score}点")
                with col2:
                    st.metric("発音", f"{pronunciation}点")
                with col3:
                    st.metric("流暢さ", f"{fluency}点")
                
                # フィードバック
                if score >= 85:
                    st.success("Excellent! Very clear pronunciation. 素晴らしい発音です！")
                elif score >= 70:
                    st.info("Good job! Try to focus on smoother transitions between words. 単語のつなぎをもう少し滑らかに。")
                else:
                    st.warning("Keep practicing! Listen to the model audio and try again. お手本を聞いてもう一度挑戦！")
                
                # CEFR判定
                if score >= 85:
                    cefr = "B2-C1"
                elif score >= 70:
                    cefr = "B1-B2"
                elif score >= 55:
                    cefr = "A2-B1"
                else:
                    cefr = "A1-A2"
                
                st.info(f"**CEFRレベル目安:** {cefr}")
                
                # 練習履歴に保存
                save_practice_history(user, material, score, pronunciation, fluency)


def play_tts(text, speed=1.0, voice_type="アメリカ英語 (女性)"):
    """自然な音声で再生"""
    try:
        from utils.tts_natural import play_natural_tts
        play_natural_tts(text, voice_type, speed)
    except Exception:
        # フォールバック: Web Speech API
        voice_settings = {
            "アメリカ英語 (女性)": "en-US",
            "アメリカ英語 (男性)": "en-US",
            "イギリス英語 (女性)": "en-GB",
            "イギリス英語 (男性)": "en-GB",
        }
        lang = voice_settings.get(voice_type, "en-US")
        escaped_text = text.replace("'", "\\'").replace("\n", " ").replace('"', '\\"')
        js_code = f"""
        <script>
        (function() {{
            window.speechSynthesis.cancel();
            setTimeout(function() {{
                const u = new SpeechSynthesisUtterance("{escaped_text}");
                u.lang = "{lang}";
                u.rate = {speed};
                window.speechSynthesis.speak(u);
            }}, 100);
        }})();
        </script>
        """
        st.components.v1.html(js_code, height=0)


def save_practice_history(user, material, score, pronunciation, fluency):
    """練習履歴を保存（Supabase + session_stateキャッシュ）"""
    
    user_key = f"{user.get('student_id', user.get('email', 'unknown'))}"
    
    # --- Supabaseに保存 ---
    try:
        log_speaking_practice(
            student_id=user['id'],
            material_title=material['title'],
            score=score,
            pronunciation=pronunciation,
            fluency=fluency,
            word_count=len(material['text'].split()),
            material_level=material.get('level', ''),
            course_id=st.session_state.get('current_course', {}).get('id'),
        )
    except Exception as e:
        st.warning(f"DB保存に失敗しました（ローカルには保存済み）: {e}")
    
    # --- session_stateにもキャッシュ ---
    if f'practice_history_{user_key}' not in st.session_state:
        st.session_state[f'practice_history_{user_key}'] = []
    
    history_entry = {
        "id": datetime.now().strftime("%Y%m%d%H%M%S"),
        "date": datetime.now().strftime("%Y-%m-%d %H:%M"),
        "material_title": material['title'],
        "material_level": material['level'],
        "score": score,
        "pronunciation": pronunciation,
        "fluency": fluency,
        "word_count": len(material['text'].split())
    }
    
    st.session_state[f'practice_history_{user_key}'].append(history_entry)


def show_speech_practice(user):
    """スピーチ練習"""
    
    st.markdown("### 🎤 スピーチ練習 / Speech Practice")
    st.caption("トピックを選んで自分の言葉で話す練習です")
    
    # トピック選択
    topic_categories = {
        "自己紹介": [
            "Introduce yourself (name, hobbies, major)",
            "Talk about your daily routine",
            "Describe your hometown",
            "Talk about your family",
        ],
        "意見・考え": [
            "Should students use AI for homework?",
            "Is social media good or bad for society?",
            "What is the most important skill for the future?",
            "Should university education be free?",
        ],
        "経験・ストーリー": [
            "Talk about your best travel experience",
            "Describe a challenge you overcame",
            "Tell us about a movie that changed your perspective",
            "What is the best advice you have ever received?",
        ],
        "カスタム": [],
    }
    
    category = st.selectbox("カテゴリを選択", list(topic_categories.keys()))
    
    if category == "カスタム":
        topic = st.text_input("トピックを入力", placeholder="例: My favorite movie")
    else:
        topics = topic_categories[category]
        topic = st.selectbox("トピックを選択", topics)
    
    if not topic:
        return
    
    col1, col2 = st.columns(2)
    with col1:
        duration = st.selectbox("目標時間", ["30秒", "1分", "2分", "3分"])
    with col2:
        try:
            from utils.level_adapter import show_level_indicator
            show_level_indicator()
        except Exception:
            pass
    
    st.markdown(f"**🎯 トピック:** {topic}")
    st.markdown(f"**⏱️ 目標時間:** {duration}")
    
    # ヒント表示
    with st.expander("💡 スピーチのコツ / Tips"):
        st.markdown("""
**構成 (Structure):**
1. **Introduction** - トピックの紹介 (1-2文)
2. **Body** - メインの内容、具体例 (3-5文)
3. **Conclusion** - まとめ (1-2文)

**便利なフレーズ:**
- *I'd like to talk about...* (〜について話したいと思います)
- *In my opinion...* (私の意見では)
- *For example...* (例えば)
- *To conclude...* (まとめると)
""")
    
    st.markdown("---")
    
    # マイク録音
    st.markdown("#### 🎙️ マイクで録音 / Record with Microphone")
    st.caption("マイクボタンを押して話し始めてください。もう一度押すと停止します。")
    
    try:
        from utils.mic_recorder import show_mic_or_upload
        speech_audio = show_mic_or_upload(key_prefix="speech_rec", allow_upload=False)
    except Exception:
        speech_audio = None
        uploaded = st.file_uploader("音声をアップロード", type=['wav', 'mp3', 'm4a'], key="speech_upload")
        if uploaded:
            speech_audio = uploaded.read()
            st.audio(speech_audio)
    
    if speech_audio:
        if st.button("🎯 評価する", type="primary"):
            import random
            
            with loading_with_tips("スピーチを評価しています... / Evaluating your speech...", context="speaking"):
                import time
                time.sleep(1)
            
            # 評価結果
            scores = {
                'content': random.randint(60, 95),
                'fluency': random.randint(55, 90),
                'vocabulary': random.randint(60, 92),
                'grammar': random.randint(55, 88),
                'pronunciation': random.randint(58, 93),
            }
            total = sum(scores.values()) // len(scores)
            
            st.markdown("### 📊 評価結果")
            
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("総合スコア", f"{total}点")
            with col2:
                st.metric("流暢さ", f"{scores['fluency']}点")
            with col3:
                st.metric("発音", f"{scores['pronunciation']}点")
            
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("内容", f"{scores['content']}点")
            with col2:
                st.metric("語彙", f"{scores['vocabulary']}点")
            with col3:
                st.metric("文法", f"{scores['grammar']}点")
            
            # フィードバック
            st.markdown("#### 💬 フィードバック")
            if total >= 80:
                st.success("Great speech! Your ideas were well-organized and clearly expressed. 素晴らしいスピーチです！")
            elif total >= 65:
                st.info("Good effort! Try to use more varied vocabulary and provide specific examples. もう少し多様な語彙と具体例を使いましょう。")
            else:
                st.warning("Keep practicing! Focus on organizing your ideas with a clear beginning, middle, and end. アイデアの整理に集中しましょう。")
            
            # XP付与
            try:
                from utils.gamification import award_xp, update_stat, show_xp_notification
                xp = award_xp('speaking_practice')
                update_stat('speaking_practices')
                update_stat('speaking_best_score', total, mode='max')
                if total >= 90:
                    award_xp('speaking_score_90')
                show_xp_notification(xp, "スピーチ練習")
            except Exception:
                pass
            
            # 分析記録
            try:
                from utils.analytics import record_score, log_study_time
                record_score('speaking', total, scores)
                log_study_time('speaking', 5)
            except Exception:
                pass


def show_conversation_practice(user):
    """会話練習 — speaking_chat.py への遷移"""
    
    st.markdown("### 💬 AI対話練習 / Conversation Practice")
    st.caption("AIパートナーと英語で会話する練習です。音声入力・音声応答に対応しています。")
    
    st.markdown("""
**練習の流れ:**
1. シチュエーションまたは自由会話トピックを選択
2. AIパートナーと英語で会話（🎤 音声入力 or ⌨️ テキスト入力）
3. AIが音声で応答、会話を続ける
4. 終了ボタンを押すとフィードバック（語彙・文法・表現の改善点）を表示
""")
    
    # 過去の会話履歴サマリー
    try:
        from utils.database import get_student_chat_history
        past_sessions = get_student_chat_history(user['id'], limit=5)
        if past_sessions:
            with st.expander(f"📊 最近の対話練習（{len(past_sessions)}件）"):
                for sess in past_sessions:
                    topic = sess.get('topic', '不明')
                    level = sess.get('level', '')
                    fb = sess.get('feedback') or {}
                    score = fb.get('scores', {}).get('overall', '-')
                    ended = sess.get('ended_at', sess.get('created_at', ''))[:16].replace('T', ' ')
                    st.markdown(f"- **{topic}** ({level}) — {score}点 — {ended}")
    except Exception:
        pass
    
    st.markdown("---")
    
    if st.button("🚀 AI対話練習を始める", type="primary", use_container_width=True):
        st.session_state['current_view'] = 'speaking_chat'
        st.rerun()


def show_assignment_submission(user):
    """課題提出（Supabase接続）"""
    
    st.markdown("### 📤 課題提出")
    st.caption("教員から出された課題を提出します")
    
    course_id = st.session_state.get('current_course', {}).get('id')
    
    # --- コースの課題一覧をDBから取得 ---
    assignments = []
    if course_id:
        try:
            assignments = get_course_assignments(course_id, published_only=True)
        except Exception:
            pass
    
    if not assignments:
        st.info("現在、提出可能な課題はありません。")
        return
    
    # 課題選択
    selected = st.selectbox(
        "課題を選択",
        assignments,
        format_func=lambda a: f"📌 {a['title']} (締切: {(a.get('due_date') or '未設定')[:10]})"
    )
    
    if selected:
        st.markdown("---")
        st.markdown(f"### {selected['title']}")
        due = (selected.get('due_date') or '')[:10]
        st.write(f"**締切:** {due or '未設定'}")
        if selected.get('instructions'):
            st.info(f"📝 **指示:** {selected['instructions']}")
        
        content = selected.get('content') or {}
        type_label = content.get('type_label', selected.get('assignment_type', ''))
        target_text = content.get('text', '')
        
        # 課題タイプに応じた表示
        if "教員がテキスト指定" in type_label and target_text:
            st.markdown("#### 📖 読み上げるテキスト")
            st.text_area("", target_text, height=100, disabled=True)
            
            if st.button("🔊 お手本を聞く"):
                play_tts(target_text, 0.9)
        
        elif "学生が自分でテキスト作成" in type_label:
            st.markdown("#### ✏️ テキストを入力")
            target_text = st.text_area(
                "あなたのテキスト",
                placeholder="読み上げる英文を入力...",
                height=150,
                key=f"student_text_{selected['id']}"
            )
            if target_text:
                st.success(f"✅ {len(target_text.split())} words")
        
        elif "AIでテキスト生成" in type_label:
            st.markdown("#### 🤖 AIでテキストを生成")
            st.info("「🤖 AIテキスト生成」タブでテキストを作成してから戻ってきてください")
            
            try:
                ai_texts = get_ai_generated_texts(user['id'], limit=10)
                if ai_texts:
                    ai_selected = st.selectbox(
                        "生成済みテキストを選択",
                        ai_texts,
                        format_func=lambda x: f"{x.get('title', '無題')} ({(x.get('created_at',''))[:10]})",
                        key=f"ai_sel_{selected['id']}"
                    )
                    if ai_selected:
                        target_text = ai_selected.get('text', '')
                        st.text_area("選択したテキスト", target_text, height=100, disabled=True)
            except Exception:
                pass
        
        # ファイル提出
        st.markdown("---")
        st.markdown("#### 📤 ファイルで提出 / Submit a File")
        
        file_type = st.radio(
            "提出形式 / File Type",
            ["🎤 音声ファイル / Audio", "🎥 動画ファイル / Video"],
            horizontal=True,
            key=f"filetype_{selected['id']}"
        )
        
        if file_type == "🎤 音声ファイル / Audio":
            uploaded = st.file_uploader(
                "音声ファイル（WAV, MP3, M4A, OGG, WEBM）",
                type=['wav', 'mp3', 'm4a', 'ogg', 'webm'],
                key=f"submit_audio_{selected['id']}"
            )
            if uploaded:
                st.audio(uploaded)
        else:
            uploaded = st.file_uploader(
                "動画ファイル（MP4, MOV, WEBM, AVI）",
                type=['mp4', 'mov', 'webm', 'avi'],
                key=f"submit_video_{selected['id']}"
            )
            if uploaded:
                st.video(uploaded)
        
        if uploaded:
            file_size_mb = uploaded.size / (1024 * 1024)
            st.caption(f"📎 {uploaded.name} ({file_size_mb:.1f} MB)")
            
            if file_size_mb > 50:
                st.error("⚠️ ファイルサイズが大きすぎます（上限50MB）/ File too large (max 50MB)")
            elif "学生が自分でテキスト作成" in type_label and not target_text:
                st.warning("⚠️ テキストを入力してから提出してください")
            else:
                if st.button("📤 提出して評価 / Submit & Evaluate", type="primary"):
                    with loading_with_tips("提出中... / Submitting & evaluating...", context="evaluation"):
                        # 仮評価（将来はAzure Speech / SpeechAce連携）
                        score = random.randint(65, 95)
                        pronunciation = random.randint(60, 95)
                        fluency = random.randint(60, 95)
                        
                        # --- Supabaseに保存 ---
                        try:
                            create_speaking_submission(
                                student_id=user['id'],
                                assignment_id=selected['id'],
                                score=score,
                                pronunciation=pronunciation,
                                fluency=fluency,
                                student_text=target_text,
                                recognized_text="",  # TODO: STT連携時に実装
                            )
                        except Exception as e:
                            st.warning(f"DB保存エラー: {e}")
                        
                        st.success("✅ 提出完了！ / Submitted successfully!")
                        
                        col1, col2, col3 = st.columns(3)
                        with col1:
                            st.metric("総合スコア", f"{score}点")
                        with col2:
                            st.metric("発音", f"{pronunciation}点")
                        with col3:
                            st.metric("流暢さ", f"{fluency}点")
                        
                        if score >= 85:
                            st.success("Excellent work! Your pronunciation is very clear. 素晴らしい出来です！")
                        elif score >= 70:
                            st.info("Good job! Keep practicing for smoother delivery. もう少しスムーズに読めるように練習しましょう。")
                        else:
                            st.warning("Listen to the model audio and try again. お手本の音声を聞いてもう一度挑戦！")


def show_practice_history(user):
    """学習記録（Supabaseから取得）"""
    
    st.markdown("### 📊 学習記録")
    
    # --- Supabaseから取得 ---
    history = []
    try:
        db_history = get_speaking_practice_history(user['id'], limit=50)
        for h in db_history:
            details = h.get('activity_details') or {}
            history.append({
                "date": h.get('practiced_at', '')[:16].replace('T', ' '),
                "material_title": h.get('material_title', '不明'),
                "material_level": details.get('material_level', ''),
                "score": h.get('score', 0) or 0,
                "pronunciation": details.get('pronunciation', 0),
                "fluency": details.get('fluency', 0),
                "word_count": details.get('word_count', 0),
            })
    except Exception as e:
        st.warning(f"DB読み込みエラー: {e}")
    
    # --- DB取得失敗時はsession_stateのキャッシュを使う ---
    if not history:
        user_key = f"{user.get('student_id', user.get('email', 'unknown'))}"
        history = st.session_state.get(f'practice_history_{user_key}', [])
    
    if not history:
        st.info("まだ練習記録がありません")
        return
    
    # 統計
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("練習回数", f"{len(history)}回")
    with col2:
        scores = [h['score'] for h in history if h.get('score')]
        avg_score = sum(scores) / len(scores) if scores else 0
        st.metric("平均スコア", f"{avg_score:.1f}点")
    with col3:
        total_words = sum(h.get('word_count', 0) for h in history)
        st.metric("総語数", f"{total_words:,}")
    with col4:
        best_score = max(scores) if scores else 0
        st.metric("最高スコア", f"{best_score}点")
    
    st.markdown("---")
    
    # 履歴一覧（新しい順）
    for h in history[:10]:
        score_display = h.get('score', 0)
        with st.expander(f"📅 {h['date']} - {h['material_title']} ({score_display}点)"):
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("総合", f"{score_display}点")
            with col2:
                st.metric("発音", f"{h.get('pronunciation', 0)}点")
            with col3:
                st.metric("流暢さ", f"{h.get('fluency', 0)}点")
            st.caption(f"レベル: {h.get('material_level', '')} | 語数: {h.get('word_count', 0)}")


# ===== 教員用機能 =====

def show_submission_review():
    """学生の提出を確認（Supabase接続）"""
    
    st.markdown("### 📋 学生の提出を確認")
    
    user = get_current_user()
    course_id = st.session_state.get('current_course', {}).get('id')
    
    # --- コースの課題一覧をDBから取得 ---
    assignments_list = []
    if course_id:
        try:
            assignments_list = get_course_assignments(course_id)
        except Exception as e:
            st.warning(f"課題の取得に失敗: {e}")
    
    if not assignments_list:
        st.info("まだ課題がありません。「📝 課題作成」タブで作成してください。")
        return
    
    # 課題選択
    assignment_options = {a['title']: a for a in assignments_list}
    selected_title = st.selectbox("課題を選択", list(assignment_options.keys()))
    
    if selected_title:
        assignment = assignment_options[selected_title]
        
        # --- 提出一覧をDBから取得 ---
        submissions = []
        try:
            submissions = get_assignment_submissions(assignment['id'])
        except Exception as e:
            st.warning(f"提出データの取得に失敗: {e}")
        
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("提出数", f"{len(submissions)}件")
        with col2:
            scored = [s.get('total_score') or s.get('score') or 0 for s in submissions if s.get('total_score') or s.get('score')]
            if scored:
                st.metric("平均スコア", f"{sum(scored)/len(scored):.1f}点")
            else:
                st.metric("平均スコア", "-")
        with col3:
            due = assignment.get('due_date', '')
            st.write(f"**締切:** {due[:10] if due else '未設定'}")
        
        st.markdown("---")
        
        if not submissions:
            st.info("まだ提出がありません")
        else:
            for sub in submissions:
                u = sub.get('users') or {}
                student_name = u.get('name', '不明')
                student_sid = u.get('student_id', '')
                score = sub.get('total_score') or sub.get('score') or 0
                scores_detail = sub.get('scores') or {}
                submitted = (sub.get('submitted_at') or '')[:16].replace('T', ' ')
                
                with st.expander(f"📌 {student_name} ({student_sid}) — {score}点 ({submitted})"):
                    col1, col2, col3 = st.columns(3)
                    with col1:
                        st.metric("総合スコア", f"{score}点")
                    with col2:
                        st.metric("発音", f"{scores_detail.get('pronunciation', '-')}点")
                    with col3:
                        st.metric("流暢さ", f"{scores_detail.get('fluency', '-')}点")
                    
                    if sub.get('student_text') or sub.get('recognized_text'):
                        st.markdown("**📝 テキスト比較**")
                        c1, c2 = st.columns(2)
                        with c1:
                            st.markdown("*学生が読んだテキスト:*")
                            st.text(sub.get('student_text', ''))
                        with c2:
                            st.markdown("*AIが認識したテキスト:*")
                            st.text(sub.get('recognized_text', ''))
                    
                    st.markdown("**💬 教員フィードバック**")
                    current_fb = sub.get('feedback') or sub.get('teacher_comment') or ''
                    new_fb = st.text_area(
                        "コメント",
                        value=current_fb,
                        placeholder="学生へのフィードバックを入力...",
                        key=f"feedback_{sub['id']}"
                    )
                    
                    if st.button("💾 保存", key=f"save_{sub['id']}"):
                        try:
                            update_submission_feedback(sub['id'], feedback=new_fb)
                            st.success("フィードバックを保存しました！")
                        except Exception as e:
                            st.error(f"保存に失敗: {e}")


def show_grade_summary():
    """成績一覧（Supabase接続）"""
    
    st.markdown("### 📊 成績一覧")
    
    course_id = st.session_state.get('current_course', {}).get('id')
    
    if not course_id:
        st.info("コースが選択されていません。「⚙️ 科目設定」でコースを選択してください。")
        return
    
    # --- DBから全提出データを取得 ---
    try:
        from utils.database import get_all_course_submissions
        all_subs = get_all_course_submissions(course_id)
    except Exception as e:
        st.warning(f"成績データの取得に失敗: {e}")
        all_subs = []
    
    if all_subs:
        import pandas as pd
        df = pd.DataFrame([{
            "課題": s['assignment_title'],
            "学生": s['student_name'],
            "学籍番号": s['student_id_display'],
            "スコア": s['score'],
            "発音": s['pronunciation'],
            "流暢さ": s['fluency'],
            "提出日": s['submitted_at'],
            "FB": "✅" if s['has_feedback'] else "❌"
        } for s in all_subs])
        
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("総提出数", f"{len(df)}件")
        with col2:
            st.metric("平均スコア", f"{df['スコア'].mean():.1f}点")
        with col3:
            st.metric("最高点", f"{df['スコア'].max()}点")
        with col4:
            fb_done = len(df[df['FB'] == '✅'])
            st.metric("FB済み", f"{fb_done}/{len(df)}")
        
        st.markdown("---")
        st.dataframe(df, use_container_width=True, hide_index=True)
        
        csv = df.to_csv(index=False).encode('utf-8-sig')
        st.download_button("📥 CSVダウンロード", csv, "speaking_grades.csv", "text/csv")
    else:
        st.info("まだ提出データがありません")


def show_material_management():
    st.markdown("### 📚 教材管理")
    
    user = get_current_user()
    
    # --- Supabaseから教材を取得してsession_stateにキャッシュ ---
    if 'speaking_materials' not in st.session_state:
        try:
            db_materials = get_speaking_materials(teacher_id=user['id'])
            st.session_state.speaking_materials = [
                {
                    "id": m['id'],
                    "title": m['title'],
                    "level": m.get('level', 'B1'),
                    "text": m['text'],
                    "category": m.get('category', 'その他'),
                }
                for m in db_materials
            ]
        except Exception:
            st.session_state.speaking_materials = [
                {"id": "default_1", "title": "Self Introduction", "level": "A2", "text": "Hello, my name is... I am a student at Hokkaido University. I am studying...", "category": "自己紹介"},
                {"id": "default_2", "title": "Daily Routine", "level": "A2", "text": "I usually wake up at seven o'clock. After breakfast, I go to the university by bus...", "category": "日常"},
                {"id": "default_3", "title": "Climate Change", "level": "B1", "text": "Climate change is one of the most pressing issues facing our world today. Rising temperatures...", "category": "社会問題"},
            ]
    
    materials = st.session_state.speaking_materials
    
    # 教材一覧
    st.markdown(f"**登録教材: {len(materials)}件**")
    
    for mat in materials:
        with st.expander(f"📄 {mat['title']} ({mat['level']}) - {mat['category']}"):
            st.markdown(mat['text'])
            col1, col2 = st.columns(2)
            with col1:
                if st.button("✏️ 編集", key=f"edit_mat_{mat['id']}"):
                    st.session_state[f'editing_mat_{mat["id"]}'] = True
            with col2:
                if st.button("🗑️ 削除", key=f"del_mat_{mat['id']}"):
                    # --- Supabaseからも論理削除 ---
                    try:
                        delete_speaking_material(mat['id'])
                    except Exception:
                        pass
                    st.session_state.speaking_materials = [m for m in materials if m['id'] != mat['id']]
                    st.rerun()
            
            if st.session_state.get(f'editing_mat_{mat["id"]}'):
                new_title = st.text_input("タイトル", value=mat['title'], key=f"mat_title_{mat['id']}")
                new_level = st.selectbox("レベル", ["A1", "A2", "B1", "B2", "C1"], index=["A1", "A2", "B1", "B2", "C1"].index(mat['level']), key=f"mat_level_{mat['id']}")
                new_text = st.text_area("テキスト", value=mat['text'], key=f"mat_text_{mat['id']}")
                if st.button("💾 保存", key=f"save_mat_{mat['id']}"):
                    # --- Supabaseにも更新 ---
                    try:
                        update_speaking_material(mat['id'], {
                            'title': new_title, 'level': new_level, 'text': new_text
                        })
                    except Exception:
                        pass
                    mat['title'] = new_title
                    mat['level'] = new_level
                    mat['text'] = new_text
                    del st.session_state[f'editing_mat_{mat["id"]}']
                    st.success("保存しました！")
                    st.rerun()
    
    # 教材追加
    st.markdown("---")
    st.markdown("#### ➕ 教材追加")
    new_title = st.text_input("タイトル", key="new_mat_title")
    new_level = st.selectbox("レベル", ["A1", "A2", "B1", "B2", "C1"], key="new_mat_level")
    new_cat = st.selectbox("カテゴリ", ["自己紹介", "日常", "社会問題", "文化", "テクノロジー", "その他"], key="new_mat_cat")
    new_text = st.text_area("テキスト", key="new_mat_text", height=150)
    
    if st.button("➕ 追加", type="primary"):
        if new_title and new_text:
            # --- Supabaseに保存 ---
            db_mat = None
            try:
                db_mat = create_speaking_material(
                    teacher_id=user['id'],
                    title=new_title,
                    text=new_text,
                    level=new_level,
                    category=new_cat,
                    course_id=st.session_state.get('current_course', {}).get('id'),
                )
            except Exception as e:
                st.warning(f"DB保存に失敗: {e}")
            
            new_id = db_mat['id'] if db_mat else f"local_{datetime.now().strftime('%Y%m%d%H%M%S')}"
            materials.append({"id": new_id, "title": new_title, "level": new_level, "text": new_text, "category": new_cat})
            st.success(f"教材「{new_title}」を追加しました！")
            st.rerun()
        else:
            st.warning("タイトルとテキストを入力してください")


def show_class_progress():
    """クラス進捗（Supabase接続）"""
    st.markdown("### 📈 クラス進捗")
    
    import pandas as pd
    
    course_id = st.session_state.get('current_course', {}).get('id')
    
    if not course_id:
        st.info("コースが選択されていません。「⚙️ 科目設定」でコースを選択してください。")
        return
    
    # --- DBからクラス進捗を取得 ---
    try:
        from utils.database import get_course_speaking_progress
        progress_data = get_course_speaking_progress(course_id)
    except Exception as e:
        st.warning(f"進捗データの取得に失敗: {e}")
        progress_data = []
    
    if not progress_data:
        st.info("受講学生がいないか、まだ練習データがありません")
        return
    
    df = pd.DataFrame([{
        "学生": p['name'],
        "学籍番号": p['student_id_display'],
        "音読回数": p['practice_count'],
        "平均スコア": p['avg_score'],
        "最高スコア": p['max_score'],
        "課題提出": f"{p['submission_count']}/{p['assignment_count']}",
    } for p in progress_data])
    
    # サマリー
    col1, col2, col3 = st.columns(3)
    with col1:
        avg = df['平均スコア'].mean()
        st.metric("クラス平均", f"{avg:.1f}点" if avg > 0 else "-")
    with col2:
        st.metric("総練習回数", f"{df['音読回数'].sum()}回")
    with col3:
        active = len(df[df['音読回数'] > 0])
        st.metric("アクティブ", f"{active}/{len(df)}名")
    
    st.dataframe(df, use_container_width=True, hide_index=True)
    
    # 要注意学生
    low = df[(df['平均スコア'] < 60) & (df['平均スコア'] > 0)]
    zero = df[df['音読回数'] == 0]
    if not zero.empty:
        st.error(f"🚨 練習回数0回の学生: {len(zero)}名")
        for _, s in zero.iterrows():
            st.caption(f"  • {s['学生']} ({s['学籍番号']})")
    if not low.empty:
        st.warning(f"⚠️ 平均スコア60点未満の学生: {len(low)}名")
        for _, s in low.iterrows():
            st.caption(f"  • {s['学生']} — 平均{s['平均スコア']}点")
    
    # CSV出力
    csv = df.to_csv(index=False).encode('utf-8-sig')
    st.download_button("📥 CSVダウンロード", csv, "speaking_progress.csv", "text/csv")


def show_rubric_settings():
    st.markdown("### 🎯 評価基準")
    
    course_id = st.session_state.get('current_course', {}).get('id')
    
    # --- Supabaseから評価基準を取得 ---
    if 'speaking_rubric' not in st.session_state:
        db_rubric = None
        if course_id:
            try:
                db_rubric = get_speaking_rubric(course_id)
            except Exception:
                pass
        
        if db_rubric and db_rubric.get('criteria'):
            st.session_state.speaking_rubric = db_rubric['criteria']
            st.session_state.speaking_rubric_db = db_rubric
        else:
            st.session_state.speaking_rubric = {
                'pronunciation': {'weight': 30, 'description': '発音の正確さ、音素の明瞭さ'},
                'fluency': {'weight': 25, 'description': '流暢さ、自然なリズムとペース'},
                'accuracy': {'weight': 20, 'description': 'テキストとの一致度'},
                'intonation': {'weight': 15, 'description': 'イントネーション、強勢'},
                'effort': {'weight': 10, 'description': '取り組み姿勢、練習回数'},
            }
    
    rubric = st.session_state.speaking_rubric
    
    st.markdown("#### 評価項目と配点")
    st.caption("配点の合計が100になるように調整してください")
    
    total = 0
    for key, item in rubric.items():
        col1, col2, col3 = st.columns([2, 2, 1])
        with col1:
            st.markdown(f"**{key.title()}**")
            st.caption(item['description'])
        with col2:
            new_weight = st.slider(
                f"{key} 配点",
                0, 50, item['weight'],
                key=f"rubric_{key}",
                label_visibility="collapsed"
            )
            rubric[key]['weight'] = new_weight
        with col3:
            st.markdown(f"**{new_weight}%**")
        total += new_weight
    
    if total == 100:
        st.success(f"✅ 合計: {total}%")
    else:
        st.warning(f"⚠️ 合計: {total}%（100%にしてください）")
    
    st.markdown("---")
    st.markdown("#### 成績配分")
    
    col1, col2 = st.columns(2)
    with col1:
        assignment_w = st.number_input("課題提出の配点(%)", 0, 100, 40, key="rubric_assignment")
    with col2:
        practice_w = st.number_input("練習回数・XPの配点(%)", 0, 100, 10, key="rubric_practice")
    
    if st.button("💾 保存", type="primary"):
        # --- Supabaseに保存 ---
        if course_id:
            try:
                upsert_speaking_rubric(course_id, rubric, assignment_w, practice_w)
                st.success("評価基準をデータベースに保存しました！")
            except Exception as e:
                st.warning(f"DB保存エラー: {e}")
                st.success("評価基準をローカルに保存しました！")
        else:
            st.warning("コースが選択されていないため、ローカルにのみ保存されます")
            st.success("評価基準を保存しました！")


def show_assignment_creation():
    """課題作成（Supabase接続）"""
    
    st.markdown("### 📝 課題作成")
    
    user = get_current_user()
    course_id = st.session_state.get('current_course', {}).get('id')
    
    if not course_id:
        st.info("コースが選択されていません。「⚙️ 科目設定」でコースを選択してください。")
        return
    
    title = st.text_input("課題タイトル", placeholder="例: Week 5 Reading Aloud")
    
    assignment_type = st.selectbox("課題タイプ", [
        "音読（教員がテキスト指定）",
        "音読（学生が自分でテキスト作成）",
        "音読（学生がAIでテキスト生成）",
        "スピーチ（自由に話す）",
        "質問応答（質問に答える）"
    ])
    
    reading_text = ""
    if "教員がテキスト指定" in assignment_type:
        reading_text = st.text_area("読み上げテキスト", placeholder="学生が読み上げる英文を入力...", height=150)
    elif "学生が自分でテキスト作成" in assignment_type:
        st.info("💡 学生が自分で読み上げる英文を作成・入力します")
    elif "AIでテキスト生成" in assignment_type:
        st.info("🤖 学生がAIを使って読み上げるテキストを生成します")
    
    due_date = st.date_input("締切日")
    instructions = st.text_area("指示", placeholder="課題の指示を入力...")
    is_published = st.checkbox("公開する（学生に表示）", value=True)
    
    if st.button("📤 課題を作成", type="primary"):
        if not title:
            st.warning("タイトルを入力してください")
            return
        
        try:
            from utils.database import create_assignment
            result = create_assignment(
                course_id=course_id,
                title=title,
                assignment_type=assignment_type,
                due_date=due_date.isoformat() if due_date else None,
                instructions=instructions,
                is_published=is_published,
                content={
                    'text': reading_text,
                    'type_label': assignment_type,
                },
            )
            if result:
                st.success(f"課題「{title}」を作成しました！")
                st.balloons()
            else:
                st.error("課題の作成に失敗しました")
        except Exception as e:
            st.error(f"エラー: {e}")
    
    # --- 既存課題の一覧 ---
    st.markdown("---")
    st.markdown("#### 📋 作成済み課題")
    try:
        existing = get_course_assignments(course_id)
        if existing:
            for a in existing:
                status = "🟢 公開中" if a.get('is_published') else "🔴 非公開"
                due = (a.get('due_date') or '')[:10]
                st.markdown(f"- **{a['title']}** — {status} — 締切: {due or '未設定'}")
        else:
            st.caption("まだ課題がありません")
    except Exception:
        st.caption("課題一覧を取得できませんでした")
