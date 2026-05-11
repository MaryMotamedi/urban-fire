from __future__ import annotations

import math
import re
import textwrap
import warnings
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, Iterable, List, Optional, Sequence, Tuple

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt



DATA_DIR = Path("data")
OUTPUT_ROOT = Path("output")
FEATURE_DEF_PATH = Path("Feature_Defintion.xlsx")

SAVE_TABLES_AS_CSV = False

TOP_N = 15
RANDOM_STATE = 42


@dataclass(frozen=True)
class DatasetConfig:
    name: str
    level: str
    path: Path
    feature_sheet: Optional[str]
    geo_key_candidates: Tuple[str, ...]
    description: str


DATASETS: Tuple[DatasetConfig, ...] = (
    DatasetConfig(
        name="incident_level",
        level="incident",
        path=DATA_DIR / "chicago_fires_full_acs_svi_nsi.csv",
        feature_sheet="Incident_Level",
        geo_key_candidates=("geo_id", "block_group_code", "tract_code", "zip5"),
        description="Individual fire incidents joined with ACS/SVI/NSI features.",
    ),
    DatasetConfig(
        name="block_group_level",
        level="block_group",
        path=DATA_DIR / "chicago_fire_block_groups_full_acs_svi_nsi.csv",
        feature_sheet="BG_Level",
        geo_key_candidates=("geo_id", "block_group_code", "tract_code"),
        description="Block-group-level aggregated fire risk, census, SVI, and building features.",
    ),
    DatasetConfig(
        name="tract_level",
        level="tract",
        path=DATA_DIR / "chicago_fires_tract_acs_svi_nsi.csv",
        feature_sheet="Tract_Level",
        geo_key_candidates=("tract_geo_id", "tract_code"),
        description="Tract-level aggregated fire risk, census, SVI, and building features.",
    ),
)

DAY_ORDER = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]



def ensure_dir(path: Path) -> Path:
    path.mkdir(parents=True, exist_ok=True)
    return path


def clean_filename(value: object, max_len: int = 90) -> str:
    text = str(value)
    text = re.sub(r"[^A-Za-z0-9_\-]+", "_", text).strip("_")
    return text[:max_len] if text else "value"


def first_existing(candidates: Iterable[str], df: pd.DataFrame) -> Optional[str]:
    for col in candidates:
        if col in df.columns:
            return col
    return None


def existing(candidates: Iterable[str], df: pd.DataFrame) -> List[str]:
    return [c for c in candidates if c in df.columns]


def numeric_series(df: pd.DataFrame, col: str) -> pd.Series:
    return pd.to_numeric(df[col], errors="coerce")


def pct(value: float) -> str:
    if pd.isna(value):
        return "NA"
    return f"{100 * value:.1f}%"


def fmt_num(value: object, digits: int = 2) -> str:
    if value is None or pd.isna(value):
        return "NA"
    try:
        value = float(value)
    except Exception:
        return str(value)
    if abs(value) >= 1_000_000:
        return f"{value:,.0f}"
    if abs(value) >= 1_000:
        return f"{value:,.1f}"
    if float(value).is_integer():
        return f"{value:,.0f}"
    return f"{value:,.{digits}f}"


def df_to_markdown(df: pd.DataFrame, max_rows: int = 20, index: bool = False) -> str:
    """Convert a dataframe to markdown, with a dependency-free fallback."""
    if df is None or df.empty:
        return "_No rows available._"
    shown = df.head(max_rows).copy()
    try:
        return shown.to_markdown(index=index)
    except Exception:
        return "```text\n" + shown.to_string(index=index) + "\n```"


def save_table_if_enabled(table: pd.DataFrame, out_dir: Path, name: str) -> None:
    if SAVE_TABLES_AS_CSV and table is not None and not table.empty:
        table.to_csv(out_dir / f"{name}.csv", index=False)


def save_current_fig(out_dir: Path, filename: str) -> None:
    plt.tight_layout()
    plt.savefig(out_dir / filename, dpi=220, bbox_inches="tight")
    plt.close()


def save_barh(
    series: pd.Series,
    out_dir: Path,
    filename: str,
    title: str,
    xlabel: str,
    ylabel: str = "",
    top_n: int = TOP_N,
) -> None:
    s = series.dropna().copy()
    if s.empty:
        return
    s = s.sort_values(ascending=False).head(top_n).sort_values(ascending=True)
    height = max(4, min(12, 0.45 * len(s) + 1.5))
    plt.figure(figsize=(10, height))
    plt.barh(s.index.astype(str), s.values)
    plt.title(title)
    plt.xlabel(xlabel)
    plt.ylabel(ylabel)
    save_current_fig(out_dir, filename)


def save_bar(
    series: pd.Series,
    out_dir: Path,
    filename: str,
    title: str,
    xlabel: str,
    ylabel: str,
) -> None:
    s = series.dropna().copy()
    if s.empty:
        return
    plt.figure(figsize=(10, 4.8))
    plt.bar(s.index.astype(str), s.values)
    plt.title(title)
    plt.xlabel(xlabel)
    plt.ylabel(ylabel)
    plt.xticks(rotation=45, ha="right")
    save_current_fig(out_dir, filename)


def save_hist(
    values: pd.Series,
    out_dir: Path,
    filename: str,
    title: str,
    xlabel: str,
    bins: int = 30,
    clip_upper_q: Optional[float] = None,
) -> None:
    x = pd.to_numeric(values, errors="coerce").dropna()
    if x.empty:
        return
    if clip_upper_q is not None and 0 < clip_upper_q < 1:
        upper = x.quantile(clip_upper_q)
        x = x.clip(upper=upper)
    plt.figure(figsize=(8, 5))
    plt.hist(x, bins=bins)
    plt.title(title)
    plt.xlabel(xlabel)
    plt.ylabel("Number of observations")
    save_current_fig(out_dir, filename)


def save_scatter(
    df: pd.DataFrame,
    x_col: str,
    y_col: str,
    out_dir: Path,
    filename: str,
    title: str,
    xlabel: Optional[str] = None,
    ylabel: Optional[str] = None,
    log_x: bool = False,
    log_y: bool = False,
) -> None:
    if x_col not in df.columns or y_col not in df.columns:
        return
    x = pd.to_numeric(df[x_col], errors="coerce")
    y = pd.to_numeric(df[y_col], errors="coerce")
    valid = x.notna() & y.notna()
    if valid.sum() < 3:
        return
    x = x[valid]
    y = y[valid]
    if log_x:
        valid_log = x > 0
        x = np.log1p(x[valid_log])
        y = y[valid_log]
        xlabel = f"log(1 + {xlabel or x_col})"
    if log_y:
        valid_log = y > 0
        y = np.log1p(y[valid_log])
        x = x[valid_log]
        ylabel = f"log(1 + {ylabel or y_col})"
    if len(x) < 3:
        return
    plt.figure(figsize=(7, 5.5))
    plt.scatter(x, y, alpha=0.65, s=24)
    plt.title(title)
    plt.xlabel(xlabel or x_col)
    plt.ylabel(ylabel or y_col)
    save_current_fig(out_dir, filename)


