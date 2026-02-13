"""
Student Profile View
====================
学生が自分のプロフィール情報を入力・編集する画面。
教員からも閲覧可能。
"""

import streamlit as st
from utils.auth import get_current_user, require_auth
from utils.database import get_student_profile, upsert_student_profile


@require_auth
def show():
    user = get_current_user()

    st.markdown("## 👤 マイプロフィール / My Profile")

    if st.button("← ホームに戻る"):
        view = "teacher_home" if user["role"] == "teacher" else "student_home"
        st.session_state["current_view"] = view
        st.rerun()

    st.markdown("---")

    # 現在のプロフィールを読み込み
    profile = None
    try:
        profile = get_student_profile(user['id'])
    except Exception:
        pass

    if profile is None:
        profile = {}

    # --- フォーム ---
    with st.form("profile_form"):
        st.markdown("### 📋 基本情報")

        col1, col2 = st.columns(2)
        with col1:
            student_number = st.text_input(
                "学籍番号 *",
                value=profile.get('student_number', ''),
                placeholder="例: 02240001",
            )
        with col2:
            faculty = st.text_input(
                "学部 *",
                value=profile.get('faculty', ''),
                placeholder="例: 文学部、工学部",
            )

        col1, col2 = st.columns(2)
        with col1:
            hometown = st.text_input(
                "出身地（任意）",
                value=profile.get('hometown', ''),
                placeholder="例: 北海道札幌市、東京都",
            )
        with col2:
            hobbies = st.text_input(
                "趣味（任意）",
                value=profile.get('hobbies', ''),
                placeholder="例: 読書、サッカー、料理",
            )

        st.markdown("---")
        st.markdown("### ✍️ 自己紹介")

        self_intro_ja = st.text_area(
            "自己紹介（日本語）",
            value=profile.get('self_intro_ja', ''),
            placeholder="自由に自己紹介を書いてください。",
            height=100,
        )

        self_intro_en = st.text_area(
            "Self-Introduction（英語）",
            value=profile.get('self_intro_en', ''),
            placeholder="Write a brief self-introduction in English.",
            height=100,
        )

        st.markdown("---")
        st.markdown("### 📊 語学スコア")
        st.caption("大学で受験済みのスコアがあれば入力してください（任意）")

        col1, col2 = st.columns(2)
        with col1:
            toefl_itp_score = st.number_input(
                "TOEFL-ITP スコア",
                min_value=0, max_value=677, step=1,
                value=profile.get('toefl_itp_score', 0) or 0,
                help="0の場合は未受験として扱います",
            )
        with col2:
            other_test_name = st.selectbox(
                "その他の語学検定",
                ["（なし）", "TOEIC", "IELTS", "英検", "TOEFL iBT", "その他"],
                index=0 if not profile.get('other_test_name') else
                    ["（なし）", "TOEIC", "IELTS", "英検", "TOEFL iBT", "その他"].index(
                        profile.get('other_test_name', '（なし）')
                    ) if profile.get('other_test_name') in ["（なし）", "TOEIC", "IELTS", "英検", "TOEFL iBT", "その他"] else 5,
            )

        if other_test_name != "（なし）":
            other_test_score = st.text_input(
                f"{other_test_name} スコア/級",
                value=profile.get('other_test_score', ''),
                placeholder="例: 730、6.5、準1級",
            )
        else:
            other_test_score = ""

        st.markdown("---")
        st.markdown("### 🎯 学習目標（任意）")

        english_weakness = st.text_area(
            "英語で苦手だと感じる部分",
            value=profile.get('english_weakness', ''),
            placeholder="例: リスニングが速いと聞き取れない、文法が苦手、スピーキングで言葉が出てこない",
            height=80,
        )

        english_goals = st.text_area(
            "英語で何ができるようになりたいか",
            value=profile.get('english_goals', ''),
            placeholder="例: 留学先で日常会話ができるようになりたい、英語で論文を読めるようになりたい",
            height=80,
        )

        st.markdown("---")

        submitted = st.form_submit_button("💾 保存する", type="primary", use_container_width=True)

    if submitted:
        # バリデーション
        if not student_number.strip():
            st.error("学籍番号を入力してください")
            return
        if not faculty.strip():
            st.error("学部を入力してください")
            return

        profile_data = {
            'student_number': student_number.strip(),
            'faculty': faculty.strip(),
            'hometown': hometown.strip() or None,
            'hobbies': hobbies.strip() or None,
            'self_intro_ja': self_intro_ja.strip() or None,
            'self_intro_en': self_intro_en.strip() or None,
            'toefl_itp_score': toefl_itp_score if toefl_itp_score > 0 else None,
            'other_test_name': other_test_name if other_test_name != "（なし）" else None,
            'other_test_score': other_test_score.strip() or None,
            'english_weakness': english_weakness.strip() or None,
            'english_goals': english_goals.strip() or None,
        }

        try:
            result = upsert_student_profile(user['id'], profile_data)
            if result:
                st.success("✅ プロフィールを保存しました！")
                st.balloons()
            else:
                st.error("保存に失敗しました。もう一度お試しください。")
        except Exception as e:
            st.error(f"保存エラー: {e}")
