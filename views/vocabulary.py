import streamlit as st
from utils.auth import get_current_user, require_auth
from utils.vocabulary import (
    get_word_details, 
    generate_quiz_question,
    generate_word_list_from_prompt,
    generate_exercises_for_word,
    grade_student_sentence,          # ← 追加
)
from utils.materials_loader import load_materials
from utils.database import (
    add_vocabulary,
    get_student_vocabulary,
    get_vocabulary_for_review,
    update_vocabulary_after_review,
    get_vocabulary_stats,
    save_quiz_result,
    save_word_list,
    log_practice,
)
import random

@require_auth
def show():
    user = get_current_user()
    
    st.markdown("## 📚 語彙学習 / Vocabulary")
    
    if st.button("← ホームに戻る / Back"):
        st.session_state['current_view'] = 'teacher_home' if user['role'] == 'teacher' else 'student_home'
        st.rerun()
    
    st.markdown("---")
    
    if user['role'] == 'teacher':
        show_teacher_view()
    else:
        show_student_view()


def show_teacher_view():
    """教員用"""
    
    tab1, tab2, tab3 = st.tabs(["🤖 AI単語リスト生成", "📋 リスト管理", "📊 学習状況"])
    
    with tab1:
        show_ai_list_generator()
    
    with tab2:
        show_list_management()
    
    with tab3:
        show_class_progress()


def show_ai_list_generator():
    """AI単語リスト生成"""
    
    st.markdown("### 🤖 AIで単語リストを生成 / Generate Word List with AI")
    st.caption("プロンプトを入力するだけで、カスタム単語リストを作成できます")
    
    # 例を表示
    with st.expander("💡 プロンプト例 / Example Prompts"):
        examples = [
            "TOEFL頻出の学術単語 20語",
            "IELTS Writing Task 2 で使える表現 15語",
            "ビジネスメールで使う丁寧な表現 10語",
            "環境問題について議論するための語彙 20語",
            "就職面接で使える表現 15語",
            "大学の授業で使うアカデミック語彙 20語",
            "映画やドラマでよく聞くスラング 10語",
            "科学論文で頻出の動詞 15語",
        ]
        for ex in examples:
            st.markdown(f"- {ex}")
    
    # 入力フォーム
    prompt = st.text_area(
        "プロンプト / Prompt",
        placeholder="例: TOEFL頻出の学術単語 20語",
        height=100
    )
    
    col1, col2 = st.columns(2)
    with col1:
        num_words = st.slider("単語数 / Number of words", 5, 50, 20)
    with col2:
        level = st.select_slider("レベル / Level", ["A1", "A2", "B1", "B2", "C1"], value="B1")
    
    if st.button("🚀 生成 / Generate", type="primary", disabled=not prompt):
        with st.spinner("単語リストを生成中... / Generating..."):
            result = generate_word_list_from_prompt(prompt, num_words, level)
        
        if result.get("success"):
            st.session_state['generated_list'] = result
            st.success("✅ 生成完了！ / Generated!")
        else:
            st.error(f"Error: {result.get('error')}")
    
    # 生成結果を表示
    if 'generated_list' in st.session_state:
        result = st.session_state['generated_list']
        
        st.markdown("---")
        st.markdown(f"### 📚 {result.get('list_name', 'Generated List')}")
        st.caption(result.get('description', ''))
        
        words = result.get('words', [])
        
        # テーブル表示
        for i, w in enumerate(words, 1):
            with st.expander(f"{i}. **{w['word']}** - {w['meaning']}"):
                st.markdown(f"**品詞 / POS:** {w.get('pos', 'N/A')}")
                st.markdown(f"**例文 / Example:** *{w.get('example', '')}*")
                if w.get('tips'):
                    st.info(f"💡 {w.get('tips')}")
        
        # 保存ボタン
        col1, col2 = st.columns(2)
        with col1:
            if st.button("💾 このリストを保存 / Save List"):
                user = get_current_user()
                try:
                    save_word_list(
                        teacher_id=user['id'],
                        list_name=result.get('list_name', 'Generated List'),
                        words=words,
                        description=result.get('description', ''),
                        level=level if 'level' in dir() else 'B1',
                        course_id=st.session_state.get('current_course', {}).get('id'),
                        is_ai_generated=True,
                    )
                    st.success("データベースに保存しました！")
                except Exception as e:
                    st.warning(f"DB保存エラー: {e}")
                    st.success("ローカルに保存しました！")
        with col2:
            if st.button("🗑️ クリア / Clear"):
                del st.session_state['generated_list']
                st.rerun()


