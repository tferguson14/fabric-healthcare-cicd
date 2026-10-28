"""Enforce a no-ff TEST -> PROD merge whose exact repository tree passed TEST."""
import os
import re
import subprocess
import requests
from scripts.common import require


def git(*args):
    return subprocess.check_output(["git", *args], text=True).strip()


def tested_parent(commit):
    require(bool(re.fullmatch(r"[0-9a-f]{40}", commit)), "Expected full Git commit SHA.")
    parents = git("show", "-s", "--format=%P", commit).split()
    require(len(parents) == 2, "PROD requires a merge commit with two parents. Use Create a merge commit; no squash/rebase/direct push.")
    candidate = parents[1]
    require(git("rev-parse", commit + "^{tree}") == git("rev-parse", candidate + "^{tree}"),
            "PROD content differs from the promoted TEST version. Resolve changes through DEV and retest.")
    return candidate


def find_successful_run(get, repository, commit):
    base = f"https://api.github.com/repos/{repository}/actions"
    runs = get(base + "/workflows/deploy-test.yml/runs", params={"head_sha": commit, "event": "push", "status": "completed", "per_page": 100})["workflow_runs"]
    for run in runs:
        if run["head_branch"] != "test" or run["head_sha"] != commit or run["conclusion"] != "success":
            continue
        jobs = get(base + f"/runs/{run['id']}/jobs", params={"per_page": 100})["jobs"]
        if not any(j["name"] == "Deploy and validate TEST" and j["conclusion"] == "success" for j in jobs):
            continue
        artifacts = get(base + f"/runs/{run['id']}/artifacts", params={"per_page": 100})["artifacts"]
        if any(a["name"] == "test-validation-" + commit and not a["expired"] for a in artifacts):
            return run["html_url"]
    raise ValueError("No successful TEST deployment and validation receipt for this exact source commit. Run or re-run TEST first.")


def main():
    candidate = tested_parent(os.environ["GITHUB_SHA"])
    session = requests.Session()
    session.headers.update({"Authorization": "Bearer " + os.environ["GH_TOKEN"], "Accept": "application/vnd.github+json", "X-GitHub-Api-Version": "2022-11-28"})
    def get(url, **kwargs):
        response = session.get(url, timeout=60, **kwargs)
        response.raise_for_status()
        return response.json()
    url = find_successful_run(get, os.environ["GITHUB_REPOSITORY"], candidate)
    print(f"Validated TEST source: {candidate}; evidence: {url}")
    if os.getenv("GITHUB_STEP_SUMMARY"):
        with open(os.environ["GITHUB_STEP_SUMMARY"], "a") as f:
            f.write(f"Production tree matches tested commit `{candidate}`. TEST evidence: {url}\n")


if __name__ == "__main__":
    main()
