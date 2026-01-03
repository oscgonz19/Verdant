"""
Analysis Page - Upload AOI and run vegetation change analysis.
"""

import streamlit as st
import ee
import tempfile
from pathlib import Path

st.set_page_config(page_title="Analysis", page_icon="📊", layout="wide")


def init_ee():
    """Initialize Earth Engine."""
    if "ee_initialized" not in st.session_state:
        try:
            ee.Initialize()
            st.session_state.ee_initialized = True
        except Exception:
            st.error("Please initialize Earth Engine from the Home page first.")
            st.stop()


def main():
    st.title("📊 Vegetation Change Analysis")

    init_ee()

    # Sidebar configuration
    st.sidebar.header("Analysis Settings")

    # Period selection
    periods = st.sidebar.multiselect(
        "Select Periods",
        options=["1990s", "2000s", "2010s", "present"],
        default=["1990s", "present"],
    )

    # Index selection
    indices = st.sidebar.multiselect(
        "Spectral Indices",
        options=["ndvi", "nbr", "ndwi", "evi"],
        default=["ndvi"],
    )

    # Reference period
    reference = st.sidebar.selectbox(
        "Reference Period",
        options=periods if periods else ["1990s"],
        index=0,
    )

    # Buffer distance
    buffer = st.sidebar.slider(
        "Buffer Distance (m)",
        min_value=0,
        max_value=2000,
        value=500,
        step=100,
    )

    # Cloud threshold
    cloud_threshold = st.sidebar.slider(
        "Max Cloud Cover (%)",
        min_value=5,
        max_value=50,
        value=20,
    )

    # Main content
    st.subheader("1. Upload Area of Interest")

    upload_method = st.radio(
        "Input Method",
        options=["Upload File", "Draw on Map", "Enter Coordinates"],
        horizontal=True,
    )

    aoi = None

    if upload_method == "Upload File":
        uploaded_file = st.file_uploader(
            "Upload AOI (KMZ, GeoJSON, Shapefile ZIP)",
            type=["kmz", "geojson", "json", "zip"],
        )

        if uploaded_file:
            # Save to temp file
            with tempfile.NamedTemporaryFile(delete=False, suffix=Path(uploaded_file.name).suffix) as tmp:
                tmp.write(uploaded_file.getvalue())
                tmp_path = tmp.name

            try:
                from veg_change_engine.io.aoi import load_aoi, aoi_to_ee_geometry, get_aoi_area

                gdf = load_aoi(tmp_path)
                st.success(f"Loaded AOI: {len(gdf)} features")

                area_ha = get_aoi_area(gdf)
                st.info(f"Total area: {area_ha:.1f} hectares")

                # Store in session
                st.session_state.aoi_gdf = gdf
                aoi = aoi_to_ee_geometry(gdf)

            except Exception as e:
                st.error(f"Error loading file: {e}")

    elif upload_method == "Enter Coordinates":
        col1, col2 = st.columns(2)

        with col1:
            min_lon = st.number_input("Min Longitude", value=-75.7, format="%.4f")
            min_lat = st.number_input("Min Latitude", value=4.4, format="%.4f")

        with col2:
            max_lon = st.number_input("Max Longitude", value=-75.6, format="%.4f")
            max_lat = st.number_input("Max Latitude", value=4.5, format="%.4f")

        if st.button("Create Rectangle AOI"):
            aoi = ee.Geometry.Rectangle([min_lon, min_lat, max_lon, max_lat])
            st.success("AOI created!")

    # Run analysis
    st.markdown("---")
    st.subheader("2. Run Analysis")

    if aoi is not None or "aoi_gdf" in st.session_state:
        if aoi is None:
            from veg_change_engine.io.aoi import aoi_to_ee_geometry
            aoi = aoi_to_ee_geometry(st.session_state.aoi_gdf)

        col1, col2 = st.columns(2)

        with col1:
            run_analysis = st.button("🚀 Run Analysis", type="primary")

        with col2:
            export_to_drive = st.checkbox("Export to Google Drive")

        if run_analysis:
            progress = st.progress(0, text="Starting analysis...")

            try:
                from veg_change_engine.pipeline import analyze_vegetation_change
                from veg_change_engine.config import VegChangeConfig

                config = VegChangeConfig(
                    periods=periods,
                    indices=indices,
                    buffer_distance=buffer,
                    cloud_threshold=cloud_threshold,
                )

                progress.progress(10, text="Creating temporal composites...")

                results = analyze_vegetation_change(
                    aoi=aoi,
                    periods=periods,
                    indices=indices,
                    reference_period=reference,
                    config=config,
                )

                progress.progress(80, text="Generating visualizations...")

                # Store results
                st.session_state.analysis_results = results

                progress.progress(100, text="Complete!")

                st.success("Analysis complete!")

                # Display results summary
                st.subheader("Results Summary")

                col1, col2, col3 = st.columns(3)

                with col1:
                    st.metric("Composites Created", len(results["composites"]))

                with col2:
                    st.metric("Change Maps", len(results["changes"]))

                with col3:
                    st.metric("Indices Calculated", len(indices))

                # Show composites
                st.write("**Composites:**", list(results["composites"].keys()))
                st.write("**Change Maps:**", list(results["changes"].keys()))

                if export_to_drive:
                    st.info("Export tasks started - check Google Drive folder")

            except Exception as e:
                st.error(f"Analysis failed: {e}")
                progress.progress(0, text="Failed")

    else:
        st.warning("Please upload or define an Area of Interest first.")


if __name__ == "__main__":
    main()
