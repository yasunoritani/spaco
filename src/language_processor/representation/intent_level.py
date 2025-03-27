#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
SPACO - 意図レベルの表現

このモジュールは、指示の基本的な意図（音生成、エフェクト適用、シーケンス作成など）を
表現するクラスを提供します。
"""

from typing import Dict, Any, List, Optional, Set, Union, Tuple
import logging
from enum import Enum, auto

from .base import RepresentationLevel, ValidationError

logger = logging.getLogger(__name__)


class IntentType(Enum):
    """意図の種類を表す列挙型"""
    
    # 音生成関連
    GENERATE_SOUND = auto()  # 基本的な音生成
    GENERATE_INSTRUMENT = auto()  # 楽器音の生成
    GENERATE_EFFECT = auto()  # エフェクト音の生成
    GENERATE_AMBIENT = auto()  # 環境音の生成
    
    # 音楽要素関連
    CREATE_MELODY = auto()  # メロディの作成
    CREATE_CHORD = auto()  # コードの作成
    CREATE_RHYTHM = auto()  # リズムの作成
    CREATE_SEQUENCE = auto()  # シーケンスの作成
    
    # エフェクト処理関連
    APPLY_EFFECT = auto()  # エフェクトの適用
    MODIFY_SOUND = auto()  # 音の加工
    
    # 制御関連
    CONTROL_PLAYBACK = auto()  # 再生の制御
    ADJUST_PARAMETER = auto()  # パラメータの調整
    
    # その他
    UNKNOWN = auto()  # 不明な意図
    COMPLEX = auto()  # 複合的な意図


class IntentLevel(RepresentationLevel):
    """
    指示の基本的な意図を表現するクラス
    
    このクラスは、自然言語指示から抽出された基本的な意図を表現します。
    例えば、「440Hzの正弦波を生成して」という指示は、GENERATE_SOUNDという意図になります。
    """
    
    def __init__(self, intent_type: IntentType, description: str, 
                 metadata: Optional[Dict[str, Any]] = None,
                 confidence: float = 1.0):
        """
        意図レベルの表現を初期化します。
        
        引数:
            intent_type: 意図の種類
            description: 意図の詳細な説明
            metadata: 追加のメタデータ
            confidence: 意図抽出の確信度（0.0〜1.0）
        """
        super().__init__()
        self.intent_type = intent_type
        self.description = description
        self.metadata = metadata or {}
        self.confidence = confidence
    
    def validate(self) -> bool:
        """
        意図表現が有効かどうかを検証します。
        
        戻り値:
            bool: 意図表現が有効な場合はTrue、そうでない場合はFalse
            
        例外:
            ValidationError: 検証中にエラーが発生した場合
        """
        # 意図の種類が設定されているか
        if not isinstance(self.intent_type, IntentType):
            raise ValidationError("意図の種類が有効ではありません", 
                                 level="IntentLevel", field="intent_type")
        
        # 説明が設定されているか
        if not isinstance(self.description, str) or not self.description:
            raise ValidationError("意図の説明が設定されていません", 
                                 level="IntentLevel", field="description")
        
        # 確信度が0.0〜1.0の範囲内か
        if not isinstance(self.confidence, (int, float)) or not (0.0 <= self.confidence <= 1.0):
            raise ValidationError("確信度は0.0〜1.0の範囲で設定してください", 
                                 level="IntentLevel", field="confidence")
            
        return True
    
    def to_dict(self) -> Dict[str, Any]:
        """
        意図表現を辞書形式に変換します。
        
        戻り値:
            Dict[str, Any]: 意図表現を表す辞書
        """
        return {
            "intent_type": self.intent_type.name,
            "description": self.description,
            "metadata": self.metadata,
            "confidence": self.confidence
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'IntentLevel':
        """
        辞書から意図表現を生成します。
        
        引数:
            data: 意図表現を表す辞書
            
        戻り値:
            IntentLevel: 生成された意図表現インスタンス
            
        例外:
            ValueError: 辞書の内容が無効な場合
        """
        try:
            intent_type = IntentType[data.get("intent_type", "UNKNOWN")]
        except (KeyError, TypeError):
            intent_type = IntentType.UNKNOWN
            
        description = data.get("description", "")
        metadata = data.get("metadata", {})
        confidence = data.get("confidence", 1.0)
        
        return cls(intent_type, description, metadata, confidence)
    
    def get_related_parameters(self) -> Set[str]:
        """
        この意図に関連するパラメータの集合を返します。
        
        戻り値:
            Set[str]: 関連パラメータ名の集合
        """
        # 意図タイプに基づいて関連パラメータを決定
        if self.intent_type == IntentType.GENERATE_SOUND:
            return {"frequency", "amplitude", "waveform", "duration"}
        elif self.intent_type == IntentType.GENERATE_INSTRUMENT:
            return {"instrument_type", "note", "velocity", "duration"}
        elif self.intent_type == IntentType.APPLY_EFFECT:
            return {"effect_type", "mix", "depth", "input_sound"}
        elif self.intent_type == IntentType.CREATE_SEQUENCE:
            return {"pattern", "tempo", "instrument", "notes"}
        else:
            # その他の意図タイプに対するデフォルトパラメータ
            return {"frequency", "amplitude", "duration"}
