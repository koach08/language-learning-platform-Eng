-- ============================================================
-- English Learning Platform - Database Setup
-- Supabase SQL Editor でこのファイルを丸ごとコピペして Run
-- ============================================================

-- ============================================================
-- 1. USERS テーブル（学生・教員）
-- ============================================================
CREATE TABLE users (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    email TEXT UNIQUE NOT NULL,
    name TEXT,
    student_id TEXT,                    -- 学籍番号（学生のみ）
    role TEXT NOT NULL DEFAULT 'student' CHECK (role IN ('student', 'teacher', 'admin')),
    profile_image_url TEXT,
    created_at TIMESTAMPTZ DEFAULT now(),
    updated_at TIMESTAMPTZ DEFAULT now()
);

-- メールアドレスで高速検索
CREATE INDEX idx_users_email ON users(email);
CREATE INDEX idx_users_role ON users(role);

-- ============================================================
-- 2. COURSES テーブル（コース・科目）
-- ============================================================
CREATE TABLE courses (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    teacher_id UUID REFERENCES users(id) ON DELETE CASCADE,
    name TEXT NOT NULL,                 -- 科目名
    description TEXT,
    year INTEGER NOT NULL,              -- 年度（例: 2026）
    semester TEXT NOT NULL CHECK (semester IN ('spring', 'fall', 'full_year')),
    
    -- テンプレートタイプ
    template_type TEXT NOT NULL DEFAULT 'custom' CHECK (template_type IN (
        'output_focused',       -- アウトプット重視（発信）
        'input_focused',        -- インプット重視（受信）
        'four_skills',          -- 基礎能力全般（4技能+やり取り）
        'toefl_itp',            -- TOEFL-ITP + 独学スキル
        'pbl_specialized',      -- PBL・専門科目英語
        'toefl_ibt',            -- TOEFL iBT対策
        'toeic',                -- TOEIC対策
        'custom'                -- カスタム
    )),
    
    -- モジュールON/OFF設定
    active_modules JSONB DEFAULT '{
        "speaking_submit": true,
        "speaking_chat": true,
        "writing_submit": true,
        "writing_practice": true,
        "listening": true,
        "reading": true,
        "vocabulary": true,
        "exam_practice": false
    }'::jsonb,
    
    -- PBL専門科目用の設定
    specialized_field TEXT,             -- 専門分野（例: メディア論）
    specialized_topics JSONB,           -- トピックリスト
    
    -- その他設定
    settings JSONB DEFAULT '{}'::jsonb,
    
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMPTZ DEFAULT now(),
    updated_at TIMESTAMPTZ DEFAULT now()
);

CREATE INDEX idx_courses_teacher ON courses(teacher_id);
CREATE INDEX idx_courses_year_semester ON courses(year, semester);

-- ============================================================
-- 3. ENROLLMENTS テーブル（履修登録）
-- ============================================================
CREATE TABLE enrollments (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    student_id UUID REFERENCES users(id) ON DELETE CASCADE,
    course_id UUID REFERENCES courses(id) ON DELETE CASCADE,
    enrolled_at TIMESTAMPTZ DEFAULT now(),
    
    UNIQUE(student_id, course_id)
);

CREATE INDEX idx_enrollments_student ON enrollments(student_id);
CREATE INDEX idx_enrollments_course ON enrollments(course_id);

-- ============================================================
-- 4. ASSIGNMENTS テーブル（課題）
-- ============================================================
CREATE TABLE assignments (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    course_id UUID REFERENCES courses(id) ON DELETE CASCADE,
    
    title TEXT NOT NULL,
    description TEXT,
    instructions TEXT,                  -- 課題の指示文
    
    -- 課題タイプ
    assignment_type TEXT NOT NULL CHECK (assignment_type IN (
        'speaking_read_aloud',      -- 音読
        'speaking_speech',          -- スピーチ
        'speaking_conversation',    -- 会話（AI対話連携）
        'writing_essay',            -- エッセイ
        'writing_summary',          -- 要約
        'writing_response',         -- 意見文
        'listening_comprehension',  -- リスニング理解
        'reading_comprehension'     -- リーディング理解
    )),
    
    -- Speaking用: 目標テキスト
    target_text TEXT,
    
    -- Listening/Reading用: 教材URL
    material_url TEXT,
    material_content TEXT,              -- テキスト教材の場合
    
    -- 締切・配点
    due_date TIMESTAMPTZ,
    max_score REAL DEFAULT 100,
    
    -- 評価設定
    grading_rubric JSONB,
    
    is_published BOOLEAN DEFAULT false,
    created_at TIMESTAMPTZ DEFAULT now(),
    updated_at TIMESTAMPTZ DEFAULT now()
);

