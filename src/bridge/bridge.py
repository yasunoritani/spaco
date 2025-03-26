#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
SPACO - MCP Bridge
このモジュールは、Claude DesktopとSuperColliderの間の通信を管理するMCP Bridgeの
コアコンポーネントを実装しています。
"""

import logging
import asyncio
import os
import yaml
from typing import Dict, Any, Optional, Callable, List, Tuple

from .mcp_server import MCPServer
from .response_generator import ResponseGenerator
from .handlers.sound_handler import SoundHandler
from ..language_processor import LanguageProcessor
from ..sc_interface.interface import SuperColliderInterface, SuperColliderError

# ロギングの設定
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class ConfigurationError(Exception):
    """設定関連のエラー"""
    pass


class RequestValidationError(Exception):
    """リクエスト検証エラー"""
    pass


class SPACOBridge:
    """
    SPACOブリッジのメインクラス
    Claude DesktopからのMCPリクエストを処理し、SuperColliderへ命令を送信します。
    """

    def __init__(self, host: str = "localhost", port: int = 8080, config_path: Optional[str] = None):
        """
        SPACOブリッジを初期化します。

        Args:
            host: MCPサーバーのホスト名（デフォルト: localhost）
            port: MCPサーバーのポート番号（デフォルト: 8080）
            config_path: 設定ファイルのパス（指定がない場合はデフォルト設定を使用）
        """
        logger.info(f"SPACOブリッジを初期化しています（{host}:{port}）")
        
        # 設定の読み込み
        self.config = self._load_config(config_path)
        
        # コンポーネントの初期化
        self.mcp_server = MCPServer(
            host=host or self.config.get("mcp_server", {}).get("host", "localhost"),
            port=port or self.config.get("mcp_server", {}).get("port", 8080)
        )
        self.language_processor = LanguageProcessor(
            models_dir=self.config.get("language_processor", {}).get("models_dir")
        )
        self.sc_interface = self._create_sc_interface()
        self.response_generator = ResponseGenerator()
        
        # ハンドラーの登録
        self.request_handlers = self._register_handlers()
        
        # MCPサーバーにハンドラーを登録
        self._setup_mcp_handlers()
        
        logger.info("SPACOブリッジの初期化が完了しました")
    
    def _load_config(self, config_path: Optional[str] = None) -> Dict[str, Any]:
        """
        設定を読み込みます。
        設定ファイルが指定されている場合はそれを、そうでない場合はデフォルト設定を使用します。
        
        Args:
            config_path: 設定ファイルのパス
            
        Returns:
            Dict[str, Any]: 設定辞書
        """
        try:
            # デフォルト設定
            default_config = {
                "mcp_server": {
                    "host": "localhost",
                    "port": 8080,
                    "rate_limit": 60  # 1分間あたりのリクエスト数制限
                },
                "sc_interface": {
                    "host": "127.0.0.1",
                    "port": 57110,
                    "sclang_path": "sclang"
                },
                "language_processor": {
                    "models_dir": os.path.join(os.path.dirname(__file__), "../models"),
                    "default_model": "default"
                },
                "logging": {
                    "level": "INFO",
                    "file": None
                }
            }
            
            # 設定ファイルが指定されている場合は読み込む
            if config_path and os.path.exists(config_path):
                with open(config_path, 'r') as f:
                    file_config = yaml.safe_load(f)
                    # デフォルト設定を更新
                    for section, settings in file_config.items():
                        if section in default_config and isinstance(settings, dict):
                            default_config[section].update(settings)
                        else:
                            default_config[section] = settings
                            
                logger.info(f"設定を {config_path} から読み込みました")
            else:
                logger.info("デフォルト設定を使用します")
                
            return default_config
            
        except Exception as e:
            logger.exception(f"設定の読み込み中にエラーが発生しました: {str(e)}")
            raise ConfigurationError(f"設定読み込みエラー: {str(e)}") from e
    
    def _create_sc_interface(self) -> SuperColliderInterface:
        """
        SuperColliderインターフェースを作成します。
        
        Returns:
            SuperColliderInterface: 初期化されたSuperColliderインターフェース
        """
        try:
            sc_config = self.config.get("sc_interface", {})
            return SuperColliderInterface(
                host=sc_config.get("host", "127.0.0.1"),
                port=sc_config.get("port", 57110),
                sclang_path=sc_config.get("sclang_path", "sclang")
            )
        except Exception as e:
            logger.exception(f"SuperColliderインターフェースの作成中にエラーが発生しました: {str(e)}")
            raise
    
    def _register_handlers(self) -> Dict[str, Any]:
        """
        リクエストハンドラーを登録します。
        
        Returns:
            Dict[str, Any]: ハンドラー辞書
        """
        logger.debug("リクエストハンドラーを作成しています")
        try:
            # ハンドラーの作成
            sound_handler = SoundHandler(self.sc_interface, self.language_processor)
            
            # ハンドラー辞書の作成
            handlers = {
                "generate_sound": sound_handler.handle_generate_sound,
                "stop_sound": sound_handler.handle_stop_sound,
                "list_sounds": sound_handler.handle_list_sounds
            }
            
            return handlers
        except Exception as e:
            logger.exception(f"ハンドラーの作成中にエラーが発生しました: {str(e)}")
            raise
    
    def _setup_mcp_handlers(self) -> None:
        """
        MCPサーバーにハンドラーを登録します。
        """
        for action, handler in self.request_handlers.items():
            self.mcp_server.register_handler(action, handler)
            logger.debug(f"ハンドラーを登録しました: {action}")
    
    async def process_request(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """
        MCPリクエストを処理します。
        
        Args:
            request: MCPリクエスト
            
        Returns:
            Dict[str, Any]: 処理結果
        """
        try:
            # リクエストの検証
            self._validate_request(request)
            
            # アクションの取得
            action = request.get("action")
            
            # 適切なハンドラーを選択
            handler = self.request_handlers.get(action)
            if not handler:
                raise RequestValidationError(f"未知のアクション: {action}")
                
            # リクエスト処理
            result = await handler(request)
            
            # レスポンス生成
            return self.response_generator.generate_response(result, request)
            
        except RequestValidationError as e:
            logger.warning(f"リクエスト検証エラー: {str(e)}")
            return self.response_generator.generate_error_response(str(e), 400, "request_validation_error")
            
        except SuperColliderError as e:
            logger.error(f"SuperColliderエラー: {str(e)}")
            return self.response_generator.generate_error_response(str(e), 500, "supercollider_error")
            
        except Exception as e:
            logger.exception(f"リクエスト処理中に予期しないエラーが発生しました: {str(e)}")
            return self.response_generator.generate_error_response(str(e), 500, "internal_error")
    
    def _validate_request(self, request: Dict[str, Any]) -> None:
        """
        MCPリクエストを検証します。
        
        Args:
            request: 検証するリクエスト
            
        Raises:
            RequestValidationError: リクエストが無効な場合
        """
        if not request:
            raise RequestValidationError("リクエストが空です")
            
        if not isinstance(request, dict):
            raise RequestValidationError("リクエストはJSONオブジェクトである必要があります")
            
        # 必須フィールドの確認
        required_fields = ["action"]
        for field in required_fields:
            if field not in request:
                raise RequestValidationError(f"必須フィールドが欠けています: {field}")
    
    def start(self) -> None:
        """
        SPACOブリッジを起動します。
        """
        logger.info("SPACOブリッジを起動しています...")
        try:
            # MCPサーバーにリクエストプロセッサを設定
            self.mcp_server.set_request_processor(self.process_request)
            
            # サーバーを起動
            self.mcp_server.start()
        except KeyboardInterrupt:
            self.stop()
        except Exception as e:
            logger.exception(f"SPACOブリッジの起動中にエラーが発生しました: {str(e)}")
            self.stop()
            raise
    
    async def start_async(self) -> None:
        """
        SPACOブリッジを非同期で起動します。
        """
        logger.info("SPACOブリッジを非同期で起動しています...")
        try:
            # MCPサーバーにリクエストプロセッサを設定
            self.mcp_server.set_request_processor(self.process_request)
            
            # サーバーを非同期で起動
            return await self.mcp_server.start_async()
        except Exception as e:
            logger.exception(f"SPACOブリッジの非同期起動中にエラーが発生しました: {str(e)}")
            await self.stop_async()
            raise
    
    def stop(self) -> None:
        """
        SPACOブリッジを停止します。
        """
        logger.info("SPACOブリッジを停止しています...")
        try:
            # SuperColliderインターフェースのクリーンアップ
            if hasattr(self, 'sc_interface') and self.sc_interface:
                # asyncioループの取得または作成
                try:
                    loop = asyncio.get_event_loop()
                except RuntimeError:
                    loop = asyncio.new_event_loop()
                    asyncio.set_event_loop(loop)
                    
                # cleanupメソッドの実行
                if loop.is_running():
                    future = asyncio.run_coroutine_threadsafe(self.sc_interface.cleanup(), loop)
                    future.result()
                else:
                    loop.run_until_complete(self.sc_interface.cleanup())
            
            # MCPサーバーの停止
            if hasattr(self, 'mcp_server') and self.mcp_server:
                self.mcp_server.stop()
                
            logger.info("SPACOブリッジを停止しました")
        except Exception as e:
            logger.exception(f"SPACOブリッジの停止中にエラーが発生しました: {str(e)}")
            # エラーがあっても続行する（最善を尽くしてクリーンアップ）
    
    async def stop_async(self) -> None:
        """
        SPACOブリッジを非同期で停止します。
        """
        logger.info("SPACOブリッジを非同期で停止しています...")
        try:
            # SuperColliderインターフェースのクリーンアップ
            if hasattr(self, 'sc_interface') and self.sc_interface:
                await self.sc_interface.cleanup()
            
            # MCPサーバーの停止
            if hasattr(self, 'mcp_server') and self.mcp_server:
                await self.mcp_server.stop_async()
                
            logger.info("SPACOブリッジを非同期で停止しました")
        except Exception as e:
            logger.exception(f"SPACOブリッジの非同期停止中にエラーが発生しました: {str(e)}")
            # エラーがあっても続行する（最善を尽くしてクリーンアップ）


if __name__ == "__main__":
    # スタンドアロンで実行する場合のサンプルコード
    import argparse
    
    # コマンドライン引数の解析
    parser = argparse.ArgumentParser(description='SPACO Bridge')
    parser.add_argument('--host', default='localhost', help='MCPサーバーのホスト名')
    parser.add_argument('--port', type=int, default=8080, help='MCPサーバーのポート番号')
    parser.add_argument('--config', help='設定ファイルのパス')
    args = parser.parse_args()
    
    try:
        # ブリッジの作成と起動
        bridge = SPACOBridge(host=args.host, port=args.port, config_path=args.config)
        bridge.start()
    except KeyboardInterrupt:
        logger.info("ユーザーによって中断されました")
    except Exception as e:
        logger.exception(f"実行中にエラーが発生しました: {str(e)}")
    finally:
        # クリーンアップを確実に実行
        if 'bridge' in locals():
            bridge.stop()
