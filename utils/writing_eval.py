import streamlit as st
from openai import OpenAI
import json

def get_openai_client():
    return OpenAI(api_key=st.secrets["openai"]["api_key"])


def evaluate_writing(text, task_type="general", level="B1", is_practice=False):
    """
    ライティングを評価（日英バイリンガルフィードバック）
    """
    
    client = get_openai_client()
    
    model = "gpt-4o-mini" if is_practice else "gpt-4o"
    
    word_count = len(text.split())
    
    prompt = f"""You are an expert English writing instructor specializing in Japanese EFL learners.

## Task
Evaluate the following English writing by a Japanese university student (Level: {level}).

## Student's Writing
{text}

## Word Count: {word_count}

## Task Type: {task_type}

## IMPORTANT: Bilingual Feedback
Provide all feedback in BOTH English and Japanese. Format: "English explanation / 日本語の説明"
This helps students learn while ensuring comprehension.

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
    "feedback": "<Bilingual feedback: English first, then Japanese. 2-3 sentences each>",
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
            "regional_note": "<World Englishes note if applicable / 地域差の補足>"
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
        "<Good point in English / 良い点（日本語）>",
        "<Another good point / もう一つの良い点>"
    ],
    "priority_improvements": [
        "<Priority 1 in English / 優先改善点1（日本語）>",
        "<Priority 2 / 優先改善点2>"
    ],
    "rewritten_sample": "<Naturally rewritten version>",
    "next_steps": "<What to focus on next (English) / 次に意識すること（日本語）>"
}}

## Guidelines
1. Be encouraging while specific about errors
2. Focus on Japanese L1 transfer issues
3. Respect World Englishes - note regional variations
4. For practice mode, focus on top 3-5 errors
5. Prioritize intelligibility over native-like perfection
6. ALL explanations must be bilingual (English / 日本語)
"""

    try:
        response = client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": "You are an expert English writing instructor. Provide bilingual (English/Japanese) feedback. Always respond in valid JSON format."},
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
        return {
            "success": False,
            "error": str(e)
        }


def format_writing_feedback(eval_result, show_full=True):
    """評価結果をMarkdown形式でフォーマット"""
    
    if not eval_result.get("success"):
        return f"⚠️ Evaluation Error / 評価エラー: {eval_result.get('error', 'Unknown error / 不明なエラー')}"
    
    feedback = []
    
    # 良かった点
    good_points = eval_result.get("good_points", [])
    if good_points:
        feedback.append("### ✅ Good Points / 良かった点")
        for point in good_points:
            feedback.append(f"- {point}")
        feedback.append("")
    
    # 総合フィードバック
    if eval_result.get("feedback"):
        feedback.append("### 💬 Feedback / フィードバック")
        feedback.append(eval_result.get("feedback"))
        feedback.append("")
    
    # 文法エラー
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
    
    # 日本語直訳・不自然な表現
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
    
    # 語彙の提案
    vocab = eval_result.get("vocabulary_suggestions", [])
    if vocab and show_full:
        feedback.append("### 📚 Vocabulary Alternatives / 語彙のバリエーション")
        for v in vocab[:3]:
            alts = ", ".join(v.get("alternatives", []))
            feedback.append(f"- **{v.get('original', '')}** → {alts}")
            if v.get("note"):
                feedback.append(f"  - {v.get('note', '')}")
        feedback.append("")
    
    # 構成のフィードバック
    org_feedback = eval_result.get("organization_feedback")
    if org_feedback and show_full:
        feedback.append("### 📝 Organization / 構成について")
        feedback.append(org_feedback)
        feedback.append("")
    
    # 優先改善点
    priorities = eval_result.get("priority_improvements", [])
    if priorities:
        feedback.append("### 🎯 Priority Improvements / 優先的に改善したい点")
        for i, p in enumerate(priorities, 1):
            feedback.append(f"{i}. {p}")
        feedback.append("")
    
    # 書き直し例
    rewritten = eval_result.get("rewritten_sample")
    if rewritten and show_full:
        feedback.append("### ✨ Rewritten Example / 書き直し例")
        feedback.append(f"> {rewritten}")
        feedback.append("")
        feedback.append("*This is just one example. Your expression is also valuable! / これは一例です。あなたの表現も大切にしてください。*")
        feedback.append("")
    
    # 次のステップ
    next_steps = eval_result.get("next_steps")
    if next_steps:
        feedback.append("### 📚 Next Steps / 次に意識すること")
        feedback.append(next_steps)
        feedback.append("")
    
    return "\n".join(feedback)


