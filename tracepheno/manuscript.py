from __future__ import annotations

import math
import textwrap
from pathlib import Path

import matplotlib

matplotlib.use("Agg")

import matplotlib.pyplot as plt
import pandas as pd

matplotlib.rcParams.update(
    {
        "font.family": ["Arial", "DejaVu Sans"],
        "pdf.fonttype": 42,
        "ps.fonttype": 42,
    }
)


def _save_dual_format(figure: plt.Figure, stem: Path) -> tuple[Path, Path]:
    png_path = stem.with_suffix(".png")
    pdf_path = stem.with_suffix(".pdf")
    stem.parent.mkdir(parents=True, exist_ok=True)
    figure.savefig(png_path, dpi=260, bbox_inches="tight", facecolor="white")
    figure.savefig(pdf_path, dpi=260, bbox_inches="tight", facecolor="white")
    plt.close(figure)
    return png_path, pdf_path


def _compose_panel_figure(
    *,
    stem: Path,
    title: str,
    subtitle: str,
    panels: list[dict[str, str | Path]],
) -> tuple[Path, Path]:
    active_panels = [panel for panel in panels if panel.get("path")]
    if not active_panels:
        raise ValueError("At least one panel image is required to compose a publication figure.")

    cols = 2
    rows = math.ceil(len(active_panels) / cols)
    figure = plt.figure(figsize=(14.5, max(8.2, rows * 5.7)))
    grid = figure.add_gridspec(rows, cols, hspace=0.13, wspace=0.08)

    figure.suptitle(title, x=0.02, y=0.982, ha="left", fontsize=15, fontweight="bold")
    figure.text(0.02, 0.958, subtitle, ha="left", va="top", fontsize=9.5, color="#5c6773")

    for index, panel in enumerate(active_panels):
        axis = figure.add_subplot(grid[index // cols, index % cols])
        image = plt.imread(str(panel["path"]))
        axis.imshow(image)
        axis.axis("off")
        axis.text(
            -0.02,
            1.02,
            str(panel["label"]),
            transform=axis.transAxes,
            fontsize=14,
            fontweight="bold",
            ha="right",
            va="bottom",
            color="#0f172a",
        )
        axis.text(
            0.01,
            1.02,
            str(panel["title"]),
            transform=axis.transAxes,
            fontsize=10,
            fontweight="bold",
            ha="left",
            va="bottom",
            color="#0f172a",
        )

    for index in range(len(active_panels), rows * cols):
        axis = figure.add_subplot(grid[index // cols, index % cols])
        axis.axis("off")

    return _save_dual_format(figure, stem)


def _relabel_panels(panels: list[dict[str, str | Path]]) -> list[dict[str, str | Path]]:
    labels = "ABCDEFGHIJKLMNOPQRSTUVWXYZ"
    relabeled: list[dict[str, str | Path]] = []
    for index, panel in enumerate(panels):
        updated = dict(panel)
        updated["label"] = labels[index]
        relabeled.append(updated)
    return relabeled


def _short_series(series: pd.Series, n: int = 4) -> str:
    if series.empty:
        return "no dominant phenotypes detected"
    labels = [str(index) for index in series.head(n).index.tolist()]
    return ", ".join(labels)


def _build_legend_markdown(
    *,
    mode: str,
    scores: pd.DataFrame,
    stats_frame: pd.DataFrame | None,
    group_column: str | None,
    figure_definitions: list[dict[str, object]],
) -> str:
    top_summary = scores.mean(axis=1).sort_values(ascending=False)
    top_text = _short_series(top_summary, n=5)
    stats_note = "No group-level statistics were available."
    if stats_frame is not None and not stats_frame.empty:
        stats_note = "Top statistical signals: " + _short_series(
            stats_frame.set_index("phenotype")["pvalue"].sort_values(ascending=True), n=4
        )

    lines = [
        "# TracePheno Publication Legends",
        "",
        f"Mode: `{mode}`",
        f"Samples: `{scores.shape[1]}`",
        f"Phenotypes: `{scores.shape[0]}`",
        f"Highest mean phenotypes: `{top_text}`",
        stats_note,
        "",
    ]

    for figure_def in figure_definitions:
        lines.append(f"## {figure_def['figure_id']} | {figure_def['title']}")
        lines.append(str(figure_def["lead"]))
        for panel in figure_def["panels"]:
            lines.append(f"Panel {panel['label']}, {panel['legend']}")
        if group_column:
            lines.append(
                f"The grouping variable used for cohort-level summaries was `{group_column}`."
            )
        lines.append("")

    return "\n".join(lines).strip() + "\n"


def save_publication_bundle(
    *,
    output_dir: Path,
    mode: str,
    scores: pd.DataFrame,
    stats_frame: pd.DataFrame | None,
    group_column: str | None,
    plot_paths: dict[str, Path | None],
    results_summary_path: Path | None = None,
) -> Path:
    publication_dir = output_dir / "publication"
    publication_dir.mkdir(parents=True, exist_ok=True)

    figure_definitions: list[dict[str, object]] = []

    figure_1_panels = [
        {
            "label": "A",
            "title": "Phenotype landscape",
            "path": plot_paths.get("phenotype_landscape"),
            "legend": "summarizes mean phenotype score, prevalence across samples, variability, and dominant evidence tier in a single overview.",
        },
        {
            "label": "B",
            "title": "Group trajectory",
            "path": plot_paths.get("group_trajectory") or plot_paths.get("group_mean"),
            "legend": "tracks how the highest-information phenotypes shift across cohorts or other sample groups.",
        },
        {
            "label": "C",
            "title": "Phenotype-space embedding",
            "path": plot_paths.get("sample_embedding"),
            "legend": "projects samples into phenotype space and highlights group separation patterns.",
        },
        {
            "label": "D",
            "title": "Evidence tier composition",
            "path": plot_paths.get("tier_summary") or plot_paths.get("overview_dashboard"),
            "legend": "shows the balance of core, accessory, and ambiguous evidence supporting each phenotype.",
        },
    ]
    active_figure_1 = [panel for panel in figure_1_panels if panel["path"]]
    if active_figure_1:
        active_figure_1 = _relabel_panels(active_figure_1)
        figure_1_png, figure_1_pdf = _compose_panel_figure(
            stem=publication_dir / "figure_1_global_landscape",
            title="Figure 1 | Global trace-element phenotype landscape",
            subtitle="Overview panels curated for manuscript-style presentation from TracePheno outputs.",
            panels=active_figure_1,
        )
        figure_definitions.append(
            {
                "figure_id": "Figure 1",
                "title": "Global trace-element phenotype landscape",
                "lead": "This figure summarizes the global structure of trace-element phenotypes inferred from the current dataset.",
                "png": figure_1_png.name,
                "pdf": figure_1_pdf.name,
                "panels": active_figure_1,
            }
        )

    figure_2_panels = [
        {
            "label": "A",
            "title": "Phenotype score heatmap",
            "path": plot_paths.get("heatmap"),
            "legend": "shows direct phenotype score magnitudes across all samples.",
        },
        {
            "label": "B",
            "title": "Hierarchical phenotype atlas",
            "path": plot_paths.get("clustered_heatmap"),
            "legend": "highlights coordinated phenotype structure using hierarchical clustering.",
        },
        {
            "label": "C",
            "title": "Raincloud group panels",
            "path": plot_paths.get("group_distribution") or plot_paths.get("group_mean"),
            "legend": "visualizes cohort-resolved phenotype distributions using violin, box, and point layers.",
        },
        {
            "label": "D",
            "title": "Marker contribution panels",
            "path": plot_paths.get("contribution_plot"),
            "legend": "identifies the strongest functional markers driving major phenotype calls.",
        },
    ]
    active_figure_2 = [panel for panel in figure_2_panels if panel["path"]]
    if active_figure_2:
        active_figure_2 = _relabel_panels(active_figure_2)
        figure_2_png, figure_2_pdf = _compose_panel_figure(
            stem=publication_dir / "figure_2_structure_and_drivers",
            title="Figure 2 | Cohort structure and phenotype drivers",
            subtitle="Detailed panels that connect sample-level patterns to the markers supporting each phenotype.",
            panels=active_figure_2,
        )
        figure_definitions.append(
            {
                "figure_id": "Figure 2",
                "title": "Cohort structure and phenotype drivers",
                "lead": "This figure links sample-level variation to the functional evidence that drives each phenotype score.",
                "png": figure_2_png.name,
                "pdf": figure_2_pdf.name,
                "panels": active_figure_2,
            }
        )

    figure_3_panels = [
        {
            "label": "A",
            "title": "Differential phenotype map",
            "path": plot_paths.get("differential_plot"),
            "legend": "combines effect size and multiple-testing-adjusted significance to highlight phenotypes that differ between groups.",
        },
        {
            "label": "B",
            "title": "Group mean heatmap",
            "path": plot_paths.get("group_mean"),
            "legend": "summarizes mean phenotype scores for each group to contextualize differential trends.",
        },
        {
            "label": "C",
            "title": "Raincloud group panels",
            "path": plot_paths.get("group_distribution"),
            "legend": "shows within-group distributions for the most informative phenotypes.",
        },
    ]
    active_figure_3 = [panel for panel in figure_3_panels if panel["path"]]
    if active_figure_3:
        active_figure_3 = _relabel_panels(active_figure_3)
        figure_3_png, figure_3_pdf = _compose_panel_figure(
            stem=publication_dir / "figure_3_differential_statistics",
            title="Figure 3 | Differential phenotype statistics",
            subtitle="Panels emphasizing cohort differences and effect-size-driven interpretation.",
            panels=active_figure_3,
        )
        figure_definitions.append(
            {
                "figure_id": "Figure 3",
                "title": "Differential phenotype statistics",
                "lead": "This figure focuses on statistical phenotype differences between groups and the distribution patterns that underlie them.",
                "png": figure_3_png.name,
                "pdf": figure_3_pdf.name,
                "panels": active_figure_3,
            }
        )

    legends_markdown = _build_legend_markdown(
        mode=mode,
        scores=scores,
        stats_frame=stats_frame,
        group_column=group_column,
        figure_definitions=figure_definitions,
    )
    (publication_dir / "figure_legends.md").write_text(legends_markdown, encoding="utf-8")

    if figure_definitions:
        manifest = pd.DataFrame(
            [
                {
                    "figure_id": figure_def["figure_id"],
                    "title": figure_def["title"],
                    "png": figure_def["png"],
                    "pdf": figure_def["pdf"],
                    "panel_count": len(figure_def["panels"]),
                }
                for figure_def in figure_definitions
            ]
        )
        manifest.to_csv(publication_dir / "figure_manifest.tsv", sep="\t", index=False)

    summary = textwrap.dedent(
        f"""
        # TracePheno Publication Bundle

        This folder contains manuscript-style composite figures and draft legends
        generated from TracePheno mode `{mode}`.

        - Samples: {scores.shape[1]}
        - Phenotypes: {scores.shape[0]}
        - Top mean phenotypes: {_short_series(scores.mean(axis=1).sort_values(ascending=False), n=5)}
        """
    ).strip()
    (publication_dir / "README.md").write_text(summary + "\n", encoding="utf-8")
    if results_summary_path is not None and results_summary_path.exists():
        (publication_dir / "results_summary.md").write_text(
            results_summary_path.read_text(encoding="utf-8"),
            encoding="utf-8",
        )

    return publication_dir
