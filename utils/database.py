"""
Supabase Database Client
========================
データベース接続とヘルパー関数
"""

import streamlit as st
from supabase import create_client, Client
from typing import Optional, Dict, Any, List
from datetime import datetime, timedelta


# ============================================================
# Cache Helpers
# ============================================================

def clear_course_cache(course_id: str = None):
    """コース関連キャッシュをクリア（課題作成・更新後に呼ぶ）"""
    _get_course_cached.clear()
    _get_course_assignments_cached.clear()
    _get_writing_assignments_cached.clear()
    _get_speaking_materials_cached.clear()
    _get_speaking_rubric_cached.clear()
    _get_course_settings_cached.clear()
    _get_learning_resources_cached.clear()

def clear_student_cache(student_id: str = None):
    """学生関連キャッシュをクリア"""
    _get_student_courses_cached.clear()
    _get_student_practice_stats_cached.clear()
    _get_vocabulary_stats_cached.clear()


@st.cache_resource
def _create_supabase_service_client() -> Client:
    """service_role_keyクライアントをアプリ全体でキャッシュ（cache_resource）
    
    cache_resourceはStreamlitのサーバー起動時に1回だけ生成され、
    全セッションで共有される読み取り専用リソース用キャッシュ。
    supabaseクライアントはステートレスなので共有しても安全。
    cache_data内から呼んでもsession_stateにアクセスしないため警告が出ない。
    """
    url = st.secrets["supabase"]["url"]
    key = st.secrets["supabase"]["service_role_key"]
    return create_client(url, key)


@st.cache_resource
def _create_supabase_anon_client() -> Client:
    """anon_keyクライアントをアプリ全体でキャッシュ"""
    url = st.secrets["supabase"]["url"]
    key = st.secrets["supabase"]["anon_key"]
    return create_client(url, key)


def get_supabase_client(use_service_role: bool = True) -> Client:
    """Supabaseクライアントを取得

    use_service_role=True（デフォルト）: service_role_keyを使用（RLS回避）
    use_service_role=False: anon_keyを使用
    
    cache_resourceで管理するため、cache_data内から呼んでも安全。
    """
    if use_service_role:
        return _create_supabase_service_client()
    else:
        return _create_supabase_anon_client()


# ============================================================
# User Operations
# ============================================================

def get_user_by_email(email: str) -> Optional[Dict]:
    """メールアドレスでユーザーを取得"""
    supabase = get_supabase_client()
    result = supabase.table('users').select('*').eq('email', email).execute()
    return result.data[0] if result.data else None


def create_user(email: str, name: str, role: str = 'student', 
                student_id: str = None, profile_image_url: str = None) -> Dict:
    """新規ユーザーを作成"""
    supabase = get_supabase_client()
    user_data = {
        'email': email,
        'name': name,
        'role': role,
        'student_id': student_id,
        'profile_image_url': profile_image_url
    }
    result = supabase.table('users').insert(user_data).execute()
    return result.data[0] if result.data else None


def update_user(user_id: str, updates: Dict) -> Dict:
    """ユーザー情報を更新"""
    supabase = get_supabase_client()
    updates['updated_at'] = datetime.utcnow().isoformat()
    result = supabase.table('users').update(updates).eq('id', user_id).execute()
    return result.data[0] if result.data else None


def get_or_create_user(email: str, name: str, profile_image_url: str = None) -> Dict:
    """ユーザーを取得、存在しなければ作成"""
    user = get_user_by_email(email)
    if user:
        # プロフィール画像を更新（Googleから取得した場合）
        if profile_image_url and user.get('profile_image_url') != profile_image_url:
            update_user(user['id'], {'profile_image_url': profile_image_url})
            user['profile_image_url'] = profile_image_url
        return user
    
    # 教員メールリストをチェック
    teacher_emails = st.secrets.get("app", {}).get("teacher_emails", "")
    if isinstance(teacher_emails, str):
        teacher_emails = [e.strip() for e in teacher_emails.split(',')]
    
    role = 'teacher' if email in teacher_emails else 'student'
    return create_user(email, name, role, profile_image_url=profile_image_url)


# ============================================================
# Course Operations
# ============================================================

def get_teacher_courses(teacher_id: str) -> List[Dict]:
    """教員の担当コースを取得（キャッシュ付き）"""
    return _get_teacher_courses_cached(teacher_id)

@st.cache_data(ttl=120)
def _get_teacher_courses_cached(teacher_id: str) -> List[Dict]:
    supabase = get_supabase_client()
    result = supabase.table('courses')\
        .select('*')\
        .eq('teacher_id', teacher_id)\
        .eq('is_active', True)\
        .order('created_at', desc=True)\
        .execute()
    return result.data


def get_student_courses(student_id: str) -> List[Dict]:
    """学生の履修コースを取得（キャッシュ付き）"""
    return _get_student_courses_cached(student_id)

@st.cache_data(ttl=120)
def _get_student_courses_cached(student_id: str) -> List[Dict]:
    supabase = get_supabase_client()
    result = supabase.table('enrollments')\
        .select('*, courses(*)')\
        .eq('student_id', student_id)\
        .execute()
    return [e['courses'] for e in result.data if e.get('courses')]


def create_course(teacher_id: str, name: str, year: int, semester: str,
                  template_type: str = 'custom', **kwargs) -> Dict:
    """コースを作成"""
    supabase = get_supabase_client()
    course_data = {
        'teacher_id': teacher_id,
        'name': name,
        'year': year,
        'semester': semester,
        'template_type': template_type,
        **kwargs
    }
    result = supabase.table('courses').insert(course_data).execute()
    clear_course_cache()  # キャッシュクリア
    return result.data[0] if result.data else None


def get_course(course_id: str) -> Optional[Dict]:
    """コースを取得（キャッシュ付き）"""
    return _get_course_cached(course_id)

@st.cache_data(ttl=300)  # 5分キャッシュ
def _get_course_cached(course_id: str) -> Optional[Dict]:
    supabase = get_supabase_client()
    result = supabase.table('courses').select('*').eq('id', course_id).execute()
    return result.data[0] if result.data else None


def update_course(course_id: str, updates: Dict) -> Dict:
    """コースを更新"""
    supabase = get_supabase_client()
    updates['updated_at'] = datetime.utcnow().isoformat()
    result = supabase.table('courses').update(updates).eq('id', course_id).execute()
    clear_course_cache(course_id)  # キャッシュクリア
    return result.data[0] if result.data else None


# ============================================================
# Enrollment Operations
# ============================================================

def enroll_student(student_id: str, course_id: str) -> Dict:
    """学生をコースに登録"""
    supabase = get_supabase_client()
    result = supabase.table('enrollments').insert({
        'student_id': student_id,
        'course_id': course_id
    }).execute()
    return result.data[0] if result.data else None


def get_course_students(course_id: str) -> List[Dict]:
    """コースの学生一覧を取得"""
    supabase = get_supabase_client()
    result = supabase.table('enrollments')\
        .select('*, users(*)')\
        .eq('course_id', course_id)\
        .execute()
    return [e['users'] for e in result.data if e.get('users')]


def unenroll_student(student_id: str, course_id: str) -> bool:
    """学生をコースから削除"""
    supabase = get_supabase_client()
    result = supabase.table('enrollments')\
        .delete()\
        .eq('student_id', student_id)\
        .eq('course_id', course_id)\
        .execute()
    return len(result.data) > 0


def get_course_by_class_code(class_code: str) -> Optional[Dict]:
    """クラスコードでコースを検索"""
    supabase = get_supabase_client()
    result = supabase.table('courses')\
        .select('*')\
        .eq('class_code', class_code)\
        .eq('is_active', True)\
        .execute()
    return result.data[0] if result.data else None


def get_student_enrollments(student_id: str) -> List[Dict]:
    """学生の履修コース一覧を取得"""
    supabase = get_supabase_client()
    result = supabase.table('enrollments')\
        .select('*, courses(*)')\
        .eq('student_id', student_id)\
        .execute()
    return result.data


def get_all_students() -> List[Dict]:
    """全学生一覧を取得（教員用）"""
    supabase = get_supabase_client()
    result = supabase.table('users')\
        .select('*')\
        .eq('role', 'student')\
        .order('name')\
        .execute()
    return result.data


# ============================================================
# Assignment Operations
# ============================================================

