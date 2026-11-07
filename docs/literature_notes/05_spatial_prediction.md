# 人流・滞在人口の空間予測モデル：空間汎化と変化予測（05）

対象：メッシュ／ゾーン単位で滞在人口・来訪者・都市の活気（urban vitality）を、建物・道路網・POI・国土数値情報などのオープン地理空間特徴量から予測する研究。重点は (a) 空間CVと未観測地域・都市への転移、(b) 経年変化の予測、(c) 使われるモデル、(d) 道路網・POIの特徴量設計。MLIT 地理空間情報データチャレンジ（第1回・第2回）の解法記事も含める。

凡例：【H2】量と質のどちらで説明できるか ／【H4】経年変化 ／【H5】空間予測・汎化 ／【CMP】コンペのモデリング実務
検証状況：✅＝今回の調査で書誌・内容を検索結果やページ取得で確かめた ／ ⚠️＝書誌は既知情報で、今回はDOIリンクのみ確認または未確認（本文の数値は引用しない）

---

## Q1. 細かいグリッドで滞在・来訪人口を予測するのに効く特徴量とモデルは何か。空間的にどこまで汎化するか

### Takeaway
道路網の中心性（betweenness・closeness）や交差点密度、POIの密度と多様性、建物・人口の密度が、どの研究でも上位の説明変数になる。モデルは勾配ブースティング（XGBoost/LightGBM）とSHAPの組み合わせが主流で、比較対象としてMGWRや空間ラグモデルが使われる。ただし、変数の効き方は都市やグリッドの大きさで変わるという報告が多い。未観測の都市への転移を厳密に検証した研究は少なく、検証している研究（Deep Gravity、衛星画像によるフロー予測、cross-city transfer）でも精度の低下が前提になっている。

### Cited Findings（文献リスト）

