# -*- coding: utf-8 -*-
"""P1（issue #10）: 勤務者を除くかどうかで、にぎわいの地図はどれだけ変わるか（東京PT H30）。

3つの地図を比べる（いずれも集中量＝着いたトリップ数、平日、帰宅を除く）
  A 全目的       non_home = 集中量合計 − 帰宅
  B 通勤・業務除く nowork  = non_home − 業務系（自宅－勤務＋自宅－業務＋勤務・業務）
  C 私事のみ     shiji_all = 自宅－私事＋私事
参考 T = 帰宅を含む集中量合計 total

指標
  - Spearman 順位相関（A・B・C・T の組み合わせ）
  - 上位 N の重なり（N=30, 60）
  - LISA（局所モラン I、クイーン隣接・行標準化・条件付き並べ替え 999 回、p<0.05）の HH（ホットスポット）の入れ替わり率
  - A→C の順位変化（パーセンタイル差）と、ゾーン属性（業務比率・昼夜比・駅乗降客数・夜間人口）との順位相関

計画基本ゾーンは密度（/km²）、500m メッシュはほぼ等面積なのでトリップ数で比べる。
メッシュは mesh-1 に載っているもののみ。小さい値は誤差が大きいので、全件と A≥5,000 トリップ（rse≦30%）の両方で相関を出す。

実行: python -I scripts/analyze_p1_h30.py （QGIS 不要）
入力: data/pt_h30_purpose.gpkg（build_purpose_h30.py）、data/pt_h30_zones_b4.gpkg、data/raw/H30_gis/H30_szone.shp、
      data/raw/stations/S12-23/UTF-8/S12-23_NumberOfPassengers.geojson
出力: data/p1_h30.gpkg（kzone_p1, mesh500_p1）、output/p1/*.csv・*.png
"""
import os, sys
import numpy as np
import pandas as pd
import geopandas as gpd
from scipy import stats, sparse

BASE = globals().get("BASE") or os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
DATA = os.path.join(BASE, "data")
RAW = os.path.join(DATA, "raw")
OUT_DIR = os.path.join(BASE, "output", "p1")
OUT_GPKG = os.path.join(DATA, "p1_h30.gpkg")
CRS = "EPSG:6677"
SEED = 20261108
PERMS = 999
ALPHA = 0.05
MAPS = {"A": "全目的（帰宅除く）", "B": "通勤・業務を除く", "C": "私事のみ", "T": "参考: 帰宅を含む全目的"}


# ---------------------------------------------------------------- LISA
def queen_weights(g):
    """ポリゴンの共有点・共有辺で隣接（クイーン）。行標準化前の 0/1 疎行列。"""
    left = g[["geometry"]].reset_index(drop=True)
    left["i"] = np.arange(len(left))
    j = gpd.sjoin(left, left, how="inner", predicate="intersects")
    j = j[j["i_left"] != j["i_right"]]
    n = len(g)
    return sparse.csr_matrix((np.ones(len(j)), (j["i_left"].values, j["i_right"].values)), shape=(n, n))


def local_moran(x, W, perms=PERMS, seed=SEED):
    """局所モラン I（行標準化）。条件付き並べ替えで擬似 p 値（片側・折り返し）。
    戻り値: I, p, quad（1=HH, 2=LH, 3=LL, 4=HL）, 島（隣接なし）は p=nan。"""
    rng = np.random.default_rng(seed)
    n = len(x)
    z = (x - x.mean()) / x.std()
    k = np.asarray(W.sum(axis=1)).ravel().astype(int)
    Wr = sparse.diags(np.where(k > 0, 1.0 / np.maximum(k, 1), 0)) @ W
    lag = Wr @ z
    I = z * lag
    p = np.full(n, np.nan)
    for kk in np.unique(k[k > 0]):
        idx = np.where(k == kk)[0]
        for s in range(0, len(idx), 400):
            rows = idx[s:s + 400]
            r = rng.integers(0, n - 1, size=(len(rows), perms, kk))
            r = r + (r >= rows[:, None, None])          # 自分自身を飛ばす
            sim = z[rows, None] * z[r].mean(axis=2)
            larger = (sim >= I[rows, None]).sum(axis=1)
            larger = np.minimum(larger, perms - larger)
            p[rows] = (larger + 1) / (perms + 1)
    quad = np.select([(z > 0) & (lag > 0), (z <= 0) & (lag > 0), (z <= 0) & (lag <= 0)], [1, 2, 3], 4)
    return I, p, quad


