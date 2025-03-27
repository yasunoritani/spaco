#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
SPACO - 最適化された表現レベル間の変換

このモジュールは、異なる表現レベル（意図、パラメータ、構造、コード）間の
変換を行うクラスの最適化版を提供します。
"""

from typing import Dict, Any, List, Optional, Set, Union, Tuple, Callable
import logging
import functools
import time

from .base import ValidationError
from .intent_level import IntentLevel, IntentType
from .parameter_level import ParameterLevel, ParameterValue, ParameterType
from .structure_level import StructureLevel, StructureComponent, StructureType
from .code_level import CodeLevel, CodeVariable, CodeType
from .converter import (
    BaseConverter, ConversionError,
    IntentToParameterConverter, ParameterToStructureConverter, StructureToCodeConverter
)

logger = logging.getLogger(__name__)


class MemoizedConverter(BaseConverter):
    """
    メモ化（キャッシュ）機能を持つ基底コンバータークラス
    
    このクラスは、変換処理の結果をキャッシュすることで、
    同じ入力に対する処理を高速化します。
    """
    
    def __init__(self, cache_size: int = 128, cache_stats: bool = False):
        """
        メモ化コンバーターを初期化します。
        
        引数:
            cache_size: キャッシュの最大サイズ
            cache_stats: キャッシュの統計情報を収集するかどうか
        """
        super().__init__()
        self.cache_size = cache_size
        self.cache_stats = cache_stats
        self.cache_hits = 0
        self.cache_misses = 0
        self.total_time_saved = 0.0
    
    def _memoize_function(self, func: Callable) -> Callable:
        """
        関数をメモ化（キャッシュ）するラッパー関数を返します。
        
        引数:
            func: メモ化する関数
            
        戻り値:
            Callable: メモ化された関数
        """
        @functools.lru_cache(maxsize=self.cache_size)
        def cached_func(*args, **kwargs):
            if self.cache_stats:
                start_time = time.time()
                
            result = func(*args, **kwargs)
            
            if self.cache_stats:
                self.cache_misses += 1
                
            return result
        
        def wrapper(*args, **kwargs):
            # キャッシュされた関数を呼び出す前に、キャッシュヒットを判定
            if self.cache_stats:
                # LRU_cacheはキャッシュヒットを直接確認する方法がないため、
                # 処理時間を測定して推測する
                start_time = time.time()
                result = cached_func(*args, **kwargs)
                elapsed = time.time() - start_time
                
                # 処理時間が極端に短い場合はキャッシュヒットと判断
                if elapsed < 0.001:  # 1ms以下
                    self.cache_hits += 1
                    # キャッシュヒットの場合、通常の処理時間を推定して加算
                    # 実際の数値はプロファイリングで調整が必要
                    self.total_time_saved += 0.01  # 推定10ms
            else:
                result = cached_func(*args, **kwargs)
                
            return result
        
        # オリジナル関数の属性を保持
        functools.update_wrapper(wrapper, func)
        return wrapper
    
    def get_cache_stats(self) -> Dict[str, Any]:
        """
        キャッシュの統計情報を返します。
        
        戻り値:
            Dict[str, Any]: キャッシュの統計情報
        """
        if not self.cache_stats:
            return {"enabled": False}
            
        total_calls = self.cache_hits + self.cache_misses
        hit_rate = self.cache_hits / total_calls if total_calls > 0 else 0
        
        return {
            "enabled": True,
            "hits": self.cache_hits,
            "misses": self.cache_misses,
            "total_calls": total_calls,
            "hit_rate": hit_rate,
            "time_saved_sec": self.total_time_saved
        }


class MemoizedIntentToParameterConverter(IntentToParameterConverter, MemoizedConverter):
    """
    メモ化機能を持つ意図レベルからパラメータレベルへの変換クラス
    
    このクラスは、意図レベルの表現からパラメータレベルの表現への変換を行い、
    結果をキャッシュします。同じ意図に対する変換を高速化します。
    """
    
    def __init__(self, default_parameters: Optional[Dict[str, Dict[str, Any]]] = None,
                 cache_size: int = 128, cache_stats: bool = False):
        """
        メモ化された意図からパラメータへの変換クラスを初期化します。
        
        引数:
            default_parameters: 意図タイプごとのデフォルトパラメータ
            cache_size: キャッシュの最大サイズ
            cache_stats: キャッシュの統計情報を収集するかどうか
        """
        IntentToParameterConverter.__init__(self, default_parameters)
        MemoizedConverter.__init__(self, cache_size, cache_stats)
        
        # 変換関数をメモ化関数に置き換える
        self._convert_impl_original = self._convert_impl
        self._convert_impl = self._memoize_function(self._convert_impl)
    
    def convert(self, intent: IntentLevel) -> ParameterLevel:
        """
        意図レベルの表現をパラメータレベルの表現に変換します。
        
        引数:
            intent: 意図レベルの表現
            
        戻り値:
            ParameterLevel: 変換されたパラメータレベルの表現
            
        例外:
            ConversionError: 変換中にエラーが発生した場合
        """
        # 入力の検証
        self._validate_input(intent)
        
        # キャッシュのキーとして使用するために不変表現に変換
        try:
            # 直接_convert_implを呼び出す（キャッシュを使用）
            result = self._convert_impl(
                intent.intent_type,
                intent.description,
                # metadataは辞書型なのでJSONに変換してからtupleに変換
                tuple(sorted(intent.metadata.items())) if intent.metadata else tuple(),
                intent.confidence
            )
            return result
        except Exception as e:
            if isinstance(e, ConversionError):
                raise
            else:
                raise ConversionError(
                    f"変換中にエラーが発生しました: {str(e)}", 
                    source_level=intent.__class__.__name__,
                    original_exception=e
                )
    
    def _convert_impl(self, intent_type: IntentType, description: str, 
                      metadata_tuple: Tuple, confidence: float) -> ParameterLevel:
        """
        意図レベルからパラメータレベルへの変換を実装します。
        このメソッドはメモ化されます。
        
        引数:
            intent_type: 意図の種類
            description: 意図の説明
            metadata_tuple: メタデータのタプル表現
            confidence: 確信度
            
        戻り値:
            ParameterLevel: 変換されたパラメータレベルの表現
        """
        # タプルを辞書に戻す
        metadata = dict(metadata_tuple) if metadata_tuple else {}
        
        # IntentLevelオブジェクトを再構築
        intent = IntentLevel(intent_type, description, metadata, confidence)
        
        # 元の変換処理を呼び出す
        return self._convert_impl_original(intent)


class MemoizedParameterToStructureConverter(ParameterToStructureConverter, MemoizedConverter):
    """
    メモ化機能を持つパラメータレベルから構造レベルへの変換クラス
    
    このクラスは、パラメータレベルの表現から構造レベルの表現への変換を行い、
    結果をキャッシュします。同じパラメータセットに対する変換を高速化します。
    """
    
    def __init__(self, structure_templates: Optional[Dict[str, Dict[str, Any]]] = None,
                 cache_size: int = 128, cache_stats: bool = False):
        """
        メモ化されたパラメータから構造への変換クラスを初期化します。
        
        引数:
            structure_templates: パラメータのパターンごとの構造テンプレート
            cache_size: キャッシュの最大サイズ
            cache_stats: キャッシュの統計情報を収集するかどうか
        """
        ParameterToStructureConverter.__init__(self, structure_templates)
        MemoizedConverter.__init__(self, cache_size, cache_stats)
        
        # 変換関数をメモ化関数に置き換える
        self._convert_impl_original = self._convert_impl
        self._convert_impl = self._memoize_function(self._convert_impl)
    
    def convert(self, param_level: ParameterLevel) -> StructureLevel:
        """
        パラメータレベルの表現を構造レベルの表現に変換します。
        
        引数:
            param_level: パラメータレベルの表現
            
        戻り値:
            StructureLevel: 変換された構造レベルの表現
            
        例外:
            ConversionError: 変換中にエラーが発生した場合
        """
        # 入力の検証
        self._validate_input(param_level)
        
        try:
            # パラメータの不変表現を作成
            param_tuples = tuple(sorted([
                (name, param.value_type, param.value, param.unit, 
                 param.min_value, param.max_value, 
                 tuple(sorted(param.metadata.items())) if param.metadata else tuple())
                for name, param in param_level.parameters.items()
            ]))
            
            # 不変表現を使用してメモ化メソッドを呼び出す
            result = self._convert_impl(
                param_tuples,
                param_level.source_intent
            )
            return result
        except Exception as e:
            if isinstance(e, ConversionError):
                raise
            else:
                raise ConversionError(
                    f"変換中にエラーが発生しました: {str(e)}", 
                    source_level=param_level.__class__.__name__,
                    original_exception=e
                )
    
    def _convert_impl(self, param_tuples: Tuple, source_intent: Optional[str]) -> StructureLevel:
        """
        パラメータレベルから構造レベルへの変換を実装します。
        このメソッドはメモ化されます。
        
        引数:
            param_tuples: パラメータの不変表現
            source_intent: パラメータレベルの元となった意図
            
        戻り値:
            StructureLevel: 変換された構造レベルの表現
        """
        # タプルからParameterLevelオブジェクトを再構築
        parameters = {}
        for param_tuple in param_tuples:
            name, value_type, value, unit, min_value, max_value, metadata_tuple = param_tuple
            metadata = dict(metadata_tuple) if metadata_tuple else {}
            parameters[name] = ParameterValue(value_type, value, unit, min_value, max_value, metadata)
        
        param_level = ParameterLevel(parameters, source_intent)
        
        # 元の変換処理を呼び出す
        return self._convert_impl_original(param_level)


class MemoizedStructureToCodeConverter(StructureToCodeConverter, MemoizedConverter):
    """
    メモ化機能を持つ構造レベルからコードレベルへの変換クラス
    
    このクラスは、構造レベルの表現からコードレベルの表現への変換を行い、
    結果をキャッシュします。同じ構造に対する変換を高速化します。
    """
    
    def __init__(self, code_templates: Optional[Dict[str, Dict[str, Any]]] = None,
                 cache_size: int = 128, cache_stats: bool = False):
        """
        メモ化された構造からコードへの変換クラスを初期化します。
        
        引数:
            code_templates: 構造タイプごとのコードテンプレート
            cache_size: キャッシュの最大サイズ
            cache_stats: キャッシュの統計情報を収集するかどうか
        """
        StructureToCodeConverter.__init__(self, code_templates)
        MemoizedConverter.__init__(self, cache_size, cache_stats)
        
        # 変換関数をメモ化関数に置き換える
        self._convert_impl_original = self._convert_impl
        self._convert_impl = self._memoize_function(self._convert_impl)
    
    def convert(self, structure: StructureLevel) -> CodeLevel:
        """
        構造レベルの表現をコードレベルの表現に変換します。
        
        引数:
            structure: 構造レベルの表現
            
        戻り値:
            CodeLevel: 変換されたコードレベルの表現
            
        例外:
            ConversionError: 変換中にエラーが発生した場合
        """
        # 入力の検証
        self._validate_input(structure)
        
        try:
            # 構造の不変表現を作成
            # 構造タイプ
            structure_type_name = structure.structure_type.name
            
            # コンポーネントをタプルに変換
            component_tuples = tuple(sorted([
                (name, comp.component_type, comp.name, self._make_hashable(comp.value), 
                 tuple(sorted(comp.metadata.items())) if comp.metadata else tuple())
                for name, comp in structure.components.items()
            ]))
            
            # 接続をタプルに変換
            connection_tuples = tuple(sorted(structure.connections))
            
            # ソースパラメータをタプルに変換
            source_param_tuples = tuple(sorted(structure.source_parameters))
            
            # メタデータをタプルに変換
            metadata_tuples = tuple(sorted([
                (key, self._make_hashable(value))
                for key, value in structure.metadata.items()
            ]))
            
            # 不変表現を使用してメモ化メソッドを呼び出す
            result = self._convert_impl(
                structure_type_name,
                component_tuples,
                connection_tuples,
                source_param_tuples,
                metadata_tuples
            )
            return result
        except Exception as e:
            if isinstance(e, ConversionError):
                raise
            else:
                raise ConversionError(
                    f"変換中にエラーが発生しました: {str(e)}", 
                    source_level=structure.__class__.__name__,
                    original_exception=e
                )
    
    def _make_hashable(self, value: Any) -> Any:
        """
        値をハッシュ可能なものに変換します。
        
        引数:
            value: 変換する値
            
        戻り値:
            Any: ハッシュ可能な値
        """
        if isinstance(value, dict):
            return tuple(sorted([
                (key, self._make_hashable(val))
                for key, val in value.items()
            ]))
        elif isinstance(value, list):
            return tuple(self._make_hashable(v) for v in value)
        elif isinstance(value, set):
            return tuple(sorted(self._make_hashable(v) for v in value))
        else:
            return value
    
    def _convert_impl(self, structure_type_name: str, component_tuples: Tuple,
                     connection_tuples: Tuple, source_param_tuples: Tuple,
                     metadata_tuples: Tuple) -> CodeLevel:
        """
        構造レベルからコードレベルへの変換を実装します。
        このメソッドはメモ化されます。
        
        引数:
            structure_type_name: 構造タイプ名
            component_tuples: コンポーネントの不変表現
            connection_tuples: 接続の不変表現
            source_param_tuples: ソースパラメータの不変表現
            metadata_tuples: メタデータの不変表現
            
        戻り値:
            CodeLevel: 変換されたコードレベルの表現
        """
        # タプルからStructureLevelオブジェクトを再構築
        try:
            structure_type = StructureType[structure_type_name]
        except (KeyError, TypeError):
            structure_type = StructureType.UNKNOWN
        
        # コンポーネントを再構築
        components = {}
        for comp_tuple in component_tuples:
            name, component_type, comp_name, value, metadata_tuple = comp_tuple
            metadata = dict(metadata_tuple) if metadata_tuple else {}
            components[name] = StructureComponent(component_type, comp_name, value, metadata)
        
        # 接続を再構築
        connections = list(connection_tuples)
        
        # ソースパラメータを再構築
        source_parameters = list(source_param_tuples)
        
        # メタデータを再構築
        metadata = {}
        for key, value in metadata_tuples:
            metadata[key] = value
        
        # StructureLevelオブジェクトを作成
        structure = StructureLevel(
            structure_type,
            components,
            connections,
            source_parameters,
            metadata
        )
        
        # 元の変換処理を呼び出す
        return self._convert_impl_original(structure)


# 最適化された変換パイプラインクラス
class OptimizedConversionPipeline:
    """
    最適化された表現レベル間の変換パイプライン
    
    このクラスは、意図レベルから最終的なコードレベルまでの変換を
    最適化された変換クラスを使用して行います。
    """
    
    def __init__(self, cache_size: int = 128, cache_stats: bool = False):
        """
        最適化された変換パイプラインを初期化します。
        
        引数:
            cache_size: 各変換器のキャッシュサイズ
            cache_stats: キャッシュの統計情報を収集するかどうか
        """
        self.intent_to_param = MemoizedIntentToParameterConverter(
            cache_size=cache_size,
            cache_stats=cache_stats
        )
        
        self.param_to_structure = MemoizedParameterToStructureConverter(
            cache_size=cache_size,
            cache_stats=cache_stats
        )
        
        self.structure_to_code = MemoizedStructureToCodeConverter(
            cache_size=cache_size,
            cache_stats=cache_stats
        )
    
    def convert_intent_to_code(self, intent: IntentLevel) -> CodeLevel:
        """
        意図レベルの表現を直接コードレベルの表現に変換します。
        
        引数:
            intent: 意図レベルの表現
            
        戻り値:
            CodeLevel: 変換されたコードレベルの表現
            
        例外:
            ConversionError: 変換中にエラーが発生した場合
        """
        # 意図 -> パラメータ
        param_level = self.intent_to_param.convert(intent)
        
        # パラメータ -> 構造
        structure = self.param_to_structure.convert(param_level)
        
        # 構造 -> コード
        code_level = self.structure_to_code.convert(structure)
        
        return code_level
    
    def get_cache_stats(self) -> Dict[str, Dict[str, Any]]:
        """
        全変換器のキャッシュ統計情報を返します。
        
        戻り値:
            Dict[str, Dict[str, Any]]: 各変換器のキャッシュ統計情報
        """
        return {
            "intent_to_param": self.intent_to_param.get_cache_stats(),
            "param_to_structure": self.param_to_structure.get_cache_stats(),
            "structure_to_code": self.structure_to_code.get_cache_stats()
        }
