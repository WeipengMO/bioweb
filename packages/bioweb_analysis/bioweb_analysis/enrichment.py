"""Gene set enrichment analysis."""

from __future__ import annotations

import os
from pathlib import Path
import textwrap
from typing import Any

import numpy as np
import pandas as pd
from scipy.stats import fisher_exact, hypergeom

from bioweb_analysis.results import ResultsManager

MSIGDB_PATH = Path("data/msigdb/msigdb.parquet")

results = ResultsManager("enrichment")


def _clean_genes(genes: list[str]) -> list[str]:
    cleaned = []
    seen = set()
    for gene in genes:
        normalized = gene.strip().upper()
        if not normalized or normalized in seen:
            continue
        cleaned.append(normalized)
        seen.add(normalized)
    if not cleaned:
        raise ValueError("At least one non-empty gene symbol is required")
    return cleaned


def _clean_optional_genes(genes: list[str] | None) -> list[str]:
    if not genes:
        return []
    return _clean_genes(genes)


def _clean_collections(collections: list[str]) -> list[str]:
    selected = [collection.strip() for collection in collections if collection.strip()]
    if not selected:
        raise ValueError("At least one gene set collection is required")
    return selected


def _load_msigdb() -> pd.DataFrame:
    """Load local MSigDB data."""
    if not MSIGDB_PATH.exists():
        raise FileNotFoundError(
            f"MSigDB data not found at {MSIGDB_PATH}. "
            f"Run: python scripts/data/download_msigdb.py"
        )
    msigdb = pd.read_parquet(MSIGDB_PATH)
    return _normalize_gene_set_table(msigdb)


def _normalize_gene_set_table(msigdb: pd.DataFrame) -> pd.DataFrame:
    """Normalize supported MSigDB table schemas to collection/term/gene."""
    rename_map = {}
    if "geneset" in msigdb.columns:
        rename_map["geneset"] = "term"
    if "term" in msigdb.columns:
        rename_map["term"] = "term"
    if "genesymbol" in msigdb.columns:
        rename_map["genesymbol"] = "gene"
    if "gene" in msigdb.columns:
        rename_map["gene"] = "gene"

    net = msigdb.rename(columns=rename_map).copy()
    required = {"collection", "term", "gene"}
    missing = required - set(net.columns)
    if missing:
        raise ValueError(f"MSigDB table is missing required columns: {sorted(missing)}")

    net = net.loc[:, ["collection", "term", "gene"]].dropna()
    net["collection"] = net["collection"].astype(str)
    net["term"] = net["term"].astype(str)
    net["gene"] = net["gene"].astype(str).str.upper()
    return net.drop_duplicates()


def _get_gene_sets(collections: list[str], msigdb: pd.DataFrame) -> pd.DataFrame:
    """Filter MSigDB to the requested collections."""
    if "ALL" in collections:
        net = msigdb.copy()
    else:
        net = msigdb[msigdb["collection"].isin(collections)].copy()

    net = net.drop_duplicates(subset=["collection", "term", "gene"])
    return net


def _benjamini_hochberg(p_values: list[float]) -> list[float]:
    """Return Benjamini-Hochberg adjusted p values in input order."""
    total = len(p_values)
    adjusted = [1.0] * total
    previous = 1.0
    ranked = sorted(enumerate(p_values), key=lambda item: item[1], reverse=True)
    for rank_from_end, (index, p_value) in enumerate(ranked, start=1):
        rank = total - rank_from_end + 1
        value = min(previous, p_value * total / rank)
        adjusted[index] = min(value, 1.0)
        previous = value
    return adjusted


def ora(
    genes: list[str],
    collections: list[str],
    up_genes: list[str] | None = None,
    down_genes: list[str] | None = None,
    background_genes: list[str] | None = None,
    min_overlap: int = 2,
    top_n: int = 10,
    fdr_threshold: float | None = None,
) -> dict:
    """Over-Representation Analysis (ORA) against local MSigDB gene sets.

    Parameters
    ----------
    genes
        List of gene symbols to test for enrichment.
    collections
        MSigDB collection names, for example ``hallmark`` and ``kegg_pathways``.
    min_overlap
        Minimum number of overlapping genes per term.
    top_n
        Maximum number of enriched terms to return.
    """
    query_genes = _clean_genes(genes)
    up_query = _clean_optional_genes(up_genes)
    down_query = _clean_optional_genes(down_genes)
    selected_collections = _clean_collections(collections)

    msigdb = _load_msigdb()
    net = _get_gene_sets(selected_collections, msigdb)
    if net.empty:
        available = sorted(msigdb["collection"].unique())
        raise ValueError(
            f"No gene sets found for collections {selected_collections}. "
            f"Available collections: {available}"
        )

    available_background = set(net["gene"].unique())
    custom_background = set(_clean_optional_genes(background_genes))
    background = (custom_background & available_background) if custom_background else available_background
    if not background:
        raise ValueError("No background genes overlap the selected gene-set collections")

    rows = []
    query_sets = []
    if up_query or down_query:
        if up_query:
            query_sets.append(("up", up_query))
        if down_query:
            query_sets.append(("down", down_query))
    else:
        query_sets.append(("query", query_genes))

    for direction, query_set in query_sets:
        rows.extend(_ora_rows_for_query(net, set(query_set), background, min_overlap, direction))

    adjusted = _benjamini_hochberg([row["p_value"] for row in rows])
    for row, adjusted_p_value in zip(rows, adjusted):
        row["adjusted_p_value"] = adjusted_p_value
    if fdr_threshold is not None:
        rows = [row for row in rows if row["adjusted_p_value"] <= fdr_threshold]
    rows.sort(key=lambda r: r["p_value"])
    records = rows[:top_n]
    plot_url = None
    if records:
        plot_path = ora_plot(records, top_n=top_n)
        plot_url = results.plot_url(plot_path)

    return {
        "summary": {
            "collections": selected_collections,
            "query_size": len(query_genes),
            "up_query_size": len(up_query),
            "down_query_size": len(down_query),
            "background_size": len(background),
            "terms_tested": len(rows),
            "fdr_threshold": fdr_threshold if fdr_threshold is not None else "none",
        },
        "plot_url": plot_url,
        "records": records,
    }


