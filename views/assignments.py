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
    
    tab1, tab2, tab3 = st.tabs(["📋 課題一覧", "➕ 課題作成", "📊 提出状況"])
    
    with tab1:
        show_assignment_list()
    with tab2:
        show_create_assignment()
    with tab3:
        show_submission_status()


def show_assignment_list():
    """課題一覧"""
    
    st.markdown("### 📋 課題一覧")
    
    if 'all_assignments' not in st.session_state:
        # デモデータ
        st.session_state.all_assignments = [
            {
                "id": "assign_001",
                "title": "Week 5: Self-Introduction (Speaking)",
                "module": "speaking",
                "type": "音読",
                "deadline": (datetime.now() + timedelta(days=5)).strftime("%Y-%m-%d"),
                "created_at": datetime.now().strftime("%Y-%m-%d"),
                "status": "公開中",
                "submissions": 12,
                "total_students": 30
            },
            {
                "id": "assign_002",
                "title": "Week 5: Essay Writing",
                "module": "writing",
                "type": "エッセイ",
                "deadline": (datetime.now() + timedelta(days=7)).strftime("%Y-%m-%d"),
                "created_at": datetime.now().strftime("%Y-%m-%d"),
                "status": "公開中",
                "submissions": 8,
                "total_students": 30
            },
            {
                "id": "assign_003",
                "title": "Week 4: Vocabulary Quiz",
                "module": "vocabulary",
                "type": "クイズ",
                "deadline": (datetime.now() - timedelta(days=2)).strftime("%Y-%m-%d"),
                "created_at": (datetime.now() - timedelta(days=9)).strftime("%Y-%m-%d"),
                "status": "締切済み",
                "submissions": 28,
                "total_students": 30
            }
        ]
    
    assignments = st.session_state.all_assignments
    
    # フィルター
    col1, col2 = st.columns(2)
    with col1:
        filter_module = st.selectbox("モジュール", ["すべて", "speaking", "writing", "vocabulary", "reading", "listening"])
    with col2:
        filter_status = st.selectbox("ステータス", ["すべて", "公開中", "締切済み", "下書き"])
    
    # フィルタリング
    filtered = assignments
    if filter_module != "すべて":
        filtered = [a for a in filtered if a['module'] == filter_module]
    if filter_status != "すべて":
        filtered = [a for a in filtered if a['status'] == filter_status]
    
    st.markdown("---")
    
    if not filtered:
        st.info("該当する課題がありません")
        return
    
    for assign in filtered:
        submission_rate = (assign['submissions'] / assign['total_students'] * 100) if assign['total_students'] > 0 else 0
        
        with st.expander(f"📌 {assign['title']} ({assign['status']})"):
            col1, col2, col3 = st.columns(3)
            with col1:
                st.write(f"**モジュール:** {assign['module']}")
                st.write(f"**タイプ:** {assign['type']}")
            with col2:
                st.write(f"**締切:** {assign['deadline']}")
                st.write(f"**作成日:** {assign['created_at']}")
            with col3:
                st.metric("提出率", f"{submission_rate:.0f}%", f"{assign['submissions']}/{assign['total_students']}")
            
            col1, col2, col3 = st.columns(3)
            with col1:
                if st.button("📊 提出確認", key=f"view_{assign['id']}"):
                    st.session_state['selected_assignment'] = assign
                    st.info("Speakingモジュールの「提出確認」タブで詳細を確認できます")
            with col2:
                if st.button("✏️ 編集", key=f"edit_{assign['id']}"):
                    st.session_state[f'editing_assign_{assign["id"]}'] = True
            
            if st.session_state.get(f'editing_assign_{assign["id"]}'):
                with st.container():
                    st.markdown("---")
                    new_title = st.text_input("タイトル", value=assign.get('title', ''), key=f"edit_title_{assign['id']}")
                    new_desc = st.text_area("説明", value=assign.get('description', ''), key=f"edit_desc_{assign['id']}")
                    ecol1, ecol2 = st.columns(2)
                    with ecol1:
                        if st.button("💾 保存", key=f"save_assign_{assign['id']}"):
                            assign['title'] = new_title
                            assign['description'] = new_desc
                            del st.session_state[f'editing_assign_{assign["id"]}']
                            st.success("保存しました！")
                            st.rerun()
                    with ecol2:
                        if st.button("❌ キャンセル", key=f"cancel_assign_{assign['id']}"):
                            del st.session_state[f'editing_assign_{assign["id"]}']
                            st.rerun()
            with col3:
                if st.button("🗑️ 削除", key=f"delete_{assign['id']}"):
                    st.session_state.all_assignments.remove(assign)
                    st.success("課題を削除しました")
                    st.rerun()


