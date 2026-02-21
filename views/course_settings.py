"""
授業設定ページ（教員用）
- スピーキング評価ウェイト（タスクタイプ別）
- ライティング評価ウェイト（タスクタイプ別）
- 授業外学習設定（目標・成績比率）
- 課題別評価基準カスタマイズ
- 全設定はcourse_settingsテーブルにJSONで永続化
"""
import streamlit as st
from utils.auth import get_current_user, require_auth
from datetime import datetime


# ============================================================
# デフォルト値
# ============================================================

def _default_speaking_weights() -> dict:
    return {
        "read_aloud": {
            "pronunciation": 40,
            "prosody": 30,
            "fluency": 20,
            "accuracy": 10,
        },
        "monologue": {
            "content": 30,
            "pronunciation": 15,
            "fluency": 25,
            "vocabulary": 15,
            "structure": 15,
        },
        "dialogue": {
            "communication": 40,
            "fluency": 25,
            "vocabulary": 20,
            "grammar": 15,
        },
    }


def _default_writing_weights() -> dict:
    return {
        "essay": {
            "content": 30,
            "structure": 20,
            "vocabulary": 20,
            "grammar": 20,
            "task_achievement": 10,
        },
        "summary": {
            "accuracy": 35,
            "vocabulary": 25,
            "grammar": 25,
            "conciseness": 15,
        },
        "email_letter": {
            "task_achievement": 35,
            "tone_format": 25,
            "vocabulary": 20,
            "grammar": 20,
        },
    }


def _default_extracurricular() -> dict:
    return {
        "speaking_target_per_week": 3,
        "writing_target_per_week": 2,
        "vocabulary_target_per_week": 5,
        "listening_target_per_week": 3,
        "reading_target_per_week": 2,
        "grade_weight_pct": 0,  # 成績への反映%（0=反映しない）
        "count_method": "sessions",  # sessions or minutes
    }


def _default_ai_feedback() -> dict:
    return {
        "speaking_priority": "balanced",   # pronunciation_focus / fluency_focus / communication_focus / balanced
        "writing_priority": "balanced",    # accuracy_focus / creativity_focus / balanced
        "feedback_language": "japanese",   # japanese / english / bilingual
        "feedback_detail": "standard",     # brief / standard / detailed
    }


# ============================================================
# ロード・セーブヘルパー
# ============================================================

def _load_settings(course_id: str) -> dict:
    cache_key = f"course_settings_full_{course_id}"
    if cache_key in st.session_state:
        return st.session_state[cache_key]
    try:
        from utils.database import get_course_settings
        s = get_course_settings(course_id) or {}
        st.session_state[cache_key] = s
        return s
    except Exception as e:
        st.error(f"設定の読み込みに失敗しました: {e}")
        return {}


def _save_settings(course_id: str, updates: dict):
    try:
        from utils.database import upsert_course_settings
        ok = upsert_course_settings(course_id, updates)
        # キャッシュクリア
        st.session_state.pop(f"course_settings_full_{course_id}", None)
        return ok is not None
    except Exception as e:
        st.error(f"保存エラー: {e}")
        return False


def _load_assignments(course_id: str) -> list:
    try:
        from utils.database import get_course_assignments
        return get_course_assignments(course_id) or []
    except Exception as e:
        st.error(f"課題の読み込みに失敗しました: {e}")
        return []


# ============================================================
# ウェイト合計チェック共通ヘルパー
# ============================================================

def _weight_editor(label_map: dict, current: dict, key_prefix: str) -> tuple[dict, bool]:
    """
    label_map: {field_key: 表示名}
    current:   {field_key: int(0-100)}
    戻り値: (new_values_dict, is_valid)
    """
    new_vals = {}
    cols = st.columns(len(label_map))
    for i, (k, label) in enumerate(label_map.items()):
        with cols[i]:
            new_vals[k] = st.slider(
                label,
                min_value=0, max_value=100,
                value=int(current.get(k, 0)),
                step=5,
                key=f"{key_prefix}_{k}"
            )
    total = sum(new_vals.values())
    if total == 100:
        st.success(f"✅ 合計: {total}%")
    else:
        diff = abs(100 - total)
        direction = "減らして" if total > 100 else "増やして"
        st.error(f"❌ 合計: {total}%（あと{diff}%{direction}ください）")
    return new_vals, (total == 100)


# ============================================================
# メインエントリ
# ============================================================

