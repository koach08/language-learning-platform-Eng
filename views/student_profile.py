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
        st.caption("受験済みのスコアがあればタブを選んで入力してください（任意）")

        # 保存済みスコアをJSONBから読み込み
        saved_scores = profile.get('test_scores') or {}

        test_tabs = st.tabs(["TOEFL-ITP", "TOEIC", "IELTS", "英検", "TOEFL iBT"])
        test_scores_input = {}

        with test_tabs[0]:
            val = st.number_input(
                "スコア（310〜677）", min_value=0, max_value=677, step=1,
                value=saved_scores.get('toefl_itp', 0) or 0,
                help="0 = 未受験", key="score_toefl_itp",
            )
            if val > 0:
                test_scores_input['toefl_itp'] = val

        with test_tabs[1]:
            val = st.number_input(
                "スコア（10〜990）", min_value=0, max_value=990, step=5,
                value=saved_scores.get('toeic', 0) or 0,
                help="0 = 未受験", key="score_toeic",
            )
            if val > 0:
                test_scores_input['toeic'] = val

        with test_tabs[2]:
            val = st.number_input(
                "Overall Band Score", min_value=0.0, max_value=9.0, step=0.5,
                value=float(saved_scores.get('ielts', 0) or 0),
                help="0 = 未受験", key="score_ielts",
            )
            if val > 0:
                test_scores_input['ielts'] = val

        with test_tabs[3]:
            eiken_options = ["（未受験）", "5級", "4級", "3級", "準2級", "2級", "準1級", "1級"]
            saved_eiken = saved_scores.get('eiken', '（未受験）')
            idx = eiken_options.index(saved_eiken) if saved_eiken in eiken_options else 0
            val = st.selectbox("取得級", eiken_options, index=idx, key="score_eiken")
            if val != "（未受験）":
                test_scores_input['eiken'] = val

        with test_tabs[4]:
            val = st.number_input(
                "スコア（0〜120）", min_value=0, max_value=120, step=1,
                value=saved_scores.get('toefl_ibt', 0) or 0,
                help="0 = 未受験", key="score_toefl_ibt",
            )
            if val > 0:
                test_scores_input['toefl_ibt'] = val

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
            'test_scores': test_scores_input if test_scores_input else None,
            # 後方互換: toefl_itp_scoreも保持
            'toefl_itp_score': test_scores_input.get('toefl_itp') if test_scores_input else None,
            'other_test_name': None,
            'other_test_score': None,
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
