# RoleplayEngine

Capsule の上に載せたロールプレイ実行系。  
表の顔はゆっくり実況台本メーカー。核は凍結したまま。

親: https://github.com/kishimoto-void/Capsule-Prototype  
先行実測: https://github.com/kishimoto-void/Capsule-Roleplay

---

## プロトタイプ現在地（2026-09-09）

今あるものは「賢い演者」ではない。  
**基準を Capsule が持ち、穴だけを演じさせる実験場** まで来ている。

```
凍結核     frozen/          min3 / BOX / Runtime。触らない
実行系     roleplay_engine  Scene / Event / Ζ / Hash-A 監視
舞台       stage_marisa     場所の手がかり。世界事実ではない
記憶深度   γ → Δ → Δ2      場所 / 場と所持 / 関係の次
芋づる     vine.py          種一本。他の場所を混ぜない
視点       eye.py           同じ種を World / 人物 / 客で見る
門         x_guard.py       乱入・場面ジャンプ・無い記憶を止める
在庫       voice_stock.py   β から idle / craft / wall の3型
表         demo.py          文章 → 貼れる台本
```

分業は変わっていない。

```
αβ / Hash-A     絶対基準。LLM の外
γ index         場所の知識。今の住所
Δ index         その場の出来事・小道具・立場
Δ2              γ が当たったときだけ。関係から次を出す。格納しない
η               演者。完成和を書かない
人間            authorize
```

できていること

- 発言を世界事実にしない。Hash-A を動かさない
- 神社の茶を引いても、店の魔導書は混ざらない
- アリス視点でミニ八卦炉を自分の物にしない
- 霊夢は場にいなければ出ない
- スタート / 本編 / 帰結は別々の `1 + ? = 0`
- デモは `python3 demo.py` と `python3 demo.py --web`
- 散歩は観測。`/look` `/move` `/approach` `/leave` `/wait`。何もない時間も残す


まだ stub であること

- 実 LLM は差していない。`llm=` の口だけある
- 台詞は β の3型在庫。上手さは演者側
- 世界は魔理沙圏のデモ固定
- 入口はまだ複数ある。見せるなら `demo.py` を使う

測り方

```bash
python3 -m unittest discover -q
python3 demo.py
python3 play.py --repl
```

---

## デモ

```bash
python3 demo.py
python3 demo.py --web
```

ブラウザは `http://127.0.0.1:8765/` 。文章を入れて「台本にする」。  
内部の穴は画面に出さない。

```bash
python3 yukkuri.py --super --out script.txt
```

---

## 定義

```
α Core        崩さない禁則。Hash-A
β Identity    口調・価値観・癖。剛性ではない
γ Narrative   今の Scene 住所。場所の知識
Δ Change      閉じた語。場・所持・立場
Δ2            関係の次。読む面。Capsule に足さない
Ζ Tension     関係の距離。Inner に入れない
Scene         履歴全文の代わり
発言          ≠ 世界の事実
consistency   ≠ rigidity
```

閉じた語は min3 のまま: `課題 / 改善点 / 結論 / 立場 / 状態`  
新しい IS 語は足さない。

経路:

```
原文 / 発話
  → 素材（事実 / 不明）
  → γ 住所
  → Δ 場と所持
  → Δ2 次（当たったときだけ）
  → η 演技
  → Capsule が採用可否を見る
```

---

## 動かす

```bash
python3 play.py --script
python3 play.py --repl
python3 experiment.py
python3 experiment_vine.py
python3 experiment_x_guard.py
```

repl の短い口

| コマンド | 意味 |
|----------|------|
| `/status` | 見える世界 |
| `/tick` | 静かな門を通して次の現象 |
| `/guard t` | 乱入・無い記憶の判定 |
| `/vine 茶` | 種から一本 |
| `/eye Alice 茶` | 視点を変えて同じ種 |
| `/stage 神社` | 手がかりで場面を換装 |
| `/hole q` | 質問の穴を演じる |
| `/save p` `/load p` | 続き。Hash-A 不一致は拒否 |

生成器は `Callable`。既定は `voice_stock`。API キーは持たない。

| ファイル | 役割 |
|----------|------|
| `frozen/` | 核。触らない |
| `roleplay_engine.py` | 実行系 |
| `stage_marisa.py` | 魔理沙圏の舞台 |
| `index_stage.py` | γ=舞台、Δ=キャラと小道具 |
| `depth_index.py` | 記憶深度 |
| `vine.py` | 芋づる |
| `eye.py` | 視点 |
| `x_guard.py` | X 側不満の門 |
| `voice_stock.py` | 3型在庫 |
| `yukkuri_*.py` | 台本メーカー |
| `rack.py` | 記憶の棚。Capsule 増設ではない |

---

## 舞台装置

魔理沙の訪れる場所は `stage_marisa.py`。本体とは分ける。  
`prepare` は住所を換装するだけ。紅魔館の場面を用意しても、行ったことにはならない。

---

## 言わないこと

口調維持の一般解、α の法律化、実 API 接続、核の更新。  
Capsule を賢くしない。人格を生成しない。安全機構を主役にしない。
