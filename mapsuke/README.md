# 東京都市圏PT（H30）時刻別滞留人口の可視化 — 再現手順

第3回 国交省 地理空間情報データチャレンジ（にぎわい予測）の検討用に、東京都市圏パーソントリップ調査（H30）の
基礎集計 b-4「ゾーン別時刻別滞留人口」を計画基本ゾーンに結合し、時刻別アニメーション（GIF）を作成したもの。

作成: 2026-11-02〜03（QGIS + Mapsuke）

## フォルダ構成

```
mapsuke/
├─ tokyo_pt_h30_zone.qgz        QGIS プロジェクト（レイヤ・スタイル・時系列コントローラ設定込み）
├─ README.md                    本書
├─ environment.json             動作確認環境
├─ styles/                      レイヤ定義・スタイル（.qlr / .qml）
│   ├─ gsi_vectortile_basemap.*   地理院ベクトルタイル背景（プロジェクトで使っているスタイル）
│   └─ kzone_b4_14classes.*       滞留人口 14段階スタイル
├─ scripts/                     処理スクリプト（QGIS 上で exec して実行）
│   └─ legacy/                    途中の版（参考として保存）
├─ data/                        ※ Git 管理外
│   ├─ raw/                       入力データ（取得したまま）
│   ├─ pt_h30_zones_b4.gpkg       加工データ（プロジェクトが参照）
│   └─ pt_h30_b4_tidy.csv         b-4 整形表（UTF-8、集計行含む）
└─ output/                      成果物 ※ Git 管理外（run_all.py で再生成）
    ├─ *.gif                      アニメーション
    ├─ frames/<名前>/             GIF のコマ PNG
    ├─ glow_samples/              グロー表現の見本
    └─ b4_compare_h03_h14.png
```

`data/` と `output/` は Git に含めない。クローンした場合は下記「入力データ」を各自取得して `data/raw/` に置き、
「再現手順」の 3 でデータから作り直す。

## 入力データ（data/raw）

| データ | ファイル | 入手元 | 備考 |
|---|---|---|---|
| H30 計画基本ゾーン・小ゾーン | `H30_gis/H30_kzone.shp`, `H30_szone.shp` | https://www.tokyo-pt.jp/static/hp/file/data/H30_gis.zip | EPSG:6677、属性 cp932 |
| b-4 ゾーン別時刻別滞留人口 | `b-4.csv` | e-Stat（利用者が取得） | cp932。計画基本ゾーン単位、時間帯27列 |
| H30 基礎集計一式 | `H30_data/*.xlsx`（b-4.xlsx ほか） | 東京都市圏交通計画協議会 https://www.tokyo-pt.jp/data/01download （利用者アンケート回答後にDL） | b-4.xlsx は b-4.csv と全655行×27列一致を確認済み |
| 記者発表資料 | `tokyo_pt_h30_1127press.pdf` | https://www.tokyo-pt.jp/static/hp/file/press/1127press.pdf | 参考 |
| 駅別乗降客数 | `stations/S12-23_GML.zip`, `stations/S12-23/` | 国土数値情報 S12 https://nlftp.mlit.go.jp/ksj/gml/data/S12/S12-23/S12-23_GML.zip （2026-11-03 取得） | 2018年値 = S12_037 |
| 駅の英語名 | `stations/osm_stations_tokyo.json` | OpenStreetMap（Overpass API, 2026-11-03 取得）© OpenStreetMap contributors, ODbL | クエリは下記 |
| その他（H10/H20/S63 等） | `H10_data/` ほか | 協議会 | 今回の処理では未使用 |

Overpass クエリ（POST `data=`、https://overpass-api.de/api/interpreter）:
```
[out:json][timeout:180];(node["railway"="station"](34.85,138.90,36.30,140.95);node["public_transport"="station"]["train"="yes"](34.85,138.90,36.30,140.95););out body;
```

背景地図（オンライン、実行時に取得）:
- 地理院ベクトルタイル（試験公開）`https://cyberjapandata.gsi.go.jp/xyz/experimental_bvmap/{z}/{x}/{y}.pbf` — スタイルは `styles/gsi_vectortile_basemap.qlr`
- 地理院地図 淡色（初期表示用、現在は非表示）

