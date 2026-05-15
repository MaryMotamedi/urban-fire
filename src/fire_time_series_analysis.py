from __future__ import annotations

import math
import re
import warnings
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, Iterable, List, Optional, Sequence, Tuple

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

warnings.filterwarnings("ignore", category=UserWarning)

try:
    from statsmodels.tsa.seasonal import STL
    from statsmodels.graphics.tsaplots import plot_acf
    HAS_STATSMODELS = True
except Exception:  # pragma: no cover
    HAS_STATSMODELS = False



INPUT_FILES: Dict[str, Path] = {
    "incident_level": Path("data/chicago_fires_full_acs_svi_nsi.csv"),
    "block_group_level": Path("data/chicago_fire_block_groups_full_acs_svi_nsi.csv"),
    "tract_level": Path("data/chicago_fires_tract_acs_svi_nsi.csv"),
}

OUTPUT_ROOT = Path("output/time_series")

TOP_N_CATEGORIES = 8
TOP_N_GEOS = 10


SAVE_INTERMEDIATE_CSV = False



DATE_PRIORITY_NAMES = [
    "incident_date",
    "incident_datetime",
    "fire_date",
    "alarm_ts",
    "alarm_time",
    "alarm_datetime",
    "dispatch_ts",
    "dispatch_datetime",
    "arrival_ts",
    "arrival_datetime",
    "created_date",
    "date",
]

YEAR_PRIORITY_NAMES = [
    "incident_year",
    "fire_year",
    "year",
    "yr",
]

MONTH_PRIORITY_NAMES = [
    "incident_month",
    "fire_month",
    "month",
    "mo",
]

DAY_PRIORITY_NAMES = [
    "incident_day",
    "fire_day",
    "day",
    "day_of_month",
]

HOUR_PRIORITY_NAMES = [
    "incident_hour",
    "fire_hour",
    "hour",
    "alarm_hour",
]

COUNT_PRIORITY_NAMES = [
    "incident_count",
    "fire_count",
    "n_incidents",
    "num_incidents",
    "total_incidents",
    "total_fires",
    "fires",
    "count",
    "cnt",
]

GEO_PRIORITY_NAMES = [
    "geo_id",
    "geoid",
    "geoid10",
    "geoid20",
    "block_group",
    "block_group_id",
    "census_block_group",
    "tract",
    "tract_id",
    "census_tract",
]

INCIDENT_TYPE_PRIORITY_NAMES = [
    "incident_type",
    "incident_type_description",
    "incident_type_code",
    "nfirs_incident_type",
]

PROPERTY_USE_PRIORITY_NAMES = [
    "property_use",
    "property_use_description",
    "property_use_code",
    "nfirs_property_use",
]

STATION_PRIORITY_NAMES = [
    "station",
    "station_id",
    "fire_station",
    "first_due_station",
    "responding_station",
]

LOSS_PRIORITY_NAMES = [
    "total_loss",
    "loss_total",
    "estimated_total_loss",
    "property_loss",
    "contents_loss",
    "estimated_property_loss",
    "estimated_contents_loss",
]

RESPONSE_TIME_PRIORITY_NAMES = [
    "response_time_min",
    "response_time_minutes",
    "response_minutes",
    "arrival_time_minutes",
    "dispatch_to_arrival_min",
    "alarm_to_arrival_min",
]


@dataclass
class TimeIndexInfo:
    date_col: Optional[str]
    date_source: str
    frequency_hint: Optional[str] = None


@dataclass
class DatasetContext:
    name: str
    path: Path
    output_dir: Path
    figures_dir: Path
    df: pd.DataFrame
    time_info: Optional[TimeIndexInfo]
    count_col: Optional[str]
    geo_col: Optional[str]
    incident_type_col: Optional[str]
    property_use_col: Optional[str]
    station_col: Optional[str]
    loss_col: Optional[str]
    response_time_col: Optional[str]


def normalize_name(name: str) -> str:
    """Normalize a column name for tolerant matching."""
    return re.sub(r"[^a-z0-9]+", "_", str(name).strip().lower()).strip("_")


def find_column(df: pd.DataFrame, candidates: Sequence[str]) -> Optional[str]:
    """Find a column by exact normalized match, then by substring match."""
    if df.empty:
        return None

    normalized_to_original = {normalize_name(c): c for c in df.columns}

    for candidate in candidates:
        key = normalize_name(candidate)
        if key in normalized_to_original:
            return normalized_to_original[key]

    # Conservative substring matching: candidate must appear as a token sequence.
    normalized_cols = [(normalize_name(c), c) for c in df.columns]
    for candidate in candidates:
        key = normalize_name(candidate)
        for norm_col, original in normalized_cols:
            if key and key in norm_col:
                return original
    return None


def parse_datetime_series(s: pd.Series) -> pd.Series:
    """Parse a datetime-like series robustly."""
    # First try the default parser.
    parsed = pd.to_datetime(s, errors="coerce")

    # If very poor parsing, try common numeric date formats.
    if parsed.notna().mean() < 0.5 and pd.api.types.is_numeric_dtype(s):
        for unit in ["s", "ms", "us", "ns"]:
            candidate = pd.to_datetime(s, errors="coerce", unit=unit)
            if candidate.notna().mean() > parsed.notna().mean():
                parsed = candidate
    return parsed


