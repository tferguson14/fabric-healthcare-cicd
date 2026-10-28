"""Produce deterministic stage substitutions after Fabric has exported DEV items."""
import yaml
from scripts.common import ROOT, config, require


def expected_parameters(cfg):
    env = cfg["environments"]
    return {"find_replace": [
        {"find_value": env["dev"][key], "replace_value": {stage: env[stage][key] for stage in ("test", "prod")}}
        for key in ("workspace_id", "lakehouse_id")
    ]}


def main():
    cfg = config()
    directory = ROOT / "fabric"
    require(directory.exists(), "First commit the DEV workspace to the fabric folder, then git pull.")
    (directory / "parameter.yml").write_text(yaml.safe_dump(expected_parameters(cfg), sort_keys=False), encoding="utf-8")
    print("Wrote fabric/parameter.yml. Review and commit it with lab-config.json.")


if __name__ == "__main__":
    main()
