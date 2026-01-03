"""
Command-line interface for Vegetation Change Intelligence Platform.

Usage:
    veg-change analyze --aoi area.geojson --periods 1990s,present
    veg-change preview --aoi area.geojson --period present
    veg-change run-demo
"""

import typer
from typing import Optional, List
from pathlib import Path
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich import print as rprint

app = typer.Typer(
    name="veg-change",
    help="Vegetation Change Intelligence Platform - GEE-based satellite analysis",
    add_completion=False,
)

console = Console()


def init_ee():
    """Initialize Earth Engine."""
    import ee
    try:
        ee.Initialize()
    except Exception:
        console.print("[yellow]Authenticating with Earth Engine...[/yellow]")
        ee.Authenticate()
        ee.Initialize()
    console.print("[green]Earth Engine initialized[/green]")


@app.command()
def analyze(
    aoi: Path = typer.Option(..., "--aoi", "-a", help="Path to AOI file (KMZ, GeoJSON, Shapefile)"),
    name: str = typer.Option("Analysis Site", "--name", "-n", help="Site name"),
    periods: str = typer.Option("1990s,2000s,2010s,present", "--periods", "-p", help="Comma-separated periods"),
    indices: str = typer.Option("ndvi,nbr", "--indices", "-i", help="Comma-separated indices"),
    reference: str = typer.Option("1990s", "--reference", "-r", help="Reference period for change"),
    buffer: float = typer.Option(500.0, "--buffer", "-b", help="Buffer distance in meters"),
    export: bool = typer.Option(False, "--export", "-e", help="Export to Google Drive"),
    folder: str = typer.Option("VegChangeAnalysis", "--folder", "-f", help="Drive folder name"),
):
    """
    Run full vegetation change analysis.

    Example:
        veg-change analyze --aoi area.geojson --periods 1990s,present --export
    """
    init_ee()

    from veg_change_engine.pipeline import run_full_analysis

    period_list = [p.strip() for p in periods.split(",")]
    index_list = [i.strip() for i in indices.split(",")]

    console.print(Panel.fit(
        f"[bold blue]Vegetation Change Analysis[/bold blue]\n"
        f"Site: {name}\n"
        f"AOI: {aoi}\n"
        f"Periods: {period_list}\n"
        f"Indices: {index_list}",
        title="Configuration"
    ))

    results = run_full_analysis(
        aoi_path=str(aoi),
        site_name=name,
        periods=period_list,
        indices=index_list,
        reference_period=reference,
        buffer_distance=buffer,
        export=export,
        export_folder=folder,
    )

    # Display summary
    console.print("\n[bold green]Analysis Complete![/bold green]")

    if "aoi_area_ha" in results:
        console.print(f"Area analyzed: {results['aoi_area_ha']:.1f} hectares")

    console.print(f"Composites created: {len(results['composites'])}")
    console.print(f"Change maps created: {len(results['changes'])}")

    if export:
        console.print(f"\n[yellow]Exports started - check Google Drive folder: {folder}[/yellow]")


@app.command()
def preview(
    aoi: Path = typer.Option(..., "--aoi", "-a", help="Path to AOI file"),
    period: str = typer.Option("present", "--period", "-p", help="Period to preview"),
    index: str = typer.Option("ndvi", "--index", "-i", help="Index to display"),
    output: Optional[Path] = typer.Option(None, "--output", "-o", help="Save map to HTML file"),
):
    """
    Generate a quick preview map.

    Example:
        veg-change preview --aoi area.geojson --period present --index ndvi
    """
    init_ee()

    from veg_change_engine.pipeline import quick_preview
    from veg_change_engine.io.aoi import load_aoi, get_aoi_centroid
    from veg_change_engine.viz.maps import create_folium_map, add_index_layer

    console.print(f"[blue]Creating preview for {period}...[/blue]")

    # Create composite
    composite = quick_preview(str(aoi), period, index)

    # Get center
    gdf = load_aoi(str(aoi))
    center = get_aoi_centroid(gdf)

    # Create map
    m = create_folium_map(center=(center["lat"], center["lon"]), zoom=13)
    m = add_index_layer(m, composite, index, f"{period.upper()} {index.upper()}")

    if output:
        m.save(str(output))
        console.print(f"[green]Map saved to: {output}[/green]")
    else:
        # Try to display in browser
        output_file = Path("/tmp/veg_change_preview.html")
        m.save(str(output_file))
        console.print(f"[green]Map saved to: {output_file}[/green]")

        try:
            import webbrowser
            webbrowser.open(f"file://{output_file}")
        except Exception:
            pass


@app.command()
def periods():
    """Show available temporal periods."""
    from veg_change_engine.config import TEMPORAL_PERIODS

    table = Table(title="Available Temporal Periods")
    table.add_column("Period", style="cyan")
    table.add_column("Start", style="green")
    table.add_column("End", style="green")
    table.add_column("Sensors", style="yellow")
    table.add_column("Description", style="white")

    for name, info in TEMPORAL_PERIODS.items():
        sensors = ", ".join([s.split("/")[1] for s in info["sensors"]])
        table.add_row(
            name,
            info["start"],
            info["end"],
            sensors,
            info["description"],
        )

    console.print(table)


@app.command()
def indices():
    """Show available spectral indices."""
    from veg_change_engine.core.indices import INDEX_REGISTRY

    table = Table(title="Available Spectral Indices")
    table.add_column("Index", style="cyan")
    table.add_column("Description", style="white")

    for name, index_obj in INDEX_REGISTRY.items():
        table.add_row(name.upper(), index_obj.description)

    console.print(table)


@app.command("run-demo")
def run_demo(
    output: Path = typer.Option(Path("outputs"), "--output", "-o", help="Output directory"),
):
    """
    Run demo analysis with sample data.

    Creates a synthetic AOI and runs the full pipeline.
    """
    init_ee()

    from veg_change_engine.pipeline import analyze_vegetation_change
    import ee

    console.print(Panel.fit(
        "[bold blue]Vegetation Change Demo[/bold blue]\n"
        "Running analysis on sample Colombian coffee region",
        title="Demo Mode"
    ))

    # Create a sample AOI (Colombian coffee region)
    # Coordinates for a small area in Quindío
    aoi = ee.Geometry.Rectangle([-75.7, 4.4, -75.6, 4.5])

    console.print("[blue]Using sample AOI in Colombian Andes...[/blue]")

    results = analyze_vegetation_change(
        aoi=aoi,
        periods=["2010s", "present"],  # Shorter demo
        indices=["ndvi"],
        reference_period="2010s",
    )

    console.print("\n[bold green]Demo Complete![/bold green]")
    console.print(f"Composites: {list(results['composites'].keys())}")
    console.print(f"Changes: {list(results['changes'].keys())}")

    console.print("\n[yellow]Note: Run with --export to save results to Google Drive[/yellow]")


@app.command()
def version():
    """Show version information."""
    from veg_change_engine import __version__

    console.print(f"[bold]Vegetation Change Intelligence Platform[/bold]")
    console.print(f"Version: {__version__}")
    console.print(f"Python GEE-based satellite analysis for vegetation monitoring")


@app.command()
def auth():
    """Authenticate with Google Earth Engine."""
    import ee

    console.print("[blue]Starting Earth Engine authentication...[/blue]")
    ee.Authenticate()
    ee.Initialize()
    console.print("[green]Authentication successful![/green]")


def main():
    """Entry point for the CLI."""
    app()


if __name__ == "__main__":
    main()
