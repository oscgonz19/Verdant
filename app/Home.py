"""
Vegetation Change Intelligence Platform - Streamlit Dashboard

Interactive web application for vegetation change analysis using
Google Earth Engine satellite imagery.
"""

# Fix PROJ_LIB before any geo imports
import os
import sys

# Set PROJ path for this conda environment
_conda_prefix = os.environ.get('CONDA_PREFIX', '')
if _conda_prefix:
    os.environ['PROJ_LIB'] = os.path.join(_conda_prefix, 'share', 'proj')
    os.environ['PROJ_DATA'] = os.path.join(_conda_prefix, 'share', 'proj')
else:
    # Fallback to buenavista-hazard env
    os.environ['PROJ_LIB'] = '/home/ozz/miniconda3/envs/buenavista-hazard/share/proj'
    os.environ['PROJ_DATA'] = '/home/ozz/miniconda3/envs/buenavista-hazard/share/proj'

import streamlit as st

st.set_page_config(
    page_title="Vegetation Change Intelligence",
    page_icon="🌿",
    layout="wide",
    initial_sidebar_state="expanded",
)


DEFAULT_PROJECT = "geoconcret-474619"

def init_ee_with_ui():
    """Initialize Earth Engine with user-friendly UI."""
    import ee

    # Already initialized
    if "ee_initialized" in st.session_state and st.session_state.ee_initialized:
        return True

    # Try to initialize with project
    try:
        project = st.session_state.get("ee_project", DEFAULT_PROJECT)
        ee.Initialize(project=project)
        st.session_state.ee_initialized = True
        st.session_state.ee_project = project
        return True

    except Exception:
        # Try without project
        try:
            ee.Initialize()
            st.session_state.ee_initialized = True
            return True
        except Exception:
            st.session_state.ee_initialized = False
            return False


def run_notebook_auth():
    """Run Earth Engine notebook authentication flow."""
    import ee
    import subprocess
    import sys

    try:
        # Use notebook auth mode which generates a URL
        ee.Authenticate(auth_mode='notebook')
        ee.Initialize()
        return True, None
    except Exception as e:
        return False, str(e)


def show_ee_auth_instructions():
    """Show Earth Engine authentication options."""
    import ee

    st.warning("⚠️ Earth Engine authentication required")

    # Show error if there was one
    if "ee_auth_error" in st.session_state:
        st.error(f"Error: {st.session_state.ee_auth_error}")

    st.markdown("### 🔐 Connect to Google Earth Engine")

    # Quick connect with Project ID (most common case)
    st.markdown("**Enter your Google Cloud Project ID:**")

    col1, col2 = st.columns([3, 1])

    with col1:
        project_id = st.text_input(
            "Project ID",
            value=DEFAULT_PROJECT,
            placeholder="my-gee-project",
            key="ee_project_input",
            label_visibility="collapsed"
        )

    with col2:
        connect_btn = st.button("🔗 Connect", type="primary", use_container_width=True)

    if connect_btn and project_id:
        with st.spinner("Connecting to Earth Engine..."):
            try:
                ee.Initialize(project=project_id)
                st.session_state.ee_initialized = True
                st.session_state.ee_project = project_id
                st.success(f"✅ Connected to: {project_id}")
                st.balloons()
                st.rerun()
            except Exception as e:
                st.session_state.ee_auth_error = str(e)
                st.error(f"❌ Connection failed: {e}")

    st.divider()

    # Additional options
    st.markdown("**Other options:**")
    tab1, tab2 = st.tabs(["💻 Terminal Auth", "❓ Help"])

    with tab1:
        st.markdown("**If credentials aren't set up, run in terminal:**")

        st.code("earthengine authenticate", language="bash")

        st.markdown("Then refresh this page.")

        if st.button("🔄 Refresh Connection", use_container_width=True):
            st.session_state.pop("ee_initialized", None)
            st.session_state.pop("ee_auth_error", None)
            st.rerun()

    with tab2:
        st.markdown("""
        ### How to get a Project ID:

        1. Go to [Google Cloud Console](https://console.cloud.google.com/)
        2. Create a new project or select existing
        3. Enable [Earth Engine API](https://console.cloud.google.com/apis/library/earthengine.googleapis.com)
        4. Copy the Project ID and paste above

        ### Don't have Earth Engine access?

        [Sign up for Earth Engine](https://earthengine.google.com/signup/)

        ### Common errors:

        - **"Not signed up"**: Register at earthengine.google.com
        - **"Project not found"**: Enable EE API in GCP Console
        - **"Permission denied"**: Run `earthengine authenticate`
        """)


