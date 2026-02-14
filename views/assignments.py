import streamlit as st
from utils.auth import get_current_user, require_auth
from datetime import datetime, timedelta


@require_auth
def show():
    user = get_current_user()
    
    if user['role'] != 'teacher':
        st.error("教員のみアクセス可能です")
        return
    
    st.markdown("## 📝 課題管理")
    
    # コース選択
    course_id = _select_course(user)
    if not course_id:
        return
    
    tab1, tab2, tab3 = st.tabs(["📋 課題一覧", "➕ 課題作成", "📊 提出状況"])
    
    with tab1:
        show_assignment_list(course_id)
    with tab2:
        show_create_assignment(course_id)
    with tab3:
        show_submission_status(course_id)


def _select_course(user):
    """教員のコースを選択"""
    try:
        from utils.database import get_teacher_courses
        courses = get_teacher_courses(user['id'])
    except Exception as e:
        st.error(f"コース取得エラー: {e}")
        return None
    
    if not courses:
        st.warning("まだコースが登録されていません。先にクラス設定でコースを作成してください。")
        return None
    
    if len(courses) == 1:
        st.info(f"📚 **{courses[0]['name']}**")
        return courses[0]['id']
    
    selected = st.selectbox(
        "コースを選択",
        courses,
        format_func=lambda c: f"{c['name']}（{c.get('year', '')}{c.get('semester', '')}）",
    )
    return selected['id'] if selected else None


def show_assignment_list(course_id: str):
    """課題一覧（DB実データ）"""
    
    st.markdown("### 📋 課題一覧")
    
    try:
        from utils.database import get_course_assignments
        assignments = get_course_assignments(course_id)
    except Exception as e:
        st.error(f"課題の取得に失敗しました: {e}")
        return
    
    if not assignments:
        st.info("まだ課題がありません。「➕ 課題作成」タブから作成してください。")
        return
    
    for a in assignments:
        status_icon = "🟢" if a.get('is_published') else "📝"
        due = a.get('due_date', '')
        due_display = due[:10] if due else '未設定'
        
        with st.expander(f"{status_icon} {a['title']}　（締切: {due_display}）"):
            st.markdown(f"**タイプ:** {a.get('assignment_type', '')}")
            if a.get('instructions'):
                st.markdown(f"**指示:** {a['instructions']}")
            if a.get('target_text'):
                st.text_area("課題テキスト", value=a['target_text'], disabled=True, height=100,
                             key=f"txt_{a['id']}")
            
            col1, col2, col3 = st.columns(3)
            with col1:
                st.caption(f"作成: {(a.get('created_at') or '')[:10]}")
            with col2:
                st.caption(f"公開: {'はい' if a.get('is_published') else 'いいえ'}")
            with col3:
                st.caption(f"配点: {a.get('max_score', 100)}点")
            
            btn_col1, btn_col2 = st.columns(2)
            with btn_col1:
                if not a.get('is_published'):
                    if st.button("🟢 公開する", key=f"pub_{a['id']}"):
                        try:
                            from utils.database import update_assignment
                            update_assignment(a['id'], {'is_published': True})
                            st.success("公開しました")
                            st.cache_data.clear()
                            st.rerun()
                        except Exception as e:
                            st.error(f"エラー: {e}")
                else:
                    if st.button("⏸️ 非公開にする", key=f"unpub_{a['id']}"):
                        try:
                            from utils.database import update_assignment
                            update_assignment(a['id'], {'is_published': False})
                            st.success("非公開にしました")
                            st.cache_data.clear()
                            st.rerun()
                        except Exception as e:
                            st.error(f"エラー: {e}")
            with btn_col2:
                if st.button("🗑️ 削除", key=f"del_{a['id']}"):
                    try:
                        from utils.database import get_supabase_client
                        supabase = get_supabase_client()
                        supabase.table('assignments').delete().eq('id', a['id']).execute()
                        st.success("削除しました")
                        st.cache_data.clear()
                        st.rerun()
                    except Exception as e:
                        st.error(f"エラー: {e}")


ASSIGNMENT_TYPES = {
    "speaking": {
        "音読（教員指定）": "speaking_read_aloud",
        "スピーチ": "speaking_speech",
        "会話": "speaking_conversation",
    },
    "writing": {
        "エッセイ": "writing_essay",
        "要約": "writing_summary",
        "意見文": "writing_response",
    },
    "listening": {
        "リスニング理解": "listening_comprehension",
    },
    "reading": {
        "リーディング理解": "reading_comprehension",
    },
}


