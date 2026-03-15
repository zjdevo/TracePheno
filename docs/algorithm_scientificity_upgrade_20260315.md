# TracePheno 算法科学性升级说明

## 调研范围

本轮算法升级以 2024 年到 2026 年 3 月的近期方法学文献为主，同时保留少量奠基性工作作为方法来源。重点检索了四类问题：

1. 微生物功能模块完备性应该怎样量化
2. 系统检测中 mandatory / accessory component 应该怎样区分
3. 基因组 / MAG 表型预测为什么不能简单奖励 copy number
4. PICRUSt2 这类功能预测结果应该怎样保守解释

## 这轮先解决了什么问题

旧版实现里最影响科学性的点主要有四个：

1. marker 支持度会按当前批次样本的最大值重新缩放，导致同一样本和不同队列一起跑时分数会漂移
2. 二值表型调用通过扫描阈值并最大化样本方差来决定，判定边界取决于当前数据集而不是生物学规则
3. genome / MAG trait 推断会把 raw gene count 直接送进打分，容易把 copy number 当成 trait 强度
4. 像 B12 合成、钼辅因子合成这种需要多块核心模块共同成立的表型，没有显式的 required core block 约束

## 文献给出的可操作原则

### 1. 用 module completion，而不是 cohort-relative scaling

KEGG module 和 MAPLE 的核心思想都是把功能能力表示为模块完备性，而不是和同一批样本里“最强的那个样本”做相对缩放。对本项目来说，这意味着 marker support 应该是样本内、绝对有界、可解释的量。

