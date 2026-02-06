"""
自然な音声合成モジュール (Natural TTS)

優先順位:
1. Edge TTS (無料、高品質、Microsoft Neural Voices)
2. OpenAI TTS (高品質、API課金あり)
3. Web Speech API (ブラウザ内蔵、フォールバック)
"""

import streamlit as st
import base64
import asyncio
import os
import tempfile
import hashlib


# ===== 音声設定 =====

VOICE_OPTIONS = {
    "アメリカ英語 (女性)": {
        "edge": "en-US-JennyNeural",
        "openai": "nova",
        "lang": "en-US",
        "label": "US Female (Jenny)",
    },
    "アメリカ英語 (男性)": {
        "edge": "en-US-GuyNeural",
        "openai": "onyx",
        "lang": "en-US",
        "label": "US Male (Guy)",
    },
    "イギリス英語 (女性)": {
        "edge": "en-GB-SoniaNeural",
        "openai": "shimmer",
        "lang": "en-GB",
        "label": "UK Female (Sonia)",
    },
    "イギリス英語 (男性)": {
        "edge": "en-GB-RyanNeural",
        "openai": "echo",
        "lang": "en-GB",
        "label": "UK Male (Ryan)",
    },
    "オーストラリア英語 (女性)": {
        "edge": "en-AU-NatashaNeural",
        "openai": "nova",
        "lang": "en-AU",
        "label": "AU Female (Natasha)",
    },
    "カナダ英語 (女性)": {
        "edge": "en-CA-ClaraNeural",
        "openai": "alloy",
        "lang": "en-CA",
        "label": "CA Female (Clara)",
    },
}

DEFAULT_VOICE = "アメリカ英語 (女性)"


# ===== キャッシュ =====

def _get_cache_key(text, voice, speed):
    """キャッシュキーを生成"""
    raw = f"{text[:500]}_{voice}_{speed}"
    return hashlib.md5(raw.encode()).hexdigest()


def _get_from_cache(cache_key):
    """キャッシュから取得"""
    cache = st.session_state.get('tts_cache', {})
    return cache.get(cache_key)


def _save_to_cache(cache_key, audio_data):
    """キャッシュに保存（最大20件）"""
    if 'tts_cache' not in st.session_state:
        st.session_state.tts_cache = {}
    
    cache = st.session_state.tts_cache
    
    # 古いキャッシュを削除
    if len(cache) >= 20:
        oldest = list(cache.keys())[0]
        del cache[oldest]
    
    cache[cache_key] = audio_data


# ===== Edge TTS (メイン) =====

def _generate_edge_tts(text, voice_key=DEFAULT_VOICE, speed=1.0):
    """Edge TTSで音声生成（無料・高品質）"""
    try:
        import edge_tts
    except ImportError:
        return None
    
    voice_config = VOICE_OPTIONS.get(voice_key, VOICE_OPTIONS[DEFAULT_VOICE])
    voice_name = voice_config['edge']
    
    # 速度をEdge TTS形式に変換 (e.g., "+20%" or "-10%")
    speed_pct = int((speed - 1.0) * 100)
    rate_str = f"+{speed_pct}%" if speed_pct >= 0 else f"{speed_pct}%"
    
    async def _generate():
        communicate = edge_tts.Communicate(text, voice_name, rate=rate_str)
        
        with tempfile.NamedTemporaryFile(suffix=".mp3", delete=False) as tmp:
            tmp_path = tmp.name
        
        await communicate.save(tmp_path)
        
        with open(tmp_path, 'rb') as f:
            audio_data = f.read()
        
        os.unlink(tmp_path)
        return audio_data
    
    try:
        # asyncio イベントループ処理
        try:
            loop = asyncio.get_event_loop()
            if loop.is_running():
                import concurrent.futures
                with concurrent.futures.ThreadPoolExecutor() as executor:
                    future = executor.submit(asyncio.run, _generate())
                    return future.result(timeout=30)
            else:
                return loop.run_until_complete(_generate())
        except RuntimeError:
            return asyncio.run(_generate())
    
    except Exception as e:
        st.warning(f"Edge TTS error: {e}")
        return None


# ===== OpenAI TTS (バックアップ) =====

def _generate_openai_tts(text, voice_key=DEFAULT_VOICE, speed=1.0):
    """OpenAI TTSで音声生成（高品質・有料）"""
    try:
        from openai import OpenAI
        client = OpenAI(api_key=st.secrets["openai"]["api_key"])
    except Exception:
        return None
    
    voice_config = VOICE_OPTIONS.get(voice_key, VOICE_OPTIONS[DEFAULT_VOICE])
    voice_name = voice_config['openai']
    
    try:
        response = client.audio.speech.create(
            model="tts-1-hd",
            voice=voice_name,
            input=text[:4096],
            speed=speed
        )
        return response.content
    except Exception as e:
        st.warning(f"OpenAI TTS error: {e}")
        return None


