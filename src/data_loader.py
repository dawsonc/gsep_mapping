"""Data loading utilities with caching support for GSEP analysis."""

import json
import os
import re
import zipfile
from pathlib import Path
from typing import Optional

import geopandas as gpd
import pandas as pd
import requests

import sys
sys.path.insert(0, str(Path(__file__).parent.parent))
from config import (
    CENSUS_ACS_YEAR,
    CENSUS_API_BASE,
    CENSUS_BG_ITEM_ID,
    CENSUS_BG_PORTAL,
    CENSUS_DIR,
    CENSUS_TIGER_YEAR,
    CODE_COMMUNITIES_FILE,
    EJ_GIS_DIR,
    FOSSIL_FUEL_FREE_FILE,
    GSEP_DOWNLOADS_DIR,
    GSEP_SEARCH_TERM,
    GSEP_SERVICE_URL,
    LDC_MAPPINGS,
    LMI_THRESHOLD,
    MA_MEDIAN_INCOME_2020,
    MA_STATE_FIPS,
    MUNICIPALITIES_ITEM_ID,
    MUNICIPALITIES_PORTAL,
    NATIONAL_GRID_DIR,
    NWA_FEEDERS,
    PROCESSED_DATA_DIR,
    RAW_DATA_DIR,
    WGS84,
)


def _safe_filename(name: str) -> str:
    """Clean string to be safe for filenames."""
    return re.sub(r'[\\/*?:"<>|]', "", name).replace(" ", "_")


def _get_json(url: str, params: Optional[dict] = None, timeout: int = 60) -> Optional[dict]:
    """Fetch JSON from a URL with optional parameters."""
    if params is None:
        params = {}
    params.setdefault("f", "json")

    token = os.environ.get("ARCGIS_TOKEN")
    if token and "token" not in params:
        params["token"] = token

    try:
        response = requests.get(url, params=params, timeout=timeout)
        response.raise_for_status()
        data = response.json()
        if isinstance(data, dict) and data.get("error"):
            print(f"ArcGIS error for {url}: {data['error']}")
            return None
        return data
    except Exception as e:
        print(f"Error fetching {url}: {e}")
        return None


def _download_arcgis_features(
    layer_url: str,
    output_path: Path,
    layer_name: str,
    batch_size: int = 2000,
) -> Optional[Path]:
    """Download all features from an ArcGIS layer using pagination."""
    print(f"  Downloading layer: {layer_name}...")
    all_features = []
    offset = 0

    while True:
        query_params = {
            "where": "1=1",
            "outFields": "*",
            "resultOffset": offset,
            "resultRecordCount": batch_size,
            "f": "geojson",
        }
        data = _get_json(f"{layer_url}/query", query_params, timeout=120)

        if not data or "features" not in data:
            print(f"    Warning: No features found for {layer_name}")
            break

        features = data.get("features", [])
        if not features:
            break

        all_features.extend(features)
        print(f"    Fetched {len(features)} features (Total: {len(all_features)})")

        if not data.get("exceededTransferLimit", False):
            break
        offset += len(features)

    if not all_features:
        print("  [INFO] Layer was empty.")
        return None

    geojson_output = {"type": "FeatureCollection", "features": all_features}
    filename = f"{_safe_filename(layer_name)}.geojson"
    filepath = output_path / filename

    with open(filepath, "w", encoding="utf-8") as f:
        json.dump(geojson_output, f)

    print(f"  [SUCCESS] Saved {len(all_features)} features to {filepath}")
    return filepath


def _find_feature_service_url(portal_root: str, item_id: str) -> Optional[str]:
    """Resolve the FeatureServer URL from an ArcGIS Online item."""
    item_url = f"{portal_root}/content/items/{item_id}"
    item_json = _get_json(item_url)
    if not item_json:
        return None

    if item_json.get("url"):
        return str(item_json["url"]).rstrip("/")

    item_data = _get_json(f"{item_url}/data")
    if not item_data:
        return None

    for key in ("url", "serviceUrl", "serviceURL"):
        if item_data.get(key):
            return str(item_data[key]).rstrip("/")
    return None


