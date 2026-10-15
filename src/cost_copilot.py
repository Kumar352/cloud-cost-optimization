"""Data-grounded Q&A for real AWS CUR line items.

The default assistant is deterministic and requires no LLM calls. An optional
Amazon Bedrock path sends only summarized cost aggregates (not account IDs,
resource IDs, or raw billing rows) to a selected foundation model.
"""
from __future__ import annotations

import json
from typing import Any

import pandas as pd


def _currency_view(frame: pd.DataFrame, currency: str) -> pd.DataFrame:
    if "Currency" not in frame.columns:
        raise ValueError("Currency column is required for CUR questions.")
    view = frame.loc[frame["Currency"].astype(str) == str(currency)].copy()
    if view.empty:
        raise ValueError(f"No CUR line items available for currency {currency}.")
    view["line_item_unblended_cost"] = pd.to_numeric(
        view["line_item_unblended_cost"], errors="coerce"
    ).fillna(0.0)
    return view


def build_cur_context(
    frame: pd.DataFrame,
    analysis: dict[str, pd.DataFrame],
    currency: str,
    max_services: int = 8,
) -> dict[str, Any]:
    """Build a small, privacy-conscious context payload for a generative answer."""
    work = _currency_view(frame, currency)
    services = analysis["services"]
    services = services.loc[services["Currency"].astype(str) == str(currency)].head(max_services)
    monthly = analysis["monthly"]
    monthly = monthly.loc[monthly["Currency"].astype(str) == str(currency)]
    outliers = analysis.get("high_cost_line_items", pd.DataFrame())
    if not outliers.empty and "Currency" in outliers.columns:
        outliers = outliers.loc[outliers["Currency"].astype(str) == str(currency)].head(5)

    # Only aggregate information is sent to Bedrock, never account IDs or raw line items.
    return {
        "source": "AWS Cost and Usage Report (CUR 2.0) delivered to project S3 data lake",
        "currency": str(currency),
        "selected_billing_periods": sorted(work["Billing_Period"].dropna().astype(str).unique().tolist()),
        "line_item_count": int(len(work)),
        "reported_unblended_cost_sum": round(float(work["line_item_unblended_cost"].sum()), 6),
        "monthly_or_period_summary": monthly[
            ["Billing_Period", "Reported_Unblended_Cost", "Line_Items"]
        ].to_dict(orient="records"),
        "top_services": services[
            ["Service", "Reported_Unblended_Cost", "Line_Items"]
        ].to_dict(orient="records"),
        "high_cost_review_candidates": (
            outliers[
                [
                    col for col in [
                        "Billing_Period", "Service", "Usage_Type",
                        "line_item_unblended_cost", "Outlier_Upper_Bound",
                    ] if col in outliers.columns
                ]
            ].to_dict(orient="records")
            if not outliers.empty else []
        ),
        "limitations": [
            "Latest billing period may be incomplete.",
            "Reported unblended line-item costs are not necessarily the final invoice total.",
            "Currencies must not be combined.",
            "A high-cost outlier is a review candidate, not proof of waste.",
            "CUR alone does not prove resource utilization or guaranteed savings.",
        ],
    }


