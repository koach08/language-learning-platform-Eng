import streamlit as st
from datetime import datetime
import json


# ===== オフライン基本辞書（API不要のフォールバック） =====
BASIC_DICTIONARY = {
    "the": {"meaning": "その", "pos": "article"},
    "a": {"meaning": "一つの", "pos": "article"},
    "is": {"meaning": "〜である", "pos": "verb"},
    "are": {"meaning": "〜である", "pos": "verb"},
    "was": {"meaning": "〜だった", "pos": "verb"},
    "have": {"meaning": "持つ", "pos": "verb"},
    "has": {"meaning": "持つ", "pos": "verb"},
    "important": {"meaning": "重要な", "pos": "adjective"},
    "significant": {"meaning": "重大な、意義のある", "pos": "adjective"},
    "however": {"meaning": "しかしながら", "pos": "adverb"},
    "therefore": {"meaning": "したがって", "pos": "adverb"},
    "although": {"meaning": "〜にもかかわらず", "pos": "conjunction"},
    "because": {"meaning": "なぜなら", "pos": "conjunction"},
    "environment": {"meaning": "環境", "pos": "noun"},
    "technology": {"meaning": "技術", "pos": "noun"},
    "education": {"meaning": "教育", "pos": "noun"},
    "government": {"meaning": "政府", "pos": "noun"},
    "development": {"meaning": "発展、開発", "pos": "noun"},
    "communication": {"meaning": "コミュニケーション、伝達", "pos": "noun"},
    "information": {"meaning": "情報", "pos": "noun"},
    "experience": {"meaning": "経験", "pos": "noun"},
    "opportunity": {"meaning": "機会", "pos": "noun"},
    "community": {"meaning": "地域社会、コミュニティ", "pos": "noun"},
    "research": {"meaning": "研究", "pos": "noun"},
    "university": {"meaning": "大学", "pos": "noun"},
    "society": {"meaning": "社会", "pos": "noun"},
    "challenge": {"meaning": "挑戦、課題", "pos": "noun"},
    "influence": {"meaning": "影響", "pos": "noun"},
    "sustainable": {"meaning": "持続可能な", "pos": "adjective"},
    "artificial": {"meaning": "人工の", "pos": "adjective"},
    "intelligence": {"meaning": "知能、情報", "pos": "noun"},
    "algorithm": {"meaning": "アルゴリズム", "pos": "noun"},
    "bias": {"meaning": "偏見、バイアス", "pos": "noun"},
    "privacy": {"meaning": "プライバシー", "pos": "noun"},
    "autonomy": {"meaning": "自律性", "pos": "noun"},
    "discrimination": {"meaning": "差別", "pos": "noun"},
    "accountability": {"meaning": "説明責任", "pos": "noun"},
    "surveillance": {"meaning": "監視", "pos": "noun"},
    "unprecedented": {"meaning": "前例のない", "pos": "adjective"},
    "sophisticated": {"meaning": "洗練された、高度な", "pos": "adjective"},
    "perpetuate": {"meaning": "永続させる", "pos": "verb"},
    "amplify": {"meaning": "増幅する", "pos": "verb"},
    "address": {"meaning": "対処する、住所", "pos": "verb/noun"},
    "implement": {"meaning": "実施する", "pos": "verb"},
    "reduce": {"meaning": "減らす", "pos": "verb"},
    "increase": {"meaning": "増加する", "pos": "verb"},
    "observe": {"meaning": "観察する", "pos": "verb"},
    "require": {"meaning": "必要とする", "pos": "verb"},
    "consider": {"meaning": "考慮する", "pos": "verb"},
    "establish": {"meaning": "確立する", "pos": "verb"},
    "achieve": {"meaning": "達成する", "pos": "verb"},
    "contribute": {"meaning": "貢献する", "pos": "verb"},
    "demonstrate": {"meaning": "実証する", "pos": "verb"},
    "maintain": {"meaning": "維持する", "pos": "verb"},
    "frequently": {"meaning": "頻繁に", "pos": "adverb"},
    "primarily": {"meaning": "主に", "pos": "adverb"},
    "particularly": {"meaning": "特に", "pos": "adverb"},
    "fundamentally": {"meaning": "根本的に", "pos": "adverb"},
    "equally": {"meaning": "等しく", "pos": "adverb"},
    "climate": {"meaning": "気候", "pos": "noun"},
    "temperature": {"meaning": "温度", "pos": "noun"},
    "fossil": {"meaning": "化石", "pos": "noun"},
    "emission": {"meaning": "排出", "pos": "noun"},
    "renewable": {"meaning": "再生可能な", "pos": "adjective"},
    "consequence": {"meaning": "結果、影響", "pos": "noun"},
    "implication": {"meaning": "影響、含意", "pos": "noun"},
    "framework": {"meaning": "枠組み", "pos": "noun"},
    "perspective": {"meaning": "視点", "pos": "noun"},
    "relevant": {"meaning": "関連のある", "pos": "adjective"},
    "crucial": {"meaning": "極めて重要な", "pos": "adjective"},
    "comprehensive": {"meaning": "包括的な", "pos": "adjective"},
    "essential": {"meaning": "不可欠な", "pos": "adjective"},
    "effective": {"meaning": "効果的な", "pos": "adjective"},
    "beneficial": {"meaning": "有益な", "pos": "adjective"},
}


