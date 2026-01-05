"""
AlphaEarth satellite embeddings integration.

Provides access to Google's pre-trained satellite embedding model for:
- Semantic change detection
- Feature extraction for ML models
- Similarity analysis between locations/times

The embeddings capture semantic meaning from Sentinel-2 imagery,
enabling more sophisticated change detection than spectral indices alone.

Reference:
    https://developers.google.com/earth-engine/datasets/catalog/GOOGLE_SATELLITE_EMBEDDING_V1_ANNUAL
"""

from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass
import ee


# =============================================================================
# CONFIGURATION
# =============================================================================

# AlphaEarth collection ID
ALPHAEARTH_COLLECTION = "GOOGLE/SATELLITE_EMBEDDING/V1/ANNUAL"

# Embedding dimensions
EMBEDDING_DIM = 1536

# Available years in the collection
AVAILABLE_YEARS = list(range(2017, 2024))  # 2017-2023


@dataclass
class EmbeddingConfig:
    """Configuration for embedding operations."""

    # Similarity metrics
    similarity_metric: str = "cosine"  # "cosine", "euclidean", "manhattan"

    # Change detection thresholds
    similarity_threshold: float = 0.85  # Below this = significant change

    # Sampling scale for statistics
    scale: int = 10  # AlphaEarth native resolution is 10m


# =============================================================================
# ALPHAEARTH CLIENT
# =============================================================================

