"""Visualization utilities for GSEP mapping analysis."""

from typing import Optional, Union

import contextily as ctx
import geopandas as gpd
import matplotlib.patches as mpatches
import matplotlib.pyplot as plt
import pandas as pd
import seaborn as sns
from matplotlib.colors import ListedColormap

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))
from config import BAR_COLORS, BAR_FIGSIZE, MAP_FIGSIZE, WEB_MERCATOR

from src.analysis import LengthStats, OverlapStats


def plot_overlay_map(
    region_gdf: gpd.GeoDataFrame,
    overlay_gdf: gpd.GeoDataFrame,
    title: str,
    region_color: str = "#00ff0044",
    region_label: str = "Region",
    overlay_column: Optional[str] = None,
    overlay_filter_col: Optional[str] = None,
    overlay_filter_value: bool = True,
    show_legend: bool = True,
    figsize: tuple = MAP_FIGSIZE,
    markersize: float = 1,
    linewidth: float = 0.5,
) -> tuple[plt.Figure, plt.Axes]:
    """
    Create an overlay map with a region layer and features on top.

    Args:
        region_gdf: GeoDataFrame for the background region polygons.
        overlay_gdf: GeoDataFrame for the overlay features (points or lines).
        title: Map title.
        region_color: Fill color for region polygons.
        region_label: Label for the region in legend.
        overlay_column: Column to use for coloring overlay features.
        overlay_filter_col: Column to filter overlay features.
        overlay_filter_value: Value to filter on.
        show_legend: Whether to show legend.
        figsize: Figure size.
        markersize: Size for point markers.
        linewidth: Width for line features.

    Returns:
        Tuple of (figure, axes).
    """
    fig, ax = plt.subplots(1, 1, figsize=figsize, frameon=False)

    # Plot region
    region_gdf.to_crs(WEB_MERCATOR).plot(
        ax=ax, color=region_color, edgecolor="none", label=region_label
    )

    # Filter overlay if requested
    overlay = overlay_gdf
    if overlay_filter_col:
        overlay = overlay_gdf[overlay_gdf[overlay_filter_col] == overlay_filter_value]

    # Plot overlay
    overlay.to_crs(WEB_MERCATOR).plot(
        column=overlay_column,
        legend=show_legend and overlay_column is not None,
        ax=ax,
        markersize=markersize,
        linewidth=linewidth,
    )

    # Add basemap
    ctx.add_basemap(ax, source=ctx.providers.CartoDB.Positron)

    ax.set_title(title)
    ax.set_xlabel("")
    ax.set_ylabel("")
    ax.set_xticks([])
    ax.set_yticks([])

    return fig, ax


def plot_overlap_bar_chart(
    stats: Union[OverlapStats, LengthStats, pd.Series],
    title: str,
    ylabel: str = "Count",
    colors: list = BAR_COLORS,
    figsize: tuple = BAR_FIGSIZE,
    show_percentages: bool = True,
    percentage_offset: float = -200,
) -> tuple[plt.Figure, plt.Axes]:
    """
    Create a bar chart showing overlap statistics.

    Args:
        stats: OverlapStats, LengthStats, or Series with counts/values.
        title: Chart title.
        ylabel: Y-axis label.
        colors: Bar colors.
        figsize: Figure size.
        show_percentages: Whether to show percentage labels.
        percentage_offset: Y offset for percentage labels.

    Returns:
        Tuple of (figure, axes).
    """
    sns.set_context("talk")
    sns.set_style("white")

    fig, ax = plt.subplots(figsize=figsize)

    # Get counts series
    if isinstance(stats, (OverlapStats, LengthStats)):
        counts = stats.to_series()
        pcts = stats.to_pct_series()
    else:
        counts = stats
        total = counts.sum()
        pcts = (counts / total * 100).round(1) if total > 0 else counts * 0

    # Plot bars
    ax.bar(counts.index, counts.values, color=colors[: len(counts)])
    ax.set_title(title)
    ax.set_ylabel(ylabel)
    ax.set_xlabel("")
    ax.tick_params(axis="x", rotation=0)
    ax.grid(axis="y", linestyle="--", alpha=0.7)

    # Add percentage labels
    if show_percentages:
        for i, (cat, val) in enumerate(counts.items()):
            pct = pcts.iloc[i] if isinstance(pcts, pd.Series) else pcts[cat]
            ax.text(
                i, val + percentage_offset, f"{pct:.1f}%", ha="center", va="bottom"
            )

    plt.tight_layout()
    return fig, ax


