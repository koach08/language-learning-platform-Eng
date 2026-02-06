import streamlit as st
from openai import OpenAI
import json
import io

def get_openai_client():
    return OpenAI(api_key=st.secrets["openai"]["api_key"])


# 話者用の声の設定
VOICES = {
    "A": "nova",      # 女性的
    "B": "echo",      # 男性的
    "C": "shimmer",   # 女性的（別）
    "D": "onyx",      # 男性的（別）
    "narrator": "alloy",  # ナレーター
    "default": "alloy"
}


# デモ用音声スクリプト
DEMO_LISTENING = {
    "intro_conversation": {
        "title": "Meeting a New Classmate",
        "level": "A2",
        "category": "Daily Conversation",
        "duration": "1:30",
        "speakers": {"A": "Yuki (female)", "B": "Sarah (female)"},
        "script": """A: Hi! Is this seat taken?
B: No, go ahead. Are you in this class too?
A: Yes, I just transferred here. My name is Yuki.
B: Nice to meet you, Yuki. I'm Sarah. Where did you transfer from?
A: I was studying in Osaka, but my family moved here last month.
B: Oh, that must be a big change. How do you like it so far?
A: It's different, but everyone has been really friendly. I'm still getting used to the campus though.
B: I can show you around after class if you want. The library is a bit hard to find.
A: That would be great! Thank you so much.
B: No problem. By the way, do you have the textbook for this class?
A: Not yet. Is there a bookstore nearby?
B: Yes, there's one right next to the cafeteria. I can take you there too.
A: You're so helpful. I really appreciate it.""",
        "questions": [
            {
                "question": "Where did Yuki transfer from?",
                "options": ["Tokyo", "Osaka", "Kyoto", "Nagoya"],
                "correct": "Osaka"
            },
            {
                "question": "What does Sarah offer to show Yuki?",
                "options": ["The classroom", "The campus", "The city", "Her notes"],
                "correct": "The campus"
            },
            {
                "question": "Where is the bookstore located?",
                "options": ["Next to the library", "Next to the cafeteria", "Near the station", "In the main building"],
                "correct": "Next to the cafeteria"
            }
        ]
    },
    "news_report": {
        "title": "Tech Industry News",
        "level": "B1",
        "category": "News",
        "duration": "2:00",
        "speakers": {"narrator": "News Anchor"},
        "script": """Good evening. Here are today's top stories in technology.

A major smartphone company announced today that it will be releasing its newest model next month. The new phone features an improved camera system and longer battery life. Industry experts predict strong sales, especially in Asian markets.

In other news, a study released today shows that more people are working remotely than ever before. According to the research, about 40 percent of employees now work from home at least part of the time. This trend is expected to continue even as pandemic restrictions ease.

Finally, a new social media platform has gained 10 million users in just two weeks since its launch. The app focuses on short video content and has become particularly popular among teenagers. Some parents and educators have expressed concerns about screen time, but the company says it is implementing features to promote healthy usage.

That's all for today's tech news. Stay tuned for weather and sports after the break.""",
        "questions": [
            {
                "question": "What features does the new smartphone have?",
                "options": ["Larger screen and better speakers", "Improved camera and longer battery", "Faster processor and more storage", "Better display and wireless charging"],
                "correct": "Improved camera and longer battery"
            },
            {
                "question": "What percentage of employees work from home at least part-time?",
                "options": ["20 percent", "30 percent", "40 percent", "50 percent"],
                "correct": "40 percent"
            },
            {
                "question": "How many users did the new social media app gain?",
                "options": ["1 million", "5 million", "10 million", "20 million"],
                "correct": "10 million"
            }
        ]
    },
    "lecture_excerpt": {
        "title": "Introduction to Psychology",
        "level": "B2",
        "category": "Academic",
        "duration": "2:30",
        "speakers": {"narrator": "Professor"},
        "script": """Today, we're going to begin our discussion of memory. Memory is one of the most fascinating aspects of human cognition, and understanding how it works has important implications for education, therapy, and everyday life.

Psychologists generally divide memory into three main types. First, there's sensory memory, which holds information from our senses for a very brief period, usually less than a second. Think of it as a quick snapshot of what you're experiencing right now.

Second, we have short-term memory, also called working memory. This is where we hold information we're currently thinking about. It has limited capacity, typically around seven items, and information here lasts only about 20 to 30 seconds without rehearsal.

Finally, there's long-term memory, which can store vast amounts of information for extended periods, potentially a lifetime. The process of moving information from short-term to long-term memory is called consolidation, and it's influenced by factors like repetition, emotional significance, and sleep.

For next class, I'd like you to read chapter three, which discusses the biological basis of memory. We'll explore how memories are actually formed in the brain.""",
        "questions": [
            {
                "question": "How long does sensory memory typically last?",
                "options": ["Less than a second", "About 10 seconds", "About 30 seconds", "Several minutes"],
                "correct": "Less than a second"
            },
            {
                "question": "What is the typical capacity of short-term memory?",
                "options": ["Three items", "Five items", "Seven items", "Ten items"],
                "correct": "Seven items"
            },
            {
                "question": "What is the process called when information moves to long-term memory?",
                "options": ["Encoding", "Consolidation", "Retrieval", "Recognition"],
                "correct": "Consolidation"
            }
        ]
    },
    "job_interview": {
        "title": "Job Interview Practice",
        "level": "B1",
        "category": "Business",
        "duration": "2:00",
        "speakers": {"A": "Interviewer (male)", "B": "Candidate (female)"},
        "script": """A: Good morning. Please have a seat. Thank you for coming in today.
B: Good morning. Thank you for having me.
A: So, I've looked at your resume. Can you tell me a little about yourself?
B: Of course. I recently graduated from university with a degree in business administration. During my studies, I completed two internships at marketing companies.
A: That's great. What interested you about this position?
B: I've always admired your company's innovative approach to digital marketing. I believe my skills in social media management would be a good fit for your team.
A: Can you give me an example of a project you're proud of?
B: Yes. During my internship, I managed a social media campaign that increased our client's followers by 30 percent in just two months.
A: Impressive. Where do you see yourself in five years?
B: I hope to grow within the company and eventually lead my own marketing team.
A: Do you have any questions for me?
B: Yes, I'd like to know more about the team I would be working with.""",
        "questions": [
            {
                "question": "What did the candidate study at university?",
                "options": ["Marketing", "Business administration", "Computer science", "Communications"],
                "correct": "Business administration"
            },
            {
                "question": "What was the result of the candidate's social media campaign?",
                "options": ["10% increase in followers", "20% increase in followers", "30% increase in followers", "50% increase in followers"],
                "correct": "30% increase in followers"
            },
            {
                "question": "What does the candidate hope to do in five years?",
                "options": ["Start their own company", "Lead a marketing team", "Move to another country", "Get an MBA"],
                "correct": "Lead a marketing team"
            }
        ]
    }
}


