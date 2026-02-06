import streamlit as st
from openai import OpenAI
import json
import random

def get_openai_client():
    return OpenAI(api_key=st.secrets["openai"]["api_key"])


# デモ用単語データ（後でDBから取得）
DEMO_WORD_LISTS = {
    "academic": {
        "name": "Academic Words / 学術語彙",
        "description": "論文やレポートで使う語彙 / Words for essays and reports",
        "words": [
            {"word": "analyze", "meaning": "分析する", "example": "We need to analyze the data carefully.", "pos": "verb"},
            {"word": "significant", "meaning": "重要な、有意な", "example": "There was a significant difference between the two groups.", "pos": "adjective"},
            {"word": "hypothesis", "meaning": "仮説", "example": "The hypothesis was supported by the results.", "pos": "noun"},
            {"word": "contribute", "meaning": "貢献する", "example": "Many factors contribute to climate change.", "pos": "verb"},
            {"word": "evidence", "meaning": "証拠", "example": "There is strong evidence for this theory.", "pos": "noun"},
            {"word": "conclude", "meaning": "結論づける", "example": "We can conclude that the treatment was effective.", "pos": "verb"},
            {"word": "relevant", "meaning": "関連のある", "example": "This information is relevant to our discussion.", "pos": "adjective"},
            {"word": "furthermore", "meaning": "さらに", "example": "Furthermore, the study showed improved outcomes.", "pos": "adverb"},
            {"word": "whereas", "meaning": "一方で", "example": "Group A improved, whereas Group B showed no change.", "pos": "conjunction"},
            {"word": "Nevertheless", "meaning": "それにもかかわらず", "example": "Nevertheless, the results were promising.", "pos": "adverb"},
        ]
    },
    "toeic": {
        "name": "TOEIC Basics / TOEIC基礎",
        "description": "TOEICによく出る基礎語彙 / Common TOEIC vocabulary",
        "words": [
            {"word": "deadline", "meaning": "締め切り", "example": "The deadline for the project is next Friday.", "pos": "noun"},
            {"word": "approve", "meaning": "承認する", "example": "The manager approved the budget.", "pos": "verb"},
            {"word": "schedule", "meaning": "予定、スケジュール", "example": "Let me check my schedule.", "pos": "noun"},
            {"word": "invoice", "meaning": "請求書", "example": "Please send the invoice by email.", "pos": "noun"},
            {"word": "negotiate", "meaning": "交渉する", "example": "We need to negotiate the contract terms.", "pos": "verb"},
            {"word": "postpone", "meaning": "延期する", "example": "The meeting was postponed until next week.", "pos": "verb"},
            {"word": "implement", "meaning": "実施する", "example": "We will implement the new policy next month.", "pos": "verb"},
            {"word": "approximately", "meaning": "およそ", "example": "It takes approximately two hours.", "pos": "adverb"},
            {"word": "mandatory", "meaning": "義務的な", "example": "Attendance is mandatory for all employees.", "pos": "adjective"},
            {"word": "refund", "meaning": "払い戻し", "example": "You can get a full refund within 30 days.", "pos": "noun"},
        ]
    },
    "daily": {
        "name": "Daily Conversation / 日常会話",
        "description": "日常会話で使える語彙 / Words for everyday conversation",
        "words": [
            {"word": "definitely", "meaning": "絶対に、確実に", "example": "I'll definitely come to your party.", "pos": "adverb"},
            {"word": "grab", "meaning": "つかむ、さっと取る", "example": "Let's grab some coffee.", "pos": "verb"},
            {"word": "awesome", "meaning": "すごい、最高の", "example": "That movie was awesome!", "pos": "adjective"},
            {"word": "hang out", "meaning": "遊ぶ、過ごす", "example": "Do you want to hang out this weekend?", "pos": "phrasal verb"},
            {"word": "figure out", "meaning": "理解する、解決する", "example": "I can't figure out this problem.", "pos": "phrasal verb"},
            {"word": "exhausted", "meaning": "疲れ果てた", "example": "I'm exhausted after the long meeting.", "pos": "adjective"},
            {"word": "binge-watch", "meaning": "一気見する", "example": "I binge-watched the entire series.", "pos": "verb"},
            {"word": "procrastinate", "meaning": "先延ばしにする", "example": "Stop procrastinating and start studying!", "pos": "verb"},
            {"word": "chill", "meaning": "リラックスする", "example": "Let's just chill at home tonight.", "pos": "verb"},
            {"word": "legit", "meaning": "本物の、正当な", "example": "This website looks legit.", "pos": "adjective"},
        ]
    }
}


def get_word_details(word):
    """単語の詳細情報をGPTで生成"""
    
    client = get_openai_client()
    
    prompt = f"""Provide detailed information about the English word "{word}" for a Japanese learner.

Output in JSON format:
{{
    "word": "{word}",
    "pronunciation": "<IPA pronunciation>",
    "meanings": [
        {{
            "pos": "<part of speech>",
            "definition_en": "<English definition>",
            "definition_ja": "<Japanese translation>",
            "examples": ["<example sentence 1>", "<example sentence 2>"],
            "examples_ja": ["<Japanese translation of example 1>", "<Japanese translation of example 2>"]
        }}
    ],
    "synonyms": ["<synonym1>", "<synonym2>"],
    "antonyms": ["<antonym1>", "<antonym2>"],
    "collocations": ["<common collocation 1>", "<common collocation 2>"],
    "usage_notes": "<Notes for Japanese learners, especially common mistakes / 日本人学習者向けの注意点>",
    "memory_tip": "<A tip to remember this word / 覚え方のヒント>"
}}
"""

    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": "You are a vocabulary expert helping Japanese learners. Respond in valid JSON."},
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


