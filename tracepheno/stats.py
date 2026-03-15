from __future__ import annotations

import math
from dataclasses import dataclass

import numpy as np
import pandas as pd
from scipy import stats


@dataclass(frozen=True)
class GroupStatResult:
    phenotype: str
    test: str
    groups: str
    statistic: float
    pvalue: float
    effect_size: float | None
    effect_name: str | None


def benjamini_hochberg(pvalues: pd.Series) -> pd.Series:
    valid = pvalues.notna()
    if not valid.any():
        return pd.Series(np.nan, index=pvalues.index)

    ranked = pvalues[valid].sort_values()
    adjusted = pd.Series(index=ranked.index, dtype=float)
    total = len(ranked)
    running = 1.0
    for rank, (index, value) in enumerate(reversed(list(ranked.items())), start=1):
        true_rank = total - rank + 1
        running = min(running, value * total / true_rank)
        adjusted.loc[index] = running
    output = pd.Series(np.nan, index=pvalues.index, dtype=float)
    output.loc[adjusted.index] = adjusted.clip(upper=1.0)
    return output


def cliffs_delta(group_a: np.ndarray, group_b: np.ndarray) -> float:
    comparisons = 0
    greater = 0
    lower = 0
    for value_a in group_a:
        for value_b in group_b:
            comparisons += 1
            if value_a > value_b:
                greater += 1
            elif value_a < value_b:
                lower += 1
    if comparisons == 0:
        return math.nan
    return (greater - lower) / comparisons


def compare_groups(scores: pd.DataFrame, metadata: pd.DataFrame, group_column: str) -> pd.DataFrame:
    if group_column not in metadata.columns:
        raise ValueError(f"Group column '{group_column}' was not found in metadata")

    aligned_samples = [sample for sample in scores.columns if sample in metadata.index]
    if not aligned_samples:
        raise ValueError("No overlapping sample IDs between score table and metadata")

    aligned_scores = scores[aligned_samples]
    aligned_meta = metadata.loc[aligned_samples]

    records: list[GroupStatResult] = []
    for phenotype in aligned_scores.index:
        phenotype_values = aligned_scores.loc[phenotype]
        grouped = []
        for group_name, subset in aligned_meta.groupby(group_column):
            sample_ids = subset.index.intersection(phenotype_values.index)
            values = phenotype_values.loc[sample_ids].astype(float).to_numpy()
            if len(values) == 0:
                continue
            grouped.append((str(group_name), values))

        if len(grouped) < 2:
            continue

        if len(grouped) == 2:
            (group_a_name, group_a), (group_b_name, group_b) = grouped
            statistic, pvalue = stats.mannwhitneyu(group_a, group_b, alternative="two-sided")
            records.append(
                GroupStatResult(
                    phenotype=phenotype,
                    test="mannwhitneyu",
                    groups=f"{group_a_name} vs {group_b_name}",
                    statistic=float(statistic),
                    pvalue=float(pvalue),
                    effect_size=float(cliffs_delta(group_a, group_b)),
                    effect_name="cliffs_delta",
                )
            )
        else:
            arrays = [values for _, values in grouped]
            statistic, pvalue = stats.kruskal(*arrays)
            group_names = ", ".join(name for name, _ in grouped)
            records.append(
                GroupStatResult(
                    phenotype=phenotype,
                    test="kruskal",
                    groups=group_names,
                    statistic=float(statistic),
                    pvalue=float(pvalue),
                    effect_size=None,
                    effect_name=None,
                )
            )

    result = pd.DataFrame([record.__dict__ for record in records])
    if result.empty:
        return result

    result["qvalue"] = benjamini_hochberg(result["pvalue"])
    result = result.sort_values(["qvalue", "pvalue", "phenotype"], na_position="last")
    return result
