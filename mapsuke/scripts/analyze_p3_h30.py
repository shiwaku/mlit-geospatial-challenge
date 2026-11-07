# -*- coding: utf-8 -*-
"""P3（issue #11）: 来訪者の量を駅と人口で説明し、残差を地図にする（東京PT H30、500m メッシュ）。

仮説 H2: 来訪者の量の大部分は駅と人口で説明でき、残差に「質」が現れる。

目的変数  C = 私事系の集中量（自宅－私事＋私事、mesh-1、平日）。
説明変数（ベースライン = 駅＋人口）
  pop        メッシュの夜間人口（2020年国勢調査 500m メッシュ）
  pop_nbr    周辺人口: 自メッシュを含む 5×5 メッシュ（約2.5km四方）の人口合計
  riders_in  近くの駅の乗降客数（S12 2018、駅グループで合計）を、メッシュ重心からの距離でガウス減衰（σ=400m）させた合計
  riders_1km メッシュ重心から 1km 以内の駅の乗降客数
追加の説明変数（残差の「質」候補）
  emp_retail 卸売・小売業、emp_food 宿泊・飲食、emp_life 生活関連サービス・娯楽の従業者数（2016年経済センサス活動調査）
  emp_all    全産業の従業者数

評価
  - ポアソン回帰（対数リンク、説明変数は log(1+x)）。逸脱度の説明率 D² と、2次メッシュ（約10km四方）単位の
    空間ブロック 5 分割 CV の D²、順位相関（全件と、実測か予測が 5,136 以上のメッシュ）
  - 残差 = log((C+1)/(予測+1))。実測か予測が 5,136 以上（rse≦30%）のメッシュで上位・下位を出す
  - 鈴木（2014）の到着数原単位の再現: C ÷（小売＋飲食＋生活関連の従業者数）

実行: python -I scripts/analyze_p3_h30.py （QGIS 不要）
入力: data/pt_h30_purpose.gpkg | mesh500_purpose（build_purpose_h30.py）
      data/raw/estat_pop500_2020/tblT001141H*.txt   e-Stat 2020年国勢調査 2分の1地域メッシュ 人口（T001141）
      data/raw/estat_econ500_2016/tblT000918H*.txt  e-Stat 2016年経済センサス活動調査 2分の1地域メッシュ（T000918）
      data/raw/stations/S12-23/UTF-8/S12-23_NumberOfPassengers.geojson
      data/p1_h30.gpkg | kzone_p1（市区町村名に使う。analyze_p1_h30.py）
出力: data/p3_h30.gpkg | mesh500_p3、output/p3/*.csv・*.png
"""
import glob, os, sys
import numpy as np
import pandas as pd
import geopandas as gpd

BASE = globals().get("BASE") or os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
DATA = os.path.join(BASE, "data")
RAW = os.path.join(DATA, "raw")
OUT_DIR = os.path.join(BASE, "output", "p3")
OUT_GPKG = os.path.join(DATA, "p3_h30.gpkg")
CRS = "EPSG:6677"
SEED = 20261108
RSE_OK = 5136          # rse = 21.5/sqrt(x) ≦ 0.30 となる最小トリップ数

# 経済センサス T000918: 001〜018 事業所数、019〜036 従業者数（同じ産業順）
ECON = {"emp_all": "T000918019", "emp_retail": "T000918028", "emp_food": "T000918032", "emp_life": "T000918033",
        "emp_office": None}   # emp_office は後で 情報通信＋金融保険＋学術専門 の合計
ECON_OFFICE = ["T000918026", "T000918029", "T000918031"]


# ---------------------------------------------------------------- 入力
def read_estat(pattern, cols):
    fs = sorted(glob.glob(pattern))
    if not fs:
        raise FileNotFoundError(pattern)
    d = pd.concat([pd.read_csv(f, encoding="cp932", skiprows=[1], dtype=str) for f in fs], ignore_index=True)
    out = pd.DataFrame({"mesh": d["KEY_CODE"].astype(np.int64)})
    for c in cols:
        out[c] = pd.to_numeric(d[c], errors="coerce")       # 秘匿「*」は欠損 → 0 扱い
    return out.groupby("mesh").sum(min_count=1).fillna(0)


