import streamlit as st
from utils.auth import get_current_user, require_auth
import random

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
    
    if selected_class in classes:
        current_class = classes[selected_class]
        st.info(f"📚 **{current_class['name']}** の成績集計")
    
    # タブ
    tab1, tab2, tab3, tab4 = st.tabs([
        "📊 成績一覧",
        "⚙️ 配分設定",
        "📈 統計・分析",
        "📥 エクスポート"
    ])
    
    with tab1:
        show_grade_list()
    with tab2:
        show_grade_settings()
    with tab3:
        show_grade_statistics()
    with tab4:
        show_export_options()


def show_grade_list():
    """成績一覧"""
    
    st.markdown("### 📊 成績一覧")
    
    # デモ用学生データ
    if 'demo_students' not in st.session_state:
        from views.teacher_dashboard import generate_demo_students
        st.session_state.demo_students = generate_demo_students(50)
    
    students = st.session_state.demo_students
    
    # 成績配分（デフォルト）
    weights = {
        "assignment": 50,
        "practice": 20,
        "final": 20,
        "participation": 10
    }
    
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
        # 各項目のスコア計算
        assignment_score = s['avg_score']
        practice_score = min(100, s['practice_count'] * 2)  # 練習回数×2（上限100）
        final_score = s['avg_score'] + random.randint(-5, 10)
        participation_score = random.randint(60, 100)
        
        # 重み付け合計
        total = (
            assignment_score * weights['assignment'] / 100 +
            practice_score * weights['practice'] / 100 +
            final_score * weights['final'] / 100 +
            participation_score * weights['participation'] / 100
        )
        
        # 評定
        if total >= 90:
            grade = "A+"
        elif total >= 80:
            grade = "A"
        elif total >= 75:
            grade = "B+"
        elif total >= 70:
            grade = "B"
        elif total >= 65:
            grade = "C+"
        elif total >= 60:
            grade = "C"
        elif total >= 50:
            grade = "D"
        else:
            grade = "F"
        
        grade_data.append({
            "name": s['name'],
            "student_id": s['student_id'],
            "assignment": assignment_score,
            "practice": practice_score,
            "final": final_score,
            "participation": participation_score,
            "total": total,
            "grade": grade,
            "student": s
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
            st.markdown(f"{g['assignment']:.1f}")
        with cols[3]:
            st.markdown(f"{g['practice']:.1f}")
        with cols[4]:
            st.markdown(f"{g['final']:.1f}")
        with cols[5]:
            st.markdown(f"{g['participation']:.1f}")
        with cols[6]:
            st.markdown(f"**{g['total']:.1f}**")
        with cols[7]:
            grade_color = {
                "A+": "🟢", "A": "🟢", "B+": "🔵", "B": "🔵",
                "C+": "🟡", "C": "🟡", "D": "🟠", "F": "🔴"
            }
            st.markdown(f"{grade_color.get(g['grade'], '')} **{g['grade']}**")
        with cols[8]:
            if st.button("詳細", key=f"grade_detail_{g['student_id']}"):
                st.session_state.selected_student = g['student']
                st.session_state['current_view'] = 'student_portfolio'
                st.rerun()
    
    st.markdown("---")
    st.caption(f"{len(grade_data)}名表示中")


def show_grade_settings():
    """成績配分設定"""
    
    st.markdown("### ⚙️ 成績配分設定")
    
    st.markdown("#### 📊 評価項目と配分")
    
    col1, col2 = st.columns(2)
    
    with col1:
        assignment_weight = st.slider(
            "課題スコア平均",
            0, 100, 50,
            help="課題提出の評価結果"
        )
        
        practice_weight = st.slider(
            "練習への取り組み",
            0, 100, 20,
            help="練習回数・頻度・改善度"
        )
    
    with col2:
        final_weight = st.slider(
            "最終テスト/期末課題",
            0, 100, 20,
            help="期末課題のスコア"
        )
        
        participation_weight = st.slider(
            "授業参加・その他",
            0, 100, 10,
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
        st.success("設定を保存しました！")


def show_grade_statistics():
    """統計・分析"""
    
    st.markdown("### 📈 成績統計")
    
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("クラス平均", "72.5点")
    with col2:
        st.metric("最高点", "95点")
    with col3:
        st.metric("最低点", "35点")
    with col4:
        st.metric("標準偏差", "12.3")
    
    st.markdown("---")
    
    st.markdown("#### 📊 評定分布")
    
    grades = {"A+": 5, "A": 12, "B+": 8, "B": 10, "C+": 6, "C": 5, "D": 3, "F": 1}
    
    for grade, count in grades.items():
        col1, col2, col3 = st.columns([1, 3, 1])
        with col1:
            st.markdown(f"**{grade}**")
        with col2:
            st.progress(count / 50)
        with col3:
            st.markdown(f"{count}名 ({count*2}%)")
    
    st.markdown("---")
    
    st.markdown("#### 📈 スコア分布ヒストグラム")
    
    score_ranges = {
        "90-100": 5,
        "80-89": 12,
        "70-79": 18,
        "60-69": 10,
        "50-59": 4,
        "~49": 1
    }
    
    for range_name, count in score_ranges.items():
        col1, col2, col3 = st.columns([1, 3, 1])
        with col1:
            st.markdown(f"**{range_name}**")
        with col2:
            st.progress(count / 20)
        with col3:
            st.markdown(f"{count}名")


def show_export_options():
    """エクスポート"""
    
    st.markdown("### 📥 成績エクスポート")
    
    st.markdown("#### 📄 エクスポート形式")
    
    export_format = st.radio(
        "形式を選択",
        ["CSV", "Excel (.xlsx)", "PDF（成績表）"]
    )
    
    st.markdown("#### 📋 含める項目")
    
    col1, col2 = st.columns(2)
    with col1:
        st.checkbox("学籍番号", value=True)
        st.checkbox("氏名", value=True)
        st.checkbox("課題スコア詳細", value=True)
        st.checkbox("練習スコア詳細", value=True)
    with col2:
        st.checkbox("合計点", value=True)
        st.checkbox("評定", value=True)
        st.checkbox("コメント", value=False)
        st.checkbox("学習履歴", value=False)
    
    st.markdown("---")
    
    col1, col2 = st.columns(2)
    with col1:
        if st.button("📥 ダウンロード", type="primary", use_container_width=True):
            st.success(f"{export_format}ファイルをダウンロードしました！（※デモ）")
    with col2:
        if st.button("📧 メールで送信", use_container_width=True):
            st.success("メールで送信しました！（※デモ）")
    
    st.markdown("---")
    
    st.markdown("#### 🔄 一括インポート")
    st.caption("参加点などを一括で入力する場合")
    
    uploaded = st.file_uploader("CSVファイルをアップロード", type=['csv'])
    if uploaded:
        st.success("ファイルを読み込みました！（※デモ）")
