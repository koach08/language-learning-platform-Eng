-- teacher_notes: 教員が学生ごとに記録するメモ・個別目標
-- Supabase SQL Editor で実行してください

CREATE TABLE IF NOT EXISTS teacher_notes (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    teacher_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    student_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    memo TEXT DEFAULT '',
    goal TEXT DEFAULT '',
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE(teacher_id, student_id)
);

-- インデックス
CREATE INDEX IF NOT EXISTS idx_teacher_notes_teacher ON teacher_notes(teacher_id);
CREATE INDEX IF NOT EXISTS idx_teacher_notes_student ON teacher_notes(student_id);

-- RLS（必要に応じて有効化）
-- ALTER TABLE teacher_notes ENABLE ROW LEVEL SECURITY;
