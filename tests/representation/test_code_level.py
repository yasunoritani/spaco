#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
SPACO - コードレベルのテスト

このモジュールは、コードレベルの表現クラスのテストを提供します。
"""

import unittest
import json
from src.language_processor.representation.base import ValidationError
from src.language_processor.representation.code_level import CodeLevel, CodeVariable, CodeType


class TestCodeVariable(unittest.TestCase):
    """コード変数クラスのテスト"""
    
    def test_init(self):
        """コード変数の初期化のテスト"""
        variable = CodeVariable("freq", 440.0, "frequency", True, {"source": "parameter"})
        self.assertEqual(variable.name, "freq")
        self.assertEqual(variable.value, 440.0)
        self.assertEqual(variable.var_type, "frequency")
        self.assertTrue(variable.is_literal)
        self.assertEqual(variable.metadata, {"source": "parameter"})
    
    def test_to_code(self):
        """コード変数のコード変換のテスト"""
        # リテラル値
        variable = CodeVariable("freq", 440.0, "frequency", True)
        self.assertEqual(variable.to_code(), "440.0")
        
        # 文字列リテラル
        variable = CodeVariable("type", "sine", "type", True)
        self.assertEqual(variable.to_code(), '"sine"')
        
        # ブール値リテラル
        variable = CodeVariable("loop", True, "loop", True)
        self.assertEqual(variable.to_code(), "true")
        
        # 非リテラル値（変数名が使用される）
        variable = CodeVariable("sig", "SinOsc.ar(440, 0, 0.5)", "signal", False)
        self.assertEqual(variable.to_code(), "sig")
    
    def test_to_dict(self):
        """コード変数の辞書変換のテスト"""
        variable = CodeVariable("freq", 440.0, "frequency", True, {"source": "parameter"})
        variable_dict = variable.to_dict()
        
        self.assertEqual(variable_dict["name"], "freq")
        self.assertEqual(variable_dict["value"], 440.0)
        self.assertEqual(variable_dict["var_type"], "frequency")
        self.assertEqual(variable_dict["is_literal"], True)
        self.assertEqual(variable_dict["metadata"], {"source": "parameter"})
    
    def test_from_dict(self):
        """コード変数の辞書からの生成のテスト"""
        variable_dict = {
            "name": "freq",
            "value": 440.0,
            "var_type": "frequency",
            "is_literal": True,
            "metadata": {"source": "parameter"}
        }
        
        variable = CodeVariable.from_dict(variable_dict)
        
        self.assertEqual(variable.name, "freq")
        self.assertEqual(variable.value, 440.0)
        self.assertEqual(variable.var_type, "frequency")
        self.assertTrue(variable.is_literal)
        self.assertEqual(variable.metadata, {"source": "parameter"})
    
    def test_create_literal(self):
        """リテラル値の作成のテスト"""
        variable = CodeVariable.create_literal(440.0, "frequency")
        self.assertEqual(variable.value, 440.0)
        self.assertEqual(variable.var_type, "frequency")
        self.assertTrue(variable.is_literal)
        self.assertEqual(variable.name, "")


class TestCodeLevel(unittest.TestCase):
    """コードレベルの表現クラスのテスト"""
    
    def test_init(self):
        """コードレベルの初期化のテスト"""
        template = """
