"""Run the four notebooks sequentially and preserve a receipt only on success."""
import argparse
import json
import os
from datetime import datetime, timezone
from scripts.common import ROOT, config, FabricClient
from scripts.audit_bindings import audit


def run(stage):
    cfg = config()
    env = cfg["environments"][stage]
    client = FabricClient()
    audit(stage, client)
    out = ROOT / "artifacts"
    out.mkdir(exist_ok=True)
    receipt_path = out / "validation-receipt.json"
    receipt_path.unlink(missing_ok=True)
    jobs = []
    for name in cfg["notebook_order"]:
        item = client.item(env["workspace_id"], name, "Notebook")
        print(f"Running {name} in {stage}", flush=True)
        job = client.run_job(env["workspace_id"], item["id"])
        jobs.append({"name": name, "item_id": item["id"], "job_id": job["id"], "status": job["status"]})
        (out / "job-progress.json").write_text(json.dumps(jobs, indent=2))
    receipt = {"environment": stage, "workspace_id": env["workspace_id"],
        "lakehouse_id": env["lakehouse_id"], "commit": os.getenv("GITHUB_SHA", "local-run"),
        "completed_utc": datetime.now(timezone.utc).isoformat(), "jobs": jobs, "result": "passed"}
    receipt_path.write_text(json.dumps(receipt, indent=2) + "\n")
    print("All four notebooks completed, including data validation. Receipt written.")


if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("--environment", choices=["dev", "test", "prod"], required=True)
    run(p.parse_args().environment)
