from __future__ import annotations

import re
from dataclasses import dataclass

import numpy as np
import pandas as pd

from tracepheno.definitions import MarkerSet, PhenotypeLibrary
from tracepheno.io_utils import normalize_columns

TOKEN_PATTERN = re.compile(r"[A-Za-z0-9][A-Za-z0-9_.-]*")
FULL_COVERAGE_TOLERANCE = 1e-9


@dataclass
class ScoringResult:
    scores: pd.DataFrame
    coverage: pd.DataFrame
    abundance: pd.DataFrame
    tier_scores: pd.DataFrame
    calls: pd.DataFrame
    thresholds: pd.DataFrame
    marker_contributions: pd.DataFrame
    match_details: pd.DataFrame


@dataclass
class TraitInferenceResult:
    matrix: pd.DataFrame
    raw_matrix: pd.DataFrame
    score_matrix: pd.DataFrame
    status: pd.DataFrame
    genome_quality: pd.DataFrame


@dataclass
class TaxonScoringResult:
    scores: pd.DataFrame
    lower_bounds: pd.DataFrame
    upper_bounds: pd.DataFrame
    knowledge_coverage: pd.DataFrame
    unknown_abundance: pd.DataFrame


def canonical_tokens(value: str) -> set[str]:
    text = str(value).strip().lower()
    if not text:
        return set()

    tokens = {text}
    normalized = (
        text.replace("|", " ")
        .replace(";", " ")
        .replace(",", " ")
        .replace("(", " ")
        .replace(")", " ")
        .replace("[", " ")
        .replace("]", " ")
        .replace("/", " ")
        .replace("\\", " ")
        .replace(":", " ")
    )
    tokens.update(token.lower() for token in TOKEN_PATTERN.findall(normalized))

    for token in list(tokens):
        if token.startswith("ko") and len(token) == 7:
            tokens.add("k" + token[2:])
        if "-" in token or "_" in token:
            for part in re.split(r"[-_]", token):
                if part:
                    tokens.add(part.lower())
    return tokens


def build_feature_lookup(index: pd.Index) -> dict[str, set[str]]:
    return {feature: canonical_tokens(str(feature)) for feature in index}


def match_feature_rows(feature_lookup: dict[str, set[str]], alias: str) -> list[str]:
    alias_tokens = canonical_tokens(alias)
    matches = []
    for feature, tokens in feature_lookup.items():
        if alias_tokens.intersection(tokens):
            matches.append(feature)
    return matches


def evaluate_marker_set(
    matrix: pd.DataFrame,
    feature_lookup: dict[str, set[str]],
    marker_set: MarkerSet,
    presence_cutoff: float,
    *,
    feature_mode: str,
    normalize_input: bool,
) -> tuple[pd.Series, pd.Series, dict[str, list[str]], pd.Series]:
    alias_presence: list[pd.Series] = []
    alias_abundance: list[pd.Series] = []
    matched_rows: dict[str, list[str]] = {}
    effective_presence_cutoff = 0.0 if feature_mode == "binary" else presence_cutoff
    for alias in marker_set.genes:
        rows = match_feature_rows(feature_lookup, alias)
        matched_rows[alias] = rows
        if rows:
            abundance = matrix.loc[rows].sum(axis=0)
        else:
            abundance = pd.Series(0.0, index=matrix.columns)
        alias_presence.append((abundance > effective_presence_cutoff).astype(float))
        alias_abundance.append(abundance.astype(float))

    if not alias_presence:
        zero = pd.Series(0.0, index=matrix.columns)
        return zero, zero, matched_rows, zero

    coverage_frame = pd.concat(alias_presence, axis=1)
    abundance_frame = pd.concat(alias_abundance, axis=1)

    if marker_set.logic == "all":
        coverage = coverage_frame.mean(axis=1)
    elif marker_set.logic == "any":
        hit_count = coverage_frame.sum(axis=1)
        coverage = (hit_count / max(marker_set.min_hits, 1)).clip(upper=1.0)
    else:
        raise ValueError(f"Unsupported marker logic: {marker_set.logic}")

    unique_rows = sorted({row for rows in matched_rows.values() for row in rows})
    if unique_rows:
        abundance = matrix.loc[unique_rows].sum(axis=0)
    else:
        abundance = pd.Series(0.0, index=matrix.columns)

    if feature_mode == "binary":
        support = coverage.copy()
    else:
        abundance = abundance.clip(lower=0.0)
        if normalize_input:
            bounded_abundance = np.sqrt(abundance.clip(upper=1.0))
        else:
            bounded_abundance = np.sqrt((abundance / (1.0 + abundance)).clip(upper=1.0))
        support = coverage * bounded_abundance
    return coverage, abundance, matched_rows, support


