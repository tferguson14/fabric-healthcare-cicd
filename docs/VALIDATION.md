# Validation record

Prepared October 28, 2026. This record separates local verification from cloud execution.

Naming and development-flow revision October 29, 2026: generalized the lab to Healthcare, renamed the four bootstrap notebooks and their script references from HF to HC, and made an isolated feature workspace part of Module 6. Feature workspace provisioning, Git synchronization, manual binding checks, and Spark runs still require live verification. The dependency files retain the user's tested commit `3d06f34` versions.

Rechecked the revised starter in a clean Python 3.12 environment: pinned requirements installed, `pip check` passed, all 20 tests passed, and bootstrap repository validation passed. This verifies the local rename without claiming a live Fabric deployment.

## Passed locally

- Installed the pinned dependency set in a clean Python 3.12 virtual environment; `pip check` found no dependency conflicts.
- Ran `python -m pytest -q`: 20 tests passed. Coverage includes denial-rate denominator and appeal handling, facility grouping, invalid fixture references, distinct environment IDs, token destination validation, fixture tampering, actual Git merge/tree checks, rejection of skipped/failed TEST evidence, and job terminal-status handling.
- Validated all three GitHub workflow files with actionlint 1.7.12, obtained from the official release and checked against its published checksum.
- Ran `python -m scripts.validate_repo --allow-bootstrap`: all Python source, bootstrap notebook code cells, and workflow YAML parsed successfully.
- Downloaded the seven source CSVs from pinned upstream commit `a84b0ff81d27c5da3b1fb8aac5641cd5507a78ac`. Verified SHA256 hashes, CSV column order, and exact record counts against `sample-manifest.json`.
- Evaluated the independent data contract on the actual pinned fixture: 10 payer groups or 30 payer/facility groups, 1025 claims, and 40 claims with status Denied.
- Inspected the installed fabric-cicd 1.4.0 constructor: the deployment script supplies an explicit token credential and keyword parameters compatible with that version.
- Rendered and visually reviewed the companion Word guide and architecture figure.

## Must pass in the user's environment

- DEV item import, schema-enabled lakehouse attachment, and Spark execution.
- Fabric-generated Git export, actual metadata shape, and strict release validation.
- GitHub repository/organization rules and actual environment approval enforcement.
- Entra OIDC trust, tenant settings, Fabric workspace roles, and external OneLake access.
- TEST and PROD publication, environment substitution, binding inspection, data upload, actual notebook job execution, and data validation receipts.
- The complete TEST-to-PROD promotion and failure/recovery exercises.
- Optional Data Pipeline service-principal execution, activity connections, and reference-format checks.
- Any added semantic model/report, connection binding, refresh, and user access checks.

No live Fabric workspace or GitHub repository was created, changed, or deployed by the package authoring process. Local tests do not validate Spark, Fabric permissions, or a customer's tenant policies. The sample source files are downloaded on demand and are not redistributed in this ZIP.

## Package boundaries

The starter intentionally omits environment-specific `lab-config.json` and Fabric-generated `fabric/` items. Module 2 creates the environment inventory; Module 3 generates the item definitions and parameter rules. Deployment jobs remain disabled until repository variable `LAB_READY` is exactly `true`. The script does not invoke orphan deletion or create workspaces automatically.

Treat the lab as ready to demonstrate only after recording the successful live checkpoints and run URLs in the guide's rehearsal record.
