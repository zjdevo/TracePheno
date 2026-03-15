from __future__ import annotations

import math
import textwrap
from dataclasses import dataclass
from pathlib import Path

import matplotlib

matplotlib.use("Agg")

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns
from matplotlib.patches import Ellipse

sns.set_theme(style="ticks", context="paper")
matplotlib.rcParams.update(
    {
        "figure.facecolor": "white",
        "axes.facecolor": "white",
        "axes.spines.top": False,
        "axes.spines.right": False,
        "axes.linewidth": 0.8,
        "axes.edgecolor": "#2f3a45",
        "xtick.color": "#2f3a45",
        "ytick.color": "#2f3a45",
        "text.color": "#1f2933",
        "axes.labelcolor": "#1f2933",
        "font.family": ["Arial", "DejaVu Sans"],
        "axes.titlesize": 12,
        "axes.labelsize": 10,
        "xtick.labelsize": 8.5,
        "ytick.labelsize": 8.5,
        "legend.fontsize": 8.5,
        "legend.title_fontsize": 8.5,
        "pdf.fonttype": 42,
        "ps.fonttype": 42,
        "savefig.facecolor": "white",
    }
)

SEQUENTIAL_CMAP = sns.blend_palette(["#f8f6f1", "#bfd2de", "#1f5a78"], as_cmap=True)
CLUSTER_CMAP = sns.blend_palette(["#fbfaf7", "#c6d5cf", "#214f4b"], as_cmap=True)
GROUP_COLORS = ["#365c8d", "#c65a3a", "#2f7a64", "#8e6c8f", "#b08b2f", "#6f889f", "#6a5b4d"]
PHENOTYPE_COLORS = ["#1f5a78", "#c65a3a", "#2f7a64", "#7b6a9b", "#a57f2c", "#5f7ea7", "#a85073", "#587c68"]
TIER_COLORS = {
    "core": "#186a64",
    "accessory": "#b77819",
    "ambiguous": "#b14d2c",
    "mixed": "#556270",
}


@dataclass(frozen=True)
class VisualizationSpec:
    title: str
    filename: str
    description: str


def _finalize_and_save(output_path: Path, figure: plt.Figure) -> Path:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    figure.savefig(output_path, dpi=300, bbox_inches="tight", facecolor="white")
    plt.close(figure)
    return output_path


def _apply_axis_style(axis: plt.Axes, grid_axis: str = "x") -> None:
    axis.spines["top"].set_visible(False)
    axis.spines["right"].set_visible(False)
    axis.spines["left"].set_color("#2f3a45")
    axis.spines["bottom"].set_color("#2f3a45")
    axis.grid(False)
    if grid_axis == "x":
        axis.xaxis.grid(True, color="#e4eaef", linewidth=0.7)
    elif grid_axis == "y":
        axis.yaxis.grid(True, color="#e4eaef", linewidth=0.7)
    elif grid_axis == "both":
        axis.xaxis.grid(True, color="#e4eaef", linewidth=0.7)
        axis.yaxis.grid(True, color="#e4eaef", linewidth=0.7)
    axis.set_axisbelow(True)


def _short_label(value: object, width: int = 28) -> str:
    text = str(value)
    if len(text) <= width:
        return text
    shortened = textwrap.shorten(text, width=width, placeholder="...")
    if len(shortened) <= width:
        return shortened
    return text[: width - 3] + "..."


def _group_palette(groups: list[str]) -> dict[str, tuple[float, float, float]]:
    palette = sns.color_palette(GROUP_COLORS, n_colors=max(len(groups), 1))
    return {group: palette[index] for index, group in enumerate(groups)}


def _add_group_ellipse(axis: plt.Axes, x: np.ndarray, y: np.ndarray, color: tuple[float, float, float]) -> None:
    if len(x) < 3:
        return
    covariance = np.cov(x, y)
    if not np.isfinite(covariance).all():
        return
    eigenvalues, eigenvectors = np.linalg.eigh(covariance)
    order = eigenvalues.argsort()[::-1]
    eigenvalues = eigenvalues[order]
    eigenvectors = eigenvectors[:, order]
    if np.any(eigenvalues <= 0):
        return
    angle = np.degrees(np.arctan2(*eigenvectors[:, 0][::-1]))
    width, height = 2.5 * 2 * np.sqrt(eigenvalues)
    ellipse = Ellipse(
        xy=(np.mean(x), np.mean(y)),
        width=width,
        height=height,
        angle=angle,
        facecolor=color,
        edgecolor=color,
        linewidth=1.0,
        alpha=0.12,
    )
    axis.add_patch(ellipse)