def _ora_rows_for_query(
    net: pd.DataFrame,
    query: set[str],
    background: set[str],
    min_overlap: int,
    direction: str,
) -> list[dict[str, Any]]:
    query_in_background = query & background
    if not query_in_background:
        return []

    rows = []
    background_size = len(background)
    query_size = len(query_in_background)
    grouped = net.groupby(["collection", "term"], sort=False)["gene"]

    for (term_collection, term), values in grouped:
        term_genes = set(values) & background
        overlap_genes = sorted(query_in_background & term_genes)
        overlap = len(overlap_genes)
        if overlap < min_overlap:
            continue

        term_size = len(term_genes)
        if term_size == 0:
            continue
        p_value = float(hypergeom.sf(overlap - 1, background_size, term_size, query_size))
        table = [
            [overlap, query_size - overlap],
            [term_size - overlap, background_size - term_size - query_size + overlap],
        ]
        odds_ratio = float(fisher_exact(table, alternative="greater").statistic)
        rows.append(
            {
                "direction": direction,
                "term": term,
                "collection": term_collection,
                "overlap": overlap,
                "term_size": term_size,
                "query_size": query_size,
                "background_size": background_size,
                "p_value": p_value,
                "odds_ratio": odds_ratio,
                "overlap_genes": ",".join(overlap_genes),
            }
        )
    return rows


def gsea(
    rankings: list[dict[str, Any]],
    collections: list[str],
    min_overlap: int = 5,
    top_n: int = 10,
    fdr_threshold: float | None = None,
) -> dict:
    """Gene Set Enrichment Analysis against local MSigDB gene sets."""
    os.environ.setdefault("MPLCONFIGDIR", "/tmp/matplotlib")
    os.environ.setdefault("XDG_CACHE_HOME", "/tmp")

    import decoupler as dc

    selected_collections = _clean_collections(collections)
    ranking = _ranking_frame(rankings)
    msigdb = _load_msigdb()
    net = _get_gene_sets(selected_collections, msigdb)
    net = net.loc[net["gene"].isin(ranking.columns), ["term", "gene"]].rename(
        columns={"term": "source", "gene": "target"}
    )
    net = net.drop_duplicates()
    if net.empty:
        raise ValueError("No ranked genes overlap the selected gene-set collections")

    scores_df, pvals_df = dc.mt.gsea(ranking, net, tmin=min_overlap, verbose=False)
    rows = []
    for term in scores_df.columns:
        p_value = float(pvals_df.loc[:, term].iloc[0]) if term in pvals_df.columns else 1.0
        term_genes = set(net.loc[net["source"] == term, "target"])
        leading_genes = sorted(term_genes & set(ranking.columns), key=lambda gene: abs(float(ranking.loc["ranking", gene])), reverse=True)
        rows.append(
            {
                "term": term,
                "score": float(scores_df.loc[:, term].iloc[0]),
                "p_value": p_value,
                "term_size": len(term_genes),
                "overlap": len(leading_genes),
                "leading_genes": ",".join(leading_genes[:30]),
            }
        )

    adjusted = _benjamini_hochberg([row["p_value"] for row in rows])
    for row, adjusted_p_value in zip(rows, adjusted):
        row["adjusted_p_value"] = adjusted_p_value
    if fdr_threshold is not None:
        rows = [row for row in rows if row["adjusted_p_value"] <= fdr_threshold]

    rows.sort(key=lambda row: (row["adjusted_p_value"], row["p_value"], -abs(row["score"])))
    records = rows[:top_n]
    plot_url = None
    if records:
        plot_path = gsea_plot(records, top_n=top_n)
        plot_url = results.plot_url(plot_path)

    return {
        "summary": {
            "collections": selected_collections,
            "ranked_genes": len(ranking.columns),
            "terms_tested": len(rows),
            "min_overlap": min_overlap,
            "fdr_threshold": fdr_threshold if fdr_threshold is not None else "none",
        },
        "plot_url": plot_url,
        "records": records,
    }


