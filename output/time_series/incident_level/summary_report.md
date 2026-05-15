# Time-Series Analysis Report: `incident_level`

Input file: `data\chicago_fires_full_acs_svi_nsi.csv`

Rows: **93,257**  
Columns: **536**

## Detected temporal structure

- Date column/source: **`incident_date`** (existing datetime column)
- Count logic: **one row = one incident/observation**
- Geography column: **`geo_id`**

## Core time-series summary

| series | start | end | periods | total_incidents | mean | median | std | min | max | zero_periods | zero_period_share | variance_to_mean | top_period_share | nonzero_periods |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| Daily | 2017-01-01 | 2024-12-31 | 2922 | 93257 | 31.9155 | 29 | 17.4186 | 0 | 297 | 1 | 0.000342231 | 9.50665 | 0.00318475 | 2921 |
| Weekly | 2017-01-01 | 2025-01-05 | 419 | 93257 | 222.57 | 207 | 75.2285 | 41 | 765 | 0 | 0 | 25.4271 | 0.00820314 | 419 |
| Monthly | 2017-01-01 | 2024-12-01 | 96 | 93257 | 971.427 | 922 | 209.446 | 660 | 1709 | 0 | 0 | 45.1579 | 0.0183257 | 96 |
| Yearly | 2017-01-01 | 2024-01-01 | 8 | 93257 | 11657.1 | 11579.5 | 556.209 | 10765 | 12524 | 0 | 0 | 26.539 | 0.134296 | 8 |

### Main temporal signals

- The observed date range runs from **2017-01-01** to **2024-12-31**.
- Zero-incident days account for **0.0%** of daily periods.
- The daily variance-to-mean ratio is **9.51**. Values above 1 indicate overdispersion/episodic clustering relative to a simple Poisson-like process.
- The highest-count day is **2020-07-05** with **297** incidents.

## Month-of-year seasonality

Highest-count calendar months in the available data:

| month_name | event_count | share_of_total |
| --- | --- | --- |
| July | 11308 | 0.121256 |
| June | 9859 | 0.105719 |
| May | 8593 | 0.0921432 |
| August | 7754 | 0.0831466 |
| September | 7451 | 0.0798975 |

## Day-of-week pattern

| weekday_name | event_count | share_of_total |
| --- | --- | --- |
| Sunday | 15313 | 0.164202 |
| Saturday | 14179 | 0.152042 |
| Monday | 13625 | 0.146102 |
| Tuesday | 12771 | 0.136944 |
| Friday | 12568 | 0.134767 |
| Thursday | 12509 | 0.134135 |
| Wednesday | 12292 | 0.131808 |

## Peak daily periods

| period_start | incident_count | share_of_total |
| --- | --- | --- |
| 2020-07-05 | 297 | 0.095437 |
| 2022-07-04 | 292 | 0.0938303 |
| 2021-07-04 | 290 | 0.0931877 |
| 2020-07-04 | 251 | 0.0806555 |
| 2024-07-04 | 236 | 0.0758355 |
| 2021-07-05 | 233 | 0.0748715 |
| 2023-07-04 | 232 | 0.0745501 |
| 2024-07-05 | 187 | 0.06009 |
| 2017-07-04 | 181 | 0.058162 |
| 2019-07-04 | 171 | 0.0549486 |

## High-count anomaly screen

The table below uses a simple rolling z-score screen. It is exploratory, not a causal event detector.

| date | incident_count | rolling_mean | rolling_std | rolling_z_score |
| --- | --- | --- | --- | --- |
| 2021-07-04 | 290 | 50.4667 | 46.6903 | 5.13026 |
| 2024-07-04 | 236 | 44.4333 | 37.58 | 5.09757 |
| 2020-07-04 | 251 | 51.2667 | 39.4618 | 5.06143 |
| 2019-07-04 | 171 | 37 | 26.8624 | 4.98839 |
| 2018-07-04 | 151 | 37.1667 | 23.1652 | 4.91398 |
| 2022-07-04 | 292 | 51.0333 | 49.4539 | 4.87255 |
| 2023-07-04 | 232 | 49.7333 | 39.0605 | 4.66627 |
| 2020-05-31 | 168 | 38.1667 | 28.2697 | 4.59266 |
| 2018-05-01 | 137 | 37.2333 | 23.0826 | 4.32216 |
| 2017-07-04 | 181 | 49.2667 | 30.6706 | 4.2951 |

## Incident-type temporal composition

A monthly trend figure for the most common incident types is saved in the figures folder.

## Property-use temporal composition

A monthly trend figure for the most common property-use categories is saved in the figures folder.

## Geographic temporal concentration

A monthly heatmap for the highest-burden geographies is saved in the figures folder.

## Generated figures

- `acf_monthly_counts.png`
- `acf_weekly_counts.png`
- `daily_incident_counts.png`
- `day_of_week_pattern.png`
- `geo_monthly_heatmap_top_geographies.png`
- `month_of_year_seasonality.png`
- `monthly_incident_counts.png`
- `monthly_top_incident_types.png`
- `monthly_top_property_uses.png`
- `monthly_top_stations.png`
- `monthly_total_loss.png`
- `stl_monthly_counts.png`
- `stl_weekly_counts.png`
- `weekly_incident_counts.png`
- `yearly_incident_counts.png`
