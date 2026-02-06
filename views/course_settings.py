import streamlit as st
from utils.auth import get_current_user, require_auth

@require_auth
def show():
    user = get_current_user()
    
    st.markdown("## ⚙️ 科目設定")
    
    if st.button("← 教員ホームに戻る"):
        st.session_state['current_view'] = 'teacher_home'
        st.rerun()
    
    st.markdown("---")
    
    # 現在のクラス
    selected_class = st.session_state.get('selected_class', 'english_specific_a')
    classes = st.session_state.get('teacher_classes', {})
    
    if selected_class in classes:
        current_class = classes[selected_class]
        st.info(f"📚 **{current_class['name']}** の設定")
    
    # デモ用設定データ
    if 'course_settings' not in st.session_state:
        st.session_state.course_settings = {
            "english_specific_a": {
                "purpose": "アウトプット力（話す・書く）の向上",
                "modules": {
                    "speaking": {"enabled": True, "weight": 50},
                    "writing": {"enabled": True, "weight": 30},
                    "pronunciation": {"enabled": True, "weight": 20},
                    "listening": {"enabled": False, "weight": 0},
                    "reading": {"enabled": False, "weight": 0},
                    "vocabulary": {"enabled": True, "weight": 0},
                },
                "speaking_rubrics": get_default_speaking_rubrics(),
                "writing_rubrics": get_default_writing_rubrics(),
                "practice_menu": {},
                "grade_settings": {
                    "assignment_weight": 50,
                    "practice_weight": 20,
                    "final_test_weight": 20,
                    "participation_weight": 10,
                }
            }
        }
    
    settings = st.session_state.course_settings.get(selected_class, {})
    
    # タブで分類
    tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs([
        "📌 科目の目的", 
        "📦 モジュール設定", 
        "🗣️ Speaking評価基準",
        "✍️ Writing評価基準",
        "📋 練習メニュー", 
        "📊 成績配分"
    ])
    
    with tab1:
        show_purpose_settings(selected_class, settings)
    
    with tab2:
        show_module_settings(selected_class, settings)
    
    with tab3:
        show_speaking_rubrics(selected_class, settings)
    
    with tab4:
        show_writing_rubrics(selected_class, settings)
    
    with tab5:
        show_practice_menu_settings(selected_class, settings)
    
    with tab6:
        show_grade_settings(selected_class, settings)


def get_default_speaking_rubrics():
    """Speaking評価基準のデフォルト"""
    return {
        "reading_aloud": {
            "name": "音読 (Reading Aloud)",
            "criteria": {
                "pronunciation": {"name": "発音 (Pronunciation)", "weight": 40, "desc": "個々の音素の正確さ"},
                "fluency": {"name": "流暢さ (Fluency)", "weight": 30, "desc": "スムーズさ、ペース"},
                "intonation": {"name": "イントネーション", "weight": 20, "desc": "抑揚、強勢"},
                "completeness": {"name": "完成度", "weight": 10, "desc": "読み飛ばし、言い直しの少なさ"},
            }
        },
        "speech": {
            "name": "スピーチ (Speech/Presentation)",
            "criteria": {
                "content": {"name": "内容 (Content)", "weight": 25, "desc": "論理性、具体性、説得力"},
                "organization": {"name": "構成 (Organization)", "weight": 20, "desc": "導入・本論・結論の明確さ"},
                "pronunciation": {"name": "発音 (Pronunciation)", "weight": 20, "desc": "明瞭さ、理解しやすさ"},
                "fluency": {"name": "流暢さ (Fluency)", "weight": 15, "desc": "自然なペース、間の取り方"},
                "delivery": {"name": "デリバリー", "weight": 10, "desc": "アイコンタクト、声の大きさ"},
                "vocabulary": {"name": "語彙・表現", "weight": 10, "desc": "適切な語彙選択"},
            }
        },
        "conversation": {
            "name": "会話 (Conversation)",
            "criteria": {
                "comprehension": {"name": "理解力", "weight": 25, "desc": "相手の発言の理解"},
                "response": {"name": "応答", "weight": 25, "desc": "適切な返答、質問"},
                "pronunciation": {"name": "発音", "weight": 20, "desc": "明瞭さ"},
                "fluency": {"name": "流暢さ", "weight": 15, "desc": "自然なやり取り"},
                "vocabulary": {"name": "語彙・表現", "weight": 15, "desc": "多様な表現の使用"},
            }
        },
        "shadowing": {
            "name": "シャドーイング",
            "criteria": {
                "accuracy": {"name": "正確さ", "weight": 40, "desc": "元の音声との一致度"},
                "timing": {"name": "タイミング", "weight": 30, "desc": "遅れずについていく"},
                "intonation": {"name": "イントネーション", "weight": 30, "desc": "抑揚の再現"},
            }
        }
    }


