#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
SPACO - 最適化された音響合成モジュール

このモジュールは、自然言語から高性能なSuperColliderコードを生成するための
音響合成エンジンの最適化実装を提供します。
"""

import logging
import time
import re
from typing import Dict, Any, List, Optional, Set, Union, Tuple, Callable
from functools import lru_cache

from .precompiled_patterns import pattern_manager, PrecompiledPattern
from .pattern_catalog import pattern_catalog, ALL_PATTERNS
from src.language_processor.representation.intent_level import IntentLevel, IntentType
from src.language_processor.representation.code_level import CodeLevel, CodeType

logger = logging.getLogger(__name__)


class OptimizedSynthesizer:
    """
    最適化された音響合成エンジン
    
    このクラスは、意図レベルから直接SuperColliderコードを生成するための
    最適化された処理を提供します。プリコンパイル済みのパターンを使用して
    パフォーマンスを大幅に向上させます。
    """
    
    def __init__(self, cache_size: int = 128, patterns_initialized: bool = False):
        """
        最適化された音響合成エンジンを初期化します。
        
        引数:
            cache_size: 各キャッシュのサイズ
            patterns_initialized: パターンが既に初期化されているかどうか
        """
        self.cache_size = cache_size
        self._performance_metrics = {
            "total_synthesis_time": 0.0,
            "total_synthesis_calls": 0,
            "pattern_hit_count": 0,
            "pattern_miss_count": 0,
            "cache_hit_count": 0
        }
        
        # パターンカタログが初期化されていなければ初期化
        if not patterns_initialized and not pattern_catalog.initialized:
            pattern_catalog.initialize()
    
    @lru_cache(maxsize=128)
    def _get_waveform_pattern(self, waveform_type: str) -> Optional[PrecompiledPattern]:
        """
        波形タイプに基づいてプリコンパイル済みのパターンを取得します。
        
        引数:
            waveform_type: 波形タイプ (sine, saw, triangle, square など)
            
        戻り値:
            Optional[PrecompiledPattern]: 見つかったパターン、または None
        """
        if waveform_type in ALL_PATTERNS:
            compiled_pattern = pattern_catalog.get_compiled_pattern(waveform_type)
            if compiled_pattern:
                return compiled_pattern
        
        # デフォルトは正弦波
        return pattern_catalog.get_compiled_pattern("sine")
    
    @lru_cache(maxsize=128)
    def _get_effect_pattern(self, effect_type: str) -> Optional[PrecompiledPattern]:
        """
        エフェクトタイプに基づいてプリコンパイル済みのパターンを取得します。
        
        引数:
            effect_type: エフェクトタイプ (reverb, delay など)
            
        戻り値:
            Optional[PrecompiledPattern]: 見つかったパターン、または None
        """
        if effect_type in ALL_PATTERNS:
            compiled_pattern = pattern_catalog.get_compiled_pattern(effect_type)
            if compiled_pattern:
                return compiled_pattern
                
        return None
    
    @lru_cache(maxsize=128)
    def _generate_synth_code(self, waveform: str, params: Tuple) -> str:
        """
        シンセサイザーコードを生成します。
        
        引数:
            waveform: 波形タイプ
            params: パラメータのタプル表現
            
        戻り値:
            str: 生成されたSuperColliderコード
        """
        # タプルからパラメータ辞書に変換
        param_dict = dict(params)
        
        # プリコンパイル済みパターンを取得
        pattern = self._get_waveform_pattern(waveform)
        if not pattern:
            # デフォルトパターンにフォールバック
            pattern = self._get_waveform_pattern("sine")
            self._performance_metrics["pattern_miss_count"] += 1
        else:
            self._performance_metrics["pattern_hit_count"] += 1
        
        # パターンのコードを取得
        code = pattern.compiled_code
        
        # パラメータを反映
        for param_name, param_value in param_dict.items():
            # パラメータ名をキャメルケースからスネークケースに変換
            sc_param_name = param_name.replace("_", "")
            
            # コード内のパラメータ値を置換
            if isinstance(param_value, (int, float)):
                code = re.sub(
                    rf"{sc_param_name}=[\d\.]+", 
                    f"{sc_param_name}={param_value}", 
                    code
                )
            elif isinstance(param_value, str):
                code = re.sub(
                    rf"{sc_param_name}=['\"][\w\d]+['\"]", 
                    f"{sc_param_name}='{param_value}'", 
                    code
                )
        
        return code
    
    @lru_cache(maxsize=64)
    def _generate_effect_code(self, effect_type: str, params: Tuple) -> str:
        """
        エフェクトコードを生成します。
        
        引数:
            effect_type: エフェクトタイプ
            params: パラメータのタプル表現
            
        戻り値:
            str: 生成されたSuperColliderコード
        """
        # タプルからパラメータ辞書に変換
        param_dict = dict(params)
        
        # プリコンパイル済みパターンを取得
        pattern = self._get_effect_pattern(effect_type)
        if not pattern:
            self._performance_metrics["pattern_miss_count"] += 1
            # エフェクトが見つからない場合は空文字列
            return ""
            
        self._performance_metrics["pattern_hit_count"] += 1
        
        # パターンのコードを取得
        code = pattern.compiled_code
        
        # パラメータを反映
        for param_name, param_value in param_dict.items():
            # パラメータ名をキャメルケースからスネークケースに変換
            sc_param_name = param_name.replace("_", "")
            
            # コード内のパラメータ値を置換
            if isinstance(param_value, (int, float)):
                code = re.sub(
                    rf"{sc_param_name}=[\d\.]+", 
                    f"{sc_param_name}={param_value}", 
                    code
                )
            elif isinstance(param_value, str):
                code = re.sub(
                    rf"{sc_param_name}=['\"][\w\d]+['\"]", 
                    f"{sc_param_name}='{param_value}'", 
                    code
                )
        
        return code
    
    def synthesize_from_intent(self, intent: IntentLevel) -> CodeLevel:
        """
        意図レベルから直接コードレベルを生成します。
        この最適化された実装は従来のパイプラインをバイパスし、
        プリコンパイル済みのパターンを使用してパフォーマンスを大幅に向上させます。
        
        引数:
            intent: 意図レベルの表現
            
        戻り値:
            CodeLevel: 生成されたコードレベルの表現
        """
        start_time = time.time()
        self._performance_metrics["total_synthesis_calls"] += 1
        
        # 意図から基本パラメータを抽出
        intent_type = intent.intent_type
        description = intent.description
        metadata = intent.metadata or {}
        
        # 波形の抽出
        waveform = "sine"  # デフォルト
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
            if jp in description or en in description.lower():
                waveform = en
                break
        
        # パラメータの抽出・設定
        params = {}
        
        # 周波数の抽出
        if "Hz" in description:
            match = re.search(r'(\d+)Hz', description)
            if match:
                params["freq"] = float(match.group(1))
        
        # アンプの抽出
        if "音量" in description:
            if "大きい" in description or "強い" in description:
                params["amp"] = 0.8
            elif "小さい" in description or "弱い" in description:
                params["amp"] = 0.3
            else:
                params["amp"] = 0.5
        
        # パンの抽出
        if "左" in description:
            params["pan"] = -0.8
        elif "右" in description:
            params["pan"] = 0.8
        
        # エンベロープの抽出
        if "ゆっくり" in description:
            params["attack"] = 2.0
            params["release"] = 3.0
        elif "速く" in description:
            params["attack"] = 0.01
            params["release"] = 0.1
        
        # 明示的に抽出されたパラメータの処理（メタデータから）
        if "extracted_parameters" in metadata:
            extracted = metadata["extracted_parameters"]
            
            if "frequency" in extracted:
                freq_data = extracted["frequency"]
                if freq_data["value_type"] == "static":
                    params["freq"] = freq_data["value"]
                    
            if "waveform" in extracted:
                waveform_data = extracted["waveform"]
                if waveform_data["value_type"] == "static":
                    waveform = waveform_data["value"]
                    
            # 他のパラメータも同様に処理
        
        # エフェクトの抽出
        effects = []
        if "エコー" in description or "echo" in description.lower():
            effects.append(("delay", {"delaytime": 0.5, "decay": 4.0, "mix": 0.4}))
            
        if "リバーブ" in description or "reverb" in description.lower():
            effects.append(("reverb", {"mix": 0.3, "room": 0.7, "damp": 0.5}))
        
        # コード生成
        # パラメータをタプルに変換（キャッシュキーとして使用）
        param_tuple = tuple(sorted(params.items()))
        
        # シンセコードを生成
        synth_code = self._generate_synth_code(waveform, param_tuple)
        
        # エフェクトコードを生成
        effect_code = ""
        for effect_type, effect_params in effects:
            effect_param_tuple = tuple(sorted(effect_params.items()))
            effect_code += self._generate_effect_code(effect_type, effect_param_tuple)
        
        # 実行コードを生成
        exec_code = ""
        if intent_type == IntentType.GENERATE_SOUND:
            exec_code = f"""
