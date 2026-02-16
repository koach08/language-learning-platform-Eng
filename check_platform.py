#!/usr/bin/env python3
"""
English Learning Platform — 自動ヘルスチェック
実行: python check_platform.py
"""

import sys
import os
import re
import importlib

# プロジェクトルートをパスに追加
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# 色付き出力
GREEN = "\033[92m"
RED = "\033[91m"
YELLOW = "\033[93m"
BLUE = "\033[94m"
RESET = "\033[0m"
BOLD = "\033[1m"

def ok(msg):
    print(f"  {GREEN}✅ {msg}{RESET}")

def fail(msg):
    print(f"  {RED}❌ {msg}{RESET}")

def warn(msg):
    print(f"  {YELLOW}⚠️  {msg}{RESET}")

def info(msg):
    print(f"  {BLUE}ℹ️  {msg}{RESET}")

def header(msg):
    print(f"\n{BOLD}{'='*60}")
    print(f"  {msg}")
    print(f"{'='*60}{RESET}")

results = {"pass": 0, "fail": 0, "warn": 0}

def check_pass(msg):
    results["pass"] += 1
    ok(msg)

def check_fail(msg):
    results["fail"] += 1
    fail(msg)

def check_warn(msg):
    results["warn"] += 1
    warn(msg)


# ============================================================
# 1. ファイル存在チェック
# ============================================================
def check_files():
    header("1. ファイル存在チェック")
    
    required_files = [
        "app.py",
        ".streamlit/secrets.toml",
        "utils/database.py",
        "utils/auth.py",
        "views/listening.py",
        "views/reading.py",
        "views/learning_log.py",
        "views/speaking.py",
        "views/writing_submit.py",
        "views/vocabulary.py",
        "views/test_prep.py",
        "views/student_home.py",
        "views/teacher_home.py",
        "views/teacher_dashboard.py",
        "views/student_portfolio.py",
        "views/grades.py",
        "views/assignments.py",
        "views/course_settings.py",
        "views/class_settings.py",
    ]
    
    for f in required_files:
        if os.path.exists(f):
            check_pass(f)
        else:
            check_fail(f"見つかりません: {f}")


# ============================================================
# 2. ダミー・スタブ残存チェック
# ============================================================
def check_stubs():
    header("2. ダミー・スタブ残存チェック")
    
    stub_patterns = [
        "データベース接続後",
        "（※デモ）",
        "（※デモ表示）",
    ]
    
    exclude_files = ["speaking_submit.py", "teacher_settings.py", "teacher_tools.py", "teacher_home.py"]
    
    found_any = False
    for root, dirs, files in os.walk("."):
        # __pycache__, venv, .git を除外
        dirs[:] = [d for d in dirs if d not in ("__pycache__", "venv", ".venv", ".git", "node_modules")]
        for fname in files:
            if not fname.endswith(".py"):
                continue
            if fname in exclude_files:
                continue
            filepath = os.path.join(root, fname)
            try:
                with open(filepath, "r", encoding="utf-8") as f:
                    content = f.read()
                for pattern in stub_patterns:
                    if pattern in content:
                        lines = content.split("\n")
                        for i, line in enumerate(lines, 1):
                            if pattern in line:
                                check_fail(f"{filepath}:{i} — 「{pattern}」が残存")
                                found_any = True
            except Exception:
                pass
    
    if not found_any:
        check_pass("主要ファイルにダミー・スタブなし")


