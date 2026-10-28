import json
import subprocess
import uuid
import pytest
from scripts import common
from scripts import verify_promotion as promotion
from scripts.fetch_sample_data import verify_file


def test_cross_environment_workspace_reuse_is_rejected(tmp_path):
    cfg = {"environments": {s: {"workspace_id": str(uuid.uuid4()), "lakehouse_id": str(uuid.uuid4())} for s in ["dev", "test", "prod"]}}
    cfg["environments"]["test"]["workspace_id"] = cfg["environments"]["dev"]["workspace_id"]
    p = tmp_path / "config.json"; p.write_text(json.dumps(cfg))
    with pytest.raises(ValueError, match="different workspace_id"): common.config(p)


@pytest.mark.parametrize("url", ["https://evil.example/v1/jobs", "http://api.fabric.microsoft.com/v1/jobs", "https://api.fabric.microsoft.com.attacker.example/v1/", "https://api.fabric.microsoft.com/other"])
def test_api_locations_cannot_receive_tokens_off_host(url):
    with pytest.raises(ValueError): common.safe_api_url(url)


def test_tampered_sample_file_rejected():
    with pytest.raises(ValueError, match="checksum"):
        verify_file(b"changed data", {"sha256": "0" * 64})


def fake_api(job_result="success", artifact=True):
    def get(url, **kwargs):
        if url.endswith("/runs"):
            return {"workflow_runs": [{"id": 3, "head_branch": "test", "head_sha": "a" * 40, "conclusion": "success", "html_url": "https://github.com/example/repo/actions/runs/3"}]}
        if url.endswith("/jobs"):
            return {"jobs": [{"name": "Deploy and validate TEST", "conclusion": job_result}]}
        return {"artifacts": [{"name": "test-validation-" + "a" * 40, "expired": False}] if artifact else []}
    return get


def test_successful_test_evidence_is_accepted():
    assert promotion.find_successful_run(fake_api(), "example/repo", "a" * 40).endswith("/3")


@pytest.mark.parametrize("state,artifact", [("skipped", True), ("failure", True), ("success", False)])
def test_skipped_failed_or_missing_evidence_is_rejected(state, artifact):
    with pytest.raises(ValueError, match="No successful TEST"):
        promotion.find_successful_run(fake_api(state, artifact), "example/repo", "a" * 40)


def test_production_requires_identical_tree_and_a_merge(tmp_path, monkeypatch):
    def git(*args):
        return subprocess.check_output(["git", "-C", str(tmp_path), *args], text=True, stderr=subprocess.DEVNULL).strip()
    git("init", "-b", "prod")
    git("config", "user.name", "Lab tests"); git("config", "user.email", "lab@example.invalid")
    (tmp_path / "file").write_text("v0")
    git("add", "."); git("commit", "-m", "baseline")
    root = git("rev-parse", "HEAD")
    git("switch", "-c", "test")
    (tmp_path / "file").write_text("v1"); git("commit", "-am", "tested change")
    tested = git("rev-parse", "HEAD")
    git("switch", "prod"); git("merge", "--no-ff", "test", "-m", "promote")
    monkeypatch.setattr(promotion, "git", git)
    assert promotion.tested_parent(git("rev-parse", "HEAD")) == tested
    with pytest.raises(ValueError, match="two parents"): promotion.tested_parent(root)
    # A production-only adjustment in the merge commit must be rejected.
    (tmp_path / "file").write_text("untested")
    git("add", "."); git("commit", "--amend", "--no-edit")
    with pytest.raises(ValueError, match="differs"): promotion.tested_parent(git("rev-parse", "HEAD"))
