# Spectral Indices Reference

A comprehensive guide to the spectral indices supported by the Vegetation Change Intelligence Platform.

## Introduction

Spectral indices are mathematical transformations of spectral bands that enhance specific features or phenomena. They reduce data dimensionality while highlighting relevant information.

## Vegetation Indices

### NDVI - Normalized Difference Vegetation Index

**The most widely used vegetation index.**

#### Formula
$$NDVI = \frac{NIR - Red}{NIR + Red}$$

#### Physical Basis
- Healthy vegetation strongly absorbs red light (chlorophyll)
- Healthy vegetation strongly reflects NIR (leaf structure)
- Ratio exploits this contrast

#### Value Range
| Range | Interpretation |
|-------|----------------|
| -1.0 to 0.0 | Water, snow, clouds |
| 0.0 to 0.1 | Bare rock, sand |
| 0.1 to 0.2 | Bare soil |
| 0.2 to 0.4 | Sparse vegetation, crops |
| 0.4 to 0.6 | Shrubland, grassland |
| 0.6 to 0.8 | Temperate forest |
| 0.8 to 1.0 | Tropical rainforest |

#### Advantages
- Simple calculation
- Well-documented in literature
- Works across sensors
- Good for general vegetation assessment

#### Limitations
- Saturates at high biomass (LAI > 3)
- Sensitive to soil background
- Affected by atmospheric conditions

#### References
- Rouse, J.W. et al. (1974)
- Tucker, C.J. (1979)

---

### EVI - Enhanced Vegetation Index

**Improved vegetation monitoring in high biomass regions.**

#### Formula
$$EVI = 2.5 \times \frac{NIR - Red}{NIR + 6 \times Red - 7.5 \times Blue + 1}$$

#### Physical Basis
- Blue band corrects for atmospheric aerosol influences
- Soil adjustment factor reduces soil background
- Better performance in high LAI conditions

#### Value Range
| Range | Interpretation |
|-------|----------------|
| -0.2 to 0.0 | Non-vegetated |
| 0.0 to 0.2 | Low vegetation |
| 0.2 to 0.4 | Moderate vegetation |
| 0.4 to 0.6 | High vegetation |
| 0.6 to 1.0 | Very high vegetation |

#### Advantages
- Less saturation in dense vegetation
- Better atmospheric correction
- Reduced soil background effects

#### Limitations
- Requires blue band (not always available)
- More complex calculation
- Negative values in some conditions

#### References
- Huete, A. et al. (2002)

---

## Disturbance Indices

### NBR - Normalized Burn Ratio

**Optimal for fire and disturbance detection.**

#### Formula
$$NBR = \frac{NIR - SWIR_2}{NIR + SWIR_2}$$

#### Physical Basis
- Fire reduces NIR reflectance (destroyed vegetation)
- Fire increases SWIR reflectance (char, exposed soil)
- Change in ratio indicates burn severity

#### Value Range
| Range | Burn Severity |
|-------|---------------|
| -0.5 to -0.25 | High severity |
| -0.25 to -0.1 | Moderate-high severity |
| -0.1 to 0.1 | Low severity / no burn |
| 0.1 to 0.27 | Low-moderate regrowth |
| 0.27 to 0.66 | High regrowth |

#### dNBR (Delta NBR)
$$dNBR = NBR_{pre-fire} - NBR_{post-fire}$$

| dNBR | Severity Class |
|------|----------------|
| > 0.66 | High severity |
| 0.44 to 0.66 | Moderate-high severity |
| 0.27 to 0.44 | Moderate-low severity |
| 0.1 to 0.27 | Low severity |
| -0.1 to 0.1 | Unburned |
| < -0.1 | Enhanced regrowth |

#### Applications
- Fire mapping
- Burn severity assessment
- Forest disturbance detection
- Post-fire recovery monitoring

#### References
- Key, C.H. & Benson, N.C. (2006)

---

## Moisture Indices

### NDWI - Normalized Difference Water Index

**Water body and moisture detection.**

#### Formula
$$NDWI = \frac{Green - NIR}{Green + NIR}$$

