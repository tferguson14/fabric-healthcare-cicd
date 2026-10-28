from decimal import Decimal
import pytest
from scripts.data_contract import expected_summary


def fixtures():
    encounters = [{"encounter_id": "e1", "facility_name": "Metro"}, {"encounter_id": "e2", "facility_name": "Riverside"}]
    claims = [{"claim_id": f"c{i}", "encounter_id": encounter, "payer": "Payer A", "claim_status": status,
               "claim_amount": "100.10", "paid_amount": "0.00" if status == "Denied" else "100.10",
               "denied_amount": "100.10" if status == "Denied" else "0.00"}
              for i, (encounter, status) in enumerate([("e1", "Denied"), ("e1", "Denied"), ("e2", "Paid on Appeal")])]
    return claims, encounters


def test_denominator_uses_all_claims_and_appeals_are_not_denied():
    claims, encounters = fixtures()
    result = expected_summary(claims, encounters)[("Payer A",)]
    assert result["claim_count"] == 3
    assert result["denied_claim_count"] == 2
    assert result["denial_rate_pct"] == Decimal("66.6667")
    assert result["claim_amount"] == Decimal("300.30")


def test_facility_grain_keeps_totals_and_separates_rates():
    claims, encounters = fixtures()
    result = expected_summary(claims, encounters, True)
    assert result[("Payer A", "Metro")]["denial_rate_pct"] == 100
    assert result[("Payer A", "Riverside")]["denial_rate_pct"] == 0
    assert sum(row["claim_count"] for row in result.values()) == 3


@pytest.mark.parametrize("mutation", ["duplicate", "orphan", "unknown_status"])
def test_bad_fixture_is_rejected(mutation):
    claims, encounters = fixtures()
    if mutation == "duplicate": claims.append(claims[0].copy())
    if mutation == "orphan": claims[0]["encounter_id"] = "missing"
    if mutation == "unknown_status": claims[0]["claim_status"] = "Unrecognized"
    with pytest.raises(ValueError): expected_summary(claims, encounters)
