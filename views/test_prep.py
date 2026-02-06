import streamlit as st
from utils.auth import get_current_user, require_auth
from datetime import datetime, timedelta
import random
import json

# 対応している検定試験
TEST_TYPES = {
    "toefl_itp": {
        "name": "TOEFL ITP",
        "full_name": "TOEFL Institutional Testing Program",
        "max_score": 677,
        "sections": [
            {"key": "listening", "name": "Listening Comprehension", "max": 68, "time": 35, "questions": 50},
            {"key": "structure", "name": "Structure & Written Expression", "max": 68, "time": 25, "questions": 40},
            {"key": "reading", "name": "Reading Comprehension", "max": 67, "time": 55, "questions": 50},
        ],
        "score_levels": [
            {"min": 627, "level": "C1", "desc": "上級"},
            {"min": 543, "level": "B2", "desc": "中上級"},
            {"min": 460, "level": "B1", "desc": "中級"},
            {"min": 337, "level": "A2", "desc": "初中級"},
        ],
        "description": "北海道大学の英語IIで受験必須。アカデミック英語力を測定。"
    },
    "toeic": {
        "name": "TOEIC L&R",
        "full_name": "Test of English for International Communication",
        "max_score": 990,
        "sections": [
            {"key": "listening", "name": "Listening", "max": 495, "time": 45, "questions": 100},
            {"key": "reading", "name": "Reading", "max": 495, "time": 75, "questions": 100},
        ],
        "score_levels": [
            {"min": 945, "level": "C1", "desc": "上級"},
            {"min": 785, "level": "B2", "desc": "中上級"},
            {"min": 550, "level": "B1", "desc": "中級"},
            {"min": 225, "level": "A2", "desc": "初中級"},
        ],
        "description": "ビジネス英語力を測定。就職活動で広く活用される。"
    },
    "toefl_ibt": {
        "name": "TOEFL iBT",
        "full_name": "TOEFL Internet-based Test",
        "max_score": 120,
        "sections": [
            {"key": "reading", "name": "Reading", "max": 30, "time": 54, "questions": 30},
            {"key": "listening", "name": "Listening", "max": 30, "time": 41, "questions": 28},
            {"key": "speaking", "name": "Speaking", "max": 30, "time": 17, "questions": 4},
            {"key": "writing", "name": "Writing", "max": 30, "time": 50, "questions": 2},
        ],
        "score_levels": [
            {"min": 95, "level": "C1", "desc": "上級"},
            {"min": 72, "level": "B2", "desc": "中上級"},
            {"min": 42, "level": "B1", "desc": "中級"},
        ],
        "description": "海外大学留学に必要。4技能を総合的に測定。"
    },
    "ielts": {
        "name": "IELTS",
        "full_name": "International English Language Testing System",
        "max_score": 9.0,
        "sections": [
            {"key": "listening", "name": "Listening", "max": 9.0, "time": 30, "questions": 40},
            {"key": "reading", "name": "Reading", "max": 9.0, "time": 60, "questions": 40},
            {"key": "writing", "name": "Writing", "max": 9.0, "time": 60, "questions": 2},
            {"key": "speaking", "name": "Speaking", "max": 9.0, "time": 15, "questions": 3},
        ],
        "score_levels": [
            {"min": 7.0, "level": "C1", "desc": "上級"},
            {"min": 5.5, "level": "B2", "desc": "中上級"},
            {"min": 4.0, "level": "B1", "desc": "中級"},
        ],
        "description": "イギリス・オーストラリア留学に必要。バンドスコアで評価。"
    },
    "eiken": {
        "name": "英検",
        "full_name": "実用英語技能検定",
        "max_score": "1級",
        "sections": [
            {"key": "reading", "name": "リーディング", "max": "-", "time": "-", "questions": "-"},
            {"key": "listening", "name": "リスニング", "max": "-", "time": "-", "questions": "-"},
            {"key": "writing", "name": "ライティング", "max": "-", "time": "-", "questions": "-"},
            {"key": "speaking", "name": "スピーキング（二次）", "max": "-", "time": "-", "questions": "-"},
        ],
        "score_levels": [
            {"min": "1級", "level": "C1", "desc": "上級"},
            {"min": "準1級", "level": "B2", "desc": "中上級"},
            {"min": "2級", "level": "B1", "desc": "中級"},
            {"min": "準2級", "level": "A2", "desc": "初中級"},
        ],
        "description": "日本で最も普及している英語検定。級別の合否判定。"
    },
}