def mesh_rc(mesh):
    """2分の1地域メッシュコードを、南西を原点とする行・列の通し番号に直す（隣接計算用）。"""
    s = mesh.astype(str)
    p, u = s.str[0:2].astype(int), s.str[2:4].astype(int)
    q, r = s.str[4].astype(int), s.str[5].astype(int)
    ss, t, h = s.str[6].astype(int), s.str[7].astype(int), s.str[8].astype(int)
    row = ((p * 8 + q) * 10 + ss) * 2 + h.isin([3, 4]).astype(int)
    col = ((u * 8 + r) * 10 + t) * 2 + h.isin([2, 4]).astype(int)
    return row.values, col.values


def neighbor_sum(mesh, values, radius=2):
    """(2r+1)×(2r+1) メッシュの合計（自メッシュを含む）。values は mesh を index に持つ Series。"""
    r_all, c_all = mesh_rc(pd.Series(values.index))
    lut = dict(zip(zip(r_all, c_all), values.values))
    r0, c0 = mesh_rc(pd.Series(mesh))
    out = np.zeros(len(mesh))
    for dr in range(-radius, radius + 1):
        for dc in range(-radius, radius + 1):
            out += np.array([lut.get((a + dr, b + dc), 0.0) for a, b in zip(r0, c0)])
    return out


def stations():
    st = gpd.read_file(os.path.join(RAW, "stations", "S12-23", "UTF-8", "S12-23_NumberOfPassengers.geojson")).to_crs(CRS)
    st["riders"] = pd.to_numeric(st["S12_037"], errors="coerce").fillna(0)     # 2018年、重複行は 0
    st["x"], st["y"] = st.geometry.centroid.x, st.geometry.centroid.y
    g = st.groupby("S12_001g").agg(name=("S12_001", "first"), riders=("riders", "sum"), x=("x", "mean"), y=("y", "mean"))
    return gpd.GeoDataFrame(g, geometry=gpd.points_from_xy(g["x"], g["y"]), crs=CRS)


# ---------------------------------------------------------------- 回帰
# 集中量は拡大後のトリップ数で、小さいメッシュほど抽出誤差が大きい。log(1+C) の最小二乗だと誤差の大きい小メッシュに
# 引きずられるので、ポアソン回帰（対数リンク、IRLS）で当てる。大きいメッシュほど重く効く。
def design(g, cols):
    X = np.column_stack([np.log1p(g[c].values) for c in cols])
    return X


def poisson_fit(X, y, iters=50):
    mu_x, sd_x = X.mean(axis=0), X.std(axis=0)
    sd_x[sd_x == 0] = 1
    Z = np.column_stack([np.ones(len(X)), (X - mu_x) / sd_x])
    b = np.zeros(Z.shape[1])
    b[0] = np.log(y.mean())
    for _ in range(iters):
        eta = Z @ b
        mu = np.exp(eta)
        zt = eta + (y - mu) / mu
        WZ = Z * mu[:, None]
        b_new = np.linalg.solve(Z.T @ WZ, WZ.T @ zt)
        if np.max(np.abs(b_new - b)) < 1e-8:
            b = b_new
            break
        b = b_new
    # 元の尺度（log1p(x)）の係数に戻す
    beta = b[1:] / sd_x
    const = b[0] - (beta * mu_x).sum()
    return np.concatenate([[const], beta])


def poisson_predict(beta, X):
    return np.exp(np.column_stack([np.ones(len(X)), X]) @ beta)


def deviance(y, mu):
    with np.errstate(divide="ignore", invalid="ignore"):
        t = np.where(y > 0, y * np.log(y / mu), 0.0)
    return 2 * (t - (y - mu)).sum()