def save_score_heatmap(scores: pd.DataFrame, output_path: Path) -> Path | None:
    if scores.empty:
        return None

    ordered = scores.loc[scores.mean(axis=1).sort_values(ascending=False).index]
    figure, axis = plt.subplots(figsize=(max(9, ordered.shape[1] * 0.95), max(6, ordered.shape[0] * 0.55)))
    annotate = ordered.shape[0] <= 12 and ordered.shape[1] <= 10
    sns.heatmap(
        ordered,
        cmap=SEQUENTIAL_CMAP,
        linewidths=0.45,
        linecolor="#f4f1ea",
        annot=annotate,
        fmt=".2f",
        vmin=0.0,
        vmax=max(1.0, float(ordered.to_numpy().max())),
        cbar_kws={"label": "Phenotype score", "shrink": 0.9},
        ax=axis,
    )
    axis.set_title("Phenotype score matrix")
    axis.set_xlabel("Samples")
    axis.set_ylabel("Phenotypes")
    axis.tick_params(axis="x", rotation=35)
    figure.tight_layout()
    return _finalize_and_save(output_path, figure)


def save_clustered_heatmap(scores: pd.DataFrame, output_path: Path) -> Path | None:
    if scores.empty or scores.shape[0] < 2 or scores.shape[1] < 2:
        return None

    cluster = sns.clustermap(
        scores,
        cmap=CLUSTER_CMAP,
        linewidths=0.2,
        linecolor="#f8f6f2",
        figsize=(max(10, scores.shape[1] * 1.0), max(8, scores.shape[0] * 0.65)),
        cbar_kws={"label": "Phenotype score"},
        method="average",
        metric="euclidean",
        dendrogram_ratio=(0.12, 0.16),
    )
    cluster.ax_heatmap.set_xlabel("Samples")
    cluster.ax_heatmap.set_ylabel("Phenotypes")
    cluster.ax_heatmap.tick_params(axis="x", rotation=35)
    cluster.fig.suptitle("Hierarchical phenotype atlas", y=1.02, fontsize=13)
    return _finalize_and_save(output_path, cluster.fig)


def save_group_mean_heatmap(
    scores: pd.DataFrame,
    metadata: pd.DataFrame,
    group_column: str,
    output_path: Path,
) -> Path | None:
    if scores.empty or metadata.empty or group_column not in metadata.columns:
        return None

    aligned_samples = [sample for sample in scores.columns if sample in metadata.index]
    if not aligned_samples:
        return None

    long_frame = scores[aligned_samples].T
    long_frame[group_column] = metadata.loc[aligned_samples, group_column].astype(str)
    grouped = long_frame.groupby(group_column).mean(numeric_only=True).T
    if grouped.empty:
        return None

    grouped = grouped.loc[grouped.mean(axis=1).sort_values(ascending=False).index]
    figure, axis = plt.subplots(figsize=(max(7.8, grouped.shape[1] * 1.15), max(6, grouped.shape[0] * 0.52)))
    sns.heatmap(
        grouped,
        annot=True,
        fmt=".2f",
        cmap=SEQUENTIAL_CMAP,
        linewidths=0.45,
        linecolor="#f4f1ea",
        cbar_kws={"label": "Mean score", "shrink": 0.9},
        ax=axis,
    )
    axis.set_title(f"Group-wise phenotype means ({group_column})")
    axis.set_xlabel(group_column)
    axis.set_ylabel("Phenotypes")
    axis.tick_params(axis="x", rotation=0)
    figure.tight_layout()
    return _finalize_and_save(output_path, figure)