# AI問題生成用プロンプトテンプレート
PROMPT_TEMPLATES = {
    "toefl_itp": {
        "listening": """You are creating a TOEFL ITP Listening Comprehension practice question.

Create a short dialogue (2-4 exchanges) followed by a question and 4 answer choices (A-D).
The dialogue should be natural academic or campus conversation.
Difficulty level: {difficulty}

Format your response as JSON:
{{
    "dialogue": "Dialogue text here",
    "question": "Question text here",
    "choices": ["A) ...", "B) ...", "C) ...", "D) ..."],
    "correct": "A",
    "explanation": "Explanation in Japanese"
}}""",
        
        "structure": """You are creating a TOEFL ITP Structure & Written Expression practice question.

Create a sentence completion or error identification question.
Type: {question_type}
Difficulty level: {difficulty}

For sentence completion:
- Provide a sentence with a blank
- Provide 4 choices (A-D)

For error identification:
- Provide a sentence with 4 underlined parts (A-D)
- One part contains a grammatical error

Format your response as JSON:
{{
    "question_type": "{question_type}",
    "sentence": "Sentence text here",
    "choices": ["A) ...", "B) ...", "C) ...", "D) ..."],
    "correct": "A",
    "explanation": "Explanation in Japanese"
}}""",

        "reading": """You are creating a TOEFL ITP Reading Comprehension practice question.

Create an academic passage ({length} words) on the topic of {topic}, followed by {num_questions} questions.
Difficulty level: {difficulty}

Format your response as JSON:
{{
    "passage": "Passage text here",
    "questions": [
        {{
            "question": "Question text",
            "choices": ["A) ...", "B) ...", "C) ...", "D) ..."],
            "correct": "A",
            "explanation": "Explanation in Japanese"
        }}
    ]
}}"""
    },
    
    "toeic": {
        "listening": """You are creating a TOEIC Listening practice question.

Part type: {part_type}
Difficulty level: {difficulty}

Create a question appropriate for the specified part:
- Part 1: Photo description
- Part 2: Question-Response
- Part 3: Short conversation
- Part 4: Short talk

Format your response as JSON:
{{
    "part": {part_type},
    "audio_script": "What listeners would hear",
    "question": "Question if applicable",
    "choices": ["A) ...", "B) ...", "C) ...", "D) ..."],
    "correct": "A",
    "explanation": "Explanation in Japanese"
}}""",

        "reading": """You are creating a TOEIC Reading practice question.

Part type: {part_type}
Difficulty level: {difficulty}

Create a question appropriate for the specified part:
- Part 5: Incomplete sentences
- Part 6: Text completion
- Part 7: Reading comprehension

Format your response as JSON:
{{
    "part": {part_type},
    "text": "Text or sentence",
    "question": "Question if Part 7",
    "choices": ["A) ...", "B) ...", "C) ...", "D) ..."],
    "correct": "A",
    "explanation": "Explanation in Japanese"
}}"""
    }
}

# 問題タイプ別の設定
QUESTION_TYPES = {
    "toefl_itp": {
        "listening": [
            {"type": "short_conversation", "name": "短い会話", "desc": "2人の短い会話を聞いて答える"},
            {"type": "long_conversation", "name": "長い会話", "desc": "長めの会話を聞いて複数の質問に答える"},
            {"type": "lecture", "name": "講義", "desc": "アカデミックな講義を聞いて答える"},
        ],
        "structure": [
            {"type": "sentence_completion", "name": "空所補充", "desc": "文法的に正しい語句を選ぶ"},
            {"type": "error_identification", "name": "誤り指摘", "desc": "文中の誤りを見つける"},
        ],
        "reading": [
            {"type": "main_idea", "name": "主旨把握", "desc": "パッセージの主旨を問う"},
            {"type": "detail", "name": "詳細理解", "desc": "具体的な情報を問う"},
            {"type": "vocabulary", "name": "語彙", "desc": "文脈から単語の意味を推測する"},
            {"type": "inference", "name": "推論", "desc": "内容から推測して答える"},
        ]
    },
    "toeic": {
        "listening": [
            {"type": "1", "name": "Part 1: 写真描写", "desc": "写真を見て正しい描写を選ぶ"},
            {"type": "2", "name": "Part 2: 応答問題", "desc": "質問に対する適切な応答を選ぶ"},
            {"type": "3", "name": "Part 3: 会話問題", "desc": "会話を聞いて質問に答える"},
            {"type": "4", "name": "Part 4: 説明文問題", "desc": "説明文を聞いて質問に答える"},
        ],
        "reading": [
            {"type": "5", "name": "Part 5: 短文穴埋め", "desc": "空所に入る適切な語句を選ぶ"},
            {"type": "6", "name": "Part 6: 長文穴埋め", "desc": "文書の空所に入る語句を選ぶ"},
            {"type": "7", "name": "Part 7: 読解問題", "desc": "文書を読んで質問に答える"},
        ]
    }
}


@require_auth
def show():
    user = get_current_user()
    
    st.markdown("## 📝 検定試験対策")
    
    if st.button("← ホームに戻る"):
        st.session_state['current_view'] = 'teacher_home' if user['role'] == 'teacher' else 'student_home'
        st.rerun()
    
    st.markdown("---")
    
    # 初期化
    if 'test_prep_data' not in st.session_state:
        st.session_state.test_prep_data = {}
    if 'generated_questions' not in st.session_state:
        st.session_state.generated_questions = {}
    if 'question_bank' not in st.session_state:
        st.session_state.question_bank = {}
    
    user_key = user.get('email', user.get('name', 'default'))
    
    if user_key not in st.session_state.test_prep_data:
        st.session_state.test_prep_data[user_key] = {
            "selected_test": "toefl_itp",
            "target_score": None,
            "test_date": None,
            "practice_history": [],
            "mock_test_results": generate_demo_mock_results(),
        }
    
    user_data = st.session_state.test_prep_data[user_key]
    
    # 教員の場合
    if user['role'] == 'teacher':
        show_teacher_view()
        return
    
    # 試験選択
    selected_test = st.selectbox(
        "🎯 対策する試験を選択",
        list(TEST_TYPES.keys()),
        format_func=lambda x: f"{TEST_TYPES[x]['name']} - {TEST_TYPES[x]['description'][:30]}...",
        index=list(TEST_TYPES.keys()).index(user_data['selected_test'])
    )
    
    user_data['selected_test'] = selected_test
    test_info = TEST_TYPES[selected_test]
    
    st.markdown("---")
    
    # タブ
    tab1, tab2, tab3, tab4, tab5 = st.tabs([
        "📊 概要・目標",
        "🤖 AI練習問題",
        "📝 模擬テスト",
        "📈 スコア推移",
        "📅 学習プラン"
    ])
    
    with tab1:
        show_overview_tab(test_info, user_data)
    with tab2:
        show_ai_practice_tab(test_info, user_data, user_key)
    with tab3:
        show_mock_test_tab(test_info, user_data)
    with tab4:
        show_score_progress_tab(test_info, user_data)
    with tab5:
        show_study_plan_tab(test_info, user_data)


