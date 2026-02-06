"""
Utils Package
=============
ユーティリティモジュール
"""

from .auth import (
    is_authenticated,
    get_current_user,
    is_teacher,
    is_student,
    login_with_google,
    logout,
    require_auth,
    require_teacher,
    require_student,
    handle_oauth_callback,
    inject_oauth_handler
)

from .database import (
    get_supabase_client,
    get_user_by_email,
    create_user,
    update_user,
    get_or_create_user,
    get_teacher_courses,
    get_student_courses,
    create_course,
    get_course,
    update_course,
    enroll_student,
    get_course_students,
    create_assignment,
    get_course_assignments,
    get_assignment,
    create_submission,
    get_student_submissions,
    get_assignment_submissions,
    update_submission,
    create_chat_session,
    update_chat_session,
    get_student_chat_sessions,
    add_vocabulary,
    get_vocabulary_for_review,
    update_vocabulary_after_review,
    log_practice,
    get_student_practice_stats,
    log_api_usage
)

__all__ = [
    # Auth
    'is_authenticated',
    'get_current_user',
    'is_teacher',
    'is_student',
    'login_with_google',
    'logout',
    'require_auth',
    'require_teacher',
    'require_student',
    'handle_oauth_callback',
    'inject_oauth_handler',
    
    # Database
    'get_supabase_client',
    'get_user_by_email',
    'create_user',
    'update_user',
    'get_or_create_user',
    'get_teacher_courses',
    'get_student_courses',
    'create_course',
    'get_course',
    'update_course',
    'enroll_student',
    'get_course_students',
    'create_assignment',
    'get_course_assignments',
    'get_assignment',
    'create_submission',
    'get_student_submissions',
    'get_assignment_submissions',
    'update_submission',
    'create_chat_session',
    'update_chat_session',
    'get_student_chat_sessions',
    'add_vocabulary',
    'get_vocabulary_for_review',
    'update_vocabulary_after_review',
    'log_practice',
    'get_student_practice_stats',
    'log_api_usage'
]
