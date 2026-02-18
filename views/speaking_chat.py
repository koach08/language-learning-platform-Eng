import streamlit as st
from utils.auth import get_current_user, require_auth
from utils.chat_ai import get_ai_response, get_session_feedback, SITUATIONS, FREE_TOPICS
from components.web_speech import text_to_speech_openai, play_audio_autoplay
from utils.database import save_chat_session_full, get_student_chat_history
import time


def _get_course_id(user) -> str:
    """course_idを複数ソースから解決"""
    cid = st.session_state.get('submit_course_id')
    if cid:
        return cid
    cid = st.session_state.get('current_course', {}).get('id')
    if cid:
        return cid
    try:
        from utils.database import get_student_enrollments
        enrollments = get_student_enrollments(user['id'])
        if enrollments:
            course = enrollments[0].get('courses')
            if course:
                return course.get('id')
    except Exception:
        pass
    return user.get('class_key')

@require_auth
def _play_web_speech_fallback(text: str, lang: str = "en-US", speed: float = 1.0):
    """OpenAI TTS失敗時のブラウザ音声フォールバック"""
    escaped = text.replace("'", "\\'").replace('"', '\\"').replace("\n", " ")
    st.components.v1.html(
        f"""<script>
        (function() {{
            window.speechSynthesis.cancel();
            setTimeout(function() {{
                var u = new SpeechSynthesisUtterance('{escaped}');
                u.lang = '{lang}';
                u.rate = {speed};
                window.speechSynthesis.speak(u);
            }}, 150);
        }})();
        </script>""",
        height=0
    )


def show():
    user = get_current_user()
    
    # セッション初期化
    if 'chat_messages' not in st.session_state:
        st.session_state.chat_messages = []
    if 'chat_started' not in st.session_state:
        st.session_state.chat_started = False
    if 'chat_situation' not in st.session_state:
        st.session_state.chat_situation = None
    if 'chat_level' not in st.session_state:
        st.session_state.chat_level = "B1"
    if 'show_feedback' not in st.session_state:
        st.session_state.show_feedback = False
    if 'used_voice_input' not in st.session_state:
        st.session_state.used_voice_input = False
    
    # 画面分岐
    if st.session_state.show_feedback:
        show_feedback_screen()
    elif not st.session_state.chat_started:
        show_setup_screen()
    else:
        show_chat_screen()


def show_setup_screen():
    """対話開始前の設定画面"""
    user = get_current_user()
    
    st.markdown("## 💬 AI対話練習")
    
    # 戻るボタン
    if st.button("← Speaking Practiceに戻る"):
        reset_chat(navigate=False)
        st.session_state['current_view'] = 'speaking'
        st.rerun()
    
    st.markdown("---")
    
    st.markdown("### 🎯 対話練習の設定")
    
    st.markdown("#### あなたの英語レベル")
    level = st.select_slider(
        "レベルを選択",
        options=["A1", "A2", "B1", "B2", "C1"],
        value="B1",
        help="A1: 初級 → C1: 上級"
    )
    st.session_state.chat_level = level
    
    level_descriptions = {
        "A1": "基本的な挨拶や自己紹介ができる",
        "A2": "日常的な話題について簡単な会話ができる",
        "B1": "身近な話題について意見を言える",
        "B2": "幅広い話題について流暢に会話できる",
        "C1": "複雑な話題でも自然に議論できる"
    }
    st.caption(f"📖 {level_descriptions[level]}")
    
    st.markdown("---")
    st.markdown("#### 練習モードを選択")
    
    tab1, tab2 = st.tabs(["🎭 シチュエーション別", "💭 自由会話"])
    
    with tab1:
        st.markdown("実際の場面を想定した会話練習")
        
        categories = {}
        for key, situation in SITUATIONS.items():
            cat = situation.get('category', 'その他')
            if cat not in categories:
                categories[cat] = []
            categories[cat].append((key, situation))
        
        for category, items in categories.items():
            st.markdown(f"**{category}**")
            cols = st.columns(2)
            for i, (key, situation) in enumerate(items):
                with cols[i % 2]:
                    if st.button(
                        f"{situation['icon']} {situation['name']}", 
                        key=f"sit_{key}",
                        use_container_width=True
                    ):
                        start_chat(key, level)
    
    with tab2:
        st.markdown("トピックを選んで自由に会話")
        
        cols = st.columns(2)
        for i, (key, topic) in enumerate(FREE_TOPICS.items()):
            with cols[i % 2]:
                if st.button(
                    f"{topic['icon']} {topic['name']}", 
                    key=f"free_{key}",
                    use_container_width=True
                ):
                    start_chat(key, level)