def save_group_distribution_plot(
    scores: pd.DataFrame,
    metadata: pd.DataFrame,
    group_column: str,
    output_path: Path,
) -> Path | None:
    if scores.empty or metadata.empty or group_column not in metadata.columns:
        return None

    aligned_samples = [sample for sample in scores.columns if sample in metadata.index]
    if not aligned_samples:
        return None

    long_frame = scores[aligned_samples].T.copy()
    long_frame[group_column] = metadata.loc[aligned_samples, group_column].astype(str)
    melted = long_frame.reset_index().rename(columns={"index": "sample"}).melt(
        id_vars=["sample", group_column],
        var_name="phenotype",
        value_name="score",
    )
    if melted.empty:
        return None

    phenotype_order = scores.mean(axis=1).sort_values(ascending=False).index.tolist()[: min(6, scores.shape[0])]
    groups = metadata.loc[aligned_samples, group_column].astype(str).drop_duplicates().tolist()
    palette_map = _group_palette(groups)

    rows = math.ceil(len(phenotype_order) / 2)
    figure, axes = plt.subplots(rows, 2, figsize=(15, max(5.6, rows * 4.3)), squeeze=False)
    axes_array = axes.ravel()

    for axis, phenotype in zip(axes_array, phenotype_order):
        subset = melted.loc[melted["phenotype"] == phenotype].copy()
        group_order = subset.groupby(group_column)["score"].mean().sort_values(ascending=False).index.tolist()
        group_palette = [palette_map[group] for group in group_order]

        sns.violinplot(
            data=subset,
            x=group_column,
            y="score",
            hue=group_column,
            order=group_order,
            palette=group_palette,
            inner=None,
            cut=0,
            linewidth=1.0,
            saturation=1.0,
            dodge=False,
            legend=False,
            ax=axis,
        )
        sns.boxplot(
            data=subset,
            x=group_column,
            y="score",
            order=group_order,
            width=0.18,
            showcaps=False,
            showfliers=False,
            boxprops={"facecolor": "white", "edgecolor": "#1f2937", "linewidth": 0.9},
            whiskerprops={"linewidth": 0.9, "color": "#1f2937"},
            medianprops={"linewidth": 1.2, "color": "#1f2937"},
            ax=axis,
        )

        for index, group in enumerate(group_order):
            values = subset.loc[subset[group_column] == group, "score"].to_numpy()
            rng = np.random.default_rng(42 + index)
            jitter = rng.normal(0.0, 0.045, size=len(values))
            axis.scatter(
                np.full(len(values), index) + jitter,
                values,
                s=22,
                color=palette_map[group],
                edgecolors="white",
                linewidth=0.45,
                alpha=0.9,
                zorder=3,
            )

        axis.set_title(_short_label(phenotype, width=34), fontsize=11)
        axis.set_xlabel("")
        axis.set_ylabel("Score")
        axis.tick_params(axis="x", rotation=18)
        _apply_axis_style(axis, grid_axis="y")

    for axis in axes_array[len(phenotype_order) :]:
        axis.axis("off")

    figure.suptitle("Raincloud phenotype distributions by group", y=1.01, fontsize=13)
    figure.tight_layout()
    return _finalize_and_save(output_path, figure)


def save_sample_embedding(
    scores: pd.DataFrame,
    metadata: pd.DataFrame | None,
    group_column: str | None,
    output_path: Path,
) -> Path | None:
    if scores.empty or scores.shape[1] < 2:
        return None

    sample_frame = scores.T.astype(float)
    centered = sample_frame - sample_frame.mean(axis=0)
    matrix = centered.to_numpy()
    if matrix.size == 0:
        return None

    _, singular_values, vh = np.linalg.svd(matrix, full_matrices=False)
    coords = matrix.dot(vh[:2].T)
    if coords.shape[1] == 1:
        coords = np.column_stack([coords[:, 0], np.zeros(coords.shape[0])])
    total_variance = float((singular_values**2).sum())
    explained = (singular_values**2 / total_variance) if total_variance > 0 else np.zeros_like(singular_values)

    embedding = pd.DataFrame(coords[:, :2], index=sample_frame.index, columns=["PC1", "PC2"])
    if metadata is not None and group_column and group_column in metadata.columns:
        embedding[group_column] = metadata.reindex(embedding.index)[group_column].astype(str)
    else:
        embedding[group_column or "group"] = "all_samples"
        group_column = group_column or "group"

    groups = embedding[group_column].drop_duplicates().tolist()
    palette_map = _group_palette(groups)

    figure, axis = plt.subplots(figsize=(8.2, 6.6))
    for group in groups:
        subset = embedding.loc[embedding[group_column] == group]
        color = palette_map[group]
        axis.scatter(
            subset["PC1"],
            subset["PC2"],
            s=72,
            color=color,
            edgecolors="white",
            linewidth=0.7,
            alpha=0.95,
            label=group,
            zorder=3,
        )
        _add_group_ellipse(axis, subset["PC1"].to_numpy(), subset["PC2"].to_numpy(), color)

    for sample_id, row in embedding.iterrows():
        axis.text(row["PC1"] + 0.012, row["PC2"] + 0.012, str(sample_id), fontsize=7.5, alpha=0.85)

    axis.axhline(0, color="#cbd5e1", linewidth=0.9, zorder=1)
    axis.axvline(0, color="#cbd5e1", linewidth=0.9, zorder=1)
    axis.set_title("Sample embedding in phenotype space")
    axis.set_xlabel(f"PC1 ({explained[0] * 100:.1f}% variance)")
    axis.set_ylabel(f"PC2 ({(explained[1] * 100 if len(explained) > 1 else 0.0):.1f}% variance)")
    axis.legend(title=group_column, frameon=False, loc="upper right")
    _apply_axis_style(axis, grid_axis="both")
    figure.tight_layout()
    return _finalize_and_save(output_path, figure)


