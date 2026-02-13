import streamlit as st
from utils.auth import get_current_user, require_auth
from datetime import datetime


@require_auth
def show():
    user = get_current_user()
    
    st.markdown("## 📈 成績集計")
    
    if st.button("← 教員ホームに戻る"):
        st.session_state['current_view'] = 'teacher_home'
        st.rerun()
    
    st.markdown("---")
    
    # クラス選択
    selected_class = st.session_state.get('selected_class', 'english_specific_a')
    classes = st.session_state.get('teacher_classes', {})
    course_id = None
    
    if selected_class in classes:
        current_class = classes[selected_class]
        course_id = current_class.get('course_id')
        st.info(f"📚 **{current_class['name']}** の成績集計")
    
    # タブ
    tab1, tab2, tab3, tab4 = st.tabs([
        "📊 成績一覧",
        "⚙️ 配分設定",
        "📈 統計・分析",
        "📥 エクスポート"
    ])
    
    with tab1:
        show_grade_list(course_id)
    with tab2:
        show_grade_settings()
    with tab3:
        show_grade_statistics(course_id)
    with tab4:
        show_export_options(course_id)


def _load_students_for_grades(course_id: str) -> list:
    """成績用の学生データをDBから取得"""
    if not course_id:
        return []
    try:
        from utils.database import get_students_with_activity_summary
        return get_students_with_activity_summary(course_id)
    except Exception as e:
        st.error(f"学生データの取得に失敗しました: {e}")
        return []


def show_grade_list(course_id: str):
    """成績一覧"""
    
    st.markdown("### 📊 成績一覧")
    
    if not course_id:
        st.warning("コースが選択されていません")
        return
    
    students = _load_students_for_grades(course_id)
    
    if not students:
        st.info("まだ学生データがありません。学生が登録し、課題を提出すると成績が表示されます。")
        return
    
    # 成績配分（デフォルト）
    weights = st.session_state.get('grade_weights', {
        "assignment": 50,
        "practice": 20,
        "final": 20,
        "participation": 10
    })
    
    # フィルタ・ソート
    col1, col2, col3 = st.columns(3)
    with col1:
        sort_by = st.selectbox("ソート", ["学籍番号順", "合計点順（高→低）", "合計点順（低→高）", "評定順"])
    with col2:
        filter_grade = st.selectbox("評定フィルタ", ["全て", "A+/A", "B+/B", "C+/C", "D/F"])
    with col3:
        search = st.text_input("🔍 検索", placeholder="名前または学籍番号")
    
    st.markdown("---")
    
    # 成績計算
    grade_data = []
    for s in students:
        assignment_score = s.get('avg_score', 0)
        
        # 練習点：練習回数ベース（上限100）
        practice_score = min(100, s.get('practice_count', 0) * 2)
        
        # 期末スコア・参加点はまだ手動入力未実装のためN/A
        final_score = 0  # TODO: 期末課題スコアをDBから取得
        participation_score = 0  # TODO: 教員の手動入力をDBから取得
        
        # 重み付け合計（入力済み項目のみ）
        total = (
            assignment_score * weights['assignment'] / 100 +
            practice_score * weights['practice'] / 100 +
            final_score * weights['final'] / 100 +
            participation_score * weights['participation'] / 100
        )
        
        # 評定
        grade = _calc_grade(total)
        
        grade_data.append({
            "name": s.get('name', ''),
            "student_id": s.get('student_id', ''),
            "user_id": s.get('user_id', ''),
            "assignment": assignment_score,
            "practice": practice_score,
            "final": final_score,
            "participation": participation_score,
            "total": total,
            "grade": grade,
            "student": s,
        })
    
    # ソート
    if sort_by == "合計点順（高→低）":
        grade_data.sort(key=lambda x: x['total'], reverse=True)
    elif sort_by == "合計点順（低→高）":
        grade_data.sort(key=lambda x: x['total'])
    elif sort_by == "評定順":
        grade_order = {"A+": 0, "A": 1, "B+": 2, "B": 3, "C+": 4, "C": 5, "D": 6, "F": 7}
        grade_data.sort(key=lambda x: grade_order.get(x['grade'], 99))
    
    # フィルタ
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
    
    # ヘッダー
    cols = st.columns([2, 1, 1, 1, 1, 1, 1, 1, 1])
    headers = ["名前", "学籍番号", f"課題({weights['assignment']}%)", f"練習({weights['practice']}%)", 
               f"期末({weights['final']}%)", f"参加({weights['participation']}%)", "合計", "評定", "操作"]
    for col, header in zip(cols, headers):
        with col:
            st.markdown(f"**{header}**")
    
    st.markdown("---")
    
    # データ表示
    for g in grade_data:
        cols = st.columns([2, 1, 1, 1, 1, 1, 1, 1, 1])
        
        with cols[0]:
            st.markdown(f"**{g['name']}**")
        with cols[1]:
            st.caption(g['student_id'])
        with cols[2]:
            st.markdown(f"{g['assignment']:.1f}" if g['assignment'] > 0 else "-")
        with cols[3]:
            st.markdown(f"{g['practice']:.1f}" if g['practice'] > 0 else "-")
        with cols[4]:
            st.markdown(f"{g['final']:.1f}" if g['final'] > 0 else "-")
        with cols[5]:
            st.markdown(f"{g['participation']:.1f}" if g['participation'] > 0 else "-")
        with cols[6]:
            st.markdown(f"**{g['total']:.1f}**" if g['total'] > 0 else "-")
        with cols[7]:
            grade_color = {
                "A+": "🟢", "A": "🟢", "B+": "🔵", "B": "🔵",
                "C+": "🟡", "C": "🟡", "D": "🟠", "F": "🔴"
            }
            st.markdown(f"{grade_color.get(g['grade'], '')} **{g['grade']}**")
        with cols[8]:
            if st.button("詳細", key=f"grade_detail_{g.get('user_id', g['student_id'])}"):
                st.session_state.selected_student = g['student']
                st.session_state['current_view'] = 'student_portfolio'
                st.rerun()
    
    st.markdown("---")
    st.caption(f"{len(grade_data)}名表示中")


