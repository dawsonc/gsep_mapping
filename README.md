# GSEP Mapping

Analyze Massachusetts Gas System Enhancement Program (GSEP) investments with respect to equity regions: Environmental Justice Communities (EJC), Low-to-Moderate Income (LMI) areas, and Gateway Cities.

## Quick Start

```bash
pip install geopandas matplotlib seaborn contextily requests pandas
python -c "from src import load_gsep_projects; print(load_gsep_projects())"
```

Or run the notebook:
```bash
jupyter notebook GSEP_analysis.ipynb
```

## Project Structure

```
gsep_mapping/
├── GSEP_analysis.ipynb      # Main analysis notebook
├── config.py                # Configuration settings
├── src/                     # Python modules
│   ├── data_loader.py       # Data loading with caching
│   ├── analysis.py          # Spatial overlap analysis
│   └── visualization.py     # Mapping and charting
└── data/
    ├── raw/                 # Source data files
    └── processed/           # Cached/processed data
```

## Usage

### Loading Data

```python
from src import load_gsep_projects, load_ejc_data, load_lmi_data

gsep_df = load_gsep_projects()  # Auto-downloads and caches
ejc_df = load_ejc_data()
lmi_df = load_lmi_data()
```

### Analyzing Overlap

```python
from src import compute_point_overlap, plot_overlap_bar_chart

gsep_df, stats = compute_point_overlap(gsep_df, ejc_df, "EJC")
plot_overlap_bar_chart(stats, title="GSEP Projects in EJCs")
```

### Adding New Layers

1. Place data file in `data/raw/`
2. Add loader function in `src/data_loader.py`
3. Use existing `compute_point_overlap()` or `compute_line_length_in_region()`

## Data Sources

- GSEP projects: MA DPU ArcGIS services
- EJC boundaries: MassGIS
- Census income data: US Census ACS API
- Gateway Cities: MassGIS

## License

MIT
