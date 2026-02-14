import streamlit as st
from datetime import datetime, timedelta
from utils.dictionary import get_word_book
import random


def get_due_words():
    """復習が必要な単語を取得"""
    word_book = get_word_book()
    today = datetime.now().strftime("%Y-%m-%d")
    return [w for w in word_book if w.get('next_review', '') <= today and not w.get('mastered')]


def get_all_reviewable():
    """復習可能な全単語（習得済み除く）"""
    word_book = get_word_book()
    return [w for w in word_book if not w.get('mastered')]


def update_srs(word_entry, quality):
    """
    SM-2アルゴリズムでSRS更新
    quality: 0-5 (0=完全に忘れた, 3=難しいが正解, 5=簡単)
    """
    ef = word_entry.get('ease_factor', 2.5)
    interval = word_entry.get('interval_days', 1)
    review_count = word_entry.get('review_count', 0)
    correct_count = word_entry.get('correct_count', 0)
    
    review_count += 1
    
    if quality >= 3:
        correct_count += 1
        if review_count == 1:
            interval = 1
        elif review_count == 2:
            interval = 3
        else:
            interval = int(interval * ef)
        
        ef = ef + (0.1 - (5 - quality) * (0.08 + (5 - quality) * 0.02))
        if ef < 1.3:
            ef = 1.3
    else:
        interval = 1
    
    # 最大90日
    interval = min(interval, 90)
    
    next_review = (datetime.now() + timedelta(days=interval)).strftime("%Y-%m-%d")
    
    word_entry['ease_factor'] = ef
    word_entry['interval_days'] = interval
    word_entry['review_count'] = review_count
    word_entry['correct_count'] = correct_count
    word_entry['next_review'] = next_review
    
    # 習得判定（正答率80%以上 & 5回以上 & interval 30日以上）
    if review_count >= 5 and (correct_count / review_count) >= 0.8 and interval >= 30:
        word_entry['mastered'] = True


def show_srs_review():
    """SRS復習セッション"""
    
    st.markdown("### 🧠 スペースドリピティション / Spaced Repetition")
    st.caption("忘却曲線に基づいて最適なタイミングで復習します")
    
    due_words = get_due_words()
    all_words = get_all_reviewable()
    
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("今日の復習", f"{len(due_words)}語")
    with col2:
        st.metric("学習中", f"{len(all_words)}語")
    with col3:
        mastered = len([w for w in get_word_book() if w.get('mastered')])
        st.metric("習得済み", f"{mastered}語")
    
    if not due_words and not all_words:
        st.info("📖 単語帳に単語を追加してから復習を始めましょう！\n\nReading や辞書検索から単語を追加できます。")
        return
    
    if not due_words:
        st.success("✅ 今日の復習は完了です！")
        if st.button("🔄 全単語から練習する"):
            st.session_state['srs_force_review'] = True
            st.rerun()
        
        if not st.session_state.get('srs_force_review'):
            return
        else:
            due_words = all_words
    
    st.markdown("---")
    
    # 復習モード選択
    mode = st.radio(
        "復習モード",
        ["flashcard", "quiz", "typing"],
        format_func=lambda x: {
            "flashcard": "📇 フラッシュカード",
            "quiz": "📝 4択クイズ",
            "typing": "⌨️ タイピング"
        }[x],
        horizontal=True
    )
    
    if mode == "flashcard":
        show_flashcard_review(due_words)
    elif mode == "quiz":
        show_quiz_review(due_words)
    else:
        show_typing_review(due_words)