def save_correlation_heatmap(
    corr: pd.DataFrame,
    out_dir: Path,
    filename: str,
    title: str,
) -> None:
    if corr is None or corr.empty or corr.shape[0] < 2:
        return
    plt.figure(figsize=(max(7, 0.5 * corr.shape[1] + 3), max(6, 0.45 * corr.shape[0] + 3)))
    im = plt.imshow(corr.values, aspect="auto", vmin=-1, vmax=1)
    plt.colorbar(im, fraction=0.046, pad=0.04, label="Correlation")
    plt.xticks(range(corr.shape[1]), corr.columns, rotation=45, ha="right")
    plt.yticks(range(corr.shape[0]), corr.index)
    plt.title(title)
    save_current_fig(out_dir, filename)



def load_feature_definitions(feature_def_path: Path) -> Dict[str, pd.DataFrame]:
    if not feature_def_path.exists():
        return {}
    sheets = pd.read_excel(feature_def_path, sheet_name=None)
    cleaned: Dict[str, pd.DataFrame] = {}
    for sheet_name, sheet_df in sheets.items():
        sheet_df = sheet_df.copy()
        sheet_df.columns = [str(c).strip() for c in sheet_df.columns]
        if "Feature" not in sheet_df.columns:
            continue
        sheet_df = sheet_df.dropna(subset=["Feature"])
        sheet_df["Feature"] = sheet_df["Feature"].astype(str).str.strip()
        cleaned[sheet_name] = sheet_df.drop_duplicates("Feature")
    return cleaned


def feature_map_for_sheet(feature_defs: Dict[str, pd.DataFrame], sheet_name: Optional[str]) -> Dict[str, str]:
    if sheet_name is None or sheet_name not in feature_defs:
        return {}
    df = feature_defs[sheet_name]
    if "Def" not in df.columns:
        return {}
    return dict(zip(df["Feature"], df["Def"].fillna("")))


def load_dataset(path: Path) -> pd.DataFrame:
    df = pd.read_csv(path, low_memory=False)
    df.columns = [str(c).strip() for c in df.columns]
    return df


def resolve_datasets() -> List[DatasetConfig]:
    """Return the configured full analysis datasets.

    The script intentionally does not fall back to sample files. If one of the
    expected cleaned CSV files is missing, that dataset is skipped and a small
    report is written explaining the missing input.
    """
    return list(DATASETS)



