"""
学習補助ページ — AIプロンプト集・AI活用法・語学アプリ紹介
Learning Resources — AI Prompts, AI Usage Guide, Language Learning Apps

将来的にはSupabaseのテーブルで管理し、教員がUIから編集可能にする予定。
"""

import streamlit as st
from utils.auth import get_current_user


# ============================================================
# データ定義（将来的にDB管理に移行予定）
# ============================================================

AI_PROMPTS = {
    "writing": {
        "icon": "✏️",
        "title": "英作文添削・文法チェック / Writing & Grammar",
        "prompts": [
            {
                "title": "英作文の添削",
                "description": "書いた英文を添削してもらう",
                "prompt": """Please proofread and correct the following English text. For each correction, explain:
1. What was wrong
2. The corrected version  
3. Why it's correct (grammar rule)

Please reply in both English and Japanese (日本語での説明もお願いします).

My text:
[ここにあなたの英文を貼り付けてください]""",
                "tip": "💡 レベルを指定すると、より適切なフィードバックが得られます（例: 'I am a CEFR B1 level student'）",
            },
            {
                "title": "文法解説リクエスト",
                "description": "特定の文法事項をわかりやすく説明してもらう",
                "prompt": """I'm a Japanese university student learning English. Please explain the following grammar point in a way that's easy to understand:

Topic: [文法項目を入力（例: present perfect vs past simple）]

Please include:
- Clear explanation in English and Japanese
- 3-5 example sentences with Japanese translations
- Common mistakes Japanese learners make
- A simple practice exercise""",
                "tip": "💡 自分が間違えた文を一緒に送ると、より具体的な説明がもらえます",
            },
            {
                "title": "パラフレーズ練習",
                "description": "同じ意味を違う表現で言い換える練習",
                "prompt": """Please help me practice paraphrasing. Give me a sentence, and I'll try to rewrite it in a different way. Then give me feedback on my paraphrase.

Level: [Beginner / Intermediate / Advanced]
Topic: [Academic / Business / Daily conversation]

Let's start! Please give me the first sentence.""",
                "tip": "💡 TOEFLやIELTSのWritingスキル向上にも直結する練習です",
            },
            {
                "title": "エッセイ構成チェック",
                "description": "エッセイの構成・論理展開をチェック",
                "prompt": """Please review the structure and logical flow of my essay. Don't correct grammar — focus only on:

1. Thesis statement clarity (主張は明確か)
2. Paragraph organization (段落構成)
3. Supporting evidence quality (根拠の質)
4. Transitions between paragraphs (段落間のつながり)
5. Conclusion effectiveness (結論の効果)

Please reply in both English and Japanese.

My essay:
[ここにエッセイを貼り付けてください]""",
                "tip": "💡 文法チェックと構成チェックを分けて依頼すると、より深いフィードバックが得られます",
            },
        ],
    },
    "conversation": {
        "icon": "💬",
        "title": "会話練習・ロールプレイ / Conversation & Role-play",
        "prompts": [
            {
                "title": "日常英会話練習",
                "description": "特定のシチュエーションで会話練習",
                "prompt": """Let's practice an English conversation! Please play the role described below and have a natural conversation with me.

Situation: [シチュエーションを選択:
- Ordering food at a restaurant
- Checking in at a hotel
- Asking for directions
- Making small talk at a party
- Shopping at a store]

Rules:
- Keep your responses natural and conversational
- If I make a grammar mistake, continue the conversation naturally, then point out the error at the end
- Use vocabulary appropriate for an intermediate English learner
- After every 5 exchanges, give me a brief feedback summary in Japanese

Let's begin! You start the conversation.""",
                "tip": "💡 同じシチュエーションを3回繰り返すと、表現が定着しやすくなります",
            },
            {
                "title": "ビジネス英語ロールプレイ",
                "description": "ビジネスシーンでの英語練習",
                "prompt": """Let's do a business English role-play.

Scenario: [ビジネスシーンを選択:
- Job interview (面接)
- Business meeting (会議)
- Client presentation (プレゼン)
- Negotiation (交渉)
- Email discussion (メールのやり取り)]

My role: [あなたの役割]
Your role: [AIの役割]

Please use professional but natural English. After the role-play, give me feedback on:
1. Professionalism of language
2. Key phrases I could have used
3. Cultural tips for this situation

Let's begin!""",
                "tip": "💡 就活やインターンの面接練習にも活用できます",
            },
            {
                "title": "ディスカッション練習",
                "description": "トピックについて議論する練習",
                "prompt": """Let's have an English discussion on a topic. Please:
1. Present a topic and give your opinion first
2. Ask me follow-up questions to keep the discussion going
3. Respectfully challenge my points to make me think deeper
4. After the discussion, evaluate my performance on: vocabulary range, argument structure, and fluency

Topic area: [トピックを選択:
- Technology and society
- Education and learning  
- Environment and sustainability
- Culture and travel
- Current events]

My English level: [Beginner / Intermediate / Advanced]

Please start with a thought-provoking question!""",
                "tip": "💡 英検の面接やIELTS Speakingの練習に最適です",
            },
            {
                "title": "発音・イントネーション練習",
                "description": "特定の発音パターンの練習文を生成",
                "prompt": """I want to practice English pronunciation. Please create a practice set for the following sound:

Target sound: [練習したい音を選択:
- /θ/ and /ð/ (th sounds)
- /r/ and /l/ 
- /v/ and /b/
- /æ/ (cat, hat)
- Word stress patterns
- Sentence intonation]

Please provide:
1. 5 minimal pairs (似た音の単語ペア)
2. 5 tongue twisters (早口言葉) at increasing difficulty
3. 3 natural sentences that contain the target sound
4. Tips for Japanese speakers specifically

日本語での発音のコツも含めてください。""",
                "tip": "💡 録音して聞き返すと、自分の発音の癖に気づけます",
            },
        ],
    },
    "vocabulary": {
        "icon": "📚",
        "title": "語彙学習・単語説明 / Vocabulary Building",
        "prompts": [
            {
                "title": "単語の深掘り学習",
                "description": "1つの単語を徹底的に理解する",
                "prompt": """Please give me a comprehensive breakdown of this English word:

Word: [単語を入力]

Please include:
1. Definition (in English and Japanese)
2. Pronunciation guide (発音記号 + カタカナ読み)
3. Part of speech and all possible forms (品詞と活用)
4. Etymology (語源 — where the word comes from)
5. 5 example sentences at different levels
6. Common collocations (よく一緒に使われる語)
7. Synonyms and antonyms (類義語・対義語)
8. Register (formal/informal/slang)
9. Common mistakes Japanese learners make with this word""",
                "tip": "💡 1日3語をこの方法で学ぶと、深い語彙力が身につきます",
            },
            {
                "title": "テーマ別語彙リスト作成",
                "description": "特定のテーマの重要語彙をまとめて学ぶ",
                "prompt": """Please create a vocabulary list for the following theme:

Theme: [テーマを選択:
- Academic English (大学の授業)
- Technology
- Environment  
- Health and Medicine
- Business and Economics
- Travel and Culture]

Level: [CEFR A2 / B1 / B2 / C1]

For each word, please provide:
- English word + Japanese translation
- Example sentence
- One useful collocation

Please give me 15-20 words organized from most useful to least useful.""",
                "tip": "💡 生成されたリストをAnkiやQuizletに入れると効率的に復習できます",
            },
            {
                "title": "語源から覚える英単語",
                "description": "ラテン語・ギリシャ語の語根から語彙を広げる",
                "prompt": """Please teach me English vocabulary through word roots (語源学習).

Root/Prefix/Suffix: [語根を入力、または「おすすめの語根を教えて」]

Please show me:
1. The meaning of this root (in English and Japanese)
2. Origin (Latin/Greek/etc.)
3. 8-10 common English words using this root
4. For each word: definition, example sentence, Japanese translation
5. A memory trick or visual image to remember the root

この方法で語彙が体系的に広がる仕組みを日本語でも説明してください。""",
                "tip": "💡 接頭辞20個 + 語根50個を覚えると、数千語の意味が推測できるようになります",
            },
        ],
    },
    "test_prep": {
        "icon": "📋",
        "title": "試験対策 / Test Preparation",
        "prompts": [
            {
                "title": "TOEIC対策 — リスニング練習",
                "description": "TOEICリスニングの練習問題を生成",
                "prompt": """Please create a TOEIC-style listening practice exercise.

Part: [パートを選択:
- Part 1 (写真描写)
- Part 2 (応答問題)
- Part 3 (会話問題)  
- Part 4 (説明文問題)]

Please provide:
1. The script (with natural business English)
2. 3 questions with 4 answer choices each
3. Correct answers with detailed explanations in Japanese
4. Key vocabulary and expressions from the script
5. Listening tips for this part type

場面設定はオフィス・会議・出張など、TOEICに頻出のシチュエーションでお願いします。""",
                "tip": "💡 スクリプトを音読すると、リスニング力とスピーキング力が同時に向上します",
            },
            {
                "title": "TOEFL iBT — Writing練習",
                "description": "TOEFL Writingの練習問題と添削",
                "prompt": """Please help me practice for the TOEFL iBT Writing section.

Task type: [タスクを選択:
- Independent Writing (自分の意見を述べる)
- Integrated Writing (リーディング+リスニング要約)]

For Independent Writing:
1. Give me a TOEFL-style question
2. After I write my response, evaluate it on the official TOEFL rubric (0-5):
   - Development, Organization, Language Use
3. Provide specific improvement suggestions
4. Show me a model paragraph for comparison

Target score: [20-25 / 25-28 / 28-30]

日本語でのアドバイスも含めてください。""",
                "tip": "💡 テンプレート構成（Intro→Body1→Body2→Conclusion）を先に身につけると効率的です",
            },
            {
                "title": "IELTS — Speaking練習",
                "description": "IELTS Speakingの模擬試験",
                "prompt": """Please conduct a mock IELTS Speaking test with me.

Please follow the official format:
- Part 1: Introduction and Interview (4-5 minutes, general questions)
- Part 2: Long Turn (1-2 minute speech on a cue card topic)
- Part 3: Discussion (4-5 minutes, abstract questions related to Part 2)

After each part, give me:
1. Band score estimate (1-9) with criteria breakdown
2. Vocabulary suggestions to improve my score
3. Grammar corrections
4. Fluency and pronunciation notes

Target band: [5.5 / 6.0 / 6.5 / 7.0+]

Let's begin with Part 1!""",
                "tip": "💡 Part 2は2分間話し続ける必要があります。メモを取る練習もしましょう",
            },
            {
                "title": "英検 — 面接対策",
                "description": "英検二次試験の模擬面接",
                "prompt": """Please conduct a mock Eiken (英検) interview for the following grade:

Grade: [級を選択: 3級 / 準2級 / 2級 / 準1級 / 1級]

Please follow the official Eiken interview format for that grade.
After the mock interview, provide:
1. Estimated score for each category
2. Model answers for questions I struggled with
3. Useful expressions I should memorize
4. Tips specific to this grade level

全体的なフィードバックは日本語でお願いします。""",
                "tip": "💡 'Let me think...' 'That's an interesting question...' などのフィラーを使って考える時間を稼ぎましょう",
            },
        ],
    },
    "general_language": {
        "icon": "🌍",
        "title": "語学学習全般 / General Language Learning",
        "prompts": [
            {
                "title": "任意の言語の会話練習",
                "description": "英語以外の言語でも会話練習可能",
                "prompt": """I want to practice [言語を入力: Chinese / Korean / French / Spanish / German / etc.].

My level: [Complete beginner / Elementary / Intermediate / Advanced]

Please:
1. Have a conversation with me in that language
2. Provide translations in Japanese after each message
3. Correct my mistakes gently
4. Teach me 3 new useful phrases each exchange
5. Gradually increase difficulty as I improve

Let's start with a simple greeting and self-introduction!""",
                "tip": "💡 このプロンプトは英語以外のどの言語にも応用できます",
            },
            {
                "title": "シャドーイング教材作成",
                "description": "自分のレベルに合ったシャドーイング素材を生成",
                "prompt": """Please create a shadowing practice text for English learners.

Level: [CEFR A2 / B1 / B2 / C1]
Topic: [お好みのトピック]
Length: [30 seconds / 1 minute / 2 minutes] worth of speech

Please provide:
1. The text (natural spoken English, not written style)
2. Difficult vocabulary with Japanese translations
3. Chunks to focus on (意味のまとまりごとの区切り)
4. Intonation and stress markers for key sentences
5. Step-by-step shadowing instructions in Japanese

テキストは自然な話し言葉で、読み上げ用に作成してください。""",
                "tip": "💡 ①聞くだけ → ②マンブリング → ③シャドーイング → ④オーバーラッピングの順で段階的に練習しましょう",
            },
            {
                "title": "学習計画の作成",
                "description": "AIに自分に合った学習計画を作ってもらう",
                "prompt": """Please help me create a personalized English study plan.

My current level: [CEFR A2 / B1 / B2 / C1]
My goal: [目標を入力:
- Pass TOEIC 700+ / 800+ / 900+
- Pass TOEFL iBT 80+ / 90+ / 100+
- Pass Eiken Grade [級]
- Improve conversational English
- Prepare for study abroad]

Available study time: [1日の学習可能時間] per day
Timeline: [目標達成までの期間]

Please create:
1. Weekly schedule (曜日ごとの学習内容)
2. Recommended resources (教材・アプリ)
3. Milestone checkpoints (中間目標)
4. Tips for staying motivated

日本語での解説もお願いします。""",
                "tip": "💡 1週間試してみて、うまくいかない部分があればAIに相談して計画を修正しましょう",
            },
        ],
    },
}

