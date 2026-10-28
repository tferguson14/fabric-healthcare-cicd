"""Load pinned synthetic lab files only into Files/raw/cicd_lab."""
import argparse
import json
from azure.identity import AzureCliCredential
from azure.storage.filedatalake import DataLakeServiceClient
from azure.core.exceptions import ResourceExistsError
from scripts.common import ROOT, config, FabricClient, require
from scripts.fetch_sample_data import fetch


def seed(stage):
    cfg = config()
    env = cfg["environments"][stage]
    credential = AzureCliCredential()
    item = FabricClient(credential).item(env["workspace_id"], cfg["lakehouse_name"], "Lakehouse")
    require(item["id"].lower() == env["lakehouse_id"], "Lakehouse ID mismatch.")
    local = fetch()
    service = DataLakeServiceClient("https://onelake.dfs.fabric.microsoft.com", credential=credential)
    filesystem = service.get_file_system_client(env["workspace_id"])
    root = f"{env['lakehouse_id']}/Files/raw/cicd_lab"
    for directory in [f"{env['lakehouse_id']}/Files/raw", root]:
        try:
            filesystem.get_directory_client(directory).create_directory()
        except ResourceExistsError:
            pass
    names = json.loads((ROOT / "sample-manifest.json").read_text())["files"]
    for source in [local / (name + ".csv") for name in names] + [ROOT / "sample-manifest.json"]:
        with source.open("rb") as stream:
            filesystem.get_file_client(f"{root}/{source.name}").upload_data(stream, overwrite=True)
        print(f"Seeded {stage}: {source.name}")


if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("--environment", choices=["dev", "test", "prod"], required=True)
    seed(p.parse_args().environment)
