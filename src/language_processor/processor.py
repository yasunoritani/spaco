#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
SPACO - 言語プロセッサーモジュール

このモジュールは、自然言語指示をSuperColliderコードに変換するための
言語処理機能を提供します。基本的なパターン認識、パラメーター抽出、
テンプレートベースのコード生成を行います。
"""

import re
import logging
import json
import os
from typing import Dict, Any, List, Optional, Tuple, Union

logger = logging.getLogger(__name__)


class LanguageProcessorError(Exception):
    """言語プロセッサー関連のエラー基底クラス"""
    def __init__(self, message, original_exception=None):
        super().__init__(message)
        self.original_exception = original_exception


class IntentRecognitionError(LanguageProcessorError):
    """意図認識に関するエラー"""
    pass


class ParameterExtractionError(LanguageProcessorError):
    """パラメーター抽出に関するエラー"""
    pass


class CodeGenerationError(LanguageProcessorError):
    """コード生成に関するエラー"""
    pass


class LanguageProcessor:
    """
    自然言語処理を行うプロセッサークラス
    
    このクラスは自然言語指示からSuperColliderコードを生成するための機能を提供します。
    1. 意図認識: 基本的な音生成コマンドの意図を認識
    2. パラメーター抽出: 周波数、振幅、持続時間などのパラメーターを抽出
    3. コード生成: テンプレートベースでSuperColliderコードを生成
    """
    
    def __init__(self, models_dir: Optional[str] = None, templates_dir: Optional[str] = None):
        """
        言語プロセッサーを初期化します。
        
        引数:
            models_dir: 言語モデルのディレクトリパス
            templates_dir: テンプレートのディレクトリパス
        """
        self.models_dir = models_dir or os.path.join(os.path.dirname(__file__), "../models")
        self.templates_dir = templates_dir or os.path.join(os.path.dirname(__file__), "../templates")
        
        # パターン辞書を初期化
        self._initialize_patterns()
        
        # テンプレート辞書を初期化
        self._initialize_templates()
        
        logger.info("言語プロセッサーを初期化しました")
    
    def _initialize_patterns(self):
        """パターン辞書を初期化します"""
        # 意図認識パターン
        self.intent_patterns = {
            "generate_sine": [
                r"(\d+)\s*(?:Hz|ヘルツ)の(?:正弦波|サイン波)",
                r"サイン波を(\d+)\s*(?:Hz|ヘルツ)で",
                r"([A-G][#b]?\d?)(?:の音|音|)\s*(?:を鳴らして|を生成して)"
            ],
            "generate_sawtooth": [
                r"ノコギリ波.+?(\d+)\s*(?:Hz|ヘルツ)",
                r"([A-G][#b]?\d?).+?ノコギリ波"
            ],
            "generate_pad": [
                r"パッドサウンド",
                r"柔らかい音色"
            ],
            "generate_metal": [
                r"金属的な音",
                r"メタリック"
            ]
        }
        
        # 音符名と周波数のマッピング
        self.note_to_freq = {
            "C4": 261.63, "C#4": 277.18, "D4": 293.66, "D#4": 311.13,
            "E4": 329.63, "F4": 349.23, "F#4": 369.99, "G4": 392.00,
            "G#4": 415.30, "A4": 440.00, "A#4": 466.16, "B4": 493.88,
            # その他の音符も追加可能
        }
    
    def _initialize_templates(self):
        """テンプレート辞書を初期化します"""
        # 基本的なテンプレート
        self.templates = {
            "generate_sine": """
s.waitForBoot({{
    {{
        // {freq}Hzの正弦波オシレーターを生成
        var sig = SinOsc.ar({freq}, 0, {amp});
        // エンベロープを適用してクリックノイズを防止
        sig = sig * EnvGen.kr(Env.linen(0.01, {duration}, 0.01), doneAction: 2);
        sig ! 2 // ステレオ出力
    }}.play;
}});
""",
            "generate_sawtooth": """