def show_list_management():
    """リスト管理"""
    
    st.markdown("### 📋 単語リスト管理 / Manage Word Lists")
    
    st.markdown("#### 既存のリスト / Existing Lists")
    word_lists = load_materials('vocabulary')
    for key, word_list in word_lists.items():
        words = word_list.get('words', [])
        name = word_list.get('name', word_list.get('title', key))
        with st.expander(f"📚 {name} ({len(words)} words) - {word_list.get('level', '')}"):
            st.caption(word_list.get('description', ''))
            for w in words[:5]:
                st.markdown(f"- **{w['word']}**: {w['meaning']}")
            if len(words) > 5:
                st.caption(f"... and {len(words) - 5} more")


def show_class_progress():
    """クラス学習状況"""
    
    st.markdown("### 📊 学習状況 / Learning Progress")
    
    # --- Supabaseからコースの学生データを取得 ---
    course_id = st.session_state.get('current_course', {}).get('id')
    if course_id:
        try:
            from utils.database import get_course_students, get_vocabulary_stats
            students = get_course_students(course_id)
            if students:
                import pandas as pd
                rows = []
                for s in students:
                    student = s.get('users', s)
                    sid = student.get('id', s.get('student_id'))
                    try:
                        vstats = get_vocabulary_stats(sid)
                    except Exception:
                        vstats = {'total': 0, 'mastered': 0}
                    rows.append({
                        '学生': student.get('name', '-'),
                        '学習単語数': vstats.get('total', 0),
                        'マスター済み': vstats.get('mastered', 0),
                    })
                df = pd.DataFrame(rows)
                
                col1, col2 = st.columns(2)
                with col1:
                    st.metric("平均学習単語数", f"{df['学習単語数'].mean():.0f}")
                with col2:
                    st.metric("平均マスター数", f"{df['マスター済み'].mean():.0f}")
                
                st.dataframe(df, use_container_width=True, hide_index=True)
                return
        except Exception:
            pass
    
    st.info("コースを選択すると、学生の学習状況が表示されます")
    
    # フォールバック: デモデータ
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("平均学習単語数", "45 words")
    with col2:
        st.metric("平均正答率", "72%")
    with col3:
        st.metric("アクティブ学生", "38/50")


def show_student_view():
    """学生用"""
    
    tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs([
        "🃏 フラッシュカード",
        "✏️ 能動的想起",
        "📝 単語テスト",
        "🤖 AI単語学習",
        "🔍 単語検索",
        "📊 学習記録"
    ])
    
    with tab1:
        show_flashcards()
    
    with tab2:
        show_active_recall()
    
    with tab3:
        show_quiz()
    
    with tab4:
        show_ai_word_learning()
    
    with tab5:
        show_word_search()
    
    with tab6:
        show_progress()


