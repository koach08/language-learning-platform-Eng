"""
utils/analytics.py
学習分析データをSupabase DBから取得する。
session_stateはキャッシュとして使い、リロード後も消えないようにする。
"""

import streamlit as st
from datetime import datetime, timedelta


# ===== module_type → カテゴリ マッピング =====
MODULE_CATEGORY = {
    'speaking': 'speaking',
    'speaking_pronunciation': 'speaking',
    'speaking_chat': 'speaking',
    'speaking_read_aloud': 'speaking',
    'writing': 'writing',
    'writing_practice': 'writing',
    'writing_submission': 'writing',
    'reading': 'reading',
    'reading_practice': 'reading',
    'listening': 'listening',
    'listening_dictation': 'listening',
    'listening_youtube': 'listening',
    'vocabulary': 'vocabulary',
    'vocabulary_quiz': 'vocabulary',
    'vocabulary_flashcard': 'vocabulary',
    'vocabulary_exercise': 'vocabulary',
}


def _get_category(module_type: str) -> str:
    return MODULE_CATEGORY.get(module_type, module_type.split('_')[0])


def get_analytics_data(days: int = 30) -> dict:
    """
    Supabase practice_logs からユーザーの学習データを取得・集計する。
    結果を session_state にキャッシュ（TTL: 60秒）。
    """
    user = st.session_state.get('user')
    if not user:
        return _empty_analytics()

    student_id = user.get('id')
    cache_key = f'analytics_db_{student_id}'
    cache_ts_key = f'analytics_db_ts_{student_id}'

    # キャッシュが60秒以内なら再利用
    now = datetime.now()
    cached_ts = st.session_state.get(cache_ts_key)
    if cached_ts and (now - cached_ts).total_seconds() < 60:
        cached = st.session_state.get(cache_key)
        if cached:
            return cached

    # DBから取得
    try:
        from utils.database import get_supabase_client
        supabase = get_supabase_client()
        since = (datetime.utcnow() - timedelta(days=days)).isoformat()

        result = supabase.table('practice_logs') \
            .select('module_type, duration_seconds, score, practiced_at') \
            .eq('student_id', student_id) \
            .gte('practiced_at', since) \
            .order('practiced_at', desc=False) \
            .execute()

        logs = result.data or []
        data = _aggregate_logs(logs)
        # NOTE: reading_logs / listening_logs は practice_logs にも同時記録されるため
        # ここでは統合しない（二重カウント防止）。
        # analytics の集計は practice_logs のみで完結する設計。

    except Exception:
        # DB接続失敗時は空データを返す（session_stateの古いデータがあれば使う）
        data = st.session_state.get(cache_key) or _empty_analytics()

    st.session_state[cache_key] = data
    st.session_state[cache_ts_key] = now
    return data


def _empty_analytics() -> dict:
    return {
        'study_sessions': [],
        'module_time': {
            'speaking': 0,
            'writing': 0,
            'vocabulary': 0,
            'reading': 0,
            'listening': 0,
        },
        'daily_time': {},
        'speaking_scores': [],
        'writing_scores': [],
        'reading_scores': [],
        'vocabulary_scores': [],
        'listening_scores': [],
        'pronunciation_details': {},
        'grammar_errors': {},
        'cefr_history': [],
        'weak_areas': [],
    }


