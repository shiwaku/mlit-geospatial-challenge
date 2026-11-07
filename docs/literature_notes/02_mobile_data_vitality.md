# モバイル／GPS位置情報データによる都市の活力（にぎわい）・来訪者・滞在人口の計測と説明要因

> 対象: 携帯電話・GPS由来の人口データ（モバイル空間統計、Agoop、ジオテクノロジーズ/トリマ、Telecom Italia、Tencent/Baidu、SafeGraph等）で都市の活力・来訪者・滞在人口を計測し、POI・駅・道路網・土地利用などで説明・予測した研究。
> 仮説の対応: H1 = 就業者を除くとにぎわいの地図は変わるか / H2 = 来訪者数は駅・人口でどこまで説明できるか（量か質か） / H3 = 滞在時間が長い・消費が多い場所の特徴 / H4 = 時間変化 / H5 = 人流の空間予測
> 検証の度合い: 【確認済】= 書誌情報を一次ページ（J-STAGE、出版社、DOAJ/PMC、arXiv等）で確認 / 【要旨のみ】= 書誌は確認したが本文は未読で、手法の詳細は要旨に基づく / 【不確実】= 二次情報やプレスリリースのみで、書誌か内容の一部が未確認
> 調査日: 2026-11-07

---

## 問1 携帯電話由来の活動量・活力を建築環境変数で回帰した研究はどれか。重要だった変数とモデル（OLS, GWR, RF, XGBoost+SHAP）は何か

### Takeaway
国際的には、Jacobsの4条件（用途混合、小さな街区、古い建物の混在、密度）を携帯電話データで検証した研究が出発点になっている（De Nadai et al. 2016; Botta & Gutiérrez-Roig 2021）。そこでは「密度」と「第三の場所（飲食・交流施設）」が一貫して効く。POIは「数」より「種類の豊かさ（richness）」が効く（Yue et al. 2017）。近年の中国の研究はXGBoost+SHAPが主流で、POI密度・POI多様性・容積率・betweennessが上位に来て、閾値効果（非線形）があると報告している。日本では、地方都市中心市街地の昼間人口（来訪者）を最も強く説明したのは「周辺の人口密度」で、施設集積と商業床面積がそれに続いた（萬家ら 2025）。この結果はH2（量の説明は人口要因が支配的）を支持する。

### Cited Findings