def weighted_series_mean(
    series_list: list[pd.Series],
    weights: list[float],
    index: pd.Index,
) -> pd.Series:
    if not series_list:
        return pd.Series(0.0, index=index)
    weight_vector = np.array(weights, dtype=float)
    weight_vector = weight_vector / weight_vector.sum()
    frame = pd.concat(series_list, axis=1)
    return pd.Series(frame.to_numpy().dot(weight_vector), index=index)


def top_k_series_mean(
    series_list: list[pd.Series],
    k: int,
    index: pd.Index,
) -> pd.Series:
    if not series_list or k <= 0:
        return pd.Series(0.0, index=index)
    frame = pd.concat(series_list, axis=1)
    bounded_k = min(k, frame.shape[1])
    sorted_values = np.sort(frame.to_numpy(), axis=1)
    return pd.Series(sorted_values[:, -bounded_k:].mean(axis=1), index=index)


def count_fully_satisfied_markers(series_list: list[pd.Series], index: pd.Index) -> pd.Series:
    if not series_list:
        return pd.Series(0, index=index, dtype=int)
    frame = pd.concat(series_list, axis=1)
    return (frame >= (1.0 - FULL_COVERAGE_TOLERANCE)).sum(axis=1).astype(int)


def normalize_fraction_series(
    values: pd.Series | None,
    index: pd.Index,
) -> pd.Series | None:
    if values is None:
        return None
    series = pd.Series(values, dtype=float).reindex(index)
    if series.dropna().gt(1.0).any():
        series = series / 100.0
    return series.clip(lower=0.0, upper=1.0)


def classify_genome_quality(
    genomes: pd.Index,
    completeness: pd.Series | None = None,
    contamination: pd.Series | None = None,
) -> pd.DataFrame:
    completeness_series = normalize_fraction_series(completeness, genomes)
    contamination_series = normalize_fraction_series(contamination, genomes)

    if completeness_series is None:
        completeness_series = pd.Series(np.nan, index=genomes, dtype=float)
    if contamination_series is None:
        contamination_series = pd.Series(np.nan, index=genomes, dtype=float)

    effective_completeness = completeness_series.fillna(1.0)
    effective_contamination = contamination_series.fillna(0.0)
    has_quality = completeness_series.notna() | contamination_series.notna()

    quality_class = pd.Series("unknown_quality", index=genomes, dtype=object)
    high_mask = has_quality & (effective_completeness >= 0.9) & (effective_contamination <= 0.05)
    medium_mask = has_quality & ~high_mask & (effective_completeness >= 0.5) & (effective_contamination <= 0.1)
    low_mask = has_quality & ~(high_mask | medium_mask)

    quality_class.loc[high_mask] = "high_quality"
    quality_class.loc[medium_mask] = "medium_quality"
    quality_class.loc[low_mask] = "low_quality"

    negative_call_policy = pd.Series("no_quality_metadata", index=genomes, dtype=object)
    negative_call_policy.loc[high_mask] = "allow_absence"
    negative_call_policy.loc[medium_mask] = "uncertain_absence"
    negative_call_policy.loc[low_mask] = "unresolved_all_calls"

    quality_score = (effective_completeness - 5.0 * effective_contamination).clip(lower=0.0)
    quality_frame = pd.DataFrame(
        {
            "completeness": completeness_series,
            "contamination": contamination_series,
            "quality_score": quality_score,
            "quality_class": quality_class,
            "negative_call_policy": negative_call_policy,
        }
    )
    quality_frame.index.name = genomes.name or "genome"
    return quality_frame