**1. De Nadai, M., Staiano, J., Larcher, R., Sebe, N., Quercia, D., Lepri, B. (2016). "The Death and Life of Great Italian Cities: A Mobile Phone Data Perspective." Proc. 25th International Conference on World Wide Web (WWW 2016), pp. 413–423. arXiv:1603.04012** ✅【H2】【H5】
- データ：イタリア6都市（arXiv版はボローニャ、フィレンツェ、ミラノ、パレルモ、ローマ、トリノ。MIT Technology Reviewの記事とは都市名が一部食い違う）。携帯の基地局活動量を活気の代理指標とし、国勢調査の土地利用・社会人口データとOpenStreetMapを説明変数に使う — [arXiv](https://www.arxiv.org/pdf/1603.04012), [MIT Tech Review](https://www.technologyreview.com/2016/03/24/161419/data-mining-reveals-the-four-urban-conditions-that-create-vibrant-city-life/amp/)
- 手法と結果：ジェイコブズの4条件（用途の混合、小さな街区、古い建物の混在、密度）を操作化して検証し、「4条件はイタリアの都市でも成り立つ」と結論。サードプレイスの存在と小さな街区が活動量と有意に相関し、人の密度も重要だった — [ar5iv](https://ar5iv.arxiv.org/html/1603.04012), [Emergent Mind要約](https://www.emergentmind.com/papers/1603.04012)
- コード公開：[GitHub denadai2/jacobs_urban_planning](https://github.imc.re/denadai2/jacobs_urban_planning)
- 使い道：H2（密度という「量」と、用途混合や街区形状という「質」の両方が効く）の古典的根拠。特徴量設計の雛形にもなる。

**2. Porta, S., Strano, E., Iacoviello, V., Messora, R., Latora, V., Cardillo, A., Wang, F., Scellato, S. (2009). "Street centrality and densities of retail and services in Bologna, Italy." Environment and Planning B: Planning and Design, 36(3), 450–465. DOI: 10.1068/b34098** ✅【H2】【H5】
- 手法：Multiple Centrality Assessment（closeness、betweenness、straightness）。道路網と店舗点の両方をカーネル密度に変換して共通の空間単位にそろえる。対象は道路セグメント7,191本、交差点5,448か所、2003年の1階店舗・サービス — [SAGE](https://journals.sagepub.com/doi/abs/10.1068/b34098), [著者PDF](https://webspace.maths.qmul.ac.uk/v.latora/porta_bologna_450_epb09.pdf)
- 結果：店舗・サービスは中心性の高い場所に集まり、global betweennessと最も強く相関し、global closenessがそれに続く。バルセロナとの比較でも同じ傾向が出た — [RePEc](https://ideas.repec.org/a/sae/envirb/v36y2009i3p450-465.html), [Strathprints](https://strathprints.strath.ac.uk/id/eprint/18474)
- 使い道：(d) 道路網の中心性をカーネル密度でメッシュに割り当てるという特徴量設計の根拠。

**3. Li, Z. (2022). "Extracting spatial effects from machine learning model using local interpretation method: An example of SHAP and XGBoost." Computers, Environment and Urban Systems, 96, 101845. DOI: 10.1016/j.compenvurbsys.2022.101845** ✅【H5】【H2】
- 手法：シミュレーションデータで、XGBoost＋SHAPを空間ラグモデル（SLM）およびMGWRと比べる。実データの事例はシカゴの配車サービス（ride-hailing）の需要 — [Glasgow eprints](https://eprints.gla.ac.uk/273108), [Turing](https://atiro.turing.ac.uk/esploro/outputs/journalArticle/Extracting-spatial-effects-from-machine-learning/9921254809548)
- 結果：SHAPで読み解いたXGBoostは、SLMやMGWRと同程度の空間効果を取り出せた。後継のGeoShapleyは、どの機械学習モデルにも使えるかたちで「位置そのものの寄与」を分離する — [arXiv 2312.03675](https://arxiv.org/pdf/2312.03675)
- 使い道：(c) GBM＋SHAPをMGWRの代わり、あるいは補完として使う理屈。座標を特徴量に入れたときの位置効果を解釈するのにも使える。

**4. XGBoost-SHAPで都市の活気を分析する研究群（中国の都市、グリッド・街区単位）** ✅（個別の書誌は要確認）【H2】【H5】
- 成都・重慶の研究は、XGBoost-SHAPで非線形効果と閾値効果を調べ、グリッドの大きさと都市を変えて比べた。最も重要な変数は成都では交差点密度、重慶では商業アクセシビリティで、変数の効き方は都市やグリッドの大きさで変わる — [Preprints.org 202502.2100](https://www.preprints.org/manuscript/202502.2100)（※検索スニペットから得た情報。著者名と最終掲載誌は未確認）
- 同じ系統の研究に、携帯シグナリングとPOI・ストリートビューを組み合わせてMGWRとXGBoost-SHAPを併用したフフホトの研究や、オープンデータだけで街区単位の閾値効果を示した鄭州の研究がある — [MDPI Buildings 15(8):1372](https://mdpi.com/2075-5309/15/8/1372), [MDPI Land 15(5):844](https://www.mdpi.com/2073-445X/15/5/844/htm)（※どのURLがどの都市の研究かは本文で未照合）
- 使い道：H5への注意喚起。説明変数の重要度は都市やスケールで入れ替わるので、未観測の地域へ外挿すると分布のずれ（shift）が起きる。

**5. Simini, F., Barlacchi, G., Luca, M., Pappalardo, L. (2021). "A Deep Gravity model for mobility flows generation." Nature Communications, 12, 6576. DOI: 10.1038/s41467-021-26752-4** ⚠️【H5】
- 書誌は既知情報で、今回は本文を取得していない — [DOI](https://doi.org/10.1038/s41467-021-26752-4)
- 内容（既知情報。数値は引用しない）：OSMから作ったPOI・土地利用・道路の特徴量を入力にして、深層ニューラルネットで重力モデルを一般化し、OD（起点・終点）フローを生成する。学習に使っていない地域でフローを生成できるかを検証し、古典的な重力モデルより精度が高かったと報告している。
- 使い道：(c)(d) OSMの特徴量だけで未観測地域の人流を生成するという枠組みの代表例。ただし予測対象はODフローで、メッシュの滞在人口とは目的変数が違う。

**6. （著者は未確認）"Predicting human mobility flows in cities using deep learning on satellite imagery." Nature Communications (2025). DOI: 10.1038/s41467-025-65373-z** ⚠️（タイトルと掲載誌は検索で確認。本文は取得できなかった）【H5】
- 検索スニペットによれば、衛星画像の特徴量、またはOSMのPOIから作った社会経済特徴量で人流フローを予測する。携帯データのない新しい都市域にも適用でき、未観測の都市環境への空間転移性を主張している — [Nature Communications](https://www.nature.com/articles/s41467-025-65373-z)
- 使い道：Deep Gravityの後継的な研究で、H5の近年の到達点。精度の数値は未確認。

**7. Stevens, F. R., Gaughan, A. E., Linard, C., Tatem, A. J. (2015). "Disaggregating census data for population mapping using random forests with remotely-sensed and ancillary data." PLoS ONE, 10(2), e0107042. DOI: 10.1371/journal.pone.0107042** ⚠️【H5】
- 書誌は既知情報 — [DOI](https://doi.org/10.1371/journal.pone.0107042)
- 内容（既知情報）：WorldPopの手法。ランダムフォレストで行政区の人口密度を学習し、道路・建物・土地被覆・夜間光などのグリッド特徴量で100mグリッドに配分する。
- 使い道：(c) 「ゾーン値を学習し、グリッドの特徴量で予測する」というRFの定番手順。夜間人口を対象にした研究なので、滞在人口とは目的変数が違う点に注意。

**8. Wang, L., Geng, X., Ma, X., Liu, F., Yang, Q. (2019). "Cross-City Transfer Learning for Deep Spatio-Temporal Prediction." Proc. IJCAI 2019 (RegionTrans). DOI: 10.24963/ijcai.2019/262** ⚠️【H5】
- 書誌は既知情報 — [DOI](https://doi.org/10.24963/ijcai.2019/262)
- 内容（既知情報）：データの多い都市で学習した時空間クロスフロー予測モデルを、データの少ない都市へ転移する。補助データ（POIなど）で都市間の地域どうしを対応づける。
- 関連研究：POI埋め込みで複数都市の人流を転移する研究 — [ACM TIST 2020](https://dl.acm.org/doi/fullHtml/10.1145/3416914)。カテゴリ別POIの分布マップを入力にした、グリッド人口推定のone-shot転移 — [arXiv 2108.06228](https://arxiv.org/pdf/2108.06228)
- 使い道：「未観測の都市」への転移では、POIの構成が似た地域どうしを対応づけるのが基本戦略になる。

**9. 中本拓也, 甘粕裕明, 土田冴恵子, 田﨑智之, 大村珠太郎, 生富直孝, 堀田剛士, 煤田遼祐, 田中啓, 陣内寛大 (2025). 「機械学習を用いた滞在人口推定モデルの開発とその活用可能性について：東京都臨海部エリアを対象として」都市計画報告集, 24(2), 348–353. DOI: 10.11361/reportscpij.24.2_348** ✅【H5】【H4】
- データ：GEOTRAのActivity Data（携帯基地局とGPSに基づく非集計の人流データ）。学習地域は江東区と中央区で、後から港区を追加した — [J-STAGE](https://www.jstage.jst.go.jp/article/reportscpij/24/2/24_348/_article/-char/ja)
- 手法と結果：建物開発の単位に当たる6次メッシュで滞在人口を推定するモデル。特徴量選択で一定の精度を得て、港区を学習に加えるとさらに改善した。虎ノ門・麻布台の再開発地区に当てはめて妥当な精度を確認し、開発の初期段階で使えると主張している。アルゴリズム名、検証方法、精度の数値は要旨に書かれていない — [J-STAGE](https://www.jstage.jst.go.jp/article/reportscpij/24/2/24_348/_article/-char/ja)
- 使い道：本コンペに最も近い国内事例（GPS人流、細かいメッシュ、未観測の再開発地区への適用）。学習地域を増やすと汎化が上がったという結果は、H5の「学習地域の多様性」の論点を支える。全文PDFの確認を推奨する。

**10. 国内の関連研究（要旨レベルで確認）** ✅【H5】
- マイクロジオデータを統合して、建物用途別のメッシュ入込人口を推計した研究（モバイル空間統計と都市計画基礎調査を統合）。土木学会論文集D3, 72(5) — [J-STAGE](https://www.jstage.jst.go.jp/article/jscejipm/72/5/72_I_515/_article/-char/ja/)
- メッシュ統計人口と個人の移動軌跡データを統合して、建物内の滞在人数を推定した研究（河森・西村・赤木, DEIM Forum 2022 D24-2） — [PDF](https://proceedings-of-deim.github.io/DEIM2022/papers/D24-2.pdf)
- 使い道：「建物の床面積・用途 → メッシュ滞在人口」という配分の考え方。国土数値情報と建物データを特徴量にする根拠になる。

### Inferences
- 本コンペ向けの特徴量の優先順位は次のとおり。道路網の中心性と交差点密度（Porta 2009、成都の研究）、POIの密度と多様性（De Nadai 2016）、建物の床面積と用途（国内研究）、駅の乗降客数とアクセシビリティ（第1回コンペの1位も使用）。
- 空間汎化の観点では、座標そのものや細かいターゲットエンコーディングは同じ場所の予測には強いが、未観測の地域では効かなくなる可能性が高い。split（分割方法）が不明なうちは、両方のバリアントを用意しておくのが安全。

### Gaps
- Deep Gravityと2025年のNature Communications論文の具体的な精度（CPCなど）は、今回本文を取得できず確認していない。
- 「GPS滞在人口 × 国土数値情報 × 未観測地域への転移」を定量的に評価した査読論文は見つからなかった。
- GNN（グラフニューラルネット）でメッシュ滞在人口を予測し、空間CVまで行った研究は、今回の調査範囲では特定できなかった。

---

## Q2. 空間CVのベストプラクティス（メッシュ回帰との関係）

### Takeaway
空間的に自己相関したデータでランダムK-foldを使うと、未観測の場所での精度を過大に見積もる。これは Roberts 2017、Ploton 2020、Meyer 2018/2021 に共通する主張で、対策はブロックCV、leave-location-out、NNDMなど。一方 Wadoux 2021 は、「推定したいのが地図全体の精度で、予測地点がサンプルと同じように分布しているなら、空間CVはむしろ悲観側に偏る」と反論している。つまり、どのCVを使うべきかは予測する場面（同じ場所の翌年か、未観測の場所か）で決まる。本コンペで split が不明な状況は、まさにこの論点に当たる。

### Cited Findings（文献リスト）

**11. Roberts, D. R., Bahn, V., Ciuti, S., Boyce, M. S., Elith, J., Guillera-Arroita, G., et al. (2017). "Cross-validation strategies for data with temporal, spatial, hierarchical, or phylogenetic structure." Ecography, 40(8), 913–929. DOI: 10.1111/ecog.02881** ⚠️【H5】【CMP】
- 書誌は既知情報 — [DOI](https://doi.org/10.1111/ecog.02881)
- 内容（既知情報）：構造を持つデータでランダムCVを使うと汎化誤差を過小評価する。ブロックCVを推奨し、ブロックの大きさは残差の自己相関の範囲以上にする。外挿を評価したいときは、ブロックを予測の場面に合わせて設計する。

**12. Ploton, P., Mortier, F., Réjou-Méchain, M., et al. (2020). "Spatial validation reveals poor predictive performance of large-scale ecological mapping models." Nature Communications, 11, 4540. DOI: 10.1038/s41467-020-18321-y** ⚠️【H5】
- 書誌は既知情報 — [DOI](https://doi.org/10.1038/s41467-020-18321-y)
- 内容（既知情報）：アフリカの森林バイオマスをランダムフォレストで地図化した事例。ランダムCVでは高いR²が出たが、空間CVにするとR²はほぼゼロまで下がった。説明力の多くが空間自己相関によるもので、空間リーケージの典型例。Wadoux 2021 はこの論文に対する反論として書かれている — [Wadoux 2021の文脈説明](https://research.wur.nl/en/publications/spatial-cross-validation-is-not-the-right-way-to-evaluate-map-acc/)

**13. Meyer, H., Reudenbach, C., Hengl, T., Katurji, M., Nauss, T. (2018). "Improving performance of spatio-temporal machine learning models using forward feature selection and target-oriented validation." Environmental Modelling & Software, 101, 1–9. DOI: 10.1016/j.envsoft.2017.12.001** ⚠️【H5】【H4】【CMP】
- 書誌は既知情報 — [DOI](https://doi.org/10.1016/j.envsoft.2017.12.001)
- 内容（既知情報）：leave-location-out（LLO）、leave-time-out（LTO）、leave-location-and-time-out（LLTO）を区別し、目的に合わせた検証（target-oriented validation）を提案した。緯度経度や地点IDのような「場所を特定できる変数」はランダムCVの精度を上げるが、LLOでは過学習を起こす。空間CVの下で前向き特徴量選択（forward feature selection）を行うと、こうした変数が落ちて汎化が改善する。
- 本コンペとの関係：「同じ場所の翌年」なら LTO、「未観測の場所」なら LLO、が直接対応する。split が不明な間は両方でCVを回す価値がある。

**14. Meyer, H., Pebesma, E. (2021). "Predicting into unknown space? Estimating the area of applicability of spatial prediction models." Methods in Ecology and Evolution, 12(9), 1620–1633. DOI: 10.1111/2041-210X.13650** ⚠️【H5】
- 書誌は既知情報 — [DOI](https://doi.org/10.1111/2041-210X.13650)
- 内容（既知情報）：特徴量空間で学習データからどれだけ離れているか（Dissimilarity Index、DI）を測り、モデルの適用範囲（Area of Applicability、AOA）を推定する。R の CAST パッケージで実装されている。続編として Meyer & Pebesma (2022, Nature Communications, DOI: 10.1038/s41467-022-29838-9) が、全球MLマップの評価の課題を整理している（⚠️）。
- 関連（⚠️）：Milà, C., Mateu, J., Pebesma, E., Meyer, H. (2022). "Nearest neighbour distance matching Leave-One-Out Cross-Validation for map validation." Methods in Ecology and Evolution. DOI: 10.1111/2041-210X.13851。予測地点と学習地点の最近傍距離の分布に合わせてCVを設計する方法 — [DOI](https://doi.org/10.1111/2041-210X.13851)

**15. Wadoux, A. M. J.-C., Heuvelink, G. B. M., de Bruin, S., Brus, D. J. (2021). "Spatial cross-validation is not the right way to evaluate map accuracy." Ecological Modelling, 457, 109692. DOI: 10.1016/j.ecolmodel.2021.109692** ✅【H5】【CMP】
- 主張：空間CVには理論的な裏付けがなく、地図の精度評価には使うべきでない。ただし標準CVもクラスター化したデータでは欠陥がある。偏りのない精度推定には、確率サンプリングとデザインベースの推論が必要 — [WUR](https://research.wur.nl/en/publications/spatial-cross-validation-is-not-the-right-way-to-evaluate-map-acc/), [著者PDF](https://alexandrewadoux.github.io/assets/pdf/Wadoux_et_al_2021.pdf)
- 事例の結果：彼らのケーススタディでは、自己相関を無視した標準CVのほうが空間CVより偏りが小さかった — [IDEAS/RePEc](https://ideas.repec.org/a/eee/ecomod/v457y2021ics0304380021002489.html)
- 論争の整理：地理空間MLのレビューは、「空間CVは過度に楽観的な評価を防ぐのに必須」とする Meyer et al. (2019) と Wadoux 2021 を対立する立場として並べている — [ar5iv 2303.18087](https://ar5iv.labs.arxiv.org/html/2303.18087)
- 使い道：テストメッシュが学習メッシュと同じ地域に混在しているなら、ランダムCVのほうがリーダーボード（LB）をよく再現する可能性がある。

### Inferences
- 本コンペで split が判明したら、CVの設計は次のように切り替える。(i) 同じメッシュの翌年を予測するなら、2023年で学習して2024年で検証する時系列ホールドアウトにする（LTO）。(ii) 未観測のメッシュを予測するなら、テスト領域の大きさと形状に合わせた空間ブロックCVにする（LLO。ブロックの大きさの目安は残差の自己相関の範囲。予測距離の分布を合わせたいならNNDM）。(iii) 学習と同じ地域の中に未観測メッシュが散らばっている場合は、ランダムCVかグループCVでもよい（Wadouxの論点）。
- 空間リーケージの主な経路は3つ。隣接メッシュの目的変数を使ったラグ特徴量とターゲットエンコーディング、座標の生値、学習・テスト間で重なる広いバッファの集計値。どれもLLOでは見かけの精度を押し上げる。
- 公開LBで順位を落とした例（第1回12位の作者は公開7位→最終13位）もあり、CVの設計とLBの間の乖離を監視することが重要。

### Gaps
- Roberts 2017、Ploton 2020、Meyer 2018/2021、Milà 2022 は今回ページを取得していないため、書誌と内容は既知情報に基づく（⚠️）。特に Ploton の具体的なR²は原文で確認が必要。

---

## Q3. 「前年値」ベースラインはどれほど強いか。変化はどうモデル化されているか

### Takeaway
メッシュ単位の滞在人口を対象に、前年値（persistence）のベースラインを明示的に比べた研究は見つからなかった。近い設計としては、事前期間で学習したMLモデルを反実仮想（counterfactual）として使う研究と、ナイーブな前年比との比較（Bradford）がある。構造変化（コロナ後など）の後はモデルが過大予測するという報告（Melbourne）もある。変化を予測する研究としては、再開発・土地利用変化を特徴量の差分として与えるもの（深圳の渋滞予測、東京臨海部の滞在人口推定）がある。

### Cited Findings（文献リスト）

**16. Bradford City of Culture 2025 の評価研究（International Journal of Population Data Science 掲載）** ✅（著者名は未確認）【H4】
- 手法：モバイルアプリ由来のデジタル人流（footfall）を対象に、2019〜2024年のデータでランダムフォレスト回帰を学習し、イベントがなかった場合の2025年の人流を推定して実測と比べた — [IJPDS](https://ijpds.org/index.php/ijpds/article/view/3782)
- 結果：ブラッドフォード中心部の2025年の年間人流は、モデルの期待値より6.8%多かった。一方、ナイーブな前年比では12.4%増だった。つまり、前年値だけで比べると変化（介入効果）を過大評価してしまう — [IJPDS](https://ijpds.org/index.php/ijpds/article/view/3782)（※検索スニペット経由の数値。本文の確認を推奨）

**17. Asher, M., Oswald, Y., Malleson, N. (2025). "Understanding pedestrian dynamics using machine learning with real-time urban sensors." Environment and Planning B: Urban Analytics and City Science. DOI: 10.1177/23998083251319058** ✅【H4】【H5】【H2】
- データ：メルボルンの歩行者センサーの毎時カウント、建築環境変数、気象 — [SAGE](https://journals.sagepub.com/doi/10.1177/23998083251319058), [White Rose PDF](https://eprints.whiterose.ac.uk/id/eprint/221809/8/asher-et-al-2025-understanding-pedestrian-dynamics-using-machine-learning-with-real-time-urban-sensors.pdf)
- 結果：建築環境は時間的な周期より影響が小さかった。コロナ後の年はモデルが人流を過大予測し、持続的な構造変化があったことを示唆する。2020年以降に新設され、学習に含まれていないセンサーの地点も予測できた — 同上（検索スニペット経由）
- 使い道：H4（変化の大部分は時間方向の共通要因で、建築環境の効果は小さい）と、H5（新しい地点への予測）の両方。

**18. Forecasting Traffic Congestion Caused by Urban Renewal: Analysing the Predictive Influence of Land Use Changes Based on Explainable Machine Learning Methods. Applied Spatial Analysis and Policy (2026). DOI: 10.1007/s12061-026-09931-y** ✅（著者は未確認）【H4】
- 深圳を対象に、XGBoost＋SHAPで土地利用変化（開発強度）と渋滞の関係を複数のスケールで分析し、都市更新による渋滞を予測する — [Springer](https://link.springer.com/article/10.1007/s12061-026-09931-y)
- 使い道：「特徴量の差分（Δ床面積、Δ施設）で目的変数の変化を説明する」という変化モデルの設計例。目的変数は人流ではなく渋滞。

**19. Deville, P., Linard, C., Martin, S., Gilbert, M., Stevens, F. R., Gaughan, A. E., Blondel, V. D., Tatem, A. J. (2014). "Dynamic population mapping using mobile phone data." PNAS, 111(45), 15888–15893. DOI: 10.1073/pnas.1408439111** ⚠️【H4】
- 書誌は既知情報 — [DOI](https://doi.org/10.1073/pnas.1408439111)
- 内容（既知情報）：携帯CDRから、ポルトガルとフランスの人口分布の時間変化（昼夜・季節）を推定し、センサスと比べた。滞在人口が時間とともに変わることを地図化した基礎文献。

### Inferences
- 推論：滞在人口のメッシュ値は空間的に強く集中しており、年をまたいでも安定していると考えられる。そのため「同じ場所の翌年」タスクなら、前年値（2024年）か、2023・2024年の加重平均そのものが非常に強いベースラインになる可能性が高い。モデルは log(2025/2024) のような変化率を予測する残差学習として組むのが合理的。ただし、前年値の強さを定量的に示した文献は見つからなかったので、この点は推論にとどまる。
- 2023→2024年の変化率は、データ提供元のパネル（GPSの母集団）の変動も含んでいる可能性がある。全体の補正係数（共通の時間効果）と、メッシュごとの変化を分けてモデル化するのが望ましい。Asher 2025 が示すとおり、時間方向の共通要因は大きい。
- 「未観測の場所」タスクでは前年値が使えないので、Q1の特徴量とGBMで直接レベルを予測する。その際、2023・2024年の両年を学習に入れて年ダミーを付ける。

### Gaps
- メッシュ単位の滞在人口や人流について、前年値ベースラインとMLの精度差を報告した論文は見つからなかった。
- 国内で滞在人口の経年変化（年単位）を建物・施設の変化で説明した査読研究は、今回の調査範囲では特定できなかった。時系列研究としては、LSTMによる短期変動予測（高森・佐々木, 土木学会, 2021）がある — [PDF](http://library.jsce.or.jp/jsce/open/00039/202112_no64/64-53-12.pdf)

---

## Q4. 過去のMLIT 地理空間情報データチャレンジ解法から得られる教訓

### Takeaway
第1回（賃料予測、2024年10〜12月、SIGNATE）の1位はestieのkenkoooo氏。LightGBMを素直に使い、国土数値情報10データセットから427特徴量を作った。効いたのは地価公示・地価調査、1kmメッシュ将来推計人口、平年値メッシュ（気候）、駅の乗降客数。12位解法では、地価の近傍10点の逆距離二乗加重平均と、人口の比率特徴量が効いた。どちらも「近傍k点の距離加重」「メッシュの包含結合」「半径内の件数」が国土数値情報の基本的な加工パターンになっている。第2回（売買価格、MAPE、2025年11月14日〜2026年1月9日）の上位解法の記事は、今回は見つからなかった。

### Cited Findings（文献リスト）

**20. kenkoooo（estie）(2024-12-24). 「国交省コンペ優勝！賃料予測コンペ1位解法」estie inside blog** ✅【CMP】【H5】
- URL：[estie inside blog](https://www.estie.jp/blog/entry/2024/12/24/160000)
- 目的変数と損失：総賃料ではなく平米単価を目的変数にし、損失はRMSEではなくMAE（`metric: l1`）にした。外れ値の影響を抑え、fold間のスコアのばらつきを小さくするため
- モデル：ハイパーパラメータ未調整のLightGBM（学習率0.1、early stopping 100）を複数シードで平均した。床面積の欠損は別のLightGBMで補完してから使った
- 国土数値情報の利用（10データセット）：
  - 地価公示と都道府県地価調査：強く効いた。過去値から変化率も作った
  - 小学校区
  - 駅別乗降客数：最寄り駅までの距離と、乗降客数上位25駅までの距離（都会度の指標）
  - 医療機関：最寄りの小児科までの距離
  - 1kmメッシュ将来推計人口：強く効いた。特に35–39歳、45–49歳、5–9歳
  - 平年値メッシュ：日照時間と最高気温が効いた
  - 用途地域：中程度
  - DID（人口集中地区）：人口密度が効いた
  - 学校：最寄りの保育所までの距離
- 近傍統計：同じ郵便番号内と半径2km内の単価の平均・分散。市区町村平均に対する相対値（築年数、面積）も作った
- リーク的な利用：テストに同じ部屋・同じ建物の過去掲載があることを、時点補正の線形回帰で活用した
- 実務面：Snowflakeとdbtでパイプライン化し、データを後から追加しやすくした
- CVの分割方法は記事に書かれていない（空間splitだったかは不明）

**21. fumito203 (2024-12-22). 「国土交通省 地理空間情報データチャレンジ 12位解法」Qiita** ✅【CMP】
- URL：[Qiita](https://qiita.com/fumito203/items/898174c8f870e93b0ff1)
- CV：building_idでグループ化した5-fold GroupKFold
- モデル：LightGBM、XGBoost、CatBoostのアンサンブル
- 国土数値情報の加工：
  - 地価は最近傍3点の値と平均、さらに10点の逆距離二乗加重平均を作り、これが最も効いた
  - 駅乗降客数は最近傍3駅の属性と距離
  - 500mメッシュ将来推計人口、1km平年値メッシュ（49変数）、宿泊容量メッシュは、物件位置を含むメッシュで結合
  - 医療・福祉・文化・集客施設は半径1km内の件数
- 知見：人口は実数より比率（0–14歳、15–64歳の割合、増加率）のほうが有効だった。ZENRINの特徴量は欠損を補完せずにそのまま使うほうがよかった
- 反省：LightGBM以外のモデルを足すと公開LBは上がったが最終スコアは上がらず、公開7位から最終13位に落ちた

**22. 第1回の公式資料と振り返り** ✅【CMP】
- 公式：開催は2024年10〜12月、表彰は2025年1月。上位の多くは100回を超える投稿をしていた。解法発表会のアーカイブ動画もある — [国土数値情報 イベントページ](https://nlftp.mlit.go.jp/ksj/event/event_02.html), [PDF](https://nlftp.mlit.go.jp/ksj/event/event_02.pdf), [報道発表](https://www.mlit.go.jp/report/press/tochi_fudousan_kensetsugyo17_hh_000001_00060.html)
- 参加者の振り返り：[Qiita kMUTOU](https://qiita.com/kMUTOU/items/a3e758eb2d9ea4edb128)、戦い方の考察：[たかいとの備忘録](https://takaito0423.hatenablog.com/entry/2024/10/23/221608)（いずれも内容は未精読）

**23. 第2回（不動産売買価格予測）** ✅（解法は未発見）【CMP】
- 期間は2025年11月14日〜2026年1月9日。評価指標はMAPE。地理空間データの活用が必須で、登記所備付地図データも提供された — [国交省 報道発表](https://www.mlit.go.jp/report/press/tochi_fudousan_kensetsugyo17_hh_000001_00067.html), [PR TIMES](https://prtimes.jp/main/html/rd/p/000000277.000038674.html), [Zenn ベースライン記事](https://zenn.dev/mmrbulbul/articles/signate-geospatial-challenge-2025-01-baseline)
- 表彰式の報道（[東京都宅建協会](https://www.tokyo-takken.or.jp/re-port/80924)）の検索スニペットに上位者名の言及があったが、本文は未確認（⚠️）
- 協賛企業の勉強会アーカイブ：[YouTube GA technologies](https://www.youtube.com/watch?v=5gOyXJa048U)

### Inferences
- 国土数値情報の加工は、次の4パターンにまとめられる。(1) 最近傍k点の値と逆距離加重、(2) 含まれるメッシュ・ポリゴンの属性の結合（将来推計人口、気候、用途地域、DID）、(3) 半径r内の施設数、(4) 最寄り施設や上位施設（例：乗降客数上位25駅）までの距離。滞在人口の予測では、ここに道路網の中心性と到達圏人口（重力型アクセシビリティ）を加えるのが自然な拡張になる。
- 不動産コンペでは、「同じ建物・同じ部屋」のリークや近傍のターゲット統計（半径2kmの単価平均）が強力だった。滞在人口コンペで「同じ場所の翌年」タスクなら、これらは前年値とその近傍平均に対応する。「未観測の場所」タスクなら、近傍の観測済みメッシュの値（空間ラグ）が使えるかどうかが鍵になる。ただし、テストが空間的にまとまったブロックの場合、ブロック内部では使えない。
- 平米単価とMAEを採用した工夫は、滞在人口では log 変換した目的変数と、評価指標に合わせた損失に相当する。

### Gaps
- 第2回の上位解法の記事（SIGNATEのディスカッション、Qiita、noteなど）は、今回の検索では見つからなかった。
- 第1回1位のCVの分割方法は記事に記載がない。
