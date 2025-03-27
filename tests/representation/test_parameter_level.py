#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
SPACO - パラメータレベルのテスト

このモジュールは、パラメータレベルの表現クラスのテストを提供します。
"""

import unittest
import json
from src.language_processor.representation.base import ValidationError
from src.language_processor.representation.parameter_level import ParameterLevel, ParameterValue, ParameterType


class TestParameterValue(unittest.TestCase):
    """パラメータ値クラスのテスト"""
    
    def test_init(self):
        """パラメータ値の初期化のテスト"""
        param_value = ParameterValue("static", 440.0, "Hz", None, None, {"source": "user"})
        self.assertEqual(param_value.value_type, "static")
        self.assertEqual(param_value.value, 440.0)
        self.assertEqual(param_value.unit, "Hz")
        self.assertIsNone(param_value.min_value)
        self.assertIsNone(param_value.max_value)
        self.assertEqual(param_value.metadata, {"source": "user"})
    
    def test_validate(self):
        """パラメータ値の検証のテスト"""
        # 有効なパラメータ値
        param_value = ParameterValue("static", 440.0, "Hz")
        self.assertTrue(param_value.validate())
        
        # 無効なパラメータ値（値の種類が空）
        with self.assertRaises(ValidationError):
            param_value = ParameterValue("", 440.0)
            param_value.validate()
        
        # 無効なパラメータ値（値がNone）
        with self.assertRaises(ValidationError):
            param_value = ParameterValue("static", None)
            param_value.validate()
        
        # 無効なパラメータ値（範囲の最小値と最大値が必要）
        with self.assertRaises(ValidationError):
            param_value = ParameterValue("range", 440.0)
            param_value.validate()
        
        # 無効なパラメータ値（最小値が最大値より大きい）
        with self.assertRaises(ValidationError):
            param_value = ParameterValue("range", 440.0, "Hz", 500.0, 100.0)
            param_value.validate()
    
    def test_to_dict(self):
        """パラメータ値の辞書変換のテスト"""
        param_value = ParameterValue("static", 440.0, "Hz", None, None, {"source": "user"})
        param_dict = param_value.to_dict()
        
        self.assertEqual(param_dict["value_type"], "static")
        self.assertEqual(param_dict["value"], 440.0)
        self.assertEqual(param_dict["unit"], "Hz")
        self.assertEqual(param_dict["metadata"], {"source": "user"})
    
    def test_from_dict(self):
        """パラメータ値の辞書からの生成のテスト"""
        param_dict = {
            "value_type": "static",
            "value": 440.0,
            "unit": "Hz",
            "metadata": {"source": "user"}
        }
        
        param_value = ParameterValue.from_dict(param_dict)
        
        self.assertEqual(param_value.value_type, "static")
        self.assertEqual(param_value.value, 440.0)
        self.assertEqual(param_value.unit, "Hz")
        self.assertEqual(param_value.metadata, {"source": "user"})
    
    def test_to_string(self):
        """パラメータ値の文字列表現のテスト"""
        # 静的値
        param_value = ParameterValue("static", 440.0, "Hz")
        self.assertEqual(str(param_value), "440.0 Hz")
        
        # 範囲値
        param_value = ParameterValue("range", None, "Hz", 100.0, 1000.0)
        self.assertEqual(str(param_value), "100.0-1000.0 Hz")
        
        # 動的値
        param_value = ParameterValue("dynamic", "LFO(0.1, 1.0)", "Hz")
        self.assertEqual(str(param_value), "LFO(0.1, 1.0) (dynamic) Hz")


class TestParameterLevel(unittest.TestCase):
    """パラメータレベルの表現クラスのテスト"""
    
    def test_init(self):
        """パラメータレベルの初期化のテスト"""
        freq_param = ParameterValue("static", 440.0, "Hz")
        amp_param = ParameterValue("static", 0.5)
        
        params = {
            "frequency": freq_param,
            "amplitude": amp_param
        }
        
        param_level = ParameterLevel(params, "GENERATE_SOUND")
        
        self.assertEqual(param_level.parameters, params)
        self.assertEqual(param_level.source_intent, "GENERATE_SOUND")
    
    def test_validate(self):
        """パラメータレベルの検証のテスト"""
        # 有効なパラメータレベル
        freq_param = ParameterValue("static", 440.0, "Hz")
        param_level = ParameterLevel({"frequency": freq_param})
        self.assertTrue(param_level.validate())
        
        # 無効なパラメータレベル（パラメータなし）
        with self.assertRaises(ValidationError):
            param_level = ParameterLevel()
            param_level.validate()
        
        # 無効なパラメータレベル（無効なパラメータ値）
        freq_param = ParameterValue("static", None)  # 無効な値
        param_level = ParameterLevel({"frequency": freq_param})
        with self.assertRaises(ValidationError):
            param_level.validate()
    
    def test_to_dict(self):
        """パラメータレベルの辞書変換のテスト"""
        freq_param = ParameterValue("static", 440.0, "Hz")
        amp_param = ParameterValue("static", 0.5)
        
        params = {
            "frequency": freq_param,
            "amplitude": amp_param
        }
        
        param_level = ParameterLevel(params, "GENERATE_SOUND")
        param_dict = param_level.to_dict()
        
        self.assertEqual(param_dict["source_intent"], "GENERATE_SOUND")
        self.assertEqual(param_dict["parameters"]["frequency"]["value"], 440.0)
        self.assertEqual(param_dict["parameters"]["frequency"]["unit"], "Hz")
        self.assertEqual(param_dict["parameters"]["amplitude"]["value"], 0.5)
    
    def test_from_dict(self):
        """パラメータレベルの辞書からの生成のテスト"""
        param_dict = {
            "source_intent": "GENERATE_SOUND",
            "parameters": {
                "frequency": {
                    "value_type": "static",
                    "value": 440.0,
                    "unit": "Hz"
                },
                "amplitude": {
                    "value_type": "static",
                    "value": 0.5
                }
            }
        }
        
        param_level = ParameterLevel.from_dict(param_dict)
        
        self.assertEqual(param_level.source_intent, "GENERATE_SOUND")
        self.assertEqual(param_level.get_parameter("frequency").value, 440.0)
        self.assertEqual(param_level.get_parameter("frequency").unit, "Hz")
        self.assertEqual(param_level.get_parameter("amplitude").value, 0.5)
    
    def test_add_parameter(self):
        """パラメータの追加のテスト"""
        param_level = ParameterLevel()
        
        freq_param = ParameterValue("static", 440.0, "Hz")
        param_level.add_parameter("frequency", freq_param)
        
        self.assertTrue(param_level.has_parameter("frequency"))
        self.assertEqual(param_level.get_parameter("frequency").value, 440.0)
    
    def test_get_parameter(self):
        """パラメータの取得のテスト"""
        freq_param = ParameterValue("static", 440.0, "Hz")
        param_level = ParameterLevel({"frequency": freq_param})
        
        self.assertEqual(param_level.get_parameter("frequency"), freq_param)
        self.assertIsNone(param_level.get_parameter("unknown"))
    
    def test_has_parameter(self):
        """パラメータの存在確認のテスト"""
        freq_param = ParameterValue("static", 440.0, "Hz")
        param_level = ParameterLevel({"frequency": freq_param})
        
        self.assertTrue(param_level.has_parameter("frequency"))
        self.assertFalse(param_level.has_parameter("unknown"))
    
    def test_get_parameter_names(self):
        """パラメータ名の取得のテスト"""
        freq_param = ParameterValue("static", 440.0, "Hz")
        amp_param = ParameterValue("static", 0.5)
        
        params = {
            "frequency": freq_param,
            "amplitude": amp_param
        }
        
        param_level = ParameterLevel(params)
        
        self.assertEqual(param_level.get_parameter_names(), {"frequency", "amplitude"})
    
    def test_missing_parameters(self):
        """不足パラメータの確認のテスト"""
        freq_param = ParameterValue("static", 440.0, "Hz")
        param_level = ParameterLevel({"frequency": freq_param})
        
        required = {"frequency", "amplitude", "duration"}
        missing = param_level.missing_parameters(required)
        
        self.assertEqual(missing, {"amplitude", "duration"})
    
    def test_set_default_parameters(self):
        """デフォルトパラメータの設定のテスト"""
        freq_param = ParameterValue("static", 440.0, "Hz")
        param_level = ParameterLevel({"frequency": freq_param})
        
        defaults = {
            "amplitude": ParameterValue("static", 0.5),
            "duration": ParameterValue("static", 1.0, "s"),
            "frequency": ParameterValue("static", 220.0, "Hz")  # 既存のパラメータは上書きされない
        }
        
        param_level.set_default_parameters(defaults)
        
        self.assertEqual(param_level.get_parameter("frequency").value, 440.0)  # 上書きされていない
        self.assertEqual(param_level.get_parameter("amplitude").value, 0.5)  # デフォルト値が設定された
        self.assertEqual(param_level.get_parameter("duration").value, 1.0)  # デフォルト値が設定された
    
    def test_to_json(self):
        """パラメータレベルのJSON変換のテスト"""
        freq_param = ParameterValue("static", 440.0, "Hz")
        amp_param = ParameterValue("static", 0.5)
        
        params = {
            "frequency": freq_param,
            "amplitude": amp_param
        }
        
        param_level = ParameterLevel(params, "GENERATE_SOUND")
        param_json = param_level.to_json()
        
        # JSONデコード
        param_dict = json.loads(param_json)
        
        self.assertEqual(param_dict["source_intent"], "GENERATE_SOUND")
        self.assertEqual(param_dict["parameters"]["frequency"]["value"], 440.0)
        self.assertEqual(param_dict["parameters"]["frequency"]["unit"], "Hz")
        self.assertEqual(param_dict["parameters"]["amplitude"]["value"], 0.5)
    
    def test_from_json(self):
        """パラメータレベルのJSONからの生成のテスト"""
        param_json = """
        {
            "source_intent": "GENERATE_SOUND",
            "parameters": {
                "frequency": {
                    "value_type": "static",
                    "value": 440.0,
                    "unit": "Hz"
                },
                "amplitude": {
                    "value_type": "static",
                    "value": 0.5
                }
            }
        }
        """
        
        param_level = ParameterLevel.from_json(param_json)
        
        self.assertEqual(param_level.source_intent, "GENERATE_SOUND")
        self.assertEqual(param_level.get_parameter("frequency").value, 440.0)
        self.assertEqual(param_level.get_parameter("frequency").unit, "Hz")
        self.assertEqual(param_level.get_parameter("amplitude").value, 0.5)


if __name__ == "__main__":
    unittest.main()
