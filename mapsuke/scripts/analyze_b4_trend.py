# -*- coding: utf-8 -*-
"""時刻別滞留人口（b-4）の経年比較：S63・H10・H20・H30 を H30 の市区町村にそろえて伸びを見る。

ゾーンの対応づけ
  協議会の「ゾーンコードの経年対応表」（zonecode.xlsx、計基ゾーン対応シート）で、過去回の計画基本ゾーンを
  H30 の計画基本ゾーンに対応させる。コードが同じでも回によって場所が違うゾーンがある（茨城南部・埼玉・千葉で
  番号の振り直し）ため、コードの一致では対応づけない。
  1つの過去ゾーンが複数の H30 ゾーンに対応するときは、H30 の3時台の滞留人口（≒夜間人口）の比で配り分ける
  （昼の値も同じ比で配るので、昼の分布が夜と違うゾーンでは近似）。
  H30 の計画基本ゾーン → 市区町村は、小ゾーンの面積が最大の市区町村（政令市は区）。

指標（平日、全目的・全員の滞留。居住者・勤務者を含む）
  day   = 14時台の滞留人口、night = 3時台の滞留人口
  share = day ÷ 4回すべてにある市区町村の day 合計（都市圏の昼の人の中での取り分）
  share_ratio = share_H30 ÷ share_S63（都市圏全体の伸びを除いた相対的な伸び）
  dn    = day ÷ night（昼夜比。1 を超えると昼に人が集まる）
注意: H20 は時刻不明が約3割あり、各時刻の値が小さく出る。share と dn は時刻不明が市区町村間で均等なら影響しないが、
      偏りは残る。経年の結論は S63→H30 と、H20 を飛ばした比較で読む。H20 と H30 は拡大手法も違う。

実行: python -I scripts/analyze_b4_trend.py （QGIS 不要、xlrd が必要）
入力: data/raw/extracted/{S63,H10,H20}/b-4/**/*.xls（各年の b-4.lzh を 7-Zip で展開したもの）、
      data/raw/zonecode_keinen/zonecode.xlsx（https://www.tokyo-pt.jp/static/hp/file/data/zonecode.xlsx）、
      data/pt_h30_b4_tidy.csv、data/raw/H30_gis/H30_szone.shp
出力: data/b4_trend.gpkg（city_b4_trend）、output/b4_trend/*.csv・*.png
"""
import os, re, glob, sys, warnings
import numpy as np
import pandas as pd
import geopandas as gpd

warnings.filterwarnings("ignore", category=RuntimeWarning)
sys.stdout.reconfigure(encoding="utf-8")

BASE = globals().get("BASE") or os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
DATA = os.path.join(BASE, "data")
RAW = os.path.join(DATA, "raw")
OUT_DIR = os.path.join(BASE, "output", "b4_trend")
OUT_GPKG = os.path.join(DATA, "b4_trend.gpkg")
CRS = "EPSG:6677"
YEARS = ["S63", "H10", "H20", "H30"]
TCOLS = ["p03_pre"] + [f"p{h:02d}" for h in range(3, 27)] + ["p27_post"]  # 26列
DAY, NIGHT = "p14", "p03"

# ---------------------------------------------------------------- 入力
def load_past_b4(year):
    f = glob.glob(os.path.join(RAW, "extracted", year, "b-4", "**", "*.xls"), recursive=True)
    assert len(f) == 1, f
    d = pd.read_excel(f[0], header=None, skiprows=4)
    code = d[1].astype(str).str.extract(r"^:(\d{4})$")[0]  # 名前の付いていない行がゾーン（集計行は名前付き）
    d = d[code.notna()].copy()
    out = pd.DataFrame({"code": code[code.notna()].values})
    for i, c in enumerate(TCOLS):
        out[c] = pd.to_numeric(d[2 + i], errors="coerce").fillna(0).values
    out["p_unknown"] = pd.to_numeric(d[28], errors="coerce").fillna(0).values
    return out


def load_h30_b4(kz_valid):
    d = pd.read_csv(os.path.join(DATA, "pt_h30_b4_tidy.csv"), dtype={"code": str})
    d = d[d["code"].isin(kz_valid)]
    return d[["code"] + TCOLS + ["p_unknown"]].copy()


def keinen_table():
    k = pd.read_excel(os.path.join(RAW, "zonecode_keinen", "zonecode.xlsx"), sheet_name="計基ゾーン対応",
                      header=None, skiprows=5, dtype=str)
    k.columns = ["pref", "seq", "H30", "H20", "H10", "S63"]
    return k.dropna(subset=["H30"])


