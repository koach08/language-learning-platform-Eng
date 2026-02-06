import streamlit as st
from utils.auth import get_current_user, require_auth
from datetime import datetime
import random
import string


@require_auth
def show():
    user = get_current_user()
    
    if user['role'] != 'teacher':
        st.error("教員のみアクセス可能です")
        return
    
    st.markdown("## 🎓 クラス設定")
    
    tab1, tab2, tab3 = st.tabs(["📋 クラス一覧", "➕ 新規作成", "⚙️ モジュール設定"])
    
    with tab1:
        show_class_list()
    with tab2:
        show_create_class()
    with tab3:
        show_module_settings()


def show_class_list():
    """クラス一覧"""
    
    st.markdown("### 📋 クラス一覧")
    
    if 'teacher_classes' not in st.session_state:
        st.session_state.teacher_classes = {}
    
    classes = st.session_state.teacher_classes
    
    if not classes:
        st.info("まだクラスがありません。「➕ 新規作成」タブからクラスを作成してください。")
        return
    
    for class_key, class_data in classes.items():
        with st.expander(f"📚 {class_data['name']} ({class_key})"):
            col1, col2 = st.columns(2)
            with col1:
                st.write(f"**クラスコード:** `{class_key}`")
                st.write(f"**作成日:** {class_data.get('created_at', '不明')}")
            with col2:
                student_count = len(class_data.get('students', []))
                st.write(f"**登録学生数:** {student_count}名")
            
            # 有効モジュール
            modules = class_data.get('modules', {})
            enabled = [k for k, v in modules.items() if v]
            st.write(f"**有効モジュール:** {', '.join(enabled) if enabled else 'なし'}")
            
            # 削除ボタン
            if st.button("🗑️ このクラスを削除", key=f"delete_{class_key}"):
                del st.session_state.teacher_classes[class_key]
                st.success("クラスを削除しました")
                st.rerun()


def show_create_class():
    """クラス新規作成"""
    
    st.markdown("### ➕ 新しいクラスを作成")
    
    with st.form("create_class_form"):
        class_name = st.text_input("クラス名", placeholder="例: 英語コミュニケーションI（月2）")
        
        col1, col2 = st.columns(2)
        with col1:
            year = st.selectbox("年度", [2026, 2025, 2024])
        with col2:
            semester = st.selectbox("学期", ["前期", "後期", "通年"])
        
        description = st.text_area("説明（任意）", placeholder="クラスの説明...")
        
        submitted = st.form_submit_button("✅ 作成", type="primary")
        
        if submitted:
            if not class_name:
                st.error("クラス名を入力してください")
            else:
                # クラスコード生成
                class_key = ''.join(random.choices(string.ascii_uppercase + string.digits, k=6))
                
                if 'teacher_classes' not in st.session_state:
                    st.session_state.teacher_classes = {}
                
                st.session_state.teacher_classes[class_key] = {
                    'name': class_name,
                    'year': year,
                    'semester': semester,
                    'description': description,
                    'created_at': datetime.now().strftime("%Y-%m-%d"),
                    'students': [],
                    'modules': {
                        'speaking': True,
                        'writing': True,
                        'vocabulary': True,
                        'reading': True,
                        'listening': True,
                        'test_prep': False
                    }
                }
                
                st.success(f"クラスを作成しました！")
                st.info(f"📋 **クラスコード:** `{class_key}`\n\nこのコードを学生に共有してください。")
                st.rerun()


def show_module_settings():
    """モジュール設定"""
    
    st.markdown("### ⚙️ モジュール設定")
    
    if 'teacher_classes' not in st.session_state or not st.session_state.teacher_classes:
        st.info("先にクラスを作成してください")
        return
    
    classes = st.session_state.teacher_classes
    
    selected_key = st.selectbox(
        "クラスを選択",
        list(classes.keys()),
        format_func=lambda x: f"{classes[x]['name']} ({x})"
    )
    
    if selected_key:
        class_data = classes[selected_key]
        modules = class_data.get('modules', {})
        
        st.markdown("---")
        st.markdown("#### 有効にするモジュール")
        
        col1, col2 = st.columns(2)
        
        with col1:
            speaking = st.checkbox("🗣️ Speaking", value=modules.get('speaking', True))
            writing = st.checkbox("✍️ Writing", value=modules.get('writing', True))
            vocabulary = st.checkbox("📚 Vocabulary", value=modules.get('vocabulary', True))
        
        with col2:
            reading = st.checkbox("📖 Reading", value=modules.get('reading', True))
            listening = st.checkbox("🎧 Listening", value=modules.get('listening', True))
            test_prep = st.checkbox("📝 検定対策", value=modules.get('test_prep', False))
        
        if st.button("💾 保存", type="primary"):
            class_data['modules'] = {
                'speaking': speaking,
                'writing': writing,
                'vocabulary': vocabulary,
                'reading': reading,
                'listening': listening,
                'test_prep': test_prep
            }
            st.success("設定を保存しました！")
            st.rerun()