def load_gsep_projects(force_download: bool = False) -> gpd.GeoDataFrame:
    """
    Load GSEP project data from all LDCs.

    Downloads data from ArcGIS services if not cached locally.

    Args:
        force_download: If True, re-download even if cached data exists.

    Returns:
        GeoDataFrame with all GSEP projects and an 'LDC' column.
    """
    GSEP_DOWNLOADS_DIR.mkdir(parents=True, exist_ok=True)

    # Check if data already exists
    check_file = GSEP_DOWNLOADS_DIR / "Boston_Gas_2026_2029_Sheet1.geojson"
    if check_file.exists() and not force_download:
        print("GSEP data already cached. Loading from disk...")
    else:
        print(f"Downloading GSEP data from {GSEP_SERVICE_URL}...")
        catalog = _get_json(GSEP_SERVICE_URL)
        if not catalog or "services" not in catalog:
            raise RuntimeError("Failed to list GSEP services")

        services = catalog["services"]
        matched = [
            s for s in services
            if GSEP_SEARCH_TERM in s["name"]
            or "Berkshire_2026" in s["name"]
            or "Berkshire_2027" in s["name"]
        ]

        print(f"Found {len(matched)} matching services")

        for service in matched:
            service_name = service["name"]
            service_url = service.get("url") or f"{GSEP_SERVICE_URL}/{service_name}/{service['type']}"

            print(f"\nProcessing: {service_name}")
            service_details = _get_json(service_url)
            if not service_details:
                continue

            for layer in service_details.get("layers", []):
                layer_url = f"{service_url}/{layer['id']}"
                full_name = f"{service_name}_{layer['name']}"
                _download_arcgis_features(layer_url, GSEP_DOWNLOADS_DIR, full_name)

    # Load and combine all GSEP files
    dfs = []
    for filename in GSEP_DOWNLOADS_DIR.iterdir():
        if filename.suffix == ".geojson" and ("2026" in filename.name or "2027" in filename.name):
            company = filename.name.split("_")[0]
            company = LDC_MAPPINGS.get(company, company)
            df = gpd.read_file(filename)
            df["LDC"] = company
            print(f"Loaded {company}: {len(df)} records")
            dfs.append(df)

    gsep_df = pd.concat(dfs, ignore_index=True)
    print(f"Total GSEP records: {len(gsep_df)}")
    return gsep_df


def load_municipalities(force_download: bool = False) -> gpd.GeoDataFrame:
    """
    Load Massachusetts municipalities layer.

    Args:
        force_download: If True, re-download even if cached.

    Returns:
        GeoDataFrame of MA municipalities.
    """
    GSEP_DOWNLOADS_DIR.mkdir(parents=True, exist_ok=True)
    output_file = GSEP_DOWNLOADS_DIR / "Massachusetts_Municipalities.geojson"

    if output_file.exists() and not force_download:
        print("Municipalities data cached. Loading from disk...")
        return gpd.read_file(output_file)

    print("Downloading municipalities layer...")
    service_url = _find_feature_service_url(MUNICIPALITIES_PORTAL, MUNICIPALITIES_ITEM_ID)
    if not service_url:
        raise RuntimeError("Could not resolve municipalities service URL")

    service_details = _get_json(service_url)
    layers = service_details.get("layers", [])

    # Find municipalities layer
    layer = None
    for lyr in layers:
        name = lyr.get("name", "").lower()
        if "municip" in name or "town" in name:
            layer = lyr
            break
    layer = layer or layers[0]

    layer_url = f"{service_url}/{layer['id']}"
    _download_arcgis_features(layer_url, GSEP_DOWNLOADS_DIR, layer["name"])

    return gpd.read_file(output_file)


def load_census_block_groups(force_download: bool = False) -> gpd.GeoDataFrame:
    """
    Load MA Census 2020 Block Groups.

    Args:
        force_download: If True, re-download even if cached.

    Returns:
        GeoDataFrame of census block groups.
    """
    GSEP_DOWNLOADS_DIR.mkdir(parents=True, exist_ok=True)
    output_file = GSEP_DOWNLOADS_DIR / "Census_2020_Block_Groups.geojson"

    if output_file.exists() and not force_download:
        print("Census block groups cached. Loading from disk...")
        return gpd.read_file(output_file)

    print("Downloading census block groups...")
    service_url = _find_feature_service_url(CENSUS_BG_PORTAL, CENSUS_BG_ITEM_ID)
    if not service_url:
        raise RuntimeError("Could not resolve census block groups service URL")

    service_details = _get_json(service_url)
    layers = service_details.get("layers", [])

    # Find block groups layer
    layer = None
    for lyr in layers:
        if lyr.get("name") == "Census 2020 Block Groups":
            layer = lyr
            break
    layer = layer or layers[0]

    layer_url = f"{service_url}/{layer['id']}"
    _download_arcgis_features(layer_url, GSEP_DOWNLOADS_DIR, layer["name"])

    return gpd.read_file(output_file)


