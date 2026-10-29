"""Optional extension: verify pipeline references, run it, independently revalidate."""
import argparse
import base64
import json
import os
from datetime import datetime, timezone
from scripts.common import ROOT, FabricClient, config, require
from scripts.audit_bindings import audit


def run(stage):
    cfg = config()
    require("DataPipeline" in cfg["items_in_scope"], "Complete Module 9 and add DataPipeline to scope first.")
    env = cfg["environments"][stage]
    client = FabricClient()
    audit(stage, client)
    pipeline = client.item(env["workspace_id"], "Healthcare_ETL", "DataPipeline")
    definition = client.definition(env["workspace_id"], pipeline["id"])
    text = "\n".join(base64.b64decode(p["payload"]).decode("utf-8")
        for p in definition["definition"]["parts"] if p["path"].endswith("pipeline-content.json"))
    require(text, "No pipeline content returned.")
    json.loads(text)
    for other in set(cfg["environments"]) - {stage}:
        for value in cfg["environments"][other].values():
            require(value not in text, "Pipeline still contains a different environment's ID.")
    for name in cfg["notebook_order"]:
        notebook = client.item(env["workspace_id"], name, "Notebook")
        require(notebook["id"] in text, f"Cannot verify the target reference for {name}. Inspect the pipeline before running.")
    out = ROOT / "artifacts"
    out.mkdir(exist_ok=True)
    (out / "validation-receipt.json").unlink(missing_ok=True)
    jobs = []
    for name, item, job_type in [
        ("Healthcare_ETL", pipeline, "Pipeline"),
        ("HC04_Validate", client.item(env["workspace_id"], "HC04_Validate", "Notebook"), "RunNotebook")]:
        result = client.run_job(env["workspace_id"], item["id"], job_type)
        jobs.append({"name": name, "item_id": item["id"], "job_id": result["id"], "status": result["status"]})
        (out / "job-progress.json").write_text(json.dumps(jobs, indent=2))
    receipt = {"environment": stage, "workspace_id": env["workspace_id"], "lakehouse_id": env["lakehouse_id"],
        "commit": os.getenv("GITHUB_SHA", "local-run"), "completed_utc": datetime.now(timezone.utc).isoformat(),
        "orchestrator": "pipeline", "jobs": jobs, "result": "passed"}
    (out / "validation-receipt.json").write_text(json.dumps(receipt, indent=2) + "\n")


if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("--environment", choices=["dev", "test", "prod"], required=True)
    run(p.parse_args().environment)
