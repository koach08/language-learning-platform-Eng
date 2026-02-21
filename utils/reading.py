import streamlit as st
from openai import OpenAI
import json
import time


def get_openai_client():
    return OpenAI(api_key=st.secrets["openai"]["api_key"])


# デモ用記事（既存のまま保持）
DEMO_ARTICLES = {
    "climate": {
        "title": "Climate Change and Global Action",
        "level": "B2",
        "category": "Environment",
        "word_count": 250,
        "text": """Climate change is one of the most pressing challenges facing humanity today. Scientists around the world agree that human activities, particularly the burning of fossil fuels, are causing global temperatures to rise at an unprecedented rate. The effects of climate change are already visible. Extreme weather events, such as hurricanes, droughts, and floods, are becoming more frequent and severe. Sea levels are rising, threatening coastal communities. Many species are struggling to adapt to rapidly changing conditions. However, there is hope. Countries around the world are taking action to reduce greenhouse gas emissions. Renewable energy sources like solar and wind power are becoming more affordable and widespread. Many businesses are adopting sustainable practices, and individuals are making changes in their daily lives to reduce their carbon footprint. The Paris Agreement, signed by nearly 200 countries, represents a global commitment to limit temperature rise to 1.5 degrees Celsius above pre-industrial levels. While challenges remain, international cooperation and technological innovation offer pathways to a more sustainable future. Young people are playing a crucial role in this movement, demanding action from governments and corporations. Their activism has helped raise awareness and push climate change to the top of the political agenda in many countries.""",
    },
    "ai_education": {
        "title": "Artificial Intelligence in Education",
        "level": "B1",
        "category": "Technology",
        "word_count": 200,
        "text": """Artificial Intelligence (AI) is changing the way we learn. From personalized tutoring to automated grading, AI tools are being used in classrooms around the world. One of the biggest benefits of AI in education is personalization. AI systems can analyze how each student learns and adapt lessons to their needs. If a student struggles with a concept, the AI can provide extra practice. If they master it quickly, they can move on to more challenging material. AI can also help teachers save time. Grading essays and tests takes many hours, but AI tools can do this work quickly. This gives teachers more time to focus on helping students directly. However, there are concerns about AI in education. Some worry that too much screen time is bad for children. Others are concerned about privacy and data security. There are also questions about whether AI can truly replace human teachers. Despite these challenges, AI will likely play an increasingly important role in education. The key is to use these tools wisely, combining the best of technology with the irreplaceable human elements of teaching.""",
    },
    "remote_work": {
        "title": "The Rise of Remote Work",
        "level": "B1",
        "category": "Business",
        "word_count": 180,
        "text": """The COVID-19 pandemic changed the way many people work. Millions of employees around the world started working from home, and many continue to do so today. Remote work has several advantages. Workers save time and money by not commuting. They often have more flexibility to balance work and personal life. Many people report being more productive when working from home. Companies also benefit from remote work. They can save money on office space and hire talented people from anywhere in the world. This has led to more diverse and global teams. However, remote work also has challenges. Some workers feel isolated and miss the social interaction of an office. Communication can be more difficult when teams are not in the same place. It can also be hard to separate work from personal life when your home is your office. Many companies are now adopting "hybrid" models, where employees work some days in the office and some days from home. This approach tries to combine the benefits of both remote and in-person work.""",
    },
}


# ============================================================
# 問題タイプ分布（レベル別）
# ============================================================