def show_teacher_view():
    """教員用ビュー"""
    
    st.markdown("### 👨‍🏫 検定試験対策（教員ビュー）")
    
    tab1, tab2, tab3, tab4 = st.tabs([
        "📊 クラス受験状況",
        "🤖 AI問題生成",
        "📚 問題バンク管理",
        "⚙️ 設定"
    ])
    
    with tab1:
        show_class_exam_status()
    
    with tab2:
        show_teacher_ai_generation()
    
    with tab3:
        show_question_bank_management()
    
    with tab4:
        show_teacher_settings()


def show_class_exam_status():
    """クラスの受験状況"""
    
    st.markdown("#### クラスの受験予定・結果")
    
    classes = st.session_state.get('teacher_classes', {})
    if not classes:
        st.info("クラスがまだ作成されていません")
        return
    
    selected_class = st.selectbox(
        "クラス",
        list(classes.keys()),
        format_func=lambda x: classes[x]['name']
    )
    
    st.markdown("---")
    
    # 受験予定者一覧（デモ）
    st.markdown("**TOEFL ITP 受験予定（2025/06/15）**")
    
    students = [
        {"name": "田中太郎", "target": 500, "current_est": 480, "practice": 45, "trend": "+15"},
        {"name": "鈴木花子", "target": 550, "current_est": 535, "practice": 62, "trend": "+22"},
        {"name": "佐藤一郎", "target": 480, "current_est": 455, "practice": 18, "trend": "+8"},
        {"name": "山田美咲", "target": 520, "current_est": 510, "practice": 55, "trend": "+18"},
    ]
    
    cols = st.columns([2, 1, 1, 1, 1])
    with cols[0]:
        st.markdown("**学生**")
    with cols[1]:
        st.markdown("**目標**")
    with cols[2]:
        st.markdown("**予測**")
    with cols[3]:
        st.markdown("**練習数**")
    with cols[4]:
        st.markdown("**伸び**")
    
    for s in students:
        cols = st.columns([2, 1, 1, 1, 1])
        with cols[0]:
            diff = s['target'] - s['current_est']
            if diff <= 0:
                st.markdown(f"✅ {s['name']}")
            elif diff <= 20:
                st.markdown(f"🟡 {s['name']}")
            else:
                st.markdown(f"🔴 {s['name']}")
        with cols[1]:
            st.caption(str(s['target']))
        with cols[2]:
            st.caption(str(s['current_est']))
        with cols[3]:
            st.caption(f"{s['practice']}回")
        with cols[4]:
            st.caption(s['trend'])


def show_teacher_ai_generation():
    """教員用AI問題生成"""
    
    st.markdown("#### 🤖 AI問題一括生成")
    st.caption("AIを使って練習問題を自動生成し、問題バンクに追加できます")
    
    col1, col2 = st.columns(2)
    
    with col1:
        test_type = st.selectbox(
            "試験タイプ",
            list(TEST_TYPES.keys()),
            format_func=lambda x: TEST_TYPES[x]['name'],
            key="teacher_test_type"
        )
    
    with col2:
        section = st.selectbox(
            "セクション",
            [s['key'] for s in TEST_TYPES[test_type]['sections']],
            format_func=lambda x: next(s['name'] for s in TEST_TYPES[test_type]['sections'] if s['key'] == x),
            key="teacher_section"
        )
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        difficulty = st.select_slider(
            "難易度",
            options=["易しい", "やや易しい", "標準", "やや難しい", "難しい"],
            value="標準",
            key="teacher_difficulty"
        )
    
    with col2:
        num_questions = st.number_input(
            "生成数",
            min_value=1,
            max_value=20,
            value=5,
            key="teacher_num"
        )
    
    with col3:
        if QUESTION_TYPES.get(test_type, {}).get(section):
            q_types = QUESTION_TYPES[test_type][section]
            selected_q_type = st.selectbox(
                "問題タイプ",
                [qt['type'] for qt in q_types],
                format_func=lambda x: next(qt['name'] for qt in q_types if qt['type'] == x),
                key="teacher_q_type"
            )
        else:
            selected_q_type = "general"
            st.caption("問題タイプ: 一般")
    
    st.markdown("---")
    
    # トピック指定（Reading用）
    if section == "reading":
        topic = st.text_input(
            "トピック（任意）",
            placeholder="例: climate change, technology, history...",
            key="teacher_topic"
        )
    
    if st.button("🤖 問題を生成", type="primary", key="teacher_generate"):
        with st.spinner(f"{num_questions}問を生成中..."):
            generated = generate_questions_batch(
                test_type, section, selected_q_type, difficulty, num_questions
            )
            
            if generated:
                # 問題バンクに追加
                bank_key = f"{test_type}_{section}"
                if bank_key not in st.session_state.question_bank:
                    st.session_state.question_bank[bank_key] = []
                
                for q in generated:
                    q['id'] = f"q_{datetime.now().timestamp()}_{random.randint(1000,9999)}"
                    q['created_at'] = datetime.now().strftime("%Y-%m-%d %H:%M")
                    q['status'] = 'pending'  # pending, approved, rejected
                    st.session_state.question_bank[bank_key].append(q)
                
                st.success(f"✅ {len(generated)}問を生成しました！問題バンクで確認・承認してください。")
    
    # 最近生成した問題のプレビュー
    bank_key = f"{test_type}_{section}"
    recent = st.session_state.question_bank.get(bank_key, [])[-3:]
    
    if recent:
        st.markdown("---")
        st.markdown("**最近生成した問題:**")
        for q in reversed(recent):
            with st.expander(f"📝 {q.get('question', q.get('sentence', ''))[:50]}..."):
                st.json(q)


