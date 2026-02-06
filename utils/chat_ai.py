import streamlit as st
from openai import OpenAI
import json

# シチュエーション定義
SITUATIONS = {
    "airport": {
        "name": "空港でのチェックイン",
        "icon": "✈️",
        "category": "旅行",
        "description": "空港のチェックインカウンターでの会話",
        "ai_role": "You are an airline check-in staff at an international airport.",
        "first_message": "Good morning! Welcome to Sky Airlines. May I see your passport and booking confirmation, please?"
    },
    "restaurant": {
        "name": "レストランでの注文",
        "icon": "🍽️",
        "category": "旅行",
        "description": "レストランでの注文や質問",
        "ai_role": "You are a friendly waiter at a casual restaurant.",
        "first_message": "Hi there! Welcome to Ocean View Cafe. Here's your menu. Can I get you something to drink while you decide?"
    },
    "hotel": {
        "name": "ホテルのチェックイン",
        "icon": "🏨",
        "category": "旅行",
        "description": "ホテルのフロントでの会話",
        "ai_role": "You are a hotel receptionist at a mid-range hotel.",
        "first_message": "Good evening and welcome to Grand Hotel. Do you have a reservation with us?"
    },
    "shopping": {
        "name": "買い物",
        "icon": "🛍️",
        "category": "日常",
        "description": "お店での買い物の会話",
        "ai_role": "You are a helpful shop assistant at a clothing store.",
        "first_message": "Hi! Welcome to our store. Is there anything specific you're looking for today?"
    },
    "directions": {
        "name": "道を尋ねる",
        "icon": "🗺️",
        "category": "日常",
        "description": "道順を聞く・教える",
        "ai_role": "You are a friendly local person on the street.",
        "first_message": "Oh, hi! You look a bit lost. Can I help you find something?"
    },
    "job_interview": {
        "name": "就職面接",
        "icon": "💼",
        "category": "ビジネス",
        "description": "英語での就職面接練習",
        "ai_role": "You are an HR manager conducting a job interview for an entry-level position.",
        "first_message": "Hello, thank you for coming in today. Please have a seat. So, tell me a little about yourself."
    },
    "presentation_qa": {
        "name": "プレゼン後のQ&A",
        "icon": "📊",
        "category": "ビジネス",
        "description": "プレゼンテーション後の質疑応答",
        "ai_role": "You are an audience member who just watched a presentation and has questions.",
        "first_message": "Thank you for the presentation. I have a question about one of your main points. Could you elaborate on that?"
    },
    "doctor": {
        "name": "病院での診察",
        "icon": "🏥",
        "category": "日常",
        "description": "医師との会話",
        "ai_role": "You are a friendly doctor at a clinic.",
        "first_message": "Hello, I'm Dr. Smith. What brings you in today? How are you feeling?"
    },
    "small_talk": {
        "name": "スモールトーク",
        "icon": "☕",
        "category": "日常",
        "description": "カジュアルな雑談",
        "ai_role": "You are a friendly colleague or acquaintance making small talk.",
        "first_message": "Hey! How's it going? Did you do anything fun this weekend?"
    },
    "academic": {
        "name": "教授との相談",
        "icon": "🎓",
        "category": "学術",
        "description": "大学の教授との相談",
        "ai_role": "You are a university professor having office hours.",
        "first_message": "Hi, come on in. What can I help you with today?"
    }
}

# 自由会話トピック
FREE_TOPICS = {
    "free_hobbies": {
        "name": "趣味について",
        "icon": "🎨",
        "prompt": "Have a casual conversation about hobbies and interests."
    },
    "free_travel": {
        "name": "旅行について",
        "icon": "✈️",
        "prompt": "Have a casual conversation about travel experiences and dream destinations."
    },
    "free_food": {
        "name": "食べ物について",
        "icon": "🍜",
        "prompt": "Have a casual conversation about food, cooking, and restaurants."
    },
    "free_movies": {
        "name": "映画・ドラマについて",
        "icon": "🎬",
        "prompt": "Have a casual conversation about movies, TV shows, and entertainment."
    },
    "free_work_study": {
        "name": "仕事・勉強について",
        "icon": "📚",
        "prompt": "Have a casual conversation about work, studies, or career goals."
    },
    "free_free": {
        "name": "完全フリートーク",
        "icon": "💬",
        "prompt": "Have a completely free conversation about anything the user wants to talk about."
    }
}


def get_openai_client():
    return OpenAI(api_key=st.secrets["openai"]["api_key"])


