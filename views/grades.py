"""
成績集計ページ（強化版）
- モジュール別スコア（Speaking/Writing/Vocabulary/Reading/Listening）をDBから正確に集計
- 成績配分をcourse_settingsに永続化（リロードで消えない）
- 出席CSVアップロード対応
- 確実に動作することを最優先（エラー時は安全にフォールバック）
"""
import streamlit as st
from utils.auth import get_current_user, require_auth
from datetime import datetime
import statistics


@require_auth
def show():
    user = get_current_user()

    st.markdown("## 📈 成績集計")

    if st.button("← 教員ホームに戻る"):
        st.session_state['current_view'] = 'teacher_home'
        st.rerun()

    st.markdown("---")

    selected_class = st.session_state.get('selected_class', '')
    classes = st.session_state.get('teacher_classes', {})
    course_id = None

    if selected_class and selected_class in classes:
        current_class = classes[selected_class]
        course_id = current_class.get('db_id') or current_class.get('course_id')
        st.info(f"📚 **{current_class['name']}** の成績集計")
    else:
        st.warning("クラスが選択されていません。教員ホームからクラスを選択してください。")
        return

    tab1, tab2, tab3, tab4, tab5 = st.tabs([
        "📊 成績一覧",
        "⚙️ 配分設定",
        "📈 統計・分析",
        "📉 スコア推移",
        "📥 エクスポート / インポート"
    ])

    with tab1:
        show_grade_list(course_id)
    with tab2:
        show_grade_settings(course_id)
    with tab3:
        show_grade_statistics(course_id)
    with tab4:
        show_score_trends(course_id)
    with tab5:
        show_export_options(course_id)


# ============================================================
# データ読み込み・計算ヘルパー
# ============================================================

def _load_module_scores(course_id: str) -> list:
    if not course_id:
        return []
    try:
        from utils.database import get_module_scores_for_course, get_extracurricular_score_for_course
        students = get_module_scores_for_course(course_id)
        # 授業外学習スコアをマージ
        extra_map = get_extracurricular_score_for_course(course_id) or {}
        for s in students:
            uid = s.get('user_id', s.get('id', ''))
            extra = extra_map.get(uid, {})
            s['extracurricular_score'] = extra.get('score', 0.0)
            s['extracurricular_points'] = extra.get('approved_points', 0)
            s['extracurricular_count'] = extra.get('log_count', 0)
        return students
    except Exception as e:
        st.error(f"モジュールスコアの取得に失敗しました: {e}")
        return []


def _load_weights(course_id: str) -> dict:
    cache_key = f'grade_weights_{course_id}'
    if cache_key in st.session_state:
        return st.session_state[cache_key]
    try:
        from utils.database import get_grade_weights
        weights = get_grade_weights(course_id)
    except Exception:
        weights = _default_weights()
    st.session_state[cache_key] = weights
    return weights


def _default_weights() -> dict:
    return {
        'speaking': 20, 'writing': 20, 'vocabulary': 15,
        'reading': 15, 'listening': 15, 'assignment': 15,
        'extracurricular': 0, 'attendance': 0,
    }


def _load_attendance(course_id: str) -> dict:
    return st.session_state.get(f'attendance_scores_{course_id}', {})