def show_question_bank_management():
    """問題バンク管理"""
    
    st.markdown("#### 📚 問題バンク管理")
    
    col1, col2 = st.columns(2)
    
    with col1:
        test_filter = st.selectbox(
            "試験",
            ["all"] + list(TEST_TYPES.keys()),
            format_func=lambda x: "すべて" if x == "all" else TEST_TYPES[x]['name'],
            key="bank_test_filter"
        )
    
    with col2:
        status_filter = st.selectbox(
            "ステータス",
            ["all", "pending", "approved", "rejected"],
            format_func=lambda x: {
                "all": "すべて",
                "pending": "⏳ 確認待ち",
                "approved": "✅ 承認済み",
                "rejected": "❌ 却下"
            }[x],
            key="bank_status_filter"
        )
    
    st.markdown("---")
    
    # 問題一覧
    all_questions = []
    for bank_key, questions in st.session_state.question_bank.items():
        for q in questions:
            q['bank_key'] = bank_key
            all_questions.append(q)
    
    # フィルタ
    if test_filter != "all":
        all_questions = [q for q in all_questions if q['bank_key'].startswith(test_filter)]
    if status_filter != "all":
        all_questions = [q for q in all_questions if q.get('status') == status_filter]
    
    st.caption(f"{len(all_questions)}問")
    
    if not all_questions:
        st.info("問題がありません。AI問題生成タブで問題を作成してください。")
        return
    
    for q in all_questions:
        col1, col2, col3 = st.columns([4, 1, 1])
        
        with col1:
            question_text = q.get('question', q.get('sentence', ''))[:60]
            st.markdown(f"**{question_text}...**")
            st.caption(f"{q['bank_key']} | {q.get('created_at', '')}")
        
        with col2:
            status = q.get('status', 'pending')
            if status == 'approved':
                st.success("✅")
            elif status == 'rejected':
                st.error("❌")
            else:
                st.warning("⏳")
        
        with col3:
            with st.popover("操作"):
                if st.button("✅ 承認", key=f"approve_{q['id']}"):
                    q['status'] = 'approved'
                    st.rerun()
                if st.button("❌ 却下", key=f"reject_{q['id']}"):
                    q['status'] = 'rejected'
                    st.rerun()
                if st.button("✏️ 編集", key=f"edit_{q['id']}"):
                    st.session_state['editing_question'] = q
                if st.button("🗑️ 削除", key=f"delete_{q['id']}"):
                    bank_key = q['bank_key']
                    st.session_state.question_bank[bank_key] = [
                        x for x in st.session_state.question_bank[bank_key] if x['id'] != q['id']
                    ]
                    st.rerun()


def show_teacher_settings():
    """教員設定"""
    
    st.markdown("#### ⚙️ 設定")
    
    st.markdown("**有効な試験:**")
    
    for test_key, test_info in TEST_TYPES.items():
        enabled = st.checkbox(
            f"{test_info['name']}を有効化",
            value=test_key in ["toefl_itp", "toeic"],
            key=f"enable_{test_key}"
        )
    
    st.markdown("---")
    
    st.markdown("**AI生成設定:**")
    
    api_key = st.text_input(
        "Anthropic API Key（任意）",
        type="password",
        help="独自のAPIキーを使用する場合に入力"
    )
    
    st.caption("※ APIキーを入力しない場合はデモモードで動作します")


def show_overview_tab(test_info, user_data):
    """概要・目標タブ"""
    
    st.markdown(f"### {test_info['name']}")
    st.markdown(f"**{test_info['full_name']}**")
    st.caption(test_info['description'])
    
    st.markdown("---")
    
    # 試験構成
    st.markdown("#### 📋 試験構成")
    
    cols = st.columns(len(test_info['sections']))
    for i, section in enumerate(test_info['sections']):
        with cols[i]:
            st.markdown(f"**{section['name']}**")
            st.caption(f"⏱️ {section['time']}分")
            st.caption(f"📝 {section['questions']}問")
            st.caption(f"🎯 最高{section['max']}点")
    
    st.markdown("---")
    
    # 目標設定
    st.markdown("#### 🎯 目標設定")
    
    col1, col2 = st.columns(2)
    
    with col1:
        if test_info['name'] == "英検":
            target = st.selectbox("目標級", ["1級", "準1級", "2級", "準2級", "3級"], index=2)
        else:
            max_score = test_info['max_score']
            if isinstance(max_score, float):
                target = st.slider("目標スコア", 0.0, max_score, 6.5, 0.5)
            else:
                target = st.slider("目標スコア", 0, max_score, int(max_score * 0.7))
        
        user_data['target_score'] = target
    
    with col2:
        test_date = st.date_input("受験予定日", value=datetime.now().date() + timedelta(days=60))
        user_data['test_date'] = test_date
        
        days_left = (test_date - datetime.now().date()).days
        if days_left > 0:
            st.metric("試験まで", f"{days_left}日")
        else:
            st.warning("試験日を過ぎています")
    
    st.markdown("---")
    
    # スコアレベル目安
    st.markdown("#### 📊 スコアレベル目安")
    
    for level in test_info['score_levels']:
        col1, col2, col3 = st.columns([1, 1, 2])
        with col1:
            st.markdown(f"**{level['level']}**")
        with col2:
            st.markdown(f"{level['min']}+")
        with col3:
            st.caption(level['desc'])