def _aggregate_logs(logs: list) -> dict:
    """practice_logs のリストを analytics_data 形式に集計"""
    data = _empty_analytics()

    for log in logs:
        raw_module = log.get('module_type', '')
        category = _get_category(raw_module)
        duration_sec = log.get('duration_seconds') or 0
        score = log.get('score')
        practiced_at = log.get('practiced_at', '')

        # 日付パース
        try:
            dt = datetime.fromisoformat(practiced_at.replace('Z', '+00:00'))
            date_str = dt.strftime('%Y-%m-%d')
        except Exception:
            date_str = datetime.now().strftime('%Y-%m-%d')

        minutes = max(1, duration_sec // 60) if duration_sec else 1

        # モジュール別累計時間
        if category in data['module_time']:
            data['module_time'][category] += minutes

        # 日別時間
        if date_str not in data['daily_time']:
            data['daily_time'][date_str] = {}
        data['daily_time'][date_str][category] = \
            data['daily_time'][date_str].get(category, 0) + minutes

        # セッション記録
        data['study_sessions'].append({
            'module': category,
            'date': date_str,
            'minutes': minutes,
            'timestamp': practiced_at,
        })

        # スコア記録
        if score is not None:
            score_key = f'{category}_scores'
            if score_key in data:
                data[score_key].append({
                    'score': float(score),
                    'date': date_str,
                    'timestamp': practiced_at,
                    'details': {}
                })

    # CEFR推定を更新
    update_cefr_estimate(data)
    return data


# ===== キャッシュ無効化 =====

def invalidate_analytics_cache():
    """練習記録後にキャッシュを無効化してすぐ反映させる"""
    user = st.session_state.get('user')
    if not user:
        return
    student_id = user.get('id')
    ts_key = f'analytics_db_ts_{student_id}'
    if ts_key in st.session_state:
        del st.session_state[ts_key]


# ===== スコア記録（後方互換・DBへの直接書き込みはしない） =====

def record_score(module, score, details=None):
    """
    後方互換用。
    実際の永続化は log_practice() (database.py) で行う。
    ここではキャッシュを無効化するだけ。
    """
    invalidate_analytics_cache()


def log_study_time(module, minutes):
    """後方互換用。キャッシュを無効化するだけ。"""
    invalidate_analytics_cache()


def start_study_session(module):
    """学習セッション開始タイマー"""
    st.session_state['_study_session'] = {
        'module': module,
        'start_time': datetime.now(),
    }


def end_study_session() -> int:
    """学習セッション終了・経過分数を返す"""
    session = st.session_state.get('_study_session')
    if not session:
        return 0
    elapsed = (datetime.now() - session['start_time']).total_seconds()
    minutes = max(1, int(elapsed / 60))
    if '_study_session' in st.session_state:
        del st.session_state['_study_session']
    invalidate_analytics_cache()
    return minutes


# ===== CEFR推定 =====

def estimate_cefr(avg_score: float) -> str:
    if avg_score >= 90:
        return 'C1'
    elif avg_score >= 80:
        return 'B2'
    elif avg_score >= 70:
        return 'B1'
    elif avg_score >= 55:
        return 'A2'
    else:
        return 'A1'


def update_cefr_estimate(data: dict):
    all_scores = []
    for key in ['speaking_scores', 'writing_scores', 'reading_scores',
                'vocabulary_scores', 'listening_scores']:
        for entry in data.get(key, []):
            all_scores.append(entry['score'])

    if not all_scores:
        return

    recent = all_scores[-20:]
    avg = sum(recent) / len(recent)
    cefr = estimate_cefr(avg)
    today = datetime.now().strftime('%Y-%m-%d')

    history = data['cefr_history']
    if not history or history[-1]['date'] != today:
        history.append({
            'date': today,
            'level': cefr,
            'avg_score': round(avg, 1)
        })


# ===== 弱点分析 =====

def analyze_weaknesses(data: dict) -> list:
    weaknesses = []

    module_avgs = {}
    for module in ['speaking', 'writing', 'reading', 'vocabulary', 'listening']:
        scores = data.get(f'{module}_scores', [])
        if scores:
            recent = [s['score'] for s in scores[-10:]]
            module_avgs[module] = sum(recent) / len(recent)

    if module_avgs:
        overall_avg = sum(module_avgs.values()) / len(module_avgs)
        module_names = {
            'speaking': 'スピーキング', 'writing': 'ライティング',
            'reading': 'リーディング', 'vocabulary': '語彙',
            'listening': 'リスニング'
        }
        for module, avg in module_avgs.items():
            if avg < overall_avg - 10:
                weaknesses.append({
                    'type': 'module',
                    'area': module_names.get(module, module),
                    'score': round(avg, 1),
                    'gap': round(overall_avg - avg, 1),
                    'suggestion': f'{module_names.get(module, module)}の練習を増やしましょう'
                })

    module_time = data.get('module_time', {})
    total_time = sum(module_time.values())
    if total_time > 60:
        module_names = {
            'speaking': 'スピーキング', 'writing': 'ライティング',
            'reading': 'リーディング', 'vocabulary': '語彙',
            'listening': 'リスニング'
        }
        for module, minutes in module_time.items():
            if total_time > 0 and minutes / total_time < 0.1:
                weaknesses.append({
                    'type': 'time',
                    'area': f'学習時間: {module_names.get(module, module)}',
                    'score': minutes,
                    'gap': 0,
                    'suggestion': f'{module_names.get(module, module)}の練習時間が少ないです'
                })

    data['weak_areas'] = weaknesses
    return weaknesses


# ===== UI表示関数（student_home等から呼ばれる） =====

def show_analytics_dashboard():
    data = get_analytics_data()

    st.markdown("### 📊 学習分析 / Learning Analytics")

    total_time = sum(data['module_time'].values())
    all_scores = []
    for key in ['speaking_scores', 'writing_scores', 'reading_scores',
                'vocabulary_scores', 'listening_scores']:
        all_scores.extend([s['score'] for s in data.get(key, [])])

    avg_score = sum(all_scores) / len(all_scores) if all_scores else 0
    cefr = estimate_cefr(avg_score) if all_scores else '-'

    col1, col2, col3, col4 = st.columns(4)
    with col1:
        hours = total_time // 60
        mins = total_time % 60
        st.metric("総学習時間", f"{hours}h {mins}m")
    with col2:
        st.metric("総セッション", f"{len(data['study_sessions'])}回")
    with col3:
        st.metric("平均スコア", f"{avg_score:.1f}" if all_scores else "-")
    with col4:
        st.metric("推定CEFR", cefr)

    st.markdown("---")
    show_study_time_chart(data)
    st.markdown("---")
    show_skill_analysis(data)
    st.markdown("---")
    show_weakness_analysis(data)
    st.markdown("---")
    show_cefr_progress(data)


def show_study_time_chart(data):
    st.markdown("#### ⏱️ 学習時間")

    module_time = data.get('module_time', {})
    module_names = {
        'speaking': '🗣️ Speaking', 'writing': '✍️ Writing',
        'reading': '📖 Reading', 'vocabulary': '📚 Vocabulary',
        'listening': '🎧 Listening'
    }

    if any(v > 0 for v in module_time.values()):
        cols = st.columns(5)
        for i, (module, minutes) in enumerate(module_time.items()):
            with cols[i]:
                hours = minutes // 60
                mins = minutes % 60
                st.metric(module_names.get(module, module), f"{hours}h {mins}m")
    else:
        st.info("まだ学習記録がありません")

    st.markdown("**過去7日間:**")
    daily_time = data.get('daily_time', {})
    days = []
    for i in range(6, -1, -1):
        date = (datetime.now() - timedelta(days=i)).strftime("%Y-%m-%d")
        day_label = (datetime.now() - timedelta(days=i)).strftime("%m/%d")
        day_total = sum(daily_time.get(date, {}).values())
        days.append({"日付": day_label, "学習時間(分)": day_total})

    if any(d['学習時間(分)'] > 0 for d in days):
        import pandas as pd
        df = pd.DataFrame(days)
        st.bar_chart(df.set_index("日付"))
    else:
        st.caption("過去7日間のデータなし")


def show_skill_analysis(data):
    st.markdown("#### 🎯 スキル別スコア")

    modules = {
        'speaking': {'name': '🗣️ Speaking', 'scores': data.get('speaking_scores', [])},
        'writing': {'name': '✍️ Writing', 'scores': data.get('writing_scores', [])},
        'reading': {'name': '📖 Reading', 'scores': data.get('reading_scores', [])},
        'vocabulary': {'name': '📚 Vocabulary', 'scores': data.get('vocabulary_scores', [])},
        'listening': {'name': '🎧 Listening', 'scores': data.get('listening_scores', [])},
    }

    has_data = False
    cols = st.columns(5)

    for i, (key, mod) in enumerate(modules.items()):
        with cols[i]:
            scores = [s['score'] for s in mod['scores']]
            if scores:
                has_data = True
                avg = sum(scores) / len(scores)
                recent = scores[-5:]
                recent_avg = sum(recent) / len(recent)
                trend = recent_avg - avg
                st.metric(mod['name'], f"{recent_avg:.0f}",
                          f"{'+' if trend >= 0 else ''}{trend:.1f}")
                st.caption(f"回数: {len(scores)}")
            else:
                st.metric(mod['name'], "-")
                st.caption("データなし")

    if not has_data:
        st.info("スコアデータがまだありません。各モジュールで練習するとここに反映されます。")

    if has_data:
        all_entries = []
        for key, mod in modules.items():
            for entry in mod['scores'][-20:]:
                all_entries.append({
                    '日付': entry['date'],
                    'スコア': entry['score'],
                    'モジュール': mod['name']
                })
        if all_entries:
            import pandas as pd
            df = pd.DataFrame(all_entries)
            st.markdown("**スコア推移（直近20件）:**")
            st.line_chart(df.pivot_table(
                index='日付', columns='モジュール', values='スコア', aggfunc='mean'))


def show_weakness_analysis(data):
    st.markdown("#### ⚠️ 弱点分析 / Weakness Analysis")
    weaknesses = analyze_weaknesses(data)

    if not weaknesses:
        st.success("🎉 現在、目立った弱点はありません。この調子で頑張りましょう！")
        st.caption("データが増えると、より詳しい分析ができるようになります。")
        return

    for w in weaknesses[:5]:
        icon = {'module': '📊', 'pronunciation': '🔊',
                'grammar': '📝', 'time': '⏱️'}.get(w['type'], '⚠️')
        with st.expander(f"{icon} {w['area']}"):
            if w['type'] == 'module':
                st.markdown(f"**スコア:** {w['score']}点（全体平均より {w['gap']}点低い）")
            elif w['type'] == 'time':
                st.markdown(f"**学習時間:** {w['score']}分")
            st.info(f"💡 {w['suggestion']}")


def show_cefr_progress(data):
    st.markdown("#### 📈 CEFRレベル推移")
    history = data.get('cefr_history', [])

    if not history:
        st.info("スコアデータが蓄積されると、CEFRレベルの推移が表示されます。")
        return

    cefr_to_num = {'A1': 1, 'A2': 2, 'B1': 3, 'B2': 4, 'C1': 5, 'C2': 6}
    import pandas as pd

    chart_data = [{'日付': e['date'],
                   'CEFRレベル': cefr_to_num.get(e['level'], 0),
                   '平均スコア': e['avg_score']} for e in history]

    if chart_data:
        df = pd.DataFrame(chart_data)
        col1, col2 = st.columns(2)
        with col1:
            st.markdown("**レベル推移:**")
            st.line_chart(df.set_index('日付')['CEFRレベル'])
            st.caption("1=A1, 2=A2, 3=B1, 4=B2, 5=C1")
        with col2:
            st.markdown("**平均スコア推移:**")
            st.line_chart(df.set_index('日付')['平均スコア'])


def show_teacher_analytics():
    """教員向けクラス分析（デモ）"""
    st.markdown("### 📊 クラス学習分析")

    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("平均学習時間", "4.2h/週")
    with col2:
        st.metric("平均スコア", "71.5")
    with col3:
        st.metric("課題提出率", "82%")
    with col4:
        st.metric("アクティブ率", "90%")

    st.markdown("---")
    st.markdown("#### ⚠️ 要注意学生")
    try:
        from utils.database import get_supabase_client
        from datetime import datetime, timedelta
        supabase = get_supabase_client()
        two_weeks_ago = (datetime.utcnow() - timedelta(weeks=2)).isoformat()

        # 全学生取得
        students_result = supabase.table('class_enrollments')            .select('student_id, profiles(display_name)')            .eq('class_id', course_id)            .execute()
        students = students_result.data if students_result.data else []

        alerts = []
        for s in students:
            sid = s.get('student_id')
            name = s.get('profiles', {}).get('display_name', sid[:8] if sid else '不明')

            # 2週間ログインなし
            login_result = supabase.table('practice_logs')                .select('id')                .eq('student_id', sid)                .gte('created_at', two_weeks_ago)                .limit(1).execute()
            if not login_result.data:
                alerts.append({"name": name, "issue": "過去2週間活動なし", "severity": "高"})
                continue

            # 課題未提出
            assign_result = supabase.table('assignment_submissions')                .select('id')                .eq('student_id', sid)                .execute()
            submitted_ids = [r['id'] for r in (assign_result.data or [])]
            all_assign = supabase.table('assignments')                .select('id')                .eq('course_id', course_id)                .execute()
            total = len(all_assign.data or [])
            missing = total - len(submitted_ids)
            if missing >= 2:
                alerts.append({"name": name, "issue": f"課題未提出が{missing}件", "severity": "中"})

        if alerts:
            for alert in alerts:
                if alert['severity'] == '高':
                    st.error(f"🚨 **{alert['name']}** - {alert['issue']}")
                else:
                    st.warning(f"⚠️ **{alert['name']}** - {alert['issue']}")
        else:
            st.success("要注意学生はいません")
    except Exception as e:
        st.info(f"要注意学生データを取得できませんでした: {e}")

    st.markdown("---")
    st.markdown("#### 📊 モジュール別クラス平均")
    try:
        import pandas as pd
        from utils.database import get_supabase_client
        supabase = get_supabase_client()
        modules = ['speaking', 'writing', 'reading', 'vocabulary', 'listening']
        rows = []
        for mod in modules:
            result = supabase.table('practice_logs')                .select('score')                .eq('course_id', course_id)                .eq('module', mod)                .not_.is_('score', 'null')                .execute()
            scores = [r['score'] for r in (result.data or []) if r.get('score')]
            avg = round(sum(scores)/len(scores)) if scores else None
            rows.append({'モジュール': mod.capitalize(), 'クラス平均': avg if avg else '—'})
        class_data = pd.DataFrame(rows)
        st.dataframe(class_data, use_container_width=True, hide_index=True)
    except Exception as e:
        st.info(f"モジュール別データを取得できませんでした: {e}")
