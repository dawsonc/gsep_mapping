"""Analysis functions for GSEP spatial overlap computations."""

from dataclasses import dataclass
from typing import Optional

import geopandas as gpd
import pandas as pd

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))
from config import MA_STATE_PLANE


@dataclass
class OverlapStats:
    """Statistics for spatial overlap analysis."""

    in_region_count: int
    outside_region_count: int
    total_count: int
    in_region_pct: float
    outside_region_pct: float
    label_in: str
    label_out: str

    def to_series(self) -> pd.Series:
        """Convert to pandas Series for plotting."""
        return pd.Series(
            {self.label_in: self.in_region_count, self.label_out: self.outside_region_count}
        )

    def to_pct_series(self) -> pd.Series:
        """Convert to percentage Series."""
        return pd.Series(
            {self.label_in: self.in_region_pct, self.label_out: self.outside_region_pct}
        )


@dataclass
class LengthStats:
    """Statistics for line length overlap analysis."""

    in_region_length: float  # in miles
    outside_region_length: float  # in miles
    total_length: float  # in miles
    in_region_pct: float
    outside_region_pct: float
    label_in: str
    label_out: str

    def to_series(self) -> pd.Series:
        """Convert to pandas Series for plotting."""
        return pd.Series(
            {self.label_in: self.in_region_length, self.label_out: self.outside_region_length}
        )

    def to_pct_series(self) -> pd.Series:
        """Convert to percentage Series."""
        return pd.Series(
            {self.label_in: self.in_region_pct, self.label_out: self.outside_region_pct}
        )


def compute_point_overlap(
    points_gdf: gpd.GeoDataFrame,
    region_gdf: gpd.GeoDataFrame,
    region_name: str = "Region",
) -> tuple[gpd.GeoDataFrame, OverlapStats]:
    """
    Compute overlap between point features and a region layer.

    Adds a boolean column 'is_in_{region_name}' to the points GeoDataFrame.

    Args:
        points_gdf: GeoDataFrame with point geometries.
        region_gdf: GeoDataFrame with polygon geometries defining the region.
        region_name: Name for the region (used in column names and labels).

    Returns:
        Tuple of (updated points_gdf with overlap column, OverlapStats).
    """
    # Ensure same CRS
    points_proj = points_gdf.to_crs(region_gdf.crs)

    # Spatial join to find points intersecting region
    points_in_region = gpd.sjoin(
        points_proj, region_gdf, how="inner", predicate="intersects"
    )

    # Add boolean column
    col_name = f"is_in_{region_name.lower().replace(' ', '_')}"
    points_gdf = points_gdf.copy()
    points_gdf[col_name] = points_gdf.index.isin(points_in_region.index)

    # Compute stats
    in_count = points_gdf[col_name].sum()
    total = len(points_gdf)
    out_count = total - in_count

    stats = OverlapStats(
        in_region_count=in_count,
        outside_region_count=out_count,
        total_count=total,
        in_region_pct=round(in_count / total * 100, 1) if total > 0 else 0,
        outside_region_pct=round(out_count / total * 100, 1) if total > 0 else 0,
        label_in=f"In {region_name}",
        label_out=f"Not in {region_name}",
    )

    return points_gdf, stats