def plot_equity_overlap_histogram(
    gdf: gpd.GeoDataFrame,
    overlap_column: str,
    title: str = "Overlap with Equity Regions",
    figsize: tuple = BAR_FIGSIZE,
) -> tuple[plt.Figure, plt.Axes]:
    """
    Create a histogram showing distribution of equity region overlaps.

    Args:
        gdf: GeoDataFrame with overlap count column.
        overlap_column: Column containing overlap counts (0, 1, 2, 3).
        title: Chart title.
        figsize: Figure size.

    Returns:
        Tuple of (figure, axes).
    """
    sns.set_context("talk")
    sns.set_style("white")

    fig, ax = plt.subplots(figsize=figsize)

    # Compute counts and percentages
    counts = gdf[overlap_column].value_counts().sort_index()
    percentages = counts / counts.sum() * 100

    # Plot histogram
    ax.hist(
        gdf[overlap_column],
        bins=[-0.5, 0.5, 1.5, 2.5, 3.5],
        edgecolor="white",
    )

    # Add percentage labels
    for x, count in counts.items():
        pct = percentages.loc[x]
        ax.text(x, count - 100, f"{pct:.0f}%", ha="center", va="bottom", color="white")

    ax.set_title(title)
    ax.set_ylabel("Number of projects")
    ax.set_xlabel("Number of equity regions overlapped")
    ax.set_xticks([0, 1, 2, 3])
    ax.grid(axis="y", linestyle="--", alpha=0.7)

    plt.tight_layout()
    return fig, ax


def plot_equity_heatmap(
    gdf: gpd.GeoDataFrame,
    overlap_column: str,
    title: str,
    figsize: tuple = MAP_FIGSIZE,
    cmap_colors: list = None,
    categories: list = None,
) -> tuple[plt.Figure, plt.Axes]:
    """
    Create a heatmap showing features colored by equity region overlap count.

    Args:
        gdf: GeoDataFrame with overlap count column.
        overlap_column: Column containing overlap counts.
        title: Map title.
        figsize: Figure size.
        cmap_colors: Colors for the colormap.
        categories: Category values for legend.

    Returns:
        Tuple of (figure, axes).
    """
    if cmap_colors is None:
        cmap_colors = ["#FFFFFF", "#CAD2DD", "#00A2FF", "#00111B"]
    if categories is None:
        categories = [0, 1, 2, 3]

    fig, ax = plt.subplots(1, 1, figsize=figsize, frameon=False)

    cmap = ListedColormap(cmap_colors)

    gdf.to_crs(WEB_MERCATOR).plot(
        column=overlap_column,
        categorical=True,
        categories=categories,
        cmap=cmap,
        legend=True,
        ax=ax,
        markersize=2,
    )

    ctx.add_basemap(ax, source=ctx.providers.CartoDB.Positron)
    ax.set_title(title)
    ax.set_xlabel("")
    ax.set_ylabel("")
    ax.set_xticks([])
    ax.set_yticks([])

    return fig, ax


def plot_code_communities_map(
    code_communities_gdf: gpd.GeoDataFrame,
    overlay_gdf: gpd.GeoDataFrame,
    title: str,
    stretch_color: str = "#7FCDBB",
    specialized_color: str = "#2C7FB8",
    base_color: str = "#F0F0F0",
    overlay_color: str = "#E31A1C",
    figsize: tuple = MAP_FIGSIZE,
    markersize: float = 2,
) -> tuple[plt.Figure, plt.Axes]:
    """
    Create a map showing code communities with GSEP projects overlaid.

    Args:
        code_communities_gdf: GeoDataFrame with code_type column (Base/Stretch/Specialized).
        overlay_gdf: GeoDataFrame for overlay features (GSEP projects).
        title: Map title.
        stretch_color: Fill color for stretch code municipalities.
        specialized_color: Fill color for specialized code municipalities.
        base_color: Fill color for base code municipalities.
        overlay_color: Color for overlay points.
        figsize: Figure size.
        markersize: Size for point markers.

    Returns:
        Tuple of (figure, axes).
    """
    fig, ax = plt.subplots(1, 1, figsize=figsize, frameon=False)

    # Project to Web Mercator for basemap compatibility
    communities_proj = code_communities_gdf.to_crs(WEB_MERCATOR)

    # Plot base code municipalities first (background)
    base = communities_proj[communities_proj["code_type"] == "Base"]
    if len(base) > 0:
        base.plot(ax=ax, color=base_color, edgecolor="#CCCCCC", linewidth=0.3)

    # Plot stretch code municipalities
    stretch = communities_proj[communities_proj["code_type"] == "Stretch"]
    if len(stretch) > 0:
        stretch.plot(ax=ax, color=stretch_color, edgecolor="#CCCCCC", linewidth=0.3)

    # Plot specialized code municipalities on top
    specialized = communities_proj[communities_proj["code_type"] == "Specialized"]
    if len(specialized) > 0:
        specialized.plot(ax=ax, color=specialized_color, edgecolor="#CCCCCC", linewidth=0.3)

    # Plot overlay points (GSEP projects)
    overlay_gdf.to_crs(WEB_MERCATOR).plot(
        ax=ax,
        color=overlay_color,
        markersize=markersize,
        alpha=0.7,
    )

    # Add basemap
    ctx.add_basemap(ax, source=ctx.providers.CartoDB.Positron, alpha=0.3)

    # Create legend
    legend_patches = [
        mpatches.Patch(color=specialized_color, label="Specialized Code"),
        mpatches.Patch(color=stretch_color, label="Stretch Code"),
        mpatches.Patch(color=base_color, label="Base Code"),
        mpatches.Patch(color=overlay_color, label="GSEP Projects"),
    ]
    ax.legend(handles=legend_patches, loc="lower right", fontsize=10)

    ax.set_title(title)
    ax.set_xlabel("")
    ax.set_ylabel("")
    ax.set_xticks([])
    ax.set_yticks([])

    return fig, ax
