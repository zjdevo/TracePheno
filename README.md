# TracePheno

`TracePheno` 是一个面向微量元素代谢相关菌群表型的功能优先型分析工具。

它主要解决这样一类问题：很多与铁、锌、锰、铜、钴/维生素 B12、镍、钼、硒相关的表型，并不能只靠 16S 分类名或属/种标签稳定推断，因为这些性状往往受到菌株差异、水平基因转移、转运模块替换以及注释粒度变化的强烈影响。

当前版本提供 5 个面向用户的 CLI 子命令：

- `list-phenotypes`
- `score-functions`
- `score-picrust2`
- `build-traits`
- `score-taxa`

如果你是从仓库根目录进入项目，请先看 [`../README.md`](../README.md) 了解整体结构；本文件则聚焦于“如何真正使用软件”。

## 工具能做什么

TracePheno 当前支持 3 条核心分析路线：

1. 直接输入功能矩阵，计算样本级微量元素表型得分。
2. 从基因组或菌株注释矩阵构建可复用的 trait matrix。
3. 结合 taxon abundance 与 trait matrix，估计群落层表型占比。

此外，它还提供了一个专门的 `PICRUSt2` 入口，用于把 16S 推断得到的 KO 表直接映射到微量元素表型。

## 为什么它是“功能优先”

微量元素相关表型通常不适合做纯 taxonomy-based phenotype transfer，原因包括：

- 很多金属相关基因是菌株水平可变的
- 转运、耐受和辅因子相关模块经常发生水平转移
- 同一属内不同菌株在 siderophore、铜耐受、钴摄取、硒利用等方面可能差异很大

因此，TracePheno 默认围绕“功能证据”而不是“分类学标签”组织分析。当前算法的几个核心特征是：

- 内置可追踪的 marker library
- 确定性的 `core-gated` 表型判定
- 显式输出 `core / accessory / ambiguous` 三层证据
- genome trait 推断默认采用 presence/absence 导向逻辑
- 自动生成期刊风格图件和 HTML 报告

## 当前内置表型

当前内置 10 个微量元素相关表型：

- `iron_acquisition`
- `iron_storage_homeostasis`
- `zinc_acquisition`
- `manganese_acquisition`
- `copper_homeostasis_resistance`
- `cobalamin_biosynthesis`
- `cobalamin_transport_cobalt_uptake`
- `nickel_utilization`
- `molybdenum_cofactor_biosynthesis`
- `selenium_utilization`

对应的 YAML 定义文件位于：

- [`tracepheno/data/trace_element_phenotypes.yaml`](tracepheno/data/trace_element_phenotypes.yaml)

查看当前内置表型最直接的方法是：

```bash
tracepheno list-phenotypes
```

如果环境里还没有 `tracepheno` 命令，也可以用：

```bash
python -m tracepheno.cli list-phenotypes
```

## 环境要求

- Python `>=3.10`
- `pip`
- 推荐使用单独的虚拟环境

运行依赖定义在 [`pyproject.toml`](pyproject.toml) 中，主要包括：

- `pandas`
- `numpy`
- `scipy`
- `matplotlib`
- `seaborn`
- `jinja2`
- `PyYAML`

## 安装

### 方案 A：在仓库根目录安装

如果你当前在仓库根目录：

```bash
pip install -e ./releases
cd releases
```

### 方案 B：进入 `releases/` 后安装

```bash
cd releases
pip install -e .
```

安装后，先确认 CLI 可用：

```bash
tracepheno --help
```

如果 `tracepheno` 不在当前环境的 `PATH` 上，请改用：

```bash
python -m tracepheno.cli --help
```

下文中的所有命令默认都假设你当前位于 `releases/` 目录。

## 30 秒快速上手

如果你只是想先确认软件能跑通，建议按这个顺序来：

```bash
tracepheno list-phenotypes
```

```bash
tracepheno score-functions \
  --abundance tracepheno/data/example_function_abundance.tsv \
  --metadata tracepheno/data/example_metadata.tsv \
  --group-column cohort \
  --outdir ../others/results/example
```

```bash
tracepheno score-picrust2 \
  --input tracepheno/data/example_picrust2_ko.tsv \
  --metadata tracepheno/data/example_metadata.tsv \
  --group-column cohort \
  --outdir ../others/results/picrust2_demo
```