def d2(y, mu):
    """逸脱度の説明率（ポアソン回帰の R² に相当）。"""
    return 1 - deviance(y, mu) / deviance(y, np.full(len(y), y.mean()))


def block_cv(X, y, blocks, k=5, seed=SEED):
    rng = np.random.default_rng(seed)
    ub = np.unique(blocks)
    fold = dict(zip(ub, rng.permutation(len(ub)) % k))
    f = np.array([fold[b] for b in blocks])
    mu = np.empty(len(y))
    for i in range(k):
        tr, te = f != i, f == i
        mu[te] = poisson_predict(poisson_fit(X[tr], y[tr]), X[te])
    return mu


def r2_log(y, mu, mask):
    a, b = np.log(y[mask]), np.log(mu[mask])
    return 1 - ((a - b) ** 2).sum() / ((a - a.mean()) ** 2).sum()


def fit_models(g):
    feats = {
        "人口のみ": ["pop", "pop_nbr"],
        "駅のみ": ["riders_in", "riders_1km"],
        "駅＋人口（ベースライン）": ["pop", "pop_nbr", "riders_in", "riders_1km"],
        "＋全産業従業者": ["pop", "pop_nbr", "riders_in", "riders_1km", "emp_all"],
        "＋小売・飲食・生活関連": ["pop", "pop_nbr", "riders_in", "riders_1km", "emp_retail", "emp_food", "emp_life"],
        "＋小売・飲食・生活関連＋オフィス系": ["pop", "pop_nbr", "riders_in", "riders_1km", "emp_retail", "emp_food",
                                    "emp_life", "emp_office"],
    }
    y = g["C"].values.astype(float)
    blocks = g["mesh"].astype(str).str[:6].values
    # 残差や順位を読む対象: 実測かベースライン予測が大きいメッシュ（目的変数だけで選ぶと偏る）
    Xb = design(g, feats["駅＋人口（ベースライン）"])
    rel = (y >= RSE_OK) | (poisson_predict(poisson_fit(Xb, y), Xb) >= RSE_OK)
    rows, coefs = [], {}
    for name, cols in feats.items():
        X = design(g, cols)
        b = poisson_fit(X, y)
        mu = poisson_predict(b, X)
        mu_cv = block_cv(X, y, blocks)
        rows.append({"モデル": name, "説明変数": " ".join(cols),
                     "D2": round(d2(y, mu), 3), "空間ブロックCV_D2": round(d2(y, mu_cv), 3),
                     f"CV_spearman（実測か予測が{RSE_OK}以上）": round(
                         pd.Series(y[rel]).corr(pd.Series(mu_cv[rel]), method="spearman"), 3),
                     "CV_spearman（全件）": round(pd.Series(y).corr(pd.Series(mu_cv), method="spearman"), 3)})
        coefs[name] = pd.Series(b, index=["const"] + cols)
    return pd.DataFrame(rows), coefs, feats


# ---------------------------------------------------------------- 図
def plot_resid(g, fname, title):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    plt.rcParams["font.family"] = ["Yu Gothic", "Meiryo", "MS Gothic", "sans-serif"]
    fig, axes = plt.subplots(1, 2, figsize=(13, 6.5))
    for ax, sub, ttl in [(axes[0], g, "全メッシュ"), (axes[1], g[g["reliable"]], f"実測か予測が {RSE_OK:,} トリップ以上")]:
        g.plot(color="#eeeeee", ax=ax, linewidth=0)
        sub.plot(column="resid", cmap="RdBu_r", vmin=-1.5, vmax=1.5, ax=ax, linewidth=0, legend=True,
                 legend_kwds={"shrink": 0.6, "label": "log(実測/予測)（赤=駅・人口から見込むより多い）"})
        ax.set_title(ttl, fontsize=11)
        ax.set_axis_off()
    fig.suptitle(title, fontsize=13)
    fig.tight_layout()
    fig.savefig(os.path.join(OUT_DIR, fname), dpi=130)
    plt.close(fig)