def save_tier_summary_plot(tier_scores: pd.DataFrame, output_path: Path) -> Path | None:
    if tier_scores.empty:
        return None

    summary = tier_scores.mean(axis=1).rename("mean_score").reset_index()
    pivot = summary.pivot(index="phenotype", columns="tier", values="mean_score").fillna(0.0)
    tier_order = [tier for tier in ["core", "accessory", "ambiguous"] if tier in pivot.columns] + [
        tier for tier in pivot.columns if tier not in {"core", "accessory", "ambiguous"}
    ]
    pivot = pivot[tier_order]
    pivot = pivot.loc[pivot.sum(axis=1).sort_values(ascending=True).index]

    figure, axis = plt.subplots(figsize=(10.2, max(6, pivot.shape[0] * 0.52)))
    left = np.zeros(len(pivot), dtype=float)
    y_positions = np.arange(len(pivot))
    for tier in tier_order:
        values = pivot[tier].to_numpy()
        axis.barh(
            y_positions,
            values,
            left=left,
            label=tier,
            color=TIER_COLORS.get(tier, "#64748b"),
            alpha=0.95,
            height=0.72,
        )
        left += values
    axis.set_yticks(y_positions)
    axis.set_yticklabels([_short_label(label, width=30) for label in pivot.index.tolist()])
    axis.set_xlabel("Mean tier score")
    axis.set_ylabel("Phenotypes")
    axis.set_title("Evidence tier composition")
    axis.legend(title="Tier", frameon=False, loc="lower right")
    _apply_axis_style(axis, grid_axis="x")
    figure.tight_layout()
    return _finalize_and_save(output_path, figure)


def save_marker_contribution_plot(contributions: pd.DataFrame, output_path: Path) -> Path | None:
    if contributions.empty:
        return None

    phenotype_order = (
        contributions.groupby("phenotype")["total_abundance"].sum().sort_values(ascending=False).head(6).index.tolist()
    )
    if not phenotype_order:
        return None

    rows = math.ceil(len(phenotype_order) / 2)
    figure, axes = plt.subplots(rows, 2, figsize=(15, max(4.8, rows * 4.7)), squeeze=False)
    axes_array = axes.ravel()

    for axis, phenotype in zip(axes_array, phenotype_order):
        subset = contributions.loc[contributions["phenotype"] == phenotype].copy()
        subset = subset.sort_values("relative_contribution", ascending=False).head(8)
        if subset.empty:
            axis.axis("off")
            continue

        marker_sets = subset["marker_set"].astype(str).drop_duplicates().tolist()
        marker_palette = {marker: color for marker, color in zip(marker_sets, sns.color_palette(PHENOTYPE_COLORS, len(marker_sets)))}
        y_positions = np.arange(len(subset))

        axis.hlines(
            y=y_positions,
            xmin=0,
            xmax=subset["relative_contribution"].to_numpy(),
            color="#d7e0e8",
            linewidth=2.0,
        )
        axis.scatter(
            subset["relative_contribution"],
            y_positions,
            s=84,
            color=[marker_palette[marker] for marker in subset["marker_set"]],
            edgecolors="white",
            linewidth=0.7,
            zorder=3,
        )
        axis.set_yticks(y_positions)
        axis.set_yticklabels([_short_label(feature, width=34) for feature in subset["feature"]])
        axis.invert_yaxis()
        axis.set_xlabel("Relative contribution")
        axis.set_title(_short_label(phenotype, width=36), fontsize=11)
        _apply_axis_style(axis, grid_axis="x")

    for axis in axes_array[len(phenotype_order) :]:
        axis.axis("off")

    figure.suptitle("Marker contribution lollipop panels", y=1.01, fontsize=13)
    figure.tight_layout()
    return _finalize_and_save(output_path, figure)