def _calc_grade(total: float) -> str:
    """合計点から評定を算出"""
    if total >= 90:
        return "A+"
    elif total >= 80:
        return "A"
    elif total >= 75:
        return "B+"
    elif total >= 70:
        return "B"
    elif total >= 65:
        return "C+"
    elif total >= 60:
        return "C"
    elif total >= 50:
        return "D"
    else:
        return "F"


def show_grade_settings():
    """成績配分設定"""
    
    st.markdown("### ⚙️ 成績配分設定")
    
    st.markdown("#### 📊 評価項目と配分")
    
    current_weights = st.session_state.get('grade_weights', {
        "assignment": 50, "practice": 20, "final": 20, "participation": 10
    })
    
    col1, col2 = st.columns(2)
    
    with col1:
        assignment_weight = st.slider(
            "課題スコア平均",
            0, 100, current_weights['assignment'],
            help="課題提出の評価結果"
        )
        
        practice_weight = st.slider(
            "練習への取り組み",
            0, 100, current_weights['practice'],
            help="練習回数・頻度・改善度"
        )
    
    with col2:
        final_weight = st.slider(
            "最終テスト/期末課題",
            0, 100, current_weights['final'],
            help="期末課題のスコア"
        )
        
        participation_weight = st.slider(
            "授業参加・その他",
            0, 100, current_weights['participation'],
            help="教員の手動入力"
        )
    
    total = assignment_weight + practice_weight + final_weight + participation_weight
    
    if total == 100:
        st.success(f"✅ 合計: {total}%")
    else:
        st.error(f"❌ 合計: {total}%（100%にしてください）")
    
    st.markdown("---")
    
    st.markdown("#### 📊 練習点の算出方法")
    
    st.markdown("""
    練習点（100点満点）は以下で自動計算：
    
    | 項目 | 配分 | 説明 |
    |------|------|------|
    | 練習回数 | 40% | 目標回数に対する達成率 |
    | 練習頻度 | 30% | 週あたりの練習日数の安定性 |
    | 改善度 | 30% | 学期初めと終わりのスコア差 |
    """)
    
    col1, col2 = st.columns(2)
    with col1:
        target_practice = st.number_input("目標練習回数（学期）", 10, 100, 50)
    with col2:
        target_days = st.number_input("目標練習日数（週）", 1, 7, 4)
    
    st.markdown("---")
    
    st.markdown("#### 🏆 成績区分")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("""
        | 評定 | 点数範囲 |
        |------|---------|
        | A+ | 90〜100 |
        | A | 80〜89 |
        | B+ | 75〜79 |
        | B | 70〜74 |
        """)
    
    with col2:
        st.markdown("""
        | 評定 | 点数範囲 |
        |------|---------|
        | C+ | 65〜69 |
        | C | 60〜64 |
        | D | 50〜59 |
        | F | 〜49 |
        """)
    
    if st.button("💾 設定を保存", type="primary"):
        st.session_state['grade_weights'] = {
            "assignment": assignment_weight,
            "practice": practice_weight,
            "final": final_weight,
            "participation": participation_weight,
        }
        st.success("設定を保存しました！")