def show_ai_word_learning():
    """AI単語学習（学生用）"""
    
    st.markdown("### 🤖 AI単語学習 / AI-Powered Learning")
    
    # モード選択
    mode = st.radio(
        "学習モード / Mode",
        ["single_word", "custom_list"],
        format_func=lambda x: {
            "single_word": "🔤 単語を深く学ぶ / Deep dive into a word",
            "custom_list": "📝 カスタムリスト生成 / Generate custom list"
        }[x],
        horizontal=True
    )
    
    if mode == "single_word":
        st.markdown("---")
        st.markdown("#### 🔤 単語を入力すると、様々な練習問題を生成します")
        
        word = st.text_input("学習したい単語 / Word to learn", placeholder="例: sustainable")
        
        if word and st.button("🚀 練習問題を生成 / Generate Exercises", type="primary"):
            with st.spinner("生成中... / Generating..."):
                result = generate_exercises_for_word(word)
            
            if result.get("success"):
                st.session_state['word_exercises'] = result
                st.success("✅ 生成完了！")
            else:
                st.error(f"Error: {result.get('error')}")
        
        # 練習問題を表示
        if 'word_exercises' in st.session_state:
            show_word_exercises(st.session_state['word_exercises'])
    
    else:  # custom_list
        st.markdown("---")
        st.markdown("#### 📝 学びたいテーマを入力してください")
        
        prompt = st.text_area(
            "テーマ / Theme",
            placeholder="例: プレゼンで使えるつなぎ言葉、環境問題の語彙、TOEIC Part 5 頻出語彙",
            height=80
        )
        
        col1, col2 = st.columns(2)
        with col1:
            num_words = st.slider("単語数", 5, 30, 15)
        with col2:
            level = st.select_slider("レベル", ["A1", "A2", "B1", "B2", "C1"], value="B1")
        
        if prompt and st.button("🚀 リスト生成 / Generate", type="primary"):
            with st.spinner("生成中... / Generating..."):
                result = generate_word_list_from_prompt(prompt, num_words, level)
            
            if result.get("success"):
                st.session_state['student_generated_list'] = result
                st.success("✅ 生成完了！")
            else:
                st.error(f"Error: {result.get('error')}")
        
        # 生成リストを表示
        if 'student_generated_list' in st.session_state:
            show_generated_list_for_student(st.session_state['student_generated_list'])


def show_word_exercises(data):
    """単語の練習問題を表示"""
    
    st.markdown("---")
    st.markdown(f"## 📚 {data.get('word', 'Word')} の練習")
    
    # 覚え方のヒント
    if data.get('memory_tips'):
        st.success(f"💡 **覚え方 / Memory Tip:** {data.get('memory_tips')}")
    
    # よくある間違い
    if data.get('common_mistakes'):
        st.warning(f"⚠️ **よくある間違い / Common Mistakes:** {data.get('common_mistakes')}")
    
    st.markdown("---")
    
    exercises = data.get('exercises', [])
    
    for i, ex in enumerate(exercises, 1):
        ex_type = ex.get('type', '')
        
        with st.expander(f"**練習 {i}:** {get_exercise_type_name(ex_type)}", expanded=(i==1)):
            
            if ex_type in ['meaning_choice', 'collocation', 'synonym']:
                # 選択問題
                st.markdown(f"**{ex.get('question', '')}**")
                
                options = ex.get('options', [])
                correct = ex.get('correct', '')
                
                # セッション状態で回答を管理
                answer_key = f"ex_{i}_answer"
                if answer_key not in st.session_state:
                    st.session_state[answer_key] = None
                
                for opt in options:
                    if st.button(opt, key=f"opt_{i}_{opt}"):
                        st.session_state[answer_key] = opt
                        st.rerun()
                
                if st.session_state[answer_key]:
                    if st.session_state[answer_key] == correct:
                        st.success("✅ Correct! / 正解！")
                    else:
                        st.error(f"❌ Incorrect. Answer: {correct}")
                    st.info(f"💡 {ex.get('explanation', '')}")
            
            elif ex_type == 'fill_blank':
                # 穴埋め
                st.markdown(f"**{ex.get('question', '')}**")
                if ex.get('hint'):
                    st.caption(f"Hint: {ex.get('hint')}")
                
                user_answer = st.text_input("Your answer:", key=f"fill_{i}")
                if user_answer:
                    correct = ex.get('answer', '')
                    if user_answer.lower().strip() == correct.lower():
                        st.success("✅ Correct!")
                    else:
                        st.error(f"❌ Answer: {correct}")
                    st.info(f"💡 {ex.get('explanation', '')}")
            
            elif ex_type == 'sentence_creation':
                # ===== 作文 + AI採点 =====
                st.markdown(f"**{ex.get('instruction', '')}**")
                
                user_sentence = st.text_area("Your sentence:", key=f"sentence_{i}", height=80)
                
                # AI採点ボタン（文字入力後のみ表示）
                grade_key = f"grade_result_{i}"
                if user_sentence.strip():
                    if st.button("🤖 採点する / Grade my sentence", key=f"grade_btn_{i}", type="primary"):
                        with st.spinner("採点中... / Grading..."):
                            context = {
                                "meaning": data.get("meaning", ""),
                                "example": ex.get("sample_answer", "")
                            }
                            result = grade_student_sentence(data.get("word", ""), user_sentence, context)
                            st.session_state[grade_key] = result
                
                # 採点結果表示
                if grade_key in st.session_state:
                    result = st.session_state[grade_key]
                    if result.get("success"):
                        score = result.get("score", 0)
                        
                        # スコア表示
                        col_s1, col_s2 = st.columns([1, 3])
                        with col_s1:
                            if score >= 80:
                                st.metric("Score", f"{score}/100", delta="Excellent! 🌟")
                            elif score >= 60:
                                st.metric("Score", f"{score}/100", delta="Good 👍")
                            else:
                                st.metric("Score", f"{score}/100", delta="Keep trying 💪")
                        with col_s2:
                            st.progress(score / 100)
                        
                        # フィードバック
                        with st.container(border=True):
                            st.markdown(f"**📝 Feedback (EN):** {result.get('feedback_en', '')}")
                            st.markdown(f"**📝 フィードバック (JA):** {result.get('feedback_ja', '')}")
                            if result.get("suggestion"):
                                st.info(f"💡 **改善提案 / Suggestion:** {result.get('suggestion')}")
                    else:
                        st.error(f"採点エラー: {result.get('error', 'Unknown error')}")
                
                # サンプル・ポイントは折りたたみ表示（答えを見るのは後から）
                with st.expander("📖 Sample answer & Key points"):
                    st.markdown(f"> {ex.get('sample_answer', '')}")
                    if ex.get('key_points'):
                        st.markdown("**Key points / ポイント:**")
                        for point in ex.get('key_points', []):
                            st.markdown(f"- {point}")


