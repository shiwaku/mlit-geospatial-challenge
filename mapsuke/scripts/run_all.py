# -*- coding: utf-8 -*-
"""東京都市圏PT H30 時刻別滞留人口アニメーション一式を再生成する（QGIS 上で exec する）。

前提: QGIS で mapsuke/tokyo_pt_h30_zone.qgz を開いていること
      （レイヤ ID で参照: 滞留人口 kzone_b4 レイヤ, 地理院ベクトルタイル背景）。
使い方: QGIS の Python コンソール等で
      exec(open(r"<このファイル>", encoding="utf-8").read())
      main()                       # GIF 一式を再生成
      main(rebuild_data=True)      # データ（GPKG）から作り直す（GPKG を使うレイヤを外してから実行）
"""
import os, time

from qgis.core import QgsProject

# mapsuke/ の場所。run_all.py から渡されたもの → このファイルの位置 → 開いている QGIS プロジェクトの場所 の順に使う
BASE = globals().get("BASE") or (os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
                                 if "__file__" in globals() else QgsProject.instance().homePath())
SCRIPTS = os.path.join(BASE, "scripts")


def _load(name, modname):
    ns = {"__name__": modname, "BASE": BASE, "__file__": os.path.join(SCRIPTS, name)}
    p = os.path.join(SCRIPTS, name)
    exec(compile(open(p, encoding="utf-8").read(), p, "exec"), ns)
    return ns


def rebuild_data():
    """1) b-4 を計画基本ゾーンへ結合し GPKG(kzone_b4, szone) と整形CSVを作成
       2) 都県境界 pref・調査対象範囲 study_area を作成
       3) 主要駅 stations_major を作成"""
    j = _load("join_b4_kzone.py", "join_b4"); print("join:", {k: v for k, v in j["run"]().items() if k != "aggregate_rows"})
    pt = _load("anim_kzone_b4_ptinfo.py", "ptinfo"); pt["ensure_boundaries"]()
    st = _load("build_stations_major.py", "stations"); err, rows = st["build"](); print("stations:", err[0], len(rows))


def export_all():
    from qgis.core import QgsProject
    proj = QgsProject.instance()
    pt = _load("anim_kzone_b4_ptinfo.py", "ptinfo")
    glow = _load("glow_samples.py", "glow")
    b4 = proj.mapLayer(pt["B4_LAYER_ID"])
    vt = proj.mapLayer("____________________bbf1ec0d_2c0d_46e0_b67d_3800b115faaf")
    if b4 is None or vt is None:
        raise RuntimeError("tokyo_pt_h30_zone.qgz を開いてから実行してください（必要レイヤが見つかりません）")
    pt["setup_style"](b4)                       # 14段階スタイル＋時系列コントローラ
    reg, k23 = pt["region_extent"](b4), pt["ku23_extent"]()
    T_REG, T_23 = "東京都市圏PT（H30）時刻別滞留人口", "東京23区 時刻別滞留人口（東京都市圏PT H30）"
    out = {}
    t = time.time()
    # 公式準拠配色・14段階（背景: 道路鉄道と文字を上、水面を下）
    out["ptinfo_region"] = pt["export"]("region", reg, T_REG, [vt])[1]
    out["ptinfo_23ku"] = pt["export"]("23ku", k23, T_23, [vt])[1]
    # 同・主要駅（日英併記）付き
    out["ptinfo_region_st"] = pt["export"]("region_st", reg, T_REG, [vt], stations_top=30)[1]
    out["ptinfo_23ku_st"] = pt["export"]("23ku_st", k23, T_23, [vt], stations_top=60)[1]
    # 夜景風（inferno＋グロー）・鉄道線＋主要駅
    out["night_region_st"] = glow["export_night"]("region_st", reg, T_REG, 30)[1]
    out["night_23ku_st"] = glow["export_night"]("23ku_st", k23, T_23, 60)[1]
    print(f"done in {time.time() - t:.0f}s")
    return out


def main(rebuild_data_first=False, rebuild_data=False):
    if rebuild_data or rebuild_data_first:
        globals()["rebuild_data"]()
    return export_all()