def infer_datetime_column(df: pd.DataFrame) -> Optional[TimeIndexInfo]:
    """Infer the best available date/time column or reconstruct one from parts."""
    if df.empty:
        return None

    # 1. Prioritized date columns
    for col in [find_column(df, DATE_PRIORITY_NAMES)]:
        if col is None:
            continue
        parsed = parse_datetime_series(df[col])
        if parsed.notna().mean() >= 0.7:
            return TimeIndexInfo(date_col=col, date_source="existing datetime column")

    # 2. Search columns with date/time/timestamp-like names, excluding metadata years
    date_like_cols = []
    for c in df.columns:
        norm = normalize_name(c)
        has_temporal_name = any(token in norm for token in ["date", "datetime", "timestamp", "time", "ts"])
        looks_metadata = any(token in norm for token in ["source_date", "census_year", "acs_year", "svi_year", "year_built"])
        if has_temporal_name and not looks_metadata:
            date_like_cols.append(c)

    best_col = None
    best_rate = 0.0
    for col in date_like_cols:
        parsed = parse_datetime_series(df[col])
        rate = parsed.notna().mean()
        if rate > best_rate:
            best_col = col
            best_rate = rate
    if best_col is not None and best_rate >= 0.7:
        return TimeIndexInfo(date_col=best_col, date_source="inferred datetime column")

    # 3. Reconstruct from year/month/day/hour parts.
    year_col = find_column(df, YEAR_PRIORITY_NAMES)
    month_col = find_column(df, MONTH_PRIORITY_NAMES)
    day_col = find_column(df, DAY_PRIORITY_NAMES)
    hour_col = find_column(df, HOUR_PRIORITY_NAMES)

    if year_col is not None:
        years = pd.to_numeric(df[year_col], errors="coerce")
        if years.between(1900, 2100).mean() >= 0.7:
            months = pd.to_numeric(df[month_col], errors="coerce") if month_col else 1
            days = pd.to_numeric(df[day_col], errors="coerce") if day_col else 1
            hours = pd.to_numeric(df[hour_col], errors="coerce") if hour_col else 0

            # Create a temporary reconstructed date column
            tmp = pd.DataFrame({
                "year": years,
                "month": months,
                "day": days,
                "hour": hours,
            })
            tmp["month"] = tmp["month"].fillna(1).clip(1, 12).astype(int)
            tmp["day"] = tmp["day"].fillna(1).clip(1, 28).astype(int)
            tmp["hour"] = tmp["hour"].fillna(0).clip(0, 23).astype(int)

            reconstructed = pd.to_datetime(tmp, errors="coerce")
            if reconstructed.notna().mean() >= 0.7:
                df["__analysis_date"] = reconstructed
                if month_col is None:
                    hint = "YS"
                elif day_col is None:
                    hint = "MS"
                else:
                    hint = None
                return TimeIndexInfo(
                    date_col="__analysis_date",
                    date_source="reconstructed from date-part columns",
                    frequency_hint=hint,
                )

    return None


def infer_count_column(df: pd.DataFrame, dataset_name: str) -> Optional[str]:
    """Infer a count column for aggregated files. Incident-level defaults to one row = one incident."""
    if dataset_name == "incident_level":
        return None

    col = find_column(df, COUNT_PRIORITY_NAMES)
    if col is not None and pd.api.types.is_numeric_dtype(pd.to_numeric(df[col], errors="coerce")):
        return col

    # Conservative fallback: search count-like numeric columns
    count_like = []
    for c in df.columns:
        norm = normalize_name(c)
        if any(token in norm for token in ["incident_count", "fire_count", "num_incident", "n_incident", "total_incident"]):
            values = pd.to_numeric(df[c], errors="coerce")
            if values.notna().mean() > 0.7:
                count_like.append(c)
    return count_like[0] if count_like else None


def infer_loss_column(df: pd.DataFrame) -> Optional[str]:
    """Infer or construct a total loss column."""
    direct = find_column(df, LOSS_PRIORITY_NAMES)
    if direct is not None:
        values = pd.to_numeric(df[direct], errors="coerce")
        if values.notna().mean() > 0.5:
            return direct

    property_col = find_column(df, ["property_loss", "estimated_property_loss"])
    contents_col = find_column(df, ["contents_loss", "estimated_contents_loss"])
    if property_col and contents_col:
        df["__total_loss"] = (
            pd.to_numeric(df[property_col], errors="coerce").fillna(0)
            + pd.to_numeric(df[contents_col], errors="coerce").fillna(0)
        )
        return "__total_loss"
    return None


def infer_response_time_column(df: pd.DataFrame) -> Optional[str]:
    direct = find_column(df, RESPONSE_TIME_PRIORITY_NAMES)
    if direct is not None:
        values = pd.to_numeric(df[direct], errors="coerce")
        if values.notna().mean() > 0.5:
            return direct
    return None



def build_event_frame(ctx: DatasetContext) -> Optional[pd.DataFrame]:
    """Return a compact frame with analysis_date and event_count."""
    if ctx.time_info is None or ctx.time_info.date_col is None:
        return None

    df = ctx.df.copy()
    date_col = ctx.time_info.date_col
    df["analysis_date"] = parse_datetime_series(df[date_col]) if date_col != "__analysis_date" else df[date_col]
    df = df[df["analysis_date"].notna()].copy()

    if df.empty:
        return None

    if ctx.count_col is not None:
        df["event_count"] = pd.to_numeric(df[ctx.count_col], errors="coerce").fillna(0)
    else:
        df["event_count"] = 1.0

    # Keep optional variables for richer temporal analysis
    keep_cols = ["analysis_date", "event_count"]
    for c in [ctx.geo_col, ctx.incident_type_col, ctx.property_use_col, ctx.station_col, ctx.loss_col, ctx.response_time_col]:
        if c is not None and c in df.columns and c not in keep_cols:
            keep_cols.append(c)
    return df[keep_cols].copy()


