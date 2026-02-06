import streamlit as st


def record_audio(key="mic_recorder", text="🎤 マイクで録音 / Record"):
    """ブラウザマイクで録音し、音声バイトを返す"""
    try:
        from audio_recorder_streamlit import audio_recorder
        audio_bytes = audio_recorder(
            text=text,
            recording_color="#e74c3c",
            neutral_color="#3498db",
            icon_size="2x",
            key=key,
        )
        return audio_bytes
    except ImportError:
        st.warning("マイク録音には `audio-recorder-streamlit` パッケージが必要です")
        st.code("pip install audio-recorder-streamlit")
        return None
    except Exception as e:
        st.error(f"録音エラー: {e}")
        return None


def show_mic_or_upload(key_prefix="audio", allow_upload=True):
    """マイク録音 or ファイルアップロードの選択UI"""
    
    if allow_upload:
        input_method = st.radio(
            "入力方法",
            ["🎤 マイクで録音", "📁 ファイルをアップロード"],
            horizontal=True,
            key=f"{key_prefix}_method"
        )
    else:
        input_method = "🎤 マイクで録音"
    
    audio_bytes = None
    
    if input_method == "🎤 マイクで録音":
        st.caption("ボタンを押して録音開始 → もう一度押して停止")
        audio_bytes = record_audio(key=f"{key_prefix}_mic")
        
        if audio_bytes:
            st.audio(audio_bytes, format="audio/wav")
            st.success("✅ 録音完了！")
    
    else:
        uploaded = st.file_uploader(
            "音声ファイル（WAV, MP3, M4A）",
            type=['wav', 'mp3', 'm4a'],
            key=f"{key_prefix}_upload"
        )
        if uploaded:
            audio_bytes = uploaded.read()
            st.audio(audio_bytes)
    
    return audio_bytes
