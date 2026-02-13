import streamlit as st
from utils.auth import get_current_user, require_auth
from utils.speech_eval import evaluate_pronunciation, get_feedback
from utils.gpt_eval import evaluate_language_use, format_gpt_feedback

@require_auth
def show():
    user = get_current_user()
    
    st.markdown("## 🎤 スピーキング")
    
    if st.button("← ホームに戻る"):
        if user['role'] == 'teacher':
            st.session_state['current_view'] = 'teacher_home'
        else:
            st.session_state['current_view'] = 'student_home'
        st.rerun()
    
    st.markdown("---")
    
    if user['role'] == 'teacher':
        show_teacher_view()
    else:
        show_student_view()


def show_teacher_view():
    """教員用：課題作成"""
    st.markdown("### 📝 スピーキング課題を作成")
    
    with st.form("create_speaking_assignment"):
        title = st.text_input("課題タイトル", placeholder="例: Unit 1 自己紹介")
        
        assignment_type = st.selectbox("課題タイプ", [
            "音読（学生が自分でテキスト作成）",
            "スピーチ（自由に話す）",
            "音読（教員がテキスト指定）",
            "質問応答（質問に答える）"
        ])
        
        target_text = ""
        if "教員がテキスト指定" in assignment_type:
            target_text = st.text_area(
                "読み上げテキスト",
                placeholder="学生が読み上げる英文を入力...",
                height=150
            )
        
        instructions = st.text_area(
            "指示文",
            placeholder="学生への指示を入力...",
            height=100
        )
        
        require_text_submission = st.checkbox(
            "学生にテキストの提出を求める",
            value=True,
            help="チェックを入れると、学生は音声と一緒にテキストも提出します"
        )
        
        submitted = st.form_submit_button("課題を作成", type="primary")
        
        if submitted:
            if title:
                st.success(f"課題「{title}」を作成しました！（※デモ）")
            else:
                st.error("タイトルを入力してください")
    
    st.markdown("---")
    st.markdown("### 📋 作成済みの課題（デモ）")
    st.info("データベース接続後、ここに課題一覧が表示されます")


def show_student_view():
    """学生用：課題提出"""
    st.markdown("### 📋 課題一覧")
    
    user = get_current_user()
    
    # DBから実課題を取得
    assignments = _load_speaking_assignments(user)
    is_demo = False
    
    if not assignments:
        # 実課題がない場合はフォールバック表示
        is_demo = True
        st.warning("⚠️ **サンプル課題を表示中** — 教員が課題を作成すると実際の課題に切り替わります。サンプル課題でも練習・提出は可能です。")
        assignments = [
            {
                "id": "sample_1", 
                "title": "【サンプル】自己紹介", 
                "type": "student_text", 
                "text": "", 
                "instructions": "自分自身について英語で紹介してください。ChatGPTなどで作成したテキストを使用してもOKです。",
                "require_text": True
            },
            {
                "id": "sample_2", 
                "title": "【サンプル】好きな本・映画の紹介", 
                "type": "student_text", 
                "text": "", 
                "instructions": "好きな本や映画について紹介してください。",
                "require_text": True
            },
            {
                "id": "sample_3", 
                "title": "【サンプル】自由スピーチ", 
                "type": "free_speech", 
                "text": "", 
                "instructions": "好きなトピックについて自由に話してください（1〜3分程度）",
                "require_text": False
            },
        ]
    
    selected = st.selectbox(
        "課題を選択",
        assignments,
        format_func=lambda x: x['title']
    )
    
    if selected:
        st.markdown("---")
        
        if selected.get('instructions'):
            st.markdown("### 📝 指示")
            st.info(selected['instructions'])
        
        target_text = ""
        
        if selected['type'] == 'teacher_text':
            st.markdown("### 📖 読み上げるテキスト")
            st.success(selected['text'])
            target_text = selected['text']
            
        elif selected['type'] == 'student_text':
            st.markdown("### ✏️ テキスト入力")
            
            if selected.get('require_text'):
                st.caption("読み上げるテキストを入力してください（ChatGPTなどで作成してもOK）")
                target_text = st.text_area(
                    "あなたのテキスト",
                    placeholder="読み上げる英文を入力...",
                    height=150,
                    key="student_text_input"
                )
            else:
                with st.expander("テキストを入力（任意）"):
                    target_text = st.text_area(
                        "テキスト（任意）",
                        placeholder="テキストがあれば入力...",
                        height=100,
                        key="optional_text_input"
                    )
            
            if target_text:
                word_count = len(target_text.split())
                st.caption(f"📊 語数: {word_count} words")
            
        else:
            with st.expander("テキストを入力（任意）"):
                st.caption("話す内容のメモや原稿があれば入力できます")
                target_text = st.text_area(
                    "テキスト（任意）",
                    placeholder="テキストがあれば入力...",
                    height=100,
                    key="free_speech_text"
                )
        
        st.markdown("---")
        st.markdown("### 🎙️ 音声または動画をアップロード")
        st.caption("対応形式: WAV, MP3, M4A, MP4（最大10分）")
        
        uploaded_file = st.file_uploader(
            "ファイルを選択",
            type=['wav', 'mp3', 'm4a', 'mp4', 'mov', 'webm']
        )
        
        if uploaded_file:
            # ファイルタイプに応じて表示
            file_ext = uploaded_file.name.lower().split('.')[-1]
            if file_ext in ['mp4', 'mov', 'webm']:
                st.video(uploaded_file)
            else:
                st.audio(uploaded_file)
            
            can_submit = True
            if selected.get('require_text') and selected['type'] == 'student_text' and not target_text:
                st.warning("⚠️ この課題ではテキストの入力が必要です")
                can_submit = False
            
            if can_submit:
                if st.button("📤 提出して評価", type="primary"):
                    evaluate_and_show_results(uploaded_file, target_text)