def show_generated_list_for_student(result):
    """学生用の生成リスト表示"""
    
    st.markdown("---")
    st.markdown(f"### 📚 {result.get('list_name', 'Generated List')}")
    st.caption(result.get('description', ''))
    
    words = result.get('words', [])
    
    # フラッシュカードモードで学習
    if st.button("🃏 このリストでフラッシュカード学習", type="primary"):
        st.session_state['custom_flashcard_words'] = words
        st.session_state['custom_flashcard_index'] = 0
        st.session_state['custom_flashcard_flipped'] = False
        st.rerun()
    
    # リスト表示
    for i, w in enumerate(words, 1):
        with st.expander(f"{i}. **{w['word']}** - {w['meaning']}"):
            st.markdown(f"**例文:** *{w.get('example', '')}*")
            if w.get('tips'):
                st.info(f"💡 {w.get('tips')}")
    
    # カスタムフラッシュカード
    if 'custom_flashcard_words' in st.session_state:
        st.markdown("---")
        show_custom_flashcards()


def show_custom_flashcards():
    """カスタム生成リストのフラッシュカード"""
    
    words = st.session_state.get('custom_flashcard_words', [])
    if not words:
        return
    
    idx = st.session_state.get('custom_flashcard_index', 0)
    flipped = st.session_state.get('custom_flashcard_flipped', False)
    
    current = words[idx]
    
    st.progress((idx + 1) / len(words))
    st.caption(f"Card {idx + 1} / {len(words)}")
    
    if not flipped:
        st.markdown(f"""
        <div style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            padding: 40px; border-radius: 20px; text-align: center; color: white;">
            <h1>{current['word']}</h1>
        </div>
        """, unsafe_allow_html=True)
    else:
        st.markdown(f"""
        <div style="background: linear-gradient(135deg, #11998e 0%, #38ef7d 100%);
            padding: 40px; border-radius: 20px; text-align: center; color: white;">
            <h2>{current['meaning']}</h2>
            <p><i>{current.get('example', '')}</i></p>
        </div>
        """, unsafe_allow_html=True)
    
    col1, col2, col3 = st.columns(3)
    with col1:
        if st.button("◀️ 前", key="custom_prev"):
            if idx > 0:
                st.session_state['custom_flashcard_index'] = idx - 1
                st.session_state['custom_flashcard_flipped'] = False
                st.rerun()
    with col2:
        if st.button("🔄 めくる", key="custom_flip", type="primary"):
            st.session_state['custom_flashcard_flipped'] = not flipped
            st.rerun()
    with col3:
        if st.button("▶️ 次", key="custom_next"):
            if idx < len(words) - 1:
                st.session_state['custom_flashcard_index'] = idx + 1
                st.session_state['custom_flashcard_flipped'] = False
                st.rerun()