def _calc_student_total(s: dict, weights: dict, attendance_map: dict) -> dict:
    def safe(val):
        return float(val) if val is not None else 0.0

    speaking        = safe(s.get('speaking_avg'))
    writing         = safe(s.get('writing_avg'))
    vocabulary      = safe(s.get('vocabulary_avg'))
    reading         = safe(s.get('reading_avg'))
    listening       = safe(s.get('listening_avg'))
    assignment      = safe(s.get('assignment_avg'))
    extracurricular = safe(s.get('extracurricular_score'))
    att_raw = attendance_map.get(s.get('student_id', ''), None)
    attendance = float(att_raw) if att_raw is not None else 0.0

    w = weights
    total = (
        speaking        * w.get('speaking', 0) / 100 +
        writing         * w.get('writing', 0) / 100 +
        vocabulary      * w.get('vocabulary', 0) / 100 +
        reading         * w.get('reading', 0) / 100 +
        listening       * w.get('listening', 0) / 100 +
        assignment      * w.get('assignment', 0) / 100 +
        extracurricular * w.get('extracurricular', 0) / 100 +
        attendance      * w.get('attendance', 0) / 100
    )

    return {
        'name': s.get('name', ''),
        'student_id': s.get('student_id', ''),
        'user_id': s.get('user_id', ''),
        'email': s.get('email', ''),
        'speaking': speaking, 'speaking_count': s.get('speaking_count', 0),
        'writing': writing, 'writing_count': s.get('writing_count', 0),
        'vocabulary': vocabulary, 'vocabulary_count': s.get('vocabulary_count', 0),
        'reading': reading, 'reading_count': s.get('reading_count', 0),
        'listening': listening, 'listening_count': s.get('listening_count', 0),
        'assignment': assignment, 'assignment_count': s.get('assignment_count', 0),
        'extracurricular': extracurricular,
        'extracurricular_points': s.get('extracurricular_points', 0),
        'extracurricular_count': s.get('extracurricular_count', 0),
        'attendance': attendance, 'attendance_input': att_raw is not None,
        'total': round(total, 1),
        'grade': _calc_grade(total),
        '_raw': s,
    }


def _calc_grade(total: float) -> str:
    if total >= 90: return "A+"
    if total >= 80: return "A"
    if total >= 75: return "B+"
    if total >= 70: return "B"
    if total >= 65: return "C+"
    if total >= 60: return "C"
    if total >= 50: return "D"
    return "F"


# ============================================================
# Tab 1: 成績一覧
# ============================================================

def show_grade_list(course_id: str):
    st.markdown("### 📊 成績一覧")

    if not course_id:
        st.warning("コースが選択されていません")
        return

    with st.spinner("成績データを読み込み中..."):
        students_raw = _load_module_scores(course_id)

    if not students_raw:
        st.info("まだ学生データがありません。学生が登録し学習を開始すると成績が表示されます。")
        return

    weights = _load_weights(course_id)
    attendance_map = _load_attendance(course_id)
    grade_data = [_calc_student_total(s, weights, attendance_map) for s in students_raw]

    col1, col2, col3 = st.columns(3)
    with col1:
        sort_by = st.selectbox("ソート", ["学籍番号順", "合計点順（高→低）", "合計点順（低→高）", "評定順"], key="grade_sort")
    with col2:
        filter_grade = st.selectbox("評定フィルタ", ["全て", "A+/A", "B+/B", "C+/C", "D/F"], key="grade_filter")
    with col3:
        search = st.text_input("🔍 検索", placeholder="名前または学籍番号", key="grade_search")

    if sort_by == "合計点順（高→低）":
        grade_data.sort(key=lambda x: x['total'], reverse=True)
    elif sort_by == "合計点順（低→高）":
        grade_data.sort(key=lambda x: x['total'])
    elif sort_by == "評定順":
        order = {"A+": 0, "A": 1, "B+": 2, "B": 3, "C+": 4, "C": 5, "D": 6, "F": 7}
        grade_data.sort(key=lambda x: order.get(x['grade'], 99))

    if filter_grade == "A+/A":
        grade_data = [g for g in grade_data if g['grade'] in ["A+", "A"]]
    elif filter_grade == "B+/B":
        grade_data = [g for g in grade_data if g['grade'] in ["B+", "B"]]
    elif filter_grade == "C+/C":
        grade_data = [g for g in grade_data if g['grade'] in ["C+", "C"]]
    elif filter_grade == "D/F":
        grade_data = [g for g in grade_data if g['grade'] in ["D", "F"]]
    if search:
        grade_data = [g for g in grade_data if search.lower() in g['name'].lower() or search in g['student_id']]

    st.markdown("---")

    w = weights
    show_extra = w.get('extracurricular', 0) > 0
    col_widths = [2, 1, 1, 1, 1, 1, 1, 1] + ([1] if show_extra else []) + [1, 1]
    cols = st.columns(col_widths)
    headers = [
        "名前", "学籍番号",
        f"Speaking\n({w.get('speaking',0)}%)",
        f"Writing\n({w.get('writing',0)}%)",
        f"Vocab\n({w.get('vocabulary',0)}%)",
        f"Reading\n({w.get('reading',0)}%)",
        f"Listening\n({w.get('listening',0)}%)",
        f"課題\n({w.get('assignment',0)}%)",
    ]
    if show_extra:
        headers.append(f"授業外\n({w.get('extracurricular',0)}%)")
    headers += ["合計 / 評定", "操作"]
    for col, header in zip(cols, headers):
        col.markdown(f"**{header}**")
    st.markdown("---")

    grade_color = {
        "A+": "🟢", "A": "🟢", "B+": "🔵", "B": "🔵",
        "C+": "🟡", "C": "🟡", "D": "🟠", "F": "🔴"
    }

    for g in grade_data:
        cols = st.columns(col_widths)

        def fmt(val, count=None):
            if val and val > 0:
                base = f"{val:.1f}"
                return f"{base} ({count}回)" if count else base
            return "－"

        with cols[0]:
            st.markdown(f"**{g['name']}**")
            if w.get('attendance', 0) > 0:
                att_str = f"{g['attendance']:.0f}点" if g['attendance_input'] else "未入力"
                st.caption(f"出席: {att_str}")
        with cols[1]:
            st.caption(g['student_id'])
        with cols[2]:
            st.markdown(fmt(g['speaking'], g['speaking_count']))
        with cols[3]:
            st.markdown(fmt(g['writing'], g['writing_count']))
        with cols[4]:
            st.markdown(fmt(g['vocabulary'], g['vocabulary_count']))
        with cols[5]:
            st.markdown(fmt(g['reading'], g['reading_count']))
        with cols[6]:
            st.markdown(fmt(g['listening'], g['listening_count']))
        with cols[7]:
            st.markdown(fmt(g['assignment'], g['assignment_count']))
        col_idx = 8
        if show_extra:
            with cols[col_idx]:
                pts = g.get('extracurricular_points', 0)
                sc = g.get('extracurricular', 0)
                if sc > 0:
                    st.markdown(f"{sc:.0f}点")
                    st.caption(f"{pts}pt")
                else:
                    st.markdown("－")
            col_idx += 1
        with cols[col_idx]:
            st.markdown(f"{grade_color.get(g['grade'], '')} **{g['grade']}** ({g['total']:.1f})")
        with cols[col_idx + 1]:
            if st.button("詳細", key=f"grade_detail_{g['user_id']}"):
                st.session_state['selected_student'] = g['_raw']
                st.session_state['current_view'] = 'student_portfolio'
                st.rerun()

    st.markdown("---")
    st.caption(f"{len(grade_data)}名表示中")


