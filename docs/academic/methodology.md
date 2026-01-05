# Scientific Methodology

This document describes the scientific methodology used in the Vegetation Change Intelligence Platform for detecting and quantifying vegetation change using satellite imagery.

## Overview

The platform implements a **multi-temporal, multi-sensor change detection approach** that:

1. Creates cloud-free composites from satellite imagery
2. Calculates spectral indices for vegetation monitoring
3. Detects changes through temporal differencing
4. Classifies changes into meaningful categories
5. Quantifies changes with area statistics

## Theoretical Framework

### Remote Sensing of Vegetation

Vegetation interacts with electromagnetic radiation in predictable ways:

- **Visible light (400-700nm)**: Absorbed by chlorophyll for photosynthesis
- **Near-infrared (700-1300nm)**: Strongly reflected by leaf cellular structure
- **Shortwave infrared (1300-2500nm)**: Absorbed by water in leaves

These spectral properties form the basis for vegetation indices.

### Spectral Vegetation Indices

#### NDVI (Normalized Difference Vegetation Index)

**Formula**:
$$NDVI = \frac{NIR - Red}{NIR + Red}$$

**Theory**: Healthy vegetation absorbs red light for photosynthesis and reflects NIR. The ratio amplifies this contrast.

**Interpretation**:
| Value | Surface Type |
|-------|--------------|
| -1.0 to 0 | Water, bare soil |
| 0 to 0.2 | Sparse vegetation |
| 0.2 to 0.4 | Grassland |
| 0.4 to 0.6 | Shrubland |
| 0.6 to 0.9 | Forest |

**References**:
- Rouse et al. (1974). Monitoring vegetation systems in the Great Plains

#### NBR (Normalized Burn Ratio)

**Formula**:
$$NBR = \frac{NIR - SWIR_2}{NIR + SWIR_2}$$

**Theory**: Burned areas show decreased NIR (destroyed chlorophyll) and increased SWIR (exposed soil, char).

**Applications**:
- Fire severity mapping
- Forest disturbance detection
- Post-fire vegetation recovery

**References**:
- Key & Benson (2006). Landscape Assessment (LA) sampling and analysis methods

### Change Detection Theory

#### Image Differencing

The simplest and most widely used approach:

$$\Delta Index = Index_{t2} - Index_{t1}$$

Where:
- $t1$ = earlier time period
- $t2$ = later time period
- Positive values = increase
- Negative values = decrease

#### Threshold Classification

Changes are classified based on magnitude thresholds:

```
Class 1 (Strong Loss):    Δ < -0.15
Class 2 (Moderate Loss):  -0.15 ≤ Δ < -0.05
Class 3 (Stable):         -0.05 ≤ Δ ≤ 0.05
Class 4 (Moderate Gain):  0.05 < Δ ≤ 0.15
Class 5 (Strong Gain):    Δ > 0.15
```

## Data Sources

### Landsat Collection 2 Level-2

| Satellite | Period | Resolution | Bands |
|-----------|--------|------------|-------|
| Landsat 5 TM | 1984-2013 | 30m | Blue, Green, Red, NIR, SWIR1, SWIR2 |
| Landsat 7 ETM+ | 1999-present | 30m | Same as TM |
| Landsat 8 OLI | 2013-present | 30m | Coastal, Blue, Green, Red, NIR, SWIR1, SWIR2 |

**Collection 2 Improvements**:
- Improved geometric accuracy
- Consistent atmospheric correction (LaSRC)
- Better cloud masking (CFMask)

### Sentinel-2 MSI

| Band | Wavelength | Resolution | Use |
|------|------------|------------|-----|
| B2 | 490nm | 10m | Blue |
| B3 | 560nm | 10m | Green |
| B4 | 665nm | 10m | Red |
| B8 | 842nm | 10m | NIR |
| B11 | 1610nm | 20m | SWIR1 |
| B12 | 2190nm | 20m | SWIR2 |

## Processing Pipeline

### 1. Cloud Masking

**Landsat** (QA_PIXEL band):
```python
# Bit positions for Collection 2
cloud = (1 << 3)      # Cloud
shadow = (1 << 4)     # Cloud shadow
snow = (1 << 5)       # Snow/ice
dilated = (1 << 1)    # Dilated cloud

mask = ~(cloud | shadow | snow | dilated)
```

**Sentinel-2** (QA60 band):
```python
cloud = (1 << 10)     # Opaque clouds
cirrus = (1 << 11)    # Cirrus clouds

mask = ~(cloud | cirrus)
```

### 2. Band Harmonization

Different sensors have different band configurations. We harmonize to common names:

| Common Name | Landsat 5/7 | Landsat 8 | Sentinel-2 |
|-------------|-------------|-----------|------------|
| blue | SR_B1 | SR_B2 | B2 |
| green | SR_B2 | SR_B3 | B3 |
| red | SR_B3 | SR_B4 | B4 |
| nir | SR_B4 | SR_B5 | B8 |
| swir1 | SR_B5 | SR_B6 | B11 |
| swir2 | SR_B7 | SR_B7 | B12 |

**Scale Factors**:
- Landsat C2: `SR = DN × 0.0000275 - 0.2`
- Sentinel-2: `SR = DN × 0.0001`

### 3. Temporal Compositing

**Median Composite**: For each pixel, the median value across all valid observations.

**Advantages**:
- Removes outliers (clouds, shadows)
- Reduces noise
- Provides representative surface conditions

**Time Periods**:
| Period | Range | Duration | Rationale |
|--------|-------|----------|-----------|
| 1990s | 1985-1999 | 15 years | Pre-2000 baseline |
| 2000s | 2000-2012 | 13 years | Early digital era |
| 2010s | 2013-2020 | 8 years | Landsat 8 era |
| present | 2021-2024 | 4 years | Current conditions |

### 4. Multi-Sensor Fusion

For the "present" period, we fuse Landsat 8 and Sentinel-2:

1. Create separate composites for each sensor
2. Harmonize bands to common names
3. Merge into single ImageCollection
4. Compute median across all images

**Benefits**:
- Higher temporal resolution (5-day revisit vs 16-day)
- More cloud-free observations
- Improved composite quality

## Validation Approach

### Internal Consistency

1. **Cross-index agreement**: Compare changes detected by NDVI vs NBR
2. **Temporal consistency**: Changes should be persistent, not noise
3. **Spatial coherence**: Changes typically occur in contiguous areas

### External Validation

1. **High-resolution imagery**: Google Earth, Planet
2. **Field data**: Ground truth campaigns
3. **Reference datasets**: Global Forest Watch, PRODES

### Accuracy Metrics

| Metric | Formula | Use |
|--------|---------|-----|
| Overall Accuracy | (TP + TN) / Total | General performance |
| Producer's Accuracy | TP / (TP + FN) | Omission error |
| User's Accuracy | TP / (TP + FP) | Commission error |
| Kappa | (Po - Pe) / (1 - Pe) | Agreement beyond chance |

## Limitations

### Methodological

1. **Threshold sensitivity**: Results depend on classification thresholds
2. **Phenological effects**: Seasonal variations can be misclassified as change
3. **Atmospheric residuals**: Imperfect atmospheric correction
4. **Mixed pixels**: 30m resolution may miss small changes

### Data Limitations

1. **Temporal gaps**: Landsat 7 SLC-off (2003+)
2. **Cloud persistence**: Some regions consistently cloudy
3. **Sensor discontinuity**: Different sensors may show bias

### Recommendations

1. **Use multiple indices**: Compare NDVI and NBR
2. **Validate locally**: Ground truth when possible
3. **Consider context**: Interpret results with local knowledge
4. **Report uncertainty**: Acknowledge limitations

## Statistical Analysis

### Area Calculation

```python
area_ha = pixel_count × (resolution_m)² / 10000
```

### Confidence Intervals

Bootstrap resampling for uncertainty estimation:

```python
for i in range(1000):
    sample = resample(data)
    stats[i] = calculate_statistic(sample)

ci_95 = np.percentile(stats, [2.5, 97.5])
```

## Future Enhancements

1. **Machine Learning Classification**: Random Forest, Deep Learning
2. **Time Series Analysis**: BFAST, LandTrendr
3. **Semantic Embeddings**: AlphaEarth integration
4. **Uncertainty Quantification**: Bayesian approaches

## References

1. Rouse, J. W., et al. (1974). "Monitoring vegetation systems in the Great Plains with ERTS." NASA Special Publication, 351, 309.

2. Tucker, C. J. (1979). "Red and photographic infrared linear combinations for monitoring vegetation." Remote Sensing of Environment, 8(2), 127-150.

3. Key, C. H., & Benson, N. C. (2006). "Landscape Assessment: Ground measure of severity, the Composite Burn Index; and Remote sensing of severity, the Normalized Burn Ratio." FIREMON: Fire Effects Monitoring and Inventory System.

4. Zhu, Z., & Woodcock, C. E. (2012). "Object-based cloud and cloud shadow detection in Landsat imagery." Remote Sensing of Environment, 118, 83-94.

5. Claverie, M., et al. (2018). "The Harmonized Landsat and Sentinel-2 surface reflectance data set." Remote Sensing of Environment, 219, 145-161.
