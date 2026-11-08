# -*- coding: utf-8 -*-
"""分析レポート（docs/pt_h30_analysis_p1_p3_p4.md）用の図を作り、output/ の図とあわせて docs/figures/pt_h30/ に置く。

実行: python -I scripts/report_figs_pt_h30.py （analyze_p1/p3/p4_h30.py の後）
"""
import os, shutil, sys
import numpy as np
import geopandas as gpd
from shapely.geometry import box

BASE = globals().get("BASE") or os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
DATA = os.path.join(BASE, "data")
OUT = os.path.join(BASE, "output")
FIG = os.path.join(BASE, "..", "docs", "figures", "pt_h30")
CRS = "EPSG:6677"
CENTER = (139.62, 35.60, 139.86, 35.76)   # 都心の範囲（経緯度）

COPY = ["p1/p1_kzone_change_CA.png", "p1/p1_mesh_lisa.png", "p3/p3_resid_map.png", "p3/p3_pred_obs.png",
        "p4/p4_quadrants.png"]


def mesh_change_center():
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    plt.rcParams["font.family"] = ["Yu Gothic", "Meiryo", "MS Gothic", "sans-serif"]
    me = gpd.read_file(os.path.join(DATA, "p1_h30.gpkg"), layer="mesh500_p1")
    kz = gpd.read_file(os.path.join(DATA, "p1_h30.gpkg"), layer="kzone_p1", columns=["kzone", "city"])
    clip = gpd.GeoSeries([box(*CENTER)], crs="EPSG:6668").to_crs(CRS).iloc[0]
    me = me[me.intersects(clip)]
    rel = me[me["A"] >= 5000].copy()
    # 誤差の小さいメッシュ（A≥5,000）の中で付け直した順位の差
    rel["chg"] = rel["C"].rank(pct=True) - rel["A"].rank(pct=True)
    fig, ax = plt.subplots(figsize=(9, 7.5))
    me.plot(color="#f0f0f0", ax=ax, linewidth=0)
    rel.plot(column="chg", cmap="RdBu_r", vmin=-0.5, vmax=0.5, ax=ax, linewidth=0, legend=True,
             legend_kwds={"shrink": 0.6, "label": "順位の差（私事のみ − 全目的、パーセンタイル）"})
    kz[kz.intersects(clip)].boundary.plot(ax=ax, color="#888888", linewidth=0.3)
    labels = {"千代田区": "丸の内・大手町", "港区": "港区", "新宿区": "新宿", "豊島区": "池袋", "渋谷区": "渋谷",
              "品川区": "品川", "中央区": "銀座・日本橋"}
    for (city, lab), (lon, lat) in zip(labels.items(), [(139.765, 35.684), (139.745, 35.655), (139.700, 35.692),
                                                        (139.711, 35.730), (139.702, 35.658), (139.739, 35.628),
                                                        (139.770, 35.672)]):
        p = gpd.GeoSeries(gpd.points_from_xy([lon], [lat]), crs="EPSG:6668").to_crs(CRS).iloc[0]
        ax.annotate(lab, (p.x, p.y), fontsize=9, ha="center",
                    bbox=dict(boxstyle="round,pad=0.15", fc="white", ec="none", alpha=0.7))
    ax.set_xlim(clip.bounds[0], clip.bounds[2]); ax.set_ylim(clip.bounds[1], clip.bounds[3])
    ax.set_axis_off()
    ax.set_title("都心の 500m メッシュ：全目的→私事のみで順位がどう動くか\n（赤=上がる, 青=下がる。全目的 5,000 トリップ以上のメッシュ、灰色はそれ未満）",
                 fontsize=11)
    fig.tight_layout()
    fig.savefig(os.path.join(FIG, "p1_mesh_change_center.png"), dpi=120)
    plt.close(fig)


def main():
    os.makedirs(FIG, exist_ok=True)
    for f in COPY:
        shutil.copy(os.path.join(OUT, f), os.path.join(FIG, os.path.basename(f)))
    mesh_change_center()
    return sorted(os.listdir(FIG))


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")
    print(main())
