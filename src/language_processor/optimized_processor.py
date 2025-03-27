#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
SPACO - 最適化された言語処理モジュール

このモジュールは、自然言語をSuperColliderコードに変換するための
最適化された処理を提供します。
"""

import logging
from typing import Dict, Any, Optional, List, Union

from .representation.optimized_converter import OptimizedConversionPipeline
from .representation.intent_level import IntentLevel, IntentType
from .representation.parameter_level import ParameterLevel
from .representation.structure_level import StructureLevel
from .representation.code_level import CodeLevel

logger = logging.getLogger(__name__)


class OptimizedLanguageProcessor:
    """
    最適化された言語処理クラス
    
    このクラスは、自然言語をSuperColliderコードに変換するための
    最適化された処理を提供します。メモ化や他の最適化テクニックを
    使用して、変換パフォーマンスを向上させます。
    """
    
    def __init__(self, cache_size: int = 256, enable_cache_stats: bool = False):
        """
        最適化された言語処理クラスを初期化します。
        
        引数:
            cache_size: 各変換器のキャッシュサイズ
            enable_cache_stats: キャッシュの統計情報を収集するかどうか
        """
        self.pipeline = OptimizedConversionPipeline(
            cache_size=cache_size,
            cache_stats=enable_cache_stats
        )
        self.cache_size = cache_size
        self.enable_cache_stats = enable_cache_stats
    
    def process(self, instruction: str) -> Dict[str, Any]:
        """
        自然言語の指示を処理し、SuperColliderコードを生成します。
        
        引数:
            instruction: 自然言語の指示
            
        戻り値:
            Dict[str, Any]: 処理結果（コード、メタデータなど）
        """
        try:
            # 指示から意図を抽出
            intent = self._extract_intent(instruction)
            
            # 意図からコードを生成
            code_level = self.pipeline.convert_intent_to_code(intent)
            
            # SuperColliderコードを生成
            sc_code = code_level.generate_code()
            
            # 結果を返す
            result = {
                "success": True,
                "code": sc_code,
                "metadata": {
                    "intent": intent.to_dict(),
                    "code_type": code_level.code_type.name
                }
            }
            
            # キャッシュ統計情報を含める（有効な場合）
            if self.enable_cache_stats:
                result["cache_stats"] = self.pipeline.get_cache_stats()
            
            return result
        except Exception as e:
            logger.error(f"言語処理中にエラーが発生しました: {str(e)}", exc_info=True)
            return {
                "success": False,
                "error": str(e),
                "error_type": type(e).__name__
            }
    
    def _extract_intent(self, instruction: str) -> IntentLevel:
        """
        自然言語の指示から意図を抽出します。
        
        引数:
            instruction: 自然言語の指示
            
        戻り値:
            IntentLevel: 抽出された意図レベルの表現
        """
        # 意図タイプを決定（簡易的な実装）
        intent_type = IntentType.GENERATE_SOUND  # デフォルト
        
        if "エフェクト" in instruction or "effect" in instruction.lower():
            intent_type = IntentType.APPLY_EFFECT
        elif "シーケンス" in instruction or "sequence" in instruction.lower():
            intent_type = IntentType.CREATE_SEQUENCE
        elif "メロディ" in instruction or "melody" in instruction.lower():
            intent_type = IntentType.CREATE_MELODY
        elif "楽器" in instruction or "instrument" in instruction.lower():
            intent_type = IntentType.GENERATE_INSTRUMENT
            
        # パラメータを抽出（簡易的な実装）
        extracted_parameters = {}
        
        # 周波数の抽出
        if "Hz" in instruction:
            import re
            match = re.search(r'(\d+)Hz', instruction)
            if match:
                frequency = float(match.group(1))
                extracted_parameters["frequency"] = {
                    "value_type": "static",
                    "value": frequency,
                    "unit": "Hz"
                }
        
        # 波形の抽出
        waveforms = {
            "正弦波": "sine",
            "sine": "sine",
            "ノコギリ波": "saw",
            "saw": "saw",
            "矩形波": "square",
            "square": "square",
            "三角波": "triangle",
            "triangle": "triangle"
        }
        
        for jp, en in waveforms.items():
            if jp in instruction or en in instruction.lower():
                extracted_parameters["waveform"] = {
                    "value_type": "static",
                    "value": en
                }
                break
                
        # 意図レベルの表現を作成
        metadata = {}
        if extracted_parameters:
            metadata["extracted_parameters"] = extracted_parameters
            
        intent = IntentLevel(intent_type, instruction, metadata)
        return intent
    
    def get_cache_stats(self) -> Dict[str, Dict[str, Any]]:
        """
        キャッシュの統計情報を返します。
        
        戻り値:
            Dict[str, Dict[str, Any]]: キャッシュの統計情報
        """
        if not self.enable_cache_stats:
            return {"enabled": False}
            
        return self.pipeline.get_cache_stats()
    
    def clear_cache(self) -> None:
        """
        すべてのキャッシュをクリアします。
        """
        # 各変換器のキャッシュをクリア
        self.pipeline.intent_to_param._convert_impl.cache_clear()
        self.pipeline.param_to_structure._convert_impl.cache_clear()
        self.pipeline.structure_to_code._convert_impl.cache_clear()
        
        logger.info("すべての変換キャッシュがクリアされました")


# グローバルな最適化プロセッサーインスタンス
# アプリケーション全体で共有するためのシングルトン
optimized_processor = OptimizedLanguageProcessor(
    cache_size=256,  # デフォルトのキャッシュサイズ
    enable_cache_stats=True  # 統計情報を有効化
)