def plot_scatter(g, fname):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    plt.rcParams["font.family"] = ["Yu Gothic", "Meiryo", "MS Gothic", "sans-serif"]
    fig, ax = plt.subplots(figsize=(6.5, 6))
    ok = g["reliable"]
    ax.scatter(g.loc[~ok, "pred_C"] + 1, g.loc[~ok, "C"] + 1, s=2, c="#bbbbbb", label="その他")
    ax.scatter(g.loc[ok, "pred_C"] + 1, g.loc[ok, "C"] + 1, s=6, c="#c0392b", label=f"実測か予測が{RSE_OK:,}以上")
    ax.set_xscale("log"); ax.set_yscale("log")
    lim = [1, g["C"].max() * 1.5]
    ax.plot(lim, lim, c="k", lw=0.8)
    ax.set_xlabel("予測 C（駅＋人口、ポアソン回帰）")
    ax.set_ylabel("実測 C（私事系集中量）")
    ax.legend()
    fig.tight_layout()
    fig.savefig(os.path.join(OUT_DIR, fname), dpi=130)
    plt.close(fig)


# ---------------------------------------------------------------- 本体
def run():
    os.makedirs(OUT_DIR, exist_ok=True)
    g = gpd.read_file(os.path.join(DATA, "pt_h30_purpose.gpkg"), layer="mesh500_purpose")
    g = g[g["in_mesh1"]].reset_index(drop=True)
    g["mesh"] = g["mesh"].astype(np.int64)
    g["C"] = g["shiji_all"]
    g["A"] = g["non_home"]

    pop = read_estat(os.path.join(RAW, "estat_pop500_2020", "tblT001141H*.txt"), ["T001141001"])["T001141001"]
    econ = read_estat(os.path.join(RAW, "estat_econ500_2016", "tblT000918H*.txt"),
                      [v for v in ECON.values() if v] + ECON_OFFICE)
    g["pop"] = g["mesh"].map(pop).fillna(0)
    g["pop_nbr"] = neighbor_sum(g["mesh"].values, pop, radius=2)
    for k, v in ECON.items():
        if v:
            g[k] = g["mesh"].map(econ[v]).fillna(0)
    g["emp_office"] = g["mesh"].map(econ[ECON_OFFICE].sum(axis=1)).fillna(0)
    g["emp_visit"] = g["emp_retail"] + g["emp_food"] + g["emp_life"]

    st = stations()
    # 駅の位置は路線線分の重心の平均で、メッシュ境界の内外が揺れる。メッシュ内の合計ではなく距離で減衰させた合計を使う
    cent = g.geometry.centroid
    sx, sy, sr = st.geometry.x.values, st.geometry.y.values, st["riders"].values
    cx, cy = cent.x.values, cent.y.values
    acc = np.zeros(len(g))
    for s0 in range(0, len(g), 2000):
        d2_ = (cx[s0:s0 + 2000, None] - sx[None]) ** 2 + (cy[s0:s0 + 2000, None] - sy[None]) ** 2
        acc[s0:s0 + 2000] = (sr[None] * np.exp(-d2_ / (2 * 400.0 ** 2))).sum(axis=1)
    g["riders_in"] = acc
    b = gpd.GeoDataFrame({"mesh": g["mesh"]}, geometry=cent.buffer(1000), crs=CRS)
    j1 = gpd.sjoin(st[["riders", "geometry"]], b, predicate="within")
    g["riders_1km"] = g["mesh"].map(j1.groupby("mesh")["riders"].sum()).fillna(0)

    kz = gpd.read_file(os.path.join(DATA, "p1_h30.gpkg"), layer="kzone_p1", columns=["kzone", "city"], ignore_geometry=True)
    g["city"] = g["kzone"].map(kz.set_index("kzone")["city"])

    models, coefs, feats = fit_models(g)
    base = "駅＋人口（ベースライン）"
    X = design(g, feats[base])
    g["pred_C"] = poisson_predict(coefs[base].values, X).round()
    g["resid"] = np.log((g["C"] + 1) / (g["pred_C"] + 1))       # 実測/予測 の対数比
    # 残差を読めるのは実測か予測が大きいメッシュ（目的変数だけで選ぶと残差が正に偏る）
    g["reliable"] = (g["C"] >= RSE_OK) | (g["pred_C"] >= RSE_OK)

    # 残差と「質」の候補の関係（信頼できるメッシュ）
    ok = g[g["reliable"]].copy()
    from scipy import stats
    cand = {"emp_retail": "小売・卸売の従業者", "emp_food": "宿泊・飲食の従業者", "emp_life": "生活関連・娯楽の従業者",
            "emp_office": "オフィス系（情報通信・金融・学術専門）の従業者", "work_share": "業務系の比率（PT）",
            "outside_share": "自ゾーン外に住む人の比率（PT、全目的）", "res_entropy": "居住地の多様性（PT）",
            "res_mean_km": "居住地からの平均距離（PT）"}
    rc = pd.DataFrame([{"候補": lab, "列": c, "n": int(ok[c].notna().sum()),
                        "spearman_残差": round(stats.spearmanr(ok[c], ok["resid"], nan_policy="omit").statistic, 3)}
                       for c, lab in cand.items()])

    # 鈴木（2014）の到着数原単位: 私事系の到着 ÷ 小売・飲食・生活関連の従業者
    g["unit_visit"] = g["C"] / g["emp_visit"].where(g["emp_visit"] >= 100)
    show = ["mesh", "city", "C", "pred_C", "resid", "pop", "pop_nbr", "riders_in", "riders_1km", "emp_visit",
            "emp_office", "unit_visit", "work_share"]
    ok = g[g["reliable"]]
    pos = ok.nlargest(30, "resid")[show]
    neg = ok.nsmallest(30, "resid")[show]
    unit_top = ok[ok["emp_visit"] >= 1000].nlargest(20, "unit_visit")[show]
    unit_low = ok[ok["emp_visit"] >= 1000].nsmallest(20, "unit_visit")[show]
    unit_q = g.loc[g["reliable"], "unit_visit"].describe(percentiles=[.1, .25, .5, .75, .9]).round(2)

    # ---- 保存
    if os.path.exists(OUT_GPKG):
        os.remove(OUT_GPKG)
    g[["mesh", "kzone", "city", "C", "A", "pop", "pop_nbr", "riders_in", "riders_1km", "emp_all", "emp_retail",
       "emp_food", "emp_life", "emp_office", "emp_visit", "pred_C", "resid", "reliable", "unit_visit", "rse_shiji",
       "work_share", "geometry"]].to_file(OUT_GPKG, layer="mesh500_p3", driver="GPKG")
    models.to_csv(os.path.join(OUT_DIR, "p3_models.csv"), index=False, encoding="utf-8-sig")
    pd.DataFrame(coefs).round(3).to_csv(os.path.join(OUT_DIR, "p3_coefs.csv"), encoding="utf-8-sig")
    rc.to_csv(os.path.join(OUT_DIR, "p3_resid_candidates.csv"), index=False, encoding="utf-8-sig")
    for n, d in [("resid_pos", pos), ("resid_neg", neg), ("unit_top", unit_top), ("unit_low", unit_low)]:
        d.to_csv(os.path.join(OUT_DIR, f"p3_{n}.csv"), index=False, encoding="utf-8-sig")
    plot_resid(g, "p3_resid_map.png", "私事系集中量の残差（駅＋人口で説明しきれない分、500mメッシュ）")
    plot_scatter(g, "p3_pred_obs.png")
    return dict(models=models, coefs=pd.DataFrame(coefs).round(3), resid_candidates=rc, resid_pos=pos,
                resid_neg=neg, unit_quantiles=unit_q, unit_top=unit_top, unit_low=unit_low)


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")
    pd.set_option("display.width", 250, "display.max_columns", 30)
    r = run()
    for k, v in r.items():
        print(f"\n==== {k}")
        print(v.round(3).to_string() if isinstance(v, (pd.DataFrame, pd.Series)) else v)