CREATE INDEX idx_assignments_course ON assignments(course_id);
CREATE INDEX idx_assignments_due ON assignments(due_date);

-- ============================================================
-- 5. SUBMISSIONS テーブル（課題提出）
-- ============================================================
CREATE TABLE submissions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    student_id UUID REFERENCES users(id) ON DELETE CASCADE,
    assignment_id UUID REFERENCES assignments(id) ON DELETE CASCADE,
    
    -- 提出内容
    content_type TEXT NOT NULL CHECK (content_type IN ('audio', 'video', 'text', 'gdrive_link')),
    audio_url TEXT,                     -- Supabase Storage URL
    video_url TEXT,
    text_content TEXT,
    gdrive_url TEXT,
    
    -- 評価結果
    scores JSONB,                       -- {"azure": {...}, "speechace": {...}, "combined": {...}}
    feedback TEXT,                      -- AI生成フィードバック
    feedback_detailed JSONB,            -- 詳細フィードバック
    
    -- スコア（換算済み）
    total_score REAL,
    cefr_level TEXT,
    
    -- 教員コメント
    teacher_comment TEXT,
    teacher_score REAL,                 -- 教員による手動スコア調整
    
    -- メタ情報
    is_practice BOOLEAN DEFAULT false,  -- 練習モードかどうか
    submitted_at TIMESTAMPTZ DEFAULT now(),
    evaluated_at TIMESTAMPTZ,
    
    -- API使用量追跡
    api_cost REAL DEFAULT 0
);

CREATE INDEX idx_submissions_student ON submissions(student_id);
CREATE INDEX idx_submissions_assignment ON submissions(assignment_id);
CREATE INDEX idx_submissions_submitted ON submissions(submitted_at);

-- ============================================================
-- 6. CHAT_SESSIONS テーブル（AI対話セッション）
-- ============================================================
CREATE TABLE chat_sessions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    student_id UUID REFERENCES users(id) ON DELETE CASCADE,
    course_id UUID REFERENCES courses(id) ON DELETE SET NULL,
    
    -- セッション情報
    topic TEXT,                         -- 対話トピック
    topic_category TEXT,                -- カテゴリ（self_intro, daily_life, academic, etc.）
    input_mode TEXT DEFAULT 'text' CHECK (input_mode IN ('text', 'voice', 'mixed')),
    
    -- 対話内容（全文保存）
    messages JSONB NOT NULL DEFAULT '[]'::jsonb,
    -- 形式: [{"role": "assistant", "content": "...", "timestamp": "..."}, 
    --        {"role": "user", "content": "...", "input_mode": "voice", "timestamp": "..."}]
    
    -- セッション統計
    turn_count INTEGER DEFAULT 0,
    duration_seconds INTEGER,
    
    -- AI分析結果（セッション終了時に生成）
    vocabulary_level TEXT,              -- 推定語彙レベル (A1-C1)
    error_summary JSONB,                -- {"article_omission": 3, "verb_agreement": 2}
    strengths TEXT,
    improvements TEXT,
    
    -- 時間
    started_at TIMESTAMPTZ DEFAULT now(),
    ended_at TIMESTAMPTZ,
    
    -- コスト追跡
    api_cost REAL DEFAULT 0
);

CREATE INDEX idx_chat_sessions_student ON chat_sessions(student_id);
CREATE INDEX idx_chat_sessions_course ON chat_sessions(course_id);
CREATE INDEX idx_chat_sessions_started ON chat_sessions(started_at);

