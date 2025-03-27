#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
SPACO - プロジェクトプロバイダー

ユーザーの音響合成プロジェクトを管理するプロバイダー実装です。
プロジェクトの保存、取得、検索機能を提供します。
"""

from typing import Dict, Any, List, Optional, Tuple, Union
import logging
import json
import sqlite3
from datetime import datetime
from pathlib import Path

from ..db.connection import DatabaseManager
from ..models.project import ProjectModel
from ..utils.i18n import translate as t
from ..utils.exceptions import DatabaseError, ProjectError

logger = logging.getLogger(__name__)


class ProjectProvider:
    """
    ユーザープロジェクトを管理するクラス
    
    SQLiteデータベースにプロジェクトを保存し、取得、検索する機能を提供します。
    """
    
    def __init__(self, db_path: Optional[str] = None):
        """
        プロジェクトプロバイダーを初期化します
        
        引数:
            db_path: データベースファイルのパス（Noneの場合はデフォルトパス）
        """
        self.db_manager = DatabaseManager(db_path)
        logger.info("プロジェクトプロバイダーを初期化しました")
    
    def get_project(self, project_id: Union[str, int]) -> Optional[ProjectModel]:
        """
        指定されたIDのプロジェクトを取得します
        
        引数:
            project_id: プロジェクトID
            
        戻り値:
            ProjectModelインスタンス（見つからない場合はNone）
        """
        query = """
        SELECT id, name, description, code, template_id, variables, tags, created_at, updated_at
        FROM projects
        WHERE id = ?
        """
        
        cursor = self.db_manager.execute(query, (str(project_id),))
        
        if cursor is None:
            return None
        
        row = cursor.fetchone()
        if not row:
            return None
        
        # JSON文字列をデシリアライズ
        variables = json.loads(row["variables"]) if row["variables"] else {}
        tags = json.loads(row["tags"]) if row["tags"] else []
        
        return ProjectModel(
            name=row["name"],
            description=row["description"],
            code=row["code"],
            template_id=row["template_id"],
            variables=variables,
            tags=tags,
            created_at=row["created_at"],
            updated_at=row["updated_at"],
            project_id=row["id"]
        )
    
    def get_all_projects(self, limit: int = 100, offset: int = 0) -> List[ProjectModel]:
        """
        すべてのプロジェクトを取得します
        
        引数:
            limit: 返す結果の最大数
            offset: 結果のオフセット
            
        戻り値:
            ProjectModelインスタンスのリスト
        """
        query = """
        SELECT id, name, description, code, template_id, variables, tags, created_at, updated_at
        FROM projects
        ORDER BY updated_at DESC
        LIMIT ? OFFSET ?
        """
        
        cursor = self.db_manager.execute(query, (limit, offset))
        
        if cursor is None:
            return []
        
        projects = []
        for row in cursor.fetchall():
            # JSON文字列をデシリアライズ
            variables = json.loads(row["variables"]) if row["variables"] else {}
            tags = json.loads(row["tags"]) if row["tags"] else []
            
            project = ProjectModel(
                name=row["name"],
                description=row["description"],
                code=row["code"],
                template_id=row["template_id"],
                variables=variables,
                tags=tags,
                created_at=row["created_at"],
                updated_at=row["updated_at"],
                project_id=row["id"]
            )
            projects.append(project)
        
        return projects
    
    def search_projects(self, query: str, limit: int = 10) -> List[ProjectModel]:
        """
        クエリに基づいてプロジェクトを検索します
        
        Args:
            query: 検索クエリ
            limit: 返す結果の最大数
            
        Returns:
            ProjectModelインスタンスのリスト
            
        Raises:
            ProjectError: 検索中にエラーが発生した場合
        """
        try:
            # クエリが空の場合は、日付順にソートして全プロジェクトを返す
            if not query or not query.strip():
                return self.get_all_projects(limit=limit)
            
            # LIKE演算子で使用する検索ワイルドカード文字をエスケープ
            escaped_query = self.db_manager.escape_like_string(query)
            search_term = f"%{escaped_query}%"
            
            # 複数フィールドで検索し、関連度によるスコア付け
            sql = """
            SELECT p.id, p.name, p.description, p.code, p.template_id, p.variables, p.tags, 
                   p.created_at, p.updated_at,
                   (CASE 
                       WHEN p.name LIKE ? THEN 3
                       WHEN p.description LIKE ? THEN 2
                       WHEN p.code LIKE ? THEN 1
                       ELSE 0
                   END) AS score
            FROM projects p
            WHERE p.name LIKE ? OR p.description LIKE ? OR p.code LIKE ?
            ORDER BY score DESC, p.updated_at DESC
            LIMIT ?
            """
            
            params = (search_term, search_term, search_term, search_term, search_term, search_term, limit)
            cursor = self.db_manager.execute(sql, params)
            
            projects = []
            for row in cursor.fetchall():
                try:
                    # JSON文字列をデシリアライズ
                    variables = json.loads(row["variables"]) if row["variables"] else {}
                    tags = json.loads(row["tags"]) if row["tags"] else []
                    
                    project = ProjectModel(
                        name=row["name"],
                        description=row["description"],
                        code=row["code"],
                        template_id=row["template_id"],
                        variables=variables,
                        tags=tags,
                        created_at=row["created_at"],
                        updated_at=row["updated_at"],
                        project_id=row["id"]
                    )
                    projects.append(project)
                except Exception as e:
                    logger.warning(f"検索結果の処理中にエラー: {str(e)}")
                    continue
            
            return projects
            
        except DatabaseError as e:
            error_msg = t("project_search_error", query=query, error=str(e))
            logger.error(error_msg)
            raise ProjectError(error_msg, details=e.details)
            
        except Exception as e:
            error_msg = t("project_search_error", query=query, error=str(e))
            logger.error(error_msg)
            raise ProjectError(error_msg)
    
    def get_projects_by_tag(self, tag: str, limit: int = 10) -> List[ProjectModel]:
        """
        指定されたタグを持つプロジェクトを取得します
        
        引数:
            tag: プロジェクトタグ
            limit: 返す結果の最大数
            
        戻り値:
            ProjectModelインスタンスのリスト
        """
        # タグはJSON配列として保存されているため、LIKEで検索
        search_term = f"%\"{tag}\"%"
        
        query = """
        SELECT id, name, description, code, template_id, variables, tags, created_at, updated_at
        FROM projects
        WHERE tags LIKE ?
        ORDER BY updated_at DESC
        LIMIT ?
        """
        
        cursor = self.db_manager.execute(query, (search_term, limit))
        
        if cursor is None:
            return []
        
        projects = []
        for row in cursor.fetchall():
            # JSON文字列をデシリアライズ
            variables = json.loads(row["variables"]) if row["variables"] else {}
            tags = json.loads(row["tags"]) if row["tags"] else []
            
            # タグが実際に含まれているか確認
            if tag in tags:
                project = ProjectModel(
                    name=row["name"],
                    description=row["description"],
                    code=row["code"],
                    template_id=row["template_id"],
                    variables=variables,
                    tags=tags,
                    created_at=row["created_at"],
                    updated_at=row["updated_at"],
                    project_id=row["id"]
                )
                projects.append(project)
        
        return projects
    
    def get_projects_by_template(self, template_id: str, limit: int = 10) -> List[ProjectModel]:
        """
        指定されたテンプレートを使用したプロジェクトを取得します
        
        引数:
            template_id: テンプレートID
            limit: 返す結果の最大数
            
        戻り値:
            ProjectModelインスタンスのリスト
        """
        query = """
        SELECT id, name, description, code, template_id, variables, tags, created_at, updated_at
        FROM projects
        WHERE template_id = ?
        ORDER BY updated_at DESC
        LIMIT ?
        """
        
        cursor = self.db_manager.execute(query, (template_id, limit))
        
        if cursor is None:
            return []
        
        projects = []
        for row in cursor.fetchall():
            # JSON文字列をデシリアライズ
            variables = json.loads(row["variables"]) if row["variables"] else {}
            tags = json.loads(row["tags"]) if row["tags"] else []
            
            project = ProjectModel(
                name=row["name"],
                description=row["description"],
                code=row["code"],
                template_id=row["template_id"],
                variables=variables,
                tags=tags,
                created_at=row["created_at"],
                updated_at=row["updated_at"],
                project_id=row["id"]
            )
            projects.append(project)
        
        return projects
    
    def save_project(self, project: ProjectModel) -> bool:
        """
        プロジェクトを保存します（新規作成または更新）
        
        Args:
            project: 保存するProjectModelインスタンス
            
        Returns:
            保存に成功した場合はTrue、それ以外はFalse
            
        Raises:
            ProjectError: プロジェクトの保存中にエラーが発生した場合
        """
        try:
            # バリデーションチェック
            if not project.is_valid():
                validation_errors = project.validate()
                error_msg = t("project_validation_failed", name=project.name)
                logger.error(f"{error_msg}: {validation_errors}")
                raise ProjectError(error_msg, details={"validation_errors": validation_errors})
            
            # データベース接続確保
            if not self.db_manager.conn:
                self.db_manager.connect()
                
            # トランザクションの開始
            with self.db_manager.transaction() as cursor:
                # 既存のプロジェクトかどうかを確認
                cursor.execute("SELECT id FROM projects WHERE id = ?", (str(project.project_id),))
                existing = cursor.fetchone()
                
                if existing:
                    # 更新
                    success = self._update_project_with_transaction(cursor, project)
                else:
                    # 新規作成
                    success = self._create_project_with_transaction(cursor, project)
                
                if not success:
                    # トランザクション内でのロールバックは自動的に行われる
                    return False
                
                # トランザクションが成功した場合は自動コミットされる
                return True
                
        except DatabaseError as e:
            error_msg = t("project_save_error", name=project.name, error=str(e))
            logger.error(error_msg)
            raise ProjectError(error_msg, project_id=project.project_id, details=e.details)
            
        except Exception as e:
            error_msg = t("project_save_error", name=project.name, error=str(e))
            logger.error(error_msg)
            raise ProjectError(error_msg, project_id=project.project_id)
    
    def _create_project_with_transaction(self, cursor: sqlite3.Cursor, project: ProjectModel) -> bool:
        """
        トランザクション内で新しいプロジェクトを作成します
        
        Args:
            cursor: データベースカーソル
            project: 作成するProjectModelインスタンス
            
        Returns:
            作成に成功した場合はTrue、それ以外はFalse
        """
        try:
            query = """
            INSERT INTO projects (
                id, name, description, code, template_id, variables, tags, created_at, updated_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """
            
            # JSON文字列にシリアライズ
            variables_json = json.dumps(project.variables) if project.variables else '{}'
            tags_json = json.dumps(project.tags) if project.tags else '[]'
            
            params = (
                str(project.project_id),
                project.name,
                project.description,
                project.code,
                project.template_id,
                variables_json,
                tags_json,
                project.created_at.isoformat(),
                project.updated_at.isoformat()
            )
            
            cursor.execute(query, params)
            logger.info(t("project_create_success", name=project.name, project_id=project.project_id))
            return True
            
        except sqlite3.Error as e:
            logger.error(t("project_create_error", name=project.name, error=str(e)))
            return False
            
    # 既存のメソッドを互換性のために残しておく
    def _create_project(self, project: ProjectModel) -> bool:
        """
        新しいプロジェクトを作成します
        
        Args:
            project: 作成するProjectModelインスタンス
            
        Returns:
            作成に成功した場合はTrue、それ以外はFalse
            
        Raises:
            ProjectError: プロジェクト作成中にエラーが発生した場合
        """
        try:
            with self.db_manager.transaction() as cursor:
                return self._create_project_with_transaction(cursor, project)
        except DatabaseError as e:
            error_msg = t("project_create_error", name=project.name, error=str(e))
            logger.error(error_msg)
            raise ProjectError(error_msg, project_id=project.project_id, details=e.details)
        except Exception as e:
            error_msg = t("project_create_error", name=project.name, error=str(e))
            logger.error(error_msg)
            raise ProjectError(error_msg, project_id=project.project_id)
    
    def _update_project_with_transaction(self, cursor: sqlite3.Cursor, project: ProjectModel) -> bool:
        """
        トランザクション内で既存のプロジェクトを更新します
        
        Args:
            cursor: データベースカーソル
            project: 更新するProjectModelインスタンス
            
        Returns:
            更新に成功した場合はTrue、それ以外はFalse
        """
        try:
            query = """
            UPDATE projects
            SET name = ?, description = ?, code = ?, template_id = ?, 
                variables = ?, tags = ?, updated_at = ?
            WHERE id = ?
            """
            
            # JSON文字列にシリアライズ
            variables_json = json.dumps(project.variables) if project.variables else '{}'
            tags_json = json.dumps(project.tags) if project.tags else '[]'
            
            params = (
                project.name,
                project.description,
                project.code,
                project.template_id,
                variables_json,
                tags_json,
                project.updated_at.isoformat(),
                str(project.project_id)
            )
            
            cursor.execute(query, params)
            rows_affected = cursor.rowcount
            
            if rows_affected == 0:
                logger.warning(t("project_update_no_changes", name=project.name, project_id=project.project_id))
            else:
                logger.info(t("project_update_success", name=project.name, project_id=project.project_id))
                
            return True
            
        except sqlite3.Error as e:
            logger.error(t("project_update_error", name=project.name, project_id=project.project_id, error=str(e)))
            return False

    # 既存のメソッドを互換性のために残しておく
    def _update_project(self, project: ProjectModel) -> bool:
        """
        既存のプロジェクトを更新します
        
        Args:
            project: 更新するProjectModelインスタンス
            
        Returns:
            更新に成功した場合はTrue、それ以外はFalse
            
        Raises:
            ProjectError: プロジェクト更新中にエラーが発生した場合
        """
        try:
            with self.db_manager.transaction() as cursor:
                return self._update_project_with_transaction(cursor, project)
        except DatabaseError as e:
            error_msg = t("project_update_error", name=project.name, project_id=project.project_id, error=str(e))
            logger.error(error_msg)
            raise ProjectError(error_msg, project_id=project.project_id, details=e.details)
        except Exception as e:
            error_msg = t("project_update_error", name=project.name, project_id=project.project_id, error=str(e))
            logger.error(error_msg)
            raise ProjectError(error_msg, project_id=project.project_id)
    
    def delete_project(self, project_id: Union[str, int]) -> bool:
        """
        プロジェクトを削除します
        
        Args:
            project_id: 削除するプロジェクトのID
            
        Returns:
            削除に成功した場合はTrue、それ以外はFalse
            
        Raises:
            ProjectError: プロジェクト削除中にエラーが発生した場合
        """
        try:
            # プロジェクトの存在を確認
            project = self.get_project(project_id)
            if not project:
                logger.warning(t("project_not_found", project_id=project_id))
                return False
            
            # データベース接続確保
            if not self.db_manager.conn:
                self.db_manager.connect()
                
            # トランザクションを使用して削除を実行
            with self.db_manager.transaction() as cursor:
                query = "DELETE FROM projects WHERE id = ?"
                cursor.execute(query, (str(project_id),))
                
                rows_affected = cursor.rowcount
                if rows_affected == 0:
                    logger.warning(t("project_delete_no_effect", project_id=project_id))
                    return False
                
                logger.info(t("project_delete_success", name=project.name, project_id=project_id))
                return True
                
        except DatabaseError as e:
            error_msg = t("project_delete_error", project_id=project_id, error=str(e))
            logger.error(error_msg)
            raise ProjectError(error_msg, project_id=project_id, details=e.details)
            
        except Exception as e:
            error_msg = t("project_delete_error", project_id=project_id, error=str(e))
            logger.error(error_msg)
            raise ProjectError(error_msg, project_id=project_id)
    
    def get_project_count(self) -> int:
        """
        データベース内のプロジェクト数を取得します
        
        戻り値:
            プロジェクト数
        """
        query = "SELECT COUNT(*) as count FROM projects"
        cursor = self.db_manager.execute(query)
        
        if cursor is None:
            return 0
        
        row = cursor.fetchone()
        return row["count"] if row else 0
