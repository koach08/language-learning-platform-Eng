import streamlit as st
from utils.auth import get_current_user, require_teacher

@require_teacher
def show():
    user = get_current_user()
    
    st.markdown("## ⚙️ コース設定")
    
    if st.button("← 戻る"):
        st.session_state['current_view'] = 'teacher_home'
        st.rerun()
    
    st.markdown("---")
    st.markdown("### ➕ 新しいコースを作成")
    
    with st.form("create_course"):
        name = st.text_input("コース名", placeholder="例: 英語I（前期）")
        
        template = st.selectbox("テンプレート", [
            "アウトプット重視（発信）",
            "インプット重視（受信）",
            "基礎能力全般",
            "TOEFL-ITP + 独学スキル",
            "PBL・専門科目英語"
        ])
        
        submitted = st.form_submit_button("作成", type="primary")
        
        if submitted:
            if name:
                st.success(f"コース「{name}」を作成しました！（※デモ表示）")
                st.info("本番ではデータベースに保存されます")
            else:
                st.error("コース名を入力してください")
