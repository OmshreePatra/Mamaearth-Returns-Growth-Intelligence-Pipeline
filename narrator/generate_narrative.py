import json
import os
from pathlib import Path

from google import genai
from google.genai import types


# ============================================================
# PATH SETUP
# ============================================================

BASE_DIR = Path(__file__).resolve().parent.parent
NARRATOR_DIR = BASE_DIR / "narrator"
FINDINGS_PATH = NARRATOR_DIR / "findings.json"
SAMPLE_OUTPUT_PATH = NARRATOR_DIR / "sample_output.txt"


# ============================================================
# LOAD VERIFIED FINDINGS
# ============================================================

def load_findings():
    with open(FINDINGS_PATH, "r", encoding="utf-8") as file:
        return json.load(file)


# ============================================================
# OFFLINE SCR NARRATOR
# ============================================================

def generate_scr_narrative_offline(findings: dict) -> dict:
    cleaned_revenue = findings["cleaned_total_revenue_inr"]
    raw_revenue = findings["raw_total_revenue_inr"]
    duplicate_delta = findings["duplicate_reconciliation_delta_inr"]

    cod_rate = findings["return_rate_by_payment"]["COD"]
    card_rate = findings["return_rate_by_payment"]["CARD"]
    upi_rate = findings["return_rate_by_payment"]["UPI"]

    risk_segment = findings["highest_risk_segment"]
    risk_payment = risk_segment["payment_method"]
    risk_tier = risk_segment["city_tier"]
    risk_rate = risk_segment["return_rate_pct"]

    peak = findings["true_peak_month"]
    peak_month = peak["month"]
    peak_revenue = peak["revenue_inr"]

    inflated = findings["outlier_inflated_month"]
    inflated_month = inflated["month"]
    apparent_revenue = inflated["apparent_revenue_inr"]
    corrected_revenue = inflated["corrected_revenue_inr"]

    peak_month_name = (
        "March"
        if peak_month == "2026-03"
        else peak_month
    )

    narrative = f"""
Situation
After cleaning the order data, verified total revenue is ₹{cleaned_revenue:,.2f}, compared with raw SQL revenue of ₹{raw_revenue:,.2f}. The analysis shows clear differences in return behaviour across payment methods. COD orders have a return rate of {cod_rate:.1f}%, compared with {card_rate:.1f}% for CARD and {upi_rate:.1f}% for UPI.

Complication
The main return-risk concentration is {risk_payment} orders from Tier-{risk_tier} cities, where the return rate reaches {risk_rate:.1f}%. The raw revenue figure is overstated by ₹{duplicate_delta:,.2f} because of duplicate transactions. In addition, {inflated_month} initially appears to be the strongest revenue month at ₹{apparent_revenue:,.2f}, but after excluding the identified quantity outliers, its corrected revenue falls to ₹{corrected_revenue:,.2f}.

Resolution
Regional operations and finance teams should prioritise reducing COD return risk in Tier-{risk_tier} cities and use the cleaned dataset rather than the raw transaction totals for reporting. After correcting the outlier effect, {peak_month_name} is the true peak month, with verified revenue of ₹{peak_revenue:,.2f}. Future reporting should continue using duplicate checks, outlier flags and segmented return-rate analysis before business decisions are made.
""".strip()

    return {
        "status": "success",
        "narrative": narrative,
        "tokens": None,
        "source": "offline"
    }


# ============================================================
# GEMINI SCR NARRATOR
# ============================================================

