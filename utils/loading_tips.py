"""
Loading Tips — 待ち時間に語学豆知識を表示するユーティリティ
英語学習プラットフォーム用

v2: 全モジュール対応・cached_spinner追加・フォールバック強化
"""

import streamlit as st
import random
import time
from contextlib import contextmanager

# ============================================================
# 語学豆知識データベース（カテゴリ別）
# ============================================================

TIPS_PRONUNCIATION = [
    "💡 英語の \"th\" は舌を歯の間に挟んで発音します。日本語にない音なので意識的に練習しましょう！",
    "💡 \"L\" と \"R\" の違い：\"L\" は舌先を上の歯茎につけ、\"R\" は舌をどこにもつけません。",
    "💡 英語は「ストレスタイミング」の言語。強く読む音節の間隔がほぼ等しくなります。",
    "💡 \"can\" と \"can't\" の聞き分け：アメリカ英語では \"can't\" の母音が長く、\"æ\" の音になります。",
    "💡 英語の母音は日本語の5つ（あいうえお）に対し、約15種類あります。",
    "💡 \"comfortable\" は4音節ではなく \"COMF-ter-ble\" と3音節で発音されることが多いです。",
    "💡 リンキング（連結）：\"pick it up\" は \"pi-ki-tup\" のようにつながって聞こえます。",
    "💡 英語の \"v\" は上の前歯を下唇に軽く当てて振動させます。\"b\" とは違う音です。",
]

TIPS_VOCABULARY = [
    "📚 英語の語彙の約60%はラテン語・フランス語由来。学術的な単語ほどその傾向が強いです。",
    "📚 最頻出の100語で英語テキストの約50%をカバーできます。",
    "📚 \"nice\" は元々「無知な、愚かな」という意味でした。意味が変化した面白い例です。",
    "📚 接頭辞 \"un-\", \"re-\", \"in-\" を覚えると、語彙力が一気に広がります。",
    "📚 \"affect\"（動詞:影響する）と \"effect\"（名詞:効果）— 混同しやすい単語の代表格です。",
    "📚 英語で最も長い単語は \"pneumonoultramicroscopicsilicovolcanoconiosis\"（45文字）です！",
    "📚 \"set\" は英語辞書で最も多くの意味を持つ単語の一つ（約430の意味！）。",
    "📚 新しい単語は7回以上異なる文脈で出会うと記憶に定着しやすいと言われています。",
]

TIPS_GRAMMAR = [
    "📝 現在完了形（have + 過去分詞）は「過去から現在への接続」を表します。日本語にない時制感覚です。",
    "📝 冠詞 \"a/the\" の使い分け：初めて話題にする → a、お互い分かっている → the。",
    "📝 \"I have been to\" は経験、\"I have gone to\" は行ったきり戻っていない、という違いがあります。",
    "📝 英語の語順は基本 SVO（主語-動詞-目的語）。日本語の SOV とは逆です。",
    "📝 仮定法 \"If I were you...\" — were を使うのは「現実と違う仮定」を表すからです。",
    "📝 関係代名詞 \"who/which/that\" は文をつなげて情報を追加する便利な道具です。",
]

TIPS_LEARNING = [
    "🎯 言語学習には「インプット仮説」が重要：自分のレベルより少し上（i+1）の内容に触れましょう。",
    "🎯 シャドーイングは、リスニング・発音・スピーキングを同時に鍛える効果的な方法です。",
    "🎯 「エビングハウスの忘却曲線」によると、1日後に約66%忘れます。定期的な復習が鍵！",
    "🎯 1日15分の集中学習は、週1回2時間の学習より効果的と言われています。",
    "🎯 間違いを恐れないで！エラーは言語習得の自然なプロセスです（中間言語理論）。",
    "🎯 多読（Extensive Reading）は語彙力・読解力を自然に伸ばす研究実証済みの方法です。",
    "🎯 英語を英語で考える「英語脳」は、毎日少しずつ英語に触れることで作られます。",
    "🎯 アウトプット（話す・書く）は言語習得に不可欠。間違えながら使うことで力がつきます。",
]

TIPS_CULTURE = [
    "🌍 英語を公用語とする国は約60カ国。世界で最も広く使われている言語の一つです。",
    "🌍 アメリカ英語とイギリス英語の違い：elevator/lift, apartment/flat, cookie/biscuit。",
    "🌍 英語の \"How are you?\" は実は挨拶。詳しい体調報告は求められていません！",
    "🌍 ビジネス英語では \"Please\" より \"Could you...\" \"Would you mind...\" がより丁寧です。",
    "🌍 英語のジェスチャー：親指を上げる（👍）は日本でもおなじみですが、一部の国では失礼な意味も。",
    "🌍 英語では名前を呼ぶことが親しみの表現。会話で相手の名前を使ってみましょう。",
]

TIPS_TEST = [
    "📋 TOEIC: リスニングはPart 3, 4の先読みが高得点の鍵。問題文を先に読みましょう。",
    "📋 TOEFL: Independent Writing は「明確な主張 → 理由 → 具体例」の構成が基本です。",
    "📋 IELTS: Writing Task 2 は250語以上。パラグラフ構成を意識しましょう。",
    "📋 英検: 面接では \"Let me think...\" と言えば考える時間が自然にもらえます。",
    "📋 TOEICのスコアと英検の対応目安：600点≒2級、730点≒準1級、860点≒1級。",
    "📋 テスト対策の王道：過去問を解く → 間違い分析 → 弱点集中トレーニング。",
]

