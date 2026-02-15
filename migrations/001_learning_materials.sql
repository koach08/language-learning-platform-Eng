-- learning_materials: 教材データベース
-- Supabase SQL Editor で実行してください

CREATE TABLE IF NOT EXISTS learning_materials (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    
    -- 教材の種類: listening, reading, vocabulary, speaking
    module_type TEXT NOT NULL,
    
    -- 教材識別キー（デモ教材との互換用: intro_conversation, climate, academic 等）
    material_key TEXT NOT NULL,
    
    -- 基本情報
    title TEXT NOT NULL,
    level TEXT DEFAULT 'B1',           -- CEFR: A1, A2, B1, B2, C1, C2
    category TEXT DEFAULT '',          -- Daily Conversation, News, Environment 等
    description TEXT DEFAULT '',
    
    -- 教材本体（JSONB で柔軟に格納）
    -- listening: {speakers, script, duration, questions}
    -- reading: {text, word_count, questions}
    -- vocabulary: {words: [{word, meaning, example, pos}]}
    -- speaking: {text, instructions}
    content JSONB NOT NULL DEFAULT '{}',
    
    -- 管理
    course_id UUID REFERENCES courses(id) ON DELETE SET NULL,  -- NULL = 共通教材
    created_by UUID REFERENCES users(id) ON DELETE SET NULL,
    is_active BOOLEAN DEFAULT TRUE,
    sort_order INT DEFAULT 0,
    
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    
    UNIQUE(module_type, material_key)
);

-- インデックス
CREATE INDEX IF NOT EXISTS idx_materials_module ON learning_materials(module_type);
CREATE INDEX IF NOT EXISTS idx_materials_course ON learning_materials(course_id);
CREATE INDEX IF NOT EXISTS idx_materials_active ON learning_materials(is_active);