def get_default_writing_rubrics():
    """Writing評価基準のデフォルト"""
    return {
        "essay": {
            "name": "エッセイ (Essay)",
            "criteria": {
                "content": {"name": "内容 (Content)", "weight": 30, "desc": "論点の明確さ、具体例、説得力"},
                "organization": {"name": "構成 (Organization)", "weight": 25, "desc": "段落構成、論理展開"},
                "grammar": {"name": "文法 (Grammar)", "weight": 20, "desc": "文法的正確さ"},
                "vocabulary": {"name": "語彙 (Vocabulary)", "weight": 15, "desc": "語彙の多様性、適切さ"},
                "mechanics": {"name": "表記", "weight": 10, "desc": "スペル、句読点"},
            }
        },
        "email": {
            "name": "メール (Email)",
            "criteria": {
                "appropriateness": {"name": "適切さ", "weight": 30, "desc": "場面・相手に応じた表現"},
                "content": {"name": "内容", "weight": 25, "desc": "必要な情報の網羅"},
                "format": {"name": "形式", "weight": 20, "desc": "メールの形式・構成"},
                "grammar": {"name": "文法", "weight": 15, "desc": "文法的正確さ"},
                "tone": {"name": "トーン", "weight": 10, "desc": "適切な丁寧さ"},
            }
        },
        "summary": {
            "name": "要約 (Summary)",
            "criteria": {
                "accuracy": {"name": "正確さ", "weight": 35, "desc": "元の内容の正確な把握"},
                "conciseness": {"name": "簡潔さ", "weight": 25, "desc": "無駄のない表現"},
                "organization": {"name": "構成", "weight": 20, "desc": "論理的なまとめ"},
                "language": {"name": "言語", "weight": 20, "desc": "文法・語彙の正確さ"},
            }
        },
        "free_writing": {
            "name": "自由作文",
            "criteria": {
                "content": {"name": "内容", "weight": 30, "desc": "アイデア、創造性"},
                "grammar": {"name": "文法", "weight": 30, "desc": "文法的正確さ"},
                "vocabulary": {"name": "語彙", "weight": 25, "desc": "語彙の適切さ"},
                "coherence": {"name": "一貫性", "weight": 15, "desc": "文章の流れ"},
            }
        }
    }


def show_speaking_rubrics(class_key, settings):
    """Speaking評価基準のカスタマイズ"""
    
    st.markdown("### 🗣️ Speaking評価基準")
    st.caption("課題タイプごとに評価の重み付けをカスタマイズできます")
    
    rubrics = settings.get("speaking_rubrics", get_default_speaking_rubrics())
    
    # 課題タイプ選択
    task_type = st.selectbox(
        "課題タイプを選択",
        list(rubrics.keys()),
        format_func=lambda x: rubrics[x]["name"]
    )
    
    st.markdown("---")
    
    current_rubric = rubrics[task_type]
    st.markdown(f"#### 📋 {current_rubric['name']} の評価基準")
    
    # プリセット選択
    col1, col2 = st.columns([3, 1])
    with col2:
        if st.button("🔄 デフォルトに戻す"):
            default = get_default_speaking_rubrics()
            rubrics[task_type] = default[task_type]
            st.session_state.course_settings[class_key]["speaking_rubrics"] = rubrics
            st.rerun()
    
    st.markdown("---")
    
    # 評価基準の編集
    new_criteria = {}
    total_weight = 0
    
    for key, criterion in current_rubric["criteria"].items():
        col1, col2, col3 = st.columns([3, 1, 1])
        
        with col1:
            st.markdown(f"**{criterion['name']}**")
            st.caption(criterion['desc'])
        
        with col2:
            weight = st.number_input(
                "配分%",
                min_value=0,
                max_value=100,
                value=criterion['weight'],
                key=f"speak_{task_type}_{key}",
                label_visibility="collapsed"
            )
        
        with col3:
            st.markdown(f"**{weight}%**")
        
        new_criteria[key] = {
            "name": criterion['name'],
            "weight": weight,
            "desc": criterion['desc']
        }
        total_weight += weight
    
    st.markdown("---")
    
    # 合計チェック
    if total_weight == 100:
        st.success(f"✅ 合計: {total_weight}%")
    else:
        st.error(f"❌ 合計: {total_weight}%（100%にしてください）")
    
    # カスタム基準の追加
    with st.expander("➕ 評価基準を追加"):
        new_name = st.text_input("基準名", placeholder="例: 創造性")
        new_desc = st.text_input("説明", placeholder="例: 独自の表現やアイデア")
        new_weight = st.number_input("配分%", 0, 100, 10, key="new_speak_weight")
        
        if st.button("追加", key="add_speak_criterion"):
            if new_name:
                new_key = new_name.lower().replace(" ", "_")
                new_criteria[new_key] = {
                    "name": new_name,
                    "weight": new_weight,
                    "desc": new_desc
                }
                st.success(f"「{new_name}」を追加しました")
    
    # 保存
    if st.button("Speaking評価基準を保存", type="primary"):
        rubrics[task_type]["criteria"] = new_criteria
        st.session_state.course_settings[class_key]["speaking_rubrics"] = rubrics
        st.success("✅ 保存しました")
    
    st.markdown("---")
    
    # プレビュー
    st.markdown("#### 👀 評価レポートプレビュー")
    st.caption("学生に表示される評価の例")
    
    preview_scores = {key: 75 + (hash(key) % 20) for key in new_criteria.keys()}
    
    for key, criterion in new_criteria.items():
        score = preview_scores[key]
        col1, col2, col3 = st.columns([3, 1, 1])
        with col1:
            st.markdown(f"{criterion['name']}")
        with col2:
            st.progress(score / 100)
        with col3:
            weighted = score * criterion['weight'] / 100
            st.markdown(f"{score}点 (×{criterion['weight']}% = {weighted:.1f})")
    
    total_score = sum(preview_scores[k] * new_criteria[k]['weight'] / 100 for k in new_criteria.keys())
    st.markdown(f"**総合スコア: {total_score:.1f}点**")


