#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
SPACO - SQLiteテンプレートプロバイダー

SQLiteデータベースからテンプレートを提供するプロバイダー実装です。
TemplateProviderインターフェースを実装し、データベースアクセスを抽象化します。
"""

from typing import Dict, Any, List, Optional, Tuple, Union
import logging
import json
import sqlite3
from pathlib import Path

from .template_provider import TemplateProvider
from ..db.connection import DatabaseManager
from ..utils.i18n import translate as t
from ..utils.exceptions import DatabaseError, TemplateError

logger = logging.getLogger(__name__)


class SqliteTemplateProvider(TemplateProvider):
    """
    SQLiteデータベースからテンプレートを提供するクラス
    
    TemplateProviderインターフェースを実装し、SQLiteデータベースから
    テンプレートを取得・保存します。ユーザー定義のカスタムテンプレートの
    永続化に使用されます。
    """
    
    def __init__(self, db_path: Optional[str] = None):
        """
        SQLiteテンプレートプロバイダーを初期化します
        
        引数:
            db_path: データベースファイルのパス（Noneの場合はデフォルトパス）
        """
        self.db_manager = DatabaseManager(db_path)
        logger.info("SQLiteテンプレートプロバイダーを初期化しました")
    
    def get_template(self, intent: str) -> Optional[str]:
        """
        指定された意図に対するテンプレートを取得します
        
        Args:
            intent: テンプレートの意図識別子
            
        Returns:
            テンプレート文字列（見つからない場合はNone）
            
        Raises:
            TemplateError: テンプレート取得中にエラーが発生した場合
        """
        if not intent:
            logger.warning(t("template_invalid_intent"))
            return None
            
        try:
            # SQLインジェクションを防止するためにパラメータ化されたクエリを使用
            query = "SELECT template_content FROM templates WHERE intent = ?"
            cursor = self.db_manager.execute(query, (intent,))
            
            row = cursor.fetchone()
            return row["template_content"] if row else None
            
        except DatabaseError as e:
            error_msg = t("template_fetch_error", intent=intent, error=str(e))
            logger.error(error_msg)
            raise TemplateError(error_msg, template_id=intent, details=e.details)
            
        except Exception as e:
            error_msg = t("template_fetch_error", intent=intent, error=str(e))
            logger.error(error_msg)
            raise TemplateError(error_msg, template_id=intent)
    
    def get_template_description(self, intent: str) -> Optional[str]:
        """
        指定された意図に対するテンプレートの説明を取得します
        
        引数:
            intent: テンプレートの意図識別子
            
        戻り値:
            テンプレートの説明（見つからない場合はNone）
        """
        query = "SELECT description FROM templates WHERE intent = ?"
        cursor = self.db_manager.execute(query, (intent,))
        
        if cursor is None:
            return None
        
        row = cursor.fetchone()
        return row["description"] if row else None
    
    def get_all_intents(self) -> List[str]:
        """
        利用可能なすべての意図識別子のリストを取得します
        
        戻り値:
            意図識別子のリスト
        """
        query = "SELECT intent FROM templates"
        cursor = self.db_manager.execute(query)
        
        if cursor is None:
            return []
        
        return [row["intent"] for row in cursor.fetchall()]
    
    def search_templates(self, query: str, limit: int = 10) -> List[Dict[str, Any]]:
        """
        クエリに基づいてテンプレートを検索します
        
        Args:
            query: 検索クエリ
            limit: 返す結果の最大数
            
        Returns:
            検索結果のリスト（各エントリは辞書形式）
            
        Raises:
            TemplateError: 検索中にエラーが発生した場合
        """
        try:
            # クエリが空の場合は空のリストを返す
            if not query or not query.strip():
                return []

            # LIKE演算子で使用する検索ワイルドカード文字をエスケープ
            escaped_query = self.db_manager.escape_like_string(query)
            search_term = f"%{escaped_query}%"
            
            # 検索結果をスコア付けするSQL
            sql = """
            SELECT t.id, t.intent, t.description, t.category, t.is_system,
                   (CASE 
                       WHEN t.intent LIKE ? THEN 3
                       WHEN t.description LIKE ? THEN 2
                       WHEN t.category LIKE ? THEN 1
                       ELSE 0
                   END) AS score
            FROM templates t
            WHERE t.intent LIKE ? OR t.description LIKE ? OR t.category LIKE ?
            UNION
            SELECT t.id, t.intent, t.description, t.category, t.is_system, 1 AS score
            FROM templates t
            JOIN template_tags tt ON t.id = tt.template_id
            WHERE tt.tag LIKE ?
            ORDER BY score DESC
            LIMIT ?
            """
            
            params = (search_term, search_term, search_term, search_term, search_term, search_term, search_term, limit)
            cursor = self.db_manager.execute(sql, params)
            
            results = []
            for row in cursor.fetchall():
                try:
                    # タグを取得
                    tags_cursor = self.db_manager.execute(
                        "SELECT tag FROM template_tags WHERE template_id = ?",
                        (row["id"],)
                    )
                    
                    tags = [tag_row["tag"] for tag_row in tags_cursor.fetchall()]
                    
                    # 結果を構築
                    result = {
                        "intent": row["intent"],
                        "description": row["description"],
                        "category": row["category"],
                        "is_system": bool(row["is_system"]),
                        "tags": tags,
                        "score": row["score"]
                    }
                    results.append(result)
                except Exception as e:
                    logger.warning(f"検索結果の処理中にエラー: {str(e)}")
                    continue
            
            return results
            
        except DatabaseError as e:
            error_msg = t("template_search_error", query=query, error=str(e))
            logger.error(error_msg)
            raise TemplateError(error_msg, details=e.details)
            
        except Exception as e:
            error_msg = t("template_search_error", query=query, error=str(e))
            logger.error(error_msg)
            raise TemplateError(error_msg)
    
    def get_templates_by_category(self, category: str) -> List[Dict[str, Any]]:
        """
        指定されたカテゴリに属するテンプレートを取得します
        
        引数:
            category: テンプレートカテゴリ
            
        戻り値:
            テンプレートのリスト
        """
        query = """
        SELECT id, intent, description, category, template_content, is_system
        FROM templates
        WHERE category = ?
        """
        
        cursor = self.db_manager.execute(query, (category,))
        
        if cursor is None:
            return []
        
        results = []
        for row in cursor.fetchall():
            # タグを取得
            tags_cursor = self.db_manager.execute(
                "SELECT tag FROM template_tags WHERE template_id = ?",
                (row["id"],)
            )
            
            tags = [tag_row["tag"] for tag_row in tags_cursor.fetchall()] if tags_cursor else []
            
            # 結果を構築
            result = {
                "intent": row["intent"],
                "description": row["description"],
                "category": row["category"],
                "is_system": bool(row["is_system"]),
                "tags": tags
            }
            results.append(result)
        
        return results
    
    def get_templates_by_tag(self, tag: str) -> List[Dict[str, Any]]:
        """
        指定されたタグを持つテンプレートを取得します
        
        引数:
            tag: テンプレートタグ
            
        戻り値:
            テンプレートのリスト
        """
        query = """
        SELECT t.id, t.intent, t.description, t.category, t.template_content, t.is_system
        FROM templates t
        JOIN template_tags tt ON t.id = tt.template_id
        WHERE tt.tag = ?
        """
        
        cursor = self.db_manager.execute(query, (tag,))
        
        if cursor is None:
            return []
        
        results = []
        for row in cursor.fetchall():
            # タグを取得
            tags_cursor = self.db_manager.execute(
                "SELECT tag FROM template_tags WHERE template_id = ?",
                (row["id"],)
            )
            
            tags = [tag_row["tag"] for tag_row in tags_cursor.fetchall()] if tags_cursor else []
            
            # 結果を構築
            result = {
                "intent": row["intent"],
                "description": row["description"],
                "category": row["category"],
                "is_system": bool(row["is_system"]),
                "tags": tags
            }
            results.append(result)
        
        return results
    
    def add_template(self, intent: str, template: str, description: str, 
                     category: Optional[str] = None, tags: Optional[List[str]] = None) -> bool:
        """
        新しいテンプレートを追加します
        
        引数:
            intent: テンプレートの意図識別子
            template: テンプレート文字列
            description: テンプレートの説明
            category: テンプレートのカテゴリ（オプション）
            tags: テンプレートのタグリスト（オプション）
            
        戻り値:
            追加に成功した場合はTrue、それ以外はFalse
        """
        # 既存のテンプレートをチェック
        check_query = "SELECT id FROM templates WHERE intent = ?"
        check_cursor = self.db_manager.execute(check_query, (intent,))
        
        if check_cursor and check_cursor.fetchone():
            logger.warning(f"テンプレートはすでに存在します: {intent}")
            return False
        
        # テンプレートを追加
        insert_query = """
        INSERT INTO templates (intent, template_content, description, category, is_system)
        VALUES (?, ?, ?, ?, 0)
        """
        
        cursor = self.db_manager.execute(insert_query, (
            intent, template, description, category or "user_defined"
        ))
        
        if cursor is None:
            logger.error(f"テンプレート追加に失敗しました: {intent}")
            return False
        
        # 最後に挿入されたIDを取得
        template_id = cursor.lastrowid
        
        # タグを追加（存在する場合）
        if tags and template_id:
            tag_values = [(template_id, tag) for tag in tags]
            tag_query = "INSERT INTO template_tags (template_id, tag) VALUES (?, ?)"
            
            tag_cursor = self.db_manager.executemany(tag_query, tag_values)
            
            if tag_cursor is None:
                logger.warning(f"テンプレートは追加されましたが、タグの追加に失敗しました: {intent}")
                # テンプレート自体は追加されたのでコミット
                self.db_manager.commit()
                return True
        
        # 変更をコミット
        if not self.db_manager.commit():
            logger.error(f"テンプレート追加のコミットに失敗しました: {intent}")
            return False
        
        logger.info(f"テンプレートをデータベースに追加しました: {intent}")
        return True
    
    def update_template(self, intent: str, template: Optional[str] = None, 
                        description: Optional[str] = None) -> bool:
        """
        既存のテンプレートを更新します
        
        引数:
            intent: 更新するテンプレートの意図識別子
            template: 新しいテンプレート文字列（Noneの場合は更新しない）
            description: 新しい説明（Noneの場合は更新しない）
            
        戻り値:
            更新に成功した場合はTrue、それ以外はFalse
        """
        # テンプレートの存在を確認
        check_query = "SELECT id FROM templates WHERE intent = ?"
        check_cursor = self.db_manager.execute(check_query, (intent,))
        
        if not check_cursor or not check_cursor.fetchone():
            logger.warning(f"更新するテンプレートが見つかりません: {intent}")
            return False
        
        # 更新するフィールドを構築
        update_fields = []
        params = []
        
        if template is not None:
            update_fields.append("template_content = ?")
            params.append(template)
        
        if description is not None:
            update_fields.append("description = ?")
            params.append(description)
        
        # 更新するフィールドがない場合
        if not update_fields:
            logger.warning(f"更新するフィールドが指定されていません: {intent}")
            return False
        
        # 更新タイムスタンプを追加
        update_fields.append("updated_at = CURRENT_TIMESTAMP")
        
        # 更新クエリを構築
        update_query = f"""
        UPDATE templates
        SET {', '.join(update_fields)}
        WHERE intent = ?
        """
        
        params.append(intent)
        
        # クエリを実行
        cursor = self.db_manager.execute(update_query, tuple(params))
        
        if cursor is None:
            logger.error(f"テンプレート更新に失敗しました: {intent}")
            return False
        
        # 変更をコミット
        if not self.db_manager.commit():
            logger.error(f"テンプレート更新のコミットに失敗しました: {intent}")
            return False
        
        logger.info(f"テンプレートを更新しました: {intent}")
        return True
    
    def delete_template(self, intent: str) -> bool:
        """
        テンプレートを削除します
        
        引数:
            intent: 削除するテンプレートの意図識別子
            
        戻り値:
            削除に成功した場合はTrue、それ以外はFalse
        """
        # テンプレートの存在を確認
        check_query = "SELECT id FROM templates WHERE intent = ?"
        check_cursor = self.db_manager.execute(check_query, (intent,))
        
        if not check_cursor:
            logger.error(f"データベースクエリエラー: {intent}")
            return False
        
        row = check_cursor.fetchone()
        if not row:
            logger.warning(f"削除するテンプレートが見つかりません: {intent}")
            return False
        
        # 外部キー制約により、テンプレートを削除するとタグも自動的に削除される
        delete_query = "DELETE FROM templates WHERE intent = ?"
        
        cursor = self.db_manager.execute(delete_query, (intent,))
        
        if cursor is None:
            logger.error(f"テンプレート削除に失敗しました: {intent}")
            return False
        
        # 変更をコミット
        if not self.db_manager.commit():
            logger.error(f"テンプレート削除のコミットに失敗しました: {intent}")
            return False
        
        logger.info(f"テンプレートを削除しました: {intent}")
        return True
