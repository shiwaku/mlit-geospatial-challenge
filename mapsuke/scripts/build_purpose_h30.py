# -*- coding: utf-8 -*-
"""東京都市圏PT H30 の目的別集中量を、計画基本ゾーンと 500m メッシュに結合する（issue #5）。

コンペの「居住者・勤務者以外の来訪者」に近づけるため、私事目的と居住地で切り分けた集中量を作る。
QGIS は不要（geopandas で実行）: python -I scripts/build_purpose_h30.py

入力（data/raw）
  H30_data/c-2.xlsx           表c-2: ゾーン別・目的種類別・発着時間帯別・発生集中量
  H30_data_other/mesh-1.xlsx  目的別メッシュ別集中量（2分の1地域メッシュ＝約500m、9桁コード）
  H30_data_other/mesh-3.xlsx  居住地別（計画基本ゾーン）メッシュ別集中量（全目的）
  data/pt_h30_zones_b4.gpkg | kzone_b4（ゾーン形状、join_b4_kzone.py で作成）
出力
  data/pt_h30_purpose.gpkg | kzone_purpose   計画基本ゾーン × 目的別集中量（終日）＋私事の到着時刻別
  data/pt_h30_purpose.gpkg | mesh500_purpose 500m メッシュ × 目的別集中量＋居住地による来訪者指標
  data/pt_h30_c2_tidy.csv                    c-2 の縦持ち表（UTF-8、集計行含む）

目的の区分（c-2・mesh-1 共通）
  自宅－勤務 / 自宅－通学 / 自宅－業務 / 自宅－私事 / 帰宅 / 勤務・業務 / 私事 / 不明
  私事系 = 自宅－私事 + 私事（自宅以外から出た私事を含む）
  業務系 = 自宅－勤務 + 自宅－業務 + 勤務・業務

注意
  - 集中量は「着いたトリップ数」でストック（滞留）ではない。目的別の滞留人口は公開集計表には無い。
  - 平日のみ。H30 の抽出率は約1%。相対誤差の目安 rse_est = 21.5 / sqrt(トリップ数)（割合）
    （データ利用の手引きの目安 21,000トリップで約15%・5,000で約30% から逆算。5,000 未満は参考値）。
  - mesh-1 は mesh-3 より約1,800メッシュ少ない（mesh-1 に無いメッシュは目的別の値が欠損）。
"""
import math, os, sys
import numpy as np
import pandas as pd
import geopandas as gpd
from shapely.geometry import box

BASE = globals().get("BASE") or os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
RAW = os.path.join(BASE, "data", "raw")
ZONES_GPKG = os.path.join(BASE, "data", "pt_h30_zones_b4.gpkg")
OUT_GPKG = os.path.join(BASE, "data", "pt_h30_purpose.gpkg")
OUT_C2 = os.path.join(BASE, "data", "pt_h30_c2_tidy.csv")
CRS = "EPSG:6677"

PURPOSES = ["自宅－勤務", "自宅－通学", "自宅－業務", "自宅－私事", "帰宅", "勤務・業務", "私事", "不明"]
P_KEY = {"自宅－勤務": "h_work", "自宅－通学": "h_school", "自宅－業務": "h_biz", "自宅－私事": "h_shiji",
         "帰宅": "home", "勤務・業務": "work_biz", "私事": "shiji", "不明": "unknown"}
RSE_K = 21.5   # 相対誤差（割合）= RSE_K / sqrt(トリップ数)


def rse(x):
    x = np.asarray(x, dtype=float)
    with np.errstate(divide="ignore"):
        return np.where(x > 0, RSE_K / np.sqrt(x), np.nan)


def add_groups(df):
    """目的のまとめ列（私事系・業務系）と比率・誤差の目安を足す。"""
    df["shiji_all"] = df["h_shiji"] + df["shiji"]
    df["work_all"] = df["h_work"] + df["h_biz"] + df["work_biz"]
    df["non_home"] = df["total"] - df["home"]                    # 帰宅を除く到着
    df["shiji_share"] = df["shiji_all"] / df["non_home"].where(df["non_home"] > 0)
    df["work_share"] = df["work_all"] / df["non_home"].where(df["non_home"] > 0)
    df["rse_shiji"] = rse(df["shiji_all"])
    df["rse_total"] = rse(df["total"])
    return df


