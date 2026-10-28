"""Inspect published notebook definitions before any notebook writes data."""
import argparse
import base64
import re
from scripts.common import FabricClient, config, require


def audit(stage, client=None):
    cfg = config()
    env = cfg["environments"][stage]
    client = client or FabricClient()
    lakehouse = client.item(env["workspace_id"], cfg["lakehouse_name"], "Lakehouse")
    require(lakehouse["id"].lower() == env["lakehouse_id"], "Target lakehouse ID differs from configuration.")
    for name in cfg["notebook_order"]:
        item = client.item(env["workspace_id"], name, "Notebook")
        definition = client.definition(env["workspace_id"], item["id"])
        parts = definition["definition"]["parts"]
        text = "\n".join(base64.b64decode(p["payload"]).decode("utf-8") for p in parts if p["path"].endswith(".py"))
        require(text, f"No Fabric Python definition returned for {name}.")
        for field, expected in [("default_lakehouse", env["lakehouse_id"]), ("default_lakehouse_workspace_id", env["workspace_id"])]:
            found = re.findall(r'"' + field + r'"\s*:\s*"([^"]+)"', text)
            require(found and all(v.lower() == expected for v in found), f"Wrong {field} in {name}.")
        for other in set(cfg["environments"]) - {stage}:
            for value in cfg["environments"][other].values():
                require(value not in text, f"Cross-environment ID found in {name}.")
        print(f"Verified {name} -> {stage}/healthcare_lakehouse")


if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("--environment", choices=["dev", "test", "prod"], required=True)
    audit(p.parse_args().environment)
