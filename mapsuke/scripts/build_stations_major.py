# -*- coding: utf-8 -*-
"""主要駅レイヤ stations_major を作る（駅名の日英併記ラベル用）。

入力:
  data/raw/stations/S12-23/UTF-8/S12-23_NumberOfPassengers.geojson  … 国土数値情報 S12（駅別乗降客数, 2011–2022）
  data/raw/stations/osm_stations_tokyo.json                         … OSM 駅ノード（Overpass, name:en 用）
  data/pt_h30_zones_b4.gpkg | study_area                             … 調査対象範囲（anim_kzone_b4_ptinfo.ensure_boundaries で作成）
出力:
  data/pt_h30_zones_b4.gpkg | stations_major（上位 TOP_N 駅, EPSG:6677）
    gid=S12駅グループコード, name_ja, name_en, riders2018=2018年乗降客数（グループ内合計）, rank
処理:
  - S12 の年次は4列1組（重複フラグ, データ有無, 備考, 乗降客数）で 2011→2022。2018年 = S12_037
  - 駅グループコード S12_001g ごとに 2018年値を合計（重複行は0）、位置は各路線線分の重心の平均
  - 調査対象範囲内のみ。英語名は OSM の同名駅（ヶ/ケ等を正規化）で 1.5 km 以内の最近傍の name:en、長音記号を除去
"""
import os, json, math, re, unicodedata
from collections import defaultdict
from qgis.core import (QgsVectorLayer, QgsFeature, QgsField, QgsGeometry, QgsPointXY, QgsCoordinateTransform,
                       QgsCoordinateReferenceSystem, QgsProject, QgsVectorFileWriter)
from qgis.PyQt.QtCore import QMetaType

# mapsuke/ の場所。run_all.py から渡されたもの → このファイルの位置 → 開いている QGIS プロジェクトの場所 の順に使う
BASE = globals().get("BASE") or (os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
                                 if "__file__" in globals() else QgsProject.instance().homePath())
S12 = os.path.join(BASE, r"data\raw\stations\S12-23\UTF-8\S12-23_NumberOfPassengers.geojson")
OSM = os.path.join(BASE, r"data\raw\stations\osm_stations_tokyo.json")
GPKG = os.path.join(BASE, r"data\pt_h30_zones_b4.gpkg")
YEAR_FIELD = "S12_037"   # 2018
TOP_N = 150


def _norm(s):
    return re.sub(r"(駅|\(.*?\)|（.*?）|\s)", "", (s or "").replace("ヶ", "ケ").replace("ヵ", "カ"))


def _plain(s):
    return "".join(c for c in unicodedata.normalize("NFKD", s) if not unicodedata.combining(c)) if s else s


def build(top_n=TOP_N, layer_name="stations_major"):
    s12 = QgsVectorLayer(S12, "s12", "ogr")
    crs = QgsCoordinateReferenceSystem("EPSG:6677"); ctx = QgsProject.instance().transformContext()
    tr = QgsCoordinateTransform(s12.crs(), crs, ctx)
    study = QgsVectorLayer(GPKG + "|layername=study_area", "st", "ogr")
    sg = next(study.getFeatures()).geometry(); sbb = sg.boundingBox()
    groups = defaultdict(lambda: {"riders": 0, "names": defaultdict(int), "pts": []})
    for f in s12.getFeatures():
        g = QgsGeometry(f.geometry()); g.transform(tr)
        c = g.centroid().asPoint()
        if not sbb.contains(c):
            continue
        gr = groups[f["S12_001g"]]
        gr["riders"] += int(f[YEAR_FIELD] or 0); gr["names"][f["S12_001"]] += 1; gr["pts"].append(c)
    rows = []
    for gid, gr in groups.items():
        x = sum(p.x() for p in gr["pts"]) / len(gr["pts"]); y = sum(p.y() for p in gr["pts"]) / len(gr["pts"])
        if not sg.contains(QgsGeometry.fromPointXY(QgsPointXY(x, y))):
            continue
        name = max(gr["names"].items(), key=lambda kv: kv[1])[0]
        rows.append({"gid": gid, "name_ja": name, "riders2018": gr["riders"], "x": x, "y": y})
    rows.sort(key=lambda r: (-r["riders2018"], r["gid"]))
    rows = rows[:top_n]
    tro = QgsCoordinateTransform(QgsCoordinateReferenceSystem("EPSG:4326"), crs, ctx)
    onodes = []
    for e in json.load(open(OSM, encoding="utf-8"))["elements"]:
        t = e.get("tags", {})
        if t.get("name:en"):
            p = tro.transform(QgsPointXY(e["lon"], e["lat"])); onodes.append((_norm(t.get("name")), t["name:en"], p.x(), p.y()))
    for r in rows:
        best = None
        for nm, en, x, y in onodes:
            d = math.hypot(x - r["x"], y - r["y"])
            if d < 1500 and nm == _norm(r["name_ja"]) and (best is None or d < best[0]):
                best = (d, en)
        r["name_en"] = _plain(best[1]) if best else None
    mem = QgsVectorLayer("Point?crs=EPSG:6677", layer_name, "memory")
    mem.dataProvider().addAttributes([QgsField("gid", QMetaType.Type.QString), QgsField("name_ja", QMetaType.Type.QString),
                                      QgsField("name_en", QMetaType.Type.QString), QgsField("riders2018", QMetaType.Type.LongLong),
                                      QgsField("rank", QMetaType.Type.Int)])
    mem.updateFields()
    feats = []
    for i, r in enumerate(rows):
        ft = QgsFeature(mem.fields()); ft.setGeometry(QgsGeometry.fromPointXY(QgsPointXY(r["x"], r["y"])))
        ft.setAttributes([r["gid"], r["name_ja"], r["name_en"], r["riders2018"], i + 1]); feats.append(ft)
    mem.dataProvider().addFeatures(feats)
    opt = QgsVectorFileWriter.SaveVectorOptions(); opt.driverName = "GPKG"; opt.layerName = layer_name
    opt.actionOnExistingFile = QgsVectorFileWriter.ActionOnExistingFile.CreateOrOverwriteLayer
    err = QgsVectorFileWriter.writeAsVectorFormatV3(mem, GPKG, ctx, opt)
    return err, rows
