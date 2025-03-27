# SPACO（SuperCollider And Claude Orchestration）要件定義書

SPACOは、Claude DesktopとSuperColliderを連携させ、自然言語による音響合成や映像制作の指示をSuperColliderで実現するシステムです。ユーザーがClaude Desktopに自然言語で音楽や音響に関する指示を出すと、MCPを通じてその指示がSuperColliderの適切なコードに変換され実行されます。

## 1. プロジェクト概要

### 1.1 目的

SPACOは、Claude DesktopとSuperColliderを連携させ、自然言語による音響合成や映像制作の指示をSuperColliderで実現するシステムです。ユーザーがClaude Desktopに自然言語で音楽や音響に関する指示を出すと、MCPを通じてその指示がSuperColliderの適切なコードに変換され実行されます。

### 1.2 背景

現代の音響合成や音楽制作は高度に専門化されており、SuperColliderのような強力なツールは独自の言語体系を持ち、習得に時間がかかります。一方、大規模言語モデル（LLM）の発展により、自然言語によるプログラミングの可能性が広がっています。SPACOは、これらの技術を組み合わせ、音楽制作の敷居を下げつつ、創造的な可能性を広げることを目指します。

### 1.3 ビジョン

「自然言語で思い描いた音響世界を、即座に聴くことができる」環境の実現。音楽家、サウンドデザイナー、メディアアーティスト、プログラミング初心者など、幅広いユーザーが直感的に高度な音響合成にアクセスできるようにします。

## 2. 基本機能要件

1. **自然言語入力処理**：Claude Desktopでの自然言語による音響合成指示の受付
2. **MCP連携**：Model Context Protocol（MCP）を通じたClaude DesktopとSuperColliderの連携
3. **コード生成**：自然言語指示からSuperColliderコードへの変換
4. **実行管理**：生成されたSuperColliderコードの実行と管理
5. **フィードバック**：実行結果のフィードバックとエラー処理

## 3. 拡張機能要件

1. **音響ライブラリ**：一般的な音響合成パターンのライブラリ化
2. **映像連携**：音響と連動した映像生成機能
3. **パラメータ調整**：生成された音響のインタラクティブな調整機能
4. **プロンプト・プロジェクト管理**：作成した音響合成コードとプロンプトの保存と管理（SQLite使用）
5. **コラボレーション**：複数ユーザーによる共同制作機能

## 4. ユーザーインターフェース要件

1. **Claude Desktop UI**：主要な入力インターフェースとしてClaude Desktopを使用
2. **SuperCollider連携UI**：SuperColliderの実行状態や出力を表示するインターフェース
3. **パラメータ調整UI**：生成された音響のパラメータをリアルタイムで調整するインターフェース
4. **プロンプト管理UI**：保存されたプロンプトの閲覧、検索、編集、カテゴリ分類を行うインターフェース

## 5. 性能要件

1. **応答時間**：自然言語指示からSuperColliderコード生成までの時間を3秒以内に抑える
2. **実行性能**：生成されたコードの実行開始までの時間を2秒以内に抑える
3. **同時処理能力**：複数の音響合成プロセスを同時に管理できる能力
4. **データベース性能**：SQLiteを使用したプロンプト検索の応答時間を1秒以内に抑える

## 6. 信頼性要件

1. **エラー処理**：不適切なコード生成や実行エラーの適切な処理と回復
2. **データ保全**：作成したプロジェクトの自動保存と復元機能
3. **安定性**：長時間の使用でもシステムの安定性を維持
4. **データベース整合性**：SQLiteデータベースの整合性維持とバックアップ機能

## 7. 拡張性要件

1. **新機能追加**：プラグインアーキテクチャによる機能拡張の容易さ
2. **外部ツール連携**：他の音楽制作ツールやDAWとの連携可能性
3. **カスタマイズ**：ユーザー独自の音響合成パターンの登録と再利用
4. **データベーススキーマ拡張**：将来的な機能追加に対応できるSQLiteスキーマ設計

## 8. セキュリティ要件

