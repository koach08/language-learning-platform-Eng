import streamlit as st
import json


# ===== よく使う単語の発音記号 =====

COMMON_PHONETICS = {
    "the": "/ðə/",
    "this": "/ðɪs/",
    "that": "/ðæt/",
    "think": "/θɪŋk/",
    "through": "/θruː/",
    "three": "/θriː/",
    "they": "/ðeɪ/",
    "there": "/ðer/",
    "their": "/ðer/",
    "these": "/ðiːz/",
    "those": "/ðoʊz/",
    "though": "/ðoʊ/",
    "thought": "/θɔːt/",
    "than": "/ðæn/",
    "them": "/ðem/",
    "then": "/ðen/",
    "world": "/wɜːrld/",
    "work": "/wɜːrk/",
    "word": "/wɜːrd/",
    "would": "/wʊd/",
    "could": "/kʊd/",
    "should": "/ʃʊd/",
    "about": "/əˈbaʊt/",
    "important": "/ɪmˈpɔːrtənt/",
    "because": "/bɪˈkɔːz/",
    "different": "/ˈdɪfrənt/",
    "between": "/bɪˈtwiːn/",
    "another": "/əˈnʌðər/",
    "people": "/ˈpiːpl/",
    "country": "/ˈkʌntri/",
    "problem": "/ˈprɒbləm/",
    "question": "/ˈkwestʃən/",
    "government": "/ˈɡʌvərnmənt/",
    "environment": "/ɪnˈvaɪrənmənt/",
    "technology": "/tekˈnɒlədʒi/",
    "education": "/ˌedʒʊˈkeɪʃn/",
    "university": "/ˌjuːnɪˈvɜːrsəti/",
    "information": "/ˌɪnfərˈmeɪʃn/",
    "development": "/dɪˈveləpmənt/",
    "experience": "/ɪkˈspɪriəns/",
    "communicate": "/kəˈmjuːnɪkeɪt/",
    "comfortable": "/ˈkʌmftəbl/",
    "Wednesday": "/ˈwenzdeɪ/",
    "February": "/ˈfebrueri/",
    "schedule": "/ˈskedʒuːl/",
    "vegetable": "/ˈvedʒtəbl/",
    "temperature": "/ˈtemprətʃər/",
    "restaurant": "/ˈrestərɒnt/",
    "interesting": "/ˈɪntrəstɪŋ/",
    "necessary": "/ˈnesəseri/",
    "particularly": "/pərˈtɪkjələrli/",
    "pronunciation": "/prəˌnʌnsiˈeɪʃn/",
}

# 日本人学習者が苦手な音素ペア
DIFFICULT_SOUNDS = {
    'θ vs s': {
        'description': 'th音（無声）vs s音',
        'examples': [('think', 'sink'), ('three', 'see'), ('path', 'pass')],
        'tip': '舌先を上前歯に軽く当てて息を出す。sは舌を歯に当てない。',
    },
    'ð vs z': {
        'description': 'th音（有声）vs z音',
        'examples': [('this', 'zip'), ('that', 'zap'), ('breathe', 'breeze')],
        'tip': '舌先を上前歯に軽く当てて声を出す。',
    },
    'l vs r': {
        'description': 'L音 vs R音',
        'examples': [('light', 'right'), ('lead', 'read'), ('long', 'wrong')],
        'tip': 'L: 舌先を歯茎につける。R: 舌を丸めて歯茎に触れない。',
    },
    'æ vs ʌ': {
        'description': 'a音（cat）vs u音（cut）',
        'examples': [('bat', 'but'), ('cap', 'cup'), ('ran', 'run')],
        'tip': 'æ: 口を横に開く。ʌ: 口を自然に開く。',
    },
    'f vs h': {
        'description': 'F音 vs H音',
        'examples': [('fun', 'hun'), ('feet', 'heat'), ('fine', 'hind')],
        'tip': 'F: 上前歯を下唇に当てる。H: 口を開けて息を出す。',
    },
    'v vs b': {
        'description': 'V音 vs B音',
        'examples': [('van', 'ban'), ('vest', 'best'), ('very', 'berry')],
        'tip': 'V: 上前歯を下唇に当てて振動。B: 両唇を閉じて破裂。',
    },
    'ɪ vs iː': {
        'description': '短いi vs 長いi',
        'examples': [('ship', 'sheep'), ('sit', 'seat'), ('bit', 'beat')],
        'tip': 'ɪ: 短く軽く。iː: 口を横に引いて長く。',
    },
}


def get_phonetic(word):
    """単語の発音記号を取得"""
    word_lower = word.lower().strip()
    
    if word_lower in COMMON_PHONETICS:
        return COMMON_PHONETICS[word_lower]
    
    # APIから取得を試行
    try:
        from utils.dictionary import lookup_word_api
        result = lookup_word_api(word_lower)
        if result and result.get('phonetic'):
            return result['phonetic']
    except Exception:
        pass
    
    return None


def show_phonetic_helper():
    """発音ヘルパーUI"""
    
    st.markdown("### 🔊 発音ヘルパー / Pronunciation Helper")
    
    tab1, tab2 = st.tabs(["🔍 発音記号を調べる", "🎯 苦手な音の練習"])
    
    with tab1:
        word = st.text_input("単語を入力", placeholder="例: pronunciation", key="phonetic_word")
        
        if word:
            phonetic = get_phonetic(word)
            if phonetic:
                st.markdown(f"### {word}")
                st.markdown(f"## `{phonetic}`")
                
                # 音声
                try:
                    from utils.dictionary import lookup_word_api
                    result = lookup_word_api(word)
                    if result and result.get('audio_url'):
                        st.audio(result['audio_url'])
                except Exception:
                    pass
            else:
                st.warning(f"「{word}」の発音記号が見つかりませんでした")
    
    with tab2:
        st.markdown("日本人学習者が苦手とする音のペアを練習しましょう。")
        
        for pair_name, pair_data in DIFFICULT_SOUNDS.items():
            with st.expander(f"🎯 {pair_data['description']}"):
                st.markdown(f"**練習のコツ:** {pair_data['tip']}")
                
                st.markdown("**ミニマルペア:**")
                for word1, word2 in pair_data['examples']:
                    p1 = COMMON_PHONETICS.get(word1, '')
                    p2 = COMMON_PHONETICS.get(word2, '')
                    st.markdown(f"- **{word1}** {p1} ↔ **{word2}** {p2}")
