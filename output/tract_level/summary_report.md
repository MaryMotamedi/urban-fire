# Chicago Fire Analysis: tract_level

## Dataset profile
```text
                       Metric     Value
                         Rows     948.0
                      Columns     504.0
              Numeric columns     499.0
  ACS/census columns detected     307.0
         SVI columns detected      71.0
NSI/building columns detected      36.0
          Unique tract_geo_id     948.0
  Total incidents represented   93245.0
 Total population represented 3450835.0
 Total structures represented  831241.0
```

## Fire-risk outcome summary
```text
                          variable   n       mean     median       p25        p75         p95          max
                    incident_count 948     98.360     75.000    41.000    126.250     273.000      670.000
            incidents_per_1000_pop 945     33.173     21.219    13.480     42.097      92.738      382.483
     incidents_per_1000_structures 948    215.320    100.863    56.597    250.793     661.660     8000.000
                incidents_per_sqmi 948      0.000      0.000     0.000      0.000       0.000        0.002
                    avg_total_loss 948   4508.747   2467.019   875.320   4513.937   13364.971   141904.915
              estimated_total_loss 948 479983.608 188801.159 49992.671 463574.202 1514453.758 16070679.054
       estimated_loss_per_1000_pop 945 160962.646  58426.474 16131.930 155183.051  580332.753  8460645.436
estimated_loss_per_1000_structures 948 775303.111 276056.403 93190.672 715240.170 2533372.369 53812145.749
               avg_total_personnel 948      2.720      2.278     1.705      3.051       5.986       29.500
               avg_total_apparatus 948      4.362      4.347     3.486      5.219       6.774       29.500
          avg_firefighter_injuries 948      0.010      0.000     0.000      0.012       0.035        1.000
                avg_other_injuries 948      0.009      0.000     0.000      0.014       0.033        0.125
        avg_firefighter_fatalities 948      0.000      0.000     0.000      0.000       0.000        0.005
              avg_other_fatalities 948      0.002      0.000     0.000      0.000       0.014        0.111
```

## Highest-risk geographies by `incidents_per_1000_structures`
These are useful for hotspot interpretation. Use normalized rates alongside raw incident counts so that large-population or high-structure areas do not mechanically dominate the analysis.

```text
geography_label  incidents_per_1000_structures  incident_count  p_total  structures_count  estimated_total_loss  avg_total_loss  rpl_overall_t
    17031980100                    8000.000000              72      0.0                 9          5.186812e+04      720.390625            NaN
    17031350100                    6388.888889             115   2421.0                18          2.398527e+05     2085.675926         0.3558
    17031350400                    3846.153846             100   1875.0                26          1.197800e+05     1197.800000         0.9284
    17031340600                    3275.862069             190   1139.0                58          4.264422e+04      224.443243         0.9145
    17031400300                    2621.468927             464   1304.0               177          5.342886e+05     1151.483945         0.9340
    17031030706                    2000.000000             140   2965.0                70          1.367025e+04       97.644628         0.7120
    17031061902                    1833.333333             187   4745.0               102          1.842622e+05      985.359551         0.3099
    17031420100                    1771.929825             101   1519.0                57          5.510604e+04      545.604396         0.8657
    17031030604                    1600.000000              96   3221.0                60          6.171733e+04      642.888889         0.6281
    17031838100                    1502.487562             302   1797.0               201          2.120556e+06     7021.709343         0.8616
    17031390300                    1496.688742             226   2815.0               151          2.356726e+05     1042.799087         0.9550
    17031320600                    1422.818792             212   5370.0               149          2.882192e+05     1359.524324         0.2673
    17031381700                    1333.333333               8      0.0                 6          0.000000e+00        0.000000            NaN
    17031390700                    1329.670330             242   5640.0               182          1.557218e+05      643.478448         0.4912
    17031351100                    1181.818182              78   2229.0                66          4.177915e+04      535.630137         0.8865
```

## Strongest exploratory feature relationships
The table below reports Spearman rank correlations between risk outcomes and ACS/SVI/NSI predictors. These are descriptive associations, not causal estimates. For publication-quality inference, add spatial controls, exposure offsets, and train/test validation.

