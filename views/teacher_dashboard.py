import streamlit as st
from utils.auth import get_current_user, require_auth
import random

@require_auth
def show():
    user = get_current_user()
    
    st.markdown("## 📊 クラスダッシュボード")
    
    if st.button("← 教員ホームに戻る"):
        st.session_state['current_view'] = 'teacher_home'
        st.rerun()
    
    st.markdown("---")
    
    # クラス選択
    classes = st.session_state.get('teacher_classes', {})
    
    if not classes:
        st.warning("まだクラスが作成されていません")
        return
    
    selected_class = st.session_state.get('selected_class', list(classes.keys())[0])
    
    if selected_class not in classes:
        selected_class = list(classes.keys())[0]
    
    current_class = classes[selected_class]
    
    # 学生数を取得（class_studentsから）
    class_students = st.session_state.get('class_students', {}).get(selected_class, [])
    student_count = len(class_students)
    
    st.info(f"📚 **{current_class['name']}**")
    st.caption(f"クラスコード: `{current_class.get('code', 'N/A')}` | 登録学生: {student_count}名")
    
    st.markdown("---")
    
    # デモ用学生データがなければ生成
    if not class_students and 'demo_students' not in st.session_state:
        st.session_state.demo_students = generate_demo_students(50)
        st.session_state.class_students = assign_students_to_classes(
            st.session_state.demo_students,
            classes
        )
        class_students = st.session_state.class_students.get(selected_class, [])
        student_count = len(class_students)
    
    # サマリーメトリクス
    show_summary_metrics(class_students)
    
    # スコア分布
    show_score_distribution(class_students)
    
    # クラス全体の弱点
    show_class_weaknesses(class_students)
    
    # 課題状況
    show_assignment_status()
    
    # 要注意学生
    show_at_risk_students(class_students)
    
    # 学生一覧
    show_student_list(class_students)


def show_summary_metrics(students):
    """サマリーメトリクス"""
    
    st.markdown("### 📈 クラスサマリー")
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        if students:
            avg = sum(s.get('avg_score', 0) for s in students) / len(students)
            st.metric("クラス平均", f"{avg:.1f}点", "+2.3")
        else:
            st.metric("クラス平均", "-")
    
    with col2:
        if students:
            active = len([s for s in students if s.get('days_since_active', 99) <= 7])
            rate = (active / len(students) * 100) if students else 0
            st.metric("今週の練習率", f"{rate:.0f}%", "+5%")
        else:
            st.metric("今週の練習率", "-")
    
    with col3:
        st.metric("課題提出率", "85%", "+3%")
    
    with col4:
        if students:
            at_risk = len([s for s in students if s.get('days_since_active', 0) > 7 or s.get('avg_score', 100) < 50])
            st.metric("要注意学生", f"{at_risk}名")
        else:
            st.metric("要注意学生", "0名")


def show_score_distribution(students):
    """スコア分布"""
    
    st.markdown("---")
    st.markdown("### 📊 スコア分布")
    
    if not students:
        st.info("学生データがありません")
        return
    
    # スコア分布を計算
    ranges = {"90-100": 0, "80-89": 0, "70-79": 0, "60-69": 0, "50-59": 0, "~49": 0}
    
    for s in students:
        score = s.get('avg_score', 0)
        if score >= 90:
            ranges["90-100"] += 1
        elif score >= 80:
            ranges["80-89"] += 1
        elif score >= 70:
            ranges["70-79"] += 1
        elif score >= 60:
            ranges["60-69"] += 1
        elif score >= 50:
            ranges["50-59"] += 1
        else:
            ranges["~49"] += 1
    
    for range_name, count in ranges.items():
        col1, col2, col3 = st.columns([1, 3, 1])
        with col1:
            st.markdown(f"**{range_name}**")
        with col2:
            st.progress(count / max(len(students), 1))
        with col3:
            st.markdown(f"{count}名")


def show_class_weaknesses(students):
    """クラス全体の弱点"""
    
    st.markdown("---")
    st.markdown("### 🎯 クラス全体の弱点 TOP3")
    
    weaknesses = [
        {"issue": "th音 → /s/ 置換", "module": "Speaking", "percent": 62},
        {"issue": "冠詞の誤用 (a/the)", "module": "Writing", "percent": 55},
        {"issue": "語末の -ed 発音", "module": "Speaking", "percent": 48},
    ]
    
    for w in weaknesses:
        col1, col2, col3 = st.columns([3, 1, 1])
        with col1:
            st.markdown(f"🔴 **{w['issue']}**")
            st.caption(w['module'])
        with col2:
            st.progress(w['percent'] / 100)
        with col3:
            st.markdown(f"{w['percent']}%")


def show_assignment_status():
    """課題状況"""
    
    st.markdown("---")
    st.markdown("### 📝 課題状況")
    
    assignments = [
        {"name": "課題1: Self-Introduction", "submitted": 48, "total": 50, "avg": 72.5, "due": "2025/04/15"},
        {"name": "課題2: Reading Aloud", "submitted": 45, "total": 50, "avg": 68.3, "due": "2025/05/01"},
        {"name": "課題3: Speech", "submitted": 30, "total": 50, "avg": 75.1, "due": "2025/05/15"},
    ]
    
    for a in assignments:
        col1, col2, col3, col4 = st.columns([3, 1, 1, 1])
        with col1:
            st.markdown(f"**{a['name']}**")
            st.caption(f"締切: {a['due']}")
        with col2:
            st.markdown(f"{a['submitted']}/{a['total']}")
        with col3:
            st.markdown(f"平均 {a['avg']:.1f}点")
        with col4:
            if st.button("詳細", key=f"assign_{a['name']}"):
                st.session_state['current_view'] = 'assignments'
                st.rerun()


