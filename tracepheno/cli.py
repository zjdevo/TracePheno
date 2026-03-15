from __future__ import annotations

import argparse

from tracepheno.definitions import bundled_phenotype_config_path, load_phenotype_library
from tracepheno.io_utils import ensure_output_dir, read_numeric_matrix, read_table, write_table
from tracepheno.manuscript import save_publication_bundle
from tracepheno.narrative import build_result_highlights, write_results_summary
from tracepheno.picrust2 import read_picrust2_ko_table
from tracepheno.report import render_report
from tracepheno.scoring import build_trait_matrix_from_features, score_feature_matrix, score_taxa_from_trait_matrix
from tracepheno.stats import compare_groups
from tracepheno.visuals import (
    build_plot_gallery,
    save_clustered_heatmap,
    save_group_distribution_plot,
    save_group_mean_heatmap,
    save_group_trajectory_plot,
    save_marker_contribution_plot,
    save_differential_phenotype_plot,
    save_overview_dashboard,
    save_phenotype_landscape_plot,
    save_sample_embedding,
    save_score_heatmap,
    save_tier_summary_plot,
)


def add_shared_config_argument(parser: argparse.ArgumentParser) -> None:
    parser.add_argument(
        "--phenotype-config",
        default=str(bundled_phenotype_config_path()),
        help="Path to a custom phenotype YAML definition. Defaults to the bundled trace-element library.",
    )


def add_function_scoring_arguments(parser: argparse.ArgumentParser, *, abundance_arg: str, abundance_help: str) -> None:
    parser.add_argument(abundance_arg, required=True, help=abundance_help)
    parser.add_argument("--metadata", help="Sample metadata table.")
    parser.add_argument("--group-column", help="Metadata column used for group statistics.")
    parser.add_argument("--outdir", required=True, help="Output directory.")
    parser.add_argument(
        "--presence-cutoff",
        type=float,
        default=0.0,
        help="Minimum abundance required to count a marker as present.",
    )
    parser.add_argument(
        "--no-normalize",
        action="store_true",
        help="Skip column-wise normalization of the feature matrix.",
    )
    add_shared_config_argument(parser)


def cmd_list_phenotypes(args: argparse.Namespace) -> int:
    library = load_phenotype_library(args.phenotype_config)
    for phenotype in library:
        print(f"{phenotype.id}\t{phenotype.name}\t{phenotype.element}")
    return 0


