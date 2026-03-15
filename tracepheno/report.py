from __future__ import annotations

from pathlib import Path

import pandas as pd
from jinja2 import Template

from tracepheno.visuals import VisualizationSpec


REPORT_TEMPLATE = Template(
    """
<!DOCTYPE html>
<html lang="zh-CN">
<head>
  <meta charset="utf-8">
  <title>TracePheno Report</title>
  <style>
    :root {
      --ink: #14213d;
      --muted: #5f6c7b;
      --panel: #ffffff;
      --line: #d7dee8;
      --accent: #0f766e;
      --bg: linear-gradient(145deg, #f5fbff 0%, #eef6f0 100%);
    }
    body {
      font-family: "Segoe UI", sans-serif;
      margin: 0;
      color: var(--ink);
      background: var(--bg);
    }
    .page {
      max-width: 1380px;
      margin: 0 auto;
      padding: 28px;
    }
    .hero {
      background: rgba(255, 255, 255, 0.86);
      border: 1px solid rgba(215, 222, 232, 0.95);
      border-radius: 22px;
      padding: 24px 28px;
      box-shadow: 0 18px 36px rgba(20, 33, 61, 0.08);
      margin-bottom: 24px;
    }
    h1 {
      margin: 0 0 8px 0;
      font-size: 2rem;
      color: #0b1f33;
    }
    h2 {
      margin: 0 0 14px 0;
      color: #0f172a;
      font-size: 1.2rem;
    }
    p {
      line-height: 1.55;
    }
    .meta {
      color: var(--muted);
      margin: 0;
    }
    .section {
      background: rgba(255, 255, 255, 0.92);
      border: 1px solid rgba(215, 222, 232, 0.95);
      border-radius: 20px;
      padding: 20px 22px;
      box-shadow: 0 16px 30px rgba(20, 33, 61, 0.06);
      margin-bottom: 22px;
    }
    .table-wrap {
      overflow-x: auto;
    }
    table {
      border-collapse: collapse;
      width: 100%;
      margin-bottom: 6px;
      background: white;
    }
    th, td {
      border: 1px solid var(--line);
      padding: 8px 10px;
      text-align: left;
      vertical-align: top;
    }
    th {
      background: #eff6ff;
    }
    .plot-grid {
      display: grid;
      grid-template-columns: repeat(auto-fit, minmax(420px, 1fr));
      gap: 18px;
    }
    .plot-card {
      border: 1px solid var(--line);
      border-radius: 18px;
      padding: 16px;
      background: linear-gradient(180deg, #ffffff 0%, #f8fbff 100%);
    }
    .plot-card p {
      color: var(--muted);
      margin-top: 0;
      margin-bottom: 12px;
      font-size: 0.95rem;
    }
    img {
      max-width: 100%;
      border: 1px solid var(--line);
      border-radius: 14px;
      background: white;
    }
  </style>
</head>
<body>
  <div class="page">
    <section class="hero">
      <h1>TracePheno Report</h1>
      <p class="meta">
        Samples: {{ sample_count }} |
        Phenotypes: {{ phenotype_count }} |
        Mode: {{ mode }}
      </p>
    </section>

    <section class="section">
      <h2>Top Phenotype Scores</h2>
      <div class="table-wrap">{{ score_table }}</div>
    </section>

    {% if stats_table %}
    <section class="section">
      <h2>Group Statistics</h2>
      <div class="table-wrap">{{ stats_table }}</div>
    </section>
    {% endif %}

    {% if highlights %}
    <section class="section">
      <h2>Result Highlights</h2>
      <ul>
        {% for item in highlights %}
        <li>{{ item }}</li>
        {% endfor %}
      </ul>
    </section>
    {% endif %}

    {% if tier_table %}
    <section class="section">
      <h2>Tiered Evidence Summary</h2>
      <div class="table-wrap">{{ tier_table }}</div>
    </section>
    {% endif %}

    {% if plots %}
    <section class="section">
      <h2>Visualization Gallery</h2>
      <div class="plot-grid">
        {% for plot in plots %}
        <article class="plot-card">
          <h2>{{ plot.title }}</h2>
          <p>{{ plot.description }}</p>
          <img src="{{ plot.filename }}" alt="{{ plot.title }}">
        </article>
        {% endfor %}
      </div>
    </section>
    {% endif %}

    {% if contribution_table %}
    <section class="section">
      <h2>Top Marker Contributions</h2>
      <div class="table-wrap">{{ contribution_table }}</div>
    </section>
    {% endif %}
  </div>
</body>
</html>
"""
)


def render_report(
    output_path: Path,
    scores: pd.DataFrame,
    tier_scores: pd.DataFrame | None,
    stats_frame: pd.DataFrame | None,
    contributions: pd.DataFrame | None,
    plots: list[VisualizationSpec],
    mode: str,
    highlights: list[str] | None = None,
) -> None:
    score_table = (
        scores.mean(axis=1)
        .sort_values(ascending=False)
        .rename("mean_score")
        .to_frame()
        .to_html(classes="table table-sm", float_format=lambda value: f"{value:.3f}")
    )
    stats_table = (
        stats_frame.to_html(index=False, float_format=lambda value: f"{value:.4f}")
        if stats_frame is not None and not stats_frame.empty
        else ""
    )
    tier_table = ""
    if tier_scores is not None and not tier_scores.empty:
        tier_summary = tier_scores.mean(axis=1).rename("mean_score").reset_index()
        tier_summary = tier_summary.sort_values(["phenotype", "tier"])
        tier_table = tier_summary.to_html(index=False, float_format=lambda value: f"{value:.3f}")
    contribution_table = (
        contributions.head(40).to_html(index=False, float_format=lambda value: f"{value:.4f}")
        if contributions is not None and not contributions.empty
        else ""
    )

    html = REPORT_TEMPLATE.render(
        sample_count=scores.shape[1],
        phenotype_count=scores.shape[0],
        mode=mode,
        score_table=score_table,
        stats_table=stats_table,
        tier_table=tier_table,
        contribution_table=contribution_table,
        plots=plots,
        highlights=highlights or [],
    )
    output_path.write_text(html, encoding="utf-8")