def _get_question_distribution(level: str, num_questions: int) -> dict:
    """レベルと問題数に応じたTrue/False・4択の分布を返す"""
    if level in ("A1", "A2", "B1"):
        # 基礎レベル: True/False多め・inference少なめ
        tf_count = max(2, num_questions // 2)
        mc_detail = max(1, (num_questions - tf_count) - 1)
        mc_inference = num_questions - tf_count - mc_detail
        mc_main_idea = 0
    else:
        # 上級レベル(B2,C1): 4択多め・TOEFL型inference含む
        tf_count = max(2, num_questions // 3)
        mc_inference = 2
        mc_main_idea = 1
        mc_detail = num_questions - tf_count - mc_inference - mc_main_idea
        mc_detail = max(1, mc_detail)

    return {
        "true_false": tf_count,
        "mc_detail": mc_detail,
        "mc_inference": mc_inference,
        "mc_main_idea": mc_main_idea,
    }


# ============================================================
# メイン問題生成（ハイブリッド: True/False + 4択）
# ============================================================

def generate_comprehension_questions(text, title, num_questions=5, level="B1"):
    """読解問題を生成（ハイブリッド版: True/False + 4択 + TOEFL型inference）
    
    モデル:
    - True/False・detail 4択: gpt-4o-mini（コスト抑制）
    - inference・main_idea 4択: gpt-4o（品質重視）
    """
    dist = _get_question_distribution(level, num_questions)
    tf_count = dist["true_false"]
    mc_detail = dist["mc_detail"]
    mc_inference = dist["mc_inference"]
    mc_main_idea = dist["mc_main_idea"]

    all_questions = []

    # --- True/False問題（gpt-4o-mini）---
    if tf_count > 0:
        tf_result = _generate_true_false(text, title, tf_count, level)
        if tf_result.get("success"):
            all_questions.extend(tf_result.get("questions", []))

    # --- detail 4択（gpt-4o-mini）---
    if mc_detail > 0:
        detail_result = _generate_mc_detail(text, title, mc_detail, level)
        if detail_result.get("success"):
            all_questions.extend(detail_result.get("questions", []))

    # --- inference + main_idea 4択（gpt-4o）---
    mc_high = mc_inference + mc_main_idea
    if mc_high > 0:
        high_result = _generate_mc_high_order(text, title, mc_inference, mc_main_idea, level)
        if high_result.get("success"):
            all_questions.extend(high_result.get("questions", []))

    if not all_questions:
        return {"success": False, "error": "問題の生成に失敗しました"}

    return {"success": True, "questions": all_questions}


def _generate_true_false(text, title, count, level):
    """True/False問題をgpt-4o-miniで生成"""
    client = get_openai_client()
    prompt = f"""You are an EFL reading test designer. Create {count} True/False questions for this article.

Article Title: {title}
Level: {level}
Article:
{text}

CRITICAL REQUIREMENT: Every question MUST be impossible to answer without reading this specific article.
- Do NOT create questions about facts that educated people already know.
- Do NOT create questions about obvious or universally known information.
- ONLY create questions about specific details, numbers, names, sequences, or claims that are UNIQUE to this article.
- If a student who has NOT read this article could guess correctly, the question is INVALID.

RULES:
1. Each statement must be verifiable ONLY by reading THIS specific article — general knowledge must be completely insufficient.
2. Focus on: specific statistics, dates, names, locations, sequences, causes, or conclusions stated in THIS article.
3. Use paraphrase and synonyms — do NOT copy sentences directly from the article.
4. False statements must contain ONE specific factual error (wrong number, reversed cause/effect, wrong subject) from the article.
5. Distribute True and False answers roughly equally.
6. Every question must include the exact quote from the article that proves the answer (text_evidence).

Output JSON:
{{
  "questions": [
    {{
      "type": "true_false",
      "question": "<Statement in English>",
      "question_ja": "<日本語訳>",
      "correct": "True" or "False",
      "explanation": "<Why True or False — EN and JA>",
      "text_evidence": "<Exact short quote from the article>"
    }}
  ]
}}"""

    try:
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": "You are an expert EFL test designer. Every question must be impossible to answer without reading the provided article. Respond in valid JSON only."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.3,
            max_tokens=2000,
            response_format={"type": "json_object"}
        )
        result = json.loads(response.choices[0].message.content)
        result["success"] = True
        return result
    except Exception as e:
        return {"success": False, "error": str(e)}


def _generate_mc_detail(text, title, count, level):
    """detail系4択問題をgpt-4o-miniで生成"""
    client = get_openai_client()
    prompt = f"""You are an EFL reading test designer. Create {count} multiple-choice detail questions.

Article Title: {title}
Level: {level}
Article:
{text}

CRITICAL REQUIREMENT: Every question MUST be impossible to answer without reading this specific article.
- Do NOT ask about things an educated person would already know.
- ONLY ask about specific details unique to this article: exact numbers, specific names, particular sequences, or specific claims made by the author.
- All 4 options must look plausible — wrong options should use content from the article but with key details changed.
- A student who skimmed or didn't read this article should NOT be able to guess correctly.

RULES:
1. Focus ONLY on specific facts, numbers, sequences, names, or comparisons stated IN THIS article.
2. Correct answer must PARAPHRASE the article — not copy it verbatim.
3. Wrong options: use words from the article but change ONE key detail (wrong number, wrong person, wrong place).
4. Absolutely cannot be answered from general knowledge alone.

Output JSON:
{{
  "questions": [
    {{
      "type": "detail",
      "question": "<Question in English>",
      "question_ja": "<日本語訳>",
      "options": ["<A>", "<B>", "<C>", "<D>"],
      "correct": "<Exact text of correct option>",
      "explanation": "<Why correct + why others wrong — EN and JA>",
      "text_evidence": "<Exact short quote from the article>"
    }}
  ]
}}"""

    try:
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": "You are an expert EFL test designer. Every question must be impossible to answer without reading the provided article. Respond in valid JSON only."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.3,
            max_tokens=2000,
            response_format={"type": "json_object"}
        )
        result = json.loads(response.choices[0].message.content)
        result["success"] = True
        return result
    except Exception as e:
        return {"success": False, "error": str(e)}