def score_feature_matrix(
    abundance_matrix: pd.DataFrame,
    library: PhenotypeLibrary,
    normalize_input: bool = True,
    presence_cutoff: float = 0.0,
    feature_mode: str = "abundance",
) -> ScoringResult:
    working = abundance_matrix.copy()
    working.index = working.index.astype(str)
    if feature_mode not in {"abundance", "binary"}:
        raise ValueError("feature_mode must be 'abundance' or 'binary'")

    if feature_mode == "binary":
        working = (working > presence_cutoff).astype(float)
    elif normalize_input:
        working = normalize_columns(working)

    feature_lookup = build_feature_lookup(working.index)

    phenotype_scores: dict[str, pd.Series] = {}
    phenotype_coverage: dict[str, pd.Series] = {}
    phenotype_abundance: dict[str, pd.Series] = {}
    phenotype_tier_scores: dict[tuple[str, str], pd.Series] = {}
    phenotype_calls: dict[str, pd.Series] = {}
    threshold_rows: list[dict[str, object]] = []
    marker_rows: list[dict[str, object]] = []
    match_rows: list[dict[str, object]] = []

    for phenotype in library:
        marker_items: list[dict[str, object]] = []
        tier_components: dict[str, list[pd.Series]] = {}
        tier_weights: dict[str, list[float]] = {}

        for marker_set in phenotype.markers:
            coverage, abundance, matched_rows, support = evaluate_marker_set(
                working,
                feature_lookup,
                marker_set,
                presence_cutoff,
                feature_mode=feature_mode,
                normalize_input=normalize_input,
            )
            if feature_mode == "binary":
                marker_score = coverage.copy()
            else:
                marker_score = 0.8 * coverage + 0.2 * support
            tier_components.setdefault(marker_set.tier, []).append(marker_score)
            tier_weights.setdefault(marker_set.tier, []).append(marker_set.weight)
            marker_items.append(
                {
                    "id": marker_set.id,
                    "tier": marker_set.tier,
                    "weight": marker_set.weight,
                    "coverage": coverage,
                    "abundance": abundance,
                    "score": marker_score,
                }
            )

            matched_union = sorted({row for rows in matched_rows.values() for row in rows})
            total_abundance = float(abundance.sum())
            for row in matched_union:
                contribution = float(working.loc[row].sum())
                marker_rows.append(
                    {
                        "phenotype": phenotype.id,
                        "marker_set": marker_set.id,
                        "feature": row,
                        "relative_contribution": contribution / total_abundance if total_abundance > 0 else 0.0,
                        "total_abundance": contribution,
                    }
                )

            for alias, rows in matched_rows.items():
                match_rows.append(
                    {
                        "phenotype": phenotype.id,
                        "marker_set": marker_set.id,
                        "alias": alias,
                        "matched_rows": ";".join(rows),
                        "matched_count": len(rows),
                    }
                )

        if not marker_items:
            zero = pd.Series(0.0, index=working.columns)
            phenotype_scores[phenotype.id] = zero
            phenotype_coverage[phenotype.id] = zero
            phenotype_abundance[phenotype.id] = zero
            phenotype_calls[phenotype.id] = zero.astype(int)
            threshold_rows.append(
                {
                    "phenotype": phenotype.id,
                    "threshold": 1.0,
                    "threshold_hint": phenotype.threshold_hint,
                    "required_core_hits": 0,
                    "available_core_marker_sets": 0,
                    "decision_rule": "no_markers",
                }
            )
            continue

        all_coverages = [item["coverage"] for item in marker_items]
        all_abundances = [item["abundance"] for item in marker_items]
        all_weights = [float(item["weight"]) for item in marker_items]

        core_items = [item for item in marker_items if item["tier"] == "core"]
        accessory_items = [item for item in marker_items if item["tier"] == "accessory"]
        ambiguous_items = [item for item in marker_items if item["tier"] == "ambiguous"]

        available_core_marker_sets = len(core_items)
        required_core_hits = min(phenotype.core_min_hits, available_core_marker_sets)

        if core_items and required_core_hits > 0:
            core_score_series = top_k_series_mean(
                [item["score"] for item in core_items],
                required_core_hits,
                working.columns,
            )
            core_coverage_series = top_k_series_mean(
                [item["coverage"] for item in core_items],
                required_core_hits,
                working.columns,
            )
            satisfied_core_series = count_fully_satisfied_markers(
                [item["coverage"] for item in core_items],
                working.columns,
            )
        else:
            core_score_series = pd.Series(0.0, index=working.columns)
            core_coverage_series = pd.Series(0.0, index=working.columns)
            satisfied_core_series = pd.Series(0, index=working.columns, dtype=int)

        accessory_score_series = weighted_series_mean(
            [item["score"] for item in accessory_items],
            [float(item["weight"]) for item in accessory_items],
            working.columns,
        )
        ambiguous_score_series = weighted_series_mean(
            [item["score"] for item in ambiguous_items],
            [float(item["weight"]) for item in ambiguous_items],
            working.columns,
        )

        if required_core_hits > 0:
            coverage_series = core_coverage_series.rename(phenotype.id)
            score_series = (
                0.8 * core_score_series
                + 0.15 * accessory_score_series
                + 0.05 * ambiguous_score_series
            ).rename(phenotype.id)
            call_series = (
                (score_series >= phenotype.threshold_hint)
                & (satisfied_core_series >= required_core_hits)
            ).astype(int)
            decision_rule = "deterministic_core_gate"
        else:
            coverage_series = weighted_series_mean(all_coverages, all_weights, working.columns).rename(phenotype.id)
            score_series = weighted_series_mean(
                [item["score"] for item in marker_items],
                all_weights,
                working.columns,
            ).rename(phenotype.id)
            call_series = (score_series >= phenotype.threshold_hint).astype(int)
            decision_rule = "deterministic_threshold_only"

        abundance_series = weighted_series_mean(all_abundances, all_weights, working.columns).rename(phenotype.id)

        for tier_name, tier_series_list in tier_components.items():
            if tier_name == "core" and required_core_hits > 0:
                tier_series = core_score_series.rename(f"{phenotype.id}|{tier_name}")
            else:
                tier_series = weighted_series_mean(
                    tier_series_list,
                    tier_weights[tier_name],
                    working.columns,
                ).rename(f"{phenotype.id}|{tier_name}")
            phenotype_tier_scores[(phenotype.id, tier_name)] = tier_series

        phenotype_coverage[phenotype.id] = coverage_series
        phenotype_abundance[phenotype.id] = abundance_series
        phenotype_scores[phenotype.id] = score_series
        phenotype_calls[phenotype.id] = call_series
        threshold_rows.append(
            {
                "phenotype": phenotype.id,
                "threshold": phenotype.threshold_hint,
                "threshold_hint": phenotype.threshold_hint,
                "required_core_hits": required_core_hits,
                "available_core_marker_sets": available_core_marker_sets,
                "decision_rule": decision_rule,
            }
        )

    score_frame = pd.DataFrame(phenotype_scores).T
    coverage_frame = pd.DataFrame(phenotype_coverage).T
    abundance_frame = pd.DataFrame(phenotype_abundance).T
    tier_frame = pd.DataFrame(phenotype_tier_scores).T
    if not tier_frame.empty:
        tier_frame.index = pd.MultiIndex.from_tuples(tier_frame.index, names=["phenotype", "tier"])
    call_frame = pd.DataFrame(phenotype_calls).T
    threshold_frame = pd.DataFrame(threshold_rows).set_index("phenotype")
    contribution_frame = pd.DataFrame(marker_rows)
    if not contribution_frame.empty:
        contribution_frame = contribution_frame.sort_values(
            ["phenotype", "marker_set", "relative_contribution"],
            ascending=[True, True, False],
        )
    match_frame = pd.DataFrame(match_rows)

    return ScoringResult(
        scores=score_frame,
        coverage=coverage_frame,
        abundance=abundance_frame,
        tier_scores=tier_frame,
        calls=call_frame,
        thresholds=threshold_frame,
        marker_contributions=contribution_frame,
        match_details=match_frame,
    )


