import streamlit as st
import streamlit.components.v1 as components
from openai import OpenAI
import base64

def get_openai_client():
    return OpenAI(api_key=st.secrets["openai"]["api_key"])


def text_to_speech_openai(text, voice="alloy"):
    """
    OpenAI TTSで音声を生成
    
    voice options: alloy, echo, fable, onyx, nova, shimmer
    - alloy: ニュートラル
    - echo: 男性的
    - fable: 表現豊か
    - onyx: 深い男性
    - nova: 女性的、温かい
    - shimmer: 女性的、明るい
    """
    
    try:
        client = get_openai_client()
        
        response = client.audio.speech.create(
            model="tts-1",  # tts-1-hd はより高品質だが高い
            voice=voice,
            input=text
        )
        
        return response.content
        
    except Exception as e:
        st.warning(f"TTS Error: {e}")
        return None


def text_to_speech_azure(text, voice="en-US-JennyNeural"):
    """Azure Neural TTSで音声を生成（バックアップ用）"""
    import requests
    
    api_key = st.secrets["azure_speech"]["api_key"]
    region = st.secrets["azure_speech"]["region"]
    
    url = f"https://{region}.tts.speech.microsoft.com/cognitiveservices/v1"
    
    headers = {
        "Ocp-Apim-Subscription-Key": api_key,
        "Content-Type": "application/ssml+xml",
        "X-Microsoft-OutputFormat": "audio-16khz-128kbitrate-mono-mp3"
    }
    
    ssml = f"""
    <speak version='1.0' xmlns='http://www.w3.org/2001/10/synthesis' xml:lang='en-US'>
        <voice name='{voice}'>
            <prosody rate='0.95'>
                {text}
            </prosody>
        </voice>
    </speak>
    """
    
    try:
        response = requests.post(url, headers=headers, data=ssml.encode('utf-8'), timeout=30)
        
        if response.status_code == 200:
            return response.content
        else:
            return None
    except:
        return None


def play_audio_autoplay(audio_data, show_controls=True):
    """音声を自動再生（JavaScript強制再生 + controlsフォールバック）"""

    if not audio_data:
        return

    b64 = base64.b64encode(audio_data).decode()

    # JavaScript で明示的に play() を呼ぶ → autoplay制限を回避しやすい
    # show_controls=True でプレイヤーも表示（ユーザーが手動再生できる）
    controls_attr = "controls" if show_controls else ""
    html = f"""
    <audio id="tts_audio" {controls_attr} style="width:100%; margin-top:4px;">
        <source src="data:audio/mp3;base64,{b64}" type="audio/mp3">
    </audio>
    <script>
    (function() {{
        var audio = document.getElementById('tts_audio');
        if (audio) {{
            audio.play().catch(function(e) {{
                console.log('Autoplay blocked:', e);
            }});
        }}
    }})();
    </script>
    """
    # height=60 でコントロールバーが見えるようにする
    height = 60 if show_controls else 1
    components.html(html, height=height)
