#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
SPACO - 音響合成パターン パラメータ抽出モジュール

このモジュールは、自然言語指示からパラメータを抽出するための機能を提供します。
定性的表現（「強い」「弱い」など）から数値への変換やデフォルト値の設定を行います。
"""

from typing import Dict, Any, List, Optional, Tuple, Union
import re
import logging
from .utils import ParameterExtractionError, NoteConverter

logger = logging.getLogger(__name__)


class ParameterExtractor:
    """
    パラメータ抽出クラス
    
    自然言語指示からパラメータを抽出するための機能を提供します。
    定性的表現（「強い」「弱い」など）から数値への変換、
    デフォルト値の設定などを行います。
    """
    
    def __init__(self):
        """パラメータ抽出機能を初期化します"""
        # 音符変換機能の初期化
        self.note_converter = NoteConverter()
        
        # 定性的表現のマッピングを作成
        self.qualitative_expressions = self._create_qualitative_expressions()
        
        logger.info("パラメータ抽出機能を初期化しました")
    
    def _create_qualitative_expressions(self) -> Dict[str, Dict[str, Dict[str, float]]]:
        """
        定性的表現のマッピングを作成します
        
        戻り値:
            Dict[str, Dict[str, Dict[str, float]]]: パラメータごとの定性的表現のマッピング
        """
        return {
            # 音量（amp）に関する表現
            "amp": {
                "強さ": {
                    r"(?:とても|かなり|非常に)(?:強く|大きく)": 0.9,
                    r"(?:強く|大きく)": 0.7,
                    r"(?:普通|中くらい)(?:の|に|)(?:大きさ|強さ)": 0.5,
                    r"(?:弱く|小さく)": 0.3,
                    r"(?:とても|かなり|非常に)(?:弱く|小さく)": 0.1
                }
            },
            
            # 持続時間（duration）に関する表現
            "duration": {
                "長さ": {
                    r"(?:とても|かなり|非常に)(?:長く|長い)": 5.0,
                    r"(?:長く|長い)": 3.0,
                    r"(?:普通|中くらい)(?:の|に|)(?:長さ)": 1.0,
                    r"(?:短く|短い)": 0.5,
                    r"(?:とても|かなり|非常に)(?:短く|短い)": 0.2
                }
            },
            
            # アタック時間（attack）に関する表現
            "attack": {
                "立ち上がり": {
                    r"(?:とても|かなり|非常に)(?:緩やか|ゆっくり)(?:な|の|)(?:立ち上がり)": 2.0,
                    r"(?:緩やか|ゆっくり)(?:な|の|)(?:立ち上がり)": 0.5,
                    r"(?:普通|中くらい)(?:の|な|)(?:立ち上がり)": 0.1,
                    r"(?:速い|急な|シャープな)(?:立ち上がり)": 0.01,
                    r"(?:とても|かなり|非常に)(?:速い|急な|シャープな)(?:立ち上がり)": 0.001
                }
            },
            
            # リリース時間（release）に関する表現
            "release": {
                "余韻": {
                    r"(?:とても|かなり|非常に)(?:長い|多い)(?:余韻|残響)": 2.0,
                    r"(?:長い|多い)(?:余韻|残響)": 1.0,
                    r"(?:普通|中くらい)(?:の|な|)(?:余韻|残響)": 0.5,
                    r"(?:短い|少ない)(?:余韻|残響)": 0.1,
                    r"(?:とても|かなり|非常に)(?:短い|少ない)(?:余韻|残響)": 0.01
                }
            },
            
            # フィルター周波数（filter_freq）に関する表現
            "filter_freq": {
                "明るさ": {
                    r"(?:とても|かなり|非常に)(?:明るい|明るく)": 5000.0,
                    r"(?:明るい|明るく)": 2000.0,
                    r"(?:普通|中くらい)(?:の|な|)(?:明るさ)": 1000.0,
                    r"(?:暗い|暗く|こもった)": 500.0,
                    r"(?:とても|かなり|非常に)(?:暗い|暗く|こもった)": 200.0
                }
            },
            
            # リバーブミックス（reverb_mix）に関する表現
            "reverb_mix": {
                "残響感": {
                    r"(?:とても|かなり|非常に)(?:強い|多い)(?:残響|リバーブ)": 0.8,
                    r"(?:強い|多い)(?:残響|リバーブ)": 0.5,
                    r"(?:普通|中くらい)(?:の|な|)(?:残響|リバーブ)": 0.3,
                    r"(?:弱い|少ない)(?:残響|リバーブ)": 0.2,
                    r"(?:とても|かなり|非常に)(?:弱い|少ない)(?:残響|リバーブ)": 0.1
                }
            },
            
            # ディストーション量（distortion_amount）に関する表現
            "distortion_amount": {
                "歪み": {
                    r"(?:とても|かなり|非常に)(?:強い|多い)(?:歪み|ディストーション)": 20.0,
                    r"(?:強い|多い)(?:歪み|ディストーション)": 10.0,
                    r"(?:普通|中くらい)(?:の|な|)(?:歪み|ディストーション)": 5.0,
                    r"(?:弱い|少ない)(?:歪み|ディストーション)": 2.0,
                    r"(?:とても|かなり|非常に)(?:弱い|少ない)(?:歪み|ディストーション)": 1.0
                }
            }
        }
    
    def extract_parameters(self, input_text: str, intent: str, match: Optional[re.Match]) -> Dict[str, Any]:
        """
        自然言語指示からパラメーターを抽出します
        
        引数:
            input_text: 処理する自然言語指示
            intent: 認識された意図
            match: 一致したパターンのマッチオブジェクト
            
        戻り値:
            Dict[str, Any]: 抽出されたパラメーター
        """
        params = {}
        
        try:
            # 基本パラメータの抽出
            params.update(self._extract_basic_parameters(input_text, intent, match))
            
            # 定性的表現からのパラメータ抽出
            params.update(self._extract_qualitative_parameters(input_text))
            
            # 特定のパターンに対する追加パラメータの抽出
            params.update(self._extract_specific_parameters(input_text, intent))
            
            return params
            
        except Exception as e:
            logger.exception(f"パラメーター抽出中にエラーが発生しました: {str(e)}")
            raise ParameterExtractionError(f"パラメータ抽出エラー: {str(e)}", original_exception=e)
    
    def _extract_basic_parameters(self, input_text: str, intent: str, match: Optional[re.Match]) -> Dict[str, Any]:
        """
        基本的なパラメータを抽出します
        
        引数:
            input_text: 処理する自然言語指示
            intent: 認識された意図
            match: 一致したパターンのマッチオブジェクト
            
        戻り値:
            Dict[str, Any]: 抽出された基本パラメーター
        """
        params = {}
        
        # 周波数の抽出
        if match and intent in ["generate_sine", "generate_sawtooth", "generate_square", "generate_triangle"]:
            value = match.group(1) if match.groups() else None
            
            if value:
                # 数値の場合
                if re.match(r"^\d+(?:\.\d+)?$", value):
                    params["freq"] = float(value)
                
                # 音符名の場合
                else:
                    freq = self.note_converter.note_to_frequency(value)
                    if freq:
                        params["freq"] = freq
        
        # 音量の抽出（百分率表記）
        volume_match = re.search(r"音量[をは]?(\d+(?:\.\d+)?)%", input_text)
        if volume_match:
            volume_percent = float(volume_match.group(1))
            params["amp"] = volume_percent / 100.0
        
        # 持続時間の抽出
        duration_match = re.search(r"(\d+(?:\.\d+)?)\s*(?:秒間|秒)", input_text)
        if duration_match:
            params["duration"] = float(duration_match.group(1))
        
        # BPM(テンポ)の抽出
        bpm_match = re.search(r"(\d+(?:\.\d+)?)\s*(?:BPM|bpm|テンポ)", input_text)
        if bpm_match:
            bpm = float(bpm_match.group(1))
            # BPMを秒に変換（4分音符1拍の長さ）
            if "duration" not in params:  # 明示的な秒指定がない場合のみ
                params["duration"] = 60.0 / bpm
        
        return params
    
    def _extract_qualitative_parameters(self, input_text: str) -> Dict[str, Any]:
        """
        定性的表現からパラメータを抽出します
        
        引数:
            input_text: 処理する自然言語指示
            
        戻り値:
            Dict[str, Any]: 定性的表現から抽出されたパラメーター
        """
        params = {}
        
        # 各パラメータタイプについてチェック
        for param_type, categories in self.qualitative_expressions.items():
            # 各カテゴリ（「強さ」「長さ」など）について
            for category, expressions in categories.items():
                # 各表現をチェック
                for expr, value in expressions.items():
                    if re.search(expr, input_text, re.IGNORECASE):
                        logger.info(f"定性的表現を検出しました: {expr} => {param_type}={value}")
                        params[param_type] = value
                        # 同じパラメータタイプの他の表現はチェックしない
                        break
        
        return params
    
    def _extract_specific_parameters(self, input_text: str, intent: str) -> Dict[str, Any]:
        """
        特定のパターンに対する追加パラメータを抽出します
        
        引数:
            input_text: 処理する自然言語指示
            intent: 認識された意図
            
        戻り値:
            Dict[str, Any]: 特定のパターン用に抽出されたパラメーター
        """
        params = {}
        
        # フィルター関連
        if intent in ["generate_lowpass", "generate_highpass", "generate_bandpass"]:
            # フィルター周波数の抽出
            filter_freq_match = re.search(r"(\d+(?:\.\d+)?)\s*(?:Hz|ヘルツ)(?:で|の|に)(?:カット|通過)", input_text)
            if filter_freq_match:
                params["filter_freq"] = float(filter_freq_match.group(1))
            
            # Qファクタの抽出（バンドパスフィルター用）
            if intent == "generate_bandpass":
                q_match = re.search(r"Q(?:値|ファクタ|)[=は]?(\d+(?:\.\d+)?)", input_text)
                if q_match:
                    params["q"] = float(q_match.group(1))
        
        # リバーブ関連
        elif intent == "generate_reverb":
            # 部屋の大きさの抽出
            room_match = re.search(r"(?:部屋|ルーム)(?:の大きさ|サイズ)[=は]?(\d+(?:\.\d+)?)", input_text)
            if room_match:
                params["reverb_size"] = min(1.0, float(room_match.group(1)) / 10.0)  # 0～1の範囲に正規化
        
        # ディレイ関連
        elif intent == "generate_delay":
            # ディレイタイムの抽出
            delay_time_match = re.search(r"(\d+(?:\.\d+)?)\s*(?:ミリ秒|ms)(?:の|で)ディレイ", input_text)
            if delay_time_match:
                delay_ms = float(delay_time_match.group(1))
                params["delay_time"] = delay_ms / 1000.0  # ミリ秒を秒に変換
        
        return params
    
    def set_default_parameters(self, params: Dict[str, Any], intent: str) -> Dict[str, Any]:
        """
        不足しているパラメーターにデフォルト値を設定します
        
        引数:
            params: 既存のパラメーター辞書
            intent: 認識された意図
            
        戻り値:
            Dict[str, Any]: デフォルト値が設定されたパラメーター辞書
        """
        # 基本的なデフォルト値
        defaults = {
            "freq": 440.0,      # A4
            "amp": 0.5,         # 中程度の音量
            "duration": 1.0,    # 1秒
            "attack": 0.01,     # 10ミリ秒のアタック
            "release": 0.01,    # 10ミリ秒のリリース
            "pulse_width": 0.5  # 矩形波のデューティ比 50%
        }
        
        # 意図に応じて特定のデフォルト値を追加
        if intent in ["generate_lowpass", "generate_highpass", "generate_bandpass"]:
            defaults.update({
                "filter_freq": 1000.0,  # フィルター周波数
                "q": 1.0,               # Q値（バンドパスフィルター用）
                "source_type": "WhiteNoise",  # 音源タイプ
                "source_param": "{amp}"  # 音源パラメータ
            })
            
        elif intent == "generate_pad":
            defaults.update({
                "detune_factor1": 1.005,  # デチューン係数1
                "detune_factor2": 1.003,  # デチューン係数2
                "filter_freq": 1000.0,    # フィルター周波数
                "decay": 0.2,             # ディケイ
                "sustain": 0.7,           # サスティン
                "attack": 1.0,            # アタックは長め
                "release": 2.0            # リリースも長め
            })
            
        elif intent == "generate_pluck":
            defaults.update({
                "exciter_decay": 0.01,   # エクサイターのディケイ
                "filter_mult": 8.0,      # フィルター周波数乗数
                "attack": 0.001          # アタックは非常に短く
            })
            
        elif intent == "generate_percussion":
            defaults.update({
                "exciter_decay": 0.05,   # エクサイターのディケイ
                "ring_freq1": 1.5,       # 共鳴周波数1
                "ring_freq2": 2.0,       # 共鳴周波数2
                "ring_time1": 0.05,      # 共鳴時間1
                "ring_time2": 0.1,       # 共鳴時間2
                "ring_time3": 0.02,      # 共鳴時間3
                "hpf_freq": 200.0,       # ハイパスフィルター周波数
                "attack": 0.001          # アタックは非常に短く
            })
            
        elif intent == "generate_reverb":
            defaults.update({
                "reverb_mix": 0.33,       # リバーブミックス（ドライ/ウェット）
                "reverb_size": 0.7,       # 部屋の大きさ
                "reverb_damp": 0.5,       # 高周波減衰
                "reverb_tail": 1.5,       # リバーブテール
                "source_type": "SinOsc",  # 音源タイプ
                "source_param": "{freq}, 0, {amp}",  # 音源パラメータ
                "src_duration": "{duration} * 0.5"   # 音源の持続時間
            })
            
        elif intent == "generate_delay":
            defaults.update({
                "max_delay_time": 1.0,     # 最大ディレイタイム
                "delay_time": 0.25,        # ディレイタイム（1/4秒）
                "delay_feedback": 2.0,     # フィードバック量
                "delay_tail": 0.5,         # ディレイテール
                "source_type": "SinOsc",   # 音源タイプ
                "source_param": "{freq}, 0, {amp}",  # 音源パラメータ
                "src_duration": "{duration} * 0.5"   # 音源の持続時間
            })
            
        elif intent == "generate_distortion":
            defaults.update({
                "distortion_amount": 5.0,   # 歪みの強さ
                "source_type": "SinOsc",    # 音源タイプ
                "source_param": "{freq}, 0, {amp}"   # 音源パラメータ
            })
            
        elif intent == "generate_metal":
            defaults.update({
                "freq_ratios": "[1, 1.7, 2.8, 3.4]",   # 周波数比
                "amp_ratios": "[1, 0.6, 0.3, 0.2]",    # 振幅比
                "ring_ratios": "[1, 0.8, 0.6, 0.4]",   # 共鳴時間比
                "impulse_freq": 0.1,                    # インパルス周波数
                "impulse_amp": 0.1                      # インパルス振幅
            })
            
        elif intent == "generate_noise":
            defaults.update({
                "noise_type": "WhiteNoise",  # ノイズタイプ
                "q": 1.0                      # Q値
            })
        
        # 不足しているパラメーターにデフォルト値を設定
        for param, default_value in defaults.items():
            if param not in params:
                params[param] = default_value
        
        return params
    
    def validate_parameters(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """
        パラメーターを検証し、必要に応じて調整します
        
        引数:
            params: パラメーター辞書
            
        戻り値:
            Dict[str, Any]: 検証・調整後のパラメーター辞書
        """
        # 周波数の有効範囲チェック（20Hz～20,000Hz）
        if "freq" in params:
            params["freq"] = max(20.0, min(20000.0, params["freq"]))
        
        # 振幅の有効範囲チェック（0～1）
        if "amp" in params:
            params["amp"] = max(0.0, min(1.0, params["amp"]))
        
        # 持続時間の有効範囲チェック（0.01秒～30秒）
        if "duration" in params:
            params["duration"] = max(0.01, min(30.0, params["duration"]))
        
        # アタック時間の有効範囲チェック（0.001秒～10秒）
        if "attack" in params:
            params["attack"] = max(0.001, min(10.0, params["attack"]))
        
        # リリース時間の有効範囲チェック（0.001秒～10秒）
        if "release" in params:
            params["release"] = max(0.001, min(10.0, params["release"]))
        
        return params
