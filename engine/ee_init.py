"""
Earth Engine initialization module with robust authentication handling.

Supports multiple authentication methods:
1. Persistent credentials (default ~/.config/earthengine/)
2. Service account authentication
3. High-volume endpoint for heavy workloads
4. Project-based authentication

This module provides graceful fallbacks and clear error messages.
"""

import os
import json
from pathlib import Path
from typing import Optional
from dataclasses import dataclass
import ee


@dataclass
class EECredentials:
    """Earth Engine credentials configuration."""
    project: Optional[str] = None
    service_account: Optional[str] = None
    private_key_file: Optional[str] = None
    use_high_volume: bool = False


class EEInitializer:
    """
    Robust Earth Engine initializer with multiple auth strategies.

    Usage:
        >>> initializer = EEInitializer()
        >>> initializer.initialize()  # Uses best available method

        # Or with specific project
        >>> initializer.initialize(project="my-gee-project")

        # Or with service account
        >>> initializer.initialize(
        ...     service_account="my-sa@project.iam.gserviceaccount.com",
        ...     private_key_file="key.json"
        ... )
    """

    def __init__(self):
        self._initialized = False
        self._project = None
        self._method = None

    @property
    def is_initialized(self) -> bool:
        """Check if EE is initialized."""
        return self._initialized

    @property
    def project(self) -> Optional[str]:
        """Get current project ID."""
        return self._project

    @property
    def auth_method(self) -> Optional[str]:
        """Get authentication method used."""
        return self._method

    def initialize(
        self,
        project: Optional[str] = None,
        service_account: Optional[str] = None,
        private_key_file: Optional[str] = None,
        use_high_volume: bool = False,
        force: bool = False,
    ) -> bool:
        """
        Initialize Earth Engine with robust error handling.

        Args:
            project: GCP project ID (optional, uses default if not specified)
            service_account: Service account email for non-interactive auth
            private_key_file: Path to service account JSON key file
            use_high_volume: Use high-volume endpoint for heavy workloads
            force: Force re-initialization even if already initialized

        Returns:
            True if initialization successful, False otherwise

        Raises:
            EEAuthenticationError: If authentication fails
        """
        if self._initialized and not force:
            return True

        # Try service account first if provided
        if service_account and private_key_file:
            return self._init_service_account(
                service_account, private_key_file, project, use_high_volume
            )

        # Try persistent credentials
        if self._has_persistent_credentials():
            return self._init_persistent(project, use_high_volume)

        # Need to authenticate
        return self._init_interactive(project, use_high_volume)

    def _has_persistent_credentials(self) -> bool:
        """Check if persistent credentials exist."""
        credentials_path = Path.home() / ".config" / "earthengine" / "credentials"
        return credentials_path.exists()

    def _init_persistent(
        self,
        project: Optional[str],
        use_high_volume: bool
    ) -> bool:
        """Initialize using persistent credentials."""
        try:
            opt_url = (
                "https://earthengine-highvolume.googleapis.com"
                if use_high_volume else None
            )

            if project:
                ee.Initialize(project=project, opt_url=opt_url)
            else:
                ee.Initialize(opt_url=opt_url)

            self._initialized = True
            self._project = project or self._detect_project()
            self._method = "persistent_credentials"
            return True

        except ee.EEException as e:
            error_msg = str(e)

            # Handle common errors
            if "not signed up" in error_msg.lower():
                raise EEAuthenticationError(
                    "Earth Engine account not registered. "
                    "Visit https://earthengine.google.com/signup/"
                )
            elif "project" in error_msg.lower():
                raise EEAuthenticationError(
                    "Project not found or not authorized. "
                    "Specify a valid project with: initialize(project='your-project-id')"
                )
            else:
                raise EEAuthenticationError(f"Initialization failed: {error_msg}")

    def _init_service_account(
        self,
        service_account: str,
        private_key_file: str,
        project: Optional[str],
        use_high_volume: bool,
    ) -> bool:
        """Initialize using service account."""
        try:
            credentials = ee.ServiceAccountCredentials(
                service_account,
                private_key_file
            )

            opt_url = (
                "https://earthengine-highvolume.googleapis.com"
                if use_high_volume else None
            )

            ee.Initialize(credentials, project=project, opt_url=opt_url)

            self._initialized = True
            self._project = project
            self._method = "service_account"
            return True

        except Exception as e:
            raise EEAuthenticationError(
                f"Service account authentication failed: {e}"
            )

    def _init_interactive(
        self,
        project: Optional[str],
        use_high_volume: bool
    ) -> bool:
        """Initialize with interactive authentication."""
        print("\n" + "=" * 60)
        print("EARTH ENGINE AUTHENTICATION REQUIRED")
        print("=" * 60)
        print("\nNo persistent credentials found.")
        print("Please authenticate with one of these methods:\n")
        print("1. Run in terminal:")
        print("   earthengine authenticate")
        print("\n2. Or run in Python:")
        print("   import ee")
        print("   ee.Authenticate()")
        print("   ee.Initialize()")
        print("\n" + "=" * 60 + "\n")

        raise EEAuthenticationError(
            "Interactive authentication required. "
            "Run 'earthengine authenticate' in terminal."
        )

    def _detect_project(self) -> Optional[str]:
        """Try to detect the current project."""
        try:
            # Try to get project from credentials file
            credentials_path = Path.home() / ".config" / "earthengine" / "credentials"
            if credentials_path.exists():
                with open(credentials_path, "r") as f:
                    creds = json.load(f)
                    return creds.get("project_id")
        except Exception:
            pass
        return None

    def authenticate(self, auth_mode: str = "notebook") -> bool:
        """
        Run interactive authentication.

        Args:
            auth_mode: Authentication mode ('notebook', 'localhost', 'gcloud')

        Returns:
            True if authentication successful
        """
        try:
            ee.Authenticate(auth_mode=auth_mode)
            return True
        except Exception as e:
            raise EEAuthenticationError(f"Authentication failed: {e}")

    def test_connection(self) -> dict:
        """
        Test Earth Engine connection and return status.

        Returns:
            Dictionary with connection status and details
        """
        if not self._initialized:
            return {
                "connected": False,
                "error": "Not initialized",
                "project": None,
                "method": None,
            }

        try:
            # Simple test - get current date
            result = ee.Date("2024-01-01").getInfo()
            return {
                "connected": True,
                "project": self._project,
                "method": self._method,
                "test_result": result,
            }
        except Exception as e:
            return {
                "connected": False,
                "error": str(e),
                "project": self._project,
                "method": self._method,
            }