- KEGG module: [KEGG MODULE database](https://www.genome.jp/kegg/module.html)
- MAPLE 2.3.0: [PubMed](https://pubmed.ncbi.nlm.nih.gov/27899639/)

因此本轮把 abundance support 改成了样本内的有界变换：

- 功能丰度模式下使用绝对有界的 abundance transform，而不再除以 cohort 内最大值
- genome trait 模式下直接回到 presence/absence 逻辑，不再奖励多拷贝

### 2. phenotype call 应该基于 required core block，而不是“谁让方差最大”

MacSyFinder 的系统检测思想非常清楚：系统通常由 mandatory、accessory 和 forbidden 组分定义，判定时首先看核心组分是否满足。这个逻辑比“扫描阈值让二元结果最有方差”更符合生物学系统识别。

- MacSyFinder: [PMC](https://pmc.ncbi.nlm.nih.gov/articles/PMC4145919/)

因此本轮把二值判定改成了：

- `threshold_hint` 只作为固定判定阈值
- `core_min_hits` 明确指定一个 phenotype 至少要满足多少个 core marker set
- accessory / ambiguous 证据只加分，不再替代 core evidence

### 3. genome phenotype prediction 更接近 phyletic pattern，而不是 copy-number scoring

Traitar 证明了从 genome feature 到 phenotype prediction 的 workflow 是可行的，而且其核心输入是基因家族的存在缺失模式。近年的 MetaPathPredict 和 DNNGIOR 也进一步说明，不完整基因组上的 pathway / reaction recovery 需要显式建模缺失，而不是把观测到的 copy number 直接当成真实能力强弱。

- Traitar: [Microbiome](https://microbiomejournal.biomedcentral.com/articles/10.1186/s40168-016-0176-1)
- MetaPathPredict: [PMC](https://pmc.ncbi.nlm.nih.gov/articles/PMC11565237/)
- DNNGIOR: [PubMed](https://pubmed.ncbi.nlm.nih.gov/38868264/)

因此 `build-traits` 现在默认使用 presence/absence-oriented scoring。连续 trait score 反映的是模块证据强度，而不是 gene dosage。

### 4. PICRUSt2 结果应当把 abundance 当作 secondary evidence

PICRUSt2 及其 2025 年的单细胞参考扩展版说明，功能预测精度和参考覆盖度密切相关。也就是说，预测 KO abundance 可以作为有用证据，但不应成为压倒 core completion 的唯一信号。

- PICRUSt2: [Nature Biotechnology](https://pubmed.ncbi.nlm.nih.gov/32483366/)
- PICRUSt2-SC: [PubMed](https://pubmed.ncbi.nlm.nih.gov/40581035/)

因此本轮保留 abundance，但把它降为 secondary evidence：

- 功能矩阵模式仍然允许高丰度样本得到更高连续分数
- 但二值 calls 现在首先由 core evidence 是否满足决定

### 5. marker library 仍然必须靠 curated evidence，而不是宽松迁移

BacMet 和 AMRFinderPlus 都表明，和金属耐受、转运、解毒相关的 marker 很容易因为家族过宽而误报。对于微量元素表型，curated marker library 和分层证据输出比“尽可能多匹配同义名”更重要。

- BacMet: [Nucleic Acids Research](https://academic.oup.com/nar/article/46/D1/D737/4600167)
- AMRFinderPlus: [PMC](https://pmc.ncbi.nlm.nih.gov/articles/PMC6811410/)

这也解释了为什么本项目继续保留 `core / accessory / ambiguous` 三层证据，而不是把所有 marker 平均相加。

## 已经落实到代码里的改进

### 1. 去掉 cohort-dependent 打分

`score_feature_matrix()` 不再使用 `support / support.max()` 这类批次内相对缩放。现在的 evidence transform 是样本内、绝对有界的，因此同一样本不会因为和谁一起分析而改分。

### 2. 改成确定性 core-gated 判定

每个 phenotype 现在都使用固定的 `threshold_hint`，并允许通过 `core_min_hits` 指定必须满足的核心 marker set 数量。

当前已显式收紧的表型包括：

- `cobalamin_biosynthesis`: 需要 2 个 core block
- `molybdenum_cofactor_biosynthesis`: 需要 3 个 core block

### 3. genome trait 构建默认采用 presence/absence 逻辑

`build_trait_matrix_from_features()` 现在会把基因组特征矩阵按 presence/absence 处理，再做 phenotype inference。这样 genome_1 和 genome_2 即使只是在同一 marker 上出现 1 拷贝和 5 拷贝，也不会被自动判成“第二个菌株表型更强”。

### 4. 阈值输出更可解释

`phenotype_thresholds.tsv` 现在除了 `threshold_hint` 外，还会额外输出：

- `required_core_hits`
- `available_core_marker_sets`
- `decision_rule`

这能直接回答“这个 phenotype 为什么被叫成 1 或 0”。

## 这轮新增的回归验证

测试里已经新增三类科学性保护：

1. 同一样本加入一个更强或更弱的无关样本后，分数和 calls 不应改变
2. 多块核心模块共同成立的路径，命中一半不能误判为存在
3. genome trait 连续分数默认不应因为 copy number 升高而自动变大

## 目前仍然保守保留的限制

这轮没有做两件事，而且是刻意没有激进处理：

1. 低完整度 MAG 的缺失 rescue 仍未默认启用
   原因是文献支持“要显式处理不完整性”，但并不支持简单地用一个经验比例把缺失 marker 全部补回来。当前版本宁愿保守，也不做容易引入假阳性的激进插补。
2. PICRUSt2 的 NSTI / reference distance 还没有显式并入不确定性传播
   这仍然值得做，但需要在输入层明确接收 sample-level quality metric，避免凭经验常数硬性下调分数。

## 下一步最值得继续增强的方向

1. 给 MAG trait 模式增加“低完整度样本输出 NA 或 low-confidence absence”的保守机制
2. 为 PICRUSt2 模式接入 NSTI-aware uncertainty 输出
3. 把别名匹配从宽松 token intersection 进一步收紧到 curated synonym table、KO 优先匹配和必要时的 HMM/profile 支持
4. 对需要复杂并列 / 替代分支的 phenotype，继续把 YAML 从“marker set 列表”升级到更接近 pathway grammar 的定义方式
