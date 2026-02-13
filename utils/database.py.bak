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


def get_supabase_client() -> Client:
    """Supabaseクライアントを取得（シングルトン）"""
    if 'supabase_client' not in st.session_state:
        url = st.secrets["supabase"]["url"]
        key = st.secrets["supabase"]["anon_key"]
        st.session_state.supabase_client = create_client(url, key)
    return st.session_state.supabase_client


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
        'score': scores.get('overall', 0) if scores else 0,
        'scores_detail': scores or {},
        'feedback': feedback,
        'details': {
            'task_type': task_type,
            'word_count': word_count,
            'cefr_level': cefr_level,
            'is_practice': is_practice,
            **kwargs
        },
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
        'score': scores.get('overall', 0) if scores else 0,
        'scores_detail': scores or {},
        'feedback': feedback,
        'details': {
            'japanese_text': japanese_text,
        },
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
        details={
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
