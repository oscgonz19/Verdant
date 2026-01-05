# References and Bibliography

A comprehensive list of scientific references, datasets, and resources related to the Vegetation Change Intelligence Platform.

## Core Scientific References

### Spectral Indices

1. **Rouse, J.W., Haas, R.H., Schell, J.A., & Deering, D.W. (1974)**. Monitoring vegetation systems in the Great Plains with ERTS. *NASA Special Publication*, 351, 309-317.
   - *Original NDVI publication*

2. **Tucker, C.J. (1979)**. Red and photographic infrared linear combinations for monitoring vegetation. *Remote Sensing of Environment*, 8(2), 127-150.
   - *NDVI theory and applications*

3. **Huete, A., Didan, K., Miura, T., Rodriguez, E.P., Gao, X., & Ferreira, L.G. (2002)**. Overview of the radiometric and biophysical performance of the MODIS vegetation indices. *Remote Sensing of Environment*, 83(1-2), 195-213.
   - *EVI development and performance*

4. **Key, C.H. & Benson, N.C. (2006)**. Landscape Assessment (LA) sampling and analysis methods. *USDA Forest Service, Rocky Mountain Research Station RMRS-GTR-164-CD*.
   - *NBR and burn severity mapping*

5. **McFeeters, S.K. (1996)**. The use of the Normalized Difference Water Index (NDWI) in the delineation of open water features. *International Journal of Remote Sensing*, 17(7), 1425-1432.
   - *NDWI for water detection*

6. **Gao, B.C. (1996)**. NDWI—A normalized difference water index for remote sensing of vegetation liquid water from space. *Remote Sensing of Environment*, 58(3), 257-266.
   - *NDMI for vegetation moisture*

### Change Detection

7. **Singh, A. (1989)**. Digital change detection techniques using remotely-sensed data. *International Journal of Remote Sensing*, 10(6), 989-1003.
   - *Foundational change detection review*

8. **Kennedy, R.E., Yang, Z., & Cohen, W.B. (2010)**. Detecting trends in forest disturbance and recovery using yearly Landsat time series: 1. LandTrendr—Temporal segmentation algorithms. *Remote Sensing of Environment*, 114(12), 2897-2910.
   - *Time series change detection*

9. **Zhu, Z., Woodcock, C.E., & Olofsson, P. (2012)**. Continuous monitoring of forest disturbance using all available Landsat imagery. *Remote Sensing of Environment*, 122, 75-91.
   - *CCDC continuous monitoring*

10. **Hansen, M.C., et al. (2013)**. High-resolution global maps of 21st-century forest cover change. *Science*, 342(6160), 850-853.
    - *Global forest change mapping*

### Remote Sensing Theory

11. **Jensen, J.R. (2015)**. *Introductory Digital Image Processing: A Remote Sensing Perspective* (4th ed.). Pearson.
    - *Comprehensive remote sensing textbook*

12. **Lillesand, T., Kiefer, R., & Chipman, J. (2015)**. *Remote Sensing and Image Interpretation* (7th ed.). Wiley.
    - *Classic remote sensing textbook*

13. **Campbell, J.B. & Wynne, R.H. (2011)**. *Introduction to Remote Sensing* (5th ed.). Guilford Press.
    - *Remote sensing fundamentals*

### Cloud Processing & Earth Engine

14. **Gorelick, N., Hancher, M., Dixon, M., Ilyushchenko, S., Thau, D., & Moore, R. (2017)**. Google Earth Engine: Planetary-scale geospatial analysis for everyone. *Remote Sensing of Environment*, 202, 18-27.
    - *Google Earth Engine platform*

15. **Zhu, Z. & Woodcock, C.E. (2012)**. Object-based cloud and cloud shadow detection in Landsat imagery. *Remote Sensing of Environment*, 118, 83-94.
    - *Fmask cloud detection algorithm*

### Landsat

16. **Wulder, M.A., et al. (2019)**. Current status of Landsat program, science, and applications. *Remote Sensing of Environment*, 225, 127-147.
    - *Landsat program overview*

17. **Claverie, M., et al. (2018)**. The Harmonized Landsat and Sentinel-2 surface reflectance data set. *Remote Sensing of Environment*, 219, 145-161.
    - *Landsat-Sentinel harmonization*

