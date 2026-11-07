# -*- coding: utf-8 -*-
"""kzone_b4 の時刻別滞留人口密度を、時間帯間を線形補間した連続色でアニメーションし GIF を書き出す。

- 1時間を SUB コマに分割。値は各時間帯の中央（h時台 = h:30）に置き、隣接時間帯と線形補間。
- 色: 密度の log10 を 2〜5（100〜100,000 人/km²）で YlOrRd に連続割当（データ定義の塗り色）。
- 時系列コントローラ: ムービーモード、N_FRAMES コマ。@frame_number が無いときは @pt_hour を使う。
使い方（QGIS 上で exec 後）:
  configure(...)               # 任意: 色の範囲・出力名の切替（23区版など）
  setup_smooth(layer)
  export_frames(layer, out_dir, start, end)   # GUI を長く止めないよう分割実行可
  make_gif(out_dir)
"""
import os
from qgis.core import (Qgis, QgsApplication, QgsFillSymbol, QgsSingleSymbolRenderer, QgsSymbolLayer,
                       QgsProperty, QgsStyle)
from qgis.PyQt.QtCore import QElapsedTimer, QRectF, QPointF
from qgis.PyQt.QtGui import QImage, QPainter, QColor, QFont, QPen, QLinearGradient
from qgis.utils import iface

SUB = 4
FIRST_HOUR, LAST_HOUR = 3, 26
N_FRAMES = (LAST_HOUR - FIRST_HOUR) * SUB + 1          # 93
LOG_MIN, LOG_MAX = 2.0, 5.0                              # 100〜100,000 人/km²
RAMP = "YlOrRd"
FRAMES_SUBDIR = os.path.join("frames", "b4_smooth")
GIF_NAME = "b4_anim_smooth.gif"

T_EXPR = f"(coalesce(@frame_number, (@pt_hour - {FIRST_HOUR}) * {SUB}) / {float(SUB)} + {FIRST_HOUR})"
DENS_EXPR = (
    "with_variable('t', " + T_EXPR + ", "
    "with_variable('h0', floor(@t), "
    "with_variable('f', @t - @h0, "
    "((1 - @f) * attribute(concat('p', lpad(to_string(@h0), 2, '0')))"
    f" + @f * attribute(concat('p', lpad(to_string(min(@h0 + 1, {LAST_HOUR})), 2, '0'))))"
    " / \"area_km2\")))"
)
TICKS = [(2, "100"), (3, "1,000"), (4, "10,000"), (5, "100,000")]   # (log10値, 表示)


def configure(**kw):
    """LOG_MIN, LOG_MAX, TICKS, FRAMES_SUBDIR, GIF_NAME などを差し替える（例: 23区版）。"""
    g = globals()
    for k, v in kw.items():
        if k.upper() not in g:
            raise KeyError(k)
        g[k.upper()] = v


def color_expr():
    return f"ramp_color('{RAMP}', scale_linear(log10(max({DENS_EXPR}, 1)), {LOG_MIN}, {LOG_MAX}, 0, 1))"


def frame_time(i):
    """コマ番号 -> 表示時刻（h時台の中央 = h:30 を基準）"""
    t = FIRST_HOUR + i / SUB + 0.5
    h = int(t); m = int(round((t - h) * 60))
    if m == 60: h, m = h + 1, 0
    return (f"翌{h - 24}:{m:02d}" if h >= 24 else f"{h}:{m:02d}"), h


def setup_smooth(layer, fps=8, loop=True):
    sym = QgsFillSymbol.createSimple({"color": "#ffffb2", "outline_color": "#707070", "outline_width": "0.1"})
    sym.symbolLayer(0).setDataDefinedProperty(QgsSymbolLayer.Property.FillColor, QgsProperty.fromExpression(color_expr()))
    layer.setRenderer(QgsSingleSymbolRenderer(sym))
    tp = layer.temporalProperties()
    tp.setMode(Qgis.VectorTemporalMode.RedrawLayerOnly)
    tp.setIsActive(True)
    nav = iface.mapCanvas().temporalController()
    nav.setNavigationMode(Qgis.TemporalNavigationMode.Movie)
    nav.setTotalMovieFrames(N_FRAMES)
    nav.setFramesPerSecond(fps)
    nav.setLooping(loop)
    layer.triggerRepaint()
    return nav


def _render_canvas(canvas):
    canvas.refresh()
    t = QElapsedTimer(); t.start()
    while not canvas.isDrawing() and t.elapsed() < 2000:
        QgsApplication.processEvents()
    canvas.waitWhileRendering()