def start_chat(situation_key, level):
    """チャットを開始"""
    st.session_state.chat_started = True
    st.session_state.chat_situation = situation_key
    st.session_state.chat_level = level
    st.session_state.chat_messages = []
    st.session_state.chat_start_time = time.time()
    st.session_state.show_feedback = False
    st.session_state.used_voice_input = False
    st.session_state.chat_session_saved = False
    st.rerun()


def show_chat_screen():
    """チャット画面"""
    
    situation_key = st.session_state.chat_situation
    level = st.session_state.chat_level
    user_turns = len([m for m in st.session_state.chat_messages if m["role"] == "user"])
    
    # === ヘッダー: タイトル + 終了ボタン ===
    col_title, col_end = st.columns([3, 1])
    with col_title:
        if situation_key in FREE_TOPICS:
            topic = FREE_TOPICS[situation_key]
            st.markdown(f"### {topic['icon']} {topic['name']}")
        elif situation_key in SITUATIONS:
            situation = SITUATIONS[situation_key]
            st.markdown(f"### {situation['icon']} {situation['name']}")
        else:
            st.markdown("### 💬 対話練習")
        st.caption(f"レベル: {level} ｜ ターン: {user_turns}")
    with col_end:
        if st.button("🔚 終了 → フィードバック", type="primary", use_container_width=True):
            st.session_state.show_feedback = True
            st.rerun()
    
    st.markdown("---")
    
    # === 最初のメッセージ（AI先攻） ===
    if not st.session_state.chat_messages:
        initial_message = get_ai_response(
            messages=[],
            situation=situation_key,
            level=level,
            is_first=True
        )
        st.session_state.chat_messages.append({
            "role": "assistant",
            "content": initial_message
        })
        # OpenAI TTSで音声生成
        audio = text_to_speech_openai(initial_message, voice="nova")
        if audio:
            play_audio_autoplay(audio)
        else:
            # フォールバック: Web Speech API
            _play_web_speech_fallback(initial_message)
    
    # === メッセージ表示 ===
    messages = st.session_state.chat_messages
    # 最新AIメッセージのインデックスを取得
    last_ai_idx = None
    for i, msg in enumerate(messages):
        if msg["role"] == "assistant":
            last_ai_idx = i

    for idx, msg in enumerate(messages):
        if msg["role"] == "assistant":
            with st.chat_message("assistant", avatar="🤖"):
                st.markdown(msg["content"])
                is_latest = (idx == last_ai_idx)
                if is_latest and st.session_state.get('_auto_play_latest', False):
                    # 最新メッセージ: 自動再生
                    audio = text_to_speech_openai(msg["content"], voice="nova")
                    if audio:
                        play_audio_autoplay(audio, show_controls=True)
                    else:
                        _play_web_speech_fallback(msg["content"])
                    st.session_state['_auto_play_latest'] = False
                else:
                    # 過去メッセージ: 🔊ボタン
                    if st.button("🔊", key=f"play_{idx}_{hash(msg['content'])}", help="音声を再生"):
                        audio = text_to_speech_openai(msg["content"], voice="nova")
                        if audio:
                            play_audio_autoplay(audio, show_controls=True)
                        else:
                            _play_web_speech_fallback(msg["content"])
        else:
            with st.chat_message("user", avatar="👤"):
                st.markdown(msg["content"])
                if msg.get("input_type") == "voice":
                    st.caption("🎤 音声入力")
                else:
                    st.caption("⌨️ テキスト入力")
    
    st.markdown("---")
    
    # === ヒントボタン ===
    with st.expander("💡 ヒントが必要ですか？"):
        if st.button("ヒントを表示", key="hint_btn"):
            hint = get_ai_response(
                messages=st.session_state.chat_messages,
                situation=situation_key,
                level=level,
                request_hint=True
            )
            st.info(f"💡 {hint}")
    
    # === 入力セクション: 音声メイン ===
    st.markdown("### 🎤 あなたの番です")
    
    # 音声入力（Streamlitネイティブ — 全ブラウザ対応）
    audio_value = st.audio_input("🎤 マイクで録音してから送信", key="voice_rec")
    
    if audio_value is not None:
        # 重複処理防止
        audio_key = f"{audio_value.name}_{audio_value.size}"
        if st.session_state.get('_last_audio_key') != audio_key:
            st.session_state['_last_audio_key'] = audio_key
            _process_whisper_audio(audio_value, situation_key, level)
    
    # テキスト入力（フォールバック）
    st.caption("⌨️ テキスト入力も使えます:")
    user_input = st.chat_input("英語で話しかけてみましょう...")
    
    if user_input:
        process_user_input(user_input, situation_key, level, is_voice=False)