1. **コード実行の安全性**：生成されたコードの安全な実行環境の提供
2. **データ保護**：ユーザープロジェクトの適切な保護
3. **アクセス制御**：機能へのアクセス制御とユーザー認証（必要に応じて）
4. **データベースセキュリティ**：SQLiteデータベースへの不正アクセス防止

## 9. システムアーキテクチャ

SPACOは以下の主要コンポーネントで構成されます：

1. **Claude Desktop**：ユーザーインターフェースと自然言語処理
2. **MCP Bridge**：Claude DesktopとSuperColliderの間の通信を管理
3. **Language Processor**：自然言語をSuperColliderコードに変換
4. **SuperCollider Interface**：SuperColliderとの通信と制御
5. **Feedback Manager**：実行結果とエラーのフィードバック管理
6. **Prompt Storage**：SQLiteを使用したプロンプトとコードの保存・管理

```
[ユーザー] <-> [Claude Desktop] <-> [MCP Bridge] <-> [Language Processor] <-> [SuperCollider Interface] <-> [SuperCollider]
                                         ^                    ^                           ^
                                         |                    |                           |
                                         v                    v                           v
                               [Feedback Manager] <-----> [Prompt Storage (SQLite)] <-> [Project Files]
```

## 10. 通信プロトコル

1. **MCP（Model Context Protocol）**：Claude DesktopとMCP Bridgeの間の通信
2. **OSC（Open Sound Control）**：SuperCollider Interfaceとscsynthの間の通信
3. **JSON-RPC**：コンポーネント間の内部通信
4. **SQLite API**：プロンプトストレージとの通信

## 11. 処理フロー

1. ユーザーがClaude Desktopに自然言語で指示を入力
2. Claude DesktopがMCP Bridgeを通じて指示を送信
3. Language Processorが指示をSuperColliderコードに変換
4. SuperCollider Interfaceがコードをsclangに送信して実行
5. 実行結果がFeedback Managerを通じてユーザーにフィードバック
6. 生成されたプロンプトとコードがPrompt Storageに保存（オプション）

## 12. MCP Bridge実装詳細

1. **MCP Server**：Claude DesktopからのMCPリクエストを受け付けるサーバー
2. **Request Handler**：MCPリクエストの解析と処理
3. **Response Generator**：MCPレスポンスの生成と送信

```python
# MCP Bridge実装例（Python）
from mcp_server import MCPServer
from language_processor import LanguageProcessor
from supercollider_interface import SuperColliderInterface
from prompt_storage import PromptStorage

class SPACOBridge:
    def __init__(self):
        self.mcp_server = MCPServer(port=8080)
        self.language_processor = LanguageProcessor()
        self.sc_interface = SuperColliderInterface()
        self.prompt_storage = PromptStorage("spaco_prompts.db")
        
        self.mcp_server.register_handler("generate_sound", self.handle_sound_request)
        self.mcp_server.register_handler("save_prompt", self.handle_save_prompt)
        self.mcp_server.register_handler("search_prompts", self.handle_search_prompts)
    
    def handle_sound_request(self, request):
        # 自然言語指示を受け取る
        instruction = request.get("instruction")
        
        # SuperColliderコードに変換
        sc_code = self.language_processor.process(instruction)
        
        # SuperColliderで実行
        result = self.sc_interface.execute(sc_code)
        
        # 結果を返す
        return {"status": "success", "result": result}
    
    def handle_save_prompt(self, request):
        # プロンプトとコードを保存
        prompt_text = request.get("prompt")
        sc_code = request.get("code")
        category = request.get("category", "general")
        tags = request.get("tags", [])
        
        prompt_id = self.prompt_storage.save_prompt(
            text=prompt_text,
            sc_code=sc_code,
            category=category,
            tags=tags
        )
        
        return {"status": "success", "prompt_id": prompt_id}
    
    def handle_search_prompts(self, request):
        # プロンプトを検索
        query = request.get("query")
        category = request.get("category")
        tags = request.get("tags")
        limit = request.get("limit", 10)
        
        prompts = self.prompt_storage.search_prompts(
            query=query,
            category=category,
            tags=tags,
            limit=limit
        )
        
        return {"status": "success", "prompts": prompts}
    
    def start(self):
        self.mcp_server.start()

if __name__ == "__main__":
    bridge = SPACOBridge()
    bridge.start()
```