def h30_zone_city():
    s = gpd.read_file(os.path.join(RAW, "H30_gis", "H30_szone.shp"), encoding="cp932").to_crs(CRS)
    s["geometry"] = s.geometry.make_valid().buffer(0)  # 点の足りないリングを含むため修復
    s["kzone"] = s["szone"].astype(str).str.zfill(5).str[:4]
    s["ckey"] = s["JisCode"].astype(str).str.zfill(5)
    s["area"] = s.area
    names = s.drop_duplicates("ckey").set_index("ckey")["CityName"].to_dict()
    a = s.groupby(["kzone", "ckey"])["area"].sum().reset_index().sort_values("area", ascending=False)
    kz = a.drop_duplicates("kzone").set_index("kzone")["ckey"]
    # 地図の単位: 計画基本ゾーンを、割り当てた市区町村ごとにまとめる。
    # 小さな町村はどの計画基本ゾーンでも面積最大にならないので、同じゾーンの市区町村にまとめて塗られる。
    s["unit"] = s["kzone"].map(kz)
    geom = s.dissolve(by="unit")[["geometry"]]
    geom.index.name = "ckey"
    absorbed = {u: "・".join(sorted({names[c] for c in grp["ckey"] if c != u})) for u, grp in s.groupby("unit")}
    geom["city"] = geom.index.map(names)
    geom["absorbed"] = [absorbed.get(k, "") for k in geom.index]
    geom["city"] = [n + ("ほか" if a else "") for n, a in zip(geom["city"], geom["absorbed"])]
    return kz, names, geom


# ---------------------------------------------------------------- 対応づけ
def zone_weights(year, keinen, kz, h30_night):
    """過去回の計画基本ゾーン → (H30 の市区町村, 重み) の表。重みは対応する H30 ゾーンの夜間人口の比。"""
    if year == "H30":
        w = pd.DataFrame({"code": kz.index, "kz30": kz.index, "w": 1.0})
    else:
        w = keinen[[year, "H30"]].dropna().drop_duplicates().rename(columns={year: "code", "H30": "kz30"})
        w["night"] = w["kz30"].map(h30_night).fillna(0) + 1e-9
        w["w"] = w["night"] / w.groupby("code")["night"].transform("sum")
    w["ckey"] = w["kz30"].map(kz)
    return w[["code", "kz30", "ckey", "w"]]


# ---------------------------------------------------------------- 図
def diverging_cmap(n_arm):
    from matplotlib.colors import LinearSegmentedColormap, ListedColormap
    blue, mid, red = "#2a78d6", "#f0efec", "#e34948"
    neg = LinearSegmentedColormap.from_list("n", [blue, mid])(np.linspace(0, 1, n_arm + 1))[:-1]
    pos = LinearSegmentedColormap.from_list("p", [mid, red])(np.linspace(0, 1, n_arm + 1))[1:]
    return ListedColormap(list(neg) + [LinearSegmentedColormap.from_list("m", [mid, mid])(0.5)] + list(pos))


def draw_map(ax, g, col, bins, labels, cmap, title, bounds=None, outline=None):
    from matplotlib.colors import BoundaryNorm
    norm = BoundaryNorm(bins, cmap.N)
    g.plot(ax=ax, column=col, cmap=cmap, norm=norm, edgecolor="#fcfcfb", linewidth=0.3,
           missing_kwds={"color": "#d9d9d6", "edgecolor": "#fcfcfb", "linewidth": 0.3})
    if outline is not None:
        outline.boundary.plot(ax=ax, color="#555", linewidth=0.6)
    if bounds is not None:
        ax.set_xlim(bounds[0], bounds[2]); ax.set_ylim(bounds[1], bounds[3])
    ax.set_title(title, fontsize=11, loc="left")
    ax.set_axis_off()