def save_differential_phenotype_plot(
    scores: pd.DataFrame,
    stats_frame: pd.DataFrame | None,
    output_path: Path,
) -> Path | None:
    if scores.empty or stats_frame is None or stats_frame.empty:
        return None
    if "effect_size" not in stats_frame.columns or stats_frame["effect_size"].dropna().empty:
        return None

    effect_frame = stats_frame.dropna(subset=["effect_size"]).copy()
    if effect_frame.empty:
        return None

    if "qvalue" in effect_frame.columns:
        qvalues = pd.to_numeric(effect_frame["qvalue"], errors="coerce")
    else:
        qvalues = pd.Series(np.nan, index=effect_frame.index, dtype=float)
    if "pvalue" in effect_frame.columns:
        pvalues = pd.to_numeric(effect_frame["pvalue"], errors="coerce")
    else:
        pvalues = pd.Series(np.nan, index=effect_frame.index, dtype=float)
    effect_frame["qvalue"] = qvalues.fillna(pvalues).fillna(1.0)
    effect_frame["minus_log10_q"] = -np.log10(effect_frame["qvalue"].clip(lower=1e-300))
    effect_frame["mean_score"] = effect_frame["phenotype"].map(scores.mean(axis=1))
    effect_frame["abs_effect"] = effect_frame["effect_size"].abs()

    group_label = None
    if "groups" in effect_frame.columns and effect_frame["groups"].notna().any():
        group_label = str(effect_frame["groups"].dropna().iloc[0])

    significance_cutoff = -np.log10(0.1)

    def classify(row: pd.Series) -> str:
        if row["qvalue"] <= 0.1 and row["effect_size"] > 0:
            return "positive"
        if row["qvalue"] <= 0.1 and row["effect_size"] < 0:
            return "negative"
        return "background"

    effect_frame["category"] = effect_frame.apply(classify, axis=1)
    palette = {"positive": "#245c78", "negative": "#ca5d3d", "background": "#b8c4cf"}

    figure, axis = plt.subplots(figsize=(9.4, 7.0))
    for category in ["background", "positive", "negative"]:
        subset = effect_frame.loc[effect_frame["category"] == category]
        if subset.empty:
            continue
        axis.scatter(
            subset["effect_size"],
            subset["minus_log10_q"],
            s=90 + subset["mean_score"].fillna(0.0).to_numpy() * 180,
            color=palette[category],
            edgecolors="white",
            linewidth=0.8,
            alpha=0.94,
            label=category,
            zorder=3 if category != "background" else 2,
        )

    for xline in (-0.33, 0.33):
        axis.axvline(xline, color="#d6dde5", linewidth=1.0, linestyle="--", zorder=1)
    axis.axhline(significance_cutoff, color="#d6dde5", linewidth=1.0, linestyle="--", zorder=1)

    label_rows = effect_frame.sort_values(["qvalue", "abs_effect"], ascending=[True, False]).head(min(8, len(effect_frame)))
    for _, row in label_rows.iterrows():
        if row["minus_log10_q"] < 0.4 and row["abs_effect"] < 0.15:
            continue
        axis.text(
            row["effect_size"] + 0.015,
            row["minus_log10_q"] + 0.02,
            _short_label(row["phenotype"], width=28),
            fontsize=8.1,
            alpha=0.92,
        )

    if group_label and " vs " in group_label:
        positive_group = group_label.split(" vs ", 1)[0]
        xlabel = f"Effect size (Cliff's delta; positive = {positive_group} higher)"
    else:
        xlabel = "Effect size"

    legend_labels = {
        "background": "Not highlighted",
        "positive": "Positive effect, q<=0.1",
        "negative": "Negative effect, q<=0.1",
    }
    handles = [
        plt.Line2D(
            [0],
            [0],
            marker="o",
            color="w",
            markerfacecolor=palette[key],
            markeredgecolor="white",
            markersize=8,
            label=legend_labels[key],
        )
        for key in ["positive", "negative", "background"]
        if key in set(effect_frame["category"])
    ]
    if handles:
        axis.legend(handles=handles, frameon=False, loc="upper right")

    axis.set_xlabel(xlabel)
    axis.set_ylabel("-log10(q value)")
    axis.set_title("Differential phenotype map")
    _apply_axis_style(axis, grid_axis="both")
    figure.tight_layout()
    return _finalize_and_save(output_path, figure)