随后打开：

- `../others/results/example/report.html`
- `../others/results/picrust2_demo/report.html`

这两步就能让你快速确认：

- 安装是否成功
- 表型库是否可用
- HTML 报告和期刊风格图件是否正常生成

## 你最常用到的目录

- 代码：[`tracepheno/`](tracepheno)
- 内置示例数据：[`tracepheno/data/`](tracepheno/data)
- 包内文档：[`docs/`](docs)
- 已包含的 MGnify 范例输入：[`data/paper_demo_mgnify_2025/`](data/paper_demo_mgnify_2025)
- 已生成的结果与图件：[`../others/results/`](../others/results)

## 输入格式总规则

对于所有“表格输入型”工作流，TracePheno 默认遵循以下约定：

- 第一列是行标识符
- 后续数值列是样本或特征
- metadata 中的样本名必须和丰度矩阵列名完全一致

内部实现上，第一列总是被当作行索引来处理。

### 1. 功能矩阵

适用于：

- `score-functions`
- `build-traits`

推荐结构如下：

```text
feature    sample_A    sample_B
feoB       10          2
znuA       0           8
K02006     4           1
```

第一列可以是：

- 基因名，例如 `feoB`、`znuA`、`selD`
- KEGG KO，例如 `K02006`
- 混合注释串，例如 `K02006 cbiO cobalt transporter ATP-binding protein`

这类输入有几个重要行为：

- 第一列之后如果存在非数值列，会自动忽略
- 缺失数值会被补成 `0`
- 默认会对每个样本列做独立归一化，除非显式传入 `--no-normalize`

### 2. Metadata

推荐结构如下：

```text
sample    cohort
sample_A  control
sample_B  case
```

要求：

- 第一列必须是样本 ID
- 样本 ID 必须与丰度矩阵列名完全一致
- 如果你希望生成 `group_statistics.tsv` 和组间比较图，需要至少一个分组列

内置示例：

- [`tracepheno/data/example_metadata.tsv`](tracepheno/data/example_metadata.tsv)

### 3. PICRUSt2 KO 表

适用于：

- `score-picrust2`

支持的输入包括：

- `pred_metagenome_unstrat.tsv.gz`
- `pred_metagenome_contrib.tsv.gz`
- 任意已经整理好的 KO x sample 宽表

一个典型的 unstratified KO 表可以长这样：

```text
function    description    control_1    control_2    case_1    case_2
K04759      FeoB ...       12           10           1         0
K09815      ZnuA ...       0            1            10        8
```

这个工作流有几个专门的兼容逻辑：

- 如果存在 `description` 列，会自动忽略
- 如果输入是 contribution 表，并且包含 `function` 与 `sample` 列，会先自动聚合成 KO x sample 矩阵
- 读取后会验证输入里是否真的存在 KO-like identifier

内置示例：

- [`tracepheno/data/example_picrust2_ko.tsv`](tracepheno/data/example_picrust2_ko.tsv)

PICRUSt2 详细说明：

- [`docs/picrust2_workflow.md`](docs/picrust2_workflow.md)

### 4. Taxon abundance 矩阵

适用于：

- `score-taxa`

推荐结构如下：

```text
taxon    sample_A    sample_B
Genome_1 0.30        0.10
Genome_2 0.20        0.40
Genome_3 0.50        0.50
```

这里的行名必须和 trait matrix 的行名一致。

### 5. Trait matrix

适用于：

- `score-taxa`
- 或者由 `build-traits` 生成

推荐结构如下：

```text
taxon    iron_acquisition    zinc_acquisition    selenium_utilization
Genome_1 1                   0                   1
Genome_2 0                   1                   0
Genome_3 1                   1                   0
```

trait 值可以是：

- 二值 `0 / 1`
- `0` 到 `1` 之间的连续数值

默认情况下，`build-traits` 会输出二值 calls。若想要连续 trait score，请加 `--continuous`。

## 工作流 1：直接分析功能矩阵

当你已经有 KO、基因家族、eggNOG 或其他注释导出的功能表时，使用 `score-functions`。

### 示例命令

```bash
tracepheno score-functions \
  --abundance tracepheno/data/example_function_abundance.tsv \
  --metadata tracepheno/data/example_metadata.tsv \
  --group-column cohort \
  --outdir ../others/results/example
```