def make_figs(g, geom):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    from matplotlib.patches import Patch
    plt.rcParams["font.family"] = ["Yu Gothic", "Meiryo", "MS Gothic", "sans-serif"]
    os.makedirs(OUT_DIR, exist_ok=True)
    pref = geom.copy(); pref["pref"] = pref.index.str[:2]; pref = pref.dissolve(by="pref")
    ku = g[g["ckey"].str.startswith("131")]
    kb = ku.total_bounds; pad = 3000; kb = (kb[0] - pad, kb[1] - pad, kb[2] + pad, kb[3] + pad)

    # 図1: 14時滞留のシェア比（相対的な伸び）
    bins = [0, 0.67, 0.8, 0.91, 1.1, 1.25, 1.5, 99]
    labs = ["0.67倍未満", "0.67〜0.8", "0.8〜0.91", "0.91〜1.1（横ばい）", "1.1〜1.25", "1.25〜1.5", "1.5倍以上"]
    cmap = diverging_cmap(3)
    for col, ttl, fn in [("share_ratio_S63_H30", "S63（1988）→ H30（2018）", "b4_trend_share_S63_H30.png"),
                         ("share_ratio_H10_H30", "H10（1998）→ H30（2018）", "b4_trend_share_H10_H30.png")]:
        fig, axs = plt.subplots(1, 2, figsize=(14, 7.2), gridspec_kw={"width_ratios": [1.15, 1]})
        draw_map(axs[0], g, col, bins, labs, cmap, f"都市圏全体", outline=pref)
        draw_map(axs[1], g, col, bins, labs, cmap, "東京23区とその周辺", bounds=kb, outline=pref)
        for _, r in g.cx[kb[0]:kb[2], kb[1]:kb[3]].iterrows():
            if r["ckey"].startswith("131") or r["day_H30"] > 300000:
                p = r.geometry.representative_point()
                if kb[0] < p.x < kb[2] and kb[1] < p.y < kb[3]:
                    axs[1].annotate(r["city"], (p.x, p.y), fontsize=7, ha="center", va="center", color="#222")
        handles = [Patch(facecolor=cmap(i), edgecolor="#999", label=l) for i, l in enumerate(labs)]
        handles.append(Patch(facecolor="#d9d9d6", edgecolor="#999", label="比較できない"))
        fig.legend(handles=handles, loc="lower center", ncol=8, fontsize=9, frameon=False)
        fig.suptitle(f"14時台の滞留人口：都市圏に占めるシェアの変化 {ttl}\n"
                     "（1.0 = 都市圏全体と同じ伸び。平日・全目的・居住者と勤務者を含む。東京都市圏PT b-4 を H30 の市区町村に集計）",
                     fontsize=12, x=0.02, ha="left")
        fig.tight_layout(rect=(0, 0.05, 1, 0.92))
        fig.savefig(os.path.join(OUT_DIR, fn), dpi=120)
        plt.close(fig)

    # 図2: 昼夜比の変化（H30 ÷ S63）
    bins = [0, 0.67, 0.8, 0.91, 1.1, 1.25, 1.5, 99]
    labs = ["0.67倍未満", "0.67〜0.8", "0.8〜0.91", "0.91〜1.1（横ばい）", "1.1〜1.25", "1.25〜1.5", "1.5倍以上"]
    fig, axs = plt.subplots(1, 2, figsize=(14, 7.2), gridspec_kw={"width_ratios": [1.15, 1]})
    draw_map(axs[0], g, "dn_ratio_S63_H30", bins, labs, cmap, "都市圏全体", outline=pref)
    draw_map(axs[1], g, "dn_ratio_S63_H30", bins, labs, cmap, "東京23区とその周辺", bounds=kb, outline=pref)
    for _, r in g.cx[kb[0]:kb[2], kb[1]:kb[3]].iterrows():
        if r["ckey"].startswith("131") or r["day_H30"] > 300000:
            p = r.geometry.representative_point()
            if kb[0] < p.x < kb[2] and kb[1] < p.y < kb[3]:
                axs[1].annotate(r["city"], (p.x, p.y), fontsize=7, ha="center", va="center", color="#222")
    handles = [Patch(facecolor=cmap(i), edgecolor="#999", label=l) for i, l in enumerate(labs)]
    handles.append(Patch(facecolor="#d9d9d6", edgecolor="#999", label="比較できない"))
    fig.legend(handles=handles, loc="lower center", ncol=8, fontsize=9, frameon=False)
    fig.suptitle("昼夜比（14時台 ÷ 3時台の滞留人口）の変化 S63（1988）→ H30（2018）：H30 の昼夜比 ÷ S63 の昼夜比\n"
                 "（1 より大きい = 昼に人が集まる度合いが強まった。小さい = 夜の人口が増えた、または昼の人が減った）",
                 fontsize=12, x=0.02, ha="left")
    fig.tight_layout(rect=(0, 0.05, 1, 0.92))
    fig.savefig(os.path.join(OUT_DIR, "b4_trend_daynight_S63_H30.png"), dpi=120)
    plt.close(fig)