def save_phenotype_landscape_plot(
    scores: pd.DataFrame,
    calls: pd.DataFrame | None,
    tier_scores: pd.DataFrame | None,
    output_path: Path,
) -> Path | None:
    if scores.empty or calls is None or calls.empty:
        return None

    summary = pd.DataFrame(
        {
            "mean_score": scores.mean(axis=1),
            "prevalence": calls.mean(axis=1),
            "variability": scores.std(axis=1),
            "max_score": scores.max(axis=1),
        }
    )
    summary.index.name = "phenotype"
    summary = summary.reset_index()

    if tier_scores is not None and not tier_scores.empty:
        tier_table = tier_scores.mean(axis=1).rename("tier_score").reset_index()
        tier_table = tier_table.pivot(index="phenotype", columns="tier", values="tier_score").fillna(0.0)
        summary["dominant_tier"] = summary["phenotype"].map(tier_table.idxmax(axis=1)).fillna("mixed")
    else:
        summary["dominant_tier"] = "mixed"

    summary = summary.sort_values(["mean_score", "prevalence"], ascending=[True, True]).reset_index(drop=True)

    figure, axis = plt.subplots(figsize=(9.8, 7.1))
    sizes = 160 + summary["variability"].to_numpy() * 1100
    axis.scatter(
        summary["mean_score"],
        summary["prevalence"],
        s=sizes,
        c=[TIER_COLORS.get(tier, TIER_COLORS["mixed"]) for tier in summary["dominant_tier"]],
        edgecolors="white",
        linewidth=0.9,
        alpha=0.94,
        zorder=3,
    )

    label_candidates = summary.sort_values(["mean_score", "prevalence"], ascending=False).head(min(8, len(summary)))
    label_candidates = label_candidates.loc[(label_candidates["mean_score"] > 0.025) | (label_candidates["prevalence"] > 0.2)]
    for _, row in label_candidates.iterrows():
        axis.text(
            row["mean_score"] + 0.012,
            row["prevalence"] + 0.012,
            _short_label(row["phenotype"], width=26),
            fontsize=8.1,
            alpha=0.9,
        )

    axis.axvline(summary["mean_score"].median(), color="#cbd5e1", linewidth=0.9, linestyle="--")
    axis.axhline(summary["prevalence"].median(), color="#cbd5e1", linewidth=0.9, linestyle="--")
    axis.set_xlim(left=max(0.0, float(summary["mean_score"].min()) - 0.05), right=min(1.05, float(summary["mean_score"].max()) + 0.12))
    axis.set_ylim(-0.02, 1.05)
    axis.set_xlabel("Mean phenotype score")
    axis.set_ylabel("Call prevalence across samples")
    axis.set_title("Phenotype landscape")

    handles = [
        plt.Line2D(
            [0],
            [0],
            marker="o",
            color="w",
            markerfacecolor=color,
            markeredgecolor="white",
            markersize=8,
            label=tier,
        )
        for tier, color in TIER_COLORS.items()
        if tier in set(summary["dominant_tier"])
    ]
    if handles:
        axis.legend(handles=handles, title="Dominant tier", frameon=False, loc="lower right")

    _apply_axis_style(axis, grid_axis="both")
    figure.tight_layout()
    return _finalize_and_save(output_path, figure)