def create_assignment(course_id: str, title: str, assignment_type: str, **kwargs) -> Dict:
    """課題を作成"""
    supabase = get_supabase_client()
    assignment_data = {
        'course_id': course_id,
        'title': title,
        'assignment_type': assignment_type,
        **kwargs
    }
    result = supabase.table('assignments').insert(assignment_data).execute()
    clear_course_cache(course_id)  # キャッシュクリア
    return result.data[0] if result.data else None


def get_course_assignments(course_id: str, published_only: bool = False) -> List[Dict]:
    """コースの課題一覧を取得（キャッシュ付き）"""
    return _get_course_assignments_cached(course_id, published_only)

@st.cache_data(ttl=120)
def _get_course_assignments_cached(course_id: str, published_only: bool = False) -> List[Dict]:
    supabase = get_supabase_client()
    query = supabase.table('assignments').select('*').eq('course_id', course_id)
    if published_only:
        query = query.eq('is_published', True)
    result = query.order('due_date').execute()
    return result.data


def get_assignment(assignment_id: str) -> Optional[Dict]:
    """課題を取得"""
    supabase = get_supabase_client()
    result = supabase.table('assignments').select('*').eq('id', assignment_id).execute()
    return result.data[0] if result.data else None


# ============================================================
# Submission Operations
# ============================================================

def create_submission(student_id: str, assignment_id: str, 
                      content_type: str, **kwargs) -> Dict:
    """提出を作成"""
    supabase = get_supabase_client()
    submission_data = {
        'student_id': student_id,
        'assignment_id': assignment_id,
        'content_type': content_type,
        **kwargs
    }
    result = supabase.table('submissions').insert(submission_data).execute()
    return result.data[0] if result.data else None


def get_student_submissions(student_id: str, assignment_id: str = None) -> List[Dict]:
    """学生の提出を取得"""
    supabase = get_supabase_client()
    query = supabase.table('submissions').select('*').eq('student_id', student_id)
    if assignment_id:
        query = query.eq('assignment_id', assignment_id)
    result = query.order('submitted_at', desc=True).execute()
    return result.data


def get_assignment_submissions(assignment_id: str) -> List[Dict]:
    """課題の全提出を取得（教員用）"""
    supabase = get_supabase_client()
    result = supabase.table('submissions')\
        .select('*, users(name, email, student_id)')\
        .eq('assignment_id', assignment_id)\
        .order('submitted_at', desc=True)\
        .execute()
    return result.data


def update_submission(submission_id: str, updates: Dict) -> Dict:
    """提出を更新"""
    supabase = get_supabase_client()
    result = supabase.table('submissions').update(updates).eq('id', submission_id).execute()
    return result.data[0] if result.data else None


# ============================================================
# Chat Session Operations
# ============================================================

def create_chat_session(student_id: str, course_id: str = None, 
                        topic: str = None, **kwargs) -> Dict:
    """AI対話セッションを作成"""
    supabase = get_supabase_client()
    session_data = {
        'student_id': student_id,
        'course_id': course_id,
        'topic': topic,
        'messages': [],
        **kwargs
    }
    result = supabase.table('chat_sessions').insert(session_data).execute()
    return result.data[0] if result.data else None


def update_chat_session(session_id: str, updates: Dict) -> Dict:
    """チャットセッションを更新"""
    supabase = get_supabase_client()
    result = supabase.table('chat_sessions').update(updates).eq('id', session_id).execute()
    return result.data[0] if result.data else None


def get_student_chat_sessions(student_id: str, limit: int = 20) -> List[Dict]:
    """学生のチャットセッション履歴を取得"""
    supabase = get_supabase_client()
    result = supabase.table('chat_sessions')\
        .select('*')\
        .eq('student_id', student_id)\
        .order('started_at', desc=True)\
        .limit(limit)\
        .execute()
    return result.data


def get_course_chat_sessions(course_id: str, limit: int = 100) -> List[Dict]:
    """コースの全チャットセッションを取得（教員用）"""
    supabase = get_supabase_client()
    result = supabase.table('chat_sessions')\
        .select('*, users(name, email, student_id)')\
        .eq('course_id', course_id)\
        .order('started_at', desc=True)\
        .limit(limit)\
        .execute()
    return result.data


# ============================================================
# Vocabulary Operations
# ============================================================

def add_vocabulary(student_id: str, word: str, meaning: str = None, 
                   source_type: str = 'manual', **kwargs) -> Dict:
    """語彙を追加（重複時は更新）"""
    supabase = get_supabase_client()
    vocab_data = {
        'student_id': student_id,
        'word': word.lower().strip(),
        'meaning': meaning,
        'source_type': source_type,
        **kwargs
    }
    result = supabase.table('vocabulary').upsert(
        vocab_data, 
        on_conflict='student_id,word'
    ).execute()
    return result.data[0] if result.data else None


def get_vocabulary_for_review(student_id: str, limit: int = 20) -> List[Dict]:
    """復習が必要な語彙を取得"""
    supabase = get_supabase_client()
    now = datetime.utcnow().isoformat()
    result = supabase.table('vocabulary')\
        .select('*')\
        .eq('student_id', student_id)\
        .lte('next_review', now)\
        .order('next_review')\
        .limit(limit)\
        .execute()
    return result.data


def update_vocabulary_after_review(vocab_id: str, quality: int) -> Dict:
    """復習後に語彙を更新（SM-2アルゴリズム）"""
    supabase = get_supabase_client()
    
    # 現在の値を取得
    vocab = supabase.table('vocabulary').select('*').eq('id', vocab_id).execute()
    if not vocab.data:
        return None
    
    v = vocab.data[0]
    ease_factor = v['ease_factor']
    interval = v['interval_days']
    repetitions = v['repetitions']
    
    # SM-2アルゴリズム
    if quality >= 3:  # 正解
        if repetitions == 0:
            interval = 1
        elif repetitions == 1:
            interval = 6
        else:
            interval = int(interval * ease_factor)
        repetitions += 1
    else:  # 不正解
        repetitions = 0
        interval = 1
    
    # Ease Factor 更新
    ease_factor = ease_factor + (0.1 - (5 - quality) * (0.08 + (5 - quality) * 0.02))
    ease_factor = max(1.3, ease_factor)
    
    # 次回復習日を計算
    from datetime import timedelta
    next_review = datetime.utcnow() + timedelta(days=interval)
    
    updates = {
        'ease_factor': ease_factor,
        'interval_days': interval,
        'repetitions': repetitions,
        'next_review': next_review.isoformat(),
        'last_reviewed': datetime.utcnow().isoformat(),
        'mastery_level': min(5, repetitions)
    }
    
    result = supabase.table('vocabulary').update(updates).eq('id', vocab_id).execute()
    return result.data[0] if result.data else None


# ============================================================
# Practice Log Operations
# ============================================================

def log_practice(student_id: str, module_type: str, 
                 course_id: str = None, **kwargs) -> Dict:
    """練習ログを記録"""
    supabase = get_supabase_client()
    log_data = {
        'student_id': student_id,
        'course_id': course_id,
        'module_type': module_type,
        'practiced_at': datetime.utcnow().isoformat(),  # 明示的にタイムスタンプを設定
        **kwargs
    }
    result = supabase.table('practice_logs').insert(log_data).execute()
    return result.data[0] if result.data else None


def get_student_practice_stats(student_id: str, days: int = 30) -> Dict:
    """学生の練習統計を取得（キャッシュ付き）"""
    return _get_student_practice_stats_cached(student_id, days)

@st.cache_data(ttl=60)  # 1分キャッシュ（頻繁に更新される）
def _get_student_practice_stats_cached(student_id: str, days: int = 30) -> Dict:
    supabase = get_supabase_client()
    since = (datetime.utcnow() - timedelta(days=days)).isoformat()
    
    result = supabase.table('practice_logs')\
        .select('module_type, duration_seconds, score')\
        .eq('student_id', student_id)\
        .gte('practiced_at', since)\
        .execute()
    
    # 集計
    stats = {}
    for log in result.data:
        module = log['module_type']
        if module not in stats:
            stats[module] = {'count': 0, 'total_seconds': 0, 'scores': []}
        stats[module]['count'] += 1
        if log.get('duration_seconds'):
            stats[module]['total_seconds'] += log['duration_seconds']
        if log.get('score'):
            stats[module]['scores'].append(log['score'])
    
    return stats


# ============================================================
# API Usage Tracking
# ============================================================