def show_grade_statistics(course_id: str):
    """統計・分析"""
    
    st.markdown("### 📈 成績統計")
    
    if not course_id:
        st.warning("コースが選択されていません")
        return
    
    students = _load_students_for_grades(course_id)
    
    if not students:
        st.info("まだ成績データがありません")
        return
    
    # 全学生のスコア
    scores = [s.get('avg_score', 0) for s in students if s.get('avg_score', 0) > 0]
    
    if not scores:
        st.info("まだスコアデータがありません")
        return
    
    import statistics
    
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("クラス平均", f"{statistics.mean(scores):.1f}点")
    with col2:
        st.metric("最高点", f"{max(scores):.1f}点")
    with col3:
        st.metric("最低点", f"{min(scores):.1f}点")
    with col4:
        stdev = statistics.stdev(scores) if len(scores) > 1 else 0
        st.metric("標準偏差", f"{stdev:.1f}")
    
    st.markdown("---")
    
    st.markdown("#### 📊 スコア分布")
    
    total = len(scores)
    score_ranges = {"90-100": 0, "80-89": 0, "70-79": 0, "60-69": 0, "50-59": 0, "~49": 0}
    
    for score in scores:
        if score >= 90:
            score_ranges["90-100"] += 1
        elif score >= 80:
            score_ranges["80-89"] += 1
        elif score >= 70:
            score_ranges["70-79"] += 1
        elif score >= 60:
            score_ranges["60-69"] += 1
        elif score >= 50:
            score_ranges["50-59"] += 1
        else:
            score_ranges["~49"] += 1
    
    max_count = max(score_ranges.values()) if score_ranges.values() else 1
    
    for range_name, count in score_ranges.items():
        col1, col2, col3 = st.columns([1, 3, 1])
        with col1:
            st.markdown(f"**{range_name}**")
        with col2:
            st.progress(count / max(max_count, 1))
        with col3:
            pct = (count / total * 100) if total > 0 else 0
            st.markdown(f"{count}名 ({pct:.0f}%)")


def show_export_options(course_id: str):
    """エクスポート"""
    
    st.markdown("### 📥 成績エクスポート")
    
    st.markdown("#### 📄 エクスポート形式")
    
    export_format = st.radio(
        "形式を選択",
        ["CSV", "Excel (.xlsx)"]
    )
    
    st.markdown("#### 📋 含める項目")
    
    col1, col2 = st.columns(2)
    with col1:
        st.checkbox("学籍番号", value=True, key="exp_sid")
        st.checkbox("氏名", value=True, key="exp_name")
        st.checkbox("課題スコア詳細", value=True, key="exp_assign")
        st.checkbox("練習スコア詳細", value=True, key="exp_practice")
    with col2:
        st.checkbox("合計点", value=True, key="exp_total")
        st.checkbox("評定", value=True, key="exp_grade")
        st.checkbox("練習回数", value=False, key="exp_count")
        st.checkbox("最終アクティブ", value=False, key="exp_active")
    
    st.markdown("---")
    
    if st.button("📥 ダウンロード", type="primary", use_container_width=True):
        if not course_id:
            st.warning("コースが選択されていません")
            return
        
        students = _load_students_for_grades(course_id)
        if not students:
            st.warning("エクスポートするデータがありません")
            return
        
        import pandas as pd
        
        weights = st.session_state.get('grade_weights', {
            "assignment": 50, "practice": 20, "final": 20, "participation": 10
        })
        
        rows = []
        for s in students:
            assignment_score = s.get('avg_score', 0)
            practice_score = min(100, s.get('practice_count', 0) * 2)
            total = (
                assignment_score * weights['assignment'] / 100 +
                practice_score * weights['practice'] / 100
            )
            grade = _calc_grade(total)
            
            rows.append({
                '学籍番号': s.get('student_id', ''),
                '氏名': s.get('name', ''),
                '課題平均': round(assignment_score, 1),
                '練習点': round(practice_score, 1),
                '合計': round(total, 1),
                '評定': grade,
                '練習回数': s.get('practice_count', 0),
                '最終アクティブ(日前)': s.get('days_since_active', '-'),
            })
        
        df = pd.DataFrame(rows)
        
        csv = df.to_csv(index=False).encode('utf-8-sig')
        st.download_button(
            "📤 CSVダウンロード",
            csv,
            f"grades_{datetime.now().strftime('%Y%m%d')}.csv",
            "text/csv"
        )
    
    st.markdown("---")
    
    st.markdown("#### 🔄 一括インポート")
    st.caption("参加点などを一括で入力する場合")
    
    uploaded = st.file_uploader("CSVファイルをアップロード", type=['csv'])
    if uploaded:
        import pandas as pd
        try:
            df = pd.read_csv(uploaded)
            st.dataframe(df, use_container_width=True)
            st.info("インポート機能は今後実装予定です")
        except Exception as e:
            st.error(f"エラー: {e}")