def _process_whisper_audio(audio_file, situation_key, level):
    """録音音声をWhisper APIで文字起こしして対話に送信"""
    import tempfile
    import os
    
    with st.spinner("🎤 音声を文字起こし中..."):
        try:
            # 一時ファイルに書き出し
            with tempfile.NamedTemporaryFile(suffix='.wav', delete=False) as tmp:
                tmp.write(audio_file.getvalue())
                tmp_path = tmp.name
            
            try:
                from openai import OpenAI
                client = OpenAI(api_key=st.secrets["openai"]["api_key"])
                
                with open(tmp_path, 'rb') as f:
                    transcript = client.audio.transcriptions.create(
                        model="whisper-1",
                        file=f,
                        language="en",
                        response_format="text"
                    )
                
                text = transcript.strip() if isinstance(transcript, str) else transcript.text.strip()
            finally:
                os.unlink(tmp_path)
            
            if text:
                process_user_input(text, situation_key, level, is_voice=True)
            else:
                st.warning("音声を認識できませんでした。もう一度話してみてください。")
                
        except Exception as e:
            st.error(f"音声認識エラー: {e}")
            st.caption("テキスト入力をお使いください。")


def process_user_input(user_input, situation_key, level, is_voice=False):
    """ユーザー入力を処理"""
    
    if is_voice:
        st.session_state.used_voice_input = True
    
    st.session_state.chat_messages.append({
        "role": "user",
        "content": user_input,
        "input_type": "voice" if is_voice else "text"
    })
    
    with st.spinner(""):
        ai_response = get_ai_response(
            messages=st.session_state.chat_messages,
            situation=situation_key,
            level=level
        )
    
    st.session_state.chat_messages.append({
        "role": "assistant",
        "content": ai_response
    })
    
    # 自動再生フラグを立てる（rerun後のメッセージ表示ループで最新AIメッセージを自動再生）
    st.session_state['_auto_play_latest'] = True
    
    st.rerun()