(
// 音を鳴らす
Synth(\\basic{waveform.capitalize()}, [
    {", ".join([f"{k}: {v}" for k, v in params.items()])}
]);
)
"""
        
        # 最終コードを結合
        final_code = f"{synth_code}\n\n{effect_code}\n\n{exec_code}".strip()
        
        # CodeLevelオブジェクトを作成
        code_level = CodeLevel(
            code_type=CodeType.SUPER_COLLIDER,
            variables=[],
            code=final_code,
            metadata={
                "waveform": waveform,
                "params": params,
                "effects": [e[0] for e in effects],
                "synthesized": True,
                "optimized": True
            }
        )
        
        # パフォーマンス計測終了
        elapsed = time.time() - start_time
        self._performance_metrics["total_synthesis_time"] += elapsed
        
        logger.debug(f"音響合成コード生成完了: {elapsed:.3f}秒")
        return code_level
    
    def get_performance_metrics(self) -> Dict[str, Any]:
        """
        パフォーマンスメトリクスを取得します。
        
        戻り値:
            Dict[str, Any]: パフォーマンスメトリクス
        """
        metrics = self._performance_metrics.copy()
        
        # 平均合成時間を計算
        if metrics["total_synthesis_calls"] > 0:
            metrics["avg_synthesis_time"] = (
                metrics["total_synthesis_time"] / metrics["total_synthesis_calls"]
            )
        else:
            metrics["avg_synthesis_time"] = 0.0
            
        # パターンヒット率を計算
        total_pattern_requests = metrics["pattern_hit_count"] + metrics["pattern_miss_count"]
        if total_pattern_requests > 0:
            metrics["pattern_hit_rate"] = metrics["pattern_hit_count"] / total_pattern_requests
        else:
            metrics["pattern_hit_rate"] = 0.0
            
        # キャッシュ情報を追加
        metrics["waveform_cache_info"] = self._get_waveform_pattern.cache_info()._asdict()
        metrics["effect_cache_info"] = self._get_effect_pattern.cache_info()._asdict()
        metrics["synth_code_cache_info"] = self._generate_synth_code.cache_info()._asdict()
        metrics["effect_code_cache_info"] = self._generate_effect_code.cache_info()._asdict()
        
        return metrics
    
    def clear_caches(self) -> None:
        """すべてのキャッシュをクリアします。"""
        self._get_waveform_pattern.cache_clear()
        self._get_effect_pattern.cache_clear()
        self._generate_synth_code.cache_clear()
        self._generate_effect_code.cache_clear()
        logger.info("すべての合成キャッシュがクリアされました")


# シングルトンインスタンス
optimized_synthesizer = OptimizedSynthesizer()