def _render_function_outputs(
    *,
    result,
    metadata,
    group_column: str | None,
    output_dir,
    mode: str,
) -> int:
    write_table(result.scores, output_dir / "phenotype_scores.tsv")
    write_table(result.coverage, output_dir / "phenotype_coverage.tsv")
    write_table(result.abundance, output_dir / "phenotype_abundance.tsv")
    write_table(result.tier_scores, output_dir / "phenotype_tier_scores.tsv")
    write_table(result.calls, output_dir / "phenotype_calls.tsv")
    write_table(result.thresholds, output_dir / "phenotype_thresholds.tsv")
    write_table(result.marker_contributions, output_dir / "marker_contributions.tsv")
    write_table(result.match_details, output_dir / "marker_matches.tsv")

    stats_frame = None
    if metadata is not None and group_column:
        stats_frame = compare_groups(result.scores, metadata, group_column)
        if not stats_frame.empty:
            write_table(stats_frame, output_dir / "group_statistics.tsv")

    overview_dashboard_path = save_overview_dashboard(
        result.scores,
        result.tier_scores,
        metadata,
        group_column,
        stats_frame,
        output_dir / "overview_dashboard.png",
    )
    phenotype_landscape_path = save_phenotype_landscape_plot(
        result.scores,
        result.calls,
        result.tier_scores,
        output_dir / "phenotype_landscape.png",
    )
    heatmap_path = save_score_heatmap(result.scores, output_dir / "phenotype_score_heatmap.png")
    clustered_heatmap_path = save_clustered_heatmap(result.scores, output_dir / "phenotype_clustered_heatmap.png")
    differential_plot_path = save_differential_phenotype_plot(
        result.scores,
        stats_frame,
        output_dir / "differential_phenotype_map.png",
    )
    sample_embedding_path = save_sample_embedding(
        result.scores,
        metadata,
        group_column,
        output_dir / "sample_embedding.png",
    )
    tier_summary_path = save_tier_summary_plot(result.tier_scores, output_dir / "tier_evidence_summary.png")
    contribution_plot_path = save_marker_contribution_plot(
        result.marker_contributions,
        output_dir / "marker_contribution_panels.png",
    )

    group_mean_path = None
    group_distribution_path = None
    group_trajectory_path = None
    if metadata is not None and group_column:
        group_mean_path = save_group_mean_heatmap(
            result.scores,
            metadata,
            group_column,
            output_dir / "group_mean_scores.png",
        )
        group_distribution_path = save_group_distribution_plot(
            result.scores,
            metadata,
            group_column,
            output_dir / "group_distribution_scores.png",
        )
        group_trajectory_path = save_group_trajectory_plot(
            result.scores,
            metadata,
            group_column,
            output_dir / "group_trajectory_scores.png",
        )

    plots = build_plot_gallery(
        overview_dashboard_path=overview_dashboard_path,
        differential_plot_path=differential_plot_path,
        phenotype_landscape_path=phenotype_landscape_path,
        heatmap_path=heatmap_path,
        clustered_heatmap_path=clustered_heatmap_path,
        group_mean_path=group_mean_path,
        group_distribution_path=group_distribution_path,
        group_trajectory_path=group_trajectory_path,
        sample_embedding_path=sample_embedding_path,
        tier_summary_path=tier_summary_path,
        contribution_plot_path=contribution_plot_path,
    )
    highlights = build_result_highlights(
        mode=mode,
        scores=result.scores,
        tier_scores=result.tier_scores,
        stats_frame=stats_frame,
        metadata=metadata,
        group_column=group_column,
    )
    results_summary_path = write_results_summary(
        output_dir=output_dir,
        mode=mode,
        scores=result.scores,
        tier_scores=result.tier_scores,
        stats_frame=stats_frame,
        metadata=metadata,
        group_column=group_column,
        highlights=highlights,
    )
    save_publication_bundle(
        output_dir=output_dir,
        mode=mode,
        scores=result.scores,
        stats_frame=stats_frame,
        group_column=group_column,
        plot_paths={
            "overview_dashboard": overview_dashboard_path,
            "differential_plot": differential_plot_path,
            "phenotype_landscape": phenotype_landscape_path,
            "heatmap": heatmap_path,
            "clustered_heatmap": clustered_heatmap_path,
            "group_mean": group_mean_path,
            "group_distribution": group_distribution_path,
            "group_trajectory": group_trajectory_path,
            "sample_embedding": sample_embedding_path,
            "tier_summary": tier_summary_path,
            "contribution_plot": contribution_plot_path,
        },
        results_summary_path=results_summary_path,
    )
    render_report(
        output_path=output_dir / "report.html",
        scores=result.scores,
        tier_scores=result.tier_scores,
        stats_frame=stats_frame,
        contributions=result.marker_contributions,
        plots=plots,
        mode=mode,
        highlights=highlights,
    )
    return 0


def cmd_score_functions(args: argparse.Namespace) -> int:
    library = load_phenotype_library(args.phenotype_config)
    abundance = read_numeric_matrix(args.abundance)
    metadata = read_table(args.metadata) if args.metadata else None
    output_dir = ensure_output_dir(args.outdir)

    result = score_feature_matrix(
        abundance_matrix=abundance,
        library=library,
        normalize_input=not args.no_normalize,
        presence_cutoff=args.presence_cutoff,
    )
    return _render_function_outputs(
        result=result,
        metadata=metadata,
        group_column=args.group_column,
        output_dir=output_dir,
        mode="function",
    )