def add_incident_derived_features(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()

    for col in ["incident_date", "alarm_ts", "arrive_scene_ts", "incident_controlled_ts"]:
        if col in df.columns:
            df[col] = pd.to_datetime(df[col], errors="coerce")

    if {"alarm_ts", "arrive_scene_ts"}.issubset(df.columns):
        df["response_minutes"] = (df["arrive_scene_ts"] - df["alarm_ts"]).dt.total_seconds() / 60
        df.loc[df["response_minutes"] < 0, "response_minutes"] = np.nan

    time_col = "alarm_ts" if "alarm_ts" in df.columns else "incident_date" if "incident_date" in df.columns else None
    if time_col is not None:
        df["year"] = df[time_col].dt.year
        df["month"] = df[time_col].dt.month
        df["month_name"] = df[time_col].dt.month_name()
        df["day_of_week"] = df[time_col].dt.day_name()
        df["hour"] = df[time_col].dt.hour
        df["is_weekend"] = df[time_col].dt.dayofweek.isin([5, 6])

    for col in [
        "property_loss", "contents_loss", "property_value", "contents_value",
        "firefighter_fatalities", "other_fatalities", "firefighter_injuries", "other_injuries",
        "suppression_apparatus_count", "ems_apparatus_count", "other_apparatus_count",
        "suppression_personnel_count", "ems_personnel_count", "other_personnel_count",
    ]:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce")

    loss_cols = existing(["property_loss", "contents_loss"], df)
    if loss_cols:
        df["total_loss"] = df[loss_cols].fillna(0).sum(axis=1)
        df["has_positive_loss"] = df["total_loss"] > 0
        positive_loss = df.loc[df["total_loss"] > 0, "total_loss"]
        if len(positive_loss) > 0:
            df["is_high_loss"] = df["total_loss"] >= positive_loss.quantile(0.75)
        else:
            df["is_high_loss"] = False

    injury_cols = existing(["firefighter_injuries", "other_injuries"], df)
    fatality_cols = existing(["firefighter_fatalities", "other_fatalities"], df)
    personnel_cols = existing(["suppression_personnel_count", "ems_personnel_count", "other_personnel_count"], df)
    apparatus_cols = existing(["suppression_apparatus_count", "ems_apparatus_count", "other_apparatus_count"], df)

    if injury_cols:
        df["total_injuries"] = df[injury_cols].fillna(0).sum(axis=1)
    if fatality_cols:
        df["total_fatalities"] = df[fatality_cols].fillna(0).sum(axis=1)
    if personnel_cols:
        df["total_personnel"] = df[personnel_cols].fillna(0).sum(axis=1)
    if apparatus_cols:
        df["total_apparatus"] = df[apparatus_cols].fillna(0).sum(axis=1)

    if "incident_type" in df.columns:
        incident_type = df["incident_type"].astype(str)
        df["is_building_fire"] = incident_type.str.contains("Building fires", case=False, na=False)
        df["is_cooking_fire"] = incident_type.str.contains("Cooking", case=False, na=False)
        df["is_rubbish_or_trash_fire"] = incident_type.str.contains("rubbish|trash|waste", case=False, na=False, regex=True)
        df["is_vehicle_fire"] = incident_type.str.contains("vehicle", case=False, na=False)
        df["is_outside_fire"] = incident_type.str.contains("outside", case=False, na=False)

    return df


def add_geographic_derived_features(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()

    for col in [
        "incident_count", "p_total", "structures_count", "tract_area_sqmi", "bg_land_area", "land_area",
        "avg_property_loss", "avg_contents_loss", "avg_suppression_personnel_count",
        "avg_ems_personnel_count", "avg_other_personnel_count",
        "avg_suppression_apparatus_count", "avg_ems_apparatus_count", "avg_other_apparatus_count",
    ]:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce")

    if {"avg_property_loss", "avg_contents_loss"}.issubset(df.columns):
        df["avg_total_loss"] = df[["avg_property_loss", "avg_contents_loss"]].fillna(0).sum(axis=1)
    elif "avg_property_loss" in df.columns:
        df["avg_total_loss"] = df["avg_property_loss"]
    elif "avg_contents_loss" in df.columns:
        df["avg_total_loss"] = df["avg_contents_loss"]

    if {"incident_count", "avg_total_loss"}.issubset(df.columns):
        df["estimated_total_loss"] = df["incident_count"] * df["avg_total_loss"]

    area_col = first_existing(["bg_land_area", "land_area", "tract_area_sqmi"], df)
    if area_col and {"incident_count", area_col}.issubset(df.columns):
        df["incidents_per_sqmi"] = df["incident_count"] / df[area_col].replace(0, np.nan)

    if {"incident_count", "p_total"}.issubset(df.columns):
        df["incidents_per_1000_pop"] = df["incident_count"] / df["p_total"].replace(0, np.nan) * 1000

    if {"incident_count", "structures_count"}.issubset(df.columns):
        df["incidents_per_1000_structures"] = df["incident_count"] / df["structures_count"].replace(0, np.nan) * 1000

    if {"estimated_total_loss", "p_total"}.issubset(df.columns):
        df["estimated_loss_per_1000_pop"] = df["estimated_total_loss"] / df["p_total"].replace(0, np.nan) * 1000

    if {"estimated_total_loss", "structures_count"}.issubset(df.columns):
        df["estimated_loss_per_1000_structures"] = (
            df["estimated_total_loss"] / df["structures_count"].replace(0, np.nan) * 1000
        )

    if {"avg_suppression_personnel_count", "avg_ems_personnel_count", "avg_other_personnel_count"}.issubset(df.columns):
        df["avg_total_personnel"] = df[[
            "avg_suppression_personnel_count", "avg_ems_personnel_count", "avg_other_personnel_count"
        ]].fillna(0).sum(axis=1)

    if {"avg_suppression_apparatus_count", "avg_ems_apparatus_count", "avg_other_apparatus_count"}.issubset(df.columns):
        df["avg_total_apparatus"] = df[[
            "avg_suppression_apparatus_count", "avg_ems_apparatus_count", "avg_other_apparatus_count"
        ]].fillna(0).sum(axis=1)

    return df


def aggregate_incidents_to_geography(
    df: pd.DataFrame,
    geo_key: str,
    feature_groups: Dict[str, List[str]],
) -> pd.DataFrame:
    """Optional incident-level geographic aggregation for hotspot/risk checks."""
    if geo_key not in df.columns:
        return pd.DataFrame()

    agg_spec = {"incident_count": (geo_key, "size")}
    if "is_building_fire" in df.columns:
        agg_spec["building_fire_count"] = ("is_building_fire", "sum")
    if "is_cooking_fire" in df.columns:
        agg_spec["cooking_fire_count"] = ("is_cooking_fire", "sum")
    if "is_rubbish_or_trash_fire" in df.columns:
        agg_spec["rubbish_or_trash_fire_count"] = ("is_rubbish_or_trash_fire", "sum")
    if "total_loss" in df.columns:
        agg_spec["total_loss"] = ("total_loss", "sum")
        agg_spec["avg_total_loss"] = ("total_loss", "mean")
    if "response_minutes" in df.columns:
        agg_spec["mean_response_minutes"] = ("response_minutes", "mean")
        agg_spec["median_response_minutes"] = ("response_minutes", "median")
    if "total_personnel" in df.columns:
        agg_spec["mean_total_personnel"] = ("total_personnel", "mean")
    if "total_apparatus" in df.columns:
        agg_spec["mean_total_apparatus"] = ("total_apparatus", "mean")

    geo = df.groupby(geo_key, dropna=False).agg(**agg_spec).reset_index()

    first_value_cols = []
    for group_name in ["geography", "acs", "svi", "nsi"]:
        first_value_cols.extend(feature_groups.get(group_name, []))
    first_value_cols = [c for c in dict.fromkeys(first_value_cols) if c in df.columns and c != geo_key]
    if first_value_cols:
        first_values = df.groupby(geo_key, dropna=False)[first_value_cols].first().reset_index()
        geo = geo.merge(first_values, on=geo_key, how="left")

    geo = add_geographic_derived_features(geo)
    return geo



def identify_feature_groups(df: pd.DataFrame) -> Dict[str, List[str]]:
    cols = list(df.columns)

    id_and_geo = {
        "state", "city", "state_fips", "county_fips", "tract_code", "block_group_code", "tract_geo_id",
        "state_name", "state_abbr", "county_name", "tract_name", "census_tract", "zip5", "geo_id",
        "geom", "zip_geom", "geom_32616", "zip_geom_32616", "geom_block_group", "geom_32616_block_group",
        "tract_geom", "tract_geom_32616", "bg_land_area", "bg_water_area", "land_area", "water_area",
        "tract_area_sqmi", "num_block_groups",
    }

    incident_specific = {
        "incident_key", "incident_date", "incident_number", "exposure_number", "station", "incident_type_code",
        "incident_type", "is_address_wildland", "aid_given_or_received_code", "incident_controlled_ts", "shift",
        "alarm_level", "district", "actions_taken_codes", "detector_alerted_occupants_code",
        "hazardous_material_released_code", "hazardous_material_released", "mixed_use_code", "mixed_use",
        "property_use_code", "property_use", "fire_department_id", "alarm_ts", "arrive_scene_ts",
        "location_type_code", "location_type", "suppression_apparatus_count", "ems_apparatus_count",
        "other_apparatus_count", "suppression_personnel_count", "ems_personnel_count", "other_personnel_count",
        "is_aid_included_in_resource_counts", "property_loss", "contents_loss", "property_value", "contents_value",
        "firefighter_fatalities", "other_fatalities", "firefighter_injuries", "other_injuries", "response_minutes",
        "total_loss", "has_positive_loss", "is_high_loss", "total_injuries", "total_fatalities", "total_personnel",
        "total_apparatus", "is_building_fire", "is_cooking_fire", "is_rubbish_or_trash_fire", "is_vehicle_fire",
        "is_outside_fire", "year", "month", "month_name", "day_of_week", "hour", "is_weekend",
    }

    aggregate_outcomes = {
        "incident_count", "avg_suppression_apparatus_count", "avg_ems_apparatus_count", "avg_other_apparatus_count",
        "avg_suppression_personnel_count", "avg_ems_personnel_count", "avg_other_personnel_count",
        "avg_property_loss", "avg_contents_loss", "avg_firefighter_fatalities", "avg_other_fatalities",
        "avg_firefighter_injuries", "avg_other_injuries", "avg_total_loss", "estimated_total_loss",
        "incidents_per_sqmi", "incidents_per_1000_pop", "incidents_per_1000_structures",
        "estimated_loss_per_1000_pop", "estimated_loss_per_1000_structures", "avg_total_personnel", "avg_total_apparatus",
        "building_fire_count", "cooking_fire_count", "rubbish_or_trash_fire_count", "vehicle_fire_count",
        "mean_response_minutes", "median_response_minutes", "mean_total_personnel", "mean_total_apparatus",
    }

    # SVI variables use EP/EPL/RPL/SPL/SF prefixes and some F_* flags
    svi = []
    for c in cols:
        if c.startswith(("ep_", "epl_", "rpl_", "spl_", "sf_")):
            svi.append(c)
        elif re.match(r"^f_.*_t\d$", c) or c in {"f_groupq_t4", "f_minrty_t3", "rpl_overall_t", "spl_overall_t", "sf_overall_t"}:
            svi.append(c)

    # NSI/building exposure variables
    nsi = []
    for c in cols:
        if c.startswith(("avg_", "count_")):
            nsi.append(c)
        elif c in {
            "structures_count", "total_p_night_u65", "total_p_night_o65", "total_p_day_u65", "total_p_day_o65",
            "total_students", "avg_ground_elevation_m", "avg_num_story", "avg_sqft", "avg_median_year_built",
            "avg_foundation_height", "avg_structure_value", "avg_contents_value",
        }:
            nsi.append(c)
    nsi = [c for c in nsi if c not in aggregate_outcomes]

    # ACS/census variables (Exclude SVI flags and aggregate outcomes)
    acs = []
    for c in cols:
        if c in svi or c in nsi or c in id_and_geo or c in incident_specific or c in aggregate_outcomes:
            continue
        if c.startswith(("p_", "m_", "f_", "hh_")) or c in {"acs_year", "acs_census_year", "acs_source_date"}:
            acs.append(c)

    geography = [c for c in cols if c in id_and_geo]
    incident = [c for c in cols if c in incident_specific]
    outcomes = [c for c in cols if c in aggregate_outcomes]

    return {
        "geography": geography,
        "incident": incident,
        "outcomes": outcomes,
        "acs": acs,
        "svi": [c for c in svi if c in cols],
        "nsi": [c for c in nsi if c in cols],
    }


def choose_geo_key(df: pd.DataFrame, candidates: Sequence[str]) -> Optional[str]:
    for key in candidates:
        if key in df.columns and df[key].nunique(dropna=True) > 0:
            return key
    return None


def choose_geo_label(df: pd.DataFrame, geo_key: Optional[str]) -> pd.Series:
    if geo_key is not None and geo_key in df.columns:
        base = df[geo_key].astype(str)
    else:
        base = pd.Series(np.arange(len(df)).astype(str), index=df.index)
    if "tract_name" in df.columns:
        label = df["tract_name"].astype(str) + " | " + base
        return label
    return base


def candidate_predictor_features(df: pd.DataFrame, feature_groups: Dict[str, List[str]]) -> List[str]:
    preferred = [
        # Basic exposure
        "p_total", "structures_count", "tract_area_sqmi", "bg_land_area", "land_area", "num_block_groups",
        # Demographics / ACS
        "p_under_18", "p_65_plus", "p_hl", "p_minority", "p_not_hl_black", "p_not_hl_asian",
        "hh_total", "hh_limeng", "p_low_income",
        # SVI
        "ep_pov150", "ep_unemp", "ep_hburd", "ep_nohsdp", "ep_uninsur", "ep_65_plus",
        "ep_17_and_younger", "ep_disabl", "ep_limeng", "ep_minrty", "ep_hs_10_plus",
        "ep_hs_crowd", "ep_noveh", "rpl_socioeconomic_t1", "rpl_households_t2",
        "rpl_minrty_t3", "rpl_housing_t4", "rpl_overall_t",
        # NSI/buildings
        "avg_num_story", "avg_sqft", "avg_median_year_built", "avg_structure_value", "avg_contents_value",
        "avg_foundation_height", "total_p_night_u65", "total_p_night_o65", "total_p_day_u65", "total_p_day_o65",
        "count_building_type_m", "count_building_type_w", "count_building_type_s", "count_building_type_c",
        "count_foundation_type_b", "count_foundation_type_s", "count_foundation_type_c",
        "count_occupancy_type_res", "count_occupancy_type_com", "count_occupancy_type_ind", "count_occupancy_type_pub",
    ]
    selected = [c for c in preferred if c in df.columns]

    # Add additional numeric ACS/SVI/NSI variables to make the script robust to naming variations
    for group in ["acs", "svi", "nsi"]:
        for c in feature_groups.get(group, []):
            if c in selected:
                continue
            if c in df.columns and pd.api.types.is_numeric_dtype(pd.to_numeric(df[c], errors="coerce")):
                selected.append(c)

    # Remove all-empty and constant predictors
    final = []
    for c in selected:
        x = pd.to_numeric(df[c], errors="coerce")
        if x.notna().sum() >= 3 and x.nunique(dropna=True) > 1:
            final.append(c)
    return final


def candidate_outcomes(df: pd.DataFrame, level: str) -> List[str]:
    if level == "incident":
        outcomes = [
            "total_loss", "has_positive_loss", "response_minutes", "total_injuries", "total_fatalities",
            "total_personnel", "total_apparatus", "is_building_fire", "is_cooking_fire", "is_rubbish_or_trash_fire",
        ]
    else:
        outcomes = [
            "incident_count", "incidents_per_1000_pop", "incidents_per_1000_structures", "incidents_per_sqmi",
            "avg_total_loss", "estimated_total_loss", "estimated_loss_per_1000_pop",
            "estimated_loss_per_1000_structures", "avg_total_personnel", "avg_total_apparatus",
            "avg_firefighter_injuries", "avg_other_injuries", "avg_firefighter_fatalities", "avg_other_fatalities",
        ]
    return [c for c in outcomes if c in df.columns]


def main_risk_target(df: pd.DataFrame) -> Optional[str]:
    for col in [
        "incidents_per_1000_structures",
        "incidents_per_1000_pop",
        "incidents_per_sqmi",
        "incident_count",
    ]:
        if col in df.columns and pd.to_numeric(df[col], errors="coerce").notna().sum() > 0:
            return col
    return None


def readable_feature_name(feature: str, feature_def_map: Dict[str, str], max_chars: int = 110) -> str:
    definition = str(feature_def_map.get(feature, "") or "").strip()
    if not definition:
        return feature
    definition = re.sub(r"\s+", " ", definition)
    if len(definition) > max_chars:
        definition = definition[: max_chars - 3] + "..."
    return f"{feature}: {definition}"



def data_profile(df: pd.DataFrame, cfg: DatasetConfig, feature_groups: Dict[str, List[str]]) -> pd.DataFrame:
    rows = [
        ("Rows", len(df)),
        ("Columns", df.shape[1]),
        ("Numeric columns", sum(pd.to_numeric(df[c], errors="coerce").notna().any() for c in df.columns)),
        ("ACS/census columns detected", len(feature_groups.get("acs", []))),
        ("SVI columns detected", len(feature_groups.get("svi", []))),
        ("NSI/building columns detected", len(feature_groups.get("nsi", []))),
    ]
    if cfg.level == "incident":
        if "incident_key" in df.columns:
            rows.append(("Unique incident keys", df["incident_key"].nunique(dropna=True)))
        time_col = "alarm_ts" if "alarm_ts" in df.columns else "incident_date" if "incident_date" in df.columns else None
        if time_col:
            rows.append(("Start date", df[time_col].min()))
            rows.append(("End date", df[time_col].max()))
        for col in ["geo_id", "tract_code", "station", "incident_type", "property_use"]:
            if col in df.columns:
                rows.append((f"Unique {col}", df[col].nunique(dropna=True)))
    else:
        geo_key = choose_geo_key(df, cfg.geo_key_candidates)
        if geo_key:
            rows.append((f"Unique {geo_key}", df[geo_key].nunique(dropna=True)))
        if "incident_count" in df.columns:
            rows.append(("Total incidents represented", numeric_series(df, "incident_count").sum()))
        if "p_total" in df.columns:
            rows.append(("Total population represented", numeric_series(df, "p_total").sum()))
        if "structures_count" in df.columns:
            rows.append(("Total structures represented", numeric_series(df, "structures_count").sum()))
    return pd.DataFrame(rows, columns=["Metric", "Value"])


def value_counts_table(df: pd.DataFrame, column: str, top_n: int = TOP_N) -> pd.DataFrame:
    if column not in df.columns:
        return pd.DataFrame()
    counts = df[column].value_counts(dropna=False).head(top_n)
    result = counts.rename_axis(column).reset_index(name="count")
    result["share"] = result["count"] / len(df)
    result["share"] = result["share"].map(lambda x: f"{100 * x:.1f}%")
    return result


def describe_numeric_table(df: pd.DataFrame, cols: Sequence[str]) -> pd.DataFrame:
    rows = []
    for col in cols:
        if col not in df.columns:
            continue
        x = pd.to_numeric(df[col], errors="coerce").dropna()
        if x.empty:
            continue
        rows.append({
            "variable": col,
            "n": int(x.shape[0]),
            "mean": x.mean(),
            "median": x.median(),
            "p25": x.quantile(0.25),
            "p75": x.quantile(0.75),
            "p95": x.quantile(0.95),
            "max": x.max(),
        })
    out = pd.DataFrame(rows)
    for c in ["mean", "median", "p25", "p75", "p95", "max"]:
        if c in out.columns:
            out[c] = out[c].map(lambda v: round(v, 3) if pd.notna(v) else v)
    return out


def top_geographies_table(df: pd.DataFrame, cfg: DatasetConfig, target: str, top_n: int = TOP_N) -> pd.DataFrame:
    if target not in df.columns:
        return pd.DataFrame()
    geo_key = choose_geo_key(df, cfg.geo_key_candidates)
    label = choose_geo_label(df, geo_key)
    work = df.copy()
    work["geography_label"] = label
    keep_cols = ["geography_label", target]
    for col in ["incident_count", "p_total", "structures_count", "estimated_total_loss", "avg_total_loss", "rpl_overall_t"]:
        if col in work.columns and col not in keep_cols:
            keep_cols.append(col)
    out = work[keep_cols].copy()
    out[target] = pd.to_numeric(out[target], errors="coerce")
    out = out.dropna(subset=[target]).sort_values(target, ascending=False).head(top_n)
    return out


def build_incident_summary_tables(df: pd.DataFrame) -> Dict[str, pd.DataFrame]:
    tables: Dict[str, pd.DataFrame] = {}
    for col in ["incident_type", "property_use", "station", "shift", "district"]:
        table = value_counts_table(df, col)
        if not table.empty:
            tables[f"top_{col}"] = table

    numeric_cols = existing([
        "response_minutes", "total_loss", "property_loss", "contents_loss", "total_personnel",
        "total_apparatus", "total_injuries", "total_fatalities",
    ], df)
    desc = describe_numeric_table(df, numeric_cols)
    if not desc.empty:
        tables["numeric_summary"] = desc

    if {"incident_type", "total_loss"}.issubset(df.columns):
        loss_by_type = df.groupby("incident_type", dropna=False).agg(
            incidents=("incident_type", "size"),
            total_loss=("total_loss", "sum"),
            mean_loss=("total_loss", "mean"),
            positive_loss_rate=("has_positive_loss", "mean") if "has_positive_loss" in df.columns else ("total_loss", lambda x: np.nan),
        ).reset_index().sort_values("total_loss", ascending=False)
        tables["loss_by_incident_type"] = loss_by_type.head(TOP_N)

    if {"property_use", "total_loss"}.issubset(df.columns):
        loss_by_property = df.groupby("property_use", dropna=False).agg(
            incidents=("property_use", "size"),
            total_loss=("total_loss", "sum"),
            mean_loss=("total_loss", "mean"),
        ).reset_index().sort_values("total_loss", ascending=False)
        tables["loss_by_property_use"] = loss_by_property.head(TOP_N)

    if {"day_of_week", "hour"}.issubset(df.columns):
        heat = pd.crosstab(df["day_of_week"], df["hour"]).reindex(DAY_ORDER).reindex(columns=range(24), fill_value=0)
        if not heat.empty:
            peak = heat.stack().sort_values(ascending=False).head(10).reset_index()
            peak.columns = ["day_of_week", "hour", "incident_count"]
            tables["peak_day_hour_windows"] = peak

    return tables


def build_geo_summary_tables(
    df: pd.DataFrame,
    cfg: DatasetConfig,
    feature_groups: Dict[str, List[str]],
    feature_def_map: Dict[str, str],
) -> Dict[str, pd.DataFrame]:
    tables: Dict[str, pd.DataFrame] = {}
    outcome_cols = candidate_outcomes(df, cfg.level)
    desc = describe_numeric_table(df, outcome_cols)
    if not desc.empty:
        tables["outcome_summary"] = desc

    target = main_risk_target(df)
    if target:
        top_geo = top_geographies_table(df, cfg, target)
        if not top_geo.empty:
            tables[f"top_geographies_by_{target}"] = top_geo

    correlations = spearman_correlations(df, cfg.level, feature_groups, feature_def_map)
    if not correlations.empty:
        tables["top_spearman_correlations"] = correlations.head(40)

    comparison = high_low_risk_feature_comparison(df, target, feature_groups, feature_def_map) if target else pd.DataFrame()
    if not comparison.empty:
        tables["high_vs_low_risk_feature_comparison"] = comparison.head(40)

    return tables


def write_report(out_dir: Path, title: str, sections: List[str]) -> None:
    text = "\n\n".join([f"# {title}"] + sections) + "\n"
    (out_dir / "summary_report.md").write_text(text, encoding="utf-8")



def spearman_correlations(
    df: pd.DataFrame,
    level: str,
    feature_groups: Dict[str, List[str]],
    feature_def_map: Dict[str, str],
) -> pd.DataFrame:
    outcomes = candidate_outcomes(df, level)
    predictors = candidate_predictor_features(df, feature_groups)

    rows = []
    min_valid = 20 if len(df) >= 50 else max(6, min(20, math.ceil(0.45 * len(df))))

    for target in outcomes:
        y = pd.to_numeric(df[target], errors="coerce")
        if y.nunique(dropna=True) <= 1:
            continue
        for feature in predictors:
            if feature == target:
                continue
            x = pd.to_numeric(df[feature], errors="coerce")
            valid = x.notna() & y.notna()
            if valid.sum() < min_valid:
                continue
            if x[valid].nunique(dropna=True) <= 1:
                continue
            corr = x[valid].corr(y[valid], method="spearman")
            if pd.isna(corr):
                continue
            rows.append({
                "target": target,
                "feature": feature,
                "spearman_corr": corr,
                "abs_corr": abs(corr),
                "n": int(valid.sum()),
                "feature_definition": feature_def_map.get(feature, ""),
            })

    result = pd.DataFrame(rows)
    if result.empty:
        return result
    return result.sort_values(["abs_corr", "target"], ascending=[False, True]).reset_index(drop=True)


def high_low_risk_feature_comparison(
    df: pd.DataFrame,
    target: Optional[str],
    feature_groups: Dict[str, List[str]],
    feature_def_map: Dict[str, str],
) -> pd.DataFrame:
    if target is None or target not in df.columns:
        return pd.DataFrame()
    y = pd.to_numeric(df[target], errors="coerce")
    if y.notna().sum() < 8 or y.nunique(dropna=True) <= 1:
        return pd.DataFrame()

    q25 = y.quantile(0.25)
    q75 = y.quantile(0.75)
    low_mask = y <= q25
    high_mask = y >= q75
    predictors = candidate_predictor_features(df, feature_groups)

    rows = []
    for feature in predictors:
        x = pd.to_numeric(df[feature], errors="coerce")
        low = x[low_mask].dropna()
        high = x[high_mask].dropna()
        if len(low) < 3 or len(high) < 3 or x.nunique(dropna=True) <= 1:
            continue
        pooled_std = x.dropna().std(ddof=0)
        mean_low = low.mean()
        mean_high = high.mean()
        standardized_diff = (mean_high - mean_low) / pooled_std if pooled_std and pooled_std > 0 else np.nan
        rows.append({
            "feature": feature,
            "target": target,
            "low_risk_mean_feature": mean_low,
            "high_risk_mean_feature": mean_high,
            "difference_high_minus_low": mean_high - mean_low,
            "standardized_difference": standardized_diff,
            "n_low": len(low),
            "n_high": len(high),
            "feature_definition": feature_def_map.get(feature, ""),
        })

    result = pd.DataFrame(rows)
    if result.empty:
        return result
    result["abs_standardized_difference"] = result["standardized_difference"].abs()
    return result.sort_values("abs_standardized_difference", ascending=False).reset_index(drop=True)



def plot_incident_level(df: pd.DataFrame, out_dir: Path) -> None:
    if "incident_type" in df.columns:
        save_barh(
            df["incident_type"].value_counts().head(TOP_N),
            out_dir,
            "01_top_incident_types.png",
            "Top Incident Types",
            "Incident count",
            "Incident type",
        )

    if "property_use" in df.columns:
        save_barh(
            df["property_use"].value_counts().head(TOP_N),
            out_dir,
            "02_top_property_uses.png",
            "Top Property Uses",
            "Incident count",
            "Property use",
        )

    if "year" in df.columns:
        counts = df.groupby("year").size().sort_index()
        save_bar(counts, out_dir, "03_incidents_by_year.png", "Incidents by Year", "Year", "Incident count")

    if "month" in df.columns:
        counts = df.groupby("month").size().reindex(range(1, 13), fill_value=0)
        save_bar(counts, out_dir, "04_incidents_by_month.png", "Incidents by Month", "Month", "Incident count")

    if "hour" in df.columns:
        counts = df.groupby("hour").size().reindex(range(24), fill_value=0)
        save_bar(counts, out_dir, "05_incidents_by_hour.png", "Incidents by Hour of Day", "Hour", "Incident count")

    if {"day_of_week", "hour"}.issubset(df.columns):
        heat = pd.crosstab(df["day_of_week"], df["hour"]).reindex(DAY_ORDER).reindex(columns=range(24), fill_value=0)
        if heat.notna().any().any():
            plt.figure(figsize=(13, 5))
            im = plt.imshow(heat.values, aspect="auto")
            plt.colorbar(im, label="Incident count")
            plt.title("Incident Heatmap: Day of Week × Hour")
            plt.xlabel("Hour")
            plt.ylabel("Day of week")
            plt.xticks(range(24), range(24))
            plt.yticks(range(len(DAY_ORDER)), DAY_ORDER)
            save_current_fig(out_dir, "06_day_hour_heatmap.png")

    if "response_minutes" in df.columns:
        save_hist(
            df["response_minutes"],
            out_dir,
            "07_response_time_distribution.png",
            "Response Time Distribution",
            "Minutes from alarm to arrival",
            bins=30,
            clip_upper_q=0.99,
        )

    if "total_loss" in df.columns:
        save_hist(
            df.loc[pd.to_numeric(df["total_loss"], errors="coerce") > 0, "total_loss"],
            out_dir,
            "08_positive_loss_distribution.png",
            "Distribution of Positive Recorded Losses",
            "Recorded loss, clipped at p99",
            bins=30,
            clip_upper_q=0.99,
        )

    if {"incident_type", "total_loss"}.issubset(df.columns):
        loss_by_type = df.groupby("incident_type")["total_loss"].sum().sort_values(ascending=False)
        save_barh(
            loss_by_type,
            out_dir,
            "09_total_loss_by_incident_type.png",
            "Total Recorded Loss by Incident Type",
            "Total loss",
            "Incident type",
        )

    if "station" in df.columns:
        save_barh(
            df["station"].value_counts().head(TOP_N),
            out_dir,
            "10_top_stations.png",
            "Top Stations by Incident Count",
            "Incident count",
            "Station",
        )


def incident_report_sections(
    df: pd.DataFrame,
    cfg: DatasetConfig,
    feature_groups: Dict[str, List[str]],
    feature_def_map: Dict[str, str],
    out_dir: Path,
) -> List[str]:
    tables = build_incident_summary_tables(df)
    for name, table in tables.items():
        save_table_if_enabled(table, out_dir, name)

    profile = data_profile(df, cfg, feature_groups)
    sections = [
        "## Dataset profile\n" + df_to_markdown(profile),
    ]

    if "incident_type" in df.columns:
        top_incident = df["incident_type"].value_counts(dropna=False)
        if not top_incident.empty:
            sections.append(
                "## Incident composition\n"
                f"The most common incident type is **{top_incident.index[0]}**, "
                f"with **{fmt_num(top_incident.iloc[0])} incidents** "
                f"({pct(top_incident.iloc[0] / len(df))} of rows).\n\n"
                + df_to_markdown(tables.get("top_incident_type", pd.DataFrame()), max_rows=TOP_N)
            )

    if "property_use" in df.columns and "top_property_use" in tables:
        top_property = df["property_use"].value_counts(dropna=False)
        sections.append(
            "## Property-use context\n"
            f"The leading property-use category is **{top_property.index[0]}**, "
            f"representing **{pct(top_property.iloc[0] / len(df))}** of incident rows.\n\n"
            + df_to_markdown(tables["top_property_use"], max_rows=TOP_N)
        )

    if "numeric_summary" in tables:
        sections.append("## Severity and response summary\n" + df_to_markdown(tables["numeric_summary"], max_rows=20))

    if "loss_by_incident_type" in tables:
        loss_tbl = tables["loss_by_incident_type"].copy()
        if not loss_tbl.empty:
            top_loss_type = loss_tbl.iloc[0]["incident_type"]
            total_loss = pd.to_numeric(df.get("total_loss", pd.Series(dtype=float)), errors="coerce").sum()
            top_loss_share = loss_tbl.iloc[0]["total_loss"] / total_loss if total_loss > 0 else np.nan
            sections.append(
                "## Loss concentration\n"
                f"Recorded loss is usually highly concentrated. In this dataset, the incident type contributing "
                f"the largest total loss is **{top_loss_type}**, contributing approximately **{pct(top_loss_share)}** "
                f"of total recorded loss.\n\n"
                + df_to_markdown(loss_tbl, max_rows=TOP_N)
            )

    if "peak_day_hour_windows" in tables:
        sections.append("## Peak temporal windows\n" + df_to_markdown(tables["peak_day_hour_windows"], max_rows=10))


    geo_key = choose_geo_key(df, cfg.geo_key_candidates)
    if geo_key:
        geo = aggregate_incidents_to_geography(df, geo_key, feature_groups)
        if not geo.empty:
            geo_target = main_risk_target(geo) or "incident_count"
            top_geo = top_geographies_table(geo, cfg, geo_target, top_n=10)
            if not top_geo.empty:
                sections.append(
                    "## Incident-level geographic hotspot check\n"
                    f"This is a quick aggregation of the incident-level data by `{geo_key}`. For final geographic "
                    "risk analysis, use the dedicated block-group and tract datasets because they are already "
                    "constructed at the correct unit of analysis.\n\n"
                    + df_to_markdown(top_geo, max_rows=10)
                )

    sections.append(
        "## Suggested discussion points\n"
        "- Separate **frequency** questions from **severity** questions. The most common incident categories are not always the largest loss drivers.\n"
        "- Use response-time and resource-use summaries to discuss operational burden, but avoid interpreting them as causal without dispatch context.\n"
        "- Do not use repeated incident-level census/SVI/NSI covariates for naive row-level socioeconomic correlations. Prefer block-group or tract-level analysis for risk-factor interpretation."
    )
    return sections



def plot_geographic_level(
    df: pd.DataFrame,
    cfg: DatasetConfig,
    feature_groups: Dict[str, List[str]],
    feature_def_map: Dict[str, str],
    out_dir: Path,
) -> pd.DataFrame:
    geo_key = choose_geo_key(df, cfg.geo_key_candidates)
    target = main_risk_target(df)

    if "incident_count" in df.columns:
        save_hist(
            df["incident_count"],
            out_dir,
            "01_incident_count_distribution.png",
            "Distribution of Incident Counts Across Geographies",
            "Incident count",
            bins=40,
            clip_upper_q=0.99,
        )

    for col, name in [
        ("incidents_per_1000_pop", "02_incidents_per_1000_population_distribution.png"),
        ("incidents_per_1000_structures", "03_incidents_per_1000_structures_distribution.png"),
        ("incidents_per_sqmi", "04_incidents_per_square_mile_distribution.png"),
        ("estimated_loss_per_1000_structures", "05_estimated_loss_per_1000_structures_distribution.png"),
    ]:
        if col in df.columns:
            save_hist(
                df[col],
                out_dir,
                name,
                f"Distribution of {col}",
                col,
                bins=40,
                clip_upper_q=0.99,
            )

    if target:
        top_geo = top_geographies_table(df, cfg, target, top_n=TOP_N)
        if not top_geo.empty:
            s = top_geo.set_index("geography_label")[target]
            save_barh(
                s,
                out_dir,
                f"06_top_geographies_by_{clean_filename(target)}.png",
                f"Top Geographies by {target}",
                target,
                geo_key or "geography",
            )

    # Exposure relationships.
    for x_col in ["p_total", "structures_count", "rpl_overall_t", "avg_median_year_built", "avg_structure_value"]:
        if target and x_col in df.columns:
            save_scatter(
                df,
                x_col,
                target,
                out_dir,
                f"07_scatter_{clean_filename(x_col)}_vs_{clean_filename(target)}.png",
                f"{target} vs {x_col}",
                xlabel=x_col,
                ylabel=target,
                log_x=x_col in {"p_total", "structures_count"},
            )

    if {"p_total", "incident_count"}.issubset(df.columns):
        save_scatter(
            df,
            "p_total",
            "incident_count",
            out_dir,
            "08_population_vs_incident_count.png",
            "Incident Count vs Population Exposure",
            xlabel="Population",
            ylabel="Incident count",
            log_x=True,
            log_y=True,
        )

    if {"structures_count", "incident_count"}.issubset(df.columns):
        save_scatter(
            df,
            "structures_count",
            "incident_count",
            out_dir,
            "09_structures_vs_incident_count.png",
            "Incident Count vs Structure Exposure",
            xlabel="Structures count",
            ylabel="Incident count",
            log_x=True,
            log_y=True,
        )

    corr_df = spearman_correlations(df, cfg.level, feature_groups, feature_def_map)
    if not corr_df.empty and target:
        target_corr = corr_df[corr_df["target"] == target].sort_values("abs_corr", ascending=False).head(15)
        if not target_corr.empty:
            s = target_corr.set_index("feature")["spearman_corr"].sort_values()
            plt.figure(figsize=(10, max(4, 0.45 * len(s) + 1.5)))
            plt.barh(s.index.astype(str), s.values)
            plt.axvline(0, linewidth=1)
            plt.title(f"Top Spearman Correlations with {target}")
            plt.xlabel("Spearman correlation")
            plt.ylabel("Feature")
            save_current_fig(out_dir, f"10_top_correlations_with_{clean_filename(target)}.png")

            # Scatter plots for the strongest few correlates.
            for _, row in target_corr.head(6).iterrows():
                feature = row["feature"]
                save_scatter(
                    df,
                    feature,
                    target,
                    out_dir,
                    f"11_scatter_{clean_filename(feature)}_vs_{clean_filename(target)}.png",
                    f"{target} vs {feature}",
                    xlabel=readable_feature_name(feature, feature_def_map, max_chars=70),
                    ylabel=target,
                )

    # Compact heatmap among major outcomes and interpretable predictors.
    heat_cols = []
    for col in [
        "incident_count", "incidents_per_1000_pop", "incidents_per_1000_structures", "incidents_per_sqmi",
        "estimated_loss_per_1000_structures", "p_total", "structures_count", "rpl_overall_t",
        "ep_pov150", "ep_unemp", "ep_limeng", "avg_median_year_built", "avg_structure_value",
    ]:
        if col in df.columns and pd.to_numeric(df[col], errors="coerce").nunique(dropna=True) > 1:
            heat_cols.append(col)
    if len(heat_cols) >= 3:
        corr = df[heat_cols].apply(pd.to_numeric, errors="coerce").corr(method="spearman")
        save_correlation_heatmap(corr, out_dir, "12_key_variable_spearman_heatmap.png", "Spearman Correlation Among Key Variables")

    return corr_df


def geographic_report_sections(
    df: pd.DataFrame,
    cfg: DatasetConfig,
    feature_groups: Dict[str, List[str]],
    feature_def_map: Dict[str, str],
    out_dir: Path,
) -> List[str]:
    tables = build_geo_summary_tables(df, cfg, feature_groups, feature_def_map)
    for name, table in tables.items():
        save_table_if_enabled(table, out_dir, name)

    profile = data_profile(df, cfg, feature_groups)
    sections = [
        "## Dataset profile\n" + df_to_markdown(profile),
    ]

    if "outcome_summary" in tables:
        sections.append("## Fire-risk outcome summary\n" + df_to_markdown(tables["outcome_summary"], max_rows=25))

    target = main_risk_target(df)
    if target:
        top_key = f"top_geographies_by_{target}"
        if top_key in tables:
            sections.append(
                f"## Highest-risk geographies by `{target}`\n"
                "These are useful for hotspot interpretation. Use normalized rates alongside raw incident counts "
                "so that large-population or high-structure areas do not mechanically dominate the analysis.\n\n"
                + df_to_markdown(tables[top_key], max_rows=TOP_N)
            )

    if "top_spearman_correlations" in tables:
        corr = tables["top_spearman_correlations"].copy()
        if not corr.empty:
            sections.append(
                "## Strongest exploratory feature relationships\n"
                "The table below reports Spearman rank correlations between risk outcomes and ACS/SVI/NSI predictors. "
                "These are descriptive associations, not causal estimates. For publication-quality inference, add spatial controls, "
                "exposure offsets, and train/test validation.\n\n"
                + df_to_markdown(corr[["target", "feature", "spearman_corr", "n", "feature_definition"]], max_rows=25)
            )

    if "high_vs_low_risk_feature_comparison" in tables:
        comp = tables["high_vs_low_risk_feature_comparison"].copy()
        if not comp.empty:
            sections.append(
                "## High-risk versus low-risk geography comparison\n"
                "This compares feature averages in the top quartile of geographic risk against the bottom quartile. "
                "Large standardized differences identify features worth investigating further.\n\n"
                + df_to_markdown(
                    comp[[
                        "feature", "target", "low_risk_mean_feature", "high_risk_mean_feature",
                        "standardized_difference", "feature_definition",
                    ]],
                    max_rows=25,
                )
            )

    sections.append(
        "## Suggested discussion points\n"
        "- Interpret raw `incident_count` as **fire burden** and normalized rates as **relative risk**. Both are useful, but they answer different questions.\n"
        "- Population, structure count, and land area are exposure variables. Always check whether a relationship persists after normalizing by exposure.\n"
        "- SVI and ACS variables should be treated as neighborhood vulnerability indicators. They may explain where fire risk overlaps with social vulnerability, but not necessarily why fires occur.\n"
        "- NSI/building variables help connect incident risk to the built environment: density, occupancy mix, building age, structure value, and residential/commercial composition."
    )
    return sections



def try_parse_wkb_centroids(df: pd.DataFrame, geom_candidates: Sequence[str]) -> Optional[pd.DataFrame]:
    geom_col = first_existing(geom_candidates, df)
    if geom_col is None:
        return None
    try:
        from shapely import wkb
    except ImportError:
        return None

    rows = []
    for idx, value in df[geom_col].items():
        try:
            if pd.isna(value):
                rows.append((idx, np.nan, np.nan))
                continue
            geom = wkb.loads(bytes.fromhex(str(value)))
            centroid = geom.centroid
            rows.append((idx, centroid.x, centroid.y))
        except Exception:
            rows.append((idx, np.nan, np.nan))
    coords = pd.DataFrame(rows, columns=["_index", "lon", "lat"]).set_index("_index")
    coords = coords.dropna()
    if coords.empty:
        return None
    return coords


def plot_optional_map(df: pd.DataFrame, cfg: DatasetConfig, out_dir: Path) -> None:
    coords = try_parse_wkb_centroids(
        df,
        geom_candidates=("geom", "geom_block_group", "tract_geom", "geom_32616", "geom_32616_block_group", "tract_geom_32616"),
    )
    if coords is None or coords.empty:
        return

    work = df.loc[coords.index].copy()
    work = pd.concat([work, coords], axis=1)
    size_col = "incident_count" if "incident_count" in work.columns else None
    sizes = pd.Series(20, index=work.index)
    if size_col:
        raw = pd.to_numeric(work[size_col], errors="coerce").fillna(0)
        if raw.max() > raw.min():
            sizes = 20 + 180 * (raw - raw.min()) / (raw.max() - raw.min())

    plt.figure(figsize=(7, 7))
    plt.scatter(work["lon"], work["lat"], s=sizes, alpha=0.65)
    plt.title(f"Spatial Distribution: {cfg.name}")
    plt.xlabel("Longitude or projected X")
    plt.ylabel("Latitude or projected Y")
    save_current_fig(out_dir, "13_spatial_distribution.png")



def analyze_dataset(cfg: DatasetConfig, feature_defs: Dict[str, pd.DataFrame]) -> Optional[pd.DataFrame]:
    out_dir = ensure_dir(OUTPUT_ROOT / cfg.name)

    if not cfg.path.exists():
        msg = (
            f"# {cfg.name}\n\n"
            f"Input file not found: `{cfg.path}`.\n\n"
            "Check that the script is being run from the project root and that the `data/` folder contains the expected file.\n"
        )
        (out_dir / "summary_report.md").write_text(msg, encoding="utf-8")
        print(f"Skipping {cfg.name}: file not found at {cfg.path}")
        return None

    print(f"Analyzing {cfg.name}: {cfg.path}")
    df = load_dataset(cfg.path)
    feature_def_map = feature_map_for_sheet(feature_defs, cfg.feature_sheet)

    if cfg.level == "incident":
        df = add_incident_derived_features(df)
    else:
        df = add_geographic_derived_features(df)

    feature_groups = identify_feature_groups(df)

    if cfg.level == "incident":
        plot_incident_level(df, out_dir)
        plot_optional_map(df, cfg, out_dir)
        sections = incident_report_sections(df, cfg, feature_groups, feature_def_map, out_dir)
    else:
        plot_geographic_level(df, cfg, feature_groups, feature_def_map, out_dir)
        plot_optional_map(df, cfg, out_dir)
        sections = geographic_report_sections(df, cfg, feature_groups, feature_def_map, out_dir)

    write_report(out_dir, f"Chicago Fire Analysis: {cfg.name}", sections)
    print(f"  Wrote report and figures to {out_dir}")
    return df


def cross_level_summary(results: Dict[str, pd.DataFrame]) -> None:
    out_dir = ensure_dir(OUTPUT_ROOT / "combined")
    lines = ["# Cross-level Summary"]

    rows = []
    for name, df in results.items():
        if df is None:
            continue
        row = {"dataset": name, "rows": len(df), "columns": df.shape[1]}
        if "incident_count" in df.columns:
            row["total_incidents_represented"] = pd.to_numeric(df["incident_count"], errors="coerce").sum()
            row["mean_incident_count"] = pd.to_numeric(df["incident_count"], errors="coerce").mean()
        elif "incident_key" in df.columns:
            row["total_incidents_represented"] = df["incident_key"].nunique(dropna=True)
            row["mean_incident_count"] = np.nan
        if "p_total" in df.columns:
            row["total_population"] = pd.to_numeric(df["p_total"], errors="coerce").sum()
        if "structures_count" in df.columns:
            row["total_structures"] = pd.to_numeric(df["structures_count"], errors="coerce").sum()
        rows.append(row)

    summary = pd.DataFrame(rows)
    lines.append("## Dataset scale comparison\n" + df_to_markdown(summary, max_rows=10))

    lines.append(
        "## How to use the three files together\n"
        "- Use the **incident-level file** to study incident composition, temporal patterns, response times, property use, and loss concentration.\n"
        "- Use the **block-group file** to study fine-grained neighborhood risk and relationships with ACS/SVI/NSI features.\n"
        "- Use the **tract file** to study smoother, more stable spatial patterns. Tracts reduce noise but may hide within-tract heterogeneity.\n"
        "- Prefer normalized rates, such as incidents per 1,000 population or per 1,000 structures, when linking risk to census and building features.\n"
    )

    (out_dir / "cross_level_summary.md").write_text("\n\n".join(lines) + "\n", encoding="utf-8")

    # Optional comparison plot for aggregate files.
    comparable = []
    for name, df in results.items():
        if df is not None and "incident_count" in df.columns:
            x = pd.to_numeric(df["incident_count"], errors="coerce").dropna()
            if not x.empty:
                comparable.append((name, x))
    if comparable:
        plt.figure(figsize=(9, 5))
        labels = [name for name, _ in comparable]
        data = [x.clip(upper=x.quantile(0.99)) for _, x in comparable]
        plt.boxplot(data, labels=labels, vert=True, showfliers=False)
        plt.title("Incident Count Distribution by Aggregation Level")
        plt.ylabel("Incident count, clipped at p99")
        plt.xticks(rotation=25, ha="right")
        save_current_fig(out_dir, "incident_count_distribution_by_level.png")



def main() -> None:
    warnings.filterwarnings("ignore", category=FutureWarning)
    ensure_dir(OUTPUT_ROOT)

    feature_defs = load_feature_definitions(FEATURE_DEF_PATH)
    configs = resolve_datasets()

    print("Starting Chicago fire data analysis.")
    print(f"Output root: {OUTPUT_ROOT.resolve()}")

    results: Dict[str, pd.DataFrame] = {}
    for cfg in configs:
        result = analyze_dataset(cfg, feature_defs)
        if result is not None:
            results[cfg.name] = result

    if results:
        cross_level_summary(results)
        print("\nAnalysis complete.")
        print(f"Reports and figures are in: {OUTPUT_ROOT.resolve()}")
        print("Main files to open:")
        for cfg_name in results:
            print(f"  - {OUTPUT_ROOT / cfg_name / 'summary_report.md'}")
        print(f"  - {OUTPUT_ROOT / 'combined' / 'cross_level_summary.md'}")
    else:
        print("\nNo datasets were analyzed. Check the configured input paths in the DATASETS section.")


if __name__ == "__main__":
    main()
