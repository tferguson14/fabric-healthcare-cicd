"""Publish the complete, explicit lab scope; never delete orphan items."""
import argparse
import os
from azure.identity import AzureCliCredential
from fabric_cicd import FabricWorkspace, publish_all_items
from scripts.common import ROOT, FabricClient, config, require
from scripts.validate_repo import validate
from scripts.audit_bindings import audit


def deploy(stage):
    validate()
    cfg = config()
    env = cfg["environments"][stage]
    require(os.environ.get("FABRIC_WORKSPACE_ID", "").lower() == env["workspace_id"],
            "FABRIC_WORKSPACE_ID must equal the selected target in lab-config.json.")
    credential = AzureCliCredential()
    client = FabricClient(credential)
    item = client.item(env["workspace_id"], cfg["lakehouse_name"], "Lakehouse")
    require(item["id"].lower() == env["lakehouse_id"], "Create the documented target lakehouse first.")
    workspace = FabricWorkspace(workspace_id=env["workspace_id"], environment=stage,
        repository_directory=str(ROOT / "fabric"), item_type_in_scope=cfg["items_in_scope"], token_credential=credential)
    publish_all_items(workspace)
    audit(stage, client)
    print(f"Published and audited {stage}. Notebook execution is a separate step.")


if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("--environment", choices=["test", "prod"], required=True)
    deploy(p.parse_args().environment)
