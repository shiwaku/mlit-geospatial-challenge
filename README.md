# 第3回 国交省 地理空間情報データチャレンジ 検討リポジトリ

第3回 国土交通省 地理空間情報データチャレンジ（テーマ: 都市のにぎわい予測、SIGNATE）に向けた調査・試作をまとめる。

## 構成

```
.
├─ README.md                 本書
├─ .gitignore                データ・生成物は除外（下記）
├─ docs/
│   ├─ geo_data_challenge3_discussion.md   コンペ概要・論点・特徴量案の検討メモ
│   ├─ literature_review.md                 東京PTで「にぎわい」仮説を絞り込むための先行研究レビュー
│   └─ literature_notes/                    レビューの元になった観点別の調査メモ（5本）
└─ mapsuke/                  東京都市圏PT（H30）時刻別滞留人口の可視化（QGIS + Mapsuke）
    ├─ README.md             データ入手元・再現手順
    ├─ tokyo_pt_h30_zone.qgz
    ├─ environment.json
    ├─ scripts/              処理スクリプト（legacy/ は途中の版）
    ├─ styles/               レイヤ定義・スタイル
    ├─ data/                 入力（raw/）と加工データ   ※ Git 管理外
    └─ output/               GIF・コマ画像・見本       ※ Git 管理外
```

## Git に含めないもの

- `mapsuke/data/`: PT 基礎集計（協議会配布）、PT ゾーン shp、e-Stat の b-4、国土数値情報 S12、OSM 抽出など。
  再配布の条件を確認していないため、入手元だけを `mapsuke/README.md` に記す。各自取得して `data/raw/` に置く。
- `mapsuke/output/`: `scripts/run_all.py` で再生成できる。