### 主要参数解释

- `--abundance`：必填，功能丰度表
- `--metadata`：可选，样本 metadata
- `--group-column`：可选，metadata 中用于分组比较的列名
- `--outdir`：必填，输出目录
- `--presence-cutoff`：将 feature 视为“出现”的最低丰度阈值
- `--no-normalize`：关闭按列归一化
- `--phenotype-config`：指定自定义 YAML 表型库

### 主要输出

这个命令会生成：

- `phenotype_scores.tsv`
- `phenotype_coverage.tsv`
- `phenotype_abundance.tsv`
- `phenotype_tier_scores.tsv`
- `phenotype_calls.tsv`
- `phenotype_thresholds.tsv`
- `marker_contributions.tsv`
- `marker_matches.tsv`
- `group_statistics.tsv`，如果提供了 metadata 且分组有效
- `report.html`
- `results_summary.md`
- 多张图件以及一个 `publication/` 子目录

### 核心输出如何理解

- `phenotype_scores.tsv`：每个样本每个表型的连续得分
- `phenotype_calls.tsv`：确定性的表型判定结果
- `phenotype_thresholds.tsv`：每个表型的 `threshold_hint`、`required_core_hits` 和判定规则
- `phenotype_tier_scores.tsv`：`core / accessory / ambiguous` 三层证据拆解
- `marker_contributions.tsv`：哪些 marker 贡献了主要得分
- `marker_matches.tsv`：输入表中哪些行被识别为 marker

## 工作流 2：分析 PICRUSt2 KO 预测结果

如果你的功能输入来自 `PICRUSt2` 而不是直接的 metagenome/genome annotation，请使用 `score-picrust2`。

### 内置示例命令

```bash
tracepheno score-picrust2 \
  --input tracepheno/data/example_picrust2_ko.tsv \
  --metadata tracepheno/data/example_metadata.tsv \
  --group-column cohort \
  --outdir ../others/results/picrust2_demo
```

### 真实 PICRUSt2 unstratified 输出示例

```bash
tracepheno score-picrust2 \
  --input KO_metagenome_out/pred_metagenome_unstrat.tsv.gz \
  --metadata sample_metadata.tsv \
  --group-column group \
  --outdir ../others/results/picrust2_real
```

### contribution 输出示例

```bash
tracepheno score-picrust2 \
  --input KO_metagenome_out/pred_metagenome_contrib.tsv.gz \
  --metadata sample_metadata.tsv \
  --group-column group \
  --outdir ../others/results/picrust2_real
```

### 这个工作流的特殊之处

- contribution 表会自动聚合为 KO x sample 宽表
- 解析后的矩阵会单独保存为 `picrust2_resolved_ko_matrix.tsv`
- 后续得分、图件和报告逻辑与 `score-functions` 保持一致

### 额外输出

除常规结果外，这个工作流还会写出：

- `picrust2_resolved_ko_matrix.tsv`
- `publication/figure_1_global_landscape.(png|pdf)`
- `publication/figure_2_structure_and_drivers.(png|pdf)`
- `publication/figure_3_differential_statistics.(png|pdf)`，如果存在可视化的组间差异统计
- `publication/figure_legends.md`
- `publication/figure_manifest.tsv`
- `publication/results_summary.md`

## 工作流 3：从基因组注释构建 trait matrix

如果你要先推断 genome/taxon 的表型能力，再在多个 cohort 中复用，请使用 `build-traits`。

### 默认二值 trait matrix

```bash
tracepheno build-traits \
  --abundance genome_features.tsv \
  --out traits.tsv
```

### 连续 trait matrix

```bash
tracepheno build-traits \
  --abundance genome_features.tsv \
  --continuous \
  --out traits_continuous.tsv
```

### 重要说明

- 默认是 presence/absence 导向，会输出二值 calls
- `--continuous` 会输出连续 phenotype score
- `--presence-cutoff` 与 `--no-normalize` 的语义与 `score-functions` 保持一致

这个工作流很适合先构建一个 reference trait panel，然后在不同 taxon abundance 数据集上重复使用。

## 工作流 4：用 taxon abundance + trait matrix 计算群落表型

如果你已经有：

- 样本 x taxon 丰度表
- taxon x phenotype trait matrix