# AI活用法ガイド
AI_USAGE_GUIDE = [
    {
        "title": "🎯 効果的なプロンプトの書き方",
        "content": """
**基本原則 / Basic Principles:**

1. **具体的に指示する** — 「英語を教えて」ではなく「TOEIC Part 5の文法問題を5問作って」
2. **自分のレベルを伝える** — 「CEFR B1レベルです」「英検2級を持っています」
3. **出力形式を指定する** — 「表形式で」「日本語と英語の両方で」「例文を3つ含めて」
4. **役割を与える** — 「あなたは英語教師です」「IELTS試験官として振る舞って」
5. **フィードバックを求める** — 「私の文の間違いを指摘して理由を説明して」
""",
    },
    {
        "title": "⚡ 学習効率を上げるコツ",
        "content": """
- **同じトピックを深掘り**: 1つの話題で複数回会話すると語彙が定着する
- **間違いを恐れない**: AIは何度間違えても嫌な顔をしません
- **復習サイクルを作る**: AIに出してもらった単語リストをAnkiに入れて復習
- **実際の場面を想定**: 「来週のプレゼンで使う英語を練習したい」など具体的に
- **段階的に難易度UP**: 最初は簡単に → 慣れたら制約を追加（「5文以上で答えて」など）
""",
    },
    {
        "title": "⚠️ AI活用の注意点",
        "content": """
- **AIは完璧ではない**: 時々間違った情報を生成することがあります。特に固有名詞や統計データは確認しましょう
- **依存しすぎない**: AIはツールであり、最終的には自分の頭で考え、実際に人と話す経験が大切です
- **個人情報に注意**: 氏名・学籍番号などの個人情報をAIに送信しないでください
- **著作権に配慮**: AIが生成した文章をそのままレポートとして提出しないでください
- **複数のAIを試す**: ChatGPT, Claude, Geminiなどそれぞれ特徴が違います。比較して自分に合うものを見つけましょう
""",
    },
    {
        "title": "🔧 おすすめのAIツール",
        "content": """
| ツール | 特徴 | 無料プラン | URL |
|--------|------|-----------|-----|
| **ChatGPT** | 会話が自然、幅広い知識 | あり（GPT-4o mini） | chat.openai.com |
| **Claude** | 長文分析が得意、丁寧な回答 | あり（Sonnet） | claude.ai |
| **Gemini** | Google連携、マルチモーダル | あり | gemini.google.com |
| **DeepL Write** | 文章の添削・改善に特化 | あり（制限付き） | deepl.com/write |
| **Grammarly** | リアルタイム文法チェック | あり（基本機能） | grammarly.com |
""",
    },
]