# ===== Web Speech API (最終フォールバック) =====

def _play_web_speech_api(text, voice_key=DEFAULT_VOICE, speed=1.0):
    """ブラウザ内蔵Web Speech APIで再生"""
    voice_config = VOICE_OPTIONS.get(voice_key, VOICE_OPTIONS[DEFAULT_VOICE])
    lang = voice_config['lang']
    
    escaped = text.replace("'", "\\'").replace("\n", " ").replace('"', '\\"')
    
    js = f"""
    <script>
    (function() {{
        window.speechSynthesis.cancel();
        setTimeout(function() {{
            const u = new SpeechSynthesisUtterance("{escaped}");
            u.lang = "{lang}";
            u.rate = {speed};
            window.speechSynthesis.speak(u);
        }}, 100);
    }})();
    </script>
    """
    st.components.v1.html(js, height=0)
    return True


# ===== メイン関数 =====

def generate_natural_audio(text, voice_key=DEFAULT_VOICE, speed=1.0, use_cache=True):
    """
    自然な音声を生成（バイトデータを返す）
    
    優先順位: Edge TTS → OpenAI TTS → None
    """
    if not text or not text.strip():
        return None
    
    # キャッシュチェック
    if use_cache:
        cache_key = _get_cache_key(text, voice_key, speed)
        cached = _get_from_cache(cache_key)
        if cached:
            return cached
    
    # 1. Edge TTS
    audio = _generate_edge_tts(text, voice_key, speed)
    
    # 2. OpenAI TTS (Edgeが使えない場合)
    if audio is None:
        audio = _generate_openai_tts(text, voice_key, speed)
    
    # キャッシュ保存
    if audio and use_cache:
        _save_to_cache(cache_key, audio)
    
    return audio


def play_natural_tts(text, voice_key=DEFAULT_VOICE, speed=1.0, use_cache=True):
    """
    自然な音声で再生（UIに埋め込み）
    
    優先順位: Edge TTS → OpenAI TTS → Web Speech API
    """
    if not text or not text.strip():
        return
    
    audio = generate_natural_audio(text, voice_key, speed, use_cache)
    
    if audio:
        b64 = base64.b64encode(audio).decode()
        audio_html = f"""
        <audio controls autoplay style="width:100%">
            <source src="data:audio/mp3;base64,{b64}" type="audio/mp3">
        </audio>
        """
        st.markdown(audio_html, unsafe_allow_html=True)
    else:
        # フォールバック
        _play_web_speech_api(text, voice_key, speed)
        st.caption("⚠️ フォールバック音声（ブラウザ内蔵）を使用中")


def stop_audio():
    """音声停止"""
    js = """
    <script>
    (function() {
        window.speechSynthesis.cancel();
        document.querySelectorAll('audio').forEach(a => { a.pause(); a.currentTime = 0; });
    })();
    </script>
    """
    st.components.v1.html(js, height=0)


# ===== UI コンポーネント =====

def show_tts_player(text, key_prefix="tts", show_voice_select=True, default_voice=DEFAULT_VOICE):
    """TTS再生プレイヤーUI"""
    
    cols = st.columns([2, 2, 1, 1] if show_voice_select else [2, 1, 1])
    col_idx = 0
    
    if show_voice_select:
        with cols[col_idx]:
            voice = st.selectbox(
                "音声",
                list(VOICE_OPTIONS.keys()),
                index=list(VOICE_OPTIONS.keys()).index(default_voice),
                key=f"{key_prefix}_voice"
            )
        col_idx += 1
    else:
        voice = default_voice
    
    with cols[col_idx]:
        speed = st.select_slider(
            "速度",
            options=[0.5, 0.75, 0.85, 1.0, 1.15, 1.25, 1.5],
            value=1.0,
            format_func=lambda x: f"{x}x",
            key=f"{key_prefix}_speed"
        )
    col_idx += 1
    
    with cols[col_idx]:
        if st.button("🔊 再生", key=f"{key_prefix}_play", use_container_width=True):
            with st.spinner("音声を生成中..."):
                play_natural_tts(text, voice, speed)
    col_idx += 1
    
    if col_idx < len(cols):
        with cols[col_idx]:
            if st.button("⏹️ 停止", key=f"{key_prefix}_stop", use_container_width=True):
                stop_audio()
    
    # 音声品質の注記
    show_tts_quality_note()
    
    return voice, speed


def show_tts_quality_note():
    """TTS音声品質に関する小さな注記"""
    st.caption(
        "💡 より自然な音声で聴きたい場合は "
        "[📘 使い方ガイド → 音声ツール] を参照してください。"
    )


def show_word_audio_button(word, key_prefix="word"):
    """単語の音声再生ボタン（小さめ）"""
    if st.button(f"🔊 {word}", key=f"{key_prefix}_{word}"):
        with st.spinner(""):
            play_natural_tts(word, DEFAULT_VOICE, 0.85)
