"""
Course Settings - 教員カスタマイズ機能
======================================
科目設定を course_settings 専用テーブルに永続化。

テーブル構造 (course_settings):
- purpose          TEXT     科目の目的
- modules          JSONB    モジュールON/OFF・配分
- speaking_rubrics JSONB    Speaking評価基準（タスクタイプ別）
- writing_rubrics  JSONB    Writing評価基準（タスクタイプ別）
- practice_menu    JSONB    練習メニュー設定
- grade_settings   JSONB    成績配分
"""

import streamlit as st
from utils.auth import get_current_user, require_auth
from utils.database import (
    get_course_settings,
    upsert_course_settings,
    update_course_settings_field,
)


# ============================================================
# デフォルト値
# ============================================================

DEFAULT_PURPOSE = "アウトプット力（話す・書く）の向上"

DEFAULT_MODULES = {
    "speaking": {"enabled": True, "weight": 50},
    "writing": {"enabled": True, "weight": 30},
    "pronunciation": {"enabled": True, "weight": 20},
    "listening": {"enabled": False, "weight": 0},
    "reading": {"enabled": False, "weight": 0},
    "vocabulary": {"enabled": True, "weight": 0},
}

DEFAULT_GRADE_SETTINGS = {
    "assignment_weight": 50,
    "practice_weight": 20,
    "final_test_weight": 20,
    "participation_weight": 10,
}


def get_default_speaking_rubrics() -> dict:
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


def get_default_writing_rubrics() -> dict:
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


# ============================================================
# ヘルパー: DBからロードしてデフォルトとマージ
# ============================================================

def _load_settings(course_id: str) -> dict:
    """DBから設定を取得し、未設定項目にはデフォルトを適用"""
    row = get_course_settings(course_id)
    if row is None:
        return {
            "purpose": DEFAULT_PURPOSE,
            "modules": DEFAULT_MODULES,
            "speaking_rubrics": get_default_speaking_rubrics(),
            "writing_rubrics": get_default_writing_rubrics(),
            "practice_menu": {},
            "grade_settings": DEFAULT_GRADE_SETTINGS,
        }
    return {
        "purpose": row.get("purpose") or DEFAULT_PURPOSE,
        "modules": row.get("modules") or DEFAULT_MODULES,
        "speaking_rubrics": row.get("speaking_rubrics") or get_default_speaking_rubrics(),
        "writing_rubrics": row.get("writing_rubrics") or get_default_writing_rubrics(),
        "practice_menu": row.get("practice_menu") or {},
        "grade_settings": row.get("grade_settings") or DEFAULT_GRADE_SETTINGS,
    }


# ============================================================
# メインページ
# ============================================================

@require_auth
def show():
    user = get_current_user()

    st.markdown("## ⚙️ 科目設定")

    if st.button("← 教員ホームに戻る"):
        st.session_state['current_view'] = 'teacher_home'
        st.rerun()

    st.markdown("---")

    # コース選択
    course_id = st.session_state.get('selected_course_id')
    course_name = st.session_state.get('selected_course_name', '')

    if not course_id:
        st.warning("コースが選択されていません。教員ホームからコースを選択してください。")
        return

    st.info(f"📚 **{course_name}** の設定")

    # DBから設定をロード
    settings = _load_settings(course_id)

    # タブ
    tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs([
        "📌 科目の目的",
        "📦 モジュール設定",
        "🗣️ Speaking評価基準",
        "✍️ Writing評価基準",
        "📋 練習メニュー",
        "📊 成績配分",
    ])

    with tab1:
        _tab_purpose(course_id, settings)
    with tab2:
        _tab_modules(course_id, settings)
    with tab3:
        _tab_rubrics(course_id, settings, skill="speaking")
    with tab4:
        _tab_rubrics(course_id, settings, skill="writing")
    with tab5:
        _tab_practice_menu(course_id, settings)
    with tab6:
        _tab_grade(course_id, settings)


# ============================================================
# Tab 1: 科目の目的
# ============================================================

def _tab_purpose(course_id: str, settings: dict):
    st.markdown("### 📌 科目の目的")

    purposes = [
        "アウトプット力（話す・書く）の向上",
        "インプット力（聞く・読む）の向上",
        "4技能バランス型",
        "試験対策（TOEFL/TOEIC）",
        "ビジネス英語",
        "アカデミック英語（論文・発表）",
    ]

    current = settings["purpose"]
    idx = purposes.index(current) if current in purposes else 0
    selected = st.selectbox("目的を選択", purposes, index=idx)

    if st.button("目的を保存", type="primary", key="save_purpose"):
        _save(course_id, "purpose", selected)


