import streamlit as st
from openai import OpenAI


def get_openai_client():
    """OpenAIクライアントを取得"""
    return OpenAI(api_key=st.secrets["openai"]["api_key"])


def _get_ai_settings(course_id: str) -> dict:
    """course_settingsからAIフィードバック設定を取得（失敗時はデフォルト）"""
    if not course_id:
        return {}
    try:
        from utils.database import get_course_settings
        s = get_course_settings(course_id) or {}
        return s.get("ai_feedback", {})
    except Exception:
        return {}


def _get_speaking_weights(course_id: str, task_type: str, assignment_id: str = None) -> dict:
    """スピーキング評価ウェイトを取得"""
    if not course_id:
        return {}
    try:
        from utils.database import get_course_settings
        s = get_course_settings(course_id) or {}

        # 課題個別設定を優先
        if assignment_id:
            rubric = s.get("assignment_rubrics", {}).get(assignment_id, {})
            if rubric.get("weights"):
                return rubric["weights"]

        sw = s.get("speaking_weights", {})
        return sw.get(task_type, {})
    except Exception:
        return {}


def _build_feedback_language_instruction(lang: str) -> str:
    if lang == "english":
        return "Provide all feedback in English only."
    elif lang == "bilingual":
        return "Provide all feedback in both English and Japanese. Format: English text / 日本語テキスト"
    else:  # japanese (default)
        return "フィードバックはすべて日本語で提供してください。"


def _build_feedback_detail_instruction(detail: str) -> str:
    if detail == "brief":
        return "フィードバックは各項目1〜2文で簡潔にまとめてください。"
    elif detail == "detailed":
        return "フィードバックは各項目について具体例を交えて詳しく説明してください。"
    else:  # standard
        return "フィードバックは各項目3〜5文程度で説明してください。"


def _build_speaking_priority_instruction(priority: str) -> str:
    if priority == "pronunciation_focus":
        return (
            "## 評価の重点方針: 発音重視\n"
            "発音の正確さ・明瞭さを最優先で評価してください。"
            "流暢さや文法よりも、個々の音・アクセント・イントネーションの改善点を具体的に指摘してください。"
        )
    elif priority == "fluency_focus":
        return (
            "## 評価の重点方針: 流暢さ重視\n"
            "即興での流暢さとコミュニケーションの継続性を最優先で評価してください。"
            "文法ミスや発音より、止まらず話し続けられているかを重視してください。"
        )
    elif priority == "communication_focus":
        return (
            "## 評価の重点方針: コミュニケーション重視\n"
            "意思疎通の成功と積極的なコミュニケーション意欲を最優先で評価してください。"
            "文法・発音のミスがあっても、伝わっていれば積極的に評価してください。"
        )
    else:  # balanced
        return (
            "## 評価の重点方針: バランス型\n"
            "発音・流暢さ・内容・コミュニケーション意欲をバランスよく評価してください。"
        )


def _build_weights_instruction(weights: dict) -> str:
    """ウェイト設定をプロンプトに変換"""
    if not weights:
        return ""
    label_map = {
        "pronunciation": "発音",
        "prosody": "プロソディー（イントネーション・リズム）",
        "fluency": "流暢さ",
        "accuracy": "正確さ",
        "content": "内容",
        "structure": "構成",
        "vocabulary": "語彙",
        "grammar": "文法",
        "communication": "コミュニケーション意欲",
    }
    lines = ["## 評価ウェイト（この配分でスコアに重み付けしてください）:"]
    for k, v in weights.items():
        label = label_map.get(k, k)
        lines.append(f"- {label}: {v}%")
    return "\n".join(lines)


# ============================================================
# Speaking評価（gpt_eval.py メイン関数）
# ============================================================