def log_api_usage(api_name: str, cost_jpy: float, 
                  user_id: str = None, **kwargs) -> Dict:
    """API使用量を記録"""
    supabase = get_supabase_client()
    usage_data = {
        'api_name': api_name,
        'cost_jpy': cost_jpy,
        'user_id': user_id,
        **kwargs
    }
    result = supabase.table('api_usage').insert(usage_data).execute()
    return result.data[0] if result.data else None


# ============================================================
# Speaking Materials Operations (Phase B)
# ============================================================

def create_speaking_material(teacher_id: str, title: str, text: str,
                             level: str = 'B1', category: str = 'その他',
                             course_id: str = None, **kwargs) -> Dict:
    """Speaking教材を作成"""
    supabase = get_supabase_client()
    data = {
        'teacher_id': teacher_id,
        'title': title,
        'text': text,
        'level': level,
        'category': category,
        'course_id': course_id,
        **kwargs
    }
    result = supabase.table('speaking_materials').insert(data).execute()
    return result.data[0] if result.data else None


def get_speaking_materials(teacher_id: str = None, course_id: str = None,
                           active_only: bool = True) -> List[Dict]:
    """Speaking教材一覧を取得（キャッシュ付き）"""
    return _get_speaking_materials_cached(teacher_id, course_id, active_only)

@st.cache_data(ttl=300)
def _get_speaking_materials_cached(teacher_id: str = None, course_id: str = None,
                                    active_only: bool = True) -> List[Dict]:
    supabase = get_supabase_client()
    query = supabase.table('speaking_materials').select('*')
    if teacher_id:
        query = query.eq('teacher_id', teacher_id)
    if course_id:
        query = query.eq('course_id', course_id)
    if active_only:
        query = query.eq('is_active', True)
    result = query.order('created_at', desc=True).execute()
    return result.data


def update_speaking_material(material_id: str, updates: Dict) -> Dict:
    """Speaking教材を更新"""
    supabase = get_supabase_client()
    updates['updated_at'] = datetime.utcnow().isoformat()
    result = supabase.table('speaking_materials').update(updates).eq('id', material_id).execute()
    return result.data[0] if result.data else None


def delete_speaking_material(material_id: str) -> bool:
    """Speaking教材を論理削除"""
    supabase = get_supabase_client()
    result = supabase.table('speaking_materials').update(
        {'is_active': False, 'updated_at': datetime.utcnow().isoformat()}
    ).eq('id', material_id).execute()
    return len(result.data) > 0


# ============================================================
# AI Generated Texts Operations (Phase B)
# ============================================================

def save_ai_generated_text(student_id: str, title: str, text: str,
                           level: str = 'B1', course_id: str = None,
                           **kwargs) -> Dict:
    """AI生成テキストを保存"""
    supabase = get_supabase_client()
    data = {
        'student_id': student_id,
        'title': title,
        'text': text,
        'level': level,
        'course_id': course_id,
        'word_count': len(text.split()),
        **kwargs
    }
    result = supabase.table('ai_generated_texts').insert(data).execute()
    return result.data[0] if result.data else None


def get_ai_generated_texts(student_id: str, limit: int = 50) -> List[Dict]:
    """学生のAI生成テキスト一覧を取得"""
    supabase = get_supabase_client()
    result = supabase.table('ai_generated_texts')\
        .select('*')\
        .eq('student_id', student_id)\
        .order('created_at', desc=True)\
        .limit(limit)\
        .execute()
    return result.data


def delete_ai_generated_text(text_id: str) -> bool:
    """AI生成テキストを削除"""
    supabase = get_supabase_client()
    result = supabase.table('ai_generated_texts').delete().eq('id', text_id).execute()
    return len(result.data) > 0


# ============================================================
# Speaking Rubrics Operations (Phase B)
# ============================================================

def get_speaking_rubric(course_id: str) -> Optional[Dict]:
    """コースの評価基準を取得（キャッシュ付き）"""
    return _get_speaking_rubric_cached(course_id)

@st.cache_data(ttl=300)
def _get_speaking_rubric_cached(course_id: str) -> Optional[Dict]:
    supabase = get_supabase_client()
    result = supabase.table('speaking_rubrics').select('*').eq('course_id', course_id).execute()
    return result.data[0] if result.data else None


def upsert_speaking_rubric(course_id: str, criteria: Dict,
                           assignment_weight: int = 40,
                           practice_weight: int = 10) -> Dict:
    """評価基準を作成/更新"""
    supabase = get_supabase_client()
    data = {
        'course_id': course_id,
        'criteria': criteria,
        'assignment_weight': assignment_weight,
        'practice_weight': practice_weight,
        'updated_at': datetime.utcnow().isoformat()
    }
    result = supabase.table('speaking_rubrics').upsert(
        data, on_conflict='course_id'
    ).execute()
    _get_speaking_rubric_cached.clear()
    return result.data[0] if result.data else None


# ============================================================
# Course Settings Operations (course_settings 専用テーブル)
# ============================================================

def get_course_settings(course_id: str) -> Optional[Dict]:
    """コース設定を取得（キャッシュ付き）。なければNone"""
    return _get_course_settings_cached(course_id)

@st.cache_data(ttl=120)
def _get_course_settings_cached(course_id: str) -> Optional[Dict]:
    supabase = get_supabase_client()
    result = supabase.table('course_settings')\
        .select('*').eq('course_id', course_id).execute()
    return result.data[0] if result.data else None


def upsert_course_settings(course_id: str, updates: Dict) -> Dict:
    """コース設定を作成/更新（部分更新対応）
    
    updates に含まれるキーだけを更新する。
    例: upsert_course_settings(cid, {"purpose": "...", "modules": {...}})
    """
    supabase = get_supabase_client()
    data = {
        'course_id': course_id,
        **updates,
        'updated_at': datetime.utcnow().isoformat()
    }
    result = supabase.table('course_settings').upsert(
        data, on_conflict='course_id'
    ).execute()
    _get_course_settings_cached.clear()
    return result.data[0] if result.data else None


def update_course_settings_field(course_id: str, field: str, value: Any) -> Dict:
    """コース設定の特定フィールドだけを更新するヘルパー
    
    例: update_course_settings_field(cid, "purpose", "4技能バランス型")
    例: update_course_settings_field(cid, "speaking_rubrics", {...})
    """
    return upsert_course_settings(course_id, {field: value})


# ============================================================
# Extended Practice Log Operations (Phase B)
# ============================================================

def log_speaking_practice(student_id: str, material_title: str,
                          score: int, pronunciation: int, fluency: int,
                          word_count: int = 0, material_level: str = '',
                          course_id: str = None, **kwargs) -> Dict:
    """Speaking練習ログを記録（詳細データ付き）"""
    activity_details = {
        'pronunciation': pronunciation,
        'fluency': fluency,
        'word_count': word_count,
        'material_level': material_level,
        **kwargs
    }
    return log_practice(
        student_id=student_id,
        module_type='speaking',
        course_id=course_id,
        score=score,
        material_title=material_title,
        activity_details=activity_details
    )


def get_speaking_practice_history(student_id: str, limit: int = 50) -> List[Dict]:
    """Speaking練習履歴を取得"""
    supabase = get_supabase_client()
    result = supabase.table('practice_logs')\
        .select('*')\
        .eq('student_id', student_id)\
        .eq('module_type', 'speaking')\
        .order('practiced_at', desc=True)\
        .limit(limit)\
        .execute()
    return result.data


# ============================================================
# Extended Chat Session Operations (Phase B)
# ============================================================

def save_chat_session_full(student_id: str, messages: List[Dict],
                           situation_key: str = None, level: str = None,
                           feedback: Dict = None, used_voice_input: bool = False,
                           course_id: str = None, topic: str = None) -> Dict:
    """チャットセッションを一括保存（終了時）"""
    supabase = get_supabase_client()
    session_data = {
        'student_id': student_id,
        'course_id': course_id,
        'topic': topic or situation_key,
        'messages': messages,
        'situation_key': situation_key,
        'level': level,
        'feedback': feedback,
        'used_voice_input': used_voice_input,
        'ended_at': datetime.utcnow().isoformat()
    }
    result = supabase.table('chat_sessions').insert(session_data).execute()
    return result.data[0] if result.data else None


def get_student_chat_history(student_id: str, limit: int = 20) -> List[Dict]:
    """学生のチャット履歴を取得（フィードバック付き）"""
    supabase = get_supabase_client()
    result = supabase.table('chat_sessions')\
        .select('id, topic, situation_key, level, feedback, used_voice_input, started_at, ended_at')\
        .eq('student_id', student_id)\
        .order('started_at', desc=True)\
        .limit(limit)\
        .execute()
    return result.data


