"""
SuperColliderインターフェースのテスト
"""

import unittest
import asyncio
import os
import time
from unittest.mock import MagicMock, patch, call, ANY

from src.sc_interface import SuperColliderInterface
from src.sc_interface.interface import (
    SuperColliderError, 
    SuperColliderExecutionError,
    SuperColliderConnectionError,
    SuperColliderResourceError
)

class TestSuperColliderInterface(unittest.TestCase):
    """SuperColliderインターフェースのテストケース"""
    
    def setUp(self):
        """各テスト前の準備"""
        # SuperColliderインターフェースをモックコンポーネントで初期化
        with patch('src.sc_interface.interface.CodeExecutor') as mock_executor, \
             patch('src.sc_interface.interface.OSCClient') as mock_osc, \
             patch('src.sc_interface.interface.StateManager') as mock_state, \
             patch('src.sc_interface.interface.os.path.exists', return_value=True):
            
            self.mock_executor = MagicMock()
            self.mock_osc = MagicMock()
            self.mock_state = MagicMock()
            
            mock_executor.return_value = self.mock_executor
            mock_osc.return_value = self.mock_osc
            mock_state.return_value = self.mock_state
            
            self.interface = SuperColliderInterface()
    
    def test_init(self):
        """初期化テスト"""
        self.assertIsNotNone(self.interface)
        self.assertEqual(self.interface.host, "127.0.0.1")
        self.assertEqual(self.interface.port, 57110)
    
    def test_init_with_invalid_path(self):
        """無効なパスでの初期化テスト"""
        with patch('src.sc_interface.interface.os.path.exists', return_value=False):
            with self.assertRaises(FileNotFoundError):
                SuperColliderInterface(sclang_path="/invalid/path/to/sclang")
    
    def test_init_with_exception(self):
        """例外発生時の初期化テスト"""
        with patch('src.sc_interface.interface.CodeExecutor', side_effect=Exception("接続エラー")), \
             patch('src.sc_interface.interface.os.path.exists', return_value=True):
            with self.assertRaises(SuperColliderConnectionError):
                SuperColliderInterface()
    
    async def _verify_server_connection_success(self):
        """サーバー接続検証の成功テスト（非同期）"""
        result = await self.interface._verify_server_connection()
        self.assertTrue(result)
        self.mock_osc.notify.assert_called_once_with(True)
        self.mock_osc.status.assert_called_once()
    
    def test_verify_server_connection_success(self):
        """サーバー接続検証の成功テスト"""
        asyncio.run(self._verify_server_connection_success())
    
    async def _verify_server_connection_failure(self):
        """サーバー接続検証の失敗テスト（非同期）"""
        self.mock_osc.notify.side_effect = Exception("接続できません")
        with self.assertRaises(SuperColliderConnectionError):
            await self.interface._verify_server_connection()
    
    def test_verify_server_connection_failure(self):
        """サーバー接続検証の失敗テスト"""
        asyncio.run(self._verify_server_connection_failure())
    
    async def _execute_success(self):
        """execute()メソッドの成功テスト（非同期）"""
        # モックの戻り値を設定
        self.mock_executor.execute.return_value = {
            "status": "success",
            "stdout": "テスト成功",
            "stderr": "",
            "returncode": 0
        }
        
        # asyncメソッドを実行
        test_code = "// テストコード"
        result = await self.interface.execute(test_code)
        
        # 結果を検証
        self.assertEqual(result["status"], "success")
        self.assertEqual(result["stdout"], "テスト成功")
        self.assertTrue("audio_id" in result)
        self.assertTrue("node_id" in result)
        
        # モックが正しく呼び出されたか確認
        # コードに node_id が埋め込まれていることを確認
        self.mock_executor.execute.assert_called_once()
        call_args = self.mock_executor.execute.call_args[0][0]
        self.assertIn("var spacoNodeID =", call_args)
        
        # 他のモックの検証
        self.mock_state.add_code_history.assert_called_once_with(test_code, ANY)
        self.mock_state.add_synth.assert_called_once_with(ANY, ANY)
    
    def test_execute_success(self):
        """execute()メソッドの成功テスト"""
        asyncio.run(self._execute_success())
    
    async def _execute_empty_code(self):
        """空のコードを実行したときのテスト（非同期）"""
        with self.assertRaises(ValueError):
            await self.interface.execute("")
    
    def test_execute_empty_code(self):
        """空のコードを実行したときのテスト"""
        asyncio.run(self._execute_empty_code())
    
    async def _execute_failure(self):
        """execute()メソッドの失敗テスト（非同期）"""
        # モックの戻り値を設定
        self.mock_executor.execute.return_value = {
            "status": "error",
            "stdout": "",
            "stderr": "実行エラー",
            "returncode": 1
        }
        
        # asyncメソッドを実行
        with self.assertRaises(SuperColliderExecutionError):
            await self.interface.execute("// エラーが発生するコード")
        
        # モックが正しく呼び出されたか確認
        self.mock_executor.execute.assert_called_once()
        self.mock_state.add_code_history.assert_called_once()
        # エラー時はシンセを追加しない
        self.mock_state.add_synth.assert_not_called()
    
    def test_execute_failure(self):
        """execute()メソッドの失敗テスト"""
        asyncio.run(self._execute_failure())
    
    async def _stop_synth_success(self):
        """stop_synth()メソッドの成功テスト（非同期）"""
        # モックの戻り値を設定
        test_node_id = 1001
        self.mock_state.get_synth.return_value = {
            "id": "test-id",
            "node_id": test_node_id,
            "name": "テストシンセ"
        }
        self.interface._node_id_map[test_node_id] = "test-id"
        
        # asyncメソッドを実行
        result = await self.interface.stop_synth("test-id")
        
        # 結果を検証
        self.assertEqual(result["status"], "success")
        
        # モックが正しく呼び出されたか確認
        self.mock_state.get_synth.assert_called_once_with("test-id")
        self.mock_osc.free_node.assert_called_once_with(test_node_id)
        self.mock_state.remove_synth.assert_called_once_with("test-id")
        # node_idマップからエントリが削除されたか確認
        self.assertNotIn(test_node_id, self.interface._node_id_map)
    
    def test_stop_synth_success(self):
        """stop_synth()メソッドの成功テスト"""
        asyncio.run(self._stop_synth_success())
    
    async def _stop_synth_not_found(self):
        """存在しないシンセの停止テスト（非同期）"""
        # モックの戻り値を設定
        self.mock_state.get_synth.return_value = None
        
        # asyncメソッドを実行
        result = await self.interface.stop_synth("non-existent-id")
        
        # 結果を検証
        self.assertEqual(result["status"], "error")
        self.assertIn("見つかりません", result["message"])
        
        # モックが正しく呼び出されたか確認
        self.mock_state.get_synth.assert_called_once_with("non-existent-id")
        self.mock_osc.free_node.assert_not_called()
        self.mock_state.remove_synth.assert_not_called()
    
    def test_stop_synth_not_found(self):
        """存在しないシンセの停止テスト"""
        asyncio.run(self._stop_synth_not_found())
    
    async def _stop_synth_invalid_id(self):
        """無効なIDでのシンセ停止テスト（非同期）"""
        with self.assertRaises(ValueError):
            await self.interface.stop_synth("")
    
    def test_stop_synth_invalid_id(self):
        """無効なIDでのシンセ停止テスト"""
        asyncio.run(self._stop_synth_invalid_id())
    
    async def _stop_synth_osc_error(self):
        """OSCエラー時のシンセ停止テスト（非同期）"""
        # モックの戻り値を設定
        test_node_id = 1001
        self.mock_state.get_synth.return_value = {
            "id": "test-id",
            "node_id": test_node_id,
            "name": "テストシンセ"
        }
        self.interface._node_id_map[test_node_id] = "test-id"
        
        # OSCエラーを発生させる
        self.mock_osc.free_node.side_effect = Exception("OSCエラー")
        
        # asyncメソッドを実行
        # OSCエラーでも処理は続行すべき
        result = await self.interface.stop_synth("test-id")
        
        # 結果を検証
        self.assertEqual(result["status"], "success")
        
        # モックが正しく呼び出されたか確認
        self.mock_state.get_synth.assert_called_once_with("test-id")
        self.mock_osc.free_node.assert_called_once_with(test_node_id)
        self.mock_state.remove_synth.assert_called_once_with("test-id")
    
    def test_stop_synth_osc_error(self):
        """OSCエラー時のシンセ停止テスト"""
        asyncio.run(self._stop_synth_osc_error())
    
    async def _stop_all_success(self):
        """stop_all()メソッドの成功テスト（非同期）"""
        # モックの戻り値を設定
        self.mock_state.get_all_synths.return_value = {
            "test-id-1": {"name": "テストシンセ1"},
            "test-id-2": {"name": "テストシンセ2"}
        }
        
        # ノードIDマッピングを追加
        self.interface._node_id_map = {1001: "test-id-1", 1002: "test-id-2"}
        
        # asyncメソッドを実行
        result = await self.interface.stop_all()
        
        # 結果を検証
        self.assertEqual(result["status"], "success")
        self.assertEqual(result["message"], "2個のシンセを停止しました")
        
        # モックが正しく呼び出されたか確認
        self.mock_osc.free_all.assert_called_once()
        self.mock_state.get_all_synths.assert_called_once()
        self.mock_state.clear_all_synths.assert_called_once()
        
        # ノードIDマッピングがクリアされたか確認
        self.assertEqual(len(self.interface._node_id_map), 0)
    
    def test_stop_all_success(self):
        """stop_all()メソッドの成功テスト"""
        asyncio.run(self._stop_all_success())
    
    async def _stop_all_failure(self):
        """stop_all()メソッドの失敗テスト（非同期）"""
        # OSCエラーを発生させる
        self.mock_osc.free_all.side_effect = Exception("OSCエラー")
        
        # asyncメソッドを実行
        with self.assertRaises(SuperColliderConnectionError):
            await self.interface.stop_all()
    
    def test_stop_all_failure(self):
        """stop_all()メソッドの失敗テスト"""
        asyncio.run(self._stop_all_failure())
    
    async def _list_synths_success(self):
        """list_synths()メソッドの成功テスト（非同期）"""
        # モックの戻り値を設定
        current_time = time.time()
        
        self.mock_state.get_all_synths.return_value = {
            "test-id-1": {
                "name": "テストシンセ1",
                "node_id": 1001,
                "created_at": current_time - 60,  # 1分前に作成
                "code": "// テストコード1"
            },
            "test-id-2": {
                "name": "テストシンセ2",
                "node_id": 1002,
                "created_at": current_time - 120,  # 2分前に作成
                "code": "// テストコード2"
            }
        }
        
        # asyncメソッドを実行
        result = await self.interface.list_synths()
        
        # 結果を検証
        self.assertEqual(len(result), 2)
        self.assertEqual(result[0]["name"], "テストシンセ1")
        self.assertEqual(result[0]["node_id"], 1001)
        self.assertEqual(result[1]["name"], "テストシンセ2")
        self.assertEqual(result[1]["node_id"], 1002)
        
        # モックが正しく呼び出されたか確認
        self.mock_state.get_all_synths.assert_called_once()
    
    def test_list_synths_success(self):
        """list_synths()メソッドの成功テスト"""
        asyncio.run(self._list_synths_success())
    
    async def _list_synths_empty(self):
        """シンセがない場合のlist_synths()メソッドのテスト（非同期）"""
        # モックの戻り値を設定
        self.mock_state.get_all_synths.return_value = {}
        
        # asyncメソッドを実行
        result = await self.interface.list_synths()
        
        # 結果を検証
        self.assertEqual(len(result), 0)
        
        # モックが正しく呼び出されたか確認
        self.mock_state.get_all_synths.assert_called_once()
    
    def test_list_synths_empty(self):
        """シンセがない場合のlist_synths()メソッドのテスト"""
        asyncio.run(self._list_synths_empty())
    
    async def _check_server_status_success(self):
        """check_server_status()メソッドの成功テスト（非同期）"""
        # モックの戻り値を設定
        self.mock_state.is_server_running.return_value = True
        self.mock_state.export_state.return_value = {
            "server_running": True,
            "active_synths": {"test-id": {"name": "テストシンセ"}}
        }
        
        # asyncメソッドを実行
        result = await self.interface.check_server_status()
        
        # 結果を検証
        self.assertEqual(result["status"], "success")
        self.assertTrue(result["server_running"])
        self.assertEqual(result["server_info"]["server_running"], True)
        
        # モックが正しく呼び出されたか確認
        self.mock_osc.notify.assert_called_once_with(True)
        self.mock_osc.status.assert_called_once()
        self.mock_state.is_server_running.assert_called_once()
        self.mock_state.export_state.assert_called_once()
    
    def test_check_server_status_success(self):
        """check_server_status()メソッドの成功テスト"""
        asyncio.run(self._check_server_status_success())
    
    async def _check_server_status_failure(self):
        """check_server_status()メソッドの失敗テスト（非同期）"""
        # OSCエラーを発生させる
        self.mock_osc.notify.side_effect = Exception("OSCエラー")
        
        # asyncメソッドを実行
        with self.assertRaises(SuperColliderConnectionError):
            await self.interface.check_server_status()
    
    def test_check_server_status_failure(self):
        """check_server_status()メソッドの失敗テスト"""
        asyncio.run(self._check_server_status_failure())
    
    async def _cleanup_success(self):
        """cleanup()メソッドの成功テスト（非同期）"""
        # モックの戻り値を設定
        self.mock_state.get_all_synths.return_value = {
            "test-id": {"name": "テストシンセ"}
        }
        
        # asyncメソッドを実行
        result = await self.interface.cleanup()
        
        # 結果を検証
        self.assertEqual(result["status"], "success")
        
        # モックが正しく呼び出されたか確認
        self.mock_osc.free_all.assert_called_once()
        self.mock_state.clear_all_synths.assert_called_once()
        self.mock_executor.stop_sclang_process.assert_called_once()
        self.mock_state.set_server_status.assert_called_once_with(False)
    
    def test_cleanup_success(self):
        """cleanup()メソッドの成功テスト"""
        asyncio.run(self._cleanup_success())
    
    async def _cleanup_with_errors(self):
        """エラーがある場合のcleanup()メソッドのテスト（非同期）"""
        # OSCエラーを発生させる
        self.mock_osc.free_all.side_effect = Exception("OSCエラー")
        
        # asyncメソッドを実行
        result = await self.interface.cleanup()
        
        # 結果を検証 - クリーンアップはエラーがあっても常に処理を続行する
        self.assertEqual(result["status"], "error")
        self.assertIn("クリーンアップエラー", result["message"])
    
    def test_cleanup_with_errors(self):
        """エラーがある場合のcleanup()メソッドのテスト"""
        asyncio.run(self._cleanup_with_errors())

if __name__ == '__main__':
    unittest.main()