# 語学系アプリ・サービス紹介
LANGUAGE_APPS = [
    {
        "category": "総合学習",
        "icon": "📱",
        "apps": [
            {
                "name": "Duolingo",
                "description": "ゲーム感覚で毎日少しずつ学べる。リマインダー機能で継続しやすい。",
                "good_for": "習慣づくり、基礎固め",
                "free": True,
                "url": "duolingo.com",
            },
            {
                "name": "Busuu",
                "description": "ネイティブスピーカーが添削してくれるコミュニティ機能あり。",
                "good_for": "ライティング添削、文化交流",
                "free": True,
                "url": "busuu.com",
            },
        ],
    },
    {
        "category": "発音・スピーキング",
        "icon": "🎙️",
        "apps": [
            {
                "name": "ELSA Speak",
                "description": "AIが発音を分析してリアルタイムでフィードバック。日本人の苦手な音に特化した練習も。",
                "good_for": "発音矯正、個別の音素練習",
                "free": True,
                "url": "elsaspeak.com",
            },
            {
                "name": "Speak",
                "description": "AI講師と音声会話練習。実際の会話に近い練習ができる。",
                "good_for": "スピーキング練習、会話の流暢さ",
                "free": False,
                "url": "speak.com",
            },
        ],
    },
    {
        "category": "語彙・暗記",
        "icon": "🧠",
        "apps": [
            {
                "name": "Anki",
                "description": "間隔反復（SRS）で効率的に暗記。自分でカードを作れる自由度の高さが魅力。",
                "good_for": "語彙、文法規則、何でも暗記",
                "free": True,
                "url": "apps.ankiweb.net",
                "note": "PC/Android無料、iOS有料",
            },
            {
                "name": "Quizlet",
                "description": "フラッシュカード作成・共有が簡単。他の学習者が作ったセットも利用可能。",
                "good_for": "語彙暗記、テスト準備",
                "free": True,
                "url": "quizlet.com",
            },
            {
                "name": "mikan",
                "description": "日本人向け英単語アプリ。TOEIC/TOEFL/英検対応の単語帳が充実。",
                "good_for": "試験対策の英単語",
                "free": True,
                "url": "mikan.link",
            },
        ],
    },
    {
        "category": "リスニング・リーディング",
        "icon": "🎧",
        "apps": [
            {
                "name": "TED Talks",
                "description": "様々なトピックの英語プレゼン。字幕・スクリプト付きで学習に最適。",
                "good_for": "リスニング、アカデミック英語、知識拡大",
                "free": True,
                "url": "ted.com",
            },
            {
                "name": "NHK World",
                "description": "日本のニュースを英語で。背景知識があるから理解しやすい。",
                "good_for": "ニュースリスニング、時事英語",
                "free": True,
                "url": "www3.nhk.or.jp/nhkworld",
            },
            {
                "name": "Podcast — 6 Minute English (BBC)",
                "description": "BBCの短い英語学習ポッドキャスト。1エピソード6分で気軽に聞ける。",
                "good_for": "リスニング、イギリス英語",
                "free": True,
                "url": "bbc.co.uk/learningenglish",
            },
        ],
    },
    {
        "category": "テスト対策",
        "icon": "📝",
        "apps": [
            {
                "name": "abceed",
                "description": "TOEIC対策に特化。AI分析でスコア予測＆弱点分析。市販教材のデジタル版も利用可能。",
                "good_for": "TOEIC対策",
                "free": True,
                "url": "abceed.com",
                "note": "基本無料、プレミアムプランあり",
            },
            {
                "name": "スタディサプリENGLISH",
                "description": "リクルート提供のTOEIC/英会話対策。動画講義とAI学習を組み合わせ。",
                "good_for": "TOEIC対策、基礎英語",
                "free": False,
                "url": "eigosapuri.jp",
            },
        ],
    },
]