def show_flashcard_review(words):
    """フラッシュカード復習"""
    
    if 'srs_index' not in st.session_state:
        st.session_state.srs_index = 0
        st.session_state.srs_shuffled = random.sample(words, len(words))
        st.session_state.srs_revealed = False
        st.session_state.srs_session_results = []
    
    shuffled = st.session_state.srs_shuffled
    idx = st.session_state.srs_index
    
    if idx >= len(shuffled):
        show_session_results()
        return
    
    current = shuffled[idx]
    
    st.markdown(f"**カード {idx + 1} / {len(shuffled)}**")
    st.progress((idx) / len(shuffled))
    
    # カード表示
    st.markdown(f"""
    <div style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); 
                padding: 40px; border-radius: 15px; text-align: center; margin: 20px 0;">
        <h1 style="color: white; margin: 0; font-size: 2.5em;">{current['word']}</h1>
        <p style="color: rgba(255,255,255,0.7); margin-top: 10px;">{current.get('pos', '')}</p>
    </div>
    """, unsafe_allow_html=True)
    
    if not st.session_state.srs_revealed:
        if st.button("👁️ 意味を表示 / Show Meaning", use_container_width=True, type="primary"):
            st.session_state.srs_revealed = True
            st.rerun()
    else:
        st.markdown(f"""
        <div style="background: #f0f2f6; padding: 20px; border-radius: 10px; text-align: center; margin: 10px 0;">
            <h3 style="margin: 0;">{current.get('definition', '')}</h3>
        </div>
        """, unsafe_allow_html=True)
        
        if current.get('example'):
            st.caption(f"📝 {current['example']}")
        
        st.markdown("**どのぐらい覚えていましたか？**")
        
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            if st.button("😰 忘れた", use_container_width=True):
                record_flashcard_result(current, 1)
        with col2:
            if st.button("😐 難しい", use_container_width=True):
                record_flashcard_result(current, 3)
        with col3:
            if st.button("😊 覚えてた", use_container_width=True):
                record_flashcard_result(current, 4)
        with col4:
            if st.button("😎 簡単！", use_container_width=True):
                record_flashcard_result(current, 5)


def record_flashcard_result(word_entry, quality):
    """フラッシュカード結果を記録"""
    update_srs(word_entry, quality)
    st.session_state.srs_session_results.append({
        'word': word_entry['word'],
        'quality': quality
    })
    st.session_state.srs_index += 1
    st.session_state.srs_revealed = False
    st.rerun()


def show_quiz_review(words):
    """4択クイズ復習"""
    
    if 'srs_quiz_index' not in st.session_state:
        st.session_state.srs_quiz_index = 0
        st.session_state.srs_quiz_words = random.sample(words, min(len(words), 10))
        st.session_state.srs_quiz_score = 0
        st.session_state.srs_quiz_answered = False
        st.session_state.srs_quiz_selected = None
    
    quiz_words = st.session_state.srs_quiz_words
    idx = st.session_state.srs_quiz_index
    
    if idx >= len(quiz_words):
        score = st.session_state.srs_quiz_score
        total = len(quiz_words)
        pct = (score / total * 100) if total > 0 else 0
        
        st.markdown(f"### 🎯 結果: {score}/{total} ({pct:.0f}%)")
        
        if pct >= 80:
            st.success("素晴らしい！🎉")
        elif pct >= 60:
            st.info("よく頑張りました！👍")
        else:
            st.warning("もう少し復習しましょう 💪")
        
        if st.button("🔄 もう一度"):
            for key in ['srs_quiz_index', 'srs_quiz_words', 'srs_quiz_score', 'srs_quiz_answered', 'srs_quiz_selected']:
                if key in st.session_state:
                    del st.session_state[key]
            st.rerun()
        return
    
    current = quiz_words[idx]
    
    st.markdown(f"**問題 {idx + 1} / {len(quiz_words)}**")
    st.progress(idx / len(quiz_words))
    
    st.markdown(f"### 📝 「{current['word']}」の意味は？")
    
    # 選択肢を生成
    all_book = get_word_book()
    other_words = [w for w in all_book if w['word'] != current['word'] and w.get('definition')]
    
    if len(other_words) >= 3:
        distractors = random.sample(other_words, 3)
        options = [current['definition']] + [d['definition'] for d in distractors]
    else:
        # 単語帳に選択肢が足りない場合のフォールバック
        fallback_options = ["動く、移動する", "考える、思考する", "作る、創造する"]
        options = [current['definition']] + fallback_options[:3]
    
    random.shuffle(options)
    
    if not st.session_state.srs_quiz_answered:
        for i, opt in enumerate(options):
            if st.button(opt, key=f"quiz_opt_{idx}_{i}", use_container_width=True):
                st.session_state.srs_quiz_selected = opt
                st.session_state.srs_quiz_answered = True
                
                if opt == current['definition']:
                    st.session_state.srs_quiz_score += 1
                    update_srs(current, 4)
                else:
                    update_srs(current, 1)
                st.rerun()
    else:
        selected = st.session_state.srs_quiz_selected
        correct = current['definition']
        
        if selected == correct:
            st.success(f"✅ 正解！ - {correct}")
        else:
            st.error(f"❌ 不正解 - 正解: {correct}")
        
        if st.button("次の問題 →", type="primary"):
            st.session_state.srs_quiz_index += 1
            st.session_state.srs_quiz_answered = False
            st.session_state.srs_quiz_selected = None
            st.rerun()


