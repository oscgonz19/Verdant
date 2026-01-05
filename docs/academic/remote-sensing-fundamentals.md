# Remote Sensing Fundamentals

A comprehensive guide to the remote sensing concepts underlying the Vegetation Change Intelligence Platform.

## What is Remote Sensing?

**Remote sensing** is the science of obtaining information about objects or areas from a distance, typically from aircraft or satellites. In Earth observation, sensors detect electromagnetic radiation reflected or emitted from Earth's surface.

## Electromagnetic Spectrum

The electromagnetic spectrum encompasses all types of electromagnetic radiation:

```
┌────────────────────────────────────────────────────────────────────┐
│                    ELECTROMAGNETIC SPECTRUM                         │
├──────────┬──────────┬──────────┬──────────┬──────────┬─────────────┤
│  Gamma   │  X-rays  │   UV     │ Visible  │ Infrared │  Microwave  │
│  rays    │          │          │          │          │             │
├──────────┴──────────┴──────────┼──────────┼──────────┴─────────────┤
│        Shorter wavelength      │400-700nm │   Longer wavelength     │
│        Higher energy           │          │   Lower energy          │
└────────────────────────────────┴──────────┴─────────────────────────┘
```

### Wavelength Regions Used in This Platform

| Region | Wavelength | Sensor Bands | Primary Use |
|--------|------------|--------------|-------------|
| Blue | 450-515 nm | L8 B2, S2 B2 | Water penetration, atmospheric scatter |
| Green | 525-600 nm | L8 B3, S2 B3 | Vegetation vigor |
| Red | 630-690 nm | L8 B4, S2 B4 | Chlorophyll absorption |
| NIR | 770-900 nm | L8 B5, S2 B8 | Vegetation structure |
| SWIR1 | 1550-1750 nm | L8 B6, S2 B11 | Soil/vegetation moisture |
| SWIR2 | 2100-2300 nm | L8 B7, S2 B12 | Minerals, fire detection |

## Spectral Signatures

Different surface types have characteristic spectral signatures:

```
Reflectance
    │
  1 │
    │    ╭──── Healthy Vegetation
    │   ╱ ╲
0.5 │──╱───╲────────────────────────
    │ ╱     ╲___________
    │╱                   ╲____ Soil
    │_______________________╲____
  0 │────────────────────────────────
    │  Blue  Green  Red   NIR  SWIR
    └────────────────────────────────
                Wavelength
```

### Vegetation Spectral Properties

| Wavelength | Vegetation Response | Reason |
|------------|---------------------|--------|
| Blue | Low reflectance | Absorbed by carotenoids |
| Green | Moderate reflectance | Green "peak" |
| Red | Very low reflectance | Absorbed by chlorophyll |
| NIR | Very high reflectance | Scattered by leaf structure |
| SWIR | Moderate reflectance | Absorbed by water content |

### The "Red Edge"

The dramatic increase in reflectance between red and NIR (~700nm) is called the **red edge**. This feature is unique to healthy vegetation and is exploited by indices like NDVI.

## Satellite Sensors

### Landsat Program

The Landsat program has provided continuous Earth observation since 1972.

**Landsat 5 TM (1984-2013)**:
- 30m multispectral resolution
- 16-day revisit
- 7 spectral bands

**Landsat 7 ETM+ (1999-present)**:
- Added 15m panchromatic band
- SLC failure in 2003 created data gaps

**Landsat 8 OLI (2013-present)**:
- Improved signal-to-noise
- Added coastal aerosol band (443nm)
- 12-bit radiometric resolution

### Sentinel-2

European Space Agency's optical mission (2015-present):

- 10m resolution in visible + NIR
- 20m in SWIR
- 5-day revisit (with twin satellites)
- 13 spectral bands

### Sensor Comparison

| Feature | Landsat 8 | Sentinel-2 |
|---------|-----------|------------|
| Spatial Resolution | 30m (15m pan) | 10-20m |
| Temporal Resolution | 16 days | 5 days |
| Spectral Bands | 11 | 13 |
| Swath Width | 185 km | 290 km |
| Launch | 2013 | 2015 |

## Image Acquisition

### How Satellites Capture Images

1. **Sun illuminates Earth's surface**
2. **Surface reflects/absorbs radiation** (based on material properties)
3. **Satellite sensor detects reflected energy**
4. **Digital numbers (DN)** recorded for each pixel
5. **Processing to surface reflectance** (atmospheric correction)

### Geometric Considerations

**Nadir**: Point directly below the satellite