配色の参考: 東京PTインフォグラフ「地域構造」時刻別滞留人口ヒートマップ（https://www.tokyo-pt.jp/info_provision/area）の凡例色を画像から抽出（#92c7ff, #fff983, #ffcd83, #ff9783, #da83b5）。

## 加工データ（data/pt_h30_zones_b4.gpkg）

| レイヤ | 内容 | 作成スクリプト |
|---|---|---|
| `kzone_b4` | 計画基本ゾーン615件＋時刻別滞留人口 `p03_pre`, `p03`〜`p26`, `p27_post`, `p_unknown`、`area_km2`, `dens_p14`, `day_night`, `peak_col` など | `join_b4_kzone.py` |
| `szone` | 小ゾーン1,660件＋親の計画基本ゾーン `kzone`（空間包含で判定） | `join_b4_kzone.py` |
| `pref` / `study_area` | 都県境界・調査対象範囲（小ゾーンを修復→融合→5km²未満の孔を除去） | `anim_kzone_b4_ptinfo.py` の `ensure_boundaries()` |
| `stations_major` | 主要駅150駅（S12 2018年乗降客数を駅グループ単位に合計、英語名は OSM name:en） | `build_stations_major.py` |

### 目的別集中量（data/pt_h30_purpose.gpkg、issue #5）

| レイヤ | 内容 |
|---|---|
| `kzone_purpose` | 計画基本ゾーン615件 × 目的別集中量（終日、c-2）。私事系 `shiji_all` = 自宅－私事＋私事、業務系 `work_all`、比率 `shiji_share`・`work_share`（帰宅を除く到着に占める割合）、私事系の到着時刻別 `shiji_a03_pre`〜`shiji_a27_post`、密度 `*_dens`、相対誤差の目安 `rse_*` |
| `mesh500_purpose` | 2分の1地域メッシュ（約500m）15,026件 × 目的別集中量（mesh-1）＋居住地による来訪者指標（mesh-3）：自ゾーン外に住む人の集中量 `att_outside`・比率 `outside_share`、居住地の多様性 `res_entropy`、居住地からの平均距離 `res_mean_km` |

作成: `python -I scripts/build_purpose_h30.py`（QGIS 不要）。c-2 の縦持ち表を `data/pt_h30_c2_tidy.csv` に出す。

- 集中量は「着いたトリップ数」で、滞留（その時刻にいる人数）ではない。目的別の滞留人口と滞在時間は公開集計表に無い（表7-1 は駐車の時間分布）。
- 平日のみ。相対誤差の目安 `rse = 21.5 / sqrt(トリップ数)`（手引きの「21,000トリップで約15%、5,000で約30%」から逆算）。
  私事系で 30% 以内に収まるのは、計画基本ゾーンで 557/614、500m メッシュで 462/11,776。**私事系の分析は計画基本ゾーン単位を基本にし、メッシュは上位メッシュか比率・順位で読む。**
- mesh-1 は mesh-3 より 1,720 メッシュ少ない（合計 689 トリップ未満が載っていないとみられる）。そのメッシュの目的別の値は欠損。
- `outside_share` は全目的（帰宅を含む）で、勤務者は除けていない。
- 検算: ゾーン合計 71,534,753 ＋ その他・不明 ≒ c-2 の圏域内合計 72,597,676。

検算: 14時台でゾーン合計＋「その他・不明」= 圏域内合計（33,786,972人）を確認。

### P1 勤務者除外でにぎわいの地図はどれだけ変わるか（data/p1_h30.gpkg・output/p1/、issue #10）

作成: `python -I scripts/analyze_p1_h30.py`（QGIS 不要、約20秒）。先に `build_purpose_h30.py` を実行しておく。

