"""Configuration settings for GSEP mapping analysis."""

from pathlib import Path

# Project root directory
PROJECT_ROOT = Path(__file__).parent

# Data directories
DATA_DIR = PROJECT_ROOT / "data"
RAW_DATA_DIR = DATA_DIR / "raw"
PROCESSED_DATA_DIR = DATA_DIR / "processed"

# Raw data subdirectories
GSEP_DOWNLOADS_DIR = RAW_DATA_DIR / "gsep_downloads"
CENSUS_DIR = RAW_DATA_DIR / "census"
EJ_GIS_DIR = RAW_DATA_DIR / "ej_gis"
NATIONAL_GRID_DIR = RAW_DATA_DIR / "national_grid"

# Code communities data file
CODE_COMMUNITIES_FILE = RAW_DATA_DIR / "stretch code 1-15-26.xlsx"

# Fossil fuel free communities data file
FOSSIL_FUEL_FREE_FILE = RAW_DATA_DIR / "fossil_fuel_free_communities.csv"

# Climate leader communities data file
CLIMATE_LEADER_FILE = RAW_DATA_DIR / "climate_leader_communities.csv"

# ArcGIS service URLs
GSEP_SERVICE_URL = "https://services5.arcgis.com/lWpwJ2MvpjCmjj94/ArcGIS/rest/services"
GSEP_SEARCH_TERM = "2026_2029"

# Portal URLs for municipalities and census data
MUNICIPALITIES_PORTAL = "https://mass-eoeea.maps.arcgis.com/sharing/rest"
MUNICIPALITIES_ITEM_ID = "9fb7faa26fe849888422a58deea1f776"

CENSUS_BG_PORTAL = "https://massgis.maps.arcgis.com/sharing/rest"
CENSUS_BG_ITEM_ID = "b05fdf4d38434e0793838513642789b0"

# Utility provider data from MassGIS
# Source: https://www.mass.gov/info-details/massgis-data-public-utility-service-providers
UTILITY_PORTAL = "https://massgis.maps.arcgis.com/sharing/rest"
ELECTRIC_UTILITY_ITEM_ID = "1710ebf6cf614b5fa97c0a269cece375"
GAS_UTILITY_ITEM_ID = "5f4f896313eb429c935b38f30bd80b46"
# Fallback MapServer URL for electric utility data
ELECTRIC_UTILITY_MAPSERVER = "http://gisprpxy.itd.state.ma.us/arcgisserver/rest/services/AGOL/ElectricityProviders/MapServer"

# Census API configuration
CENSUS_API_BASE = "https://api.census.gov/data"
CENSUS_ACS_YEAR = 2023
CENSUS_TIGER_YEAR = 2024
MA_STATE_FIPS = "25"

# LMI threshold (80% of MA median income)
MA_MEDIAN_INCOME_2020 = 84_385
LMI_THRESHOLD = 0.8

# Coordinate reference systems
WGS84 = "EPSG:4326"
WEB_MERCATOR = "EPSG:3857"
MA_STATE_PLANE = "EPSG:26986"

# Company name mappings for GSEP data
LDC_MAPPINGS = {
    "EGMA": "Eversource",
    "Boston": "National Grid",
    "Colonial": "National Grid",
}

# NWA opportunity feeders (National Grid)
NWA_FEEDERS = [
    "05_01_26W2", "05_01_304W2", "05_01_304W3", "05_01_304W4", "05_01_304W5",
    "05_01_304W6", "05_01_26W3", "05_01_406L2", "05_01_406L4", "05_01_412L1",
    "05_01_412L3", "05_01_412L6", "05_01_415L2", "05_01_406L1", "05_01_406L3",
    "05_01_413L4", "05_01_415L1", "05_01_415L3", "05_05_3451W2", "05_07_912W21",
    "05_07_797W1", "05_07_797W20", "05_07_912W22", "05_07_912W55", "05_07_912W73",
    "05_07_912W74", "05_07_912W75", "05_14_75L2", "05_12_11J13", "05_09_523L4",
    "05_09_501L2", "05_09_523L1", "05_09_523L2", "05_01_4J324", "05_01_8J364",
    "05_01_9J329", "05_01_3J341", "05_01_3J372", "05_01_3J373", "05_09_702W2",
    "05_09_702W1", "05_09_702W3", "05_09_705W3", "05_07_93W42", "05_07_93W43",
    "05_07_797W24", "05_07_797W29", "05_07_95W3", "05_07_99W62", "05_07_91W47",
    "05_07_91W41", "05_07_911W77", "05_12_67J4", "05_12_67J1", "05_12_5C3",
    "05_12_5J10", "05_12_5C1", "05_09_503L1", "05_09_503L2", "05_09_503L4",
    "05_09_514L1", "05_09_139L1", "05_09_139L3", "05_09_139L5", "05_09_507L2",
    "05_09_508L4", "05_12_21J30", "05_12_21J21", "05_12_21J25", "05_12_21J32",
    "05_12_21J23", "05_12_3J903", "05_01_HT52", "05_01_HT45", "04_04_101L2",
    "04_04_101L4", "04_04_101L6", "04_04_101L8", "05_05_3431W1", "05_05_3431W2",
    "05_05_3432W1", "05_05_3432W2", "05_05_3424W1", "05_05_3424W3", "05_05_3424W5",
    "05_05_349W1", "05_12_3J6", "05_12_1J12", "05_12_49W6", "05_12_29W3",
    "05_12_3J2", "05_12_3J3", "05_12_3J4", "05_07_75W5", "05_07_75W3",
    "05_07_75W1", "05_07_75W7", "05_07_97W5",
]

# Visualization settings
MAP_FIGSIZE = (15, 15)
BAR_FIGSIZE = (8, 6)
BAR_COLORS = ["skyblue", "lightcoral"]
