# 常见微量元素表型词典第二轮精修说明

更新时间：2026-03-15

本轮精修的目标不是简单“多加一些基因”，而是同时提升两件事：

1. 常见微量元素表型的生物学特异性
2. 对真实注释结果中同义名、KO 号、融合基因名称的兼容性

## 本轮做了什么

### 1. 去掉过泛的调控基因

首版为了覆盖面，曾把一些全局调控因子也纳入表型，例如：

- `fur`
- `zur`
- `mntR`
- `nikR`
- `cueR`

这些基因在金属稳态里确实重要，但它们常常“比具体代谢能力更普遍”，容易让表型变成“很多菌都有一点”。第二轮里，这些因子被移除或只在少数系统中保留为极低权重的辅助证据。

### 2. 降低 promiscuous transporter 的权重

一些转运蛋白会跨多个二价金属共享底物谱，直接高权重纳入会带来误判。最典型的是：

- `zupT`

因此第二轮把这类 marker 改为低权重辅助信号，而不再作为核心判定依据。

### 3. 更强调“核心模块”而不是单个常见名字

例如：

- 锌获取优先看 `ZnuABC / AdcABC`
- 锰获取优先看 `MntH`、`MntABC-like`、`SitABCD-like`
- 铜耐受优先看 `CopA / CusCFBA / CueO`
- 钼辅因子优先看 KEGG `M00880` 的保守核心，而不是只看 `mobA`
- 硒利用优先看 `SelA/SelB/SelD`

### 4. 支持同义名和 KO 号合并匹配

词典现在允许一个逻辑 marker 用一个条目表达多个别名，例如：

- `btuB|K16092`
- `cbiO|K02006`
- `moaD-moaE|moaE-moaD|K21142`

打分时会把这些当成“同一个逻辑 marker”，避免同一个 feature 因为同时带基因名和 KO 号被重复计分。

## 元素级改动摘要

## 铁

改动重点：

- 提高 `FeoB` 的权重，因为它是 Feo 系统核心，而 `FeoA/FeoC` 只作为辅助
- 把 `TonB/ExbBD` 降为低权重，因为它们为多种外膜摄取系统供能，特异性不足
- 补入 `FhuABCD`、`Isd` 等常见摄铁/血红素系统
- 将铁储存表型改为以 `bfr/ftnA/ftnB/dps` 为主，移除 `Fur`

依据：

- Feo 系统综述显示 `FeoB` 是核心跨膜转运蛋白，而 `FeoC` 并非普遍存在。
- 铁获取系统存在明显的 ferric、ferrous、heme 三条主路线，不宜只靠单个 `tonB` 类基因判断。

## 锌

改动重点：

- 以 `ZnuABC / AdcABC` 作为高权重核心
- 保留 `ZinT`、`AdcAII/Lmb` 作为辅助锌捕获模块
- 将 `ZupT` 下调为低权重
- 移除 `Zur`

依据：

- 文献反复指出高亲和力锌获取核心是 `ZnuABC` 或同源 `AdcABC`，而 `ZupT` 更偏广谱二价金属摄取。

## 锰

改动重点：

- 以 `MntH`、`MntABC-like`、`SitABCD-like` 作为主干
- 增加 `Mts/Slo/SsaB` 等常见别名
- 移除 `MntR`

依据：

- 细菌锰获取最常见的高置信路线是 `MntH` 和 ABC 型 `MntABC/SitABCD`。

## 铜

改动重点：

- 提高 `CopA/CopB` 权重
- 保留 `CusCFBA` 与 `CueO/CueP`
- 用 `CopZ/CopY/CsoR` 代表 Gram-positive/Gram-negative 常见伴随模块
- 移除 `CutC/GolS` 这类更偏上下文依赖或调控型信号

依据：

- 铜稳态的主轴是外排和解毒，而不是单个调控子是否存在。

## 钴 / 维生素 B12

改动重点：

- 将 B12 合成拆成：
  - 厌氧 corrin ring 核心
  - late completion
  - aerobic signature
- 纠正原先把 `M00122` 当作 B12 转运模块的错误；它实际上是 cobalamin biosynthesis 的一部分
- B12 转运 / 钴摄取表型中，把 `BtuB/F/C/D` 与 `CbiMNQO` 分开建模
- 加入 `cbiZ/cblZ` 等 salvage 相关 marker

依据：

- 比较基因组研究表明，`cbiLHFDGJTECA`、`cobGF`、`cobUSC` 等 signature 对区分 de novo 合成与 salvage 很有用。

## 镍

改动重点：

- 以 `NikABCDE` 和 `NiCoT family (NixA/HoxN)` 为转运核心
- 以 `HypABCDEF` 代表氢化酶成熟
- 将 urease 分成结构和辅助两部分
- 移除 `NikR`

依据：

- 镍利用更多体现为“运进来 + 正确装配给酶”，因此单靠调控因子或单个结构酶并不稳。

## 钼

改动重点：

- 按 KEGG `M00880` 重新组织 MoCo 核心：
  - `moaA/moaC`
  - `moaD/moaE`
  - `mogA/moeA`
- `mobA/mobB` 改成低权重扩展，因为它们更偏 bis-MGD
- `modABC` 作为钼酸根摄取模块保留

依据：

- 第二轮更接近 KEGG 模块定义，避免把 `mobA` 误当成“所有 MoCo 都必须有”的核心。

## 硒

改动重点：

- `SelA/SelB/SelD` 提升为绝对核心
- `SelU/YbbB` 下调为低权重，因为它更偏 selenouridine
- 保留 `SrdABC` 作为 selenium respiration 相关信号

依据：

- Sec 插入和 selenouridine 修饰在功能上不等价，不能混成同一强证据。

## 使用建议

如果你的输入是：

- `HUMAnN` KO abundance：优先保留 KO 号与 gene symbol 的联合注释
- `eggNOG`：建议先抽取 gene symbol，再配合 KO 列
- `KOfamScan`：本轮词典对部分关键模块已经兼容 KO 号，但仍建议保留 gene name

如果后续要继续提精度，最值得做的三件事是：

1. 针对每个元素建立 `core / accessory / ambiguous` 三层 marker 体系
2. 给每个 marker 增加 KO / EC / TIGRFAM / PFAM 多重别名
3. 加入 pathway-completeness 打分，而不是只按 marker hit 聚合

## 关键来源

- Feo and bacterial ferrous iron transport: https://pmc.ncbi.nlm.nih.gov/articles/PMC5789311/
- Zinc and manganese transport review: https://pmc.ncbi.nlm.nih.gov/articles/PMC4448232/
- Zinc homeostasis review: https://pmc.ncbi.nlm.nih.gov/articles/PMC5420566/
- Copper homeostasis review: https://pmc.ncbi.nlm.nih.gov/articles/PMC5574447/
- Comparative genomics of cobalt transport and B12 synthesis: https://www.frontiersin.org/journals/microbiology/articles/10.3389/fmicb.2018.02392/full
- KEGG cobalamin biosynthesis modules:
  - https://www.genome.jp/entry/M00924
  - https://www.genome.jp/entry/M00122
- KEGG cobalt/nickel transport system: https://www.genome.jp/entry/M00245
- KEGG molybdenum cofactor biosynthesis: https://www.genome.jp/entry/M00880
- Selenium utilization review: https://pmc.ncbi.nlm.nih.gov/articles/PMC6205751/