- 比べる地図（集中量、帰宅を除く）: A 全目的 / B 通勤・業務を除く / C 私事のみ。計画基本ゾーンは密度、500m メッシュはトリップ数。
- 指標: Spearman 順位相関、上位30・60の重なり、LISA（局所モラン I、クイーン隣接、999回並べ替え、p<0.05）の HH の入れ替わり、A→C の順位変化と属性の順位相関。
- レイヤ: `kzone_p1`（`A`〜`C`・`T` の密度、`*_pct`、`lisa_*`、順位差 `d_CA`、市区町村 `city`、駅乗降客数 `riders2018` など）、`mesh500_p1`。
- 表: `p1_compare.csv`（比較の要約）、`p1_mesh_top30.csv`、`p1_rankchange_attrs.csv`、`p1_kzone_{fall,rise,hh_lost,hh_new}.csv`。図: `p1_*.png`。

### P3 来訪者の量を駅・人口で説明し残差を地図化（data/p3_h30.gpkg・output/p3/、issue #11）

作成: `python -I scripts/analyze_p3_h30.py`（QGIS 不要）。先に `build_purpose_h30.py` と `analyze_p1_h30.py` を実行しておく。

追加の入力（e-Stat 地図で見る統計 統計データダウンロード、2分の1地域メッシュ、1次メッシュ 5238〜5240・5338〜5340・5438〜5440 の9区画）
- `data/raw/estat_pop500_2020/tblT001141H*.txt`: 2020年国勢調査 人口及び世帯（統計表ID T001141）
  `https://www.e-stat.go.jp/gis/statmap-search/data?statsId=T001141&code=<1次メッシュ>&downloadType=2`
- `data/raw/estat_econ500_2016/tblT000918H*.txt`: 2016年経済センサス活動調査 産業大分類別 事業所数・従業者数（T000918）。
  列 001〜018 が事業所数、019〜036 が従業者数（同じ産業順）。URL は上の statsId を差し替える。

- 私事系集中量を、ポアソン回帰（対数リンク）で「駅＋人口」とそれに従業者数を足したモデルで当て、逸脱度の説明率 D² と空間ブロック CV（2次メッシュ単位5分割）で比べる。
- 駅は乗降客数を距離でガウス減衰（σ=400m）させた合計 `riders_in` と 1km 以内の合計 `riders_1km`。周辺人口 `pop_nbr` は 5×5 メッシュの合計。
- 残差 `resid` = log((実測+1)/(予測+1))。読むのは実測か予測が 5,136 トリップ以上（`reliable`）のメッシュ。
- 鈴木（2014）の到着数原単位 `unit_visit` = 私事系集中量 ÷（小売・飲食・生活関連の従業者数、100人以上）。
- 表: `p3_models.csv`、`p3_coefs.csv`、`p3_resid_candidates.csv`、`p3_resid_{pos,neg}.csv`、`p3_unit_{top,low}.csv`。図: `p3_resid_map.png`、`p3_pred_obs.png`。

### P4 私事来訪の量 × 消費額で類型化（data/p4_h30.gpkg・output/p4/、issue #12）

作成: `python -I scripts/analyze_p4_h30.py`（QGIS 不要）。先に `analyze_p1_h30.py` を実行しておく。

- 入力: 表4-4（目的別消費額別発生集中量）と表4-2（目的別発生集中量の発着施設構成）。私事系 = 自宅－私事＋その他私事。私事系の合計は 4-4・4-2・c-2 で一致する。
- 高消費率 `high_spend` = 1,001円以上の割合（不明4%を除く）。平均消費額 `mean_spend` は区分の代表値（0/500/3,000/7,500/15,000円）による概算。
- 4象限 `quad` = 私事系の密度 × 高消費率をそれぞれ中央値で分ける（中央値は私事系 5,136 トリップ以上の 557 ゾーンで決める）。
- **ゾーン単位の高消費率は標本誤差が大きい**（標準誤差の中央値 0.063 に対し、ゾーン間の四分位範囲は 0.085）。消費側の分類が 95% で確かなのは 557 ゾーン中 37 だけ（`spend_side_sure`）。個々のゾーンの象限ではなく、施設構成との相関など全体の傾向で読む。
- 表: `p4_check.csv`、`p4_volume_vs_spend.csv`、`p4_facility_corr.csv`、`p4_quadrants.csv`、`p4_{hh,hl,lh}_top.csv`、`p4_spend_top.csv`。図: `p4_quadrants.png`。

## スクリプト（scripts/）

