"""
教材管理 / Material Manager
============================
教員向け教材管理画面
- 初期教材のDB投入（seed_default_materials）
- 教材一覧の閲覧・管理
- 教材の追加・編集・無効化

※ 既存ファイルへの変更は不要。このファイルを追加するだけで動作する。
"""

import streamlit as st
import json
from utils.auth import get_current_user, require_auth
from utils.database import (
    get_learning_materials,
    get_learning_material,
    upsert_learning_material,
    delete_learning_material,
    seed_default_materials,
    get_supabase_client,
)


# ============================================================
# メイン表示
# ============================================================

def show():
    """教材管理画面のメイン"""
    user = get_current_user()
    if not user or user["role"] != "teacher":
        st.warning("教員アカウントでログインしてください")
        return

    st.markdown("## 📚 教材管理 / Material Manager")
    st.caption("学習モジュールで使用する教材データの管理")

    if st.button("← ホームに戻る"):
        st.session_state["current_view"] = "teacher_home"
        st.rerun()

    st.markdown("---")

    # タブ構成
    tab1, tab2, tab3 = st.tabs([
        "📋 教材一覧",
        "➕ 教材追加",
        "⚙️ 初期データ・メンテナンス",
    ])

    with tab1:
        _show_material_list()

    with tab2:
        _show_add_material()

    with tab3:
        _show_maintenance()


# ============================================================
# タブ1: 教材一覧
# ============================================================

def _show_material_list():
    """登録済み教材の一覧表示"""

    # モジュールタイプ選択
    module_types = ["listening", "reading", "vocabulary", "speaking", "writing"]
    selected_type = st.selectbox(
        "モジュール",
        module_types,
        format_func=lambda x: {
            "listening": "🎧 Listening",
            "reading": "📖 Reading",
            "vocabulary": "📝 Vocabulary",
            "speaking": "🗣️ Speaking",
            "writing": "✏️ Writing",
        }.get(x, x),
    )

    # 無効な教材も含めるかどうか
    show_inactive = st.checkbox("無効化した教材も表示", value=False)

    # データ取得
    materials = get_learning_materials(
        module_type=selected_type,
        active_only=not show_inactive,
    )

    if not materials:
        st.info(f"{selected_type} の教材はまだ登録されていません。"
                f"\n\n「⚙️ 初期データ・メンテナンス」タブから初期教材を投入できます。")
        return

    st.success(f"✅ {len(materials)} 件の教材が登録されています")

    # 教材カード表示
    for i, mat in enumerate(materials):
        is_active = mat.get("is_active", True)
        status_icon = "✅" if is_active else "🚫"

        with st.expander(
            f"{status_icon} {mat.get('title', '無題')} "
            f"({mat.get('level', '-')}) "
            f"[key: {mat.get('material_key', '-')}]",
            expanded=False,
        ):
            col1, col2, col3 = st.columns([2, 2, 1])
            with col1:
                st.markdown(f"**タイプ:** {mat.get('module_type', '-')}")
                st.markdown(f"**レベル:** {mat.get('level', '-')}")
                st.markdown(f"**カテゴリ:** {mat.get('category', '-')}")
            with col2:
                st.markdown(f"**キー:** `{mat.get('material_key', '-')}`")
                st.markdown(f"**並び順:** {mat.get('sort_order', 0)}")
                st.markdown(f"**状態:** {'有効' if is_active else '無効'}")
            with col3:
                if mat.get('course_id'):
                    st.markdown(f"**コース専用**")
                else:
                    st.markdown(f"**共通教材**")

            # 説明文
            if mat.get("description"):
                st.markdown(f"**説明:** {mat['description']}")

            # contentの概要表示（JSONなので一部だけ）
            content = mat.get("content")
            if content:
                if isinstance(content, str):
                    try:
                        content = json.loads(content)
                    except Exception:
                        pass

                if isinstance(content, dict):
                    keys = list(content.keys())
                    st.caption(f"コンテンツ項目: {', '.join(keys[:10])}"
                              f"{'...' if len(keys) > 10 else ''}")
                else:
                    st.caption(f"コンテンツ: {str(content)[:200]}")

            # 操作ボタン
            col_a, col_b = st.columns(2)
            with col_a:
                if is_active:
                    if st.button(f"🚫 無効化", key=f"deactivate_{mat['id']}"):
                        delete_learning_material(mat["id"])
                        st.success("無効化しました")
                        st.rerun()
                else:
                    if st.button(f"✅ 有効化", key=f"activate_{mat['id']}"):
                        try:
                            supabase = get_supabase_client()
                            supabase.table('learning_materials')\
                                .update({'is_active': True})\
                                .eq('id', mat['id']).execute()
                            st.success("有効化しました")
                            st.rerun()
                        except Exception as e:
                            st.error(f"エラー: {e}")


# ============================================================
# タブ2: 教材追加
# ============================================================

