"""YouTube関連の機能"""

import streamlit as st
from openai import OpenAI
import json
import re
import tempfile
import os

def get_openai_client():
    return OpenAI(api_key=st.secrets["openai"]["api_key"])


def extract_youtube_id(url):
    """YouTubeのURLからVideo IDを抽出"""
    patterns = [
        r'(?:youtube\.com\/watch\?v=|youtu\.be\/|youtube\.com\/embed\/)([a-zA-Z0-9_-]{11})',
        r'youtube\.com\/shorts\/([a-zA-Z0-9_-]{11})'
    ]
    for pattern in patterns:
        match = re.search(pattern, url)
        if match:
            return match.group(1)
    return None


def get_youtube_transcript(video_id):
    """YouTube動画の字幕を取得（既存の字幕）"""
    try:
        from youtube_transcript_api import YouTubeTranscriptApi
        
        try:
            captions = YouTubeTranscriptApi.get_transcript(video_id, languages=['en', 'en-US', 'en-GB'])
        except:
            return {"success": False, "error": "英語字幕が見つかりませんでした", "no_subtitles": True}
        
        full_text = ' '.join([item['text'] for item in captions])
        return {"success": True, "transcript": full_text, "segments": captions, "method": "youtube_subtitles"}
        
    except ImportError:
        return {"success": False, "error": "youtube-transcript-api がインストールされていません"}
    except Exception as e:
        return {"success": False, "error": str(e), "no_subtitles": True}


def download_youtube_audio(video_id):
    """YouTube動画の音声をダウンロード"""
    try:
        import yt_dlp
        
        url = f"https://www.youtube.com/watch?v={video_id}"
        
        # 一時ファイルに保存
        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = os.path.join(tmpdir, "audio")
            
            ydl_opts = {
                'format': 'bestaudio/best',
                'outtmpl': output_path,
                'postprocessors': [{
                    'key': 'FFmpegExtractAudio',
                    'preferredcodec': 'mp3',
                    'preferredquality': '128',
                }],
                'quiet': True,
                'no_warnings': True,
            }
            
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(url, download=True)
                title = info.get('title', 'Unknown')
                duration = info.get('duration', 0)
            
            # 音声ファイルを読み込み
            audio_file = output_path + ".mp3"
            if os.path.exists(audio_file):
                with open(audio_file, 'rb') as f:
                    audio_data = f.read()
                return {
                    "success": True,
                    "audio_data": audio_data,
                    "title": title,
                    "duration": duration
                }
            else:
                return {"success": False, "error": "音声ファイルが見つかりません"}
                
    except ImportError:
        return {"success": False, "error": "yt-dlp がインストールされていません"}
    except Exception as e:
        return {"success": False, "error": str(e)}


def transcribe_with_whisper(audio_data, filename="audio.mp3"):
    """Whisper APIで音声を文字起こし"""
    
    client = get_openai_client()
    
    try:
        # 一時ファイルに保存
        with tempfile.NamedTemporaryFile(suffix=".mp3", delete=False) as tmp:
            tmp.write(audio_data)
            tmp_path = tmp.name
        
        # Whisper APIで文字起こし
        with open(tmp_path, "rb") as audio_file:
            transcript = client.audio.transcriptions.create(
                model="whisper-1",
                file=audio_file,
                language="en"
            )
        
        # 一時ファイル削除
        os.unlink(tmp_path)
        
        return {
            "success": True,
            "transcript": transcript.text,
            "method": "whisper"
        }
        
    except Exception as e:
        return {"success": False, "error": str(e)}


def get_transcript_auto(video_id):
    """
    自動で最適な方法で字幕を取得
    1. まずYouTube字幕を試す
    2. なければWhisperで文字起こし
    """
    
    # まずYouTube字幕を試す
    result = get_youtube_transcript(video_id)
    
    if result.get("success"):
        return result
    
    # 字幕がなければWhisperで文字起こし
    if result.get("no_subtitles"):
        st.info("📝 字幕がないため、Whisper AIで音声認識中...")
        
        # 音声をダウンロード
        audio_result = download_youtube_audio(video_id)
        
        if not audio_result.get("success"):
            return {"success": False, "error": f"音声ダウンロードエラー: {audio_result.get('error')}"}
        
        # Whisperで文字起こし
        whisper_result = transcribe_with_whisper(audio_result.get("audio_data"))
        
        if whisper_result.get("success"):
            whisper_result["title"] = audio_result.get("title")
            whisper_result["duration"] = audio_result.get("duration")
            return whisper_result
        else:
            return whisper_result
    
    return result