def show_typing_review(words):
    """タイピング復習（意味→英単語）"""
    
    if 'srs_type_index' not in st.session_state:
        st.session_state.srs_type_index = 0
        st.session_state.srs_type_words = random.sample(words, min(len(words), 10))
        st.session_state.srs_type_score = 0
        st.session_state.srs_type_checked = False
    
    type_words = st.session_state.srs_type_words
    idx = st.session_state.srs_type_index
    
    if idx >= len(type_words):
        score = st.session_state.srs_type_score
        total = len(type_words)
        pct = (score / total * 100) if total > 0 else 0
        
        st.markdown(f"### 🎯 結果: {score}/{total} ({pct:.0f}%)")
        
        if pct >= 80:
            st.success("素晴らしい！🎉")
        elif pct >= 60:
            st.info("よく頑張りました！👍")
        else:
            st.warning("もう少し復習しましょう 💪")
        
        if st.button("🔄 もう一度"):
            for key in ['srs_type_index', 'srs_type_words', 'srs_type_score', 'srs_type_checked']:
                if key in st.session_state:
                    del st.session_state[key]
            st.rerun()
        return
    
    current = type_words[idx]
    
    st.markdown(f"**問題 {idx + 1} / {len(type_words)}**")
    st.progress(idx / len(type_words))
    
    st.markdown(f"### この意味の英単語を入力してください:")
    st.markdown(f"**{current.get('definition', '')}**")
    if current.get('pos'):
        st.caption(f"品詞: {current['pos']}")
    
    answer = st.text_input("英単語", key=f"type_answer_{idx}", placeholder="英単語を入力...")
    
    if not st.session_state.srs_type_checked:
        if st.button("✅ 回答する", type="primary"):
            st.session_state.srs_type_checked = True
            if answer.lower().strip() == current['word'].lower().strip():
                st.session_state.srs_type_score += 1
                update_srs(current, 5)
            else:
                update_srs(current, 1)
            st.rerun()
    else:
        if answer.lower().strip() == current['word'].lower().strip():
            st.success(f"✅ 正解！ **{current['word']}**")
        else:
            st.error(f"❌ 不正解 - 正解: **{current['word']}** (あなたの回答: {answer})")
        
        if st.button("次の問題 →", type="primary"):
            st.session_state.srs_type_index += 1
            st.session_state.srs_type_checked = False
            st.rerun()


def show_session_results():
    """セッション結果表示"""
    results = st.session_state.get('srs_session_results', [])
    
    st.markdown("### 🎉 復習完了！")
    
    if results:
        good = len([r for r in results if r['quality'] >= 3])
        total = len(results)
        pct = (good / total * 100) if total > 0 else 0
        
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("復習した単語", f"{total}語")
        with col2:
            st.metric("覚えていた", f"{good}語")
        with col3:
            st.metric("正答率", f"{pct:.0f}%")
        
        # XP付与
        try:
            from utils.gamification import award_xp, update_stat
            xp = award_xp('vocabulary_review', extra_xp=good * 2)
            update_stat('words_learned', total)
            if xp > 0:
                st.success(f"✨ +{xp} XP 獲得！")
        except Exception:
            pass
    
    if st.button("🔄 もう一度復習する"):
        for key in ['srs_index', 'srs_shuffled', 'srs_revealed', 'srs_session_results', 'srs_force_review']:
            if key in st.session_state:
                del st.session_state[key]
        st.rerun()