def parse_dialogue(script):
    """会話スクリプトを話者ごとに分割"""
    
    lines = script.strip().split('\n')
    parsed = []
    
    for line in lines:
        line = line.strip()
        if not line:
            continue
        
        # "A: text" または "B: text" の形式をチェック
        if len(line) > 2 and line[1] == ':':
            speaker = line[0].upper()
            text = line[2:].strip()
            parsed.append({"speaker": speaker, "text": text})
        else:
            # ナレーション（話者指定なし）
            parsed.append({"speaker": "narrator", "text": line})
    
    return parsed


def generate_audio_with_openai(text, voice="alloy"):
    """音声を生成（Edge TTS優先 → OpenAI TTS フォールバック）"""
    
    # OpenAI voice → Edge TTS voice マッピング
    edge_voice_map = {
        "alloy": "en-US-JennyNeural",
        "nova": "en-US-JennyNeural",
        "shimmer": "en-GB-SoniaNeural",
        "echo": "en-US-GuyNeural",
        "onyx": "en-GB-RyanNeural",
        "fable": "en-AU-NatashaNeural",
    }
    
    # 1. Edge TTS を試行
    try:
        from utils.tts_natural import _generate_edge_tts
        edge_voice = edge_voice_map.get(voice, "en-US-JennyNeural")
        
        # _generate_edge_tts は voice_key を受け取るので直接 edge voice name で呼ぶ
        audio = _generate_edge_tts_direct(text, edge_voice)
        if audio:
            return audio
    except Exception:
        pass
    
    # 2. OpenAI TTS フォールバック
    try:
        client = get_openai_client()
        response = client.audio.speech.create(
            model="tts-1",
            voice=voice,
            input=text
        )
        return response.content
    except Exception as e:
        st.error(f"TTS Error: {e}")
        return None