# ============================================================
# Extended Submission Operations (Phase B)
# ============================================================

def create_speaking_submission(student_id: str, assignment_id: str,
                               score: int = None, pronunciation: int = None,
                               fluency: int = None, student_text: str = None,
                               recognized_text: str = None,
                               audio_url: str = None, **kwargs) -> Dict:
    """Speaking課題提出を作成"""
    scores_json = {}
    if pronunciation is not None:
        scores_json['pronunciation'] = pronunciation
    if fluency is not None:
        scores_json['fluency'] = fluency
    scores_json.update(kwargs.get('extra_scores', {}))

    return create_submission(
        student_id=student_id,
        assignment_id=assignment_id,
        content_type='speaking',
        total_score=score,
        scores=scores_json,
        student_text=student_text,
        recognized_text=recognized_text,
        audio_url=audio_url
    )


def update_submission_feedback(submission_id: str, feedback: str = None,
                                teacher_comment: str = None,
                                teacher_score: float = None) -> Dict:
    """提出にフィードバックを追加（教員用）"""
    updates = {}
    if feedback is not None:
        updates['feedback'] = feedback
    if teacher_comment is not None:
        updates['teacher_comment'] = teacher_comment
    if teacher_score is not None:
        updates['teacher_score'] = teacher_score
    return update_submission(submission_id, updates)


def get_speaking_submissions_for_assignment(assignment_id: str) -> List[Dict]:
    """課題のSpeaking提出を取得（教員用・ユーザー情報付き）"""
    return get_assignment_submissions(assignment_id)


# ============================================================
# Teacher Dashboard: Course Progress (Phase B-2)
# ============================================================

def get_course_speaking_progress(course_id: str) -> List[Dict]:
    """コースのSpeaking進捗を学生ごとに集計（教員用）"""
    supabase = get_supabase_client()

    # 受講学生一覧
    enrollments = supabase.table('enrollments')\
        .select('student_id, users(name, email, student_id)')\
        .eq('course_id', course_id)\
        .execute()

    students = []
    for e in enrollments.data:
        sid = e['student_id']
        u = e.get('users') or {}

        # 練習ログ集計
        logs = supabase.table('practice_logs')\
            .select('score, duration_seconds')\
            .eq('student_id', sid)\
            .eq('course_id', course_id)\
            .eq('module_type', 'speaking')\
            .execute()

        scores = [l['score'] for l in logs.data if l.get('score') is not None]
        practice_count = len(logs.data)

        # 課題提出数
        subs = supabase.table('submissions')\
            .select('id')\
            .eq('student_id', sid)\
            .execute()

        # コースの課題数
        assigns = supabase.table('assignments')\
            .select('id')\
            .eq('course_id', course_id)\
            .execute()

        students.append({
            'name': u.get('name', '不明'),
            'student_id_display': u.get('student_id', ''),
            'practice_count': practice_count,
            'avg_score': round(sum(scores) / len(scores), 1) if scores else 0,
            'max_score': max(scores) if scores else 0,
            'submission_count': len(subs.data),
            'assignment_count': len(assigns.data),
        })

    return students


def get_all_course_submissions(course_id: str) -> List[Dict]:
    """コースの全課題・全提出を取得（成績一覧用）"""
    supabase = get_supabase_client()

    assignments = supabase.table('assignments')\
        .select('id, title')\
        .eq('course_id', course_id)\
        .order('due_date')\
        .execute()

    all_subs = []
    for a in assignments.data:
        subs = supabase.table('submissions')\
            .select('*, users(name, email, student_id)')\
            .eq('assignment_id', a['id'])\
            .order('submitted_at', desc=True)\
            .execute()
        for s in subs.data:
            u = s.get('users') or {}
            all_subs.append({
                'assignment_title': a['title'],
                'student_name': u.get('name', '不明'),
                'student_id_display': u.get('student_id', ''),
                'score': s.get('total_score') or s.get('score') or 0,
                'pronunciation': (s.get('scores') or {}).get('pronunciation', 0),
                'fluency': (s.get('scores') or {}).get('fluency', 0),
                'submitted_at': (s.get('submitted_at') or '')[:16].replace('T', ' '),
                'has_feedback': bool(s.get('feedback') or s.get('teacher_comment')),
            })

    return all_subs


def update_assignment(assignment_id: str, updates: Dict) -> Dict:
    """課題を更新"""
    supabase = get_supabase_client()
    result = supabase.table('assignments').update(updates).eq('id', assignment_id).execute()
    return result.data[0] if result.data else None


# ============================================================
# Writing Operations (Phase B-2)
# ============================================================

def save_writing_submission(student_id: str, assignment_id: str = None,
                            text: str = '', task_type: str = '',
                            word_count: int = 0, scores: Dict = None,
                            feedback: str = '', cefr_level: str = '',
                            is_practice: bool = False,
                            course_id: str = None, **kwargs) -> Dict:
    """ライティング提出を保存"""
    supabase = get_supabase_client()
    data = {
        'student_id': student_id,
        'content_type': 'writing',
        'student_text': text,
        'total_score': scores.get('overall', 0) if scores else 0,
        'scores': scores or {},
        'feedback': feedback,
        'feedback_detailed': {
            'task_type': task_type,
            'word_count': word_count,
            'cefr_level': cefr_level,
            'is_practice': is_practice,
            **kwargs
        },
        'cefr_level': cefr_level,
        'is_practice': is_practice,
    }
    if assignment_id:
        data['assignment_id'] = assignment_id
    if course_id:
        data['course_id'] = course_id
    
    result = supabase.table('submissions').insert(data).execute()
    return result.data[0] if result.data else None


def save_translation_check(student_id: str, japanese_text: str,
                           english_text: str, scores: Dict = None,
                           feedback: str = '',
                           course_id: str = None) -> Dict:
    """翻訳チェック結果を保存"""
    supabase = get_supabase_client()
    data = {
        'student_id': student_id,
        'content_type': 'translation',
        'student_text': english_text,
        'total_score': scores.get('overall', 0) if scores else 0,
        'scores': scores or {},
        'feedback': feedback,
        'feedback_detailed': {
            'japanese_text': japanese_text,
        },
        'is_practice': True,
    }
    if course_id:
        data['course_id'] = course_id
    
    result = supabase.table('submissions').insert(data).execute()
    return result.data[0] if result.data else None


def get_writing_history(student_id: str, limit: int = 30) -> List[Dict]:
    """ライティング履歴を取得"""
    supabase = get_supabase_client()
    result = supabase.table('submissions')\
        .select('*')\
        .eq('student_id', student_id)\
        .in_('content_type', ['writing', 'translation'])\
        .order('submitted_at', desc=True)\
        .limit(limit)\
        .execute()
    return result.data


def get_writing_assignments(course_id: str) -> List[Dict]:
    """ライティング課題一覧を取得（キャッシュ付き）"""
    return _get_writing_assignments_cached(course_id)

@st.cache_data(ttl=120)
def _get_writing_assignments_cached(course_id: str) -> List[Dict]:
    supabase = get_supabase_client()
    result = supabase.table('assignments')\
        .select('*')\
        .eq('course_id', course_id)\
        .eq('assignment_type', 'writing')\
        .order('due_date')\
        .execute()
    return result.data


def create_writing_assignment(course_id: str, title: str, task_type: str,
                              instructions: str = '', min_words: int = 0,
                              max_words: int = 0, is_required: bool = True,
                              due_date: str = None) -> Dict:
    """ライティング課題を作成"""
    return create_assignment(
        course_id=course_id,
        title=title,
        assignment_type='writing',
        instructions=instructions,
        is_published=True,
        due_date=due_date,
        config={
            'task_type': task_type,
            'min_words': min_words,
            'max_words': max_words,
            'is_required': is_required,
        }
    )


# ============================================================
# Vocabulary Operations Extended (Phase B-2)
# ============================================================

def get_student_vocabulary(student_id: str, limit: int = 200) -> List[Dict]:
    """学生の全語彙を取得"""
    supabase = get_supabase_client()
    result = supabase.table('vocabulary')\
        .select('*')\
        .eq('student_id', student_id)\
        .order('created_at', desc=True)\
        .limit(limit)\
        .execute()
    return result.data


def get_vocabulary_stats(student_id: str) -> Dict:
    """語彙学習統計を取得（キャッシュ付き）"""
    return _get_vocabulary_stats_cached(student_id)

