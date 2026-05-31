# Visual Designer — Council Round 7 Review

**Report:** `final_report_v3.pdf` · Data Storm 7.0 · smile Labs
**Reviewer role:** Visual Designer
**Date:** 2026-05-16

---

# TL;DR

- The Palatino + smile Labs blue/green/orange palette is internally consistent and semantically sound, but **margins cut to 1.5 cm push body-text line length to ~110 characters/line** — well beyond the comfortable 65–85 cpl reading band.
- Pages 1 and 5 fail the 30-second scan: the cover is logo-free and upper-half empty; page 5 hides the sensitivity robustness result in dense prose instead of a chart.
- Three quick fixes (DAG font, sensitivity heatmap, cover header band) would lift perceived professionalism by roughly two full letter grades.

---

# Per-Page Visual Scorecard

| Page | Title              | Score /10    | One-line evidence                                                                                                                                                                                                                       |
| ---- | ------------------ | ------------ | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| 1    | Cover              | **6 / 10**   | No logo, no brand bar; ~40 % of the page is bare white above the method box; `\Huge` blue title is the only anchor                                                                                                                      |
| 2    | Data Forensics     | **7.5 / 10** | B-S-G TikZ diagram breaks up the tables well; two `\scriptsize` edge labels ("6 DQ checks", "features") are on the edge of legibility at 150 DPI                                                                                        |
| 3    | POI Acquisition    | **6.5 / 10** | Well-structured but entirely figure-free; 80.9 % coverage stat buried in a table row rather than visualised; OSM-tags column in `\texttt{}` at 10 pt is cramped                                                                         |
| 4    | Methodology        | **7 / 10**   | Four method boxes provide rhythm; DAG `\scriptsize` node font + `\tiny` "right-censored" arrow label are borderline unreadable at print size; all four boxes share identical primary-blue colour — no visual hierarchy within the stack |
| 5    | Validation + GenAI | **5 / 10**   | Green `accent!25` OK cells are the clearest hit; sensitivity sweep is prose-only; bibliography is raw `\scriptsize` text with no visual separator, crammed under the deliverables list                                                  |

---

# Typography Critique

**Font choice — Palatino (`\usepackage{palatino}`):**
Palatino is a legitimate choice for a technical-academic document: high x-height, elegant serifs, and good math companion via `amsmath`. It reads as "scholarly" rather than "corporate", which is a minor mismatch for a John Keells business audience who expect something closer to Calibri/Gill Sans territory. Not a blocker, but worth noting.

**Heading hierarchy:**

- `\section`: `\large\bfseries` in `primary` (RGB 0,71,132) — clear
- `\subsection`: `\normalsize\bfseries` in `primary!85` — **only one optical step below section**. At 10 pt body, `\normalsize` bold vs `\large` bold is a very tight gap. A reader skimming quickly may not distinguish section from subsection headings.
- Callout box titles (e.g. "One-line method", "Robust lower bound") are rendered in the same `\normalsize\bfseries` as subsection headers, further collapsing the hierarchy.

**Spacing:**

- `\parskip=0.3em`, `\parindent=0pt` — fine for dense technical content.
- `\titlespacing*` gives sections 0.6 em before and 0.3 em after — correct but minimal. A small increase to 0.8/0.4 em would give headers more breathing room without eating page space.

**Line length (the biggest flaw):**
Margin is `1.5 cm` left/right on A4 (210 mm). Usable text width = 210 − 30 = **180 mm**. At 10 pt Palatino (~2.1 mm average char width for body text), that yields **~86 characters/line** for pure prose — already at the top end. Inside `tabularx` full-width tables (pages 2, 3, 5), the OSM-tag and "AI usage" cells approach **110–120 cpl**, causing the wrapped lines in those cells to feel dense and fatiguing.

**Colour palette assessment:**

| Colour    | RGB           | Use                                         | Verdict                                                       |
| --------- | ------------- | ------------------------------------------- | ------------------------------------------------------------- |
| `primary` | 0, 71, 132    | Headings, methodbox, DAG fill               | Strong, authoritative — good                                  |
| `accent`  | 0, 153, 102   | findingbox, OK cell highlights              | Contrasts well with blue, legible on white                    |
| `warn`    | 215, 95, 0    | caveatbox, Rejected TikZ node               | Orange on white passes WCAG AA (≥4.5:1); semantically correct |
| `soft`    | 240, 244, 248 | Table header rows                           | Subtle — nearly invisible on low-contrast screens/printouts   |
| `rule`    | 180, 192, 205 | (defined but unused in any visible element) | Dead colour — remove                                          |