#### Physical Basis
- Water absorbs NIR
- Water reflects green
- Maximizes contrast between water and vegetation

#### Value Range
| Range | Interpretation |
|-------|----------------|
| > 0.3 | Open water |
| 0.0 to 0.3 | Moisture/flooding |
| -0.3 to 0.0 | Dry vegetation |
| < -0.3 | Very dry conditions |

#### Applications
- Water body mapping
- Flood extent mapping
- Wetland monitoring
- Irrigation analysis

#### References
- McFeeters, S.K. (1996)

---

### NDMI - Normalized Difference Moisture Index

**Vegetation water content assessment.**

#### Formula
$$NDMI = \frac{NIR - SWIR_1}{NIR + SWIR_1}$$

#### Physical Basis
- SWIR is sensitive to water in leaves
- NIR reflects from leaf structure
- Ratio indicates canopy moisture content

#### Value Range
| Range | Moisture Level |
|-------|----------------|
| > 0.4 | Very high moisture |
| 0.2 to 0.4 | High moisture |
| 0.0 to 0.2 | Moderate moisture |
| -0.2 to 0.0 | Low moisture (stress) |
| < -0.2 | Very low moisture (severe stress) |

#### Applications
- Drought monitoring
- Irrigation scheduling
- Forest health assessment
- Fire risk mapping

#### References
- Gao, B.C. (1996)

---

## Band Reference Table

| Index | Band 1 | Band 2 | Band 3 | L8 Bands | S2 Bands |
|-------|--------|--------|--------|----------|----------|
| NDVI | NIR | Red | - | B5, B4 | B8, B4 |
| EVI | NIR | Red | Blue | B5, B4, B2 | B8, B4, B2 |
| NBR | NIR | SWIR2 | - | B5, B7 | B8, B12 |
| NDWI | Green | NIR | - | B3, B5 | B3, B8 |
| NDMI | NIR | SWIR1 | - | B5, B6 | B8, B11 |

## Change Detection with Indices

### Delta Index Calculation

$$\Delta Index = Index_{after} - Index_{before}$$

### Interpretation

| dNDVI | Interpretation |
|-------|----------------|
| < -0.15 | Strong vegetation loss |
| -0.15 to -0.05 | Moderate vegetation loss |
| -0.05 to 0.05 | Stable |
| 0.05 to 0.15 | Moderate vegetation gain |
| > 0.15 | Strong vegetation gain |

### Best Practices

1. **Use consistent time of year** to avoid phenological effects
2. **Use multiple indices** for cross-validation
3. **Consider local conditions** when interpreting thresholds
4. **Validate with field data** when possible

## Implementation in Platform

```python
from engine.indices import add_ndvi, add_nbr, add_all_indices

# Add single index
image = add_ndvi(composite)

# Add multiple indices
image = add_all_indices(composite, ['ndvi', 'nbr', 'ndmi'])

# Calculate change
from engine.indices import calculate_delta_indices
delta = calculate_delta_indices(
    before=composite_1990s,
    after=composite_present,
    indices=['ndvi', 'nbr']
)
```

## Index Selection Guide

| Application | Primary Index | Secondary Index |
|-------------|---------------|-----------------|
| General vegetation | NDVI | EVI |
| Dense forest | EVI | NDVI |
| Fire mapping | NBR | NDVI |
| Drought | NDMI | NDVI |
| Water bodies | NDWI | - |
| Agriculture | NDVI | NDMI |

## References

1. **Rouse, J.W., et al. (1974)**. Monitoring vegetation systems in the Great Plains with ERTS.

2. **Tucker, C.J. (1979)**. Red and photographic infrared linear combinations for monitoring vegetation.

3. **Huete, A., et al. (2002)**. Overview of the radiometric and biophysical performance of the MODIS vegetation indices.

4. **Key, C.H. & Benson, N.C. (2006)**. Landscape Assessment: Ground measure of severity.

5. **McFeeters, S.K. (1996)**. The use of the Normalized Difference Water Index (NDWI) in the delineation of open water features.

6. **Gao, B.C. (1996)**. NDWI - A normalized difference water index for remote sensing of vegetation liquid water.