# ============================================================
# 表示関数
# ============================================================

def show():
    """学習補助ページのメイン表示"""
    user = get_current_user()
    if not user:
        st.warning("ログインしてください")
        return

    st.markdown("## 🚀 学習補助 / Learning Resources")
    st.caption("AIを活用した英語学習のヒントとリソース集")

    if st.button("← ホームに戻る"):
        st.session_state["current_view"] = (
            "teacher_home" if user["role"] == "teacher" else "student_home"
        )
        st.rerun()

    st.markdown("---")

    # タブ構成
    tab1, tab2, tab3 = st.tabs([
        "🤖 AIプロンプト集",
        "📖 AI活用ガイド",
        "📱 語学アプリ・サービス紹介",
    ])

    with tab1:
        show_ai_prompts()

    with tab2:
        show_ai_usage_guide()

    with tab3:
        show_language_apps()


def show_ai_prompts():
    """AIプロンプト集の表示（DB優先、fallback でハードコード）"""
    st.markdown("### 🤖 AIプロンプト集 / AI Prompt Collection")
    st.markdown("""
    以下のプロンプトをコピーして、ChatGPT・Claude・Geminiなどの生成AIに貼り付けて使ってください。
    `[ ]` の部分を自分の状況に合わせて変更するとより効果的です。
    """)

    # DB からプロンプトを取得（コースが選択されている場合）
    db_prompts = []
    course_id = st.session_state.get('selected_course_id')
    if course_id:
        try:
            from utils.database import get_learning_resources
            db_prompts = get_learning_resources(
                course_id=course_id, resource_type='prompt'
            )
        except Exception:
            db_prompts = []

    if db_prompts:
        # DB版プロンプト表示
        # カテゴリ定義
        cat_labels = {
            "writing": "✏️ 英作文添削・文法チェック / Writing & Grammar",
            "conversation": "💬 会話練習・ロールプレイ / Conversation & Role-play",
            "vocabulary": "📚 語彙学習・単語説明 / Vocabulary Building",
            "test_prep": "📋 試験対策 / Test Preparation",
            "general_language": "🌍 語学学習全般 / General Language Learning",
            "custom": "🔧 カスタム",
        }

        # カテゴリ別にグループ化
        by_cat = {}
        for r in db_prompts:
            cat = r.get("category", "custom")
            by_cat.setdefault(cat, []).append(r)

        # カテゴリフィルター
        categories = list(by_cat.keys())
        selected_cat = st.selectbox(
            "カテゴリを選択 / Select Category",
            options=["all"] + categories,
            format_func=lambda x: "📋 すべて表示" if x == "all"
                else cat_labels.get(x, f"🔧 {x}"),
        )

        cats_to_show = categories if selected_cat == "all" else [selected_cat]

        for cat_key in cats_to_show:
            items = by_cat.get(cat_key, [])
            cat_label = cat_labels.get(cat_key, f"🔧 {cat_key}")
            st.markdown(f"#### {cat_label}")

            for item in items:
                with st.expander(f"**{item['title']}** — {item.get('description', '')}"):
                    st.code(item.get("content", ""), language=None)
                    if item.get("tip"):
                        st.caption(item["tip"])
                    st.markdown(f"""
                    <div style="
                        background: #f0f7ff;
                        border-radius: 8px;
                        padding: 10px 14px;
                        font-size: 13px;
                        margin-top: 8px;
                        border-left: 3px solid #4A90D9;
                    ">
                        📋 <strong>使い方:</strong> 上のテキストをコピー → ChatGPT/Claude/Geminiに貼り付け → <code>[ ]</code> の部分を変更して送信
                    </div>
                    """, unsafe_allow_html=True)

            st.markdown("---")
    else:
        # Fallback: ハードコード版（DB未登録の場合）
        _show_ai_prompts_hardcoded()