@require_auth
def show():
    user = get_current_user()
    if user.get('role') != 'teacher':
        st.warning("この画面は教員専用です。")
        return

    st.markdown("## ⚙️ 授業設定")

    if st.button("← 教員ホームに戻る"):
        st.session_state['current_view'] = 'teacher_home'
        st.rerun()

    selected_class = st.session_state.get('selected_class', '')
    classes = st.session_state.get('teacher_classes', {})
    course_id = None

    if selected_class and selected_class in classes:
        current_class = classes[selected_class]
        course_id = current_class.get('db_id') or current_class.get('course_id')
        st.info(f"📚 **{current_class['name']}** の設定")
    else:
        st.warning("クラスが選択されていません。教員ホームからクラスを選択してください。")
        return

    st.markdown("---")

    tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs([
        "🎤 スピーキング評価",
        "✍️ ライティング評価",
        "📚 授業外学習",
        "📝 課題別設定",
        "🤖 AIフィードバック",
        "📝 教材・プロンプト集",
    ])

    settings = _load_settings(course_id)

    with tab1:
        show_speaking_settings(course_id, settings)
    with tab2:
        show_writing_settings(course_id, settings)
    with tab3:
        show_extracurricular_settings(course_id, settings)
    with tab4:
        show_assignment_settings(course_id, settings)
    with tab5:
        show_ai_feedback_settings(course_id, settings)
    with tab6:
        _tab_learning_resources(course_id)


# ============================================================
# Tab 1: スピーキング評価設定
# ============================================================

def show_speaking_settings(course_id: str, settings: dict):
    st.markdown("### 🎤 スピーキング評価ウェイト設定")
    st.caption(
        "タスクタイプ（音読 / スピーチ / 対話）ごとに、AIフィードバックと成績評価の比重を設定します。"
        "各タスクで合計が100%になるよう調整してください。"
    )

    current_sw = settings.get("speaking_weights", _default_speaking_weights())

    # ── 音読 ──────────────────────────────────────────────
    st.markdown("#### 📖 音読（Read Aloud）")
    st.caption("発音の正確さとプロソディー（イントネーション・リズム）を重視")
    ra_labels = {
        "pronunciation": "🔤 発音",
        "prosody":        "🎵 プロソディー",
        "fluency":        "⚡ 流暢さ",
        "accuracy":       "✅ 正確さ（語順）",
    }
    ra_vals, ra_ok = _weight_editor(ra_labels, current_sw.get("read_aloud", {}), "ra")

    st.markdown("---")

    # ── スピーチ（モノローグ）──────────────────────────
    st.markdown("#### 🎙️ スピーチ（Monologue）")
    st.caption("内容・構成・語彙などの総合的な表現力を重視")
    mn_labels = {
        "content":        "💡 内容・アイデア",
        "structure":      "🏗️ 構成・まとまり",
        "fluency":        "⚡ 流暢さ",
        "vocabulary":     "📖 語彙の豊かさ",
        "pronunciation":  "🔤 発音",
    }
    mn_vals, mn_ok = _weight_editor(mn_labels, current_sw.get("monologue", {}), "mn")

    st.markdown("---")

    # ── 対話 ──────────────────────────────────────────────
    st.markdown("#### 💬 対話（Dialogue / Chat）")
    st.caption("即興性・コミュニケーション意欲を重視。文法ミスがあっても積極性を評価")
    dl_labels = {
        "communication":  "🗣️ コミュニケーション意欲",
        "fluency":        "⚡ 流暢さ・即興性",
        "vocabulary":     "📖 語彙",
        "grammar":        "📐 文法正確さ",
    }
    dl_vals, dl_ok = _weight_editor(dl_labels, current_sw.get("dialogue", {}), "dl")

    st.markdown("---")

    all_ok = ra_ok and mn_ok and dl_ok
    if not all_ok:
        st.warning("⚠️ 合計が100%でないタスクがあります。保存できません。")

    if st.button("💾 スピーキング設定を保存", type="primary", disabled=not all_ok, key="save_speaking"):
        new_sw = {
            "read_aloud": ra_vals,
            "monologue":  mn_vals,
            "dialogue":   dl_vals,
        }
        if _save_settings(course_id, {"speaking_weights": new_sw}):
            st.success("✅ スピーキング評価ウェイトを保存しました。")
            st.session_state.pop(f"course_settings_full_{course_id}", None)
        else:
            st.error("保存に失敗しました。")


# ============================================================
# Tab 2: ライティング評価設定
# ============================================================