def lookup_word_api(word):
    """Free Dictionary APIで単語を検索"""
    import urllib.request
    import urllib.error
    
    word = word.lower().strip()
    url = f"https://api.dictionaryapi.dev/api/v2/entries/en/{word}"
    
    try:
        req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
        with urllib.request.urlopen(req, timeout=5) as response:
            data = json.loads(response.read().decode())
        
        if data and isinstance(data, list):
            entry = data[0]
            
            result = {
                'word': entry.get('word', word),
                'phonetic': '',
                'audio_url': '',
                'meanings': [],
                'source': 'api'
            }
            
            # 発音記号
            if entry.get('phonetic'):
                result['phonetic'] = entry['phonetic']
            
            # 音声URL
            for phonetic in entry.get('phonetics', []):
                if phonetic.get('audio'):
                    result['audio_url'] = phonetic['audio']
                    if not result['phonetic'] and phonetic.get('text'):
                        result['phonetic'] = phonetic['text']
                    break
            
            # 意味
            for meaning in entry.get('meanings', []):
                pos = meaning.get('partOfSpeech', '')
                for definition in meaning.get('definitions', [])[:3]:
                    result['meanings'].append({
                        'pos': pos,
                        'definition': definition.get('definition', ''),
                        'example': definition.get('example', ''),
                        'synonyms': definition.get('synonyms', [])[:5]
                    })
            
            return result
    
    except (urllib.error.URLError, urllib.error.HTTPError, json.JSONDecodeError, Exception):
        pass
    
    return None


def lookup_word(word):
    """単語を検索（API → オフライン辞書のフォールバック）"""
    word_lower = word.lower().strip()
    
    # まずAPIを試す
    api_result = lookup_word_api(word_lower)
    if api_result and api_result['meanings']:
        return api_result
    
    # フォールバック：オフライン辞書
    if word_lower in BASIC_DICTIONARY:
        entry = BASIC_DICTIONARY[word_lower]
        return {
            'word': word_lower,
            'phonetic': '',
            'audio_url': '',
            'meanings': [{
                'pos': entry.get('pos', ''),
                'definition': entry.get('meaning', ''),
                'example': '',
                'synonyms': []
            }],
            'source': 'offline'
        }
    
    return None


# ===== 単語帳機能 =====

def get_word_book():
    """ユーザーの単語帳を取得"""
    user = st.session_state.get('user')
    if not user:
        return []
    
    user_key = user.get('student_id') or user.get('email') or 'unknown'
    key = f'word_book_{user_key}'
    
    if key not in st.session_state:
        st.session_state[key] = []
    
    return st.session_state[key]


