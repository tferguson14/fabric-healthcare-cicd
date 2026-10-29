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

# # HC02_Silver
# Validate keys and build typed claims with facility context
# 
# Attach the schema-enabled healthcare_lakehouse in this workspace before running.
# The lab overwrites only its bronze, silver, and gold demonstration tables.


# CELL ********************

from pyspark.sql import functions as F

def unique_key(df, key):
    assert df.filter(F.col(key).isNull() | (F.trim(F.col(key)) == '')).count() == 0, key + ': missing keys'
    assert df.select(key).distinct().count() == df.count(), key + ': duplicates'

patients = spark.table('dbo.bronze_patients')
encounters = spark.table('dbo.bronze_encounters')
claims = spark.table('dbo.bronze_claims')
unique_key(patients, 'patient_id')
unique_key(encounters, 'encounter_id')
unique_key(claims, 'claim_id')
assert encounters.join(patients.select('patient_id'), 'patient_id', 'left_anti').count() == 0
assert claims.join(encounters.select('encounter_id'), 'encounter_id', 'left_anti').count() == 0
assert claims.join(patients.select('patient_id'), 'patient_id', 'left_anti').count() == 0

patients = patients.withColumn('age', F.col('age').cast('int'))
encounters = encounters.withColumn('encounter_date', F.to_date('encounter_date'))
claims = claims.withColumn('claim_date', F.to_date('claim_date'))
from decimal import Decimal

for field in ['claim_amount', 'paid_amount', 'denied_amount']:
    claims = claims.withColumn(field, F.col(field).cast('decimal(18,2)'))
    assert claims.filter(F.col(field).isNull()).count() == 0, field + ': missing or invalid amount'
    if field != 'denied_amount':
        assert claims.filter(F.col(field) < 0).count() == 0, field + ': negative amount'

# Explicit exceptions for this pinned synthetic dataset; preserve source values.
negative_denials = claims.filter(F.col('denied_amount') < 0).select(
    'claim_id', 'claim_status', 'claim_amount', 'paid_amount', 'denied_amount'
).collect()

expected_negative_denials = {
    'CL00407': Decimal('-537.29'),
    'CL00438': Decimal('-59.10'),
    'CL00627': Decimal('-121.63'),
    'CL00789': Decimal('-245.23'),
    'CL00969': Decimal('-33.46'),
    'CL01012': Decimal('-151.80'),
}

assert {
    r['claim_id']: r['denied_amount'] for r in negative_denials
} == expected_negative_denials, 'Unexpected negative denied amounts'

assert all(
    r['claim_status'] == 'Paid on Appeal'
    and r['denied_amount'] == r['claim_amount'] - r['paid_amount']
    for r in negative_denials
), 'Known sample-data exception changed'

print(f'Preserved {len(negative_denials)} known synthetic-data exceptions.')
lookup = encounters.select('encounter_id', F.col('patient_id').alias('encounter_patient_id'), 'facility_name')
claims = claims.join(lookup, 'encounter_id', 'inner')
assert claims.filter(F.col('patient_id') != F.col('encounter_patient_id')).count() == 0
claims = claims.drop('encounter_patient_id')
assert claims.filter(F.col('payer').isNull() | F.col('facility_name').isNull()).count() == 0
for name, df in [('patients', patients), ('encounters', encounters), ('claims', claims)]:
    df.write.mode('overwrite').option('overwriteSchema', 'true').format('delta').saveAsTable('dbo.silver_' + name)
    print(name, df.count())


# METADATA ********************

# META {
# META   "language": "python",
# META   "language_group": "synapse_pyspark"
# META }
