#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
SPACO - 音響合成モジュール

このモジュールは、SuperColliderを使った音響合成に関する機能を提供します。
"""

from .precompiled_patterns import (
    PrecompiledPattern,
    PatternCompiler,
    PatternManager,
    pattern_manager
)

__all__ = [
    'PrecompiledPattern',
    'PatternCompiler',
    'PatternManager',
    'pattern_manager'
]
