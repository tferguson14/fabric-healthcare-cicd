"""Offline release checks. --allow-bootstrap permits a repository with no Fabric export yet."""
import argparse
import ast
import json
import uuid
import yaml
from scripts.common import ROOT, config, require
from scripts.prepare_parameters import expected_parameters


def validate(allow_bootstrap=False):
    for path in (ROOT / "scripts").glob("*.py"):
        ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    for path in (ROOT / "bootstrap").glob("*.ipynb"):
        notebook = json.loads(path.read_text())
        for cell in notebook["cells"]:
            if cell["cell_type"] == "code":
                ast.parse("".join(cell["source"]), filename=str(path))
    for path in (ROOT / ".github/workflows").glob("*.yml"):
        yaml.safe_load(path.read_text())
    if not list((ROOT / "fabric").rglob(".platform")):
        require(allow_bootstrap, "No Fabric-generated item definitions. Complete the DEV bootstrap and Git sync.")
        print("Bootstrap package checks passed. This repository is not yet a deployable Fabric release.")
        return
    cfg = config()
    require(yaml.safe_load((ROOT / "fabric/parameter.yml").read_text()) == expected_parameters(cfg),
            "Parameter mappings differ from configuration; run python -m scripts.prepare_parameters.")
    logical_ids, items = set(), set()
    for path in (ROOT / "fabric").rglob(".platform"):
        platform = json.loads(path.read_text())
        meta = platform["metadata"]
        name, kind = meta["displayName"], meta["type"]
        logical_id = str(uuid.UUID(platform["config"]["logicalId"]))
        require(logical_id not in logical_ids, "Duplicate logical ID.")
        require((name, kind) not in items, "Duplicate name and type.")
        logical_ids.add(logical_id)
        items.add((name, kind))
        if kind == "Notebook":
            content = (path.parent / "notebook-content.py").read_text(encoding="utf-8")
            ast.parse(content, filename=str(path.parent))
            for key in ("workspace_id", "lakehouse_id"):
                require(cfg["environments"]["dev"][key] in content, f"{name}: missing DEV {key} attachment.")
            for stage in ("test", "prod"):
                require(cfg["environments"][stage]["workspace_id"] not in content, f"{name}: target ID leaked into source.")
    expected = {(cfg["lakehouse_name"], "Lakehouse")} | {(n, "Notebook") for n in cfg["notebook_order"]}
    require(expected <= items, f"Missing required items: {expected - items}")
    unexpected = {(n, k) for n, k in items if k not in cfg["items_in_scope"]}
    require(not unexpected, f"Unscoped items in lab export: {unexpected}")
    require({n for n,k in items if k == "Notebook"} == set(cfg["notebook_order"]), "Core lab expects exactly four notebooks.")
    print(f"Release checks passed for {len(items)} Fabric definitions.")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--allow-bootstrap", action="store_true")
    validate(parser.parse_args().allow_bootstrap)