def compute_line_length_in_region(
    lines_gdf: gpd.GeoDataFrame,
    region_gdf: gpd.GeoDataFrame,
    region_name: str = "Region",
    filter_col: Optional[str] = None,
    filter_value: bool = True,
) -> tuple[gpd.GeoDataFrame, LengthStats]:
    """
    Compute length of line features within a region.

    Args:
        lines_gdf: GeoDataFrame with line geometries.
        region_gdf: GeoDataFrame with polygon geometries defining the region.
        region_name: Name for the region (used in column names).
        filter_col: Optional column to filter lines before analysis.
        filter_value: Value to filter on if filter_col is provided.

    Returns:
        Tuple of (updated lines_gdf with length column, LengthStats).
    """
    col_name = f"length_in_{region_name.lower().replace(' ', '_')}"

    # Project to state plane for accurate length calculations
    lines_proj = lines_gdf.to_crs(MA_STATE_PLANE)
    region_proj = region_gdf.to_crs(MA_STATE_PLANE)

    # Compute intersection length
    region_union = region_proj.geometry.union_all()
    lines_gdf = lines_gdf.copy()
    lines_gdf[col_name] = (
        lines_proj.geometry.intersection(region_union).length.fillna(0.0)
    )

    # Filter if requested
    if filter_col:
        subset = lines_gdf[lines_gdf[filter_col] == filter_value]
    else:
        subset = lines_gdf

    # Compute stats (convert meters to miles: m -> km -> miles)
    in_length_m = subset[col_name].sum()
    total_length_m = lines_proj[lines_proj.index.isin(subset.index)].geometry.length.sum()
    out_length_m = total_length_m - in_length_m

    # Convert to miles
    m_to_miles = 1e-3 * 0.621371
    in_length = in_length_m * m_to_miles
    out_length = out_length_m * m_to_miles
    total_length = total_length_m * m_to_miles

    stats = LengthStats(
        in_region_length=in_length,
        outside_region_length=out_length,
        total_length=total_length,
        in_region_pct=round(in_length / total_length * 100, 1) if total_length > 0 else 0,
        outside_region_pct=round(out_length / total_length * 100, 1) if total_length > 0 else 0,
        label_in=f"In {region_name}",
        label_out=f"Not in {region_name}",
    )

    return lines_gdf, stats


def add_equity_region_flags(
    gdf: gpd.GeoDataFrame,
    layers: dict[str, gpd.GeoDataFrame],
) -> gpd.GeoDataFrame:
    """
    Add overlap flags for multiple equity region layers.

    Args:
        gdf: GeoDataFrame to analyze.
        layers: Dict mapping region names to region GeoDataFrames.

    Returns:
        GeoDataFrame with boolean columns for each region.
    """
    result = gdf.copy()
    for region_name, region_gdf in layers.items():
        result, _ = compute_point_overlap(result, region_gdf, region_name)
    return result


def compute_equity_overlap_counts(gdf: gpd.GeoDataFrame, flag_columns: list[str]) -> pd.Series:
    """
    Count how many equity regions each feature overlaps with.

    Args:
        gdf: GeoDataFrame with boolean overlap columns.
        flag_columns: List of column names containing overlap flags.

    Returns:
        Series with overlap counts (0, 1, 2, 3, etc.).
    """
    overlap_count = sum(gdf[col].astype(int) for col in flag_columns)
    return overlap_count


def compute_block_region_fraction(
    block_gdf: gpd.GeoDataFrame,
    region_gdf: gpd.GeoDataFrame,
    muni_gdf: gpd.GeoDataFrame,
    region_name: str,
) -> gpd.GeoDataFrame:
    """
    Compute the fraction of census blocks in each municipality that fall within a region.

    Args:
        block_gdf: Census block groups GeoDataFrame.
        region_gdf: Region polygon GeoDataFrame.
        muni_gdf: Municipalities GeoDataFrame.
        region_name: Name of the region for column naming.

    Returns:
        Updated muni_gdf with '{region_name}_fraction' column.
    """
    col_name = f"{region_name.lower()}_fraction"
    flag_col = f"is_{region_name.lower()}"

    # Label blocks by whether their centroid is in the region
    region_centroids = region_gdf.copy()
    region_centroids["geometry"] = region_gdf.centroid
    region_centroids = region_centroids.to_crs(block_gdf.crs)

    region_block_idx = gpd.sjoin(
        region_centroids, block_gdf, how="inner", predicate="within"
    ).index_right

    block_gdf = block_gdf.copy()
    block_gdf[flag_col] = False
    block_gdf.loc[region_block_idx, flag_col] = True

    # Compute fraction per municipality
    block_muni = gpd.sjoin(block_gdf, muni_gdf, how="inner", predicate="intersects")
    stats = block_muni.groupby("index_right").agg(
        total_blocks=(flag_col, "count"),
        in_region_blocks=(flag_col, "sum"),
    )
    stats[col_name] = stats["in_region_blocks"] / stats["total_blocks"]

    muni_gdf = muni_gdf.copy()
    muni_gdf = muni_gdf.join(stats[[col_name]], how="left")
    muni_gdf[col_name] = muni_gdf[col_name].fillna(0)

    return muni_gdf