def _fetch_census_acs_data(variables: list[str], acs_year: int = CENSUS_ACS_YEAR) -> pd.DataFrame:
    """Fetch ACS 5-year data for MA block groups."""
    base = f"{CENSUS_API_BASE}/{acs_year}/acs/acs5"

    # Get counties first
    counties_url = f"{base}?get=NAME&for=county:*&in=state:{MA_STATE_FIPS}"
    counties = requests.get(counties_url, timeout=60)
    counties.raise_for_status()
    county_fips = [row[-1] for row in counties.json()[1:]]

    frames = []
    for county in county_fips:
        url = (
            f"{base}?get={','.join(variables)}"
            f"&for=block%20group:*"
            f"&in=state:{MA_STATE_FIPS}%20county:{county}%20tract:*"
        )
        r = requests.get(url, timeout=120)
        r.raise_for_status()
        data = r.json()
        df = pd.DataFrame(data[1:], columns=data[0])
        df["GEOID"] = df["state"] + df["county"] + df["tract"] + df["block group"]
        frames.append(df)

    out = pd.concat(frames, ignore_index=True)

    # Convert numeric columns
    for var in variables:
        if var != "NAME":
            out[var] = pd.to_numeric(out[var], errors="coerce")

    return out


def _download_tiger_blockgroups(tiger_year: int = CENSUS_TIGER_YEAR) -> Path:
    """Download TIGER/Line MA block group shapefile."""
    CENSUS_DIR.mkdir(parents=True, exist_ok=True)

    url = f"https://www2.census.gov/geo/tiger/TIGER{tiger_year}/BG/tl_{tiger_year}_{MA_STATE_FIPS}_bg.zip"
    zip_path = CENSUS_DIR / f"tl_{tiger_year}_{MA_STATE_FIPS}_bg.zip"

    if not zip_path.exists():
        print(f"Downloading TIGER block groups from {url}...")
        resp = requests.get(url, timeout=120)
        resp.raise_for_status()
        zip_path.write_bytes(resp.content)

    return zip_path


def load_lmi_data(force_download: bool = False) -> gpd.GeoDataFrame:
    """
    Load Low-to-Moderate Income (LMI) census block groups.

    Downloads Census ACS income data and TIGER geometries if not cached.

    Args:
        force_download: If True, re-download even if cached.

    Returns:
        GeoDataFrame with LMI block groups (income <= 80% MA median).
    """
    PROCESSED_DATA_DIR.mkdir(parents=True, exist_ok=True)
    output_file = PROCESSED_DATA_DIR / "ma_bg_income.geojson"

    if output_file.exists() and not force_download:
        print("LMI data cached. Loading from disk...")
        gdf = gpd.read_file(output_file)
    else:
        print("Building LMI dataset from Census data...")

        # Fetch ACS income and household data
        income_vars = ["NAME", "B19013_001E", "B19013_001M"]
        hh_vars = ["NAME", "B11001_001E", "B11001_001M"]

        income_df = _fetch_census_acs_data(income_vars)
        hh_df = _fetch_census_acs_data(hh_vars)

        # Download TIGER geometries
        tiger_zip = _download_tiger_blockgroups()
        extract_dir = tiger_zip.with_suffix("")

        if not extract_dir.exists():
            with zipfile.ZipFile(tiger_zip) as zf:
                zf.extractall(extract_dir)

        shp_path = next(extract_dir.glob("*.shp"))
        gdf = gpd.read_file(shp_path)

        # Join data
        gdf = gdf.merge(income_df[["GEOID", "B19013_001E", "B19013_001M"]], on="GEOID", how="left")
        gdf = gdf.merge(hh_df[["GEOID", "B11001_001E", "B11001_001M"]], on="GEOID", how="left")

        gdf = gdf.to_crs(WGS84)
        gdf.to_file(output_file, driver="GeoJSON")
        print(f"Saved income data to {output_file}")

    # Filter to LMI
    gdf = gdf[gdf["B19013_001E"].notna() & (gdf["B19013_001E"] > 0)].copy()
    threshold = MA_MEDIAN_INCOME_2020 * LMI_THRESHOLD
    gdf["is_lmi"] = gdf["B19013_001E"] <= threshold

    return gdf


