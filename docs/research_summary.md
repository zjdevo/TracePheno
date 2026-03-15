# 微量元素代谢菌群表型工具调研摘要

## 任务范围

目标是开发一个面向微量元素代谢相关能力的微生物群落表型分析工具，分析对象包括铁获取、锌与锰摄取、铜稳态、钴/维生素 B12 合成、镍利用、钼辅因子合成和硒利用等能力。

本次调研重点关注 2018 年到 2026 年 3 月之间仍有现实指导意义的资源，并以既有菌群表型工具和 trait workflow 作为设计参照。

## 结论先行

1. 经典菌群表型工具的分析框架值得借鉴，但其默认输入与表型空间不适合直接迁移到微量元素代谢问题。
2. 微量元素代谢性状更适合从功能层或基因组层建模，而不是仅凭 16S taxonomy 推断。
3. 一个合理的首版实现路径是：
   - 用 KEGG 模块和经典金属稳态文献定义核心 marker set
   - 用 BacMet 思路扩展金属耐受与外排相关 marker
   - 用 MetaTraits / Traitar 式 workflow 构建 taxon trait matrix
   - 在样本层保留确定性判定、组间比较和贡献拆解

## 1. 经典表型工具提供了什么

经典菌群表型工具明确展示了三个对本项目最有价值的设计点：

- 它把 phenotype 看成一组可映射到注释特征的离散能力。
- 它允许用户使用 KEGG level 3 feature 自定义 phenotype。
- 它会为每个 phenotype 选择一个阈值，并输出样本间比较和 taxon contribution。

这意味着，我们完全可以继承这类工具的“分析骨架”，但把 phenotype dictionary 换成微量元素代谢 marker set，并把输入改成更靠谱的功能层矩阵。

## 2. 为什么不建议直接从 16S taxonomy 猜微量元素表型

与好氧性、革兰氏染色、生物膜形成这类较稳定 trait 相比，金属相关性状存在几个问题：

- 同属不同株的金属获取和耐受能力差异很大。
- siderophore、铜外排、钴/镍转运等模块常常位于可移动遗传元件上。
- 分类学到功能的映射在这类 trait 上容易失真。

因此，默认输入应该是：

- KO / gene abundance
- MAG / isolate genome annotation matrix
- taxon abundance + 自建 trait matrix

## 3. 可直接复用的数据资源

### KEGG

KEGG 最适合定义“核心代谢能力”：

- `M00122` 对应 vitamin B12 transport system
- `M00245` 对应 cobalt/nickel transport system
- `map00450` 对应 selenocompound metabolism

类似地，钼辅因子、B12 合成和金属转运相关 gene family 可以从 KEGG 模块或 KO 页面中提取核心成分。

### BacMet

BacMet 2018 更新版强调，它同时收录实验验证和预测的抗菌剂 / 金属耐受基因，是构建“金属耐受 / 外排 / 解毒”扩展层最合适的数据库思路之一。它特别适合支撑：

- 铜外排与耐受
- 锌/镉/钴跨膜外排
- 砷、汞等氧阴离子 / 重金属解毒

### MetaTraits

2025 年的 MetaTraits 提供了一个大规模 microbial trait database，整合培养性状、文献记录与 genome-based prediction。它对于后续把 `TracePheno` 从功能模式扩展到“taxonomy + reference trait matrix”模式非常关键，因为它说明 trait matrix 可以通过多源整合来构建，而不必只依赖单一数据库。

### Traitar

Traitar 证明了“从基因组特征到 phenotype prediction”的基本工作流是可操作的。对本项目来说，它更像是一条工程路线参考，而不是直接使用的数据库。

## 4. 为什么首版 phenotype dictionary 只纳入这些模块

首版内置了 10 类 phenotype，原则是“有明确 marker、跨菌群较常见、能从标准功能注释中识别”：

1. 铁获取
2. 铁储存 / 稳态
3. 锌获取
4. 锰获取
5. 铜稳态 / 耐受
6. 维生素 B12 合成
7. B12 转运 / 钴摄取
8. 镍利用
9. 钼辅因子合成
10. 硒利用

没有把所有重金属耐受系统一次性塞进 MVP，是因为：

- 不少系统更偏环境毒理学而非“代谢能力”
- 同源外排泵的功能边界容易过宽
- 需要更多 curated negative set 来降低误报

## 5. 工具设计选择

### 已保留的核心思路

- phenotype dictionary
- 确定性判定
- 样本组间统计比较
- trait / marker contribution 输出

### 做出的关键修改