def evaluate_and_show_results(uploaded_file, target_text):
    """評価を実行して結果を表示"""
    
    with st.spinner("🎧 音声を分析中..."):
        pronunciation_result = evaluate_pronunciation(uploaded_file, target_text)
    
    if not pronunciation_result["success"]:
        st.error(f"発音評価エラー: {pronunciation_result['error']}")
        return
    
    recognized_text = pronunciation_result.get("recognized_text", "")
    text_to_evaluate = recognized_text if recognized_text else target_text
    
    gpt_result = None
    if text_to_evaluate and len(text_to_evaluate.split()) >= 5:
        with st.spinner("📝 言語使用を分析中..."):
            gpt_result = evaluate_language_use(text_to_evaluate, context="speaking")
    
    st.success("✅ 評価完了！")
    
    show_results(pronunciation_result, gpt_result, target_text)


def show_results(pronunciation_result, gpt_result, target_text):
    """評価結果を表示"""
    
    scores = pronunciation_result.get("scores", {})
    intelligibility = pronunciation_result.get("intelligibility", {})
    duration = pronunciation_result.get("duration", 0)
    
    tab1, tab2, tab3 = st.tabs(["📊 サマリー", "🎤 発音評価", "📝 言語使用評価"])
    
    with tab1:
        show_summary(scores, intelligibility, duration, gpt_result)
    
    with tab2:
        show_pronunciation_details(pronunciation_result, target_text)
    
    with tab3:
        show_language_details(gpt_result)