@st.cache_data(ttl=60)
def _get_vocabulary_stats_cached(student_id: str) -> Dict:
    supabase = get_supabase_client()
    all_vocab = supabase.table('vocabulary')\
        .select('mastery_level, repetitions, last_reviewed')\
        .eq('student_id', student_id)\
        .execute()
    
    data = all_vocab.data or []
    total = len(data)
    mastered = len([v for v in data if v.get('mastery_level', 0) >= 4])
    reviewed_today = 0
    today = datetime.utcnow().strftime('%Y-%m-%d')
    for v in data:
        lr = v.get('last_reviewed', '') or ''
        if lr.startswith(today):
            reviewed_today += 1
    
    return {
        'total': total,
        'mastered': mastered,
        'in_progress': total - mastered,
        'reviewed_today': reviewed_today,
    }


def save_quiz_result(student_id: str, list_name: str, quiz_type: str,
                     score: int, total: int,
                     course_id: str = None) -> Dict:
    """クイズ結果を保存"""
    return log_practice(
        student_id=student_id,
        module_type='vocabulary_quiz',
        course_id=course_id,
        score=score,
        activity_details={
            'list_name': list_name,
            'quiz_type': quiz_type,
            'total_questions': total,
            'percentage': round(score / total * 100) if total > 0 else 0,
        }
    )


def save_word_list(student_id: str = None, teacher_id: str = None,
                   list_name: str = '', words: List[Dict] = None,
                   description: str = '', level: str = 'B1',
                   course_id: str = None, is_ai_generated: bool = False) -> Dict:
    """単語リストを保存（教員 or 学生が生成したリスト）"""
    supabase = get_supabase_client()
    data = {
        'title': list_name,
        'text': description,
        'level': level,
        'category': 'ai_generated' if is_ai_generated else 'custom',
        'details': {
            'words': words or [],
            'word_count': len(words) if words else 0,
            'is_ai_generated': is_ai_generated,
        },
    }
    if teacher_id:
        data['teacher_id'] = teacher_id
    if student_id:
        data['student_id'] = student_id
    if course_id:
        data['course_id'] = course_id
    
    # speaking_materialsテーブルを流用（汎用教材テーブルとして）
    # 将来的には word_lists テーブルに分離可能
    result = supabase.table('ai_generated_texts').insert(data).execute()
    return result.data[0] if result.data else None


# ============================================================
# Learning Resources Operations (プロンプト集・教材コンテンツ管理)
# ============================================================

def get_learning_resources(course_id: str = None, resource_type: str = None,
                           category: str = None, active_only: bool = True) -> List[Dict]:
    """学習リソース一覧を取得"""
    return _get_learning_resources_cached(course_id, resource_type, category, active_only)

@st.cache_data(ttl=120)
def _get_learning_resources_cached(course_id: str = None, resource_type: str = None,
                                    category: str = None, active_only: bool = True) -> List[Dict]:
    supabase = get_supabase_client()
    query = supabase.table('learning_resources').select('*')
    if course_id:
        query = query.eq('course_id', course_id)
    if resource_type:
        query = query.eq('resource_type', resource_type)
    if category:
        query = query.eq('category', category)
    if active_only:
        query = query.eq('is_active', True)
    result = query.order('sort_order').order('created_at', desc=True).execute()
    return result.data


def create_learning_resource(teacher_id: str, course_id: str = None,
                             resource_type: str = 'prompt', category: str = 'general',
                             title: str = '', description: str = '',
                             content: str = '', tip: str = '',
                             sort_order: int = 0, metadata: Dict = None) -> Dict:
    """学習リソースを作成"""
    supabase = get_supabase_client()
    data = {
        'teacher_id': teacher_id,
        'course_id': course_id,
        'resource_type': resource_type,
        'category': category,
        'title': title,
        'description': description,
        'content': content,
        'tip': tip,
        'sort_order': sort_order,
        'metadata': metadata or {},
    }
    result = supabase.table('learning_resources').insert(data).execute()
    _get_learning_resources_cached.clear()
    return result.data[0] if result.data else None


def update_learning_resource(resource_id: str, updates: Dict) -> Dict:
    """学習リソースを更新"""
    supabase = get_supabase_client()
    updates['updated_at'] = datetime.utcnow().isoformat()
    result = supabase.table('learning_resources').update(updates).eq('id', resource_id).execute()
    _get_learning_resources_cached.clear()
    return result.data[0] if result.data else None


def delete_learning_resource(resource_id: str, soft: bool = True) -> bool:
    """学習リソースを削除（デフォルトは論理削除）"""
    supabase = get_supabase_client()
    if soft:
        result = supabase.table('learning_resources').update(
            {'is_active': False, 'updated_at': datetime.utcnow().isoformat()}
        ).eq('id', resource_id).execute()
    else:
        result = supabase.table('learning_resources').delete().eq('id', resource_id).execute()
    _get_learning_resources_cached.clear()
    return len(result.data) > 0


def bulk_import_learning_resources(teacher_id: str, course_id: str,
                                    resources: List[Dict]) -> int:
    """プロンプト集をハードコードから一括インポート"""
    supabase = get_supabase_client()
    rows = []
    for r in resources:
        rows.append({
            'teacher_id': teacher_id,
            'course_id': course_id,
            'resource_type': r.get('resource_type', 'prompt'),
            'category': r.get('category', 'general'),
            'title': r.get('title', ''),
            'description': r.get('description', ''),
            'content': r.get('content', ''),
            'tip': r.get('tip', ''),
            'sort_order': r.get('sort_order', 0),
            'metadata': r.get('metadata', {}),
        })
    result = supabase.table('learning_resources').insert(rows).execute()
    _get_learning_resources_cached.clear()
    return len(result.data)


# ============================================================
# Student Profile Operations (学生プロフィール)
# ============================================================

def get_student_profile(user_id: str) -> Optional[Dict]:
    """学生プロフィールを取得"""
    supabase = get_supabase_client()
    result = supabase.table('student_profiles')\
        .select('*').eq('user_id', user_id).execute()
    return result.data[0] if result.data else None


def upsert_student_profile(user_id: str, profile_data: Dict) -> Dict:
    """学生プロフィールを作成/更新"""
    supabase = get_supabase_client()
    data = {
        'user_id': user_id,
        **profile_data,
        'updated_at': datetime.utcnow().isoformat(),
    }
    result = supabase.table('student_profiles').upsert(
        data, on_conflict='user_id'
    ).execute()
    return result.data[0] if result.data else None


def get_course_student_profiles(course_id: str) -> List[Dict]:
    """コースの全学生プロフィールを取得（教員用）"""
    supabase = get_supabase_client()
    # enrollmentsを経由して取得
    result = supabase.table('enrollments')\
        .select('student_id, users(id, name, email, student_id)')\
        .eq('course_id', course_id)\
        .execute()

    user_ids = []
    user_map = {}
    for e in result.data:
        u = e.get('users')
        if u:
            user_ids.append(u['id'])
            user_map[u['id']] = u

    if not user_ids:
        return []

    # student_profilesから一括取得
    profiles_result = supabase.table('student_profiles')\
        .select('*')\
        .in_('user_id', user_ids)\
        .execute()

    profile_map = {p['user_id']: p for p in profiles_result.data}

    # user情報とprofileをマージ
    merged = []
    for uid in user_ids:
        u = user_map.get(uid, {})
        p = profile_map.get(uid, {})
        merged.append({**u, 'profile': p})

    return merged


# ============================================================
# Course Submissions (教員用: コースの提出物一覧)
# ============================================================

def get_course_submissions(course_id: str, limit: int = 20) -> List[Dict]:
    """コースの最近の提出物を取得"""
    supabase = get_supabase_client()
    result = supabase.table('submissions')\
        .select('*, users(name, email, student_id)')\
        .eq('course_id', course_id)\
        .order('created_at', desc=True)\
        .limit(limit)\
        .execute()
    return result.data


# ============================================================
# Dashboard / Alert Aggregate Functions (Phase 1追加)
# ============================================================

