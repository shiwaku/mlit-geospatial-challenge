# -*- coding: utf-8 -*-
"""P4（issue #12）: 私事来訪の「量」と「消費額」で計画基本ゾーンを類型化し、着施設構成で特徴づける（東京PT H30）。

仮説 H3: 「集まる」と「にぎわいを生む」は別の現象で、消費額が大きい場所には共通の特徴がある。

入力（data/raw/H30_data_other）
  4-4.xlsx  表4-4 目的別消費額別発生集中量（計画基本ゾーン × 目的 × 消費額6区分）
  4-2.xlsx  表4-2 目的別発生集中量の発着施設構成（計画基本ゾーン × 目的 × 着施設16区分）
  data/p1_h30.gpkg | kzone_p1（形状・市区町村名・私事系密度。analyze_p1_h30.py）
出力
  data/p4_h30.gpkg | kzone_p4、output/p4/*.csv・*.png

定義
  私事系 = 自宅－私事 ＋ その他私事（c-2 の「私事」と同じ）の集中量（着いたトリップ）
  消費額は区分のみ。不明を除き、区分の代表値（0, 500, 3,000, 7,500, 15,000 円）で 1トリップあたりの平均を概算する。
  高消費率 = 1,001円以上の割合（不明を除く）。10,001円～ の代表値は仮置きなので、主指標は高消費率にする。
  来訪の量 = 私事系の集中量の密度（/km²）
  4象限 = 量と高消費率のそれぞれ中央値で分ける（私事系の相対誤差 30% 以内のゾーンだけで中央値を決める）
  標本の目安: rse = 21.5/√x から有効標本数 n_eff ≈ x / 462。比率の標準誤差 ≈ √(p(1−p)/n_eff)
"""
import os, sys
import numpy as np
import pandas as pd
import geopandas as gpd
from scipy import stats

BASE = globals().get("BASE") or os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
DATA = os.path.join(BASE, "data")
RAW = os.path.join(DATA, "raw", "H30_data_other")
OUT_DIR = os.path.join(BASE, "output", "p4")
OUT_GPKG = os.path.join(DATA, "p4_h30.gpkg")
SHIJI = ["自宅－私事", "その他私事"]
RSE_OK = 5136
N_EFF_DIV = 21.5 ** 2   # ≈ 462

SPEND = ["0円", "1～1000円", "1001～5000円", "5001～10000円", "10001円～", "不明"]
SPEND_KEY = {"0円": "sp0", "1～1000円": "sp1k", "1001～5000円": "sp5k", "5001～10000円": "sp10k", "10001円～": "sp10kp",
             "不明": "sp_na"}
SPEND_MID = {"sp0": 0, "sp1k": 500, "sp5k": 3000, "sp10k": 7500, "sp10kp": 15000}
FAC_KEY = {"住宅・寮": "f_home", "学校・保育・文化施設": "f_school", "医療施設": "f_medical", "高齢福祉施設": "f_welfare",
           "公園・自然地・スポーツ施設等": "f_park", "その他の生活系施設": "f_life_other", "大規模小売店": "f_retail_l",
           "小規模小売店": "f_retail_s", "宿泊施設・ホテル": "f_hotel", "飲食施設": "f_food",
           "アミューズメント施設": "f_amuse", "その他の商業系施設": "f_comm_other", "事務所・会社・銀行": "f_office",
           "官公庁施設": "f_gov", "その他の業務系・工業系施設": "f_ind", "不明": "f_na"}
FAC_LABEL = {v: k for k, v in FAC_KEY.items()}
QUAD = {"HH": "多く来て消費も大きい", "HL": "多く来るが消費は小さい", "LH": "来訪は少ないが消費は大きい",
        "LL": "来訪も消費も小さい"}


def zone_code(s):
    return pd.to_numeric(s.astype(str).str.extract(r"^:(\d{4}):")[0], errors="coerce")