# ============================================================
# Tab 2: 配分設定
# ============================================================

def show_grade_settings(course_id: str):
    st.markdown("### ⚙️ 成績配分設定")
    st.caption("各モジュールの成績への比重を設定します。合計が100%になるよう調整してください。")

    current = _load_weights(course_id)

    st.markdown("#### 📊 モジュール別配分")
    col1, col2 = st.columns(2)
    with col1:
        sp  = st.slider("🎤 Speaking",   0, 100, current.get('speaking', 20),   key="w_sp")
        wr  = st.slider("✍️ Writing",    0, 100, current.get('writing', 20),    key="w_wr")
        vo  = st.slider("📚 Vocabulary", 0, 100, current.get('vocabulary', 15), key="w_vo")
    with col2:
        rd  = st.slider("📖 Reading",    0, 100, current.get('reading', 15),    key="w_rd")
        ls  = st.slider("👂 Listening",  0, 100, current.get('listening', 15),  key="w_ls")
        as_ = st.slider("📝 課題提出",   0, 100, current.get('assignment', 15), key="w_as")

    st.markdown("#### 📓 授業外学習（learning_logs）")
    ex = st.slider("📓 授業外学習", 0, 50, current.get('extracurricular', 0), key="w_ex",
                   help="承認済みの授業外学習ポイントを成績に反映。0%の場合は計算に含まれません。100ポイント=100点換算。")

    st.markdown("#### 📋 出席（CSVインポート）")
    at = st.slider("🗓️ 出席点", 0, 100, current.get('attendance', 0), key="w_at",
                   help="0%の場合は成績計算に含まれません")

    total = sp + wr + vo + rd + ls + as_ + ex + at
    if total == 100:
        st.success(f"✅ 合計: {total}%")
    else:
        diff = total - 100
        st.error(f"❌ 合計: {total}%（{'あと' if diff < 0 else ''}{ abs(diff) }%{'減らして' if diff > 0 else '増やして'}ください）")

    st.markdown("---")
    st.markdown("#### 🏆 評定基準")
    col1, col2 = st.columns(2)
    with col1:
        st.markdown("| 評定 | 点数範囲 |\n|------|-------|\n| A+ | 90〜100 |\n| A | 80〜89 |\n| B+ | 75〜79 |\n| B | 70〜74 |")
    with col2:
        st.markdown("| 評定 | 点数範囲 |\n|------|-------|\n| C+ | 65〜69 |\n| C | 60〜64 |\n| D | 50〜59 |\n| F | 〜49 |")

    if st.button("💾 設定を保存（DB）", type="primary", disabled=(total != 100)):
        new_weights = {
            'speaking': sp, 'writing': wr, 'vocabulary': vo,
            'reading': rd, 'listening': ls, 'assignment': as_,
            'extracurricular': ex, 'attendance': at,
        }
        try:
            from utils.database import save_grade_weights
            ok = save_grade_weights(course_id, new_weights)
            if ok:
                st.session_state[f'grade_weights_{course_id}'] = new_weights
                st.success("✅ 設定をDBに保存しました。次回以降も反映されます。")
            else:
                st.error("保存に失敗しました。")
        except Exception as e:
            st.error(f"保存エラー: {e}")