s.waitForBoot({
    {
        var sig = SinOsc.ar({freq}, 0, {amp});
        sig = sig * EnvGen.kr(Env.linen(0.01, {duration}, 0.01), doneAction: 2);
        sig ! 2
    }.play;
});
"""
        
        variables = {
            "freq": CodeVariable("freq", 440.0, "frequency", True),
            "amp": CodeVariable("amp", 0.5, "amplitude", True),
            "duration": CodeVariable("duration", 1.0, "duration", True)
        }
        
        code = CodeLevel(CodeType.SYNTH, template, variables, "SYNTH_DEF", {"source": "template"})
        
        self.assertEqual(code.code_type, CodeType.SYNTH)
        self.assertEqual(code.template, template)
        self.assertEqual(code.variables, variables)
        self.assertEqual(code.source_structure, "SYNTH_DEF")
        self.assertEqual(code.metadata, {"source": "template"})
    
    def test_validate(self):
        """コードレベルの検証のテスト"""
        # 有効なコード
        template = "var sig = SinOsc.ar({freq}, 0, {amp});"
        variables = {
            "freq": CodeVariable("freq", 440.0, "frequency", True),
            "amp": CodeVariable("amp", 0.5, "amplitude", True)
        }
        code = CodeLevel(CodeType.SYNTH, template, variables)
        self.assertTrue(code.validate())
        
        # 無効なコード（タイプがNone）
        with self.assertRaises(ValidationError):
            code = CodeLevel(None, template, variables)
            code.validate()
        
        # 無効なコード（テンプレートが空）
        with self.assertRaises(ValidationError):
            code = CodeLevel(CodeType.SYNTH, "", variables)
            code.validate()
        
        # 無効なコード（不足している変数）
        template = "var sig = SinOsc.ar({freq}, 0, {amp}, {phase});"
        variables = {
            "freq": CodeVariable("freq", 440.0, "frequency", True),
            "amp": CodeVariable("amp", 0.5, "amplitude", True)
            # phase変数が不足
        }
        with self.assertRaises(ValidationError):
            code = CodeLevel(CodeType.SYNTH, template, variables)
            code.validate()
    
    def test_to_dict(self):
        """コードレベルの辞書変換のテスト"""
        template = "var sig = SinOsc.ar({freq}, 0, {amp});"
        variables = {
            "freq": CodeVariable("freq", 440.0, "frequency", True),
            "amp": CodeVariable("amp", 0.5, "amplitude", True)
        }
        code = CodeLevel(CodeType.SYNTH, template, variables, "SYNTH_DEF", {"source": "template"})
        code_dict = code.to_dict()
        
        self.assertEqual(code_dict["code_type"], "SYNTH")
        self.assertEqual(code_dict["template"], template)
        self.assertEqual(code_dict["source_structure"], "SYNTH_DEF")
        self.assertEqual(code_dict["metadata"], {"source": "template"})
        self.assertEqual(code_dict["variables"]["freq"]["value"], 440.0)
        self.assertEqual(code_dict["variables"]["amp"]["value"], 0.5)
    
    def test_from_dict(self):
        """コードレベルの辞書からの生成のテスト"""
        code_dict = {
            "code_type": "SYNTH",
            "template": "var sig = SinOsc.ar({freq}, 0, {amp});",
            "variables": {
                "freq": {
                    "name": "freq",
                    "value": 440.0,
                    "var_type": "frequency",
                    "is_literal": True
                },
                "amp": {
                    "name": "amp",
                    "value": 0.5,
                    "var_type": "amplitude",
                    "is_literal": True
                }
            },
            "source_structure": "SYNTH_DEF",
            "metadata": {"source": "template"}
        }
        
        code = CodeLevel.from_dict(code_dict)
        
        self.assertEqual(code.code_type, CodeType.SYNTH)
        self.assertEqual(code.template, "var sig = SinOsc.ar({freq}, 0, {amp});")
        self.assertEqual(code.source_structure, "SYNTH_DEF")
        self.assertEqual(code.metadata, {"source": "template"})
        self.assertEqual(code.variables["freq"].value, 440.0)
        self.assertEqual(code.variables["amp"].value, 0.5)
    
    def test_add_variable(self):
        """変数の追加のテスト"""
        code = CodeLevel(CodeType.SYNTH, "var sig = SinOsc.ar({freq}, 0, {amp});")
        
        freq_var = CodeVariable("freq", 440.0, "frequency", True)
        code.add_variable("freq", freq_var)
        
        self.assertTrue(code.has_variable("freq"))
        self.assertEqual(code.get_variable("freq"), freq_var)
    
    def test_get_variable(self):
        """変数の取得のテスト"""
        freq_var = CodeVariable("freq", 440.0, "frequency", True)
        code = CodeLevel(CodeType.SYNTH, "var sig = SinOsc.ar({freq}, 0, 0.5);", {"freq": freq_var})
        
        self.assertEqual(code.get_variable("freq"), freq_var)
        self.assertIsNone(code.get_variable("unknown"))
    
    def test_has_variable(self):
        """変数の存在確認のテスト"""
        freq_var = CodeVariable("freq", 440.0, "frequency", True)
        code = CodeLevel(CodeType.SYNTH, "var sig = SinOsc.ar({freq}, 0, 0.5);", {"freq": freq_var})
        
        self.assertTrue(code.has_variable("freq"))
        self.assertFalse(code.has_variable("unknown"))
    
    def test_get_variable_names(self):
        """変数名の取得のテスト"""
        freq_var = CodeVariable("freq", 440.0, "frequency", True)
        amp_var = CodeVariable("amp", 0.5, "amplitude", True)
        
        variables = {
            "freq": freq_var,
            "amp": amp_var
        }
        
        code = CodeLevel(CodeType.SYNTH, "var sig = SinOsc.ar({freq}, 0, {amp});", variables)
        
        self.assertEqual(code.get_variable_names(), {"freq", "amp"})
    
    def test_to_code(self):
        """コード生成のテスト"""
        template = """