ALL_TIPS = (
    TIPS_PRONUNCIATION + TIPS_VOCABULARY + TIPS_GRAMMAR +
    TIPS_LEARNING + TIPS_CULTURE + TIPS_TEST
)

CONTEXT_TIPS = {
    "speaking":    TIPS_PRONUNCIATION + TIPS_LEARNING,
    "evaluation":  TIPS_PRONUNCIATION + TIPS_LEARNING + TIPS_TEST,
    "writing":     TIPS_GRAMMAR + TIPS_VOCABULARY,
    "vocabulary":  TIPS_VOCABULARY + TIPS_LEARNING,
    "reading":     TIPS_VOCABULARY + TIPS_GRAMMAR + TIPS_CULTURE,
    "listening":   TIPS_PRONUNCIATION + TIPS_CULTURE + TIPS_TEST,
    "test_prep":   TIPS_TEST + TIPS_LEARNING,
    "generating":  TIPS_LEARNING + TIPS_CULTURE,
    "tts":         TIPS_PRONUNCIATION + TIPS_CULTURE,
    "saving":      TIPS_LEARNING,
    "general":     ALL_TIPS,
}


def get_random_tip(context="general"):
    """コンテキストに合った豆知識をランダムに返す"""
    tips = CONTEXT_TIPS.get(context, ALL_TIPS)
    return random.choice(tips)


# ============================================================
# v2 追加: シンプルなキャッシュ対応スピナー
# ============================================================

@contextmanager  
def smart_spinner(message: str, context: str = "general"):
    """
    st.spinner の改良版。
    - 豆知識をメッセージ下に表示
    - 完了後に自動でクリア
    
    使い方（既存の st.spinner と同じ記法）:
        with smart_spinner("AI生成中...", context="writing"):
            result = call_openai(...)
    """
    tip = get_random_tip(context)
    placeholder = st.empty()
    placeholder.markdown(
        f"""
        <div style="
            background:#f0f4ff;
            border-left:4px solid #4a90d9;
            border-radius:8px;
            padding:14px 18px;
            margin:8px 0;
        ">
            <div style="font-weight:600;color:#333;margin-bottom:8px;">
                ⏳ {message}
            </div>
            <div style="font-size:13px;color:#555;line-height:1.6;">
                {tip}
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )
    try:
        yield
    finally:
        placeholder.empty()


@contextmanager
def loading_with_tips(message="処理中...", context="general"):
    """
    既存コードとの互換性を保ちつつ豆知識表示。
    speaking.py など既存の呼び出し元はそのまま動く。
    """
    tip = get_random_tip(context)
    loading_container = st.container()

    with loading_container:
        st.markdown(
            f"""
            <div style="
                background: linear-gradient(135deg, #667eea33 0%, #764ba233 100%);
                border-radius: 12px;
                padding: 20px;
                margin: 10px 0;
                border-left: 4px solid #667eea;
            ">
                <div style="display:flex;align-items:center;margin-bottom:12px;">
                    <span style="font-size:16px;font-weight:600;color:#333;">⏳ {message}</span>
                </div>
                <div style="
                    background:white;border-radius:8px;
                    padding:12px 16px;font-size:14px;color:#555;line-height:1.6;
                ">
                    {tip}
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    try:
        yield
    finally:
        loading_container.empty()


def show_progress_with_tips(steps, context="general"):
    """
    複数ステップの処理をプログレスバー＋豆知識で表示。
    
    使い方:
        results = show_progress_with_tips([
            ("音声分析中...", lambda: analyze_audio(data)),
            ("評価生成中...", lambda: generate_feedback(data)),
        ], context="evaluation")
    """
    tip = get_random_tip(context)
    progress_container = st.container()
    results = []

    with progress_container:
        st.markdown(
            f"""
            <div style="
                background:#f8f9fa;border-radius:8px;
                padding:12px 16px;margin-bottom:8px;
                font-size:14px;color:#555;
            ">{tip}</div>
            """,
            unsafe_allow_html=True,
        )
        progress_bar = st.progress(0)
        status_text = st.empty()

        for i, (step_msg, step_func) in enumerate(steps):
            progress_bar.progress(i / len(steps))
            status_text.markdown(f"⏳ **{step_msg}**")
            results.append(step_func())

        progress_bar.progress(1.0)
        status_text.markdown("✅ **完了しました！**")
        time.sleep(0.3)

    progress_container.empty()
    return results


def show_quick_tip(context="general"):
    """豆知識を1つ表示するだけのシンプルな関数"""
    tip = get_random_tip(context)
    st.markdown(
        f"""
        <div style="
            background:linear-gradient(135deg,#f5f7fa 0%,#c3cfe2 100%);
            border-radius:8px;padding:12px 16px;
            font-size:13px;color:#444;margin:8px 0;
        ">
            <strong>💡 Did you know?</strong><br>{tip}
        </div>
        """,
        unsafe_allow_html=True,
    )