def show_writing_settings(course_id: str, settings: dict):
    st.markdown("### ✍️ ライティング評価ウェイト設定")
    st.caption("タスクタイプ（エッセイ / 要約 / メール・手紙）ごとに評価比重を設定します。")

    current_ww = settings.get("writing_weights", _default_writing_weights())

    # ── エッセイ ─────────────────────────────────────────
    st.markdown("#### 📄 エッセイ（Essay）")
    es_labels = {
        "task_achievement": "🎯 課題達成度",
        "content":          "💡 内容・論点",
        "structure":        "🏗️ 構成・まとまり",
        "vocabulary":       "📖 語彙",
        "grammar":          "📐 文法正確さ",
    }
    es_vals, es_ok = _weight_editor(es_labels, current_ww.get("essay", {}), "es")

    st.markdown("---")

    # ── 要約 ──────────────────────────────────────────────
    st.markdown("#### 📝 要約（Summary）")
    su_labels = {
        "accuracy":    "✅ 内容の正確さ",
        "conciseness": "✂️ 簡潔さ",
        "vocabulary":  "📖 語彙",
        "grammar":     "📐 文法",
    }
    su_vals, su_ok = _weight_editor(su_labels, current_ww.get("summary", {}), "su")

    st.markdown("---")

    # ── メール・手紙 ─────────────────────────────────────
    st.markdown("#### 📧 メール・手紙（Email / Letter）")
    em_labels = {
        "task_achievement": "🎯 課題達成度・目的",
        "tone_format":      "🎩 トーン・フォーマット",
        "vocabulary":       "📖 語彙",
        "grammar":          "📐 文法",
    }
    em_vals, em_ok = _weight_editor(em_labels, current_ww.get("email_letter", {}), "em")

    st.markdown("---")

    all_ok = es_ok and su_ok and em_ok
    if not all_ok:
        st.warning("⚠️ 合計が100%でないタスクがあります。保存できません。")

    if st.button("💾 ライティング設定を保存", type="primary", disabled=not all_ok, key="save_writing"):
        new_ww = {
            "essay":        es_vals,
            "summary":      su_vals,
            "email_letter": em_vals,
        }
        if _save_settings(course_id, {"writing_weights": new_ww}):
            st.success("✅ ライティング評価ウェイトを保存しました。")
            st.session_state.pop(f"course_settings_full_{course_id}", None)
        else:
            st.error("保存に失敗しました。")


# ============================================================
# Tab 3: 授業外学習設定
# ============================================================

def show_extracurricular_settings(course_id: str, settings: dict):
    st.markdown("### 📚 授業外学習設定")
    st.caption(
        "シラバスに合わせて各モジュールの週あたり目標練習回数と、"
        "授業外学習スコアの成績への反映%を設定します。"
    )

    cur = settings.get("extracurricular", _default_extracurricular())

    st.markdown("#### 🎯 週あたり目標練習回数")
    col1, col2, col3 = st.columns(3)
    with col1:
        sp_t = st.number_input("🎤 Speaking", min_value=0, max_value=20,
                               value=int(cur.get("speaking_target_per_week", 3)), key="ext_sp")
        wr_t = st.number_input("✍️ Writing", min_value=0, max_value=20,
                               value=int(cur.get("writing_target_per_week", 2)), key="ext_wr")
    with col2:
        vo_t = st.number_input("📚 Vocabulary", min_value=0, max_value=20,
                               value=int(cur.get("vocabulary_target_per_week", 5)), key="ext_vo")
        ls_t = st.number_input("👂 Listening", min_value=0, max_value=20,
                               value=int(cur.get("listening_target_per_week", 3)), key="ext_ls")
    with col3:
        rd_t = st.number_input("📖 Reading", min_value=0, max_value=20,
                               value=int(cur.get("reading_target_per_week", 2)), key="ext_rd")

    st.markdown("---")
    st.markdown("#### 📊 成績への反映")

    count_method = st.radio(
        "達成度の計測方法",
        options=["sessions", "minutes"],
        format_func=lambda x: "練習回数（セッション数）" if x == "sessions" else "練習時間（分）",
        index=0 if cur.get("count_method", "sessions") == "sessions" else 1,
        key="ext_method",
        horizontal=True,
    )

    grade_pct = st.slider(
        "📈 授業外学習スコアを成績に反映する割合（%）",
        min_value=0, max_value=50,
        value=int(cur.get("grade_weight_pct", 0)),
        step=5,
        key="ext_grade_pct",
        help="0%の場合は成績計算に含まれません。grades.pyの成績配分設定と合わせて調整してください。"
    )

    if grade_pct > 0:
        st.info(
            f"💡 授業外学習スコアが成績の{grade_pct}%を占めます。"
            "grades.pyの「⚙️ 配分設定」タブでも反映させる場合は、"
            "そちらの「課題提出」ウェイトを調整してください。"
        )

    st.markdown("---")
    st.markdown("#### 📅 授業外学習スコアの算出方法")
    st.caption("各モジュールの週目標達成率（0〜100%）を加重平均して算出します。")

    col1, col2 = st.columns(2)
    with col1:
        st.markdown("""
**算出例（Speaking目標3回/週の場合）:**
- 3回練習 → 100点
- 2回練習 → 67点
- 0回練習 → 0点
""")
    with col2:
        st.markdown("""
**成績への反映タイミング:**
- 毎週月曜に前週分を集計
- 学期末に全週の平均を最終スコアとして使用
""")

    if st.button("💾 授業外学習設定を保存", type="primary", key="save_ext"):
        new_ext = {
            "speaking_target_per_week":   sp_t,
            "writing_target_per_week":    wr_t,
            "vocabulary_target_per_week": vo_t,
            "listening_target_per_week":  ls_t,
            "reading_target_per_week":    rd_t,
            "grade_weight_pct":           grade_pct,
            "count_method":               count_method,
        }
        if _save_settings(course_id, {"extracurricular": new_ext}):
            st.success("✅ 授業外学習設定を保存しました。")
            st.session_state.pop(f"course_settings_full_{course_id}", None)
        else:
            st.error("保存に失敗しました。")