-- ============================================================
-- 7. LISTENING_LOGS テーブル（リスニング学習ログ）
-- ============================================================
CREATE TABLE listening_logs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    student_id UUID REFERENCES users(id) ON DELETE CASCADE,
    course_id UUID REFERENCES courses(id) ON DELETE SET NULL,
    assignment_id UUID REFERENCES assignments(id) ON DELETE SET NULL,
    
    -- 教材情報
    video_url TEXT,
    video_title TEXT,
    video_duration_seconds INTEGER,
    estimated_level TEXT,               -- CEFRレベル推定
    
    -- 学習タイプ
    activity_type TEXT NOT NULL CHECK (activity_type IN ('assigned', 'extensive', 'practice')),
    
    -- 3段階学習活動の記録
    pre_listening JSONB,                -- {predictions: "...", keywords_checked: [...]}
    while_listening JSONB,              -- {view_count: 3, notes: "..."}
    post_listening JSONB,               -- {summary: "...", reflection: "..."}
    
    -- クイズ結果
    quiz_results JSONB,                 -- [{question, user_answer, correct_answer, is_correct}]
    quiz_score REAL,
    
    -- 学習時間
    time_spent_seconds INTEGER,
    completed_at TIMESTAMPTZ DEFAULT now(),
    
    api_cost REAL DEFAULT 0
);

CREATE INDEX idx_listening_logs_student ON listening_logs(student_id);
CREATE INDEX idx_listening_logs_course ON listening_logs(course_id);

-- ============================================================
-- 8. READING_LOGS テーブル（リーディング学習ログ）
-- ============================================================
CREATE TABLE reading_logs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    student_id UUID REFERENCES users(id) ON DELETE CASCADE,
    course_id UUID REFERENCES courses(id) ON DELETE SET NULL,
    assignment_id UUID REFERENCES assignments(id) ON DELETE SET NULL,
    
    -- 教材情報
    source_url TEXT,
    source_title TEXT,
    word_count INTEGER,
    estimated_level TEXT,
    
    -- 学習タイプ
    activity_type TEXT NOT NULL CHECK (activity_type IN ('assigned', 'extensive', 'intensive')),
    
    -- 3段階学習活動の記録
    pre_reading JSONB,
    while_reading JSONB,
    post_reading JSONB,
    
    -- クイズ結果
    quiz_results JSONB,
    quiz_score REAL,
    
    -- 感想・メモ（多読用）
    personal_notes TEXT,
    rating INTEGER CHECK (rating >= 1 AND rating <= 5),
    
    time_spent_seconds INTEGER,
    completed_at TIMESTAMPTZ DEFAULT now(),
    
    api_cost REAL DEFAULT 0
);

CREATE INDEX idx_reading_logs_student ON reading_logs(student_id);
CREATE INDEX idx_reading_logs_course ON reading_logs(course_id);

-- ============================================================
-- 9. VOCABULARY テーブル（語彙帳）
-- ============================================================
CREATE TABLE vocabulary (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    student_id UUID REFERENCES users(id) ON DELETE CASCADE,
    
    -- 語彙情報
    word TEXT NOT NULL,
    meaning TEXT,                       -- 日本語訳
    pronunciation TEXT,                 -- 発音記号
    part_of_speech TEXT,                -- 品詞
    example_sentence TEXT,
    example_translation TEXT,           -- 例文の日本語訳
    context TEXT,                       -- 出会った文脈
    notes TEXT,                         -- 学生のメモ
    
    -- 出典
    source_type TEXT CHECK (source_type IN ('listening', 'reading', 'chat', 'writing', 'manual', 'exam')),
    source_id UUID,                     -- 元のログID
    
    -- SM-2 間隔反復パラメータ
    ease_factor REAL DEFAULT 2.5,
    interval_days INTEGER DEFAULT 1,
    repetitions INTEGER DEFAULT 0,
    next_review TIMESTAMPTZ DEFAULT now(),
    last_reviewed TIMESTAMPTZ,
    
    -- 習得状態
    mastery_level INTEGER DEFAULT 0 CHECK (mastery_level >= 0 AND mastery_level <= 5),
    
    added_at TIMESTAMPTZ DEFAULT now(),
    
    -- 同じ学生の同じ単語は1つだけ
    UNIQUE(student_id, word)
);

