#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
SPACO - 音響合成パターンモジュール

このモジュールは、基本的な音響合成パターンのテンプレートを提供します。
SuperColliderの基本的なオシレーター、エンベロープ、フィルター、エフェクトを
自然言語から生成するためのテンプレートとパターンを定義します。
"""

from typing import Dict, Any, List, Optional, Tuple, Union
import re
import logging
import json
import os

from .synthesis.templates import TemplateManager
from .synthesis.patterns import PatternMatcher
from .synthesis.parameters import ParameterExtractor
from .synthesis.utils import (
    SynthesisPatternError, 
    TemplateLoadingError, 
    PatternMatchingError, 
    ParameterExtractionError
)

logger = logging.getLogger(__name__)


class SynthesisPatterns:
    """
    音響合成パターンを提供するファサードクラス
    
    基本的な音響合成パターン（オシレーター、エンベロープ、フィルター、エフェクト）の
    テンプレートとパターンを管理し、自然言語指示からSuperColliderコードを生成するための
    基盤を提供します。
    
    このクラスはファサードパターンを利用して、各種サブモジュールの機能を統合します。
    """
    
    def __init__(self, templates_dir: Optional[str] = None):
        """
        音響合成パターンを初期化します
        
        引数:
            templates_dir: テンプレートファイルのディレクトリパス。指定しない場合はデフォルト値を使用します。
        """
        try:
            # サブモジュールの初期化
            self.template_manager = TemplateManager(templates_dir)
            self.pattern_matcher = PatternMatcher()
            self.parameter_extractor = ParameterExtractor()
            
            # 各モジュールから必要なデータを取得
            self.templates = self._get_templates()
            self.intent_patterns = self._get_intent_patterns()
            self.note_to_freq = self._get_note_to_freq_mapping()
            
            logger.info("音響合成パターンを初期化しました")
            
        except Exception as e:
            logger.exception(f"音響合成パターンの初期化中にエラーが発生しました: {str(e)}")
            raise SynthesisPatternError(f"初期化エラー: {str(e)}", original_exception=e)
    
    def _get_templates(self) -> Dict[str, Dict[str, str]]:
        """
        テンプレート管理サブモジュールからテンプレートを取得します

        戻り値:
            Dict[str, Dict[str, str]]: テンプレート辞書
        """
        # template_manager から全テンプレートを取得
        templates = {}
        
        # すべての意図IDを取得
        intent_ids = self.template_manager.get_all_intents()
        
        # 各意図についてテンプレートと説明を取得
        for intent_id in intent_ids:
            template = self.template_manager.get_template(intent_id)
            description = self.template_manager.get_template_description(intent_id)
            
            if template:
                templates[intent_id] = {
                    "template": template,
                    "description": description or ""
                }
                
        return templates

    def _get_intent_patterns(self) -> Dict[str, List[str]]:
        """
        パターン認識サブモジュールから意図パターンを取得します
        
        戻り値:
            Dict[str, List[str]]: 意図パターン辞書
        """
        return self.pattern_matcher.get_all_patterns()
        
    def _get_note_to_freq_mapping(self) -> Dict[str, float]:
        """
        パラメータ抽出サブモジュールから音符マッピングを取得します
        
        戻り値:
            Dict[str, float]: 音符名と周波数のマッピング
        """
        return self.parameter_extractor.note_converter.note_to_freq
    
    def get_default_parameters(self, intent: str) -> Dict[str, Any]:
        """
        意図に応じたデフォルトパラメーターを取得します
        
        引数:
            intent: パターンの意図
            
        戻り値:
            Dict[str, Any]: デフォルトパラメーター辞書
        """
        # パラメータ抽出モジュールからデフォルト値を取得
        return self.parameter_extractor.set_default_parameters({}, intent)
    
    def process(self, input_text: str) -> Dict[str, Any]:
        """
        自然言語指示を処理して音響合成パターンのSuperColliderコードを生成します
        
        引数:
            input_text: 自然言語による指示テキスト
            
        戻り値:
            Dict[str, Any]: 処理結果（生成コード、認識された意図、抽出されたパラメーター）
        """
        try:
            # 意図を認識
            intent, pattern, match = self.pattern_matcher.match_intent(input_text)
            
            # 意図を認識できなかった場合
            if intent is None:
                logger.warning(f"意図を認識できませんでした: {input_text}")
                return {
                    "status": "error",
                    "error_type": "intent_recognition",
                    "message": f"意図を認識できませんでした: {input_text}"
                }
            
            logger.info(f"意図を認識しました: {intent}")
            
            # パラメーターを抽出
            params = self.parameter_extractor.extract_parameters(input_text, intent, match)
            logger.info(f"パラメーターを抽出しました: {params}")
            
            # デフォルトパラメーターを設定
            params = self.parameter_extractor.set_default_parameters(params, intent)
            
            # パラメーターを検証
            params = self.parameter_extractor.validate_parameters(params)
            
            # テンプレートを取得
            template = self.template_manager.get_template(intent)
            if not template:
                logger.error(f"テンプレートが見つかりません: {intent}")
                return {
                    "status": "error",
                    "error_type": "template_not_found",
                    "message": f"テンプレートが見つかりません: {intent}"
                }
            
            # テンプレートにパラメーターを適用してコードを生成
            code = template.format(**params)
            logger.info(f"コードを生成しました: {code[:50]}...")
            
            # 結果を返す
            return {
                "status": "success",
                "code": code,
                "intent": intent,
                "parameters": params
            }
            
        except PatternMatchingError as e:
            logger.error(f"パターンマッチングエラー: {str(e)}")
            return {
                "status": "error",
                "error_type": "pattern_matching",
                "message": str(e)
            }
        except ParameterExtractionError as e:
            logger.error(f"パラメーター抽出エラー: {str(e)}")
            return {
                "status": "error",
                "error_type": "parameter_extraction",
                "message": str(e)
            }
        except TemplateLoadingError as e:
            logger.error(f"テンプレートロードエラー: {str(e)}")
            return {
                "status": "error",
                "error_type": "template_loading",
                "message": str(e)
            }
        except Exception as e:
            logger.exception(f"予期しないエラー: {str(e)}")
            return {
                "status": "error",
                "error_type": "unknown",
                "message": f"予期しないエラー: {str(e)}"
            }