def save_group_trajectory_plot(
    scores: pd.DataFrame,
    metadata: pd.DataFrame,
    group_column: str,
    output_path: Path,
) -> Path | None:
    if scores.empty or metadata.empty or group_column not in metadata.columns:
        return None

    aligned_samples = [sample for sample in scores.columns if sample in metadata.index]
    if not aligned_samples:
        return None

    group_means = scores[aligned_samples].T.join(metadata.loc[aligned_samples, [group_column]]).groupby(group_column).mean(numeric_only=True).T
    if group_means.shape[1] < 2:
        return None

    phenotype_order = group_means.std(axis=1).sort_values(ascending=False).head(min(6, group_means.shape[0])).index.tolist()
    group_means = group_means.loc[phenotype_order]
    group_order = group_means.mean(axis=0).sort_values(ascending=False).index.tolist()
    group_means = group_means[group_order]

    figure, axis = plt.subplots(figsize=(max(8.2, group_means.shape[1] * 1.5), 6.2))
    x_positions = np.arange(len(group_order))
    phenotype_palette = sns.color_palette(PHENOTYPE_COLORS, n_colors=len(phenotype_order))

    for color, phenotype in zip(phenotype_palette, phenotype_order):
        values = group_means.loc[phenotype].to_numpy(dtype=float)
        axis.plot(
            x_positions,
            values,
            marker="o",
            markersize=6.5,
            linewidth=2.0,
            color=color,
            alpha=0.96,
            label=_short_label(phenotype, width=40),
        )

    axis.set_xticks(x_positions)
    axis.set_xticklabels(group_order, rotation=18)
    axis.set_ylabel("Mean phenotype score")
    axis.set_xlabel(group_column)
    axis.set_title("Group trajectory of dominant phenotypes")
    axis.legend(title="Phenotype", frameon=False, bbox_to_anchor=(1.02, 1.0), loc="upper left")
    _apply_axis_style(axis, grid_axis="y")
    figure.tight_layout()
    return _finalize_and_save(output_path, figure)


def save_overview_dashboard(
    scores: pd.DataFrame,
    tier_scores: pd.DataFrame | None,
    metadata: pd.DataFrame | None,
    group_column: str | None,
    stats_frame: pd.DataFrame | None,
    output_path: Path,
) -> Path | None:
    if scores.empty:
        return None

    figure, axes = plt.subplots(2, 2, figsize=(16.2, 11.8))
    axes = axes.ravel()

    top_mean = scores.mean(axis=1).sort_values(ascending=True).tail(8)
    axes[0].hlines(top_mean.index, xmin=0, xmax=top_mean.values, color="#d7e0e8", linewidth=2.4)
    axes[0].scatter(top_mean.values, top_mean.index, s=78, color="#245c78", edgecolors="white", linewidth=0.7, zorder=3)
    axes[0].set_title("Top mean phenotype scores")
    axes[0].set_xlabel("Mean score")
    _apply_axis_style(axes[0], grid_axis="x")

    sample_load = scores.sum(axis=0).sort_values(ascending=False)
    if metadata is not None and group_column and group_column in metadata.columns:
        groups = metadata.reindex(sample_load.index)[group_column].astype(str)
        palette_map = _group_palette(groups.drop_duplicates().tolist())
        bar_colors = [palette_map[group] for group in groups]
    else:
        bar_colors = ["#3C5488"] * len(sample_load)
    axes[1].bar(sample_load.index, sample_load.values, color=bar_colors, width=0.72)
    axes[1].set_title("Sample total phenotype load")
    axes[1].set_ylabel("Summed score")
    axes[1].tick_params(axis="x", rotation=35)
    _apply_axis_style(axes[1], grid_axis="y")

    if stats_frame is not None and not stats_frame.empty and "effect_size" in stats_frame.columns and stats_frame["effect_size"].notna().any():
        effect_frame = stats_frame.dropna(subset=["effect_size"]).copy().sort_values("effect_size")
        axes[2].hlines(effect_frame["phenotype"], xmin=0, xmax=effect_frame["effect_size"], color="#eadbd3", linewidth=2.0)
        axes[2].scatter(effect_frame["effect_size"], effect_frame["phenotype"], color="#ca5d3d", s=68, edgecolors="white", linewidth=0.6, zorder=3)
        axes[2].axvline(0, color="#94a3b8", linewidth=1)
        axes[2].set_title("Group effect sizes")
        axes[2].set_xlabel(
            effect_frame["effect_name"].dropna().iloc[0]
            if effect_frame["effect_name"].notna().any()
            else "Effect size"
        )
        _apply_axis_style(axes[2], grid_axis="x")
    else:
        variability = scores.std(axis=1).sort_values()
        axes[2].barh(variability.index, variability.values, color="#c58b39")
        axes[2].set_title("Phenotype variability across samples")
        axes[2].set_xlabel("Standard deviation")
        _apply_axis_style(axes[2], grid_axis="x")

    if tier_scores is not None and not tier_scores.empty:
        tier_summary = tier_scores.mean(axis=1).rename("mean_score").reset_index()
        pivot = tier_summary.pivot(index="phenotype", columns="tier", values="mean_score").fillna(0.0)
        pivot = pivot.loc[scores.mean(axis=1).sort_values(ascending=True).tail(8).index.intersection(pivot.index)]
        tier_order = [tier for tier in ["core", "accessory", "ambiguous"] if tier in pivot.columns]
        left = np.zeros(len(pivot), dtype=float)
        for tier in tier_order:
            axes[3].barh(
                pivot.index,
                pivot[tier].to_numpy(),
                left=left,
                color=TIER_COLORS[tier],
                label=tier,
                height=0.72,
            )
            left += pivot[tier].to_numpy()
        axes[3].set_title("Tier composition of leading phenotypes")
        axes[3].set_xlabel("Mean tier score")
        if tier_order:
            axes[3].legend(title="Tier", frameon=False, loc="lower right")
        _apply_axis_style(axes[3], grid_axis="x")
    else:
        phenotype_max = scores.max(axis=1).sort_values()
        axes[3].barh(phenotype_max.index, phenotype_max.values, color="#648f78")
        axes[3].set_title("Maximum sample score by phenotype")
        axes[3].set_xlabel("Max score")
        _apply_axis_style(axes[3], grid_axis="x")

    figure.tight_layout()
    return _finalize_and_save(output_path, figure)


