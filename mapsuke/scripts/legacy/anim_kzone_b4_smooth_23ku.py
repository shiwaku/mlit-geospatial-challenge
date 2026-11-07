# -*- coding: utf-8 -*-
"""23区範囲で補間アニメーション GIF を作る（anim_kzone_b4_smooth.py を利用）。
QGIS 上で exec し、run_part(0, 47) → run_part(47, 93) → finish() の順に実行。
描画はオフスクリーン（キャンバス非依存）。レイヤ構成は既定でキャンバス表示中のものを使う。
"""
import os, math
from qgis.core import QgsProject, QgsRectangle, QgsFeatureRequest, QgsVectorLayer
from qgis.utils import iface

# mapsuke/ の場所。run_all.py から渡されたもの → このファイルの位置 → 開いている QGIS プロジェクトの場所 の順に使う
BASE = globals().get("BASE") or (os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
                                 if "__file__" in globals() else QgsProject.instance().homePath())
OUT_DIR = os.path.join(BASE, "output")
GPKG = os.path.join(BASE, "data", "pt_h30_zones_b4.gpkg")
LAYER_ID = "H30________________pt_hour____f18faf5d_2889_43f7_b9e2_a86a3b75d640"
OUTLINE_ID = "H30_________977574ba_d5da_49a2_a0d2_db1c897cf418"
TITLE = "東京23区 計画基本ゾーン別 滞留人口密度（東京都市圏PT H30）"

anim = {"__name__": "anim_smooth"}
_p = os.path.join(BASE, "scripts", "legacy", "anim_kzone_b4_smooth.py")
exec(compile(open(_p, encoding="utf-8").read(), _p, "exec"), anim)
anim["configure"](log_min=3.5, log_max=5.2,
                  ticks=[(math.log10(5000), "5,000"), (math.log10(20000), "20,000"), (5, "100,000")],
                  frames_subdir=os.path.join("frames", "b4_smooth_23ku"), gif_name="b4_anim_smooth_23ku.gif")


def ku23_extent(buffer_ratio=0.04):
    sz = QgsVectorLayer(GPKG + "|layername=szone", "sz", "ogr")
    ext = QgsRectangle(); ext.setNull()
    for f in sz.getFeatures(QgsFeatureRequest().setFilterExpression('"JisCode" >= 13101 AND "JisCode" <= 13123')):
        ext.combineExtentWith(f.geometry().boundingBox())
    ext.scale(1 + buffer_ratio)
    return ext


def _layers():
    proj = QgsProject.instance()
    return proj.mapLayer(LAYER_ID), proj.mapLayer(OUTLINE_ID)


def run_part(start, end, layers=None, size=(968, 877), dpi=96.0):
    """キャンバスを使わずに範囲・サイズを固定して描画する（書き出し中に地図を動かしても影響しない）。
    layers 省略時は、呼び出し時点でキャンバスに表示中のレイヤ構成を使う。"""
    lyr, outline = _layers()
    if start == 0:
        anim["setup_smooth"](lyr)
    if layers is None:
        layers = list(iface.mapCanvas().mapSettings().layers())
    if outline is not None:
        outline.setLabelsEnabled(False)
    try:
        return anim["export_frames_offscreen"](layers, ku23_extent(), OUT_DIR, range(start, min(end, anim["N_FRAMES"])),
                                               TITLE, size, dpi)
    finally:
        if outline is not None:
            outline.setLabelsEnabled(True)


def finish():
    lyr, outline = _layers()
    if outline is not None:
        outline.setLabelsEnabled(True); outline.triggerRepaint()
    return anim["make_gif"](OUT_DIR)