The palette is coherent. The one jar: all four method boxes on page 4 use identical `primary!8 / primary` colouring. When four boxes stack vertically with the same colour, they merge visually into a blue wall instead of signalling four distinct components.

---

# Information Density

| Page                  | Assessment                                                                                                                                                                                                                                                                                                                              |
| --------------------- | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| P1 Cover              | **Too sparse** — upper 40 % is empty, the table is 7 rows, the two callout boxes are appropriately sized. Room to add a logo or coloured header band without crowding.                                                                                                                                                                  |
| P2 Forensics          | **Balanced** — diagram + 2 tables fill the page without feeling cramped.                                                                                                                                                                                                                                                                |
| P3 POI                | **Slightly dense** — the 9-row OSM category table plus the 63-column feature description prose plus the caveat box nearly fills the page. A horizontal bar chart replacing the feature-design prose paragraph would relieve density while adding signal.                                                                                |
| P4 Methodology        | **Dense by necessity** — four stacked tcolorboxes with equation display math. Acceptable for a methodology page, but the identical colouring (noted above) makes it feel monotone.                                                                                                                                                      |
| P5 Validation + GenAI | **Overpacked** — three tables + deliverables list + unseparated bibliography in ~30 lines of scriptsize text at the bottom. The bibliography has no visual separator (no `\vspace`, no rule, no heading) from the deliverables bullet list. At screen zoom it looks like the deliverables ran out of bullets and turned into citations. |

**Page 5 bibliography specifically:** Six references rendered at `\scriptsize` (≈8 pt) with `\bibitemsep=0pt` — zero leading between entries. Reference [5] (Romano et al.) and [6] (Chernozhukov et al.) at this size and density are difficult to parse. A thin rule and `\footnotesize` (9 pt) with 2 pt `\bibitemsep` would be legible without eating more than 3 extra lines.

---

# 30-Second Test (per page)

**PASS / FAIL criteria:** Can a skimming judge find the single most important number or claim within 30 seconds?

| Page           | Result              | Reason                                                                                                                                                                                                                                   |
| -------------- | ------------------- | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| P1 Cover       | **PASS**            | `1.250×` and `6/6 PASS` are bold in the KPI table — they pop immediately                                                                                                                                                                 |
| P2 Forensics   | **PASS**            | The B-S-G diagram signals "data pipeline" at a glance; "10,179 rows rejected" is visible in the reject box                                                                                                                               |
| P3 POI         | **BORDERLINE FAIL** | "42,386 POIs" and "80.9 %" are in table cells — scannable, but there is no chart to make the coverage number viscerally obvious; a judge reads the whole table before extracting the headline                                            |
| P4 Methodology | **FAIL**            | The four method boxes are a uniform blue wall; no callout number, no bold headline figure is immediately visible. A judge must read to find `cs ≥ 0.40 → 1.25× uplift floor` — it's bolded inside a method box, but buried mid-paragraph |
| P5 Validation  | **PASS (barely)**   | The green `OK` column in Table 4 is the visual hit — judges find the "all green" pattern fast. The sensitivity result (`[1.000, 1.022]`) is hidden in prose                                                                              |

---

# Figures Audit

## B-S-G pipeline TikZ (Page 2)

**Readable? Yes, just.** The four-node horizontal chain (Raw CSVs → Bronze → Silver → Gold) with the downward Rejected branch is clean and appropriately sized (~40% of text width). Edge labels "6 DQ checks" and "features" are rendered at `\scriptsize` — at 150 DPI PNG they are legible but marginal at print size. The `warn!12` fill on the Rejected box is semantically correct.

**Crowded? No.** Adequate whitespace between nodes (0.8 cm gap). The figure does its job.

**One issue:** The arrow from `(silver) -- node[above]{features} (gold)` mislabels direction — the annotation says "features" but the conceptual content is "feature parquet output", not just the data path. A label like "feature parquet" would be more precise.

## DAG TikZ (Page 4)

**Readable? Barely.** Node text is `\scriptsize` (≈8 pt at document size). The edge label `right-censored` is `\tiny` (≈6 pt) — this is **below the minimum legible print size of 7 pt**. At 150 DPI rendered PNG it appears as ~5-6 px text. On paper it would require a magnifier.

**Crowded? Yes.** `node distance=0.8cm and 1.2cm` is tight. The rightmost "Estimand E[Y*|X]" node in a dashed box overlaps with the edge label space. The figure needs either (a) increased `node distance` to 1.0 cm and 1.8 cm, or (b) a wider figure scale.

**Fix:** Change `font=\scriptsize` → `font=\small` in `attr/latent/obs` styles; change `\tiny` → `\scriptsize` on the right-censored label; increase `xshift` on the estimand node from `0.4cm` to `1.0cm`.

