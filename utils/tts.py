import streamlit as st
from openai import OpenAI
import base64

def get_openai_client():
    return OpenAI(api_key=st.secrets["openai"]["api_key"])


def text_to_speech(text, voice="alloy", speed=1.0):
    """
    音声を生成（Edge TTS優先 → OpenAI TTSフォールバック）
    
    voice options: alloy, echo, fable, onyx, nova, shimmer
    """
    
    # 1. Edge TTS を試行（無料・高品質）
    try:
        from utils.tts_natural import generate_natural_audio
        
        # OpenAI voice → 表示名マッピング
        voice_to_display = {
            "alloy": "アメリカ英語 (女性)",
            "nova": "アメリカ英語 (女性)",
            "shimmer": "イギリス英語 (女性)",
            "echo": "アメリカ英語 (男性)",
            "onyx": "イギリス英語 (男性)",
            "fable": "オーストラリア英語 (女性)",
        }
        display_voice = voice_to_display.get(voice, "アメリカ英語 (女性)")
        
        audio_data = generate_natural_audio(text, display_voice, speed)
        if audio_data:
            return {"success": True, "audio": audio_data}
    except Exception:
        pass
    
    # 2. OpenAI TTS フォールバック
    try:
        client = get_openai_client()
        response = client.audio.speech.create(
            model="tts-1",
            voice=voice,
            input=text,
            speed=speed
        )
        audio_data = response.content
        return {"success": True, "audio": audio_data}
    except Exception as e:
        return {"success": False, "error": str(e)}


def play_audio(audio_data):
    """音声を再生（Streamlit）"""
    if audio_data:
        b64 = base64.b64encode(audio_data).decode()
        audio_html = f"""
        <audio controls autoplay>
            <source src="data:audio/mp3;base64,{b64}" type="audio/mp3">
        </audio>
        """
        st.markdown(audio_html, unsafe_allow_html=True)


def get_word_pronunciation(word):
    """単語の発音と意味を取得"""
    
    client = get_openai_client()
    
    # 音声生成
    audio_result = text_to_speech(word, voice="nova", speed=0.9)
    
    # 意味を取得（簡易版）
    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": "You are a dictionary. Respond in JSON."},
                {"role": "user", "content": f"""Give brief info for "{word}":
{{"word": "{word}", "pronunciation": "<IPA>", "meaning_ja": "<日本語>", "meaning_en": "<English definition>", "example": "<short example>"}}"""}
            ],
            temperature=0.3,
            response_format={"type": "json_object"}
        )
        
        import json
        meaning_data = json.loads(response.choices[0].message.content)
        
        return {
            "success": True,
            "audio": audio_result.get("audio") if audio_result.get("success") else None,
            "data": meaning_data
        }
        
    except Exception as e:
        return {"success": False, "error": str(e)}
