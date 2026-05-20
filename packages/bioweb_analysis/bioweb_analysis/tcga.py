from functools import lru_cache
import os
from pathlib import Path

os.environ.setdefault("MPLCONFIGDIR", "/tmp/bioweb-matplotlib")
Path(os.environ["MPLCONFIGDIR"]).mkdir(parents=True, exist_ok=True)

import matplotlib  # noqa: E402
import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402
from lifelines import KaplanMeierFitter  # noqa: E402
from lifelines.statistics import logrank_test  # noqa: E402
from scipy import stats  # noqa: E402

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402

from bioweb_analysis.results import ResultsManager  # noqa: E402

PANCAN_DIR = Path("data/tcga/pancanatlas")
EXPRESSION_PATH = PANCAN_DIR / "raw/EBPlusPlusAdjustPANCAN_IlluminaHiSeq_RNASeqV2.geneExp.tsv"
CDR_PATH = PANCAN_DIR / "raw/TCGA-CDR-SupplementalTableS1.xlsx"
EXPRESSION_PARQUET_PATH = PANCAN_DIR / "processed/pancanatlas_rnaseq_gene_expression_wide.parquet"
CDR_PARQUET_PATH = PANCAN_DIR / "processed/tcga_cdr_survival.parquet"

results = ResultsManager("tcga")

# TCGA barcode sample type codes
# https://gdc.cancer.gov/resources-tcga-users/tcga-code-books/tcga-barcode
# Tumor: 01-09, Normal: 10-19
_TUMOR_CODES = {"01", "02", "03", "04", "05", "06", "07", "08", "09"}
_NORMAL_CODES = {"10", "11", "12", "13", "14", "15", "16", "17", "18", "19"}

_SAMPLE_TYPE_LABELS = {
    "01": "Primary Solid Tumor",
    "02": "Recurrent Solid Tumor",
    "03": "Primary Blood Derived Cancer - Peripheral Blood",
    "04": "Recurrent Blood Derived Cancer - Bone Marrow",
    "05": "Additional - New Primary",
    "06": "Metastatic",
    "07": "Additional Metastatic",
    "08": "Human Tumor Original Cells",
    "09": "Primary Blood Derived Cancer - Bone Marrow",
    "10": "Blood Derived Normal",
    "11": "Solid Tissue Normal",
    "12": "Buccal Cell Normal",
    "13": "EBV Immortalized Normal",
    "14": "Bone Marrow Normal",
    "15": "Sample Type 15",
    "16": "Sample Type 16",
    "17": "Sample Type 17",
    "18": "Sample Type 18",
    "19": "Sample Type 19",
}


def _mock_expression(genes: list[str], sample_count: int = 120) -> dict[str, np.ndarray]:
    seed = abs(hash(tuple(sorted(genes)))) % (2**32)
    rng = np.random.default_rng(seed)
    return {gene: rng.normal(loc=8.0, scale=2.0, size=sample_count) for gene in genes}


def _signature(genes: list[str], sample_count: int = 120) -> np.ndarray:
    expression = _mock_expression(genes, sample_count)
    return np.vstack([expression[gene] for gene in genes]).mean(axis=0)


def _normalize_gene_id(value: str) -> str:
    return value.strip().strip('"').split("|", maxsplit=1)[0].upper()


def _normalize_sample_id(value: str) -> str:
    return value.strip().strip('"')


def _patient_id(sample_id: str) -> str:
    return sample_id[:12]


def _sample_type_code(sample_id: str) -> str:
    parts = sample_id.split("-")
    if len(parts) < 4:
        return ""
    return parts[3][:2]


def _is_tumor(code: str) -> bool:
    return code in _TUMOR_CODES


def _is_normal(code: str) -> bool:
    return code in _NORMAL_CODES


@lru_cache(maxsize=1)
def _clinical_cdr() -> pd.DataFrame:
    if CDR_PARQUET_PATH.exists():
        return pd.read_parquet(CDR_PARQUET_PATH)
    if not CDR_PATH.exists():
        raise FileNotFoundError(f"Missing TCGA-CDR file: {CDR_PATH}")
    frame = pd.read_excel(CDR_PATH, sheet_name="TCGA-CDR")
    frame["bcr_patient_barcode"] = frame["bcr_patient_barcode"].astype(str)
    frame["project"] = "TCGA-" + frame["type"].astype(str)
    return frame


