# Data Storm 2026 Challenge Brief

## Overview

The objective is to design a robust analytical framework and model to estimate the latent maximum monthly volume potential, in liters, for traditional trade retail outlets in Sri Lanka for January 2026.

The key business shift is from historical-sales-based allocation to potential-based allocation. Historical sales show what an outlet did sell, but not what it could sell if constraints such as credit limits, stockouts, delivery caps, or poor execution were removed.

## Business Context

A leading beverage manufacturer in Sri Lanka operates a distribution network covering more than 80,000 traditional retail outlets, including urban grocery stores, town-center kades, small rural corner shops, eateries, and pharmacies.

Sales teams currently allocate trade marketing budgets, coolers, and promotional discounts using historical sales averages. This can misallocate resources because observed sales may be constrained by operational limitations rather than true consumer demand.

## Current Scope

The challenge focuses on 20,000 traditional trade outlets serviced by 10 key distributors across 4 provinces in Sri Lanka.

| Province | Number of Distributors | Distributor IDs |
| --- | ---: | --- |
| Western | 3 | `DIST_W_01`, `DIST_W_02`, `DIST_W_03` |
| Central | 3 | `DIST_C_01`, `DIST_C_02`, `DIST_C_03` |
| North-Western | 2 | `DIST_NW_01`, `DIST_NW_02` |
| Southern | 2 | `DIST_S_01`, `DIST_S_02` |

## Problem Statement

Estimate the hidden maximum monthly purchase potential for every outlet for January 2026.

There is no perfect ground truth target variable. Potential is a theoretical ceiling and should be treated as a latent variable. Historical volume is censored because observed purchases represent the minimum of:

1. True consumer demand.
2. Systemic constraints such as credit limits, stockouts, or delivery caps.

The model should therefore uncap observed demand using defensible statistical, probabilistic, causal, or business-rule-driven logic.

## Technical Requirements

### Lakehouse Pipeline Architecture

The codebase should follow a Bronze, Silver, and Gold data pipeline structure.

| Layer | Purpose |
| --- | --- |
| Bronze | Ingest all flat files as-is with no transformations. This layer preserves the original data exactly as provided. |
| Silver | Apply data engineering checks and cleaning logic. Invalid records must be quarantined into a rejected records store with documented failure reasons. |
| Gold | Apply feature engineering and produce model-ready datasets using all valid Silver-layer data, including internal and externally acquired data. |

### Reusable Data Quality Checks

Data quality checks should be reusable, parameterizable, and consistently applied across datasets.

Recommended checks include:

- Duplicate checks using configurable primary keys.
- Null checks for mandatory fields.
- Referential integrity checks between foreign keys and reference datasets.
- Value range checks for numeric fields.
- Format and type checks for dates, IDs, and other structured fields.

Records that fail validation should not be silently dropped or carried forward. They should be written to a rejected records store with a clear reason.

## Required Deliverables

### 1. Latent Potential Output

Submit a single CSV file named `teamname_predictions.csv` containing:

| Column | Description |
| --- | --- |
| `Outlet_ID` | Unique outlet identifier. |
| `Maximum_Monthly_Liters` | Predicted uncapped monthly volume potential for January 2026. |

### 2. Reproducible Codebase

Submit the complete GitHub repository or zipped codebase, including:

- `README.md` with instructions to run the pipeline end to end.
- Clear Bronze, Silver, and Gold directory separation.
- Data cleaning, POI acquisition, feature engineering, EDA, modeling, and final prediction code.

### 3. PDF Summary Report

Submit a technical report of at most 5 pages, including the cover page. The report must cover:

- Data forensics and hygiene.
- Records quarantined and failure reasons.
- Reusable data engineering checks.
- POI data acquisition approach.
- POI categories used as catchment demand drivers.
- Method used to map POIs to internal outlets.
- Causal or probabilistic logic for estimating uncapped potential.
- Generative AI transparency log describing how LLMs were used and validated.

## Evaluation Criteria

| Criteria | Weight |
| --- | ---: |
| Data Engineering and Forensics | 40% |
| Methodology and Base Math | 40% |
| Generative AI Utilization and Workflow | 20% |

### Data Engineering and Forensics

Judges will assess whether the solution includes:

- A clear Bronze, Silver, and Gold pipeline.
- A rejected records store.
- Reusable and parameterizable data quality checks.
- Identification and neutralization of legacy system artifacts.
- Robust web scraping or API-based external POI acquisition.
- Relevant features that help isolate true market demand signals.

### Methodology and Base Math

Judges will assess:

- How the team defines and conceptualizes latent potential.
- How the model handles missing ground truth.
- How the method addresses censored historical demand.
- Whether the final uncap logic is mathematically and commercially defensible.

### Generative AI Utilization and Workflow

Judges will assess:

- Whether LLM usage is documented clearly.
- Whether AI was used as an engineering accelerator.
- Whether AI-generated assumptions and code were critically reviewed, tested, and validated.

## Recommended Solution Direction

A strong solution should combine:

- A defensible lakehouse pipeline.
- Thorough data quality checks and rejected-record tracking.
- External geospatial catchment features such as nearby schools, transport hubs, markets, eateries, supermarkets, offices, hospitals, and population-density proxies.
- A transparent latent-demand framework that separates observed volume from constrained potential.
- Explainable final predictions that can support business allocation decisions for trade spend, coolers, and promotions.