# ============================================================
# Tab 4: 課題別評価基準設定
# ============================================================

def show_assignment_settings(course_id: str, settings: dict):
    st.markdown("### 📝 課題別評価基準カスタマイズ")
    st.caption(
        "個々の課題に対して、タスクタイプ・評価基準・AIフィードバック比重を個別設定できます。"
        "設定しない課題はTab1/Tab2のデフォルトウェイトが適用されます。"
    )

    assignments = _load_assignments(course_id)

    if not assignments:
        st.info("まだ課題が作成されていません。課題管理ページで課題を作成してください。")
        return

    # 課題をタイプ別に分類
    speaking_assignments = [a for a in assignments if a.get('assignment_type') in ('speaking', 'speaking_chat')]
    writing_assignments  = [a for a in assignments if a.get('assignment_type') == 'writing']
    other_assignments    = [a for a in assignments
                            if a.get('assignment_type') not in ('speaking', 'speaking_chat', 'writing')]

    assignment_rubrics = settings.get("assignment_rubrics", {})

    # ── スピーキング課題 ──────────────────────────────────
    if speaking_assignments:
        st.markdown("#### 🎤 スピーキング課題")
        for a in speaking_assignments:
            aid = a['id']
            title = a.get('title', '無題の課題')
            due = a.get('due_date', '')
            due_str = f"（締切: {due[:10]}）" if due else ""

            with st.expander(f"📌 {title} {due_str}", expanded=False):
                cur_rubric = assignment_rubrics.get(aid, {})

                # タスクタイプ選択
                task_type = st.selectbox(
                    "タスクタイプ",
                    options=["read_aloud", "monologue", "dialogue", "custom"],
                    format_func=lambda x: {
                        "read_aloud": "音読（Read Aloud）",
                        "monologue":  "スピーチ（Monologue）",
                        "dialogue":   "対話（Dialogue）",
                        "custom":     "カスタム（独自設定）",
                    }.get(x, x),
                    index=["read_aloud", "monologue", "dialogue", "custom"].index(
                        cur_rubric.get("task_type", "monologue")
                    ),
                    key=f"asgn_sp_type_{aid}"
                )

                selected_type = st.session_state.get(f"asgn_sp_type_{aid}", task_type)

                if selected_type == "custom":
                    st.markdown("**カスタム評価項目（各項目0〜100%、合計100%）**")
                    default_custom = cur_rubric.get("weights", {
                        "pronunciation": 25, "fluency": 25,
                        "content": 25, "communication": 25
                    })
                    custom_labels = {
                        "pronunciation":  "🔤 発音",
                        "fluency":        "⚡ 流暢さ",
                        "content":        "💡 内容",
                        "communication":  "🗣️ コミュニケーション",
                    }
                    custom_vals, custom_ok = _weight_editor(
                        custom_labels, default_custom, f"custom_sp_{aid}"
                    )
                    weights_to_save = custom_vals
                    can_save = custom_ok
                else:
                    # 選択タイプのデフォルトをプレビュー表示
                    default_map = _default_speaking_weights()
                    preset = settings.get("speaking_weights", default_map).get(selected_type, {})
                    st.caption("このタスクタイプのウェイト（Tab1の設定が適用されます）:")
                    cols = st.columns(len(preset))
                    label_map_sp = {
                        "pronunciation": "発音", "prosody": "プロソディー",
                        "fluency": "流暢さ", "accuracy": "正確さ",
                        "content": "内容", "structure": "構成",
                        "vocabulary": "語彙", "grammar": "文法",
                        "communication": "コミュニケーション",
                    }
                    for i, (k, v) in enumerate(preset.items()):
                        cols[i].metric(label_map_sp.get(k, k), f"{v}%")
                    weights_to_save = preset
                    can_save = True

                # 配点設定
                max_score = st.number_input(
                    "満点（点数）", min_value=10, max_value=200,
                    value=int(cur_rubric.get("max_score", 100)),
                    step=10, key=f"asgn_sp_max_{aid}"
                )

                # 課題メモ（採点時に表示）
                grading_note = st.text_area(
                    "採点メモ（採点時に表示されます）",
                    value=cur_rubric.get("grading_note", ""),
                    height=80,
                    placeholder="例：発音より流暢さを優先して評価。ミスしても止まらないことを重視。",
                    key=f"asgn_sp_note_{aid}"
                )

                if st.button("💾 この課題の設定を保存", key=f"save_asgn_sp_{aid}", disabled=not can_save):
                    new_rubric = dict(assignment_rubrics)
                    new_rubric[aid] = {
                        "type":         "speaking",
                        "task_type":    selected_type,
                        "weights":      weights_to_save,
                        "max_score":    max_score,
                        "grading_note": grading_note,
                        "updated_at":   datetime.utcnow().isoformat(),
                    }
                    if _save_settings(course_id, {"assignment_rubrics": new_rubric}):
                        st.success(f"✅ 「{title}」の設定を保存しました。")
                        st.session_state.pop(f"course_settings_full_{course_id}", None)
                    else:
                        st.error("保存に失敗しました。")

    # ── ライティング課題 ──────────────────────────────────
    if writing_assignments:
        st.markdown("#### ✍️ ライティング課題")
        for a in writing_assignments:
            aid = a['id']
            title = a.get('title', '無題の課題')
            due = a.get('due_date', '')
            due_str = f"（締切: {due[:10]}）" if due else ""

            with st.expander(f"📌 {title} {due_str}", expanded=False):
                cur_rubric = assignment_rubrics.get(aid, {})

                task_type_wr = st.selectbox(
                    "タスクタイプ",
                    options=["essay", "summary", "email_letter", "custom"],
                    format_func=lambda x: {
                        "essay":        "エッセイ（Essay）",
                        "summary":      "要約（Summary）",
                        "email_letter": "メール・手紙",
                        "custom":       "カスタム（独自設定）",
                    }.get(x, x),
                    index=["essay", "summary", "email_letter", "custom"].index(
                        cur_rubric.get("task_type", "essay")
                    ),
                    key=f"asgn_wr_type_{aid}"
                )

                selected_wr = st.session_state.get(f"asgn_wr_type_{aid}", task_type_wr)

                if selected_wr == "custom":
                    st.markdown("**カスタム評価項目（各項目0〜100%、合計100%）**")
                    default_custom_wr = cur_rubric.get("weights", {
                        "content": 25, "structure": 25,
                        "vocabulary": 25, "grammar": 25,
                    })
                    custom_wr_labels = {
                        "content":          "💡 内容",
                        "structure":        "🏗️ 構成",
                        "vocabulary":       "📖 語彙",
                        "grammar":          "📐 文法",
                    }
                    custom_wr_vals, custom_wr_ok = _weight_editor(
                        custom_wr_labels, default_custom_wr, f"custom_wr_{aid}"
                    )
                    weights_wr_save = custom_wr_vals
                    can_save_wr = custom_wr_ok
                else:
                    default_wr_map = _default_writing_weights()
                    preset_wr = settings.get("writing_weights", default_wr_map).get(selected_wr, {})
                    st.caption("このタスクタイプのウェイト（Tab2の設定が適用されます）:")
                    cols = st.columns(len(preset_wr))
                    label_map_wr = {
                        "task_achievement": "課題達成", "content": "内容",
                        "structure": "構成", "vocabulary": "語彙",
                        "grammar": "文法", "accuracy": "正確さ",
                        "conciseness": "簡潔さ", "tone_format": "トーン",
                    }
                    for i, (k, v) in enumerate(preset_wr.items()):
                        cols[i].metric(label_map_wr.get(k, k), f"{v}%")
                    weights_wr_save = preset_wr
                    can_save_wr = True

                # 最低語数・最大語数
                col1, col2 = st.columns(2)
                with col1:
                    min_words = st.number_input(
                        "最低語数", min_value=0, max_value=2000,
                        value=int(cur_rubric.get("min_words", 0)),
                        step=10, key=f"asgn_wr_min_{aid}"
                    )
                with col2:
                    max_words = st.number_input(
                        "最大語数（0=制限なし）", min_value=0, max_value=5000,
                        value=int(cur_rubric.get("max_words", 0)),
                        step=10, key=f"asgn_wr_max_{aid}"
                    )

                max_score_wr = st.number_input(
                    "満点（点数）", min_value=10, max_value=200,
                    value=int(cur_rubric.get("max_score", 100)),
                    step=10, key=f"asgn_wr_max_score_{aid}"
                )

                grading_note_wr = st.text_area(
                    "採点メモ",
                    value=cur_rubric.get("grading_note", ""),
                    height=80,
                    placeholder="例：文法ミスより内容の豊かさを重視。引用は避けること。",
                    key=f"asgn_wr_note_{aid}"
                )

                if st.button("💾 この課題の設定を保存", key=f"save_asgn_wr_{aid}", disabled=not can_save_wr):
                    new_rubric = dict(assignment_rubrics)
                    new_rubric[aid] = {
                        "type":         "writing",
                        "task_type":    selected_wr,
                        "weights":      weights_wr_save,
                        "min_words":    min_words,
                        "max_words":    max_words,
                        "max_score":    max_score_wr,
                        "grading_note": grading_note_wr,
                        "updated_at":   datetime.utcnow().isoformat(),
                    }
                    if _save_settings(course_id, {"assignment_rubrics": new_rubric}):
                        st.success(f"✅ 「{title}」の設定を保存しました。")
                        st.session_state.pop(f"course_settings_full_{course_id}", None)
                    else:
                        st.error("保存に失敗しました。")

    # ── その他の課題 ──────────────────────────────────────
    if other_assignments:
        st.markdown("#### 📋 その他の課題")
        for a in other_assignments:
            aid = a['id']
            title = a.get('title', '無題の課題')
            atype = a.get('assignment_type', '不明')
            due = a.get('due_date', '')
            due_str = f"（締切: {due[:10]}）" if due else ""

            with st.expander(f"📌 {title}【{atype}】{due_str}", expanded=False):
                cur_rubric = assignment_rubrics.get(aid, {})
                max_score_other = st.number_input(
                    "満点（点数）", min_value=10, max_value=200,
                    value=int(cur_rubric.get("max_score", 100)),
                    step=10, key=f"asgn_other_max_{aid}"
                )
                grading_note_other = st.text_area(
                    "採点メモ",
                    value=cur_rubric.get("grading_note", ""),
                    height=80,
                    key=f"asgn_other_note_{aid}"
                )
                if st.button("💾 この課題の設定を保存", key=f"save_asgn_other_{aid}"):
                    new_rubric = dict(assignment_rubrics)
                    new_rubric[aid] = {
                        "type":         atype,
                        "max_score":    max_score_other,
                        "grading_note": grading_note_other,
                        "updated_at":   datetime.utcnow().isoformat(),
                    }
                    if _save_settings(course_id, {"assignment_rubrics": new_rubric}):
                        st.success(f"✅ 「{title}」の設定を保存しました。")
                        st.session_state.pop(f"course_settings_full_{course_id}", None)
                    else:
                        st.error("保存に失敗しました。")


