#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
SPACO - MCP Server
このモジュールは、Model Context Protocol (MCP) サーバーを実装し、
Claude DesktopからのMCPリクエストを処理します。
"""

import json
import logging
import threading
import asyncio
from http.server import HTTPServer, BaseHTTPRequestHandler
from typing import Dict, Any, Callable, Optional, Union

# 非同期通信のためのライブラリ（実装時は適切なものをインポート）
try:
    import aiohttp
    from aiohttp import web
    ASYNC_SUPPORT = True
except ImportError:
    ASYNC_SUPPORT = False

# ロギングの設定
logger = logging.getLogger(__name__)


class MCPRequestHandler(BaseHTTPRequestHandler):
    """
    MCPリクエストを処理するためのHTTPリクエストハンドラー
    """

    def __init__(self, *args, **kwargs):
        # ハンドラーディクショナリはサーバーから取得
        self.handlers = {}
        super().__init__(*args, **kwargs)

    def do_POST(self):
        """
        POSTリクエストを処理します。
        """
        logger.debug(f"リクエストを受信しました: {self.path}")
        
        try:
            # リクエストの内容長を取得
            content_length = int(self.headers['Content-Length'])
            
            # リクエストボディを読み込む
            body = self.rfile.read(content_length).decode('utf-8')
            data = json.loads(body)
            
            # MCPのメッセージタイプを取得
            message_type = data.get('type', data.get('action'))
            
            if not message_type:
                self._send_error_response(400, "メッセージタイプが指定されていません")
                return

            # 対応するハンドラーを検索
            handler = self.server.handlers.get(message_type)
            
            if not handler:
                self._send_error_response(404, f"未知のメッセージタイプです: {message_type}")
                return
            
            # ハンドラーが非同期関数かどうかを判断
            if asyncio.iscoroutinefunction(handler):
                # 非同期ハンドラーの場合、新しいイベントループで実行
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                response_data = loop.run_until_complete(handler(data))
                loop.close()
            else:
                # 同期ハンドラーの場合、そのまま実行
                response_data = handler(data)
            
            # レスポンスを送信
            self._send_response(200, response_data)
            
        except json.JSONDecodeError:
            self._send_error_response(400, "無効なJSONフォーマットです")
        except Exception as e:
            logger.error(f"リクエスト処理中にエラーが発生しました: {str(e)}", exc_info=True)
            self._send_error_response(500, f"内部サーバーエラー: {str(e)}")
    
    def _send_response(self, status_code: int, data: Dict[str, Any]) -> None:
        """
        クライアントにJSONレスポンスを送信します。

        Args:
            status_code: HTTPステータスコード
            data: レスポンスデータ
        """
        self.send_response(status_code)
        self.send_header('Content-Type', 'application/json')
        self.end_headers()
        
        response = json.dumps(data).encode('utf-8')
        self.wfile.write(response)
    
    def _send_error_response(self, status_code: int, message: str) -> None:
        """
        クライアントにエラーレスポンスを送信します。

        Args:
            status_code: HTTPステータスコード
            message: エラーメッセージ
        """
        self._send_response(status_code, {
            "status": "error",
            "message": message
        })
    
    def log_message(self, format, *args):
        """
        HTTPサーバーのログメッセージをカスタマイズします。
        """
        logger.info(f"{self.address_string()} - {format % args}")


class MCPServer:
    """
    Model Context Protocol (MCP) サーバー
    Claude DesktopからのMCPリクエストを受け付け、処理します。
    """

    def __init__(self, host: str = "localhost", port: int = 8080):
        """
        MCPサーバーを初期化します。

        Args:
            host: サーバーのホスト名（デフォルト: localhost）
            port: サーバーのポート番号（デフォルト: 8080）
        """
        self.host = host
        self.port = port
        self.handlers = {}
        self.server = None
        self.server_thread = None
        self.is_running = False
        
        # 非同期サポート用のaiohttp Webアプリケーション
        if ASYNC_SUPPORT:
            self.app = web.Application()
            self.app.router.add_post('/mcp', self.handle_async_request)
            self.app.router.add_get('/status', self.handle_async_status)
        
        logger.info(f"MCPサーバーを初期化しました: {host}:{port}")
    
    def register_handler(self, message_type: str, handler: Callable) -> None:
        """
        メッセージタイプに対応するハンドラーを登録します。

        Args:
            message_type: MCPメッセージタイプ
            handler: メッセージを処理するハンドラー関数（同期または非同期）
        """
        logger.debug(f"ハンドラーを登録しています: {message_type}")
        self.handlers[message_type] = handler
    
    def start(self) -> None:
        """
        MCPサーバーを起動します。
        """
        if self.is_running:
            logger.warning("サーバーは既に実行中です")
            return
        
        # 非同期サポートがある場合はaiohttpを使う
        if ASYNC_SUPPORT:
            logger.info(f"非同期MCPサーバーを起動しています: {self.host}:{self.port}")
            web.run_app(self.app, host=self.host, port=self.port)
            return
        
        # 非同期サポートがない場合は従来のHTTPServerを使う
        # カスタムHTTPServerクラスの作成
        class MCPHTTPServer(HTTPServer):
            def __init__(self_server, *args, **kwargs):
                self_server.handlers = self.handlers
                super().__init__(*args, **kwargs)
        
        logger.info(f"MCPサーバーを起動しています: {self.host}:{self.port}")
        
        # サーバーの作成
        self.server = MCPHTTPServer((self.host, self.port), MCPRequestHandler)
        
        # サーバーの実行（別スレッド）
        self.server_thread = threading.Thread(target=self._run_server)
        self.server_thread.daemon = True
        self.server_thread.start()
        
        self.is_running = True
        logger.info("MCPサーバーの起動が完了しました")
    
    def _run_server(self) -> None:
        """
        サーバーのメインループを実行します。
        """
        try:
            self.server.serve_forever()
        except Exception as e:
            logger.error(f"サーバー実行中にエラーが発生しました: {str(e)}", exc_info=True)
    
    def stop(self) -> None:
        """
        MCPサーバーを停止します。
        """
        if not self.is_running:
            logger.warning("サーバーは実行されていません")
            return
        
        logger.info("MCPサーバーを停止しています...")
        
        if self.server:
            self.server.shutdown()
            self.server.server_close()
        
        if self.server_thread:
            # スレッドの終了を待機（タイムアウト付き）
            self.server_thread.join(timeout=5.0)
        
        self.is_running = False
        logger.info("MCPサーバーを停止しました")
    
    async def start_async(self) -> Any:
        """
        MCPサーバーを非同期で起動します。
        
        Returns:
            実行中のサーバーインスタンス
        """
        if not ASYNC_SUPPORT:
            raise RuntimeError("非同期サポートが利用できません。aiohttp をインストールしてください。")
        
        logger.info(f"非同期MCPサーバーを起動しています: {self.host}:{self.port}")
        runner = web.AppRunner(self.app)
        await runner.setup()
        site = web.TCPSite(runner, self.host, self.port)
        await site.start()
        self.is_running = True
        logger.info("非同期MCPサーバーの起動が完了しました")
        return runner
    
    async def handle_async_request(self, request: Any) -> web.Response:
        """
        非同期MCPリクエストを処理します。

        Args:
            request: aiohttpリクエスト

        Returns:
            aiohttpレスポンス
        """
        try:
            # リクエストボディをJSONとして解析
            data = await request.json()
            logger.info(f"非同期リクエストを受信しました: {data}")
            
            # メッセージタイプを取得
            message_type = data.get('type', data.get('action'))
            
            if not message_type:
                return web.json_response({
                    "status": "error",
                    "message": "メッセージタイプが指定されていません"
                }, status=400)
            
            # ハンドラーを検索
            handler = self.handlers.get(message_type)
            
            if not handler:
                return web.json_response({
                    "status": "error",
                    "message": f"未知のメッセージタイプです: {message_type}"
                }, status=404)
            
            # ハンドラーを実行
            if asyncio.iscoroutinefunction(handler):
                result = await handler(data)
            else:
                result = handler(data)
            
            # レスポンスを返す
            return web.json_response({
                "status": "success",
                "result": result
            })
            
        except json.JSONDecodeError:
            return web.json_response({
                "status": "error",
                "message": "無効なJSONフォーマットです"
            }, status=400)
        except Exception as e:
            logger.error(f"非同期リクエスト処理中にエラーが発生しました: {str(e)}", exc_info=True)
            return web.json_response({
                "status": "error",
                "message": f"内部サーバーエラー: {str(e)}"
            }, status=500)
    
    async def handle_async_status(self, request: Any) -> web.Response:
        """
        サーバーステータスリクエストを処理します。

        Args:
            request: aiohttpリクエスト

        Returns:
            aiohttpレスポンス
        """
        return web.json_response({
            "status": "running",
            "handlers": list(self.handlers.keys())
        })


if __name__ == "__main__":
    # スタンドアロンで実行する場合のサンプルコード
    logging.basicConfig(level=logging.INFO)
    
    # テスト用のエコーハンドラー
    async def async_echo_handler(request):
        return {"echo": request, "async": True}
    
    def sync_echo_handler(request):
        return {"echo": request, "async": False}
    
    # サーバーの作成と起動
    server = MCPServer()
    server.register_handler("echo_async", async_echo_handler)
    server.register_handler("echo_sync", sync_echo_handler)
    
    try:
        server.start()
        print(f"MCPサーバーを起動しました: {server.host}:{server.port}")
        print("終了するには Ctrl+C を押してください...")
        
        # メインスレッドを実行し続ける
        while True:
            import time
            time.sleep(1)
            
    except KeyboardInterrupt:
        print("サーバーを停止しています...")
        server.stop()
        print("サーバーを停止しました")
