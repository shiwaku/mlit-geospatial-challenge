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

検算: 14時台でゾーン合計＋「その他・不明」= 圏域内合計（33,786,972人）を確認。

## スクリプト（scripts/）

| ファイル | 役割 |
|---|---|
| `run_all.py` | **一括実行**（データ作成→GIF 6本） |
| `join_b4_kzone.py` | b-4 を計画基本ゾーンに結合（GPKG を作り直す） |
| `build_stations_major.py` | 主要駅レイヤ作成 |
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