def _decorate(img, i, title):
    ramp = QgsStyle.defaultStyle().colorRamp(RAMP)
    p = QPainter(img)
    p.setRenderHint(QPainter.RenderHint.Antialiasing)
    f = QFont("Meiryo"); f.setPointSize(11); p.setFont(f)
    box_w = max(330, p.fontMetrics().horizontalAdvance(title) + 24)
    p.fillRect(QRectF(10, 10, box_w, 92), QColor(255, 255, 255, 225))
    p.setPen(QColor("#333333")); p.drawText(20, 34, title)
    label, _ = frame_time(i)
    f.setPointSize(24); f.setBold(True); p.setFont(f); p.setPen(QColor("#99000d"))
    p.drawText(20, 82, label)
    # time progress bar
    bx, by, bw = 20, 92, box_w - 20
    p.fillRect(QRectF(bx, by, bw, 4), QColor("#dddddd"))
    p.fillRect(QRectF(bx, by, bw * i / (N_FRAMES - 1), 4), QColor("#99000d"))
    # gradient legend
    lx, ly, lw, lh = 10, img.height() - 92, 260, 76
    p.fillRect(QRectF(lx, ly, lw, lh), QColor(255, 255, 255, 225))
    f = QFont("Meiryo"); f.setPointSize(9); p.setFont(f); p.setPen(QColor("#333333"))
    p.drawText(lx + 10, ly + 18, "滞留人口密度（人/km²、対数）")
    gx, gy, gw, gh = lx + 14, ly + 26, lw - 34, 14
    grad = QLinearGradient(QPointF(gx, 0), QPointF(gx + gw, 0))
    for k in range(11):
        grad.setColorAt(k / 10, ramp.color(k / 10))
    p.fillRect(QRectF(gx, gy, gw, gh), grad)
    p.setPen(QPen(QColor("#606060"))); p.drawRect(QRectF(gx, gy, gw, gh))
    p.setPen(QColor("#333333"))
    for v, lab in TICKS:
        x = gx + gw * (v - LOG_MIN) / (LOG_MAX - LOG_MIN)
        p.drawLine(QPointF(x, gy + gh), QPointF(x, gy + gh + 4))
        w = p.fontMetrics().horizontalAdvance(lab)
        p.drawText(int(x - w / 2), int(gy + gh + 18), lab)
    f.setPointSize(8); p.setFont(f); p.setPen(QColor("#555555"))
    src = "出典: 東京都市圏PT調査(H30) b-4（時間帯間は線形補間）/ 地理院地図 淡色"
    sw = p.fontMetrics().horizontalAdvance(src)
    p.fillRect(QRectF(img.width() - sw - 18, img.height() - 24, sw + 12, 20), QColor(255, 255, 255, 225))
    p.drawText(img.width() - sw - 12, img.height() - 10, src)
    p.end()


def export_frames(layer, out_dir, start=0, end=N_FRAMES,
                  title="東京都市圏PT（H30）計画基本ゾーン別 滞留人口密度"):
    canvas = iface.mapCanvas()
    nav = canvas.temporalController()
    d = os.path.join(out_dir, FRAMES_SUBDIR); os.makedirs(d, exist_ok=True)
    paths = []
    for i in range(start, min(end, N_FRAMES)):
        nav.setCurrentFrameNumber(i)
        layer.triggerRepaint()
        _render_canvas(canvas)
        p = os.path.join(d, f"frame_{i:03d}.png")
        canvas.saveAsImage(p)
        img = QImage(p); _decorate(img, i, title); img.save(p)
        paths.append(p)
    return paths


def make_gif(out_dir, frame_ms=120, hold_ms=600):
    from PIL import Image
    d = os.path.join(out_dir, FRAMES_SUBDIR)
    paths = [os.path.join(d, f"frame_{i:03d}.png") for i in range(N_FRAMES)]
    missing = [p for p in paths if not os.path.exists(p)]
    if missing:
        raise RuntimeError(f"missing {len(missing)} frames, e.g. {missing[0]}")
    ims = [Image.open(p).convert("RGB").quantize(colors=128, method=Image.Quantize.MEDIANCUT) for p in paths]
    dur = [frame_ms] * N_FRAMES
    dur[0] = dur[-1] = hold_ms
    gif = os.path.join(out_dir, GIF_NAME)
    ims[0].save(gif, save_all=True, append_images=ims[1:], duration=dur, loop=0, optimize=True)
    return gif


def render_offscreen(layers, extent, frame, size=(968, 877), dpi=None, crs="EPSG:6677", bg="#ffffff"):
    """キャンバスを使わず、範囲・サイズ・レイヤを固定して1コマ描画する（操作の影響を受けない）。"""
    from qgis.core import (QgsProject, QgsMapSettings, QgsMapRendererCustomPainterJob, QgsExpressionContext,
                           QgsExpressionContextUtils, QgsExpressionContextScope, QgsCoordinateReferenceSystem)
    from qgis.PyQt.QtCore import QSize
    ms = QgsMapSettings()
    ms.setLayers(layers)
    ms.setDestinationCrs(QgsCoordinateReferenceSystem(crs))
    ms.setOutputSize(QSize(*size))
    if dpi:
        ms.setOutputDpi(dpi)
    ms.setExtent(extent)
    ms.setBackgroundColor(QColor(bg))
    ctx = QgsExpressionContext()
    ctx.appendScopes(QgsExpressionContextUtils.globalProjectLayerScopes(None))
    ctx.appendScope(QgsExpressionContextUtils.mapSettingsScope(ms))
    sc = QgsExpressionContextScope("frame"); sc.setVariable("frame_number", frame)
    ctx.appendScope(sc)
    ms.setExpressionContext(ctx)
    img = QImage(QSize(*size), QImage.Format.Format_ARGB32_Premultiplied)
    img.fill(QColor(bg))
    p = QPainter(img)
    job = QgsMapRendererCustomPainterJob(ms, p)
    job.renderSynchronously()
    p.end()
    return img


def export_frames_offscreen(layers, extent, out_dir, frames, title, size=(968, 877), dpi=None):
    d = os.path.join(out_dir, FRAMES_SUBDIR); os.makedirs(d, exist_ok=True)
    paths = []
    for i in frames:
        img = render_offscreen(layers, extent, i, size, dpi)
        _decorate(img, i, title)
        p = os.path.join(d, f"frame_{i:03d}.png"); img.save(p); paths.append(p)
    return paths
