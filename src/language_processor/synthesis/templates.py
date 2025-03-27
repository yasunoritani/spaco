#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
SPACO - 音響合成パターン テンプレート管理モジュール

このモジュールは、音響合成パターンのテンプレートの読み込みと管理を担当します。
JSON形式で保存されたテンプレートファイルを読み込んでテンプレート辞書を提供します。
"""

from typing import Dict, Any, List, Optional, Tuple, Union
import json
import os
import logging
from pathlib import Path
from .utils import TemplateLoadingError

logger = logging.getLogger(__name__)


class TemplateManager:
    """
    テンプレート管理クラス
    
    音響合成パターンのテンプレートを外部ファイルから読み込み、
    テンプレート辞書として提供します。
    """
    
    def __init__(self, templates_dir: Optional[str] = None):
        """
        テンプレート管理を初期化します
        
        引数:
            templates_dir: テンプレートファイルのディレクトリパス
        """
        self.templates_dir = templates_dir or os.path.join(
            os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 
            "templates/synthesis"
        )
        logger.info(f"テンプレートディレクトリ: {self.templates_dir}")
        
        # テンプレート辞書を読み込み
        self.templates = self._load_all_templates()
        
        if not self.templates:
            logger.warning("テンプレートを読み込めませんでした。フォールバックテンプレートを使用します。")
            self.templates = self._create_fallback_templates()
        
        logger.info(f"{len(self.templates)}個のテンプレートを読み込みました")
    
    def _load_all_templates(self) -> Dict[str, Dict[str, str]]:
        """
        すべてのテンプレートファイルを読み込みます
        
        戻り値:
            Dict[str, Dict[str, str]]: テンプレート辞書
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
            raise TemplateLoadingError(f"テンプレート読み込みエラー: {str(e)}", original_exception=e)
    
    def _load_template_file(self, file_path: Path) -> Dict[str, Dict[str, str]]:
        """
        単一のテンプレートファイルを読み込みます
        
        引数:
            file_path: テンプレートファイルのパス
            
        戻り値:
            Dict[str, Dict[str, str]]: テンプレート辞書
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
    
    def _create_fallback_templates(self) -> Dict[str, Dict[str, str]]:
        """
        フォールバックテンプレートを作成します（テンプレートファイルが読み込めない場合用）
        
        戻り値:
            Dict[str, Dict[str, str]]: 基本的なテンプレート辞書
        """
        return {
            "generate_sine": {
                "description": "基本的な正弦波オシレーターを生成します。",
                "template": "s.waitForBoot({\n    {\n        // {freq}Hzの正弦波を生成\n        var sig = SinOsc.ar({freq}, 0, {amp});\n        sig = sig * EnvGen.kr(Env.linen(0.01, {duration}, 0.01), doneAction: 2);\n        sig ! 2\n    }.play;\n});"
            },
            "generate_sawtooth": {
                "description": "ノコギリ波オシレーターを生成します。",
                "template": "s.waitForBoot({\n    {\n        // {freq}Hzのノコギリ波を生成\n        var sig = Saw.ar({freq}, {amp});\n        sig = sig * EnvGen.kr(Env.linen(0.01, {duration}, 0.01), doneAction: 2);\n        sig ! 2\n    }.play;\n});"
            }
        }
    
    def get_template(self, intent: str) -> Optional[str]:
        """
        指定された意図に対するテンプレートを取得します
        
        引数:
            intent: テンプレートの意図識別子
            
        戻り値:
            Optional[str]: テンプレート文字列（見つからない場合はNone）
        """
        if intent not in self.templates:
            logger.warning(f"テンプレートが見つかりません: {intent}")
            return None
        
        return self.templates[intent].get("template")
    
    def get_template_description(self, intent: str) -> Optional[str]:
        """
        指定された意図に対するテンプレートの説明を取得します
        
        引数:
            intent: テンプレートの意図識別子
            
        戻り値:
            Optional[str]: テンプレートの説明（見つからない場合はNone）
        """
        if intent not in self.templates:
            return None
        
        return self.templates[intent].get("description")
    
    def get_all_intents(self) -> List[str]:
        """
        利用可能なすべての意図識別子のリストを取得します
        
        戻り値:
            List[str]: 意図識別子のリスト
        """
        return list(self.templates.keys())