def build_wide_year_series(df: pd.DataFrame) -> Optional[pd.DataFrame]:
    """
    Fallback for geography-level files that store counts in wide year columns.

    This only accepts columns with count/fire/incident language near a 4-digit year,
    to avoid confusing ACS/SVI metadata years or building-year variables with counts.
    """
    year_col_map: Dict[int, str] = {}
    for c in df.columns:
        norm = normalize_name(c)
        if not any(token in norm for token in ["fire", "fires", "incident", "incidents", "count", "counts"]):
            continue
        years = re.findall(r"(?:19|20)\d{2}", norm)
        if not years:
            continue
        values = pd.to_numeric(df[c], errors="coerce")
        if values.notna().mean() < 0.6:
            continue
        # Use the last year in the name if multiple appear.
        year = int(years[-1])
        year_col_map[year] = c

    if not year_col_map:
        return None

    rows = []
    for year, col in sorted(year_col_map.items()):
        rows.append({
            "analysis_date": pd.Timestamp(year=year, month=1, day=1),
            "event_count": pd.to_numeric(df[col], errors="coerce").fillna(0).sum(),
            "source_column": col,
        })
    return pd.DataFrame(rows)


def aggregate_series(event_df: pd.DataFrame, freq: str) -> pd.Series:
    """Aggregate event_count by a pandas frequency string."""
    if event_df is None or event_df.empty:
        return pd.Series(dtype=float)

    s = (
        event_df.set_index("analysis_date")["event_count"]
        .sort_index()
        .resample(freq)
        .sum()
    )
    return s.astype(float)


def calculate_basic_ts_summary(daily: pd.Series, weekly: pd.Series, monthly: pd.Series, yearly: pd.Series) -> pd.DataFrame:
    """Compact summary statistics for core time series."""
    rows = []
    for name, s in [("Daily", daily), ("Weekly", weekly), ("Monthly", monthly), ("Yearly", yearly)]:
        if s.empty:
            continue
        nonzero = s[s > 0]
        mean_val = s.mean()
        var_val = s.var(ddof=1) if len(s) > 1 else np.nan
        rows.append({
            "series": name,
            "start": s.index.min().date(),
            "end": s.index.max().date(),
            "periods": len(s),
            "total_incidents": float(s.sum()),
            "mean": float(mean_val),
            "median": float(s.median()),
            "std": float(s.std(ddof=1)) if len(s) > 1 else np.nan,
            "min": float(s.min()),
            "max": float(s.max()),
            "zero_periods": int((s == 0).sum()),
            "zero_period_share": float((s == 0).mean()),
            "variance_to_mean": float(var_val / mean_val) if mean_val > 0 and not np.isnan(var_val) else np.nan,
            "top_period_share": float(s.max() / s.sum()) if s.sum() > 0 else np.nan,
            "nonzero_periods": int(len(nonzero)),
        })
    return pd.DataFrame(rows)


def top_periods(s: pd.Series, n: int = 10) -> pd.DataFrame:
    if s.empty:
        return pd.DataFrame()
    result = s.sort_values(ascending=False).head(n).reset_index()
    result.columns = ["period_start", "incident_count"]
    result["period_start"] = result["period_start"].astype(str)
    result["share_of_total"] = result["incident_count"] / result["incident_count"].sum() if result["incident_count"].sum() > 0 else np.nan
    return result


def monthly_seasonality(event_df: pd.DataFrame) -> pd.DataFrame:
    if event_df is None or event_df.empty:
        return pd.DataFrame()
    tmp = event_df.copy()
    tmp["month"] = tmp["analysis_date"].dt.month
    out = tmp.groupby("month", dropna=False)["event_count"].sum().reset_index()
    out["month_name"] = pd.to_datetime(out["month"], format="%m").dt.month_name()
    out["share_of_total"] = out["event_count"] / out["event_count"].sum() if out["event_count"].sum() > 0 else np.nan
    return out[["month", "month_name", "event_count", "share_of_total"]]


def weekday_pattern(event_df: pd.DataFrame) -> pd.DataFrame:
    if event_df is None or event_df.empty:
        return pd.DataFrame()
    tmp = event_df.copy()
    tmp["weekday"] = tmp["analysis_date"].dt.dayofweek
    tmp["weekday_name"] = tmp["analysis_date"].dt.day_name()
    out = tmp.groupby(["weekday", "weekday_name"], dropna=False)["event_count"].sum().reset_index()
    out["share_of_total"] = out["event_count"] / out["event_count"].sum() if out["event_count"].sum() > 0 else np.nan
    return out.sort_values("weekday")


def hourly_pattern(event_df: pd.DataFrame) -> pd.DataFrame:
    if event_df is None or event_df.empty:
        return pd.DataFrame()
    tmp = event_df.copy()
    tmp["hour"] = tmp["analysis_date"].dt.hour
    # If the date column has no useful time component, all hours may be zero.
    if tmp["hour"].nunique(dropna=True) <= 1:
        return pd.DataFrame()
    out = tmp.groupby("hour", dropna=False)["event_count"].sum().reset_index()
    out["share_of_total"] = out["event_count"] / out["event_count"].sum() if out["event_count"].sum() > 0 else np.nan
    return out


