#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
SPACO - 音響パターンカタログ

このモジュールは、一般的な音響パターンのテンプレートカタログを提供します。
これらのパターンはプリコンパイルされ、高速なコード生成に使用されます。
"""

import logging
import json
import os
from typing import Dict, Any, List, Optional, Set, Union, Tuple

from .precompiled_patterns import pattern_manager, PatternCompilationError

logger = logging.getLogger(__name__)

# 基本的な波形のテンプレート
BASIC_WAVEFORMS = {
    "sine": {
        "name": "基本正弦波",
        "pattern_type": "synth_def",
        "source_code": """
SynthDef(\\basicSine, {
    arg freq=440, amp=0.5, pan=0, attack=0.01, release=1.0, gate=1;
    var env, sig;
    env = EnvGen.kr(Env.asr(attack, 1, release), gate, doneAction: 2);
    sig = SinOsc.ar(freq, 0, amp) * env;
    sig = Pan2.ar(sig, pan);
    Out.ar(0, sig);
}).add;
""",
        "metadata": {
            "description": "基本的な正弦波シンセサイザー",
            "parameters": ["freq", "amp", "pan", "attack", "release", "gate"],
            "category": "basic_waveform"
        }
    },
    "saw": {
        "name": "基本ノコギリ波",
        "pattern_type": "synth_def",
        "source_code": """
SynthDef(\\basicSaw, {
    arg freq=440, amp=0.5, pan=0, attack=0.01, release=1.0, gate=1;
    var env, sig;
    env = EnvGen.kr(Env.asr(attack, 1, release), gate, doneAction: 2);
    sig = Saw.ar(freq, amp) * env;
    sig = Pan2.ar(sig, pan);
    Out.ar(0, sig);
}).add;
""",
        "metadata": {
            "description": "基本的なノコギリ波シンセサイザー",
            "parameters": ["freq", "amp", "pan", "attack", "release", "gate"],
            "category": "basic_waveform"
        }
    },
    "square": {
        "name": "基本矩形波",
        "pattern_type": "synth_def",
        "source_code": """
SynthDef(\\basicSquare, {
    arg freq=440, amp=0.5, pan=0, attack=0.01, release=1.0, gate=1, width=0.5;
    var env, sig;
    env = EnvGen.kr(Env.asr(attack, 1, release), gate, doneAction: 2);
    sig = Pulse.ar(freq, width, amp) * env;
    sig = Pan2.ar(sig, pan);
    Out.ar(0, sig);
}).add;
""",
        "metadata": {
            "description": "基本的な矩形波シンセサイザー",
            "parameters": ["freq", "amp", "pan", "attack", "release", "gate", "width"],
            "category": "basic_waveform"
        }
    },
    "triangle": {
        "name": "基本三角波",
        "pattern_type": "synth_def",
        "source_code": """
SynthDef(\\basicTriangle, {
    arg freq=440, amp=0.5, pan=0, attack=0.01, release=1.0, gate=1;
    var env, sig;
    env = EnvGen.kr(Env.asr(attack, 1, release), gate, doneAction: 2);
    sig = LFTri.ar(freq, 0, amp) * env;
    sig = Pan2.ar(sig, pan);
    Out.ar(0, sig);
}).add;
""",
        "metadata": {
            "description": "基本的な三角波シンセサイザー",
            "parameters": ["freq", "amp", "pan", "attack", "release", "gate"],
            "category": "basic_waveform"
        }
    }
}

# 一般的なエフェクトのテンプレート
COMMON_EFFECTS = {
    "reverb": {
        "name": "リバーブエフェクト",
        "pattern_type": "effect",
        "source_code": """
SynthDef(\\basicReverb, {
    arg in=0, out=0, mix=0.33, room=0.5, damp=0.5;
    var sig, wet;
    sig = In.ar(in, 2);
    wet = FreeVerb.ar(sig, mix, room, damp);
    Out.ar(out, wet);
}).add;
""",
        "metadata": {
            "description": "基本的なリバーブエフェクト",
            "parameters": ["in", "out", "mix", "room", "damp"],
            "category": "effect"
        }
    },
    "delay": {
        "name": "ディレイエフェクト",
        "pattern_type": "effect",
        "source_code": """
SynthDef(\\basicDelay, {
    arg in=0, out=0, delaytime=0.5, decay=4, mix=0.5;
    var sig, delayed, wet;
    sig = In.ar(in, 2);
    delayed = CombL.ar(sig, 5.0, delaytime, decay);
    wet = (sig * (1 - mix)) + (delayed * mix);
    Out.ar(out, wet);
}).add;
""",
        "metadata": {
            "description": "基本的なディレイエフェクト",
            "parameters": ["in", "out", "delaytime", "decay", "mix"],
            "category": "effect"
        }
    }
}

# 基本的なシーケンスパターンのテンプレート
SEQUENCE_PATTERNS = {
    "basic_sequence": {
        "name": "基本シーケンス",
        "pattern_type": "pattern",
        "source_code": """