def show_writing_rubrics(class_key, settings):
    """Writing評価基準のカスタマイズ"""
    
    st.markdown("### ✍️ Writing評価基準")
    st.caption("課題タイプごとに評価の重み付けをカスタマイズできます")
    
    rubrics = settings.get("writing_rubrics", get_default_writing_rubrics())
    
    # 課題タイプ選択
    task_type = st.selectbox(
        "課題タイプを選択",
        list(rubrics.keys()),
        format_func=lambda x: rubrics[x]["name"],
        key="writing_task_type"
    )
    
    st.markdown("---")
    
    current_rubric = rubrics[task_type]
    st.markdown(f"#### 📋 {current_rubric['name']} の評価基準")
    
    col1, col2 = st.columns([3, 1])
    with col2:
        if st.button("🔄 デフォルトに戻す", key="reset_writing"):
            default = get_default_writing_rubrics()
            rubrics[task_type] = default[task_type]
            st.session_state.course_settings[class_key]["writing_rubrics"] = rubrics
            st.rerun()
    
    st.markdown("---")
    
    # 評価基準の編集
    new_criteria = {}
    total_weight = 0
    
    for key, criterion in current_rubric["criteria"].items():
        col1, col2, col3 = st.columns([3, 1, 1])
        
        with col1:
            st.markdown(f"**{criterion['name']}**")
            st.caption(criterion['desc'])
        
        with col2:
            weight = st.number_input(
                "配分%",
                min_value=0,
                max_value=100,
                value=criterion['weight'],
                key=f"write_{task_type}_{key}",
                label_visibility="collapsed"
            )
        
        with col3:
            st.markdown(f"**{weight}%**")
        
        new_criteria[key] = {
            "name": criterion['name'],
            "weight": weight,
            "desc": criterion['desc']
        }
        total_weight += weight
    
    st.markdown("---")
    
    if total_weight == 100:
        st.success(f"✅ 合計: {total_weight}%")
    else:
        st.error(f"❌ 合計: {total_weight}%（100%にしてください）")
    
    # カスタム基準の追加
    with st.expander("➕ 評価基準を追加"):
        new_name = st.text_input("基準名", placeholder="例: 引用の適切さ", key="new_write_name")
        new_desc = st.text_input("説明", placeholder="例: 出典の明記、引用形式", key="new_write_desc")
        new_weight = st.number_input("配分%", 0, 100, 10, key="new_write_weight")
        
        if st.button("追加", key="add_write_criterion"):
            if new_name:
                new_key = new_name.lower().replace(" ", "_")
                new_criteria[new_key] = {
                    "name": new_name,
                    "weight": new_weight,
                    "desc": new_desc
                }
                st.success(f"「{new_name}」を追加しました")
    
    if st.button("Writing評価基準を保存", type="primary", key="save_writing"):
        rubrics[task_type]["criteria"] = new_criteria
        st.session_state.course_settings[class_key]["writing_rubrics"] = rubrics
        st.success("✅ 保存しました")


