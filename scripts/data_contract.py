"""Independent fixture contract used to check the Spark result."""
from collections import defaultdict
from decimal import Decimal, ROUND_HALF_UP


def expected_summary(claims, encounters, by_facility=False):
    facilities = {r["encounter_id"]: r["facility_name"] for r in encounters}
    totals = defaultdict(lambda: {"claim_count": 0, "denied_claim_count": 0,
        "claim_amount": Decimal("0"), "paid_amount": Decimal("0"), "denied_amount": Decimal("0")})
    seen = set()
    for row in claims:
        if not row["claim_id"] or row["claim_id"] in seen:
            raise ValueError("Claims must have distinct nonempty claim_id values.")
        seen.add(row["claim_id"])
        if row["encounter_id"] not in facilities:
            raise ValueError("Claim references an unknown encounter.")
        if row["claim_status"] not in {"Denied", "Paid", "Paid on Appeal"}:
            raise ValueError("Unexpected claim status.")
        key = (row["payer"], facilities[row["encounter_id"]]) if by_facility else (row["payer"],)
        group = totals[key]
        group["claim_count"] += 1
        group["denied_claim_count"] += int(row["claim_status"] == "Denied")
        for field in ("claim_amount", "paid_amount", "denied_amount"):
            group[field] += Decimal(row[field])
    for group in totals.values():
        group["denial_rate_pct"] = (Decimal(100) * group["denied_claim_count"] / group["claim_count"]).quantize(Decimal("0.0001"), rounding=ROUND_HALF_UP)
    return dict(totals)