def read_spend():
    x = pd.read_excel(os.path.join(RAW, "4-4.xlsx"), header=None, skiprows=4)
    # 列: 目的, 地域, 発生量7列, 集中量7列, 発生集中量7列 → 集中量（9〜14列目）
    d = pd.DataFrame({"purpose": x[0], "kzone": zone_code(x[1])})
    for i, s in enumerate(SPEND):
        d[SPEND_KEY[s]] = pd.to_numeric(x[9 + i], errors="coerce")
    d = d[d["purpose"].isin(SHIJI) & d["kzone"].notna()]
    return d.groupby("kzone")[list(SPEND_KEY.values())].sum()


def read_facility():
    x = pd.read_excel(os.path.join(RAW, "4-2.xlsx"), header=None, skiprows=4)
    # 列: 地域, 目的, 発生量17列, 集中量17列, 発生集中量17列 → 集中量（19〜34列目）
    d = pd.DataFrame({"kzone": zone_code(x[0]), "purpose": x[1]})
    for i, k in enumerate(FAC_KEY.values()):
        d[k] = pd.to_numeric(x[19 + i], errors="coerce")
    d = d[d["purpose"].isin(SHIJI) & d["kzone"].notna()]
    return d.groupby("kzone")[list(FAC_KEY.values())].sum()


def plot_quadrant(g, fname):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    plt.rcParams["font.family"] = ["Yu Gothic", "Meiryo", "MS Gothic", "sans-serif"]
    colors = {"HH": "#c0392b", "HL": "#e67e22", "LH": "#2980b9", "LL": "#95a5a6"}
    fig, axes = plt.subplots(1, 2, figsize=(14, 6.5), gridspec_kw={"width_ratios": [1, 1.1]})
    ax = axes[0]
    ok = g["reliable"]
    for q, c in colors.items():
        s = g[ok & (g["quad"] == q)]
        ax.scatter(s["C_dens"], s["high_spend"], s=10, c=c, label=f"{q} {QUAD[q]}（{len(s)}）")
    ax.scatter(g.loc[~ok, "C_dens"], g.loc[~ok, "high_spend"], s=6, c="#dddddd", label="誤差大（参考）")
    ax.set_xscale("log")
    ax.axvline(g.attrs["x_med"], c="k", lw=0.6)
    ax.axhline(g.attrs["y_med"], c="k", lw=0.6)
    ax.set_xlabel("私事系の集中量密度（トリップ/km²、対数）")
    ax.set_ylabel("1,001円以上の割合（私事系、不明を除く）")
    ax.legend(fontsize=8, loc="lower right")
    for _, r in g[ok].nlargest(8, "C_dens").iterrows():
        ax.annotate(r["city"], (r["C_dens"], r["high_spend"]), fontsize=7)
    ax = axes[1]
    g.plot(color=g["quad"].map(colors).where(g["reliable"], "#eeeeee"), ax=ax, linewidth=0.1, edgecolor="white")
    ax.set_axis_off()
    ax.set_title("4象限（灰色は誤差大）")
    fig.suptitle("私事来訪の量 × 消費額（計画基本ゾーン、東京PT H30 平日）", fontsize=13)
    fig.tight_layout()
    fig.savefig(os.path.join(OUT_DIR, fname), dpi=130)
    plt.close(fig)