def show_ai_practice_tab(test_info, user_data, user_key):
    """AI練習問題タブ"""
    
    st.markdown("### 🤖 AI練習問題")
    st.caption("AIが自動生成した練習問題で対策しましょう")
    
    test_type = user_data['selected_test']
    
    # セクション選択
    section = st.selectbox(
        "セクションを選択",
        [s['key'] for s in test_info['sections']],
        format_func=lambda x: next(s['name'] for s in test_info['sections'] if s['key'] == x)
    )
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        difficulty = st.select_slider(
            "難易度",
            options=["易しい", "やや易しい", "標準", "やや難しい", "難しい"],
            value="標準"
        )
    
    with col2:
        num_questions = st.selectbox("問題数", [5, 10, 15, 20], index=0)
    
    with col3:
        if QUESTION_TYPES.get(test_type, {}).get(section):
            q_types = QUESTION_TYPES[test_type][section]
            selected_q_type = st.selectbox(
                "問題タイプ",
                ["all"] + [qt['type'] for qt in q_types],
                format_func=lambda x: "ランダム" if x == "all" else next(qt['name'] for qt in q_types if qt['type'] == x)
            )
        else:
            selected_q_type = "all"
    
    st.markdown("---")
    
    # 練習開始
    if st.button("🎯 練習を開始", type="primary"):
        st.session_state['current_practice'] = {
            'test_type': test_type,
            'section': section,
            'difficulty': difficulty,
            'num_questions': num_questions,
            'question_type': selected_q_type,
            'questions': [],
            'current_index': 0,
            'answers': {},
            'started_at': datetime.now()
        }
        
        # 問題を生成
        with st.spinner("問題を生成中..."):
            questions = get_practice_questions(test_type, section, selected_q_type, difficulty, num_questions)
            st.session_state['current_practice']['questions'] = questions
        
        st.rerun()
    
    # 練習中の場合
    if 'current_practice' in st.session_state and st.session_state['current_practice']:
        practice = st.session_state['current_practice']
        
        if practice['questions']:
            show_practice_session(practice, user_key)
        else:
            st.error("問題の生成に失敗しました。もう一度お試しください。")
            if st.button("リセット"):
                st.session_state['current_practice'] = None
                st.rerun()
    
    st.markdown("---")
    
    # 練習履歴
    st.markdown("#### 📋 練習履歴")
    
    history = user_data.get('practice_history', [])
    
    if history:
        for h in history[:5]:
            col1, col2, col3, col4 = st.columns([2, 1, 1, 1])
            with col1:
                st.caption(h['date'])
            with col2:
                st.caption(h['section'])
            with col3:
                st.caption(f"{h['score']}%")
            with col4:
                st.caption(f"{h['time']}分")
    else:
        st.info("まだ練習履歴がありません")


def get_practice_questions(test_type, section, q_type, difficulty, num):
    """練習問題を取得（問題バンクまたはAI生成）"""
    
    bank_key = f"{test_type}_{section}"
    bank = st.session_state.question_bank.get(bank_key, [])
    
    # 承認済みの問題から取得
    approved = [q for q in bank if q.get('status') == 'approved']
    
    if len(approved) >= num:
        # 問題バンクから出題
        return random.sample(approved, num)
    else:
        # 不足分をAI生成（デモモード）
        generated = generate_questions_batch(test_type, section, q_type, difficulty, num)
        return generated


def generate_questions_batch(test_type, section, q_type, difficulty, num):
    """問題を一括生成（デモモード）"""
    
    questions = []
    
    # デモ用問題を生成
    for i in range(num):
        if section == "listening":
            q = generate_listening_question(test_type, q_type, difficulty)
        elif section == "structure":
            q = generate_structure_question(test_type, q_type, difficulty)
        elif section == "reading":
            q = generate_reading_question(test_type, q_type, difficulty)
        else:
            q = generate_general_question(test_type, section, difficulty)
        
        q['id'] = f"gen_{i}_{random.randint(1000, 9999)}"
        q['difficulty'] = difficulty
        questions.append(q)
    
    return questions


def generate_listening_question(test_type, q_type, difficulty):
    """リスニング練習問題生成（問題バンクから取得）"""
    try:
        from utils.test_question_bank import get_test_questions
        q = get_test_questions(test_type, "listening", difficulty, q_type)
        if q:
            return q
    except Exception:
        pass
    
    # フォールバック
    return {
        "dialogue": "W: Have you finished the assignment?\nM: Not yet. I need another day.",
        "question": "What does the man mean?",
        "choices": ["A) He finished it.", "B) He needs more time.", "C) He lost it.", "D) He forgot about it."],
        "correct": "B",
        "explanation": "男性はもう1日必要と言っているのでBが正解。",
    }


def generate_structure_question(test_type, q_type, difficulty):
    """文法問題生成（問題バンクから取得）"""
    try:
        from utils.test_question_bank import get_test_questions
        q = get_test_questions(test_type, "structure", difficulty, q_type)
        if q:
            return q
    except Exception:
        pass
    
    return {
        "question_type": "sentence_completion",
        "sentence": "The number of students ______ increased this year.",
        "choices": ["A) have", "B) has", "C) are", "D) were"],
        "correct": "B",
        "explanation": "The number of ~ は単数扱いなので has が正解。",
    }


    return random.choice(questions)


