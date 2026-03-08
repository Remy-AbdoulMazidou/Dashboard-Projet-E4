import numpy as np
import pandas as pd


def pearson_matrix(df: pd.DataFrame) -> pd.DataFrame:
    numeric = df.select_dtypes(include="number")
    return numeric.corr(method="pearson")


def top_correlations(corr_matrix: pd.DataFrame, n: int = 15) -> pd.DataFrame:
    upper = corr_matrix.where(np.triu(np.ones(corr_matrix.shape), k=1).astype(bool))
    stacked = upper.stack().reset_index()
    stacked.columns = ["var_1", "var_2", "r"]
    stacked["abs_r"] = stacked["r"].abs()
    return stacked.sort_values("abs_r", ascending=False).head(n).reset_index(drop=True)


def linear_regression(x: pd.Series, y: pd.Series):
    mask = x.notna() & y.notna()
    x_clean = x[mask].to_numpy(dtype=float)
    y_clean = y[mask].to_numpy(dtype=float)
    if len(x_clean) < 3:
        return None
    coeffs = np.polyfit(x_clean, y_clean, 1)
    slope, intercept = float(coeffs[0]), float(coeffs[1])
    y_pred = slope * x_clean + intercept
    ss_res = float(np.sum((y_clean - y_pred) ** 2))
    ss_tot = float(np.sum((y_clean - y_clean.mean()) ** 2))
    r_squared = 1 - ss_res / ss_tot if ss_tot > 0 else 0.0
    return {
        "slope": slope,
        "intercept": intercept,
        "r_squared": r_squared,
        "x_line": [float(x_clean.min()), float(x_clean.max())],
        "y_line": [slope * float(x_clean.min()) + intercept, slope * float(x_clean.max()) + intercept],
    }


def summary_stats(series: pd.Series) -> dict:
    return {
        "mean": series.mean(),
        "median": series.median(),
        "std": series.std(),
        "min": series.min(),
        "max": series.max(),
        "q25": series.quantile(0.25),
        "q75": series.quantile(0.75),
        "count": series.count(),
    }


def format_large_number(value: float) -> str:
    if value >= 1_000_000:
        return f"{value / 1_000_000:.1f}M"
    if value >= 1_000:
        return f"{value / 1_000:.1f}k"
    return f"{value:.0f}"