## 13. 言語処理実装詳細

1. **自然言語解析**：指示の意図と音響パラメータの抽出
2. **中間表現生成**：音響合成の抽象的な中間表現への変換
3. **コード生成**：中間表現からSuperColliderコードの生成

自然言語からSuperColliderコードへの変換を効率的に行うため、以下の階層的な中間表現モデルを採用します：

1. **意図レベル**：指示の基本的な意図（音生成、エフェクト適用、シーケンス作成など）
2. **パラメータレベル**：音響パラメータ（周波数、振幅、エンベロープなど）
3. **構造レベル**：音響合成の構造と関係性（レイヤー、シーケンス、並列処理など）
4. **DSLレベル**：SuperCollider固有の構文とセマンティクスへのマッピング

```python
# Language Processor実装例（Python）
import re
import json
from typing import Dict, List, Any

class LanguageProcessor:
    def __init__(self):
        self.intent_recognizer = IntentRecognizer()
        self.parameter_extractor = ParameterExtractor()
        self.structure_builder = StructureBuilder()
        self.code_generator = CodeGenerator()
        
    def process(self, instruction: str) -> str:
        # 意図認識
        intent = self.intent_recognizer.recognize(instruction)
        
        # パラメータ抽出
        parameters = self.parameter_extractor.extract(instruction, intent)
        
        # 構造構築
        structure = self.structure_builder.build(intent, parameters)
        
        # コード生成
        sc_code = self.code_generator.generate(structure)
        
        return sc_code
    
class IntentRecognizer:
    def recognize(self, instruction: str) -> Dict[str, Any]:
        # 基本的な意図を認識（音生成、エフェクト適用など）
        # 実装...
        return {"type": "sound_generation", "subtype": "simple_tone"}
    
class ParameterExtractor:
    def extract(self, instruction: str, intent: Dict[str, Any]) -> Dict[str, Any]:
        # 意図に基づいてパラメータを抽出
        # 実装...
        return {"frequency": 440, "amplitude": 0.5, "duration": 2.0}
    
class StructureBuilder:
    def build(self, intent: Dict[str, Any], parameters: Dict[str, Any]) -> Dict[str, Any]:
        # 意図とパラメータから構造を構築
        # 実装...
        return {
            "type": "synth",
            "def_name": "simpleTone",
            "parameters": parameters,
            "connections": []
        }
    
class CodeGenerator:
    def generate(self, structure: Dict[str, Any]) -> str:
        # 構造からSuperColliderコードを生成
        # 実装...
        return "SynthDef(\\simpleTone, { |out=0, freq=440, amp=0.5, gate=1|\n  var sig, env;\n  sig = SinOsc.ar(freq);\n  env = EnvGen.kr(Env.asr(0.01, 1, 0.1), gate, doneAction: 2);\n  Out.ar(out, sig * env * amp);\n}).add;\n\nSynth(\\simpleTone, [\\freq, 440, \\amp, 0.5]);"
```

## 14. プロンプトストレージ実装詳細

1. **データベーススキーマ**：プロンプト、コード、カテゴリ、タグの関係を定義
2. **CRUD操作**：プロンプトの作成、読み取り、更新、削除
3. **検索機能**：テキスト検索、カテゴリ・タグによるフィルタリング