def generate_reading_question(test_type, q_type, difficulty):
    """読解問題生成（問題バンクから取得）"""
    try:
        from utils.test_question_bank import get_test_questions
        q = get_test_questions(test_type, "reading", difficulty, q_type)
        if q:
            return q
    except Exception:
        pass
    
    return {
        "question": "What is the passage mainly about?",
        "passage": "Scientists have long studied the effects of climate change on polar ecosystems.",
        "choices": ["A) Polar wildlife", "B) Climate change effects", "C) Ocean currents", "D) Ice formations"],
        "correct": "B",
        "explanation": "パッセージは気候変動が極地の生態系に与える影響について述べています。Bが正解。",
    }



def generate_general_question(test_type, section, difficulty):
    """汎用問題生成（問題バンクから取得）"""
    try:
        from utils.test_question_bank import get_test_questions
        q = get_test_questions(test_type, section, difficulty)
        if q:
            return q
    except Exception:
        pass
    
    return {
        "question": "Choose the best answer.",
        "sentence": "The meeting has been ______ until next week.",
        "choices": ["A) postponed", "B) postponing", "C) postpone", "D) to postpone"],
        "correct": "A",
        "explanation": "has been + 過去分詞で受動態。postponed が正解。",
    }



def show_practice_session(practice, user_key):
    """練習セッション表示"""
    
    questions = practice['questions']
    current_idx = practice['current_index']
    
    if current_idx >= len(questions):
        show_practice_results(practice, user_key)
        return
    
    q = questions[current_idx]
    
    # 進捗バー
    progress = (current_idx + 1) / len(questions)
    st.progress(progress)
    st.caption(f"問題 {current_idx + 1} / {len(questions)}")
    
    st.markdown("---")
    
    # パッセージがある場合
    if 'passage' in q:
        with st.expander("📖 パッセージを読む", expanded=True):
            st.markdown(q['passage'])
    
    # ダイアログがある場合（リスニング問題）
    if 'dialogue' in q:
        st.markdown("**🎧 リスニング問題 / Listening Question**")
        st.caption("まず音声を聞いてから、質問に答えてください。/ Listen first, then answer the question.")
        
        dialogue_text = q['dialogue']
        
        # 音声再生
        audio_col1, audio_col2 = st.columns([3, 1])
        with audio_col1:
            if st.button("🔊 音声を再生 / Play Audio", key=f"play_dialogue_{current_idx}", type="primary", use_container_width=True):
                with st.spinner("音声を生成中..."):
                    try:
                        from utils.tts_natural import generate_natural_audio
                        
                        # 話者を分けて自然に再生
                        lines = dialogue_text.strip().split("\n")
                        combined_audio = b""
                        
                        for line in lines:
                            line = line.strip()
                            if not line:
                                continue
                            
                            # 話者判定
                            if line.startswith("W:") or line.startswith("Woman:"):
                                voice = "アメリカ英語 (女性)"
                                speak_text = line.split(":", 1)[1].strip()
                            elif line.startswith("M:") or line.startswith("Man:"):
                                voice = "アメリカ英語 (男性)"
                                speak_text = line.split(":", 1)[1].strip()
                            else:
                                voice = "アメリカ英語 (女性)"
                                speak_text = line
                            
                            audio_part = generate_natural_audio(speak_text, voice, 0.9)
                            if audio_part:
                                combined_audio += audio_part
                        
                        if combined_audio:
                            import base64
                            b64 = base64.b64encode(combined_audio).decode()
                            st.markdown(f"""
                            <audio controls autoplay style="width:100%">
                                <source src="data:audio/mp3;base64,{b64}" type="audio/mp3">
                            </audio>
                            """, unsafe_allow_html=True)
                        else:
                            st.warning("音声生成に失敗しました。テキストで確認してください。")
                    except Exception as e:
                        st.warning(f"音声再生エラー: {e}。テキストで確認してください。")
        
        with audio_col2:
            speed_opt = st.selectbox("速度", [0.75, 0.85, 1.0], index=2, format_func=lambda x: f"{x}x", key=f"speed_dialogue_{current_idx}")
        
        # スクリプト表示（トグル）
        with st.expander("📝 スクリプトを見る / Show Script（※実際の試験では見られません）"):
            for line in dialogue_text.strip().split("\n"):
                line = line.strip()
                if line.startswith("W:") or line.startswith("Woman:"):
                    st.markdown(f"👩 **{line}**")
                elif line.startswith("M:") or line.startswith("Man:"):
                    st.markdown(f"👨 **{line}**")
                else:
                    st.markdown(line)
        
        st.markdown("---")
    
    # 文がある場合（Structure）
    if 'sentence' in q:
        st.markdown(f"**{q['sentence']}**")
        st.markdown("---")
    
    # 質問
    st.markdown(f"**{q.get('question', 'Choose the correct answer:')}**")
    
    # 選択肢
    answer_key = f"answer_{current_idx}"
    
    selected = st.radio(
        "選択してください",
        q['choices'],
        key=answer_key,
        index=None
    )
    
    col1, col2, col3 = st.columns([1, 1, 1])
    
    with col1:
        if current_idx > 0:
            if st.button("← 前の問題"):
                practice['current_index'] -= 1
                st.rerun()
    
    with col2:
        if st.button("回答を確認"):
            if selected:
                practice['answers'][current_idx] = selected[0]  # A, B, C, D
                
                # 正誤判定
                is_correct = selected[0] == q['correct']
                
                if is_correct:
                    st.success("✅ 正解！")
                else:
                    st.error(f"❌ 不正解。正解は {q['correct']} です。")
                
                st.info(f"**解説:** {q.get('explanation', '解説はありません')}")
    
    with col3:
        if st.button("次の問題 →"):
            if selected:
                practice['answers'][current_idx] = selected[0]
            practice['current_index'] += 1
            st.rerun()
    
    st.markdown("---")
    
    if st.button("練習を終了"):
        practice['current_index'] = len(questions)  # 結果画面へ
        st.rerun()


