# Fabric notebook source

# METADATA ********************

# META {
# META   "kernel_info": {
# META     "name": "synapse_pyspark"
# META   },
# META   "dependencies": {
# META     "lakehouse": {
# META       "default_lakehouse": "7812ae59-47aa-4b69-8ce1-f54842a0e628",
# META       "default_lakehouse_name": "healthcare_lakehouse",
# META       "default_lakehouse_workspace_id": "3cbafb61-c063-4698-a8fe-360ded48fd06",
# META       "known_lakehouses": [
# META         {
# META           "id": "7812ae59-47aa-4b69-8ce1-f54842a0e628"
# META         }
# META       ]
# META     }
# META   }
# META }

# MARKDOWN ********************

# # HC04_Validate
# Check Spark outputs against an independent raw CSV calculation
# 
# Attach the schema-enabled healthcare_lakehouse in this workspace before running.
# The lab overwrites only its bronze, silver, and gold demonstration tables.


# CELL ********************

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


# METADATA ********************

# META {
# META   "language": "python",
# META   "language_group": "synapse_pyspark"
# META }

# CELL ********************

from pathlib import Path
import csv
import json

raw = Path('/lakehouse/default/Files/raw/cicd_lab')
manifest = json.loads((raw / 'sample-manifest.json').read_text())
for name, spec in manifest['files'].items():
    assert spark.table('dbo.bronze_' + name).count() == spec['rows'], name + ': Bronze count'
for name in ['patients', 'encounters', 'claims']:
    assert spark.table('dbo.silver_' + name).count() == manifest['files'][name]['rows'], name + ': Silver count'
def read_csv(name):
    with (raw / (name + '.csv')).open(encoding='utf-8-sig', newline='') as f:
        return list(csv.DictReader(f))
actual_df = spark.table('dbo.gold_claims_denial')
by_facility = 'facility_name' in actual_df.columns
expected = expected_summary(read_csv('claims'), read_csv('encounters'), by_facility)
actual = actual_df.collect()
assert len(actual) == len(expected), 'Unexpected Gold group count'
seen = set()
for row in actual:
    key = (row['payer'], row['facility_name']) if by_facility else (row['payer'],)
    assert key not in seen and key in expected, 'Unexpected or duplicate Gold group'
    seen.add(key)
    for field, value in expected[key].items():
        assert row[field] is not None, field + ': null result'
        assert abs(Decimal(str(row[field])) - Decimal(str(value))) <= Decimal('0.0001'), f'{key} {field}: wrong result'
print(json.dumps({'validation': 'passed', 'gold_groups': len(actual), 'by_facility': by_facility,
                  'fixture_commit': manifest['commit']}))


# METADATA ********************

# META {
# META   "language": "python",
# META   "language_group": "synapse_pyspark"
# META }
