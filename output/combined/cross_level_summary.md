# Cross-level Summary

## Dataset scale comparison
```text
          dataset  rows  columns  total_incidents_represented  mean_incident_count  total_population  total_structures
   incident_level 93257      555                        93257                  NaN      1.296291e+08        29137836.0
block_group_level  2457      510                        93245            37.950753      3.098592e+06          715927.0
      tract_level   948      504                        93245            98.359705      3.450835e+06          831241.0
```

## How to use the three files together
- Use the **incident-level file** to study incident composition, temporal patterns, response times, property use, and loss concentration.
- Use the **block-group file** to study fine-grained neighborhood risk and relationships with ACS/SVI/NSI features.
- Use the **tract file** to study smoother, more stable spatial patterns. Tracts reduce noise but may hide within-tract heterogeneity.
- Prefer normalized rates, such as incidents per 1,000 population or per 1,000 structures, when linking risk to census and building features.

