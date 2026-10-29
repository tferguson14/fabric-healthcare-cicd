# Healthcare Fabric CI/CD lab

Build a personal Fabric CI/CD demonstration with GitHub Actions, VS Code, Entra OIDC, and fabric-cicd.

**Start with [the lab guide](docs/LAB_GUIDE.md).** Complete one checkpoint at a time. The package contains four importable notebooks, three GitHub workflows, deployment and validation tools, tests, and a pinned source-data manifest. Fabric-generated item definitions are created during Module 2; they cannot contain your real workspace IDs before that setup.

The core lab runs the four notebooks through the Fabric API. Module 9 adds Fabric Data Pipeline orchestration and a Power BI extension. PROD is a dedicated demonstration workspace with synthetic data. The notebook writes replace only the lab's demonstration tables.

Module 6 pairs `feature/claims-by-facility` with `HC-CICD-FEAT-Claims` for isolated runtime testing before the PR merges into `dev`. Three permanent workspaces use the names `HC-CICD-DEV`, `HC-CICD-TEST`, and `HC-CICD-PROD`. Feature and DEV Git synchronization is manual; TEST and PROD are published by GitHub Actions. Follow the guide's lakehouse-binding checks before running a feature notebook.

## Local setup

Use Python 3.12 and run commands from this repository root. Windows PowerShell:

```powershell
py -3.12 -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe -m scripts.validate_repo --allow-bootstrap
.\.venv\Scripts\python.exe -m pytest -q
.\.venv\Scripts\python.exe -m scripts.fetch_sample_data
```

The downloader verifies the seven files against a pinned upstream commit and SHA256 manifest. The downloaded `data/` directory is ignored by Git. The source data is not bundled in this package; internet access to the pinned public source is needed during setup and workflow execution.

## Repository map

| Path | Purpose |
|---|---|
| `bootstrap/` | Import these notebooks into DEV once |
| `fabric/` | Created by Fabric Git integration during the lab |
| `.github/workflows/` | CI, TEST deployment, PROD deployment |
| `scripts/` | Parameter preparation, deployment, binding audit, data seeding, execution, promotion guard |
| `tests/` | Business contract and release safety tests |
| `sample-manifest.json` | Pinned upstream commit, file hashes, schemas, counts |
| `lab-config.example.json` | Copy to `lab-config.json` and enter all environment IDs |
| `docs/LAB_GUIDE.md` | Detailed modules and customer explanations |
| `docs/GIT_FLOW.md` | Feature branches, workspaces, and promotion diagram |
| `docs/architecture.png` | Architecture visual |
| `docs/VALIDATION.md` | What was verified locally and what remains for Fabric |

See [source attribution](SOURCE_NOTICES.md). This is an original teaching implementation adapted to the referenced workflow, not an official Microsoft product or a tested deployment in your tenant.
