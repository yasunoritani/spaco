#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
SPACO - 中間表現の基本クラス

このモジュールは、SPACOで使用する中間表現の基本クラスを定義します。
すべての表現レベル（意図、パラメータ、構造、コード）は、この基本クラスを継承します。
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional, Set, Union, Tuple
import json
import logging

logger = logging.getLogger(__name__)


class ValidationError(Exception):
    """中間表現の検証に失敗した場合に発生する例外"""
    def __init__(self, message, level=None, field=None):
        super().__init__(message)
        self.level = level
        self.field = field


class RepresentationLevel(ABC):
    """
    すべての表現レベルの基底クラス
    
    このクラスは、すべての表現レベルが実装すべきインターフェースを定義します。
    各表現レベルは、このクラスを継承し、抽象メソッドを実装する必要があります。
    """
    
    def __init__(self):
        """表現レベルを初期化します。"""
        self._is_valid = False
    
    @abstractmethod
    def validate(self) -> bool:
        """
        表現が有効かどうかを検証します。
        
        戻り値:
            bool: 表現が有効な場合はTrue、そうでない場合はFalse
        """
        pass
    
    @abstractmethod
    def to_dict(self) -> Dict[str, Any]:
        """
        表現を辞書形式に変換します。
        
        戻り値:
            Dict[str, Any]: 表現を表す辞書
        """
        pass
    
    @classmethod
    @abstractmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'RepresentationLevel':
        """
        辞書から表現を生成します。
        
        引数:
            data: 表現を表す辞書
            
        戻り値:
            RepresentationLevel: 生成された表現インスタンス
        """
        pass
    
    def to_json(self) -> str:
        """
        表現をJSON文字列に変換します。
        
        戻り値:
            str: JSON形式の文字列
        """
        return json.dumps(self.to_dict(), ensure_ascii=False, indent=2)
    
    @classmethod
    def from_json(cls, json_str: str) -> 'RepresentationLevel':
        """
        JSON文字列から表現を生成します。
        
        引数:
            json_str: JSON形式の文字列
            
        戻り値:
            RepresentationLevel: 生成された表現インスタンス
        """
        data = json.loads(json_str)
        return cls.from_dict(data)
    
    def __str__(self) -> str:
        """
        表現の文字列表現を返します。
        
        戻り値:
            str: 表現の文字列表現
        """
        return f"{self.__class__.__name__}: {self.to_json()}"
    
    def __repr__(self) -> str:
        """
        表現のプログラム的な文字列表現を返します。
        
        戻り値:
            str: 表現のプログラム的な文字列表現
        """
        return f"{self.__class__.__name__}({self.to_dict()})"
    
    def is_valid(self) -> bool:
        """
        表現が有効かどうかを返します。
        
        戻り値:
            bool: 表現が有効な場合はTrue、そうでない場合はFalse
        """
        if not self._is_valid:
            self._is_valid = self.validate()
        return self._is_valid