# ============================================================
# Tab 5: AIフィードバック設定
# ============================================================

def show_ai_feedback_settings(course_id: str, settings: dict):
    st.markdown("### 🤖 AIフィードバック設定")
    st.caption(
        "AIが生成するフィードバックの方針・言語・詳細度を設定します。"
        "ここで設定した内容はAIへのプロンプトに反映されます。"
    )

    cur = settings.get("ai_feedback", _default_ai_feedback())

    st.markdown("#### 🎤 スピーキングフィードバックの方針")
    sp_priority = st.radio(
        "重点方針",
        options=["pronunciation_focus", "fluency_focus", "communication_focus", "balanced"],
        format_func=lambda x: {
            "pronunciation_focus":  "🔤 発音重視（音読・発音練習向け）",
            "fluency_focus":        "⚡ 流暢さ重視（即興スピーチ向け）",
            "communication_focus":  "🗣️ コミュニケーション重視（対話向け）",
            "balanced":             "⚖️ バランス型（汎用）",
        }.get(x, x),
        index=["pronunciation_focus", "fluency_focus", "communication_focus", "balanced"].index(
            cur.get("speaking_priority", "balanced")
        ),
        key="ai_sp_priority",
        horizontal=False,
    )

    st.markdown("---")
    st.markdown("#### ✍️ ライティングフィードバックの方針")
    wr_priority = st.radio(
        "重点方針",
        options=["accuracy_focus", "creativity_focus", "balanced"],
        format_func=lambda x: {
            "accuracy_focus":    "📐 正確さ重視（文法・語法の指摘を詳しく）",
            "creativity_focus":  "💡 創造性重視（内容・表現のアイデアを提案）",
            "balanced":          "⚖️ バランス型（汎用）",
        }.get(x, x),
        index=["accuracy_focus", "creativity_focus", "balanced"].index(
            cur.get("writing_priority", "balanced")
        ),
        key="ai_wr_priority",
        horizontal=False,
    )

    st.markdown("---")
    st.markdown("#### 🌐 フィードバック言語・詳細度")
    col1, col2 = st.columns(2)

    with col1:
        fb_lang = st.selectbox(
            "フィードバック言語",
            options=["japanese", "english", "bilingual"],
            format_func=lambda x: {
                "japanese":  "🇯🇵 日本語",
                "english":   "🇺🇸 英語",
                "bilingual": "🇯🇵🇺🇸 バイリンガル（日英）",
            }.get(x, x),
            index=["japanese", "english", "bilingual"].index(
                cur.get("feedback_language", "japanese")
            ),
            key="ai_fb_lang"
        )

    with col2:
        fb_detail = st.selectbox(
            "フィードバック詳細度",
            options=["brief", "standard", "detailed"],
            format_func=lambda x: {
                "brief":    "📌 簡潔（1〜2文）",
                "standard": "📝 標準（3〜5文）",
                "detailed": "📄 詳細（項目別・具体例付き）",
            }.get(x, x),
            index=["brief", "standard", "detailed"].index(
                cur.get("feedback_detail", "standard")
            ),
            key="ai_fb_detail"
        )

    st.markdown("---")
    st.markdown("#### ✏️ フィードバックへの追加指示（プロンプト補足）")
    st.caption("ここに書いた内容がAIへのプロンプトに追記されます。授業の特徴や注意事項を記載してください。")

    extra_instruction = st.text_area(
        "追加指示（任意）",
        value=cur.get("extra_instruction", ""),
        height=120,
        placeholder=(
            "例：\n"
            "- この授業はビジネス英語コースです。ビジネス場面での自然さを重視してください。\n"
            "- 学習者は日本語母語話者の大学生です。\n"
            "- 冠詞や三単現のミスは指摘せず、コミュニケーション面に集中してください。"
        ),
        key="ai_extra_instruction"
    )

    if st.button("💾 AIフィードバック設定を保存", type="primary", key="save_ai"):
        new_ai = {
            "speaking_priority":  sp_priority,
            "writing_priority":   wr_priority,
            "feedback_language":  fb_lang,
            "feedback_detail":    fb_detail,
            "extra_instruction":  extra_instruction,
        }
        if _save_settings(course_id, {"ai_feedback": new_ai}):
            st.success("✅ AIフィードバック設定を保存しました。")
            st.session_state.pop(f"course_settings_full_{course_id}", None)
        else:
            st.error("保存に失敗しました。")


