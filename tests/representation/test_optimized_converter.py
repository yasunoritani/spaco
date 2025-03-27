#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
SPACO - 最適化された表現レベル間の変換テスト

このモジュールは、最適化された表現レベル間の変換クラスのテストを提供します。
"""

import unittest
import time
from src.language_processor.representation.base import ValidationError
from src.language_processor.representation.intent_level import IntentLevel, IntentType
from src.language_processor.representation.parameter_level import ParameterLevel, ParameterValue, ParameterType
from src.language_processor.representation.structure_level import StructureLevel, StructureComponent, StructureType
from src.language_processor.representation.code_level import CodeLevel, CodeVariable, CodeType
from src.language_processor.representation.optimized_converter import (
    MemoizedConverter, MemoizedIntentToParameterConverter,
    MemoizedParameterToStructureConverter, MemoizedStructureToCodeConverter,
    OptimizedConversionPipeline
)


class TestMemoizedIntentToParameterConverter(unittest.TestCase):
    """最適化された意図レベルからパラメータレベルへの変換クラスのテスト"""
    
    def setUp(self):
        """テスト前の準備"""
        # キャッシュ統計情報を有効化
        self.converter = MemoizedIntentToParameterConverter(cache_stats=True)
    
    def test_basic_conversion(self):
        """基本的な変換のテスト"""
        # 同じ意図を2回変換し、2回目はキャッシュから取得されるはず
        intent = IntentLevel(IntentType.GENERATE_SOUND, "440Hzの正弦波を生成")
        
        # 1回目の変換
        start_time = time.time()
        param_level1 = self.converter.convert(intent)
        first_conversion_time = time.time() - start_time
        
        # 同じ意図で2回目の変換
        start_time = time.time()
        param_level2 = self.converter.convert(intent)
        second_conversion_time = time.time() - start_time
        
        # 結果が同じであることを確認
        self.assertEqual(param_level1.to_dict(), param_level2.to_dict())
        
        # キャッシュ統計情報を確認
        stats = self.converter.get_cache_stats()
        self.assertTrue(stats["enabled"])
        # 少なくとも1回はキャッシュミスが発生している
        self.assertGreaterEqual(stats["misses"], 1)
    
    def test_different_intents(self):
        """異なる意図の変換のテスト"""
        # 異なる意図に対しては別々にキャッシュされるはず
        intent1 = IntentLevel(IntentType.GENERATE_SOUND, "440Hzの正弦波を生成")
        intent2 = IntentLevel(IntentType.GENERATE_SOUND, "220Hzのノコギリ波を生成")
        
        param_level1 = self.converter.convert(intent1)
        param_level2 = self.converter.convert(intent2)
        
        # 異なる結果が得られることを確認
        self.assertNotEqual(param_level1.to_dict(), param_level2.to_dict())
        
        # 同じ意図を再度変換してキャッシュヒット
        param_level1_again = self.converter.convert(intent1)
        self.assertEqual(param_level1.to_dict(), param_level1_again.to_dict())
        
        # 統計情報を確認
        stats = self.converter.get_cache_stats()
        # 少なくとも2回はキャッシュミス（2種類の意図）が発生している
        self.assertGreaterEqual(stats["misses"], 2)


class TestOptimizedConversionPipeline(unittest.TestCase):
    """最適化された変換パイプラインのテスト"""
    
    def setUp(self):
        """テスト前の準備"""
        self.pipeline = OptimizedConversionPipeline(cache_stats=True)
    
    def test_full_conversion_chain(self):
        """完全な変換チェーンのテスト"""
        # 同じ意図を2回変換し、2回目はキャッシュを活用するはず
        intent = IntentLevel(IntentType.GENERATE_SOUND, "440Hzの正弦波を生成")
        
        # 1回目の変換
        start_time = time.time()
        code_level1 = self.pipeline.convert_intent_to_code(intent)
        first_conversion_time = time.time() - start_time
        
        # 同じ意図で2回目の変換
        start_time = time.time()
        code_level2 = self.pipeline.convert_intent_to_code(intent)
        second_conversion_time = time.time() - start_time
        
        # 結果が同じであることを確認
        self.assertEqual(code_level1.to_dict(), code_level2.to_dict())
        
        # キャッシュ統計情報を確認
        stats = self.pipeline.get_cache_stats()
        # 各コンバーターで少なくとも1回のキャッシュミスが発生しているはず
        self.assertGreaterEqual(stats["intent_to_param"]["misses"], 1)
        self.assertGreaterEqual(stats["param_to_structure"]["misses"], 1)
        self.assertGreaterEqual(stats["structure_to_code"]["misses"], 1)
    
    def test_performance_with_different_intents(self):
        """異なる意図でのパフォーマンステスト"""
        # 複数の異なる意図を変換し、処理時間を測定
        intents = [
            IntentLevel(IntentType.GENERATE_SOUND, f"{freq}Hzの正弦波を生成")
            for freq in [440, 880, 220, 110, 1760]
        ]
        
        # 各意図を一度変換
        for intent in intents:
            code_level = self.pipeline.convert_intent_to_code(intent)
            self.assertIsInstance(code_level, CodeLevel)
        
        # 同じ意図を再度変換（キャッシュから取得されるはず）
        for intent in intents:
            code_level = self.pipeline.convert_intent_to_code(intent)
            self.assertIsInstance(code_level, CodeLevel)
        
        # キャッシュ統計情報を確認
        stats = self.pipeline.get_cache_stats()
        # 少なくとも5回のキャッシュミスが各コンバーターで発生しているはず
        self.assertGreaterEqual(stats["intent_to_param"]["misses"], 5)
        self.assertGreaterEqual(stats["param_to_structure"]["misses"], 5)
        self.assertGreaterEqual(stats["structure_to_code"]["misses"], 5)


if __name__ == "__main__":
    unittest.main()
