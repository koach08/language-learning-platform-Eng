import streamlit as st


def record_audio(key="mic_recorder", text="🎤 マイクで録音 / Record"):
    """ブラウザマイクで録音し、音声バイトを返す。
    st.audio_input（Streamlit標準）を使用 — 外部コンポーネント不要。
    """
    audio = st.audio_input(text, key=key)
    if audio is not None:
        return audio.read()
    return None


def show_mic_or_upload(key_prefix="audio", allow_upload=True):
    """マイク録音 or ファイルアップロードの選択UI"""

    input_method = st.radio(
        "入力方法 / Input method",
        ["🎤 マイクで録音", "📁 ファイルをアップロード"],
        horizontal=True,
        key=f"{key_prefix}_method"
    )

    audio_bytes = None

    if input_method == "🎤 マイクで録音":

        reset_key = f"{key_prefix}_reset_count"
        if reset_key not in st.session_state:
            st.session_state[reset_key] = 0

        saved_audio_key = f"{key_prefix}_saved_audio"

        st.info(
            "**📋 録音の手順:**\n"
            "① マイクボタンを**クリック** → 録音開始\n"
            "② 英文を読み上げる\n"
            "③ もう一度ボタンをクリック → 録音停止\n"
            "④ ▶️ 再生プレーヤーで確認できます"
        )

        mic_key = f"{key_prefix}_mic_v{st.session_state[reset_key]}"
        new_audio = record_audio(key=mic_key)

        if new_audio:
            if new_audio != st.session_state.get(saved_audio_key):
                with st.spinner("⏳ 録音データを処理しています..."):
                    st.session_state[saved_audio_key] = new_audio

        audio_bytes = st.session_state.get(saved_audio_key)

        if audio_bytes:
            st.success("✅ 録音完了！ 下のプレーヤーで確認できます")
            st.audio(audio_bytes, format="audio/wav")

            if st.button("🔄 やり直す / Record again", key=f"{key_prefix}_retry_{st.session_state[reset_key]}"):
                st.session_state[reset_key] += 1
                if saved_audio_key in st.session_state:
                    del st.session_state[saved_audio_key]
                st.rerun()
        else:
            st.caption("⏳ 上のマイクボタンを押して録音してください")

        st.caption(
            "⚠️ Safari で録音できない場合は「📁 ファイルをアップロード」を選ぶか、"
            "Chrome / Edge をお使いください。"
        )

    else:
        st.info("💡 スマホのボイスメモや録音アプリで録音した音声ファイルをアップロードできます。")
        uploaded = st.file_uploader(
            "音声ファイル（WAV, MP3, M4A, WEBM）",
            type=['wav', 'mp3', 'm4a', 'webm', 'ogg', 'mp4'],
            key=f"{key_prefix}_upload"
        )
        if uploaded:
            audio_bytes = uploaded.read()
            st.audio(audio_bytes)
            st.success("✅ ファイル読み込み完了！")

    return audio_bytes