(
Pdef(\\basicSequence, 
    Pbind(
        \\instrument, \\basicSine,
        \\dur, Pseq([0.25, 0.25, 0.5, 0.5, 0.25, 0.25], inf),
        \\freq, Pseq([440, 493.88, 523.25, 587.33, 659.25, 587.33], inf),
        \\amp, 0.5,
        \\legato, 0.8
    )
);
)
""",
        "metadata": {
            "description": "基本的な音楽シーケンス",
            "category": "pattern"
        }
    },
    "random_sequence": {
        "name": "ランダムシーケンス",
        "pattern_type": "pattern",
        "source_code": """
(
Pdef(\\randomSequence, 
    Pbind(
        \\instrument, \\basicSine,
        \\dur, Pwhite(0.1, 0.5, inf),
        \\freq, Prand([440, 493.88, 523.25, 587.33, 659.25, 698.46, 783.99], inf),
        \\amp, Pwhite(0.3, 0.7, inf),
        \\pan, Pwhite(-0.8, 0.8, inf),
        \\legato, 0.6
    )
);
)
""",
        "metadata": {
            "description": "ランダムな音楽シーケンス",
            "category": "pattern"
        }
    }
}

# 環境音のテンプレート
AMBIENT_SOUNDS = {
    "rain": {
        "name": "雨音",
        "pattern_type": "synth_def",
        "source_code": """
SynthDef(\\rainSound, {
    arg amp=0.5, density=10;
    var droplets, sig;
    droplets = Mix.fill(density, {
        var t;
        t = Dust.ar(1);
        Pan2.ar(
            WhiteNoise.ar * EnvGen.ar(Env.perc(0.001, Rand(0.05, 0.2)), t, Rand(0.01, 0.05)),
            Rand(-1.0, 1.0)
        )
    });
    sig = droplets * amp;
    Out.ar(0, sig);
}).add;
""",
        "metadata": {
            "description": "雨の音を生成するシンセ",
            "parameters": ["amp", "density"],
            "category": "ambient"
        }
    },
    "wind": {
        "name": "風の音",
        "pattern_type": "synth_def",
        "source_code": """