def answer_cur_question(
    question: str,
    frame: pd.DataFrame,
    analysis: dict[str, pd.DataFrame],
    currency: str,
) -> str:
    """Answer common FinOps questions from the loaded CUR data without guessing."""
    question = " ".join(str(question).lower().split())
    if not question:
        return "Ask about reported spend, the most expensive AWS services, billing-period trends, line-item types, or high-cost review candidates."

    context = build_cur_context(frame, analysis, currency)
    services = context["top_services"]
    periods = context["monthly_or_period_summary"]
    outliers = context["high_cost_review_candidates"]
    amount = lambda value: f"{float(value):,.2f} {currency}"

    if any(token in question for token in ("help", "what can you", "examples", "what can i ask")):
        return (
            "I can answer from the currently loaded AWS CUR records. Try: "
            "“What is the reported total?”, “Which services cost the most?”, "
            "“Did cost increase between periods?”, “Show high-cost line items”, "
            "or “What should I investigate to reduce cost?”. "
            "I do not infer unused resources or guaranteed savings from billing records alone."
        )

    if any(token in question for token in ("anomal", "outlier", "unusual", "high-cost", "high cost", "spike")):
        if not outliers:
            return (
                f"No positive-cost CUR line items in {currency} crossed the current IQR review threshold. "
                "This does not prove there are no billing issues; inspect service and usage trends too."
            )
        rows = []
        for item in outliers[:5]:
            period = item.get("Billing_Period", "unknown period")
            service = item.get("Service", "Unknown service")
            cost = amount(item.get("line_item_unblended_cost", 0))
            rows.append(f"- {period}: {service} — {cost}")
        return (
            f"I found {len(outliers)} high-cost review candidate(s) in the displayed IQR sample for {currency}. "
            "The table is capped at 100 candidates, so this is not necessarily the total count. Top candidates:\n"
            + "\n".join(rows)
            + "\nThese are statistical review candidates, not confirmed billing errors or waste."
        )

    if any(token in question for token in ("trend", "increase", "increased", "decrease", "compare", "over time", "monthly", "period")):
        if not periods:
            return "There are no billing-period summary rows for this currency."
        lines = [
            f"- {p['Billing_Period']}: {amount(p['Reported_Unblended_Cost'])} across {int(p['Line_Items']):,} line items"
            for p in periods
        ]
        text = "Reported unblended costs by CUR billing-period partition:\n" + "\n".join(lines)
        ordered = sorted(periods, key=lambda x: str(x["Billing_Period"]))
        if len(ordered) >= 2:
            previous, latest = ordered[-2], ordered[-1]
            delta = float(latest["Reported_Unblended_Cost"]) - float(previous["Reported_Unblended_Cost"])
            text += (
                f"\nLatest-minus-previous difference: {amount(delta)}. "
                "Do not treat this as a like-for-like monthly increase if the latest month is partial."
            )
        return text

    if any(token in question for token in ("line item type", "charge type", "usage type", "credit", "refund", "discount")):
        types = analysis.get("line_item_types", pd.DataFrame())
        if types.empty:
            return "No line-item type summary is available for this currency."
        types = types.loc[types["Currency"].astype(str) == str(currency)].head(8)
        rows = [
            f"- {row['Line_Item_Type']}: {amount(row['Reported_Unblended_Cost'])} "
            f"({int(row['Line_Items']):,} line items)"
            for _, row in types.iterrows()
        ]
        return "CUR costs grouped by line-item type:\n" + "\n".join(rows)

    if any(token in question for token in ("recommend", "optimi", "save", "saving", "reduce", "waste", "expensive", "top service", "top services", "highest service", "cost the most", "spend the most")):
        if not services:
            return "No AWS service summary is available for this currency."
        top = services[:5]
        rows = [
            f"- {item['Service']}: {amount(item['Reported_Unblended_Cost'])} "
            f"({int(item['Line_Items']):,} line items)"
            for item in top
        ]
        return (
            "Start an investigation with the highest reported service totals:\n"
            + "\n".join(rows)
            + "\nSuggested next steps: compare daily usage and line-item types; inspect AWS Cost Explorer "
            "and the resource inventory/CloudWatch metrics for the highest-cost services; check commitments, "
            "rightsizing, storage lifecycle, and data-transfer architecture where relevant. "
            "CUR is billing evidence, not utilization telemetry, so I will not claim a resource is idle or "
            "assign a savings amount without supporting measurements."
        )

    if any(token in question for token in ("total", "overall", "how much", "reported cost", "reported spend", "spend")):
        return (
            f"The sum of line_item_unblended_cost for the loaded CUR partitions and selected currency "
            f"{currency} is {amount(context['reported_unblended_cost_sum'])} across "
            f"{context['line_item_count']:,} line items. This is a reported unblended line-item sum, "
            "not necessarily the final invoice total; the latest period may be incomplete."
        )

    if services:
        top = services[0]
        return (
            f"I couldn't map that question to a supported calculation yet. In the loaded CUR data for "
            f"{currency}, the highest summarized service is {top['Service']} at "
            f"{amount(top['Reported_Unblended_Cost'])}. Ask about totals, top services, period trends, "
            "line-item types, high-cost review candidates, or cost-investigation ideas."
        )
    return "I could not find enough relevant CUR summary data to answer. Try asking for total reported spend, top services, period trends, or high-cost review candidates."


def invoke_bedrock_answer(
    question: str,
    context: dict[str, Any],
    model_id: str,
    region: str = "us-east-1",
    session=None,
) -> str:
    """Optionally generate a natural-language response using Amazon Bedrock Converse API.

    This calls Bedrock only when the user explicitly chooses the Bedrock mode.
    The account must have model access and bedrock:InvokeModel / Converse permissions.
    """
    model_id = str(model_id or "").strip()
    if not model_id:
        raise ValueError("Set CLOUD_COST_BEDROCK_MODEL_ID or provide a Bedrock model ID.")

    import boto3

    session = session or boto3.Session(region_name=region)
    client = session.client("bedrock-runtime", region_name=region)
    prompt = (
        "You are a cautious cloud FinOps analyst. Answer the user's question using only the supplied "
        "aggregated AWS CUR context. Do not invent amounts, service usage, resource utilization, model "
        "metrics, or savings. If evidence is insufficient, say so. Keep currencies separate. Label the "
        "cost fields as reported unblended line-item sums; the most recent month may be partial and this "
        "is not necessarily the final invoice. Recommendations must be investigation steps, not claims "
        "of confirmed waste. State the relevant billing period and currency when quoting a number.\n\n"
        f"CUR context JSON:\n{json.dumps(context, default=str, ensure_ascii=False)}\n\n"
        f"User question: {question}"
    )
    response = client.converse(
        modelId=model_id,
        messages=[{"role": "user", "content": [{"text": prompt}]}],
        inferenceConfig={"maxTokens": 600, "temperature": 0.1},
    )
    blocks = response.get("output", {}).get("message", {}).get("content", [])
    answer = "\n".join(block.get("text", "") for block in blocks if block.get("text"))
    return answer.strip() or "Bedrock returned no text answer."