s.waitForBoot({
    {
        // {freq}Hzの正弦波オシレーターを生成
        var sig = SinOsc.ar({freq}, 0, {amp});
        // エンベロープを適用
        sig = sig * EnvGen.kr(Env.linen(0.01, {duration}, 0.01), doneAction: 2);
        sig ! 2 // ステレオ出力
    }.play;
});
"""
        
        variables = {
            "freq": CodeVariable("freq", 440.0, "frequency", True),
            "amp": CodeVariable("amp", 0.5, "amplitude", True),
            "duration": CodeVariable("duration", 1.0, "duration", True)
        }
        
        code = CodeLevel(CodeType.SYNTH, template, variables)
        generated_code = code.to_code()
        
        # 変数が置換されていることを確認
        self.assertIn("SinOsc.ar(440.0, 0, 0.5)", generated_code)
        self.assertIn("Env.linen(0.01, 1.0, 0.01)", generated_code)
        
        # 無効なコードからの生成はエラー
        code = CodeLevel(CodeType.SYNTH, template, {})  # 変数が不足
        with self.assertRaises(ValidationError):
            code.to_code()
    
    def test_utility_methods(self):
        """ユーティリティメソッドのテスト"""
        # 正弦波コード生成
        sine_code = CodeLevel.create_sine_wave_code(440.0, 0.5, 1.0)
        self.assertEqual(sine_code.code_type, CodeType.SYNTH)
        self.assertEqual(sine_code.variables["freq"].value, 440.0)
        self.assertEqual(sine_code.variables["amp"].value, 0.5)
        self.assertEqual(sine_code.variables["duration"].value, 1.0)
        
        # ノコギリ波コード生成
        saw_code = CodeLevel.create_saw_wave_code(220.0, 0.3, 2.0)
        self.assertEqual(saw_code.code_type, CodeType.SYNTH)
        self.assertEqual(saw_code.variables["freq"].value, 220.0)
        self.assertEqual(saw_code.variables["amp"].value, 0.3)
        self.assertEqual(saw_code.variables["duration"].value, 2.0)
        
        # パッドサウンドコード生成
        pad_code = CodeLevel.create_pad_sound_code(330.0, 0.4)
        self.assertEqual(pad_code.code_type, CodeType.SYNTH)
        self.assertEqual(pad_code.variables["freq"].value, 330.0)
        self.assertEqual(pad_code.variables["amp"].value, 0.4)
    
    def test_to_json(self):
        """コードレベルのJSON変換のテスト"""
        template = "var sig = SinOsc.ar({freq}, 0, {amp});"
        variables = {
            "freq": CodeVariable("freq", 440.0, "frequency", True),
            "amp": CodeVariable("amp", 0.5, "amplitude", True)
        }
        code = CodeLevel(CodeType.SYNTH, template, variables, "SYNTH_DEF", {"source": "template"})
        code_json = code.to_json()
        
        # JSONデコード
        code_dict = json.loads(code_json)
        
        self.assertEqual(code_dict["code_type"], "SYNTH")
        self.assertEqual(code_dict["template"], template)
        self.assertEqual(code_dict["source_structure"], "SYNTH_DEF")
        self.assertEqual(code_dict["metadata"], {"source": "template"})
        self.assertEqual(code_dict["variables"]["freq"]["value"], 440.0)
        self.assertEqual(code_dict["variables"]["amp"]["value"], 0.5)
    
    def test_from_json(self):
        """コードレベルのJSONからの生成のテスト"""
        code_json = """
        {
            "code_type": "SYNTH",
            "template": "var sig = SinOsc.ar({freq}, 0, {amp});",
            "variables": {
                "freq": {
                    "name": "freq",
                    "value": 440.0,
                    "var_type": "frequency",
                    "is_literal": true
                },
                "amp": {
                    "name": "amp",
                    "value": 0.5,
                    "var_type": "amplitude",
                    "is_literal": true
                }
            },
            "source_structure": "SYNTH_DEF",
            "metadata": {"source": "template"}
        }
        """
        
        code = CodeLevel.from_json(code_json)
        
        self.assertEqual(code.code_type, CodeType.SYNTH)
        self.assertEqual(code.template, "var sig = SinOsc.ar({freq}, 0, {amp});")
        self.assertEqual(code.source_structure, "SYNTH_DEF")
        self.assertEqual(code.metadata, {"source": "template"})
        self.assertEqual(code.variables["freq"].value, 440.0)
        self.assertEqual(code.variables["amp"].value, 0.5)


if __name__ == "__main__":
    unittest.main()
