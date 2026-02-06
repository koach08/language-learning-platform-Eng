import streamlit as st
from openai import OpenAI
import json
import time

def get_openai_client():
    return OpenAI(api_key=st.secrets["openai"]["api_key"])


# デモ用記事
DEMO_ARTICLES = {
    "climate": {
        "title": "Climate Change and Global Action",
        "level": "B2",
        "category": "Environment",
        "word_count": 250,
        "text": """Climate change is one of the most pressing challenges facing humanity today. Scientists around the world agree that human activities, particularly the burning of fossil fuels, are causing global temperatures to rise at an unprecedented rate.

The effects of climate change are already visible. Extreme weather events, such as hurricanes, droughts, and floods, are becoming more frequent and severe. Sea levels are rising, threatening coastal communities. Many species are struggling to adapt to rapidly changing conditions.

However, there is hope. Countries around the world are taking action to reduce greenhouse gas emissions. Renewable energy sources like solar and wind power are becoming more affordable and widespread. Many businesses are adopting sustainable practices, and individuals are making changes in their daily lives to reduce their carbon footprint.

The Paris Agreement, signed by nearly 200 countries, represents a global commitment to limit temperature rise to 1.5 degrees Celsius above pre-industrial levels. While challenges remain, international cooperation and technological innovation offer pathways to a more sustainable future.

Young people are playing a crucial role in this movement, demanding action from governments and corporations. Their activism has helped raise awareness and push climate change to the top of the political agenda in many countries.""",
    },
    "ai_education": {
        "title": "Artificial Intelligence in Education",
        "level": "B1",
        "category": "Technology",
        "word_count": 200,
        "text": """Artificial Intelligence (AI) is changing the way we learn. From personalized tutoring to automated grading, AI tools are being used in classrooms around the world.

One of the biggest benefits of AI in education is personalization. AI systems can analyze how each student learns and adapt lessons to their needs. If a student struggles with a concept, the AI can provide extra practice. If they master it quickly, they can move on to more challenging material.

AI can also help teachers save time. Grading essays and tests takes many hours, but AI tools can do this work quickly. This gives teachers more time to focus on helping students directly.

However, there are concerns about AI in education. Some worry that too much screen time is bad for children. Others are concerned about privacy and data security. There are also questions about whether AI can truly replace human teachers.

Despite these challenges, AI will likely play an increasingly important role in education. The key is to use these tools wisely, combining the best of technology with the irreplaceable human elements of teaching.""",
    },
    "remote_work": {
        "title": "The Rise of Remote Work",
        "level": "B1",
        "category": "Business",
        "word_count": 180,
        "text": """The COVID-19 pandemic changed the way many people work. Millions of employees around the world started working from home, and many continue to do so today.

Remote work has several advantages. Workers save time and money by not commuting. They often have more flexibility to balance work and personal life. Many people report being more productive when working from home.

Companies also benefit from remote work. They can save money on office space and hire talented people from anywhere in the world. This has led to more diverse and global teams.

However, remote work also has challenges. Some workers feel isolated and miss the social interaction of an office. Communication can be more difficult when teams are not in the same place. It can also be hard to separate work from personal life when your home is your office.

Many companies are now adopting "hybrid" models, where employees work some days in the office and some days from home. This approach tries to combine the benefits of both remote and in-person work.""",
    },
}


def generate_comprehension_questions(text, title, num_questions=5, level="B1"):
    """読解問題を生成"""
    
    client = get_openai_client()
    
    prompt = f"""Based on this article, create reading comprehension questions for a Japanese English learner (Level: {level}).

Article Title: {title}
Article Text:
{text}

Generate {num_questions} questions in JSON format:
{{
    "questions": [
        {{
            "question": "<Question in English>",
            "question_ja": "<日本語訳>",
            "type": "<main_idea / detail / inference / vocabulary>",
            "options": ["<A>", "<B>", "<C>", "<D>"],
            "correct": "<Correct option>",
            "explanation": "<Why this is correct / 正解の理由 - bilingual>"
        }}
    ]
}}

Include:
- 1-2 main idea questions
- 2-3 detail questions  
- 1 inference question
- 1 vocabulary in context question

Make options challenging but fair. All options should be plausible."""

    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": "You are a reading comprehension expert. Create questions for Japanese English learners. Respond in valid JSON."},
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