CREATE INDEX idx_vocabulary_student ON vocabulary(student_id);
CREATE INDEX idx_vocabulary_next_review ON vocabulary(next_review);
CREATE INDEX idx_vocabulary_source ON vocabulary(source_type);

-- ============================================================
-- 10. VOCABULARY_REVIEWS テーブル（語彙復習ログ）
-- ============================================================
CREATE TABLE vocabulary_reviews (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    vocabulary_id UUID REFERENCES vocabulary(id) ON DELETE CASCADE,
    student_id UUID REFERENCES users(id) ON DELETE CASCADE,
    
    -- SM-2評価 (0-5)
    quality INTEGER NOT NULL CHECK (quality >= 0 AND quality <= 5),
    -- 0: 完全に忘れた
    -- 1: 間違えた、見たら思い出した
    -- 2: 間違えた、すぐ思い出した
    -- 3: 正解、かなり考えた
    -- 4: 正解、少し考えた
    -- 5: 正解、即答
    
    -- 復習形式
    review_type TEXT CHECK (review_type IN ('en_to_ja', 'ja_to_en', 'fill_blank', 'collocation', 'sentence')),
    
    reviewed_at TIMESTAMPTZ DEFAULT now()
);

CREATE INDEX idx_vocab_reviews_vocabulary ON vocabulary_reviews(vocabulary_id);
CREATE INDEX idx_vocab_reviews_student ON vocabulary_reviews(student_id);

-- ============================================================
-- 11. PRACTICE_LOGS テーブル（練習記録 - 全モジュール共通）
-- ============================================================
CREATE TABLE practice_logs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    student_id UUID REFERENCES users(id) ON DELETE CASCADE,
    course_id UUID REFERENCES courses(id) ON DELETE SET NULL,
    
    -- 練習タイプ
    module_type TEXT NOT NULL CHECK (module_type IN (
        'speaking_pronunciation',
        'speaking_chat',
        'writing_practice',
        'listening_practice',
        'reading_practice',
        'vocabulary_review',
        'exam_practice'
    )),
    
    -- 練習内容
    activity_details JSONB,
    
    -- 結果
    score REAL,
    duration_seconds INTEGER,
    
    practiced_at TIMESTAMPTZ DEFAULT now(),
    api_cost REAL DEFAULT 0
);

CREATE INDEX idx_practice_logs_student ON practice_logs(student_id);
CREATE INDEX idx_practice_logs_module ON practice_logs(module_type);

-- ============================================================
-- 12. EXAM_PRACTICE_LOGS テーブル（検定練習ログ）
-- ============================================================
CREATE TABLE exam_practice_logs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    student_id UUID REFERENCES users(id) ON DELETE CASCADE,
    
    -- 検定情報
    exam_type TEXT NOT NULL CHECK (exam_type IN ('toefl_itp', 'toefl_ibt', 'toeic', 'eiken', 'ielts')),
    section TEXT NOT NULL,              -- 例: 'structure', 'reading', 'listening', 'writing', 'speaking'
    level TEXT,                         -- 英検の級など
    
    -- 問題と回答
    questions JSONB,                    -- 生成された問題
    answers JSONB,                      -- 学生の回答
    
    -- 結果
    score REAL,
    total_questions INTEGER,
    correct_count INTEGER,
    
    -- 詳細フィードバック
    feedback JSONB,
    
    -- 予測スコア
    predicted_score JSONB,              -- {"toefl_itp": 520, "cefr": "B1", ...}
    
    practiced_at TIMESTAMPTZ DEFAULT now(),
    duration_seconds INTEGER,
    api_cost REAL DEFAULT 0
);

CREATE INDEX idx_exam_practice_student ON exam_practice_logs(student_id);
CREATE INDEX idx_exam_practice_type ON exam_practice_logs(exam_type);