def run():
    os.makedirs(OUT_DIR, exist_ok=True)
    kz = gpd.read_file(os.path.join(DATA, "p1_h30.gpkg"), layer="kzone_p1",
                       columns=["kzone", "city", "area_km2", "C", "work_share", "shiji_all", "rse_shiji"])
    kz = kz.rename(columns={"C": "C_dens"})
    sp = read_spend()
    fa = read_facility()
    g = kz.merge(sp, left_on="kzone", right_index=True, how="left").merge(fa, left_on="kzone", right_index=True, how="left")

    keys = list(SPEND_MID)
    g["sp_known"] = g[keys].sum(axis=1)
    g["sp_total"] = g["sp_known"] + g["sp_na"]
    g["spend_na_share"] = g["sp_na"] / g["sp_total"]
    g["high_spend"] = (g["sp5k"] + g["sp10k"] + g["sp10kp"]) / g["sp_known"]
    g["zero_spend"] = g["sp0"] / g["sp_known"]
    g["mean_spend"] = sum(g[k] * v for k, v in SPEND_MID.items()) / g["sp_known"]
    g["spend_dens"] = g["mean_spend"] * g["C_dens"]          # 面積あたりの消費額（概算、円/km²/日）
    n_eff = g["sp_known"] / N_EFF_DIV
    g["high_spend_se"] = np.sqrt(g["high_spend"] * (1 - g["high_spend"]) / n_eff)

    fcols = list(FAC_KEY.values())
    ftot = g[fcols].sum(axis=1)
    for c in fcols:
        g["s_" + c] = g[c] / ftot
    g["s_shop"] = g["s_f_retail_l"] + g["s_f_retail_s"]
    g["s_food_amuse"] = g["s_f_food"] + g["s_f_amuse"] + g["s_f_hotel"]
    g["s_daily"] = g["s_f_medical"] + g["s_f_welfare"] + g["s_f_home"] + g["s_f_school"]
    # 施設の種類の多様性（シャノン、不明を除く）
    P = g[[c for c in fcols if c != "f_na"]].div(g[[c for c in fcols if c != "f_na"]].sum(axis=1), axis=0)
    g["fac_entropy"] = -(P * np.log(P.where(P > 0))).sum(axis=1)

    g["reliable"] = g["shiji_all"] >= RSE_OK
    ok = g[g["reliable"]]
    x_med, y_med = ok["C_dens"].median(), ok["high_spend"].median()
    g.attrs.update(x_med=x_med, y_med=y_med)
    g["quad"] = np.where(g["C_dens"] >= x_med, "H", "L")
    g["quad"] = g["quad"] + np.where(g["high_spend"] >= y_med, "H", "L")
    # 消費側の分類が標本誤差に対して確かか（中央値から 1.96SE 以上離れている）
    g["spend_side_sure"] = (g["high_spend"] - y_med).abs() >= 1.96 * g["high_spend_se"]

    # ---- 検算: 4-4 と 4-2 の私事系の合計、c-2 との一致
    chk = pd.Series({"4-4 私事系合計（ゾーン）": int(g["sp_total"].sum()), "4-2 私事系合計（ゾーン）": int(ftot.sum()),
                     "c-2 私事系合計（ゾーン）": int(g["shiji_all"].sum()),
                     "消費額不明の割合": round(g["sp_na"].sum() / g["sp_total"].sum(), 3),
                     "高消費率の中央値": round(y_med, 3), "高消費率の標準誤差の中央値（信頼ゾーン）": round(ok["high_spend_se"].median(), 3),
                     "信頼ゾーン数": int(g["reliable"].sum()),
                     "高消費率の四分位範囲（信頼ゾーン）": round(ok["high_spend"].quantile(.75) - ok["high_spend"].quantile(.25), 3),
                     "消費側の分類が確かなゾーン（信頼ゾーン中）": int(g.loc[g["reliable"], "spend_side_sure"].sum())})

    # ---- 量と消費の関係
    ok = g[g["reliable"]]
    rel = pd.DataFrame([
        {"指標の組": "量 × 高消費率", "spearman": stats.spearmanr(ok["C_dens"], ok["high_spend"]).statistic},
        {"指標の組": "量 × 平均消費額（概算）", "spearman": stats.spearmanr(ok["C_dens"], ok["mean_spend"]).statistic},
        {"指標の組": "量 × 消費額密度", "spearman": stats.spearmanr(ok["C_dens"], ok["spend_dens"]).statistic},
    ]).round(3)

    # ---- 高消費率と着施設構成・業務比率の順位相関
    attrs = {**{"s_" + k: FAC_LABEL[k] for k in fcols if k != "f_na"},
             "s_shop": "小売（大規模＋小規模）", "s_food_amuse": "飲食＋アミューズメント＋宿泊",
             "s_daily": "住宅・学校・医療・福祉", "fac_entropy": "施設の多様性", "work_share": "業務系の比率（P1）"}
    fac_rel = pd.DataFrame([{"属性": lab, "列": c,
                             "spearman_高消費率": stats.spearmanr(ok[c], ok["high_spend"], nan_policy="omit").statistic,
                             "spearman_量": stats.spearmanr(ok[c], ok["C_dens"], nan_policy="omit").statistic}
                            for c, lab in attrs.items()]).round(3).sort_values("spearman_高消費率", ascending=False)

    # ---- 象限ごとの着施設構成（トリップ加重）
    show_f = ["f_retail_l", "f_retail_s", "f_food", "f_amuse", "f_hotel", "f_park", "f_medical", "f_welfare",
              "f_home", "f_school", "f_office", "f_life_other", "f_comm_other"]
    qs = ok.groupby("quad")[fcols].sum()
    qs = qs.div(qs.sum(axis=1), axis=0)[show_f].rename(columns=FAC_LABEL)
    qsum = ok.groupby("quad").agg(ゾーン数=("kzone", "size"), 量の中央値=("C_dens", "median"),
                                  高消費率の中央値=("high_spend", "median"), 平均消費額の中央値=("mean_spend", "median"),
                                  業務比率の中央値=("work_share", "median"))
    quad_tab = qsum.join(qs).round(3)
    quad_tab.index = [f"{q} {QUAD[q]}" for q in quad_tab.index]

    show = ["kzone", "city", "C_dens", "high_spend", "high_spend_se", "mean_spend", "s_shop", "s_food_amuse",
            "s_f_medical", "s_f_park", "work_share", "quad"]
    lists = {
        "hh_top": ok[ok["quad"] == "HH"].nlargest(20, "spend_dens")[show],
        "hl_top": ok[ok["quad"] == "HL"].nlargest(20, "C_dens")[show],
        "lh_top": ok[ok["quad"] == "LH"].nlargest(20, "high_spend")[show],
        "spend_top": ok.nlargest(20, "high_spend")[show],
    }

    # ---- 保存
    if os.path.exists(OUT_GPKG):
        os.remove(OUT_GPKG)
    out_cols = (["kzone", "city", "area_km2", "C_dens", "shiji_all", "rse_shiji", "reliable", "quad", "spend_side_sure", "high_spend",
                 "high_spend_se", "zero_spend", "mean_spend", "spend_dens", "spend_na_share", "work_share", "fac_entropy",
                 "s_shop", "s_food_amuse", "s_daily"] + ["s_" + c for c in fcols] + list(SPEND_KEY.values()) + ["geometry"])
    g[out_cols].to_file(OUT_GPKG, layer="kzone_p4", driver="GPKG")
    chk.to_csv(os.path.join(OUT_DIR, "p4_check.csv"), encoding="utf-8-sig", header=["値"])
    rel.to_csv(os.path.join(OUT_DIR, "p4_volume_vs_spend.csv"), index=False, encoding="utf-8-sig")
    fac_rel.to_csv(os.path.join(OUT_DIR, "p4_facility_corr.csv"), index=False, encoding="utf-8-sig")
    quad_tab.to_csv(os.path.join(OUT_DIR, "p4_quadrants.csv"), encoding="utf-8-sig")
    for k, d in lists.items():
        d.to_csv(os.path.join(OUT_DIR, f"p4_{k}.csv"), index=False, encoding="utf-8-sig")
    plot_quadrant(g, "p4_quadrants.png")
    return dict(check=chk, volume_vs_spend=rel, facility_corr=fac_rel, quadrants=quad_tab, **lists)


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")
    pd.set_option("display.width", 250, "display.max_columns", 30)
    for k, v in run().items():
        print(f"\n==== {k}")
        print(v.round(3).to_string())