def _show_add_material():
    """新規教材の追加フォーム"""

    st.markdown("### ➕ 新規教材の追加")
    st.caption("手動で教材を1件追加します。大量投入は「初期データ」タブを使用してください。")

    with st.form("add_material_form"):
        module_type = st.selectbox(
            "モジュールタイプ *",
            ["listening", "reading", "vocabulary", "speaking", "writing"],
        )

        material_key = st.text_input(
            "教材キー *",
            placeholder="例: unit1_conversation, toeic_part3_01",
            help="一意の識別子。英数字とアンダースコアを使用",
        )

        title = st.text_input(
            "タイトル *",
            placeholder="例: Meeting a New Classmate",
        )

        col1, col2 = st.columns(2)
        with col1:
            level = st.selectbox(
                "レベル",
                ["A1", "A2", "B1", "B2", "C1", "C2"],
                index=2,
            )
        with col2:
            category = st.text_input(
                "カテゴリ",
                placeholder="例: Daily Conversation",
            )

        description = st.text_area(
            "説明",
            placeholder="教材の概要を入力",
        )

        sort_order = st.number_input(
            "並び順",
            min_value=0,
            max_value=999,
            value=0,
            help="小さい数字が先に表示されます",
        )

        content_json = st.text_area(
            "コンテンツ (JSON)",
            placeholder='例: {"text": "Hello, my name is...", "questions": [...]}',
            height=200,
            help="教材の本体データをJSON形式で入力",
        )

        submitted = st.form_submit_button("💾 教材を保存", use_container_width=True)

        if submitted:
            # バリデーション
            if not material_key or not title:
                st.error("教材キーとタイトルは必須です")
            else:
                # contentのパース
                content = {}
                if content_json.strip():
                    try:
                        content = json.loads(content_json)
                    except json.JSONDecodeError as e:
                        st.error(f"JSONの形式が正しくありません: {e}")
                        return

                data = {
                    "module_type": module_type,
                    "material_key": material_key,
                    "title": title,
                    "level": level,
                    "category": category,
                    "description": description,
                    "sort_order": sort_order,
                    "content": content,
                }

                result = upsert_learning_material(data)
                if result:
                    st.success(f"✅ 教材「{title}」を保存しました")
                    st.rerun()
                else:
                    st.error("保存に失敗しました。データベース接続を確認してください。")


# ============================================================
# タブ3: 初期データ・メンテナンス
# ============================================================

def _show_maintenance():
    """初期データ投入とメンテナンス"""

    st.markdown("### ⚙️ 初期教材データの投入")

    # 現在の教材数を表示
    _show_current_counts()

    st.markdown("---")

    st.markdown("#### 🌱 デモ教材の一括投入")
    st.markdown("""
    以下のソースから教材データをDBに投入します：
    - `utils/listening.py` → DEMO_LISTENING
    - `utils/reading.py` → DEMO_ARTICLES  
    - `utils/vocabulary.py` → DEMO_WORD_LISTS
    
    既に同じ `material_key` のデータがある場合は **上書き（upsert）** されます。
    既存の教材が削除されることはありません。
    """)

    col1, col2 = st.columns(2)
    with col1:
        if st.button("🌱 初期教材を投入", use_container_width=True, type="primary"):
            with st.spinner("教材データを投入中..."):
                try:
                    count = seed_default_materials()
                    if count > 0:
                        st.success(f"✅ {count} 件の教材を投入しました！")
                        st.balloons()
                    else:
                        st.warning("投入された教材はありませんでした。"
                                  "既に全データが登録済みか、ソースデータが見つかりません。")
                except Exception as e:
                    st.error(f"エラーが発生しました: {e}")

    with col2:
        if st.button("🔄 教材数を再確認", use_container_width=True):
            st.rerun()

    st.markdown("---")

    st.markdown("#### 📊 データベース状態")
    _show_db_status()


def _show_current_counts():
    """各モジュールの教材数を表示"""

    module_types = ["listening", "reading", "vocabulary", "speaking", "writing"]
    icons = {
        "listening": "🎧",
        "reading": "📖",
        "vocabulary": "📝",
        "speaking": "🗣️",
        "writing": "✏️",
    }

    cols = st.columns(len(module_types))
    total = 0
    for col, mt in zip(cols, module_types):
        materials = get_learning_materials(module_type=mt, active_only=False)
        count = len(materials)
        total += count
        with col:
            st.metric(
                label=f"{icons[mt]} {mt.capitalize()}",
                value=count,
            )

    if total == 0:
        st.warning("⚠️ 教材がまだ1件も登録されていません。「🌱 初期教材を投入」ボタンで投入してください。")
    else:
        st.info(f"📚 合計 {total} 件の教材が登録されています")


def _show_db_status():
    """learning_materialsテーブルの状態確認"""
    try:
        supabase = get_supabase_client()
        result = supabase.table('learning_materials')\
            .select('module_type, is_active')\
            .execute()

        if not result.data:
            st.info("learning_materials テーブルは空です")
            return

        # モジュールタイプ別に集計
        stats = {}
        for row in result.data:
            mt = row.get('module_type', 'unknown')
            active = row.get('is_active', True)
            if mt not in stats:
                stats[mt] = {"active": 0, "inactive": 0}
            if active:
                stats[mt]["active"] += 1
            else:
                stats[mt]["inactive"] += 1

        for mt, counts in sorted(stats.items()):
            st.markdown(
                f"- **{mt}**: {counts['active']} 件有効"
                f"{f', {counts[\"inactive\"]} 件無効' if counts['inactive'] > 0 else ''}"
            )

    except Exception as e:
        st.error(f"データベース接続エラー: {e}")