def generate_scr_narrative(findings: dict) -> dict:
    api_key = os.getenv("GEMINI_API_KEY")

    # No API key -> deterministic offline fallback
    if not api_key:
        print(
            "No GEMINI_API_KEY detected. "
            "Using offline narrator."
        )

        return generate_scr_narrative_offline(findings)

    system_instruction = """
You are a senior data analyst writing for Mamaearth's regional
operations and finance heads.

Write a concise business narrative using exactly three labeled sections:

Situation
Complication
Resolution

Every numerical value in the response must come directly from the
supplied findings. Do not invent, estimate, infer, alter, or introduce
any statistic that is not present in the findings.

Preserve the supplied numerical values and business meaning.
""".strip()

    # The user prompt is generated from the findings dictionary.
    # Numbers are not manually hardcoded into the prompt.
    user_prompt = f"""
Create an SCR business narrative from these verified findings:

{json.dumps(findings, indent=2)}

Important:
- Mention the cleaned revenue.
- Mention the duplicate-driven reconciliation difference.
- Compare return rates by payment method.
- Identify the highest-risk segment.
- Explain the outlier-inflated month.
- Identify March as the true peak month when supported by the findings.
- Use only numbers contained in the supplied findings.
""".strip()

    try:
        client = genai.Client(
            api_key=api_key,

            # google-genai HttpOptions.timeout is in milliseconds.
            # 15000 ms = 15 seconds.
            http_options=types.HttpOptions(
                timeout=15000
            )
        )

        response = client.models.generate_content(
            model="gemini-3.8-flash",
            contents=user_prompt,
            config=types.GenerateContentConfig(
                system_instruction=system_instruction,

                # Deterministic setting because this is a factual
                # business report, not creative writing.
                temperature=0.0,

                # Explicit token limit as required by the brief.
                max_output_tokens=500
            )
        )

        narrative = response.text

        token_count = None

        if response.usage_metadata is not None:
            token_count = (
                response.usage_metadata.total_token_count
            )

        return {
            "status": "success",
            "narrative": narrative,
            "tokens": token_count,
            "source": "gemini"
        }

    except Exception as err:
        print("\nGemini API call failed:")
        print(str(err))

        print(
            "\nFalling back to deterministic offline narrator."
        )

        offline_result = generate_scr_narrative_offline(
            findings
        )

        offline_result["message"] = str(err)

        return offline_result


# ============================================================
# NUMERIC ACCURACY CHECKER
# ============================================================

def check_required_figures(narrative: str) -> bool:
    normalized = narrative.replace(",", "")

    checks = {
        "cleaned_total_revenue":
            ["97358.30", "97358.3"],

        "cod_return_rate":
            ["44.4"],

        "highest_risk_segment":
            ["54.5"],

        "duplicate_delta":
            ["2501.90", "2501.9"],

        "true_peak_month":
            ["March"],

        "true_peak_revenue":
            ["20318.90", "20318.9"]
    }

    all_passed = True

    print("\n" + "=" * 60)
    print("NUMERIC ACCURACY CHECK")
    print("=" * 60)

    for label, accepted_values in checks.items():
        passed = any(
            value in normalized
            for value in accepted_values
        )

        print(
            f"{label}: "
            f"{'PASS' if passed else 'FAIL'}"
        )

        if not passed:
            all_passed = False

    return all_passed


# ============================================================
# SAVE SAMPLE OUTPUT
# ============================================================

def save_sample_output(narrative: str):
    with open(
        SAMPLE_OUTPUT_PATH,
        "w",
        encoding="utf-8"
    ) as file:
        file.write(narrative)

    print(
        f"\nSample output saved to:\n"
        f"{SAMPLE_OUTPUT_PATH}"
    )


# ============================================================
# MAIN
# ============================================================

if __name__ == "__main__":
    findings = load_findings()

    result = generate_scr_narrative(findings)

    print("\n" + "=" * 60)
    print("SCR NARRATIVE")
    print("=" * 60)

    print(f"\nSource: {result['source']}")

    if result["tokens"] is not None:
        print(f"Tokens: {result['tokens']}")

    print("\n" + result["narrative"])

    checker_result = check_required_figures(
        result["narrative"]
    )

    print("\nOverall checker result:")
    print(
        "PASS"
        if checker_result
        else "FAIL"
    )

    # sample_output.txt must contain a successful Gemini response,
    # not the offline fallback.
    if checker_result and result["source"] == "gemini":
        save_sample_output(
            result["narrative"]
        )

    elif result["source"] == "offline":
        print(
            "\nOffline fallback succeeded."
            "\nGemini sample_output.txt was not overwritten."
        )