def _generate_edge_tts_direct(text, voice_name="en-US-JennyNeural", speed=1.0):
    """Edge TTSで直接音声生成（voice名を直接指定）"""
    try:
        import edge_tts
        import asyncio
        import tempfile
        import os
    except ImportError:
        return None
    
    rate_str = "+0%"
    
    async def _gen():
        communicate = edge_tts.Communicate(text, voice_name, rate=rate_str)
        with tempfile.NamedTemporaryFile(suffix=".mp3", delete=False) as tmp:
            tmp_path = tmp.name
        await communicate.save(tmp_path)
        with open(tmp_path, 'rb') as f:
            data = f.read()
        os.unlink(tmp_path)
        return data
    
    try:
        try:
            loop = asyncio.get_event_loop()
            if loop.is_running():
                import concurrent.futures
                with concurrent.futures.ThreadPoolExecutor() as executor:
                    future = executor.submit(asyncio.run, _gen())
                    return future.result(timeout=30)
            else:
                return loop.run_until_complete(_gen())
        except RuntimeError:
            return asyncio.run(_gen())
    except Exception:
        return None


def generate_dialogue_audio(script, voice_mapping=None):
    """
    会話スクリプトを話者別の声で音声生成
    voice_mapping: {"A": "nova", "B": "echo"} のような辞書
    """
    
    if voice_mapping is None:
        voice_mapping = {
            "A": "nova",      # 女性 → Edge: en-US-JennyNeural
            "B": "echo",      # 男性 → Edge: en-US-GuyNeural
            "C": "shimmer",   # 女性(UK) → Edge: en-GB-SoniaNeural
            "D": "onyx",      # 男性(UK) → Edge: en-GB-RyanNeural
            "narrator": "alloy"  # → Edge: en-US-JennyNeural
        }
    
    parsed = parse_dialogue(script)
    
    if not parsed:
        # 会話形式でない場合は通常の音声生成
        return generate_audio_with_openai(script, voice_mapping.get("narrator", "alloy"))
    
    # 各パートの音声を生成して結合
    audio_parts = []
    
    for part in parsed:
        speaker = part["speaker"]
        text = part["text"]
        voice = voice_mapping.get(speaker, voice_mapping.get("default", "alloy"))
        
        audio = generate_audio_with_openai(text, voice)
        if audio:
            audio_parts.append(audio)
    
    # 音声を結合
    if audio_parts:
        return combine_audio_parts(audio_parts)
    
    return None


def combine_audio_parts(audio_parts):
    """複数の音声データを結合（シンプルな連結）"""
    
    # MP3ファイルを単純に連結（完全ではないが動作する）
    combined = b''
    for part in audio_parts:
        combined += part
    
    return combined


def check_dictation(original, user_input):
    """ディクテーションの正確さをチェック"""
    
    client = get_openai_client()
    
    prompt = f"""Compare the original text with the user's dictation and provide feedback.

Original text:
{original}

User's dictation:
{user_input}

Provide feedback in JSON format:
{{
    "accuracy_percentage": <0-100>,
    "correct_parts": ["<correctly transcribed parts>"],
    "errors": [
        {{
            "user_wrote": "<what user wrote>",
            "should_be": "<correct text>",
            "error_type": "<spelling/missing_word/extra_word/word_order>"
        }}
    ],
    "feedback": "<Encouraging feedback in English and Japanese>",
    "tips": "<Specific tips for improvement / 改善のためのヒント>"
}}
"""

    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": "You are a dictation checker for English learners. Be encouraging but specific. Respond in valid JSON."},
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


