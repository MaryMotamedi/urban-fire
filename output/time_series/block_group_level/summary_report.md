# Time-Series Analysis Report: `block_group_level`

Input file: `data\chicago_fire_block_groups_full_acs_svi_nsi.csv`

Rows: **2,457**  
Columns: **501**

## Detected temporal structure

- Date column/source: **`avg_contents_value`** (inferred datetime column)
- Count column used for aggregation: **`incident_count`**
- Geography column: **`geo_id`**

## Core time-series summary

| series | start | end | periods | total_incidents | mean | median | std | min | max | zero_periods | zero_period_share | variance_to_mean | top_period_share | nonzero_periods |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| Daily | 1970-01-01 | 1970-01-01 | 1 | 93245 | 93245 | 93245 |  | 93245 | 93245 | 0 | 0 |  | 1 | 1 |
| Weekly | 1970-01-04 | 1970-01-04 | 1 | 93245 | 93245 | 93245 |  | 93245 | 93245 | 0 | 0 |  | 1 | 1 |
| Monthly | 1970-01-01 | 1970-01-01 | 1 | 93245 | 93245 | 93245 |  | 93245 | 93245 | 0 | 0 |  | 1 | 1 |
| Yearly | 1970-01-01 | 1970-01-01 | 1 | 93245 | 93245 | 93245 |  | 93245 | 93245 | 0 | 0 |  | 1 | 1 |

### Main temporal signals

- The observed date range runs from **1970-01-01** to **1970-01-01**.
- Zero-incident days account for **0.0%** of daily periods.
- The highest-count day is **1970-01-01** with **93245** incidents.

## Month-of-year seasonality

Highest-count calendar months in the available data:

| month_name | event_count | share_of_total |
| --- | --- | --- |
| January | 93245 | 1 |

## Day-of-week pattern

| weekday_name | event_count | share_of_total |
| --- | --- | --- |
| Thursday | 93245 | 1 |

## Peak daily periods

| period_start | incident_count | share_of_total |
| --- | --- | --- |
| 1970-01-01 | 93245 | 1 |

## Generated figures

- `daily_incident_counts.png`
- `day_of_week_pattern.png`
- `month_of_year_seasonality.png`
- `monthly_incident_counts.png`
- `monthly_total_loss.png`
- `weekly_incident_counts.png`
- `yearly_incident_counts.png`
