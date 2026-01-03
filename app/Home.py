"""
Vegetation Change Intelligence Platform - Streamlit Dashboard

Interactive web application for vegetation change analysis using
Google Earth Engine satellite imagery.
"""

import streamlit as st
import ee

st.set_page_config(
    page_title="Vegetation Change Intelligence",
    page_icon="🌿",
    layout="wide",
    initial_sidebar_state="expanded",
)


def init_ee():
    """Initialize Earth Engine with caching."""
    if "ee_initialized" not in st.session_state:
        try:
            ee.Initialize()
            st.session_state.ee_initialized = True
        except Exception as e:
            st.error(f"Earth Engine initialization failed: {e}")
            st.info("Please run `earthengine authenticate` in terminal first.")
            st.stop()


def main():
    st.title("🌿 Vegetation Change Intelligence Platform")

    st.markdown("""
    **GEE-based satellite analysis for detecting and quantifying vegetation change**

    This platform analyzes multi-decadal satellite imagery to track vegetation dynamics:
    - **Temporal Composites**: Cloud-free imagery from Landsat 5/7/8 and Sentinel-2
    - **Spectral Indices**: NDVI, NBR, and other vegetation metrics
    - **Change Detection**: Identify areas of vegetation loss and gain
    - **Export Results**: Download GeoTIFFs or save to Google Drive
    """)

    # Sidebar configuration
    st.sidebar.title("⚙️ Configuration")

    # Initialize EE
    with st.sidebar:
        if st.button("🔄 Initialize Earth Engine"):
            init_ee()
            st.success("Earth Engine ready!")

    # Main content
    col1, col2 = st.columns(2)

    with col1:
        st.subheader("📊 Available Periods")

        from veg_change_engine.config import TEMPORAL_PERIODS

        for period, info in TEMPORAL_PERIODS.items():
            with st.expander(f"**{period.upper()}** ({info['start'][:4]}-{info['end'][:4]})"):
                st.write(f"**Description:** {info['description']}")
                st.write(f"**Sensors:** {', '.join([s.split('/')[1] for s in info['sensors']])}")

    with col2:
        st.subheader("📈 Available Indices")

        indices_info = {
            "NDVI": "Normalized Difference Vegetation Index - vegetation health",
            "NBR": "Normalized Burn Ratio - burn severity and recovery",
            "NDWI": "Normalized Difference Water Index - water content",
            "EVI": "Enhanced Vegetation Index - high biomass areas",
            "NDMI": "Normalized Difference Moisture Index - vegetation moisture",
        }

        for idx, desc in indices_info.items():
            st.markdown(f"**{idx}**: {desc}")

    # Quick start guide
    st.markdown("---")
    st.subheader("🚀 Quick Start")

    st.markdown("""
    1. **Upload AOI**: Go to the Analysis page and upload your area of interest (KMZ, GeoJSON, Shapefile)
    2. **Select Periods**: Choose which time periods to analyze
    3. **Run Analysis**: Generate composites and change detection maps
    4. **Export**: Download results or save to Google Drive

    Use the sidebar to navigate between pages.
    """)

    # Demo section
    st.markdown("---")
    st.subheader("🎯 Demo Mode")

    if st.button("Run Demo Analysis"):
        init_ee()

        with st.spinner("Running demo analysis on Colombian Andes region..."):
            from veg_change_engine.pipeline import analyze_vegetation_change

            # Sample AOI
            aoi = ee.Geometry.Rectangle([-75.7, 4.4, -75.6, 4.5])

            results = analyze_vegetation_change(
                aoi=aoi,
                periods=["2010s", "present"],
                indices=["ndvi"],
                reference_period="2010s",
            )

            st.success("Demo complete!")
            st.json({
                "composites": list(results["composites"].keys()),
                "changes": list(results["changes"].keys()),
            })

    # Footer
    st.markdown("---")
    st.markdown("""
    <div style="text-align: center; color: gray; font-size: 12px;">
        Vegetation Change Intelligence Platform v1.0.0<br>
        Built with Google Earth Engine + Streamlit
    </div>
    """, unsafe_allow_html=True)


if __name__ == "__main__":
    main()