def build_plot_gallery(
    *,
    overview_dashboard_path: Path | None = None,
    heatmap_path: Path | None = None,
    clustered_heatmap_path: Path | None = None,
    differential_plot_path: Path | None = None,
    phenotype_landscape_path: Path | None = None,
    group_mean_path: Path | None = None,
    group_distribution_path: Path | None = None,
    group_trajectory_path: Path | None = None,
    sample_embedding_path: Path | None = None,
    tier_summary_path: Path | None = None,
    contribution_plot_path: Path | None = None,
) -> list[VisualizationSpec]:
    plots: list[VisualizationSpec] = []
    if overview_dashboard_path:
        plots.append(
            VisualizationSpec(
                title="Overview Dashboard",
                filename=overview_dashboard_path.name,
                description="A multi-panel summary of dominant phenotypes, total load, variability, and evidence composition.",
            )
        )
    if differential_plot_path:
        plots.append(
            VisualizationSpec(
                title="Differential Phenotype Map",
                filename=differential_plot_path.name,
                description="Effect-size vs significance plot highlighting phenotype shifts between groups.",
            )
        )
    if phenotype_landscape_path:
        plots.append(
            VisualizationSpec(
                title="Phenotype Landscape",
                filename=phenotype_landscape_path.name,
                description="Bubble plot summarizing mean strength, prevalence across samples, variability, and dominant evidence tier.",
            )
        )
    if heatmap_path:
        plots.append(
            VisualizationSpec(
                title="Phenotype Score Heatmap",
                filename=heatmap_path.name,
                description="Publication-style heatmap of phenotype scores across all samples.",
            )
        )
    if clustered_heatmap_path:
        plots.append(
            VisualizationSpec(
                title="Hierarchical Phenotype Atlas",
                filename=clustered_heatmap_path.name,
                description="Clustering view that reveals samples and phenotypes with related trace-element programs.",
            )
        )
    if group_mean_path:
        plots.append(
            VisualizationSpec(
                title="Group Mean Heatmap",
                filename=group_mean_path.name,
                description="Average phenotype intensity per group for rapid cohort-level comparison.",
            )
        )
    if group_distribution_path:
        plots.append(
            VisualizationSpec(
                title="Raincloud Group Panels",
                filename=group_distribution_path.name,
                description="Small-multiple violin, box, and point plots for the highest-scoring phenotypes.",
            )
        )
    if group_trajectory_path:
        plots.append(
            VisualizationSpec(
                title="Group Trajectory Plot",
                filename=group_trajectory_path.name,
                description="Slope-style comparison showing how dominant phenotypes shift across groups.",
            )
        )
    if sample_embedding_path:
        plots.append(
            VisualizationSpec(
                title="Sample Embedding",
                filename=sample_embedding_path.name,
                description="Two-dimensional phenotype-space embedding with group ellipses for visual separation.",
            )
        )
    if tier_summary_path:
        plots.append(
            VisualizationSpec(
                title="Tiered Evidence Composition",
                filename=tier_summary_path.name,
                description="Stacked evidence profile separating core, accessory, and ambiguous support.",
            )
        )
    if contribution_plot_path:
        plots.append(
            VisualizationSpec(
                title="Marker Contribution Panels",
                filename=contribution_plot_path.name,
                description="Lollipop panels highlighting the features that most strongly drive each phenotype.",
            )
        )
    return plots