def _show_ai_prompts_hardcoded():
    """ハードコード版AIプロンプト集の表示（DB未登録時のフォールバック）"""
    # カテゴリフィルター
    categories = list(AI_PROMPTS.keys())
    category_labels = {k: f"{v['icon']} {v['title']}" for k, v in AI_PROMPTS.items()}

    selected_cat = st.selectbox(
        "カテゴリを選択 / Select Category",
        options=["all"] + categories,
        format_func=lambda x: "📋 すべて表示" if x == "all" else category_labels[x],
    )

    # プロンプト表示
    cats_to_show = categories if selected_cat == "all" else [selected_cat]

    for cat_key in cats_to_show:
        cat_data = AI_PROMPTS[cat_key]
        st.markdown(f"#### {cat_data['icon']} {cat_data['title']}")

        for i, prompt_data in enumerate(cat_data["prompts"]):
            with st.expander(f"**{prompt_data['title']}** — {prompt_data['description']}"):
                # プロンプト本文
                st.code(prompt_data["prompt"], language=None)

                # コピーボタン（Streamlitではst.codeがコピー機能付き）
                st.caption(f"{prompt_data['tip']}")

                # 使い方ヒント
                st.markdown(f"""
                <div style="
                    background: #f0f7ff;
                    border-radius: 8px;
                    padding: 10px 14px;
                    font-size: 13px;
                    margin-top: 8px;
                    border-left: 3px solid #4A90D9;
                ">
                    📋 <strong>使い方:</strong> 上のテキストをコピー → ChatGPT/Claude/Geminiに貼り付け → <code>[ ]</code> の部分を変更して送信
                </div>
                """, unsafe_allow_html=True)

        st.markdown("---")


