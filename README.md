# SPACO (SuperCollider And Claude Orchestration)

SPACO（SuperCollider And Claude Orchestration）は、Claude DesktopとSuperColliderを連携させ、自然言語による音響合成や映像制作の指示をSuperColliderで実現するシステムです。

## プロジェクト構造

```
/Users/mymac/spaco/
├── src/                   # ソースコード
│   ├── bridge/            # MCP Bridge
│   │   ├── handlers/      # リクエストハンドラー
│   │   ├── bridge.py      # メインブリッジクラス
│   │   ├── mcp_server.py  # MCPサーバー
│   │   └── response_generator.py # レスポンス生成
│   └── __init__.py
└── tests/                 # テスト
    └── test_mcp_bridge.py # MCP Bridgeのテスト
```

## 使用方法

SPACOは現在開発中であり、基本的な機能のみが実装されています。以下に簡単な使用例を示します：

```python
from spaco.src.bridge import SPACOBridge

# SPACOブリッジを作成して起動
bridge = SPACOBridge(host="localhost", port=8080)
bridge.start()
```

## MCPブリッジ

MCPブリッジは、Claude DesktopからModel Context Protocol (MCP)を通じて送信された指示を受け取り、SuperColliderで実行できるコードに変換します。現在の実装では以下の機能を提供しています：

1. MCPリクエストを受け付けるHTTPサーバー
2. 音響合成指示の簡易的な処理
3. SuperColliderコードの生成と実行
4. エラー処理とフィードバック

## 次のステップ

1. SuperCollider Interfaceの実装
2. 自然言語処理機能の強化
3. 音響合成パターンライブラリの充実
4. ユーザーインターフェースの改善

## ライセンス

このプロジェクトはMITライセンスの下で公開されています。