def get_exercise_type_name(ex_type):
    """練習問題タイプの日本語名"""
    names = {
        "meaning_choice": "意味を選ぶ / Choose the meaning",
        "fill_blank": "穴埋め / Fill in the blank",
        "collocation": "コロケーション / Collocation",
        "synonym": "類義語 / Synonym",
        "sentence_creation": "作文 + AI採点 / Create a sentence"
    }
    return names.get(ex_type, ex_type)


def show_flashcards():
    """フラッシュカードモード（既存リスト用）"""
    
    st.markdown("### 🃏 フラッシュカード / Flashcards")
    
    word_lists = load_materials('vocabulary')
    if not word_lists:
        st.info("単語リストがありません")
        return
    list_options = {key: f"{data.get('name', data.get('title', key))} ({data.get('level', '')})" for key, data in word_lists.items()}
    selected_list = st.selectbox(
        "単語リストを選択 / Select Word List",
        options=list(list_options.keys()),
        format_func=lambda x: list_options[x]
    )
    
    if selected_list:
        word_list = word_lists[selected_list]
        words = word_list.get('words', [])
        
        if 'flashcard_index' not in st.session_state:
            st.session_state.flashcard_index = 0
        if 'flashcard_flipped' not in st.session_state:
            st.session_state.flashcard_flipped = False
        if 'flashcard_list' not in st.session_state:
            st.session_state.flashcard_list = selected_list
        
        if st.session_state.flashcard_list != selected_list:
            st.session_state.flashcard_index = 0
            st.session_state.flashcard_flipped = False
            st.session_state.flashcard_list = selected_list
        
        current_word = words[st.session_state.flashcard_index]
        
        st.progress((st.session_state.flashcard_index + 1) / len(words))
        st.caption(f"Card {st.session_state.flashcard_index + 1} / {len(words)}")
        
        st.markdown("---")
        
        if not st.session_state.flashcard_flipped:
            st.markdown(f"""
            <div style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                padding: 40px; border-radius: 20px; text-align: center; color: white; min-height: 200px;">
                <h1 style="margin: 0; font-size: 2.5em;">{current_word['word']}</h1>
                <p style="margin-top: 10px; opacity: 0.8;">{current_word['pos']}</p>
            </div>
            """, unsafe_allow_html=True)
        else:
            st.markdown(f"""
            <div style="background: linear-gradient(135deg, #11998e 0%, #38ef7d 100%);
                padding: 40px; border-radius: 20px; text-align: center; color: white; min-height: 200px;">
                <h2 style="margin: 0;">{current_word['meaning']}</h2>
                <p style="margin-top: 20px; font-style: italic;">"{current_word['example']}"</p>
            </div>
            """, unsafe_allow_html=True)
        
        st.markdown("---")
        
        col1, col2, col3, col4, col5 = st.columns(5)
        
        with col1:
            if st.button("⏮️", use_container_width=True):
                st.session_state.flashcard_index = 0
                st.session_state.flashcard_flipped = False
                st.rerun()
        with col2:
            if st.button("◀️", use_container_width=True):
                if st.session_state.flashcard_index > 0:
                    st.session_state.flashcard_index -= 1
                    st.session_state.flashcard_flipped = False
                    st.rerun()
        with col3:
            if st.button("🔄 めくる", use_container_width=True, type="primary"):
                st.session_state.flashcard_flipped = not st.session_state.flashcard_flipped
                st.rerun()
        with col4:
            if st.button("▶️", use_container_width=True):
                if st.session_state.flashcard_index < len(words) - 1:
                    st.session_state.flashcard_index += 1
                    st.session_state.flashcard_flipped = False
                    st.rerun()
        with col5:
            if st.button("🔀", use_container_width=True):
                random.shuffle(words)
                st.session_state.flashcard_index = 0
                st.session_state.flashcard_flipped = False
                st.rerun()


