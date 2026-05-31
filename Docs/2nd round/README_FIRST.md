# Data Storm v7.0 — Final Round

> **Read this first.** This is the converted problem statement for the Final Round of Data Storm v7.0.
> Organized by the Rotaract Club of University of Moratuwa · Powered by OCTAVE (John Keells Group).

---

## Table of Contents

1. [Background](#1-background)
   - [1.1 Bridge from Preliminary Round](#11-bridge-from-preliminary-round)
   - [1.2 Business Context](#12-business-context)
   - [1.3 Current Scope](#13-current-scope)
2. [Advanced Problem Statement](#2-advanced-problem-statement)
   - [2.1 Spatial Distance-Decay Modeling](#21-spatial-distance-decay-modeling)
   - [2.2 Competitive Catchment Density](#22-competitive-catchment-density)
   - [2.3 Marketing Spend Optimization](#23-marketing-spend-optimization)
3. [Data Description](#3-data-description)
4. [Advanced Technical & Architecture Requirements](#4-advanced-technical--architecture-requirements)
   - [4.1 Functional Explainable AI (XAI) Integration](#41-functional-explainable-ai-xai-integration)
5. [Final Deliverables](#5-final-deliverables)
6. [Evaluation Metrics](#6-evaluation-metrics)

---

## 1. Background

### 1.1 Bridge from Preliminary Round

Welcome to the Final Round of **Data Storm v7.0**. Out of highly competitive preliminary submissions, your team has successfully proven its core data science logic, programmatic data forensics, and foundational Lakehouse architecture.

In Phase 1, the focus was on uncovering historical data anomalies and establishing an initial unconstrained baseline. Now the challenge has evolved. The task is to transform those preliminary pipelines into an **enterprise-grade decision engine**. Leadership is no longer looking for a standalone predictive metric; they expect a comprehensive solution that converts volume potential into **actionable trade marketing strategies**, backed by intuitive user interfaces, automated explainability, and seamless decision-support capabilities.

### 1.2 Business Context

A leading beverage manufacturer in Sri Lanka operates a massive distribution network spanning **over 80,000 traditional retail outlets** — from bustling urban grocery stores in Colombo to small *"kades"* (corner shops) and local eateries in rural outstations.

Currently, sales teams allocate trade marketing budgets, coolers, and promotional discounts based on **historical sales averages**. Leadership considers this fundamentally flawed: historical sales reflect only what an outlet *did* sell, not what it *could* sell. A high-traffic town-center kade might be underperforming due to poor stock management or credit constraints, while a small village shop might already be maxed out.

The company wants to shift from historical-based resource allocation to **Potential-Based Allocation** — predicting the **Maximum Monthly Purchase Potential** of every traditional trade outlet to optimize trade spend and cooler deployments.

### 1.3 Current Scope

This challenge focuses on **20,000 traditional trade outlets** (kades, groceries, eateries, pharmacies, etc.) serviced by **10 key distributors** across **4 key provinces** in Sri Lanka.

| Province       | # Distributors | Distributor IDs                          |
| -------------- | -------------- | ---------------------------------------- |
| Western        | 3              | `DIST_W_01`, `DIST_W_02`, `DIST_W_03`    |
| Central        | 3              | `DIST_C_01`, `DIST_C_02`, `DIST_C_03`    |
| North-Western  | 2              | `DIST_NW_01`, `DIST_NW_02`               |
| Southern       | 2              | `DIST_S_01`, `DIST_S_02`                 |

---

## 2. Advanced Problem Statement

The main objective is to build an analytical solution that **estimates the maximum possible sales volume for January 2026** while considering real-world business limitations and decision-making factors. The solution should go beyond prediction and support actual business decisions.

> The solution should consider the following challenges. *(Well done if already done — but you can always improve your work.)*

### 2.1 Spatial Distance-Decay Modeling

Simply **counting nearby Points of Interest (POIs) within a fixed radius is not enough** for a strong real-world model. Distance must be treated as an important factor: closer places should have a stronger influence than distant ones. For example, a bus stop 20 m away should have a much bigger impact on demand than one 400 m away, even though both are "within range."

Apply **non-linear distance-decay functions** — e.g., Gravity Models, Gaussian decay, or exponential decay — which gradually reduce the influence of a location as distance increases, instead of treating everything equally inside a boundary.

*If distance-decay was already implemented in the preliminary round, further improve and fine-tune it in this phase.*

### 2.2 Competitive Catchment Density

Consider how many **competing outlets** exist around each location to estimate how "crowded" or "isolated" a store is in its local market. An outlet in a dense commercial area with many nearby competitors behaves differently from one in a less crowded or rural-like area.

Use **external location data** to estimate the level of competition and market saturation, then adjust the model to reflect whether an outlet operates in a highly competitive cluster or in a relatively untapped market area.

### 2.3 Marketing Spend Optimization

Assume the company has allocated a fixed promotional budget of **LKR 5 million for the Western Province for January 2026**.

Create a program or optimization model that uses the predicted sales-potential values to decide how this budget should be distributed among distributors and outlets. This may include assigning discounts, merchandising (billboards, posters) incentives, or promotional spending to selected outlets.

**Goal:** maximize the **additional sales volume gained** compared to normal historical sales patterns, while ensuring total spending does **not exceed the LKR 5 million budget**.

---

## 3. Data Description

Finalists continue utilizing the exact same internal datasets provided in Phase 1:

1. **`transactions_history_final.csv`** — Granular outlet-level data.
2. **`outlet_master.csv`** — Outlet related data.
3. **`outlet_master.csv`** — Longitude and Latitude for each outlet.
4. **`distributor_seasonality_details.csv`** — Month-specific seasonality for distributors.
5. **`holiday_list.csv`** — List of holidays.

> **Note:** Expectations for the **External Data Layer (Gold Enrichment)** are significantly raised.

---

## 4. Advanced Technical & Architecture Requirements

All requirements from the Preliminary Round remain fully in effect. The solution must continue to follow a clear **Medallion Lakehouse architecture (Bronze → Silver → Gold)**, ensure **strict pipeline idempotency**, and apply **reusable data quality checks** at every stage. Any corrupted or invalid records must be systematically routed to a dedicated **Rejected Records Store** for traceability and debugging.

### 4.1 Functional Explainable AI (XAI) Integration

Generative AI should **not** be treated as a backend logging tool. It must become a **user-facing layer** that explains model decisions in simple business terms.

Embed a **Dynamic Explainability (XAI) module** directly into the solution pipeline. For each outlet, it should surface:

- Its predicted sales score
- Key model drivers (feature importance / weights)
- Local environment signals (e.g., POI density, competitor intensity)
- Operational constraints (e.g., cooler capacity, supply limits, historical performance patterns)

An **LLM-based component** should then transform this technical information into a clear, human-readable explanation covering:

- **Why** the model gave that outlet its specific score
- **Which** factors increased or decreased the prediction
- **How** local conditions and constraints influenced the result

**Goal:** translate complex statistical and spatial signals into an intuitive narrative that non-technical business leaders can easily understand and trust.

---

## 5. Final Deliverables

This challenge reflects a real-world end-to-end data science and data engineering problem. There is **no hidden "correct answer"** to optimize toward — evaluation is based entirely on the **quality of the approach**: pipeline design, analytical rigor, and business reasoning.

Final teams must submit the following **deliverables**:

1. **The "Latent Potential" Output (CSV)** — `teamname_predictions.csv`
   A single file with final, **uncapped** volume predictions. Must include `Outlet_ID` and the predicted `Maximum_Monthly_Liters` for **January 2026**.

2. **The Marketing Spend Allocation Output (CSV)** — `teamname_budget_allocations.csv`
   A single file with trade allocation for **Western Province** outlets. Must contain `Outlet_ID` and a column with the recommended **Trade Spend Allocation (LKR)** from the optimization task.

3. **The Enterprise Codebase (GitHub link or zipped repo)**
   Complete code (Python scripts / Jupyter Notebooks) for data cleaning, POI scraping, and modeling. Must include a **`README.md`** with clear end-to-end run instructions. *(Extended version of the preliminary round code base.)*

4. **The Outlet Intelligence Web App**
   A functional web application allowing business users to explore and interact with model outputs. Any tech stack is allowed. Must be runnable locally with setup instructions in the `README.md`. The app should support:
   - Browsing outlet-level predictions across the full dataset.
   - Filtering by distributor and/or province.
   - Drilling into a specific outlet to view its predicted potential and the reasoning behind the score.

5. **The Comprehensive Methodology & Technical Paper (PDF)** — *max 10 pages incl. cover*
   Must explicitly address:
   - **a. Data Engineering & Scraping Pipeline** — approach to acquiring external POI data (web scraping, Overpass API, etc.); features engineered to proxy footfall and market potential.
   - **b. Data Cleaning** — initial data quality assessment summary; exact programmatic steps to clean the "dirty" master data and neutralize system artifacts.
   - **c. The Mathematical Framework** — core logic; statistical/causal/probabilistic methods used to handle left-censored demand and "uncap" artificial ceilings.
   - **d. Spend Optimization Logic** — mathematical constraints and allocation strategies applied to the 5M budget.
   - **e. GenAI Transparency Log** — how, where, and why Generative AI (Gemini, Copilot, ChatGPT, etc.) was used as an advanced thought partner, including the most effective prompts.

6. **The Executive Pitch Deck (PDF)** — *strictly capped at 10 slides*
   For a non-technical C-suite audience. Should:
   - **a.** Explain how the framework unmasked outlet potential without dense mathematical jargon.
   - **b.** Demonstrate how trade marketing spend was strategically divided across the Western province network using the new Potential-Based Allocation model.
   - **c.** Quantify strategic business impact — projected incremental volume gains, regional growth opportunities, and overall financial efficiency.
   - **d.** Briefly overview how the allocation strategy can be practically rolled out to sales teams and distributors on the ground.

   **Pitch format:** 10-minute pitch → 5-minute live system demonstration and technical Q&A session.

---

## 6. Evaluation Metrics

The judging panel of data scientists, data engineers, and business leaders evaluates on:

| Criteria                                   | Weight |
| ------------------------------------------ | ------ |
| Methodology and Framework Design           | 30%    |
| Data Engineering and Feature Creation      | 30%    |
| Business Viability and Explainability      | 25%    |
| Generative AI Utilization and Workflow     | 15%    |

### Methodology and Base Math (30%)
- How successfully did the team conceptualize and isolate unobserved **"Latent Potential"** from historical records?
- What advanced modeling approaches (e.g., **Tobit regression, hurdle models, spatial clustering**) were deployed to solve right/left-censored data mechanics?
- Are the physical constraints of traditional retail trade (cooler replenishment cycles) logically represented within the math?

### Data Engineering and Feature Creation (30%)
- Is the codebase demonstrably structured into distinct **Bronze, Silver, and Gold** layers with an effective **quarantine pattern**?
- Are data quality checks **parameterized, reusable**, and applied consistently across multiple internal and external data tables?
- How robust is the POI pipeline? Did the team translate spatial proximity into **non-linear signals (gravity/decay models)** rather than flat counts?

### Business Viability and UI Delivery (25%)
- Does the 5M LKR promotional spend allocation logic make practical commercial sense to maximize absolute volume lifts?
- Is the web application highly functional, intuitive, and capable of displaying localized intelligence quickly?
- Did the team present a clear, compelling corporate narrative during the live pitch that justifies algorithmic outputs to non-technical leadership?

### Generative AI Utilization and Workflow (15%)
- Did the team build a working, dynamic XAI prompt integration inside the web app that generates accurate, highly contextualized business reasoning?
- Is the GenAI Transparency Log comprehensive, clear, and honest about prompts used across the development pipeline?
- Is there explicit evidence that the team rigorously validated and iteratively engineered AI output rather than blindly accepting generated logic?

---

*Source: `Problem Statement - 2nd Round.pdf` — OCTAVE, John Keells Group · Data Storm v7.0 Final Round.*
