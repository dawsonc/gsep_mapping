"""GSEP Mapping Analysis Package.

This package provides tools for analyzing Gas System Enhancement Program (GSEP)
investments in Massachusetts with respect to equity regions.
"""

from src.data_loader import (
    load_census_block_groups,
    load_climate_leader_communities,
    load_code_communities,
    load_ejc_data,
    load_electric_utility_providers,
    load_gas_utility_providers,
    load_fossil_fuel_free_communities,
    load_gateway_cities,
    load_gsep_projects,
    load_lmi_data,
    load_municipal_usage,
    load_municipalities,
    load_national_grid_feeders,
    load_utility_providers,
)
from src.analysis import (
    OverlapStats,
    LengthStats,
    add_equity_region_flags,
    compute_block_region_fraction,
    compute_equity_overlap_counts,
    compute_line_length_in_region,
    compute_point_overlap,
)
from src.visualization import (
    plot_code_communities_map,
    plot_equity_heatmap,
    plot_equity_overlap_histogram,
    plot_overlay_map,
    plot_overlap_bar_chart,
)

__all__ = [
    # Data loading
    "load_gsep_projects",
    "load_municipalities",
    "load_census_block_groups",
    "load_lmi_data",
    "load_ejc_data",
    "load_gateway_cities",
    "load_national_grid_feeders",
    "load_municipal_usage",
    "load_code_communities",
    "load_electric_utility_providers",
    "load_gas_utility_providers",
    "load_utility_providers",
    "load_fossil_fuel_free_communities",
    "load_climate_leader_communities",
    # Analysis
    "OverlapStats",
    "LengthStats",
    "compute_point_overlap",
    "compute_line_length_in_region",
    "add_equity_region_flags",
    "compute_equity_overlap_counts",
    "compute_block_region_fraction",
    # Visualization
    "plot_overlay_map",
    "plot_overlap_bar_chart",
    "plot_equity_overlap_histogram",
    "plot_equity_heatmap",
    "plot_code_communities_map",
]