-- ============================================================
-- 13. GRADING_CONFIG テーブル（評価設定）
-- ============================================================
CREATE TABLE grading_config (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    course_id UUID REFERENCES courses(id) ON DELETE CASCADE,
    
    -- Speaking評価比率
    speaking_weights JSONB DEFAULT '{
        "pronunciation": 0.3,
        "fluency": 0.25,
        "accuracy": 0.25,
        "content": 0.2
    }'::jsonb,
    
    -- Writing評価比率
    writing_weights JSONB DEFAULT '{
        "grammar": 0.3,
        "vocabulary": 0.2,
        "organization": 0.2,
        "expression": 0.2,
        "content": 0.1
    }'::jsonb,
    
    -- CEFRバンド閾値
    cefr_thresholds JSONB DEFAULT '{
        "C2": 95,
        "C1": 85,
        "B2": 70,
        "B1": 55,
        "A2": 40,
        "A1": 0
    }'::jsonb,
    
    -- その他設定
    settings JSONB DEFAULT '{}'::jsonb,
    
    created_at TIMESTAMPTZ DEFAULT now(),
    updated_at TIMESTAMPTZ DEFAULT now(),
    
    UNIQUE(course_id)
);

-- ============================================================
-- 14. API_USAGE テーブル（API使用量追跡）
-- ============================================================
CREATE TABLE api_usage (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    
    -- 使用者
    user_id UUID REFERENCES users(id) ON DELETE SET NULL,
    course_id UUID REFERENCES courses(id) ON DELETE SET NULL,
    
    -- API情報
    api_name TEXT NOT NULL CHECK (api_name IN (
        'azure_speech',
        'speechace',
        'openai_gpt4o',
        'openai_gpt4o_mini',
        'edge_tts'
    )),
    
    -- 使用量
    tokens_input INTEGER,
    tokens_output INTEGER,
    audio_seconds REAL,
    
    -- コスト（円）
    cost_jpy REAL,
    
    -- 関連ID
    related_type TEXT,                  -- 'submission', 'chat_session', etc.
    related_id UUID,
    
    used_at TIMESTAMPTZ DEFAULT now()
);

CREATE INDEX idx_api_usage_user ON api_usage(user_id);
CREATE INDEX idx_api_usage_date ON api_usage(used_at);
CREATE INDEX idx_api_usage_api ON api_usage(api_name);

-- ============================================================
-- 15. Row Level Security (RLS) 設定
-- ============================================================

-- RLSを有効化
ALTER TABLE users ENABLE ROW LEVEL SECURITY;
ALTER TABLE courses ENABLE ROW LEVEL SECURITY;
ALTER TABLE enrollments ENABLE ROW LEVEL SECURITY;
ALTER TABLE assignments ENABLE ROW LEVEL SECURITY;
ALTER TABLE submissions ENABLE ROW LEVEL SECURITY;
ALTER TABLE chat_sessions ENABLE ROW LEVEL SECURITY;
ALTER TABLE listening_logs ENABLE ROW LEVEL SECURITY;
ALTER TABLE reading_logs ENABLE ROW LEVEL SECURITY;
ALTER TABLE vocabulary ENABLE ROW LEVEL SECURITY;
ALTER TABLE vocabulary_reviews ENABLE ROW LEVEL SECURITY;
ALTER TABLE practice_logs ENABLE ROW LEVEL SECURITY;
ALTER TABLE exam_practice_logs ENABLE ROW LEVEL SECURITY;
ALTER TABLE grading_config ENABLE ROW LEVEL SECURITY;
ALTER TABLE api_usage ENABLE ROW LEVEL SECURITY;

-- ============================================================
-- 16. RLS Policies
-- ============================================================

-- Users: 自分のデータのみ読み書き可、教員は全員閲覧可
CREATE POLICY "Users can view own data" ON users
    FOR SELECT USING (auth.uid()::text = id::text);

CREATE POLICY "Users can update own data" ON users
    FOR UPDATE USING (auth.uid()::text = id::text);

-- 新規ユーザー登録を許可（認証後の初回アクセス時）
CREATE POLICY "Enable insert for authenticated users" ON users
    FOR INSERT WITH CHECK (auth.uid() IS NOT NULL);

-- Courses: 教員は自分のコース、学生は履修コースを閲覧
CREATE POLICY "Teachers can manage own courses" ON courses
    FOR ALL USING (auth.uid()::text = teacher_id::text);