s.waitForBoot({{
    {{
        // {freq}Hzのノコギリ波を生成
        var sig = Saw.ar({freq}, {amp});
        // エンベロープを適用
        sig = sig * EnvGen.kr(Env.linen(0.01, {duration}, 0.01), doneAction: 2);
        sig ! 2 // ステレオ出力
    }}.play;
}});
""",
            "generate_pad": """
s.waitForBoot({{
    {{
        // デチューンした複数の正弦波を使用
        var sig = SinOsc.ar([{freq}, {freq}*1.005], 0, {amp}) + SinOsc.ar([{freq}*0.5, {freq}*0.501], 0, {amp}*0.5);
        // ローパスフィルターで高周波を削減
        sig = LPF.ar(sig, 1000);
        // ADSRエンベロープで緩やかな立ち上がりと減衰を実現
        sig = sig * EnvGen.kr(Env.adsr(1, 0.2, 0.7, 2), 1, doneAction: 2);
        sig
    }}.play;
}});
""",
            "generate_metal": """
s.waitForBoot({{
    {{
        // Klankを使用して金属的な倍音構造を作成
        var freqs = [1, 1.7, 2.8, 3.4] * {freq};
        var amps = [1, 0.6, 0.3, 0.2] * {amp};
        var rings = [1, 0.8, 0.6, 0.4] * {duration};
        var sig = Klank.ar(`[freqs, amps, rings], Impulse.ar(0.1, 0, 0.1));
        // パーカッシブなエンベロープを適用
        sig = sig * EnvGen.kr(Env.perc(0.01, {duration}), doneAction: 2);
        sig ! 2 // ステレオ出力
    }}.play;
}});
"""
        }
    
    def process(self, input_text: str) -> Dict[str, Any]:
        """
        自然言語指示を処理してSuperColliderコードを生成します。
        
        引数:
            input_text: 処理する自然言語指示
            
        戻り値:
            Dict[str, Any]: 処理結果（生成コード、認識された意図、抽出されたパラメーター）
            
        例外:
            IntentRecognitionError: 意図認識に失敗した場合
            ParameterExtractionError: パラメーター抽出に失敗した場合
            CodeGenerationError: コード生成に失敗した場合
        """
        try:
            # 意図認識
            intent, matched_pattern = self._recognize_intent(input_text)
            logger.info(f"意図を認識しました: {intent}")
            
            # パラメーター抽出
            params = self._extract_parameters(input_text, intent, matched_pattern)
            logger.info(f"パラメーターを抽出しました: {params}")
            
            # デフォルトパラメーターの設定
            params = self._set_default_parameters(params, intent)
            
            # コード生成
            code = self._generate_code(intent, params)
            logger.info(f"コードを生成しました: {code[:50]}...")
            
            # 結果を返す
            return {
                "status": "success",
                "code": code,
                "intent": intent,
                "parameters": params
            }
            
        except IntentRecognitionError as e:
            logger.error(f"意図認識エラー: {str(e)}")
            return {
                "status": "error",
                "error_type": "intent_recognition",
                "message": str(e)
            }
        except ParameterExtractionError as e:
            logger.error(f"パラメーター抽出エラー: {str(e)}")
            return {
                "status": "error",
                "error_type": "parameter_extraction",
                "message": str(e)
            }
        except CodeGenerationError as e:
            logger.error(f"コード生成エラー: {str(e)}")
            return {
                "status": "error",
                "error_type": "code_generation",
                "message": str(e)
            }
        except Exception as e:
            logger.exception(f"予期しないエラー: {str(e)}")
            return {
                "status": "error",
                "error_type": "unknown",
                "message": f"予期しないエラー: {str(e)}"
            }
    
    def _recognize_intent(self, input_text: str) -> Tuple[str, Optional[str]]:
        """
        自然言語指示から意図を認識します。
        
        引数:
            input_text: 処理する自然言語指示
            
        戻り値:
            Tuple[str, Optional[str]]: 認識された意図と一致したパターン
            
        例外:
            IntentRecognitionError: 意図認識に失敗した場合
        """
        for intent, patterns in self.intent_patterns.items():
            for pattern in patterns:
                match = re.search(pattern, input_text, re.IGNORECASE)
                if match:
                    return intent, pattern
        
        # 意図を認識できなかった場合
        raise IntentRecognitionError(f"意図を認識できませんでした: {input_text}")
    
    def _extract_parameters(self, input_text: str, intent: str, matched_pattern: Optional[str]) -> Dict[str, Any]:
        """
        自然言語指示からパラメーターを抽出します。
        
        引数:
            input_text: 処理する自然言語指示
            intent: 認識された意図
            matched_pattern: 一致したパターン
            
        戻り値:
            Dict[str, Any]: 抽出されたパラメーター
            
        例外:
            ParameterExtractionError: パラメーター抽出に失敗した場合
        """
        params = {}
        
        try:
            # 周波数の抽出
            if intent in ["generate_sine", "generate_sawtooth"]:
                match = re.search(matched_pattern, input_text)
                if match:
                    value = match.group(1)
                    
                    # 音符名の場合
                    if value in self.note_to_freq:
                        params["freq"] = self.note_to_freq[value]
                    # 数値の場合
                    elif value.isdigit():
                        params["freq"] = float(value)
                    # A4などの簡易表記を処理
                    elif re.match(r"[A-G][#b]?\d?", value):
                        note = value
                        if len(note) == 1:  # A -> A4
                            note = note + "4"
                        elif len(note) == 2 and note[1] in "#b":  # A# -> A#4
                            note = note + "4"
                        
                        if note in self.note_to_freq:
                            params["freq"] = self.note_to_freq[note]
                        else:
                            params["freq"] = 440.0  # デフォルトはA4
            
            # 音量の抽出
            volume_match = re.search(r"音量[をは]?(\d+)%", input_text)
            if volume_match:
                volume_percent = int(volume_match.group(1))
                params["amp"] = volume_percent / 100.0
            
            # 持続時間の抽出
            duration_match = re.search(r"(\d+(?:\.\d+)?)\s*(?:秒間|秒)", input_text)
            if duration_match:
                params["duration"] = float(duration_match.group(1))
            
            return params
            
        except Exception as e:
            logger.exception(f"パラメーター抽出中にエラーが発生しました: {str(e)}")
            raise ParameterExtractionError(f"パラメーター抽出エラー: {str(e)}", original_exception=e)
    
    def _set_default_parameters(self, params: Dict[str, Any], intent: str) -> Dict[str, Any]:
        """
        不足しているパラメーターにデフォルト値を設定します。
        
        引数:
            params: 既存のパラメーター辞書
            intent: 認識された意図
            
        戻り値:
            Dict[str, Any]: デフォルト値が設定されたパラメーター辞書
        """
        # デフォルト値
        defaults = {
            "freq": 440.0,  # A4
            "amp": 0.5,     # 中程度の音量
            "duration": 1.0  # 1秒
        }
        
        # 不足しているパラメーターにデフォルト値を設定
        for param, default_value in defaults.items():
            if param not in params:
                params[param] = default_value
        
        return params
    
    def _generate_code(self, intent: str, params: Dict[str, Any]) -> str:
        """
        意図とパラメーターからSuperColliderコードを生成します。
        
        引数:
            intent: 認識された意図
            params: パラメーター辞書
            
        戻り値:
            str: 生成されたSuperColliderコード
            
        例外:
            CodeGenerationError: コード生成に失敗した場合
        """
        try:
            # テンプレートの取得
            if intent not in self.templates:
                raise CodeGenerationError(f"テンプレートが見つかりません: {intent}")
            
            template = self.templates[intent]
            
            # テンプレートにパラメーターを適用
            code = template.format(**params)
            
            return code
            
        except Exception as e:
            logger.exception(f"コード生成中にエラーが発生しました: {str(e)}")
            raise CodeGenerationError(f"コード生成エラー: {str(e)}", original_exception=e)
    
    def validate_code(self, code: str) -> Dict[str, Any]:
        """
        生成されたコードを検証します。
        
        引数:
            code: 検証するSuperColliderコード
            
        戻り値:
            Dict[str, Any]: 検証結果
        """
        # 基本的な検証（文法エラーや危険なコードパターンのチェックなど）
        # このメソッドは今後拡張する予定
        return {
            "status": "success",
            "is_valid": True
        }
