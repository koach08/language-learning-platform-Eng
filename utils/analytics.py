import streamlit as st
from datetime import datetime, timedelta


def get_user_key():
    """現在のユーザーキーを取得"""
    user = st.session_state.get('user')
    if user:
        return user.get('student_id') or user.get('email') or 'unknown'
    return 'unknown'


def get_analytics_data():
    """学習分析データを取得"""
    user_key = get_user_key()
    key = f'analytics_{user_key}'
    
    if key not in st.session_state:
        st.session_state[key] = {
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
    
    return st.session_state[key]


# ===== 学習時間トラッキング =====

def start_study_session(module):
    """学習セッション開始"""
    st.session_state['_study_session'] = {
        'module': module,
        'start_time': datetime.now(),
    }


def end_study_session():
    """学習セッション終了・記録"""
    session = st.session_state.get('_study_session')
    if not session:
        return 0
    
    elapsed = (datetime.now() - session['start_time']).total_seconds()
    minutes = int(elapsed / 60)
    
    if minutes < 1:
        minutes = 1
    
    data = get_analytics_data()
    module = session['module']
    today = datetime.now().strftime("%Y-%m-%d")
    
    # モジュール別累計
    data['module_time'][module] = data['module_time'].get(module, 0) + minutes
    
    # 日別累計
    if today not in data['daily_time']:
        data['daily_time'][today] = {}
    data['daily_time'][today][module] = data['daily_time'][today].get(module, 0) + minutes
    
    # セッション記録
    data['study_sessions'].append({
        'module': module,
        'date': today,
        'minutes': minutes,
        'timestamp': datetime.now().strftime("%Y-%m-%d %H:%M")
    })
    
    # セッション削除
    if '_study_session' in st.session_state:
        del st.session_state['_study_session']
    
    return minutes


def log_study_time(module, minutes):
    """学習時間を直接記録"""
    data = get_analytics_data()
    today = datetime.now().strftime("%Y-%m-%d")
    
    data['module_time'][module] = data['module_time'].get(module, 0) + minutes
    
    if today not in data['daily_time']:
        data['daily_time'][today] = {}
    data['daily_time'][today][module] = data['daily_time'][today].get(module, 0) + minutes
    
    data['study_sessions'].append({
        'module': module,
        'date': today,
        'minutes': minutes,
        'timestamp': datetime.now().strftime("%Y-%m-%d %H:%M")
    })


# ===== スコア記録 =====

def record_score(module, score, details=None):
    """スコアを記録"""
    data = get_analytics_data()
    
    entry = {
        'score': score,
        'date': datetime.now().strftime("%Y-%m-%d"),
        'timestamp': datetime.now().strftime("%Y-%m-%d %H:%M"),
        'details': details or {}
    }
    
    key = f'{module}_scores'
    if key in data:
        data[key].append(entry)
    
    # CEFR推定更新
    update_cefr_estimate(data)


def record_pronunciation_detail(phoneme, correct):
    """発音の音素別データを記録"""
    data = get_analytics_data()
    
    if phoneme not in data['pronunciation_details']:
        data['pronunciation_details'][phoneme] = {'total': 0, 'correct': 0}
    
    data['pronunciation_details'][phoneme]['total'] += 1
    if correct:
        data['pronunciation_details'][phoneme]['correct'] += 1


def record_grammar_error(error_type, example=''):
    """文法エラーを記録"""
    data = get_analytics_data()
    
    if error_type not in data['grammar_errors']:
        data['grammar_errors'][error_type] = {'count': 0, 'examples': []}
    
    data['grammar_errors'][error_type]['count'] += 1
    if example and len(data['grammar_errors'][error_type]['examples']) < 5:
        data['grammar_errors'][error_type]['examples'].append(example)


# ===== CEFR推定 =====

def estimate_cefr(avg_score):
    """平均スコアからCEFRレベルを推定"""
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


def update_cefr_estimate(data):
    """全スコアからCEFR推定を更新"""
    all_scores = []
    for key in ['speaking_scores', 'writing_scores', 'reading_scores', 'vocabulary_scores', 'listening_scores']:
        for entry in data.get(key, []):
            all_scores.append(entry['score'])
    
    if not all_scores:
        return
    
    recent = all_scores[-20:]
    avg = sum(recent) / len(recent)
    cefr = estimate_cefr(avg)
    
    today = datetime.now().strftime("%Y-%m-%d")
    
    # 同日の重複を避ける
    history = data['cefr_history']
    if not history or history[-1]['date'] != today:
        history.append({
            'date': today,
            'level': cefr,
            'avg_score': round(avg, 1)
        })


# ===== 弱点分析 =====

def analyze_weaknesses(data):
    """弱点を分析"""
    weaknesses = []
    
    # モジュール別スコア比較
    module_avgs = {}
    for module in ['speaking', 'writing', 'reading', 'vocabulary', 'listening']:
        scores = data.get(f'{module}_scores', [])
        if scores:
            recent = [s['score'] for s in scores[-10:]]
            module_avgs[module] = sum(recent) / len(recent)
    
    if module_avgs:
        overall_avg = sum(module_avgs.values()) / len(module_avgs)
        for module, avg in module_avgs.items():
            if avg < overall_avg - 10:
                module_names = {
                    'speaking': 'スピーキング',
                    'writing': 'ライティング',
                    'reading': 'リーディング',
                    'vocabulary': '語彙',
                    'listening': 'リスニング'
                }
                weaknesses.append({
                    'type': 'module',
                    'area': module_names.get(module, module),
                    'score': round(avg, 1),
                    'gap': round(overall_avg - avg, 1),
                    'suggestion': f'{module_names.get(module, module)}の練習を増やしましょう'
                })
    
    # 発音の弱点
    for phoneme, stats in data.get('pronunciation_details', {}).items():
        if stats['total'] >= 3:
            accuracy = stats['correct'] / stats['total']
            if accuracy < 0.6:
                weaknesses.append({
                    'type': 'pronunciation',
                    'area': f'発音: {phoneme}',
                    'score': round(accuracy * 100, 1),
                    'gap': round((0.8 - accuracy) * 100, 1),
                    'suggestion': f'「{phoneme}」の発音を重点的に練習しましょう'
                })
    
    # 文法エラー
    for error_type, stats in data.get('grammar_errors', {}).items():
        if stats['count'] >= 3:
            weaknesses.append({
                'type': 'grammar',
                'area': f'文法: {error_type}',
                'score': stats['count'],
                'gap': 0,
                'suggestion': f'「{error_type}」のエラーが多いです。復習しましょう'
            })
    
    # 学習時間の偏り
    module_time = data.get('module_time', {})
    total_time = sum(module_time.values())
    if total_time > 60:
        for module, minutes in module_time.items():
            ratio = minutes / total_time
            if ratio < 0.1:
                module_names = {
                    'speaking': 'スピーキング',
                    'writing': 'ライティング',
                    'reading': 'リーディング',
                    'vocabulary': '語彙',
                    'listening': 'リスニング'
                }
                weaknesses.append({
                    'type': 'time',
                    'area': f'学習時間: {module_names.get(module, module)}',
                    'score': minutes,
                    'gap': 0,
                    'suggestion': f'{module_names.get(module, module)}の練習時間が少ないです'
                })
    
    data['weak_areas'] = weaknesses
    return weaknesses


# ===== UI表示関数 =====

def show_analytics_dashboard():
    """学習分析ダッシュボード"""
    
    data = get_analytics_data()
    
    st.markdown("### 📊 学習分析 / Learning Analytics")
    
    # ===== 概要 =====
    total_time = sum(data['module_time'].values())
    total_sessions = len(data['study_sessions'])
    
    all_scores = []
    for key in ['speaking_scores', 'writing_scores', 'reading_scores', 'vocabulary_scores', 'listening_scores']:
        all_scores.extend([s['score'] for s in data.get(key, [])])
    
    avg_score = sum(all_scores) / len(all_scores) if all_scores else 0
    cefr = estimate_cefr(avg_score) if all_scores else '-'
    
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        hours = total_time // 60
        mins = total_time % 60
        st.metric("総学習時間", f"{hours}h {mins}m")
    with col2:
        st.metric("総セッション", f"{total_sessions}回")
    with col3:
        st.metric("平均スコア", f"{avg_score:.1f}" if all_scores else "-")
    with col4:
        st.metric("推定CEFR", cefr)
    
    st.markdown("---")
    
    # ===== 学習時間 =====
    show_study_time_chart(data)
    
    st.markdown("---")
    
    # ===== スキル別分析 =====
    show_skill_analysis(data)
    
    st.markdown("---")
    
    # ===== 弱点分析 =====
    show_weakness_analysis(data)
    
    st.markdown("---")
    
    # ===== CEFR推移 =====
    show_cefr_progress(data)


def show_study_time_chart(data):
    """学習時間グラフ"""
    
    st.markdown("#### ⏱️ 学習時間")
    
    # モジュール別
    module_time = data.get('module_time', {})
    module_names = {
        'speaking': '🗣️ Speaking',
        'writing': '✍️ Writing',
        'reading': '📖 Reading',
        'vocabulary': '📚 Vocabulary',
        'listening': '🎧 Listening'
    }
    
    if any(v > 0 for v in module_time.values()):
        cols = st.columns(5)
        for i, (module, minutes) in enumerate(module_time.items()):
            with cols[i]:
                name = module_names.get(module, module)
                hours = minutes // 60
                mins = minutes % 60
                st.metric(name, f"{hours}h {mins}m")
    else:
        st.info("まだ学習記録がありません")
    
    # 過去7日間
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
    """スキル別分析"""
    
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
                
                st.metric(
                    mod['name'],
                    f"{recent_avg:.0f}",
                    f"{'+' if trend >= 0 else ''}{trend:.1f}"
                )
                st.caption(f"回数: {len(scores)}")
            else:
                st.metric(mod['name'], "-")
                st.caption("データなし")
    
    if not has_data:
        st.info("スコアデータがまだありません。各モジュールで練習するとここに反映されます。")
    
    # スコア推移（全体）
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
            st.line_chart(df.pivot_table(index='日付', columns='モジュール', values='スコア', aggfunc='mean'))


def show_weakness_analysis(data):
    """弱点分析表示"""
    
    st.markdown("#### ⚠️ 弱点分析 / Weakness Analysis")
    
    weaknesses = analyze_weaknesses(data)
    
    if not weaknesses:
        st.success("🎉 現在、目立った弱点はありません。この調子で頑張りましょう！")
        st.caption("データが増えると、より詳しい分析ができるようになります。")
        return
    
    for w in weaknesses[:5]:
        icon = {
            'module': '📊',
            'pronunciation': '🔊',
            'grammar': '📝',
            'time': '⏱️'
        }.get(w['type'], '⚠️')
        
        with st.expander(f"{icon} {w['area']}"):
            if w['type'] == 'module':
                st.markdown(f"**スコア:** {w['score']}点（全体平均より {w['gap']}点低い）")
            elif w['type'] == 'pronunciation':
                st.markdown(f"**正答率:** {w['score']}%")
            elif w['type'] == 'grammar':
                st.markdown(f"**エラー回数:** {w['score']}回")
            elif w['type'] == 'time':
                st.markdown(f"**学習時間:** {w['score']}分")
            
            st.info(f"💡 {w['suggestion']}")


def show_cefr_progress(data):
    """CEFR推移"""
    
    st.markdown("#### 📈 CEFRレベル推移")
    
    history = data.get('cefr_history', [])
    
    if not history:
        st.info("スコアデータが蓄積されると、CEFRレベルの推移が表示されます。")
        return
    
    cefr_to_num = {'A1': 1, 'A2': 2, 'B1': 3, 'B2': 4, 'C1': 5, 'C2': 6}
    
    import pandas as pd
    
    chart_data = []
    for entry in history:
        chart_data.append({
            '日付': entry['date'],
            'CEFRレベル': cefr_to_num.get(entry['level'], 0),
            '平均スコア': entry['avg_score']
        })
    
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


# ===== 教員向け分析 =====

def show_teacher_analytics():
    """教員向けクラス分析"""
    
    st.markdown("### 📊 クラス学習分析")
    
    # デモデータ
    st.markdown("#### 👥 クラス全体")
    
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
    
    # 要注意学生
    st.markdown("#### ⚠️ 要注意学生")
    
    alerts = [
        {"name": "学生A", "issue": "過去2週間ログインなし", "severity": "高"},
        {"name": "学生B", "issue": "スピーキングスコアが低下傾向", "severity": "中"},
        {"name": "学生C", "issue": "課題未提出が2件", "severity": "中"},
    ]
    
    for alert in alerts:
        if alert['severity'] == '高':
            st.error(f"🚨 **{alert['name']}** - {alert['issue']}")
        else:
            st.warning(f"⚠️ **{alert['name']}** - {alert['issue']}")
    
    st.markdown("---")
    
    # モジュール別クラス平均
    st.markdown("#### 📊 モジュール別クラス平均")
    
    import pandas as pd
    
    class_data = pd.DataFrame({
        'モジュール': ['Speaking', 'Writing', 'Reading', 'Vocabulary', 'Listening'],
        'クラス平均': [72, 68, 75, 80, 70],
        '前週比': ['+3', '-2', '+1', '+5', '+2']
    })
    
    st.dataframe(class_data, use_container_width=True, hide_index=True)
    
    st.markdown("---")
    
    # 学習時間分布
    st.markdown("#### ⏱️ 学習時間分布")
    
    time_data = pd.DataFrame({
        '学習時間帯': ['0-1h', '1-2h', '2-3h', '3-4h', '4h+'],
        '学生数': [3, 8, 10, 6, 3]
    })
    
    st.bar_chart(time_data.set_index('学習時間帯'))