- 默认从 `feature abundance -> phenotype score`，而不是 `taxonomy -> phenotype`
- 输出连续的 `coverage`、`abundance`、`combined score`
- taxon 模式要求用户显式提供或自行构建 trait matrix
- 当前实现已进一步改为“required core block + accessory support”的确定性判定，不再对同一批样本做数据依赖的自动找阈值

## 6. MVP 的证据边界

本工具适合回答：

- 哪些样本的铁获取相关功能更强？
- 哪个组别的铜稳态 / 排出能力更高？
- 哪些 marker gene 对某个 phenotype 的得分贡献最大？
- 如果我有 genome annotation，哪些 genome 具有某种微量元素表型？

本工具当前不应该过度解释为：

- 某个属一定具备某种金属代谢能力
- 仅凭 16S OTU 就能稳定重建这些表型
- marker 出现就等于活跃表达或真实生态位实现

## 7. 推荐的后续扩展

1. 接入 BacMet 派生的重金属耐受扩展包。
2. 针对 HUMAnN、eggNOG、KOfamScan、DRAM 增加官方 feature alias preset。
3. 基于 GTDB representative genomes 预构建一个大规模 taxon trait reference。
4. 加入 pathway completeness learning 或 HMM score，而不仅是基于 feature ID 的 marker hit。

## 8. 第二轮精修结果

在 2026-03-15 的第二轮资料补查后，词典又做了一轮“收紧而不是单纯扩充”的修订，详见 [marker_curation_round2.md](marker_curation_round2.md)。这轮调整主要包括：

- 去掉 `fur`、`zur`、`mntR`、`nikR`、`cueR` 这类过泛调控因子，降低“很多菌都像有这个表型”的风险
- 下调 `zupT`、`tonB/exbBD` 这类底物谱宽或系统级供能组件的权重
- 补入更常见、但首版遗漏的核心模块，例如 `FhuABCD`、`Isd`、`SitABCD`、`NiCoT`、`MoaD-MoaE fusion`
- 将 B12 合成拆为厌氧核心、late completion 与 aerobic signature，并纠正 `M00122` 的模块解释
- 将硒表型的核心证据收紧到 `SelA/SelB/SelD`，把 `SelU/YbbB` 降为低权重辅助信号
- 词典条目增加同义名和 KO 号联配形式，以提升对真实注释表的兼容性

## 9. 第三轮精修结果

在 2026-03-15 的第三轮补查后，工具进一步把“资料结论”落到了计算规则，详见 [marker_curation_round3.md](marker_curation_round3.md)。这轮新增的要点是：

- 为 Fe、Zn、Mn、Cu、B12/Co、Ni、Mo、Se 的常见核心 marker 补入已核实的 KEGG KO 别名
- 新增 `core / accessory / ambiguous` marker 分层，用来区分高置信核心证据和低特异性辅助信号
- `score-functions` 额外导出 `phenotype_tier_scores.tsv`，便于人工快速识别“高分但核心证据不足”的样本
- 纠正了 `btuF` 的 KO 别名，保留 `K06858`，移除前一版中不够稳妥的 `K06075`

## 10. 第四轮算法科学性升级

在 2026-03-15 的第四轮补查中，重点不再只是“补 marker”，而是把 scoring rule 本身改得更符合近期方法学文献：

- 去掉 cohort-dependent 的支持度缩放，避免同一样本因为和谁一起分析而改变分数
- 去掉通过样本方差自动寻找二值阈值的做法，改成确定性的 `threshold_hint + required core hits`
- 对需要多块核心模块共同成立的表型显式加入 `core_min_hits`
  目前 `cobalamin_biosynthesis` 需要 2 个 core block，`molybdenum_cofactor_biosynthesis` 需要 3 个 core block
- `build-traits` 默认改为 presence/absence 导向，不再让 gene copy number 自动提高 genome trait score

这一轮改动更接近 KEGG / MAPLE 的 module completeness 思路、MacSyFinder 的 mandatory/accessory system detection 逻辑，以及 Traitar / MetaPathPredict / DNNGIOR 这类 genome phenotype prediction 方法对不完整基因组问题的处理方式。

## 参考来源

- BacMet update paper: https://academic.oup.com/nar/article/46/D1/D737/4600167
- MetaTraits paper: https://www.nature.com/articles/s41564-025-02053-8
- Traitar paper: https://microbiomejournal.biomedcentral.com/articles/10.1186/s40168-016-0176-1
- Zinc and manganese transport review: https://pmc.ncbi.nlm.nih.gov/articles/PMC4448232/
- Cobalamin biosynthesis module: https://www.genome.jp/entry/M00924
- Vitamin B12 transport module: https://www.genome.jp/entry/M00122
- Cobalt/nickel transport module: https://www.genome.jp/entry/M00245
- Selenocompound metabolism: https://www.genome.jp/pathway/map00450