# ============================================================
# 3. Supabase接続チェック
# ============================================================
def check_supabase():
    header("3. Supabase接続チェック")
    
    try:
        # streamlit のsecretsを模擬
        import toml
        secrets_path = ".streamlit/secrets.toml"
        if not os.path.exists(secrets_path):
            check_fail("secrets.toml が見つかりません")
            return
        
        secrets = toml.load(secrets_path)
        url = secrets.get("supabase", {}).get("url", "")
        key = secrets.get("supabase", {}).get("anon_key", "")
        
        if not url or not key:
            check_fail("supabase URL または anon_key が設定されていません")
            return
        
        check_pass(f"secrets.toml 読み込みOK (URL: {url[:40]}...)")
        
        from supabase import create_client
        supabase = create_client(url, key)
        
        # テーブル存在チェック
        tables_to_check = [
            "users", "courses", "enrollments", "assignments", "submissions",
            "chat_sessions", "vocabulary", "practice_logs", "api_usage",
            "reading_logs", "listening_logs", "learning_logs",
            "writing_submissions", "teacher_notes", "learning_materials",
        ]
        
        for table in tables_to_check:
            try:
                result = supabase.table(table).select("id").limit(1).execute()
                count_result = supabase.table(table).select("id", count="exact").execute()
                count = count_result.count if count_result.count is not None else len(count_result.data)
                check_pass(f"テーブル {table} — OK ({count}件)")
            except Exception as e:
                err_str = str(e)
                if "does not exist" in err_str or "relation" in err_str:
                    check_fail(f"テーブル {table} — 存在しません！")
                else:
                    check_warn(f"テーブル {table} — アクセスエラー: {err_str[:80]}")
    
    except ImportError as e:
        check_warn(f"インポートエラー: {e} (pip install supabase toml)")
    except Exception as e:
        check_fail(f"Supabase接続エラー: {e}")


# ============================================================
# 4. database.py 関数チェック
# ============================================================
def check_database_functions():
    header("4. database.py 関数チェック")
    
    required_functions = [
        # User
        "get_or_create_user", "get_user_by_email",
        # Course
        "get_teacher_courses", "get_course_students",
        # Practice
        "log_practice", "get_student_practice_stats",
        # Speaking
        "create_speaking_submission",
        # Writing
        "save_writing_submission", "get_writing_assignments",
        # Vocabulary
        "add_vocabulary", "get_vocabulary_for_review",
        # Reading
        "log_reading", "get_student_reading_logs",
        # Listening（今回追加）
        "log_listening", "get_student_listening_logs", "get_listening_stats_for_course",
        # Learning Log（今回追加）
        "save_learning_log", "get_student_learning_logs", "delete_learning_log",
        # Chat
        "save_chat_session_full",
        # Teacher
        "get_students_with_activity_summary",
    ]
    
    try:
        with open("utils/database.py", "r", encoding="utf-8") as f:
            content = f.read()
        
        for func in required_functions:
            if f"def {func}" in content:
                check_pass(f"{func}()")
            else:
                check_fail(f"{func}() — database.pyに未定義")
    except Exception as e:
        check_fail(f"database.py読み込みエラー: {e}")


# ============================================================
# 5. Views → database.py 接続チェック
# ============================================================
def check_view_db_integration():
    header("5. Views → DB接続チェック")
    
    view_checks = {
        "views/speaking.py": ["log_practice", "create_speaking_submission"],
        "views/writing_submit.py": ["save_writing_submission"],
        "views/vocabulary.py": ["add_vocabulary", "log_practice"],
        "views/reading.py": ["get_student_reading_logs"],
        "views/listening.py": ["log_listening", "log_practice", "get_student_listening_logs"],
        "views/learning_log.py": ["save_learning_log", "get_student_learning_logs", "delete_learning_log"],
        "views/student_portfolio.py": ["get_student_practice_stats"],
        "views/teacher_dashboard.py": ["get_students_with_activity_summary"],
        "views/assignments.py": ["create_assignment"],
    }
    
    for filepath, functions in view_checks.items():
        if not os.path.exists(filepath):
            check_fail(f"{filepath} — ファイルなし")
            continue
        
        with open(filepath, "r", encoding="utf-8") as f:
            content = f.read()
        
        missing = []
        for func in functions:
            if func not in content:
                missing.append(func)
        
        if not missing:
            check_pass(f"{filepath} — DB接続OK ({', '.join(functions)})")
        else:
            check_fail(f"{filepath} — 未接続: {', '.join(missing)}")


# ============================================================
# 6. 年度チェック
# ============================================================
def check_year():
    header("6. 年度チェック（2026年度）")
    
    files_to_check = {
        "views/teacher_home.py": "DEFAULT_CLASSES",
    }
    
    for filepath, context in files_to_check.items():
        if not os.path.exists(filepath):
            check_warn(f"{filepath} — ファイルなし")
            continue
        
        with open(filepath, "r", encoding="utf-8") as f:
            content = f.read()
        
        if "2025前期" in content or "ESA2025" in content or "ESB2025" in content:
            check_fail(f"{filepath} — 2025年度のクラスデータが残存")
        elif "2026" in content:
            check_pass(f"{filepath} — 2026年度に更新済み")
        else:
            check_warn(f"{filepath} — 年度情報が見つかりません")
    
    # 旧クラスキー参照チェック
    old_keys = ["english_specific_a", "english_specific_b", "english_seminar", "ENGSEM2025"]
    for root, dirs, files in os.walk("views"):
        dirs[:] = [d for d in dirs if d != "__pycache__"]
        for fname in files:
            if not fname.endswith(".py"):
                continue
            filepath = os.path.join(root, fname)
            with open(filepath, "r", encoding="utf-8") as f:
                content = f.read()
            for key in old_keys:
                if key in content:
                    check_fail(f"{filepath} — 旧クラスキー「{key}」が残存")