def cmd_score_picrust2(args: argparse.Namespace) -> int:
    library = load_phenotype_library(args.phenotype_config)
    abundance = read_picrust2_ko_table(args.input)
    metadata = read_table(args.metadata) if args.metadata else None
    output_dir = ensure_output_dir(args.outdir)

    write_table(abundance, output_dir / "picrust2_resolved_ko_matrix.tsv")
    result = score_feature_matrix(
        abundance_matrix=abundance,
        library=library,
        normalize_input=not args.no_normalize,
        presence_cutoff=args.presence_cutoff,
    )
    return _render_function_outputs(
        result=result,
        metadata=metadata,
        group_column=args.group_column,
        output_dir=output_dir,
        mode="picrust2",
    )


def cmd_build_traits(args: argparse.Namespace) -> int:
    library = load_phenotype_library(args.phenotype_config)
    abundance = read_numeric_matrix(args.abundance)
    trait_matrix = build_trait_matrix_from_features(
        abundance_matrix=abundance,
        library=library,
        normalize_input=not args.no_normalize,
        presence_cutoff=args.presence_cutoff,
        binary=not args.continuous,
    )
    write_table(trait_matrix, args.out)
    return 0


def cmd_score_taxa(args: argparse.Namespace) -> int:
    abundance = read_numeric_matrix(args.abundance)
    traits = read_numeric_matrix(args.traits)
    metadata = read_table(args.metadata) if args.metadata else None
    output_dir = ensure_output_dir(args.outdir)

    scores = score_taxa_from_trait_matrix(
        abundance_matrix=abundance,
        trait_matrix=traits,
        normalize_input=not args.no_normalize,
    )
    write_table(scores, output_dir / "phenotype_scores.tsv")

    stats_frame = None
    if metadata is not None and args.group_column:
        stats_frame = compare_groups(scores, metadata, args.group_column)
        if not stats_frame.empty:
            write_table(stats_frame, output_dir / "group_statistics.tsv")

    overview_dashboard_path = save_overview_dashboard(
        scores,
        None,
        metadata,
        args.group_column,
        stats_frame,
        output_dir / "overview_dashboard.png",
    )
    heatmap_path = save_score_heatmap(scores, output_dir / "phenotype_score_heatmap.png")
    clustered_heatmap_path = save_clustered_heatmap(scores, output_dir / "phenotype_clustered_heatmap.png")
    differential_plot_path = save_differential_phenotype_plot(
        scores,
        stats_frame,
        output_dir / "differential_phenotype_map.png",
    )
    sample_embedding_path = save_sample_embedding(scores, metadata, args.group_column, output_dir / "sample_embedding.png")

    group_mean_path = None
    group_distribution_path = None
    group_trajectory_path = None
    if metadata is not None and args.group_column:
        group_mean_path = save_group_mean_heatmap(scores, metadata, args.group_column, output_dir / "group_mean_scores.png")
        group_distribution_path = save_group_distribution_plot(
            scores,
            metadata,
            args.group_column,
            output_dir / "group_distribution_scores.png",
        )
        group_trajectory_path = save_group_trajectory_plot(
            scores,
            metadata,
            args.group_column,
            output_dir / "group_trajectory_scores.png",
        )

    plots = build_plot_gallery(
        overview_dashboard_path=overview_dashboard_path,
        differential_plot_path=differential_plot_path,
        heatmap_path=heatmap_path,
        clustered_heatmap_path=clustered_heatmap_path,
        group_mean_path=group_mean_path,
        group_distribution_path=group_distribution_path,
        group_trajectory_path=group_trajectory_path,
        sample_embedding_path=sample_embedding_path,
    )
    highlights = build_result_highlights(
        mode="taxon",
        scores=scores,
        tier_scores=None,
        stats_frame=stats_frame,
        metadata=metadata,
        group_column=args.group_column,
    )
    results_summary_path = write_results_summary(
        output_dir=output_dir,
        mode="taxon",
        scores=scores,
        tier_scores=None,
        stats_frame=stats_frame,
        metadata=metadata,
        group_column=args.group_column,
        highlights=highlights,
    )
    save_publication_bundle(
        output_dir=output_dir,
        mode="taxon",
        scores=scores,
        stats_frame=stats_frame,
        group_column=args.group_column,
        plot_paths={
            "overview_dashboard": overview_dashboard_path,
            "differential_plot": differential_plot_path,
            "heatmap": heatmap_path,
            "clustered_heatmap": clustered_heatmap_path,
            "group_mean": group_mean_path,
            "group_distribution": group_distribution_path,
            "group_trajectory": group_trajectory_path,
            "sample_embedding": sample_embedding_path,
        },
        results_summary_path=results_summary_path,
    )
    render_report(
        output_path=output_dir / "report.html",
        scores=scores,
        tier_scores=None,
        stats_frame=stats_frame,
        contributions=None,
        plots=plots,
        mode="taxon",
        highlights=highlights,
    )
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="tracepheno",
        description="Function-first phenotype analysis for trace-element metabolism in microbiomes.",
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    list_parser = subparsers.add_parser("list-phenotypes", help="List bundled trace-element phenotypes.")
    add_shared_config_argument(list_parser)
    list_parser.set_defaults(func=cmd_list_phenotypes)

    score_functions_parser = subparsers.add_parser(
        "score-functions",
        help="Score samples from a feature abundance matrix.",
    )
    add_function_scoring_arguments(
        score_functions_parser,
        abundance_arg="--abundance",
        abundance_help="Feature abundance table.",
    )
    score_functions_parser.set_defaults(func=cmd_score_functions)

    score_picrust2_parser = subparsers.add_parser(
        "score-picrust2",
        help="Score trace-element phenotypes from PICRUSt2 KO predictions.",
    )
    add_function_scoring_arguments(
        score_picrust2_parser,
        abundance_arg="--input",
        abundance_help="PICRUSt2 KO table such as pred_metagenome_unstrat.tsv.gz or pred_metagenome_contrib.tsv.gz.",
    )
    score_picrust2_parser.set_defaults(func=cmd_score_picrust2)

    build_traits_parser = subparsers.add_parser(
        "build-traits",
        help="Build a genome/taxon trait matrix from feature annotations using presence/absence-oriented scoring.",
    )
    build_traits_parser.add_argument("--abundance", required=True, help="Genome feature matrix.")
    build_traits_parser.add_argument("--out", required=True, help="Output path for the trait matrix.")
    build_traits_parser.add_argument(
        "--continuous",
        action="store_true",
        help="Write continuous scores instead of binary calls.",
    )
    build_traits_parser.add_argument(
        "--presence-cutoff",
        type=float,
        default=0.0,
        help="Minimum abundance required to count a marker as present.",
    )
    build_traits_parser.add_argument(
        "--no-normalize",
        action="store_true",
        help="Skip column-wise normalization of the feature matrix.",
    )
    add_shared_config_argument(build_traits_parser)
    build_traits_parser.set_defaults(func=cmd_build_traits)

    score_taxa_parser = subparsers.add_parser(
        "score-taxa",
        help="Score samples from taxon abundance and a trait matrix.",
    )
    score_taxa_parser.add_argument("--abundance", required=True, help="Taxon abundance table.")
    score_taxa_parser.add_argument("--traits", required=True, help="Taxon trait matrix.")
    score_taxa_parser.add_argument("--metadata", help="Sample metadata table.")
    score_taxa_parser.add_argument("--group-column", help="Metadata column used for group statistics.")
    score_taxa_parser.add_argument("--outdir", required=True, help="Output directory.")
    score_taxa_parser.add_argument(
        "--no-normalize",
        action="store_true",
        help="Skip column-wise normalization of the abundance matrix.",
    )
    score_taxa_parser.set_defaults(func=cmd_score_taxa)

    return parser


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())
