"""
Login View (Simplified)
=======================
シンプルなログイン画面
"""

import streamlit as st
from utils.auth import login_with_email


def show():
    """ログイン画面を表示"""
    
    # ヘッダー
    st.markdown("""
    <div style="text-align: center; padding: 40px 0;">
        <h1>🎓 English Learning Platform</h1>
        <p style="color: #666;">北海道大学 英語学習プラットフォーム</p>
    </div>
    """, unsafe_allow_html=True)
    
    # ログインフォーム
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        login_with_email()
        
        st.markdown("""
        <div style="text-align: center; margin-top: 30px; color: #888; font-size: 0.9rem;">
            <p>📝 テスト用ログイン</p>
            <p>教員メールアドレスでログインすると教員画面が表示されます</p>
        </div>
        """, unsafe_allow_html=True)


def show_registration_form():
    """初回登録フォーム（学生用）"""
    user = st.session_state.get('user', {})
    
    st.markdown("### 📝 学籍番号を登録")
    
    with st.form("registration_form"):
        student_id = st.text_input(
            "学籍番号",
            placeholder="例: 01234567"
        )
        
        submitted = st.form_submit_button("登録", use_container_width=True)
        
        if submitted:
            if not student_id:
                st.error("学籍番号を入力してください")
            else:
                st.session_state['user']['student_id'] = student_id
                st.success("登録完了！")
                st.rerun()