def show_purpose_settings(class_key, settings):
    """科目の目的設定"""
    
    st.markdown("### 📌 科目の目的")
    
    purposes = [
        "アウトプット力（話す・書く）の向上",
        "インプット力（聞く・読む）の向上",
        "4技能バランス型",
        "試験対策（TOEFL/TOEIC）",
        "ビジネス英語",
        "アカデミック英語（論文・発表）"
    ]
    
    current_purpose = settings.get("purpose", purposes[0])
    
    selected_purpose = st.selectbox(
        "目的を選択",
        purposes,
        index=purposes.index(current_purpose) if current_purpose in purposes else 0
    )
    
    if st.button("目的を保存", type="primary"):
        st.session_state.course_settings[class_key]["purpose"] = selected_purpose
        st.success("✅ 保存しました")


def show_module_settings(class_key, settings):
    """モジュール設定"""
    
    st.markdown("### 📦 使用モジュール")
    
    modules = settings.get("modules", {})
    
    module_list = [
        {"key": "speaking", "name": "🗣️ スピーキング"},
        {"key": "writing", "name": "✍️ ライティング"},
        {"key": "pronunciation", "name": "🎤 発音矯正"},
        {"key": "listening", "name": "🎧 リスニング"},
        {"key": "reading", "name": "📖 リーディング"},
        {"key": "vocabulary", "name": "📚 語彙"},
    ]
    
    total_weight = 0
    new_modules = {}
    
    for mod in module_list:
        col1, col2, col3 = st.columns([3, 1, 1])
        mod_settings = modules.get(mod["key"], {"enabled": False, "weight": 0})
        
        with col1:
            enabled = st.checkbox(mod["name"], value=mod_settings.get("enabled", False), key=f"mod_{mod['key']}")
        with col2:
            weight = st.number_input("配分%", 0, 100, mod_settings.get("weight", 0), key=f"modw_{mod['key']}", label_visibility="collapsed") if enabled else 0
        with col3:
            if enabled and weight > 0:
                st.markdown(f"**{weight}%**")
        
        new_modules[mod["key"]] = {"enabled": enabled, "weight": weight}
        if enabled:
            total_weight += weight
    
    st.markdown("---")
    if total_weight > 0:
        if total_weight == 100:
            st.success(f"✅ 合計: {total_weight}%")
        else:
            st.warning(f"⚠️ 合計: {total_weight}%")
    
    if st.button("モジュール設定を保存", type="primary"):
        st.session_state.course_settings[class_key]["modules"] = new_modules
        st.success("✅ 保存しました")


def show_practice_menu_settings(class_key, settings):
    """練習メニュー設定"""
    
    st.markdown("### 📋 練習メニュー")
    
    practice_menu = settings.get("practice_menu", {})
    
    options = [
        {"key": "daily_reading", "name": "毎日10分の音読練習"},
        {"key": "weekly_speech", "name": "週1回のスピーチ提出"},
        {"key": "weekly_writing", "name": "週2回のライティング練習"},
        {"key": "listening_practice", "name": "毎日15分のリスニング"},
        {"key": "vocabulary_daily", "name": "毎日の単語学習（10語）"},
    ]
    
    new_menu = {}
    for opt in options:
        new_menu[opt["key"]] = st.checkbox(opt["name"], value=practice_menu.get(opt["key"], False), key=f"prac_{opt['key']}")
    
    if st.button("練習メニューを保存", type="primary"):
        st.session_state.course_settings[class_key]["practice_menu"] = new_menu
        st.success("✅ 保存しました")


def show_grade_settings(class_key, settings):
    """成績配分設定"""
    
    st.markdown("### 📊 成績配分")
    
    grade_settings = settings.get("grade_settings", {})
    
    col1, col2 = st.columns(2)
    with col1:
        assignment_weight = st.slider("課題スコア平均", 0, 100, grade_settings.get("assignment_weight", 50))
        practice_weight = st.slider("練習への取り組み", 0, 100, grade_settings.get("practice_weight", 20))
    with col2:
        final_test_weight = st.slider("最終テスト", 0, 100, grade_settings.get("final_test_weight", 20))
        participation_weight = st.slider("授業参加・その他", 0, 100, grade_settings.get("participation_weight", 10))
    
    total = assignment_weight + practice_weight + final_test_weight + participation_weight
    
    if total == 100:
        st.success(f"✅ 合計: {total}%")
    else:
        st.error(f"❌ 合計: {total}%")
    
    if st.button("成績配分を保存", type="primary"):
        st.session_state.course_settings[class_key]["grade_settings"] = {
            "assignment_weight": assignment_weight,
            "practice_weight": practice_weight,
            "final_test_weight": final_test_weight,
            "participation_weight": participation_weight,
        }
        st.success("✅ 保存しました")
