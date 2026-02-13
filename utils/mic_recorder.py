import streamlit as st


def record_audio(key="mic_recorder", text="🎤 マイクで録音 / Record"):
    """ブラウザマイクで録音し、音声バイトを返す。
    
    energy_threshold: 無音と判定する音量の閾値（低いほど小さな声でも録音継続）
    pause_threshold: 無音がこの秒数続いたら自動停止（長いほど途切れにくい）
    """
    try:
        from audio_recorder_streamlit import audio_recorder
        audio_bytes = audio_recorder(
            text=text,
            energy_threshold=0.005,
            pause_threshold=30.0,
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
    """マイク録音 or ファイルアップロードの選択UI（Safari対応版）

    Safari では audio-recorder-streamlit が MediaRecorder API の
    互換性問題でエラーになることがあるため、常にファイルアップロード
    オプションを表示してフォールバックできるようにする。
    """

    input_method = st.radio(
        "入力方法 / Input method",
        ["🎤 マイクで録音", "📁 ファイルをアップロード"],
        horizontal=True,
        key=f"{key_prefix}_method"
    )

    audio_bytes = None

    if input_method == "🎤 マイクで録音":
        st.caption("ボタンを押して録音開始 → もう一度押して停止")
        audio_bytes = record_audio(key=f"{key_prefix}_mic")

        if audio_bytes:
            st.audio(audio_bytes, format="audio/wav")
            st.success("✅ 録音完了！")

        st.caption(
            "⚠️ Safari で録音エラーが出る場合は「📁 ファイルをアップロード」を使うか、"
            "Chrome / Edge をお試しください。"
        )

    else:
        st.info(
            "💡 スマホのボイスメモ等で録音した音声ファイルをアップロードできます。"
        )
        uploaded = st.file_uploader(
            "音声ファイル（WAV, MP3, M4A, WEBM） / Upload audio file",
            type=['wav', 'mp3', 'm4a', 'webm', 'ogg', 'mp4'],
            key=f"{key_prefix}_upload"
        )
        if uploaded:
            audio_bytes = uploaded.read()
            st.audio(audio_bytes)
            st.success("✅ ファイル読み込み完了！")

    return audio_bytes