def lisa_class(x, W):
    I, p, quad = local_moran(np.log1p(np.asarray(x, dtype=float)), W)
    lab = np.array(["HH", "LH", "LL", "HL"])[quad - 1]
    return np.where(p < ALPHA, lab, "ns")


def turnover(a, b):
    """a のホットスポットのうち b で外れた割合、Jaccard 係数。"""
    a, b = set(a), set(b)
    if not a:
        return np.nan, np.nan
    return len(a - b) / len(a), len(a & b) / len(a | b)


def compare(df, cols, key, label):
    """順位相関・上位 N の重なり・HH の入れ替わりの表を返す。"""
    rows = []
    for i, c1 in enumerate(cols):
        for c2 in cols[i + 1:]:
            ok = df[[c1, c2]].notna().all(axis=1)
            rho = stats.spearmanr(df.loc[ok, c1], df.loc[ok, c2]).statistic
            r = {"単位": label, "地図1": c1, "地図2": c2, "n": int(ok.sum()), "spearman": round(rho, 3)}
            for N in (30, 60):
                t1 = set(df.loc[ok].nlargest(N, c1)[key])
                t2 = set(df.loc[ok].nlargest(N, c2)[key])
                r[f"上位{N}の重なり"] = len(t1 & t2) / N
            h1 = df.loc[df[f"lisa_{c1}"] == "HH", key]
            h2 = df.loc[df[f"lisa_{c2}"] == "HH", key]
            out, jac = turnover(h1, h2)
            r.update({"HH数1": len(h1), "HH数2": len(h2), "HH1→2で外れた割合": round(out, 3), "HH_Jaccard": round(jac, 3)})
            rows.append(r)
    return pd.DataFrame(rows)


# ---------------------------------------------------------------- 属性
def zone_attributes(kz):
    b4 = gpd.read_file(os.path.join(DATA, "pt_h30_zones_b4.gpkg"), layer="kzone_b4")
    kz = kz.merge(b4[["kzone", "p04", "p14", "day_night"]].rename(columns={"p04": "pop_04", "p14": "pop_14"}),
                  on="kzone", how="left")
    kz["pop04_dens"] = kz["pop_04"] / kz["area_km2"]
    # 市区町村名（小ゾーンの面積最大のもの）
    sz = gpd.read_file(os.path.join(RAW, "H30_gis", "H30_szone.shp"), encoding="cp932").to_crs(CRS)
    sz["a"] = sz.geometry.area
    szk = gpd.read_file(os.path.join(DATA, "pt_h30_zones_b4.gpkg"), layer="szone", columns=["szone", "kzone"],
                        ignore_geometry=True)
    sz = sz.merge(szk, on="szone", how="left")
    city = sz.sort_values("a", ascending=False).drop_duplicates("kzone").set_index("kzone")["CityName"]
    kz["city"] = kz["kzone"].map(city)
    # 駅乗降客数 2018（S12、全駅・路線別の行を合計。重複フラグ行は 0 として扱う）
    st = gpd.read_file(os.path.join(RAW, "stations", "S12-23", "UTF-8", "S12-23_NumberOfPassengers.geojson"))
    st = st.to_crs(CRS)
    st["riders"] = pd.to_numeric(st["S12_037"], errors="coerce").fillna(0)
    st["geometry"] = st.geometry.centroid
    j = gpd.sjoin(st[["riders", "geometry"]], kz[["kzone", "geometry"]], predicate="within")
    kz["riders2018"] = kz["kzone"].map(j.groupby("kzone")["riders"].sum()).fillna(0)
    kz["riders_dens"] = kz["riders2018"] / kz["area_km2"]
    major = gpd.read_file(os.path.join(DATA, "pt_h30_zones_b4.gpkg"), layer="stations_major").nsmallest(30, "rank")
    kz["dist_major30_km"] = kz.geometry.centroid.apply(lambda p: major.distance(p).min() / 1000)
    return kz


# ---------------------------------------------------------------- 図
def plot_maps(g, cols, fname, title, scheme_col_suffix="_pct"):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    plt.rcParams["font.family"] = ["Yu Gothic", "Meiryo", "MS Gothic", "sans-serif"]
    fig, axes = plt.subplots(1, len(cols), figsize=(5.2 * len(cols), 5.6))
    for ax, c in zip(np.atleast_1d(axes), cols):
        v = g[c + scheme_col_suffix]
        g.assign(v=np.floor(v * 10).clip(0, 9)).plot(column="v", cmap="magma", ax=ax, linewidth=0,
                                                     missing_kwds={"color": "#dddddd"})
        ax.set_title(f"{c}: {MAPS[c]}", fontsize=11)
        ax.set_axis_off()
    fig.suptitle(title, fontsize=13)
    fig.tight_layout()
    fig.savefig(os.path.join(OUT_DIR, fname), dpi=130)
    plt.close(fig)


