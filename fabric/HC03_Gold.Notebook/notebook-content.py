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

# # HC03_Gold
# Aggregate claim denials for the release demonstration
# 
# Attach the schema-enabled healthcare_lakehouse in this workspace before running.
# The lab overwrites only its bronze, silver, and gold demonstration tables.


# CELL ********************

from pyspark.sql import functions as F

# Module 6 changes this to True in the Fabric-generated Git source.
GROUP_BY_FACILITY = False
dimensions = ['payer', 'facility_name'] if GROUP_BY_FACILITY else ['payer']
claims = spark.table('dbo.silver_claims')
summary = claims.groupBy(*dimensions).agg(
    F.count('*').alias('claim_count'),
    F.sum(F.when(F.col('claim_status') == 'Denied', 1).otherwise(0)).alias('denied_claim_count'),
    F.sum('claim_amount').alias('claim_amount'),
    F.sum('paid_amount').alias('paid_amount'),
    F.sum('denied_amount').alias('denied_amount'))
summary = summary.withColumn('denial_rate_pct',
    F.round(100.0 * F.col('denied_claim_count') / F.col('claim_count'), 4))
summary.write.mode('overwrite').option('overwriteSchema', 'true').format('delta').saveAsTable('dbo.gold_claims_denial')
display(summary.orderBy(*dimensions))


# METADATA ********************

# META {
# META   "language": "python",
# META   "language_group": "synapse_pyspark"
# META }
