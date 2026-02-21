import streamlit as st
from openai import OpenAI
import json


def get_openai_client():
    return OpenAI(api_key=st.secrets["openai"]["api_key"])


def _get_ai_settings(course_id: str) -> dict:
    if not course_id:
        return {}
    try:
        from utils.database import get_course_settings
        s = get_course_settings(course_id) or {}
        return s.get("ai_feedback", {})
    except Exception:
        return {}


def _get_writing_weights(course_id: str, task_type: str, assignment_id: str = None) -> dict:
    if not course_id:
        return {}
    try:
        from utils.database import get_course_settings
        s = get_course_settings(course_id) or {}
        if assignment_id:
            rubric = s.get("assignment_rubrics", {}).get(assignment_id, {})
            if rubric.get("weights"):
                return rubric["weights"]
        ww = s.get("writing_weights", {})
        # task_typeをwriting_weightsのキーにマッピング
        key_map = {
            "essay": "essay",
            "summary": "summary",
            "email": "email_letter",
            "letter": "email_letter",
            "email_letter": "email_letter",
            "general": "essay",
        }
        mapped = key_map.get(task_type, task_type)
        return ww.get(mapped, {})
    except Exception:
        return {}


def _build_feedback_language_instruction(lang: str) -> str:
    if lang == "english":
        return "Provide all feedback in English only."
    elif lang == "bilingual":
        return "Provide all feedback in both English and Japanese. Format: English text / 日本語テキスト"
    else:
        return "フィードバックはすべて日本語で提供してください。"


def _build_feedback_detail_instruction(detail: str) -> str:
    if detail == "brief":
        return "各項目1〜2文で簡潔にまとめてください。"
    elif detail == "detailed":
        return "各項目について具体例を交えて詳しく説明してください。"
    else:
        return "各項目3〜5文程度で説明してください。"


def _build_writing_priority_instruction(priority: str) -> str:
    if priority == "accuracy_focus":
        return (
            "## 評価の重点方針: 正確さ重視\n"
            "文法・語法の正確さを最優先で評価してください。"
            "誤りは具体的に指摘し、正しい形を示してください。"
        )
    elif priority == "creativity_focus":
        return (
            "## 評価の重点方針: 創造性重視\n"
            "内容の豊かさ・独自性・表現の多様さを最優先で評価してください。"
            "文法の細かいミスより、アイデアや表現力を重視してください。"
        )
    else:
        return (
            "## 評価の重点方針: バランス型\n"
            "内容・構成・語彙・文法をバランスよく評価してください。"
        )


def _build_weights_instruction(weights: dict) -> str:
    if not weights:
        return ""
    label_map = {
        "task_achievement": "課題達成度",
        "content": "内容・アイデア",
        "structure": "構成・まとまり",
        "vocabulary": "語彙",
        "grammar": "文法正確さ",
        "accuracy": "内容の正確さ",
        "conciseness": "簡潔さ",
        "tone_format": "トーン・フォーマット",
    }
    lines = ["## 評価ウェイト（この配分でスコアに重み付けしてください）:"]
    for k, v in weights.items():
        label = label_map.get(k, k)
        lines.append(f"- {label}: {v}%")
    return "\n".join(lines)


# ============================================================
# Writing評価（メイン）
# ============================================================

