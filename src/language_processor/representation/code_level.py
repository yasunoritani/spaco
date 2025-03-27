#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
SPACO - コードレベルの表現

このモジュールは、SuperColliderの具体的なコード構造を表現するクラスを提供します。
"""

from typing import Dict, Any, List, Optional, Set, Union, Tuple
import logging
from enum import Enum, auto
import re

from .base import RepresentationLevel, ValidationError

logger = logging.getLogger(__name__)


class CodeType(Enum):
    """SuperColliderコードの種類を表す列挙型"""
    
    SYNTH = auto()  # シンセサイザーコード
    PATTERN = auto()  # パターンコード
    EFFECT = auto()  # エフェクトコード
    SEQUENCE = auto()  # シーケンスコード
    SYNTHDEF = auto()  # SynthDefコード
    CONTROL = auto()  # 制御コード
    ROUTINE = auto()  # ルーチンコード
    TASK = auto()  # タスクコード
    SERVER = auto()  # サーバー関連コード
    FUNCTION = auto()  # 関数コード
    COMPOSITE = auto()  # 複合コード
    CUSTOM = auto()  # カスタムコード
    UNKNOWN = auto()  # 不明なコード


class CodeVariable:
    """
    SuperColliderコード内の変数を表現するクラス
    
    このクラスは、コード内の変数（周波数、振幅、エンベロープなど）を表現します。
    """
    
    def __init__(self, name: str, value: Any, var_type: Optional[str] = None, 
                 is_literal: bool = False, metadata: Optional[Dict[str, Any]] = None):
        """
        コード変数を初期化します。
        
        引数:
            name: 変数名
            value: 変数の値
            var_type: 変数の型（"freq", "amp", "env"など）
            is_literal: リテラル値かどうか
            metadata: 追加のメタデータ
        """
        self.name = name
        self.value = value
        self.var_type = var_type
        self.is_literal = is_literal
        self.metadata = metadata or {}
    
    def to_code(self) -> str:
        """
        変数をSuperColliderコードとして返します。
        
        戻り値:
            str: SuperColliderコード
        """
        if self.is_literal:
            if isinstance(self.value, str):
                return f'"{self.value}"'
            elif isinstance(self.value, bool):
                return str(self.value).lower()
            else:
                return str(self.value)
        else:
            return self.name
    
    def to_dict(self) -> Dict[str, Any]:
        """
        変数を辞書形式に変換します。
        
        戻り値:
            Dict[str, Any]: 変数を表す辞書
        """
        result = {
            "name": self.name,
            "value": self.value,
            "is_literal": self.is_literal
        }
        
        if self.var_type:
            result["var_type"] = self.var_type
            
        if self.metadata:
            result["metadata"] = self.metadata
            
        return result
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'CodeVariable':
        """
        辞書から変数を生成します。
        
        引数:
            data: 変数を表す辞書
            
        戻り値:
            CodeVariable: 生成された変数インスタンス
        """
        name = data.get("name", "")
        value = data.get("value")
        var_type = data.get("var_type")
        is_literal = data.get("is_literal", False)
        metadata = data.get("metadata", {})
        
        return cls(name, value, var_type, is_literal, metadata)
    
    @staticmethod
    def create_literal(value: Any, var_type: Optional[str] = None) -> 'CodeVariable':
        """
        リテラル値の変数を作成するユーティリティメソッド
        
        引数:
            value: リテラル値
            var_type: 変数の型（オプション）
            
        戻り値:
            CodeVariable: 作成された変数インスタンス
        """
        return CodeVariable("", value, var_type, True)


class CodeLevel(RepresentationLevel):
    """
    SuperColliderコードを表現するクラス
    
    このクラスは、最終的なSuperColliderコードのテンプレートと変数を表現します。
    構造レベルの表現から、実行可能なSuperColliderコードを生成するための表現です。
    """
    
    def __init__(self, code_type: CodeType, template: str, 
                 variables: Optional[Dict[str, CodeVariable]] = None,
                 source_structure: Optional[str] = None,
                 metadata: Optional[Dict[str, Any]] = None):
        """
        コードレベルの表現を初期化します。
        
        引数:
            code_type: コードの種類
            template: コードテンプレート（変数のプレースホルダを含む）
            variables: 変数名と変数のマッピング
            source_structure: このコードの元となった構造
            metadata: 追加のメタデータ
        """
        super().__init__()
        self.code_type = code_type
        self.template = template
        self.variables = variables or {}
        self.source_structure = source_structure
        self.metadata = metadata or {}
    
    def validate(self) -> bool:
        """
        コード表現が有効かどうかを検証します。
        
        戻り値:
            bool: コード表現が有効な場合はTrue、そうでない場合はFalse
            
        例外:
            ValidationError: 検証中にエラーが発生した場合
        """
        # コードの種類が有効か
        if not isinstance(self.code_type, CodeType):
            raise ValidationError("コードの種類が有効ではありません", 
                                 level="CodeLevel", field="code_type")
        
        # テンプレートが設定されているか
        if not isinstance(self.template, str) or not self.template:
            raise ValidationError("コードテンプレートが設定されていません", 
                                 level="CodeLevel", field="template")
            
        # テンプレート内のプレースホルダがすべて変数として定義されているか
        placeholders = set(re.findall(r'\{(\w+)\}', self.template))
        missing_vars = placeholders - set(self.variables.keys())
        if missing_vars:
            raise ValidationError(f"テンプレート内のプレースホルダ{list(missing_vars)}に対応する変数が定義されていません", 
                                 level="CodeLevel", field="variables")
            
        return True
    
    def to_dict(self) -> Dict[str, Any]:
        """
        コード表現を辞書形式に変換します。
        
        戻り値:
            Dict[str, Any]: コード表現を表す辞書
        """
        variables_dict = {name: var.to_dict() for name, var in self.variables.items()}
        
        result = {
            "code_type": self.code_type.name,
            "template": self.template,
            "variables": variables_dict
        }
        
        if self.source_structure:
            result["source_structure"] = self.source_structure
            
        if self.metadata:
            result["metadata"] = self.metadata
            
        return result
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'CodeLevel':
        """
        辞書からコード表現を生成します。
        
        引数:
            data: コード表現を表す辞書
            
        戻り値:
            CodeLevel: 生成されたコード表現インスタンス
        """
        try:
            code_type = CodeType[data.get("code_type", "UNKNOWN")]
        except (KeyError, TypeError):
            code_type = CodeType.UNKNOWN
            
        template = data.get("template", "")
        
        variables_data = data.get("variables", {})
        variables = {
            name: CodeVariable.from_dict(var_data)
            for name, var_data in variables_data.items()
        }
        
        source_structure = data.get("source_structure")
        metadata = data.get("metadata", {})
        
        return cls(code_type, template, variables, source_structure, metadata)
    
    def add_variable(self, name: str, variable: CodeVariable) -> None:
        """
        変数を追加します。
        
        引数:
            name: 変数名
            variable: 変数
        """
        self.variables[name] = variable
        # 追加されたので検証状態をリセット
        self._is_valid = False
    
    def get_variable(self, name: str) -> Optional[CodeVariable]:
        """
        指定した名前の変数を取得します。
        
        引数:
            name: 変数名
            
        戻り値:
            Optional[CodeVariable]: 該当する変数（存在しない場合はNone）
        """
        return self.variables.get(name)
    
    def has_variable(self, name: str) -> bool:
        """
        指定した名前の変数が存在するかどうかを返します。
        
        引数:
            name: 変数名
            
        戻り値:
            bool: 変数が存在する場合はTrue、そうでない場合はFalse
        """
        return name in self.variables
    
    def get_variable_names(self) -> Set[str]:
        """
        すべての変数名の集合を返します。
        
        戻り値:
            Set[str]: 変数名の集合
        """
        return set(self.variables.keys())
    
    def to_code(self) -> str:
        """
        表現をSuperColliderコードとして返します。
        
        戻り値:
            str: SuperColliderコード
            
        例外:
            ValidationError: コード生成中にエラーが発生した場合
        """
        if not self.is_valid():
            raise ValidationError("無効なコード表現からコードを生成することはできません", 
                                 level="CodeLevel")
            
        # テンプレート内のプレースホルダを変数の値で置換
        result = self.template
        for name, variable in self.variables.items():
            placeholder = "{" + name + "}"
            code_value = variable.to_code()
            result = result.replace(placeholder, code_value)
            
        return result
        
    def generate_code(self) -> str:
        """
        表現をSuperColliderコードとして返します。to_code メソッドの別名です。
        
        戻り値:
            str: SuperColliderコード
            
        例外:
            ValidationError: コード生成中にエラーが発生した場合
        """
        return self.to_code()
    
    @staticmethod
    def create_sine_wave_code(freq: float, amp: float, duration: float) -> 'CodeLevel':
        """
        正弦波コードを作成するユーティリティメソッド
        
        引数:
            freq: 周波数（Hz）
            amp: 振幅（0.0〜1.0）
            duration: 持続時間（秒）
            
        戻り値:
            CodeLevel: 作成されたコードレベル表現
        """
        template = """