def plot_lisa(g, cols, fname, title):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    plt.rcParams["font.family"] = ["Yu Gothic", "Meiryo", "MS Gothic", "sans-serif"]
    colors = {"HH": "#d7191c", "HL": "#fdae61", "LH": "#abd9e9", "LL": "#2c7bb6", "ns": "#eeeeee"}
    fig, axes = plt.subplots(1, len(cols), figsize=(5.2 * len(cols), 5.6))
    for ax, c in zip(np.atleast_1d(axes), cols):
        g.plot(color=g[f"lisa_{c}"].map(colors).fillna("#dddddd"), ax=ax, linewidth=0)
        ax.set_title(f"{c}: {MAPS[c]}  HH={int((g[f'lisa_{c}'] == 'HH').sum())}", fontsize=11)
        ax.set_axis_off()
    fig.suptitle(title + "（赤=HH, 橙=HL, 水色=LH, 青=LL, p<0.05）", fontsize=13)
    fig.tight_layout()
    fig.savefig(os.path.join(OUT_DIR, fname), dpi=130)
    plt.close(fig)


def plot_change(g, col, fname, title):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    plt.rcParams["font.family"] = ["Yu Gothic", "Meiryo", "MS Gothic", "sans-serif"]
    fig, ax = plt.subplots(figsize=(7, 6.5))
    g.plot(column=col, cmap="RdBu_r", vmin=-0.4, vmax=0.4, ax=ax, linewidth=0, legend=True,
           legend_kwds={"shrink": 0.6, "label": "パーセンタイル順位の差（C − A）"}, missing_kwds={"color": "#dddddd"})
    ax.set_title(title, fontsize=12)
    ax.set_axis_off()
    fig.tight_layout()
    fig.savefig(os.path.join(OUT_DIR, fname), dpi=130)
    plt.close(fig)


# ---------------------------------------------------------------- 本体
def prep(g):
    g = g.copy()
    g["A"] = g["non_home"]
    g["B"] = g["non_home"] - g["work_all"]
    g["C"] = g["shiji_all"]
    g["T"] = g["total"]
    return g


