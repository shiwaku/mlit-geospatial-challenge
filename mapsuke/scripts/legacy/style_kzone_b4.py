# -*- coding: utf-8 -*-
"""kzone_b4 レイヤに「時間帯切替式」の滞留人口密度スタイルを設定する。
プロジェクト変数 @pt_hour（3〜26）で表示する時間帯を切り替える。区分は全時間帯共通の固定値。
"""
from qgis.core import (QgsProject, QgsGraduatedSymbolRenderer, QgsRendererRange, QgsFillSymbol,
                       QgsExpressionContextUtils, QgsStyle)

BREAKS = [0, 500, 2000, 4000, 7000, 10000, 15000, 30000, 200000]   # 人/km²
EXPR = "attribute(concat('p', lpad(to_string(@pt_hour), 2, '0'))) / \"area_km2\""


def apply(layer, hour=14, project=None):
    project = project or QgsProject.instance()
    ramp = QgsStyle.defaultStyle().colorRamp("YlOrRd")
    n = len(BREAKS) - 1
    ranges = []
    for i in range(n):
        c = ramp.color(i / (n - 1))
        sym = QgsFillSymbol.createSimple({"color": c.name(), "outline_color": "#606060", "outline_width": "0.1"})
        lab = f"{BREAKS[i]:,} – {BREAKS[i+1]:,}" if i < n - 1 else f"{BREAKS[i]:,} 以上"
        ranges.append(QgsRendererRange(BREAKS[i], BREAKS[i + 1], sym, lab + " 人/km²"))
    layer.setRenderer(QgsGraduatedSymbolRenderer(EXPR, ranges))
    QgsExpressionContextUtils.setProjectVariable(project, "pt_hour", hour)
    layer.triggerRepaint()