def _generate_mc_high_order(text, title, inference_count, main_idea_count, level):
    """inference・main_idea 4択をgpt-4oで生成（TOEFL型）"""
    client = get_openai_client()

    inference_instruction = ""
    if inference_count > 0:
        inference_instruction = f"""
INFERENCE QUESTIONS ({inference_count} questions) — TOEFL iBT style:
- Ask what can be INFERRED or IMPLIED — NOT directly stated.
- Examples of good inference questions:
  * "What does the author imply about X?"
  * "Which statement would the author most likely agree with?"
  * "What can be inferred about X from the passage?"
  * "The passage suggests that the author's attitude toward X is..."
- Wrong options: one too strong/extreme, one contradicts the passage, one is unrelated.
- The correct answer must follow LOGICALLY from the passage's specific content — not from general knowledge.
"""

    main_idea_instruction = ""
    if main_idea_count > 0:
        main_idea_instruction = f"""
MAIN IDEA QUESTIONS ({main_idea_count} questions) — TOEFL iBT style:
- Ask about the PRIMARY purpose or central argument of THIS specific article.
- Wrong options: too narrow (one detail), too broad (general topic), opposite of the article's stance.
"""

    prompt = f"""You are an expert TOEFL iBT reading test designer. Create high-order thinking questions.

Article Title: {title}
Level: {level}
Article:
{text}

{inference_instruction}
{main_idea_instruction}

CRITICAL: Every question must require careful reading of THIS article. General knowledge must not be sufficient.

Output JSON:
{{
  "questions": [
    {{
      "type": "inference" or "main_idea",
      "question": "<Question in English>",
      "question_ja": "<日本語訳>",
      "options": ["<A>", "<B>", "<C>", "<D>"],
      "correct": "<Exact text of correct option>",
      "explanation": "<Detailed explanation: why correct, why each wrong option fails — EN and JA>",
      "text_evidence": "<Passage clue(s) that support the inference>"
    }}
  ]
}}"""

    try:
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": "You are an expert TOEFL iBT reading test designer. Respond in valid JSON only."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.4,
            response_format={"type": "json_object"}
        )
        result = json.loads(response.choices[0].message.content)
        result["success"] = True
        return result
    except Exception as e:
        return {"success": False, "error": str(e)}


# ============================================================
# 検定対策問題生成（gpt-4o使用）
# ============================================================

EXAM_CONFIGS = {
    "TOEFL": {
        "label": "TOEFL iBT",
        "description": "inference・rhetorical purpose・vocabulary in context",
        "type_distribution": {
            "true_false": 0,
            "mc_detail": 1,
            "mc_inference": 3,
            "mc_main_idea": 1,
        },
        "system_prompt": "You are an expert TOEFL iBT Academic Reading test designer with 20+ years experience.",
        "style_note": """TOEFL iBT style:
- inference: "What does the author imply about...?" / "What can be inferred from paragraph X?"
- rhetorical_purpose: "Why does the author mention X?" / "What is the purpose of paragraph X?"
- vocabulary_in_context: "The word X in paragraph Y is closest in meaning to..."
- Distractors must be plausible to test-takers who skimmed without careful reading."""
    },
    "TOEIC": {
        "label": "TOEIC L&R",
        "description": "NOT問題・言い換え・ビジネス文書",
        "type_distribution": {
            "true_false": 0,
            "mc_detail": 2,
            "mc_inference": 1,
            "mc_main_idea": 1,
            "mc_not": 1,
        },
        "system_prompt": "You are an expert TOEIC L&R Part 7 test designer.",
        "style_note": """TOEIC Part 7 style:
- NOT questions: "Which is NOT mentioned in the article?" (1 question)
- detail: specific facts with paraphrase answers
- inference: business-context implied meaning
- main_idea: what the article is mainly about
- Use business/professional vocabulary and context."""
    },
    "EIKEN": {
        "label": "英検（準1級〜1級）",
        "description": "内容一致・要旨把握・語句の意味",
        "type_distribution": {
            "true_false": 0,
            "mc_detail": 2,
            "mc_inference": 1,
            "mc_main_idea": 1,
        },
        "system_prompt": "You are an expert Eiken (英検) Grade Pre-1 / Grade 1 reading test designer.",
        "style_note": """英検スタイル:
- 内容一致問題: specific content matching with paraphrase
- 要旨把握: main point of a paragraph or the whole passage  
- 語句の意味: vocabulary in context
- Questions may be in Japanese or English depending on level
- Follow authentic 英検 question stems: 「本文の内容と一致するものを選びなさい」"""
    },
}


