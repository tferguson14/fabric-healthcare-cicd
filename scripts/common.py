"""Shared configuration and a bounded Fabric REST client. No credentials in files."""
import json
import time
import uuid
from pathlib import Path
from urllib.parse import urlparse

import requests
from azure.identity import AzureCliCredential

ROOT = Path(__file__).resolve().parents[1]
API = "https://api.fabric.microsoft.com/v1"
SCOPE = "https://api.fabric.microsoft.com/.default"


def guid(value):
    return str(uuid.UUID(value))


def config(path=None):
    path = Path(path or ROOT / "lab-config.json")
    if not path.exists():
        raise ValueError("Create lab-config.json from lab-config.example.json and enter all six IDs.")
    cfg = json.loads(path.read_text(encoding="utf-8"))
    for stage in ("dev", "test", "prod"):
        for key in ("workspace_id", "lakehouse_id"):
            cfg["environments"][stage][key] = guid(cfg["environments"][stage][key])
    for key in ("workspace_id", "lakehouse_id"):
        if len({cfg["environments"][s][key] for s in ("dev", "test", "prod")}) != 3:
            raise ValueError(f"Each environment needs a different {key}.")
    if cfg["lakehouse_name"] != "healthcare_lakehouse":
        raise ValueError("This lab expects lakehouse_name healthcare_lakehouse.")
    if cfg["notebook_order"] != ["HC01_Bronze", "HC02_Silver", "HC03_Gold", "HC04_Validate"]:
        raise ValueError("Keep the four lab notebooks in the documented order.")
    scope = set(cfg["items_in_scope"])
    if not {"Lakehouse", "Notebook"} <= scope or not scope <= {"Lakehouse", "Notebook", "DataPipeline"}:
        raise ValueError("Lab scope must include Lakehouse and Notebook; DataPipeline is optional.")
    return cfg


def require(condition, message):
    if not condition:
        raise ValueError(message)


def safe_api_url(url):
    parsed = urlparse(url)
    require(parsed.scheme == "https" and parsed.netloc == "api.fabric.microsoft.com", "Unexpected Fabric API URL.")
    require(parsed.path.startswith("/v1/"), "Unexpected Fabric API path.")
    return url


class FabricClient:
    def __init__(self, credential=None, session=None):
        self.credential = credential or AzureCliCredential()
        self.session = session or requests.Session()

    def request(self, method, path, **kwargs):
        url = safe_api_url(path if path.startswith("https:") else API + path)
        # Refresh the token for every request; the Azure credential caches valid tokens.
        for attempt in range(6):
            response = self.session.request(method, url, headers={
                "Authorization": "Bearer " + self.credential.get_token(SCOPE).token,
                "Content-Type": "application/json"}, timeout=90, **kwargs)
            if response.status_code == 429:
                time.sleep(max(1, int(response.headers.get("Retry-After", "30"))))
                continue
            # Do not automatically replay POSTs after transport errors/5xx: a job may exist.
            response.raise_for_status()
            return response
        raise RuntimeError(f"Rate limit retries exhausted for {method} {url}")

    def items(self, workspace):
        url = f"/workspaces/{guid(workspace)}/items"
        result = []
        while url:
            body = self.request("GET", url).json()
            result.extend(body.get("value", []))
            url = body.get("continuationUri")
        return result

    def item(self, workspace, name, kind):
        matches = [i for i in self.items(workspace) if i["displayName"] == name and i["type"] == kind]
        require(len(matches) == 1, f"Expected exactly one {kind} named {name}; found {len(matches)}.")
        return matches[0]

    def definition(self, workspace, item_id):
        response = self.request("POST", f"/workspaces/{guid(workspace)}/items/{guid(item_id)}/getDefinition")
        if response.status_code == 200:
            return response.json()
        require(response.status_code == 202, "Unexpected definition response.")
        location = safe_api_url(response.headers["Location"])
        deadline = time.monotonic() + 900
        while time.monotonic() < deadline:
            time.sleep(max(1, int(response.headers.get("Retry-After", "5"))))
            response = self.request("GET", location)
            body = response.json()
            if body.get("status") == "Succeeded":
                return self.request("GET", location.rstrip("/") + "/result").json()
            if body.get("status") in {"Failed", "Canceled", "Cancelled"}:
                raise RuntimeError(f"Definition retrieval failed: {body.get('error')}")
        raise TimeoutError("Definition retrieval exceeded 15 minutes.")

    def run_job(self, workspace, item_id, job_type="RunNotebook", timeout_seconds=3600):
        workspace, item_id = guid(workspace), guid(item_id)
        # The current notebook-specific endpoint has a stable release switch.
        if job_type == "RunNotebook":
            path = f"/workspaces/{workspace}/notebooks/{item_id}/jobs/execute/instances?beta=false"
        else:
            require(job_type == "Pipeline", "Unsupported lab job type.")
            path = f"/workspaces/{workspace}/items/{item_id}/jobs/Pipeline/instances"
        response = self.request("POST", path, json={})
        require(response.status_code == 202, "Job was not accepted.")
        location = safe_api_url(response.headers["Location"])
        deadline = time.monotonic() + timeout_seconds
        while time.monotonic() < deadline:
            time.sleep(max(1, int(response.headers.get("Retry-After", "15"))))
            response = self.request("GET", location)
            body = response.json()
            status = body.get("status")
            print(f"Job {body.get('id', item_id)}: {status}", flush=True)
            if status == "Completed":
                return body
            if status in {"Failed", "Cancelled", "Canceled", "Deduped"}:
                raise RuntimeError(f"Job did not complete successfully: {body.get('failureReason') or status}")
        raise TimeoutError(f"Job exceeded timeout; inspect or cancel it in Fabric before retrying: {location}")