def evaluate_writing(text, task_type="general", level="B1", is_practice=False,
                     course_id: str = None, assignment_id: str = None):
    """
    ライティングを評価（日英バイリンガルフィードバック）
    course_idが指定された場合、course_settingsの設定をプロンプトに反映。

    引数:
        text          : 評価対象テキスト
        task_type     : "essay"/"summary"/"email_letter"/"general" など
        level         : CEFR想定レベル
        is_practice   : 練習モードか（Trueならgpt-4o-mini使用）
        course_id     : コースID（設定反映に使用）
        assignment_id : 課題ID（課題別設定を優先する場合）
    """
    client = get_openai_client()
    model = "gpt-4o-mini" if is_practice else "gpt-4o"
    word_count = len(text.split())

    # ── 設定取得 ──────────────────────────────────────────
    ai_settings = _get_ai_settings(course_id)
    weights = _get_writing_weights(course_id, task_type, assignment_id)

    wr_priority = ai_settings.get("writing_priority", "balanced")
    fb_lang     = ai_settings.get("feedback_language", "bilingual")  # writingはデフォルトbilingual
    fb_detail   = ai_settings.get("feedback_detail", "standard")
    extra_instr = ai_settings.get("extra_instruction", "")

    priority_block = _build_writing_priority_instruction(wr_priority)
    lang_block     = _build_feedback_language_instruction(fb_lang)
    detail_block   = _build_feedback_detail_instruction(fb_detail)
    weights_block  = _build_weights_instruction(weights)
    extra_block    = f"\n## 教員からの追加指示:\n{extra_instr}" if extra_instr else ""

    prompt = f"""You are an expert English writing instructor specializing in Japanese EFL learners.

## Task
Evaluate the following English writing by a Japanese university student (Level: {level}).

## Student's Writing
{text}

## Word Count: {word_count}
## Task Type: {task_type}

{priority_block}
{weights_block}
{extra_block}

## Feedback Language: {lang_block}
## Feedback Detail Level: {detail_block}

## IMPORTANT: Bilingual Feedback
Provide all feedback in BOTH English and Japanese unless instructed otherwise above.
Format: "English explanation / 日本語の説明"

## Evaluation Criteria & Output Format (JSON)

{{
    "scores": {{
        "overall": <0-100>,
        "grammar": <0-100>,
        "vocabulary": <0-100>,
        "organization": <0-100>,
        "content": <0-100>,
        "expression": <0-100>
    }},
    "cefr_level": "<A1/A2/B1/B2/C1>",
    "feedback": "<Bilingual feedback: 2-3 sentences each>",
    "grammar_errors": [
        {{
            "original": "<error>",
            "corrected": "<correction>",
            "explanation": "<English explanation / 日本語の説明>",
            "error_type": "<article/tense/subject-verb agreement/preposition/word order/other>"
        }}
    ],
    "japanese_english_issues": [
        {{
            "original": "<unnatural expression>",
            "improved": "<natural English>",
            "explanation": "<English explanation / 日本語の説明>",
            "regional_note": "<World Englishes note if applicable>"
        }}
    ],
    "vocabulary_suggestions": [
        {{
            "original": "<original word>",
            "alternatives": ["<alt1>", "<alt2>"],
            "note": "<When to use each / 使い分けのポイント>"
        }}
    ],
    "organization_feedback": "<English feedback / 日本語のフィードバック>",
    "good_points": [
        "<Good point / 良い点>",
        "<Another good point / もう一つの良い点>"
    ],
    "priority_improvements": [
        "<Priority 1 / 優先改善点1>",
        "<Priority 2 / 優先改善点2>"
    ],
    "rewritten_sample": "<Naturally rewritten version>",
    "next_steps": "<What to focus on next / 次に意識すること>"
}}

## Guidelines
1. Be encouraging while specific about errors
2. Focus on Japanese L1 transfer issues
3. Respect World Englishes - note regional variations
4. For practice mode, focus on top 3-5 errors
5. Prioritize intelligibility over native-like perfection
"""

    try:
        response = client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": (
                    "You are an expert English writing instructor. "
                    "Provide bilingual (English/Japanese) feedback unless instructed otherwise. "
                    "Always respond in valid JSON format."
                )},
                {"role": "user", "content": prompt}
            ],
            temperature=0.3,
            response_format={"type": "json_object"}
        )
        result = json.loads(response.choices[0].message.content)
        result["success"] = True
        result["word_count"] = word_count
        result["model_used"] = model
        return result

    except Exception as e:
        return {"success": False, "error": str(e)}


# ============================================================
# format_writing_feedback（変更なし・互換性維持）
# ============================================================