# ---------------------------------------------------------------- c-2
def read_c2():
    raw = pd.read_excel(os.path.join(RAW, "H30_data", "c-2.xlsx"), header=None, skiprows=4)
    raw = raw.iloc[:, 2:31]
    cols = ["area", "time"] + [f"{kind}|{p}" for kind in ("gen", "att", "genatt") for p in PURPOSES + ["計"]]
    raw.columns = cols
    raw["code"] = raw["area"].str.extract(r"^:(\S+)")[0]
    raw["area_name"] = raw["area"].str.replace(r"^:\S+\s*", "", regex=True)
    long = raw.melt(id_vars=["code", "area_name", "time"], value_vars=cols[2:], var_name="kp", value_name="trips")
    long[["measure", "purpose"]] = long["kp"].str.split("|", expand=True)
    long["measure"] = long["measure"].map({"gen": "発生量", "att": "集中量", "genatt": "発生集中量"})
    long = long.drop(columns="kp")[["code", "area_name", "time", "measure", "purpose", "trips"]]
    return raw, long


def time_key(t):
    t = str(t).translate(str.maketrans("０１２３４５６７８９", "0123456789"))
    if t.startswith("～"):
        return "a03_pre"
    if t.endswith("～"):
        return "a27_post"
    if t.endswith("時台"):
        return "a%02d" % int(t[:-2])
    return None


def kzone_table(raw, kzones):
    z = raw[raw["code"].str.fullmatch(r"\d{4}")].copy()
    z["kzone"] = z["code"].astype(int)
    z = z[z["kzone"].isin(kzones)]          # 8200 東京都 などの集計行を除く
    day = z[z["time"] == "合計"].set_index("kzone")
    out = pd.DataFrame(index=day.index)
    for p in PURPOSES:
        out[P_KEY[p]] = day[f"att|{p}"].astype(float)
    out["total"] = day["att|計"].astype(float)
    out = add_groups(out)
    # 私事系の到着時刻別（～3時, 3〜26時台, 27時～）
    z["tk"] = z["time"].map(time_key)
    zt = z[z["tk"].notna()].copy()
    zt["v"] = zt["att|自宅－私事"].astype(float) + zt["att|私事"].astype(float)
    hourly = zt.pivot_table(index="kzone", columns="tk", values="v", aggfunc="sum")
    order = ["a03_pre"] + ["a%02d" % h for h in range(3, 27)] + ["a27_post"]
    hourly = hourly.reindex(columns=order).fillna(0)
    hourly.columns = ["shiji_" + c for c in hourly.columns]
    out = out.join(hourly)
    out["shiji_peak_hour"] = hourly.iloc[:, 1:-1].values.argmax(axis=1) + 3
    return out.reset_index()


# ---------------------------------------------------------------- 500m メッシュ
def half_mesh_box(code):
    """2分の1地域メッシュ（9桁）の外形（経緯度）。末尾 1=南西, 2=南東, 3=北西, 4=北東。"""
    s = str(code)
    p, u, q, r, ss, t, h = int(s[0:2]), int(s[2:4]), int(s[4]), int(s[5]), int(s[6]), int(s[7]), int(s[8])
    lat0 = p / 1.5 + q * 5 / 60 + ss * 30 / 3600
    lon0 = u + 100 + r * 7.5 / 60 + t * 45 / 3600
    dlat, dlon = 15 / 3600, 22.5 / 3600
    lat0 += dlat if h in (3, 4) else 0
    lon0 += dlon if h in (2, 4) else 0
    return box(lon0, lat0, lon0 + dlon, lat0 + dlat)


