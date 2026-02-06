import streamlit as st


# ===== CEFR レベル定義 =====

CEFR_LEVELS = {
    'A1': {
        'name': 'Beginner',
        'vocab_range': '500-1000',
        'sentence_length': 'short (5-8 words)',
        'grammar': 'simple present, simple past, basic questions',
        'topics': 'self, family, daily routines, food, weather',
        'wpm_target': 80,
        'word_count_range': (50, 100),
    },
    'A2': {
        'name': 'Elementary',
        'vocab_range': '1000-2000',
        'sentence_length': 'short to medium (8-12 words)',
        'grammar': 'present continuous, future (will/going to), comparatives',
        'topics': 'hobbies, travel, shopping, directions, health',
        'wpm_target': 100,
        'word_count_range': (80, 150),
    },
    'B1': {
        'name': 'Intermediate',
        'vocab_range': '2000-4000',
        'sentence_length': 'medium (10-15 words)',
        'grammar': 'present perfect, conditionals (1st/2nd), passive voice, relative clauses',
        'topics': 'work, education, technology, environment, culture',
        'wpm_target': 130,
        'word_count_range': (120, 250),
    },
    'B2': {
        'name': 'Upper-Intermediate',
        'vocab_range': '4000-8000',
        'sentence_length': 'medium to long (12-20 words)',
        'grammar': 'all conditionals, reported speech, complex passives, subjunctive',
        'topics': 'society, politics, science, philosophy, media',
        'wpm_target': 160,
        'word_count_range': (200, 400),
    },
    'C1': {
        'name': 'Advanced',
        'vocab_range': '8000-15000',
        'sentence_length': 'long and complex (15-25 words)',
        'grammar': 'inversion, cleft sentences, mixed conditionals, advanced modals',
        'topics': 'academic research, ethics, global issues, abstract concepts',
        'wpm_target': 200,
        'word_count_range': (300, 600),
    },
}


def get_student_level():
    """学生の現在のCEFRレベルを取得"""
    try:
        from utils.analytics import get_analytics_data, estimate_cefr
        data = get_analytics_data()
        
        all_scores = []
        for key in ['speaking_scores', 'writing_scores', 'reading_scores', 'vocabulary_scores', 'listening_scores']:
            all_scores.extend([s['score'] for s in data.get(key, [])])
        
        if all_scores:
            recent = all_scores[-20:]
            avg = sum(recent) / len(recent)
            return estimate_cefr(avg)
    except Exception:
        pass
    
    return 'A2'  # デフォルト


def get_target_level(current_level='A2'):
    """i+1レベルを計算"""
    levels = ['A1', 'A2', 'B1', 'B2', 'C1']
    idx = levels.index(current_level) if current_level in levels else 1
    
    # i+1: 現在レベルの少し上
    target_idx = min(idx + 1, len(levels) - 1)
    return levels[target_idx]


def get_level_prompt(level, content_type='reading'):
    """レベルに応じたプロンプト指示を生成"""
    config = CEFR_LEVELS.get(level, CEFR_LEVELS['A2'])
    
    prompt = f"""
Target CEFR Level: {level} ({config['name']})
Vocabulary Range: {config['vocab_range']} words
Sentence Length: {config['sentence_length']}
Grammar Structures: {config['grammar']}
Suitable Topics: {config['topics']}
"""
    
    if content_type == 'reading':
        word_range = config['word_count_range']
        prompt += f"Article Length: {word_range[0]}-{word_range[1]} words\n"
        prompt += "Include context clues for difficult vocabulary.\n"
    
    elif content_type == 'speaking':
        prompt += f"Speaking pace target: {config['wpm_target']} WPM\n"
        prompt += "Use natural conversational patterns appropriate for this level.\n"
    
    elif content_type == 'writing':
        prompt += "Provide writing prompts appropriate for this level.\n"
        prompt += "Include model phrases and sentence starters.\n"
    
    elif content_type == 'listening':
        prompt += f"Speaking rate: {config['wpm_target']} WPM\n"
        prompt += "Clear pronunciation with natural but not too fast delivery.\n"
    
    return prompt


def get_adaptive_prompt(content_type='reading', topic=''):
    """適応型プロンプトを生成（学生レベル自動判定）"""
    current = get_student_level()
    target = get_target_level(current)
    
    level_prompt = get_level_prompt(target, content_type)
    
    adaptive_prompt = f"""
The student's current estimated level is {current}.
Generate content at level {target} (slightly above current level for optimal learning - i+1 hypothesis).

{level_prompt}

IMPORTANT: 
- The content should be challenging but comprehensible.
- Include 3-5 words that are slightly above the student's level (with context clues).
- Avoid making it too easy or too difficult.
"""
    
    if topic:
        adaptive_prompt += f"\nTopic: {topic}\n"
    
    return adaptive_prompt, current, target


def show_level_indicator():
    """レベルインジケーター表示"""
    current = get_student_level()
    target = get_target_level(current)
    config = CEFR_LEVELS.get(current, CEFR_LEVELS['A2'])
    
    st.caption(f"📊 あなたのレベル: **{current}** ({config['name']}) → 教材レベル: **{target}**")


def show_level_selector(default=None):
    """レベル手動選択（オーバーライド用）"""
    current = default or get_student_level()
    levels = list(CEFR_LEVELS.keys())
    
    idx = levels.index(current) if current in levels else 1
    
    selected = st.select_slider(
        "レベル調整",
        options=levels,
        value=levels[idx],
        format_func=lambda x: f"{x} ({CEFR_LEVELS[x]['name']})"
    )
    
    return selected