def build_trait_matrix_from_features(
    abundance_matrix: pd.DataFrame,
    library: PhenotypeLibrary,
    normalize_input: bool = False,
    presence_cutoff: float = 0.0,
    binary: bool = True,
    completeness: pd.Series | None = None,
    contamination: pd.Series | None = None,
    quality_policy: str = "mimag",
) -> pd.DataFrame:
    result = infer_trait_matrix_from_features(
        abundance_matrix=abundance_matrix,
        library=library,
        normalize_input=normalize_input,
        presence_cutoff=presence_cutoff,
        binary=binary,
        completeness=completeness,
        contamination=contamination,
        quality_policy=quality_policy,
    )
    return result.matrix


def infer_trait_matrix_from_features(
    abundance_matrix: pd.DataFrame,
    library: PhenotypeLibrary,
    normalize_input: bool = False,
    presence_cutoff: float = 0.0,
    binary: bool = True,
    completeness: pd.Series | None = None,
    contamination: pd.Series | None = None,
    quality_policy: str = "mimag",
) -> TraitInferenceResult:
    if quality_policy not in {"mimag", "none"}:
        raise ValueError("quality_policy must be 'mimag' or 'none'")

    result = score_feature_matrix(
        abundance_matrix=abundance_matrix,
        library=library,
        normalize_input=normalize_input,
        presence_cutoff=presence_cutoff,
        feature_mode="binary",
    )

    raw_call_matrix = result.calls.T.astype(float)
    raw_call_matrix.index.name = abundance_matrix.columns.name or "genome"
    raw_call_matrix.columns.name = "phenotype"

    score_matrix = result.scores.T.astype(float)
    score_matrix.index.name = abundance_matrix.columns.name or "genome"
    score_matrix.columns.name = "phenotype"

    if binary:
        matrix = raw_call_matrix.astype("Float64")
    else:
        matrix = score_matrix.copy()

    status = raw_call_matrix.map(lambda value: "present" if value >= 0.5 else "absent")
    status.index.name = raw_call_matrix.index.name
    status.columns.name = raw_call_matrix.columns.name

    genome_quality = classify_genome_quality(raw_call_matrix.index, completeness, contamination)
    has_quality_metadata = genome_quality["quality_class"].ne("unknown_quality").any()
    if quality_policy == "mimag" and binary and has_quality_metadata:
        medium_quality_genomes = genome_quality.index[genome_quality["quality_class"] == "medium_quality"]
        for genome_id in medium_quality_genomes:
            negative_mask = raw_call_matrix.loc[genome_id] < 0.5
            if negative_mask.any():
                matrix.loc[genome_id, negative_mask] = pd.NA
                status.loc[genome_id, negative_mask] = "uncertain_absence"

        low_quality_genomes = genome_quality.index[genome_quality["quality_class"] == "low_quality"]
        for genome_id in low_quality_genomes:
            positive_mask = raw_call_matrix.loc[genome_id] >= 0.5
            status.loc[genome_id, positive_mask] = "uncertain_presence"
            status.loc[genome_id, ~positive_mask] = "unresolved_low_quality"
            matrix.loc[genome_id] = pd.NA

    return TraitInferenceResult(
        matrix=matrix,
        raw_matrix=raw_call_matrix if binary else score_matrix,
        score_matrix=score_matrix,
        status=status,
        genome_quality=genome_quality,
    )


