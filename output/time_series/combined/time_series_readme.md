# Cross-Dataset Time-Series Notes

This folder contains time-series analysis outputs for the incident-level, block-group-level, and tract-level datasets.

## How to interpret the levels

- **Incident level** is the most reliable source for temporal analysis because each row usually corresponds to one incident with an event date/time.
- **Block-group level** is useful for spatially localized temporal risk only if the file keeps a date/year/month dimension. If it is purely cross-sectional, use the incident-level file to construct block-group time series.
- **Tract level** smooths local noise and is useful for broader neighborhood-scale temporal risk, again only if temporal information exists.

## Suggested reporting narrative

1. Start with the incident-level daily/weekly/monthly pattern to describe the overall fire burden over time.
2. Use seasonality figures to discuss whether fire incidents concentrate in particular months, weekdays, or hours.
3. Use incident-type/property-use temporal plots to separate routine confined fires from more severe structural or building-related incidents.
4. Use geographic heatmaps to identify whether high-risk geographies are consistently high over time or spike only in specific periods.
5. For modeling, prefer count models or forecasting models that can handle overdispersion and seasonality, rather than assuming stable independent daily counts.

## Generated dataset reports

- `incident_level`: `output\time_series\incident_level\summary_report.md`
- `block_group_level`: `output\time_series\block_group_level\summary_report.md`
- `tract_level`: `output\time_series\tract_level\summary_report.md`