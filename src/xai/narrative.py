"""LLM narrative generation for the XAI layer.

Turns a DriverPayload into a short, plain-language explanation aimed at a
non-technical sales/trade-marketing leader. Uses the Anthropic API when
ANTHROPIC_API_KEY is set; otherwise renders a deterministic template so the
web app and pipeline always produce an explanation (judges may run offline).

The same structured payload is shown to the LLM and to the template, so the
narrative is always grounded in the model's actual drivers — never free-floating.
"""

from __future__ import annotations

import os
import textwrap

from .drivers import DriverPayload

DEFAULT_MODEL = "claude-opus-4-8"

SYSTEM_PROMPT = textwrap.dedent(
    """
    You are a trade-marketing analyst for a beverage distributor in Sri Lanka.
    You explain why a machine-learning model assigned a specific monthly sales
    *potential* (in litres) to a single retail outlet, for a non-technical sales
    leader.

    Rules:
    - Use plain business language. No statistics jargon, no model names, no maths.
    - Ground every sentence in the provided drivers. Never invent numbers.
    - Be specific: name the outlet type, the headroom, and the local conditions.
    - Cover three things: (1) why the score is what it is, (2) which factors
      pushed it up or down, (3) how local conditions and constraints shaped it.
    - 110-160 words, 2 short paragraphs. End with one concrete action if a trade
      spend is recommended.
    """
).strip()


def _payload_to_prompt(p: DriverPayload) -> str:
    lines = [
        f"Outlet {p.outlet_id} — {p.outlet_size} {p.outlet_type} in {p.province} "
        f"province (distributor {p.distributor}).",
        f"Predicted monthly potential: {p.predicted_potential_liters:,.0f} L.",
        f"Normal historical month: {p.normal_baseline_liters:,.0f} L; "
        f"best month ever: {p.best_month_liters:,.0f} L.",
        f"Potential is {p.uplift_vs_normal:.2f}x the normal month and "
        f"{p.uplift_vs_best_month:.2f}x the best month.",
        "",
        "KEY MODEL DRIVERS (signed):",
    ]
    for d in p.drivers:
        lines.append(f"  - [{d['direction']}] {d['name']}: {d['detail']}")
    lines.append("LOCAL ENVIRONMENT SIGNALS:")
    for d in p.local_signals:
        lines.append(f"  - [{d['direction']}] {d['name']}: {d['detail']}")
    lines.append("OPERATIONAL CONSTRAINTS:")
    for d in p.constraints:
        lines.append(f"  - [{d['direction']}] {d['name']}: {d['detail']}")
    if p.allocation:
        a = p.allocation
        lines += [
            "",
            f"RECOMMENDED TRADE SPEND: LKR {a['trade_spend_lkr']:,.0f}, expected to add "
            f"{a['expected_incremental_liters']:,.0f} L "
            f"(LKR {a['expected_incremental_revenue_lkr']:,.0f} revenue).",
        ]
    return "\n".join(lines)


def render_offline_narrative(p: DriverPayload) -> str:
    """Deterministic, grounded narrative used when no LLM is available."""
    ups = [d for d in p.drivers + p.local_signals if d["direction"] == "increases"]
    downs = [d for d in p.drivers + p.local_signals + p.constraints if d["direction"] == "decreases"]

    headroom = p.predicted_potential_liters - p.normal_baseline_liters
    para1 = (
        f"This {p.outlet_size.lower()} {p.outlet_type.lower()} in {p.province} province is "
        f"predicted to be able to move about {p.predicted_potential_liters:,.0f} litres in a "
        f"strong month — roughly {p.uplift_vs_normal:.1f} times its normal "
        f"{p.normal_baseline_liters:,.0f} litres. The model sees around {headroom:,.0f} litres of "
        f"untapped headroom: the outlet has demonstrated higher demand in its best month "
        f"({p.best_month_liters:,.0f} L) than it captures in a typical one, which signals room to grow."
    )

    up_txt = "; ".join(d["name"].lower() for d in ups[:2]) or "its underlying demand"
    down_txt = "; ".join(d["name"].lower() for d in downs[:2]) or "no major limits"
    para2 = (
        f"The score is lifted mainly by {up_txt}. It is held back by {down_txt}. "
    )
    # surface the single most important constraint detail in business terms
    if downs:
        para2 += downs[0]["detail"].split("—")[-1].strip().capitalize() + " "

    if p.allocation:
        a = p.allocation
        para2 += (
            f"Recommended action: invest about LKR {a['trade_spend_lkr']:,.0f} here next month, "
            f"which is expected to unlock roughly {a['expected_incremental_liters']:,.0f} extra litres."
        )
    else:
        para2 += "It was not prioritised for promotional spend this cycle, as the budget earns more elsewhere."

    return f"{para1}\n\n{para2}"


def explain_outlet(
    payload: DriverPayload,
    model: str = DEFAULT_MODEL,
    max_tokens: int = 400,
    force_offline: bool = False,
    api_key: str | None = None,
) -> dict:
    """Return {'narrative', 'source', 'model'}; falls back to template offline.

    api_key, if given, takes precedence over the ANTHROPIC_API_KEY env var so a
    user can paste a key into the web app at runtime.
    """
    api_key = api_key or os.environ.get("ANTHROPIC_API_KEY")
    if force_offline or not api_key:
        return {"narrative": render_offline_narrative(payload), "source": "offline_template", "model": None}

    try:
        import anthropic

        client = anthropic.Anthropic(api_key=api_key)
        msg = client.messages.create(
            model=model,
            max_tokens=max_tokens,
            system=SYSTEM_PROMPT,
            messages=[{"role": "user", "content": _payload_to_prompt(payload)}],
        )
        text = "".join(block.text for block in msg.content if getattr(block, "type", None) == "text")
        return {"narrative": text.strip(), "source": "anthropic_api", "model": model}
    except Exception as exc:  # network / key / quota -> graceful fallback
        return {
            "narrative": render_offline_narrative(payload),
            "source": f"offline_fallback ({type(exc).__name__})",
            "model": None,
        }
