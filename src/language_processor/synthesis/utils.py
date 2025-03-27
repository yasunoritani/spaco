#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
SPACO - 音響合成パターン ユーティリティモジュール

音響合成パターンに関する共通ユーティリティを提供します。
エラークラスや音符変換などの機能が含まれます。
"""

from typing import Dict, Any, List, Optional, Tuple, Union
import logging

logger = logging.getLogger(__name__)


class SynthesisPatternError(Exception):
    """音響合成パターン関連のエラー基底クラス"""
    def __init__(self, message, original_exception=None):
        super().__init__(message)
        self.original_exception = original_exception


class TemplateLoadingError(SynthesisPatternError):
    """テンプレートロードに関するエラー"""
    pass


class PatternMatchingError(SynthesisPatternError):
    """パターンマッチングに関するエラー"""
    pass


class ParameterExtractionError(SynthesisPatternError):
    """パラメータ抽出に関するエラー"""
    pass


class NoteConverter:
    """
    音符名と周波数の変換を行うクラス
    
    音楽的表記（C4、A#3など）と周波数（Hz）の相互変換機能を提供します。
    """
    
    def __init__(self):
        """音符変換機能を初期化します"""
        self.note_to_freq = self._create_note_to_freq_mapping()
        self.ja_note_names = self._create_japanese_note_names()
        logger.info("音符変換機能を初期化しました")
    
    def _create_note_to_freq_mapping(self) -> Dict[str, float]:
        """音符名と周波数のマッピングを作成します"""
        # 基本的な12音階のピッチクラス（C=0, C#/Db=1, ..., B=11）
        pitch_classes = {
            "C": 0, "C#": 1, "Db": 1,
            "D": 2, "D#": 3, "Eb": 3,
            "E": 4,
            "F": 5, "F#": 6, "Gb": 6,
            "G": 7, "G#": 8, "Ab": 8,
            "A": 9, "A#": 10, "Bb": 10,
            "B": 11
        }
        
        # 音符名から周波数へのマッピングを生成
        note_to_freq = {}
        
        # 各オクターブについて
        for octave in range(0, 9):
            for note_name, semitones in pitch_classes.items():
                # 音符名の生成（例: "C4", "A#5"）
                note = f"{note_name}{octave}"
                
                # 周波数の計算: A4 = 440Hz, 半音上がるごとに2^(1/12)倍
                # C0を基準とし、A4まで57半音
                semitones_from_c0 = semitones + (octave * 12)
                semitones_from_a4 = semitones_from_c0 - 57
                freq = 440.0 * (2 ** (semitones_from_a4 / 12.0))
                
                note_to_freq[note] = round(freq, 2)
                
                # C, D, E, F, G, A, B の場合、オクターブなしの表記も追加
                if len(note_name) == 1 and octave == 4:
                    note_to_freq[note_name] = round(freq, 2)
                
                # シャープやフラットを含む表記で、オクターブが4の場合も登録
                if len(note_name) == 2 and octave == 4:
                    note_to_freq[note_name] = round(freq, 2)
        
        return note_to_freq
    
    def _create_japanese_note_names(self) -> Dict[str, str]:
        """日本語の音名と西洋音名のマッピングを作成します"""
        return {
            "ド": "C", "ド#": "C#", "レ♭": "Db",
            "レ": "D", "レ#": "D#", "ミ♭": "Eb",
            "ミ": "E",
            "ファ": "F", "ファ#": "F#", "ソ♭": "Gb",
            "ソ": "G", "ソ#": "G#", "ラ♭": "Ab",
            "ラ": "A", "ラ#": "A#", "シ♭": "Bb",
            "シ": "B",
            # 別表記も追加
            "ドのシャープ": "C#", "レのフラット": "Db",
            "レのシャープ": "D#", "ミのフラット": "Eb",
            "ファのシャープ": "F#", "ソのフラット": "Gb",
            "ソのシャープ": "G#", "ラのフラット": "Ab",
            "ラのシャープ": "A#", "シのフラット": "Bb"
        }
    
    def note_to_frequency(self, note_name: str, default_octave: int = 4) -> Optional[float]:
        """
        音符名を周波数に変換します
        
        引数:
            note_name: 音符名（例: 'A4', 'C#', 'ド', 'ファ#'）
            default_octave: オクターブが指定されていない場合のデフォルト値
            
        戻り値:
            float: 周波数（Hz）、変換できない場合はNone
        """
        try:
            # 日本語音名から西洋音名へ変換
            for ja_name, western_name in self.ja_note_names.items():
                if ja_name in note_name:
                    note_name = note_name.replace(ja_name, western_name)
                    break
            
            # オクターブが指定されていない場合、デフォルト値を追加
            if note_name[-1] not in "0123456789":
                note_name = f"{note_name}{default_octave}"
            
            # マッピングから周波数を取得
            if note_name in self.note_to_freq:
                return self.note_to_freq[note_name]
            
            # 変換できない場合
            logger.warning(f"音符名 '{note_name}' を周波数に変換できませんでした")
            return None
            
        except Exception as e:
            logger.error(f"音符変換中にエラーが発生しました: {str(e)}")
            return None
    
    def frequency_to_nearest_note(self, frequency: float) -> Optional[str]:
        """
        周波数に最も近い音符名を取得します
        
        引数:
            frequency: 周波数（Hz）
            
        戻り値:
            str: 最も近い音符名、変換できない場合はNone
        """
        try:
            # 周波数から半音数を計算（A4 = 440Hz基準）
            if frequency <= 0:
                logger.warning(f"無効な周波数: {frequency}Hz")
                return None
                
            semitones_from_a4 = 12 * (log2(frequency / 440.0))
            semitones_from_c0 = semitones_from_a4 + 57  # A4はC0から57半音上
            
            # オクターブと半音を計算
            octave = int(semitones_from_c0 / 12)
            semitone = round(semitones_from_c0 % 12)
            
            # 半音から音名を取得
            pitch_names = ["C", "C#", "D", "D#", "E", "F", "F#", "G", "G#", "A", "A#", "B"]
            pitch_name = pitch_names[semitone]
            
            return f"{pitch_name}{octave}"
            
        except Exception as e:
            logger.error(f"周波数変換中にエラーが発生しました: {str(e)}")
            return None
