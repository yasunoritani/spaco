#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
SPACO - 構造レベルの表現

このモジュールは、音響構造（シンセ定義、パターン、エフェクトチェーンなど）を
表現するクラスを提供します。
"""

from typing import Dict, Any, List, Optional, Set, Union, Tuple
import logging
from enum import Enum, auto

from .base import RepresentationLevel, ValidationError

logger = logging.getLogger(__name__)


class StructureType(Enum):
    """構造の種類を表す列挙型"""
    
    # 基本的な音源構造
    SYNTH_DEF = auto()  # シンセ定義
    FUNCTION = auto()  # 関数定義
    
    # パターン構造
    PATTERN = auto()  # シーケンスパターン
    PBIND = auto()  # 音列パターン
    
    # エフェクト構造
    EFFECT_CHAIN = auto()  # エフェクトチェーン
    EFFECT_NODE = auto()  # エフェクトノード
    
    # グラフ構造
    NODE_GRAPH = auto()  # ノードグラフ
    BUS = auto()  # バス接続
    
    # 制御構造
    ENVELOPE = auto()  # エンベロープ
    CONTROL_RATE = auto()  # 制御レート信号
    
    # 複合構造
    COMPOSITE = auto()  # 複合構造
    
    # その他
    CUSTOM = auto()  # カスタム構造
    UNKNOWN = auto()  # 不明な構造


class StructureComponent:
    """
    構造の構成要素を表現するクラス
    
    このクラスは、構造を構成する要素（シンセパラメータ、エフェクトパラメータなど）を表現します。
    """
    
    def __init__(self, component_type: str, name: str, 
                 value: Any, metadata: Optional[Dict[str, Any]] = None):
        """
        構造の構成要素を初期化します。
        
        引数:
            component_type: 構成要素の種類
            name: 構成要素の名前
            value: 構成要素の値
            metadata: 追加のメタデータ
        """
        self.component_type = component_type
        self.name = name
        self.value = value
        self.metadata = metadata or {}
    
    def validate(self) -> bool:
        """
        構造の構成要素が有効かどうかを検証します。
        
        戻り値:
            bool: 構造の構成要素が有効な場合はTrue、そうでない場合はFalse
            
        例外:
            ValidationError: 検証中にエラーが発生した場合
        """
        # 構成要素の種類が設定されているか
        if not isinstance(self.component_type, str) or not self.component_type:
            raise ValidationError("構成要素の種類が設定されていません", 
                                 field="component_type")
        
        # 名前が設定されているか
        if not isinstance(self.name, str) or not self.name:
            raise ValidationError("構成要素の名前が設定されていません", 
                                 field="name")
        
        # 値がNoneでないか
        if self.value is None:
            raise ValidationError("構成要素の値が設定されていません", 
                                 field="value")
            
        return True
    
    def to_dict(self) -> Dict[str, Any]:
        """
        構造の構成要素を辞書形式に変換します。
        
        戻り値:
            Dict[str, Any]: 構造の構成要素を表す辞書
        """
        result = {
            "component_type": self.component_type,
            "name": self.name,
            "value": self.value
        }
        
        if self.metadata:
            result["metadata"] = self.metadata
            
        return result
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'StructureComponent':
        """
        辞書から構造の構成要素を生成します。
        
        引数:
            data: 構造の構成要素を表す辞書
            
        戻り値:
            StructureComponent: 生成された構造の構成要素インスタンス
        """
        component_type = data.get("component_type", "unknown")
        name = data.get("name", "")
        value = data.get("value")
        metadata = data.get("metadata", {})
        
        return cls(component_type, name, value, metadata)


class StructureLevel(RepresentationLevel):
    """
    音響構造を表現するクラス
    
    このクラスは、音響合成の構造（シンセ定義、パターン、エフェクトチェーンなど）を表現します。
    パラメータレベルの表現から、より具体的なSuperColliderコードの構造を表現します。
    """
    
    def __init__(self, structure_type: StructureType, 
                 components: Optional[Dict[str, StructureComponent]] = None,
                 connections: Optional[List[Tuple[str, str]]] = None,
                 source_parameters: Optional[List[str]] = None,
                 metadata: Optional[Dict[str, Any]] = None):
        """
        構造レベルの表現を初期化します。
        
        引数:
            structure_type: 構造の種類
            components: 構造の構成要素
            connections: 構成要素間の接続関係（出力名、入力名）のリスト
            source_parameters: この構造の元となったパラメータのリスト
            metadata: 追加のメタデータ
        """
        super().__init__()
        self.structure_type = structure_type
        self.components = components or {}
        self.connections = connections or []
        self.source_parameters = source_parameters or []
        self.metadata = metadata or {}
    
    def validate(self) -> bool:
        """
        構造表現が有効かどうかを検証します。
        
        戻り値:
            bool: 構造表現が有効な場合はTrue、そうでない場合はFalse
            
        例外:
            ValidationError: 検証中にエラーが発生した場合
        """
        # 構造の種類が有効か
        if not isinstance(self.structure_type, StructureType):
            raise ValidationError("構造の種類が有効ではありません", 
                                 level="StructureLevel", field="structure_type")
        
        # 構造の構成要素が少なくとも1つ設定されているか
        if not self.components:
            # 一部の構造タイプは構成要素が不要な場合がある
            if self.structure_type not in [StructureType.CUSTOM, StructureType.UNKNOWN]:
                raise ValidationError("構造の構成要素が設定されていません", 
                                     level="StructureLevel", field="components")
        
        # 各構成要素を検証
        for comp_name, component in self.components.items():
            try:
                component.validate()
            except ValidationError as e:
                raise ValidationError(f"構成要素'{comp_name}'が無効です: {str(e)}", 
                                     level="StructureLevel", field=f"components.{comp_name}")
            
        # 接続の検証
        for output_name, input_name in self.connections:
            if output_name not in self.components:
                raise ValidationError(f"接続の出力'{output_name}'が存在しません", 
                                     level="StructureLevel", field="connections")
            if input_name not in self.components:
                raise ValidationError(f"接続の入力'{input_name}'が存在しません", 
                                     level="StructureLevel", field="connections")
            
        return True
    
    def to_dict(self) -> Dict[str, Any]:
        """
        構造表現を辞書形式に変換します。
        
        戻り値:
            Dict[str, Any]: 構造表現を表す辞書
        """
        components_dict = {name: comp.to_dict() for name, comp in self.components.items()}
        
        result = {
            "structure_type": self.structure_type.name,
            "components": components_dict,
            "connections": self.connections,
            "source_parameters": self.source_parameters
        }
        
        if self.metadata:
            result["metadata"] = self.metadata
            
        return result
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'StructureLevel':
        """
        辞書から構造表現を生成します。
        
        引数:
            data: 構造表現を表す辞書
            
        戻り値:
            StructureLevel: 生成された構造表現インスタンス
        """
        try:
            structure_type = StructureType[data.get("structure_type", "UNKNOWN")]
        except (KeyError, TypeError):
            structure_type = StructureType.UNKNOWN
            
        components_data = data.get("components", {})
        components = {
            name: StructureComponent.from_dict(comp_data)
            for name, comp_data in components_data.items()
        }
        
        connections = data.get("connections", [])
        source_parameters = data.get("source_parameters", [])
        metadata = data.get("metadata", {})
        
        return cls(structure_type, components, connections, source_parameters, metadata)
    
    def add_component(self, name: str, component: StructureComponent) -> None:
        """
        構成要素を追加します。
        
        引数:
            name: 構成要素の名前
            component: 構成要素
        """
        self.components[name] = component
        # 追加されたので検証状態をリセット
        self._is_valid = False
    
    def add_connection(self, output_name: str, input_name: str) -> None:
        """
        構成要素間の接続を追加します。
        
        引数:
            output_name: 出力側の構成要素名
            input_name: 入力側の構成要素名
        """
        self.connections.append((output_name, input_name))
        # 追加されたので検証状態をリセット
        self._is_valid = False
    
    def get_component(self, name: str) -> Optional[StructureComponent]:
        """
        指定した名前の構成要素を取得します。
        
        引数:
            name: 構成要素の名前
            
        戻り値:
            Optional[StructureComponent]: 該当する構成要素（存在しない場合はNone）
        """
        return self.components.get(name)
    
    def has_component(self, name: str) -> bool:
        """
        指定した名前の構成要素が存在するかどうかを返します。
        
        引数:
            name: 構成要素の名前
            
        戻り値:
            bool: 構成要素が存在する場合はTrue、そうでない場合はFalse
        """
        return name in self.components
    
    def get_component_names(self) -> Set[str]:
        """
        すべての構成要素名の集合を返します。
        
        戻り値:
            Set[str]: 構成要素名の集合
        """
        return set(self.components.keys())
    
    def get_connections_to(self, input_name: str) -> List[str]:
        """
        指定した入力に接続されている出力の一覧を返します。
        
        引数:
            input_name: 入力側の構成要素名
            
        戻り値:
            List[str]: 接続されている出力側の構成要素名のリスト
        """
        return [output for output, input_ in self.connections if input_ == input_name]
    
    def get_connections_from(self, output_name: str) -> List[str]:
        """
        指定した出力が接続されている入力の一覧を返します。
        
        引数:
            output_name: 出力側の構成要素名
            
        戻り値:
            List[str]: 接続されている入力側の構成要素名のリスト
        """
        return [input_ for output, input_ in self.connections if output == output_name]
