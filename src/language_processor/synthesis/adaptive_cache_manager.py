#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
SPACO - アダプティブキャッシュマネージャー

このモジュールは、システムのメモリ使用状況に応じて動的にキャッシュサイズを
調整する機能を提供します。メモリ使用量が高くなりすぎると自動的にキャッシュを
クリアし、システムの安定性を確保します。
"""

import os
import sys
import time
import logging
import threading
import psutil
from typing import Dict, Any, Optional, Callable

logger = logging.getLogger(__name__)

# スレッドセーフなシングルトンパターンを保証するためのロック
_cache_manager_lock = threading.RLock()

class AdaptiveCacheManager:
    """
    アダプティブキャッシュマネージャー
    
    メモリ使用状況に基づいてキャッシュの自動調整を行います。
    メモリ使用率が高くなりすぎた場合に自動的にキャッシュを削減し、
    システムの安定性を確保します。
    """
    
    def __init__(self, 
                 high_memory_threshold: float = 0.85,
                 low_memory_threshold: float = 0.65,
                 critical_memory_threshold: float = 0.95,
                 check_interval: int = 60):
        """
        アダプティブキャッシュマネージャーを初期化します。
        
        引数:
            high_memory_threshold: 高メモリ使用率のしきい値（割合）
            low_memory_threshold: 低メモリ使用率のしきい値（割合）
            critical_memory_threshold: 緊急メモリ使用率のしきい値（割合）
            check_interval: メモリ使用状況のチェック間隔（秒）
        """
        self.high_memory_threshold = high_memory_threshold
        self.low_memory_threshold = low_memory_threshold
        self.critical_memory_threshold = critical_memory_threshold
        self.check_interval = check_interval
        
        # キャッシュクリア関数のリスト
        self.cache_clear_callbacks = []
        
        # 現在のメモリ使用状況
        self.current_memory_usage = 0.0
        self.last_check_time = 0
        
        # 統計情報
        self.stats = {
            "total_checks": 0,
            "high_memory_events": 0,
            "critical_memory_events": 0,
            "cache_clears": 0,
            "last_memory_usage": 0.0,
            "peak_memory_usage": 0.0
        }
        
        # 監視スレッド
        self.monitor_thread = None
        self.stop_monitoring = threading.Event()
    
    def register_cache_clear_callback(self, callback: Callable[[], None]) -> None:
        """
        キャッシュクリアコールバックを登録します。
        
        引数:
            callback: キャッシュをクリアするための関数
        """
        if callback not in self.cache_clear_callbacks:
            self.cache_clear_callbacks.append(callback)
            logger.debug(f"キャッシュクリアコールバックが登録されました（合計：{len(self.cache_clear_callbacks)}）")
    
    def unregister_cache_clear_callback(self, callback: Callable[[], None]) -> None:
        """
        キャッシュクリアコールバックの登録を解除します。
        
        引数:
            callback: 登録解除する関数
        """
        if callback in self.cache_clear_callbacks:
            self.cache_clear_callbacks.remove(callback)
            logger.debug(f"キャッシュクリアコールバックの登録が解除されました（残り：{len(self.cache_clear_callbacks)}）")
    
    def start_monitoring(self) -> None:
        """メモリ使用状況の監視を開始します"""
        if self.monitor_thread and self.monitor_thread.is_alive():
            logger.warning("監視スレッドは既に実行中です")
            return
        
        self.stop_monitoring.clear()
        self.monitor_thread = threading.Thread(target=self._monitor_memory_usage, 
                                              daemon=True, 
                                              name="MemoryMonitorThread")
        self.monitor_thread.start()
        logger.info("メモリ使用状況の監視を開始しました")
    
    def stop_monitor(self) -> None:
        """メモリ使用状況の監視を停止します"""
        if not self.monitor_thread or not self.monitor_thread.is_alive():
            logger.warning("監視スレッドは実行されていません")
            return
        
        self.stop_monitoring.set()
        self.monitor_thread.join(timeout=2.0)
        logger.info("メモリ使用状況の監視を停止しました")
    
    def _monitor_memory_usage(self) -> None:
        """メモリ使用状況を監視するスレッド"""
        while not self.stop_monitoring.is_set():
            try:
                self.check_memory_usage()
                time.sleep(self.check_interval)
            except Exception as e:
                logger.error(f"メモリ監視中にエラーが発生しました: {str(e)}", exc_info=True)
                time.sleep(self.check_interval * 2)  # エラー時は間隔を長くする
    
    def check_memory_usage(self) -> float:
        """
        メモリ使用状況をチェックし、必要に応じてキャッシュをクリアします。
        
        戻り値:
            float: 現在のメモリ使用率（0.0〜1.0）
        """
        now = time.time()
        
        # 最小チェック間隔を強制（過剰なチェックを防止）
        if now - self.last_check_time < 5:  # 最小5秒間隔
            return self.current_memory_usage
        
        self.last_check_time = now
        self.stats["total_checks"] += 1
        
        # メモリ使用状況を取得
        process = psutil.Process(os.getpid())
        memory_info = process.memory_info()
        system_memory = psutil.virtual_memory()
        
        # プロセスのメモリ使用率
        process_memory_percent = memory_info.rss / system_memory.total
        self.current_memory_usage = process_memory_percent
        self.stats["last_memory_usage"] = process_memory_percent
        
        # ピークメモリ使用率を更新
        if process_memory_percent > self.stats["peak_memory_usage"]:
            self.stats["peak_memory_usage"] = process_memory_percent
        
        # クリティカルメモリ使用率を超えた場合の緊急対応
        if process_memory_percent >= self.critical_memory_threshold:
            logger.warning(f"クリティカルメモリ使用率に達しました: {process_memory_percent:.2%}")
            self.stats["critical_memory_events"] += 1
            self._clear_all_caches()
            return process_memory_percent
        
        # 高メモリ使用率を超えた場合
        if process_memory_percent >= self.high_memory_threshold:
            logger.info(f"高メモリ使用率を検出: {process_memory_percent:.2%}")
            self.stats["high_memory_events"] += 1
            self._clear_all_caches()
        
        return process_memory_percent
    
    def _clear_all_caches(self) -> None:
        """登録されたすべてのキャッシュをクリアします"""
        if not self.cache_clear_callbacks:
            logger.warning("キャッシュクリアコールバックが登録されていません")
            return
        
        logger.info(f"{len(self.cache_clear_callbacks)}個のキャッシュをクリアします")
        
        for callback in self.cache_clear_callbacks:
            try:
                callback()
            except Exception as e:
                logger.error(f"キャッシュクリア中にエラーが発生しました: {str(e)}", exc_info=True)
        
        self.stats["cache_clears"] += 1
    
    def get_stats(self) -> Dict[str, Any]:
        """キャッシュマネージャーの統計情報を取得します"""
        return {
            **self.stats,
            "current_memory_usage": self.current_memory_usage,
            "registered_callbacks": len(self.cache_clear_callbacks),
            "monitoring_active": bool(self.monitor_thread and self.monitor_thread.is_alive()),
            "high_memory_threshold": self.high_memory_threshold,
            "low_memory_threshold": self.low_memory_threshold,
            "critical_memory_threshold": self.critical_memory_threshold,
            "check_interval": self.check_interval
        }


# シングルトンインスタンス
_cache_manager_instance = None

def get_cache_manager() -> AdaptiveCacheManager:
    """
    キャッシュマネージャーのシングルトンインスタンスを取得します。
    
    戻り値:
        AdaptiveCacheManager: キャッシュマネージャーのインスタンス
    """
    global _cache_manager_instance
    
    # ダブルチェックロッキングパターン
    if _cache_manager_instance is None:
        with _cache_manager_lock:
            if _cache_manager_instance is None:
                _cache_manager_instance = AdaptiveCacheManager()
                
    return _cache_manager_instance


# プロセス終了時のクリーンアップ処理
def _cleanup_cache_manager():
    """プロセス終了時にキャッシュマネージャーをクリーンアップします"""
    global _cache_manager_instance
    
    if _cache_manager_instance:
        with _cache_manager_lock:
            if _cache_manager_instance:
                _cache_manager_instance.stop_monitor()
                logger.info("キャッシュマネージャーがクリーンアップされました")


# 自動クリーンアップ登録
import atexit
atexit.register(_cleanup_cache_manager)