def show_ai_usage_guide():
    """AI活用法ガイドの表示"""
    st.markdown("### 📖 生成AIで語学学習する方法 / How to Learn Languages with AI")
    st.markdown("生成AI（ChatGPT、Claude、Geminiなど）を語学学習に効果的に使うためのガイドです。")
    st.markdown("")

    for section in AI_USAGE_GUIDE:
        with st.expander(f"**{section['title']}**", expanded=True):
            st.markdown(section["content"])

    # 追加のアドバイス
    st.markdown("---")
    st.markdown("#### 🎓 大学生向け活用シナリオ")

    col1, col2 = st.columns(2)

    with col1:
        st.markdown("""
        <div style="
            background: linear-gradient(135deg, #667eea22 0%, #764ba222 100%);
            border-radius: 12px;
            padding: 16px;
            margin: 8px 0;
        ">
            <h4 style="margin-top: 0;">📝 授業の予習・復習</h4>
            <ul style="font-size: 14px;">
                <li>教科書の英文をAIに解説してもらう</li>
                <li>講義で出てきた専門用語の例文を作成</li>
                <li>エッセイの下書きを添削してもらう</li>
            </ul>
        </div>
        """, unsafe_allow_html=True)

        st.markdown("""
        <div style="
            background: linear-gradient(135deg, #f5af1922 0%, #f1281822 100%);
            border-radius: 12px;
            padding: 16px;
            margin: 8px 0;
        ">
            <h4 style="margin-top: 0;">🏢 就活・キャリア準備</h4>
            <ul style="font-size: 14px;">
                <li>英語面接の模擬練習</li>
                <li>英文履歴書・CVの添削</li>
                <li>ビジネス英語メールの書き方を学ぶ</li>
            </ul>
        </div>
        """, unsafe_allow_html=True)

    with col2:
        st.markdown("""
        <div style="
            background: linear-gradient(135deg, #11998e22 0%, #38ef7d22 100%);
            border-radius: 12px;
            padding: 16px;
            margin: 8px 0;
        ">
            <h4 style="margin-top: 0;">📊 資格試験対策</h4>
            <ul style="font-size: 14px;">
                <li>TOEIC/TOEFL/IELTSの練習問題を無限生成</li>
                <li>英検の面接練習をAIと実施</li>
                <li>弱点分野の集中トレーニング</li>
            </ul>
        </div>
        """, unsafe_allow_html=True)

        st.markdown("""
        <div style="
            background: linear-gradient(135deg, #a18cd122 0%, #fbc2eb22 100%);
            border-radius: 12px;
            padding: 16px;
            margin: 8px 0;
        ">
            <h4 style="margin-top: 0;">🌏 留学・国際交流</h4>
            <ul style="font-size: 14px;">
                <li>留学先での生活英語をシミュレーション</li>
                <li>異文化理解のトピックでディスカッション</li>
                <li>英語以外の言語の基礎学習</li>
            </ul>
        </div>
        """, unsafe_allow_html=True)


