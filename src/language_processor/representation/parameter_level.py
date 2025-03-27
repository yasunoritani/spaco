#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
SPACO - パラメータレベルの表現

このモジュールは、音響パラメータ（周波数、振幅、エンベロープなど）を
表現するクラスを提供します。
"""

from typing import Dict, Any, List, Optional, Set, Union, Tuple
import logging
from enum import Enum, auto

from .base import RepresentationLevel, ValidationError

logger = logging.getLogger(__name__)


class ParameterType(Enum):
    """パラメータの種類を表す列挙型"""
    
    # 基本パラメータ
    FREQUENCY = auto()  # 周波数
    AMPLITUDE = auto()  # 振幅
    DURATION = auto()  # 持続時間
    
    # 波形関連
    WAVEFORM = auto()  # 波形の種類
    PHASE = auto()  # 位相
    
    # エンベロープ関連
    ATTACK = auto()  # アタック時間
    DECAY = auto()  # ディケイ時間
    SUSTAIN = auto()  # サステインレベル
    RELEASE = auto()  # リリース時間
    
    # 変調関連
    MODULATION_TYPE = auto()  # 変調の種類
    MODULATION_RATE = auto()  # 変調の速度
    MODULATION_DEPTH = auto()  # 変調の深さ
    
    # フィルター関連
    FILTER_TYPE = auto()  # フィルターの種類
    CUTOFF_FREQUENCY = auto()  # カットオフ周波数
    RESONANCE = auto()  # レゾナンス
    
    # エフェクト関連
    EFFECT_TYPE = auto()  # エフェクトの種類
    MIX = auto()  # ミックス（ドライ/ウェット）
    FEEDBACK = auto()  # フィードバック
    
    # 空間関連
    PAN = auto()  # パンニング
    REVERB_SIZE = auto()  # リバーブサイズ
    DELAY_TIME = auto()  # ディレイタイム
    
    # 音楽関連
    NOTE = auto()  # 音符
    SCALE = auto()  # スケール
    CHORD = auto()  # コード
    TEMPO = auto()  # テンポ
    
    # その他
    CUSTOM = auto()  # カスタムパラメータ
    UNKNOWN = auto()  # 不明なパラメータ


class ParameterValue:
    """
    パラメータの値を表現するクラス
    
    このクラスは、静的な値、範囲、変動値など、様々なタイプのパラメータ値を表現します。
    """
    
    def __init__(self, value_type: str, value: Any, unit: Optional[str] = None, 
                 min_value: Optional[float] = None, max_value: Optional[float] = None,
                 metadata: Optional[Dict[str, Any]] = None):
        """
        パラメータ値を初期化します。
        
        引数:
            value_type: 値の種類（"static", "range", "dynamic", "envelope", "sequence"など）
            value: パラメータの値
            unit: 値の単位（"Hz", "s", "dB"など）
            min_value: 値の最小値（範囲や変動値の場合）
            max_value: 値の最大値（範囲や変動値の場合）
            metadata: 追加のメタデータ
        """
        self.value_type = value_type
        self.value = value
        self.unit = unit
        self.min_value = min_value
        self.max_value = max_value
        self.metadata = metadata or {}
    
    def validate(self) -> bool:
        """
        パラメータ値が有効かどうかを検証します。
        
        戻り値:
            bool: パラメータ値が有効な場合はTrue、そうでない場合はFalse
            
        例外:
            ValidationError: 検証中にエラーが発生した場合
        """
        # 値の種類が設定されているか
        if not isinstance(self.value_type, str) or not self.value_type:
            raise ValidationError("値の種類が設定されていません", 
                                 field="value_type")
        
        # 値がNoneでないか
        if self.value is None:
            raise ValidationError("値が設定されていません", 
                                 field="value")
        
        # 範囲の場合、最小値と最大値が設定されているか
        if self.value_type == "range":
            if self.min_value is None or self.max_value is None:
                raise ValidationError("範囲値の場合、最小値と最大値を設定してください", 
                                     field="min_value/max_value")
            if self.min_value > self.max_value:
                raise ValidationError("最小値は最大値以下である必要があります", 
                                     field="min_value/max_value")
        
        return True
    
    def to_dict(self) -> Dict[str, Any]:
        """
        パラメータ値を辞書形式に変換します。
        
        戻り値:
            Dict[str, Any]: パラメータ値を表す辞書
        """
        result = {
            "value_type": self.value_type,
            "value": self.value,
        }
        
        if self.unit:
            result["unit"] = self.unit
            
        if self.min_value is not None:
            result["min_value"] = self.min_value
            
        if self.max_value is not None:
            result["max_value"] = self.max_value
            
        if self.metadata:
            result["metadata"] = self.metadata
            
        return result
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ParameterValue':
        """
        辞書からパラメータ値を生成します。
        
        引数:
            data: パラメータ値を表す辞書
            
        戻り値:
            ParameterValue: 生成されたパラメータ値インスタンス
        """
        value_type = data.get("value_type", "static")
        value = data.get("value")
        unit = data.get("unit")
        min_value = data.get("min_value")
        max_value = data.get("max_value")
        metadata = data.get("metadata", {})
        
        return cls(value_type, value, unit, min_value, max_value, metadata)
    
    def __str__(self) -> str:
        """パラメータ値の文字列表現を返します。"""
        if self.value_type == "static":
            result = f"{self.value}"
            if self.unit:
                result += f" {self.unit}"
        elif self.value_type == "range":
            result = f"{self.min_value}-{self.max_value}"
            if self.unit:
                result += f" {self.unit}"
        elif self.value_type == "dynamic":
            result = f"{self.value} (dynamic)"
            if self.unit:
                result += f" {self.unit}"
        else:
            result = str(self.value)
        
        return result


class ParameterLevel(RepresentationLevel):
    """
    音響パラメータを表現するクラス
    
    このクラスは、自然言語指示から抽出された音響パラメータを表現します。
    例えば、「440Hzの正弦波を生成して」という指示からは、周波数=440Hz、波形=正弦波というパラメータが抽出されます。
    """
    
    def __init__(self, parameters: Optional[Dict[str, ParameterValue]] = None,
                 source_intent: Optional[str] = None):
        """
        パラメータレベルの表現を初期化します。
        
        引数:
            parameters: パラメータ名と値のマッピング
            source_intent: このパラメータセットの元となった意図
        """
        super().__init__()
        self.parameters = parameters or {}
        self.source_intent = source_intent
    
    def validate(self) -> bool:
        """
        パラメータ表現が有効かどうかを検証します。
        
        戻り値:
            bool: パラメータ表現が有効な場合はTrue、そうでない場合はFalse
            
        例外:
            ValidationError: 検証中にエラーが発生した場合
        """
        # パラメータが少なくとも1つ設定されているか
        if not self.parameters:
            raise ValidationError("パラメータが設定されていません", 
                                 level="ParameterLevel", field="parameters")
        
        # 各パラメータ値を検証
        for param_name, param_value in self.parameters.items():
            try:
                param_value.validate()
            except ValidationError as e:
                raise ValidationError(f"パラメータ'{param_name}'の値が無効です: {str(e)}", 
                                     level="ParameterLevel", field=f"parameters.{param_name}")
            
        return True
    
    def to_dict(self) -> Dict[str, Any]:
        """
        パラメータ表現を辞書形式に変換します。
        
        戻り値:
            Dict[str, Any]: パラメータ表現を表す辞書
        """
        params_dict = {name: value.to_dict() for name, value in self.parameters.items()}
        result = {"parameters": params_dict}
        
        if self.source_intent:
            result["source_intent"] = self.source_intent
            
        return result
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ParameterLevel':
        """
        辞書からパラメータ表現を生成します。
        
        引数:
            data: パラメータ表現を表す辞書
            
        戻り値:
            ParameterLevel: 生成されたパラメータ表現インスタンス
        """
        parameters_data = data.get("parameters", {})
        parameters = {
            name: ParameterValue.from_dict(value_data)
            for name, value_data in parameters_data.items()
        }
        
        source_intent = data.get("source_intent")
        
        return cls(parameters, source_intent)
    
    def add_parameter(self, name: str, value: ParameterValue) -> None:
        """
        パラメータを追加します。
        
        引数:
            name: パラメータ名
            value: パラメータ値
        """
        self.parameters[name] = value
        # 追加されたので検証状態をリセット
        self._is_valid = False
    
    def get_parameter(self, name: str) -> Optional[ParameterValue]:
        """
        指定した名前のパラメータを取得します。
        
        引数:
            name: パラメータ名
            
        戻り値:
            Optional[ParameterValue]: 該当するパラメータ値（存在しない場合はNone）
        """
        return self.parameters.get(name)
    
    def has_parameter(self, name: str) -> bool:
        """
        指定した名前のパラメータが存在するかどうかを返します。
        
        引数:
            name: パラメータ名
            
        戻り値:
            bool: パラメータが存在する場合はTrue、そうでない場合はFalse
        """
        return name in self.parameters
    
    def get_parameter_names(self) -> Set[str]:
        """
        すべてのパラメータ名の集合を返します。
        
        戻り値:
            Set[str]: パラメータ名の集合
        """
        return set(self.parameters.keys())
    
    def missing_parameters(self, required_params: Set[str]) -> Set[str]:
        """
        必要なパラメータのうち、不足しているものを返します。
        
        引数:
            required_params: 必要なパラメータ名の集合
            
        戻り値:
            Set[str]: 不足しているパラメータ名の集合
        """
        return required_params - self.get_parameter_names()
    
    def set_default_parameters(self, defaults: Dict[str, ParameterValue]) -> None:
        """
        不足しているパラメータにデフォルト値を設定します。
        既に存在するパラメータは上書きされません。
        
        引数:
            defaults: パラメータ名とデフォルト値のマッピング
        """
        for name, value in defaults.items():
            if name not in self.parameters:
                self.parameters[name] = value
        
        # デフォルト値が追加されたので検証状態をリセット
        self._is_valid = False
    
    @staticmethod
    def create_frequency_parameter(frequency: float) -> ParameterValue:
        """
        周波数パラメータを作成するユーティリティメソッド
        
        引数:
            frequency: 周波数の値（Hz）
            
        戻り値:
            ParameterValue: 作成されたパラメータ値
        """
        return ParameterValue("static", frequency, "Hz")
    
    @staticmethod
    def create_amplitude_parameter(amplitude: float) -> ParameterValue:
        """
        振幅パラメータを作成するユーティリティメソッド
        
        引数:
            amplitude: 振幅の値（0.0〜1.0）
            
        戻り値:
            ParameterValue: 作成されたパラメータ値
        """
        return ParameterValue("static", amplitude, None, 0.0, 1.0)
    
    @staticmethod
    def create_duration_parameter(duration: float) -> ParameterValue:
        """
        持続時間パラメータを作成するユーティリティメソッド
        
        引数:
            duration: 持続時間の値（秒）
            
        戻り値:
            ParameterValue: 作成されたパラメータ値
        """
        return ParameterValue("static", duration, "s", 0.0, None)
    
    @staticmethod
    def create_waveform_parameter(waveform: str) -> ParameterValue:
        """
        波形パラメータを作成するユーティリティメソッド
        
        引数:
            waveform: 波形の種類（"sine", "saw", "square", "triangle"など）
            
        戻り値:
            ParameterValue: 作成されたパラメータ値
        """
        return ParameterValue("static", waveform)
    
    @staticmethod
    def create_envelope_parameter(attack: float, decay: float, 
                                sustain: float, release: float) -> ParameterValue:
        """
        エンベロープパラメータを作成するユーティリティメソッド
        
        引数:
            attack: アタック時間（秒）
            decay: ディケイ時間（秒）
            sustain: サステインレベル（0.0〜1.0）
            release: リリース時間（秒）
            
        戻り値:
            ParameterValue: 作成されたパラメータ値
        """
        envelope_data = {
            "attack": attack,
            "decay": decay,
            "sustain": sustain,
            "release": release
        }
        return ParameterValue("envelope", envelope_data)