@lru_cache(maxsize=64)
def _expression_for_genes(genes_key: tuple[str, ...]) -> pd.DataFrame:
    wanted = {gene.upper() for gene in genes_key}
    if EXPRESSION_PARQUET_PATH.exists():
        frame = pd.read_parquet(EXPRESSION_PARQUET_PATH)
        rows = frame.loc[frame["gene_symbol"].isin(wanted)].drop_duplicates("gene_symbol")
        missing = sorted(wanted - set(rows["gene_symbol"]))
        if missing:
            raise ValueError(f"Genes not found in PanCanAtlas expression matrix: {', '.join(missing)}")
        expression = rows.drop(columns=["gene_id"]).set_index("gene_symbol").T
        expression.index.name = None
        return expression.astype(float)

    if not EXPRESSION_PATH.exists():
        raise FileNotFoundError(f"Missing PanCanAtlas expression matrix: {EXPRESSION_PATH}")
    found: dict[str, np.ndarray] = {}
    sample_ids: list[str] | None = None
    with EXPRESSION_PATH.open() as handle:
        header = handle.readline().rstrip("\n").split("\t")
        sample_ids = [_normalize_sample_id(value) for value in header[1:]]
        for line in handle:
            fields = line.rstrip("\n").split("\t")
            if not fields:
                continue
            gene = _normalize_gene_id(fields[0])
            if gene in wanted and gene not in found:
                found[gene] = np.asarray(fields[1:], dtype=float)
                if len(found) == len(wanted):
                    break
    missing = sorted(wanted - set(found))
    if missing:
        raise ValueError(f"Genes not found in PanCanAtlas expression matrix: {', '.join(missing)}")
    return pd.DataFrame(found, index=sample_ids)


def _best_threshold(values: pd.Series, time: pd.Series, event: pd.Series) -> tuple[float, float]:
    best_threshold = float(values.median())
    best_p_value = 1.0
    for percentile in range(20, 81, 5):
        threshold = float(np.percentile(values, percentile))
        high = values >= threshold
        low = ~high
        if high.sum() < 10 or low.sum() < 10:
            continue
        result = logrank_test(time[high], time[low], event_observed_A=event[high], event_observed_B=event[low])
        if float(result.p_value) < best_p_value:
            best_p_value = float(result.p_value)
            best_threshold = threshold
    return best_threshold, best_p_value


def _km_plot(
    frame: pd.DataFrame,
    *,
    project: str,
    genes: list[str],
    survival_metric: str,
    axis_unit: str,
    p_value: float,
) -> Path:
    results.clear_module()
    output = results.next_png(f"survival_{project}_{'_'.join(genes)}")
    kmf = KaplanMeierFitter()
    fig, ax = plt.subplots(figsize=(6.2, 4.8))
    for group, color in [("high", "#dc2626"), ("low", "#2563eb")]:
        subset = frame[frame["group"] == group]
        kmf.fit(subset["time"], event_observed=subset["event"], label=f"{group.title()} (n={len(subset)})")
        kmf.plot_survival_function(ax=ax, ci_show=False, color=color)
    title_parts = [project]
    if len(genes) == 1:
        title_parts.append(genes[0])
    title_parts.append(survival_metric)
    ax.set_title(" ".join(title_parts))
    ax.set_xlabel("Time (months)" if axis_unit == "months" else "Time (days)")
    ax.set_ylabel("Survival probability")
    ax.legend(frameon=False)
    ax.text(0.02, 0.05, f"p = {p_value:.3g}", ha="left", va="bottom", transform=ax.transAxes)
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    fig.tight_layout()
    fig.savefig(output, dpi=180)
    plt.close(fig)
    return output