def evaluate_translation(japanese_text, english_text, level="B1"):
    """
    日本語→英語翻訳をチェック
    直訳の問題点と自然な英語を対比表示
    """
    
    client = get_openai_client()
    
    word_count = len(english_text.split())
    
    prompt = f"""You are an expert English writing instructor specializing in Japanese-to-English translation for Japanese university students.

## Task
A Japanese student wrote the following Japanese text and translated it into English.
Analyze the translation, identify direct translation issues, and suggest natural English alternatives.

## Original Japanese
{japanese_text}

## Student's English Translation
{english_text}

## Student Level: {level}

## IMPORTANT: Provide bilingual feedback (English / 日本語)

## Output Format (JSON)

{{
    "scores": {{
        "overall": <0-100: 総合評価>,
        "accuracy": <0-100: 意味の正確さ>,
        "naturalness": <0-100: 英語としての自然さ>,
        "grammar": <0-100: 文法の正確さ>
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

## Focus Areas
1. Japanese sentence structures that don't work in English (e.g., topic-comment vs subject-verb)
2. Expressions unique to Japanese that need adaptation (e.g., honorifics, humble forms)
3. Word-for-word translations that sound awkward
4. Missing subjects or articles
5. Cultural concepts that need explanation or adaptation
6. Praise good translation choices to reinforce learning
"""

    try:
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": "You are an expert in Japanese-to-English translation instruction. Provide bilingual feedback. Always respond in valid JSON."},
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
        return {
            "success": False,
            "error": str(e)
        }


def format_translation_feedback(eval_result):
    """翻訳評価結果をMarkdown形式でフォーマット"""
    
    if not eval_result.get("success"):
        return f"⚠️ Error / エラー: {eval_result.get('error', 'Unknown error')}"
    
    feedback = []
    scores = eval_result.get("scores", {})
    
    # 総合フィードバック
    if eval_result.get("overall_feedback"):
        feedback.append("### 💬 Overall Feedback / 総合フィードバック")
        feedback.append(eval_result.get("overall_feedback"))
        feedback.append("")
    
    # うまく訳せた部分
    good = eval_result.get("good_translations", [])
    if good:
        feedback.append("### ✅ Well Translated / うまく訳せた部分")
        for g in good:
            feedback.append(f"**日本語:** {g.get('japanese_part', '')}")
            feedback.append(f"**Your translation:** {g.get('student_translation', '')}")
            feedback.append(f"👍 {g.get('comment', '')}")
            feedback.append("")
    
    # 直訳の問題点（対比表示）
    issues = eval_result.get("direct_translation_issues", [])
    if issues:
        feedback.append("### ⚠️ Direct Translation Issues / 直訳の問題点")
        feedback.append("")
        feedback.append("| 日本語 | Your Translation | Problem | Natural English |")
        feedback.append("|--------|------------------|---------|-----------------|")
        for issue in issues:
            jp = issue.get('japanese_part', '')
            student = issue.get('student_translation', '')
            natural = issue.get('natural_english', '')
            feedback.append(f"| {jp} | ❌ {student} | | ✅ {natural} |")
        feedback.append("")
        
        # 詳細説明
        feedback.append("**Details / 詳細:**")
        for i, issue in enumerate(issues, 1):
            feedback.append(f"")
            feedback.append(f"**{i}. {issue.get('japanese_part', '')}**")
            feedback.append(f"- ❌ {issue.get('student_translation', '')}")
            feedback.append(f"- ✅ {issue.get('natural_english', '')}")
            feedback.append(f"- 💡 {issue.get('explanation', '')}")
        feedback.append("")
    
    # 文法エラー
    grammar = eval_result.get("grammar_errors", [])
    if grammar:
        feedback.append("### ✏️ Grammar Errors / 文法エラー")
        for g in grammar:
            feedback.append(f"- ❌ {g.get('original', '')} → ✅ {g.get('corrected', '')}")
            feedback.append(f"  - {g.get('explanation', '')}")
        feedback.append("")
    
    # 文化的なノート
    cultural = eval_result.get("cultural_notes", [])
    if cultural:
        feedback.append("### 🌍 Cultural Notes / 文化的な違い")
        for c in cultural:
            feedback.append(f"**{c.get('topic', '')}**")
            feedback.append(f"{c.get('explanation', '')}")
            feedback.append("")
    
    # 自然な英語版（全文）
    natural_full = eval_result.get("full_natural_version")
    if natural_full:
        feedback.append("### ✨ Natural English Version / 自然な英語版")
        feedback.append(f"> {natural_full}")
        feedback.append("")
        feedback.append("*Compare with your version to see the differences! / あなたの訳と比べてみてください！*")
        feedback.append("")
    
    # 翻訳のコツ
    tips = eval_result.get("translation_tips")
    if tips:
        feedback.append("### 📚 Translation Tips / 翻訳のコツ")
        feedback.append(tips)
        feedback.append("")
    
    return "\n".join(feedback)