class EEAuthenticationError(Exception):
    """Custom exception for Earth Engine authentication errors."""
    pass


# =============================================================================
# CONVENIENCE FUNCTIONS
# =============================================================================

# Global initializer instance
_initializer = EEInitializer()


def initialize_ee(
    project: Optional[str] = None,
    service_account: Optional[str] = None,
    private_key_file: Optional[str] = None,
    use_high_volume: bool = False,
    force: bool = False,
) -> bool:
    """
    Initialize Earth Engine with best available method.

    This is the recommended way to initialize EE in the platform.

    Args:
        project: GCP project ID
        service_account: Service account email
        private_key_file: Path to service account key
        use_high_volume: Use high-volume endpoint
        force: Force re-initialization

    Returns:
        True if successful

    Example:
        >>> from engine.ee_init import initialize_ee
        >>> initialize_ee()  # Uses persistent credentials
        >>> initialize_ee(project="my-project")  # Specific project
    """
    return _initializer.initialize(
        project=project,
        service_account=service_account,
        private_key_file=private_key_file,
        use_high_volume=use_high_volume,
        force=force,
    )


def is_ee_initialized() -> bool:
    """Check if Earth Engine is initialized."""
    return _initializer.is_initialized


def get_ee_status() -> dict:
    """Get Earth Engine connection status."""
    return _initializer.test_connection()


def authenticate_ee(auth_mode: str = "notebook") -> bool:
    """Run interactive Earth Engine authentication."""
    return _initializer.authenticate(auth_mode)


# =============================================================================
# STREAMLIT HELPER
# =============================================================================

def init_ee_streamlit(
    project: Optional[str] = None,
    show_status: bool = True,
) -> bool:
    """
    Initialize Earth Engine for Streamlit apps.

    Handles session state and provides UI feedback.

    Args:
        project: GCP project ID
        show_status: Show status messages in Streamlit

    Returns:
        True if initialized successfully
    """
    try:
        import streamlit as st
    except ImportError:
        return initialize_ee(project=project)

    # Check session state
    if "ee_initialized" in st.session_state and st.session_state.ee_initialized:
        return True

    try:
        success = initialize_ee(project=project)
        st.session_state.ee_initialized = success

        if show_status and success:
            st.success("Earth Engine connected")

        return success

    except EEAuthenticationError as e:
        st.session_state.ee_initialized = False

        if show_status:
            st.error(f"{str(e)}")
            st.info("""
            **To authenticate Earth Engine:**

            1. Open a terminal and run:
            ```bash
            earthengine authenticate
            ```

            2. Follow the browser prompts to authorize

            3. Refresh this page
            """)

        return False
