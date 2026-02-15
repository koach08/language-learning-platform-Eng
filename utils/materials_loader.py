"""
Materials Loader
=================
教材の読み込みを一元管理。
DB（learning_materials テーブル）があればDBを優先、なければデモ教材にフォールバック。

使い方:
    from utils.materials_loader import load_materials
    materials = load_materials('listening')  # -> dict {key: material_data}
    materials = load_materials('reading', course_id='xxx')
"""

from typing import Dict, Optional


def load_materials(module_type: str, course_id: str = None) -> Dict:
    """
    教材を読み込む。DB優先、フォールバックでデモ教材。

    Returns:
        dict: {material_key: material_data} 形式
        material_data はデモ教材と同じ構造（title, level, category + コンテンツ）
    """
    # 1. DBから取得を試みる
    db_materials = _load_from_db(module_type, course_id)
    if db_materials:
        return db_materials

    # 2. フォールバック: デモ教材
    return _load_demo(module_type)


def _load_from_db(module_type: str, course_id: str = None) -> Dict:
    """DBから教材を読み込み、デモ教材と同じ形式に変換"""
    try:
        from utils.database import get_learning_materials
        rows = get_learning_materials(module_type, course_id=course_id)
        if not rows:
            return {}

        materials = {}
        for row in rows:
            key = row.get('material_key', row.get('id', ''))
            content = row.get('content', {}) or {}

            # デモ教材と同じ構造にマージ
            data = {
                'title': row.get('title', key),
                'level': row.get('level', 'B1'),
                'category': row.get('category', ''),
                'description': row.get('description', ''),
                '_db_id': row.get('id'),  # DB管理用
                **content,
            }
            materials[key] = data

        return materials
    except Exception:
        return {}


def _load_demo(module_type: str) -> Dict:
    """デモ教材を読み込み"""
    try:
        if module_type == 'listening':
            from utils.listening import DEMO_LISTENING
            return DEMO_LISTENING
        elif module_type == 'reading':
            from utils.reading import DEMO_ARTICLES
            return DEMO_ARTICLES
        elif module_type == 'vocabulary':
            from utils.vocabulary import DEMO_WORD_LISTS
            return DEMO_WORD_LISTS
        else:
            return {}
    except Exception:
        return {}
