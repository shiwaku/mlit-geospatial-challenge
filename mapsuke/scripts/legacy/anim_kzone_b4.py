# -*- coding: utf-8 -*-
"""kzone_b4 の時刻別滞留人口密度を QGIS 時系列コントローラ（ムービーモード）でアニメーションし、GIF を書き出す。

- 描画式: 時間帯 = coalesce(@frame_number, @pt_hour - 3) + 3  （frame 0 = 3時台 … frame 23 = 26時台）
- レイヤの時系列モードは「レイヤの再描画のみ」（コマ変更で再描画させるため）
- GIF: キャンバスを1コマずつ保存し、時間帯ラベルと凡例を描き込んで Pillow で結合
QGIS 上で exec して setup_movie(layer) / export_gif(layer, out_dir) を呼ぶ。
"""
import os
from qgis.core import (Qgis, QgsApplication, QgsGraduatedSymbolRenderer, QgsRendererRange, QgsFillSymbol,
                       QgsStyle)
from qgis.PyQt.QtCore import QElapsedTimer, Qt, QRectF
from qgis.PyQt.QtGui import QImage, QPainter, QColor, QFont, QPen
from qgis.utils import iface

BREAKS = [0, 500, 2000, 4000, 7000, 10000, 15000, 30000, 200000]   # 人/km²
HOUR_EXPR = "(coalesce(@frame_number, @pt_hour - 3) + 3)"
EXPR = "attribute(concat('p', lpad(to_string(" + HOUR_EXPR + "), 2, '0'))) / \"area_km2\""
FIRST_HOUR, N_FRAMES = 3, 24


def hour_label(h):
    return f"{h}時台" + (f"（翌{h - 24}時台）" if h >= 24 else "")


def _ranges():
    ramp = QgsStyle.defaultStyle().colorRamp("YlOrRd")
    n = len(BREAKS) - 1
    out = []
    for i in range(n):
        c = ramp.color(i / (n - 1))
        sym = QgsFillSymbol.createSimple({"color": c.name(), "outline_color": "#606060", "outline_width": "0.1"})
        lab = f"{BREAKS[i]:,} – {BREAKS[i+1]:,}" if i < n - 1 else f"{BREAKS[i]:,} 以上"
        out.append((QgsRendererRange(BREAKS[i], BREAKS[i + 1], sym, lab + " 人/km²"), c, lab))
    return out


def setup_movie(layer, fps=2, loop=True):
    layer.setRenderer(QgsGraduatedSymbolRenderer(EXPR, [r for r, _, _ in _ranges()]))
    tp = layer.temporalProperties()
    tp.setMode(Qgis.VectorTemporalMode.RedrawLayerOnly)
    tp.setIsActive(True)
    nav = iface.mapCanvas().temporalController()
    nav.setNavigationMode(Qgis.TemporalNavigationMode.Movie)
    nav.setTotalMovieFrames(N_FRAMES)
    nav.setFramesPerSecond(fps)
    nav.setLooping(loop)
    nav.setCurrentFrameNumber(0)
    layer.triggerRepaint()
    return nav


def _render_canvas(canvas, timeout_ms=60000):
    canvas.refresh()
    t = QElapsedTimer(); t.start()
    while not canvas.isDrawing() and t.elapsed() < 2000:      # 遅延リフレッシュの開始を待つ
        QgsApplication.processEvents()
    canvas.waitWhileRendering()


def _decorate(img, hour, title):
    p = QPainter(img)
    p.setRenderHint(QPainter.RenderHint.Antialiasing)
    f = QFont("Meiryo"); f.setPointSize(11); p.setFont(f); p.setPen(QColor("#333333"))
    box_w = max(330, p.fontMetrics().horizontalAdvance(title) + 24)
    p.fillRect(QRectF(10, 10, box_w, 92), QColor(255, 255, 255, 225))
    p.drawText(20, 34, title)
    f.setPointSize(24); f.setBold(True); p.setFont(f); p.setPen(QColor("#99000d"))
    p.drawText(20, 82, hour_label(hour))
    # legend
    rs = _ranges()
    x0, y0, rh = 10, img.height() - 20 - 20 * len(rs) - 26, 20
    p.fillRect(QRectF(x0, y0, 210, 20 * len(rs) + 34), QColor(255, 255, 255, 215))
    f = QFont("Meiryo"); f.setPointSize(9); p.setFont(f); p.setPen(QColor("#333333"))
    p.drawText(x0 + 8, y0 + 18, "滞留人口密度（人/km²）")
    for i, (_, c, lab) in enumerate(rs):
        y = y0 + 26 + i * rh
        p.fillRect(QRectF(x0 + 8, y, 22, 14), c)
        p.setPen(QPen(QColor("#606060"))); p.drawRect(QRectF(x0 + 8, y, 22, 14))
        p.setPen(QColor("#333333")); p.drawText(x0 + 38, y + 12, lab)
    f.setPointSize(8); p.setFont(f); p.setPen(QColor("#555555"))
    p.drawText(img.width() - 330, img.height() - 10, "出典: 東京都市圏PT調査(H30) b-4 / 地理院地図 淡色")
    p.end()


def export_gif(layer, out_dir, gif_name="b4_anim.gif", frame_ms=600,
               title="東京都市圏PT（H30）計画基本ゾーン別 滞留人口密度"):
    from PIL import Image
    canvas = iface.mapCanvas()
    nav = setup_movie(layer)
    frames_dir = os.path.join(out_dir, "frames", "b4")
    os.makedirs(frames_dir, exist_ok=True)
    paths = []
    for i in range(N_FRAMES):
        nav.setCurrentFrameNumber(i)
        layer.triggerRepaint()
        _render_canvas(canvas)
        p = os.path.join(frames_dir, f"frame_{i:02d}_h{FIRST_HOUR + i:02d}.png")
        canvas.saveAsImage(p)
        img = QImage(p)
        _decorate(img, FIRST_HOUR + i, title)
        img.save(p)
        paths.append(p)
    nav.setCurrentFrameNumber(14 - FIRST_HOUR)   # 14時台に戻す
    ims = [Image.open(p).convert("RGB") for p in paths]
    pal = [im.quantize(colors=128, method=Image.Quantize.MEDIANCUT) for im in ims]
    gif = os.path.join(out_dir, gif_name)
    pal[0].save(gif, save_all=True, append_images=pal[1:], duration=frame_ms, loop=0, optimize=True)
    return gif, paths