def generate_listening_from_prompt(prompt, level="B1", duration="short"):
    """プロンプトからリスニング素材を生成"""
    
    client = get_openai_client()
    
    duration_guide = {
        "short": "30-60 seconds, about 80-120 words",
        "medium": "1-2 minutes, about 150-250 words",
        "long": "2-3 minutes, about 300-400 words"
    }
    
    system_prompt = f"""Create listening material for Japanese English learners at {level} level.
Duration should be {duration_guide.get(duration, duration_guide['medium'])}.
For dialogues, use format "A: text" and "B: text" to indicate different speakers."""

    user_prompt = f"""Create a listening exercise based on this request:
"{prompt}"

Output in JSON format:
{{
    "title": "<Title>",
    "category": "<Category>",
    "level": "{level}",
    "is_dialogue": <true if it's a conversation between people, false for narration>,
    "speakers": {{"A": "<Speaker A description>", "B": "<Speaker B description>"}} or null if not dialogue,
    "script": "<The full script. For dialogues use 'A: text' and 'B: text' format>",
    "duration": "<estimated duration>",
    "vocabulary": [
        {{"word": "<key word>", "meaning": "<日本語>"}}
    ],
    "questions": [
        {{
            "question": "<Comprehension question>",
            "question_ja": "<日本語訳>",
            "options": ["<A>", "<B>", "<C>", "<D>"],
            "correct": "<correct answer>"
        }}
    ]
}}

Guidelines:
- Use natural, conversational English appropriate for {level}
- Include 3-5 comprehension questions
- For dialogues, make each speaker's voice distinct in personality
"""

    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            temperature=0.8,
            response_format={"type": "json_object"}
        )
        
        result = json.loads(response.choices[0].message.content)
        result["success"] = True
        result["generated"] = True
        return result
        
    except Exception as e:
        return {"success": False, "error": str(e)}


def extract_youtube_id(url):
    """YouTubeのURLからVideo IDを抽出"""
    import re
    
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
    """YouTube動画の字幕を取得（youtube-transcript-apiが必要）"""
    
    try:
        from youtube_transcript_api import YouTubeTranscriptApi
        
        # 英語字幕を優先、なければ自動生成字幕
        transcript_list = YouTubeTranscriptApi.list_transcripts(video_id)
        
        # 英語字幕を探す
        try:
            transcript = transcript_list.find_transcript(['en'])
        except:
            # 自動生成の英語字幕を探す
            try:
                transcript = transcript_list.find_generated_transcript(['en'])
            except:
                return {"success": False, "error": "英語字幕が見つかりませんでした / No English subtitles found"}
        
        # 字幕を取得
        captions = transcript.fetch()
        
        # テキストを結合
        full_text = ' '.join([item['text'] for item in captions])
        
        return {
            "success": True,
            "transcript": full_text,
            "segments": captions,  # タイムスタンプ付き
            "language": transcript.language
        }
        
    except ImportError:
        return {"success": False, "error": "youtube-transcript-api がインストールされていません"}
    except Exception as e:
        return {"success": False, "error": str(e)}