就使用 `score-taxa`。

### 示例命令

```bash
tracepheno score-taxa \
  --abundance taxon_abundance.tsv \
  --traits traits.tsv \
  --metadata sample_metadata.tsv \
  --group-column condition \
  --outdir ../others/results/taxa_mode
```

### 它做的事情

该工作流会将 taxon 丰度与 trait 值相结合，计算样本层面的群落表型强度。

### 这个工作流的输出

与 `score-functions` 相比，这条路线更偏向“群落表型总量”，所以输出会更轻一些，主要包括：

- `phenotype_scores.tsv`
- `group_statistics.tsv`，如果提供 metadata
- `report.html`
- `results_summary.md`
- heatmap、差异图、sample embedding、group-level 图件
- `publication/` 子目录

这条路线不会生成以下 feature-level 输出：

- `phenotype_coverage.tsv`
- `phenotype_calls.tsv`
- `marker_contributions.tsv`

因为它的起点不是原始 marker 证据，而是预先构建好的 trait matrix。

## 工作流 5：查看仓库中已附带的 MGnify 论文范例

仓库中已经附带了一个基于 MGnify representative human-gut genomes 整理出的论文级示例数据与结果，你可以直接查看，不需要额外下载。

### 已包含的输入

- [`data/paper_demo_mgnify_2025/feature_matrix.tsv`](data/paper_demo_mgnify_2025/feature_matrix.tsv)
- [`data/paper_demo_mgnify_2025/genome_metadata.tsv`](data/paper_demo_mgnify_2025/genome_metadata.tsv)
- [`data/paper_demo_mgnify_2025/selected_genomes.tsv`](data/paper_demo_mgnify_2025/selected_genomes.tsv)
- [`data/paper_demo_mgnify_2025/paper_context.json`](data/paper_demo_mgnify_2025/paper_context.json)

### 已包含的输出

- [`../others/results/paper_demo_mgnify_2025/report.html`](../others/results/paper_demo_mgnify_2025/report.html)
- [`../others/results/paper_demo_mgnify_2025/results_summary.md`](../others/results/paper_demo_mgnify_2025/results_summary.md)
- [`../others/results/paper_demo_mgnify_2025/publication/`](../others/results/paper_demo_mgnify_2025/publication/)

### 解读说明

- [`docs/paper_demo_mgnify_2025.md`](docs/paper_demo_mgnify_2025.md)

## 可视化与投稿风格输出

TracePheno 不仅输出表格，还会自动生成期刊风格图件。当前版本常见输出包括：

- `overview_dashboard.png`
- `phenotype_landscape.png`
- `differential_phenotype_map.png`
- `phenotype_score_heatmap.png`
- `phenotype_clustered_heatmap.png`
- `group_mean_scores.png`
- `group_distribution_scores.png`
- `group_trajectory_scores.png`
- `sample_embedding.png`
- `tier_evidence_summary.png`
- `marker_contribution_panels.png`
- `publication/figure_*.png`
- `publication/figure_*.pdf`

这些图件既适合探索性分析，也适合后续整理成汇报或论文图。

## 确定性判定与结果解释

当前算法不再使用依赖当前队列分布的 threshold scanning，而是采用更明确的确定性规则：

- 每个表型有固定的 `threshold_hint`
- 存在 core marker 的表型使用 `deterministic core-gated` 判定
- 多模块通路可以通过 `core_min_hits` 要求多个核心 block 同时满足
- genome trait 推断默认回到 presence/absence 导向

你可以从以下位置直接查看这些规则：

- 结果中的 [`phenotype_thresholds.tsv`](../others/results/paper_demo_mgnify_2025/phenotype_thresholds.tsv)
- 内置定义文件 [`tracepheno/data/trace_element_phenotypes.yaml`](tracepheno/data/trace_element_phenotypes.yaml)
- 算法升级说明 [`docs/algorithm_scientificity_upgrade_20260315.md`](docs/algorithm_scientificity_upgrade_20260315.md)

## 如何自定义表型库

如果你想扩展内置表型，最稳妥的方式是：

1. 复制一份 [`tracepheno/data/trace_element_phenotypes.yaml`](tracepheno/data/trace_element_phenotypes.yaml)
2. 在副本中新增或修改 phenotype 定义
3. 运行时用 `--phenotype-config` 指向你的 YAML