def generate_quiz_question(word_data, all_words, quiz_type="meaning"):
    """クイズ問題を生成"""
    
    word = word_data["word"]
    meaning = word_data["meaning"]
    example = word_data.get("example", "")
    
    # 不正解の選択肢を生成
    other_words = [w for w in all_words if w["word"] != word]
    distractors = random.sample(other_words, min(3, len(other_words)))
    
    if quiz_type == "meaning":
        # 意味を当てる
        question = f"What does **{word}** mean?"
        correct = meaning
        options = [meaning] + [d["meaning"] for d in distractors]
        random.shuffle(options)
        hint = f"Example: {example}" if example else None
        
    elif quiz_type == "word":
        # 単語を当てる
        question = f"Which word means **{meaning}**?"
        correct = word
        options = [word] + [d["word"] for d in distractors]
        random.shuffle(options)
        hint = None
        
    elif quiz_type == "fill":
        # 穴埋め
        if example:
            blank_example = example.replace(word, "_____").replace(word.capitalize(), "_____")
            question = f"Fill in the blank:\n\n*{blank_example}*"
            correct = word
            options = [word] + [d["word"] for d in distractors]
            random.shuffle(options)
            hint = f"Meaning: {meaning}"
        else:
            return generate_quiz_question(word_data, all_words, "meaning")
    
    return {
        "question": question,
        "correct": correct,
        "options": options,
        "hint": hint,
        "word_data": word_data
    }


def generate_word_list_from_prompt(prompt, num_words=20, level="B1"):
    """
    プロンプトから単語リストを自動生成
    例: "TOEFL頻出単語", "環境問題の語彙", "ビジネスメールで使う表現"
    """
    
    client = get_openai_client()
    
    system_prompt = """You are a vocabulary expert for Japanese English learners.
Generate word lists based on user requests.
Always respond in valid JSON format."""

    user_prompt = f"""Generate a vocabulary list based on this request:
"{prompt}"

Requirements:
- Number of words: {num_words}
- Target level: {level} (CEFR)
- For Japanese university students

Output format (JSON):
{{
    "list_name": "<リスト名 in English and Japanese>",
    "description": "<説明 in English and Japanese>",
    "level": "{level}",
    "words": [
        {{
            "word": "<English word or phrase>",
            "meaning": "<Japanese meaning>",
            "example": "<Example sentence>",
            "pos": "<part of speech>",
            "tips": "<Usage tip for Japanese learners / 日本人学習者向けのヒント>"
        }}
    ]
}}

Make sure:
1. Words are appropriate for the requested topic/test
2. Examples are practical and natural
3. Include tips specific to Japanese learners (common mistakes, similar Japanese expressions, etc.)
"""

    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            temperature=0.7,
            response_format={"type": "json_object"}
        )
        
        result = json.loads(response.choices[0].message.content)
        result["success"] = True
        result["generated"] = True
        return result
        
    except Exception as e:
        return {"success": False, "error": str(e)}


def generate_exercises_for_word(word, exercise_types=["meaning", "example", "collocation"]):
    """
    1つの単語に対して様々な練習問題を生成
    """
    
    client = get_openai_client()
    
    prompt = f"""Create various exercises for the English word "{word}" for Japanese learners.

Generate exercises in JSON format:
{{
    "word": "{word}",
    "exercises": [
        {{
            "type": "meaning_choice",
            "question": "<Question in English>",
            "options": ["<option1>", "<option2>", "<option3>", "<option4>"],
            "correct": "<correct answer>",
            "explanation": "<Explanation in English / 日本語の説明>"
        }},
        {{
            "type": "fill_blank",
            "question": "<Sentence with _____ for the blank>",
            "answer": "{word}",
            "hint": "<Hint / ヒント>",
            "explanation": "<Explanation / 説明>"
        }},
        {{
            "type": "collocation",
            "question": "Which word goes with '{word}'?",
            "options": ["<word1>", "<word2>", "<word3>", "<word4>"],
            "correct": "<correct collocation>",
            "full_phrase": "<full collocation phrase>",
            "explanation": "<Explanation / 説明>"
        }},
        {{
            "type": "synonym",
            "question": "Which word is closest in meaning to '{word}'?",
            "options": ["<synonym1>", "<word2>", "<word3>", "<word4>"],
            "correct": "<correct synonym>",
            "explanation": "<Explanation / 説明>"
        }},
        {{
            "type": "sentence_creation",
            "instruction": "Create a sentence using '{word}'",
            "sample_answer": "<Sample sentence>",
            "key_points": ["<Point 1>", "<Point 2>"]
        }}
    ],
    "memory_tips": "<Tips to remember this word / この単語の覚え方>",
    "common_mistakes": "<Common mistakes Japanese learners make / 日本人がよくする間違い>"
}}
"""

    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": "You are a vocabulary exercise creator for Japanese English learners. Respond in valid JSON."},
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