CREATE POLICY "Students can view enrolled courses" ON courses
    FOR SELECT USING (
        EXISTS (
            SELECT 1 FROM enrollments e
            WHERE e.course_id = courses.id
            AND e.student_id::text = auth.uid()::text
        )
    );

-- Enrollments: 学生は自分の履修、教員は自分のコースの履修を管理
CREATE POLICY "Students view own enrollments" ON enrollments
    FOR SELECT USING (auth.uid()::text = student_id::text);

CREATE POLICY "Teachers manage course enrollments" ON enrollments
    FOR ALL USING (
        EXISTS (
            SELECT 1 FROM courses c
            WHERE c.id = enrollments.course_id
            AND c.teacher_id::text = auth.uid()::text
        )
    );

-- Assignments: 教員は自分のコースの課題を管理、学生は履修コースの課題を閲覧
CREATE POLICY "Teachers manage assignments" ON assignments
    FOR ALL USING (
        EXISTS (
            SELECT 1 FROM courses c
            WHERE c.id = assignments.course_id
            AND c.teacher_id::text = auth.uid()::text
        )
    );

CREATE POLICY "Students view course assignments" ON assignments
    FOR SELECT USING (
        EXISTS (
            SELECT 1 FROM enrollments e
            JOIN courses c ON c.id = e.course_id
            WHERE e.student_id::text = auth.uid()::text
            AND c.id = assignments.course_id
        )
    );

-- Submissions: 学生は自分の提出、教員はコースの全提出を閲覧
CREATE POLICY "Students manage own submissions" ON submissions
    FOR ALL USING (auth.uid()::text = student_id::text);

CREATE POLICY "Teachers view course submissions" ON submissions
    FOR SELECT USING (
        EXISTS (
            SELECT 1 FROM assignments a
            JOIN courses c ON c.id = a.course_id
            WHERE a.id = submissions.assignment_id
            AND c.teacher_id::text = auth.uid()::text
        )
    );

-- Chat Sessions: 学生は自分、教員はコースの全セッションを閲覧
CREATE POLICY "Students manage own chat sessions" ON chat_sessions
    FOR ALL USING (auth.uid()::text = student_id::text);

CREATE POLICY "Teachers view course chat sessions" ON chat_sessions
    FOR SELECT USING (
        EXISTS (
            SELECT 1 FROM courses c
            WHERE c.id = chat_sessions.course_id
            AND c.teacher_id::text = auth.uid()::text
        )
    );

-- Learning Logs: 学生は自分のみ
CREATE POLICY "Students manage own listening logs" ON listening_logs
    FOR ALL USING (auth.uid()::text = student_id::text);

CREATE POLICY "Students manage own reading logs" ON reading_logs
    FOR ALL USING (auth.uid()::text = student_id::text);

-- Vocabulary: 学生は自分のみ
CREATE POLICY "Students manage own vocabulary" ON vocabulary
    FOR ALL USING (auth.uid()::text = student_id::text);

CREATE POLICY "Students manage own vocab reviews" ON vocabulary_reviews
    FOR ALL USING (auth.uid()::text = student_id::text);

-- Practice Logs: 学生は自分のみ
CREATE POLICY "Students manage own practice logs" ON practice_logs
    FOR ALL USING (auth.uid()::text = student_id::text);

CREATE POLICY "Students manage own exam practice" ON exam_practice_logs
    FOR ALL USING (auth.uid()::text = student_id::text);

-- Grading Config: 教員のみ
CREATE POLICY "Teachers manage grading config" ON grading_config
    FOR ALL USING (
        EXISTS (
            SELECT 1 FROM courses c
            WHERE c.id = grading_config.course_id
            AND c.teacher_id::text = auth.uid()::text
        )
    );

-- API Usage: 管理者のみ（通常は使用しない）
CREATE POLICY "Admin only api usage" ON api_usage
    FOR ALL USING (
        EXISTS (
            SELECT 1 FROM users u
            WHERE u.id::text = auth.uid()::text
            AND u.role = 'admin'
        )
    );

-- ============================================================
-- 完了メッセージ
-- ============================================================
-- すべてのテーブルとポリシーが作成されました！
-- 次のステップ: Google OAuth の設定