示例：

```bash
tracepheno score-functions \
  --abundance my_function_table.tsv \
  --metadata my_metadata.tsv \
  --group-column group \
  --phenotype-config my_trace_phenotypes.yaml \
  --outdir results/custom_library
```

内置 YAML 中每个 phenotype 通常包含这些字段：

- `id`
- `name`
- `element`
- `summary`
- `threshold_hint`
- `core_min_hits`
- `markers`

每个 marker block 一般包含：

- `id`
- `tier`
- `logic`
- `min_hits`
- `weight`
- `notes`
- `genes`

如果你是第一次自定义，最推荐的方式不是从零写 YAML，而是复制现有表型再做修改。

## 包内自带示例数据

随包附带的最小示例包括：

- [`tracepheno/data/example_function_abundance.tsv`](tracepheno/data/example_function_abundance.tsv)
- [`tracepheno/data/example_picrust2_ko.tsv`](tracepheno/data/example_picrust2_ko.tsv)
- [`tracepheno/data/example_metadata.tsv`](tracepheno/data/example_metadata.tsv)

它们的作用主要是：

- 验证安装是否正确
- 快速熟悉 CLI 参数
- 观察各类输出文件长什么样

## 常见问题与排错

### 1. 找不到 `tracepheno` 命令

请先试：

```bash
python -m tracepheno.cli --help
```

如果这样可以运行，说明代码安装没有问题，只是当前环境里没有把 `tracepheno` script 放到可执行路径上。

### 2. metadata 没有生效

请检查：

- 第一列是不是样本 ID
- 样本 ID 是否与丰度矩阵列名完全一致
- 是否传入了 `--group-column`

如果 metadata 或 group column 无法正确对齐，就不会生成分组统计和组间比较图。

### 3. 我的输入里有 `description` 列

没关系。第一列之后的非数值列会在数值化时自动被丢弃，不会影响计算。

### 4. 我只有 taxonomy，没有功能表

这种情况下建议：

- 用 `PICRUSt2` 后走 `score-picrust2`
- 或先构建一个 trait matrix，再走 `score-taxa`

TracePheno 有意避免直接从 taxonomy 名称去“猜测”金属相关表型。

### 5. 为什么有些图没有生成

有些图依赖 metadata 和有效分组。例如：

- 没有 metadata，就不会有 group-level heatmap 和分布图
- 没有有效的组间比较，就不会有完整的 differential plot

### 6. 什么时候该用 `--no-normalize`

大多数 cohort 级功能矩阵分析，保留默认归一化更合适。

只有在以下情况才建议考虑 `--no-normalize`：

- 你的矩阵已经按你想要的方式归一化过
- 你的输入本身就是 binary / presence-absence
- 你明确希望用原始量纲参与后续打分

## 仓库内相关文档

- 研究与设计摘要：[`docs/research_summary.md`](docs/research_summary.md)
- PICRUSt2 使用说明：[`docs/picrust2_workflow.md`](docs/picrust2_workflow.md)
- marker 精修第 2 轮：[`docs/marker_curation_round2.md`](docs/marker_curation_round2.md)
- marker 精修第 3 轮：[`docs/marker_curation_round3.md`](docs/marker_curation_round3.md)
- 算法科学性升级：[`docs/algorithm_scientificity_upgrade_20260315.md`](docs/algorithm_scientificity_upgrade_20260315.md)
- MGnify 论文范例说明：[`docs/paper_demo_mgnify_2025.md`](docs/paper_demo_mgnify_2025.md)

## 代码与论文

- GitHub 仓库：<https://github.com/zjdevo/TracePheno>
- 论文正文：[`../latex/main.tex`](../latex/main.tex)
- 参考文献：[`../latex/refs.bib`](../latex/refs.bib)

## 推荐的第一次使用顺序

如果你第一次接触这个项目，建议按下面顺序操作：

1. 用 `pip install -e ./releases` 安装
2. 运行 `tracepheno list-phenotypes`
3. 用内置示例运行一次 `score-functions`
4. 打开生成的 `report.html`
5. 再运行一次 `score-picrust2`
6. 如果需要群落层表型估计，再用 `build-traits` + `score-taxa`

这一套流程足够覆盖项目里最关键的功能，而且启动成本最低。
