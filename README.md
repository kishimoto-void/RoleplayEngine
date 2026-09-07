# RoleplayEngine

Capsule の上に載せたロールプレイ専用の実行系。

```
Capsule-Prototype   核。凍結。触らない
Capsule-Roleplay    最初の実測スナップショット
RoleplayEngine      本リポジトリ。実行系の名前
```

親: https://github.com/kishimoto-void/Capsule-Prototype  
先行実測: https://github.com/kishimoto-void/Capsule-Roleplay

Capsule を賢くしない。人格を生成しない。安全機構を主役にしない。  
LLM は物語の支配者ではなく、次の現象を提案する演算器である。

---

## 定義

```
α Core        崩さない禁則。Hash-A
β Identity    口調・価値観・癖。剛性ではない
γ Narrative   今の Scene 住所
Δ Change      閉じた語の更新。Hash-B
Ζ Tension     関係の距離。Inner に入れない
Scene         履歴全文の代わり
発言          ≠ 世界の事実
consistency   ≠ rigidity
```

経路:

```
World → BOX → Character Capsule → generator → Proposed Event → 発話 / Δ
```

閉じた語は min3 のまま: `課題 / 改善点 / 結論 / 立場 / 状態`  
信頼そのものは Ζ に置く。新しい IS 語は足さない。

---

## 動かす

```bash
python3 -m unittest test_roleplay_engine.py
python3 experiment.py
python3 play.py
python3 play.py --script
```

| ファイル | 役割 |
|----------|------|
| `roleplay_engine.py` | Character / World / Scene / Event / Ζ |
| `play.py` | 短い実行口。生成器は stub |
| `test_roleplay_engine.py` | 核不変・発言≠事実・イベント・三層記憶 |
| `experiment.py` | 仕様 8 項の実走 |
| `frozen/` | min3 / BOX / Runtime の引用。触らない |

生成器は `Callable`。既定 stub。API キーは持たない。

---

## 需要面（2026-09-08）

Grok 側のロールプレイで欠けやすいところだけ足した。核は増やしていない。

| 需要 | 口 | やること / やらないこと |
|------|----|--------------------------|
| 続きから再開 | `save` / `load` | Ζ・事件・Scene を戻す。Hash-A 不一致は拒否。修復しない |
| 状態が見える | `status` | 関係と事実だけ。制御プロンプトは出さない |
| 場が動く | `tick` | ユーザーが黙っても Capsule が次の現象を出す |
| 同じ台詞の反復 | 直前発話との照合 | 同じ刺激でも次の候補へずらす |
| 声が混ざる | `VOICE` | Alice と Marisa で在庫を分けた |
| 場面転換 | `enter` | `exits` に無い住所は広げない |

場面は JSON で用意できる。`scenes/` が帳。

```bash
python3 experiment_scenes.py
python3 play.py --repl
# /scenes
# /prepare alice-house
# /go scarlet-mansion   # no_route
```

`prepare` は住所を換装するだけ。紅魔館の場面を用意しても、行ったことにはならない。


```bash
python3 -m unittest test_roleplay_engine.py test_demand.py
python3 experiment_demand.py
python3 play.py --script
python3 play.py --repl
```

---

## 実測（2026-09-08）

```
python3 -m unittest test_roleplay_engine.py   # 10/10 OK
python3 experiment.py                         # 8/8 OK
python3 play.py --script
```

| 項 | 結果 |
|----|------|
| 剛性ではない | β「強気」のまま恐怖で `黙る`。Hash-A 不変 |
| Scene | 履歴なし。`start + ? = goal` |
| ? | 助けを求められ `強がる` |
| 事実分離 | 印なしでは残らない。authorize で World `結論` |
| イベント | trust 0.42→0.51 / tension 0.71→0.59 |
| 記憶 | 寒さは落ちる。裏切りは persistent |
| 自律 | ツンデレ指定なしで壁の台詞 |
| 物理法則 | Alice / Marisa / World の Hash-A は動かない |

言わないこと: 口調維持の一般解、α の法律化、実 API 接続、核の更新。


