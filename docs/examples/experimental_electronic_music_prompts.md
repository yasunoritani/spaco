# 実験的電子音楽スタイルのSuperColliderプロンプト例

このドキュメントでは、Oval、Autechre、Nikakoiなどの実験的電子音楽アーティストのスタイルを模倣するためのSuperColliderプロンプト例を提供します。これらのプロンプトは、SPACOシステムを通じて自然言語からSuperColliderコードへの変換に使用できます。

## 1. Oval風のグリッチ・アンビエント

### プロンプト例1: 「CDスキップのようなグリッチ効果を持つ穏やかなアンビエントパッドを作成して」

```supercollider
s.waitForBoot({
  // Ovalスタイルのグリッチアンビエント
  SynthDef(\ovalPad, { |out=0, freq=220, amp=0.3, gate=1, skipRate=3, skipAmt=0.2|
    var sig, env, skip, pan;
    
    // 基本となるパッドサウンド
    sig = Array.fill(4, { 
      SinOsc.ar(
        freq * (1 + LFNoise1.kr(0.1).range(-0.02, 0.02)), 
        0, 
        LFNoise1.kr(0.3).range(0.5, 1.0)
      ) 
    }).sum;
    
    // フィルタリング
    sig = LPF.ar(sig, LFNoise2.kr(0.2).range(freq, freq*4));
    
    // CDスキップ効果
    skip = Dust.kr(skipRate);
    sig = sig * (1 - (skip * skipAmt));
    sig = sig + (skip * HPF.ar(WhiteNoise.ar(0.1), 3000) * skipAmt);
    
    // 時折発生するクリック音
    sig = sig + (Dust.ar(0.8) * 0.04);
    
    // エンベロープ
    env = EnvGen.kr(Env.asr(3, 1, 5), gate, doneAction: 2);
    
    // パンニング
    pan = LFNoise1.kr(0.1).range(-0.7, 0.7);
    
    Out.ar(out, Pan2.ar(sig * env * amp, pan));
  }).add;
  
  // 複数のパッドを異なる周波数で再生
  Routine({
    var notes = [220, 275, 330, 440, 550];
    var skipRates = [2, 3, 5, 8];
    
    notes.do({ |note, i|
      Synth(\ovalPad, [
        \freq, note, 
        \amp, 0.2, 
        \skipRate, skipRates.choose,
        \skipAmt, rrand(0.1, 0.3)
      ]);
      rrand(3.0, 8.0).wait;
    });
  }).play;
});
```

### プロンプト例2: 「微細なテクスチャーの変化と時折のグリッチを持つ浮遊感のあるドローン音響を作成して」

```supercollider
s.waitForBoot({
  // Oval風の微細テクスチャードローン
  SynthDef(\ovalDrone, { |out=0, freq=55, amp=0.3, modFreq=0.1, modAmt=0.02, noiseAmt=0.1|
    var sig, mod, noise, pan;
    
    // 基本となるドローン音
    mod = SinOsc.kr(modFreq).range(1-modAmt, 1+modAmt);
    sig = SinOsc.ar(freq * mod) * 0.3 +
          SinOsc.ar(freq * 2.01 * mod) * 0.2 +
          SinOsc.ar(freq * 4.01 * mod) * 0.1 +
          SinOsc.ar(freq * 5.97 * mod) * 0.05;
    
    // 微細なテクスチャー変化
    noise = LPF.ar(WhiteNoise.ar(noiseAmt), 
                  LFNoise2.kr(0.3).range(500, 3000));
    sig = sig + noise;
    
    // 時折のグリッチ
    sig = sig * (1 - (Dust.kr(0.7) * LFNoise0.kr(1).range(0, 0.5)));
    sig = sig + (Dust.ar(1) * LFNoise0.kr(0.5).range(0, 0.05));
    
    // フィルタリング
    sig = LPF.ar(sig, LFNoise2.kr(0.1).range(freq*2, freq*10));
    
    // パンニング
    pan = LFNoise1.kr(0.05).range(-0.6, 0.6);
    
    Out.ar(out, Pan2.ar(sig * amp, pan));
  }).add;
  
  // 複数のドローンを異なる周波数で再生
  Routine({
    var baseFreqs = [55, 55*5/4, 55*3/2, 55*2];
    
    baseFreqs.do({ |freq, i|
      Synth(\ovalDrone, [
        \freq, freq, 
        \amp, 0.15, 
        \modFreq, rrand(0.05, 0.2), 
        \modAmt, rrand(0.01, 0.03),
        \noiseAmt, rrand(0.05, 0.15)
      ]);
      2.0.wait;
    });
  }).play;
});
```

## 2. Autechre風の複雑なリズムと音響設計

### プロンプト例1: 「非対称なリズムパターンと金属的な音色を持つAutechre風のビートを作成して」

```supercollider
s.waitForBoot({
  // Autechre風の複雑なビート構造
  SynthDef(\aeBeat, { |out=0, freq=300, amp=0.3, release=0.1, pan=0, lpf=5000, resonance=0.5|
    var sig, env;
    
    // 金属的な音源
    sig = Ringz.ar(
      Impulse.ar(0), 
      freq, 
      release, 
      amp
    );
    
    // フィルタリング
    sig = RLPF.ar(sig, lpf, resonance);
    
    // エンベロープ
    env = EnvGen.kr(Env.perc(0.001, release, 1, -4), doneAction: 2);
    
    Out.ar(out, Pan2.ar(sig * env, pan));
  }).add;
  
  // 複雑なシーケンサー
  Routine({
    var patterns = [
      [1, 0, 0, 1, 0, 1, 0, 0, 1, 0, 0, 0, 1, 0, 1, 0],
      [0, 0, 1, 0, 0, 0, 1, 0, 0, 1, 0, 1, 0, 0, 0, 1],
      [1, 0, 0, 0, 1, 0, 0, 1, 0, 0, 1, 0, 0, 0, 1, 0],
      [0, 1, 0, 1, 0, 0, 1, 0, 1, 0, 0, 0, 1, 0, 0, 1]
    ];
    
    var freqs = [
      [300, 450, 600, 750],
      [320, 480, 640, 800],
      [270, 405, 540, 675],
      [350, 525, 700, 875]
    ];
    
    var releases = [0.1, 0.15, 0.05, 0.2];
    var tempos = [0.11, 0.12, 0.13, 0.14]; // 異なるレイヤーで微妙にテンポを変える
    
    // 各パターンを並行して再生
    4.do({ |i|
      Routine({
        inf.do({ |j|
          var step = j % 16;
          if(patterns[i][step] == 1, {
            Synth(\aeBeat, [
              \freq, freqs[i].choose,
              \amp, rrand(0.1, 0.3),
              \release, releases[i] * rrand(0.8, 1.2),
              \pan, rrand(-0.7, 0.7),
              \lpf, rrand(2000, 8000),
              \resonance, rrand(0.3, 0.7)
            ]);
          });
          tempos[i].wait;
        });
      }).play;
    });
  }).play;
});
```
