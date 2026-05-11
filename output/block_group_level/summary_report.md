# Chicago Fire Analysis: block_group_level

## Dataset profile
```text
                       Metric        Value
                         Rows 2.457000e+03
                      Columns 5.100000e+02
              Numeric columns 5.030000e+02
  ACS/census columns detected 3.090000e+02
         SVI columns detected 7.100000e+01
NSI/building columns detected 3.600000e+01
                Unique geo_id 2.457000e+03
  Total incidents represented 9.324500e+04
 Total population represented 3.098592e+06
 Total structures represented 7.159270e+05
```

## Fire-risk outcome summary
```text
                          variable    n       mean     median       p25        p75         p95          max
                    incident_count 2457     37.951     26.000    15.000     44.000     104.000      635.000
            incidents_per_1000_pop 2451     34.244     20.926    12.269     40.728     100.967      684.670
     incidents_per_1000_structures 2457    234.507     99.338    52.731    218.232     689.738    14333.333
                incidents_per_sqmi 2457      0.000      0.000     0.000      0.000       0.001        0.003
                    avg_total_loss 2457   4882.587   1784.615   445.000   4543.000   16250.900   417666.667
              estimated_total_loss 2457 185986.120  52920.000  9750.968 151652.174  628939.325 15674061.699
       estimated_loss_per_1000_pop 2451 177524.391  44382.589  8059.529 139725.705  598686.788 20226297.540
estimated_loss_per_1000_structures 2457 784135.311 203216.019 41982.380 609621.816 2707149.663 98547544.022
               avg_total_personnel 2457      2.833      2.348     1.562      3.429       6.540       29.500
               avg_total_apparatus 2457      4.571      4.376     3.316      5.588       7.805       29.500
          avg_firefighter_injuries 2457      0.009      0.000     0.000      0.000       0.053        1.000
                avg_other_injuries 2457      0.010      0.000     0.000      0.000       0.056        0.889
        avg_firefighter_fatalities 2457      0.000      0.000     0.000      0.000       0.000        0.015
              avg_other_fatalities 2457      0.002      0.000     0.000      0.000       0.014        0.364
```

## Highest-risk geographies by `incidents_per_1000_structures`
These are useful for hotspot interpretation. Use normalized rates alongside raw incident counts so that large-population or high-structure areas do not mechanically dominate the analysis.

```text
                    geography_label  incidents_per_1000_structures  incident_count     p_total  structures_count  estimated_total_loss  avg_total_loss  rpl_overall_t
    Census Tract 313 | 170310313001                   14333.333333             172 1508.075581                12          9.353024e+04      543.780488         0.8105
   Census Tract 3907 | 170313907003                   13692.307692             178 2305.606742                13          7.639305e+04      429.174419         0.4912
   Census Tract 3501 | 170313501002                    8750.000000              70 1532.442857                 8          2.037986e+05     2911.409091         0.3558
 Census Tract 619.02 | 170310619023                    8111.111111             146 1568.198630                18          1.849905e+05     1267.057971         0.3099
   Census Tract 9801 | 170319801001                    8000.000000              72    0.000000                 9          5.186812e+04      720.390625            NaN
   Census Tract 3511 | 170313511001                    8000.000000               8  785.000000                 1          1.868000e+03      233.500000         0.8865
 Census Tract 307.02 | 170310307021                    6500.000000              26  927.692308                 4          5.100000e+03      196.153846         0.6970
    Census Tract 608 | 170310608002                    6000.000000               6    0.000000                 1          0.000000e+00        0.000000         0.2676
   Census Tract 3903 | 170313903001                    5884.615385             153  984.267974                26          4.382300e+04      286.424837         0.9550
    Census Tract 609 | 170310609002                    5666.666667              17    0.000000                 3          5.893333e+01        3.466667         0.2354
   Census Tract 8381 | 170318381001                    4800.000000              48  729.166667                10          6.820000e+02       14.208333         0.8616
   Census Tract 3501 | 170313501001                    4500.000000              45  856.400000                10          3.546429e+04      788.095238         0.3558
   Census Tract 3504 | 170313504001                    3846.153846             100 1875.100000                26          1.197800e+05     1197.800000         0.9284
Census Tract 5401.02 | 170315401021                    3679.245283             390 1100.658974               106          2.201307e+06     5644.377660         0.8100
   Census Tract 3510 | 170313510002                    3636.363636              40  854.525000                11          9.466667e+04     2366.666667         0.4950
```

## Strongest exploratory feature relationships
The table below reports Spearman rank correlations between risk outcomes and ACS/SVI/NSI predictors. These are descriptive associations, not causal estimates. For publication-quality inference, add spatial controls, exposure offsets, and train/test validation.