def get_system_prompt(situation_key, level):
    """システムプロンプトを生成"""
    
    level_instructions = {
        "A1": "Use very simple vocabulary and short sentences. Speak slowly and clearly. If the user struggles, offer simple choices or yes/no questions.",
        "A2": "Use simple vocabulary and basic sentence structures. Be patient and rephrase if needed.",
        "B1": "Use everyday vocabulary and moderate complexity. Encourage the user to express opinions.",
        "B2": "Use natural, varied vocabulary. Engage in more complex discussions. Gently challenge the user.",
        "C1": "Use sophisticated vocabulary and complex structures naturally. Discuss abstract topics. Treat the user as a near-native speaker."
    }
    
    base_prompt = f"""You are having a spoken English conversation practice with a Japanese university student.

IMPORTANT GUIDELINES:
1. Level: The student's level is {level}. {level_instructions.get(level, level_instructions['B1'])}

2. Conversation Style:
   - Keep responses concise (2-4 sentences max) to maintain natural conversation flow
   - Sound natural and friendly, not like a textbook
   - React to what the user says before adding new information
   - Ask follow-up questions to keep the conversation going

3. Support:
   - If the user seems stuck, offer gentle prompts or rephrase your question
   - Don't correct errors directly during conversation (save for feedback)
   - If there's a communication breakdown, try to understand the intent

4. Natural Speech:
   - Use contractions (I'm, you're, don't, etc.)
   - Include filler words occasionally (well, you know, actually)
   - Show reactions (Oh really?, That's interesting!, I see)

5. Cultural Awareness:
   - Be aware the user is Japanese and may have different cultural references
   - Don't assume Western cultural knowledge
   - Be encouraging - many Japanese learners are shy about speaking

"""
    
    if situation_key in FREE_TOPICS:
        topic = FREE_TOPICS[situation_key]
        base_prompt += f"\nTOPIC: {topic['prompt']}\n"
        base_prompt += "Start with a friendly greeting and naturally lead into the topic."
    elif situation_key in SITUATIONS:
        situation = SITUATIONS[situation_key]
        base_prompt += f"\nROLE: {situation.get('ai_role', 'You are a friendly conversation partner.')}\n"
        base_prompt += f"SCENARIO: {situation.get('description', '')}\n"
    
    return base_prompt


def get_ai_response(messages, situation, level, is_first=False, request_hint=False):
    """AI応答を取得"""
    
    client = get_openai_client()
    
    if is_first:
        if situation in FREE_TOPICS:
            first_messages = {
                "free_hobbies": "Hey! So I'm curious, what do you like to do in your free time?",
                "free_travel": "Hi there! Have you traveled anywhere interesting recently? Or is there somewhere you'd love to go?",
                "free_food": "Hey! I was just thinking about lunch. What kind of food do you like?",
                "free_movies": "Hi! Have you watched anything good lately? I'm always looking for recommendations!",
                "free_work_study": "Hey! How's everything going with your studies? Busy semester?",
                "free_free": "Hi! It's nice to chat with you. So, what's on your mind today?"
            }
            return first_messages.get(situation, "Hi! What would you like to talk about?")
        elif situation in SITUATIONS:
            return SITUATIONS[situation].get("first_message", "Hello! How can I help you today?")
        else:
            return "Hi! What would you like to talk about?"
    
    if request_hint:
        hint_prompt = f"""The student seems stuck. Based on the conversation, give a SHORT hint in Japanese about what they could say next.
Keep it to one simple suggestion. Format: 「〜と言ってみましょう」

Last few messages:
{messages[-3:] if len(messages) >= 3 else messages}
"""
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": hint_prompt}],
            max_tokens=100,
            temperature=0.7
        )
        return response.choices[0].message.content
    
    system_prompt = get_system_prompt(situation, level)
    
    api_messages = [{"role": "system", "content": system_prompt}]
    for msg in messages:
        api_messages.append({
            "role": msg["role"],
            "content": msg["content"]
        })
    
    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=api_messages,
        max_tokens=150,
        temperature=0.8
    )
    
    return response.choices[0].message.content


def get_session_feedback(messages, level, situation, used_voice_input=False):
    """セッション終了時のフィードバックを生成"""
    
    client = get_openai_client()
    
    user_messages = [m["content"] for m in messages if m["role"] == "user"]
    user_text = "\n".join(user_messages)
    
    # 音声入力を使用したかどうかで発音フィードバックの有無を変える
    pronunciation_instruction = ""
    if used_voice_input:
        pronunciation_instruction = """
    "pronunciation_tips": "<音声入力で練習したため、認識された内容から推測される発音のポイント（日本語）>",
"""
    else:
        pronunciation_instruction = """
    "pronunciation_tips": null,
"""
    
    prompt = f"""Analyze this English conversation practice by a Japanese university student (Level: {level}).

Student's utterances:
{user_text}

Voice input used: {used_voice_input}

Provide feedback in JSON format:
{{
    "scores": {{
        "overall": <0-100: 総合評価>,
        "vocabulary": <0-100: 語彙の適切さ・多様性>,
        "grammar": <0-100: 文法の正確さ>,
        "communication": <0-100: コミュニケーション能力（会話の継続、質問への応答）>
    }},
    "feedback": "<総合フィードバック（日本語、3-4文）励ましを含めつつ、具体的な改善点を指摘>",
    "improvements": [
        {{
            "original": "<学生の元の表現>",
            "improved": "<より自然な表現>",
            "explanation": "<なぜその表現が良いか（日本語）>"
        }}
    ],
    "good_points": ["<良かった点1（日本語）>", "<良かった点2（日本語）>"],
    {pronunciation_instruction}
    "speaking_practice_tip": "<実際に人と話すときのアドバイス（日本語）。テキスト入力の場合は音声練習を勧める内容を含める>",
    "advice": "<次の学習ステップへのアドバイス（日本語）>"
}}

Important notes:
- Focus on Japanese-specific issues (articles, verb forms, unnatural expressions from L1 transfer)
- Keep feedback encouraging but specific
- Suggest expressions that work across different English varieties (World Englishes perspective)
- {"Since voice input was used, you can comment on potential pronunciation issues based on common Japanese learner patterns for the words they used." if used_voice_input else "Since text input was used, do NOT provide specific pronunciation feedback. Instead, encourage them to try voice input next time for pronunciation practice."}
"""

    try:
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": "You are an expert English teacher specializing in Japanese EFL learners. Respond only in valid JSON."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.3,
            response_format={"type": "json_object"}
        )
        
        result = json.loads(response.choices[0].message.content)
        result["success"] = True
        result["used_voice_input"] = used_voice_input
        return result
        
    except Exception as e:
        return {"success": False, "error": str(e)}