```python
# Prompt Storage実装例（Python with SQLite）
import sqlite3
import json
from typing import Dict, List, Any, Optional

class PromptStorage:
    def __init__(self, db_path="spaco_prompts.db"):
        self.db_path = db_path
        self.conn = sqlite3.connect(db_path)
        self.create_tables()
    
    def create_tables(self):
        """データベーステーブルの作成"""
        cursor = self.conn.cursor()
        
        # プロンプトテーブル
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS prompts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            text TEXT NOT NULL,
            sc_code TEXT NOT NULL,
            category TEXT DEFAULT 'general',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            rating INTEGER DEFAULT 0
        )
        ''')
        
        # タグテーブル
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS tags (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT UNIQUE NOT NULL
        )
        ''')
        
        # プロンプト-タグ関連テーブル
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS prompt_tags (
            prompt_id INTEGER,
            tag_id INTEGER,
            PRIMARY KEY (prompt_id, tag_id),
            FOREIGN KEY (prompt_id) REFERENCES prompts (id) ON DELETE CASCADE,
            FOREIGN KEY (tag_id) REFERENCES tags (id) ON DELETE CASCADE
        )
        ''')
        
        self.conn.commit()
    
    def save_prompt(self, text: str, sc_code: str, category: str = "general", tags: List[str] = None) -> int:
        """プロンプトの保存"""
        cursor = self.conn.cursor()
        
        # プロンプトの挿入
        cursor.execute(
            "INSERT INTO prompts (text, sc_code, category) VALUES (?, ?, ?)",
            (text, sc_code, category)
        )
        prompt_id = cursor.lastrowid
        
        # タグの処理
        if tags:
            for tag in tags:
                # タグが存在しなければ作成
                cursor.execute(
                    "INSERT OR IGNORE INTO tags (name) VALUES (?)",
                    (tag,)
                )
                
                # タグIDの取得
                cursor.execute("SELECT id FROM tags WHERE name = ?", (tag,))
                tag_id = cursor.fetchone()[0]
                
                # プロンプト-タグ関連の作成
                cursor.execute(
                    "INSERT INTO prompt_tags (prompt_id, tag_id) VALUES (?, ?)",
                    (prompt_id, tag_id)
                )
        
        self.conn.commit()
        return prompt_id
    
    def get_prompt(self, prompt_id: int) -> Optional[Dict[str, Any]]:
        """IDによるプロンプトの取得"""
        cursor = self.conn.cursor()
        
        # プロンプトの取得
        cursor.execute(
            "SELECT id, text, sc_code, category, created_at, updated_at, rating FROM prompts WHERE id = ?",
            (prompt_id,)
        )
        prompt_row = cursor.fetchone()
        
        if not prompt_row:
            return None
        
        prompt = {
            "id": prompt_row[0],
            "text": prompt_row[1],
            "sc_code": prompt_row[2],
            "category": prompt_row[3],
            "created_at": prompt_row[4],
            "updated_at": prompt_row[5],
            "rating": prompt_row[6],
            "tags": []
        }
        
        # タグの取得
        cursor.execute(
            """
            SELECT t.name
            FROM tags t
            JOIN prompt_tags pt ON t.id = pt.tag_id
            WHERE pt.prompt_id = ?
            """,
            (prompt_id,)
        )
        
        prompt["tags"] = [row[0] for row in cursor.fetchall()]
        
        return prompt
    
    def search_prompts(self, query: str = None, category: str = None, tags: List[str] = None, limit: int = 10) -> List[Dict[str, Any]]:
        """プロンプトの検索"""
        cursor = self.conn.cursor()
        sql_query = """
        SELECT DISTINCT p.id
        FROM prompts p
        """
        
        params = []
        where_clauses = []
        
        # タグによる絞り込み
        if tags:
            sql_query += """
            JOIN prompt_tags pt ON p.id = pt.prompt_id
            JOIN tags t ON pt.tag_id = t.id
            """
            placeholders = ", ".join(["?" for _ in tags])
            where_clauses.append(f"t.name IN ({placeholders})")
            params.extend(tags)
        
        # テキスト検索
        if query:
            where_clauses.append("p.text LIKE ? OR p.sc_code LIKE ?")
            params.extend([f"%{query}%", f"%{query}%"])
        
        # カテゴリによる絞り込み
        if category:
            where_clauses.append("p.category = ?")
            params.append(category)
        
        # WHERE句の構築
        if where_clauses:
            sql_query += " WHERE " + " AND ".join(where_clauses)
        
        # 並び替えと制限
        sql_query += " ORDER BY p.updated_at DESC LIMIT ?"
        params.append(limit)
        
        cursor.execute(sql_query, params)
        prompt_ids = [row[0] for row in cursor.fetchall()]
        
        # 結果の取得
        results = []
        for prompt_id in prompt_ids:
            prompt = self.get_prompt(prompt_id)
            if prompt:
                results.append(prompt)
        
        return results
    
    def update_prompt(self, prompt_id: int, text: str = None, sc_code: str = None, category: str = None, tags: List[str] = None) -> bool:
        """プロンプトの更新"""
        cursor = self.conn.cursor()
        
        # 更新対象フィールドの収集
        update_fields = []
        params = []
        
        if text is not None:
            update_fields.append("text = ?")
            params.append(text)
        
        if sc_code is not None:
            update_fields.append("sc_code = ?")
            params.append(sc_code)
        
        if category is not None:
            update_fields.append("category = ?")
            params.append(category)
        
        # 更新時刻の更新
        update_fields.append("updated_at = CURRENT_TIMESTAMP")
        
        if not update_fields:
            return False
        
        # プロンプトの更新
        sql_query = f"UPDATE prompts SET {', '.join(update_fields)} WHERE id = ?"
        params.append(prompt_id)
        
        cursor.execute(sql_query, params)
        
        # タグの更新
        if tags is not None:
            # 既存のタグ関連を削除
            cursor.execute("DELETE FROM prompt_tags WHERE prompt_id = ?", (prompt_id,))
            
            # 新しいタグ関連を作成
            for tag in tags:
                cursor.execute("INSERT OR IGNORE INTO tags (name) VALUES (?)", (tag,))
                cursor.execute("SELECT id FROM tags WHERE name = ?", (tag,))
                tag_id = cursor.fetchone()[0]
                cursor.execute(
                    "INSERT INTO prompt_tags (prompt_id, tag_id) VALUES (?, ?)",
                    (prompt_id, tag_id)
                )
        
        self.conn.commit()
        return cursor.rowcount > 0
    
    def delete_prompt(self, prompt_id: int) -> bool:
        """プロンプトの削除"""
        cursor = self.conn.cursor()
        cursor.execute("DELETE FROM prompts WHERE id = ?", (prompt_id,))
        self.conn.commit()
        return cursor.rowcount > 0
    
    def update_prompt_rating(self, prompt_id, rating):
        """プロンプトの評価を更新"""
        cursor = self.conn.cursor()
        cursor.execute("UPDATE prompts SET rating = ? WHERE id = ?", (rating, prompt_id))
        self.conn.commit()
    
    def __del__(self):
        self.conn.close()
```