def show_feedback_screen():
    """フィードバック画面"""
    
    st.markdown("## 📊 セッションフィードバック")
    
    user = get_current_user()
    messages = st.session_state.chat_messages
    level = st.session_state.chat_level
    situation = st.session_state.chat_situation
    used_voice = st.session_state.used_voice_input
    
    user_messages = [m for m in messages if m["role"] == "user"]
    if len(user_messages) < 2:
        st.warning("会話が短すぎるため、詳細なフィードバックを生成できません。もう少し会話を続けてみましょう。")
        
        col1, col2 = st.columns(2)
        with col1:
            if st.button("🔙 会話に戻る", type="primary"):
                st.session_state.show_feedback = False
                st.rerun()
        with col2:
            if st.button("🔄 新しい対話を始める"):
                reset_chat()
        return
    
    if used_voice:
        st.success("🎤 音声入力を使用しました → 発音アドバイスを含むフィードバック")
    else:
        st.info("⌨️ テキスト入力のみ → 次回は音声入力で発音も練習してみましょう！")
    
    with st.spinner("フィードバックを生成中..."):
        feedback = get_session_feedback(messages, level, situation, used_voice_input=used_voice)
    
    if feedback.get("success"):
        display_feedback(feedback)
        
        # --- Supabaseにセッションを保存 ---
        if not st.session_state.get('chat_session_saved'):
            try:
                # トピック名を取得
                topic_name = situation
                if situation in SITUATIONS:
                    topic_name = SITUATIONS[situation].get('name', situation)
                elif situation in FREE_TOPICS:
                    topic_name = FREE_TOPICS[situation].get('name', situation)
                
                save_chat_session_full(
                    student_id=user['id'],
                    messages=messages,
                    situation_key=situation,
                    level=level,
                    feedback=feedback,
                    used_voice_input=used_voice,
                    course_id=_get_course_id(user),
                    topic=topic_name,
                )
                st.session_state.chat_session_saved = True
            except Exception as e:
                st.caption(f"⚠️ セッション保存エラー: {e}")
    else:
        st.error(f"フィードバック生成エラー: {feedback.get('error', '不明なエラー')}")
    
    st.markdown("---")
    
    col1, col2 = st.columns(2)
    with col1:
        if st.button("🔄 新しい対話を始める", type="primary", use_container_width=True):
            reset_chat()
    with col2:
        if st.button("← Speaking Practiceに戻る", use_container_width=True):
            reset_chat(navigate=False)
            st.session_state['current_view'] = 'speaking'
            st.rerun()


def display_feedback(feedback):
    """フィードバックを表示"""
    
    scores = feedback.get("scores", {})
    used_voice = feedback.get("used_voice_input", False)
    
    st.markdown("### 📈 スコア")
    
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("総合", f"{scores.get('overall', 0)}/100")
    with col2:
        st.metric("語彙", f"{scores.get('vocabulary', 0)}/100")
    with col3:
        st.metric("文法", f"{scores.get('grammar', 0)}/100")
    with col4:
        st.metric("コミュニケーション", f"{scores.get('communication', 0)}/100")
    
    good_points = feedback.get("good_points", [])
    if good_points:
        st.markdown("### ✅ 良かった点")
        for point in good_points:
            st.markdown(f"- {point}")
    
    if feedback.get("feedback"):
        st.markdown("### 💬 フィードバック")
        st.info(feedback.get("feedback"))
    
    improvements = feedback.get("improvements", [])
    if improvements:
        st.markdown("### ✨ より自然な表現例")
        for imp in improvements:
            st.markdown(f"❌ **あなた:** {imp.get('original', '')}")
            st.markdown(f"✅ **より自然:** {imp.get('improved', '')}")
            st.caption(f"💡 {imp.get('explanation', '')}")
            st.markdown("---")
    
    pronunciation_tips = feedback.get("pronunciation_tips")
    if pronunciation_tips and used_voice:
        st.markdown("### 🎤 発音・通じやすさのアドバイス")
        st.markdown(pronunciation_tips)
    
    speaking_tip = feedback.get("speaking_practice_tip")
    if speaking_tip:
        st.markdown("### 🗣️ 実際の会話に向けて")
        st.markdown(speaking_tip)
    
    if feedback.get("advice"):
        st.markdown("### 📚 次のステップ")
        st.success(feedback.get("advice"))


def reset_chat(navigate=True):
    """チャットをリセット"""
    st.session_state.chat_started = False
    st.session_state.chat_messages = []
    st.session_state.chat_situation = None
    st.session_state.show_feedback = False
    st.session_state.used_voice_input = False
    st.session_state.chat_session_saved = False
    if navigate:
        st.rerun()
