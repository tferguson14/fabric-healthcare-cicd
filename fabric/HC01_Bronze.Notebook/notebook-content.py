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

# # HC01_Bronze
# Load pinned synthetic healthcare fixtures into Bronze tables
# 
# Attach the schema-enabled healthcare_lakehouse in this workspace before running.
# The lab overwrites only its bronze, silver, and gold demonstration tables.


# CELL ********************

from pathlib import Path
import csv
import hashlib
import io
import json

raw = Path('/lakehouse/default/Files/raw/cicd_lab')
manifest = json.loads((raw / 'sample-manifest.json').read_text())
for name, spec in manifest['files'].items():
    content = (raw / (name + '.csv')).read_bytes()
    assert hashlib.sha256(content).hexdigest() == spec['sha256'], f'{name}: wrong fixture bytes'
    records = list(csv.DictReader(io.StringIO(content.decode('utf-8-sig'))))
    assert len(records) == spec['rows'], f'{name}: wrong fixture row count'
    df = (spark.read.option('header', True).option('multiLine', True)
          .option('quote', '"').option('escape', '"')
          .csv(f'Files/raw/cicd_lab/{name}.csv'))
    assert df.columns == spec['columns'], f'{name}: wrong schema'
    assert df.count() == spec['rows'], f'{name}: CSV parsing changed row count'
    df.write.mode('overwrite').option('overwriteSchema', 'true').format('delta').saveAsTable(f'dbo.bronze_{name}')
    print(name, spec['rows'])
print('Bronze complete: seven verified synthetic fixtures.')


# METADATA ********************

# META {
# META   "language": "python",
# META   "language_group": "synapse_pyspark"
# META }
