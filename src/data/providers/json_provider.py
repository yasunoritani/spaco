#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
SPACO - JSONテンプレートプロバイダー

JSON形式で保存されたテンプレートファイルを読み込み、
テンプレートプロバイダーインターフェースを実装します。
"""

from typing import Dict, Any, List, Optional, Tuple, Union
import json
import os
import logging
import re
from pathlib import Path

from .template_provider import TemplateProvider
from ..utils.i18n import translate as t
from ..utils.exceptions import TemplateError, FileError

logger = logging.getLogger(__name__)


class JsonTemplateProvider(TemplateProvider):
    """
    JSON形式のテンプレートファイルからテンプレートを提供するクラス
    
    TemplateProviderインターフェースを実装し、JSON形式で保存された
    テンプレートファイルを読み込み、提供します。
    """
    
    def __init__(self, templates_dir: Optional[str] = None):
        """
        JSONテンプレートプロバイダーを初期化します
        
        引数:
            templates_dir: テンプレートファイルのディレクトリパス（Noneの場合はデフォルトパス）
        """
        self.templates_dir = templates_dir or os.path.join(
            os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__)))), 
            "templates/synthesis"
        )
        logger.info(f"JSONテンプレートディレクトリ: {self.templates_dir}")
        
        # テンプレート辞書を読み込み
        self.templates = self._load_all_templates()
        
        if not self.templates:
            logger.warning("JSONテンプレートを読み込めませんでした。フォールバックテンプレートを使用します。")
            self.templates = self._create_fallback_templates()
        
        # テンプレートにカテゴリとタグを追加（JSONファイル名をカテゴリとして使用）
        self._add_categories_and_tags()
        
        logger.info(f"{len(self.templates)}個のJSONテンプレートを読み込みました")
    
    def _load_all_templates(self) -> Dict[str, Dict[str, Any]]:
        """
        すべてのテンプレートファイルを読み込みます
        
        戻り値:
            Dict[str, Dict[str, Any]]: テンプレート辞書
        """
        all_templates = {}
        
        try:
            # テンプレートディレクトリの存在確認
            template_path = Path(self.templates_dir)
            if not template_path.exists() or not template_path.is_dir():
                logger.error(f"テンプレートディレクトリが存在しません: {self.templates_dir}")
                return {}
            
            # JSONファイルを検索して読み込み
            json_files = list(template_path.glob("*.json"))
            if not json_files:
                logger.warning(f"テンプレートディレクトリにJSONファイルが見つかりません: {self.templates_dir}")
                return {}
            
            # 各JSONファイルからテンプレートを読み込み
            for json_file in json_files:
                logger.info(f"テンプレートファイルを読み込み中: {json_file}")
                templates = self._load_template_file(json_file)
                all_templates.update(templates)
            
            return all_templates
            
        except Exception as e:
            logger.exception(f"テンプレート読み込み中にエラーが発生しました: {str(e)}")
            return {}
    
    def _load_template_file(self, file_path: Path) -> Dict[str, Dict[str, Any]]:
        """
        単一のテンプレートファイルを読み込みます
        
        引数:
            file_path: テンプレートファイルのパス
            
        戻り値:
            Dict[str, Dict[str, Any]]: テンプレート辞書
        """
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                templates = json.load(f)
            
            # テンプレートの検証
            for intent, template_info in templates.items():
                if not isinstance(template_info, dict):
                    logger.warning(f"無効なテンプレート形式: {intent}")
                    continue
                
                if 'template' not in template_info:
                    logger.warning(f"テンプレート文字列が見つかりません: {intent}")
                    continue
            
            return templates
            
        except json.JSONDecodeError as e:
            logger.error(f"JSONパースエラー ({file_path}): {str(e)}")
            return {}
        except Exception as e:
            logger.error(f"テンプレートファイル読み込みエラー ({file_path}): {str(e)}")
            return {}
    
    def _create_fallback_templates(self) -> Dict[str, Dict[str, Any]]:
        """
        フォールバックテンプレートを作成します（テンプレートファイルが読み込めない場合用）
        
        戻り値:
            Dict[str, Dict[str, Any]]: 基本的なテンプレート辞書
        """
        return {
            "generate_sine": {
                "description": "基本的な正弦波オシレーターを生成します。",
                "template": "s.waitForBoot({\n    {\n        // {freq}Hzの正弦波を生成\n        var sig = SinOsc.ar({freq}, 0, {amp});\n        sig = sig * EnvGen.kr(Env.linen(0.01, {duration}, 0.01), doneAction: 2);\n        sig ! 2\n    }.play;\n});",
                "category": "oscillators",
                "tags": ["basic", "wave", "sine"]
            },
            "generate_sawtooth": {
                "description": "ノコギリ波オシレーターを生成します。",
                "template": "s.waitForBoot({\n    {\n        // {freq}Hzのノコギリ波を生成\n        var sig = Saw.ar({freq}, {amp});\n        sig = sig * EnvGen.kr(Env.linen(0.01, {duration}, 0.01), doneAction: 2);\n        sig ! 2\n    }.play;\n});",
                "category": "oscillators",
                "tags": ["basic", "wave", "sawtooth"]
            }
        }
    
    def _add_categories_and_tags(self):
        """
        テンプレートにカテゴリとタグを追加します
        
        JSONファイル名をカテゴリとして使用し、基本的なタグを追加します。
        """
        template_path = Path(self.templates_dir)
        if not template_path.exists() or not template_path.is_dir():
            return
        
        for json_file in template_path.glob("*.json"):
            category = json_file.stem  # ファイル名（拡張子なし）をカテゴリとして使用
            
            # ファイルからテンプレートを読み込み
            try:
                with open(json_file, 'r', encoding='utf-8') as f:
                    templates = json.load(f)
                
                # 各テンプレートにカテゴリとタグを追加
                for intent, template_info in templates.items():
                    if intent in self.templates:
                        # カテゴリを追加
                        self.templates[intent]["category"] = category
                        
                        # 基本的なタグを生成
                        if "tags" not in self.templates[intent]:
                            tags = [category]
                            
                            # 意図識別子からタグを抽出（例: generate_sine -> "generate", "sine"）
                            intent_parts = intent.split('_')
                            tags.extend(intent_parts)
                            
                            # 説明からキーワードを抽出
                            if "description" in self.templates[intent]:
                                description = self.templates[intent]["description"]
                                # 主要な名詞や形容詞を抽出（簡易的な実装）
                                keywords = re.findall(r'\b[a-zA-Z]{4,}\b', description)
                                tags.extend([k.lower() for k in keywords])
                            
                            # 重複を削除して保存
                            self.templates[intent]["tags"] = list(set(tags))
            
            except Exception as e:
                logger.error(f"カテゴリ/タグ追加中にエラーが発生しました ({json_file}): {str(e)}")
    
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
        try:
            if not intent:
                logger.warning(t("template_invalid_intent"))
                return None
            
            if intent not in self.templates:
                logger.debug(t("template_not_found", intent=intent))
                return None
            
            template_content = self.templates[intent].get("template")
            if not template_content:
                logger.warning(t("template_missing_content", intent=intent))
                return None
            
            return template_content
            
        except Exception as e:
            error_msg = t("template_fetch_error", intent=intent, error=str(e))
            logger.error(error_msg)
            raise TemplateError(error_msg, template_id=intent)
    
    def get_template_description(self, intent: str) -> Optional[str]:
        """
        指定された意図に対するテンプレートの説明を取得します
        
        Args:
            intent: テンプレートの意図識別子
            
        Returns:
            テンプレートの説明（見つからない場合はNone）
            
        Raises:
            TemplateError: 説明取得中にエラーが発生した場合
        """
        try:
            if not intent:
                logger.warning(t("template_invalid_intent"))
                return None
                
            if intent not in self.templates:
                logger.debug(t("template_not_found", intent=intent))
                return None
                
            return self.templates[intent].get("description")
            
        except Exception as e:
            error_msg = t("template_description_error", intent=intent, error=str(e))
            logger.error(error_msg)
            raise TemplateError(error_msg, template_id=intent)
    
    def get_all_intents(self) -> List[str]:
        """
        利用可能なすべての意図識別子のリストを取得します
        
        Returns:
            意図識別子のリスト
            
        Raises:
            TemplateError: 意図識別子一覧取得中にエラーが発生した場合
        """
        try:
            intents = list(self.templates.keys())
            logger.debug(t("template_get_all_intents_success", count=len(intents)))
            return intents
            
        except Exception as e:
            error_msg = t("template_get_all_intents_error", error=str(e))
            logger.error(error_msg)
            raise TemplateError(error_msg)
    
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
                logger.debug(t("template_empty_search_query"))
                return []
                
            results = []
            query = query.lower()
            
            for intent, template_info in self.templates.items():
                try:
                    score = 0
                    
                    # 意図識別子に検索クエリが含まれているか
                    if query in intent.lower():
                        score += 3
                    
                    # 説明に検索クエリが含まれているか
                    description = template_info.get("description", "")
                    if description and query in description.lower():
                        score += 2
                    
                    # カテゴリに検索クエリが含まれているか
                    category = template_info.get("category", "")
                    if category and query in category.lower():
                        score += 1
                    
                    # タグに検索クエリが含まれているか
                    tags = template_info.get("tags", [])
                    if any(query in tag.lower() for tag in tags):
                        score += 1
                    
                    # スコアが0より大きい場合、結果に追加
                    if score > 0:
                        result = {
                            "intent": intent,
                            "description": description,
                            "category": template_info.get("category", ""),
                            "is_system": template_info.get("is_system", True),
                            "tags": tags,
                            "score": score
                        }
                        results.append(result)
                except Exception as e:
                    logger.warning(f"検索中のテンプレート処理エラー: {intent}, {str(e)}")
                    continue
            
            # スコアに基づいてソートし、上位N件を返す
            results.sort(key=lambda x: (-x["score"], x["intent"]))
            return results[:limit]
            
        except Exception as e:
            error_msg = t("template_search_error", query=query, error=str(e))
            logger.error(error_msg)
            raise TemplateError(error_msg)
    
    def get_templates_by_category(self, category: str) -> List[Dict[str, Any]]:
        """
        指定されたカテゴリに属するテンプレートを取得します
        
        Args:
            category: テンプレートカテゴリ
            
        Returns:
            テンプレートのリスト
            
        Raises:
            TemplateError: カテゴリ別テンプレート取得中にエラーが発生した場合
        """
        try:
            if not category:
                logger.warning(t("template_invalid_category"))
                return []
                
            results = []
            
            for intent, template_info in self.templates.items():
                try:
                    template_category = template_info.get("category", "")
                    if template_category and template_category.lower() == category.lower():
                        result = {
                            "intent": intent,
                            "description": template_info.get("description", ""),
                            "category": category,
                            "is_system": template_info.get("is_system", True),
                            "tags": template_info.get("tags", [])
                        }
                        results.append(result)
                except Exception as e:
                    logger.warning(f"カテゴリ検索中のテンプレート処理エラー: {intent}, {str(e)}")
                    continue
            
            logger.debug(t("template_category_search_results", category=category, count=len(results)))
            return results
            
        except Exception as e:
            error_msg = t("template_category_search_error", category=category, error=str(e))
            logger.error(error_msg)
            raise TemplateError(error_msg)
    
    def get_templates_by_tag(self, tag: str) -> List[Dict[str, Any]]:
        """
        指定されたタグを持つテンプレートを取得します
        
        Args:
            tag: テンプレートタグ
            
        Returns:
            テンプレートのリスト
            
        Raises:
            TemplateError: タグ別テンプレート取得中にエラーが発生した場合
        """
        try:
            if not tag:
                logger.warning(t("template_invalid_tag"))
                return []
                
            results = []
            tag_lower = tag.lower()
            
            for intent, template_info in self.templates.items():
                try:
                    tags = template_info.get("tags", [])
                    # 大文字小文字を無視して検索
                    if any(tag_lower == t.lower() for t in tags):
                        result = {
                            "intent": intent,
                            "description": template_info.get("description", ""),
                            "category": template_info.get("category", ""),
                            "is_system": template_info.get("is_system", True),
                            "tags": tags
                        }
                        results.append(result)
                except Exception as e:
                    logger.warning(f"タグ検索中のテンプレート処理エラー: {intent}, {str(e)}")
                    continue
            
            logger.debug(t("template_tag_search_results", tag=tag, count=len(results)))
            return results
            
        except Exception as e:
            error_msg = t("template_tag_search_error", tag=tag, error=str(e))
            logger.error(error_msg)
            raise TemplateError(error_msg)
    
    def add_template(self, intent: str, template: str, description: str, 
                     category: Optional[str] = None, tags: Optional[List[str]] = None) -> bool:
        """
        新しいテンプレートを追加します
        
        Args:
            intent: テンプレートの意図識別子
            template: テンプレート文字列
            description: テンプレートの説明
            category: テンプレートのカテゴリ（オプション）
            tags: テンプレートのタグリスト（オプション）
            
        Returns:
            追加に成功した場合はTrue、それ以外はFalse
            
        Raises:
            TemplateError: テンプレート追加中にエラーが発生した場合
            ValidationError: 入力値が無効な場合
        """
        try:
            # 入力値のバリデーション
            if not intent or not intent.strip():
                error_msg = t("template_invalid_intent")
                logger.error(error_msg)
                raise ValidationError(error_msg)
                
            if not template or not template.strip():
                error_msg = t("template_invalid_content", intent=intent)
                logger.error(error_msg)
                raise ValidationError(error_msg)
                
            if intent in self.templates:
                error_msg = t("template_already_exists", intent=intent)
                logger.warning(error_msg)
                return False
            
            # JSONプロバイダーでは新しいテンプレートの追加はメモリ内でのみ可能
            # 実際の用途ではSQLiteプロバイダーを使用して永続化する
            
            # 最小限のタグを生成
            generated_tags = []
            if category:
                generated_tags.append(category.lower())
            
            # 意図からキーワードを抽出
            intent_parts = intent.lower().split('_')
            generated_tags.extend(intent_parts)
            
            # ユーザー指定のタグを結合
            if tags:
                generated_tags.extend([t.lower() for t in tags])
            
            # 重複を除去
            unique_tags = list(set(generated_tags))
            
            self.templates[intent] = {
                "template": template,
                "description": description or "",
                "category": category or "user_defined",
                "tags": unique_tags,
                "is_system": False  # ユーザー定義テンプレートはシステムテンプレートではない
            }
            
            logger.info(t("template_add_success", intent=intent))
            return True
            
        except ValidationError:
            # すでにログが出力されているので再送出しない
            raise
            
        except Exception as e:
            error_msg = t("template_add_error", intent=intent, error=str(e))
            logger.error(error_msg)
            raise TemplateError(error_msg)
    
    def update_template(self, intent: str, template: Optional[str] = None, 
                        description: Optional[str] = None, category: Optional[str] = None, 
                        tags: Optional[List[str]] = None) -> bool:
        """
        既存のテンプレートを更新します
        
        Args:
            intent: 更新するテンプレートの意図識別子
            template: 新しいテンプレート文字列（Noneの場合は更新しない）
            description: 新しい説明（Noneの場合は更新しない）
            category: 新しいカテゴリ（Noneの場合は更新しない）
            tags: 新しいタグリスト（Noneの場合は更新しない）
            
        Returns:
            更新に成功した場合はTrue、それ以外はFalse
            
        Raises:
            TemplateError: テンプレート更新中にエラーが発生した場合
            ValidationError: 入力値が無効な場合
        """
        try:
            # 入力パラメータのバリデーション
            if not intent or not intent.strip():
                error_msg = t("template_invalid_intent")
                logger.error(error_msg)
                raise ValidationError(error_msg)
            
            # テンプレートの存在確認
            if intent not in self.templates:
                error_msg = t("template_not_found", intent=intent)
                logger.warning(error_msg)
                return False
            
            # システムテンプレートの確認
            if self.templates[intent].get("is_system", False):
                logger.warning(t("template_system_update_warning", intent=intent))
            
            # テンプレート内容のバリデーション
            if template is not None and not template.strip():
                error_msg = t("template_invalid_content", intent=intent)
                logger.error(error_msg)
                raise ValidationError(error_msg)
            
            # 更新する値がセットされているか確認
            update_performed = False
            
            if template is not None:
                self.templates[intent]["template"] = template
                update_performed = True
            
            if description is not None:
                self.templates[intent]["description"] = description
                update_performed = True
            
            if category is not None:
                self.templates[intent]["category"] = category
                update_performed = True
                
            if tags is not None:
                self.templates[intent]["tags"] = [t.lower() for t in tags]
                update_performed = True
            
            if not update_performed:
                logger.info(t("template_no_changes", intent=intent))
                return True
            
            logger.info(t("template_update_success", intent=intent))
            return True
            
        except ValidationError:
            # すでにログが出力されているので再送出しない
            raise
            
        except Exception as e:
            error_msg = t("template_update_error", intent=intent, error=str(e))
            logger.error(error_msg)
            raise TemplateError(error_msg)
    
    def delete_template(self, intent: str, force: bool = False) -> bool:
        """
        テンプレートを削除します
        
        Args:
            intent: 削除するテンプレートの意図識別子
            force: システムテンプレートの削除を強制するかどうか
            
        Returns:
            削除に成功した場合はTrue、それ以外はFalse
            
        Raises:
            TemplateError: テンプレート削除中にエラーが発生した場合
            ValidationError: 入力値が無効な場合
            PermissionError: システムテンプレートをforceなしで削除しようとした場合
        """
        try:
            # 入力パラメータのバリデーション
            if not intent or not intent.strip():
                error_msg = t("template_invalid_intent")
                logger.error(error_msg)
                raise ValidationError(error_msg)
            
            # テンプレートの存在確認
            if intent not in self.templates:
                error_msg = t("template_not_found", intent=intent)
                logger.warning(error_msg)
                return False
            
            # システムテンプレートの保護
            if self.templates[intent].get("is_system", False) and not force:
                error_msg = t("template_system_delete_error", intent=intent)
                logger.error(error_msg)
                raise PermissionError(error_msg)
            
            # 削除実行
            template_info = self.templates[intent].copy()  # ログ用にコピーを保存
            del self.templates[intent]
            
            # ログ出力
            if template_info.get("is_system", False):
                logger.warning(t("template_system_delete_warning", intent=intent))
            else:
                logger.info(t("template_delete_success", intent=intent))
                
            return True
            
        except (ValidationError, PermissionError):
            # すでにログが出力されているので再送出しない
            raise
            
        except Exception as e:
            error_msg = t("template_delete_error", intent=intent, error=str(e))
            logger.error(error_msg)
            raise TemplateError(error_msg)