def load_ejc_data() -> gpd.GeoDataFrame:
    """
    Load Environmental Justice Communities (EJC) data.

    Returns:
        GeoDataFrame of EJC polygons.
    """
    shp_file = EJ_GIS_DIR / "EJ_POLY.shp"
    if not shp_file.exists():
        raise FileNotFoundError(
            f"EJC shapefile not found at {shp_file}. "
            "Please place the EJ_POLY.* files in data/raw/ej_gis/"
        )

    print("Loading EJC data...")
    return gpd.read_file(shp_file)


def load_gateway_cities() -> gpd.GeoDataFrame:
    """
    Load Massachusetts Gateway Cities.

    Returns:
        GeoDataFrame of Gateway City polygons.
    """
    geojson_file = RAW_DATA_DIR / "Massachusetts_Gateway_Cities.geojson"
    if not geojson_file.exists():
        raise FileNotFoundError(
            f"Gateway cities file not found at {geojson_file}. "
            "Please place Massachusetts_Gateway_Cities.geojson in data/raw/"
        )

    print("Loading Gateway Cities data...")
    gdf = gpd.read_file(geojson_file)
    return gdf[gdf["GATEWAY"] == "Y"].copy()


def load_national_grid_feeders() -> gpd.GeoDataFrame:
    """
    Load National Grid distribution feeder data.

    Returns:
        GeoDataFrame with feeders and NWA opportunity flag.
    """
    if not NATIONAL_GRID_DIR.exists():
        raise FileNotFoundError(
            f"National Grid data not found at {NATIONAL_GRID_DIR}. "
            "Please place the distribution_assets_*.geojson files in data/raw/national_grid/"
        )

    print("Loading National Grid feeder data...")
    dfs = []
    for filepath in NATIONAL_GRID_DIR.glob("*.geojson"):
        df = gpd.read_file(filepath)
        dfs.append(df)

    if not dfs:
        raise FileNotFoundError("No GeoJSON files found in National Grid directory")

    gdf = pd.concat(dfs, ignore_index=True)
    gdf["nwa_opportunity"] = gdf["Master_CDF"].isin(NWA_FEEDERS)

    print(f"Loaded {len(gdf)} feeder segments ({gdf['nwa_opportunity'].sum()} NWA opportunities)")
    return gdf


def load_municipal_usage() -> pd.DataFrame:
    """
    Load municipal energy usage data.

    Returns:
        DataFrame with municipal energy usage statistics.
    """
    csv_file = RAW_DATA_DIR / "2023_municipal_usage_data.csv"
    if not csv_file.exists():
        raise FileNotFoundError(
            f"Municipal usage data not found at {csv_file}. "
            "Please place 2023_municipal_usage_data.csv in data/raw/"
        )

    print("Loading municipal usage data...")
    df = pd.read_csv(csv_file)

    df["Annual Electric Usage (MWh)"] = pd.to_numeric(
        df["Annual Electric Usage (MWh)"], errors="coerce"
    ).fillna(0)
    df["Annual Gas Usage (Therms)"] = pd.to_numeric(
        df["Annual Gas Usage (Therms)"], errors="coerce"
    ).fillna(0)

    # Convert gas to MWh equivalent (1 therm = 0.0293001 MWh)
    df["Annual Energy Usage (MWh)"] = (
        df["Annual Electric Usage (MWh)"] + 0.0293001 * df["Annual Gas Usage (Therms)"]
    )
    df["Municipality"] = df["Municipality"].str.upper()

    return df