def generate_learning_from_topic(topic, video_description="", level="B1"):
    """
    トピックから学習素材を生成（動画の字幕なしで使用）
    学生が動画を見ながら使う補助教材
    """
    
    client = get_openai_client()
    
    prompt = f"""A Japanese university student wants to learn English by watching a YouTube video about the following topic.
Create learning materials to help them understand and learn from the video.

Topic: {topic}
Video Description: {video_description}
Student Level: {level}

Create materials in JSON format:
{{
    "topic_summary": {{
        "english": "<Brief explanation of this topic in simple English>",
        "japanese": "<トピックの日本語説明>"
    }},
    "key_vocabulary": [
        {{
            "word": "<Word likely to appear in videos about this topic>",
            "meaning": "<日本語の意味>",
            "pronunciation_tip": "<発音のヒント>",
            "example": "<Example sentence>"
        }}
    ],
    "useful_phrases": [
        {{
            "phrase": "<Common phrase in this topic>",
            "meaning": "<日本語>",
            "context": "<When/how it's used>"
        }}
    ],
    "background_knowledge": [
        "<Background info that helps understand videos on this topic / このトピックの動画を理解するための予備知識>"
    ],
    "listening_tips": [
        "<Tip for understanding videos on this topic / このトピックの動画を聞くときのコツ>"
    ],
    "practice_questions": [
        {{
            "question": "<Question to think about while watching>",
            "question_ja": "<日本語>"
        }}
    ],
    "related_vocabulary_categories": [
        {{
            "category": "<Category name>",
            "words": ["<word1>", "<word2>", "<word3>"]
        }}
    ]
}}

Guidelines:
- Include 15-20 key vocabulary items
- Include 8-10 useful phrases
- Make it specific to the topic
- Consider what Japanese learners might find difficult
- Include cultural context if relevant
"""

    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": "Create English learning materials for Japanese students. Respond in valid JSON."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.7,
            response_format={"type": "json_object"}
        )
        
        result = json.loads(response.choices[0].message.content)
        result["success"] = True
        return result
        
    except Exception as e:
        return {"success": False, "error": str(e)}


def generate_exercises_from_transcript(transcript, video_title="", level="B1"):
    """字幕から学習素材を生成"""
    
    client = get_openai_client()
    
    if len(transcript) > 3000:
        transcript = transcript[:3000] + "..."
    
    prompt = f"""Based on this video transcript, create English learning materials for a Japanese student (Level: {level}).

Title: {video_title}
Transcript:
{transcript}

Create in JSON format:
{{
    "summary": {{
        "english": "<2-3 sentence summary>",
        "japanese": "<日本語要約>"
    }},
    "key_vocabulary": [
        {{
            "word": "<important word>",
            "meaning": "<日本語>",
            "example_from_video": "<usage in video>"
        }}
    ],
    "comprehension_questions": [
        {{
            "question": "<Question>",
            "question_ja": "<日本語>",
            "options": ["<A>", "<B>", "<C>", "<D>"],
            "correct": "<answer>",
            "explanation": "<解説>"
        }}
    ],
    "dictation_segments": [
        {{
            "text": "<10-20 word segment>",
            "difficulty": "<easy/medium/hard>"
        }}
    ],
    "discussion_questions": ["<question>"],
    "shadowing_tips": "<シャドーイングのコツ>"
}}

Include 8-12 vocabulary, 5 questions, 3-5 dictation segments."""

    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": "Create learning materials from transcripts. Respond in valid JSON."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.7,
            response_format={"type": "json_object"}
        )
        
        result = json.loads(response.choices[0].message.content)
        result["success"] = True
        return result
        
    except Exception as e:
        return {"success": False, "error": str(e)}


def analyze_video_difficulty(transcript, level="B1"):
    """動画の難易度を分析"""
    
    client = get_openai_client()
    
    sample = transcript[:1500] if len(transcript) > 1500 else transcript
    
    prompt = f"""Analyze this transcript's difficulty for a Japanese learner ({level}).

Transcript:
{sample}

JSON format:
{{
    "estimated_cefr": "<A2/B1/B2/C1>",
    "difficulty_factors": {{
        "speech_speed": "<slow/moderate/fast>",
        "vocabulary_level": "<basic/intermediate/advanced>",
        "technical_terms": <true/false>
    }},
    "suitability_score": <1-10>,
    "recommendations": "<学習アドバイス>"
}}"""

    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": "Assess difficulty. Respond in valid JSON."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.3,
            response_format={"type": "json_object"}
        )
        
        result = json.loads(response.choices[0].message.content)
        result["success"] = True
        return result
        
    except Exception as e:
        return {"success": False, "error": str(e)}


# 教員用：動画リスト管理
CURATED_VIDEO_LIST = {
    "ted_talks": {
        "name": "TED Talks（おすすめ）",
        "description": "様々なトピックの短いプレゼンテーション",
        "videos": [
            {
                "id": "8jPQjjsBbIc",
                "title": "The power of introverts",
                "speaker": "Susan Cain",
                "duration": "19:04",
                "level": "B2",
                "topic": "Psychology",
                "has_subtitles": True
            },
            {
                "id": "arj7oStGLkU",
                "title": "How to speak so that people want to listen",
                "speaker": "Julian Treasure",
                "duration": "9:58",
                "level": "B1",
                "topic": "Communication",
                "has_subtitles": True
            }
        ]
    },
    "bbc_learning": {
        "name": "BBC Learning English",
        "description": "英語学習者向けの教材",
        "videos": [
            {
                "id": "G4IG4cUfRwI",
                "title": "6 Minute English - Various Topics",
                "speaker": "BBC",
                "duration": "6:00",
                "level": "B1",
                "topic": "Various",
                "has_subtitles": True
            }
        ]
    },
    "custom": {
        "name": "カスタム（教員追加）",
        "description": "教員が追加した動画",
        "videos": []
    }
}