18. **Masek, J.G., et al. (2020)**. Landsat 9: Empowering open science and applications through continuity. *Remote Sensing of Environment*, 248, 111968.
    - *Landsat program continuity*

### Sentinel-2

19. **Drusch, M., et al. (2012)**. Sentinel-2: ESA's optical high-resolution mission for GMES operational services. *Remote Sensing of Environment*, 120, 25-36.
    - *Sentinel-2 mission overview*

20. **Main-Knorn, M., et al. (2017)**. Sen2Cor for Sentinel-2. *Proceedings of SPIE*, 10427, 1042704.
    - *Sentinel-2 atmospheric correction*

---

## Datasets and Data Sources

### Satellite Imagery

| Dataset | Provider | Access |
|---------|----------|--------|
| Landsat Collection 2 | USGS | [EarthExplorer](https://earthexplorer.usgs.gov/) |
| Sentinel-2 | ESA | [Copernicus Hub](https://scihub.copernicus.eu/) |
| Both (cloud) | Google | [Earth Engine Data Catalog](https://developers.google.com/earth-engine/datasets) |

### Reference Datasets

| Dataset | Description | Access |
|---------|-------------|--------|
| Global Forest Watch | Forest change maps | [globalforestwatch.org](https://www.globalforestwatch.org/) |
| PRODES | Amazon deforestation | [INPE](http://www.obt.inpe.br/prodes/) |
| GLAD Alerts | Near real-time alerts | [GLAD UMD](https://glad.umd.edu/) |
| JRC Global Surface Water | Water dynamics | [JRC](https://global-surface-water.appspot.com/) |

### Administrative Boundaries

| Dataset | Coverage | Format |
|---------|----------|--------|
| Natural Earth | Global | Shapefile, GeoJSON |
| GADM | Global (admin) | Shapefile, GeoPackage |
| OSM | Global | Various |

---

## Software and Tools

### Earth Engine

- **Documentation**: [developers.google.com/earth-engine](https://developers.google.com/earth-engine)
- **Python API**: `earthengine-api`
- **JavaScript API**: Code Editor

### Geospatial Python

| Library | Purpose | Documentation |
|---------|---------|---------------|
| GeoPandas | Vector data | [geopandas.org](https://geopandas.org/) |
| Rasterio | Raster data | [rasterio.readthedocs.io](https://rasterio.readthedocs.io/) |
| Shapely | Geometry | [shapely.readthedocs.io](https://shapely.readthedocs.io/) |
| Folium | Web maps | [python-visualization.github.io/folium](https://python-visualization.github.io/folium/) |

### Visualization

| Tool | Type | Link |
|------|------|------|
| QGIS | Desktop GIS | [qgis.org](https://qgis.org/) |
| Folium | Python maps | [folium](https://python-visualization.github.io/folium/) |
| geemap | EE + maps | [geemap.org](https://geemap.org/) |

---

## Online Resources

### Tutorials and Courses

1. **Google Earth Engine User Guide**
   - https://developers.google.com/earth-engine/guides

2. **Spatial Thoughts - QGIS & Python**
   - https://courses.spatialthoughts.com/

3. **NASA ARSET - Remote Sensing Training**
   - https://appliedsciences.nasa.gov/what-we-do/capacity-building/arset

4. **USGS Landsat Education**
   - https://www.usgs.gov/landsat-missions/landsat-education

### Community

- **GEE Developers Forum**: https://groups.google.com/g/google-earth-engine-developers
- **GIS Stack Exchange**: https://gis.stackexchange.com/
- **GitHub Earth Engine Community**: https://github.com/google/earthengine-community

---

## Citation

If you use this platform in your research, please cite:

```bibtex
@software{veg_change_platform,
  title = {Vegetation Change Intelligence Platform},
  author = {Gonzalez, Oscar},
  year = {2024},
  url = {https://github.com/oscgonz19/vegetation-change-platform},
  version = {1.0.0}
}
```

---

## Acknowledgments

This platform was built using:

- Google Earth Engine (Gorelick et al., 2017)
- Landsat imagery courtesy of USGS
- Sentinel-2 imagery courtesy of ESA/Copernicus
- Open-source Python geospatial community