class AlphaEarthClient:
    """
    Client for working with AlphaEarth satellite embeddings.

    AlphaEarth provides 1536-dimensional embeddings that capture semantic
    meaning from Sentinel-2 imagery. These embeddings are useful for:
    - Detecting semantic changes (land use, not just spectral)
    - Finding similar locations
    - Feature extraction for machine learning

    Example:
        >>> client = AlphaEarthClient()
        >>> emb_2020 = client.get_embedding(aoi, 2020)
        >>> emb_2023 = client.get_embedding(aoi, 2023)
        >>> similarity = client.compute_similarity(emb_2020, emb_2023)
    """

    def __init__(self, config: Optional[EmbeddingConfig] = None):
        """
        Initialize AlphaEarth client.

        Args:
            config: Optional configuration object
        """
        self.config = config or EmbeddingConfig()
        self.collection = ee.ImageCollection(ALPHAEARTH_COLLECTION)

    def get_embedding(
        self,
        aoi: ee.Geometry,
        year: int,
    ) -> ee.Image:
        """
        Get satellite embedding for a specific year.

        Args:
            aoi: Area of interest
            year: Year to retrieve (2017-2023)

        Returns:
            ee.Image with 1536 embedding bands

        Raises:
            ValueError: If year is not available
        """
        if year not in AVAILABLE_YEARS:
            raise ValueError(
                f"Year {year} not available. "
                f"Available years: {AVAILABLE_YEARS[0]}-{AVAILABLE_YEARS[-1]}"
            )

        # Filter to specific year
        embedding = (
            self.collection
            .filter(ee.Filter.calendarRange(year, year, 'year'))
            .first()
            .clip(aoi)
        )

        return embedding

    def get_multi_year_embeddings(
        self,
        aoi: ee.Geometry,
        years: List[int],
    ) -> Dict[int, ee.Image]:
        """
        Get embeddings for multiple years.

        Args:
            aoi: Area of interest
            years: List of years to retrieve

        Returns:
            Dictionary mapping year to embedding image
        """
        embeddings = {}
        for year in years:
            embeddings[year] = self.get_embedding(aoi, year)
        return embeddings

    def compute_similarity(
        self,
        emb1: ee.Image,
        emb2: ee.Image,
        method: Optional[str] = None,
    ) -> ee.Image:
        """
        Compute similarity between two embeddings.

        Args:
            emb1: First embedding image
            emb2: Second embedding image
            method: Similarity metric ("cosine", "euclidean", "manhattan")
                   Defaults to config setting.

        Returns:
            ee.Image with similarity values (0-1 for cosine, higher=more similar)
        """
        method = method or self.config.similarity_metric

        if method == "cosine":
            return self._cosine_similarity(emb1, emb2)
        elif method == "euclidean":
            return self._euclidean_distance(emb1, emb2)
        elif method == "manhattan":
            return self._manhattan_distance(emb1, emb2)
        else:
            raise ValueError(f"Unknown similarity method: {method}")

    def _cosine_similarity(
        self,
        emb1: ee.Image,
        emb2: ee.Image,
    ) -> ee.Image:
        """
        Compute cosine similarity between embeddings.

        Cosine similarity = (A · B) / (||A|| * ||B||)

        Returns:
            ee.Image with similarity values (0-1, higher=more similar)
        """
        # Dot product
        dot_product = emb1.multiply(emb2).reduce(ee.Reducer.sum())

        # Magnitudes
        mag1 = emb1.pow(2).reduce(ee.Reducer.sum()).sqrt()
        mag2 = emb2.pow(2).reduce(ee.Reducer.sum()).sqrt()

        # Cosine similarity
        similarity = dot_product.divide(mag1.multiply(mag2))

        return similarity.rename('cosine_similarity')

    def _euclidean_distance(
        self,
        emb1: ee.Image,
        emb2: ee.Image,
    ) -> ee.Image:
        """
        Compute Euclidean distance between embeddings.

        Returns:
            ee.Image with distance values (lower=more similar)
        """
        diff = emb1.subtract(emb2)
        distance = diff.pow(2).reduce(ee.Reducer.sum()).sqrt()

        return distance.rename('euclidean_distance')

    def _manhattan_distance(
        self,
        emb1: ee.Image,
        emb2: ee.Image,
    ) -> ee.Image:
        """
        Compute Manhattan distance between embeddings.

        Returns:
            ee.Image with distance values (lower=more similar)
        """
        diff = emb1.subtract(emb2).abs()
        distance = diff.reduce(ee.Reducer.sum())

        return distance.rename('manhattan_distance')

    def detect_change_embedding(
        self,
        aoi: ee.Geometry,
        year_before: int,
        year_after: int,
    ) -> Dict[str, Any]:
        """
        Detect semantic changes using embeddings.

        This captures land use changes that may not be visible
        in traditional spectral indices.

        Args:
            aoi: Area of interest
            year_before: Earlier year
            year_after: Later year

        Returns:
            Dictionary with:
            - similarity: Similarity image
            - change_mask: Binary mask of significant changes
            - statistics: Summary statistics
        """
        # Get embeddings
        emb_before = self.get_embedding(aoi, year_before)
        emb_after = self.get_embedding(aoi, year_after)

        # Compute similarity
        similarity = self.compute_similarity(emb_before, emb_after)

        # Create change mask (low similarity = significant change)
        change_mask = similarity.lt(self.config.similarity_threshold)

        # Calculate statistics
        stats = similarity.reduceRegion(
            reducer=ee.Reducer.mean()
                .combine(ee.Reducer.stdDev(), '', True)
                .combine(ee.Reducer.min(), '', True)
                .combine(ee.Reducer.max(), '', True),
            geometry=aoi,
            scale=self.config.scale,
            maxPixels=1e9,
        )

        return {
            "similarity": similarity,
            "change_mask": change_mask.rename('embedding_change'),
            "emb_before": emb_before,
            "emb_after": emb_after,
            "statistics": stats,
        }

    def extract_features_for_ml(
        self,
        aoi: ee.Geometry,
        year: int,
        sample_points: Optional[ee.FeatureCollection] = None,
        num_samples: int = 1000,
    ) -> ee.FeatureCollection:
        """
        Extract embedding features for machine learning.

        Samples embedding values at points for use as ML features.

        Args:
            aoi: Area of interest
            year: Year to extract features from
            sample_points: Optional pre-defined sample points.
                          If None, generates random points.
            num_samples: Number of random samples if sample_points is None

        Returns:
            ee.FeatureCollection with embedding values as properties
        """
        embedding = self.get_embedding(aoi, year)

        if sample_points is None:
            sample_points = ee.FeatureCollection.randomPoints(
                region=aoi,
                points=num_samples,
                seed=42,
            )

        # Sample embedding values
        features = embedding.sampleRegions(
            collection=sample_points,
            scale=self.config.scale,
            geometries=True,
        )

        return features

    def get_temporal_trajectory(
        self,
        aoi: ee.Geometry,
        years: Optional[List[int]] = None,
    ) -> Dict[str, Any]:
        """
        Get temporal trajectory of embeddings.

        Useful for analyzing how a location changes over time.

        Args:
            aoi: Area of interest
            years: Years to analyze (defaults to all available)

        Returns:
            Dictionary with:
            - embeddings: Dict of year -> embedding
            - similarities: List of year-to-year similarities
        """
        if years is None:
            years = AVAILABLE_YEARS

        years = sorted(years)
        embeddings = self.get_multi_year_embeddings(aoi, years)

        # Calculate year-to-year similarities
        similarities = []
        for i in range(len(years) - 1):
            y1, y2 = years[i], years[i + 1]
            sim = self.compute_similarity(embeddings[y1], embeddings[y2])
            similarities.append({
                "year_from": y1,
                "year_to": y2,
                "similarity": sim,
            })

        return {
            "embeddings": embeddings,
            "similarities": similarities,
            "years": years,
        }