def add_to_word_book(word, definition, pos='', example='', context='', source_module=''):
    """単語帳に追加"""
    word_book = get_word_book()
    
    # 重複チェック
    existing = [w for w in word_book if w['word'].lower() == word.lower()]
    if existing:
        return False, "既に単語帳に登録されています"
    
    entry = {
        'word': word.lower(),
        'definition': definition,
        'pos': pos,
        'example': example,
        'context': context,
        'source_module': source_module,
        'added_at': datetime.now().strftime("%Y-%m-%d %H:%M"),
        'review_count': 0,
        'correct_count': 0,
        'next_review': datetime.now().strftime("%Y-%m-%d"),
        'ease_factor': 2.5,
        'interval_days': 1,
        'mastered': False
    }
    
    word_book.append(entry)
    return True, "単語帳に追加しました！"


def remove_from_word_book(word):
    """単語帳から削除"""
    word_book = get_word_book()
    word_book[:] = [w for w in word_book if w['word'].lower() != word.lower()]


def is_in_word_book(word):
    """単語帳に登録済みか"""
    word_book = get_word_book()
    return any(w['word'].lower() == word.lower() for w in word_book)


# ===== UI表示関数 =====

def show_dictionary_popup(word_key="dict_word"):
    """辞書検索ポップアップUI"""
    
    word = st.text_input(
        "🔍 単語を検索 / Look up a word",
        placeholder="英単語を入力...",
        key=word_key
    )
    
    if word:
        with st.spinner("検索中..."):
            result = lookup_word(word)
        
        if result:
            show_word_result(result)
        else:
            st.warning(f"「{word}」が見つかりませんでした")


def show_word_result(result, show_add_button=True):
    """単語検索結果を表示"""
    
    word = result['word']
    
    # ヘッダー
    header = f"### 📖 {word}"
    if result.get('phonetic'):
        header += f"  `{result['phonetic']}`"
    st.markdown(header)
    
    # 音声再生
    if result.get('audio_url'):
        st.audio(result['audio_url'])
    
    # 意味
    for i, meaning in enumerate(result['meanings'][:5]):
        pos_label = f"*({meaning['pos']})*" if meaning['pos'] else ''
        st.markdown(f"**{i+1}.** {pos_label} {meaning['definition']}")
        
        if meaning.get('example'):
            st.caption(f"📝 {meaning['example']}")
        
        if meaning.get('synonyms'):
            st.caption(f"≈ {', '.join(meaning['synonyms'][:5])}")
    
    # 単語帳に追加
    if show_add_button:
        if is_in_word_book(word):
            st.success("✅ 単語帳に登録済み")
        else:
            if st.button(f"📝 単語帳に追加", key=f"add_{word}"):
                first_meaning = result['meanings'][0] if result['meanings'] else {}
                success, msg = add_to_word_book(
                    word=word,
                    definition=first_meaning.get('definition', ''),
                    pos=first_meaning.get('pos', ''),
                    example=first_meaning.get('example', ''),
                )
                if success:
                    st.success(f"✅ {msg}")
                else:
                    st.info(msg)