def mesh_table(kz_geom):
    m1 = pd.read_excel(os.path.join(RAW, "H30_data_other", "mesh-1.xlsx"), header=3)
    m1 = m1.rename(columns={"メッシュ": "mesh", "合計": "total", **P_KEY})
    m3 = pd.read_excel(os.path.join(RAW, "H30_data_other", "mesh-3.xlsx"), header=3)
    m3.columns = ["mesh", "res", "trips"]
    m3["res_kzone"] = m3["res"].str.rstrip(":").astype(int)
    m3 = m3[m3["trips"] > 0]

    meshes = sorted(set(m1["mesh"]) | set(m3["mesh"]))
    g = gpd.GeoDataFrame({"mesh": meshes}, geometry=[half_mesh_box(c) for c in meshes], crs="EPSG:6668").to_crs(CRS)
    g["in_mesh1"] = g["mesh"].isin(m1["mesh"])
    # メッシュが属する計画基本ゾーン（重心で判定）
    cent = g.set_geometry(g.geometry.centroid)
    j = gpd.sjoin(cent[["mesh", "geometry"]], kz_geom[["kzone", "geometry"]], how="left", predicate="within")
    g["kzone"] = g["mesh"].map(j.drop_duplicates("mesh").set_index("mesh")["kzone"]).astype("Int64")

    g = g.merge(m1, on="mesh", how="left")
    g = add_groups(g)                       # mesh-1 に無いメッシュは欠損のまま

    # 居住地による来訪者指標（mesh-3、全目的）
    m3 = m3.merge(g[["mesh", "kzone"]], on="mesh", how="left")
    m3["outside"] = m3["res_kzone"] != m3["kzone"]
    kc = kz_geom.set_index("kzone").geometry.centroid
    mc = g.set_index("mesh").geometry.centroid
    m3["dist_km"] = [kc[r].distance(mc[m]) / 1000 if r in kc.index else np.nan
                     for r, m in zip(m3["res_kzone"], m3["mesh"])]
    agg = m3.groupby("mesh").agg(att_all=("trips", "sum"), n_res_zones=("res_kzone", "nunique"))
    agg["att_outside"] = m3[m3["outside"]].groupby("mesh")["trips"].sum()
    agg["att_outside"] = agg["att_outside"].fillna(0)
    agg["outside_share"] = agg["att_outside"] / agg["att_all"]
    # 居住地の多様性（シャノンエントロピー、自ゾーン居住者を除く）と平均距離（トリップ加重）
    out = m3[m3["outside"]].copy()
    out["w"] = out["trips"] / out.groupby("mesh")["trips"].transform("sum")
    out["plogp"] = -out["w"] * np.log(out["w"])
    out["wd"] = out["trips"] * out["dist_km"]
    out["tw"] = out["trips"].where(out["dist_km"].notna())
    o = out.groupby("mesh")[["plogp", "wd", "tw"]].sum(min_count=1)
    agg["res_entropy"] = o["plogp"]
    agg["res_mean_km"] = o["wd"] / o["tw"]
    g = g.merge(agg.reset_index(), on="mesh", how="left")
    g["rse_outside"] = rse(g["att_outside"])
    g["area_km2"] = g.geometry.area / 1e6
    return g


def run():
    kz = gpd.read_file(ZONES_GPKG, layer="kzone_b4")[["kzone", "area_km2", "geometry"]]
    kz["geometry"] = kz.geometry.make_valid()   # 元データに自己交差・退化リングがある
    raw, long = read_c2()
    long.to_csv(OUT_C2, index=False, encoding="utf-8")

    kt = kzone_table(raw, set(kz["kzone"]))
    kzp = kz.merge(kt, on="kzone", how="left")
    for c in ("shiji_all", "work_all", "non_home", "total"):
        kzp[c + "_dens"] = kzp[c] / kzp["area_km2"]

    mesh = mesh_table(kz)

    if os.path.exists(OUT_GPKG):
        os.remove(OUT_GPKG)
    kzp.to_file(OUT_GPKG, layer="kzone_purpose", driver="GPKG")
    mesh.to_file(OUT_GPKG, layer="mesh500_purpose", driver="GPKG")

    # ---- 検算
    chk = {}
    tot = raw[(raw["code"] == "8600") & (raw["time"] == "合計")]["att|計"].iloc[0]
    chk["c2_圏域内合計_集中量"] = int(tot)
    chk["kzone合計_集中量"] = int(kt["total"].sum())
    chk["kzone_未結合"] = int(kzp["total"].isna().sum())
    chk["mesh数"] = len(mesh)
    chk["mesh1に無いmesh"] = int((~mesh["in_mesh1"]).sum())
    chk["mesh1の合計の最小"] = int(mesh.loc[mesh["in_mesh1"], "total"].min())
    chk["ゾーン外mesh(重心が圏域外)"] = int(mesh["kzone"].isna().sum())
    chk["私事系_rse30%以下のmesh"] = int((mesh["rse_shiji"] <= 0.30).sum())
    chk["私事系_rse30%以下のkzone"] = int((kzp["rse_shiji"] <= 0.30).sum())
    return chk


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")
    for k, v in run().items():
        print(f"{k}: {v}")