# =============================================================================
# CONVENIENCE FUNCTIONS
# =============================================================================

def get_alphaearth_embedding(
    aoi: ee.Geometry,
    year: int,
) -> ee.Image:
    """
    Get AlphaEarth embedding for a year.

    Args:
        aoi: Area of interest
        year: Year (2017-2023)

    Returns:
        ee.Image with 1536 embedding bands
    """
    client = AlphaEarthClient()
    return client.get_embedding(aoi, year)


def detect_semantic_change(
    aoi: ee.Geometry,
    year_before: int,
    year_after: int,
    similarity_threshold: float = 0.85,
) -> Dict[str, Any]:
    """
    Detect semantic changes using satellite embeddings.

    This captures land use and land cover changes that may not
    be visible in traditional spectral indices like NDVI.

    Args:
        aoi: Area of interest
        year_before: Earlier year
        year_after: Later year
        similarity_threshold: Threshold for significant change

    Returns:
        Dictionary with similarity, change_mask, and statistics

    Example:
        >>> results = detect_semantic_change(aoi, 2018, 2023)
        >>> change_map = results['change_mask']
    """
    config = EmbeddingConfig(similarity_threshold=similarity_threshold)
    client = AlphaEarthClient(config)
    return client.detect_change_embedding(aoi, year_before, year_after)


def combine_with_spectral_change(
    spectral_change: ee.Image,
    embedding_change: ee.Image,
    weights: Tuple[float, float] = (0.5, 0.5),
) -> ee.Image:
    """
    Combine spectral and embedding-based change detection.

    Creates a hybrid change map that leverages both approaches.

    Args:
        spectral_change: Change from spectral indices (e.g., dNDVI)
        embedding_change: Similarity from embeddings
        weights: Weights for (spectral, embedding)

    Returns:
        ee.Image with combined change metric
    """
    # Normalize spectral change to 0-1 (invert so high = change)
    # Assuming spectral_change is like dNDVI where negative = loss
    spectral_normalized = spectral_change.abs()

    # Invert embedding similarity (so high = change)
    embedding_inverted = ee.Image(1).subtract(embedding_change)

    # Weighted combination
    combined = (
        spectral_normalized.multiply(weights[0])
        .add(embedding_inverted.multiply(weights[1]))
    ).rename('combined_change')

    return combined