s.waitForBoot({
    {
        // {freq}Hzの正弦波オシレーターを生成
        var sig = SinOsc.ar({freq}, 0, {amp});
        // エンベロープを適用してクリックノイズを防止
        sig = sig * EnvGen.kr(Env.linen(0.01, {duration}, 0.01), doneAction: 2);
        sig ! 2 // ステレオ出力
    }.play;
});
"""
        
        variables = {
            "freq": CodeVariable("freq", freq, "freq", True),
            "amp": CodeVariable("amp", amp, "amp", True),
            "duration": CodeVariable("duration", duration, "duration", True)
        }
        
        return CodeLevel(CodeType.SYNTH, template, variables)
    
    @staticmethod
    def create_saw_wave_code(freq: float, amp: float, duration: float) -> 'CodeLevel':
        """
        ノコギリ波コードを作成するユーティリティメソッド
        
        引数:
            freq: 周波数（Hz）
            amp: 振幅（0.0〜1.0）
            duration: 持続時間（秒）
            
        戻り値:
            CodeLevel: 作成されたコードレベル表現
        """
        template = """
s.waitForBoot({
    {
        // {freq}Hzのノコギリ波を生成
        var sig = Saw.ar({freq}, {amp});
        // エンベロープを適用
        sig = sig * EnvGen.kr(Env.linen(0.01, {duration}, 0.01), doneAction: 2);
        sig ! 2 // ステレオ出力
    }.play;
});
"""
        
        variables = {
            "freq": CodeVariable("freq", freq, "freq", True),
            "amp": CodeVariable("amp", amp, "amp", True),
            "duration": CodeVariable("duration", duration, "duration", True)
        }
        
        return CodeLevel(CodeType.SYNTH, template, variables)
    
    @staticmethod
    def create_pad_sound_code(freq: float, amp: float) -> 'CodeLevel':
        """
        パッドサウンドコードを作成するユーティリティメソッド
        
        引数:
            freq: 周波数（Hz）
            amp: 振幅（0.0〜1.0）
            
        戻り値:
            CodeLevel: 作成されたコードレベル表現
        """
        template = """
s.waitForBoot({
    {
        // デチューンした複数の正弦波を使用
        var sig = SinOsc.ar([{freq}, {freq}*1.005], 0, {amp}) + SinOsc.ar([{freq}*0.5, {freq}*0.501], 0, {amp}*0.5);
        // ローパスフィルターで高周波を削減
        sig = LPF.ar(sig, 1000);
        // ADSRエンベロープで緩やかな立ち上がりと減衰を実現
        sig = sig * EnvGen.kr(Env.adsr(1, 0.2, 0.7, 2), 1, doneAction: 2);
        sig
    }.play;
});
"""
        
        variables = {
            "freq": CodeVariable("freq", freq, "freq", True),
            "amp": CodeVariable("amp", amp, "amp", True)
        }
        
        return CodeLevel(CodeType.SYNTH, template, variables)