**Off-nadir viewing**: Can cause distortion at image edges

**Sun angle**: Affects illumination and shadows

### Temporal Considerations

**Revisit time**: How often the satellite passes over the same location

**Seasonal effects**: Vegetation phenology, snow cover

**Time of day**: Landsat/Sentinel are sun-synchronous (~10:30 AM local time)

## Atmospheric Correction

### Why It Matters

Raw satellite data (Top-of-Atmosphere reflectance) includes:
- Surface reflectance (what we want)
- Atmospheric scattering
- Atmospheric absorption

### Surface Reflectance Products

Both Landsat Collection 2 and Sentinel-2 SR products have been atmospherically corrected:

- **Landsat**: LaSRC algorithm
- **Sentinel-2**: Sen2Cor processor

This allows comparison across time and sensors.

## Cloud Masking

### The Challenge

Clouds obstruct the view of Earth's surface and are one of the biggest challenges in optical remote sensing.

### Detection Methods

**Brightness thresholds**: Clouds are typically bright

**Temperature**: Clouds are cold in thermal bands

**Spectral tests**: Clouds have specific spectral properties

### Quality Assessment Bands

**Landsat QA_PIXEL**: Bitwise flags for cloud, shadow, snow, etc.

**Sentinel-2 QA60**: Cloud and cirrus masks

### Cloud Shadow Detection

Shadows are cast by clouds and must also be masked:

1. Detect cloud location
2. Calculate shadow position using sun angle
3. Project shadow mask on ground

## Resolution Concepts

### Spatial Resolution

The size of the smallest feature that can be detected.

| Resolution | Size | Example Sensors |
|------------|------|-----------------|
| Coarse | > 250m | MODIS |
| Medium | 10-30m | Landsat, Sentinel-2 |
| High | 1-10m | Planet, SPOT |
| Very High | < 1m | WorldView, Maxar |

### Spectral Resolution

The number and width of spectral bands.

- **Panchromatic**: Single broad band
- **Multispectral**: Several discrete bands (4-12)
- **Hyperspectral**: Many narrow bands (100+)

### Temporal Resolution

How often imagery is acquired for the same location.

### Radiometric Resolution

The number of brightness levels that can be recorded.

- 8-bit: 256 levels
- 12-bit: 4,096 levels
- 16-bit: 65,536 levels

## Compositing Methods

### Why Composite?

Single images often have:
- Cloud contamination
- Atmospheric haze
- Seasonal noise

Compositing combines multiple images to reduce these issues.

### Median Composite

For each pixel, take the median value across all observations.

**Advantages**:
- Robust to outliers
- Simple to implement
- Good for most applications

**Disadvantages**:
- May not preserve extreme values
- Can create artifacts at cloud edges

### Other Methods

| Method | Description | Use Case |
|--------|-------------|----------|
| Mean | Average of all values | General purpose |
| Maximum | Highest value | Cloud removal (MAX NDVI) |
| Minimum | Lowest value | Water detection |
| Greenest pixel | Max NDVI selection | Vegetation peak |

## Image Interpretation

### Visual Interpretation

RGB composites for visual analysis:

| Composite | Bands | Appearance |
|-----------|-------|------------|
| True Color | R, G, B | Natural colors |
| False Color | NIR, R, G | Vegetation is red |
| SWIR Composite | SWIR2, NIR, R | Urban areas, geology |

### Quantitative Analysis

Using indices and algorithms for automated analysis:

- Spectral indices (NDVI, NBR)
- Classification (supervised, unsupervised)
- Change detection

## Key Terminology

| Term | Definition |
|------|------------|
| **Pixel** | Smallest picture element |
| **Band** | Single wavelength channel |
| **Scene** | Single image acquisition |
| **Tile** | Standard geographic subset |
| **Stack** | Multiple bands/dates combined |
| **Composite** | Derived from multiple images |
| **Mask** | Binary image for filtering |
| **AOI** | Area of Interest |

## Further Reading

1. **Jensen, J. R. (2015)**. Introductory Digital Image Processing. Pearson.

2. **Lillesand, T., Kiefer, R., & Chipman, J. (2015)**. Remote Sensing and Image Interpretation. Wiley.

3. **Gorelick, N., et al. (2017)**. Google Earth Engine: Planetary-scale geospatial analysis for everyone. Remote Sensing of Environment, 202, 18-27.

4. **USGS Landsat Mission**: https://www.usgs.gov/landsat-missions

5. **ESA Sentinel Online**: https://sentinel.esa.int/web/sentinel/home
