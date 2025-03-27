#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
SPACO - 音響合成パターン 認識モジュール

このモジュールは、自然言語指示からパターンを認識するための機能を提供します。
正規表現パターンと意図のマッピングを管理します。
"""

from typing import Dict, Any, List, Optional, Tuple, Union
import re
import logging
from .utils import PatternMatchingError

logger = logging.getLogger(__name__)


class PatternMatcher:
    """
    パターン認識クラス
    
    自然言語指示からパターンを認識するための機能を提供します。
    正規表現パターンと意図のマッピングを管理し、マッチングを行います。
    """
    
    def __init__(self):
        """パターン認識機能を初期化します"""
        # 意図認識パターン
        self.intent_patterns = self._create_intent_patterns()
        logger.info(f"{sum(len(patterns) for patterns in self.intent_patterns.values())}個のパターンを初期化しました")
    
    def _create_intent_patterns(self) -> Dict[str, List[str]]:
        """
        認識パターン辞書を作成します
        
        戻り値:
            Dict[str, List[str]]: 意図とそれに対応するパターンのマッピング
        """
        return {
            # 基本的なオシレーター
            "generate_sine": [
                r"(\d+(?:\.\d+)?)\s*(?:Hz|ヘルツ)の(?:正弦波|サイン波)",
                r"サイン波を(\d+(?:\.\d+)?)\s*(?:Hz|ヘルツ)で",
                r"([A-G][#b♯♭]?\d?)(?:の音|音|)\s*(?:を鳴らして|を生成して)",
                r"(ド|レ|ミ|ファ|ソ|ラ|シ)[#♯b♭]?(?:\d?)(?:の音|音|)\s*(?:を鳴らして|を生成して)"
            ],
            "generate_sawtooth": [
                r"ノコギリ波.+?(\d+(?:\.\d+)?)\s*(?:Hz|ヘルツ)",
                r"ノコギリ波で([A-G][#b♯♭]?\d?)(?:の音|音|)",
                r"([A-G][#b♯♭]?\d?).+?ノコギリ波",
                r"(ド|レ|ミ|ファ|ソ|ラ|シ)[#♯b♭]?(?:\d?).+?ノコギリ波"
            ],
            "generate_square": [
                r"矩形波.+?(\d+(?:\.\d+)?)\s*(?:Hz|ヘルツ)",
                r"矩形波で([A-G][#b♯♭]?\d?)(?:の音|音|)",
                r"([A-G][#b♯♭]?\d?).+?矩形波",
                r"(ド|レ|ミ|ファ|ソ|ラ|シ)[#♯b♭]?(?:\d?).+?矩形波"
            ],
            "generate_triangle": [
                r"三角波.+?(\d+(?:\.\d+)?)\s*(?:Hz|ヘルツ)",
                r"三角波で([A-G][#b♯♭]?\d?)(?:の音|音|)",
                r"([A-G][#b♯♭]?\d?).+?三角波",
                r"(ド|レ|ミ|ファ|ソ|ラ|シ)[#♯b♭]?(?:\d?).+?三角波"
            ],
            
            # エンベロープを使用した音
            "generate_pad": [
                r"パッドサウンド",
                r"柔らかい音色",
                r"持続(?:する|した)音",
                r"シンセパッド"
            ],
            "generate_pluck": [
                r"弦(?:の|みたい|のような)音",
                r"ピック(?:の|みたい|のような)音",
                r"プラック(?:の|みたい|のような)音",
                r"ギター(?:の|みたい|のような)音"
            ],
            "generate_percussion": [
                r"打楽器(?:の|みたい|のような)音",
                r"ドラム(?:の|みたい|のような)音",
                r"パーカッション(?:の|みたい|のような)音",
                r"叩(?:く|いた)音"
            ],
            
            # フィルター
            "generate_lowpass": [
                r"ローパス(?:フィルター|フィルタ).+?(\d+(?:\.\d+)?)\s*(?:Hz|ヘルツ)",
                r"低域通過(?:フィルター|フィルタ)",
                r"高音をカット"
            ],
            "generate_highpass": [
                r"ハイパス(?:フィルター|フィルタ).+?(\d+(?:\.\d+)?)\s*(?:Hz|ヘルツ)",
                r"高域通過(?:フィルター|フィルタ)",
                r"低音をカット"
            ],
            "generate_bandpass": [
                r"バンドパス(?:フィルター|フィルタ).+?(\d+(?:\.\d+)?)\s*(?:Hz|ヘルツ)",
                r"帯域通過(?:フィルター|フィルタ)",
                r"特定の周波数(?:だけ|のみ)を通(?:す|した)"
            ],
            
            # エフェクト
            "generate_reverb": [
                r"リバーブ(?:の|を|が)(?:かかった|強い|付いた)",
                r"残響(?:の|を|が)(?:ある|多い)",
                r"エコー(?:の|が)(?:ある|多い)",
                r"(?:広い|大きな)空間"
            ],
            "generate_delay": [
                r"(?:ディレイ|遅延)(?:の|を|が)(?:かかった|強い|付いた)",
                r"エコー(?:の|を|が)(?:ある|強い)",
                r"繰り返(?:す|し)(?:音|効果)"
            ],
            "generate_distortion": [
                r"(?:ディストーション|歪み)(?:の|を|が)(?:かかった|強い|付いた)",
                r"歪んだ音",
                r"ギター(?:の|みたいな)(?:歪み|ディストーション)"
            ],
            
            # 特殊な音響
            "generate_metal": [
                r"金属(?:的|みたいな|のような)(?:音|音色)",
                r"メタリック(?:な|の|)(?:音|音色)",
                r"(?:鐘|ベル)(?:の|みたいな|のような)(?:音|音色)"
            ],
            "generate_noise": [
                r"(?:ノイズ|雑音)(?:の|を|が)",
                r"ホワイトノイズ",
                r"ピンクノイズ",
                r"(?:波|風|雨)(?:の|みたいな|のような)(?:音|音色)"
            ]
        }
    
    def match_intent(self, input_text: str) -> Tuple[Optional[str], Optional[str], Optional[re.Match]]:
        """
        自然言語指示から意図を認識します
        
        引数:
            input_text: 処理する自然言語指示
            
        戻り値:
            Tuple[Optional[str], Optional[str], Optional[re.Match]]: 
                (認識された意図, 一致したパターン, マッチオブジェクト)
        """
        try:
            for intent, patterns in self.intent_patterns.items():
                for pattern in patterns:
                    match = re.search(pattern, input_text, re.IGNORECASE)
                    if match:
                        logger.info(f"意図を認識しました: {intent}, パターン: {pattern}")
                        return intent, pattern, match
            
            # 意図を認識できなかった場合
            logger.warning(f"意図を認識できませんでした: {input_text}")
            return None, None, None
            
        except Exception as e:
            logger.exception(f"パターンマッチング中にエラーが発生しました: {str(e)}")
            raise PatternMatchingError(f"パターンマッチングエラー: {str(e)}", original_exception=e)
    
    def get_all_patterns(self) -> Dict[str, List[str]]:
        """
        すべての認識パターンを取得します
        
        戻り値:
            Dict[str, List[str]]: すべてのパターン辞書
        """
        return self.intent_patterns.copy()