def evaluate_language_use(text, context="speaking",
                          course_id: str = None,
                          task_type: str = "monologue",
                          assignment_id: str = None):
    """
    GPT-4oで語彙・文法・内容・自然さを評価。
    course_idが指定された場合、course_settingsの設定をプロンプトに反映。

    引数:
        text          : 評価対象テキスト
        context       : "speaking" / "dialogue" / "read_aloud" など
        course_id     : コースID（設定反映に使用、Noneなら従来通り）
        task_type     : "read_aloud" / "monologue" / "dialogue"
        assignment_id : 課題ID（課題別設定を優先する場合）
    """
    client = get_openai_client()

    # ── 設定取得 ──────────────────────────────────────────
    ai_settings = _get_ai_settings(course_id)
    weights = _get_speaking_weights(course_id, task_type, assignment_id)

    sp_priority   = ai_settings.get("speaking_priority", "balanced")
    fb_lang       = ai_settings.get("feedback_language", "japanese")
    fb_detail     = ai_settings.get("feedback_detail", "standard")
    extra_instr   = ai_settings.get("extra_instruction", "")

    # ── プロンプト組み立て ─────────────────────────────────
    priority_block  = _build_speaking_priority_instruction(sp_priority)
    lang_block      = _build_feedback_language_instruction(fb_lang)
    detail_block    = _build_feedback_detail_instruction(fb_detail)
    weights_block   = _build_weights_instruction(weights)
    extra_block     = f"\n## 教員からの追加指示:\n{extra_instr}" if extra_instr else ""

    prompt = f"""あなたは World Englishes（世界の多様な英語）に精通した英語教育の専門家です。

## 重要な前提:
- 英語には「正しい」単一の形はありません
- 評価の基準は「ネイティブらしさ」ではなく「国際的な通じやすさ（International Intelligibility）」です
- 学習者の努力を認め、励ましを含める

{priority_block}
{weights_block}
{extra_block}

## フィードバック言語: {lang_block}
## フィードバック詳細度: {detail_block}

## 分析対象テキスト:
{text}

## コンテキスト: {context} / タスクタイプ: {task_type}

## 評価項目と出力形式（JSON形式で出力してください）:

{{
    "scores": {{
        "vocabulary": <0-100の整数: 語彙の適切さ・多様性>,
        "grammar": <0-100の整数: 文法の正確さ>,
        "content": <0-100の整数: 内容の充実度・論理性>,
        "intelligibility": <0-100の整数: 国際的な通じやすさ>
    }},
    "expression_feedback": [
        {{
            "original": "<原文の該当箇所>",
            "status": "<acceptable/regional/suggest_alternative>",
            "regions_used": "<この表現が使われる地域・文脈があれば記載。なければnull>",
            "note": "<この表現についての説明>",
            "alternatives": [
                {{
                    "expression": "<代替表現>",
                    "region": "<主に使われる地域: American/British/Australian/International等>",
                    "formality": "<formal/neutral/informal>"
                }}
            ],
            "recommendation": "<学習者へのアドバイス>"
        }}
    ],
    "grammar_feedback": [
        {{
            "original": "<原文の該当箇所>",
            "is_error": <true/false>,
            "is_regional_variant": <true/false>,
            "correction": "<修正が必要な場合の修正後>",
            "explanation": "<説明>",
            "regions_where_acceptable": "<この文法が許容される地域があれば記載>"
        }}
    ],
    "vocabulary_analysis": {{
        "cefr_level": "<A1/A2/B1/B2/C1>",
        "strengths": "<語彙の良い点>",
        "suggestions": "<より多様な語彙の提案>",
        "academic_words_used": ["<使用されているアカデミックな語彙>"],
        "colloquial_words_used": ["<使用されている口語表現>"]
    }},
    "content_analysis": {{
        "clarity": "<内容の明確さについて>",
        "organization": "<構成について>",
        "strengths": "<良い点>",
        "suggestions": "<改善提案>"
    }},
    "cultural_notes": [
        {{
            "topic": "<文化的に注意が必要なトピック>",
            "note": "<説明>"
        }}
    ],
    "overall_feedback": "<総合的なフィードバック（励ましを含めて3-4文）>",
    "enhanced_version": {{
        "text": "<国際的に通じやすい英語に調整した全文>",
        "changes_made": "<どのような変更を加えたかの説明>"
    }}
}}

## 判断基準:
- "acceptable": 国際的に広く通じる表現
- "regional": 特定地域で使われる表現（間違いではない）
- "suggest_alternative": より広く通じる表現が提案できるもの（「間違い」とは言わない）

## 注意:
- 「間違い」という言葉は極力避け、「より広く通じる表現」という言い方をする
- 学習者の努力を認め、励ましを含める
"""

    try:
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": (
                    "You are an expert in World Englishes and English language education, "
                    "specializing in helping Japanese EFL learners communicate effectively "
                    "in international contexts. Always respond in valid JSON format. "
                    "Be encouraging while providing specific, actionable feedback."
                )},
                {"role": "user", "content": prompt}
            ],
            temperature=0.3,
            response_format={"type": "json_object"}
        )

        import json
        result = json.loads(response.choices[0].message.content)
        result["success"] = True
        return result

    except Exception as e:
        return {"success": False, "error": str(e)}


# ============================================================
# format_gpt_feedback（変更なし・互換性維持）
# ============================================================

