#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
SPACO - 階層的中間表現モジュール

このモジュールは、自然言語からSuperColliderコードへの変換を効率的に行うための
階層的中間表現モデルを提供します。

以下の階層構造を持ちます：
1. 意図レベル: 指示の基本的な意図（音生成、エフェクト適用、シーケンス作成など）
2. パラメータレベル: 音響パラメータ（周波数、振幅、エンベロープなど）
3. 構造レベル: 音響構造（シンセ定義、パターン、エフェクトチェーンなど）
4. コードレベル: SuperColliderの具体的なコード構造
"""

from .base import RepresentationLevel, ValidationError
from .intent_level import IntentLevel
from .parameter_level import ParameterLevel
from .structure_level import StructureLevel
from .code_level import CodeLevel
from .converter import IntentToParameterConverter, ParameterToStructureConverter, StructureToCodeConverter
