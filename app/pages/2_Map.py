"""
Map Page - Interactive visualization of analysis results.
"""

import streamlit as st
import ee

st.set_page_config(page_title="Map Viewer", page_icon="🗺️", layout="wide")


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
    st.title("🗺️ Map Viewer")

    init_ee()

    # Check for results
    if "analysis_results" not in st.session_state:
        st.warning("No analysis results available. Please run an analysis first.")
        st.page_link("pages/1_Analysis.py", label="Go to Analysis", icon="📊")
        return

    results = st.session_state.analysis_results

    # Sidebar controls
    st.sidebar.header("Layer Controls")

    # Select visualization type
    viz_type = st.sidebar.radio(
        "Visualization",
        options=["Composites", "Change Detection", "Comparison"],
    )

    if viz_type == "Composites":
        period = st.sidebar.selectbox(
            "Period",
            options=list(results["composites"].keys()),
        )

        layer_type = st.sidebar.selectbox(
            "Layer Type",
            options=["RGB", "NDVI", "NBR", "False Color"],
        )

        opacity = st.sidebar.slider("Opacity", 0.0, 1.0, 0.8)

    elif viz_type == "Change Detection":
        change_key = st.sidebar.selectbox(
            "Period Comparison",
            options=list(results["changes"].keys()),
        )

        change_band = st.sidebar.selectbox(
            "Band",
            options=["change_class", "dndvi", "dnbr"],
        )

        opacity = st.sidebar.slider("Opacity", 0.0, 1.0, 0.8)

    # Main map area
    st.subheader("Interactive Map")

    try:
        import folium
        from streamlit_folium import st_folium

        from veg_change_engine.viz.maps import (
            create_folium_map,
            add_composite_layer,
            add_change_layer,
            add_legend,
        )
        from veg_change_engine.viz.colors import get_vis_params

        # Get center from AOI if available
        center = (4.45, -75.65)  # Default
        if "aoi_gdf" in st.session_state:
            from veg_change_engine.io.aoi import get_aoi_centroid
            centroid = get_aoi_centroid(st.session_state.aoi_gdf)
            center = (centroid["lat"], centroid["lon"])

        # Create map
        m = create_folium_map(center=center, zoom=12)

        if viz_type == "Composites":
            composite = results["composites"][period]

            if layer_type == "RGB":
                vis_params = get_vis_params("rgb").to_dict()
                from veg_change_engine.viz.maps import add_ee_layer
                m = add_ee_layer(m, composite, vis_params, f"{period} RGB", opacity=opacity)

            elif layer_type == "NDVI":
                m = add_composite_layer(m, composite, period, "ndvi", opacity=opacity)
                m = add_legend(m, "ndvi")

            elif layer_type == "NBR":
                m = add_composite_layer(m, composite, period, "nbr", opacity=opacity)

            elif layer_type == "False Color":
                vis_params = get_vis_params("false_color").to_dict()
                from veg_change_engine.viz.maps import add_ee_layer
                m = add_ee_layer(m, composite, vis_params, f"{period} False Color", opacity=opacity)

        elif viz_type == "Change Detection":
            change_image = results["changes"][change_key]
            m = add_change_layer(m, change_image, change_key, change_band, opacity=opacity)

            if change_band == "change_class":
                m = add_legend(m, "change_class")

        # Display map
        st_data = st_folium(m, width=None, height=600)

    except ImportError:
        st.error("streamlit-folium is required: `pip install streamlit-folium`")

        # Fallback: show tile URL info
        st.subheader("Layer Information")

        if viz_type == "Composites":
            st.write(f"**Period:** {period}")
            st.write(f"**Layer:** {layer_type}")

        elif viz_type == "Change Detection":
            st.write(f"**Comparison:** {change_key}")
            st.write(f"**Band:** {change_band}")

    # Legend
    st.markdown("---")
    st.subheader("Legend")

    if viz_type == "Change Detection" and change_band == "change_class":
        from veg_change_engine.config import CHANGE_CLASSES

        cols = st.columns(5)
        for i, (class_num, info) in enumerate(CHANGE_CLASSES.items()):
            with cols[i]:
                st.markdown(
                    f'<div style="background-color: {info["color"]}; '
                    f'padding: 10px; text-align: center; border-radius: 5px;">'
                    f'{info["label"]}</div>',
                    unsafe_allow_html=True,
                )

    elif viz_type == "Composites" and layer_type == "NDVI":
        st.markdown("""
        | Value | Description |
        |-------|-------------|
        | < 0 | Water, bare soil |
        | 0-0.2 | Sparse vegetation |
        | 0.2-0.4 | Low vegetation |
        | 0.4-0.6 | Moderate vegetation |
        | > 0.6 | Dense vegetation |
        """)


if __name__ == "__main__":
    main()
