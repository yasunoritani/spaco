#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
SuperCollider インターフェース

このモジュールは、OSCプロトコルとコード実行を使用してSuperColliderを制御するための
統合インターフェースを提供します。code_executor、osc_client、state_managerモジュールの
機能を組み合わせています。
"""

import asyncio
import logging
import os
import subprocess
import time
import uuid
from typing import Dict, Any, List, Optional, Union, Tuple

from .code_executor import CodeExecutor
from .osc_client import OSCClient
from .state_manager import StateManager

logger = logging.getLogger(__name__)

class SuperColliderError(Exception):
    """SuperCollider関連の例外の基底クラス"""
    def __init__(self, message, original_exception=None):
        super().__init__(message)
        self.original_exception = original_exception

class SuperColliderExecutionError(SuperColliderError):
    """SuperColliderコードの実行中に発生したエラー"""
    pass

class SuperColliderConnectionError(SuperColliderError):
    """SuperColliderサーバーへの接続に関するエラー"""
    pass

class SuperColliderResourceError(SuperColliderError):
    """SuperColliderリソースの管理に関するエラー"""
    pass

class SuperColliderTimeoutError(SuperColliderError):
    """SuperColliderの操作がタイムアウトした場合のエラー"""
    pass

class SuperColliderInterface:
    """
    SuperCollider統合インターフェース
    
    このクラスは以下の機能を提供します：
    - SuperColliderコードの実行
    - OSCを介したSuperColliderサーバー(scsynth)との通信
    - 実行中のSuperColliderプロセスの状態管理
    
    非同期コンテキストマネージャーとして使用できます：
    ```python
    async with SuperColliderInterface() as sc:
        await sc.execute("{ SinOsc.ar(440, 0, 0.2) }.play")
    ```
    """
    
    def __init__(self, 
                 host: str = "127.0.0.1", 
                 port: int = 57110, 
                 sclang_path: str = "sclang",
                 timeout: int = 30):
        """
        SuperColliderインターフェースを初期化します。
        
        引数:
            host (str): SuperColliderサーバーが実行されているホスト
            port (int): SuperColliderサーバーとのOSC通信用ポート
            sclang_path (str): sclang実行ファイルへのパス
            timeout (int): 操作のタイムアウト秒数
        
        例外:
            FileNotFoundError: sclangが見つからない場合
            SuperColliderConnectionError: 初期化中にエラーが発生した場合
        """
        self.host = host
        self.port = port
        self.sclang_path = sclang_path
        self.timeout = timeout
        self._initialized = False
        
        # sclangが存在するか確認
        if not os.path.exists(sclang_path) and "/" in sclang_path:
            raise FileNotFoundError(f"sclangが見つかりません: {sclang_path}")
            
        # 危険なSuperColliderコマンドのパターン
        self._dangerous_patterns = [
            "Server.killAll", 
            "0.exit", 
            "thisProcess.shutdown",
            "Quarks.install",
            "File.delete",
            "Pipe.new",
            "unixCmd"
        ]
            
        try:
            # コンポーネントの初期化
            self.code_executor = CodeExecutor(sclang_path=sclang_path)
            self.osc_client = OSCClient(host=host, port=port)
            self.state_manager = StateManager()
            
            # シンセIDとSuperCollider node IDのマッピング
            self._node_id_map = {}
            # 次に使用する予定のnode ID
            self._next_node_id = 1000  # 任意の開始点
            
            logger.info(f"SuperColliderインターフェースを初期化しました (host: {host}, port: {port})")
        except Exception as e:
            logger.exception("SuperColliderインターフェースの初期化中にエラーが発生しました")
            raise SuperColliderConnectionError(f"初期化エラー: {str(e)}", original_exception=e) from e
    
    async def __aenter__(self):
        """非同期コンテキストマネージャーのエントリーポイント"""
        await self.initialize()
        return self
        
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """非同期コンテキストマネージャーの終了処理"""
        await self.close()
        
    async def initialize(self):
        """インターフェースの初期化"""
        try:
            # サーバー接続を検証
            await self._verify_server_connection()
            self._initialized = True
            logger.info("SuperColliderインターフェースの初期化が完了しました")
        except Exception as e:
            logger.exception("インターフェースの初期化中にエラーが発生しました")
            raise SuperColliderConnectionError(f"初期化エラー: {str(e)}", original_exception=e) from e
            
    async def close(self):
        """インターフェースのクリーンアップ"""
        try:
            # 実行中のすべてのシンセを停止
            if self._initialized:
                await self.stop_all()
                
                # OSCクライアントを閉じる
                if hasattr(self, 'osc_client') and self.osc_client:
                    await self._run_in_executor(self.osc_client.close)
                    
                # コードエグゼキュータをクリーンアップ
                if hasattr(self, 'code_executor') and self.code_executor:
                    await self._run_in_executor(self.code_executor.stop_sclang_process)
                    
                self._initialized = False
                logger.info("SuperColliderインターフェースを正常に閉じました")
        except Exception as e:
            logger.error(f"インターフェースを閉じる際にエラーが発生しました: {str(e)}")
            raise SuperColliderError(f"クリーンアップエラー: {str(e)}", original_exception=e) from e
    
    async def _run_in_executor(self, func, *args, **kwargs):
        """
        関数を別スレッドで実行するためのヘルパーメソッド。
        
        引数:
            func: 実行する関数
            *args, **kwargs: 関数の引数
            
        戻り値:
            関数の戻り値
        """
        loop = asyncio.get_running_loop()
        return await loop.run_in_executor(
            None, 
            lambda: func(*args, **kwargs)
        )
        
    def _get_next_node_id(self) -> int:
        """
        次に使用するSuperCollider node IDを返します。
        
        戻り値:
            int: 次のnode ID
        """
        node_id = self._next_node_id
        self._next_node_id += 1
        return node_id
    
    async def _verify_server_connection(self) -> bool:
        """
        SuperColliderサーバーとの接続を検証します。
        
        戻り値:
            bool: 接続が成功した場合はTrue
            
        例外:
            SuperColliderConnectionError: 接続に失敗した場合
        """
        try:
            # 通知登録
            await self._run_in_executor(self.osc_client.notify, True)
            # ステータス要求（応答を待たない）
            await self._run_in_executor(self.osc_client.status)
            return True
        except Exception as e:
            logger.error(f"SuperColliderサーバーとの接続検証に失敗しました: {str(e)}")
            raise SuperColliderConnectionError(f"サーバー接続エラー: {str(e)}") from e
    
    def sanitize_code(self, sc_code: str) -> str:
        """
        SuperColliderコードをサニタイズし、安全に実行できるようにします。
        
        引数:
            sc_code (str): サニタイズするSuperColliderコード
            
        戻り値:
            str: サニタイズされたコード
        """
        if not sc_code:
            return sc_code
            
        # 危険な操作をブロック
        for pattern in self._dangerous_patterns:
            if pattern in sc_code:
                logger.warning(f"危険な操作がブロックされました: {pattern}")
                sc_code = sc_code.replace(pattern, f"// BLOCKED: {pattern}")
        
        # リソース使用量の制限
        if "inf" in sc_code and ("do {" in sc_code or "while {" in sc_code):
            logger.warning("無限ループの可能性があるコードが検出されました")
            
        # 実行時間制限の追加
        timeout_wrapper = f"""
        var executionStartTime = Main.elapsedTime;
        var maxExecutionTime = {min(10, self.timeout)}; // {min(10, self.timeout)}秒の実行時間制限
        
        // 実行時間監視関数
        {{
            while(Main.elapsedTime - executionStartTime < maxExecutionTime) {{
                0.5.wait;
            }};
            "SPACO: コード実行時間が制限を超えました。実行を中断します。".postln;
            // 強制的にノードを解放
            s.freeAll;
        }}.fork;
        
        // 元のコード
        {sc_code}
        """
        
        return timeout_wrapper
    
    async def _validate_input(self, sc_code: str) -> None:
        """
        入力コードを検証します。
        
        引数:
            sc_code (str): 検証するSuperColliderコード
            
        例外:
            ValueError: 入力が無効な場合
        """
        if not sc_code or not isinstance(sc_code, str):
            raise ValueError("実行するコードが無効です")
    
    async def _ensure_server_connection(self) -> None:
        """
        サーバー接続を確保します。
        
        例外:
            SuperColliderConnectionError: 接続に失敗した場合
        """
        if not self._initialized:
            await self.initialize()
        else:
            await self._verify_server_connection()
    
    async def _prepare_code(self, sc_code: str) -> Tuple[str, int, str]:
        """
        実行用にコードを準備します。
        
        引数:
            sc_code (str): 準備するSuperColliderコード
            
        戻り値:
            Tuple[str, int, str]: audio_id, node_id, 修正されたコード
        """
        audio_id = str(uuid.uuid4())
        node_id = self._get_next_node_id()
        
        # コードをサニタイズ
        sanitized_code = self.sanitize_code(sc_code)
        
        # SuperCollider node IDを変数として埋め込む
        modified_code = sanitized_code.replace(
            "{", 
            f"{{ \n// SPACO node ID: {node_id}\nvar spacoNodeID = {node_id};\n",
            1  # 最初の出現のみ置換
        )
        
        return audio_id, node_id, modified_code
    
    async def _execute_code(self, prepared_code: str) -> Dict[str, Any]:
        """
        準備されたコードを実行します。
        
        引数:
            prepared_code (str): 実行する準備済みコード
            
        戻り値:
            Dict[str, Any]: 実行結果
            
        例外:
            SuperColliderExecutionError: 実行中にエラーが発生した場合
        """
        logger.info(f"SuperColliderコードを実行中: {prepared_code[:50]}...")
        
        # コードを別スレッドで実行
        result = await self._run_in_executor(
            self.code_executor.execute, prepared_code
        )
        
        if result.get("status") != "success":
            logger.warning(f"SuperColliderコードの実行に失敗しました: {result.get('stderr', '')}")
            raise SuperColliderExecutionError(f"コード実行エラー: {result.get('stderr', '')}", 
                                             original_exception=None)
            
        return result
    
    async def _register_synth(self, audio_id: str, node_id: int, sc_code: str, result: Dict[str, Any]) -> None:
        """
        シンセを状態マネージャーに登録します。
        
        引数:
            audio_id (str): シンセの一意識別子
            node_id (int): SuperCollider node ID
            sc_code (str): 実行されたコード
            result (Dict[str, Any]): 実行結果
        """
        synth_data = {
            "id": audio_id,
            "node_id": node_id,
            "name": "生成されたシンセ",
            "code": sc_code,
            "result": result,
            "created_at": time.time()
        }
        
        await self._run_in_executor(
            self.state_manager.add_synth,
            audio_id, synth_data
        )
        
        # node IDとaudio_idのマッピングを保存
        self._node_id_map[node_id] = audio_id
        
        result["audio_id"] = audio_id
        result["node_id"] = node_id
        logger.info(f"SuperColliderコードが正常に実行されました。audio_id: {audio_id}, node_id: {node_id}")
    
    async def execute(self, sc_code: str) -> Dict[str, Any]:
        """
        SuperColliderコードを実行します。
        
        引数:
            sc_code (str): 実行するSuperColliderコード
            
        戻り値:
            Dict[str, Any]: 実行結果
            
        例外:
            SuperColliderExecutionError: コード実行中にエラーが発生した場合
        """
        try:
            # 入力検証
            await self._validate_input(sc_code)
            
            # サーバー接続確認
            await self._ensure_server_connection()
            
            # コード準備
            audio_id, node_id, prepared_code = await self._prepare_code(sc_code)
            
            # コード実行
            result = await self._execute_code(prepared_code)
            
            # 実行履歴に追加
            await self._run_in_executor(
                self.state_manager.add_code_history, 
                sc_code, result
            )
            
            # シンセを登録
            await self._register_synth(audio_id, node_id, sc_code, result)
            
            return result
            
        except SuperColliderError:
            # 既に適切に処理された例外は再スロー
            raise
        except ValueError as e:
            # 入力値に関するエラー
            logger.exception("コード実行の入力値が無効です")
            raise ValueError(str(e))
        except Exception as e:
            # その他の未処理例外
            logger.exception("SuperColliderコードの実行中に予期しないエラーが発生しました")
            raise SuperColliderExecutionError(f"コード実行エラー: {str(e)}", original_exception=e) from e
    
    async def stop_synth(self, audio_id: str) -> Dict[str, Any]:
        """
        特定のシンセを停止します。
        
        引数:
            audio_id (str): 停止するシンセのID
            
        戻り値:
            Dict[str, Any]: 操作の結果
            
        例外:
            ValueError: 無効なaudio_idが指定された場合
            SuperColliderResourceError: シンセの停止に失敗した場合
        """
        if not audio_id:
            raise ValueError("無効なaudio_idです")
            
        try:
            # 状態マネージャーからシンセ情報を取得
            synth_info = await self._run_in_executor(
                self.state_manager.get_synth, audio_id
            )
            
            if not synth_info:
                logger.warning(f"シンセ {audio_id} が状態マネージャーに見つかりません")
                return {
                    "status": "error",
                    "message": f"シンセ {audio_id} が見つかりません",
                    "returncode": 1
                }
            
            # SuperCollider node IDを取得
            node_id = synth_info.get("node_id")
            if node_id:
                try:
                    # 特定のノードを解放するOSCメッセージを送信
                    await self._run_in_executor(self.osc_client.free_node, node_id)
                    logger.info(f"OSCメッセージを送信してノード {node_id} を解放しました")
                except Exception as e:
                    logger.warning(f"OSCメッセージの送信中にエラー: {str(e)}")
            
            # シンセを状態から削除
            await self._run_in_executor(
                self.state_manager.remove_synth, audio_id
            )
            
            # ノードIDのマッピングからも削除
            if node_id in self._node_id_map:
                del self._node_id_map[node_id]
            
            return {
                "status": "success",
                "message": f"シンセ {audio_id} を停止しました",
                "returncode": 0
            }
            
        except ValueError:
            # 既に処理された値エラーは再スロー
            raise
        except Exception as e:
            logger.exception(f"シンセ {audio_id} の停止中にエラーが発生しました")
            raise SuperColliderResourceError(f"シンセ停止エラー: {str(e)}") from e
    
    async def stop_all(self) -> Dict[str, Any]:
        """
        実行中のすべてのシンセを停止します。
        
        戻り値:
            Dict[str, Any]: 操作の結果
            
        例外:
            SuperColliderConnectionError: OSC通信に失敗した場合
        """
        try:
            # OSCコマンドを別スレッドで実行
            await self._run_in_executor(self.osc_client.free_all)
            
            # 状態マネージャーからすべてのシンセのカウントを取得
            all_synths = await self._run_in_executor(
                self.state_manager.get_all_synths
            )
            synth_count = len(all_synths)
            
            # 状態マネージャーからすべてのシンセをクリア
            await self._run_in_executor(
                self.state_manager.clear_all_synths
            )
            
            # ノードIDマッピングもクリア
            self._node_id_map.clear()
            
            return {
                "status": "success",
                "message": f"{synth_count}個のシンセを停止しました",
                "returncode": 0
            }
            
        except Exception as e:
            logger.exception("すべてのシンセの停止中にエラーが発生しました")
            raise SuperColliderConnectionError(f"シンセ停止エラー: {str(e)}") from e
    
    async def list_synths(self) -> List[Dict[str, Any]]:
        """
        アクティブなシンセをすべてリスト表示します。
        
        戻り値:
            List[Dict[str, Any]]: アクティブなシンセのリスト
        """
        try:
            # 状態マネージャーからすべてのシンセを取得
            all_synths = await self._run_in_executor(
                self.state_manager.get_all_synths
            )
            
            # 現在時刻を取得（実行時間の計算用）
            current_time = time.time()
            
            # シンセ情報のリストを生成
            return [
                {
                    "id": synth_id,
                    "node_id": synth_data.get("node_id", "不明"),
                    "name": synth_data.get("name", "不明"),
                    "created_at": synth_data.get("created_at", 0),
                    "runtime": current_time - synth_data.get("created_at", current_time),
                    "code_snippet": synth_data.get("code", "")[:50] + "..." 
                        if len(synth_data.get("code", "")) > 50 
                        else synth_data.get("code", "")
                }
                for synth_id, synth_data in all_synths.items()
            ]
        except Exception as e:
            logger.exception("シンセ一覧の取得中にエラーが発生しました")
            return []
            
    async def check_server_status(self) -> Dict[str, Any]:
        """
        SuperColliderサーバーの状態を確認します。
        
        戻り値:
            Dict[str, Any]: サーバーのステータス情報
            
        例外:
            SuperColliderConnectionError: サーバーに接続できない場合
        """
        try:
            # サーバー接続を検証
            await self._verify_server_connection()
            
            # サーバーステータスを取得
            server_status = self.state_manager.is_server_running()
            server_stats = self.state_manager.export_state()
            
            return {
                "status": "success",
                "server_running": server_status,
                "server_info": server_stats,
                "returncode": 0
            }
        except SuperColliderConnectionError:
            # 既に処理された接続エラーは再スロー
            raise
        except Exception as e:
            logger.exception("サーバー状態の確認中にエラーが発生しました")
            raise SuperColliderConnectionError(f"ステータス確認エラー: {str(e)}") from e
            
    async def cleanup(self) -> Dict[str, Any]:
        """
        すべてのリソースをクリーンアップします。
        
        戻り値:
            Dict[str, Any]: クリーンアップ結果
        """
        try:
            # インターフェースを閉じる
            await self.close()
            
            # 状態をリセット
            await self._run_in_executor(
                self.state_manager.reset
            )
            
            # メモリの解放を促進
            self._node_id_map.clear()
            
            logger.info("SuperColliderインターフェースのリソースをクリーンアップしました")
            return {
                "status": "success",
                "message": "すべてのリソースがクリーンアップされました",
                "returncode": 0
            }
        except Exception as e:
            logger.exception("リソースのクリーンアップ中にエラーが発生しました")
            return {
                "status": "error",
                "message": f"クリーンアップエラー: {str(e)}",
                "returncode": 1
            }