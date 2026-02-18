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
    """YouTube動画の字幕を取得（全言語対応）"""
    try:
        from youtube_transcript_api import YouTubeTranscriptApi

        transcript_list = YouTubeTranscriptApi.list_transcripts(video_id)

        # 1. 手動英語字幕を試す
        try:
            transcript = transcript_list.find_transcript(['en', 'en-US', 'en-GB'])
            captions = transcript.fetch()
            full_text = ' '.join([item['text'] for item in captions])
            return {"success": True, "transcript": full_text, "segments": captions, "method": "manual"}
        except Exception:
            pass

        # 2. 自動生成英語字幕を試す
        try:
            transcript = transcript_list.find_generated_transcript(['en', 'en-US', 'en-GB'])
            captions = transcript.fetch()
            full_text = ' '.join([item['text'] for item in captions])
            return {"success": True, "transcript": full_text, "segments": captions, "method": "auto"}
        except Exception:
            pass

        # 3. 利用可能な全字幕から英語を含むものを探す
        for transcript in transcript_list:
            if 'en' in transcript.language_code.lower():
                try:
                    captions = transcript.fetch()
                    full_text = ' '.join([item['text'] for item in captions])
                    return {"success": True, "transcript": full_text, "segments": captions, "method": "any_en"}
                except Exception:
                    continue

        # 4. 英語字幕がなければ他言語字幕を英語に翻訳
        for transcript in transcript_list:
            try:
                translated = transcript.translate('en')
                captions = translated.fetch()
                full_text = ' '.join([item['text'] for item in captions])
                return {"success": True, "transcript": full_text, "segments": captions, "method": "translated"}
            except Exception:
                continue

        return {"success": False, "error": "字幕が見つかりませんでした", "no_subtitles": True}

    except ImportError:
        return {"success": False, "error": "youtube-transcript-api がインストールされていません"}
    except Exception as e:
        return {"success": False, "error": str(e), "no_subtitles": True}


def get_transcript_auto(video_id):
    """字幕を取得する。エラーの場合は実際の原因を表示する。"""
    result = get_youtube_transcript(video_id)

    if result.get("success"):
        return result

    # 実際のエラーメッセージをそのまま返す
    actual_error = result.get("error", "不明なエラー")
    return {
        "success": False,
        "error": f"字幕取得エラー: {actual_error}"
    }


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
        "<Background info that helps understand videos on this topic>"
    ],
    "listening_tips": [
        "<Tip for understanding videos on this topic>"
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
Transcript: {transcript}

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

Transcript: {sample}

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
