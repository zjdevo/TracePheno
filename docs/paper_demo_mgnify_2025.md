# MGnify Paper Demo for TracePheno

## Representative paper

- Title: Global landscape of antibiotic resistance genes in the human gut microbiome metagenome-assembled genomes
- Journal: BMC Microbiology
- DOI: 10.1186/s12866-025-04586-0
- Article page: https://link.springer.com/article/10.1186/s12866-025-04586-0
- Online publication date: 2025-12-09
- Issue assignment on the publisher page: 2026-12

This paper was selected as a practical recent demo source because its data availability section points to the MGnify human-gut genome catalogue, which exposes species-representative genome annotations with ready-to-use eggNOG and KEGG-derived fields. That makes it a strong fit for genome-level trace-element phenotype profiling.

## Public data used

- MGnify human gut genome catalogue root:
  https://ftp.ebi.ac.uk/pub/databases/metagenomics/mgnify_genomes/human-gut/v2.0.2/
- README:
  https://ftp.ebi.ac.uk/pub/databases/metagenomics/mgnify_genomes/human-gut/v2.0.2/README_v2.0.2.txt
- Metadata table:
  https://ftp.ebi.ac.uk/pub/databases/metagenomics/mgnify_genomes/human-gut/v2.0.2/genomes-all_metadata.tsv

The README states that species-representative genomes provide eggNOG annotations and that KEGG results are derived from those eggNOG annotations.

## Demo design

TracePheno is deliberately conservative for trace-element phenotypes and prefers function or genome-trait evidence over naive 16S-only inference. For this real-world demo:

1. Eleven high-quality human-gut species representatives were selected from the MGnify catalogue.
2. Each representative genome's `*_eggNOG.tsv` annotation file was downloaded.
3. A genome-by-feature matrix was built from eggNOG `Preferred_name` and `KEGG_ko` fields.
4. Genomes were treated as samples and scored with TracePheno in function mode with `--no-normalize` logic.
5. A full visualization report was rendered from the resulting phenotype score matrix.

This is a genome-level demonstration of the tool, not a sample-abundance community study.

## Selected representative genomes

The reproducible input set is written by the demo script to:

- `data/paper_demo_mgnify_2025/selected_genomes.tsv`
- `data/paper_demo_mgnify_2025/genome_metadata.tsv`

The current run used the following representatives:

- MGYG000000002, Blautia_A faecis, Firmicutes
- MGYG000000003, Alistipes shahii, Bacteroidota
- MGYG000000004, Anaerotruncus colihominis, Firmicutes
- MGYG000000013, Bacteroides sp902362375, Bacteroidota
- MGYG000000022, Faecalibacterium prausnitzii_C, Firmicutes
- MGYG000000076, Roseburia intestinalis, Firmicutes
- MGYG000000106, Enterococcus_D gallinarum, Firmicutes
- MGYG000000215, Prevotella stercorea, Bacteroidota
- MGYG000000756, Bifidobacterium sp002742445, Other
- MGYG000001881, Akkermansia muciniphila_A, Other
- MGYG000002323, Escherichia sp000208585, Other

## How to rerun

```bash
python scripts/run_mgnify_paper_demo.py
```

The script will cache annotation downloads under `data/paper_demo_mgnify_2025/eggnog/`, rebuild the feature matrix, and regenerate the report under `results/paper_demo_mgnify_2025/`.

## Current run outputs

Input tables:

- `data/paper_demo_mgnify_2025/feature_matrix.tsv`
- `data/paper_demo_mgnify_2025/paper_context.json`

Main TracePheno outputs:

- `results/paper_demo_mgnify_2025/report.html`
- `results/paper_demo_mgnify_2025/phenotype_scores.tsv`
- `results/paper_demo_mgnify_2025/phenotype_calls.tsv`
- `results/paper_demo_mgnify_2025/genome_trait_scores.tsv`
- `results/paper_demo_mgnify_2025/genome_trait_calls.tsv`
- `results/paper_demo_mgnify_2025/overview_dashboard.png`
- `results/paper_demo_mgnify_2025/phenotype_landscape.png`
- `results/paper_demo_mgnify_2025/phenotype_score_heatmap.png`
- `results/paper_demo_mgnify_2025/phenotype_clustered_heatmap.png`
- `results/paper_demo_mgnify_2025/group_mean_scores.png`
- `results/paper_demo_mgnify_2025/group_distribution_scores.png`
- `results/paper_demo_mgnify_2025/group_trajectory_scores.png`
- `results/paper_demo_mgnify_2025/sample_embedding.png`
- `results/paper_demo_mgnify_2025/tier_evidence_summary.png`
- `results/paper_demo_mgnify_2025/marker_contribution_panels.png`
- `results/paper_demo_mgnify_2025/publication/figure_1_global_landscape.png`
- `results/paper_demo_mgnify_2025/publication/figure_1_global_landscape.pdf`
- `results/paper_demo_mgnify_2025/publication/figure_2_structure_and_drivers.png`
- `results/paper_demo_mgnify_2025/publication/figure_2_structure_and_drivers.pdf`
- `results/paper_demo_mgnify_2025/publication/figure_3_differential_statistics.png`
- `results/paper_demo_mgnify_2025/publication/figure_3_differential_statistics.pdf`
- `results/paper_demo_mgnify_2025/publication/figure_legends.md`
- `results/paper_demo_mgnify_2025/results_summary.md`

## Key findings from the current run

### 1. Data scale

- Feature matrix size: 7,731 annotation-derived features x 11 representative genomes
- Largest annotated genome in this subset: MGYG000002323 (Escherichia sp000208585)

### 2. Highest mean phenotype scores across the 11 genomes

- copper_homeostasis_resistance: 0.516
- iron_acquisition: 0.448
- cobalamin_biosynthesis: 0.429
- zinc_acquisition: 0.425
- cobalamin_transport_cobalt_uptake: 0.336

### 3. Group-level patterns in this small genome panel

- Firmicutes showed the highest mean cobalamin biosynthesis score (0.611), compared with Bacteroidota (0.271) and Other (0.281).
- Firmicutes also had higher molybdenum cofactor biosynthesis (0.450) and selenium utilization (0.345) than the Bacteroidota subset, where both averaged 0.000 in this panel.
- Bacteroidota showed somewhat higher zinc acquisition (0.487) and manganese acquisition (0.289) than the Firmicutes subset in this run.
- Copper homeostasis and iron acquisition appeared broadly distributed across all three coarse groups.

### 4. Representative genome-level phenotype examples

- Blautia_A faecis, Faecalibacterium prausnitzii_C, and Roseburia intestinalis were all topped by cobalamin biosynthesis.
- Prevotella stercorea was topped by iron acquisition.
- Akkermansia muciniphila_A was topped by cobalamin transport and cobalt uptake.
- Bifidobacterium sp002742445 was topped by manganese acquisition.
- Escherichia sp000208585 was topped by iron storage and homeostasis.

### 5. Statistical caution

- Group statistics were exploratory only.
- With 11 genomes split into three coarse groups, none of the group comparisons were FDR-significant in the current run.

## Caveats

- This demonstration uses species-representative genomes rather than metagenomic sample abundances, so it validates genome-level trait scoring more directly than community-level enrichment.
- eggNOG `Preferred_name` and KO-derived annotations are not always perfectly aligned in display labels. For interpretation, phenotype-level and marker-set-level evidence should be trusted more than any individual raw preferred-name string.
- The built-in phenotype library currently emphasizes common trace elements. Heavy-metal resistance extensions such as arsenic, mercury, cadmium, and chromium remain a logical next expansion step.
