# Chicago Fire Analysis: incident_level

## Dataset profile
```text
                       Metric               Value
                         Rows               93257
                      Columns                 555
              Numeric columns                 531
  ACS/census columns detected                 310
         SVI columns detected                  71
NSI/building columns detected                  36
         Unique incident keys               93257
                   Start date 2017-01-01 00:01:00
                     End date 2024-12-31 20:32:00
                Unique geo_id                2457
            Unique tract_code                 946
               Unique station                 167
         Unique incident_type                  41
          Unique property_use                 139
```

## Incident composition
The most common incident type is **Trash or rubbish fire, contained**, with **19,124.0 incidents** (20.5% of rows).

```text
                                  incident_type  count share
               Trash or rubbish fire, contained  19124 20.5%
            Cooking fire, confined to container  16441 17.6%
                         Passenger vehicle fire  13083 14.0%
                                 Building fires  11651 12.5%
           Outside rubbish, trash or waste fire  10616 11.4%
                                    Fire, other   6843  7.3%
                    Outside rubbish fire, other   5787  6.2%
          Mobile property (vehicle) fire, other   2404  2.6%
         Brush, or brush and grass mixture fire   1171  1.3%
Dumpster or other outside trash receptacle fire   1092  1.2%
   Fires in structures other than in a building   1092  1.2%
                                     Grass fire    686  0.7%
         Road freight or transport vehicle fire    561  0.6%
                    Special outside fire, other    432  0.5%
                         Outside equipment fire    355  0.4%
```

## Property-use context
The leading property-use category is **Street, other**, representing **29.8%** of incident rows.

```text
                                    property_use  count share
                                   Street, other  27748 29.8%
                           Multifamily dwellings  19301 20.7%
                          1 or 2 family dwelling  14810 15.9%
Residential street, road or residential driveway   6843  7.3%
               Street or road in commercial area   2724  2.9%
                              Open land or field   2349  2.5%
                      Highway or divided highway   2150  2.3%
                                             NaN   1816  1.9%
                            Vehicle parking area   1741  1.9%
              Outside or special property, other   1561  1.7%
                     Mercantile, business, other   1477  1.6%
   Parking garage, (detached residential garage)   1342  1.4%
                              Residential, other   1200  1.3%
                                      Vacant lot    736  0.8%
                         Restaurant or cafeteria    526  0.6%
```

## Severity and response summary
```text
        variable     n     mean  median  p25  p75     p95        max
response_minutes 93257    4.419     4.0  3.0  5.0     8.0     2885.0
      total_loss 93257 4199.668     0.0  0.0  0.0 10000.0 13000000.0
   property_loss 82524 3453.518     0.0  0.0  0.0 10000.0 12000000.0
   contents_loss 82487 1292.935     0.0  0.0  0.0  2000.0  5000000.0
 total_personnel 93257    2.443     1.0  0.0  3.0    14.0       91.0
 total_apparatus 93257    4.440     2.0  1.0  5.0    16.0      466.0
  total_injuries 93257    0.019     0.0  0.0  0.0     0.0       15.0
total_fatalities 93257    0.002     0.0  0.0  0.0     0.0        8.0
```

## Loss concentration
Recorded loss is usually highly concentrated. In this dataset, the incident type contributing the largest total loss is **Building fires**, contributing approximately **62.9%** of total recorded loss.

```text
                                     incident_type  incidents  total_loss    mean_loss  positive_loss_rate
                                    Building fires      11651 246504364.0 21157.356793            0.407175
                                       Fire, other       6843  59186763.0  8649.241999            0.273564
                            Passenger vehicle fire      13083  55239445.0  4222.230757            0.339219
             Mobile property (vehicle) fire, other       2404   7365365.0  3063.795757            0.324875
                            Outside equipment fire        355   5205080.0 14662.197183            0.107042
      Fires in structures other than in a building       1092   4838083.0  4430.478938            0.342491
            Road freight or transport vehicle fire        561   3415352.0  6087.971480            0.126560
                                 Rail vehicle fire         53   2160000.0 40754.716981            0.075472
          Off-road vehicle or heavy equipment fire         61   1987000.0 32573.770492            0.327869
                  Trash or rubbish fire, contained      19124   1900616.0    99.383811            0.076762
               Cooking fire, confined to container      16441   1429374.0    86.939602            0.129372
            Brush, or brush and grass mixture fire       1171   1038069.0   886.480786            0.021349
Fire in mobile prop. used as a fixed struc., other        137    273578.0  1996.919708            0.211679
     Fuel burner/boiler malfunction, fire confined        316    180931.0   572.566456            0.205696
 Chimney or flue fire, confined to chimney or flue        287    139075.0   484.581882            0.174216
```

## Peak temporal windows
```text
day_of_week  hour  incident_count
     Sunday    18             942
     Sunday    19             922
     Sunday    21             908
     Sunday    17             899
     Sunday    20             870
   Saturday    18             860
     Monday    18             841
     Sunday    22             841
     Monday    21             837
    Tuesday    20             832
```

## Incident-level geographic hotspot check
This is a quick aggregation of the incident-level data by `geo_id`. For final geographic risk analysis, use the dedicated block-group and tract datasets because they are already constructed at the correct unit of analysis.

```text
                     geography_label  incidents_per_1000_structures  incident_count  p_total  structures_count  estimated_total_loss  avg_total_loss  rpl_overall_t
   Census Tract 313 | 170310313001.0                   14333.333333             172   1618.0              12.0               89180.0      518.488372         0.8105
  Census Tract 3907 | 170313907003.0                   13692.307692             178   2580.0              13.0               73818.0      414.707865         0.4912
  Census Tract 3501 | 170313501002.0                    8750.000000              70   1467.0               8.0              192153.0     2745.042857         0.3558
Census Tract 619.02 | 170310619023.0                    8111.111111             146   1566.0              18.0              174854.0     1197.630137         0.3099
  Census Tract 9801 | 170319801001.0                    8000.000000              72      0.0               9.0               46105.0      640.347222            NaN
  Census Tract 3511 | 170313511001.0                    8000.000000               8      0.0               1.0                1401.0      175.125000         0.8865
Census Tract 307.02 | 170310307021.0                    6500.000000              26    998.0               4.0                5100.0      196.153846         0.6970
   Census Tract 608 | 170310608002.0                    6000.000000               6      0.0               1.0                   0.0        0.000000         0.2676
  Census Tract 3903 | 170313903001.0                    5884.615385             153    947.0              26.0               43823.0      286.424837         0.9550
   Census Tract 609 | 170310609002.0                    5666.666667              17      0.0               3.0                  52.0        3.058824         0.2354
```

## Suggested discussion points
- Separate **frequency** questions from **severity** questions. The most common incident categories are not always the largest loss drivers.
- Use response-time and resource-use summaries to discuss operational burden, but avoid interpreting them as causal without dispatch context.
- Do not use repeated incident-level census/SVI/NSI covariates for naive row-level socioeconomic correlations. Prefer block-group or tract-level analysis for risk-factor interpretation.