# ============================================================
# Tab 3: 統計・分析
# ============================================================

def show_grade_statistics(course_id: str):
    st.markdown("### 📈 成績統計")

    if not course_id:
        st.warning("コースが選択されていません")
        return

    with st.spinner("データを読み込み中..."):
        students_raw = _load_module_scores(course_id)

    if not students_raw:
        st.info("まだ成績データがありません")
        return

    weights = _load_weights(course_id)
    attendance_map = _load_attendance(course_id)
    grade_data = [_calc_student_total(s, weights, attendance_map) for s in students_raw]

    totals = [g['total'] for g in grade_data if g['total'] > 0]

    if not totals:
        st.info("スコアデータがまだありません")
        return

    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("クラス平均", f"{statistics.mean(totals):.1f}点")
    with col2:
        st.metric("最高点", f"{max(totals):.1f}点")
    with col3:
        st.metric("最低点", f"{min(totals):.1f}点")
    with col4:
        stdev = statistics.stdev(totals) if len(totals) > 1 else 0
        st.metric("標準偏差", f"{stdev:.1f}")

    st.markdown("---")
    st.markdown("#### 🏆 評定分布")

    grade_counts = {}
    for g in grade_data:
        gr = g['grade']
        grade_counts[gr] = grade_counts.get(gr, 0) + 1

    grade_order = ["A+", "A", "B+", "B", "C+", "C", "D", "F"]
    total_students = len(grade_data)
    max_count = max(grade_counts.values()) if grade_counts else 1
    for gr in grade_order:
        count = grade_counts.get(gr, 0)
        pct = count / total_students * 100 if total_students > 0 else 0
        col1, col2, col3 = st.columns([1, 4, 1])
        with col1:
            st.markdown(f"**{gr}**")
        with col2:
            st.progress(count / max_count if max_count > 0 else 0)
        with col3:
            st.caption(f"{count}名 ({pct:.0f}%)")

    st.markdown("---")
    st.markdown("#### 📊 モジュール別クラス平均")

    modules = [
        ("🎤 Speaking", "speaking"), ("✍️ Writing", "writing"),
        ("📚 Vocabulary", "vocabulary"), ("📖 Reading", "reading"),
        ("👂 Listening", "listening"), ("📝 課題提出", "assignment"),
    ]
    col1, col2, col3 = st.columns(3)
    for i, (label, key) in enumerate(modules):
        vals = [g[key] for g in grade_data if g.get(key, 0) > 0]
        avg = statistics.mean(vals) if vals else None
        with [col1, col2, col3][i % 3]:
            if avg is not None:
                st.metric(label, f"{avg:.1f}点", help=f"データあり: {len(vals)}名")
            else:
                st.metric(label, "データなし")


