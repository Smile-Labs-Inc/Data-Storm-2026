"""Build the causal DAG for the report.

Renders a graphviz DAG for the latent-demand framing:

    outlet_attrs   ->  true_demand
    POI_catchment  ->  true_demand
    constraints    ->  observed_volume
    true_demand    ->  observed_volume   (via min())
    constraints    <-  cooler / SKU breadth / credit cycle / delivery freq

If graphviz is not installed, falls back to writing a Mermaid markdown source
that the team can paste into the PDF report verbatim.
"""

from __future__ import annotations

from pathlib import Path


MERMAID_SRC = """
```mermaid
flowchart LR
    OutletAttrs["Outlet attributes\\n(size, type, cooler)"] --> TrueDemand["True consumer demand\\n(latent)"]
    POI["POI catchment\\n(schools, transport, etc.)"] --> TrueDemand
    LK["Sri Lanka calendar\\n(Avurudu, Poya, etc.)"] --> TrueDemand
    Constraints["Operational constraints\\n(credit, stockouts,\\ndelivery, cooler space)"] --> Observed
    TrueDemand --> Observed["Observed volume\\n= min(true, constraints)"]
    Observed -.->|right-censored| Latent["Estimand:\\nE[true demand | X]"]
    style Latent stroke-dasharray: 5
```
"""


def build_dag(out_dir: Path | str) -> dict[str, Path]:
    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    paths: dict[str, Path] = {}

    mermaid_path = out_dir / "dag.mmd"
    mermaid_path.write_text(MERMAID_SRC.strip(), encoding="utf-8")
    paths["mermaid"] = mermaid_path

    try:
        import graphviz

        g = graphviz.Digraph("latent_demand_dag", format="png")
        g.attr(rankdir="LR")
        g.node("OutletAttrs", "Outlet attributes\n(size, type, cooler)")
        g.node("POI", "POI catchment")
        g.node("LK", "LK calendar\n(Avurudu, Poya...)")
        g.node("Constraints", "Constraints\n(credit, stockouts,\ndelivery, cooler)")
        g.node("TrueDemand", "True demand (latent)")
        g.node("Observed", "Observed volume\n= min(true, constraints)")
        g.node("Latent", "Estimand:\nE[true_demand | X]", style="dashed")

        g.edge("OutletAttrs", "TrueDemand")
        g.edge("POI", "TrueDemand")
        g.edge("LK", "TrueDemand")
        g.edge("TrueDemand", "Observed")
        g.edge("Constraints", "Observed")
        g.edge("Observed", "Latent", style="dashed", label="right-censored")

        png_path = out_dir / "dag.png"
        g.render(filename="dag", directory=str(out_dir), format="png", cleanup=True)
        paths["png"] = png_path
    except Exception as e:
        paths["png"] = out_dir / "dag.NOT_RENDERED.txt"
        paths["png"].write_text(
            f"graphviz not available; mermaid source written instead. Error: {e}",
            encoding="utf-8",
        )

    return paths
