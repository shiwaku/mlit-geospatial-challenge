# -*- coding: utf-8 -*-
"""pt_h30_purpose.gpkg の2レイヤに色分けスタイルを付け、gpkg 内に保存する（issue #5）。

kzone_purpose   : 既定 = 私事系の比率 shiji_share。別名スタイル = 業務系の比率、私事系の密度
mesh500_purpose : 既定 = 自ゾーン外に住む人の比率 outside_share
QGIS で gpkg を追加すると既定スタイルで表示される。別名スタイルはレイヤ右クリック →「スタイル」で切り替え。

実行（QGIS の外から）:
  "C:\\Program Files\\QGIS 4.0.0\\bin\\python-qgis.bat" scripts\\style_purpose_h30.py
QGIS の Python コンソールから exec してもよい。
"""
import os, sys
from qgis.core import (QgsApplication, QgsVectorLayer, QgsGraduatedSymbolRenderer, QgsRendererRange,
                       QgsFillSymbol, QgsStyle)

BASE = globals().get("BASE") or os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
GPKG = os.path.join(BASE, "data", "pt_h30_purpose.gpkg")

# (列, 区切り, 凡例の書式, ランプ名, スタイル名, 説明)
KZONE_STYLES = [
    ("shiji_share", [0, 0.30, 0.40, 0.45, 0.50, 0.55, 0.60, 1.0], "{:.0%}–{:.0%}", "Viridis",
     "私事系の比率", "帰宅を除く到着に占める私事系（自宅－私事＋私事）の割合"),
    ("work_share", [0, 0.15, 0.20, 0.25, 0.30, 0.40, 0.55, 1.0], "{:.0%}–{:.0%}", "Viridis",
     "業務系の比率", "帰宅を除く到着に占める業務系（自宅－勤務＋自宅－業務＋勤務・業務）の割合"),
    ("shiji_all_dens", [0, 300, 1000, 3000, 6000, 10000, 20000, 1e7], "{:,.0f}–{:,.0f}", "Magma",
     "私事系の密度", "私事系の集中量（トリップ/km²、終日）"),
]
MESH_STYLES = [
    ("outside_share", [0, 0.1, 0.2, 0.3, 0.5, 0.7, 1.0001], "{:.0%}–{:.0%}", "Viridis",
     "自ゾーン外居住者の比率", "全目的の集中量のうち、そのメッシュの計画基本ゾーンの外に住む人の割合（勤務者を含む）"),
]


def renderer(field, breaks, fmt, ramp_name):
    ramp = QgsStyle.defaultStyle().colorRamp(ramp_name)
    n = len(breaks) - 1
    ranges = []
    for i in range(n):
        lo, hi = breaks[i], breaks[i + 1]
        sym = QgsFillSymbol.createSimple({"color": ramp.color(i / max(n - 1, 1)).name(),
                                          "outline_style": "no"})
        label = fmt.format(lo, min(hi, 1.0) if "%" in fmt else hi)
        if i == n - 1:
            label = (fmt.split("–")[0].format(lo)) + " 以上"
        ranges.append(QgsRendererRange(lo, hi, sym, label))
    r = QgsGraduatedSymbolRenderer(field, ranges)
    return r


def save_styles(layer_name, styles):
    lyr = QgsVectorLayer(f"{GPKG}|layername={layer_name}", layer_name, "ogr")
    if not lyr.isValid():
        raise RuntimeError(f"レイヤを開けません: {layer_name}")
    msgs = []
    for k, (field, breaks, fmt, ramp, name, desc) in enumerate(styles):
        lyr.setRenderer(renderer(field, breaks, fmt, ramp))
        lyr.setOpacity(0.85)
        res = lyr.saveStyleToDatabase(name, desc, k == 0, "")
        msgs.append((name, res))
    return msgs


def main():
    out = save_styles("kzone_purpose", KZONE_STYLES) + save_styles("mesh500_purpose", MESH_STYLES)
    for name, res in out:
        print(name, "->", res if res else "ok")


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")
    app = QgsApplication([], False)
    app.initQgis()
    try:
        main()
    finally:
        app.exitQgis()
