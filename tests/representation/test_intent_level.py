#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
SPACO - 意図レベルのテスト

このモジュールは、意図レベルの表現クラスのテストを提供します。
"""

import unittest
import json
from src.language_processor.representation.base import ValidationError
from src.language_processor.representation.intent_level import IntentLevel, IntentType


class TestIntentLevel(unittest.TestCase):
    """意図レベルの表現クラスのテスト"""
    
    def test_init(self):
        """意図レベルの初期化のテスト"""
        intent = IntentLevel(IntentType.GENERATE_SOUND, "440Hzの正弦波を生成")
        self.assertEqual(intent.intent_type, IntentType.GENERATE_SOUND)
        self.assertEqual(intent.description, "440Hzの正弦波を生成")
        self.assertEqual(intent.confidence, 1.0)
        self.assertEqual(intent.metadata, {})
    
    def test_validate(self):
        """意図レベルの検証のテスト"""
        # 有効な意図
        intent = IntentLevel(IntentType.GENERATE_SOUND, "440Hzの正弦波を生成")
        self.assertTrue(intent.validate())
        
        # 無効な意図（意図タイプがNone）
        with self.assertRaises(ValidationError):
            intent = IntentLevel(None, "440Hzの正弦波を生成")
            intent.validate()
        
        # 無効な意図（説明が空）
        with self.assertRaises(ValidationError):
            intent = IntentLevel(IntentType.GENERATE_SOUND, "")
            intent.validate()
        
        # 無効な意図（確信度が範囲外）
        with self.assertRaises(ValidationError):
            intent = IntentLevel(IntentType.GENERATE_SOUND, "440Hzの正弦波を生成", confidence=1.5)
            intent.validate()
    
    def test_to_dict(self):
        """意図レベルの辞書変換のテスト"""
        intent = IntentLevel(IntentType.GENERATE_SOUND, "440Hzの正弦波を生成", {"extracted_parameters": {"frequency": 440}}, 0.9)
        intent_dict = intent.to_dict()
        
        self.assertEqual(intent_dict["intent_type"], "GENERATE_SOUND")
        self.assertEqual(intent_dict["description"], "440Hzの正弦波を生成")
        self.assertEqual(intent_dict["confidence"], 0.9)
        self.assertEqual(intent_dict["metadata"], {"extracted_parameters": {"frequency": 440}})
    
    def test_from_dict(self):
        """意図レベルの辞書からの生成のテスト"""
        intent_dict = {
            "intent_type": "GENERATE_SOUND",
            "description": "440Hzの正弦波を生成",
            "confidence": 0.9,
            "metadata": {"extracted_parameters": {"frequency": 440}}
        }
        
        intent = IntentLevel.from_dict(intent_dict)
        
        self.assertEqual(intent.intent_type, IntentType.GENERATE_SOUND)
        self.assertEqual(intent.description, "440Hzの正弦波を生成")
        self.assertEqual(intent.confidence, 0.9)
        self.assertEqual(intent.metadata, {"extracted_parameters": {"frequency": 440}})
    
    def test_get_related_parameters(self):
        """関連パラメータの取得のテスト"""
        # 音生成の意図
        intent = IntentLevel(IntentType.GENERATE_SOUND, "440Hzの正弦波を生成")
        params = intent.get_related_parameters()
        self.assertTrue("frequency" in params)
        self.assertTrue("amplitude" in params)
        self.assertTrue("waveform" in params)
        self.assertTrue("duration" in params)
        
        # 楽器生成の意図
        intent = IntentLevel(IntentType.GENERATE_INSTRUMENT, "ピアノでC4の音を鳴らす")
        params = intent.get_related_parameters()
        self.assertTrue("instrument_type" in params)
        self.assertTrue("note" in params)
        self.assertTrue("velocity" in params)
        self.assertTrue("duration" in params)
    
    def test_to_json(self):
        """意図レベルのJSON変換のテスト"""
        intent = IntentLevel(IntentType.GENERATE_SOUND, "440Hzの正弦波を生成", {"extracted_parameters": {"frequency": 440}}, 0.9)
        intent_json = intent.to_json()
        
        # JSONデコード
        intent_dict = json.loads(intent_json)
        
        self.assertEqual(intent_dict["intent_type"], "GENERATE_SOUND")
        self.assertEqual(intent_dict["description"], "440Hzの正弦波を生成")
        self.assertEqual(intent_dict["confidence"], 0.9)
        self.assertEqual(intent_dict["metadata"], {"extracted_parameters": {"frequency": 440}})
    
    def test_from_json(self):
        """意図レベルのJSONからの生成のテスト"""
        intent_json = """
        {
            "intent_type": "GENERATE_SOUND",
            "description": "440Hzの正弦波を生成",
            "confidence": 0.9,
            "metadata": {"extracted_parameters": {"frequency": 440}}
        }
        """
        
        intent = IntentLevel.from_json(intent_json)
        
        self.assertEqual(intent.intent_type, IntentType.GENERATE_SOUND)
        self.assertEqual(intent.description, "440Hzの正弦波を生成")
        self.assertEqual(intent.confidence, 0.9)
        self.assertEqual(intent.metadata, {"extracted_parameters": {"frequency": 440}})


if __name__ == "__main__":
    unittest.main()
