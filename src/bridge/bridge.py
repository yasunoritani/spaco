#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
SPACO - MCP Bridge
このモジュールは、Claude DesktopとSuperColliderの間の通信を管理するMCP Bridgeの
コアコンポーネントを実装しています。
"""

import logging
import asyncio
from typing import Dict, Any, Optional

from .mcp_server import MCPServer
from .handlers.sound_handler import SoundHandler
from ..language_processor import LanguageProcessor
from ..supercollider_interface import SuperColliderInterface

# ロギングの設定
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class SPACOBridge:
    """
    SPACOブリッジのメインクラス
    Claude DesktopからのMCPリクエストを処理し、SuperColliderへ命令を送信します。
    """

    def __init__(self, host: str = "localhost", port: int = 8080):
        """
        SPACOブリッジを初期化します。

        Args:
            host: MCPサーバーのホスト名（デフォルト: localhost）
            port: MCPサーバーのポート番号（デフォルト: 8080）
        """
        logger.info(f"SPACOブリッジを初期化しています（{host}:{port}）")
        self.mcp_server = MCPServer(host=host, port=port)
        self.language_processor = LanguageProcessor()
        self.sc_interface = SuperColliderInterface()
        
        # ハンドラーの作成
        self.sound_handler = SoundHandler(self.sc_interface)
        
        # ハンドラーの登録
        self.register_handlers()
        
        logger.info("SPACOブリッジの初期化が完了しました")
    
    def register_handlers(self) -> None:
        """
        MCPサーバーにリクエストハンドラーを登録します。
        """
        logger.debug("リクエストハンドラーを登録しています")
        self.mcp_server.register_handler("generate_sound", self.sound_handler.handle_generate_sound)
        self.mcp_server.register_handler("stop_sound", self.sound_handler.handle_stop_sound)
    
    def start(self) -> None:
        """
        SPACOブリッジを起動します。
        """
        logger.info("SPACOブリッジを起動しています...")
        try:
            self.mcp_server.start()
        except KeyboardInterrupt:
            self.stop()
    
    async def start_async(self) -> None:
        """
        SPACOブリッジを非同期で起動します。
        """
        logger.info("SPACOブリッジを非同期で起動しています...")
        return await self.mcp_server.start_async()
    
    def stop(self) -> None:
        """
        SPACOブリッジを停止します。
        """
        logger.info("SPACOブリッジを停止しています...")
        self.mcp_server.stop()
        logger.info("SPACOブリッジを停止しました")


if __name__ == "__main__":
    # スタンドアロンで実行する場合のサンプルコード
    bridge = SPACOBridge()
    try:
        bridge.start()
    except KeyboardInterrupt:
        bridge.stop()
