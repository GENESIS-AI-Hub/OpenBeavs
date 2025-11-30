import os
import uuid
import requests
import pytest


@pytest.fixture(scope="session")
def base_url() -> str:
    """
    Base URL for the backend under test.

    - Default: local dev server at http://localhost:8000
    - Override by setting BASE_URL env var, e.g.:
      BASE_URL="https://my-backend-xyz.a.run.app"
    """
    return os.environ.get("BASE_URL", "http://localhost:8000").rstrip("/")


@pytest.fixture(scope="session")
def session() -> requests.Session:
    """
    Reuse a requests Session for connection pooling.
    """
    return requests.Session()


@pytest.mark.contract
def test_contract_root_health(base_url, session):
    """
    Contract: GET / returns a 200 and a JSON body with a 'message' string
    starting with 'OSU Genesis Hub Backend'.
    """
    resp = session.get(f"{base_url}/")
    assert resp.status_code == 200

    data = resp.json()
    assert isinstance(data, dict)
    assert "message" in data
    assert isinstance(data["message"], str)
    assert data["message"].startswith("OSU Genesis Hub Backend")


@pytest.mark.contract
def test_contract_well_known_agent_metadata(base_url, session):
    """
    Contract: GET /.well-known/agent.json returns hub metadata with:
      - name == 'OSU Genesis Hub'
      - capabilities.streaming is True
      - url looks like an http(s) URL
    """
    resp = session.get(f"{base_url}/.well-known/agent.json")
    assert resp.status_code == 200

    data = resp.json()
    assert data.get("name") == "OSU Genesis Hub"

    caps = data.get("capabilities", {})
    assert isinstance(caps, dict)
    assert caps.get("streaming") is True

    url = data.get("url", "")
    assert isinstance(url, str)
    assert url.startswith("http")


@pytest.mark.contract
def test_contract_agents_seeded_cyrano(base_url, session):
    """
    Contract: GET /agents returns a list of agents including the seeded
    'cyrano_agent' from startup.
    """
    resp = session.get(f"{base_url}/agents")
    assert resp.status_code == 200

    agents = resp.json()
    assert isinstance(agents, list)
    assert any(a.get("id") == "cyrano_agent" for a in agents)


@pytest.mark.contract
def test_contract_chat_lifecycle_and_message_roundtrip(base_url, session):
    """
    Contract: we can:
      - create a chat for cyrano_agent
      - fetch it back
      - list it in GET /chats
      - send a message and get an assistant reply
      - fetch messages and see 2 entries (user + assistant)
    """
    # 1) Create chat
    create_payload = {"title": "HTTP contract test", "agent_id": "cyrano_agent"}
    resp = session.post(f"{base_url}/chats", json=create_payload)
    assert resp.status_code == 200
    chat = resp.json()
    chat_id = chat["id"]

    # 2) Get the chat
    resp = session.get(f"{base_url}/chats/{chat_id}")
    assert resp.status_code == 200
    chat_info = resp.json()
    assert chat_info["id"] == chat_id
    assert chat_info["title"] == "HTTP contract test"

    # 3) List chats and confirm chat_id is present
    resp = session.get(f"{base_url}/chats")
    assert resp.status_code == 200
    chats = resp.json()
    all_ids = [c["id"] for c in chats]
    assert chat_id in all_ids

    # 4) Send a message
    msg_payload = {"content": "Hello, Cyrano (HTTP test)"}
    resp = session.post(f"{base_url}/chats/{chat_id}/messages", json=msg_payload)
    assert resp.status_code == 200
    assistant_msg = resp.json()
    assert assistant_msg["role"] == "assistant"
    assert isinstance(assistant_msg["content"], str)

    # 5) Fetch messages and assert user + assistant present
    resp = session.get(f"{base_url}/chats/{chat_id}/messages")
    assert resp.status_code == 200
    history = resp.json()
    assert len(history) == 2
    assert history[0]["role"] == "user"
    assert history[1]["role"] == "assistant"


@pytest.mark.contract
def test_contract_post_message_to_nonexistent_chat(base_url, session):
    """
    Contract: posting a message to a non-existent chat returns 404.
    (Same behavior locally and post-deploy.)
    """
    fake_chat_id = str(uuid.uuid4())
    resp = session.post(
        f"{base_url}/chats/{fake_chat_id}/messages",
        json={"content": "Does this exist?"},
    )
    assert resp.status_code == 404


@pytest.mark.contract
def test_contract_jsonrpc_unknown_method_does_not_crash(base_url, session):
    """
    Contract: /jsonrpc responds with a JSON-RPC error for unknown methods,
    and never crashes (always HTTP 200 with error or result).
    """
    payload = {"jsonrpc": "2.0", "method": "NonExisting", "params": {}, "id": 1}
    resp = session.post(f"{base_url}/jsonrpc", json=payload)
    # JSON-RPC servers typically return 200 even for errors
    assert resp.status_code == 200

    body = resp.json()
    assert isinstance(body, dict)
    assert "error" in body or "result" in body