def show_practice_results(practice, user_key):
    """練習結果表示"""
    
    st.markdown("### 🎉 練習完了！")
    
    questions = practice['questions']
    answers = practice['answers']
    
    # スコア計算
    correct_count = 0
    for idx, q in enumerate(questions):
        if answers.get(idx) == q['correct']:
            correct_count += 1
    
    score = int(correct_count / len(questions) * 100)
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric("スコア", f"{score}%")
    with col2:
        st.metric("正解数", f"{correct_count}/{len(questions)}")
    with col3:
        elapsed = (datetime.now() - practice['started_at']).seconds // 60
        st.metric("所要時間", f"{elapsed}分")
    
    st.markdown("---")
    
    # 結果詳細
    st.markdown("#### 📋 結果詳細")
    
    for idx, q in enumerate(questions):
        user_answer = answers.get(idx, "-")
        is_correct = user_answer == q['correct']
        
        with st.expander(f"{'✅' if is_correct else '❌'} 問題 {idx + 1}"):
            if 'sentence' in q:
                st.markdown(f"**{q['sentence']}**")
            elif 'question' in q:
                st.markdown(f"**{q['question']}**")
            
            st.markdown(f"あなたの回答: **{user_answer}**")
            st.markdown(f"正解: **{q['correct']}**")
            st.info(q.get('explanation', ''))
    
    # 履歴に保存
    user_data = st.session_state.test_prep_data.get(user_key, {})
    if 'practice_history' not in user_data:
        user_data['practice_history'] = []
    
    user_data['practice_history'].insert(0, {
        'date': datetime.now().strftime("%Y-%m-%d %H:%M"),
        'section': practice['section'],
        'score': score,
        'time': elapsed,
        'num_questions': len(questions)
    })
    
    st.markdown("---")
    
    col1, col2 = st.columns(2)
    
    with col1:
        if st.button("🔄 もう一度練習"):
            st.session_state['current_practice'] = None
            st.rerun()
    
    with col2:
        if st.button("🏠 ホームに戻る"):
            st.session_state['current_practice'] = None
            st.session_state['current_view'] = 'student_home'
            st.rerun()


