import streamlit as st
from openai import OpenAI

def get_openai_client():
    """OpenAIクライアントを取得"""
    return OpenAI(api_key=st.secrets["openai"]["api_key"])

def evaluate_language_use(text, context="speaking"):
    """
    GPT-4oで語彙・文法・内容・自然さを評価
    
    World Englishes（世界の多様な英語）を尊重しつつ、
    国際的なコミュニケーションで通じやすい表現を提案
    """
    
    client = get_openai_client()
    
    prompt = f"""あなたは World Englishes（世界の多様な英語）に精通した英語教育の専門家です。

## 重要な前提:
- 英語には「正しい」単一の形はありません
- アメリカ英語、イギリス英語、オーストラリア英語、インド英語、シンガポール英語、南アフリカ英語、フィリピン英語など、すべて正当な英語の変種です
- 日本で使われる英語表現も、国際的に通じるものであれば尊重されるべきです
- 評価の基準は「ネイティブらしさ」ではなく「国際的な通じやすさ（International Intelligibility）」です

## 分析対象テキスト:
{text}

## コンテキスト: {context}

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
            "note": "<この表現についての説明（日本語）>",
            "alternatives": [
                {{
                    "expression": "<代替表現>",
                    "region": "<主に使われる地域: American/British/Australian/International等>",
                    "formality": "<formal/neutral/informal>"
                }}
            ],
            "recommendation": "<学習者へのアドバイス（日本語）>"
        }}
    ],
    "grammar_feedback": [
        {{
            "original": "<原文の該当箇所>",
            "is_error": <true/false>,
            "is_regional_variant": <true/false>,
            "correction": "<修正が必要な場合の修正後>",
            "explanation": "<説明（日本語）>",
            "regions_where_acceptable": "<この文法が許容される地域があれば記載>"
        }}
    ],
    "vocabulary_analysis": {{
        "cefr_level": "<A1/A2/B1/B2/C1>",
        "strengths": "<語彙の良い点（日本語）>",
        "suggestions": "<より多様な語彙の提案（日本語）>",
        "academic_words_used": ["<使用されているアカデミックな語彙>"],
        "colloquial_words_used": ["<使用されている口語表現>"]
    }},
    "content_analysis": {{
        "clarity": "<内容の明確さについて（日本語）>",
        "organization": "<構成について（日本語）>",
        "strengths": "<良い点（日本語）>",
        "suggestions": "<改善提案（日本語）>"
    }},
    "cultural_notes": [
        {{
            "topic": "<文化的に注意が必要なトピック>",
            "note": "<説明（日本語）>"
        }}
    ],
    "overall_feedback": "<総合的なフィードバック（日本語、励ましを含めて3-4文）>",
    "enhanced_version": {{
        "text": "<国際的に通じやすい英語に調整した全文>",
        "changes_made": "<どのような変更を加えたかの説明（日本語）>"
    }}
}}

## 判断基準:

### "acceptable"（そのままでOK）:
- 国際的に広く通じる表現
- 特定の地域で一般的だが、他の地域でも理解される表現

### "regional"（地域限定だが問題なし）:
- 特定の英語圏で使われる表現
- 例: "flat"（英）vs "apartment"（米）— どちらも正しい
- 学習者には両方の存在を伝える

### "suggest_alternative"（代替を提案）:
- 文法的には正しいが、国際的に通じにくい可能性がある表現
- ただし「間違い」とは言わず、「より広く通じる表現もある」という形で提案

## 特に注意すべき表現（日本の英語教育で教わるが、実際の使用頻度が低いもの）:

1. "My hobby is ~" 
   - 間違いではないが、カジュアルな会話では "I enjoy ~ing" / "I'm into ~" / "I like to ~" がより自然
   - ただしフォーマルな自己紹介では使われることもある

2. "I belong to ~ university"
   - 日本語の「〜に所属している」の直訳
   - "I'm a student at ~" / "I study at ~" / "I attend ~" が一般的

3. "I entered the university"
   - "I started university" / "I enrolled at ~" / "I began studying at ~"

4. "Please teach me"
   - 文脈による。"Could you show me?" / "Could you help me understand?" / "I'd like to learn about ~"

5. "How do you think?"
   - "What do you think?" が正しい（howは方法を聞く時）

6. "almost all Japanese people" vs "most Japanese people"
   - "most" の方が自然な場合が多い

## 注意:
- 「間違い」という言葉は極力避け、「より広く通じる表現」「国際的な場面では」という言い方をする
- 学習者の努力を認め、励ましを含める
- 日本人としてのアイデンティティを否定しない（日本語アクセントは問題ではない）
"""

    try:
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": "You are an expert in World Englishes and English language education, specializing in helping Japanese EFL learners communicate effectively in international contexts. Always respond in valid JSON format. Be encouraging while providing specific, actionable feedback."},
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
        return {
            "success": False,
            "error": str(e)
        }