def show_create_assignment(course_id: str):
    """課題作成（DB保存）"""
    
    st.markdown("### ➕ 新しい課題を作成")
    
    with st.form("create_assignment_form"):
        title = st.text_input("課題タイトル", placeholder="例: Week 6: My Favorite Movie")
        
        col1, col2 = st.columns(2)
        with col1:
            module = st.selectbox("モジュール", ["speaking", "writing", "reading", "listening"])
        with col2:
            type_options = ASSIGNMENT_TYPES.get(module, {"その他": "speaking_read_aloud"})
            type_label = st.selectbox("タイプ", list(type_options.keys()))
            assignment_type = type_options[type_label]
        
        instructions = st.text_area("指示", placeholder="課題の指示を入力...")
        
        target_text = ""
        if module in ["speaking", "writing"]:
            target_text = st.text_area("課題テキスト（該当する場合）",
                                       placeholder="学生が読む/参照するテキスト...")
        
        col1, col2 = st.columns(2)
        with col1:
            deadline = st.date_input("締切日", value=datetime.now() + timedelta(days=7))
        with col2:
            deadline_time = st.time_input("締切時間",
                                          value=datetime.strptime("23:59", "%H:%M").time())
        
        max_score = st.number_input("配点", min_value=1, max_value=1000, value=100, step=10)
        is_published = st.checkbox("すぐに公開する", value=True)
        
        submitted = st.form_submit_button("✅ 作成", type="primary")
        
        if submitted:
            if not title.strip():
                st.error("タイトルを入力してください")
            else:
                try:
                    from utils.database import create_assignment
                    
                    due_datetime = datetime.combine(deadline, deadline_time).isoformat()
                    
                    result = create_assignment(
                        course_id=course_id,
                        title=title.strip(),
                        assignment_type=assignment_type,
                        instructions=instructions.strip() or None,
                        target_text=target_text.strip() or None,
                        due_date=due_datetime,
                        max_score=max_score,
                        is_published=is_published,
                    )
                    
                    if result:
                        st.success(f"✅ 課題「{title}」を作成しました！")
                        st.cache_data.clear()
                        import time
                        time.sleep(1)
                        st.rerun()
                    else:
                        st.error("課題の作成に失敗しました。もう一度お試しください。")
                except Exception as e:
                    st.error(f"課題作成エラー: {e}")


def show_submission_status(course_id: str):
    """提出状況（DB実データ）"""
    
    st.markdown("### 📊 提出状況サマリー")
    
    try:
        from utils.database import get_course_assignments, get_course_students
        assignments = get_course_assignments(course_id, published_only=True)
        students = get_course_students(course_id)
    except Exception as e:
        st.error(f"データ取得エラー: {e}")
        return
    
    if not assignments:
        st.info("公開中の課題がありません")
        return
    
    total_students = len(students) if students else 0
    
    try:
        from utils.database import get_supabase_client
        supabase = get_supabase_client()
        
        assignment_stats = []
        total_submissions = 0
        
        for a in assignments:
            subs = supabase.table('submissions')\
                .select('id')\
                .eq('assignment_id', a['id'])\
                .execute()
            sub_count = len(subs.data) if subs.data else 0
            total_submissions += sub_count
            
            assignment_stats.append({
                'title': a['title'],
                'type': a.get('assignment_type', ''),
                'due': (a.get('due_date') or '')[:10],
                'submissions': sub_count,
                'total': total_students,
                'rate': round(sub_count / total_students * 100) if total_students > 0 else 0,
            })
    except Exception as e:
        st.error(f"提出データ取得エラー: {e}")
        return
    
    total_expected = total_students * len(assignments)
    overall_rate = round(total_submissions / total_expected * 100) if total_expected > 0 else 0
    
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("公開中の課題", f"{len(assignments)}件")
    with col2:
        st.metric("総提出数", f"{total_submissions}件")
    with col3:
        st.metric("全体提出率", f"{overall_rate}%")
    
    if assignment_stats:
        st.markdown("---")
        st.markdown("#### 課題別提出状況")
        
        import pandas as pd
        df = pd.DataFrame([{
            "課題": s['title'][:30],
            "タイプ": s['type'],
            "締切": s['due'],
            "提出": s['submissions'],
            "対象": s['total'],
            "提出率": f"{s['rate']}%",
        } for s in assignment_stats])
        
        st.dataframe(df, use_container_width=True, hide_index=True)
