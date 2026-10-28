import pytest
from scripts.common import FabricClient


class Response:
    def __init__(self, code, body, headers=None):
        self.status_code = code; self.body = body; self.headers = headers or {"Retry-After": "1"}
    def json(self): return self.body


def client_with_states(monkeypatch, states):
    monkeypatch.setattr("scripts.common.time.sleep", lambda _: None)
    client = FabricClient(credential=object())
    responses = iter([Response(202, {}, {"Location": "https://api.fabric.microsoft.com/v1/workspaces/w/items/i/jobs/instances/j", "Retry-After": "1"})]
        + [Response(200, {"id": "j", "status": s}) for s in states])
    client.request = lambda *args, **kwargs: next(responses)
    return client


def test_job_acceptance_is_not_completion(monkeypatch):
    client = client_with_states(monkeypatch, ["NotStarted", "InProgress", "Completed"])
    assert client.run_job("1" * 32, "2" * 32)["status"] == "Completed"


@pytest.mark.parametrize("status", ["Failed", "Cancelled", "Deduped"])
def test_non_success_terminal_state_fails_release(monkeypatch, status):
    client = client_with_states(monkeypatch, [status])
    with pytest.raises(RuntimeError): client.run_job("1" * 32, "2" * 32)