def show_at_risk_students(students):
    """要注意学生"""
    
    st.markdown("---")
    st.markdown("### ⚠️ 要注意学生")
    
    if not students:
        st.info("学生データがありません")
        return
    
    at_risk = [s for s in students if s.get('days_since_active', 0) > 7 or s.get('avg_score', 100) < 50]
    
    if not at_risk:
        st.success("✅ 要注意学生はいません")
        return
    
    # 深刻度でソート
    at_risk.sort(key=lambda x: (x.get('days_since_active', 0), -x.get('avg_score', 0)), reverse=True)
    
    for s in at_risk[:5]:
        issues = []
        if s.get('days_since_active', 0) > 7:
            issues.append(f"🔴 {s.get('days_since_active', 0)}日間活動なし")
        if s.get('avg_score', 100) < 50:
            issues.append(f"🔴 平均スコア {s.get('avg_score', 0):.1f}点")
        
        col1, col2, col3 = st.columns([2, 2, 1])
        with col1:
            st.markdown(f"**{s['name']}**")
            st.caption(s.get('student_id', ''))
        with col2:
            st.markdown(", ".join(issues))
        with col3:
            if st.button("詳細", key=f"risk_{s.get('student_id', s['name'])}"):
                st.session_state.selected_student = s
                st.session_state['current_view'] = 'student_portfolio'
                st.rerun()


def show_student_list(students):
    """学生一覧"""
    
    st.markdown("---")
    st.markdown("### 👥 学生一覧")
    
    if not students:
        st.info("学生データがありません")
        return
    
    # フィルタ
    col1, col2, col3 = st.columns(3)
    with col1:
        sort_by = st.selectbox("ソート", ["学籍番号順", "スコア順", "活動順"], key="dash_sort")
    with col2:
        filter_by = st.selectbox("フィルタ", ["全員", "要注意のみ", "高得点者"], key="dash_filter")
    with col3:
        if st.button("📥 CSV出力", key="dash_csv"):
            st.success("CSVをダウンロードしました（※デモ）")
    
    # フィルタ処理
    filtered = students.copy()
    
    if filter_by == "要注意のみ":
        filtered = [s for s in filtered if s.get('days_since_active', 0) > 7 or s.get('avg_score', 100) < 50]
    elif filter_by == "高得点者":
        filtered = [s for s in filtered if s.get('avg_score', 0) >= 80]
    
    # ソート
    if sort_by == "スコア順":
        filtered.sort(key=lambda x: x.get('avg_score', 0), reverse=True)
    elif sort_by == "活動順":
        filtered.sort(key=lambda x: x.get('days_since_active', 99))
    
    st.caption(f"{len(filtered)}名表示中")
    
    # 学生リスト
    for s in filtered[:20]:
        col1, col2, col3, col4, col5 = st.columns([2, 1, 1, 1, 1])
        
        with col1:
            if s.get('days_since_active', 0) > 7 or s.get('avg_score', 100) < 50:
                st.markdown(f"⚠️ **{s['name']}**")
            else:
                st.markdown(f"**{s['name']}**")
            st.caption(s.get('student_id', ''))
        
        with col2:
            score = s.get('avg_score', 0)
            color = "🟢" if score >= 70 else "🟡" if score >= 50 else "🔴"
            st.markdown(f"{color} {score:.1f}")
        
        with col3:
            st.markdown(f"{s.get('practice_count', 0)}回")
        
        with col4:
            days = s.get('days_since_active', 0)
            if days == 0:
                st.markdown("今日")
            elif days <= 3:
                st.markdown(f"{days}日前")
            else:
                st.markdown(f"🔴 {days}日前")
        
        with col5:
            if st.button("👤", key=f"dash_detail_{s.get('student_id', s['name'])}"):
                st.session_state.selected_student = s
                st.session_state['current_view'] = 'student_portfolio'
                st.rerun()
    
    if len(filtered) > 20:
        st.caption(f"... 他 {len(filtered) - 20}名")
        if st.button("全学生を見る"):
            st.session_state['current_view'] = 'student_management'
            st.rerun()


def generate_demo_students(n):
    """デモ学生生成"""
    last_names = ["田中", "鈴木", "佐藤", "山田", "渡辺", "伊藤", "中村", "小林", "加藤", "吉田"]
    first_names = ["太郎", "花子", "一郎", "美咲", "健", "さくら", "大輔", "愛", "翔", "結衣"]
    
    students = []
    for i in range(n):
        name = f"{random.choice(last_names)}{random.choice(first_names)}"
        students.append({
            "name": name,
            "student_id": f"24A{str(i+1).zfill(3)}",
            "avg_score": max(20, min(100, random.gauss(70, 15))),
            "practice_count": random.randint(0, 80),
            "days_since_active": random.choices([0, 1, 2, 3, 5, 7, 10, 14], weights=[20, 15, 15, 10, 10, 8, 7, 5])[0],
            "assignments_submitted": random.randint(0, 4),
            "pronunciation_score": random.randint(50, 90),
            "fluency_score": random.randint(50, 90),
            "grammar_score": random.randint(50, 90),
        })
    return students


def assign_students_to_classes(students, classes):
    """学生をクラスに割り当て"""
    class_keys = list(classes.keys())
    class_students = {k: [] for k in class_keys}
    
    for i, student in enumerate(students):
        class_key = class_keys[i % len(class_keys)]
        student['class_key'] = class_key
        student['class_name'] = classes[class_key]['name']
        class_students[class_key].append(student)
    
    return class_students