# ============================================================
# Tab 2: モジュール設定
# ============================================================

def _tab_modules(course_id: str, settings: dict):
    st.markdown("### 📦 使用モジュール")

    modules = settings["modules"]
    module_defs = [
        ("speaking", "🗣️ スピーキング"),
        ("writing", "✍️ ライティング"),
        ("pronunciation", "🎤 発音矯正"),
        ("listening", "🎧 リスニング"),
        ("reading", "📖 リーディング"),
        ("vocabulary", "📚 語彙"),
    ]

    total_weight = 0
    new_modules = {}

    for key, label in module_defs:
        mod = modules.get(key, {"enabled": False, "weight": 0})
        col1, col2, col3 = st.columns([3, 1, 1])

        with col1:
            enabled = st.checkbox(label, value=mod.get("enabled", False), key=f"mod_{key}")
        with col2:
            weight = (
                st.number_input("配分%", 0, 100, mod.get("weight", 0),
                                key=f"modw_{key}", label_visibility="collapsed")
                if enabled else 0
            )
        with col3:
            if enabled and weight > 0:
                st.markdown(f"**{weight}%**")

        new_modules[key] = {"enabled": enabled, "weight": weight}
        if enabled:
            total_weight += weight

    st.markdown("---")
    if total_weight > 0:
        if total_weight == 100:
            st.success(f"✅ 合計: {total_weight}%")
        else:
            st.warning(f"⚠️ 合計: {total_weight}%")

    if st.button("モジュール設定を保存", type="primary", key="save_modules"):
        _save(course_id, "modules", new_modules)


# ============================================================
# Tab 3 & 4: 評価基準（Speaking / Writing 共通ロジック）
# ============================================================

def _tab_rubrics(course_id: str, settings: dict, skill: str):
    """Speaking / Writing 評価基準の共通UI
    
    skill: "speaking" or "writing"
    """
    is_speaking = (skill == "speaking")
    icon = "🗣️" if is_speaking else "✍️"
    label = "Speaking" if is_speaking else "Writing"
    field = "speaking_rubrics" if is_speaking else "writing_rubrics"
    defaults_fn = get_default_speaking_rubrics if is_speaking else get_default_writing_rubrics

    st.markdown(f"### {icon} {label}評価基準")
    st.caption("課題タイプごとに評価の重み付けをカスタマイズできます")

    rubrics = settings[field]

    # 課題タイプ選択
    task_type = st.selectbox(
        "課題タイプを選択",
        list(rubrics.keys()),
        format_func=lambda x: rubrics[x]["name"],
        key=f"{skill}_task_type",
    )

    st.markdown("---")
    current_rubric = rubrics[task_type]
    st.markdown(f"#### 📋 {current_rubric['name']} の評価基準")

    # デフォルトに戻す
    col_l, col_r = st.columns([3, 1])
    with col_r:
        if st.button("🔄 デフォルトに戻す", key=f"reset_{skill}"):
            defaults = defaults_fn()
            rubrics[task_type] = defaults[task_type]
            _save(course_id, field, rubrics)
            st.rerun()

    st.markdown("---")

    # 評価基準の編集
    new_criteria = {}
    total_weight = 0

    for key, criterion in current_rubric["criteria"].items():
        c1, c2, c3 = st.columns([3, 1, 1])
        with c1:
            st.markdown(f"**{criterion['name']}**")
            st.caption(criterion['desc'])
        with c2:
            weight = st.number_input(
                "配分%", 0, 100, criterion['weight'],
                key=f"{skill}_{task_type}_{key}",
                label_visibility="collapsed",
            )
        with c3:
            st.markdown(f"**{weight}%**")

        new_criteria[key] = {
            "name": criterion['name'],
            "weight": weight,
            "desc": criterion['desc'],
        }
        total_weight += weight

    # 基準の削除UI
    if len(new_criteria) > 1:
        with st.expander("🗑️ 評価基準を削除"):
            del_key = st.selectbox(
                "削除する基準を選択",
                list(new_criteria.keys()),
                format_func=lambda k: new_criteria[k]["name"],
                key=f"del_{skill}_{task_type}",
            )
            if st.button("この基準を削除", key=f"delbtn_{skill}_{task_type}"):
                del new_criteria[del_key]
                total_weight = sum(c["weight"] for c in new_criteria.values())
                st.success(f"「{rubrics[task_type]['criteria'][del_key]['name']}」を削除しました（保存してください）")

    st.markdown("---")

    # 合計チェック
    if total_weight == 100:
        st.success(f"✅ 合計: {total_weight}%")
    else:
        st.error(f"❌ 合計: {total_weight}%（100%にしてください）")

    # カスタム基準の追加
    with st.expander("➕ 評価基準を追加"):
        new_name = st.text_input("基準名", placeholder="例: 創造性", key=f"new_{skill}_name")
        new_desc = st.text_input("説明", placeholder="例: 独自の表現やアイデア", key=f"new_{skill}_desc")
        new_weight = st.number_input("配分%", 0, 100, 10, key=f"new_{skill}_weight")

        if st.button("追加", key=f"add_{skill}_criterion"):
            if new_name:
                new_key = new_name.lower().replace(" ", "_").replace("　", "_")
                if new_key in new_criteria:
                    st.warning("同名の基準が既に存在します")
                else:
                    new_criteria[new_key] = {
                        "name": new_name,
                        "weight": new_weight,
                        "desc": new_desc,
                    }
                    st.success(f"「{new_name}」を追加しました（保存ボタンを押してください）")
            else:
                st.warning("基準名を入力してください")

    # 保存
    if st.button(f"{label}評価基準を保存", type="primary", key=f"save_{skill}"):
        rubrics[task_type]["criteria"] = new_criteria
        _save(course_id, field, rubrics)

    st.markdown("---")

    # プレビュー
    _rubric_preview(new_criteria)