def format_gpt_feedback(eval_result):
    """GPT評価結果をMarkdown形式でフォーマット"""
    
    if not eval_result.get("success"):
        return f"⚠️ 言語評価エラー: {eval_result.get('error', '不明なエラー')}"
    
    feedback = []
    
    scores = eval_result.get("scores", {})
    
    # === スコアサマリー ===
    feedback.append("## 📝 言語使用の評価")
    feedback.append("")
    feedback.append("| 項目 | スコア | 説明 |")
    feedback.append("|------|--------|------|")
    feedback.append(f"| 語彙 | {scores.get('vocabulary', 0)}/100 | 語彙の適切さ・多様性 |")
    feedback.append(f"| 文法 | {scores.get('grammar', 0)}/100 | 文法の正確さ |")
    feedback.append(f"| 内容 | {scores.get('content', 0)}/100 | 内容の充実度・論理性 |")
    feedback.append(f"| 通じやすさ | {scores.get('intelligibility', 0)}/100 | 国際的なコミュニケーションでの通じやすさ |")
    feedback.append("")
    
    # === 表現フィードバック ===
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
            
            if status == "acceptable":
                icon = "✅"
                status_text = "問題なし"
            elif status == "regional":
                icon = "🌐"
                status_text = "地域差あり"
            else:
                icon = "💡"
                status_text = "代替表現あり"
            
            feedback.append(f"**{icon} 「{original}」** — {status_text}")
            feedback.append("")
            
            # 使用地域
            regions = expr.get("regions_used")
            if regions:
                feedback.append(f"   📍 使用地域: {regions}")
                feedback.append("")
            
            # 説明
            note = expr.get("note", "")
            if note:
                feedback.append(f"   {note}")
                feedback.append("")
            
            # 代替表現
            alternatives = expr.get("alternatives", [])
            if alternatives:
                feedback.append("   **代替表現:**")
                for alt in alternatives:
                    region = alt.get("region", "")
                    formality = alt.get("formality", "")
                    formality_ja = {"formal": "フォーマル", "neutral": "普通", "informal": "カジュアル"}.get(formality, formality)
                    feedback.append(f"   - \"{alt.get('expression', '')}\" ({region}, {formality_ja})")
                feedback.append("")
            
            # アドバイス
            rec = expr.get("recommendation", "")
            if rec:
                feedback.append(f"   💡 {rec}")
                feedback.append("")
    
    # === 文法フィードバック ===
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
    
    # === 語彙分析 ===
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
    
    # === 内容分析 ===
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
    
    # === 文化的注意点 ===
    cultural = eval_result.get("cultural_notes", [])
    if cultural:
        feedback.append("---")
        feedback.append("### 🎭 文化的な補足")
        feedback.append("")
        
        for note in cultural:
            feedback.append(f"- **{note.get('topic', '')}**: {note.get('note', '')}")
        feedback.append("")
    
    # === 改善版 ===
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
    
    # === 総合フィードバック ===
    overall = eval_result.get("overall_feedback", "")
    if overall:
        feedback.append("---")
        feedback.append("### 📋 総合フィードバック")
        feedback.append("")
        feedback.append(overall)
        feedback.append("")
    
    return "\n".join(feedback)
