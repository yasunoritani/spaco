#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
SPACO - 表現レベル間の変換

このモジュールは、異なる表現レベル（意図、パラメータ、構造、コード）間の
変換を行うクラスを提供します。
"""

from typing import Dict, Any, List, Optional, Set, Union, Tuple
import logging
import re

from .base import ValidationError
from .intent_level import IntentLevel, IntentType
from .parameter_level import ParameterLevel, ParameterValue, ParameterType
from .structure_level import StructureLevel, StructureComponent, StructureType
from .code_level import CodeLevel, CodeVariable, CodeType

logger = logging.getLogger(__name__)


class ConversionError(Exception):
    """表現レベル間の変換に失敗した場合に発生する例外"""
    def __init__(self, message, source_level=None, target_level=None, original_exception=None):
        super().__init__(message)
        self.source_level = source_level
        self.target_level = target_level
        self.original_exception = original_exception


class BaseConverter:
    """
    表現レベル間の変換の基底クラス
    
    このクラスは、表現レベル間の変換の基本的な機能を提供します。
    各変換クラスは、このクラスを継承します。
    """
    
    def __init__(self):
        """変換クラスを初期化します。"""
        pass
    
    def _validate_input(self, input_representation):
        """入力の表現が有効かどうかを検証します。"""
        if not input_representation.is_valid():
            raise ConversionError("入力の表現が無効です", 
                                 source_level=input_representation.__class__.__name__)
    
    def convert(self, input_representation):
        """
        入力の表現を変換します。
        
        引数:
            input_representation: 入力の表現
            
        戻り値:
            変換された表現
            
        例外:
            ConversionError: 変換中にエラーが発生した場合
        """
        # 入力の検証
        self._validate_input(input_representation)
        
        # サブクラスで実装される変換処理
        try:
            return self._convert_impl(input_representation)
        except Exception as e:
            if isinstance(e, ConversionError):
                raise
            else:
                raise ConversionError(
                    f"変換中にエラーが発生しました: {str(e)}", 
                    source_level=input_representation.__class__.__name__,
                    original_exception=e
                )
    
    def _convert_impl(self, input_representation):
        """
        実際の変換処理を行います。
        このメソッドは、サブクラスで実装する必要があります。
        """
        raise NotImplementedError("サブクラスで実装する必要があります")


class IntentToParameterConverter(BaseConverter):
    """
    意図レベルからパラメータレベルへの変換を行うクラス
    
    このクラスは、意図レベルの表現からパラメータレベルの表現への変換を行います。
    """
    
    def __init__(self, default_parameters: Optional[Dict[str, Dict[str, Any]]] = None):
        """
        意図からパラメータへの変換クラスを初期化します。
        
        引数:
            default_parameters: 意図タイプごとのデフォルトパラメータ
        """
        super().__init__()
        self.default_parameters = default_parameters or {
            IntentType.GENERATE_SOUND: {
                "frequency": {"value": 440.0, "unit": "Hz"},
                "amplitude": {"value": 0.5},
                "duration": {"value": 1.0, "unit": "s"}
            },
            IntentType.GENERATE_INSTRUMENT: {
                "instrument_type": {"value": "piano"},
                "note": {"value": "A4"},
                "velocity": {"value": 0.7},
                "duration": {"value": 1.0, "unit": "s"}
            },
            IntentType.APPLY_EFFECT: {
                "effect_type": {"value": "reverb"},
                "mix": {"value": 0.5},
                "depth": {"value": 0.5}
            }
            # 他の意図タイプのデフォルトパラメータも追加可能
        }
    
    def _convert_impl(self, intent: IntentLevel) -> ParameterLevel:
        """
        意図レベルからパラメータレベルへの変換を実装します。
        
        引数:
            intent: 意図レベルの表現
            
        戻り値:
            ParameterLevel: 変換されたパラメータレベルの表現
        """
        # メタデータから既存のパラメータを取得
        existing_params = {}
        if "extracted_parameters" in intent.metadata:
            for param_name, param_data in intent.metadata["extracted_parameters"].items():
                param_value = ParameterValue(
                    param_data.get("value_type", "static"),
                    param_data.get("value"),
                    param_data.get("unit"),
                    param_data.get("min_value"),
                    param_data.get("max_value"),
                    param_data.get("metadata", {})
                )
                existing_params[param_name] = param_value
        
        # 意図タイプに基づいてデフォルトパラメータを設定
        param_level = ParameterLevel(existing_params, intent.intent_type.name)
        
        # 意図タイプに対応するデフォルトパラメータを取得
        default_params = self.default_parameters.get(intent.intent_type, {})
        
        # デフォルトパラメータから不足しているパラメータを追加
        for param_name, param_data in default_params.items():
            if param_name not in param_level.parameters:
                param_value = ParameterValue(
                    param_data.get("value_type", "static"),
                    param_data.get("value"),
                    param_data.get("unit"),
                    param_data.get("min_value"),
                    param_data.get("max_value"),
                    param_data.get("metadata", {})
                )
                param_level.add_parameter(param_name, param_value)
        
        # 波形タイプのパラメータがない場合は、意図タイプに基づいて設定
        if "waveform" not in param_level.parameters and intent.intent_type == IntentType.GENERATE_SOUND:
            # 波形のデフォルト値を決定（意図の説明から推測）
            waveform = "sine"  # デフォルト
            if "sine" in intent.description.lower() or "正弦波" in intent.description:
                waveform = "sine"
            elif "saw" in intent.description.lower() or "ノコギリ波" in intent.description:
                waveform = "saw"
            elif "square" in intent.description.lower() or "矩形波" in intent.description:
                waveform = "square"
            elif "triangle" in intent.description.lower() or "三角波" in intent.description:
                waveform = "triangle"
                
            param_level.add_parameter("waveform", ParameterValue("static", waveform))
        
        return param_level


class ParameterToStructureConverter(BaseConverter):
    """
    パラメータレベルから構造レベルへの変換を行うクラス
    
    このクラスは、パラメータレベルの表現から構造レベルの表現への変換を行います。
    """
    
    def __init__(self, structure_templates: Optional[Dict[str, Dict[str, Any]]] = None):
        """
        パラメータから構造への変換クラスを初期化します。
        
        引数:
            structure_templates: パラメータのパターンごとの構造テンプレート
        """
        super().__init__()
        self.structure_templates = structure_templates or {
            "basic_sine": {
                "structure_type": StructureType.SYNTH_DEF,
                "required_params": {"frequency", "amplitude", "duration"},
                "optional_params": {"phase"},
                "waveform": "sine"
            },
            "basic_saw": {
                "structure_type": StructureType.SYNTH_DEF,
                "required_params": {"frequency", "amplitude", "duration"},
                "optional_params": {"phase"},
                "waveform": "saw"
            },
            "pad_sound": {
                "structure_type": StructureType.SYNTH_DEF,
                "required_params": {"frequency", "amplitude"},
                "optional_params": {"attack", "decay", "sustain", "release"},
                "waveform": "pad"
            },
            "effect_reverb": {
                "structure_type": StructureType.EFFECT_CHAIN,
                "required_params": {"mix", "room"},
                "optional_params": {"damp", "input_sound"},
                "effect_type": "reverb"
            }
            # 他の構造テンプレートも追加可能
        }
    
    def _select_template(self, parameters: ParameterLevel) -> Tuple[str, Dict[str, Any]]:
        """
        パラメータに最も適合する構造テンプレートを選択します。
        
        引数:
            parameters: パラメータレベルの表現
            
        戻り値:
            Tuple[str, Dict[str, Any]]: テンプレート名とテンプレート辞書のタプル
        """
        best_match = None
        best_score = -1
        best_template_name = None
        
        param_names = parameters.get_parameter_names()
        
        for template_name, template in self.structure_templates.items():
            # 必須パラメータがすべて存在するか確認
            required_params = template.get("required_params", set())
            if not required_params.issubset(param_names):
                continue
                
            # 波形パラメータが一致するか確認
            if "waveform" in template and parameters.has_parameter("waveform"):
                if parameters.get_parameter("waveform").value != template["waveform"]:
                    continue
                    
            # エフェクトタイプが一致するか確認
            if "effect_type" in template and parameters.has_parameter("effect_type"):
                if parameters.get_parameter("effect_type").value != template["effect_type"]:
                    continue
            
            # スコアを計算（必須パラメータ + オプションパラメータの一致数）
            optional_params = template.get("optional_params", set())
            score = len(required_params) + len(optional_params.intersection(param_names))
            
            if score > best_score:
                best_score = score
                best_match = template
                best_template_name = template_name
        
        return best_template_name, best_match
    
    def _convert_impl(self, parameters: ParameterLevel) -> StructureLevel:
        """
        パラメータレベルから構造レベルへの変換を実装します。
        
        引数:
            parameters: パラメータレベルの表現
            
        戻り値:
            StructureLevel: 変換された構造レベルの表現
        """
        # パラメータから適切な構造テンプレートを選択
        template_name, template = self._select_template(parameters)
        
        if not template:
            raise ConversionError("適切な構造テンプレートが見つかりませんでした",
                                 source_level="ParameterLevel",
                                 target_level="StructureLevel")
        
        # 構造タイプを取得
        structure_type = template["structure_type"]
        
        # 構造の構成要素を作成
        components = {}
        
        # 基本的な音源構造の場合
        if structure_type == StructureType.SYNTH_DEF:
            # オシレーター構成要素
            if "frequency" in parameters.parameters:
                freq_param = parameters.get_parameter("frequency")
                components["oscillator"] = StructureComponent(
                    "oscillator",
                    "oscillator",
                    {
                        "type": parameters.get_parameter("waveform").value if parameters.has_parameter("waveform") else "sine",
                        "frequency": freq_param.value,
                        "unit": freq_param.unit
                    }
                )
            
            # エンベロープ構成要素
            env_params = {}
            if parameters.has_parameter("attack"):
                env_params["attack"] = parameters.get_parameter("attack").value
            if parameters.has_parameter("decay"):
                env_params["decay"] = parameters.get_parameter("decay").value
            if parameters.has_parameter("sustain"):
                env_params["sustain"] = parameters.get_parameter("sustain").value
            if parameters.has_parameter("release"):
                env_params["release"] = parameters.get_parameter("release").value
                
            if env_params:
                components["envelope"] = StructureComponent(
                    "envelope",
                    "envelope",
                    env_params
                )
            elif parameters.has_parameter("duration"):
                # 持続時間からエンベロープを作成
                dur_param = parameters.get_parameter("duration")
                components["envelope"] = StructureComponent(
                    "envelope",
                    "envelope",
                    {
                        "type": "linen",
                        "attack": 0.01,
                        "sustain": dur_param.value - 0.02 if dur_param.value > 0.02 else 0.01,
                        "release": 0.01
                    }
                )
            
            # 振幅構成要素
            if parameters.has_parameter("amplitude"):
                amp_param = parameters.get_parameter("amplitude")
                components["amplitude"] = StructureComponent(
                    "amplitude",
                    "amplitude",
                    {
                        "value": amp_param.value
                    }
                )
            
            # 出力構成要素
            components["output"] = StructureComponent(
                "output",
                "output",
                {
                    "channels": 2,
                    "doneAction": 2
                }
            )
        
        # エフェクト構造の場合
        elif structure_type == StructureType.EFFECT_CHAIN:
            # エフェクト構成要素
            effect_type = parameters.get_parameter("effect_type").value if parameters.has_parameter("effect_type") else "reverb"
            effect_params = {}
            
            if effect_type == "reverb":
                if parameters.has_parameter("mix"):
                    effect_params["mix"] = parameters.get_parameter("mix").value
                if parameters.has_parameter("room"):
                    effect_params["room"] = parameters.get_parameter("room").value
                if parameters.has_parameter("damp"):
                    effect_params["damp"] = parameters.get_parameter("damp").value
            
            components["effect"] = StructureComponent(
                "effect",
                "effect",
                {
                    "type": effect_type,
                    "parameters": effect_params
                }
            )
            
            # 入力構成要素
            if parameters.has_parameter("input_sound"):
                components["input"] = StructureComponent(
                    "input",
                    "input",
                    {
                        "sound": parameters.get_parameter("input_sound").value
                    }
                )
            
            # 出力構成要素
            components["output"] = StructureComponent(
                "output",
                "output",
                {
                    "channels": 2
                }
            )
        
        # 構造レベルの表現を作成
        structure = StructureLevel(
            structure_type,
            components,
            [],  # 接続を追加
            [param for param in parameters.get_parameter_names()],  # ソースパラメータ
            {"template_name": template_name}  # メタデータ
        )
        
        # 構成要素間の接続を設定
        if structure_type == StructureType.SYNTH_DEF:
            if "oscillator" in components and "envelope" in components:
                structure.add_connection("oscillator", "envelope")
            if "envelope" in components and "amplitude" in components:
                structure.add_connection("envelope", "amplitude")
            if "amplitude" in components and "output" in components:
                structure.add_connection("amplitude", "output")
        elif structure_type == StructureType.EFFECT_CHAIN:
            if "input" in components and "effect" in components:
                structure.add_connection("input", "effect")
            if "effect" in components and "output" in components:
                structure.add_connection("effect", "output")
        
        return structure


class StructureToCodeConverter(BaseConverter):
    """
    構造レベルからコードレベルへの変換を行うクラス
    
    このクラスは、構造レベルの表現からコードレベルの表現への変換を行います。
    """
    
    def __init__(self, code_templates: Optional[Dict[str, Dict[str, Any]]] = None):
        """
        構造からコードへの変換クラスを初期化します。
        
        引数:
            code_templates: 構造タイプごとのコードテンプレート
        """
        super().__init__()
        self.code_templates = code_templates or {
            StructureType.SYNTH_DEF: {
                "sine": {
                    "code_type": CodeType.SYNTH,
                    "template": """
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
                },
                "saw": {
                    "code_type": CodeType.SYNTH,
                    "template": """
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
                },
                "pad": {
                    "code_type": CodeType.SYNTH,
                    "template": """
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
                }
            },
            StructureType.EFFECT_CHAIN: {
                "reverb": {
                    "code_type": CodeType.EFFECT,
                    "template": """
s.waitForBoot({
    {
        // 入力信号
        var input = {input_sound};
        // リバーブを適用
        var wet = FreeVerb.ar(input, {mix}, {room}, {damp});
        wet ! 2 // ステレオ出力
    }.play;
});
"""
                }
            }
            # 他のテンプレートも追加可能
        }
    
    def _select_template(self, structure: StructureLevel) -> Tuple[CodeType, str]:
        """
        構造に最も適合するコードテンプレートを選択します。
        
        引数:
            structure: 構造レベルの表現
            
        戻り値:
            Tuple[CodeType, str]: コードタイプとテンプレート文字列のタプル
        """
        structure_type = structure.structure_type
        
        if structure_type not in self.code_templates:
            raise ConversionError(f"構造タイプ'{structure_type}'に対応するコードテンプレートがありません",
                                 source_level="StructureLevel",
                                 target_level="CodeLevel")
        
        # 波形タイプを取得
        waveform = "sine"  # デフォルト
        if "oscillator" in structure.components:
            osc_comp = structure.get_component("oscillator")
            if isinstance(osc_comp.value, dict) and "type" in osc_comp.value:
                waveform = osc_comp.value["type"]
        
        # エフェクトタイプを取得
        effect_type = "reverb"  # デフォルト
        if "effect" in structure.components:
            effect_comp = structure.get_component("effect")
            if isinstance(effect_comp.value, dict) and "type" in effect_comp.value:
                effect_type = effect_comp.value["type"]
        
        # テンプレートを選択
        if structure_type == StructureType.SYNTH_DEF:
            if waveform in self.code_templates[structure_type]:
                template_data = self.code_templates[structure_type][waveform]
                return template_data["code_type"], template_data["template"]
            else:
                # デフォルトのテンプレート
                template_data = self.code_templates[structure_type]["sine"]
                return template_data["code_type"], template_data["template"]
        elif structure_type == StructureType.EFFECT_CHAIN:
            if effect_type in self.code_templates[structure_type]:
                template_data = self.code_templates[structure_type][effect_type]
                return template_data["code_type"], template_data["template"]
            else:
                # デフォルトのテンプレート
                template_data = self.code_templates[structure_type]["reverb"]
                return template_data["code_type"], template_data["template"]
        else:
            raise ConversionError(f"構造タイプ'{structure_type}'に対応するコードテンプレートがありません",
                                 source_level="StructureLevel",
                                 target_level="CodeLevel")
    
    def _convert_impl(self, structure: StructureLevel) -> CodeLevel:
        """
        構造レベルからコードレベルへの変換を実装します。
        
        引数:
            structure: 構造レベルの表現
            
        戻り値:
            CodeLevel: 変換されたコードレベルの表現
        """
        # 構造から適切なコードテンプレートを選択
        code_type, template = self._select_template(structure)
        
        # 変数を作成
        variables = {}
        
        # 基本的な音源構造の場合
        if structure.structure_type == StructureType.SYNTH_DEF:
            # 周波数変数
            if "oscillator" in structure.components:
                osc_comp = structure.get_component("oscillator")
                if isinstance(osc_comp.value, dict) and "frequency" in osc_comp.value:
                    freq = osc_comp.value["frequency"]
                    variables["freq"] = CodeVariable("freq", freq, "frequency", True)
            
            # 振幅変数
            if "amplitude" in structure.components:
                amp_comp = structure.get_component("amplitude")
                if isinstance(amp_comp.value, dict) and "value" in amp_comp.value:
                    amp = amp_comp.value["value"]
                    variables["amp"] = CodeVariable("amp", amp, "amplitude", True)
            
            # 持続時間変数
            if "envelope" in structure.components:
                env_comp = structure.get_component("envelope")
                if isinstance(env_comp.value, dict):
                    if "sustain" in env_comp.value:
                        duration = env_comp.value["sustain"]
                        variables["duration"] = CodeVariable("duration", duration, "duration", True)
                    elif "type" in env_comp.value and env_comp.value["type"] == "linen" and "sustain" in env_comp.value:
                        duration = env_comp.value["sustain"]
                        variables["duration"] = CodeVariable("duration", duration, "duration", True)
        
        # エフェクト構造の場合
        elif structure.structure_type == StructureType.EFFECT_CHAIN:
            # エフェクトパラメータ変数
            if "effect" in structure.components:
                effect_comp = structure.get_component("effect")
                if isinstance(effect_comp.value, dict) and "parameters" in effect_comp.value:
                    params = effect_comp.value["parameters"]
                    if "mix" in params:
                        variables["mix"] = CodeVariable("mix", params["mix"], "mix", True)
                    if "room" in params:
                        variables["room"] = CodeVariable("room", params["room"], "room", True)
                    if "damp" in params:
                        variables["damp"] = CodeVariable("damp", params["damp"], "damp", True)
            
            # 入力音変数
            if "input" in structure.components:
                input_comp = structure.get_component("input")
                if isinstance(input_comp.value, dict) and "sound" in input_comp.value:
                    input_sound = input_comp.value["sound"]
                    variables["input_sound"] = CodeVariable("input_sound", input_sound, "input_sound", True)
        
        # デフォルト値を設定
        if "freq" not in variables:
            variables["freq"] = CodeVariable("freq", 440.0, "frequency", True)
        if "amp" not in variables:
            variables["amp"] = CodeVariable("amp", 0.5, "amplitude", True)
        if "duration" not in variables:
            variables["duration"] = CodeVariable("duration", 1.0, "duration", True)
        if structure.structure_type == StructureType.EFFECT_CHAIN:
            if "mix" not in variables:
                variables["mix"] = CodeVariable("mix", 0.33, "mix", True)
            if "room" not in variables:
                variables["room"] = CodeVariable("room", 0.5, "room", True)
            if "damp" not in variables:
                variables["damp"] = CodeVariable("damp", 0.5, "damp", True)
            if "input_sound" not in variables:
                variables["input_sound"] = CodeVariable("input_sound", "WhiteNoise.ar(0.2)", "input_sound", False)
        
        # コードレベルの表現を作成
        code = CodeLevel(
            code_type,
            template,
            variables,
            structure.structure_type.name,  # ソース構造
            {"source_parameters": structure.source_parameters}  # メタデータ
        )
        
        return code
