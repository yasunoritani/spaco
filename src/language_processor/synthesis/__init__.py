#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
SPACO - 音響合成パターン サブパッケージ

このパッケージは音響合成パターンに関する機能を提供します。
パターン認識、テンプレート管理、パラメータ抽出などのモジュールが含まれます。
"""

from .templates import TemplateManager
from .patterns import PatternMatcher
from .parameters import ParameterExtractor
from .utils import NoteConverter

__all__ = ['TemplateManager', 'PatternMatcher', 'ParameterExtractor', 'NoteConverter']
