from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd


def enrichment_barplot(records: list[dict], output_path: str | Path, top_n: int = 20) -> Path:
    output = Path(output_path)
    output.parent.mkdir(parents=True, exist_ok=True)
    frame = pd.DataFrame.from_records(records).head(top_n)
    if frame.empty:
        raise ValueError("No enrichment records to plot")
    frame = frame.sort_values("p_value", ascending=True)
    fig, ax = plt.subplots(figsize=(8, max(3, 0.35 * len(frame))))
    ax.barh(frame["term"], -frame["p_value"].clip(lower=1e-300).apply(np_log10))
    ax.set_xlabel("-log10(p value)")
    ax.invert_yaxis()
    fig.tight_layout()
    fig.savefig(output, dpi=160)
    plt.close(fig)
    return output


def np_log10(value: float) -> float:
    import numpy as np

    return float(np.log10(value))