# ============================================================
# 設定取得ユーティリティ（他モジュールから呼び出し用）
# ============================================================

def get_speaking_weights_for_task(course_id: str, task_type: str,
                                  assignment_id: str = None) -> dict:
    """
    指定タスクタイプのスピーキング評価ウェイトを返す。
    assignment_idが指定されていて個別設定があればそちらを優先。
    他モジュール（speaking.py等）から呼び出して使用。

    使用例:
        from views.course_settings import get_speaking_weights_for_task
        weights = get_speaking_weights_for_task(course_id, "read_aloud", assignment_id)
    """
    try:
        from utils.database import get_course_settings
        s = get_course_settings(course_id) or {}
    except Exception:
        s = {}

    # 課題別設定を優先
    if assignment_id:
        rubric = s.get("assignment_rubrics", {}).get(assignment_id, {})
        if rubric.get("weights"):
            return rubric["weights"]

    # タスクタイプ別デフォルト
    sw = s.get("speaking_weights", _default_speaking_weights())
    return sw.get(task_type, sw.get("monologue", _default_speaking_weights()["monologue"]))


def get_writing_weights_for_task(course_id: str, task_type: str,
                                 assignment_id: str = None) -> dict:
    """
    指定タスクタイプのライティング評価ウェイトを返す。
    他モジュール（writing.py等）から呼び出して使用。
    """
    try:
        from utils.database import get_course_settings
        s = get_course_settings(course_id) or {}
    except Exception:
        s = {}

    if assignment_id:
        rubric = s.get("assignment_rubrics", {}).get(assignment_id, {})
        if rubric.get("weights"):
            return rubric["weights"]

    ww = s.get("writing_weights", _default_writing_weights())
    return ww.get(task_type, ww.get("essay", _default_writing_weights()["essay"]))


