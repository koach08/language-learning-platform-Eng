import streamlit as st
from datetime import datetime


def get_user_key():
    user = st.session_state.get('user')
    if user:
        return user.get('student_id') or user.get('email') or 'unknown'
    return 'unknown'


def get_messages_store():
    """メッセージストアを取得"""
    if 'messages_store' not in st.session_state:
        st.session_state.messages_store = {
            'direct_messages': [],
            'announcements': [],
            'question_board': [],
        }
    return st.session_state.messages_store


def send_direct_message(from_id, from_name, from_role, to_id, to_name, subject, body):
    """ダイレクトメッセージ送信"""
    store = get_messages_store()
    msg = {
        'id': f"dm_{len(store['direct_messages'])+1}",
        'from_id': from_id,
        'from_name': from_name,
        'from_role': from_role,
        'to_id': to_id,
        'to_name': to_name,
        'subject': subject,
        'body': body,
        'timestamp': datetime.now().strftime("%Y-%m-%d %H:%M"),
        'read': False,
    }
    store['direct_messages'].append(msg)
    return msg


def post_announcement(from_id, from_name, class_key, title, body, priority='normal'):
    """お知らせ投稿"""
    store = get_messages_store()
    ann = {
        'id': f"ann_{len(store['announcements'])+1}",
        'from_id': from_id,
        'from_name': from_name,
        'class_key': class_key,
        'title': title,
        'body': body,
        'priority': priority,
        'timestamp': datetime.now().strftime("%Y-%m-%d %H:%M"),
        'read_by': [],
    }
    store['announcements'].append(ann)
    return ann


def post_question(from_id, from_name, class_key, title, body, tags=None):
    """質問掲示板に投稿"""
    store = get_messages_store()
    q = {
        'id': f"q_{len(store['question_board'])+1}",
        'from_id': from_id,
        'from_name': from_name,
        'class_key': class_key,
        'title': title,
        'body': body,
        'tags': tags or [],
        'timestamp': datetime.now().strftime("%Y-%m-%d %H:%M"),
        'replies': [],
        'resolved': False,
        'upvotes': 0,
    }
    store['question_board'].append(q)
    return q


def reply_to_question(question_id, from_id, from_name, from_role, body):
    """質問に回答"""
    store = get_messages_store()
    for q in store['question_board']:
        if q['id'] == question_id:
            reply = {
                'id': f"r_{len(q['replies'])+1}",
                'from_id': from_id,
                'from_name': from_name,
                'from_role': from_role,
                'body': body,
                'timestamp': datetime.now().strftime("%Y-%m-%d %H:%M"),
                'is_best_answer': False,
            }
            q['replies'].append(reply)
            return reply
    return None


def get_unread_count(user_id):
    """未読メッセージ数"""
    store = get_messages_store()
    count = 0
    for msg in store['direct_messages']:
        if msg['to_id'] == user_id and not msg['read']:
            count += 1
    return count


def get_my_messages(user_id):
    """自分宛のメッセージ"""
    store = get_messages_store()
    return [m for m in store['direct_messages'] if m['to_id'] == user_id]


def get_sent_messages(user_id):
    """送信済みメッセージ"""
    store = get_messages_store()
    return [m for m in store['direct_messages'] if m['from_id'] == user_id]


def get_class_announcements(class_key=None):
    """クラスのお知らせ"""
    store = get_messages_store()
    if class_key:
        return [a for a in store['announcements'] if a['class_key'] == class_key]
    return store['announcements']


def get_class_questions(class_key=None):
    """クラスの質問"""
    store = get_messages_store()
    if class_key:
        return [q for q in store['question_board'] if q['class_key'] == class_key]
    return store['question_board']


# ===== 初期データ（空） =====

def init_demo_messages():
    """メッセージストアを初期化（空の状態で開始）"""
    # デモデータは使用しない。
    # 教員がお知らせを投稿するか、学生が質問を投稿するまで空。
    pass


# ===== UI表示関数 =====

def show_messaging_page(user):
    """メッセージングページ"""
    
    init_demo_messages()
    
    user_id = user.get('student_id') or user.get('email') or 'unknown'
    user_name = user.get('name', 'Unknown')
    user_role = user.get('role', 'student')
    
    st.markdown("## 💬 メッセージ / Messages")
    
    if st.button("← ホームに戻る"):
        st.session_state['current_view'] = 'teacher_home' if user_role == 'teacher' else 'student_home'
        st.rerun()
    
    unread = get_unread_count(user_id)
    if unread > 0:
        st.info(f"📩 未読メッセージが{unread}件あります")
    
    st.markdown("---")
    
    if user_role == 'teacher':
        tab1, tab2, tab3, tab4 = st.tabs(["📢 お知らせ", "📩 受信箱", "✉️ メッセージ送信", "❓ 質問掲示板"])
    else:
        tab1, tab2, tab3, tab4 = st.tabs(["📢 お知らせ", "📩 メッセージ", "✉️ 先生に質問", "❓ 質問掲示板"])
    
    with tab1:
        show_announcements_tab(user_id, user_name, user_role)
    
    with tab2:
        show_inbox_tab(user_id, user_name, user_role)
    
    with tab3:
        show_compose_tab(user_id, user_name, user_role)
    
    with tab4:
        show_question_board_tab(user_id, user_name, user_role)