## Missing charts — where text should be a figure

1. **Page 3 — POI category bar chart:** The 9-row count table (5,694 / 5,799 / 2,007 / ...) is information-rich but visually flat. A horizontal `pgfplots` bar chart (10 lines of code) would make the religious-places dominance (9,255 — the highest count) immediately visible.
2. **Page 5 — Sensitivity heatmap or bar chart:** The sensitivity sweep (`0.85/0.90/0.95 × 3 schemes × 5 cap multipliers`) produces a 3×3×5 result space, but the report reduces it to a single prose sentence: "remains in [1.000, 1.022]". A 3×3 `pgfplots` colour-coded heatmap of median uplift by quantile × scheme (15 cells) would be the strongest single robustness visual in the document. Effort: ~25 minutes.

---

# 3 Concrete Visual Fixes (ranked by ROI)

## Fix 1 — DAG node/label font bump (Page 4) · ~5 min · Impact: +1.5 pts on p4

**Problem:** `font=\scriptsize` in node styles and `font=\tiny` on the right-censored edge make the Figure 2 DAG unreadable at print size.

**Fix in `final_report_v3.tex`:**

```latex
% In tikzpicture styles on page 4, change:
attr/.style={..., font=\small},          % was \scriptsize
latent/.style={..., font=\small},        % was \scriptsize
obs/.style={..., font=\small},           % was \scriptsize

% Edge label:
\draw[ar, dashed, gray] (yo) -- node[above, font=\scriptsize]{right-censored} (est);
%                                        ^^^^^^^^^^^^^ was \tiny

% And widen the estimand node:
\node[latent, right=of yo, xshift=1.0cm] (est) {...};  % was xshift=0.4cm
```

**ROI:** Lowest effort, highest legibility gain. The DAG is the only causal figure in the report — it must be readable.

---

## Fix 2 — Sensitivity heatmap to replace prose (Page 5) · ~25 min · Impact: +2 pts on p5

**Problem:** The most important robustness claim ("prediction is stable across all knob combinations") is invisible to a skimming judge because it is prose.

**Fix:** Replace the sensitivity paragraph with a `pgfplots` matrix plot (3 rows = quantile; 3 cols = scheme; cell value = median uplift). Add a `\colorbar` from white (1.000) to `accent` (1.025). Caption: "Median uplift across all 45 sweep combinations. All cells in [1.000, 1.022]; cap-binding rate 0 % throughout."

This turns a forgettable paragraph into the most memorable visual on p5 and directly answers the "robustness" rubric criterion.

---

## Fix 3 — Cover header band (Page 1) · ~15 min · Impact: +1.5 pts on p1

**Problem:** The cover is text-only. The upper 40 % is bare white. A John Keells executive flipping to page 1 gets no visual brand signal.

**Fix:** Add a full-width coloured band at the top of the cover page. In LaTeX this requires `\begin{tikzpicture}[remember picture, overlay]` with a filled rectangle from `(current page.north west)` to a point 3 cm below:

```latex
\begin{tikzpicture}[remember picture, overlay]
  \fill[primary] (current page.north west) rectangle
    ([yshift=-3cm]current page.north east);
  \node[anchor=north, text=white, font=\Large\bfseries, yshift=-1.2cm]
    at (current page.north) {smile Labs · Data Storm 7.0};
\end{tikzpicture}
\vspace*{0.8cm}  % adjust to push title below band
```

This takes the cover from "LaTeX article" to "branded submission" in 10 lines. Move the `\Huge` title to white-on-primary if you use a full header band, or keep it blue on white below the band.

---

# Verdict

**For a John Keells panel of business + design-literate executives:**

**Rating: "Credible but homebrew" — not yet "professional".**

The document has clear structural logic, consistent colour semantics, and genuinely useful TikZ diagrams. The Palatino serif gives it a scholarly seriousness that some executives will read as competence. However:

- No logo or brand band on the cover breaks brand trust immediately.
- The DAG on page 4 (the conceptual centrepiece) is printed at sizes that require a magnifier — a room-filling projector or a scanned printout will render it illegible.
- The sensitivity robustness claim — arguably the strongest credibility argument in the document — is invisible in prose on page 5.
- The bibliography crammed without separation below the deliverables list looks like a formatting error, not a design choice.

With the three fixes above (total ~45 minutes of LaTeX work), the document would cross into **"polished technical submission"** territory. Without them, a design-literate judge will notice the cover and page 5 within the first 10 seconds and the overall impression will be anchored lower than the methodology deserves.

**Score before fixes: 6.4 / 10 (visual dimension only)**
**Score after fixes: 8.0 / 10 (estimated)**
