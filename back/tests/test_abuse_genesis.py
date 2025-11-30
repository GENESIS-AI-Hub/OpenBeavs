# back/tests/test_abuse_genesis.py
import requests
import pytest

# Uses the fixtures from conftest.py:
# - app_and_state
# - client


def test_abuse_oversized_http_message_content(client, app_and_state):
    """
    Oversized message body should not crash the server.
    We don't enforce a size limit yet, but this documents behavior under large input.
    """
    # Create a normal chat
    chat = client.post(
        "/chats",
        json={"title": "BigMsg", "agent_id": "cyrano_agent"},
    ).json()
    chat_id = chat["id"]

    big_content = "A" * 500_000  # 500 KB of text

    resp = client.post(
        f"/chats/{chat_id}/messages",
        json={"content": big_content},
    )

    # Current implementation likely returns 200,
    # but we explicitly allow 400/413 if a limit is added later.
    assert resp.status_code in (200, 400, 413)

    # If it accept it, make sure history is consistent
    if resp.status_code == 200:
        hist = client.get(f"/chats/{chat_id}/messages").json()
        assert len(hist) == 2
        assert hist[0]["role"] == "user"
        assert hist[1]["role"] == "assistant"


def test_abuse_jsonrpc_missing_params_no_crash(client):
    """
    JSON-RPC call with missing 'params' should return a JSON-RPC error, not crash.
    """
    payload = {
        "jsonrpc": "2.0",
        "method": "SendMessageRequest",
        # 'params' intentionally omitted
        "id": 1,
    }
    r = client.post("/jsonrpc", json=payload)
    assert r.status_code == 200
    body = r.json()
    # Either a JSON-RPC error or a result, but no 500s / stack traces exposed
    assert "error" in body or "result" in body
    if "error" in body and isinstance(body["error"].get("message"), str):
        # Make sure we don't leak a full traceback
        assert "Traceback" not in body["error"]["message"]


def test_abuse_jsonrpc_oversized_params_no_crash(client, app_and_state):
    """
    Very large JSON-RPC params should not crash the server.
    """
    # Normal chat first
    chat = client.post(
        "/chats",
        json={"title": "RPC Big", "agent_id": "cyrano_agent"},
    ).json()
    chat_id = chat["id"]

    big_msg = "B" * 500_000

    payload = {
        "jsonrpc": "2.0",
        "method": "SendMessageRequest",
        "params": {"chat_id": chat_id, "message": big_msg},
        "id": 1,
    }

    r = client.post("/jsonrpc", json=payload)
    assert r.status_code == 200
    body = r.json()
    assert "error" in body or "result" in body


def test_abuse_fetch_well_known_missing_agent_url(client):
    """
    Calling /agents/fetch-well-known without a usable agent_url should be rejected cleanly.
    """
    # Empty string should be treated as invalid
    r = client.get("/agents/fetch-well-known", params={"agent_url": ""})
    assert r.status_code == 400
    body = r.json()
    # Message comes from explicit HTTPException in main.py
    assert "Agent URL is required" in body.get("detail", "")


def test_abuse_register_by_url_network_failure_surface_safe_error(client, monkeypatch):
    """
    Simulate a network failure when fetching an agent's .well-known/agent.json
    and verify we get a clean 400 with a safe error message (no traceback).
    """

    def fake_get(*args, **kwargs):
        raise requests.exceptions.RequestException("simulated network failure")

    # Patch the 'requests.get' function used inside main.py
    monkeypatch.setattr(requests, "get", fake_get)

    r = client.post(
        "/agents/register-by-url",
        json={"agent_url": "malicious.example.internal"},
    )
    assert r.status_code == 400
    body = r.json()
    detail = body.get("detail", "")
    assert "Error fetching agent's .well-known/agent.json file" in detail
    assert "Traceback" not in detail


def test_abuse_register_by_url_invalid_json_surface_safe_error(client, monkeypatch):
    """
    Simulate a response that is not valid JSON to ensure we return a 400 with a safe error message.
    """

    class FakeResp:
        status_code = 200

        def raise_for_status(self):
            pass

        def json(self):
            # Simulate ValueError from response.json()
            raise ValueError("not json")

    def fake_get(*args, **kwargs):
        return FakeResp()

    monkeypatch.setattr(requests, "get", fake_get)

    r = client.post(
        "/agents/register-by-url",
        json={"agent_url": "broken-agent.example"},
    )
    assert r.status_code == 400
    body = r.json()
    detail = body.get("detail", "")
    assert "Invalid JSON response from agent's .well-known/agent.json file" in detail
    assert "Traceback" not in detail


def test_abuse_jsonrpc_unknown_method_large_payload_no_crash(client):
    """
    Large payload to an unknown JSON-RPC method should still produce a JSON-RPC error, not a crash.
    """
    payload = {
        "jsonrpc": "2.0",
        "method": "NonExisting",
        "params": {"junk": "X" * 500_000},
        "id": 999,
    }
    r = client.post("/jsonrpc", json=payload)
    assert r.status_code == 200
    body = r.json()
    assert "error" in body or "result" in body
    if "error" in body and isinstance(body["error"].get("message"), str):
        assert "Traceback" not in body["error"]["message"]