def show_language_apps():
    """語学アプリ・サービス紹介の表示"""
    st.markdown("### 📱 語学アプリ・サービス紹介 / Language Learning Apps & Services")
    st.markdown("自主学習に役立つアプリやサービスを紹介します。このプラットフォームと組み合わせて使うと効果的です。")
    st.markdown("")

    st.info("💡 **ヒント**: 複数のアプリを使い分けるより、2-3個に絞って継続する方が効果的です。まずは1つ試してみましょう！")

    for category_data in LANGUAGE_APPS:
        st.markdown(f"#### {category_data['icon']} {category_data['category']}")

        cols = st.columns(min(len(category_data["apps"]), 3))

        for i, app in enumerate(category_data["apps"]):
            col_idx = i % len(cols)
            with cols[col_idx]:
                free_badge = "🆓 無料" if app.get("free") else "💰 有料"
                note = f"\n_{app['note']}_" if app.get("note") else ""

                st.markdown(f"""
                <div style="
                    background: white;
                    border: 1px solid #e0e0e0;
                    border-radius: 12px;
                    padding: 16px;
                    margin: 8px 0;
                    min-height: 200px;
                    box-shadow: 0 2px 4px rgba(0,0,0,0.05);
                ">
                    <h4 style="margin: 0 0 8px 0; color: #333;">{app['name']} <span style="font-size: 12px; background: {'#e8f5e9' if app.get('free') else '#fff3e0'}; padding: 2px 8px; border-radius: 10px;">{free_badge}</span></h4>
                    <p style="font-size: 13px; color: #555; margin-bottom: 8px;">{app['description']}</p>
                    <p style="font-size: 12px; color: #888; margin-bottom: 4px;">🎯 <strong>おすすめ:</strong> {app['good_for']}</p>
                    <p style="font-size: 12px; color: #4A90D9;">🔗 {app['url']}</p>
                    {f'<p style="font-size: 11px; color: #999;">{note}</p>' if note else ''}
                </div>
                """, unsafe_allow_html=True)

        st.markdown("---")

    # 免責事項
    st.caption("※ 上記のアプリ・サービスは参考情報として紹介しています。本プラットフォームとは無関係です。利用は各自の判断でお願いします。")