```text
                       target                  feature  spearman_corr   n feature_definition
incidents_per_1000_structures                 ep_noveh       0.758923 945                   
incidents_per_1000_structures             epl_noveh_t4       0.758923 945                   
           incidents_per_sqmi             epl_noveh_t4       0.745650 945                   
           incidents_per_sqmi                 ep_noveh       0.745648 945                   
incidents_per_1000_structures count_occupancy_type_res      -0.684612 948                   
incidents_per_1000_structures count_structure_source_p      -0.679236 948                   
incidents_per_1000_structures         structures_count      -0.674614 948                   
incidents_per_1000_structures               f_noveh_t4       0.669235 945                   
incidents_per_1000_structures  count_foundation_type_b      -0.656914 948                   
           incidents_per_sqmi          tract_area_sqmi      -0.648023 948                   
           incidents_per_sqmi                land_area      -0.648023 948                   
           incidents_per_sqmi               f_noveh_t4       0.643758 945                   
       incidents_per_1000_pop           p_not_hl_white      -0.635612 945                   
incidents_per_1000_structures            sf_housing_t4       0.627174 945                   
       incidents_per_1000_pop       p_not_hl_white_moe      -0.624821 945                   
           incidents_per_sqmi         structures_count      -0.589801 948                   
       incidents_per_1000_pop                ep_minrty       0.584559 945                   
       incidents_per_1000_pop            rpl_minrty_t3       0.584559 945                   
       incidents_per_1000_pop            epl_minrty_t3       0.584559 945                   
       incidents_per_1000_pop            spl_minrty_t3       0.584559 945                   
           incidents_per_sqmi count_occupancy_type_res      -0.583280 948                   
           incidents_per_sqmi count_structure_source_p      -0.581634 948                   
       incidents_per_1000_pop                  ep_afam       0.564471 945                   
       incidents_per_1000_pop                 ep_noveh       0.563200 945                   
       incidents_per_1000_pop             epl_noveh_t4       0.563199 945                   
```

## High-risk versus low-risk geography comparison
This compares feature averages in the top quartile of geographic risk against the bottom quartile. Large standardized differences identify features worth investigating further.

```text
                 feature                        target  low_risk_mean_feature  high_risk_mean_feature  standardized_difference feature_definition
                ep_noveh incidents_per_1000_structures               9.747458               40.385106                 1.938452                   
count_occupancy_type_res incidents_per_1000_structures            1266.586498              314.088608                -1.748517                   
count_structure_source_p incidents_per_1000_structures            1354.603376              355.599156                -1.740930                   
        structures_count incidents_per_1000_structures            1399.194093              391.189873                -1.728280                   
              f_noveh_t4 incidents_per_1000_structures               0.084746                0.919149                 1.669017                   
 count_foundation_type_b incidents_per_1000_structures            1156.135021              272.329114                -1.664942                   
            epl_noveh_t4 incidents_per_1000_structures               0.614871                0.946670                 1.636857                   
           sf_housing_t4 incidents_per_1000_structures               0.292373                1.672340                 1.614887                   
            sf_overall_t incidents_per_1000_structures               1.224576                4.612766                 1.417649                   
   count_building_type_m incidents_per_1000_structures             783.594937              196.510549                -1.379188                   
           ep_hs_10_plus incidents_per_1000_structures               9.064979               43.520675                 1.353144                   
         f_hs_10_plus_t4 incidents_per_1000_structures               0.033898                0.497872                 1.216403                   
               ep_pov150 incidents_per_1000_structures              18.142194               37.934177                 1.207871                   
   count_building_type_w incidents_per_1000_structures             435.987342              142.932489                -1.197516                   
   avg_foundation_height incidents_per_1000_structures               1.773141                1.432805                -1.186495                   
                ep_hburd incidents_per_1000_structures              27.248945               42.606751                 1.167099                   
           epl_pov150_t1 incidents_per_1000_structures               0.418833                0.743762                 1.159264                   
                 ep_afam incidents_per_1000_structures              12.294915               55.886383                 1.156495                   
            epl_hburd_t1 incidents_per_1000_structures               0.513428                0.806915                 1.122753                   
          spl_housing_t4 incidents_per_1000_structures               2.047703                2.808669                 1.088844                   
          rpl_housing_t4 incidents_per_1000_structures               0.433746                0.701840                 1.073911                   
           avg_num_story incidents_per_1000_structures               1.499685                2.115537                 1.055834                   
       epl_hs_10_plus_t4 incidents_per_1000_structures               0.481686                0.796377                 1.052409                   
                avg_sqft incidents_per_1000_structures            2955.419390             8181.227894                 1.023931                   
  avg_ground_elevation_m incidents_per_1000_structures             192.187006              181.742310                -1.023110                   
```

## Suggested discussion points
- Interpret raw `incident_count` as **fire burden** and normalized rates as **relative risk**. Both are useful, but they answer different questions.
- Population, structure count, and land area are exposure variables. Always check whether a relationship persists after normalizing by exposure.
- SVI and ACS variables should be treated as neighborhood vulnerability indicators. They may explain where fire risk overlaps with social vulnerability, but not necessarily why fires occur.
- NSI/building variables help connect incident risk to the built environment: density, occupancy mix, building age, structure value, and residential/commercial composition.