| ファイル | 役割 |
|---|---|
| `run_all.py` | **一括実行**（データ作成→GIF 6本） |
| `join_b4_kzone.py` | b-4 を計画基本ゾーンに結合（GPKG を作り直す） |
| `build_stations_major.py` | 主要駅レイヤ作成 |
| `build_purpose_h30.py` | 目的別集中量を計画基本ゾーンと 500m メッシュに結合（geopandas、QGIS 不要） |
| `analyze_p1_h30.py` | P1: 全目的・通勤業務除く・私事のみの地図を順位相関と LISA で比較（geopandas、QGIS 不要） |
| `analyze_p3_h30.py` | P3: 私事系集中量を駅・人口・従業者数でポアソン回帰し残差を地図化（geopandas、QGIS 不要） |
| `analyze_p4_h30.py` | P4: 私事来訪の量と消費額で計画基本ゾーンを4象限に分け、着施設構成で特徴づける（geopandas、QGIS 不要） |
| `anim_kzone_b4_ptinfo.py` | **主系**: 公式準拠配色・14段階、背景の上下分割、主要駅ラベル、オフスクリーン描画、固定パレット GIF |
| `glow_samples.py` | 夜景風（inferno＋グロー）＋鉄道線＋主要駅、見本と `export_night()` |
| `legacy/anim_kzone_b4.py`, `legacy/anim_kzone_b4_smooth.py`, `legacy/anim_kzone_b4_smooth_23ku.py`, `legacy/style_kzone_b4.py` | 途中の版（キャンバス書き出し・補間・対数配色）。参考として保存 |

## 再現手順

1. QGIS 4.0 で `tokyo_pt_h30_zone.qgz` を開く（背景の地理院ベクトルタイルはネット接続が必要）。
2. Python コンソールで:
   ```python
   exec(open(r"<このフォルダ>\scripts\run_all.py", encoding="utf-8").read())
   main()                    # GIF 6本を再生成（約3分）
   ```
3. データから作り直す場合は、GPKG を参照しているレイヤをプロジェクトから外すか QGIS を新規プロジェクトにしてから
   `rebuild_data()` を実行し、その後プロジェクトを開き直して `main()`。
   新規プロジェクトで実行するときは、exec の前に `BASE = r"<このフォルダ>"` を定義しておく。
   （`join_b4_kzone.py` は GPKG を削除して作り直すため、開いているとファイルロックで失敗する）

## 成果物（output/）

| GIF | 内容 |
|---|---|
| `b4_anim_ptinfo_region.gif` / `_23ku.gif` | 公式準拠配色・14段階、1時間刻み26コマ（〜3時, 3〜26時台, 27時〜） |
| `b4_anim_ptinfo_region_st.gif` / `_23ku_st.gif` | 同＋主要駅（都市圏30駅／23区60駅、日英併記） |
| `b4_anim_night_region_st.gif` / `_23ku_st.gif` | 夜景風（inferno＋グロー）＋鉄道線＋主要駅 |
| `b4_anim.gif`, `b4_anim_smooth.gif`, `b4_anim_smooth_23ku.gif` | 途中の版（8段階・補間・対数配色） |

14段階の区分（人/km²）: 0 / 500 / 1,000 / 2,000 / 3,000 / 4,000 / 5,000 / 7,500 / 10,000 / 12,500 / 15,000 / 20,000 / 30,000 / 50,000以上。
公式インフォグラフ（5段階）より細分化している点に注意。

## 注意・限界

- b-4 は全目的・全員（居住者・勤務者を含む）の滞留人口。コンペの「来訪者」に近づけるには c-2 等で私事目的に絞る必要がある。
- 公式インフォグラフは地点別滞留人口のヒートマップ。本成果は計画基本ゾーン単位の塗り分けによる近似。
- S12 の乗降客数は事業者別の合計のため、乗り入れの多い駅（綾瀬・押上など）が大きめに出る。
- 背景は地理院のオンラインタイル（試験公開）を使うため、将来のスタイル・データ更新で見た目が変わる可能性がある。
- スクリプトは `tokyo_pt_h30_zone.qgz` 内のレイヤを ID で参照している。フォルダの場所は自動で決まる（`run_all.py` から渡された `BASE` → スクリプトの位置 → 開いているプロジェクトの場所の順）。