def _rubric_preview(criteria: dict):
    """評価レポートのプレビュー表示"""
    st.markdown("#### 👀 評価レポートプレビュー")
    st.caption("学生に表示される評価の例")

    preview_scores = {k: 75 + (hash(k) % 20) for k in criteria}

    for key, criterion in criteria.items():
        score = preview_scores[key]
        c1, c2, c3 = st.columns([3, 1, 1])
        with c1:
            st.markdown(criterion['name'])
        with c2:
            st.progress(score / 100)
        with c3:
            weighted = score * criterion['weight'] / 100
            st.markdown(f"{score}点 (×{criterion['weight']}% = {weighted:.1f})")

    total = sum(
        preview_scores[k] * criteria[k]['weight'] / 100
        for k in criteria
    )
    st.markdown(f"**総合スコア: {total:.1f}点**")


# ============================================================
# Tab 5: 練習メニュー
# ============================================================

def _tab_practice_menu(course_id: str, settings: dict):
    st.markdown("### 📋 練習メニュー")

    menu = settings["practice_menu"]
    options = [
        ("daily_reading", "毎日10分の音読練習"),
        ("weekly_speech", "週1回のスピーチ提出"),
        ("weekly_writing", "週2回のライティング練習"),
        ("listening_practice", "毎日15分のリスニング"),
        ("vocabulary_daily", "毎日の単語学習（10語）"),
    ]

    new_menu = {}
    for key, label in options:
        new_menu[key] = st.checkbox(label, value=menu.get(key, False), key=f"prac_{key}")

    if st.button("練習メニューを保存", type="primary", key="save_practice"):
        _save(course_id, "practice_menu", new_menu)


# ============================================================
# Tab 6: 成績配分
# ============================================================

def _tab_grade(course_id: str, settings: dict):
    st.markdown("### 📊 成績配分")

    grade = settings["grade_settings"]

    col1, col2 = st.columns(2)
    with col1:
        aw = st.slider("課題スコア平均", 0, 100, grade.get("assignment_weight", 50))
        pw = st.slider("練習への取り組み", 0, 100, grade.get("practice_weight", 20))
    with col2:
        fw = st.slider("最終テスト", 0, 100, grade.get("final_test_weight", 20))
        ppw = st.slider("授業参加・その他", 0, 100, grade.get("participation_weight", 10))

    total = aw + pw + fw + ppw
    if total == 100:
        st.success(f"✅ 合計: {total}%")
    else:
        st.error(f"❌ 合計: {total}%（100%にしてください）")

    if st.button("成績配分を保存", type="primary", key="save_grade"):
        new_grade = {
            "assignment_weight": aw,
            "practice_weight": pw,
            "final_test_weight": fw,
            "participation_weight": ppw,
        }
        _save(course_id, "grade_settings", new_grade)


# ============================================================
# 共通保存ヘルパー
# ============================================================

def _save(course_id: str, field: str, value):
    """フィールドをDBに保存し、結果をUIに表示"""
    try:
        update_course_settings_field(course_id, field, value)
        st.success("✅ DBに保存しました")
    except Exception as e:
        st.error(f"保存に失敗しました: {e}")