def main():
    # Header
    st.title("🌿 Vegetation Change Intelligence Platform")

    # Sidebar - EE Status
    with st.sidebar:
        st.header("🔌 Connection Status")

        ee_ready = init_ee_with_ui()

        if ee_ready:
            st.success("✅ Earth Engine Connected")

            # Show connection details
            try:
                from veg_change_engine.ee_init import get_ee_status
                status = get_ee_status()
                if status.get("project"):
                    st.caption(f"Project: {status['project']}")
            except Exception:
                pass
        else:
            st.error("❌ Not Connected")

        st.divider()

        # Navigation info
        st.header("📍 Navigation")
        st.markdown("""
        - **Home**: Overview & status
        - **Analysis**: Run change detection
        - **Map**: View results
        """)

    # Main content
    if not ee_ready:
        show_ee_auth_instructions()
        return

    # Platform overview
    st.markdown("""
    **GEE-based satellite analysis for detecting and quantifying vegetation change**

    This platform analyzes multi-decadal satellite imagery to track vegetation dynamics:
    """)

    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.metric("📅 Temporal Range", "1985-2024")
    with col2:
        st.metric("🛰️ Sensors", "4")
    with col3:
        st.metric("📊 Indices", "5")
    with col4:
        st.metric("🎯 Resolution", "30m")

    # Feature cards
    st.subheader("✨ Features")

    col1, col2 = st.columns(2)

    with col1:
        with st.container(border=True):
            st.markdown("### 🛰️ Multi-Sensor Fusion")
            st.markdown("""
            Combines imagery from multiple satellites:
            - Landsat 5 TM (1985-2012)
            - Landsat 7 ETM+ (1999-present)
            - Landsat 8 OLI (2013-present)
            - Sentinel-2 MSI (2017-present)
            """)

        with st.container(border=True):
            st.markdown("### 📊 Spectral Indices")
            st.markdown("""
            Calculate vegetation and change metrics:
            - **NDVI**: Vegetation health
            - **NBR**: Burn severity
            - **NDWI**: Water content
            - **EVI**: Enhanced vegetation
            - **NDMI**: Moisture index
            """)

    with col2:
        with st.container(border=True):
            st.markdown("### 🔄 Change Detection")
            st.markdown("""
            Classify vegetation change:
            - 🔴 Strong Loss
            - 🟠 Moderate Loss
            - 🟡 Stable
            - 🟢 Moderate Gain
            - 🌲 Strong Gain
            """)

        with st.container(border=True):
            st.markdown("### 💾 Smart Caching")
            st.markdown("""
            Avoid repeated API consumption:
            - EE Asset persistence
            - Local metadata cache
            - Tile URL caching (24h TTL)
            """)

    # Available periods
    st.subheader("📅 Temporal Periods")

    from veg_change_engine.config import TEMPORAL_PERIODS

    period_data = []
    for name, info in TEMPORAL_PERIODS.items():
        sensors = ", ".join([s.split("/")[1] for s in info["sensors"]])
        period_data.append({
            "Period": name.upper(),
            "Years": f"{info['start'][:4]} - {info['end'][:4]}",
            "Sensors": sensors,
            "Description": info["description"],
        })

    st.dataframe(period_data, use_container_width=True, hide_index=True)

    # Quick actions
    st.subheader("🚀 Quick Start")

    col1, col2, col3 = st.columns(3)

    with col1:
        if st.button("📊 Run Analysis", use_container_width=True):
            st.switch_page("pages/1_Analysis.py")

    with col2:
        if st.button("🗺️ View Map", use_container_width=True):
            st.switch_page("pages/2_Map.py")

    with col3:
        if st.button("🎯 Run Demo", use_container_width=True):
            run_demo()

    # Footer
    st.divider()
    st.caption("""
    Vegetation Change Intelligence Platform v1.0.0 |
    Built with Google Earth Engine + Streamlit |
    [GitHub](https://github.com/oscgonz19/vegetation-change-platform)
    """)


def run_demo():
    """Run a quick demo analysis."""
    import ee

    st.subheader("🎯 Demo Analysis")

    with st.status("Running demo on Colombian Andes region...", expanded=True) as status:
        try:
            st.write("Creating sample AOI...")
            aoi = ee.Geometry.Rectangle([-75.7, 4.4, -75.6, 4.5])

            st.write("Loading configuration...")
            from veg_change_engine.config import VegChangeConfig

            config = VegChangeConfig(
                site_name="Demo Site",
                periods=["2010s", "present"],
                indices=["ndvi"],
            )

            st.write("Running analysis (this may take a moment)...")
            from veg_change_engine.pipeline import analyze_vegetation_change

            results = analyze_vegetation_change(
                aoi=aoi,
                periods=["2010s", "present"],
                indices=["ndvi"],
                reference_period="2010s",
                config=config,
            )

            status.update(label="Demo complete!", state="complete", expanded=False)

            # Show results
            col1, col2 = st.columns(2)
            with col1:
                st.success(f"✅ Composites: {list(results['composites'].keys())}")
            with col2:
                st.success(f"✅ Changes: {list(results['changes'].keys())}")

            st.session_state.analysis_results = results
            st.info("Results saved. Go to Map page to visualize.")

        except Exception as e:
            status.update(label="Demo failed", state="error")
            st.error(f"Error: {e}")


if __name__ == "__main__":
    main()
