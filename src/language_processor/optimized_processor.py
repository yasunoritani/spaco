#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
SPACO - 最適化された言語処理モジュール

このモジュールは、自然言語をSuperColliderコードに変換するための
最適化された処理を提供します。
"""

import logging
import time
from typing import Dict, Any, Optional, List, Union, Tuple

from .representation.optimized_converter import OptimizedConversionPipeline
from .representation.intent_level import IntentLevel, IntentType
from .representation.parameter_level import ParameterLevel
from .representation.structure_level import StructureLevel
from .representation.code_level import CodeLevel, CodeType

# プリコンパイルパターン関連のインポート
from .synthesis.precompiled_patterns import pattern_manager
from .synthesis.pattern_catalog import pattern_catalog
from .synthesis.optimized_synthesizer import optimized_synthesizer

logger = logging.getLogger(__name__)


class OptimizedLanguageProcessor:
    """
    最適化された言語処理クラス
    
    このクラスは、自然言語をSuperColliderコードに変換するための
    最適化された処理を提供します。メモ化や他の最適化テクニックを
    使用して、変換パフォーマンスを向上させます。
    """
    
    def __init__(self, cache_size: int = 256, enable_cache_stats: bool = False,
                 use_precompiled_patterns: bool = False, initialize_patterns: bool = False):
        """
        最適化された言語処理クラスを初期化します。
        
        引数:
            cache_size: 各変換器のキャッシュサイズ
            enable_cache_stats: キャッシュの統計情報を収集するかどうか
            use_precompiled_patterns: プリコンパイルパターンを使用するか
            initialize_patterns: 起動時にパターンを初期化するか
        """
        self.pipeline = OptimizedConversionPipeline(
            cache_size=cache_size,
            cache_stats=enable_cache_stats
        )
        self.cache_size = cache_size
        self.enable_cache_stats = enable_cache_stats
        self.use_precompiled_patterns = use_precompiled_patterns
        
        # パフォーマンス計測用メトリクス
        self.performance_metrics = {
            "total_calls": 0,
            "total_processing_time": 0.0,
            "pattern_route_count": 0,
            "pipeline_route_count": 0,
            "pattern_match_success": 0,
            "pattern_match_failure": 0
        }
        
        # プリコンパイルパターンの初期化
        if use_precompiled_patterns and initialize_patterns:
            try:
                pattern_catalog.initialize()
                logger.info("音響パターンカタログが初期化されました")
            except Exception as e:
                logger.error(f"音響パターンカタログの初期化中にエラーが発生しました: {str(e)}", exc_info=True)
                # エラーが発生しても処理は続行
    
    def process(self, instruction: str) -> Dict[str, Any]:
        """
        自然言語の指示を処理し、SuperColliderコードを生成します。
        
        引数:
            instruction: 自然言語の指示
            
        戻り値:
            Dict[str, Any]: 処理結果（コード、メタデータなど）
        """
        start_time = time.time()
        self.performance_metrics["total_calls"] += 1
        
        try:
            # 指示から意図を抽出
            intent = self._extract_intent(instruction)
            
            # プリコンパイルパターンを使用するか判断
            use_patterns = False
            if self.use_precompiled_patterns:
                # パターンルートが適用可能かチェック
                if intent.intent_type in [IntentType.GENERATE_SOUND, IntentType.APPLY_EFFECT]:
                    use_patterns = True
            
            if use_patterns:
                # プリコンパイルパターンを使用した高速ルート
                try:
                    code_level = optimized_synthesizer.synthesize_from_intent(intent)
                    self.performance_metrics["pattern_route_count"] += 1
                    self.performance_metrics["pattern_match_success"] += 1
                except Exception as e:
                    # パターンルートが失敗した場合、通常のパイプラインにフォールバック
                    logger.warning(f"パターンルートが失敗しました: {str(e)}", exc_info=True)
                    code_level = self.pipeline.convert_intent_to_code(intent)
                    self.performance_metrics["pipeline_route_count"] += 1
                    self.performance_metrics["pattern_match_failure"] += 1
            else:
                # 通常の変換パイプライン
                code_level = self.pipeline.convert_intent_to_code(intent)
                self.performance_metrics["pipeline_route_count"] += 1
            
            # SuperColliderコードを生成
            sc_code = code_level.generate_code()
            
            # 結果を返す
            result = {
                "success": True,
                "code": sc_code,
                "metadata": {
                    "intent": intent.to_dict(),
                    "code_type": code_level.code_type.name,
                    "processing_route": "pattern" if use_patterns else "pipeline"
                }
            }
            
            # キャッシュ統計情報を含める（有効な場合）
            if self.enable_cache_stats:
                stats = self.get_cache_stats()
                result["cache_stats"] = stats
            
            # パフォーマンスメトリクスを更新
            end_time = time.time()
            self.performance_metrics["total_processing_time"] += (end_time - start_time)
            
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
        
        stats = {"pipeline": self.pipeline.get_cache_stats()}
        
        if self.use_precompiled_patterns:
            stats["synthesizer"] = optimized_synthesizer.get_performance_metrics()
            stats["pattern_catalog"] = pattern_catalog.get_stats()
        
        # パフォーマンスメトリクスを追加
        metrics = self.performance_metrics.copy()
        if metrics["total_calls"] > 0:
            metrics["avg_processing_time"] = (
                metrics["total_processing_time"] / metrics["total_calls"]
            )
        else:
            metrics["avg_processing_time"] = 0.0
        
        stats["performance"] = metrics
        
        return stats
    
    def clear_cache(self) -> None:
        """
        すべてのキャッシュをクリアします。
        """
        # 各変換器のキャッシュをクリア
        self.pipeline.intent_to_param._convert_impl.cache_clear()
        self.pipeline.param_to_structure._convert_impl.cache_clear()
        self.pipeline.structure_to_code._convert_impl.cache_clear()
        
        # 合成エンジンのキャッシュもクリア
        if self.use_precompiled_patterns:
            optimized_synthesizer.clear_caches()
        
        logger.info("すべての変換キャッシュがクリアされました")
    
    def get_performance_report(self) -> Dict[str, Any]:
        """
        詳細なパフォーマンスレポートを生成します。
        
        戻り値:
            Dict[str, Any]: パフォーマンスレポート
        """
        # 基本的なパフォーマンスメトリクス
        metrics = self.performance_metrics.copy()
        
        # 平均処理時間を計算
        if metrics["total_calls"] > 0:
            metrics["avg_processing_time"] = (
                metrics["total_processing_time"] / metrics["total_calls"]
            )
        else:
            metrics["avg_processing_time"] = 0.0
        
        # ルートの割合を計算
        if metrics["total_calls"] > 0:
            metrics["pattern_route_percentage"] = (
                metrics["pattern_route_count"] / metrics["total_calls"] * 100
            )
            metrics["pipeline_route_percentage"] = (
                metrics["pipeline_route_count"] / metrics["total_calls"] * 100
            )
        else:
            metrics["pattern_route_percentage"] = 0.0
            metrics["pipeline_route_percentage"] = 0.0
        
        # パイプラインとシンセサイザーの統計情報
        report = {
            "performance_metrics": metrics,
            "pipeline_stats": self.pipeline.get_cache_stats() if self.enable_cache_stats else {},
        }
        
        if self.use_precompiled_patterns:
            # シンセサイザーの統計情報
            synth_metrics = optimized_synthesizer.get_performance_metrics()
            
            # 合成ルート使用時の平均速度向上
            if (synth_metrics["total_synthesis_calls"] > 0 and
                metrics["pipeline_route_count"] > 0):
                
                # パイプラインルートの平均時間を推定
                avg_pipeline_time = (
                    metrics["total_processing_time"] - synth_metrics["total_synthesis_time"]
                ) / metrics["pipeline_route_count"]
                
                # パターンルートの平均時間
                avg_pattern_time = (
                    synth_metrics["total_synthesis_time"] / synth_metrics["total_synthesis_calls"]
                )
                
                # 速度向上率を計算（パイプラインに対するパターンの速度）
                if avg_pattern_time > 0:
                    speedup = avg_pipeline_time / avg_pattern_time
                else:
                    speedup = float('inf')  # ゼロ除算を避ける
                
                synth_metrics["speedup_vs_pipeline"] = speedup
            
            report["synthesizer_stats"] = synth_metrics
            report["pattern_stats"] = pattern_catalog.get_stats()
        
        return report


# グローバルな最適化プロセッサーインスタンス
# アプリケーション全体で共有するためのシングルトン
optimized_processor = OptimizedLanguageProcessor(
    cache_size=256,  # デフォルトのキャッシュサイズ
    enable_cache_stats=True,  # 統計情報を有効化
    use_precompiled_patterns=True,  # プリコンパイルパターンを使用
    initialize_patterns=True  # 起動時にパターンを初期化
)