# ============================================================
# Tab 4: スコア推移グラフ
# ============================================================

def show_score_trends(course_id: str):
    """クラス全体・個人のスコア推移を時系列グラフで可視化"""
    st.markdown("### 📉 スコア推移")

    if not course_id:
        st.warning("コースが選択されていません")
        return

    # ── 表示モード選択 ──────────────────────────────────────
    mode = st.radio(
        "表示モード",
        ["クラス平均推移", "個人スコア比較", "モジュール別ヒートマップ"],
        horizontal=True,
        key="trend_mode"
    )
    st.markdown("---")

    if mode == "クラス平均推移":
        _show_class_avg_trend(course_id)
    elif mode == "個人スコア比較":
        _show_individual_trend(course_id)
    else:
        _show_module_heatmap(course_id)


def _show_class_avg_trend(course_id: str):
    """クラス全体の週次平均スコア推移"""
    st.markdown("#### 📊 クラス平均スコア推移（週次）")
    st.caption("各モジュールの週次平均スコアを折れ線グラフで表示します。")

    try:
        from utils.database import get_course_practice_logs_for_trend
        logs = get_course_practice_logs_for_trend(course_id, days=90)
    except Exception:
        logs = None

    # フォールバック: get_module_scores_for_courseから擬似推移を生成
    if not logs:
        st.info(
            "週次データを取得するには `get_course_practice_logs_for_trend()` が必要です。"
            "現在は直近スコア一覧を代替表示しています。"
        )
        _show_class_avg_fallback(course_id)
        return

    try:
        import pandas as pd
        df = pd.DataFrame(logs)
        if df.empty:
            st.info("推移データがまだありません")
            return

        df['practiced_at'] = pd.to_datetime(df['practiced_at'])
        df['week'] = df['practiced_at'].dt.to_period('W').apply(lambda x: str(x.start_time)[:10])

        MODULE_MAP = {
            'speaking': '🎤 Speaking',
            'speaking_pronunciation': '🎤 Speaking',
            'speaking_read_aloud': '🎤 Speaking',
            'writing_practice': '✍️ Writing',
            'writing_submission': '✍️ Writing',
            'vocabulary_quiz': '📚 Vocabulary',
            'vocabulary_flashcard': '📚 Vocabulary',
            'reading_practice': '📖 Reading',
            'listening_practice': '👂 Listening',
            'listening_dictation': '👂 Listening',
        }
        df['module_group'] = df['module_type'].map(MODULE_MAP)
        df = df[df['module_group'].notna() & df['score'].notna() & (df['score'] > 0)]

        weekly = df.groupby(['week', 'module_group'])['score'].mean().round(1).reset_index()
        pivot = weekly.pivot(index='week', columns='module_group', values='score')

        st.line_chart(pivot)

        # 直近週と先週の比較サマリー
        if len(pivot) >= 2:
            st.markdown("**直近2週の比較:**")
            last_week = pivot.iloc[-1]
            prev_week = pivot.iloc[-2]
            cols = st.columns(len(pivot.columns))
            for i, col_name in enumerate(pivot.columns):
                last_val = last_week.get(col_name)
                prev_val = prev_week.get(col_name)
                with cols[i]:
                    if last_val is not None and prev_val is not None:
                        delta = last_val - prev_val
                        st.metric(col_name, f"{last_val:.1f}点", f"{delta:+.1f}")
                    elif last_val is not None:
                        st.metric(col_name, f"{last_val:.1f}点")

    except Exception as e:
        st.error(f"グラフの生成に失敗しました: {e}")


def _show_class_avg_fallback(course_id: str):
    """get_course_practice_logs_for_trendがない場合の代替表示"""
    students_raw = _load_module_scores(course_id)
    if not students_raw:
        st.info("データがありません")
        return

    import statistics
    modules = [
        ("🎤 Speaking",   "speaking_avg"),
        ("✍️ Writing",    "writing_avg"),
        ("📚 Vocabulary", "vocabulary_avg"),
        ("📖 Reading",    "reading_avg"),
        ("👂 Listening",  "listening_avg"),
    ]
    cols = st.columns(len(modules))
    for i, (label, key) in enumerate(modules):
        vals = [float(s[key]) for s in students_raw if s.get(key) and float(s[key]) > 0]
        with cols[i]:
            if vals:
                avg = statistics.mean(vals)
                st.metric(label, f"{avg:.1f}点", help=f"{len(vals)}名のデータ")
            else:
                st.metric(label, "－")