def format_writing_feedback(eval_result, show_full=True):
    """評価結果をMarkdown形式でフォーマット"""
    if not eval_result.get("success"):
        return f"⚠️ Evaluation Error / 評価エラー: {eval_result.get('error', 'Unknown error / 不明なエラー')}"

    feedback = []

    good_points = eval_result.get("good_points", [])
    if good_points:
        feedback.append("### ✅ Good Points / 良かった点")
        for point in good_points:
            feedback.append(f"- {point}")
        feedback.append("")

    if eval_result.get("feedback"):
        feedback.append("### 💬 Feedback / フィードバック")
        feedback.append(eval_result.get("feedback"))
        feedback.append("")

    grammar_errors = eval_result.get("grammar_errors", [])
    if grammar_errors:
        feedback.append("### ✏️ Grammar Corrections / 文法の修正点")
        for i, error in enumerate(grammar_errors[:5], 1):
            error_type = error.get('error_type', 'grammar')
            feedback.append(f"**{i}. {error_type}**")
            feedback.append(f"- ❌ {error.get('original', '')}")
            feedback.append(f"- ✅ {error.get('corrected', '')}")
            feedback.append(f"- 💡 {error.get('explanation', '')}")
            feedback.append("")

    jp_issues = eval_result.get("japanese_english_issues", [])
    if jp_issues:
        feedback.append("### 🇯🇵→🌍 More Natural Expressions / より自然な表現")
        feedback.append("These aren't \"wrong,\" but here are more natural alternatives:")
        feedback.append("以下は「間違い」ではありませんが、より自然な表現があります：")
        feedback.append("")
        for issue in jp_issues[:5]:
            feedback.append(f"- ❌ **{issue.get('original', '')}**")
            feedback.append(f"  - ✅ {issue.get('improved', '')}")
            feedback.append(f"  - 💡 {issue.get('explanation', '')}")
            if issue.get('regional_note'):
                feedback.append(f"  - 🌍 {issue.get('regional_note', '')}")
            feedback.append("")

    vocab = eval_result.get("vocabulary_suggestions", [])
    if vocab and show_full:
        feedback.append("### 📚 Vocabulary Alternatives / 語彙のバリエーション")
        for v in vocab[:3]:
            alts = ", ".join(v.get("alternatives", []))
            feedback.append(f"- **{v.get('original', '')}** → {alts}")
            if v.get("note"):
                feedback.append(f"  - {v.get('note', '')}")
        feedback.append("")

    org_feedback = eval_result.get("organization_feedback")
    if org_feedback and show_full:
        feedback.append("### 📝 Organization / 構成について")
        feedback.append(org_feedback)
        feedback.append("")

    priorities = eval_result.get("priority_improvements", [])
    if priorities:
        feedback.append("### 🎯 Priority Improvements / 優先的に改善したい点")
        for i, p in enumerate(priorities, 1):
            feedback.append(f"{i}. {p}")
        feedback.append("")

    rewritten = eval_result.get("rewritten_sample")
    if rewritten and show_full:
        feedback.append("### ✨ Rewritten Example / 書き直し例")
        feedback.append(f"> {rewritten}")
        feedback.append("")
        feedback.append("*This is just one example. / これは一例です。あなたの表現も大切にしてください。*")
        feedback.append("")

    next_steps = eval_result.get("next_steps")
    if next_steps:
        feedback.append("### 📚 Next Steps / 次に意識すること")
        feedback.append(next_steps)
        feedback.append("")

    return "\n".join(feedback)


# ============================================================
# evaluate_translation / format_translation_feedback（変更なし）
# ============================================================

def evaluate_translation(japanese_text, english_text, level="B1",
                         course_id: str = None):
    """
    日本語→英語翻訳をチェック。
    course_idが指定された場合、extra_instructionをプロンプトに反映。
    """
    client = get_openai_client()
    word_count = len(english_text.split())

    ai_settings = _get_ai_settings(course_id)
    extra_instr = ai_settings.get("extra_instruction", "")
    extra_block = f"\n## 教員からの追加指示:\n{extra_instr}" if extra_instr else ""

    prompt = f"""You are an expert English writing instructor specializing in Japanese-to-English translation for Japanese university students.

## Task
A Japanese student wrote the following Japanese text and translated it into English.
Analyze the translation, identify direct translation issues, and suggest natural English alternatives.

## Original Japanese
{japanese_text}

## Student's English Translation
{english_text}

## Student Level: {level}
{extra_block}

## IMPORTANT: Provide bilingual feedback (English / 日本語)

## Output Format (JSON)

{{
    "scores": {{
        "overall": <0-100>,
        "accuracy": <0-100>,
        "naturalness": <0-100>,
        "grammar": <0-100>
    }},
    "overall_feedback": "<Bilingual feedback on the translation / 翻訳全体のフィードバック>",
    "direct_translation_issues": [
        {{
            "japanese_part": "<問題のある日本語部分>",
            "student_translation": "<学生の英訳（直訳）>",
            "problem": "<Why this is unnatural / なぜ不自然か>",
            "natural_english": "<Natural English expression / 自然な英語表現>",
            "explanation": "<Detailed explanation / 詳しい説明>"
        }}
    ],
    "good_translations": [
        {{
            "japanese_part": "<うまく訳せた日本語部分>",
            "student_translation": "<学生の英訳>",
            "comment": "<Why this works well / なぜこれが良いか>"
        }}
    ],
    "grammar_errors": [
        {{
            "original": "<誤り>",
            "corrected": "<修正>",
            "explanation": "<English / 日本語>"
        }}
    ],
    "cultural_notes": [
        {{
            "topic": "<文化的な違いがある点>",
            "explanation": "<How to handle this in English / 英語でどう表現するか>"
        }}
    ],
    "full_natural_version": "<The full text rewritten naturally in English>",
    "translation_tips": "<General tips for Japanese-to-English translation / 日英翻訳のコツ>"
}}
"""

    try:
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": (
                    "You are an expert in Japanese-to-English translation instruction. "
                    "Provide bilingual feedback. Always respond in valid JSON."
                )},
                {"role": "user", "content": prompt}
            ],
            temperature=0.3,
            response_format={"type": "json_object"}
        )
        result = json.loads(response.choices[0].message.content)
        result["success"] = True
        result["word_count"] = word_count
        return result

    except Exception as e:
        return {"success": False, "error": str(e)}