def generate_exercises_from_transcript(transcript, video_title="", level="B1"):
    """字幕から学習素材を生成"""
    
    client = get_openai_client()
    
    # 長すぎる場合は最初の部分のみ使用
    if len(transcript) > 3000:
        transcript = transcript[:3000] + "..."
    
    prompt = f"""Based on this YouTube video transcript, create English learning materials for a Japanese university student (Level: {level}).

Video Title: {video_title}
Transcript:
{transcript}

Create learning materials in JSON format:
{{
    "summary": {{
        "english": "<2-3 sentence summary of the video>",
        "japanese": "<日本語要約>"
    }},
    "key_vocabulary": [
        {{
            "word": "<important word/phrase from the video>",
            "meaning": "<日本語の意味>",
            "timestamp_hint": "<roughly where in the video>",
            "example_from_video": "<how it was used in the video>"
        }}
    ],
    "comprehension_questions": [
        {{
            "question": "<Question about the video content>",
            "question_ja": "<日本語訳>",
            "options": ["<A>", "<B>", "<C>", "<D>"],
            "correct": "<correct answer>",
            "explanation": "<Why this is correct / 解説>"
        }}
    ],
    "dictation_segments": [
        {{
            "text": "<A short, clear segment good for dictation practice (10-20 words)>",
            "difficulty": "<easy/medium/hard>"
        }}
    ],
    "discussion_questions": [
        "<Discussion question related to the video topic / ディスカッション質問>"
    ],
    "shadowing_tips": "<Tips for shadowing practice with this video / シャドーイング練習のコツ>"
}}

Guidelines:
- Extract 8-12 key vocabulary items
- Create 5 comprehension questions
- Select 3-5 good segments for dictation
- Focus on vocabulary and expressions that would be useful for Japanese learners
- Consider what prior knowledge Japanese students might have about this topic
"""

    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": "You are an English learning material creator specializing in content for Japanese learners. Create engaging materials from video transcripts. Respond in valid JSON."},
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
    
    # サンプルを取得
    sample = transcript[:1500] if len(transcript) > 1500 else transcript
    
    prompt = f"""Analyze the difficulty of this English video transcript for a Japanese learner.

Transcript sample:
{sample}

Provide analysis in JSON format:
{{
    "estimated_cefr": "<A2/B1/B2/C1/C2>",
    "difficulty_factors": {{
        "speech_speed": "<slow/moderate/fast>",
        "vocabulary_level": "<basic/intermediate/advanced>",
        "accent": "<description of accent if notable>",
        "technical_terms": <true/false>,
        "slang_informal": <true/false>
    }},
    "suitability_for_{level}": {{
        "score": <1-10>,
        "explanation": "<Why suitable or not / 適切かどうかの説明>"
    }},
    "recommendations": "<Tips for studying with this video / この動画で学習するためのアドバイス>"
}}
"""

    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": "You are an expert in assessing English learning materials. Respond in valid JSON."},
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


def get_voice_for_speaker(speaker, speaker_info=None):
    """話者に適した声を選択"""
    
    if speaker_info:
        info_lower = speaker_info.lower()
        if "female" in info_lower or "woman" in info_lower or "girl" in info_lower:
            if speaker in ["A", "C"]:
                return "nova"
            else:
                return "shimmer"
        elif "male" in info_lower or "man" in info_lower or "boy" in info_lower:
            if speaker in ["A", "C"]:
                return "echo"
            else:
                return "onyx"
    
    default_mapping = {
        "A": "nova",
        "B": "echo", 
        "C": "shimmer",
        "D": "onyx",
        "narrator": "alloy"
    }
    
    return default_mapping.get(speaker, "alloy")


def parse_dialogue(script):
    """会話スクリプトを話者ごとに分割"""
    
    lines = script.strip().split('\n')
    parsed = []
    
    for line in lines:
        line = line.strip()
        if not line:
            continue
        
        if len(line) > 2 and line[1] == ':':
            speaker = line[0].upper()
            text = line[2:].strip()
            parsed.append({"speaker": speaker, "text": text})
        else:
            parsed.append({"speaker": "narrator", "text": line})
    
    return parsed


def generate_dialogue_audio(script, voice_mapping=None):
    """会話スクリプトを話者別の声で音声生成"""
    
    if voice_mapping is None:
        voice_mapping = {
            "A": "nova",
            "B": "echo",
            "C": "shimmer",
            "D": "onyx",
            "narrator": "alloy"
        }
    
    parsed = parse_dialogue(script)
    
    if not parsed:
        return generate_audio_with_openai(script, voice_mapping.get("narrator", "alloy"))
    
    audio_parts = []
    
    for part in parsed:
        speaker = part["speaker"]
        text = part["text"]
        voice = voice_mapping.get(speaker, "alloy")
        
        audio = generate_audio_with_openai(text, voice)
        if audio:
            audio_parts.append(audio)
    
    if audio_parts:
        combined = b''
        for part in audio_parts:
            combined += part
        return combined
    
    return None


def generate_dialogue_audio_with_speakers(script, speakers_info=None):
    """会話を話者情報に基づいて適切な声で生成"""
    
    voice_mapping = {}
    
    if speakers_info:
        for speaker, info in speakers_info.items():
            voice_mapping[speaker] = get_voice_for_speaker(speaker, info)
    else:
        voice_mapping = {
            "A": "nova",
            "B": "echo",
            "C": "shimmer", 
            "D": "onyx",
            "narrator": "alloy"
        }
    
    return generate_dialogue_audio(script, voice_mapping)
