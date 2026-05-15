# Channel 4 — OSM Overpass for Sri Lanka POI Acquisition

> Production-ready playbook for fetching POI counts/distances around 20,000 Sri Lanka beverage retail outlets across 9 categories and multiple radii, in the constrained timeframe of a 36-hour hackathon.

---

## TL;DR (3 bullets)

- **Do NOT hammer the public Overpass API with 20,000 × 9 × 4 around-radius queries.** Download the **Geofabrik `sri-lanka-latest.osm.pbf`** (~136 MB, daily-refreshed) once and run all POI extraction locally. Sri Lanka is small enough that the whole country fits comfortably in memory.
- **Primary tool: `pyrosm`** (Cython + Pyrobuf, reads PBF directly to GeoDataFrames). Use it to load all amenity/shop/tourism/railway/highway features once into GeoDataFrames, then do spatial joins in `geopandas` (`sjoin_nearest` + per-radius `buffer`) against the 20k outlets. This converts the problem from `O(20000 × 9 × 4)` HTTP calls to **a single in-process spatial join** taking minutes, not hours.
- **Use Overpass only for two narrow purposes:** (a) sanity-checking sparse categories against the live API for a sample of outlets, and (b) optional refresh in the last 24h before submission. When you do call Overpass, use **`overpass.private.coffee` (formerly kumi.systems, no rate limit)** with **bbox-per-province** chunking, `[out:json][timeout:900][maxsize:1073741824]`, and exponential backoff on 429/504.

---

## Recommended Approach

### Why local PBF beats live Overpass for this problem

You have **20,000 outlets × 9 categories × 4 radii = 720,000 logical lookups**. Even at the kindest Overpass mirror that is operationally insane:

| Approach | Network calls | Realistic wall-clock | Rubric risk |
|---|---|---|---|
| `node(around:R)[amenity=...]` per outlet × cat × radius | 720,000 | Days; will be rate-limited or banned | Pipeline looks fragile, judges will notice |
| Bbox-per-province × 9 categories on Overpass | ~36 calls total | 5–20 min if servers are healthy | Acceptable but server-dependent |
| **Local PBF + pyrosm + spatial join** (recommended) | **1 (the pbf download)** | **~10–25 min total** | **Robust, reproducible, defensible** |

You'll still **show** Overpass QL queries (the rubric explicitly judges "robustness of web-scraping / API pipeline"), but execute the bulk via PBF. Best of both worlds.

### One-paragraph architecture

```
1. Download sri-lanka-latest.osm.pbf from Geofabrik (~136 MB).
2. Open with pyrosm.OSM(pbf_path).
3. For each of 9 logical categories, call osm.get_pois(custom_filter={...})
   to get a GeoDataFrame of all matching POIs in Sri Lanka.
4. Project both outlets (20k) and POIs to a metric CRS
   (EPSG:5235 - Sri Lanka Grid 1999, or UTM 44N/44N depending on outlet split).
5. For each radius R in [250, 500, 1000, 2000] m:
   - Buffer outlets by R, spatial-join against POIs (gpd.sjoin),
     groupby outlet_id, count.
6. Also compute distance to nearest of each category via gpd.sjoin_nearest.
7. Persist features to data/silver/poi_features.parquet.
8. (Optional) Re-run a per-province Overpass bbox query for "fresh" comparison
   and log diff into Docs/data_quality_report.md to demonstrate a live API
   pipeline for the rubric.
```

---

## Overpass QL Snippets (per category)

All snippets target Sri Lanka by ISO area code (the OSM relation for Sri Lanka has ID 536807; using `area["ISO3166-1"="LK"]` is the portable form). Replace `{{bbox}}` for province slicing.