def show_active_recall():
    """能動的想起モード（タイプ入力で単語を答える）"""
    st.markdown("### ✏️ 能動的想起 / Active Recall")
    st.caption("日本語の意味を見て、英単語をタイプ入力で答えましょう")

    word_lists = load_materials('vocabulary')
    if not word_lists:
        st.info("単語リストがありません")
        return

    list_options = {key: f"{data.get('name', data.get('title', key))} ({data.get('level', '')})" for key, data in word_lists.items()}
    selected_list = st.selectbox(
        "単語リストを選択",
        options=list(list_options.keys()),
        format_func=lambda x: list_options[x],
        key="ar_list"
    )

    if not selected_list:
        return

    word_list = word_lists[selected_list]
    words = word_list.get('words', [])
    if not words:
        st.info("単語がありません")
        return

    # セッション初期化
    ar_list_key = 'ar_list_id'
    if st.session_state.get(ar_list_key) != selected_list:
        st.session_state[ar_list_key] = selected_list
        st.session_state['ar_index'] = 0
        st.session_state['ar_results'] = []
        st.session_state['ar_answered'] = False
        st.session_state['ar_correct'] = None

    idx = st.session_state.get('ar_index', 0)

    # 全問完了
    if idx >= len(words):
        results = st.session_state.get('ar_results', [])
        correct_count = sum(1 for r in results if r['correct'])
        score = correct_count / max(len(results), 1) * 100
        st.markdown(f"### 🎯 結果: {correct_count}/{len(results)} ({score:.0f}%)")
        for r in results:
            if r['correct']:
                st.success(f"✅ {r['meaning']} → **{r['word']}**")
            else:
                st.error(f"❌ {r['meaning']} → 正解: **{r['word']}** / あなたの回答: {r['user_answer']}")

        # DB保存
        try:
            user = st.session_state.get('user')
            if user and user.get('role') != 'teacher':
                from utils.database import log_practice
                from utils.analytics import invalidate_analytics_cache
                log_practice(
                    student_id=user['id'],
                    module_type='vocabulary_flashcard',
                    score=score,
                    activity_details={'type': 'active_recall', 'list': selected_list, 'correct': correct_count, 'total': len(results)}
                )
                invalidate_analytics_cache()
        except Exception as e:
            st.warning(f"⚠️ 記録の保存に失敗しました: {e}")

        if st.button("🔄 もう一度", type="primary", key="ar_retry"):
            st.session_state['ar_index'] = 0
            st.session_state['ar_results'] = []
            st.session_state['ar_answered'] = False
            st.session_state['ar_correct'] = None
            st.rerun()
        return

    current_word = words[idx]
    st.progress((idx + 1) / len(words))
    st.caption(f"問題 {idx + 1} / {len(words)}")
    st.markdown("---")

    # 問題表示（日本語の意味）
    st.markdown(f"""
    <div style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        padding: 40px; border-radius: 20px; text-align: center; color: white; min-height: 160px;">
        <p style="margin: 0; opacity: 0.8; font-size: 1em;">{current_word.get('pos', '')}</p>
        <h2 style="margin: 10px 0;">{current_word['meaning']}</h2>
        <p style="margin-top: 10px; opacity: 0.7; font-size: 0.9em; font-style: italic;">{current_word.get('example', '')}</p>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("---")

    answered = st.session_state.get('ar_answered', False)

    if not answered:
        user_input = st.text_input(
            "英単語を入力してください",
            key=f"ar_input_{idx}",
            placeholder="Type the English word..."
        )
        if st.button("✅ 確認", type="primary", key=f"ar_check_{idx}"):
            if not user_input.strip():
                st.warning("単語を入力してください")
            else:
                correct_word = current_word['word'].lower().strip()
                user_word = user_input.lower().strip()
                is_correct = correct_word == user_word
                st.session_state['ar_answered'] = True
                st.session_state['ar_correct'] = is_correct
                st.session_state['ar_results'].append({
                    'word': current_word['word'],
                    'meaning': current_word['meaning'],
                    'user_answer': user_input,
                    'correct': is_correct
                })
                st.rerun()
    else:
        is_correct = st.session_state.get('ar_correct', False)
        if is_correct:
            st.success(f"✅ 正解！ **{current_word['word']}**")
        else:
            last = st.session_state['ar_results'][-1]
            st.error(f"❌ 不正解。正解: **{current_word['word']}** / あなたの回答: {last['user_answer']}")
        st.markdown(f"*例文:* {current_word.get('example', '')}")

        if st.button("▶️ 次の単語", type="primary", key=f"ar_next_{idx}"):
            st.session_state['ar_index'] = idx + 1
            st.session_state['ar_answered'] = False
            st.session_state['ar_correct'] = None
            st.rerun()


def show_quiz():
    """単語テスト"""
    
    st.markdown("### 📝 単語テスト / Vocabulary Quiz")
    
    word_lists = load_materials('vocabulary')
    if not word_lists:
        st.info("単語リストがありません")
        return
    list_options = {key: data.get('name', data.get('title', key)) for key, data in word_lists.items()}
    selected_list = st.selectbox(
        "単語リストを選択",
        options=list(list_options.keys()),
        format_func=lambda x: list_options[x],
        key="quiz_list"
    )
    
    quiz_type = st.radio(
        "クイズタイプ",
        ["meaning", "word", "fill"],
        format_func=lambda x: {"meaning": "🔤 意味を当てる", "word": "📖 単語を当てる", "fill": "✏️ 穴埋め"}[x],
        horizontal=True
    )
    
    if 'quiz_started' not in st.session_state:
        st.session_state.quiz_started = False
    
    word_list = word_lists[selected_list]
    words = word_list['words']
    
    if not st.session_state.quiz_started:
        num_q = st.slider("問題数", 5, min(20, len(words)), min(10, len(words)))
        
        if st.button("🚀 開始", type="primary"):
            st.session_state.quiz_started = True
            st.session_state.quiz_score = 0
            st.session_state.quiz_total = num_q
            st.session_state.quiz_questions = random.sample(words, num_q)
            st.session_state.quiz_index = 0
            st.session_state.quiz_answered = False
            st.session_state.quiz_type = quiz_type
            st.rerun()
    else:
        if st.session_state.quiz_index < st.session_state.quiz_total:
            st.progress(st.session_state.quiz_index / st.session_state.quiz_total)
            st.markdown(f"**Q{st.session_state.quiz_index + 1}/{st.session_state.quiz_total}** | Score: {st.session_state.quiz_score}")
            
            current = st.session_state.quiz_questions[st.session_state.quiz_index]
            q = generate_quiz_question(current, words, st.session_state.quiz_type)
            
            st.markdown(f"### {q['question']}")
            
            if not st.session_state.quiz_answered:
                for opt in q['options']:
                    if st.button(opt, key=f"q_{opt}"):
                        st.session_state.quiz_answered = True
                        st.session_state.quiz_last_correct = (opt == q['correct'])
                        if st.session_state.quiz_last_correct:
                            st.session_state.quiz_score += 1
                        st.rerun()
            else:
                if st.session_state.quiz_last_correct:
                    st.success("✅ Correct!")
                else:
                    st.error(f"❌ Answer: {q['correct']}")
                
                if st.button("▶️ Next"):
                    st.session_state.quiz_index += 1
                    st.session_state.quiz_answered = False
                    st.rerun()
        else:
            pct = (st.session_state.quiz_score / st.session_state.quiz_total) * 100
            st.markdown(f"## 🎉 完了！ Score: {st.session_state.quiz_score}/{st.session_state.quiz_total} ({pct:.0f}%)")
            
            # --- Supabaseに保存 ---
            if not st.session_state.get('quiz_saved'):
                user = get_current_user()
                try:
                    save_quiz_result(
                        student_id=user['id'],
                        list_name=word_list.get('name', selected_list),
                        quiz_type=st.session_state.quiz_type,
                        score=st.session_state.quiz_score,
                        total=st.session_state.quiz_total,
                        course_id=st.session_state.get('current_course', {}).get('id'),
                    )
                    # practice_logsに記録（ダッシュボード集計用）
                    log_practice(
                        student_id=user['id'],
                        module_type='vocabulary_quiz',
                        course_id=st.session_state.get('current_course', {}).get('id'),
                        score=round(pct, 1),
                        duration_seconds=st.session_state.quiz_total * 20,  # 1問20秒で概算
                        activity_details={
                            'activity': 'vocabulary_quiz',
                            'list_name': word_list.get('name', selected_list),
                            'quiz_type': st.session_state.quiz_type,
                            'correct': st.session_state.quiz_score,
                            'total': st.session_state.quiz_total,
                        }
                    )
                    st.session_state.quiz_saved = True
                except Exception:
                    pass
            
            if st.button("🔄 もう一度"):
                st.session_state.quiz_started = False
                st.session_state.quiz_saved = False
                st.rerun()


def show_word_search():
    """単語検索"""
    
    st.markdown("### 🔍 単語検索 / Word Search")
    
    word = st.text_input("英単語を入力", placeholder="例: sustainable")
    
    if word and st.button("🔍 検索", type="primary"):
        with st.spinner("検索中..."):
            result = get_word_details(word)
        
        if result.get("success"):
            st.markdown(f"## {result.get('word', word)}")
            st.caption(f"🔊 {result.get('pronunciation', '')}")
            
            for m in result.get("meanings", []):
                st.markdown(f"### {m.get('pos', '')}")
                st.markdown(f"**EN:** {m.get('definition_en', '')}")
                st.markdown(f"**JP:** {m.get('definition_ja', '')}")
                for ex in m.get("examples", []):
                    st.markdown(f"- *{ex}*")
            
            if result.get("usage_notes"):
                st.info(f"💡 {result.get('usage_notes')}")
            
            # --- 単語帳に追加 ---
            if st.button("📚 単語帳に追加 / Add to My Vocabulary", key="add_vocab"):
                user = get_current_user()
                meanings = result.get("meanings", [])
                meaning_text = meanings[0].get('definition_ja', '') if meanings else ''
                try:
                    add_vocabulary(
                        student_id=user['id'],
                        word=word,
                        meaning=meaning_text,
                        source_type='search',
                        pos=meanings[0].get('pos', '') if meanings else '',
                        example_sentence=meanings[0].get('examples', [''])[0] if meanings and meanings[0].get('examples') else '',
                    )
                    st.success(f"「{word}」を単語帳に追加しました！")
                except Exception as e:
                    st.warning(f"保存エラー: {e}")


def show_progress():
    """学習記録（Supabaseから取得）"""
    
    st.markdown("### 📊 学習記録 / Progress")
    
    user = get_current_user()
    
    # --- Supabaseから統計を取得 ---
    stats = {'total': 0, 'mastered': 0, 'in_progress': 0, 'reviewed_today': 0}
    try:
        stats = get_vocabulary_stats(user['id'])
    except Exception:
        pass
    
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("学習単語数", f"{stats['total']}")
    with col2:
        st.metric("マスター済み", f"{stats['mastered']}")
    with col3:
        st.metric("学習中", f"{stats['in_progress']}")
    with col4:
        st.metric("今日の復習", f"{stats['reviewed_today']}")
    
    # --- 単語帳一覧 ---
    st.markdown("---")
    st.markdown("#### 📚 あなたの単語帳 / My Vocabulary")
    
    vocab_list = []
    try:
        vocab_list = get_student_vocabulary(user['id'], limit=50)
    except Exception:
        pass
    
    if vocab_list:
        for v in vocab_list[:20]:
            mastery = v.get('mastery_level', 0) or 0
            mastery_stars = "⭐" * min(mastery, 5)
            with st.expander(f"**{v.get('word', '')}** — {v.get('meaning', '')} {mastery_stars}"):
                st.caption(f"品詞: {v.get('pos', '-')} | 復習回数: {v.get('repetitions', 0)} | 追加元: {v.get('source_type', '-')}")
                if v.get('example_sentence'):
                    st.markdown(f"*{v['example_sentence']}*")
    else:
        st.info("まだ単語が追加されていません。「🔍 単語検索」で単語を検索し、単語帳に追加してみましょう！")