def show_announcements_tab(user_id, user_name, user_role):
    """お知らせタブ"""
    
    if user_role == 'teacher':
        st.markdown("#### 📢 お知らせを投稿")
        
        class_key = st.session_state.get('selected_class', '')
        title = st.text_input("タイトル", key="ann_title")
        body = st.text_area("内容", key="ann_body", height=100)
        priority = st.radio("重要度", ["normal", "high"], format_func=lambda x: {"normal": "通常", "high": "🔴 重要"}[x], horizontal=True)
        
        if st.button("📢 投稿", type="primary"):
            if title and body:
                post_announcement(user_id, user_name, class_key, title, body, priority)
                st.success("お知らせを投稿しました！")
                st.rerun()
            else:
                st.warning("タイトルと内容を入力してください")
        
        st.markdown("---")
    
    st.markdown("#### 📋 お知らせ一覧")
    announcements = get_class_announcements()
    
    if not announcements:
        st.info("お知らせはまだありません")
        return
    
    for ann in reversed(announcements):
        priority_icon = "🔴" if ann['priority'] == 'high' else "📢"
        with st.expander(f"{priority_icon} {ann['title']} ({ann['timestamp']})"):
            st.markdown(ann['body'])
            st.caption(f"投稿者: {ann['from_name']}")


def show_inbox_tab(user_id, user_name, user_role):
    """受信箱タブ"""
    
    messages = get_my_messages(user_id)
    
    st.markdown(f"#### 📩 受信メッセージ ({len(messages)}件)")
    
    if not messages:
        st.info("メッセージはまだありません")
        return
    
    for msg in reversed(messages):
        read_icon = "📩" if not msg['read'] else "✉️"
        with st.expander(f"{read_icon} {msg['subject']} - {msg['from_name']} ({msg['timestamp']})"):
            st.markdown(msg['body'])
            st.caption(f"送信者: {msg['from_name']}")
            if not msg['read']:
                msg['read'] = True


def show_compose_tab(user_id, user_name, user_role):
    """メッセージ作成タブ"""
    
    if user_role == 'teacher':
        st.markdown("#### ✉️ メッセージ送信")
        to_name = st.text_input("宛先（学生名）", key="compose_to")
        to_id = to_name.lower().replace(' ', '_') if to_name else ''
    else:
        st.markdown("#### ✉️ 先生にメッセージ")
        to_name = "先生"
        to_id = "teacher"
    
    subject = st.text_input("件名", key="compose_subject")
    body = st.text_area("本文", key="compose_body", height=150)
    
    if st.button("📤 送信", type="primary", key="compose_send"):
        if subject and body:
            send_direct_message(user_id, user_name, user_role, to_id, to_name, subject, body)
            st.success(f"メッセージを{to_name}に送信しました！")
        else:
            st.warning("件名と本文を入力してください")


def show_question_board_tab(user_id, user_name, user_role):
    """質問掲示板タブ"""
    
    st.markdown("#### ❓ 質問掲示板")
    
    # 新規質問
    with st.expander("📝 新しい質問を投稿"):
        q_title = st.text_input("質問タイトル", key="q_title")
        q_body = st.text_area("質問内容", key="q_body", height=100)
        q_tags = st.multiselect("タグ", ["speaking", "writing", "reading", "listening", "vocabulary", "grammar", "pronunciation", "other"], key="q_tags")
        
        class_key = st.session_state.get('selected_class', 'english_1_a')
        
        if st.button("📤 質問を投稿", key="q_submit"):
            if q_title and q_body:
                post_question(user_id, user_name, class_key, q_title, q_body, q_tags)
                st.success("質問を投稿しました！")
                st.rerun()
            else:
                st.warning("タイトルと内容を入力してください")
    
    st.markdown("---")
    
    # フィルター
    filter_tag = st.selectbox("タグでフィルター", ["all"] + ["speaking", "writing", "reading", "listening", "vocabulary", "grammar", "pronunciation"],
                              format_func=lambda x: "すべて" if x == "all" else x)
    
    questions = get_class_questions()
    
    if filter_tag != "all":
        questions = [q for q in questions if filter_tag in q.get('tags', [])]
    
    if not questions:
        st.info("質問はまだありません。最初の質問を投稿してみましょう！")
        return
    
    # 質問表示
    for q in reversed(questions):
        resolved_icon = "✅" if q['resolved'] else "❓"
        reply_count = len(q.get('replies', []))
        
        with st.expander(f"{resolved_icon} {q['title']} ({reply_count}件の回答) - 👍{q['upvotes']}"):
            st.markdown(f"**{q['from_name']}** ({q['timestamp']})")
            st.markdown(q['body'])
            
            if q.get('tags'):
                st.caption(f"タグ: {', '.join(q['tags'])}")
            
            # 回答表示
            if q['replies']:
                st.markdown("---")
                st.markdown("**回答:**")
                for reply in q['replies']:
                    role_badge = "👨‍🏫" if reply['from_role'] == 'teacher' else "🎓"
                    best = "⭐ ベストアンサー" if reply.get('is_best_answer') else ""
                    st.markdown(f"{role_badge} **{reply['from_name']}** {best}")
                    st.markdown(f"> {reply['body']}")
                    st.caption(reply['timestamp'])
            
            # 回答入力
            reply_body = st.text_area("回答を入力", key=f"reply_{q['id']}", height=80)
            
            col1, col2 = st.columns(2)
            with col1:
                if st.button("💬 回答する", key=f"reply_btn_{q['id']}"):
                    if reply_body:
                        reply_to_question(q['id'], user_id, user_name, user_role, reply_body)
                        st.success("回答を投稿しました！")
                        st.rerun()
            with col2:
                if st.button(f"👍 {q['upvotes']}", key=f"upvote_{q['id']}"):
                    q['upvotes'] += 1
                    st.rerun()
