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
    """マイク録音 or ファイルアップロードの選択UI（Safari対応・UX改善版）"""

    input_method = st.radio(
        "入力方法 / Input method",
        ["🎤 マイクで録音", "📁 ファイルをアップロード"],
        horizontal=True,
        key=f"{key_prefix}_method"
    )

    audio_bytes = None

    if input_method == "🎤 マイクで録音":

        # ── やり直し用カウンター ──
        reset_key = f"{key_prefix}_reset_count"
        if reset_key not in st.session_state:
            st.session_state[reset_key] = 0

        # 録音済み音声を保持するキー
        saved_audio_key = f"{key_prefix}_saved_audio"

        # ── 録音手順（常に表示） ──
        st.info(
            "**📋 録音の手順:**\n"
            "① 🔵 青いマイクボタンを**クリック** → ボタンが **🔴 赤** に変わり録音開始\n"
            "② そのまま英文を読み上げる（録音中はボタンが赤いままです）\n"
            "③ 読み終わったら **🔴 赤いボタンをもう一度クリック** → 録音停止\n"
            "④ 下に ▶️ 再生プレーヤーと「✅ 録音完了！」が表示されます"
        )

        # ── 録音コンポーネント ──
        mic_key = f"{key_prefix}_mic_v{st.session_state[reset_key]}"
        new_audio = record_audio(key=mic_key)

        # 新しい録音があれば保存
        if new_audio:
            st.session_state[saved_audio_key] = new_audio

        # 保存済みの音声を取得
        audio_bytes = st.session_state.get(saved_audio_key)

        # ── 録音結果の表示 ──
        if audio_bytes:
            st.success("✅ 録音完了！ 下のプレーヤーで確認できます / Recording complete!")
            st.audio(audio_bytes, format="audio/wav")

            # やり直しボタン
            if st.button("🔄 やり直す / Record again", key=f"{key_prefix}_retry_{st.session_state[reset_key]}"):
                st.session_state[reset_key] += 1
                if saved_audio_key in st.session_state:
                    del st.session_state[saved_audio_key]
                st.rerun()
        else:
            st.warning("⏳ 録音待ち — 上の青いマイクボタン 🎤 を押してください / Press the blue mic button above to start")

        st.caption(
            "⚠️ Safari で録音できない場合は「📁 ファイルをアップロード」を選ぶか、"
            "Chrome / Edge をお使いください。"
        )

    else:
        st.info(
            "💡 スマホのボイスメモや録音アプリで録音した音声ファイルをアップロードできます。"
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