**[1] De Nadai, M., Staiano, J., Larcher, R., Sebe, N., Quercia, D., Lepri, B. (2016). The Death and Life of Great Italian Cities: A Mobile Phone Data Perspective. Proc. WWW 2016, pp. 413–423. DOI: 10.1145/2872427.2883084 / arXiv:1603.04012【確認済】**
- データ: TIM（Telecom Italia）の携帯電話活動量（60分集計、TIM顧客とローミング客を含む、2014年2〜10月）。対象はBologna, Florence, Milan, Palermo, Rome, Turinの6都市。説明変数は国勢調査、OpenStreetMap、Foursquare由来の変数 — [arXiv/ar5iv](https://ar5iv.arxiv.org/html/1603.04012); [UniTN IRIS](https://iris.unitn.it/handle/11572/139303)
- 結果: Jacobsの4条件はイタリアの都市でも成り立った。人の密度が重要。土地利用（古い建物の混在）の効果はイタリアでは弱めだった — [MIT Technology Review](https://www.technologyreview.com/2016/03/24/161419/data-mining-reveals-the-four-urban-conditions-that-create-vibrant-city-life/amp/)
- 「第三の場所と小さな街区が携帯活動量と有意に相関する」という要約は二次情報（Emergent Mind）で、本文では未確認【不確実】 — [Emergent Mind](https://www.emergentmind.com/papers/1603.04012)
- 該当仮説: H2（密度・人口の説明力）、H3（第三の場所）

**[2] Botta, F., Gutiérrez-Roig, M. (2021). Modelling urban vibrancy with mobile phone and OpenStreetMap data. PLoS ONE 16(6): e0252015. DOI: 10.1371/journal.pone.0252015【確認済】**
- データ: Telecom Italia Big Data Challenge 2015の携帯在圏データ（2015年3〜4月）。対象はMilan, Rome, Turin, Naples, Palermo, Bari, Veniceの7都市。説明変数は国勢調査とOSMの都市特徴 — [PMC8172046](https://www.ncbi.nlm.nih.gov/pmc/articles/PMC8172046/)
- 手法: 空間モデルで都市特徴とvibrancyの関係を推定し、年齢層ごとに効く要因が変わるかも検証した — [PMC8172046](https://www.ncbi.nlm.nih.gov/pmc/articles/PMC8172046/)
- 結果: 都市特徴とvibrancyは強く関連し、特に「第三の場所（third places、交流空間）」が重要だった — [PMC8172046](https://www.ncbi.nlm.nih.gov/pmc/articles/PMC8172046/)
- 該当仮説: H3（交流型の施設が人を引きつける）、H5（OSMのようなオープンデータでvibrancyを空間予測できる）。国土数値情報で予測するコンペの設定に近い

**[3] Yue, Y., Zhuang, Y., Yeh, A.G.O., Xie, J.-Y., Ma, C.-L., Li, Q.-Q. (2017). Measurements of POI-based mixed use and their relationships with neighbourhood vibrancy. IJGIS 31(4): 658–675. DOI: 10.1080/13658816.2016.1220561【確認済（書誌）/ 要旨のみ（結果）】**
- データ: 24時間の携帯電話利用者数をneighbourhood vibrancyの代理指標とした（深圳）。用途混合はナビ用データベースのPOIからHill数（richness, entropy, Simpson）で測った — [HKU Repository](https://repository.hku.hk/handle/10722/248107); [dblp](https://dblp.dagstuhl.de/rec/journals/gis/YueZYXML17.html)
- 結果: POI密度やentropyだけではvibrancyをほとんど説明しない（約1%との要約あり）。POIのrichness（種類数）は有意に寄与した。POIを単に増やすより、補完的なPOIを混ぜる方が効果がある — 検索要約による。数値は本文で要確認【不確実】
- 該当仮説: H2（量より質・多様性）。POIの「件数」より「業種の種類数」を特徴量にすべきという示唆

**[4] Wu, W. ほか (2019). Influence of Built Environment on Urban Vitality: Case Study of Shanghai Using Mobile Phone Location Data. Journal of Urban Planning and Development 145(3): 04019007. DOI: 10.1061/(ASCE)UP.1943-5444.0000513【要旨のみ・共著者名は未確認】**
- データ: 上海中心部の携帯位置データ。都市活動の強度を6つの時間帯で算出し、活力の代理指標とした — [ASCE Library](https://ascelibrary.com/doi/abs/10.1061/%28ASCE%29UP.1943-5444.0000513)
- 手法: 6種類の空間計量経済モデル（空間ラグ・空間誤差系）で建築環境の効果を推定 — [ResearchGate](https://www.researchgate.net/publication/335531391_Influence_of_Built_Environment_on_Urban_Vitality_Case_Study_of_Shanghai_Using_Mobile_Phone_Location_Data)
- 該当仮説: H4（時間帯で効く要因が変わる）、H5（空間自己相関を考慮した予測）

**[5] 萬家隆介・小沢啓太郎・田村将太・田中貴宏・塚井誠人 (2025). 地方都市における中心市街地の昼間人口集積と施設特性・立地特性の関連分析. 日本建築学会計画系論文集 90(831): 1001–1010. DOI: 10.3130/aija.90.1001【要旨のみ】**
- データ: キーワードはモバイル空間統計と流動人口データ。スマホ位置情報から1日の起点・終点で推定居住地を求め、周辺圏域から中心市街地への「来訪者数（滞在）」を集計したとみられる（検索要約による。対象は呉市・東広島市）【不確実】 — [J-STAGE PDF](https://www.jstage.jst.go.jp/article/aija/90/831/90_1001/_pdf)
- 結果: 平日と休日で一部異なる傾向。周辺人口密度が平日・休日とも最も影響の大きい指標で、施設集積とショッピングセンター床面積の効果も確認された — [J-STAGE](https://www.jstage.jst.go.jp/article/aija/90/831/90_1001/_article/-char/ja/)
- 該当仮説: **H2を強く支持**（来訪量はまず人口＝後背地の量で決まり、施設の質は二次的）。H4（平日と休日の差）

**[6] XGBoost+SHAPによる活力研究群（中国）【書誌・詳細は不確実】**
- 煙台: 昼と夜の活力を分けてXGBoost+SHAPで分析。事業所系POI密度、容積率（FAR）、POI多様性、betweennessが強い非線形効果を持つと報告 — [ScienceDirect S2590252025000583](https://www.sciencedirect.com/science/article/pii/S2590252025000583)（活力指標が携帯データかどうかは未確認）
- 西安: 携帯シグナリングデータに加え、POI・AOI・ストリートビューを使い、XGBoost+SHAPで非線形・閾値効果を分析 — [ResearchGate](https://www.researchgate.net/publication/386191515_Integrating_Multi-Source_Urban_Data_with_Interpretable_Machine_Learning_for_Uncovering_the_Multidimensional_Drivers_of_Urban_Vitality)
- 瀋陽の歴史地区: Baidu Heat MapとXGBoost+SHAPで、曜日による建築環境の効果の違いを分析 — [Land 15(3):431, DOI 10.3390/land15030431](https://doi.org/10.3390/land15030431)
- 該当仮説: H4、H5。非線形・閾値効果があるため、コンペでは線形回帰より勾配ブースティングが妥当という根拠になる

**[7] Kim, Y.-L. (2020). Data-driven approach to characterize urban vitality: how spatiotemporal context dynamically defines Seoul's nighttime. IJGIS 34(6): 1235–1256. DOI: 10.1080/13658816.2019.1694680【要旨のみ】**
- データ・手法: ソウルの24時間歩行者流動（floating population）データに関数主成分分析（FPCA）を適用し、活力の時間パターンを抽出 — [Taylor & Francis](https://informahealthcare.com/doi/abs/10.1080/13658816.2019.1694680); [Peeref](https://www.peeref.com/works/19300873)
- 結果: 昼のパターンに埋もれていた夜間の活力パターンを取り出せた。地域差・季節差もある — 同上
- データの具体的な出所（通信事業者データか）は未確認
- 該当仮説: H4（時間変化）、H1（昼の就業者の流れを除くと別の「にぎわい」が見える、という発想と同じ）

**[参考・携帯データ以外] Xia, C., Yeh, A.G.O., Zhang, A. (2020). Analyzing spatial relationships between urban land use intensity and urban vitality at street block level: A case study of five Chinese megacities. Landscape and Urban Planning 193: 103669【要旨のみ】**
- 昼の活力は小規模飲食店データ、夜の活力は夜間光で測った（携帯データではない）。LISAで土地利用強度と活力の局所的なミスマッチ（過密・低利用）を検出した — [HKU Hub](https://hub.hku.hk/handle/10722/305133)
- 続編（Annals of AAG, 2021, 15都市）は、接続性・コンパクト性・建物配置・ランドマーク・交通施設・オープンスペースが重要で、用途混合と建物密度の効果は限定的とした — [T&F](https://informahealthcare.com/doi/full/10.1080/24694452.2021.1919502)【要旨のみ】
- 該当仮説: H2（建物密度＝量だけでは説明しきれない）

### Inferences
- 研究全体で効く順はおおむね「人口・密度（量）」→「POIの種類・第三の場所（質）」→「ネットワーク中心性」となっている。コンペの特徴量設計では、人口（国土数値情報の将来推計人口メッシュ、国勢調査）と駅の乗降客数をベースラインに置き、残差を施設の多様性や中心性で説明するという段階的な検証がH2に直接答える。
- Yue et al.の「件数より種類数」は、国土数値情報の施設系レイヤー（医療、学校、文化施設、観光資源など）から「メッシュ内の施設種別数」を特徴量にする根拠になる。

### Gaps
- XGBoost+SHAP系の中国研究は数が多いが、ここに挙げた個別論文の著者名と掲載誌は一次ページで確認できていない。引用する前に確認が必要。
- 国土数値情報だけ（商用POIなし）で携帯由来の人口を予測した研究は見つからなかった。

---

## 問2 モバイルデータで居住者・就業者・来訪者をどう分けるか（自宅・勤務地推定）。日本の来訪者・交流人口推計の研究

### Takeaway
標準的な手法は、夜間の滞在から自宅を、平日昼の長時間滞在から勤務地を推定し、それ以外の滞在を「来訪」とみなすものである。ただし、自宅推定アルゴリズムの基準を変えるだけで最大約40%の利用者の自宅判定が変わり、国勢調査との相関も最大0.60程度にとどまる（Vanhoof et al. 2018）。そのため、就業者を除外した結果の地図は、除外の定義に敏感である可能性が高い（H1の検証では感度分析が必須）。日本では、モバイル空間統計の居住地別集計を使った交流人口推計、GPSで推定した自宅・勤務地からの距離で滞在を分類する研究、来街者の居住地の多様性で商業集積を類型化した研究がある。

### Cited Findings

**[8] Vanhoof, M., Reis, F., Ploetz, T., Smoreda, Z. (2018). Assessing the quality of home detection from mobile phone data for official statistics. Journal of Official Statistics 34(4): 935–960. DOI: 10.2478/jos-2018-0046【確認済】**
- フランスの大規模CDRで5種類の自宅推定アルゴリズム（HDA）を比較した。基準の選び方で最大約40%の利用者の自宅判定が変わり、検証データとの一致も低い — [RePEc/IDEAS](https://ideas.repec.org/a/vrs/offsta/v34y2018i4p935-960n7.html); [arXiv 1809.07567 (CAS catalog)](https://katalog.lib.cas.cz/KNAV/EdsRecord/edsarx,edsarx.1809.07567)
- 関連研究（Vanhoof, Lee, Smoreda）: 約1,800万人で9つのアルゴリズムを試し、全国規模の自宅推定の性能は「良くて中程度」、国勢調査との相関は最大0.60 — [arXiv 1809.09911](https://ar5iv.labs.arxiv.org/html/1809.09911)
- 該当仮説: **H1**（就業者や居住者の除外は推定誤差を含むので、除外ルールを変えた感度分析が必要）

**[9] 秋山祐樹・ホラノン ティーラユット・柴崎亮介 (2013). 大規模人流データを用いた商業地域における来訪者数の時系列分析. 地理情報システム学会 講演論文集 (2013), C-5-4【要旨のみ（検索要約）】**
- 関東の1年分のGPSログから、Horanont et al. (2010) の方法で自宅エリアと勤務地エリアを推定した。滞留15分以上かつ自宅・勤務地から200m以内の滞在に自宅・勤務地フラグを付け、商業地域の来訪者数を時系列で分析した — [GISA PDF](https://www.gisa-japan.org/content/files/conferences/proceedings/2013cd/papers/C-5-4.pdf)
- 該当仮説: H1（来訪者の定義の実装例）、H4

**[10] 清家剛・三牧浩也・森田祥子 (2015). モバイル空間統計を活用した都市拠点地区の人口特性分析に係る研究. 日本建築学会計画系論文集 80(713): 1625–1633. DOI: 10.3130/aija.80.1625【要旨のみ】**
- 柏市中心部のアンケートとモバイル空間統計を組み合わせた地区分析モデル、および千葉県の基地局を比較する3つのモデルを作った。モバイル空間統計で人口分布が容易に把握できると結論 — [J-STAGE](https://www.jstage.jst.go.jp/article/aija/80/713/80_1625/_article/-char/ja/)
- 関連: 都市計画論文集 46(3) (2011) の柏市の論文は、モバイル空間統計の「現在人口」と常住人口の違いを整理し、拠点地区・住居地区・田園地区で1日の人口推移を比較している（著者名は未確認） — [J-STAGE PDF](https://www.jstage.jst.go.jp/article/journalcpij/46/3/46_3_451/_pdf)
- 要旨からは居住者と来訪者を分離しているかは確認できない
- 該当仮説: H4（日内変動）、H1（現在人口と常住人口の差＝流入人口）

**[11] 西垣友貴・Jan-Dirk Schmöcker・山田忠史・中尾聡史 (2022). GPSデータを用いたメッシュ人口に基づく観光者数の推定. 土木学会論文集D3（土木計画学） 77(5): I_549–I_563. DOI: 10.2208/jscejipm.77.5_I_549【要旨のみ】**
- 京都市の観光者数を、GPSなどのメッシュ人口から重回帰と階層線形モデルで推定した。月別の変動を考慮した階層線形モデルの方が良い。1日に訪れたエリア数でGPSデータを抽出すると有効。観光地以外も対象に含める場合はGPS以外のデータも有効 — [J-STAGE](https://www.jstage.jst.go.jp/article/jscejipm/77/5/77_I_549/_article/-char/ja/)
- データの提供元は要旨に記載なし
- 該当仮説: **H1・H5**（「1日の訪問エリア数」で来訪者らしい利用者を抽出するのは、就業者を除外するルールの代替案になる）、H4（月別の変動）

**[12] 竹内真雄・嚴先鏞・鈴木勉 (2024). 東京区部における業種構成・滞在パターンに基づく商業集積地の類型化と滞在移動特性の分析. 都市計画論文集 59(3): 555–562. DOI: 10.11361/journalcpij.59.555【書誌確認済・内容は検索要約】**
- GPSデータで東京区部の商業集積地を業種構成と滞在パターンから類型化し、滞在者の密度、居住地の多様性、移動距離を定量化した — [J-STAGE 目次](https://www.jstage.jst.go.jp/browse/journalcpij/59/3/_contents/-char/ja)
- データの提供元と滞在の定義（閾値）は未確認（記事ページがHTTP 500で取得できなかった）
- 該当仮説: **H3**（滞在パターンと業種構成の関係）、H1（来訪者の居住地の多様性）

**[13] 天谷ら（天谷・岡田・中村・出口） (2024). 東京都区部の大規模開発集積地における従業者・来街者の回遊行動の傾向の変化に関する研究. 都市計画論文集 59(3): 659–666【タイトルと著者のみ確認・内容は未確認】**
- 人流データを使い、従業者と来街者を分けて回遊行動の変化を分析している（タイトルから） — [J-STAGE 目次](https://www.jstage.jst.go.jp/browse/journalcpij/59/3/_contents/-char/ja)
- 該当仮説: **H1・H4**（従業者と来街者を分けた分析の直接の先行例。本文の確認を推奨）

**[14] その他の日本の関連研究【不確実】**
- 綿井剛 (2020). モバイル空間統計を用いた滞在人口及び関係・交流人口の推計. Discussion Paper Series 20-2（兵庫県立大学系の研究グループと推定）。滞在人口から県外居住者を抽出し、年齢割合で割り戻して関係・交流人口を算出（検索要約による。PDFは暗号化されていて本文を読めず） — [PDF](https://drg-u-hyogo.jp/wp-content/themes/gensai2020/pdf/publication/drgdps20-2.pdf)
- 多次元ガウス混合モデルによる携帯GPSデータの滞在目的分類 (2024, 人工知能学会SIG-SAI-051)。京都市で、同一メッシュ内5分以上の記録を「滞在」と定義し、位置・時刻・推定居住地からの距離・滞在時間でGMMにより滞在目的を分類（著者名は未確認） — [J-STAGE PDF](https://www.jstage.jst.go.jp/article/jsaisigtwo/2024/SAI-051/2024_03/_pdf/-char/ja)
- 白・卯月 (2022). GPSデータを用いた来場者人流特性統計分析手法とシステムツール. 都市計画報告集 20(4): 386-。携帯GPSデータをMySQLとQGISで処理し、みなとみらい21地区の来場者の滞在と移動を分析 — [J-STAGE](https://www.jstage.jst.go.jp/article/reportscpij/20/4/20_386/_article/-char/ja/)
- モバイル空間統計は居住地別（どこから来たか）の集計ができ、最小500mメッシュ — [mobaku.jp](https://mobaku.jp/service/jpn_distribution/)

### Inferences
- 文献でよく使われる来訪者判定のルールは「滞在5〜15分以上」「推定自宅・勤務地から200m以上離れている」の組み合わせである。コンペの「非居住者・非就業者の滞在人口」はおそらくこれに近い定義で作られていると推測される（コンペ資料で要確認）。
- H1の検証では、(a) 全滞在人口、(b) 居住者を除いた人口、(c) 居住者と就業者を除いた人口、の3つの地図を作り、順位相関とホットスポットの入れ替わり（LISA）を比べるのが文献と整合的である。

### Gaps
- 就業者を除くかどうかでにぎわいの地図がどれだけ変わるかを定量的に示した日本の論文は見つからなかった（天谷ら2024が最も近い候補だが、本文未確認）。
- モバイル空間統計の「居住者・来訪者」の区分方法（住所登録ベース）の詳細な論文は今回確認できなかった。

---

## 問3 スペースシンタックス・ネットワーク中心性とPOI・土地利用は、滞在と通過のどちらをよく予測するか

### Takeaway
携帯やGPSのデータで「滞在」と「通過」を分け、スペースシンタックス指標とPOIのどちらがそれぞれを予測するかを直接比べた論文は見つからなかった。間接的な証拠としては、(i) 中心性（特にbetweenness）は街路の歩行者量や活力とよく相関し、歩行圏スケール（500〜1500m）で最も効く。(ii) スマホのポイントデータから求めた街路の歩行者密度・速度は、スペースシンタックス指標、駅からの距離ポテンシャル、土地利用でかなり説明できる。(iii) 滞在時間（dwell time）と建築環境の関係を扱った研究はまだ少ない。

### Cited Findings

**[15] 清水光輝・西宏章・岸本達也 (2019). スマートフォンの時空間情報を用いた街路網における歩行者密度および速度の推定. 都市計画報告集 18(1): 64–71. DOI: 10.11361/reportscpij.18.1_64【要旨のみ】**
- スマホのポイントデータから街路ごとの歩行者密度と歩行速度を算出し、スペースシンタックス指標、駅からの距離ポテンシャル、土地利用、道路形状を説明変数とする重回帰で推定した。説明力は高いと報告（係数やR²は要旨に記載なし） — [J-STAGE](https://www.jstage.jst.go.jp/article/reportscpij/18/1/18_64/_article/-char/ja/)
- 該当仮説: **H5**、H3（歩行速度が遅い＝滞留的な街路を特定できる。滞在と通過を分ける指標として使える）

**[16] Fang, C., He, S., Wang, L. (2021). Spatial Characterization of Urban Vitality and the Association With Various Street Network Metrics From the Multi-Scalar Perspective. Frontiers in Public Health 9: 677910. DOI: 10.3389/fpubh.2021.677910【確認済・携帯データではない】**
- 武漢。活力はPOI・WorldPop・住宅価格などの合成指標（携帯データは不使用）。説明変数はsDNAの16指標を5つの半径で計算し、Geodetectorで評価 — [Frontiers](https://www.frontiersin.org/journals/public-health/articles/10.3389/fpubh.2021.677910/full)
- 結果: 接続性（r=0.65、1500m）とbetweenness（q=46.7%、1500m）が強い。severance（分断）は約10%と弱い。歩行圏スケールの指標が自動車圏スケールの指標より効く。ただし本文中で「最大の寄与要因」の記述が要旨と結果で食い違う — 同上
- 該当仮説: H2・H5（ネットワーク中心性は量の予測に効く。スケールの選び方が重要）

**[17] 携帯データとスペースシンタックスの組み合わせ（中国・日本）【不確実】**
- 武漢のレビューデータを使った研究では、活力への影響はbetweennessが最大、次いでcloseness、straightnessが最小だった（Sustainability 11(16): 4356, 2019） — [MDPI](https://www.mdpi.com/2071-1050/11/16/4356)（携帯データではない）
- 名古屋工業大学の科研費18H03825の成果報告書に「携帯電話位置データとスペースシンタックスによるにぎわい分布の要因分析」が含まれるとの検索要約があるが、PDFを読めず未確認 — [KAKEN PDF](https://kaken.nii.ac.jp/en/file/KAKENHI-PROJECT-18H03825/18H03825seika.pdf)

**[18] 滞在時間（dwell time）と建築環境: SafeGraph系【要旨のみ・不確実】**
- フェニックス: SafeGraphで、通勤・買物・私用・社交の目的別にPOI訪問頻度と建築環境の関連を空間誤差モデルとOLSで分析（"Multifaceted associations between built environments and POI visit patterns by trip purposes", Cities 誌と推定、2025） — [ScienceDirect S0264275125002033](https://www.sciencedirect.com/science/article/abs/pii/S0264275125002033)
- SafeGraphのdwell timeはPOIごとの中央値と4区間（[0,5), [5,20), [20,60), [60,∞)分）しかなく、分布の異質性はわからないという制約が指摘されている — [PMC10118388](https://pmc.ncbi.nlm.nih.gov/articles/PMC10118388/)
- 施設・場所ごとの滞在時間を地図化・分析した研究は少ない、との指摘（2025年のデータセット論文） — [arXiv 2508.13295](https://arxiv.org/pdf/2508.13295)
- 該当仮説: **H3**（滞在時間の研究自体が手薄で、コンペで検証すれば新規性がある）

### Inferences
- 「通過」の量はネットワーク中心性（betweenness/choice）と駅の近さで、「滞在」の量は飲食・商業・交流施設の種類数と床面積で説明される、という仮説は文献と矛盾しない。ただし直接検証した研究は未発見で、仮説のまま扱うべきである。
- 国土数値情報だけでも、道路中心線（基盤地図情報を併用）からbetweennessを、駅別乗降客数から駅ポテンシャルを作れるので、量と質の分解（H2）を行う材料はそろう。

### Gaps
- 携帯・GPSで滞在と通過を分け、中心性とPOIの説明力を比べた査読論文は見つからなかった。
- 日本でスペースシンタックスと携帯人流を組み合わせた査読論文（都市計画論文集など）も確認できなかった。

---

## 問4 ジオテクノロジーズ/トリマやAgoopのデータを使った日本の研究（J-STAGE）

### Takeaway
ジオテクノロジーズ（トリマ）のGPSデータを使った査読論文として確認できたのは、能登半島地震の避難行動の論文（Communications Earth & Environment）1件と、JR東日本の乗換経路の技術論文1件（いずれも同社プレスリリース経由）のみである。都市の活力や来訪者を扱ったJ-STAGE論文は見つからなかった。Agoopのデータは「流動人口データ」として萬家ら(2025)のキーワードに現れるが、提供元を明記した都市計画論文集の論文は今回確認できなかった。

### Cited Findings
- **[19] 能登半島地震の避難行動（ジオテクノロジーズのデータ）**: "Large-scale geolocation data reveal evacuation behaviour during the 2024 Noto Peninsula earthquake and tsunami", Communications Earth & Environment, DOI: 10.1038/s43247-025-02819-8。東北大学災害科学国際研究所と東京大学先端科学技術研究センターの研究者が、ジオテクノロジーズのスマホGPSログで避難実態を分析 — [プレスリリース（TV Tokyo PR）](https://www.tv-tokyo.co.jp/plus/external-pr/entry/48101.html)【不確実: プレスリリース経由。著者名と巻号は未確認】
- **[20] JR東日本の技術論文（2026年10月）**: 山口祐樹・小西勇介「GPS人流データを活用した鉄道利用者の乗換経路実態把握」。約10秒間隔で取れるデータの連続性が評価されて採用された。自動改札や車両の重量センサのデータと比べて、実際の利用傾向に近い判定ができた。アルゴリズムの構築はLocationMindが支援 — [ジオテクノロジーズ 2026-10-22](https://geot.jp/info-20261022/)【不確実: 社外報。掲載誌は未確認】
- 東京大学空間情報科学研究センター（CSIS）との共同研究（2023年2月開始）で、トリマ利用者の歩行移動に注目。データは無償提供で、「よく歩く街ランキング」（1都3県で逗子市が1位）を公表 — [ジオテクノロジーズ 2023-02-03](https://geot.jp/pressrelease-20230203/)
- Agoopの流動人口データは、最小50mメッシュ・1時間ごとの来訪・滞在人数とFrom-Toの流れを提供する（ベンダー情報で、査読付きの精度評価ではない） — [Agoop](https://agoop.co.jp/service/dynamic-population-data/)
- 関本「人々の流動データの基礎的な処理・分析手法について」（写真測量とリモートセンシング 52(6): 321）は、携帯・GPS・ICカードなどの流動データの処理と、滞在人数・通過人数の集計法を解説 — [J-STAGE PDF](https://www.jstage.jst.go.jp/article/jsprs/52/6/52_321/_pdf)【要旨のみ】
- 国交省の資料は、GPSデータは基地局データと違って地下や建物内の移動も取得できると整理している — [MLIT PDF](https://www.mlit.go.jp/common/001243364.pdf)

### Inferences
- トリマのデータはポイ活アプリ由来なので、利用者の属性に偏り（年齢層、ポイ活志向）がある可能性が高い。拡大推計の方法はコンペ資料で確認すべきである。約10秒間隔の高頻度測位は滞在時間と通過の判別（H3、問3）に有利である。
- トリマのデータで都市の活力を扱った先行論文がほぼないことは、コンペ成果の新規性になる。

### Gaps
- J-STAGEで「トリマ」「ジオテクノロジーズ」を直接検索したわけではなく、該当論文の有無は完全には確認できていない（Web検索とプレスリリース経由の確認にとどまる）。
- Agoopのデータを明記した都市計画論文集・交通工学論文集の論文は、今回の検索では特定できなかった。
- 該当しない候補として、Sulis et al. (2018, JOSIS 16: 137–162, DOI 10.5311/JOSIS.2018.16.384) は交通ICカードとTwitterを使っていて携帯・GPSデータではない（[JOSIS](https://josis.org/index.php/josis/article/view/92)）。Ye, Li, Liu (2018, Urban Geography 39(4): 631–652) は小規模飲食店を活力の代理指標にしている（[HKU](https://hub.hku.hk/handle/10722/246383)）。どちらも方法論の参考にはなるが、モバイルデータの研究ではない。
