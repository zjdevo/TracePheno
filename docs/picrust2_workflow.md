# PICRUSt2 Workflow in TracePheno

## What is supported

`TracePheno` now provides a dedicated CLI entry point for `PICRUSt2` KO-based functional prediction tables:

```bash
tracepheno score-picrust2 \
  --input KO_metagenome_out/pred_metagenome_unstrat.tsv.gz \
  --metadata sample_metadata.tsv \
  --group-column group \
  --outdir results/picrust2_tracepheno
```

It also accepts the stratified contribution table:

```bash
tracepheno score-picrust2 \
  --input KO_metagenome_out/pred_metagenome_contrib.tsv.gz \
  --metadata sample_metadata.tsv \
  --group-column group \
  --outdir results/picrust2_tracepheno
```

For contribution tables, `TracePheno` automatically aggregates the data to a `function x sample` KO matrix before scoring.

## Why KO output is the preferred PICRUSt2 input

The current trace-element phenotype dictionary is primarily curated around:

- gene symbols
- KEGG KO identifiers
- KO-linked aliases

That means `PICRUSt2` KO metagenome predictions are the cleanest bridge from 16S-based functional inference to trace-element phenotype scoring.

## Practical recommendations

1. Prefer `pred_metagenome_unstrat.tsv.gz` when you only need sample-level phenotype prediction.
2. Use `pred_metagenome_contrib.tsv.gz` when you want a stratified PICRUSt2 result but still need a phenotype summary at sample level.
3. Keep metadata sample IDs exactly aligned with the PICRUSt2 table column names.
4. If you added functional descriptions to the KO table, keep them; `TracePheno` will automatically remove non-numeric description columns during import.

## Example files in this project

- Example PICRUSt2-like KO table:
  `tracepheno/data/example_picrust2_ko.tsv`
- Example metadata:
  `tracepheno/data/example_metadata.tsv`
- Example result report:
  `results/picrust2_demo/report.html`
- Example publication bundle:
  `results/picrust2_demo/publication/`
- Example auto-written summary:
  `results/picrust2_demo/results_summary.md`

## Official references checked during implementation

- PICRUSt2 project repository:
  https://github.com/picrust/picrust2
- PICRUSt2 wiki:
  https://github.com/picrust/picrust2/wiki
- PICRUSt2 tutorial page:
  https://github-wiki-see.page/m/picrust/picrust2/wiki/PICRUSt2-Tutorial-%28v2.1.4-beta%29
- PICRUSt2 metagenome pipeline source:
  https://raw.githubusercontent.com/picrust/picrust2/master/scripts/metagenome_pipeline.py

These sources were used to confirm that KO metagenome output is the correct attachment point for `TracePheno`, and that the unstratified and contribution-style outputs should be handled separately.

## Publication-oriented outputs

When you run `score-picrust2`, TracePheno now writes:

- `results_summary.md`
- `differential_phenotype_map.png`
- `publication/figure_1_global_landscape.(png|pdf)`
- `publication/figure_2_structure_and_drivers.(png|pdf)`
- `publication/figure_3_differential_statistics.(png|pdf)` when differential statistics are available
- `publication/figure_legends.md`

This means a PICRUSt2 KO prediction table can now move directly from 16S-derived functional inference into a phenotype report with manuscript-style figures and a starter Results summary.