# ---------------------------------------------------------------- 本体
def main():
    os.makedirs(OUT_DIR, exist_ok=True)
    kz, names, geom = h30_zone_city()
    keinen = keinen_table()
    b4 = {y: load_past_b4(y) for y in YEARS[:3]}
    b4["H30"] = load_h30_b4(set(kz.index))
    h30_night = b4["H30"].set_index("code")[NIGHT]

    maplog, frames = [], []
    for y in YEARS:
        d = b4[y]
        w = zone_weights(y, keinen, kz, h30_night)
        j = d.merge(w, on="code", how="left")
        un = j[j["ckey"].isna()]
        split = w.groupby("code")["ckey"].nunique()
        sp_codes = split[split > 1].index
        print(f"{y}: ゾーン {len(d)}、対応表に無い {un['code'].nunique()}（14時滞留 {un[DAY].sum():,.0f}）、"
              f"複数の市区町村に配り分け {len(sp_codes)} ゾーン（14時滞留の "
              f"{d.loc[d['code'].isin(sp_codes), DAY].sum() / d[DAY].sum():.2%}）")
        if len(un):
            print("   対応表に無いゾーン:", sorted(un["code"].unique()))
        for c in TCOLS + ["p_unknown"]:
            j[c] = j[c] * j["w"]
        maplog.append(j[["code", "kz30", "ckey", "w", DAY]].assign(year=y, city=j["ckey"].map(names)))
        agg = j.dropna(subset=["ckey"]).groupby("ckey")[TCOLS + ["p_unknown"]].sum()
        agg["year"] = y
        frames.append(agg.reset_index())
    pd.concat(maplog).to_csv(os.path.join(OUT_DIR, "b4_trend_zone_mapping.csv"), index=False, encoding="utf-8-sig")

    panel = pd.concat(frames, ignore_index=True)
    panel["city"] = panel["ckey"].map(names)
    panel.to_csv(os.path.join(OUT_DIR, "b4_trend_city_panel.csv"), index=False, encoding="utf-8-sig")

    wide = panel.pivot(index="ckey", columns="year", values=[DAY, NIGHT, "p_unknown"])
    g = geom.copy()
    g["ckey"] = g.index
    for y in YEARS:
        g[f"day_{y}"] = wide[(DAY, y)].reindex(g.index)
        g[f"night_{y}"] = wide[(NIGHT, y)].reindex(g.index)
        g[f"unk_{y}"] = wide[("p_unknown", y)].reindex(g.index)
    full = g[[f"day_{y}" for y in YEARS]].notna().all(axis=1) & (g[[f"day_{y}" for y in YEARS]] > 0).all(axis=1)
    g["in_all4"] = full
    for y in YEARS:
        tot = g.loc[full, f"day_{y}"].sum()
        g[f"share_{y}"] = np.where(full, g[f"day_{y}"] / tot, np.nan)
        g[f"dn_{y}"] = np.where(full, g[f"day_{y}"] / g[f"night_{y}"], np.nan)
        print(f"{y}: 4回共通 {full.sum()} 市区町村の14時滞留 合計 {tot:,.0f}、3時 {g.loc[full, f'night_{y}'].sum():,.0f}")
    for a, b in [("S63", "H30"), ("H10", "H30"), ("S63", "H10"), ("H10", "H20"), ("H20", "H30")]:
        g[f"share_ratio_{a}_{b}"] = g[f"share_{b}"] / g[f"share_{a}"]
        g[f"day_ratio_{a}_{b}"] = g[f"day_{b}"] / g[f"day_{a}"]
        g[f"dn_ratio_{a}_{b}"] = g[f"dn_{b}"] / g[f"dn_{a}"]
    g["unk_rate_H20"] = g["unk_H20"] / (g["night_H20"] + 1)

    keep = ["ckey", "city", "absorbed", "in_all4"] + [c for c in g.columns if re.match(r"(day|night|share|dn|share_ratio|day_ratio|dn_ratio)_", c)] + ["unk_rate_H20"]
    tab = g[keep].sort_values("share_ratio_S63_H30", ascending=False)
    tab.to_csv(os.path.join(OUT_DIR, "b4_trend_city.csv"), index=False, encoding="utf-8-sig")
    if os.path.exists(OUT_GPKG):
        os.remove(OUT_GPKG)
    g[keep + ["geometry"]].reset_index(drop=True).to_file(OUT_GPKG, layer="city_b4_trend", driver="GPKG")

    show = ["city", "day_S63", "day_H30", "share_ratio_S63_H30", "share_ratio_H10_H30", "dn_S63", "dn_H30"]
    t = tab[tab["in_all4"] & (tab["day_H30"] >= 50000)][show]
    with pd.option_context("display.float_format", "{:,.2f}".format, "display.width", 200):
        print("\n伸びの大きい市区町村（14時滞留 5万人以上）\n", t.head(20).to_string(index=False))
        print("\n伸びの小さい市区町村\n", t.tail(20).to_string(index=False))
        r = tab[tab["in_all4"]]
        print("\n相関（シェア比 S63→H10 と H10→H30、順位）:",
              round(r["share_ratio_S63_H10"].rank().corr(r["share_ratio_H10_H30"].rank()), 3))
        print("相関（シェア比 H10→H20 と H20→H30、順位）:",
              round(r["share_ratio_H10_H20"].rank().corr(r["share_ratio_H20_H30"].rank()), 3))
        print("H20 時刻不明率と シェア比 H10→H20 の順位相関:",
              round(r["unk_rate_H20"].rank().corr(r["share_ratio_H10_H20"].rank()), 3))
    make_figs(g, geom)
    print("出力:", OUT_GPKG, OUT_DIR)


if __name__ == "__main__":
    main()
