#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
SPACO - プリコンパイルされた音響パターン

このモジュールは、よく使われる音響パターンをプリコンパイルして
保存・管理する機能を提供します。パターンをあらかじめコンパイル
しておくことで、実行時のパフォーマンスを向上させます。
"""

import logging
import time
import os
import json
import hashlib
from typing import Dict, Any, List, Optional, Set, Union, Tuple, Callable
import sqlite3
import threading
from functools import lru_cache

# データベース関連のインポート
from src.data.db.connection import get_connection, transaction
from src.data.utils.exceptions import ValidationError, DatabaseError
from src.data.utils.i18n import t

logger = logging.getLogger(__name__)

# スレッドローカルストレージ
_thread_local = threading.local()


class PatternCompilationError(Exception):
    """音響パターンのコンパイル中に発生したエラー"""
    
    def __init__(self, message: str, pattern_name: Optional[str] = None,
                 original_exception: Optional[Exception] = None):
        self.pattern_name = pattern_name
        self.original_exception = original_exception
        super().__init__(message)


class PrecompiledPattern:
    """プリコンパイルされた音響パターン"""
    
    def __init__(self, name: str, pattern_type: str, source_code: str,
                 compiled_code: str, metadata: Optional[Dict[str, Any]] = None):
        """
        プリコンパイルされた音響パターンを初期化します。
        
        引数:
            name: パターン名
            pattern_type: パターンタイプ
            source_code: オリジナルのソースコード
            compiled_code: コンパイル済みのコード
            metadata: パターンに関するメタデータ
        """
        self.name = name
        self.pattern_type = pattern_type
        self.source_code = source_code
        self.compiled_code = compiled_code
        self.metadata = metadata or {}
        self.compilation_time = time.time()
        
        # パターン識別子を計算（キャッシュキーとして使用）
        self.pattern_id = self._calculate_pattern_id()
    
    def _calculate_pattern_id(self) -> str:
        """パターン識別子を計算します"""
        # ソースコードとタイプからハッシュを生成
        hasher = hashlib.md5()
        hasher.update(f"{self.pattern_type}:{self.source_code}".encode("utf-8"))
        return hasher.hexdigest()
    
    def to_dict(self) -> Dict[str, Any]:
        """辞書表現に変換します"""
        return {
            "name": self.name,
            "pattern_type": self.pattern_type,
            "source_code": self.source_code,
            "compiled_code": self.compiled_code,
            "metadata": self.metadata,
            "pattern_id": self.pattern_id,
            "compilation_time": self.compilation_time
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "PrecompiledPattern":
        """辞書からPrecompiledPatternを作成します"""
        pattern = cls(
            name=data["name"],
            pattern_type=data["pattern_type"],
            source_code=data["source_code"],
            compiled_code=data["compiled_code"],
            metadata=data.get("metadata", {})
        )
        # 保存されたcompilation_timeがあれば使用
        if "compilation_time" in data:
            pattern.compilation_time = data["compilation_time"]
        return pattern


class PatternCompiler:
    """音響パターンのコンパイラ"""
    
    def __init__(self):
        """音響パターンコンパイラを初期化します"""
        self.compilation_stats = {
            "total_compiled": 0,
            "compilation_errors": 0,
            "total_compilation_time": 0.0
        }
    
    def compile_pattern(self, name: str, pattern_type: str, source_code: str,
                        metadata: Optional[Dict[str, Any]] = None) -> PrecompiledPattern:
        """
        音響パターンをコンパイルします。
        
        引数:
            name: パターン名
            pattern_type: パターンタイプ
            source_code: コンパイルするソースコード
            metadata: パターンに関するメタデータ
            
        戻り値:
            PrecompiledPattern: コンパイルされたパターン
            
        例外:
            PatternCompilationError: コンパイル中にエラーが発生した場合
        """
        try:
            start_time = time.time()
            
            # ここでSuperColliderのコード最適化処理を行う
            # 実際のところ、SCコードのプリコンパイルは内部表現の最適化が中心
            compiled_code = self._optimize_sc_code(source_code, pattern_type)
            
            compilation_time = time.time() - start_time
            
            # 統計情報を更新
            self.compilation_stats["total_compiled"] += 1
            self.compilation_stats["total_compilation_time"] += compilation_time
            
            # プリコンパイルパターンを作成
            pattern = PrecompiledPattern(
                name=name,
                pattern_type=pattern_type,
                source_code=source_code,
                compiled_code=compiled_code,
                metadata=metadata
            )
            
            logger.debug(f"パターン '{name}' のコンパイルが完了しました（{compilation_time:.3f}秒）")
            return pattern
            
        except Exception as e:
            # 統計情報を更新
            self.compilation_stats["compilation_errors"] += 1
            
            # エラーログを記録
            logger.error(f"パターン '{name}' のコンパイル中にエラーが発生しました: {str(e)}", 
                         exc_info=True)
            
            # 例外を再構築して発生
            raise PatternCompilationError(
                message=f"パターンのコンパイル中にエラーが発生しました: {str(e)}",
                pattern_name=name,
                original_exception=e
            )
    
    def _optimize_sc_code(self, source_code: str, pattern_type: str) -> str:
        """
        SuperColliderコードを最適化します。
        
        引数:
            source_code: 最適化するソースコード
            pattern_type: パターンタイプ
            
        戻り値:
            str: 最適化されたコード
        """
        # 基本的な最適化: 不要な空白や改行の削除
        code = source_code.strip()
        
        # パターンタイプに基づく最適化
        if pattern_type == "synth_def":
            # SynthDefを最適化（例: 変数の結合、不要な演算の削減など）
            code = self._optimize_synth_def(code)
        elif pattern_type == "pattern":
            # パターンの最適化
            code = self._optimize_pattern_code(code)
        elif pattern_type == "effect":
            # エフェクトの最適化
            code = self._optimize_effect_code(code)
        
        return code
    
    def _optimize_synth_def(self, code: str) -> str:
        """SynthDef定義を最適化"""
        # このメソッドでは以下の最適化を行う:
        # - 定数演算の事前計算
        # - 不要な変数の削除
        # - UGen グラフの最適化
        
        # 現在のバージョンでは簡易的な実装のみ
        # 実際の実装ではもっと複雑なSCコード解析と最適化が必要
        
        # 簡易的な定数演算の事前計算（シンプルな掛け算や足し算など）
        import re
        # 数値演算のパターン（例: 2 * 3, 4 + 5）
        const_ops = re.findall(r'(\d+\s*[\*\+\-\/]\s*\d+)', code)
        for op in const_ops:
            try:
                # 安全に評価（数値演算のみを許可）
                result = eval(op.replace("*", "*").replace("+", "+").replace("-", "-").replace("/", "/"))
                code = code.replace(op, str(result))
            except:
                # 評価に失敗した場合は置換しない
                pass
        
        return code
    
    def _optimize_pattern_code(self, code: str) -> str:
        """パターンコードを最適化"""
        # パターン固有の最適化
        # 現在のバージョンでは簡易的な実装のみ
        return code
    
    def _optimize_effect_code(self, code: str) -> str:
        """エフェクトコードを最適化"""
        # エフェクト固有の最適化
        # 現在のバージョンでは簡易的な実装のみ
        return code
    
    def get_compilation_stats(self) -> Dict[str, Any]:
        """コンパイル統計情報を取得します"""
        return {
            **self.compilation_stats,
            "avg_compilation_time": (
                self.compilation_stats["total_compilation_time"] / 
                self.compilation_stats["total_compiled"]
                if self.compilation_stats["total_compiled"] > 0 else 0
            )
        }


class PatternManager:
    """プリコンパイルされた音響パターンの管理"""
    
    def __init__(self, cache_size: int = 100):
        """
        パターンマネージャーを初期化します。
        
        引数:
            cache_size: メモリ内キャッシュのサイズ
        """
        self.compiler = PatternCompiler()
        self.cache_size = cache_size
        self._init_db()
    
    def _init_db(self):
        """SQLiteスキーマを初期化します"""
        try:
            with get_connection() as conn:
                cursor = conn.cursor()
                
                # プリコンパイルされたパターンテーブルの作成
                cursor.execute("""
                CREATE TABLE IF NOT EXISTS precompiled_patterns (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT NOT NULL,
                    pattern_type TEXT NOT NULL,
                    pattern_id TEXT UNIQUE NOT NULL,
                    source_code TEXT NOT NULL,
                    compiled_code TEXT NOT NULL,
                    metadata TEXT,
                    compilation_time REAL,
                    created_at REAL NOT NULL,
                    last_used_at REAL
                );
                """)
                
                # パターンタイプと名前に対するインデックスを作成
                cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_pattern_type 
                ON precompiled_patterns(pattern_type);
                """)
                
                cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_pattern_name 
                ON precompiled_patterns(name);
                """)
                
                conn.commit()
                logger.info("プリコンパイルパターンのデータベーススキーマが初期化されました")
                
        except Exception as e:
            logger.error(f"データベースの初期化中にエラーが発生しました: {str(e)}", exc_info=True)
            raise DatabaseError(
                message=t("データベースの初期化に失敗しました"),
                original_exception=e
            )
    
    @lru_cache(maxsize=100)
    def get_pattern(self, pattern_id: str) -> Optional[PrecompiledPattern]:
        """
        パターンIDに基づいてプリコンパイルされたパターンを取得します。
        まずメモリキャッシュを確認し、なければデータベースから取得します。
        
        引数:
            pattern_id: パターン識別子
            
        戻り値:
            Optional[PrecompiledPattern]: 見つかったパターン、または None
        """
        try:
            # データベースからパターンを検索
            with get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                SELECT name, pattern_type, source_code, compiled_code, metadata, 
                       compilation_time, pattern_id
                FROM precompiled_patterns
                WHERE pattern_id = ?
                """, (pattern_id,))
                
                row = cursor.fetchone()
                if row is None:
                    return None
                
                # 最終使用時間を更新
                cursor.execute("""
                UPDATE precompiled_patterns
                SET last_used_at = ?
                WHERE pattern_id = ?
                """, (time.time(), pattern_id))
                
                conn.commit()
                
                # パターンオブジェクトを構築
                name, pattern_type, source_code, compiled_code, metadata_json, compilation_time, pattern_id = row
                metadata = json.loads(metadata_json) if metadata_json else {}
                
                pattern = PrecompiledPattern(
                    name=name,
                    pattern_type=pattern_type,
                    source_code=source_code,
                    compiled_code=compiled_code,
                    metadata=metadata
                )
                pattern.compilation_time = compilation_time
                
                return pattern
                
        except Exception as e:
            logger.error(f"パターン取得中にエラーが発生しました: {str(e)}", exc_info=True)
            return None
    
    def find_pattern_by_name(self, name: str, pattern_type: Optional[str] = None) -> Optional[PrecompiledPattern]:
        """
        名前とオプションのタイプでパターンを検索します。
        
        引数:
            name: パターン名
            pattern_type: パターンタイプ（オプション）
            
        戻り値:
            Optional[PrecompiledPattern]: 見つかったパターン、または None
        """
        try:
            with get_connection() as conn:
                cursor = conn.cursor()
                
                # SQLクエリを構築
                query = "SELECT pattern_id FROM precompiled_patterns WHERE name = ?"
                params = [name]
                
                if pattern_type:
                    query += " AND pattern_type = ?"
                    params.append(pattern_type)
                
                # 最も最近使用されたパターンを取得
                query += " ORDER BY last_used_at DESC NULLS LAST LIMIT 1"
                
                cursor.execute(query, params)
                row = cursor.fetchone()
                
                if row is None:
                    return None
                
                pattern_id = row[0]
                # 取得したIDからパターンを取得（キャッシュを活用）
                return self.get_pattern(pattern_id)
                
        except Exception as e:
            logger.error(f"パターン検索中にエラーが発生しました: {str(e)}", exc_info=True)
            return None
    
    def find_patterns_by_type(self, pattern_type: str) -> List[PrecompiledPattern]:
        """
        タイプでパターンを検索します。
        
        引数:
            pattern_type: パターンタイプ
            
        戻り値:
            List[PrecompiledPattern]: 見つかったパターンのリスト
        """
        try:
            with get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                SELECT pattern_id
                FROM precompiled_patterns
                WHERE pattern_type = ?
                ORDER BY last_used_at DESC NULLS LAST
                """, (pattern_type,))
                
                rows = cursor.fetchall()
                patterns = []
                
                for row in rows:
                    pattern_id = row[0]
                    pattern = self.get_pattern(pattern_id)
                    if pattern:
                        patterns.append(pattern)
                
                return patterns
                
        except Exception as e:
            logger.error(f"パターン検索中にエラーが発生しました: {str(e)}", exc_info=True)
            return []
    
    @transaction()
    def save_pattern(self, pattern: PrecompiledPattern) -> bool:
        """
        プリコンパイルされたパターンを保存します。
        
        引数:
            pattern: 保存するパターン
            
        戻り値:
            bool: 保存に成功したかどうか
        """
        try:
            conn = getattr(_thread_local, 'conn', None)
            if not conn:
                raise DatabaseError(message=t("トランザクションコンテキストがありません"))
                
            cursor = conn.cursor()
            
            # 既存のパターンを確認
            cursor.execute("""
            SELECT id FROM precompiled_patterns WHERE pattern_id = ?
            """, (pattern.pattern_id,))
            
            existing = cursor.fetchone()
            metadata_json = json.dumps(pattern.metadata)
            now = time.time()
            
            if existing:
                # 既存のパターンを更新
                cursor.execute("""
                UPDATE precompiled_patterns
                SET name = ?, pattern_type = ?, source_code = ?, 
                    compiled_code = ?, metadata = ?, compilation_time = ?,
                    last_used_at = ?
                WHERE pattern_id = ?
                """, (
                    pattern.name, pattern.pattern_type, pattern.source_code,
                    pattern.compiled_code, metadata_json, pattern.compilation_time,
                    now, pattern.pattern_id
                ))
            else:
                # 新しいパターンを挿入
                cursor.execute("""
                INSERT INTO precompiled_patterns
                (name, pattern_type, pattern_id, source_code, compiled_code, 
                 metadata, compilation_time, created_at, last_used_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    pattern.name, pattern.pattern_type, pattern.pattern_id,
                    pattern.source_code, pattern.compiled_code, metadata_json,
                    pattern.compilation_time, now, now
                ))
            
            # LRUキャッシュを無効化して再取得を強制
            self.get_pattern.cache_clear()
            
            return True
            
        except Exception as e:
            logger.error(f"パターン保存中にエラーが発生しました: {str(e)}", exc_info=True)
            raise DatabaseError(
                message=t("パターンの保存に失敗しました"),
                original_exception=e
            )
    
    def compile_and_save(self, name: str, pattern_type: str, source_code: str,
                         metadata: Optional[Dict[str, Any]] = None) -> PrecompiledPattern:
        """
        パターンをコンパイルして保存します。
        
        引数:
            name: パターン名
            pattern_type: パターンタイプ
            source_code: コンパイルするソースコード
            metadata: パターンに関するメタデータ
            
        戻り値:
            PrecompiledPattern: コンパイル・保存されたパターン
            
        例外:
            PatternCompilationError: コンパイル中にエラーが発生した場合
            DatabaseError: データベース操作中にエラーが発生した場合
        """
        # パターンをコンパイル
        pattern = self.compiler.compile_pattern(
            name=name,
            pattern_type=pattern_type,
            source_code=source_code,
            metadata=metadata
        )
        
        # パターンを保存
        success = self.save_pattern(pattern)
        if not success:
            raise DatabaseError(message=t("パターンの保存に失敗しました"))
            
        return pattern
    
    def delete_pattern(self, pattern_id: str) -> bool:
        """
        パターンを削除します。
        
        引数:
            pattern_id: 削除するパターンのID
            
        戻り値:
            bool: 削除に成功したかどうか
        """
        try:
            with get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                DELETE FROM precompiled_patterns WHERE pattern_id = ?
                """, (pattern_id,))
                conn.commit()
                
                # キャッシュから削除
                self.get_pattern.cache_clear()
                
                return cursor.rowcount > 0
                
        except Exception as e:
            logger.error(f"パターン削除中にエラーが発生しました: {str(e)}", exc_info=True)
            return False
    
    def clear_unused_patterns(self, older_than_days: int = 30) -> int:
        """
        一定期間使用されていないパターンを削除します。
        
        引数:
            older_than_days: この日数より前に最後に使用されたパターンを削除
            
        戻り値:
            int: 削除されたパターンの数
        """
        try:
            cutoff_time = time.time() - (older_than_days * 24 * 60 * 60)
            
            with get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                DELETE FROM precompiled_patterns 
                WHERE last_used_at < ? OR last_used_at IS NULL
                """, (cutoff_time,))
                
                deleted_count = cursor.rowcount
                conn.commit()
                
                # キャッシュをクリア
                self.get_pattern.cache_clear()
                
                logger.info(f"{deleted_count}個の未使用パターンが削除されました")
                return deleted_count
                
        except Exception as e:
            logger.error(f"未使用パターン削除中にエラーが発生しました: {str(e)}", exc_info=True)
            return 0
    
    def get_pattern_stats(self) -> Dict[str, Any]:
        """
        パターン関連の統計情報を取得します。
        
        戻り値:
            Dict[str, Any]: 統計情報
        """
        try:
            with get_connection() as conn:
                cursor = conn.cursor()
                
                # 総パターン数
                cursor.execute("SELECT COUNT(*) FROM precompiled_patterns")
                total_patterns = cursor.fetchone()[0]
                
                # タイプごとのパターン数
                cursor.execute("""
                SELECT pattern_type, COUNT(*) 
                FROM precompiled_patterns 
                GROUP BY pattern_type
                """)
                type_counts = {row[0]: row[1] for row in cursor.fetchall()}
                
                # キャッシュ情報
                cache_info = self.get_pattern.cache_info()
                cache_stats = {
                    "hits": cache_info.hits,
                    "misses": cache_info.misses,
                    "max_size": cache_info.maxsize,
                    "current_size": cache_info.currsize
                }
                
                return {
                    "total_patterns": total_patterns,
                    "type_counts": type_counts,
                    "cache_stats": cache_stats,
                    "compiler_stats": self.compiler.get_compilation_stats()
                }
                
        except Exception as e:
            logger.error(f"統計情報取得中にエラーが発生しました: {str(e)}", exc_info=True)
            return {
                "error": str(e),
                "total_patterns": 0,
                "type_counts": {},
                "cache_stats": {},
                "compiler_stats": {}
            }


# シングルトンインスタンス
pattern_manager = PatternManager(cache_size=100)