def get_students_with_activity_summary(course_id: str) -> List[Dict]:
    """コース学生の活動サマリーを取得（教員アラート・ダッシュボード用）
    
    enrollments + users + practice_logs + submissions をJOINし、
    各学生の最終ログイン、提出率、平均スコア、最近の学習時間を計算する。
    """
    supabase = get_supabase_client()
    
    # 1. コースの学生一覧を取得
    enrollments = supabase.table('enrollments')\
        .select('student_id, users(id, name, email, student_id, last_login)')\
        .eq('course_id', course_id)\
        .execute()
    
    if not enrollments.data:
        return []
    
    # 2. コースの課題数を取得
    assignments = supabase.table('assignments')\
        .select('id')\
        .eq('course_id', course_id)\
        .execute()
    total_assignments = len(assignments.data) if assignments.data else 0
    
    # 3. 各学生の情報を集計
    students_summary = []
    now = datetime.utcnow()
    week_ago = (now - timedelta(days=7)).isoformat()
    assignment_ids = [a["id"] for a in (assignments.data or [])]
    
    for enrollment in enrollments.data:
        user = enrollment.get('users')
        if not user:
            continue
        
        student_id = user['id']
        
        # 提出数を取得（assignmentsのIDリスト経由）
        subs_data = []
        for aid in assignment_ids:
            s = supabase.table('submissions')\
                .select('id, total_score')\
                .eq('student_id', student_id)\
                .eq('assignment_id', aid)\
                .execute()
            subs_data.extend(s.data or [])
        submission_count = len(subs_data)
        
        # 平均スコア
        scores = []
        for s in (subs_data or []):
            sc = s.get('total_score')
            if sc and sc > 0:
                scores.append(sc)
        avg_score = sum(scores) / len(scores) if scores else 0
        
        # 最近の練習ログ
        logs = supabase.table('practice_logs')\
            .select('practiced_at, duration_seconds, score')\
            .eq('student_id', student_id)\
            .gte('practiced_at', week_ago)\
            .execute()
        
        practice_count = len(logs.data) if logs.data else 0
        weekly_seconds = sum(
            (l.get('duration_seconds') or 0) for l in (logs.data or [])
        )
        
        # スコアトレンド（直近と過去を比較 — 簡易版）
        recent_scores = [l.get('score') for l in (logs.data or []) if l.get('score')]
        score_trend = 0  # TODO: 過去月と比較して算出
        
        # 最終ログイン日
        last_login_str = user.get('last_login')
        if last_login_str:
            try:
                last_login = datetime.fromisoformat(last_login_str.replace('Z', '+00:00'))
                days_inactive = (now - last_login.replace(tzinfo=None)).days
            except (ValueError, TypeError):
                days_inactive = 99
        else:
            days_inactive = 99
        
        students_summary.append({
            'name': user.get('name', '名前未設定'),
            'student_id': user.get('student_id', ''),
            'user_id': student_id,
            'email': user.get('email', ''),
            'last_login': last_login_str or '',
            'days_since_active': days_inactive,
            'submissions': submission_count,
            'total_assignments': total_assignments,
            'avg_score': round(avg_score, 1),
            'score_trend': score_trend,
            'practice_count': practice_count,
            'weekly_study_minutes': round(weekly_seconds / 60),
            'streak': 0,  # TODO: 連続学習日数の算出
        })
    
    return students_summary


def get_student_assignment_status(student_id: str, course_id: str) -> List[Dict]:
    """学生の課題+提出状況を取得（学生ホーム用）
    
    assignments LEFT JOIN submissions で未提出/提出済/採点済を判定
    """
    supabase = get_supabase_client()
    
    # コースの課題一覧
    assignments = supabase.table('assignments')\
        .select('*')\
        .eq('course_id', course_id)\
        .order('due_date')\
        .execute()
    
    if not assignments.data:
        return []
    
    # 学生の提出物（assignment_id経由でフィルタ）
    assignment_ids = [a['id'] for a in assignments.data]
    all_subs = []
    for aid in assignment_ids:
        s = supabase.table('submissions')\
            .select('*')\
            .eq('student_id', student_id)\
            .eq('assignment_id', aid)\
            .execute()
        all_subs.extend(s.data or [])
    
    submissions_data = all_subs
    
    sub_map = {}
    for s in submissions_data:
        aid = s.get('assignment_id')
        if aid:
            sub_map[aid] = s
    
    result = []
    for a in assignments.data:
        sub = sub_map.get(a['id'])
        if sub:
            score = sub.get('total_score') or sub.get('score') or 0
            has_feedback = bool(sub.get('feedback') or sub.get('teacher_comment'))
            status = '採点済' if has_feedback else '提出済'
        else:
            score = 0
            status = '未提出'
        
        result.append({
            'assignment_id': a['id'],
            'title': a.get('title', ''),
            'type': a.get('assignment_type', ''),
            'due_date': a.get('due_date', ''),
            'status': status,
            'score': score,
            'submission': sub,
        })
    
    return result


def get_student_recent_activity(student_id: str, limit: int = 10) -> List[Dict]:
    """学生の最近の学習アクティビティを取得（学生ホーム用）
    
    practice_logs + submissions から最新のものを取得
    """
    supabase = get_supabase_client()
    
    # 練習ログ
    logs = supabase.table('practice_logs')\
        .select('*')\
        .eq('student_id', student_id)\
        .order('practiced_at', desc=True)\
        .limit(limit)\
        .execute()
    
    # 提出物
    subs = supabase.table('submissions')\
        .select('*, assignments(title)')\
        .eq('student_id', student_id)\
        .order('submitted_at', desc=True)\
        .limit(limit)\
        .execute()
    
    activities = []
    
    for log in (logs.data or []):
        activities.append({
            'type': 'practice',
            'module': log.get('module_type', ''),
            'score': log.get('score'),
            'duration_seconds': log.get('duration_seconds'),
            'timestamp': log.get('practiced_at', ''),
            'description': f"{log.get('module_type', '')} 練習",
        })
    
    for sub in (subs.data or []):
        assignment = sub.get('assignments') or {}
        activities.append({
            'type': 'submission',
            'module': sub.get('content_type', ''),
            'score': sub.get('total_score') or sub.get('score'),
            'timestamp': sub.get('submitted_at', ''),
            'description': f"{assignment.get('title', '課題')} 提出",
        })
    
    # タイムスタンプでソート
    activities.sort(key=lambda x: x.get('timestamp', ''), reverse=True)
    
    return activities[:limit]


def get_course_chat_session_summary(course_id: str) -> Dict:
    """コースのAI対話セッションのサマリー統計を取得（教員チャットログ用）"""
    supabase = get_supabase_client()
    
    sessions = supabase.table('chat_sessions')\
        .select('*, users(id, name, email, student_id)')\
        .eq('course_id', course_id)\
        .order('started_at', desc=True)\
        .execute()
    
    if not sessions.data:
        return {
            'total_sessions': 0,
            'active_students': 0,
            'avg_score': 0,
            'students': [],
        }
    
    # 学生ごとに集計
    student_map = {}
    total_scores = []
    
    for s in sessions.data:
        user = s.get('users') or {}
        uid = user.get('id', '')
        
        if uid not in student_map:
            student_map[uid] = {
                'name': user.get('name', '不明'),
                'student_id_display': user.get('student_id', ''),
                'user_id': uid,
                'sessions': [],
                'scores': [],
            }
        
        student_map[uid]['sessions'].append(s)
        score = s.get('score') or s.get('total_score')
        if score:
            student_map[uid]['scores'].append(score)
            total_scores.append(score)
    
    # 学生サマリーを構築
    student_summaries = []
    for uid, data in student_map.items():
        avg = sum(data['scores']) / len(data['scores']) if data['scores'] else 0
        
        # 最終セッション
        last_session = data['sessions'][0] if data['sessions'] else {}
        last_active = last_session.get('started_at', '')
        
        # トレンド（簡易: 直近5回の平均 vs 全体平均）
        recent = data['scores'][:5]
        recent_avg = sum(recent) / len(recent) if recent else 0
        trend = '↑' if recent_avg > avg + 2 else ('↓' if recent_avg < avg - 2 else '→')
        
        student_summaries.append({
            'name': data['name'],
            'id': data['student_id_display'],
            'user_id': uid,
            'sessions': len(data['sessions']),
            'avg_score': round(avg, 1),
            'last_active': last_active,
            'trend': trend,
            'recent_sessions': data['sessions'][:5],
        })
    
    # セッション数でソート
    student_summaries.sort(key=lambda x: x['sessions'], reverse=True)
    
    return {
        'total_sessions': len(sessions.data),
        'active_students': len(student_map),
        'avg_score': round(sum(total_scores) / len(total_scores), 1) if total_scores else 0,
        'students': student_summaries,
    }


# ============================================================
# Reading Logs (リーディング学習記録)
# ============================================================