SynthDef(\\windSound, {
    arg amp=0.5, freq=800, fluctuation=5;
    var sig;
    sig = BPF.ar(
        WhiteNoise.ar,
        freq * SinOsc.kr(fluctuation, 0, 0.3, 1),
        0.1
    ) * amp;
    sig = Pan2.ar(sig, SinOsc.kr(0.1));
    Out.ar(0, sig);
}).add;
""",
        "metadata": {
            "description": "風の音を生成するシンセ",
            "parameters": ["amp", "freq", "fluctuation"],
            "category": "ambient"
        }
    }
}

# すべてのパターンを結合
ALL_PATTERNS = {
    **BASIC_WAVEFORMS,
    **COMMON_EFFECTS,
    **SEQUENCE_PATTERNS,
    **AMBIENT_SOUNDS
}


class PatternCatalog:
    """音響パターンカタログ管理クラス"""
    
    def __init__(self):
        """パターンカタログを初期化します"""
        self.initialized = False
        self.pattern_count = 0
    
    def initialize(self, force_recompile: bool = False) -> Dict[str, Any]:
        """
        パターンカタログを初期化し、すべてのパターンをプリコンパイルします。
        
        引数:
            force_recompile: True の場合、既存のパターンも再コンパイルします
            
        戻り値:
            Dict[str, Any]: 初期化結果の統計情報
        """
        if self.initialized and not force_recompile:
            logger.info("パターンカタログは既に初期化されています")
            return {"status": "already_initialized", "pattern_count": self.pattern_count}
        
        # 初期化ステータスをリセット
        self.initialized = False
        self.pattern_count = 0
        
        # コンパイル結果の統計情報
        results = {
            "total": len(ALL_PATTERNS),
            "success": 0,
            "failed": 0,
            "patterns": {}
        }
        
        # 各パターンのコンパイルを試行
        for pattern_id, pattern_info in ALL_PATTERNS.items():
            try:
                # 既存のパターンを確認（force_recompileがFalseの場合はそれを使用）
                existing_pattern = None
                if not force_recompile:
                    existing_pattern = pattern_manager.find_pattern_by_name(
                        pattern_info["name"], 
                        pattern_info["pattern_type"]
                    )
                
                if existing_pattern and not force_recompile:
                    results["success"] += 1
                    results["patterns"][pattern_id] = {
                        "status": "existing",
                        "name": pattern_info["name"]
                    }
                    self.pattern_count += 1
                else:
                    # パターンをコンパイルして保存
                    compiled_pattern = pattern_manager.compile_and_save(
                        name=pattern_info["name"],
                        pattern_type=pattern_info["pattern_type"],
                        source_code=pattern_info["source_code"],
                        metadata=pattern_info.get("metadata", {})
                    )
                    
                    results["success"] += 1
                    results["patterns"][pattern_id] = {
                        "status": "compiled",
                        "name": pattern_info["name"]
                    }
                    self.pattern_count += 1
                    
            except Exception as e:
                logger.error(f"パターン '{pattern_id}' のコンパイルに失敗しました: {str(e)}", exc_info=True)
                results["failed"] += 1
                results["patterns"][pattern_id] = {
                    "status": "failed",
                    "name": pattern_info["name"],
                    "error": str(e)
                }
        
        # 初期化完了をマーク
        self.initialized = True
        
        logger.info(f"パターンカタログの初期化が完了しました: "
                   f"{results['success']}/{results['total']} 成功")
        
        return results
    
    def get_pattern_by_id(self, pattern_id: str) -> Optional[Dict[str, Any]]:
        """
        パターンIDに基づいてパターン情報を取得します。
        
        引数:
            pattern_id: パターンID（キー）
            
        戻り値:
            Optional[Dict[str, Any]]: パターン情報、または None
        """
        if not self.initialized:
            self.initialize()
            
        if pattern_id in ALL_PATTERNS:
            return ALL_PATTERNS[pattern_id]
            
        return None
    
    def get_compiled_pattern(self, pattern_id: str) -> Any:
        """
        パターンIDに基づいてコンパイル済みパターンを取得します。
        
        引数:
            pattern_id: パターンID（キー）
            
        戻り値:
            Any: コンパイル済みパターン、またはNone
        """
        if not self.initialized:
            self.initialize()
            
        if pattern_id not in ALL_PATTERNS:
            return None
            
        pattern_info = ALL_PATTERNS[pattern_id]
        return pattern_manager.find_pattern_by_name(
            pattern_info["name"], 
            pattern_info["pattern_type"]
        )
    
    def get_patterns_by_category(self, category: str) -> List[Dict[str, Any]]:
        """
        カテゴリに基づいてパターンリストを取得します。
        
        引数:
            category: パターンカテゴリ
            
        戻り値:
            List[Dict[str, Any]]: パターン情報リスト
        """
        if not self.initialized:
            self.initialize()
            
        result = []
        
        for pattern_id, pattern_info in ALL_PATTERNS.items():
            metadata = pattern_info.get("metadata", {})
            if metadata.get("category") == category:
                result.append({
                    "id": pattern_id,
                    **pattern_info
                })
                
        return result
    
    def get_pattern_categories(self) -> List[str]:
        """
        利用可能なパターンカテゴリの一覧を取得します。
        
        戻り値:
            List[str]: カテゴリリスト
        """
        if not self.initialized:
            self.initialize()
            
        categories = set()
        
        for pattern_info in ALL_PATTERNS.values():
            metadata = pattern_info.get("metadata", {})
            if "category" in metadata:
                categories.add(metadata["category"])
                
        return sorted(list(categories))
    
    def get_stats(self) -> Dict[str, Any]:
        """
        カタログの統計情報を取得します。
        
        戻り値:
            Dict[str, Any]: 統計情報
        """
        if not self.initialized:
            self.initialize()
            
        categories = {}
        pattern_types = {}
        
        for pattern_info in ALL_PATTERNS.values():
            # パターンタイプごとに集計
            pattern_type = pattern_info["pattern_type"]
            pattern_types[pattern_type] = pattern_types.get(pattern_type, 0) + 1
            
            # カテゴリごとに集計
            metadata = pattern_info.get("metadata", {})
            if "category" in metadata:
                category = metadata["category"]
                categories[category] = categories.get(category, 0) + 1
        
        return {
            "total_patterns": len(ALL_PATTERNS),
            "pattern_count_by_type": pattern_types,
            "pattern_count_by_category": categories,
            "compiled_patterns": self.pattern_count,
            "initialized": self.initialized,
            "pattern_manager_stats": pattern_manager.get_pattern_stats()
        }


# シングルトンインスタンス
pattern_catalog = PatternCatalog()