def get_ai_feedback_settings(course_id: str) -> dict:
    """
    AIフィードバック設定を返す。
    speaking.py / writing.py のAIプロンプト生成時に呼び出して使用。

    使用例:
        from views.course_settings import get_ai_feedback_settings
        ai_cfg = get_ai_feedback_settings(course_id)
        lang = ai_cfg.get("feedback_language", "japanese")
        extra = ai_cfg.get("extra_instruction", "")
    """
    try:
        from utils.database import get_course_settings
        s = get_course_settings(course_id) or {}
        return s.get("ai_feedback", _default_ai_feedback())
    except Exception:
        return _default_ai_feedback()


def get_extracurricular_settings(course_id: str) -> dict:
    """
    授業外学習設定を返す。analytics.py / student_home.py から呼び出して使用。
    """
    try:
        from utils.database import get_course_settings
        s = get_course_settings(course_id) or {}
        return s.get("extracurricular", _default_extracurricular())
    except Exception:
        return _default_extracurricular()


# ============================================================
# Tab 6: 教材・プロンプト集
# ============================================================

def _is_uuid(s: str) -> bool:
    import re
    return bool(re.match(
        r'^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$',
        str(s), re.IGNORECASE
    ))


def _tab_learning_resources(course_id: str):
    st.markdown("### 📝 教材・プロンプト集管理")

    if not _is_uuid(course_id):
        st.info("⚠️ この機能はDBコース（UUID）でのみ利用できます。\n\n教員ホームからDBコースを選択してください。")
        return

    from utils.auth import get_current_user
    user = get_current_user()
    teacher_id = user.get("id", "") if user else ""

    subtab1, subtab2, subtab3 = st.tabs(["📋 一覧・編集", "➕ 新規追加", "📥 一括インポート"])

    with subtab1:
        _resources_list(course_id)
    with subtab2:
        _resources_add(course_id, teacher_id)
    with subtab3:
        _resources_import(course_id, teacher_id)