def _project_expression_frame(project: str, genes: list[str]) -> pd.DataFrame:
    clinical = _clinical_cdr().loc[:, ["bcr_patient_barcode", "project"]].copy()
    clinical = clinical.loc[clinical["project"] == project]
    expression = _expression_for_genes(tuple(sorted(genes))).copy()
    expression["patient"] = [_patient_id(sample) for sample in expression.index]
    expression["sample_type_code"] = [_sample_type_code(sample) for sample in expression.index]
    frame = expression.merge(clinical, left_on="patient", right_on="bcr_patient_barcode", how="inner")
    return frame


def _boxplot(frame: pd.DataFrame, *, project: str, gene: str, p_value: float, show_points: bool = True) -> Path:
    results.clear_module()
    output = results.next_png(f"tumor_normal_{project}_{gene}")
    tumor = frame.loc[frame["group"] == "Tumor", "expression"]
    normal = frame.loc[frame["group"] == "Normal", "expression"]
    fig, ax = plt.subplots(figsize=(4, 4))
    box = ax.boxplot(
        [tumor, normal],
        tick_labels=["Tumor", "Normal"],
        patch_artist=True,
        widths=0.55,
        showfliers=False,
        boxprops={"edgecolor": "#111827", "linewidth": 1.4},
        medianprops={"color": "#111827", "linewidth": 1.5},
        whiskerprops={"color": "#111827", "linewidth": 1.2},
        capprops={"color": "#111827", "linewidth": 1.2},
    )
    fill_colors = ["#fb7185", "#60a5fa"]
    for patch, color in zip(box["boxes"], fill_colors):
        patch.set_facecolor(color)
        patch.set_alpha(0.42)
    if show_points:
        point_colors = ["#e11d48", "#2563eb"]
        rng = np.random.default_rng(0)
        for index, (values, color) in enumerate([(tumor, point_colors[0]), (normal, point_colors[1])], start=1):
            jitter = rng.normal(index, 0.035, size=len(values))
            ax.scatter(jitter, values, s=12, alpha=0.42, color=color, linewidths=0)
    ax.set_title(f"{project} {gene}")
    ax.set_ylabel("Expression")
    ax.text(0.5, 0.96, f"p = {p_value:.3g}", ha="center", va="top", transform=ax.transAxes)
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    fig.tight_layout()
    fig.savefig(output, dpi=180)
    plt.close(fig)
    return output


def _expression_distribution_plot(
    frame: pd.DataFrame,
    *,
    label: str,
    categories: list[str],
    output_stem: str,
    title: str,
    ylabel: str,
    show_points: bool = True,
) -> Path:
    results.clear_module()
    output = results.next_png(output_stem)

    values = [frame.loc[frame[label] == category, "expression"].astype(float) for category in categories]
    width = max(7.0, min(18.0, 0.42 * len(categories) + 4.8))
    fig, ax = plt.subplots(figsize=(width, 4.8))
    box = ax.boxplot(
        values,
        tick_labels=categories,
        patch_artist=True,
        widths=0.55,
        showfliers=False,
        boxprops={"edgecolor": "#111827", "linewidth": 1.2},
        medianprops={"color": "#111827", "linewidth": 1.4},
        whiskerprops={"color": "#111827", "linewidth": 1.1},
        capprops={"color": "#111827", "linewidth": 1.1},
    )
    for patch in box["boxes"]:
        patch.set_facecolor("#ADD8E6")
        patch.set_alpha(0.75)
    if show_points:
        rng = np.random.default_rng(0)
        for index, series in enumerate(values, start=1):
            jitter = rng.normal(index, 0.035, size=len(series))
            ax.scatter(jitter, series, s=11, alpha=0.35, color="#2980b9", linewidths=0)

    ax.set_title(title)
    ax.set_ylabel(ylabel)
    ax.tick_params(axis="x", rotation=55 if len(categories) > 5 else 30)
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    fig.tight_layout()
    fig.savefig(output, dpi=180)
    plt.close(fig)
    return output