# ============================================================
# 7. secrets.toml 設定チェック
# ============================================================
def check_secrets():
    header("7. secrets.toml 設定チェック")
    
    try:
        import toml
        secrets = toml.load(".streamlit/secrets.toml")
        
        required_keys = {
            "supabase": ["url", "anon_key"],
            "openai": ["api_key"],
            "azure_speech": ["api_key", "region"],
            "app": ["teacher_emails"],
        }
        
        for section, keys in required_keys.items():
            if section not in secrets:
                check_fail(f"[{section}] セクションなし")
                continue
            for key in keys:
                if key in secrets[section] and secrets[section][key]:
                    check_pass(f"[{section}].{key} — 設定済み")
                else:
                    check_fail(f"[{section}].{key} — 未設定")
    
    except ImportError:
        check_warn("toml パッケージなし (pip install toml)")
    except Exception as e:
        check_fail(f"secrets.toml エラー: {e}")


# ============================================================
# 8. Python構文チェック
# ============================================================
def check_syntax():
    header("8. Python構文チェック")
    
    import ast
    
    py_files = []
    for root, dirs, files in os.walk("."):
        dirs[:] = [d for d in dirs if d not in ("__pycache__", "venv", ".venv", ".git")]
        for fname in files:
            if fname.endswith(".py"):
                py_files.append(os.path.join(root, fname))
    
    errors = []
    for filepath in py_files:
        try:
            with open(filepath, "r", encoding="utf-8") as f:
                ast.parse(f.read())
        except SyntaxError as e:
            errors.append((filepath, e))
    
    if not errors:
        check_pass(f"全{len(py_files)}ファイル — 構文エラーなし")
    else:
        for filepath, e in errors:
            check_fail(f"{filepath}:{e.lineno} — {e.msg}")


# ============================================================
# 9. app.py ルーティングチェック
# ============================================================
def check_routing():
    header("9. app.py ルーティングチェック")
    
    with open("app.py", "r", encoding="utf-8") as f:
        content = f.read()
    
    expected_routes = [
        "speaking", "writing", "vocabulary", "reading", 
        "listening", "test_prep", "learning_log",
        "teacher_home", "student_home",
    ]
    
    for route in expected_routes:
        if f'"{route}"' in content:
            check_pass(f"ルート: {route}")
        else:
            check_warn(f"ルート: {route} — app.pyに未定義")


# ============================================================
# メイン
# ============================================================
def main():
    print(f"\n{BOLD}🔍 English Learning Platform ヘルスチェック{RESET}")
    print(f"   実行日時: {__import__('datetime').datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"   ディレクトリ: {os.getcwd()}")
    
    check_files()
    check_stubs()
    check_supabase()
    check_database_functions()
    check_view_db_integration()
    check_year()
    check_secrets()
    check_syntax()
    check_routing()
    
    # サマリー
    header("📊 結果サマリー")
    total = results["pass"] + results["fail"] + results["warn"]
    print(f"  {GREEN}✅ PASS: {results['pass']}{RESET}")
    print(f"  {RED}❌ FAIL: {results['fail']}{RESET}")
    print(f"  {YELLOW}⚠️  WARN: {results['warn']}{RESET}")
    print(f"  合計: {total}項目\n")
    
    if results["fail"] == 0:
        print(f"  {GREEN}{BOLD}🎉 全チェック合格！試用運転の準備ができています。{RESET}\n")
    else:
        print(f"  {RED}{BOLD}⚠️  {results['fail']}件の問題があります。上記の❌を確認してください。{RESET}\n")
    
    return results["fail"]


if __name__ == "__main__":
    sys.exit(main())