def generate_summary_and_vocabulary(text, title, level="B1"):
    """要約と重要語彙を生成"""
    
    client = get_openai_client()
    
    prompt = f"""Analyze this article for a Japanese English learner (Level: {level}).

Article Title: {title}
Article Text:
{text}

Provide analysis in JSON format:
{{
    "summary_en": "<3-4 sentence summary in English>",
    "summary_ja": "<日本語要約>",
    "main_points": [
        "<Main point 1 / 要点1>",
        "<Main point 2 / 要点2>",
        "<Main point 3 / 要点3>"
    ],
    "key_vocabulary": [
        {{
            "word": "<Important word from the text>",
            "meaning": "<日本語の意味>",
            "context": "<How it's used in the article>"
        }}
    ],
    "discussion_questions": [
        "<Discussion question 1 / ディスカッション質問1>",
        "<Discussion question 2>"
    ],
    "related_topics": ["<Related topic 1>", "<Related topic 2>"]
}}
"""

    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": "You are a reading instructor helping Japanese English learners. Respond in valid JSON."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.5,
            response_format={"type": "json_object"}
        )
        
        result = json.loads(response.choices[0].message.content)
        result["success"] = True
        return result
        
    except Exception as e:
        return {"success": False, "error": str(e)}


def generate_article_from_prompt(prompt, level="B1", word_count=200):
    """プロンプトから記事を生成"""
    
    client = get_openai_client()
    
    system_prompt = f"""You are a content creator for English learners.
Create engaging, educational articles appropriate for {level} level Japanese university students.
Articles should be approximately {word_count} words."""

    user_prompt = f"""Create a reading article based on this request:
"{prompt}"

Output in JSON format:
{{
    "title": "<Article title>",
    "category": "<Category: Technology/Environment/Business/Culture/Science/Health/etc>",
    "level": "{level}",
    "text": "<Article text, approximately {word_count} words>",
    "word_count": <actual word count>
}}

Guidelines:
- Use vocabulary appropriate for {level} level
- Include some challenging words with context clues
- Make the content interesting and relevant to university students
- Use clear paragraph structure"""

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


def calculate_wpm(word_count, reading_time_seconds):
    """読解速度（WPM）を計算"""
    if reading_time_seconds <= 0:
        return 0
    return int((word_count / reading_time_seconds) * 60)


def get_wpm_feedback(wpm, level):
    """WPMに基づくフィードバック"""
    
    # 目安（ネイティブは200-300 WPM、学習者はレベルによる）
    targets = {
        "A1": (50, 80),
        "A2": (80, 120),
        "B1": (120, 180),
        "B2": (180, 220),
        "C1": (220, 280)
    }
    
    target_min, target_max = targets.get(level, (120, 180))
    
    if wpm < target_min:
        return {
            "rating": "🐢 ゆっくり / Slow",
            "message": f"目標: {target_min}-{target_max} WPM。焦らず、徐々にスピードを上げていきましょう。/ Target: {target_min}-{target_max} WPM. Take your time and gradually increase your speed.",
            "color": "orange"
        }
    elif wpm <= target_max:
        return {
            "rating": "👍 良いペース / Good pace",
            "message": f"目標範囲内です！この調子で続けましょう。/ You're within the target range! Keep it up.",
            "color": "green"
        }
    else:
        return {
            "rating": "🚀 速い / Fast",
            "message": f"素晴らしい速さです！理解度も確認しましょう。/ Great speed! Make sure you're also comprehending well.",
            "color": "blue"
        }
