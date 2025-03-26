#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
SPACO - 言語プロセッサーモジュールのユニットテスト
"""

import unittest
import os
import sys
import json
from unittest.mock import patch, MagicMock

# テスト対象のモジュールをインポート
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from src.language_processor.processor import (
    LanguageProcessor,
    LanguageProcessorError,
    IntentRecognitionError,
    ParameterExtractionError,
    CodeGenerationError
)


class TestLanguageProcessor(unittest.TestCase):
    """言語プロセッサーのテストケース"""

    def setUp(self):
        """
        テスト実行前の準備
        """
        self.processor = LanguageProcessor()

    def test_initialization(self):
        """
        初期化が正常に行われることを確認
        """
        self.assertIsNotNone(self.processor.intent_patterns)
        self.assertIsNotNone(self.processor.templates)
        self.assertIsNotNone(self.processor.note_to_freq)

    def test_basic_intent_recognition(self):
        """
        基本的な意図認識のテスト
        """
        # 正弦波生成の意図認識テスト
        intent, pattern = self.processor._recognize_intent("440Hzの正弦波を鳴らして")
        self.assertEqual(intent, "generate_sine")

        # ノコギリ波生成の意図認識テスト
        intent, pattern = self.processor._recognize_intent("ノコギリ波を220Hzで生成")
        self.assertEqual(intent, "generate_sawtooth")

        # パッドサウンド生成の意図認識テスト
        intent, pattern = self.processor._recognize_intent("柔らかいパッドサウンドを作って")
        self.assertEqual(intent, "generate_pad")
    
    def test_note_frequency_mapping(self):
        """
        音符名と周波数のマッピングテスト
        """
        self.assertEqual(self.processor.note_to_freq.get("A4"), 440.0)
        self.assertEqual(self.processor.note_to_freq.get("C4"), 261.63)
        self.assertEqual(self.processor.note_to_freq.get("G4"), 392.00)
    
    def test_parameter_extraction(self):
        """
        パラメーター抽出のテスト
        """
        # 周波数抽出テスト
        intent = "generate_sine"
        pattern = r"(\d+)\s*(?:Hz|ヘルツ)の(?:正弦波|サイン波)"
        params = self.processor._extract_parameters("440Hzの正弦波", intent, pattern)
        self.assertEqual(params.get("freq"), 440.0)
        
        # 音量抽出テスト
        params = self.processor._extract_parameters("440Hzの正弦波 音量50%", intent, pattern)
        self.assertEqual(params.get("freq"), 440.0)
        self.assertEqual(params.get("amp"), 0.5)
        
        # 持続時間抽出テスト
        params = self.processor._extract_parameters("440Hzの正弦波を2.5秒間", intent, pattern)
        self.assertEqual(params.get("freq"), 440.0)
        self.assertEqual(params.get("duration"), 2.5)
    
    def test_default_parameters(self):
        """
        デフォルトパラメーターの設定テスト
        """
        # 空のパラメーター辞書
        params = {}
        filled_params = self.processor._set_default_parameters(params, "generate_sine")
        
        # すべてのデフォルト値が設定されていることを確認
        self.assertEqual(filled_params.get("freq"), 440.0)
        self.assertEqual(filled_params.get("amp"), 0.5)
        self.assertEqual(filled_params.get("duration"), 1.0)
        
        # 一部のパラメーターのみが存在する場合
        params = {"freq": 880.0}
        filled_params = self.processor._set_default_parameters(params, "generate_sine")
        
        # 指定したパラメーターは保持され、不足分のみ追加されることを確認
        self.assertEqual(filled_params.get("freq"), 880.0)
        self.assertEqual(filled_params.get("amp"), 0.5)
        self.assertEqual(filled_params.get("duration"), 1.0)
    
    def test_code_generation(self):
        """
        コード生成のテスト
        """
        # 正弦波生成のコードテスト
        params = {"freq": 440.0, "amp": 0.5, "duration": 1.0}
        code = self.processor._generate_code("generate_sine", params)
        
        # 必要なパラメーターが含まれていることを確認
        self.assertIn("SinOsc.ar(440.0", code)
        self.assertIn("0.5", code)
        self.assertIn("Env.linen(0.01, 1.0", code)
        
        # ノコギリ波生成のコードテスト
        code = self.processor._generate_code("generate_sawtooth", params)
        self.assertIn("Saw.ar(440.0", code)
    
    def test_full_process_flow(self):
        """
        処理フロー全体のテスト
        """
        # 正常パターン
        result = self.processor.process("440Hzの正弦波を2秒間鳴らして")
        
        self.assertEqual(result.get("status"), "success")
        self.assertEqual(result.get("intent"), "generate_sine")
        self.assertEqual(result.get("parameters").get("freq"), 440.0)
        self.assertEqual(result.get("parameters").get("duration"), 2.0)
        self.assertIsNotNone(result.get("code"))

    def test_error_handling(self):
        """
        エラー処理のテスト
        """
        # 意図認識エラー
        result = self.processor.process("これは音に関係ない文章です")
        self.assertEqual(result.get("status"), "error")
        self.assertEqual(result.get("error_type"), "intent_recognition")
        
        # コード生成エラー（存在しない意図を指定）
        with patch.object(self.processor, '_recognize_intent', return_value=("non_existent_intent", None)):
            result = self.processor.process("テスト")
            self.assertEqual(result.get("status"), "error")
            self.assertEqual(result.get("error_type"), "code_generation")


if __name__ == "__main__":
    unittest.main()
