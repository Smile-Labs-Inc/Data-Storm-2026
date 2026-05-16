"""POI pipeline config. No CLI flags -- edit constants here."""

from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parent

DATA_RAW = ROOT / "data" / "raw"
DATA_POIS = ROOT / "data" / "pois"
OUTPUT_DIR = ROOT / "output"

PBF_URL = "https://download.geofabrik.de/asia/sri-lanka-latest.osm.pbf"
PBF_PATH = DATA_RAW / "sri-lanka-latest.osm.pbf"

# Source for outlet coordinates (raw competition file).
OUTLET_COORDINATES_CSV = ROOT.parent.parent / "datastorm-7-0-rotaract" / "outlet_coordinates.csv"

# Output of the build step.
POI_FEATURES_PARQUET = OUTPUT_DIR / "poi_features.parquet"
COVERAGE_REPORT_MD = OUTPUT_DIR / "poi_coverage_report.md"

# 9 POI categories with their OSM tag filters (per research/04 brief).
# Each filter is a dict mapping OSM key -> list of accepted values, or True for any.
CATEGORIES: dict[str, dict[str, object]] = {
    "schools": {"amenity": ["school", "university", "college", "kindergarten"]},
    "transport_hubs": {
        "amenity": ["bus_station"],
        "highway": ["bus_stop"],
        "railway": ["station", "halt", "tram_stop"],
        "public_transport": ["station", "stop_position", "platform"],
    },
    "hospitals": {
        "amenity": ["hospital", "clinic", "doctors", "pharmacy"],
        "healthcare": True,
    },
    "restaurants": {"amenity": ["restaurant", "cafe", "fast_food", "food_court"]},
    "supermarkets": {
        "shop": ["supermarket", "convenience", "grocery"],
        "amenity": ["marketplace"],
    },
    "religious_places": {"amenity": ["place_of_worship"]},
    "hotels": {"tourism": ["hotel", "guest_house", "hostel", "motel", "attraction"]},
    "offices": {"office": True, "amenity": ["townhall", "post_office"]},
    "banks": {"amenity": ["bank", "atm"]},
}

# Feature engineering knobs.
RADII_M: tuple[int, ...] = (250, 500, 1000, 2000)
GAUSSIAN_SIGMA_URBAN_KM = 0.75
GAUSSIAN_SIGMA_RURAL_KM = 2.0
URBAN_DENSITY_THRESHOLD = 50  # outlets within 1 km -> urban

# Sri Lanka bounding box (matches src/quality/checks.py).
LAT_RANGE = (5.5, 10.0)
LON_RANGE = (79.0, 82.5)
EARTH_RADIUS_KM = 6371.0


def ensure_dirs() -> None:
    for d in (DATA_RAW, DATA_POIS, OUTPUT_DIR):
        d.mkdir(parents=True, exist_ok=True)