## 15. 中間表現の技術的リスク対策

SuperColliderの独自言語からの変換における中間表現の技術的リスクに対処するため、以下の方法を採用します：

1. **テンプレートベースのアプローチ**：一般的なユースケースに対応するテンプレートライブラリを構築
2. **階層的変換**：抽象度の高い表現から低レベルのコードへ段階的に変換
3. **型安全な中間表現**：厳格な型チェックによる変換エラーの早期発見
4. **フォールバックメカニズム**：変換が難しい場合に備えた代替手段の用意
5. **ユーザーフィードバック**：生成されたコードの品質改善のためのフィードバックループ
6. **制約付き言語モデル**：SuperColliderの制約とセマンティクスを考慮した言語モデルの活用

## 16. パフォーマンス最適化戦略

SPACOシステムのパフォーマンスを最適化するため、以下の戦略を採用します：

1. **メモ化**：頻繁に使用される変換パターンの結果をキャッシュ
2. **並列処理**：独立した処理の並列実行による全体の応答時間短縮
3. **プリコンパイル**：一般的なパターンの事前コンパイルとキャッシング
4. **インデックス最適化**：SQLiteデータベースの検索クエリのインデックス最適化
5. **リソース管理**：メモリとCPU使用率の適切な管理
6. **非同期処理**：長時間実行タスクの非同期処理によるUI応答性向上
7. **バッチ処理**：複数の小さな操作をバッチ処理でまとめることによる効率化
8. **プロファイリングとモニタリング**：継続的なパフォーマンス評価と改善