```text
                       target                  feature  spearman_corr    n feature_definition
incidents_per_1000_structures                 ep_noveh       0.708401 2454                   
incidents_per_1000_structures             epl_noveh_t4       0.708401 2454                   
           incidents_per_sqmi             epl_noveh_t4       0.684704 2454                   
           incidents_per_sqmi                 ep_noveh       0.684702 2454                   
incidents_per_1000_structures count_occupancy_type_res      -0.621878 2457                   
incidents_per_1000_structures               f_noveh_t4       0.619311 2454                   
incidents_per_1000_structures  count_foundation_type_b      -0.612608 2457                   
incidents_per_1000_structures count_structure_source_p      -0.596853 2457                   
incidents_per_1000_structures            sf_housing_t4       0.595585 2454                   
           incidents_per_sqmi               f_noveh_t4       0.591583 2454                   
incidents_per_1000_structures         structures_count      -0.584647 2457                   
incidents_per_1000_structures        avg_vehicle_value       0.559652 2457                   
incidents_per_1000_structures    count_building_type_m      -0.552619 2457                   
           incidents_per_sqmi          tract_area_sqmi      -0.548017 2457                   
       incidents_per_1000_pop                  ep_afam       0.547265 2451                   
incidents_per_1000_structures                 avg_sqft       0.545385 2457                   
       incidents_per_1000_pop           p_not_hl_white      -0.541547 2451                   
           incidents_per_sqmi             bg_land_area      -0.539976 2457                   
       incidents_per_1000_pop       p_not_hl_white_moe      -0.537852 2451                   
       incidents_per_1000_pop                ep_minrty       0.534145 2451                   
       incidents_per_1000_pop            rpl_minrty_t3       0.534145 2451                   
       incidents_per_1000_pop            epl_minrty_t3       0.534145 2451                   
       incidents_per_1000_pop            spl_minrty_t3       0.534145 2451                   
               incident_count           p_not_hl_black       0.532864 2457                   
incidents_per_1000_structures             sf_overall_t       0.524095 2454                   
```

## High-risk versus low-risk geography comparison
This compares feature averages in the top quartile of geographic risk against the bottom quartile. Large standardized differences identify features worth investigating further.

```text
                 feature                        target  low_risk_mean_feature  high_risk_mean_feature  standardized_difference feature_definition
                ep_noveh incidents_per_1000_structures              10.779967               39.540783                 1.869140                   
              f_noveh_t4 incidents_per_1000_structures               0.112378                0.915171                 1.605894                   
           sf_housing_t4 incidents_per_1000_structures               0.288274                1.626427                 1.564120                   
            epl_noveh_t4 incidents_per_1000_structures               0.657950                0.946704                 1.563656                   
 count_foundation_type_b incidents_per_1000_structures             343.297561              117.695935                -1.548850                   
count_occupancy_type_res incidents_per_1000_structures             359.578862              135.395122                -1.543362                   
count_structure_source_p incidents_per_1000_structures             380.453659              154.777236                -1.453178                   
        structures_count incidents_per_1000_structures             389.382114              168.770732                -1.388770                   
   count_building_type_m incidents_per_1000_structures             248.780488               86.061789                -1.344130                   
            sf_overall_t incidents_per_1000_structures               1.260586                4.358891                 1.322914                   
   avg_foundation_height incidents_per_1000_structures               1.839477                1.417237                -1.319474                   
           ep_hs_10_plus incidents_per_1000_structures               8.920163               42.995610                 1.299723                   
         f_hs_10_plus_t4 incidents_per_1000_structures               0.026059                0.482871                 1.203846                   
               ep_pov150 incidents_per_1000_structures              17.667805               36.107317                 1.172109                   
                ep_hburd incidents_per_1000_structures              27.778049               42.389919                 1.137697                   
          spl_housing_t4 incidents_per_1000_structures               2.090295                2.842947                 1.106395                   
          rpl_housing_t4 incidents_per_1000_structures               0.443549                0.714501                 1.100541                   
           epl_pov150_t1 incidents_per_1000_structures               0.419419                0.720478                 1.093777                   
                 ep_afam incidents_per_1000_structures              11.582410               52.900163                 1.083046                   
            epl_hburd_t1 incidents_per_1000_structures               0.528257                0.796010                 1.059070                   
          p_not_hl_black incidents_per_1000_structures             133.340582              600.088536                 1.014946                   
       epl_hs_10_plus_t4 incidents_per_1000_structures               0.499676                0.791130                 1.002993                   
         p_itpr_under_50 incidents_per_1000_structures              49.725141              153.135008                 1.002469                   
                 m_noveh incidents_per_1000_structures              90.988618              194.508943                 0.997736                   
  avg_ground_elevation_m incidents_per_1000_structures             189.023350              181.807894                -0.993586                   
```

## Suggested discussion points
- Interpret raw `incident_count` as **fire burden** and normalized rates as **relative risk**. Both are useful, but they answer different questions.
- Population, structure count, and land area are exposure variables. Always check whether a relationship persists after normalizing by exposure.
- SVI and ACS variables should be treated as neighborhood vulnerability indicators. They may explain where fire risk overlaps with social vulnerability, but not necessarily why fires occur.
- NSI/building variables help connect incident risk to the built environment: density, occupancy mix, building age, structure value, and residential/commercial composition.