def score_taxa_from_trait_matrix(
    abundance_matrix: pd.DataFrame,
    trait_matrix: pd.DataFrame,
    normalize_input: bool = True,
) -> pd.DataFrame:
    return score_taxa_from_trait_matrix_detailed(
        abundance_matrix=abundance_matrix,
        trait_matrix=trait_matrix,
        normalize_input=normalize_input,
    ).scores


def score_taxa_from_trait_matrix_detailed(
    abundance_matrix: pd.DataFrame,
    trait_matrix: pd.DataFrame,
    normalize_input: bool = True,
) -> TaxonScoringResult:
    working_abundance = abundance_matrix.copy()
    working_abundance.index = working_abundance.index.astype(str)
    working_traits = trait_matrix.copy()
    working_traits.index = working_traits.index.astype(str)

    if normalize_input:
        working_abundance = normalize_columns(working_abundance)

    common_taxa = working_abundance.index.intersection(working_traits.index)
    if len(common_taxa) == 0:
        raise ValueError("No overlapping taxa/genomes between abundance table and trait matrix")

    aligned_abundance = working_abundance.loc[common_taxa]
    aligned_traits = working_traits.loc[common_taxa].apply(pd.to_numeric, errors="coerce")

    lower_bound = aligned_traits.fillna(0.0).T.dot(aligned_abundance)
    unknown_abundance = aligned_traits.isna().astype(float).T.dot(aligned_abundance)
    known_abundance = aligned_traits.notna().astype(float).T.dot(aligned_abundance)

    total_abundance = aligned_abundance.sum(axis=0)
    safe_total_abundance = total_abundance.where(total_abundance > 0, np.nan)
    knowledge_coverage = known_abundance.divide(safe_total_abundance, axis=1).fillna(0.0)
    upper_bound = lower_bound + unknown_abundance

    lower_bound.index.name = "phenotype"
    upper_bound.index.name = "phenotype"
    knowledge_coverage.index.name = "phenotype"
    unknown_abundance.index.name = "phenotype"

    return TaxonScoringResult(
        scores=lower_bound,
        lower_bounds=lower_bound,
        upper_bounds=upper_bound,
        knowledge_coverage=knowledge_coverage,
        unknown_abundance=unknown_abundance,
    )