def show_summary(scores, intelligibility, duration, gpt_result):
    """サマリータブ"""
    
    st.markdown("### 🎯 評価サマリー")
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        overall = scores.get('overall', 0)
        st.metric("総合スコア", f"{overall:.0f}/100")
    
    with col2:
        icon = intelligibility.get('icon', '🟡')
        level = intelligibility.get('level', '中程度')
        st.metric("通じやすさ", f"{icon} {level}")
    
    with col3:
        st.metric("音声長", f"{duration:.1f}秒")
    
    with col4:
        cefr = get_cefr_from_score(scores.get('overall', 0))
        st.metric("CEFRレベル", cefr)
    
    if gpt_result and gpt_result.get("success"):
        gpt_scores = gpt_result.get("scores", {})
        
        st.markdown("---")
        st.markdown("### 📊 詳細スコア")
        
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric("発音", f"{scores.get('accuracy', 0):.0f}/100")
        with col2:
            st.metric("流暢さ", f"{scores.get('fluency', 0):.0f}/100")
        with col3:
            st.metric("語彙", f"{gpt_scores.get('vocabulary', 0)}/100")
        with col4:
            st.metric("文法", f"{gpt_scores.get('grammar', 0)}/100")
    
    if gpt_result and gpt_result.get("overall_feedback"):
        st.markdown("---")
        st.markdown("### 💬 総合フィードバック")
        st.info(gpt_result.get("overall_feedback"))


def show_pronunciation_details(result, target_text):
    """発音評価の詳細"""
    
    scores = result.get("scores", {})
    recognized_text = result.get("recognized_text", "")
    
    st.markdown("### 📊 発音スコア詳細")
    
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("発音の明瞭さ", f"{scores.get('accuracy', 0):.0f}/100")
    with col2:
        st.metric("流暢さ", f"{scores.get('fluency', 0):.0f}/100")
    with col3:
        st.metric("完全性", f"{scores.get('completeness', 0):.0f}/100")
    with col4:
        st.metric("イントネーション", f"{scores.get('prosody', 0):.0f}/100")
    
    if recognized_text:
        st.markdown("---")
        st.markdown("### 🎧 認識されたテキスト")
        st.text_area("AIが聞き取った内容", recognized_text, height=100, disabled=True)
    
    st.markdown("---")
    problem_words = result.get("problem_words", [])
    problem_phonemes = result.get("problem_phonemes", [])
    duration = result.get("duration", 0)
    
    feedback = get_feedback(scores, problem_words, problem_phonemes, target_text, duration)
    st.markdown(feedback["feedback"])


def show_language_details(gpt_result):
    """言語使用評価の詳細"""
    
    if not gpt_result:
        st.info("💡 音声が短いか、テキストが認識されなかったため、言語使用の詳細評価はスキップされました。")
        return
    
    if not gpt_result.get("success"):
        st.error(f"言語評価エラー: {gpt_result.get('error', '不明なエラー')}")
        return
    
    formatted = format_gpt_feedback(gpt_result)
    st.markdown(formatted)


def _load_speaking_assignments(user):
    """DBからスピーキング課題を取得"""
    try:
        # コースIDを取得
        course_id = None
        if user['role'] == 'student':
            registered = st.session_state.get('student_registered_classes', [])
            if registered:
                course_id = registered[0].get('class_key')
        
        if not course_id:
            return []
        
        from utils.database import get_course_assignments
        all_assignments = get_course_assignments(course_id)
        
        if not all_assignments:
            return []
        
        # スピーキング課題のみフィルタ
        speaking = []
        for a in all_assignments:
            atype = (a.get('assignment_type') or '').lower()
            if 'speaking' in atype or 'speech' in atype or 'pronunciation' in atype or 'reading_aloud' in atype:
                speaking.append({
                    'id': a['id'],
                    'title': a.get('title', ''),
                    'type': _map_assignment_type(a),
                    'text': a.get('target_text', '') or a.get('description', '') or '',
                    'instructions': a.get('instructions', '') or a.get('description', ''),
                    'require_text': a.get('require_text_submission', True),
                })
        
        return speaking
    except Exception:
        return []


def _map_assignment_type(assignment):
    """DB課題タイプをUI用に変換"""
    atype = (assignment.get('assignment_type') or '').lower()
    if 'teacher_text' in atype or 'reading_aloud' in atype:
        return 'teacher_text'
    elif 'free' in atype or 'speech' in atype:
        return 'free_speech'
    else:
        return 'student_text'


def get_cefr_from_score(score):
    if score >= 85: return "C1"
    elif score >= 70: return "B2"
    elif score >= 55: return "B1"
    elif score >= 40: return "A2"
    else: return "A1"
