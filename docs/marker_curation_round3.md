# 常见微量元素表型词典第三轮精修说明

更新时间：2026-03-15

第二轮精修已经把常见微量元素的 marker 从“能用”收紧到“更少假阳性”。第三轮继续做两件事：

1. 为常见核心 marker 补入已核实的 KEGG KO 别名，提高纯 KO abundance 输入的命中率。
2. 在工具输出中显式区分 `core`、`accessory`、`ambiguous` 三层证据，避免把宽泛 transporter 与高置信核心模块混成一个分值。

## 新增的结果文件

`score-functions` 现在会额外输出：

- `phenotype_tier_scores.tsv`

该表的行索引为 `(phenotype, tier)`，其中：

- `core` 表示高置信核心证据
- `accessory` 表示辅助或上下文相关证据
- `ambiguous` 表示底物谱偏宽、容易跨系统共享、因此被刻意降权的证据

推荐解读方式：

- `overall score` 高且 `core` 高：高置信
- `overall score` 中等但只有 `accessory` 高：提示存在相关潜力，但不应强判
- `ambiguous` 高而 `core` 低：优先人工复核

## 本轮纳入的 KO 别名

以下 KO 映射在本轮被明确加入到词典中，用于提升 KO-only 输入兼容性。

### 铁

- `feoB -> K04759`

### 锌

- `znuA / adcA -> K09815`
- `znuB / adcB -> K09816`
- `znuC / adcC -> K09817`

### 锰

- `mntH -> K03322`

### 铜

- `copA -> K17686`
- `copB -> K01533`
- `copZ -> K14588`
- `copY -> K07787`
- `csoR -> K07798`
- `cueO / pcoA -> K07213`
- `cusA -> K07793`
- `cusB -> K07794`
- `cusC -> K07795`
- `cusF -> K07796`

### 维生素 B12 / 钴摄取

- `btuB -> K16092`
- `btuF -> K06858`
- `btuC -> K06073`
- `btuD -> K06074`
- `cbiM -> K02007`
- `cbiN -> K02009`
- `cbiQ -> K02008`
- `cbiO -> K02006`

### 镍

- `nikA / cntA -> K15584`
- `nikB / cntB -> K15585`
- `nikC / cntC -> K15586`
- `nikD / cntD -> K15587`
- `nikE -> K10824`

### 钼

- `modA -> K02020`
- `modB -> K02018`
- `modC -> K02017`
- `modE -> K03576`
- `moaA -> K03639`
- `moaC -> K03637`
- `moaA-moaC fusion -> K20967`
- `moaD -> K03636`
- `moaE -> K03635`
- `moaD-moaE fusion -> K21142`
- `mogA -> K03831`
- `moeA -> K03750`

### 硒

- `selA -> K01042`
- `selD -> K01008`
- `selU / ybbB -> K06917`

## 为什么要分层

单纯把 marker 越加越多，并不会自动更准。相反，它会引入两类误差：

1. 广谱转运子被误当成元素特异核心
2. 调控因子或伴随蛋白把弱信号抬得太高

因此，本轮明确把 marker 分成三层：

### Core

这些 marker 在当前 phenotype 中被视为高置信主证据，例如：

- `FeoB`
- `ZnuABC / AdcABC`
- `MntH`
- `CopA`
- `CusA/B/C/F`
- `BtuB/F/C/D`
- `CbiMNQO`
- `NikABCDE`
- `MoaA/MoaC`
- `MoaD/MoaE`
- `MogA/MoeA`
- `SelA/SelB/SelD`

### Accessory

这些 marker 与相关表型高度相关，但更适合作为补充，而不是单独高置信判定：

- `FeoA/FeoC`
- `ZinT`
- `AdcAII/Lmb`
- `CopZ/CopY/CsoR`
- `CueO/PcoA`
- `corrinoid salvage` 模块
- `Hyp` 成熟蛋白
- `SelU/YbbB`

### Ambiguous

这些 marker 的生物学意义是真实的，但特异性不足，因此需要谨慎解释：

- `TonB/ExbBD`
- `ZupT`

## 这一轮背后的资料依据

本轮主要依据以下检索到的官方或研究来源：

- KEGG pathway hits for zinc transporter `ZnuABC`, results visible as `K09815/K09816/K09817`: [KEGG map02010 search result](https://www.genome.jp/dbget-bin/www_bfind_sub?mode=bfind&max_hit=1000&locale=en&serv=gn&dbkey=pathway&keywords=ZnuABC)
- KEGG result for `FeoB K04759`: [KEGG search](https://www.genome.jp/dbget-bin/www_bfind_sub?mode=bfind&max_hit=1000&locale=en&serv=gn&dbkey=pathway&keywords=FeoB)
- KEGG result for `MntH K03322`: [KEGG search](https://www.genome.jp/dbget-bin/www_bfind_sub?mode=bfind&max_hit=1000&locale=en&serv=gn&dbkey=pathway&keywords=MntH)
- KEGG copper-pathway hits for `CopA`, `CopY`, `CusCFBA`, `CueO`: [KEGG copper transport search](https://www.genome.jp/dbget-bin/www_bfind_sub?mode=bfind&max_hit=1000&locale=en&serv=gn&dbkey=pathway&keywords=Copper%20transport%20system)
- KEGG cobalamin uptake hits for `BtuB/F/C/D`: [KEGG BtuB search](https://www.genome.jp/dbget-bin/www_bfind_sub?mode=bfind&max_hit=1000&locale=en&serv=gn&dbkey=pathway&keywords=BtuB)
- KEGG nickel transporter hits for `NikABCDE`: [KEGG NikA search](https://www.genome.jp/dbget-bin/www_bfind_sub?mode=bfind&max_hit=1000&locale=en&serv=gn&dbkey=pathway&keywords=NikA)
- KEGG molybdenum cofactor module `M00880`: [KEGG M00880](https://www.genome.jp/entry/M00880)
- KEGG selenocompound metabolism `map00450`: [KEGG map00450](https://www.genome.jp/pathway/map00450)

补充研究型来源：

- Ferrous iron transport and Feo system review: https://pmc.ncbi.nlm.nih.gov/articles/PMC5789311/
- Zinc and manganese transport review: https://pmc.ncbi.nlm.nih.gov/articles/PMC4448232/
- Copper homeostasis review: https://pmc.ncbi.nlm.nih.gov/articles/PMC5574447/
- Cobalt transport and B12 comparative genomics: https://www.frontiersin.org/journals/microbiology/articles/10.3389/fmicb.2018.02392/full
- Selenium utilization review: https://pmc.ncbi.nlm.nih.gov/articles/PMC6205751/