def format_translation_feedback(eval_result):
    """翻訳評価結果をMarkdown形式でフォーマット"""
    if not eval_result.get("success"):
        return f"⚠️ Error / エラー: {eval_result.get('error', 'Unknown error')}"

    feedback = []

    if eval_result.get("overall_feedback"):
        feedback.append("### 💬 Overall Feedback / 総合フィードバック")
        feedback.append(eval_result.get("overall_feedback"))
        feedback.append("")

    good = eval_result.get("good_translations", [])
    if good:
        feedback.append("### ✅ Well Translated / うまく訳せた部分")
        for g in good:
            feedback.append(f"**日本語:** {g.get('japanese_part', '')}")
            feedback.append(f"**Your translation:** {g.get('student_translation', '')}")
            feedback.append(f"👍 {g.get('comment', '')}")
            feedback.append("")

    issues = eval_result.get("direct_translation_issues", [])
    if issues:
        feedback.append("### ⚠️ Direct Translation Issues / 直訳の問題点")
        feedback.append("")
        feedback.append("| 日本語 | Your Translation | Natural English |")
        feedback.append("|--------|-----------------|-----------------|")
        for issue in issues:
            jp = issue.get('japanese_part', '')
            student = issue.get('student_translation', '')
            natural = issue.get('natural_english', '')
            feedback.append(f"| {jp} | ❌ {student} | ✅ {natural} |")
        feedback.append("")
        feedback.append("**Details / 詳細:**")
        for i, issue in enumerate(issues, 1):
            feedback.append(f"")
            feedback.append(f"**{i}. {issue.get('japanese_part', '')}**")
            feedback.append(f"- ❌ {issue.get('student_translation', '')}")
            feedback.append(f"- ✅ {issue.get('natural_english', '')}")
            feedback.append(f"- 💡 {issue.get('explanation', '')}")
        feedback.append("")

    grammar = eval_result.get("grammar_errors", [])
    if grammar:
        feedback.append("### ✏️ Grammar Errors / 文法エラー")
        for g in grammar:
            feedback.append(f"- ❌ {g.get('original', '')} → ✅ {g.get('corrected', '')}")
            feedback.append(f"  - {g.get('explanation', '')}")
        feedback.append("")

    cultural = eval_result.get("cultural_notes", [])
    if cultural:
        feedback.append("### 🌍 Cultural Notes / 文化的な違い")
        for c in cultural:
            feedback.append(f"**{c.get('topic', '')}**")
            feedback.append(f"{c.get('explanation', '')}")
            feedback.append("")

    natural_full = eval_result.get("full_natural_version")
    if natural_full:
        feedback.append("### ✨ Natural English Version / 自然な英語版")
        feedback.append(f"> {natural_full}")
        feedback.append("")
        feedback.append("*Compare with your version! / あなたの訳と比べてみてください！*")
        feedback.append("")

    tips = eval_result.get("translation_tips")
    if tips:
        feedback.append("### 📚 Translation Tips / 翻訳のコツ")
        feedback.append(tips)
        feedback.append("")

    return "\n".join(feedback)