def survival_analysis(
    project: str,
    genes: list[str],
    grouping_method: str = "median",
    low_percentile: float | None = None,
    high_percentile: float | None = None,
    survival_metric: str = "OS",
    axis_unit: str = "days",
) -> dict:
    genes = [gene.upper() for gene in genes]
    survival_metric = survival_metric.upper()
    time_column = f"{survival_metric}.time"
    clinical = _clinical_cdr()
    if survival_metric not in clinical.columns or time_column not in clinical.columns:
        raise ValueError(f"Unsupported survival metric '{survival_metric}'")

    clinical = clinical.loc[clinical["project"] == project].copy()
    clinical["event"] = pd.to_numeric(clinical[survival_metric], errors="coerce")
    clinical["time"] = pd.to_numeric(clinical[time_column], errors="coerce")
    clinical = clinical.dropna(subset=["event", "time"])
    if axis_unit == "months":
        clinical["time"] = clinical["time"] / 30.4375

    expression = _expression_for_genes(tuple(sorted(genes)))
    expression = expression.loc[[_is_tumor(_sample_type_code(sample)) for sample in expression.index]].copy()
    expression["patient"] = [_patient_id(sample) for sample in expression.index]
    expression["signature"] = expression[genes].mean(axis=1)
    signature = expression.groupby("patient", as_index=False)["signature"].mean()

    frame = clinical.merge(signature, left_on="bcr_patient_barcode", right_on="patient", how="inner")
    if len(frame) < 20:
        raise ValueError(f"Not enough matched samples for {project}, {survival_metric}, and {', '.join(genes)}")

    values = frame["signature"]
    threshold = float(values.median())
    if grouping_method == "percentile":
        percentile = high_percentile if high_percentile is not None else 50
        threshold = float(np.percentile(values, percentile))
    if grouping_method == "optimal":
        threshold, _ = _best_threshold(values, frame["time"], frame["event"])

    frame["group"] = np.where(values >= threshold, "high", "low")
    high = frame["group"] == "high"
    low = frame["group"] == "low"
    if high.sum() < 2 or low.sum() < 2:
        raise ValueError("Grouping threshold produced a group with fewer than 2 samples")

    logrank = logrank_test(
        frame.loc[high, "time"],
        frame.loc[low, "time"],
        event_observed_A=frame.loc[high, "event"],
        event_observed_B=frame.loc[low, "event"],
    )
    p_value = float(logrank.p_value)
    plot_path = _km_plot(
        frame,
        project=project,
        genes=genes,
        survival_metric=survival_metric,
        axis_unit=axis_unit,
        p_value=p_value,
    )
    plot_url = results.plot_url(plot_path)
    return {
        "summary": {
            "project": project,
            "genes": genes,
            "survival_metric": survival_metric,
            "axis_unit": axis_unit,
            "grouping_method": grouping_method,
            "threshold": threshold,
            "high_n": int(high.sum()),
            "low_n": int(low.sum()),
            "p_value": p_value,
            "plot_url": plot_url,
        },
        "plot_url": plot_url,
        "records": [
            {
                "group": "high",
                "n": int(high.sum()),
                "events": int(frame.loc[high, "event"].sum()),
                "median_signature": float(np.median(values[high])),
            },
            {
                "group": "low",
                "n": int(low.sum()),
                "events": int(frame.loc[low, "event"].sum()),
                "median_signature": float(np.median(values[low])),
            },
        ],
    }