def show_clickable_text(text, key_prefix="clickable"):
    """クリック可能なテキスト表示（単語をクリックで辞書検索）"""
    import re
    
    words = re.findall(r'\b[a-zA-Z]+\b', text)
    unique_words = list(dict.fromkeys(words))  # 重複排除、順序維持
    
    # テキスト表示
    st.markdown(text)
    
    # 単語選択
    st.markdown("---")
    st.markdown("**📖 単語をタップして意味を確認:**")
    
    # 頻出単語を除外
    skip_words = {'the', 'a', 'an', 'is', 'are', 'was', 'were', 'be', 'been', 'being',
                  'have', 'has', 'had', 'do', 'does', 'did', 'will', 'would', 'could',
                  'should', 'may', 'might', 'shall', 'can', 'need', 'dare', 'ought',
                  'to', 'of', 'in', 'for', 'on', 'with', 'at', 'by', 'from', 'as',
                  'into', 'about', 'like', 'through', 'after', 'over', 'between',
                  'out', 'against', 'during', 'without', 'before', 'under', 'around',
                  'among', 'and', 'but', 'or', 'nor', 'not', 'so', 'yet', 'both',
                  'either', 'neither', 'each', 'every', 'all', 'both', 'few', 'more',
                  'most', 'other', 'some', 'such', 'no', 'only', 'own', 'same', 'than',
                  'too', 'very', 'just', 'also', 'now', 'here', 'there', 'then', 'when',
                  'where', 'why', 'how', 'what', 'which', 'who', 'whom', 'this', 'that',
                  'these', 'those', 'i', 'me', 'my', 'we', 'us', 'our', 'you', 'your',
                  'he', 'him', 'his', 'she', 'her', 'it', 'its', 'they', 'them', 'their',
                  'if', 'up', 'down', 'let', 'get', 'got', 'go', 'going', 'went', 'come',
                  'came', 'make', 'made', 'take', 'took', 'give', 'gave', 'say', 'said',
                  'tell', 'told', 'see', 'saw', 'know', 'knew', 'think', 'thought',
                  'much', 'many', 'well', 'back', 'even', 'still', 'new', 'old',
                  'first', 'last', 'long', 'great', 'little', 'right', 'big', 'small',
                  'one', 'two', 'three', 'four', 'five', 'six', 'seven', 'eight', 'nine', 'ten',
                  }
    
    content_words = [w for w in unique_words if w.lower() not in skip_words and len(w) > 2]
    
    if content_words:
        selected_word = st.selectbox(
            "単語を選択",
            [""] + content_words,
            key=f"{key_prefix}_select",
            format_func=lambda x: x if x else "-- 単語を選んでください --"
        )
        
        if selected_word:
            with st.spinner(f"「{selected_word}」を検索中..."):
                result = lookup_word(selected_word)
            
            if result:
                show_word_result(result)
            else:
                st.warning(f"「{selected_word}」が見つかりませんでした")


def show_word_book_summary():
    """単語帳サマリー（コンパクト版）"""
    word_book = get_word_book()
    
    if not word_book:
        return
    
    today = datetime.now().strftime("%Y-%m-%d")
    due_words = [w for w in word_book if w.get('next_review', '') <= today and not w.get('mastered')]
    
    if due_words:
        st.info(f"📝 **復習が必要な単語: {len(due_words)}語**")


def show_word_book_full():
    """単語帳フル表示"""
    word_book = get_word_book()
    
    st.markdown("### 📖 マイ単語帳 / My Word Book")
    
    if not word_book:
        st.info("まだ単語が登録されていません。テキストを読みながら単語を追加しましょう！")
        return
    
    st.metric("登録単語数", f"{len(word_book)}語")
    
    # フィルター
    filter_option = st.radio(
        "表示",
        ["すべて", "復習が必要", "習得済み"],
        horizontal=True
    )
    
    today = datetime.now().strftime("%Y-%m-%d")
    
    if filter_option == "復習が必要":
        filtered = [w for w in word_book if w.get('next_review', '') <= today and not w.get('mastered')]
    elif filter_option == "習得済み":
        filtered = [w for w in word_book if w.get('mastered')]
    else:
        filtered = word_book
    
    st.caption(f"{len(filtered)}語表示中")
    
    for i, entry in enumerate(filtered):
        with st.expander(f"📝 {entry['word']} - {entry['definition'][:40]}..."):
            if entry.get('pos'):
                st.caption(f"品詞: {entry['pos']}")
            st.markdown(f"**意味:** {entry['definition']}")
            if entry.get('example'):
                st.caption(f"例文: {entry['example']}")
            if entry.get('context'):
                st.caption(f"出典: {entry['context']}")
            
            col1, col2, col3 = st.columns(3)
            with col1:
                st.caption(f"復習回数: {entry.get('review_count', 0)}")
            with col2:
                st.caption(f"正答率: {entry.get('correct_count', 0)}/{entry.get('review_count', 0)}")
            with col3:
                if st.button("🗑️ 削除", key=f"del_wb_{i}"):
                    remove_from_word_book(entry['word'])
                    st.rerun()