def load_code_communities() -> gpd.GeoDataFrame:
    """
    Load Massachusetts code communities data (Base, Stretch, Specialized codes).

    Reads the stretch code Excel file and joins with municipality geometries.

    Returns:
        GeoDataFrame with municipality polygons and code_type column:
        - "Base": Municipalities with only base energy code (50)
        - "Stretch": Municipalities with stretch code but not specialized (189)
        - "Specialized": Municipalities with specialized energy code (56)
    """
    if not CODE_COMMUNITIES_FILE.exists():
        raise FileNotFoundError(
            f"Code communities data not found at {CODE_COMMUNITIES_FILE}. "
            "Please place the stretch code Excel file in data/raw/"
        )

    print("Loading code communities data...")

    # Read Excel file with proper column names
    df = pd.read_excel(CODE_COMMUNITIES_FILE, header=0)
    df.columns = [
        "Municipality",
        "Population",
        "Base_Code",
        "Stretch_Code_Date",
        "Specialized_Code_Date",
    ]

    # Skip header row and filter out summary rows
    df = df.iloc[1:]
    df = df[df["Municipality"].notna()]
    df = df[~df["Municipality"].astype(str).str.match(r"^\d+\.?\d*$")]

    # Determine code type for each municipality
    def get_code_type(row):
        if pd.notna(row["Specialized_Code_Date"]):
            return "Specialized"
        elif pd.notna(row["Stretch_Code_Date"]):
            return "Stretch"
        elif row["Base_Code"] == "X":
            return "Base"
        return "Base"  # Default fallback

    df["code_type"] = df.apply(get_code_type, axis=1)

    # Normalize municipality names for joining
    df["Municipality_upper"] = df["Municipality"].str.upper().str.strip()
    # Handle name mismatch
    df["Municipality_upper"] = df["Municipality_upper"].replace(
        "MANCHESTER BY THE SEA", "MANCHESTER-BY-THE-SEA"
    )

    # Load municipality geometries from Gateway Cities file (has all MA municipalities)
    muni_geojson = RAW_DATA_DIR / "Massachusetts_Gateway_Cities.geojson"
    if not muni_geojson.exists():
        raise FileNotFoundError(
            f"Municipality geometry file not found at {muni_geojson}. "
            "Please place Massachusetts_Gateway_Cities.geojson in data/raw/"
        )

    muni_gdf = gpd.read_file(muni_geojson)
    muni_gdf["TOWN_upper"] = muni_gdf["TOWN"].str.upper().str.strip()

    # Join code data with geometries
    result = muni_gdf.merge(
        df[["Municipality_upper", "code_type", "Population"]],
        left_on="TOWN_upper",
        right_on="Municipality_upper",
        how="left",
    )

    # Fill any missing code types as Base
    result["code_type"] = result["code_type"].fillna("Base")

    # Clean up columns
    result = result[["TOWN", "code_type", "Population", "geometry"]]
    result.columns = ["Municipality", "code_type", "Population", "geometry"]

    print(f"Loaded {len(result)} municipalities:")
    print(f"  - Base: {(result['code_type'] == 'Base').sum()}")
    print(f"  - Stretch: {(result['code_type'] == 'Stretch').sum()}")
    print(f"  - Specialized: {(result['code_type'] == 'Specialized').sum()}")

    return result


def load_fossil_fuel_free_communities() -> gpd.GeoDataFrame:
    """
    Load Massachusetts Fossil Fuel Free communities data.

    Reads the fossil fuel free communities CSV and joins with municipality geometries.

    Returns:
        GeoDataFrame with municipality polygons and is_fossil_fuel_free boolean column.
    """
    if not FOSSIL_FUEL_FREE_FILE.exists():
        raise FileNotFoundError(
            f"Fossil fuel free communities data not found at {FOSSIL_FUEL_FREE_FILE}. "
            "Please place fossil_fuel_free_communities.csv in data/raw/"
        )

    print("Loading fossil fuel free communities data...")

    # Read CSV file
    df = pd.read_csv(FOSSIL_FUEL_FREE_FILE)

    # Normalize municipality names for joining
    df["Municipality_upper"] = df["Municipality"].str.upper().str.strip()

    # Load municipality geometries from Gateway Cities file (has all MA municipalities)
    muni_geojson = RAW_DATA_DIR / "Massachusetts_Gateway_Cities.geojson"
    if not muni_geojson.exists():
        raise FileNotFoundError(
            f"Municipality geometry file not found at {muni_geojson}. "
            "Please place Massachusetts_Gateway_Cities.geojson in data/raw/"
        )

    muni_gdf = gpd.read_file(muni_geojson)
    muni_gdf["TOWN_upper"] = muni_gdf["TOWN"].str.upper().str.strip()

    # Mark fossil fuel free municipalities
    fff_set = set(df["Municipality_upper"])
    muni_gdf["is_fossil_fuel_free"] = muni_gdf["TOWN_upper"].isin(fff_set)

    # Clean up columns
    result = muni_gdf[["TOWN", "is_fossil_fuel_free", "geometry"]].copy()
    result.columns = ["Municipality", "is_fossil_fuel_free", "geometry"]

    fff_count = result["is_fossil_fuel_free"].sum()
    print(f"Loaded {len(result)} municipalities:")
    print(f"  - Fossil Fuel Free: {fff_count}")
    print(f"  - Other: {len(result) - fff_count}")

    return result