def run():
    os.makedirs(OUT_DIR, exist_ok=True)
    pur = os.path.join(DATA, "pt_h30_purpose.gpkg")
    cols = ["A", "B", "C"]
    res = {}

    # ---- 計画基本ゾーン（密度）
    kz = prep(gpd.read_file(pur, layer="kzone_purpose"))
    kz = kz[kz["total"].notna()].reset_index(drop=True)
    kz["geometry"] = kz.geometry.make_valid()
    for c in cols + ["T"]:
        kz[c] = kz[c] / kz["area_km2"]
    kz = zone_attributes(kz)
    Wz = queen_weights(kz)
    for c in cols + ["T"]:
        kz[c + "_pct"] = kz[c].rank(pct=True)
        kz[f"lisa_{c}"] = lisa_class(kz[c], Wz)
    kz["d_CA"] = kz["C_pct"] - kz["A_pct"]
    kz["d_BA"] = kz["B_pct"] - kz["A_pct"]
    cz = compare(kz, cols + ["T"], "kzone", "計画基本ゾーン（密度）")
    # 全ゾーンの順位相関は都市部と郊外の差で高く出るので、A の上位だけでも見る
    sub = []
    for q in (0.5, 0.8, 0.9):
        t = kz[kz["A_pct"] >= q]
        c = compare(t, cols, "kzone", f"計画基本ゾーン（A上位{round((1 - q) * 100)}%）")
        sub.append(c.drop(columns=[x for x in c.columns if x.startswith("HH")]))
    cz = pd.concat([cz] + sub, ignore_index=True)

    # 順位変化と属性
    attrs = {"work_share": "業務系の比率", "day_night": "昼夜比（14時/4時の滞留）", "pop04_dens": "夜間（4時）滞留密度",
             "riders_dens": "駅乗降客数密度(2018)", "dist_major30_km": "主要30駅までの距離", "A": "A の密度"}
    ar = []
    for a, lab in attrs.items():
        ok = kz[[a, "d_CA"]].notna().all(axis=1)
        ar.append({"属性": lab, "列": a, "spearman_d_CA": round(stats.spearmanr(kz.loc[ok, a], kz.loc[ok, "d_CA"]).statistic, 3),
                   "spearman_d_BA": round(stats.spearmanr(kz.loc[ok, a], kz.loc[ok, "d_BA"]).statistic, 3)})
    ar = pd.DataFrame(ar)

    show = ["kzone", "city", "A", "C", "A_pct", "C_pct", "d_CA", "work_share", "day_night", "riders2018",
            "lisa_A", "lisa_C"]
    top = kz[kz["A_pct"] >= 0.5]   # 中位以上のゾーンで、大きく落ちる・上がる場所
    fall = top.nsmallest(20, "d_CA")[show]
    rise = kz.nlargest(20, "d_CA")[show]
    hh_lost = kz[(kz["lisa_A"] == "HH") & (kz["lisa_C"] != "HH")][show]
    hh_new = kz[(kz["lisa_C"] == "HH") & (kz["lisa_A"] != "HH")][show]

    # ---- 500m メッシュ（トリップ数）
    me = prep(gpd.read_file(pur, layer="mesh500_purpose"))
    me = me[me["in_mesh1"]].reset_index(drop=True)
    Wm = queen_weights(me)
    for c in cols:
        me[c + "_pct"] = me[c].rank(pct=True)
        me[f"lisa_{c}"] = lisa_class(me[c], Wm)
    me["d_CA"] = me["C_pct"] - me["A_pct"]
    cm = compare(me, cols, "mesh", "500mメッシュ（全件）")
    rel = me[me["A"] >= 5000]
    cm_rel = compare(rel, cols, "mesh", "500mメッシュ（A≥5,000）")
    me["city"] = me["kzone"].map(kz.set_index("kzone")["city"])
    for c in cols:
        me[f"rank_{c}"] = me[c].rank(ascending=False, method="min")
    mtop = me[(me["rank_A"] <= 30) | (me["rank_C"] <= 30)].sort_values("rank_A")[
        ["mesh", "city", "A", "C", "rank_A", "rank_B", "rank_C", "work_share"]]
    cm_rel = cm_rel.drop(columns=[c for c in cm_rel.columns if c.startswith("HH")])  # LISA は全件で推定したもの

    # ---- 保存
    if os.path.exists(OUT_GPKG):
        os.remove(OUT_GPKG)
    kz.to_file(OUT_GPKG, layer="kzone_p1", driver="GPKG")
    me[["mesh", "kzone", "city", "rank_A", "rank_C", "A", "B", "C", "A_pct", "B_pct", "C_pct", "d_CA", "lisa_A", "lisa_B", "lisa_C",
        "rse_total", "rse_shiji", "geometry"]].to_file(OUT_GPKG, layer="mesh500_p1", driver="GPKG")
    summary = pd.concat([cz, cm, cm_rel], ignore_index=True)
    summary.to_csv(os.path.join(OUT_DIR, "p1_compare.csv"), index=False, encoding="utf-8-sig")
    ar.to_csv(os.path.join(OUT_DIR, "p1_rankchange_attrs.csv"), index=False, encoding="utf-8-sig")
    for name, d in [("mesh_top30", mtop), ("kzone_fall", fall), ("kzone_rise", rise), ("kzone_hh_lost", hh_lost),
                    ("kzone_hh_new", hh_new)]:
        d.to_csv(os.path.join(OUT_DIR, f"p1_{name}.csv"), index=False, encoding="utf-8-sig")

    plot_maps(kz, cols, "p1_kzone_deciles.png", "計画基本ゾーン 集中量密度の十分位（平日・東京PT H30）")
    plot_lisa(kz, cols, "p1_kzone_lisa.png", "計画基本ゾーン LISA")
    plot_change(kz, "d_CA", "p1_kzone_change_CA.png", "全目的→私事のみ で順位がどう動くか（赤=上がる, 青=下がる）")
    plot_maps(me, cols, "p1_mesh_deciles.png", "500mメッシュ 集中量の十分位")
    plot_lisa(me, cols, "p1_mesh_lisa.png", "500mメッシュ LISA")

    res.update(mesh_top30=mtop, summary=summary, attrs=ar, fall=fall, rise=rise, hh_lost=hh_lost, hh_new=hh_new)
    return res


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")
    pd.set_option("display.width", 250, "display.max_columns", 30)
    r = run()
    for k in ("summary", "mesh_top30", "attrs", "fall", "rise", "hh_lost", "hh_new"):
        print(f"\n==== {k}")
        print(r[k].round(3).to_string(index=False))
