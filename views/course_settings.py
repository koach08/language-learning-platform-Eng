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
import re
from utils.auth import get_current_user, require_auth
from utils.database import (
    get_course_settings,
    upsert_course_settings,
    update_course_settings_field,
    get_learning_resources,
    create_learning_resource,
    update_learning_resource,
    delete_learning_resource,
    bulk_import_learning_resources,
)


def _is_uuid(value: str) -> bool:
    """course_idがUUID形式かどうか判定"""
    if not value:
        return False
    return bool(re.match(
        r'^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$',
        value, re.IGNORECASE
    ))


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
# ヘルパー: UUID判定
# ============================================================

import re
_UUID_RE = re.compile(
    r'^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$',
    re.IGNORECASE
)

def _is_uuid(value: str) -> bool:
    """文字列がUUID形式かどうか判定"""
    return bool(_UUID_RE.match(value or ''))


# ============================================================
# ヘルパー: DBからロードしてデフォルトとマージ
# ============================================================

def _load_settings(course_id: str) -> dict:
    """DBから設定を取得し、未設定項目にはデフォルトを適用"""
    row = None
    if _is_uuid(course_id):
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

    # コース選択（DB版 or ハードコード版のどちらにも対応）
    course_id = st.session_state.get('selected_course_id')
    course_name = st.session_state.get('selected_course_name', '')

    # DB版のcourse_idがない場合、teacher_homeのselected_classをフォールバック
    if not course_id:
        selected_class = st.session_state.get('selected_class')
        if selected_class:
            # ハードコードクラスキーをcourse_idとして使用
            course_id = selected_class
            classes = st.session_state.get('teacher_classes', {})
            course_name = classes.get(selected_class, {}).get('name', selected_class)
            # 以降の処理で使えるようにセット
            st.session_state['selected_course_id'] = course_id
            st.session_state['selected_course_name'] = course_name

    if not course_id:
        # デバッグ: 何がsession_stateにあるか表示
        with st.expander("🔍 デバッグ情報（原因特定用）"):
            st.write("selected_course_id:", st.session_state.get('selected_course_id'))
            st.write("selected_course_name:", st.session_state.get('selected_course_name'))
            st.write("selected_class:", st.session_state.get('selected_class'))
            st.write("teacher_classes keys:", list(st.session_state.get('teacher_classes', {}).keys()))

        st.warning("コースが選択されていません。教員ホームからコースを選択してください。")

        # 簡易コース選択UI（フォールバック）
        classes = st.session_state.get('teacher_classes', {})
        if classes:
            st.markdown("#### 👇 ここからコースを選択できます")
            selected = st.selectbox(
                "コースを選択",
                list(classes.keys()),
                format_func=lambda x: classes[x].get('name', x),
                key="fallback_course_select",
            )
            if st.button("このコースで設定を開く", type="primary"):
                st.session_state['selected_class'] = selected
                st.session_state['selected_course_id'] = selected
                st.session_state['selected_course_name'] = classes[selected].get('name', selected)
                st.rerun()
        return

    st.info(f"📚 **{course_name}** の設定")

    # DBから設定をロード
    settings = _load_settings(course_id)

    # タブ
    tab1, tab2, tab3, tab4, tab5, tab6, tab7 = st.tabs([
        "📌 科目の目的",
        "📦 モジュール設定",
        "🗣️ Speaking評価基準",
        "✍️ Writing評価基準",
        "📋 練習メニュー",
        "📊 成績配分",
        "📝 教材・プロンプト集",
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
    with tab7:
        _tab_learning_resources(course_id, user)


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

    # 組み込みモジュール定義
    builtin_module_defs = {
        "speaking": "🗣️ スピーキング",
        "writing": "✍️ ライティング",
        "pronunciation": "🎤 発音矯正",
        "listening": "🎧 リスニング",
        "reading": "📖 リーディング",
        "vocabulary": "📚 語彙",
    }

    # 全モジュール（組み込み + カスタム）をまとめて表示
    all_keys = list(builtin_module_defs.keys())
    # カスタムモジュール（組み込み以外）もリストに追加
    for key in modules:
        if key not in all_keys:
            all_keys.append(key)

    total_weight = 0
    new_modules = {}

    for key in all_keys:
        mod = modules.get(key, {"enabled": False, "weight": 0})
        label = builtin_module_defs.get(key, f"🔧 {mod.get('label', key)}")
        is_custom = key not in builtin_module_defs

        col1, col2, col3, col4 = st.columns([3, 1, 0.5, 0.5])

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
        with col4:
            if is_custom:
                if st.button("🗑️", key=f"delmod_{key}", help="カスタムモジュールを削除"):
                    # 削除フラグ
                    st.session_state[f"_del_mod_{key}"] = True
                    st.rerun()

        # 削除フラグ処理
        if st.session_state.pop(f"_del_mod_{key}", False):
            continue  # このモジュールをスキップ

        entry = {"enabled": enabled, "weight": weight}
        if is_custom:
            entry["label"] = mod.get("label", key)
            entry["custom"] = True
        new_modules[key] = entry
        if enabled:
            total_weight += weight

    st.markdown("---")
    if total_weight > 0:
        if total_weight == 100:
            st.success(f"✅ 合計: {total_weight}%")
        else:
            st.warning(f"⚠️ 合計: {total_weight}%")

    # カスタムモジュール追加
    with st.expander("➕ 新規モジュールを追加"):
        new_mod_label = st.text_input(
            "モジュール名", placeholder="例: プレゼンテーション",
            key="new_mod_label"
        )
        new_mod_weight = st.number_input(
            "初期配分%", 0, 100, 0, key="new_mod_weight"
        )
        if st.button("モジュールを追加", key="add_custom_mod"):
            if new_mod_label:
                new_key = new_mod_label.lower().replace(" ", "_").replace("　", "_")
                if new_key in new_modules:
                    st.warning("同名のモジュールが既に存在します")
                else:
                    new_modules[new_key] = {
                        "enabled": True,
                        "weight": new_mod_weight,
                        "label": new_mod_label,
                        "custom": True,
                    }
                    st.success(f"「{new_mod_label}」を追加しました（保存ボタンを押してください）")
            else:
                st.warning("モジュール名を入力してください")

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
# Tab 7: 教材・プロンプト集管理
# ============================================================

# プロンプト集のカテゴリ定義
RESOURCE_CATEGORIES = {
    "writing": "✏️ 英作文添削・文法チェック",
    "conversation": "💬 会話練習・ロールプレイ",
    "vocabulary": "📚 語彙学習・単語説明",
    "test_prep": "📋 試験対策",
    "general_language": "🌍 語学学習全般",
    "custom": "🔧 カスタム",
}


def _tab_learning_resources(course_id: str, user: dict):
    st.markdown("### 📝 教材・プロンプト集管理")
    st.caption("学生に表示するAIプロンプト集を管理できます")

    teacher_id = user["id"]

    # DBからリソースを取得（UUID形式のcourse_idの場合のみ）
    resources = []
    if _is_uuid(course_id):
        resources = get_learning_resources(course_id=course_id, resource_type='prompt')
    else:
        st.info("💡 このクラスはローカル設定のため、教材管理はデモモードです。DBコースを作成すると完全なDB管理が利用できます。")

    # サブタブ
    sub1, sub2, sub3 = st.tabs(["📋 一覧・編集", "➕ 新規追加", "📥 一括インポート"])

    with sub1:
        _resources_list(course_id, resources)

    with sub2:
        _resources_add(course_id, teacher_id)

    with sub3:
        _resources_import(course_id, teacher_id, resources)


def _resources_list(course_id: str, resources: list):
    """リソース一覧・編集・削除"""
    if not resources:
        st.info("まだプロンプトが登録されていません。「新規追加」タブから追加するか、「一括インポート」でデフォルトをインポートしてください。")
        return

    st.markdown(f"**{len(resources)} 件のプロンプトが登録されています**")

    # カテゴリ別にグループ化
    by_cat = {}
    for r in resources:
        cat = r.get("category", "custom")
        by_cat.setdefault(cat, []).append(r)

    for cat, items in by_cat.items():
        cat_label = RESOURCE_CATEGORIES.get(cat, f"🔧 {cat}")
        st.markdown(f"#### {cat_label}")

        for item in items:
            with st.expander(f"**{item['title']}** — {item.get('description', '')}"):
                # 編集モード
                edit_key = f"edit_{item['id']}"

                new_title = st.text_input(
                    "タイトル", value=item["title"], key=f"t_{item['id']}"
                )
                new_desc = st.text_input(
                    "説明", value=item.get("description", ""), key=f"d_{item['id']}"
                )
                new_content = st.text_area(
                    "プロンプト本文", value=item.get("content", ""),
                    height=200, key=f"c_{item['id']}"
                )
                new_tip = st.text_input(
                    "💡 ヒント", value=item.get("tip", ""), key=f"tip_{item['id']}"
                )
                new_cat = st.selectbox(
                    "カテゴリ",
                    list(RESOURCE_CATEGORIES.keys()),
                    index=list(RESOURCE_CATEGORIES.keys()).index(cat) if cat in RESOURCE_CATEGORIES else 0,
                    format_func=lambda x: RESOURCE_CATEGORIES.get(x, x),
                    key=f"cat_{item['id']}",
                )
                new_order = st.number_input(
                    "表示順", 0, 999, item.get("sort_order", 0), key=f"ord_{item['id']}"
                )

                col_save, col_del = st.columns([1, 1])
                with col_save:
                    if st.button("💾 更新", key=f"upd_{item['id']}", type="primary"):
                        update_learning_resource(item["id"], {
                            "title": new_title,
                            "description": new_desc,
                            "content": new_content,
                            "tip": new_tip,
                            "category": new_cat,
                            "sort_order": new_order,
                        })
                        st.success("更新しました")
                        st.rerun()
                with col_del:
                    if st.button("🗑️ 削除", key=f"del_{item['id']}"):
                        delete_learning_resource(item["id"])
                        st.success("削除しました")
                        st.rerun()

        st.markdown("---")


def _resources_add(course_id: str, teacher_id: str):
    """新規プロンプト追加"""
    st.markdown("#### ➕ 新しいプロンプトを追加")

    if not _is_uuid(course_id):
        st.warning("DBコースでのみ利用可能です")
        return

    new_cat = st.selectbox(
        "カテゴリ",
        list(RESOURCE_CATEGORIES.keys()),
        format_func=lambda x: RESOURCE_CATEGORIES.get(x, x),
        key="new_res_cat",
    )
    new_title = st.text_input("タイトル", placeholder="例: エッセイ構成チェック", key="new_res_title")
    new_desc = st.text_input("説明", placeholder="例: エッセイの構成・論理展開をチェック", key="new_res_desc")
    new_content = st.text_area(
        "プロンプト本文",
        placeholder="Please review the structure...",
        height=250,
        key="new_res_content",
    )
    new_tip = st.text_input("💡 ヒント（任意）", placeholder="例: 文法チェックと構成チェックを分けると効果的", key="new_res_tip")
    new_order = st.number_input("表示順（小さいほど上）", 0, 999, 0, key="new_res_order")

    if st.button("プロンプトを追加", type="primary", key="btn_add_resource"):
        if not new_title:
            st.warning("タイトルを入力してください")
        elif not new_content:
            st.warning("プロンプト本文を入力してください")
        else:
            create_learning_resource(
                teacher_id=teacher_id,
                course_id=course_id,
                resource_type='prompt',
                category=new_cat,
                title=new_title,
                description=new_desc,
                content=new_content,
                tip=new_tip,
                sort_order=new_order,
            )
            st.success(f"「{new_title}」を追加しました！")
            st.rerun()


def _resources_import(course_id: str, teacher_id: str, existing_resources: list):
    """ハードコード済みプロンプト集からの一括インポート"""
    st.markdown("#### 📥 デフォルトプロンプト集をインポート")
    st.caption("あらかじめ用意されたプロンプト集をこのコースに一括登録します")

    if not _is_uuid(course_id):
        st.warning("DBコースでのみ利用可能です")
        return

    if existing_resources:
        st.info(f"このコースには既に {len(existing_resources)} 件のプロンプトが登録されています。重複が発生する可能性があります。")

    # インポートするカテゴリを選択
    from views.learning_resources import AI_PROMPTS

    available_cats = list(AI_PROMPTS.keys())
    selected_cats = st.multiselect(
        "インポートするカテゴリを選択",
        available_cats,
        default=available_cats,
        format_func=lambda x: RESOURCE_CATEGORIES.get(x, x),
        key="import_cats",
    )

    # プレビュー
    total_count = 0
    for cat in selected_cats:
        cat_data = AI_PROMPTS[cat]
        total_count += len(cat_data["prompts"])

    st.markdown(f"**{total_count} 件のプロンプトをインポートします**")

    if st.button("一括インポート実行", type="primary", key="btn_import"):
        rows = []
        for cat in selected_cats:
            cat_data = AI_PROMPTS[cat]
            for i, p in enumerate(cat_data["prompts"]):
                rows.append({
                    "resource_type": "prompt",
                    "category": cat,
                    "title": p["title"],
                    "description": p.get("description", ""),
                    "content": p["prompt"],
                    "tip": p.get("tip", ""),
                    "sort_order": i,
                })

        count = bulk_import_learning_resources(teacher_id, course_id, rows)
        st.success(f"✅ {count} 件をインポートしました！")
        st.rerun()


# ============================================================
# 共通保存ヘルパー
# ============================================================

def _save(course_id: str, field: str, value):
    """フィールドをDBに保存し、結果をUIに表示"""
    if not _is_uuid(course_id):
        # ハードコードクラスの場合はsession_stateに保存
        key = f"_settings_{course_id}"
        if key not in st.session_state:
            st.session_state[key] = {}
        st.session_state[key][field] = value
        st.success("✅ 設定を保存しました（セッション内）")
        return

    try:
        update_course_settings_field(course_id, field, value)
        st.success("✅ DBに保存しました")
    except Exception as e:
        st.error(f"保存に失敗しました: {e}")