def _ranking_frame(rankings: list[dict[str, Any]]) -> pd.DataFrame:
    values: dict[str, float] = {}
    for item in rankings:
        gene = str(item.get("gene", "")).strip().upper()
        if not gene:
            continue
        score = float(item["score"])
        if np.isfinite(score):
            values[gene] = score
    if len(values) < 2:
        raise ValueError("GSEA requires at least two ranked genes with numeric scores")
    ordered = sorted(values.items(), key=lambda item: item[1], reverse=True)
    return pd.DataFrame([[score for _, score in ordered]], index=["ranking"], columns=[gene for gene, _ in ordered])


def ora_plot(records: list[dict], output_stem: str = "ora", top_n: int = 10) -> Path:
    """Generate an ORA barplot of enrichment results."""
    os.environ.setdefault("MPLCONFIGDIR", "/tmp/matplotlib")
    os.environ.setdefault("XDG_CACHE_HOME", "/tmp")

    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    from bioweb_analysis.plotting import np_log10

    results.clear_module()
    output = results.next_png(output_stem)

    frame = pd.DataFrame.from_records(records).head(top_n)
    if frame.empty:
        raise ValueError("No enrichment records to plot")

    frame = frame.sort_values("p_value", ascending=True)
    scores = -frame["p_value"].clip(lower=1e-300).apply(np_log10)
    max_score = max(float(scores.max()), 1.0)
    labels = [_wrap_term_label(term, max_chars=42) for term in frame["term"]]
    max_label_len = max(len(line) for label in labels for line in label.splitlines())
    max_label_lines = max(label.count("\n") + 1 for label in labels)

    width = min(max(8.0, 5.5 + max_label_len * 0.11), 15.0)
    row_height = max(0.7, 0.34 * max_label_lines)
    height = max(3.2, 1.2 + row_height * len(frame))

    fig, ax = plt.subplots(figsize=(width, height))
    y_positions = range(len(frame))
    ax.barh(y_positions, scores, color="#ADD8E6", edgecolor="none")
    ax.set_yticks([])
    ax.set_xlabel("-log10(p value)")
    ax.set_xlim(0, max_score * 1.12)
    ax.invert_yaxis()
    ax.spines[["top", "right", "left"]].set_visible(False)
    ax.tick_params(axis="y", length=0)

    label_x = max_score * 0.025
    for y_position, label in zip(y_positions, labels):
        ax.text(
            label_x,
            y_position,
            label,
            va="center",
            ha="left",
            color="#000000",
            fontsize=11,
            linespacing=1.1,
        )

    fig.tight_layout()
    fig.savefig(output, dpi=160)
    plt.close(fig)

    return output


def gsea_plot(records: list[dict], output_stem: str = "gsea", top_n: int = 10) -> Path:
    """Generate a signed GSEA score barplot."""
    os.environ.setdefault("MPLCONFIGDIR", "/tmp/matplotlib")
    os.environ.setdefault("XDG_CACHE_HOME", "/tmp")

    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    results.clear_module()
    output = results.next_png(output_stem)

    frame = pd.DataFrame.from_records(records).head(top_n)
    if frame.empty:
        raise ValueError("No GSEA records to plot")

    frame = frame.sort_values("score", ascending=True)
    labels = [_wrap_term_label(term, max_chars=42) for term in frame["term"]]
    max_label_len = max(len(line) for label in labels for line in label.splitlines())
    max_label_lines = max(label.count("\n") + 1 for label in labels)
    width = min(max(9.0, 6.0 + max_label_len * 0.1), 15.0)
    row_height = max(0.7, 0.34 * max_label_lines)
    height = max(3.2, 1.2 + row_height * len(frame))

    fig, ax = plt.subplots(figsize=(width, height))
    y_positions = range(len(frame))
    colors = ["#ADD8E6" if score < 0 else "#F4A3A3" for score in frame["score"]]
    ax.barh(y_positions, frame["score"], color=colors, edgecolor="none", alpha=0.9)
    ax.set_yticks([])
    ax.set_xlabel("GSEA score")
    ax.axvline(0, color="#111827", linewidth=0.8)
    ax.spines[["top", "right", "left"]].set_visible(False)
    ax.tick_params(axis="y", length=0)

    x_min, x_max = ax.get_xlim()
    offset = (x_max - x_min) * 0.02
    for y_position, label, score in zip(y_positions, labels, frame["score"]):
        if score >= 0:
            ax.text(offset, y_position, label, va="center", ha="left", color="#000000", fontsize=11, linespacing=1.1)
        else:
            ax.text(-offset, y_position, label, va="center", ha="right", color="#000000", fontsize=11, linespacing=1.1)

    fig.tight_layout()
    fig.savefig(output, dpi=160)
    plt.close(fig)
    return output


def _wrap_term_label(term: str, max_chars: int) -> str:
    label = str(term).replace("_", " ")
    return "\n".join(textwrap.wrap(label, width=max_chars, break_long_words=False)) or label