> **Header settings.** `[out:json][timeout:900][maxsize:1073741824];` is the safe default for country-wide queries on a tolerant mirror. The defaults on overpass-api.de are `timeout:180` and `maxsize:512MB`; bumping to 900s and 1GB is well-supported but only honored if the server has spare capacity. Source: [OSM Wiki — Overpass QL](https://wiki.openstreetmap.org/wiki/Overpass_QL).

### 0. Re-usable area handle

```overpassql
[out:json][timeout:900][maxsize:1073741824];
area["ISO3166-1"="LK"][admin_level=2]->.lk;
```

Province bbox alternatives (Western/Central/Southern/Sabaragamuwa cover most of the 4 hackathon provinces — confirm exact bbox from the outlet coordinates):

| Province | Approx bbox (south,west,north,east) |
|---|---|
| Western | `6.70,79.80,7.30,80.30` |
| Central | `6.90,80.40,7.70,81.10` |
| Southern | `5.90,80.00,6.55,81.30` |
| Sabaragamuwa | `6.30,80.20,7.20,80.90` |

Replace these with exact bounds derived from `outlets[['lat','lon']].agg(['min','max'])` per province in your real data.

### 1. Schools and universities (`amenity=school`, `amenity=college`, `amenity=university`, `amenity=kindergarten`)

```overpassql
[out:json][timeout:900][maxsize:1073741824];
area["ISO3166-1"="LK"][admin_level=2]->.lk;
(
  nwr["amenity"~"^(school|college|university|kindergarten)$"](area.lk);
);
out center tags;
```

Wiki refs: [`amenity=school`](https://wiki.openstreetmap.org/wiki/Tag:amenity%3Dschool), [`amenity=university`](https://wiki.openstreetmap.org/wiki/Tag:amenity%3Duniversity).

### 2. Transport hubs (bus stops, railway stations/halts, public-transport stop positions)

```overpassql
[out:json][timeout:900][maxsize:1073741824];
area["ISO3166-1"="LK"][admin_level=2]->.lk;
(
  node["highway"="bus_stop"](area.lk);
  nwr["amenity"="bus_station"](area.lk);
  nwr["public_transport"~"^(station|stop_position|platform)$"](area.lk);
  nwr["railway"~"^(station|halt|tram_stop)$"](area.lk);
);
out center tags;
```

Wiki refs: [`highway=bus_stop`](https://wiki.openstreetmap.org/wiki/Tag:highway%3Dbus_stop), [`railway=station`](https://wiki.openstreetmap.org/wiki/Railway_stations), [`public_transport=stop_position`](https://wiki.openstreetmap.org/wiki/Tag:public_transport%3Dstop_position).

> Note: PTv2 schema means a single physical stop can be tagged as **both** `highway=bus_stop` (legacy node on the road) **and** `public_transport=platform` (PTv2 node/way next to it). Dedupe — see §7.

### 3. Markets and shopping centres (`amenity=marketplace`, `shop=mall`, `shop=department_store`)

```overpassql
[out:json][timeout:900][maxsize:1073741824];
area["ISO3166-1"="LK"][admin_level=2]->.lk;
(
  nwr["amenity"="marketplace"](area.lk);
  nwr["shop"~"^(mall|department_store|wholesale)$"](area.lk);
);
out center tags;
```

### 4. Offices and banks (`amenity=bank`, `amenity=atm`, `office=*`)

```overpassql
[out:json][timeout:900][maxsize:1073741824];
area["ISO3166-1"="LK"][admin_level=2]->.lk;
(
  nwr["amenity"~"^(bank|atm|bureau_de_change|post_office)$"](area.lk);
  nwr["office"](area.lk);
);
out center tags;
```

> `office=*` captures every value (`office=company`, `office=government`, `office=insurance`, etc.). For a beverage-demand model this is what you want — total office density correlates with weekday foot traffic.

### 5. Hospitals and clinics (`amenity=hospital`, `clinic`, `doctors`, `pharmacy`)

```overpassql
[out:json][timeout:900][maxsize:1073741824];
area["ISO3166-1"="LK"][admin_level=2]->.lk;
(
  nwr["amenity"~"^(hospital|clinic|doctors|dentist|pharmacy)$"](area.lk);
  nwr["healthcare"](area.lk);
);
out center tags;
```

### 6. Restaurants, cafes, bakeries, eateries

```overpassql
[out:json][timeout:900][maxsize:1073741824];
area["ISO3166-1"="LK"][admin_level=2]->.lk;
(
  nwr["amenity"~"^(restaurant|cafe|fast_food|food_court|ice_cream|pub|bar|biergarten)$"](area.lk);
  nwr["shop"="bakery"](area.lk);
);
out center tags;
```

Wiki ref: [`shop=bakery`](https://wiki.openstreetmap.org/wiki/Tag:shop%3Dbakery).

### 7. Supermarkets and groceries

```overpassql
[out:json][timeout:900][maxsize:1073741824];
area["ISO3166-1"="LK"][admin_level=2]->.lk;
(
  nwr["shop"~"^(supermarket|convenience|grocery|greengrocer|general|kiosk|alcohol|beverages)$"](area.lk);
);
out center tags;
```

Wiki refs: [`shop=supermarket`](https://wiki.openstreetmap.org/wiki/Tag:shop%3Dsupermarket), [`Key:shop`](https://wiki.openstreetmap.org/wiki/Key:shop). For a beverage problem, **`shop=alcohol`** and **`shop=beverages`** are gold — pull them as a separate sub-feature too.

### 8. Religious places of worship

```overpassql
[out:json][timeout:900][maxsize:1073741824];
area["ISO3166-1"="LK"][admin_level=2]->.lk;
(
  nwr["amenity"="place_of_worship"](area.lk);
);
out center tags;
```

You can split by religion using the `religion=*` sub-tag (`buddhist`, `hindu`, `christian`, `muslim`) — useful in Sri Lanka because demand patterns differ by community calendar.

### 9. Hotels and tourist attractions

```overpassql
[out:json][timeout:900][maxsize:1073741824];
area["ISO3166-1"="LK"][admin_level=2]->.lk;
(
  nwr["tourism"~"^(hotel|guest_house|hostel|motel|apartment|resort|attraction|museum|viewpoint|theme_park|zoo|gallery)$"](area.lk);
);
out center tags;
```

Wiki ref: [`tourism=hotel`](https://wiki.openstreetmap.org/wiki/Tag:tourism%3Dhotel), [`tourism=attraction`](https://wiki.openstreetmap.org/wiki/Tag:tourism%3Dattraction).

### Bonus: per-outlet around-radius (only for spot-checks, not bulk)

```overpassql
[out:json][timeout:60];
(
  nwr(around:500, 6.9271, 79.8612)["amenity"="restaurant"];
);
out center tags;
```

Use this against ~50 outlets to validate that your local-PBF counts agree with live OSM within ±5%. Document the audit in `Docs/data_quality_report.md`.

---

## Pipeline Architecture

### Library choice: pyrosm (primary), osmnx (fallback)

| Library | Source | Speed | Use case here |
|---|---|---|---|
| **`pyrosm`** | local `.osm.pbf` | Cython + Pyrobuf, ~2–4× protobuf default; fastest of all options for country-wide PBFs | **Primary.** All bulk extraction. |
| `osmnx` | live Overpass | Network-bound; auto-splits large geometries, caches JSON | Fallback if PBF parse fails; also for per-outlet `features_from_point(center_point, tags, dist)`. |
| `overpy` | live Overpass | Thin wrapper, no caching | Avoid for bulk; OK for one-off audits. |
| `osmium` (PyOsmium) | local `.osm.pbf` | Streaming C++ parser, lowest memory | Use only if pyrosm hits memory issues — unlikely for 136 MB Sri Lanka. |

Sources: [pyrosm benchmarks](https://pyrosm.readthedocs.io/en/stable/benchmarking.html), [osm-python-readers-benchmark](https://github.com/RaczeQ/osm-python-readers-benchmark), [OSMnx 2.1 features module](https://osmnx.readthedocs.io/en/stable/user-reference.html#osmnx.features.features_from_point).

### Reference Python skeleton (pyrosm primary path)

```python
# scripts/poi_extract.py
from pathlib import Path

import geopandas as gpd
import pandas as pd
from pyrosm import OSM

PBF_PATH = Path("data/bronze/osm/sri-lanka-latest.osm.pbf")
OUTLETS_PATH = Path("data/bronze/outlets.csv")
OUT_PATH = Path("data/silver/poi_features.parquet")

METRIC_CRS = "EPSG:5235"
RADII_M = [250, 500, 1000, 2000]

CATEGORY_FILTERS = {
    "education":       {"amenity": ["school", "college", "university", "kindergarten"]},
    "transport":       {"highway": ["bus_stop"],
                        "amenity": ["bus_station"],
                        "railway": ["station", "halt", "tram_stop"],
                        "public_transport": ["station", "stop_position", "platform"]},
    "market_mall":     {"amenity": ["marketplace"],
                        "shop":    ["mall", "department_store", "wholesale"]},
    "office_bank":     {"amenity": ["bank", "atm", "bureau_de_change", "post_office"],
                        "office":  True},
    "health":          {"amenity": ["hospital", "clinic", "doctors", "dentist", "pharmacy"],
                        "healthcare": True},
    "food_drink":      {"amenity": ["restaurant", "cafe", "fast_food", "food_court",
                                    "ice_cream", "pub", "bar", "biergarten"],
                        "shop":    ["bakery"]},
    "grocery":         {"shop": ["supermarket", "convenience", "grocery", "greengrocer",
                                 "general", "kiosk", "alcohol", "beverages"]},
    "worship":         {"amenity": ["place_of_worship"]},
    "tourism_lodging": {"tourism": ["hotel", "guest_house", "hostel", "motel", "apartment",
                                    "resort", "attraction", "museum", "viewpoint",
                                    "theme_park", "zoo", "gallery"]},
}


def extract_pois() -> dict[str, gpd.GeoDataFrame]:
    osm = OSM(str(PBF_PATH))
    pois: dict[str, gpd.GeoDataFrame] = {}
    for cat, flt in CATEGORY_FILTERS.items():
        gdf = osm.get_pois(custom_filter=flt)
        if gdf is None or gdf.empty:
            print(f"[warn] {cat}: no rows")
            continue
        gdf = gdf[gdf.geometry.notna()].copy()
        gdf["geometry"] = gdf.geometry.representative_point()
        gdf["category"] = cat
        gdf["poi_uid"]  = gdf["category"] + "_" + gdf.index.astype(str)
        pois[cat] = gdf.to_crs(METRIC_CRS)
        print(f"[ok]   {cat}: {len(gdf):,} POIs")
    return pois


def build_features(outlets: gpd.GeoDataFrame, pois: dict) -> pd.DataFrame:
    out = outlets[["outlet_id", "geometry"]].to_crs(METRIC_CRS).copy()
    rows = out[["outlet_id"]].copy()
    for cat, gdf in pois.items():
        gdf = dedupe_pois(gdf)
        # nearest distance
        nearest = gpd.sjoin_nearest(out, gdf[["poi_uid", "geometry"]],
                                    distance_col=f"dist_nearest_{cat}_m")
        rows = rows.merge(
            nearest.groupby("outlet_id")[f"dist_nearest_{cat}_m"].min().reset_index(),
            on="outlet_id", how="left",
        )
        # radius counts
        for r in RADII_M:
            buf = out.copy()
            buf["geometry"] = buf.buffer(r)
            j = gpd.sjoin(buf[["outlet_id", "geometry"]],
                          gdf[["poi_uid", "geometry"]], predicate="contains")
            counts = j.groupby("outlet_id").size().rename(f"n_{cat}_{r}m").reset_index()
            rows = rows.merge(counts, on="outlet_id", how="left")
    return rows.fillna({c: 0 for c in rows.columns if c.startswith("n_")})


def dedupe_pois(gdf: gpd.GeoDataFrame) -> gpd.GeoDataFrame:
    """Drop near-duplicates: same (rounded-lat, rounded-lon, name) cluster."""
    g = gdf.copy()
    g["lat_r"]  = g.geometry.y.round(5)   # ~1.1 m precision
    g["lon_r"]  = g.geometry.x.round(5)
    g["name_l"] = g.get("name", pd.Series("", index=g.index)).fillna("").str.lower().str.strip()
    return g.drop_duplicates(subset=["lat_r", "lon_r", "name_l"]).drop(
        columns=["lat_r", "lon_r", "name_l"])


def main():
    outlets = gpd.read_file(OUTLETS_PATH).set_crs("EPSG:4326")
    pois    = extract_pois()
    feats   = build_features(outlets, pois)
    feats.to_parquet(OUT_PATH)
    print(f"wrote {OUT_PATH} ({len(feats):,} rows, {feats.shape[1]} cols)")


if __name__ == "__main__":
    main()
```

> Tested-pattern caveat: `osm.get_pois(custom_filter=...)` is the documented entry point per the [pyrosm filter docs](https://pyrosm.readthedocs.io/en/stable/custom_filter.html). For categories that pyrosm classifies as not-a-POI (e.g. `office=*` is a tag pyrosm doesn't extract under `get_pois` by default), fall back to `osm.get_data_by_custom_criteria(custom_filter=...)`.

### Batching strategy when you DO use Overpass

Use one of three patterns, in order of preference:

1. **One bbox per province × 9 categories = 36 queries total.** Fits inside any normal Overpass quota. Run sequentially with 2-second sleep between calls.
2. **Country-wide ISO area filter (`area["ISO3166-1"="LK"]`) × 9 categories = 9 queries.** Faster, but each query is heavier — risk timeout on overpass-api.de.
3. **Per-outlet `around:radius` × 720k.** **Avoid.** Will get you IP-banned and won't finish in time.

### Rate-limit + retry logic

Public mirror policies (sources: [Overpass commons](https://dev.overpass-api.de/overpass-doc/en/preface/commons.html), [Private.coffee mirror page](https://overpass.kumi.systems/index.html)):

| Mirror | Soft daily cap | Hard policy | Recommended use |
|---|---|---|---|
| `overpass-api.de` (gall + lambert) | ~10,000 req/day, ≤1 GB/day per IP; load-shedding when busy | 429 + `Retry-After` header | OK for the 36 audit queries |
| `overpass.private.coffee` (ex `kumi.systems`) | "no rate limit, share fairly" | Operator may rate-limit abusers | OK for medium-scale, **still don't** point 720k queries at it |
| Self-hosted (`docker run wiktorn/overpass-api`) | None | You pay the CPU | Overkill for one country, but trivial to spin up if needed |

Production-grade retry wrapper:

```python
import time, requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

ENDPOINTS = [
    "https://overpass.private.coffee/api/interpreter",
    "https://overpass-api.de/api/interpreter",
    "https://overpass.kumi.systems/api/interpreter",
]

def overpass_session() -> requests.Session:
    s = requests.Session()
    s.headers.update({"User-Agent": "logical-context-poi/1.0 (datastorm7)"})
    retry = Retry(total=5, backoff_factor=2.0,
                  status_forcelist=[429, 500, 502, 503, 504],
                  allowed_methods={"POST"}, respect_retry_after_header=True)
    s.mount("https://", HTTPAdapter(max_retries=retry))
    return s

def overpass_query(ql: str, timeout: int = 900) -> dict:
    last_err = None
    for url in ENDPOINTS:
        try:
            r = overpass_session().post(url, data={"data": ql}, timeout=timeout + 30)
            if r.status_code == 200:
                return r.json()
            if r.status_code == 429 and "Retry-After" in r.headers:
                time.sleep(int(r.headers["Retry-After"]) + 1)
            last_err = f"{url} -> {r.status_code}"
        except requests.RequestException as e:
            last_err = f"{url} -> {e!r}"
    raise RuntimeError(f"All Overpass endpoints failed: {last_err}")
```

### Self-hosted Overpass (escape hatch)

```bash
docker run -d --name overpass-lk \
  -e OVERPASS_META=yes \
  -e OVERPASS_MODE=init \
  -e OVERPASS_PLANET_URL=https://download.geofabrik.de/asia/sri-lanka-latest.osm.bz2 \
  -e OVERPASS_DIFF_URL=https://download.geofabrik.de/asia/sri-lanka-updates/ \
  -v $PWD/overpass-db:/db \
  -p 12345:80 \
  wiktorn/overpass-api
```

Initialization for Sri Lanka takes ~10 min on a laptop (the bz2 is small). After that, point queries at `http://localhost:12345/api/interpreter` and run as fast as you like.

---

## Sri Lanka Coverage Notes

Quantitative checkpoints from public sources:

| Source | Datapoint |
|---|---|
| [Geofabrik download server](https://download.geofabrik.de/asia/sri-lanka.html) | `sri-lanka-latest.osm.pbf` ≈ **136 MB**, daily-refreshed |
| [osmtoday Sri Lanka extract](https://osmtoday.com/asia/sri_lanka.html) | Amenity points: **19,601**; amenity areas: **7,452**; leisure points: **1,335**; building objects: **2.5M** |
| [HDX Sri Lanka POIs](https://data.humdata.org/dataset/hotosm_lka_points_of_interest) | Country-wide POI export, regularly refreshed by HOT |
| [OSM Wiki — Sri Lanka project](https://wiki.openstreetmap.org/wiki/Sri_Lanka) | Active local mapping community; HOT-supported work in Batticaloa post-2016 floods; tagging guidelines page |

**What this means for your 9 categories** (qualitative, based on amenity-point density and HOT export composition):

| Category | Coverage in Sri Lanka | Notes |
|---|---|---|
| Schools / universities | **Good** — well-mapped country-wide | `amenity=school` density mirrors government school registry; universities often as polygons (use `out center`) |
| Bus stops / railway | **Mixed** — railway stations excellent; bus stops sparse outside Colombo/Kandy | Compensate with `amenity=bus_station` (terminals) |
| Markets / malls | **Good in Western/Southern**, sparse in North-Central | Use both `amenity=marketplace` and `shop=mall` |
| Offices / banks | **Bank network well-mapped** (Commercial, BoC, HNB, Sampath all branded); generic `office=*` patchy | Brand lookups with `brand=*` and `operator=*` |
| Hospitals / clinics | **Good** — government hospitals well-tagged; private clinics under-mapped | Add `healthcare=*` for redundancy |
| Restaurants / cafes | **Good in tourist belt** (Colombo, Galle, Kandy, Negombo); thin elsewhere | Counts will skew; keep distance-to-nearest as the more honest signal |
| Supermarkets / grocery | **Good for chains** (Cargills, Keells, Arpico, Laughs); kade/grocery very sparse | Critical caveat for your beverage problem — see "Failure modes" below |
| Religious places | **Excellent** — Sri Lanka is one of the most-mapped countries for `place_of_worship` per capita | Split by `religion=*` for richer features |
| Hotels / attractions | **Excellent in tourist zones**, otherwise sparse | Tourist-focused tagging from HOT post-2016 |

**Honest caveat for the rubric:** the grocery/kade gap matters because beverage demand is heavily driven by small independent retailers that are NOT on OSM. Acknowledge this explicitly in `data_quality_report.md` — judges reward honest gap-analysis over silent over-claiming.

---

## Geocoding Fallback (Nominatim)

If an outlet coordinate is suspect (lat/lon offshore, in another country, or zero-zero), fall back to **Nominatim reverse geocoding** to verify:

```python
import time, requests

def reverse(lat: float, lon: float) -> dict:
    r = requests.get(
        "https://nominatim.openstreetmap.org/reverse",
        params={"lat": lat, "lon": lon, "format": "jsonv2", "zoom": 14},
        headers={"User-Agent": "logical-context-poi/1.0 (datastorm7)"},
        timeout=30,
    )
    time.sleep(1.0)  # Nominatim policy: 1 req/sec
    return r.json()
```

**Public Nominatim policy** (source: [Nominatim Usage Policy](https://operations.osmfoundation.org/policies/nominatim/)):

- ≤ 1 request/second per IP, single thread
- Bulk jobs > 1 day or scheduled: ≤ 4 requests/minute
- Required: distinct `User-Agent` or `Referer`
- Cache results locally; redistribute under ODbL

For 20k bulk reverse-geocoding **do not use the public service** — either (a) only run it on the suspect subset (typically <1%), or (b) self-host Nominatim in Docker for the day. Public service is for low-volume validation.

---

## POI Deduplication

**The same physical thing is often tagged multiple ways.** Examples seen in Sri Lanka data:

- A grocery store tagged `shop=supermarket` AND inside an `amenity=marketplace` polygon → would be double-counted in the `market_mall` and `grocery` categories.
- A bus terminal tagged `amenity=bus_station` AND containing several `highway=bus_stop` nodes AND PTv2 `public_transport=platform` ways → 3-5× count inflation in `transport`.
- A restaurant in a hotel tagged `tourism=hotel` (the building) AND `amenity=restaurant` (the venue inside).

**Three-step dedup (apply per category):**

1. **Geometric snap.** Round geometry centroid to 5-decimal lat/lon (~1.1 m). Drop pairs within the same rounded cell with the same lowercase name.
2. **OSM `id` collapse for the same physical feature.** When you ingest both nodes and ways, a hotel mapped as both a node AND a polygon will have two records — collapse `(name, lower) + nearest 50m` clusters using `geopandas.sjoin_nearest` or `scipy.spatial.cKDTree`.
3. **Cross-category leak.** Apply once across all categories together: if a POI appears in `worship` and `tourism_lodging` (e.g. heritage temple that's also a tourist attraction), keep both — it genuinely contributes to both signals.

The reference dedup function in the script above handles step 1. For steps 2-3, add a `cKDTree` pass before persisting.

---

## Wall-clock Estimates (20,000 outlets × 9 categories × 4 radii on a laptop)

Assumptions: 16 GB RAM, decent SSD, fibre internet, no heroic GPU.

| Approach | Download | POI extraction | Spatial join | Total wall-clock |
|---|---|---|---|---|
| **pyrosm + geopandas (recommended)** | ~30 s (136 MB pbf) | ~3–6 min (9 categories) | ~5–15 min (depends on radii) | **~10–25 min** |
| `osmnx.features_from_point` per outlet × 9 cats × 4 radii | 0 | ~720k Overpass calls; **abandon — would take days** | n/a | n/a |
| Overpass bbox-per-province × 9 cats (36 queries) | 0 | 5–20 min on healthy mirror | ~5–15 min locally | ~15–35 min |
| Self-hosted Overpass + per-outlet around | ~10 min init | ~30–60 min for 720k local calls | n/a | ~45–75 min |
| `osmium tags-filter` CLI + `geopandas` join | ~30 s | ~2 min per category × 9 = ~18 min | ~5–15 min | ~25–35 min |

**Bottom line:** pyrosm wins by a wide margin. Keep one Overpass bbox-query path implemented for "fresh-data audit" — judges see both robustness and speed.

---

## Failure-Mode Handling

| Failure | Default / mitigation |
|---|---|
| Outlet has 0 POIs of category `c` within max radius | Set `n_c_Rm = 0`, `dist_nearest_c_m = max_radius * 2` (do NOT use NaN — boosting models will treat it as "missing" instead of "far"). Add a binary `has_c_within_Rm` flag. |
| Outlet coordinate offshore / outside Sri Lanka | Drop or geocode-correct. Log to `data_quality_report.md`. |
| pyrosm parse error on a category | Fall back to `osmium tags-filter sri-lanka-latest.osm.pbf nwr/amenity=hospital -o hospitals.osm.pbf` then re-load. |
| Overpass mirror down | Auto-failover to next endpoint in `ENDPOINTS` list above; retry with exponential backoff via `urllib3.util.retry.Retry`. |
| pbf is stale (> 7 days old at submission) | Re-download from Geofabrik (it's daily). Document the snapshot date in `data/silver/poi_features.parquet` metadata. |
| Province boundary uncertainty (outlet near a border) | Use country-wide PBF, not per-province extracts; `pyrosm` handles country PBF in one shot anyway. |
| Distance metric drift near coast/UTM boundary | Use **Sri Lanka Grid 1999 (EPSG:5235)** as the canonical metric CRS — designed for the country, sub-metre accuracy nationwide. |

---

## Definitive recommendations

1. **Use `pyrosm` against the Geofabrik `sri-lanka-latest.osm.pbf`** as the primary path. One ~10-25 min job replaces 720k network calls.
2. **Implement a parallel Overpass bbox-per-province path** (36 queries against `overpass.private.coffee`) and run it once for cross-validation. Document the diff. The rubric explicitly rewards the visible scraping pipeline.
3. **Use Nominatim only for outlier geocoding** (typically <200 outlets out of 20k) — keep under 1 req/sec.
4. **Dedup per-category, then across categories.** The grocery/marketplace double-count is the most common failure.
5. **Persist features to Parquet** at `data/silver/poi_features.parquet` with snapshot date in metadata. Schema: `outlet_id`, then for each of 9 categories: `dist_nearest_<cat>_m`, `n_<cat>_250m`, `n_<cat>_500m`, `n_<cat>_1000m`, `n_<cat>_2000m`, `has_<cat>_within_500m`. That's `1 + 9 × 6 = 55` columns.
6. **Be honest about coverage gaps** in `Docs/data_quality_report.md` — kades and small grocers are under-mapped on OSM in Sri Lanka, and that's a known limitation the model needs to acknowledge.

---

## References

- [OSM Wiki — Overpass QL](https://wiki.openstreetmap.org/wiki/Overpass_QL) — `timeout`, `maxsize`, `out:json`, `area`, `around` syntax.
- [OSM Wiki — Overpass API by Example](https://wiki.openstreetmap.org/wiki/Overpass_API/Overpass_API_by_Example) — full query patterns.
- [OSM Wiki — Key:amenity](https://wiki.openstreetmap.org/wiki/Key:amenity) — 329 amenity values, including `school`, `hospital`, `bank`, `place_of_worship`.
- [OSM Wiki — Key:shop](https://wiki.openstreetmap.org/wiki/Key:shop) — supermarket, convenience, mall, alcohol, beverages, bakery.
- [OSM Wiki — Tag:tourism=hotel](https://wiki.openstreetmap.org/wiki/Tag:tourism%3Dhotel) and [Tag:tourism=attraction](https://wiki.openstreetmap.org/wiki/Tag:tourism%3Dattraction).
- [OSM Wiki — Public transport](https://wiki.openstreetmap.org/wiki/Public_transit), [Tag:highway=bus_stop](https://wiki.openstreetmap.org/wiki/Tag:highway%3Dbus_stop), [Railway stations](https://wiki.openstreetmap.org/wiki/Railway_stations).
- [OSM Wiki — Sri Lanka WikiProject](https://wiki.openstreetmap.org/wiki/Sri_Lanka) — local community, tagging guidelines.
- [Geofabrik — Sri Lanka extract](https://download.geofabrik.de/asia/sri-lanka.html) — 136 MB pbf, daily refresh.
- [osmtoday — Sri Lanka stats](https://osmtoday.com/asia/sri_lanka.html) — quantitative POI counts.
- [HDX — Sri Lanka POI export (HOT)](https://data.humdata.org/dataset/hotosm_lka_points_of_interest) — alternative ready-made download.
- [Pyrosm docs — basic usage](https://pyrosm.readthedocs.io/en/stable/basics.html) and [custom filters](https://pyrosm.readthedocs.io/en/stable/custom_filter.html).
- [Pyrosm benchmarks](https://pyrosm.readthedocs.io/en/stable/benchmarking.html) — 2–4× faster than alternatives.
- [OSMnx user reference](https://osmnx.readthedocs.io/en/stable/user-reference.html) — `features_from_point`, `features_from_bbox`.
- [Overpass Commons — public mirrors](https://dev.overpass-api.de/overpass-doc/en/preface/commons.html) — official rate-limit policy.
- [Private.coffee Overpass mirror](https://overpass.kumi.systems/index.html) — successor to `kumi.systems`, no rate limit.
- [Nominatim Usage Policy](https://operations.osmfoundation.org/policies/nominatim/) — 1 req/sec, attribution requirements.
- [osm-python-readers-benchmark](https://github.com/RaczeQ/osm-python-readers-benchmark) — comparison of pyrosm/osmnx/PyOsmium/QuackOSM/PyDriosm.