def format_gpt_feedback(eval_result):
    """GPT評価結果をMarkdown形式でフォーマット"""

    if not eval_result.get("success"):
        return f"⚠️ 言語評価エラー: {eval_result.get('error', '不明なエラー')}"

    feedback = []
    scores = eval_result.get("scores", {})

    feedback.append("## 📝 言語使用の評価")
    feedback.append("")
    feedback.append("| 項目 | スコア | 説明 |")
    feedback.append("|------|--------|------|")
    feedback.append(f"| 語彙 | {scores.get('vocabulary', 0)}/100 | 語彙の適切さ・多様性 |")
    feedback.append(f"| 文法 | {scores.get('grammar', 0)}/100 | 文法の正確さ |")
    feedback.append(f"| 内容 | {scores.get('content', 0)}/100 | 内容の充実度・論理性 |")
    feedback.append(f"| 通じやすさ | {scores.get('intelligibility', 0)}/100 | 国際的なコミュニケーションでの通じやすさ |")
    feedback.append("")

    expressions = eval_result.get("expression_feedback", [])
    if expressions:
        feedback.append("---")
        feedback.append("### 🌍 表現についてのフィードバック")
        feedback.append("")
        feedback.append("※ 英語には多様な変種があります。以下は「間違い」ではなく、国際的なコミュニケーションでの選択肢を示しています。")
        feedback.append("")
        for expr in expressions:
            original = expr.get("original", "")
            status = expr.get("status", "")
            icon = "✅" if status == "acceptable" else "🌐" if status == "regional" else "💡"
            status_text = {"acceptable": "問題なし", "regional": "地域差あり"}.get(status, "代替表現あり")
            feedback.append(f"**{icon} 「{original}」** — {status_text}")
            feedback.append("")
            regions = expr.get("regions_used")
            if regions:
                feedback.append(f"   📍 使用地域: {regions}")
                feedback.append("")
            note = expr.get("note", "")
            if note:
                feedback.append(f"   {note}")
                feedback.append("")
            alternatives = expr.get("alternatives", [])
            if alternatives:
                feedback.append("   **代替表現:**")
                for alt in alternatives:
                    region = alt.get("region", "")
                    formality = alt.get("formality", "")
                    formality_ja = {"formal": "フォーマル", "neutral": "普通", "informal": "カジュアル"}.get(formality, formality)
                    feedback.append(f"   - \"{alt.get('expression', '')}\" ({region}, {formality_ja})")
                feedback.append("")
            rec = expr.get("recommendation", "")
            if rec:
                feedback.append(f"   💡 {rec}")
                feedback.append("")

    grammar = eval_result.get("grammar_feedback", [])
    if grammar:
        errors = [g for g in grammar if g.get("is_error")]
        regional = [g for g in grammar if g.get("is_regional_variant") and not g.get("is_error")]
        if errors:
            feedback.append("---")
            feedback.append("### ✏️ 文法の修正点")
            feedback.append("")
            for g in errors:
                feedback.append(f"- ❌ {g.get('original', '')}")
                feedback.append(f"  → ✅ **{g.get('correction', '')}**")
                feedback.append(f"  - {g.get('explanation', '')}")
                feedback.append("")
        if regional:
            feedback.append("---")
            feedback.append("### 🌐 地域による文法の違い")
            feedback.append("")
            for g in regional:
                feedback.append(f"- 「{g.get('original', '')}」")
                feedback.append(f"  - {g.get('explanation', '')}")
                regions = g.get("regions_where_acceptable", "")
                if regions:
                    feedback.append(f"  - 許容される地域: {regions}")
                feedback.append("")

    vocab = eval_result.get("vocabulary_analysis", {})
    if vocab:
        feedback.append("---")
        feedback.append("### 📚 語彙分析")
        feedback.append("")
        feedback.append(f"**CEFRレベル: {vocab.get('cefr_level', 'N/A')}**")
        feedback.append("")
        if vocab.get("strengths"):
            feedback.append(f"✅ **良い点:** {vocab.get('strengths')}")
            feedback.append("")
        if vocab.get("suggestions"):
            feedback.append(f"💡 **提案:** {vocab.get('suggestions')}")
            feedback.append("")
        academic = vocab.get("academic_words_used", [])
        if academic:
            feedback.append(f"📖 使用されたアカデミックな語彙: {', '.join(academic)}")
            feedback.append("")

    content = eval_result.get("content_analysis", {})
    if content:
        feedback.append("---")
        feedback.append("### 💭 内容分析")
        feedback.append("")
        if content.get("strengths"):
            feedback.append(f"✅ **良い点:** {content.get('strengths')}")
            feedback.append("")
        if content.get("suggestions"):
            feedback.append(f"💡 **改善点:** {content.get('suggestions')}")
            feedback.append("")

    cultural = eval_result.get("cultural_notes", [])
    if cultural:
        feedback.append("---")
        feedback.append("### 🎭 文化的な補足")
        feedback.append("")
        for note in cultural:
            feedback.append(f"- **{note.get('topic', '')}**: {note.get('note', '')}")
        feedback.append("")

    enhanced = eval_result.get("enhanced_version", {})
    if enhanced and enhanced.get("text"):
        feedback.append("---")
        feedback.append("### ✨ 国際的に通じやすい表現例")
        feedback.append("")
        feedback.append(f"> {enhanced.get('text', '')}")
        feedback.append("")
        if enhanced.get("changes_made"):
            feedback.append(f"📝 変更点: {enhanced.get('changes_made')}")
            feedback.append("")
        feedback.append("※ これは一例です。あなたの個性や意図を優先してください。")
        feedback.append("")

    overall = eval_result.get("overall_feedback", "")
    if overall:
        feedback.append("---")
        feedback.append("### 📋 総合フィードバック")
        feedback.append("")
        feedback.append(overall)
        feedback.append("")

    return "\n".join(feedback)