def generate_exam_questions(text, title, exam_type="TOEFL", level="B2"):
    """検定対策問題をgpt-4oで生成
    
    exam_type: "TOEFL" | "TOEIC" | "EIKEN"
    """
    config = EXAM_CONFIGS.get(exam_type, EXAM_CONFIGS["TOEFL"])
    client = get_openai_client()

    dist = config["type_distribution"]
    total = sum(dist.values())

    prompt = f"""{config['system_prompt']}

Create {total} reading comprehension questions for this article in {config['label']} style.

Article Title: {title}
CEFR Level: {level}
Article:
{text}

==============================
{config['style_note']}
==============================

ANTI-CHEAT RULES (apply to ALL questions):
1. Cannot be answered from general knowledge — requires reading THIS article.
2. Correct answer uses paraphrase/synonyms, NOT copied text.
3. Wrong options are plausible to someone who skimmed but did not read carefully.
4. Include text_evidence for every question.

Question type distribution: {dist}

Output JSON:
{{
  "exam_type": "{exam_type}",
  "questions": [
    {{
      "type": "<detail|inference|main_idea|rhetorical_purpose|vocabulary_in_context|not_mentioned>",
      "question": "<Question>",
      "question_ja": "<日本語訳（英検以外も参考用に記載）>",
      "options": ["<A>", "<B>", "<C>", "<D>"],
      "correct": "<Exact text of correct option>",
      "explanation": "<Detailed EN + JA explanation>",
      "text_evidence": "<Relevant passage excerpt>"
    }}
  ]
}}"""

    try:
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": config["system_prompt"] + " Respond in valid JSON only."},
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


# ============================================================
# 既存関数（変更なし）
# ============================================================

def generate_summary_and_vocabulary(text, title, level="B1"):
    """要約と重要語彙を生成（gpt-4o-mini）"""
    client = get_openai_client()
    prompt = f"""Analyze this article for a Japanese English learner (Level: {level}).

Article Title: {title}
Article Text: {text}

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
}}"""
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
    """プロンプトから記事を生成（gpt-4o-mini）"""
    client = get_openai_client()
    system_prompt = f"""You are a content creator for English learners. Create engaging, educational articles appropriate for {level} level Japanese university students. Articles should be approximately {word_count} words."""
    user_prompt = f"""Create a reading article based on this request: "{prompt}"

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
- Use clear paragraph structure
- Include specific facts, numbers, and details that can be tested"""
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
    if reading_time_seconds <= 0:
        return 0
    return int((word_count / reading_time_seconds) * 60)


def get_wpm_feedback(wpm, level):
    targets = {
        "A1": (50, 80), "A2": (80, 120), "B1": (120, 180),
        "B2": (180, 220), "C1": (220, 280)
    }
    target_min, target_max = targets.get(level, (120, 180))
    if wpm < target_min:
        return {
            "rating": "🐢 ゆっくり / Slow",
            "message": f"目標: {target_min}-{target_max} WPM。焦らず、徐々にスピードを上げていきましょう。",
            "color": "orange"
        }
    elif wpm <= target_max:
        return {
            "rating": "👍 良いペース / Good pace",
            "message": f"目標範囲内です！この調子で続けましょう。",
            "color": "green"
        }
    else:
        return {
            "rating": "🚀 速い / Fast",
            "message": f"素晴らしい速さです！理解度も確認しましょう。",
            "color": "blue"
        }