def log_reading(student_id: str, course_id: str = None, **kwargs) -> Dict:
    """リーディング学習をreading_logsに記録
    
    kwargs:
        source_title, source_url, word_count, estimated_level,
        activity_type ('assigned'|'extensive'|'intensive'),
        quiz_results (list of dicts), quiz_score (float),
        time_spent_seconds, personal_notes, rating
    """
    supabase = get_supabase_client()
    log_data = {
        'student_id': student_id,
        'course_id': course_id,
        **kwargs
    }
    result = supabase.table('reading_logs').insert(log_data).execute()
    return result.data[0] if result.data else None


def get_student_reading_logs(student_id: str, days: int = 30, 
                              course_id: str = None) -> List[Dict]:
    """学生のリーディング履歴を取得"""
    supabase = get_supabase_client()
    since = (datetime.utcnow() - timedelta(days=days)).isoformat()
    
    query = supabase.table('reading_logs')\
        .select('*')\
        .eq('student_id', student_id)\
        .gte('completed_at', since)\
        .order('completed_at', desc=True)
    
    if course_id:
        query = query.eq('course_id', course_id)
    
    result = query.execute()
    return result.data if result.data else []


# ============================================================
# Listening Logs (リスニング学習記録)
# ============================================================

def log_listening(student_id: str, course_id: str = None, **kwargs) -> Dict:
    """リスニング学習をlistening_logsに記録

    kwargs:
        video_url, video_title, video_duration_seconds, estimated_level,
        activity_type ('assigned'|'extensive'|'practice'),
        pre_listening (dict), while_listening (dict), post_listening (dict),
        quiz_results (list of dicts), quiz_score (float),
        time_spent_seconds, api_cost
    """
    supabase = get_supabase_client()
    log_data = {
        'student_id': student_id,
        'course_id': course_id,
        **kwargs
    }
    result = supabase.table('listening_logs').insert(log_data).execute()
    return result.data[0] if result.data else None


def get_student_listening_logs(student_id: str, days: int = 30,
                                course_id: str = None) -> List[Dict]:
    """学生のリスニング履歴を取得"""
    supabase = get_supabase_client()
    since = (datetime.utcnow() - timedelta(days=days)).isoformat()
    
    query = supabase.table('listening_logs')\
        .select('*')\
        .eq('student_id', student_id)\
        .gte('completed_at', since)\
        .order('completed_at', desc=True)
    
    if course_id:
        query = query.eq('course_id', course_id)
    
    result = query.execute()
    return result.data if result.data else []


def get_listening_stats_for_course(course_id: str) -> List[Dict]:
    """コース内の学生リスニング統計を取得（教員用）"""
    supabase = get_supabase_client()
    try:
        result = supabase.table('listening_logs')\
            .select('student_id, quiz_score, time_spent_seconds, activity_type, completed_at')\
            .eq('course_id', course_id)\
            .order('completed_at', desc=True)\
            .execute()
        return result.data if result.data else []
    except Exception:
        return []


# ============================================================
# Learning Logs (授業外学習ログ)
# ============================================================

def save_learning_log(student_id: str, log_data: dict) -> Dict:
    """授業外学習ログをDBに保存"""
    supabase = get_supabase_client()
    data = {
        'student_id': student_id,
        'log_date': log_data.get('date'),
        'category': log_data.get('category'),
        'language': log_data.get('language', 'english'),
        'title': log_data.get('title'),
        'description': log_data.get('description'),
        'duration_minutes': log_data.get('duration_minutes', 0),
        'points': log_data.get('points', 0),
        'evidence_url': log_data.get('evidence_url'),
        'evidence_file_name': log_data.get('evidence_file'),
        'status': log_data.get('status', 'pending'),
    }
    result = supabase.table('learning_logs').insert(data).execute()
    return result.data[0] if result.data else None


def get_student_learning_logs(student_id: str, limit: int = 100) -> List[Dict]:
    """学生の授業外学習ログを取得"""
    supabase = get_supabase_client()
    result = supabase.table('learning_logs')\
        .select('*')\
        .eq('student_id', student_id)\
        .order('log_date', desc=True)\
        .limit(limit)\
        .execute()
    return result.data if result.data else []


def update_learning_log(log_id: str, updates: dict) -> Dict:
    """授業外学習ログを更新"""
    supabase = get_supabase_client()
    result = supabase.table('learning_logs')\
        .update(updates)\
        .eq('id', log_id)\
        .execute()
    return result.data[0] if result.data else None


def delete_learning_log(log_id: str) -> bool:
    """授業外学習ログを削除"""
    supabase = get_supabase_client()
    try:
        supabase.table('learning_logs')\
            .delete()\
            .eq('id', log_id)\
            .execute()
        return True
    except Exception:
        return False


def get_learning_logs_for_course(course_id: str) -> List[Dict]:
    """コース内の学生の授業外学習ログを取得（教員用）"""
    supabase = get_supabase_client()
    try:
        # enrollmentsから学生ID一覧を取得してフィルタ
        enrollments = supabase.table('enrollments')\
            .select('student_id')\
            .eq('course_id', course_id)\
            .execute()
        if not enrollments.data:
            return []
        student_ids = [e['student_id'] for e in enrollments.data]
        result = supabase.table('learning_logs')\
            .select('*, users(name, email)')\
            .in_('student_id', student_ids)\
            .order('log_date', desc=True)\
            .limit(200)\
            .execute()
        return result.data if result.data else []
    except Exception:
        return []


# ============================================================
# Practice Logs Detail (練習ログ詳細取得)
# ============================================================

def get_student_practice_details(student_id: str, days: int = 30,
                                  module_type: str = None) -> List[Dict]:
    """学生の練習ログ詳細を取得（activity_details含む）"""
    supabase = get_supabase_client()
    since = (datetime.utcnow() - timedelta(days=days)).isoformat()
    
    query = supabase.table('practice_logs')\
        .select('*')\
        .eq('student_id', student_id)\
        .gte('practiced_at', since)\
        .order('practiced_at', desc=True)
    
    if module_type:
        query = query.eq('module_type', module_type)
    
    result = query.execute()
    return result.data if result.data else []


# ============================================================
# Grade Aggregation (成績集計 — grades.py用)
# ============================================================

def get_module_scores_for_course(course_id: str) -> List[Dict]:
    """コース全学生のモジュール別スコアを集計（成績計算用）
    
    Returns list of dicts per student:
    {
        user_id, name, student_id, email,
        speaking_avg, speaking_count,
        writing_avg, writing_count,
        vocabulary_avg, vocabulary_count,
        reading_avg, reading_count,
        listening_avg, listening_count,
        assignment_avg, assignment_count,
    }
    """
    supabase = get_supabase_client()

    # 受講学生一覧
    enrollments = supabase.table('enrollments')\
        .select('student_id, users(id, name, email, student_id)')\
        .eq('course_id', course_id)\
        .execute()

    if not enrollments.data:
        return []

    # module_type → カテゴリマッピング
    MODULE_CATEGORY = {
        'speaking': 'speaking',
        'speaking_chat': 'speaking',
        'speaking_pronunciation': 'speaking',
        'writing_practice': 'writing',
        'writing_submission': 'writing',
        'writing_translation': 'writing',
        'vocabulary_quiz': 'vocabulary',
        'vocabulary_flashcard': 'vocabulary',
        'reading_practice': 'reading',
        'listening_practice': 'listening',
    }

    results = []
    for e in enrollments.data:
        user = e.get('users') or {}
        sid = e['student_id']
        uid = user.get('id', sid)

        # practice_logs 全件取得（course_id絞り込み）
        logs_res = supabase.table('practice_logs')\
            .select('module_type, score')\
            .eq('student_id', uid)\
            .eq('course_id', course_id)\
            .execute()

        # カテゴリ別スコア集計
        cat_scores: dict = {
            'speaking': [], 'writing': [], 'vocabulary': [],
            'reading': [], 'listening': []
        }
        for log in (logs_res.data or []):
            cat = MODULE_CATEGORY.get(log.get('module_type', ''))
            sc = log.get('score')
            if cat and sc is not None:
                cat_scores[cat].append(float(sc))

        def avg(lst):
            return round(sum(lst) / len(lst), 1) if lst else None

        # 課題提出スコア（submissions）
        subs_res = supabase.table('submissions')\
            .select('total_score')\
            .eq('student_id', uid)\
            .eq('course_id', course_id)\
            .execute()
        sub_scores = [
            float(s['total_score']) for s in (subs_res.data or [])
            if s.get('total_score') is not None
        ]

        results.append({
            'user_id': uid,
            'name': user.get('name', '不明'),
            'student_id': user.get('student_id', ''),
            'email': user.get('email', ''),
            'speaking_avg': avg(cat_scores['speaking']),
            'speaking_count': len(cat_scores['speaking']),
            'writing_avg': avg(cat_scores['writing']),
            'writing_count': len(cat_scores['writing']),
            'vocabulary_avg': avg(cat_scores['vocabulary']),
            'vocabulary_count': len(cat_scores['vocabulary']),
            'reading_avg': avg(cat_scores['reading']),
            'reading_count': len(cat_scores['reading']),
            'listening_avg': avg(cat_scores['listening']),
            'listening_count': len(cat_scores['listening']),
            'assignment_avg': avg(sub_scores),
            'assignment_count': len(sub_scores),
        })

    return results