def show_mock_test_tab(test_info, user_data):
    """模擬テストタブ"""
    
    st.markdown("### 📝 模擬テスト")
    
    import random
    
    test_key = test_info.get('key', 'test')
    mock_state_key = f'mock_test_{test_key}'
    
    if mock_state_key not in st.session_state:
        st.session_state[mock_state_key] = {
            'started': False,
            'current_q': 0,
            'answers': {},
            'submitted': False,
            'score': 0,
        }
    
    mock = st.session_state[mock_state_key]
    
    # 模擬テスト問題（テスト別）
    sections_raw = test_info.get('sections', [{'name': 'Listening'}, {'name': 'Reading'}, {'name': 'Grammar'}])
    # sectionsがdictのリストの場合、名前を抽出
    if sections_raw and isinstance(sections_raw[0], dict):
        sections = [s.get('name', s.get('key', 'Section')) for s in sections_raw]
    else:
        sections = sections_raw
    
    mock_questions = []
    for section in sections:
        for i in range(5):
            q_num = len(mock_questions) + 1
            mock_questions.append({
                'id': q_num,
                'section': section,
                'question': f"[{section}] Question {i+1}: Choose the best answer to complete the sentence.",
                'sentence': [
                    "The project was _____ successful than we expected.",
                    "She has been working here _____ five years.",
                    "If I _____ more time, I would travel the world.",
                    "The report _____ by the committee last week.",
                    "He suggested that she _____ the meeting early.",
                ][i % 5],
                'options': [
                    ["A) more", "B) most", "C) much", "D) many"],
                    ["A) since", "B) for", "C) during", "D) while"],
                    ["A) have", "B) had", "C) having", "D) has"],
                    ["A) was reviewed", "B) reviewed", "C) is reviewing", "D) reviews"],
                    ["A) attends", "B) attend", "C) attending", "D) attended"],
                ][i % 5],
                'correct': [0, 1, 1, 0, 1][i % 5],
            })
    
    total_q = len(mock_questions)
    time_limit = total_q * 1  # 1分/問
    
    if not mock['started'] and not mock['submitted']:
        st.markdown(f"""
        **テスト情報:**
        - 問題数: {total_q}問
        - セクション: {', '.join(sections)}
        - 目安時間: {time_limit}分
        """)
        
        if st.button("🚀 模擬テスト開始", type="primary"):
            mock['started'] = True
            mock['current_q'] = 0
            mock['answers'] = {}
            mock['submitted'] = False
            st.rerun()
        return
    
    if mock['started'] and not mock['submitted']:
        # 進捗
        answered = len(mock['answers'])
        st.progress(answered / total_q)
        st.caption(f"回答済み: {answered}/{total_q}")
        
        # 問題表示
        idx = mock['current_q']
        q = mock_questions[idx]
        
        st.markdown(f"#### 問題 {q['id']} / {total_q}  [{q['section']}]")
        st.markdown(f"**{q['sentence']}**")
        
        selected = st.radio(
            "回答を選択",
            q['options'],
            key=f"mock_q_{q['id']}",
            index=mock['answers'].get(q['id'], None)
        )
        
        # 回答保存
        if selected:
            mock['answers'][q['id']] = q['options'].index(selected)
        
        # ナビゲーション
        col1, col2, col3 = st.columns(3)
        with col1:
            if idx > 0:
                if st.button("← 前の問題"):
                    mock['current_q'] = idx - 1
                    st.rerun()
        with col2:
            if idx < total_q - 1:
                if st.button("次の問題 →"):
                    mock['current_q'] = idx + 1
                    st.rerun()
        with col3:
            if len(mock['answers']) == total_q:
                if st.button("📤 提出する", type="primary"):
                    # 採点
                    score = 0
                    for mq in mock_questions:
                        if mock['answers'].get(mq['id']) == mq['correct']:
                            score += 1
                    mock['score'] = score
                    mock['submitted'] = True
                    st.rerun()
        
        # 問題ジャンプ
        with st.expander("📋 問題一覧"):
            cols = st.columns(10)
            for i, mq in enumerate(mock_questions):
                with cols[i % 10]:
                    answered_mark = "✅" if mq['id'] in mock['answers'] else "⬜"
                    if st.button(f"{answered_mark}{mq['id']}", key=f"jump_{mq['id']}"):
                        mock['current_q'] = i
                        st.rerun()
        return
    
    if mock['submitted']:
        # 結果表示
        score = mock['score']
        pct = (score / total_q * 100) if total_q > 0 else 0
        
        st.markdown("### 🎯 模擬テスト結果")
        
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("正解数", f"{score}/{total_q}")
        with col2:
            st.metric("正答率", f"{pct:.0f}%")
        with col3:
            if pct >= 80:
                st.metric("評価", "A 🎉")
            elif pct >= 60:
                st.metric("評価", "B 👍")
            else:
                st.metric("評価", "C 💪")
        
        # セクション別結果
        st.markdown("#### セクション別:")
        for section in sections:
            section_qs = [q for q in mock_questions if q['section'] == section]
            section_correct = sum(1 for q in section_qs if mock['answers'].get(q['id']) == q['correct'])
            section_pct = (section_correct / len(section_qs) * 100) if section_qs else 0
            st.markdown(f"- **{section}**: {section_correct}/{len(section_qs)} ({section_pct:.0f}%)")
        
        # 正誤一覧
        with st.expander("📋 正誤一覧"):
            for q in mock_questions:
                user_ans = mock['answers'].get(q['id'])
                correct = q['correct']
                is_correct = user_ans == correct
                
                mark = "✅" if is_correct else "❌"
                st.markdown(f"{mark} **Q{q['id']}** [{q['section']}] {q['sentence']}")
                if not is_correct:
                    st.caption(f"  あなたの回答: {q['options'][user_ans] if user_ans is not None else '未回答'} → 正解: {q['options'][correct]}")
        
        # XP
        try:
            from utils.gamification import award_xp
            xp = award_xp('listening_complete', extra_xp=int(pct / 5))
            if xp > 0:
                st.success(f"✨ +{xp} XP")
        except Exception:
            pass
        
        if st.button("🔄 もう一度受験する"):
            del st.session_state[mock_state_key]
            st.rerun()


def show_score_progress_tab(test_info, user_data):
    """スコア推移タブ"""
    
    st.markdown("### 📈 スコア推移")
    
    history = user_data.get('practice_history', [])
    
    if not history:
        st.info("練習を開始すると、スコア推移が表示されます")
        return
    
    # グラフ
    dates = [h['date'][:10] for h in reversed(history[-10:])]
    scores = [h['score'] for h in reversed(history[-10:])]
    
    st.line_chart({"日付": dates, "スコア": scores}, x="日付", y="スコア")


def show_study_plan_tab(test_info, user_data):
    """学習プランタブ"""
    
    st.markdown("### 📅 学習プラン")
    
    test_date = user_data.get('test_date', datetime.now().date() + timedelta(days=60))
    days_left = (test_date - datetime.now().date()).days
    
    if days_left <= 0:
        st.warning("試験日を過ぎています。新しい目標を設定してください。")
        return
    
    st.info(f"🎯 試験まで **{days_left}日**")
    
    st.markdown("---")
    
    # 推奨学習量
    st.markdown("#### 📋 推奨学習量")
    
    sections = test_info['sections']
    
    for section in sections:
        col1, col2, col3 = st.columns([2, 1, 1])
        with col1:
            st.markdown(f"**{section['name']}**")
        with col2:
            st.caption("週3回以上")
        with col3:
            if st.button(f"練習開始", key=f"plan_{section['key']}"):
                st.session_state['current_view'] = 'test_prep'
                st.rerun()


def generate_demo_mock_results():
    """デモ用模擬テスト結果"""
    return [
        {
            "date": "2025-02-01",
            "total_score": 520,
            "section_scores": {"listening": 52, "structure": 50, "reading": 48},
            "time_taken": 115
        },
        {
            "date": "2025-01-15",
            "total_score": 490,
            "section_scores": {"listening": 48, "structure": 47, "reading": 45},
            "time_taken": 120
        },
    ]