def correlation_analysis(project: str, genes: list[str], target_genes: list[str], method: str = "pearson") -> dict:
    """Correlation between two gene signatures.

    Each list is averaged into a single signature (mean expression across
    genes).  When a list contains only one gene, that gene's expression is
    used directly.
    """
    x_genes = [gene.upper() for gene in genes]
    y_genes = [gene.upper() for gene in target_genes]
    all_genes = list(set(x_genes + y_genes))
    frame = _project_expression_frame(project, all_genes)
    # Use only tumor samples (sample type codes 01-09)
    frame = frame.loc[frame["sample_type_code"].isin(_TUMOR_CODES)].copy()
    if len(frame) < 5:
        raise ValueError(
            f"Not enough tumor samples for {project} to run correlation "
            f"(found {len(frame)} samples)."
        )

    # Compute each signature as mean across genes, then aggregate by patient
    frame["x_sig"] = frame[x_genes].mean(axis=1)
    frame["y_sig"] = frame[y_genes].mean(axis=1)
    patient = frame.groupby("patient", as_index=False)[["x_sig", "y_sig"]].mean()

    if len(patient) < 5:
        raise ValueError(f"Not enough matched samples for {project}")

    x = patient["x_sig"].astype(float)
    y = patient["y_sig"].astype(float)
    if method == "spearman":
        coefficient, p_value = stats.spearmanr(x, y)
    else:
        coefficient, p_value = stats.pearsonr(x, y)

    plot_path = _correlation_scatter(
        x=x,
        y=y,
        project=project,
        x_genes=x_genes,
        y_genes=y_genes,
        method=method,
        r=float(coefficient),
        p_value=float(p_value),
    )
    plot_url = results.plot_url(plot_path)

    return {
        "summary": {
            "project": project,
            "x_genes": x_genes,
            "y_genes": y_genes,
            "method": method,
            "r": float(coefficient),
            "p_value": float(p_value),
            "n_samples": int(len(patient)),
            "plot_url": plot_url,
        },
        "plot_url": plot_url,
        "records": [
            {
                "project": project,
                "x_genes": ",".join(x_genes),
                "y_genes": ",".join(y_genes),
                "method": method,
                "r": float(coefficient),
                "p_value": float(p_value),
                "n_samples": int(len(patient)),
            }
        ],
    }


def _axis_label(genes: list[str]) -> str:
    if len(genes) == 1:
        return f"{genes[0]} expression"
    return f"Mean expression of signature (nGenes={len(genes)})"


def _correlation_scatter(
    *,
    x: pd.Series,
    y: pd.Series,
    project: str,
    x_genes: list[str],
    y_genes: list[str],
    method: str,
    r: float,
    p_value: float,
) -> Path:
    results.clear_module()
    x_label = _axis_label(x_genes)
    y_label = _axis_label(y_genes)
    x_tag = ",".join(x_genes) if len(x_genes) <= 3 else f"{x_genes[0]}+{len(x_genes)-1}"
    y_tag = ",".join(y_genes) if len(y_genes) <= 3 else f"{y_genes[0]}+{len(y_genes)-1}"
    output = results.next_png(f"correlation_{project}_{x_tag}_vs_{y_tag}")

    fig, ax = plt.subplots(figsize=(5.5, 5.5))
    ax.scatter(x, y, s=18, alpha=0.55, color="#2563eb", linewidths=0, zorder=2)

    # Linear fit line
    slope, intercept = np.polyfit(x, y, 1)
    x_line = np.linspace(float(x.min()), float(x.max()), 100)
    ax.plot(x_line, slope * x_line + intercept, color="#dc2626", linewidth=1.8, zorder=3)

    ax.set_xlabel(x_label)
    ax.set_ylabel(y_label)
    ax.set_title(f"{project}  {method.capitalize()} correlation")
    ax.text(
        0.04, 0.96,
        f"r = {r:.3f}\np = {p_value:.3g}",
        ha="left", va="top",
        transform=ax.transAxes,
        fontsize=10,
        bbox=dict(boxstyle="round,pad=0.3", facecolor="white", alpha=0.85, edgecolor="#d9e2ec"),
    )
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    fig.tight_layout()
    fig.savefig(output, dpi=180)
    plt.close(fig)
    return output