def get_grade_weights(course_id: str) -> Dict:
    """成績配分をcourse_settingsから取得（なければデフォルト値を返す）"""
    defaults = {
        'speaking': 20,
        'writing': 20,
        'vocabulary': 15,
        'reading': 15,
        'listening': 15,
        'assignment': 15,
        'attendance': 0,
    }
    try:
        settings = get_course_settings(course_id)
        if settings and settings.get('grade_weights'):
            saved = settings['grade_weights']
            # デフォルトに上書きマージ（新項目が増えても壊れない）
            return {**defaults, **saved}
    except Exception:
        pass
    return defaults


def save_grade_weights(course_id: str, weights: Dict) -> bool:
    """成績配分をcourse_settingsに保存"""
    try:
        upsert_course_settings(course_id, {'grade_weights': weights})
        return True
    except Exception:
        return False


# ============================================================
# Teacher Notes (教員メモ — 学生カルテ用)
# ============================================================

def get_teacher_note(teacher_id: str, student_id: str) -> Optional[Dict]:
    """教員が特定の学生に対して保存したメモ・目標を取得"""
    supabase = get_supabase_client()
    try:
        result = supabase.table('teacher_notes')\
            .select('*')\
            .eq('teacher_id', teacher_id)\
            .eq('student_id', student_id)\
            .execute()
        return result.data[0] if result.data else None
    except Exception:
        return None


def upsert_teacher_note(teacher_id: str, student_id: str,
                        memo: str = '', goal: str = '') -> Optional[Dict]:
    """教員メモを作成/更新"""
    supabase = get_supabase_client()
    data = {
        'teacher_id': teacher_id,
        'student_id': student_id,
        'memo': memo,
        'goal': goal,
        'updated_at': datetime.utcnow().isoformat(),
    }
    try:
        result = supabase.table('teacher_notes').upsert(
            data, on_conflict='teacher_id,student_id'
        ).execute()
        return result.data[0] if result.data else None
    except Exception:
        return None


# ============================================================
# Learning Materials (教材データベース)
# ============================================================

def get_learning_materials(module_type: str, course_id: str = None,
                           active_only: bool = True) -> List[Dict]:
    """教材一覧を取得。course_id指定でコース専用教材も含む"""
    supabase = get_supabase_client()
    try:
        query = supabase.table('learning_materials')\
            .select('*')\
            .eq('module_type', module_type)

        if active_only:
            query = query.eq('is_active', True)

        query = query.order('sort_order').order('created_at')
        result = query.execute()

        if not result.data:
            return []

        # 共通教材 + コース専用教材をフィルタ
        materials = []
        for m in result.data:
            if m.get('course_id') is None or m.get('course_id') == course_id:
                materials.append(m)
        return materials
    except Exception:
        return []


def get_learning_material(material_id: str) -> Optional[Dict]:
    """教材を1件取得"""
    supabase = get_supabase_client()
    try:
        result = supabase.table('learning_materials')\
            .select('*').eq('id', material_id).execute()
        return result.data[0] if result.data else None
    except Exception:
        return None


def upsert_learning_material(data: Dict) -> Optional[Dict]:
    """教材を作成/更新"""
    supabase = get_supabase_client()
    data['updated_at'] = datetime.utcnow().isoformat()
    try:
        result = supabase.table('learning_materials').upsert(
            data, on_conflict='module_type,material_key'
        ).execute()
        return result.data[0] if result.data else None
    except Exception:
        return None


def delete_learning_material(material_id: str) -> bool:
    """教材を削除（論理削除: is_active=False）"""
    supabase = get_supabase_client()
    try:
        supabase.table('learning_materials')\
            .update({'is_active': False, 'updated_at': datetime.utcnow().isoformat()})\
            .eq('id', material_id).execute()
        return True
    except Exception:
        return False


def seed_default_materials() -> int:
    """デモ教材をDBに投入（既存があればスキップ）"""
    count = 0

    # Listening
    try:
        from utils.listening import DEMO_LISTENING
        for key, data in DEMO_LISTENING.items():
            content = {k: v for k, v in data.items() if k not in ('title', 'level', 'category')}
            result = upsert_learning_material({
                'module_type': 'listening',
                'material_key': key,
                'title': data.get('title', key),
                'level': data.get('level', 'B1'),
                'category': data.get('category', ''),
                'content': content,
            })
            if result:
                count += 1
    except Exception:
        pass

    # Reading
    try:
        from utils.reading import DEMO_ARTICLES
        for key, data in DEMO_ARTICLES.items():
            content = {k: v for k, v in data.items() if k not in ('title', 'level', 'category')}
            result = upsert_learning_material({
                'module_type': 'reading',
                'material_key': key,
                'title': data.get('title', key),
                'level': data.get('level', 'B1'),
                'category': data.get('category', ''),
                'content': content,
            })
            if result:
                count += 1
    except Exception:
        pass

    # Vocabulary
    try:
        from utils.vocabulary import DEMO_WORD_LISTS
        for key, data in DEMO_WORD_LISTS.items():
            result = upsert_learning_material({
                'module_type': 'vocabulary',
                'material_key': key,
                'title': data.get('name', key),
                'description': data.get('description', ''),
                'content': {'words': data.get('words', [])},
            })
            if result:
                count += 1
    except Exception:
        pass

    return count


def get_student_reading_level(student_id: str, course_id: str = None) -> str:
    """学生のリーディングレベルをクイズ履歴から自動判定
    
    ロジック:
    - 履歴なし → B1（デフォルト）
    - 直近3回の平均スコアで判定
      80%以上 → 現レベルより1つ上
      50%未満 → 現レベルより1つ下
      その他  → 現レベル維持
    """
    supabase = get_supabase_client()
    
    LEVELS = ["A1", "A2", "B1", "B2", "C1"]
    DEFAULT_LEVEL = "B1"
    
    try:
        query = supabase.table('reading_logs')\
            .select('quiz_score, estimated_level')\
            .eq('student_id', student_id)\
            .not_.is_('quiz_score', 'null')\
            .order('completed_at', desc=True)\
            .limit(3)
        
        if course_id:
            query = query.eq('course_id', course_id)
        
        result = query.execute()
        logs = result.data if result.data else []
        
        if not logs:
            return DEFAULT_LEVEL
        
        scores = [l['quiz_score'] for l in logs if l.get('quiz_score') is not None]
        if not scores:
            return DEFAULT_LEVEL
        
        avg_score = sum(scores) / len(scores)
        current_level = logs[0].get('estimated_level', DEFAULT_LEVEL)
        if current_level not in LEVELS:
            current_level = DEFAULT_LEVEL
        
        current_idx = LEVELS.index(current_level)
        
        if avg_score >= 80 and current_idx < len(LEVELS) - 1:
            return LEVELS[current_idx + 1]
        elif avg_score < 50 and current_idx > 0:
            return LEVELS[current_idx - 1]
        else:
            return current_level
            
    except Exception:
        return DEFAULT_LEVEL



def get_extracurricular_score_for_course(course_id: str) -> dict:
    """授業外学習スコアを学生ごとに取得（course_id単位）"""
    try:
        supabase = get_supabase_client()
        result = supabase.table('practice_logs')            .select('student_id, score')            .eq('course_id', course_id)            .execute()
        logs = result.data if result.data else []
        from collections import defaultdict
        student_scores = defaultdict(list)
        for l in logs:
            if l.get('score') is not None:
                student_scores[l['student_id']].append(l['score'])
        return {
            sid: {
                "total_score": round(sum(scores) / len(scores)),
                "activity_count": len(scores)
            }
            for sid, scores in student_scores.items()
        }
    except Exception:
        return {}