def _show_individual_trend(course_id: str):
    """個人スコアの時系列推移"""
    st.markdown("#### 👤 個人スコア推移")

    students_raw = _load_module_scores(course_id)
    if not students_raw:
        st.info("学生データがありません")
        return

    # 学生選択
    student_options = {
        s.get('user_id', s.get('id', '')): f"{s.get('name', '不明')} ({s.get('student_id', '')})"
        for s in students_raw
    }
    selected_uid = st.selectbox(
        "学生を選択",
        list(student_options.keys()),
        format_func=lambda x: student_options.get(x, x),
        key="trend_student_select"
    )

    module_filter = st.multiselect(
        "表示するモジュール",
        options=["Speaking", "Writing", "Vocabulary", "Reading", "Listening"],
        default=["Speaking", "Writing"],
        key="trend_module_filter"
    )

    days_option = st.select_slider(
        "期間",
        options=[30, 60, 90, 180],
        value=90,
        format_func=lambda x: f"直近{x}日",
        key="trend_days"
    )

    if not selected_uid:
        return

    try:
        from utils.database import get_student_practice_details
        logs = get_student_practice_details(selected_uid, days=days_option) or []

        if not logs:
            st.info("この学生の練習データがまだありません")
            return

        import pandas as pd

        MODULE_GROUP_MAP = {
            'speaking': 'Speaking', 'speaking_pronunciation': 'Speaking',
            'speaking_read_aloud': 'Speaking', 'speaking_chat': 'Speaking',
            'writing_practice': 'Writing', 'writing_submission': 'Writing',
            'vocabulary_quiz': 'Vocabulary', 'vocabulary_flashcard': 'Vocabulary',
            'reading_practice': 'Reading',
            'listening_practice': 'Listening', 'listening_dictation': 'Listening',
        }

        rows = []
        for l in logs:
            if not l.get('score') or float(l.get('score', 0)) <= 0:
                continue
            date = (l.get('practiced_at') or '')[:10]
            group = MODULE_GROUP_MAP.get(l.get('module_type', ''))
            if not date or not group:
                continue
            if group not in module_filter:
                continue
            rows.append({'日付': date, 'module': group, 'score': float(l['score'])})

        if not rows:
            st.info("選択したモジュールのスコアデータがありません")
            return

        df = pd.DataFrame(rows)
        # 日付×モジュールで平均
        pivot = df.groupby(['日付', 'module'])['score'].mean().round(1).reset_index()
        pivot = pivot.pivot(index='日付', columns='module', values='score')

        st.line_chart(pivot)

        # 最新スコアとトレンド
        st.markdown("**最新スコアとトレンド:**")
        cols = st.columns(len(module_filter))
        for i, mod in enumerate(module_filter):
            mod_data = df[df['module'] == mod].sort_values('日付')
            with cols[i]:
                if len(mod_data) >= 2:
                    half = max(1, len(mod_data) // 2)
                    first_avg = mod_data.head(half)['score'].mean()
                    last_avg = mod_data.tail(half)['score'].mean()
                    delta = last_avg - first_avg
                    st.metric(f"📊 {mod}", f"{last_avg:.1f}点", f"{delta:+.1f}")
                elif len(mod_data) == 1:
                    st.metric(f"📊 {mod}", f"{mod_data.iloc[0]['score']:.1f}点")
                else:
                    st.metric(f"📊 {mod}", "－")

    except Exception as e:
        st.error(f"個人データの取得に失敗: {e}")


def _show_module_heatmap(course_id: str):
    """学生×モジュールのスコアヒートマップ"""
    st.markdown("#### 🗂️ クラス全体 モジュール別スコアマップ")
    st.caption("各学生のモジュール別スコアを色で表示します。空欄は未練習。")

    students_raw = _load_module_scores(course_id)
    if not students_raw:
        st.info("データがありません")
        return

    weights = _load_weights(course_id)
    attendance_map = _load_attendance(course_id)
    grade_data = [_calc_student_total(s, weights, attendance_map) for s in students_raw]

    # ソートオプション
    sort_key = st.selectbox(
        "ソート",
        ["学籍番号順", "合計点順（高→低）", "Speaking順", "Writing順"],
        key="heatmap_sort"
    )
    if sort_key == "合計点順（高→低）":
        grade_data.sort(key=lambda x: x['total'], reverse=True)
    elif sort_key == "Speaking順":
        grade_data.sort(key=lambda x: x['speaking'], reverse=True)
    elif sort_key == "Writing順":
        grade_data.sort(key=lambda x: x['writing'], reverse=True)

    MODULES = [
        ("Speaking",   "speaking"),
        ("Writing",    "writing"),
        ("Vocabulary", "vocabulary"),
        ("Reading",    "reading"),
        ("Listening",  "listening"),
        ("課題",        "assignment"),
    ]

    def _score_color(val):
        if not val or val <= 0:
            return "#f3f4f6", "#9ca3af"  # bg, text
        if val >= 80:
            return "#bbf7d0", "#15803d"
        elif val >= 70:
            return "#fef08a", "#854d0e"
        elif val >= 60:
            return "#fed7aa", "#9a3412"
        else:
            return "#fecaca", "#991b1b"

    # ヘッダー行
    header_cols = st.columns([2] + [1] * len(MODULES) + [1])
    header_cols[0].markdown("**氏名**")
    for i, (label, _) in enumerate(MODULES):
        header_cols[i + 1].markdown(f"**{label}**")
    header_cols[-1].markdown("**合計**")

    st.markdown("---")

    for g in grade_data:
        row_cols = st.columns([2] + [1] * len(MODULES) + [1])
        with row_cols[0]:
            st.markdown(f"**{g['name']}**")
            st.caption(g['student_id'])

        for i, (label, key) in enumerate(MODULES):
            val = g.get(key, 0)
            bg, fg = _score_color(val)
            with row_cols[i + 1]:
                if val and val > 0:
                    st.markdown(
                        f"<div style='background:{bg};color:{fg};text-align:center;"
                        f"border-radius:4px;padding:4px;font-weight:bold;font-size:0.9em;'>"
                        f"{val:.0f}</div>",
                        unsafe_allow_html=True
                    )
                else:
                    st.markdown(
                        "<div style='background:#f3f4f6;color:#d1d5db;text-align:center;"
                        "border-radius:4px;padding:4px;font-size:0.9em;'>－</div>",
                        unsafe_allow_html=True
                    )

        with row_cols[-1]:
            total = g.get('total', 0)
            bg_t, fg_t = _score_color(total)
            st.markdown(
                f"<div style='background:{bg_t};color:{fg_t};text-align:center;"
                f"border-radius:4px;padding:4px;font-weight:bold;'>"
                f"{total:.0f}</div>",
                unsafe_allow_html=True
            )

    st.markdown("---")
    st.markdown("""
    **凡例:** 
    🟢 80点以上　🟡 70〜79点　🟠 60〜69点　🔴 59点以下　⬜ データなし
    """)


# ============================================================
# Tab 4: エクスポート / 出席インポート
# ============================================================

def show_export_options(course_id: str):
    st.markdown("### 📥 エクスポート / インポート")
    exp_tab, att_tab = st.tabs(["📤 成績CSVエクスポート", "🗓️ 出席CSVインポート"])
    with exp_tab:
        _show_export(course_id)
    with att_tab:
        _show_attendance_import(course_id)


def _show_export(course_id: str):
    st.markdown("#### 📄 成績CSVダウンロード")

    if not course_id:
        st.warning("コースが選択されていません")
        return

    include_modules = st.checkbox("モジュール別スコアを含める", value=True, key="exp_modules")
    include_counts  = st.checkbox("練習回数を含める", value=False, key="exp_counts")
    include_att     = st.checkbox("出席点を含める（CSVインポート済みの場合）", value=True, key="exp_att")

    if st.button("📥 CSVを生成してダウンロード", type="primary"):
        with st.spinner("成績データを集計中..."):
            students_raw = _load_module_scores(course_id)

        if not students_raw:
            st.warning("エクスポートするデータがありません")
            return

        weights = _load_weights(course_id)
        attendance_map = _load_attendance(course_id)
        grade_data = [_calc_student_total(s, weights, attendance_map) for s in students_raw]

        import pandas as pd
        rows = []
        for g in grade_data:
            row = {'学籍番号': g['student_id'], '氏名': g['name']}
            if include_modules:
                row['Speaking']   = g['speaking']   if g['speaking'] > 0   else ''
                row['Writing']    = g['writing']     if g['writing'] > 0    else ''
                row['Vocabulary'] = g['vocabulary']  if g['vocabulary'] > 0 else ''
                row['Reading']    = g['reading']     if g['reading'] > 0    else ''
                row['Listening']  = g['listening']   if g['listening'] > 0  else ''
                row['課題提出']    = g['assignment']  if g['assignment'] > 0  else ''
            if include_att and weights.get('attendance', 0) > 0:
                row['出席点'] = g['attendance'] if g['attendance_input'] else ''
            if include_counts:
                row['Speaking回数']   = g['speaking_count']
                row['Writing回数']    = g['writing_count']
                row['Vocabulary回数'] = g['vocabulary_count']
                row['Reading回数']    = g['reading_count']
                row['Listening回数']  = g['listening_count']
                row['課題提出数']      = g['assignment_count']
            row['合計点'] = g['total']
            row['評定']   = g['grade']
            rows.append(row)

        df = pd.DataFrame(rows)
        st.dataframe(df, use_container_width=True, hide_index=True)
        csv = df.to_csv(index=False).encode('utf-8-sig')
        st.download_button(
            "📤 CSVダウンロード",
            csv,
            f"grades_{datetime.now().strftime('%Y%m%d_%H%M')}.csv",
            "text/csv",
            use_container_width=True,
        )


def _show_attendance_import(course_id: str):
    st.markdown("#### 🗓️ 出席点CSVアップロード")
    st.caption("Numbers / Excel などで管理している出席データをCSVで取り込めます。")

    st.markdown("""
**CSVフォーマット（必須列）:**
```
学籍番号,出席点
B123456,85
B234567,100
```
- `学籍番号` 列: usersテーブルの`student_id`と一致するもの
- `出席点` 列: 0〜100の数値
    """)

    uploaded = st.file_uploader("出席CSVをアップロード", type=['csv'], key="att_upload")

    if uploaded:
        import pandas as pd
        try:
            df = pd.read_csv(uploaded, dtype=str)
            df.columns = df.columns.str.strip()

            sid_col   = next((c for c in df.columns if '学籍' in c or 'student' in c.lower()), None)
            score_col = next((c for c in df.columns if '出席' in c or 'attendance' in c.lower() or 'score' in c.lower()), None)

            if not sid_col or not score_col:
                st.error(f"列が見つかりません。検出された列: {list(df.columns)}\n`学籍番号`と`出席点`の列が必要です。")
                return

            st.success(f"✅ {len(df)}件を読み込みました")
            st.dataframe(df[[sid_col, score_col]], use_container_width=True, hide_index=True)

            if st.button("📥 この出席データを成績計算に適用", type="primary"):
                att_map = {}
                errors = []
                for _, row in df.iterrows():
                    sid = str(row[sid_col]).strip()
                    try:
                        score = float(str(row[score_col]).strip())
                        if 0 <= score <= 100:
                            att_map[sid] = score
                        else:
                            errors.append(f"{sid}: スコア範囲外 ({score})")
                    except ValueError:
                        errors.append(f"{sid}: 数値変換エラー ({row[score_col]})")

                st.session_state[f'attendance_scores_{course_id}'] = att_map
                st.success(f"✅ {len(att_map)}件の出席データを適用しました。「成績一覧」タブで確認できます。")
                if errors:
                    st.warning("以下の行はスキップされました:\n" + "\n".join(errors))

        except Exception as e:
            st.error(f"CSVの読み込みに失敗しました: {e}")

    existing = _load_attendance(course_id)
    if existing:
        st.markdown("---")
        st.success(f"現在 {len(existing)}名分の出席データが読み込まれています。")
        if st.button("🗑️ 出席データをクリア"):
            st.session_state.pop(f'attendance_scores_{course_id}', None)
            st.rerun()