def show_create_assignment():
    """課題作成"""
    
    st.markdown("### ➕ 新しい課題を作成")
    
    with st.form("create_assignment_form"):
        title = st.text_input("課題タイトル", placeholder="例: Week 6: My Favorite Movie")
        
        col1, col2 = st.columns(2)
        with col1:
            module = st.selectbox("モジュール", ["speaking", "writing", "vocabulary", "reading", "listening"])
        with col2:
            if module == "speaking":
                assign_type = st.selectbox("タイプ", ["音読（教員指定）", "音読（学生作成）", "音読（AI生成）", "スピーチ", "会話"])
            elif module == "writing":
                assign_type = st.selectbox("タイプ", ["エッセイ", "要約", "意見文", "メール作成"])
            else:
                assign_type = st.selectbox("タイプ", ["クイズ", "練習問題", "その他"])
        
        instructions = st.text_area("指示", placeholder="課題の指示を入力...")
        
        # Speaking/Writing用のテキスト
        if module in ["speaking", "writing"]:
            target_text = st.text_area("課題テキスト（該当する場合）", placeholder="学生が読む/参照するテキスト...")
        
        col1, col2 = st.columns(2)
        with col1:
            deadline = st.date_input("締切日", value=datetime.now() + timedelta(days=7))
        with col2:
            deadline_time = st.time_input("締切時間", value=datetime.strptime("23:59", "%H:%M").time())
        
        is_published = st.checkbox("すぐに公開する", value=True)
        
        submitted = st.form_submit_button("✅ 作成", type="primary")
        
        if submitted:
            if not title:
                st.error("タイトルを入力してください")
            else:
                new_assignment = {
                    "id": f"assign_{datetime.now().strftime('%Y%m%d%H%M%S')}",
                    "title": title,
                    "module": module,
                    "type": assign_type,
                    "instructions": instructions,
                    "deadline": deadline.strftime("%Y-%m-%d"),
                    "created_at": datetime.now().strftime("%Y-%m-%d"),
                    "status": "公開中" if is_published else "下書き",
                    "submissions": 0,
                    "total_students": 30
                }
                
                if 'all_assignments' not in st.session_state:
                    st.session_state.all_assignments = []
                
                st.session_state.all_assignments.insert(0, new_assignment)
                st.success(f"課題「{title}」を作成しました！")
                st.rerun()


def show_submission_status():
    """提出状況"""
    
    st.markdown("### 📊 提出状況サマリー")
    
    if 'all_assignments' not in st.session_state:
        st.info("まだ課題がありません")
        return
    
    assignments = st.session_state.all_assignments
    active = [a for a in assignments if a['status'] == '公開中']
    
    if not active:
        st.info("公開中の課題がありません")
        return
    
    # 統計
    total_submissions = sum(a['submissions'] for a in active)
    total_expected = sum(a['total_students'] for a in active)
    overall_rate = (total_submissions / total_expected * 100) if total_expected > 0 else 0
    
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("公開中の課題", f"{len(active)}件")
    with col2:
        st.metric("総提出数", f"{total_submissions}件")
    with col3:
        st.metric("全体提出率", f"{overall_rate:.1f}%")
    
    st.markdown("---")
    st.markdown("#### 課題別提出状況")
    
    import pandas as pd
    
    data = []
    for a in active:
        rate = (a['submissions'] / a['total_students'] * 100) if a['total_students'] > 0 else 0
        data.append({
            "課題": a['title'][:30] + "..." if len(a['title']) > 30 else a['title'],
            "モジュール": a['module'],
            "締切": a['deadline'],
            "提出": a['submissions'],
            "対象": a['total_students'],
            "提出率": f"{rate:.0f}%"
        })
    
    df = pd.DataFrame(data)
    st.dataframe(df, use_container_width=True, hide_index=True)
    
    # 未提出者リスト（デモ）
    st.markdown("---")
    st.markdown("#### ⚠️ 未提出者が多い課題")
    
    for a in active:
        rate = (a['submissions'] / a['total_students'] * 100) if a['total_students'] > 0 else 0
        if rate < 50:
            st.warning(f"**{a['title']}** - 提出率 {rate:.0f}% ({a['submissions']}/{a['total_students']})")