def _resources_list(course_id: str):
    from utils.database import get_learning_resources, update_learning_resource, delete_learning_resource
    resources = get_learning_resources(course_id=course_id)

    if not resources:
        st.info("まだプロンプト・教材が登録されていません。「➕ 新規追加」または「📥 一括インポート」から追加してください。")
        return

    st.success(f"{len(resources)} 件登録済み")

    categories = sorted(set(r.get("category", "general") for r in resources))
    sel_cat = st.selectbox("カテゴリで絞り込み", ["すべて"] + categories)

    filtered = resources if sel_cat == "すべて" else [r for r in resources if r.get("category") == sel_cat]

    for r in filtered:
        with st.expander(f"{'✅' if r.get('is_active', True) else '🚫'} {r.get('title', '無題')} [{r.get('category','-')}]"):
            new_title = st.text_input("タイトル", value=r.get("title",""), key=f"rt_{r['id']}")
            new_desc  = st.text_area("説明", value=r.get("description",""), key=f"rd_{r['id']}", height=60)
            new_content = st.text_area("プロンプト本文", value=r.get("content",""), key=f"rc_{r['id']}", height=120)
            new_tip   = st.text_input("使い方ヒント", value=r.get("tip",""), key=f"rp_{r['id']}")
            col1, col2, col3 = st.columns(3)
            with col1:
                new_cat = st.text_input("カテゴリ", value=r.get("category",""), key=f"rcat_{r['id']}")
            with col2:
                new_order = st.number_input("表示順", value=r.get("sort_order",0), key=f"ro_{r['id']}")
            with col3:
                st.write("")
                if st.button("💾 保存", key=f"rsave_{r['id']}"):
                    update_learning_resource(r["id"], {
                        "title": new_title, "description": new_desc,
                        "content": new_content, "tip": new_tip,
                        "category": new_cat, "sort_order": int(new_order),
                    })
                    st.success("保存しました")
                    st.rerun()
                if st.button("🗑️ 削除", key=f"rdel_{r['id']}"):
                    delete_learning_resource(r["id"])
                    st.success("削除しました")
                    st.rerun()


def _resources_add(course_id: str, teacher_id: str):
    from utils.database import create_learning_resource
    st.markdown("#### ➕ プロンプト・教材を1件追加")
    with st.form("add_resource_form"):
        title    = st.text_input("タイトル *")
        category = st.selectbox("カテゴリ", ["writing","conversation","vocabulary","test_prep","general_language","ai_usage","custom"])
        desc     = st.text_area("説明", height=60)
        content  = st.text_area("プロンプト本文 *", height=150)
        tip      = st.text_input("使い方ヒント")
        order    = st.number_input("表示順", min_value=0, value=0)
        submitted = st.form_submit_button("💾 追加", use_container_width=True)

    if submitted:
        if not title or not content:
            st.error("タイトルとプロンプト本文は必須です")
        else:
            result = create_learning_resource(
                teacher_id=teacher_id, course_id=course_id,
                resource_type="prompt", category=category,
                title=title, description=desc, content=content,
                tip=tip, sort_order=int(order),
            )
            if result:
                st.success(f"「{title}」を追加しました")
                st.rerun()
            else:
                st.error("追加に失敗しました")


def _resources_import(course_id: str, teacher_id: str):
    from utils.database import bulk_import_learning_resources
    st.markdown("#### 📥 ハードコードプロンプトを一括インポート")
    st.caption("learning_resources.pyに含まれるデフォルトプロンプトをDBに登録します。")

    try:
        from views.learning_resources import PROMPTS_BY_CATEGORY
        categories = list(PROMPTS_BY_CATEGORY.keys())
        sel = st.multiselect("インポートするカテゴリ", categories, default=categories)
        if st.button("📥 インポート実行", type="primary"):
            items = []
            for cat in sel:
                for p in PROMPTS_BY_CATEGORY.get(cat, []):
                    items.append({
                        "resource_type": "prompt",
                        "category": cat,
                        "title": p.get("title",""),
                        "description": p.get("description",""),
                        "content": p.get("content",""),
                        "tip": p.get("tip",""),
                        "sort_order": p.get("sort_order", 0),
                    })
            if items:
                count = bulk_import_learning_resources(teacher_id, course_id, items)
                st.success(f"✅ {count} 件インポートしました")
                st.rerun()
            else:
                st.warning("インポート対象がありません")
    except ImportError:
        st.warning("learning_resources.pyが見つかりません。ファイルを確認してください。")
    except AttributeError:
        st.info("PROMPTS_BY_CATEGORYが定義されていません。個別追加タブをご利用ください。")
