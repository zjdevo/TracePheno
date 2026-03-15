from __future__ import annotations

from pathlib import Path

import pandas as pd


def _format_series(series: pd.Series, *, n: int = 5, digits: int = 3) -> str:
    if series.empty:
        return "none"
    pieces = [f"{index} ({value:.{digits}f})" for index, value in series.head(n).items()]
    return ", ".join(pieces)


def build_result_highlights(
    *,
    mode: str,
    scores: pd.DataFrame,
    tier_scores: pd.DataFrame | None,
    stats_frame: pd.DataFrame | None,
    metadata: pd.DataFrame | None,
    group_column: str | None,
) -> list[str]:
    highlights: list[str] = []

    mean_scores = scores.mean(axis=1).sort_values(ascending=False)
    variability = scores.std(axis=1).sort_values(ascending=False)
    highlights.append(
        f"In `{mode}` mode, the highest mean phenotype scores were {_format_series(mean_scores, n=5)}."
    )
    highlights.append(
        f"The most variable phenotypes across samples were {_format_series(variability, n=4)}."
    )

    if tier_scores is not None and not tier_scores.empty:
        tier_summary = tier_scores.mean(axis=1).rename("mean_score").reset_index()
        tier_pivot = tier_summary.pivot(index="phenotype", columns="tier", values="mean_score").fillna(0.0)
        dominant_tiers = tier_pivot.idxmax(axis=1)
        dominant_counts = dominant_tiers.value_counts()
        tier_text = ", ".join(f"{tier}: {count}" for tier, count in dominant_counts.items())
        highlights.append(f"Dominant evidence tiers across phenotypes were distributed as {tier_text}.")

    if metadata is not None and group_column and group_column in metadata.columns:
        aligned_samples = [sample for sample in scores.columns if sample in metadata.index]
        if aligned_samples:
            group_means = (
                scores[aligned_samples]
                .T.join(metadata.loc[aligned_samples, [group_column]])
                .groupby(group_column)
                .mean(numeric_only=True)
                .T
            )
            spread = (group_means.max(axis=1) - group_means.min(axis=1)).sort_values(ascending=False)
            highlights.append(
                f"The strongest between-group phenotype separations were {_format_series(spread, n=4)}."
            )

    if stats_frame is not None and not stats_frame.empty:
        stats_sorted = stats_frame.sort_values(["qvalue", "pvalue"], na_position="last")
        if "effect_size" in stats_sorted.columns and stats_sorted["effect_size"].notna().any():
            effect_rows = stats_sorted.dropna(subset=["effect_size"]).copy()
            significant = effect_rows.loc[effect_rows["qvalue"].fillna(1.0) <= 0.1]
            if not significant.empty:
                positive = significant.sort_values(["effect_size", "qvalue"], ascending=[False, True]).head(3)
                negative = significant.sort_values(["effect_size", "qvalue"], ascending=[True, True]).head(3)
                if not positive.empty:
                    group_text = str(positive["groups"].iloc[0]) if "groups" in positive.columns else "first group"
                    highlights.append(
                        f"Positive differential phenotypes in {group_text} included {_format_series(positive.set_index('phenotype')['effect_size'], n=3)}."
                    )
                if not negative.empty:
                    group_text = str(negative["groups"].iloc[0]) if "groups" in negative.columns else "second group"
                    highlights.append(
                        f"Negative differential phenotypes in {group_text} included {_format_series(negative.set_index('phenotype')['effect_size'], n=3)}."
                    )
            else:
                highlights.append(
                    f"No phenotypes reached q<=0.1; the strongest exploratory signals were {_format_series(stats_sorted.set_index('phenotype')['pvalue'], n=4)} by raw p value."
                )
        else:
            highlights.append(
                f"The smallest between-group q values were {_format_series(stats_sorted.set_index('phenotype')['qvalue'], n=4)}."
            )

    return highlights


def write_results_summary(
    *,
    output_dir: Path,
    mode: str,
    scores: pd.DataFrame,
    tier_scores: pd.DataFrame | None,
    stats_frame: pd.DataFrame | None,
    metadata: pd.DataFrame | None,
    group_column: str | None,
    highlights: list[str] | None = None,
) -> Path:
    if highlights is None:
        highlights = build_result_highlights(
            mode=mode,
            scores=scores,
            tier_scores=tier_scores,
            stats_frame=stats_frame,
            metadata=metadata,
            group_column=group_column,
        )

    lines = [
        "# TracePheno Results Summary",
        "",
        f"- Mode: `{mode}`",
        f"- Samples: `{scores.shape[1]}`",
        f"- Phenotypes: `{scores.shape[0]}`",
    ]
    if metadata is not None and group_column and group_column in metadata.columns:
        groups = metadata[group_column].astype(str).value_counts()
        lines.append(
            "- Groups: " + ", ".join(f"`{group}` ({count})" for group, count in groups.items())
        )

    lines.extend(["", "## Highlights", ""])
    lines.extend([f"- {highlight}" for highlight in highlights])

    path = output_dir / "results_summary.md"
    path.write_text("\n".join(lines).strip() + "\n", encoding="utf-8")
    return path