def tumor_normal_compare(project: str, genes: list[str], show_points: bool = True) -> dict:
    if len(genes) != 1:
        raise ValueError("Tumor vs normal comparison currently supports exactly one gene")
    gene = genes[0].upper()
    frame = _project_expression_frame(project, [gene])
    frame = frame.loc[frame["sample_type_code"].isin(_TUMOR_CODES | _NORMAL_CODES)].copy()
    frame["group"] = np.where(frame["sample_type_code"].isin(_TUMOR_CODES), "Tumor", "Normal")
    frame["expression"] = pd.to_numeric(frame[gene], errors="coerce")
    frame = frame.dropna(subset=["expression"])
    tumor = frame.loc[frame["group"] == "Tumor", "expression"]
    normal = frame.loc[frame["group"] == "Normal", "expression"]
    if len(tumor) < 2:
        raise ValueError(
            f"Not enough tumor samples for {project} and {gene} "
            f"(found {len(tumor)} tumor, {len(normal)} normal). "
            f"This cancer project may not have normal tissue samples in TCGA."
        )
    if len(normal) < 2:
        raise ValueError(
            f"Not enough normal samples for {project} and {gene} "
            f"(found {len(tumor)} tumor, {len(normal)} normal). "
            f"This cancer project may not have normal tissue samples in TCGA."
        )
    statistic, p_value = stats.ttest_ind(tumor, normal, equal_var=False)
    plot_path = _boxplot(frame, project=project, gene=gene, p_value=float(p_value), show_points=show_points)
    plot_url = results.plot_url(plot_path)
    return {
        "summary": {
            "project": project,
            "gene": gene,
            "tumor_n": int(len(tumor)),
            "normal_n": int(len(normal)),
            "tumor_median": float(tumor.median()),
            "normal_median": float(normal.median()),
            "p_value": float(p_value),
            "plot_url": plot_url,
        },
        "plot_url": plot_url,
        "records": [
            {
                "group": "Tumor",
                "n": int(len(tumor)),
                "mean": float(tumor.mean()),
                "median": float(tumor.median()),
            },
            {
                "group": "Normal",
                "n": int(len(normal)),
                "mean": float(normal.mean()),
                "median": float(normal.median()),
            },
        ],
    }


def expression_visualization(
    project: str,
    genes: list[str],
    show_points: bool = True,
    sort_by: str = "alphabetical",
) -> dict:
    genes = [gene.upper() for gene in genes]
    clinical = _clinical_cdr().loc[:, ["bcr_patient_barcode", "project"]].copy()
    expression = _expression_for_genes(tuple(sorted(genes))).copy()
    expression = expression.loc[[_is_tumor(_sample_type_code(sample)) for sample in expression.index]].copy()
    expression["patient"] = [_patient_id(sample) for sample in expression.index]
    expression["sample_type_code"] = [_sample_type_code(sample) for sample in expression.index]
    frame = expression.merge(clinical, left_on="patient", right_on="bcr_patient_barcode", how="inner")
    if project != "ALL":
        frame = frame.loc[frame["project"] == project].copy()
    if frame.empty:
        raise ValueError(f"No tumor samples found for {project}")

    frame["expression"] = frame[genes].mean(axis=1)
    long = frame.loc[:, ["project", "patient", "expression"]].copy()
    long["expression"] = pd.to_numeric(long["expression"], errors="coerce")
    long = long.dropna(subset=["expression"])
    if long.empty:
        raise ValueError(f"No expression values found for {project} and {', '.join(genes)}")

    grouped = long.groupby("project", sort=False)["expression"]
    records = [
        {
            "project": cancer_project,
            "n_samples": int(group.shape[0]),
            "mean": float(group.mean()),
            "median": float(group.median()),
            "min": float(group.min()),
            "max": float(group.max()),
        }
        for cancer_project, group in grouped
    ]
    if sort_by == "expression_desc":
        records.sort(key=lambda record: record["median"], reverse=True)
    else:
        records.sort(key=lambda record: record["project"])

    projects = [record["project"] for record in records]
    tag = "_".join(genes[:3]) if len(genes) <= 3 else f"{genes[0]}_plus_{len(genes) - 1}"
    plot_path = _expression_distribution_plot(
        long,
        label="project",
        categories=projects,
        output_stem=f"expression_pan_cancer_{tag}",
        title=f"{' / '.join(genes)} tumor expression across TCGA projects",
        ylabel="Mean expression" if len(genes) > 1 else "Expression",
        show_points=show_points,
    )
    plot_url = results.plot_url(plot_path)

    return {
        "summary": {
            "project": project,
            "genes": genes,
            "n_genes": len(genes),
            "n_projects": len(projects),
            "n_samples": int(long.shape[0]),
            "sample_type": "tumor",
            "sort_by": sort_by,
            "plot_url": plot_url,
        },
        "plot_url": plot_url,
        "records": records,
    }