def detect_anomalous_days(daily: pd.Series, window: int = 30, z_threshold: float = 2.5) -> pd.DataFrame:
    """Simple rolling z-score anomaly screen for unusually high-count days."""
    if daily.empty or len(daily) < window + 5:
        return pd.DataFrame()
    rolling_mean = daily.rolling(window=window, min_periods=max(7, window // 3)).mean()
    rolling_std = daily.rolling(window=window, min_periods=max(7, window // 3)).std(ddof=1)
    z = (daily - rolling_mean) / rolling_std.replace(0, np.nan)
    out = pd.DataFrame({
        "date": daily.index,
        "incident_count": daily.values,
        "rolling_mean": rolling_mean.values,
        "rolling_std": rolling_std.values,
        "rolling_z_score": z.values,
    })
    out = out[out["rolling_z_score"] >= z_threshold].sort_values("rolling_z_score", ascending=False)
    out["date"] = out["date"].astype(str)
    return out.head(25)



def save_line_plot(s: pd.Series, title: str, y_label: str, path: Path, rolling_window: Optional[int] = None) -> None:
    if s.empty:
        return
    fig, ax = plt.subplots(figsize=(12, 5))
    ax.plot(s.index, s.values, linewidth=1.5, label="Observed")
    if rolling_window is not None and len(s) >= rolling_window:
        ax.plot(s.index, s.rolling(rolling_window, min_periods=max(2, rolling_window // 4)).mean(), linewidth=2.0, label=f"{rolling_window}-period rolling mean")
        ax.legend()
    ax.set_title(title)
    ax.set_xlabel("Date")
    ax.set_ylabel(y_label)
    fig.tight_layout()
    fig.savefig(path, dpi=200)
    plt.close(fig)


def save_bar_plot(df: pd.DataFrame, x: str, y: str, title: str, x_label: str, y_label: str, path: Path, rotate: bool = False) -> None:
    if df.empty:
        return
    fig, ax = plt.subplots(figsize=(10, 5))
    ax.bar(df[x].astype(str), df[y])
    ax.set_title(title)
    ax.set_xlabel(x_label)
    ax.set_ylabel(y_label)
    if rotate:
        ax.tick_params(axis="x", rotation=45)
    fig.tight_layout()
    fig.savefig(path, dpi=200)
    plt.close(fig)


def save_category_monthly_plot(event_df: pd.DataFrame, category_col: str, title: str, path: Path, top_n: int = TOP_N_CATEGORIES) -> pd.DataFrame:
    if event_df is None or event_df.empty or category_col not in event_df.columns:
        return pd.DataFrame()

    tmp = event_df.copy()
    tmp[category_col] = tmp[category_col].astype(str).replace({"nan": "Unknown"})
    top_categories = tmp.groupby(category_col)["event_count"].sum().sort_values(ascending=False).head(top_n).index
    tmp = tmp[tmp[category_col].isin(top_categories)].copy()
    tmp["month_start"] = tmp["analysis_date"].dt.to_period("M").dt.to_timestamp()
    pivot = tmp.pivot_table(index="month_start", columns=category_col, values="event_count", aggfunc="sum", fill_value=0)

    if pivot.empty:
        return pd.DataFrame()

    fig, ax = plt.subplots(figsize=(12, 6))
    for col in pivot.columns:
        ax.plot(pivot.index, pivot[col], linewidth=1.5, label=str(col)[:45])
    ax.set_title(title)
    ax.set_xlabel("Month")
    ax.set_ylabel("Incident count")
    ax.legend(fontsize=8, loc="best")
    fig.tight_layout()
    fig.savefig(path, dpi=200)
    plt.close(fig)

    return pivot.reset_index()


def save_geo_monthly_heatmap(event_df: pd.DataFrame, geo_col: str, path: Path, top_n: int = TOP_N_GEOS) -> pd.DataFrame:
    if event_df is None or event_df.empty or geo_col not in event_df.columns:
        return pd.DataFrame()

    tmp = event_df.copy()
    tmp[geo_col] = tmp[geo_col].astype(str)
    top_geos = tmp.groupby(geo_col)["event_count"].sum().sort_values(ascending=False).head(top_n).index
    tmp = tmp[tmp[geo_col].isin(top_geos)].copy()
    tmp["month_start"] = tmp["analysis_date"].dt.to_period("M").dt.to_timestamp()
    pivot = tmp.pivot_table(index=geo_col, columns="month_start", values="event_count", aggfunc="sum", fill_value=0)

    if pivot.empty or pivot.shape[1] < 2:
        return pd.DataFrame()

    fig, ax = plt.subplots(figsize=(14, max(4, 0.45 * len(pivot))))
    im = ax.imshow(pivot.values, aspect="auto")
    ax.set_title(f"Monthly incident counts for top {len(pivot)} geographies")
    ax.set_xlabel("Month")
    ax.set_ylabel(geo_col)
    ax.set_yticks(np.arange(len(pivot.index)))
    ax.set_yticklabels([str(x) for x in pivot.index], fontsize=8)

    # Reduce x labels for readability
    x_positions = np.linspace(0, len(pivot.columns) - 1, min(12, len(pivot.columns))).astype(int)
    ax.set_xticks(x_positions)
    ax.set_xticklabels([pd.Timestamp(pivot.columns[i]).strftime("%Y-%m") for i in x_positions], rotation=45, ha="right")
    fig.colorbar(im, ax=ax, label="Incident count")
    fig.tight_layout()
    fig.savefig(path, dpi=200)
    plt.close(fig)

    return pivot.reset_index()


def save_day_hour_heatmap(event_df: pd.DataFrame, path: Path) -> pd.DataFrame:
    if event_df is None or event_df.empty:
        return pd.DataFrame()
    tmp = event_df.copy()
    tmp["weekday"] = tmp["analysis_date"].dt.day_name()
    tmp["weekday_num"] = tmp["analysis_date"].dt.dayofweek
    tmp["hour"] = tmp["analysis_date"].dt.hour
    if tmp["hour"].nunique(dropna=True) <= 1:
        return pd.DataFrame()
    pivot = tmp.pivot_table(index=["weekday_num", "weekday"], columns="hour", values="event_count", aggfunc="sum", fill_value=0)
    pivot = pivot.reset_index().sort_values("weekday_num").set_index("weekday").drop(columns=["weekday_num"])

    fig, ax = plt.subplots(figsize=(12, 5))
    im = ax.imshow(pivot.values, aspect="auto")
    ax.set_title("Incident counts by day of week and hour")
    ax.set_xlabel("Hour of day")
    ax.set_ylabel("Day of week")
    ax.set_xticks(np.arange(len(pivot.columns)))
    ax.set_xticklabels([str(c) for c in pivot.columns])
    ax.set_yticks(np.arange(len(pivot.index)))
    ax.set_yticklabels(pivot.index)
    fig.colorbar(im, ax=ax, label="Incident count")
    fig.tight_layout()
    fig.savefig(path, dpi=200)
    plt.close(fig)
    return pivot.reset_index()


def save_stl_plot(s: pd.Series, title: str, path: Path, period: int) -> None:
    if not HAS_STATSMODELS or s.empty or len(s) < 2 * period:
        return
    # Fill missing values and avoid failures with all-zero or constant series.
    y = s.astype(float).asfreq(s.index.freq or pd.infer_freq(s.index))
    y = y.interpolate(limit_direction="both").fillna(0)
    if y.nunique() <= 1:
        return
    try:
        result = STL(y, period=period, robust=True).fit()
        fig = result.plot()
        fig.set_size_inches(12, 8)
        fig.suptitle(title, y=1.02)
        fig.tight_layout()
        fig.savefig(path, dpi=200, bbox_inches="tight")
        plt.close(fig)
    except Exception:
        return


def save_acf_plot(s: pd.Series, title: str, path: Path, lags: int = 52) -> None:
    if not HAS_STATSMODELS or s.empty or len(s) < 10 or s.nunique() <= 1:
        return
    try:
        fig, ax = plt.subplots(figsize=(10, 5))
        plot_acf(s.fillna(0), lags=min(lags, max(1, len(s) // 2 - 1)), ax=ax)
        ax.set_title(title)
        fig.tight_layout()
        fig.savefig(path, dpi=200)
        plt.close(fig)
    except Exception:
        return



def write_excel_tables(path: Path, tables: Dict[str, pd.DataFrame]) -> None:
    """Write compact analysis tables to one Excel workbook."""
    path.parent.mkdir(parents=True, exist_ok=True)
    with pd.ExcelWriter(path, engine="openpyxl") as writer:
        for name, table in tables.items():
            if table is None or table.empty:
                continue
            safe_name = re.sub(r"[^A-Za-z0-9_]+", "_", name)[:31]
            table.to_excel(writer, sheet_name=safe_name, index=False)


def markdown_table(df: pd.DataFrame, max_rows: int = 10) -> str:
    if df is None or df.empty:
        return "_No table available._\n"

    display = df.head(max_rows).copy()

    def fmt(value: object) -> str:
        if pd.isna(value):
            return ""
        if isinstance(value, float):
            return f"{value:.6g}"
        return str(value).replace("|", "\\|").replace("\n", " ")

    headers = [fmt(col) for col in display.columns]
    rows = [[fmt(value) for value in row] for row in display.itertuples(index=False, name=None)]
    lines = [
        "| " + " | ".join(headers) + " |",
        "| " + " | ".join(["---"] * len(headers)) + " |",
    ]
    lines.extend("| " + " | ".join(row) + " |" for row in rows)
    return "\n".join(lines) + "\n"


def format_percent(x: float) -> str:
    if pd.isna(x):
        return "NA"
    return f"{100 * x:.1f}%"


def write_summary_report(
    ctx: DatasetContext,
    tables: Dict[str, pd.DataFrame],
    daily: pd.Series,
    weekly: pd.Series,
    monthly: pd.Series,
    yearly: pd.Series,
    wide_year_used: bool = False,
) -> None:
    report_path = ctx.output_dir / "summary_report.md"

    lines: List[str] = []
    lines.append(f"# Time-Series Analysis Report: `{ctx.name}`\n")
    lines.append(f"Input file: `{ctx.path}`\n")
    lines.append(f"Rows: **{ctx.df.shape[0]:,}**  \nColumns: **{ctx.df.shape[1]:,}**\n")

    if ctx.time_info is None and not wide_year_used:
        lines.append("## Temporal data availability\n")
        lines.append(
            "No usable date/time, year/month, or wide yearly incident-count columns were detected. "
            "This file appears to be a purely cross-sectional geographic aggregate. "
            "A genuine time-series analysis cannot be performed from this file alone.\n"
        )
        lines.append(
            "Recommended next step: create block-group or tract time series from the incident-level file "
            "by grouping incidents by geography and date period, then join ACS/SVI/NSI features.\n"
        )
        report_path.write_text("\n".join(lines), encoding="utf-8")
        return

    if ctx.time_info is not None:
        lines.append("## Detected temporal structure\n")
        lines.append(f"- Date column/source: **`{ctx.time_info.date_col}`** ({ctx.time_info.date_source})")
        if ctx.count_col:
            lines.append(f"- Count column used for aggregation: **`{ctx.count_col}`**")
        else:
            lines.append("- Count logic: **one row = one incident/observation**")
        if ctx.geo_col:
            lines.append(f"- Geography column: **`{ctx.geo_col}`**")
        lines.append("")
    elif wide_year_used:
        lines.append("## Detected temporal structure\n")
        lines.append("No regular date column was found, but wide yearly incident-count columns were detected and summed.\n")

    basic = tables.get("basic_summary", pd.DataFrame())
    if not basic.empty:
        total = basic.loc[basic["series"] == "Daily", "total_incidents"]
        if total.empty:
            total = basic.loc[basic["series"] == "Monthly", "total_incidents"]
        lines.append("## Core time-series summary\n")
        lines.append(markdown_table(basic, max_rows=10))

        # Interpretive bullets from daily/monthly data.
        if not daily.empty:
            zero_share = float((daily == 0).mean())
            vtm = float(daily.var(ddof=1) / daily.mean()) if daily.mean() > 0 and len(daily) > 1 else np.nan
            lines.append("### Main temporal signals\n")
            lines.append(f"- The observed date range runs from **{daily.index.min().date()}** to **{daily.index.max().date()}**.")
            lines.append(f"- Zero-incident days account for **{format_percent(zero_share)}** of daily periods.")
            if not pd.isna(vtm):
                lines.append(f"- The daily variance-to-mean ratio is **{vtm:.2f}**. Values above 1 indicate overdispersion/episodic clustering relative to a simple Poisson-like process.")
            if daily.sum() > 0:
                top_day = daily.idxmax()
                lines.append(f"- The highest-count day is **{top_day.date()}** with **{daily.max():.0f}** incidents.")
            lines.append("")

    if "monthly_seasonality" in tables and not tables["monthly_seasonality"].empty:
        seasonality = tables["monthly_seasonality"].sort_values("event_count", ascending=False)
        lines.append("## Month-of-year seasonality\n")
        lines.append("Highest-count calendar months in the available data:\n")
        lines.append(markdown_table(seasonality[["month_name", "event_count", "share_of_total"]], max_rows=5))

    if "weekday_pattern" in tables and not tables["weekday_pattern"].empty:
        weekday = tables["weekday_pattern"].sort_values("event_count", ascending=False)
        lines.append("## Day-of-week pattern\n")
        lines.append(markdown_table(weekday[["weekday_name", "event_count", "share_of_total"]], max_rows=7))

    if "hourly_pattern" in tables and not tables["hourly_pattern"].empty:
        hourly = tables["hourly_pattern"].sort_values("event_count", ascending=False)
        lines.append("## Hour-of-day pattern\n")
        lines.append(markdown_table(hourly[["hour", "event_count", "share_of_total"]], max_rows=10))

    if "top_daily_periods" in tables and not tables["top_daily_periods"].empty:
        lines.append("## Peak daily periods\n")
        lines.append(markdown_table(tables["top_daily_periods"], max_rows=10))

    if "rolling_anomaly_days" in tables and not tables["rolling_anomaly_days"].empty:
        lines.append("## High-count anomaly screen\n")
        lines.append(
            "The table below uses a simple rolling z-score screen. It is exploratory, not a causal event detector.\n"
        )
        lines.append(markdown_table(tables["rolling_anomaly_days"], max_rows=10))

    if "category_monthly_incident_type" in tables and not tables["category_monthly_incident_type"].empty:
        lines.append("## Incident-type temporal composition\n")
        lines.append("A monthly trend figure for the most common incident types is saved in the figures folder.\n")

    if "category_monthly_property_use" in tables and not tables["category_monthly_property_use"].empty:
        lines.append("## Property-use temporal composition\n")
        lines.append("A monthly trend figure for the most common property-use categories is saved in the figures folder.\n")

    if "geo_monthly_heatmap" in tables and not tables["geo_monthly_heatmap"].empty:
        lines.append("## Geographic temporal concentration\n")
        lines.append("A monthly heatmap for the highest-burden geographies is saved in the figures folder.\n")

    lines.append("## Generated figures\n")
    figure_files = sorted(p.name for p in ctx.figures_dir.glob("*.png"))
    if figure_files:
        for f in figure_files:
            lines.append(f"- `{f}`")
    else:
        lines.append("No figures were generated, likely because temporal information was unavailable or too sparse.")
    lines.append("")

    report_path.write_text("\n".join(lines), encoding="utf-8")



def create_context(name: str, path: Path) -> Optional[DatasetContext]:
    if not path.exists():
        print(f"[SKIP] {name}: file not found -> {path}")
        return None

    print(f"[READ] {name}: {path}")
    df = pd.read_csv(path, low_memory=False)

    output_dir = OUTPUT_ROOT / name
    figures_dir = output_dir / "figures"
    figures_dir.mkdir(parents=True, exist_ok=True)

    time_info = infer_datetime_column(df)
    count_col = infer_count_column(df, name)

    return DatasetContext(
        name=name,
        path=path,
        output_dir=output_dir,
        figures_dir=figures_dir,
        df=df,
        time_info=time_info,
        count_col=count_col,
        geo_col=find_column(df, GEO_PRIORITY_NAMES),
        incident_type_col=find_column(df, INCIDENT_TYPE_PRIORITY_NAMES),
        property_use_col=find_column(df, PROPERTY_USE_PRIORITY_NAMES),
        station_col=find_column(df, STATION_PRIORITY_NAMES),
        loss_col=infer_loss_column(df),
        response_time_col=infer_response_time_column(df),
    )


def analyze_dataset(ctx: DatasetContext) -> None:
    print(f"[ANALYZE] {ctx.name}")
    tables: Dict[str, pd.DataFrame] = {}

    event_df = build_event_frame(ctx)
    wide_year_used = False

    if event_df is None or event_df.empty:
        wide_event_df = build_wide_year_series(ctx.df)
        if wide_event_df is not None and not wide_event_df.empty:
            event_df = wide_event_df[["analysis_date", "event_count"]].copy()
            tables["wide_year_sources"] = wide_event_df
            wide_year_used = True
        else:
            write_summary_report(
                ctx=ctx,
                tables=tables,
                daily=pd.Series(dtype=float),
                weekly=pd.Series(dtype=float),
                monthly=pd.Series(dtype=float),
                yearly=pd.Series(dtype=float),
                wide_year_used=False,
            )
            print(f"[DONE] {ctx.name}: no temporal data detected")
            return

    daily = aggregate_series(event_df, "D")
    weekly = aggregate_series(event_df, "W-SUN")
    monthly = aggregate_series(event_df, "MS")
    yearly = aggregate_series(event_df, "YS")

    tables["basic_summary"] = calculate_basic_ts_summary(daily, weekly, monthly, yearly)
    tables["top_daily_periods"] = top_periods(daily, 15)
    tables["top_weekly_periods"] = top_periods(weekly, 15)
    tables["top_monthly_periods"] = top_periods(monthly, 15)
    tables["monthly_seasonality"] = monthly_seasonality(event_df)
    tables["weekday_pattern"] = weekday_pattern(event_df)
    tables["hourly_pattern"] = hourly_pattern(event_df)
    tables["rolling_anomaly_days"] = detect_anomalous_days(daily)

    save_line_plot(daily, f"{ctx.name}: daily incident counts", "Incident count", ctx.figures_dir / "daily_incident_counts.png", rolling_window=30)
    save_line_plot(weekly, f"{ctx.name}: weekly incident counts", "Incident count", ctx.figures_dir / "weekly_incident_counts.png", rolling_window=8)
    save_line_plot(monthly, f"{ctx.name}: monthly incident counts", "Incident count", ctx.figures_dir / "monthly_incident_counts.png", rolling_window=6)
    save_line_plot(yearly, f"{ctx.name}: yearly incident counts", "Incident count", ctx.figures_dir / "yearly_incident_counts.png", rolling_window=None)

    if not tables["monthly_seasonality"].empty:
        save_bar_plot(
            tables["monthly_seasonality"],
            x="month_name",
            y="event_count",
            title=f"{ctx.name}: incidents by calendar month",
            x_label="Month",
            y_label="Incident count",
            path=ctx.figures_dir / "month_of_year_seasonality.png",
            rotate=True,
        )
    if not tables["weekday_pattern"].empty:
        save_bar_plot(
            tables["weekday_pattern"],
            x="weekday_name",
            y="event_count",
            title=f"{ctx.name}: incidents by day of week",
            x_label="Day of week",
            y_label="Incident count",
            path=ctx.figures_dir / "day_of_week_pattern.png",
            rotate=True,
        )
    if not tables["hourly_pattern"].empty:
        save_bar_plot(
            tables["hourly_pattern"],
            x="hour",
            y="event_count",
            title=f"{ctx.name}: incidents by hour of day",
            x_label="Hour of day",
            y_label="Incident count",
            path=ctx.figures_dir / "hour_of_day_pattern.png",
            rotate=False,
        )
        tables["day_hour_heatmap"] = save_day_hour_heatmap(event_df, ctx.figures_dir / "day_hour_heatmap.png")

    if len(weekly.dropna()) >= 104:
        save_stl_plot(weekly, f"{ctx.name}: STL decomposition of weekly incident counts", ctx.figures_dir / "stl_weekly_counts.png", period=52)
        save_acf_plot(weekly, f"{ctx.name}: autocorrelation of weekly incident counts", ctx.figures_dir / "acf_weekly_counts.png", lags=52)
    if len(monthly.dropna()) >= 24:
        save_stl_plot(monthly, f"{ctx.name}: STL decomposition of monthly incident counts", ctx.figures_dir / "stl_monthly_counts.png", period=12)
        save_acf_plot(monthly, f"{ctx.name}: autocorrelation of monthly incident counts", ctx.figures_dir / "acf_monthly_counts.png", lags=24)

    if ctx.incident_type_col and ctx.incident_type_col in event_df.columns:
        tables["category_monthly_incident_type"] = save_category_monthly_plot(
            event_df,
            category_col=ctx.incident_type_col,
            title=f"{ctx.name}: monthly counts by top incident types",
            path=ctx.figures_dir / "monthly_top_incident_types.png",
        )

    if ctx.property_use_col and ctx.property_use_col in event_df.columns:
        tables["category_monthly_property_use"] = save_category_monthly_plot(
            event_df,
            category_col=ctx.property_use_col,
            title=f"{ctx.name}: monthly counts by top property-use categories",
            path=ctx.figures_dir / "monthly_top_property_uses.png",
        )

    if ctx.station_col and ctx.station_col in event_df.columns:
        tables["category_monthly_station"] = save_category_monthly_plot(
            event_df,
            category_col=ctx.station_col,
            title=f"{ctx.name}: monthly counts by top stations",
            path=ctx.figures_dir / "monthly_top_stations.png",
        )

    if ctx.geo_col and ctx.geo_col in event_df.columns:
        tables["geo_monthly_heatmap"] = save_geo_monthly_heatmap(
            event_df,
            geo_col=ctx.geo_col,
            path=ctx.figures_dir / "geo_monthly_heatmap_top_geographies.png",
        )

    if ctx.loss_col and ctx.loss_col in event_df.columns:
        tmp = event_df.copy()
        tmp["loss_value"] = pd.to_numeric(tmp[ctx.loss_col], errors="coerce").fillna(0)
        monthly_loss = tmp.set_index("analysis_date")["loss_value"].sort_index().resample("MS").sum()
        tables["monthly_loss"] = monthly_loss.reset_index().rename(columns={"analysis_date": "month_start", "loss_value": "total_loss"})
        save_line_plot(monthly_loss, f"{ctx.name}: monthly total recorded loss", "Total loss", ctx.figures_dir / "monthly_total_loss.png", rolling_window=6)

    if ctx.response_time_col and ctx.response_time_col in event_df.columns:
        tmp = event_df.copy()
        tmp["response_time"] = pd.to_numeric(tmp[ctx.response_time_col], errors="coerce")
        monthly_response = tmp.set_index("analysis_date")["response_time"].sort_index().resample("MS").median()
        tables["monthly_median_response_time"] = monthly_response.reset_index().rename(columns={"analysis_date": "month_start", "response_time": "median_response_time"})
        save_line_plot(monthly_response, f"{ctx.name}: monthly median response time", "Median response time", ctx.figures_dir / "monthly_median_response_time.png", rolling_window=6)

    if SAVE_INTERMEDIATE_CSV:
        series_dir = ctx.output_dir / "series_csv"
        series_dir.mkdir(parents=True, exist_ok=True)
        daily.rename("incident_count").to_csv(series_dir / "daily_counts.csv")
        weekly.rename("incident_count").to_csv(series_dir / "weekly_counts.csv")
        monthly.rename("incident_count").to_csv(series_dir / "monthly_counts.csv")
        yearly.rename("incident_count").to_csv(series_dir / "yearly_counts.csv")

    write_excel_tables(ctx.output_dir / "tables.xlsx", tables)
    write_summary_report(ctx, tables, daily, weekly, monthly, yearly, wide_year_used=wide_year_used)
    print(f"[DONE] {ctx.name}: outputs -> {ctx.output_dir}")


def write_cross_dataset_report(contexts: List[DatasetContext]) -> None:
    combined_dir = OUTPUT_ROOT / "combined"
    combined_dir.mkdir(parents=True, exist_ok=True)
    path = combined_dir / "time_series_readme.md"

    lines = [
        "# Cross-Dataset Time-Series Notes\n",
        "This folder contains time-series analysis outputs for the incident-level, block-group-level, and tract-level datasets.\n",
        "## How to interpret the levels\n",
        "- **Incident level** is the most reliable source for temporal analysis because each row usually corresponds to one incident with an event date/time.",
        "- **Block-group level** is useful for spatially localized temporal risk only if the file keeps a date/year/month dimension. If it is purely cross-sectional, use the incident-level file to construct block-group time series.",
        "- **Tract level** smooths local noise and is useful for broader neighborhood-scale temporal risk, again only if temporal information exists.\n",
        "## Suggested reporting narrative\n",
        "1. Start with the incident-level daily/weekly/monthly pattern to describe the overall fire burden over time.",
        "2. Use seasonality figures to discuss whether fire incidents concentrate in particular months, weekdays, or hours.",
        "3. Use incident-type/property-use temporal plots to separate routine confined fires from more severe structural or building-related incidents.",
        "4. Use geographic heatmaps to identify whether high-risk geographies are consistently high over time or spike only in specific periods.",
        "5. For modeling, prefer count models or forecasting models that can handle overdispersion and seasonality, rather than assuming stable independent daily counts.\n",
    ]

    lines.append("## Generated dataset reports\n")
    for ctx in contexts:
        rel = ctx.output_dir / "summary_report.md"
        lines.append(f"- `{ctx.name}`: `{rel}`")

    path.write_text("\n".join(lines), encoding="utf-8")


def main() -> None:
    OUTPUT_ROOT.mkdir(parents=True, exist_ok=True)

    contexts: List[DatasetContext] = []
    for name, path in INPUT_FILES.items():
        ctx = create_context(name, path)
        if ctx is None:
            continue
        analyze_dataset(ctx)
        contexts.append(ctx)

    if contexts:
        write_cross_dataset_report(contexts)
        print(f"[DONE] combined notes -> {OUTPUT_ROOT / 'combined'}")
    else:
        print("No input files were found. Check INPUT_FILES at the top of the script.")


if __name__ == "__main__":
    main()
