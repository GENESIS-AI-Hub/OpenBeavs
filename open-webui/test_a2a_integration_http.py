#!/usr/bin/env python3
"""
A2A HTTP contract tests for Open WebUI.

These tests:
- Talk to Open WebUI over real HTTP (no in-process FastAPI client)
- Can run against localhost or a deployed instance via env vars
- Verify basic A2A config + model + chat contract

Required env vars:
- OPENWEBUI_URL       (default: http://localhost:8080)
- OPENWEBUI_API_KEY   (required for privileged A2A config APIs)
- AGENT_URL           (URL of A2A agent, e.g. http://localhost:8000)
"""

import os
import time
import pytest
import requests


def _assert_ok_or_skip_unauthorized(resp: requests.Response, feature: str):
    """
    Helper: if the response is 401, skip the test with a clear message.
    Otherwise, require 200 OK.
    """
    if resp.status_code == 401:
        pytest.skip(
            f"Unauthorized (401) when accessing {feature} - likely missing/invalid OPENWEBUI_API_KEY"
        )
    assert resp.status_code == 200


@pytest.fixture(scope="session")
def openwebui_url() -> str:
    """
    Base URL for Open WebUI backend.

    Defaults to local dev at http://localhost:8080,
    but can be overridden with OPENWEBUI_URL env var.
    """
    return os.environ.get("OPENWEBUI_URL", "http://localhost:8080").rstrip("/")


@pytest.fixture(scope="session")
def api_key() -> str:
    """
    Open WebUI API key.

    Must be set in OPENWEBUI_API_KEY; otherwise we skip the A2A tests.
    """
    key = os.environ.get("OPENWEBUI_API_KEY")
    if not key:
        pytest.skip("OPENWEBUI_API_KEY not set; skipping A2A contract tests")
    return key


@pytest.fixture(scope="session")
def agent_url() -> str:
    """
    URL of the A2A agent.

    Typically something like:
      - http://localhost:8001  (example agent)
      - http://localhost:8000  (your Genesis Hub backend acting as an agent)

    Must be set in AGENT_URL; otherwise we skip tests that require an agent.
    """
    url = os.environ.get("AGENT_URL")
    if not url:
        pytest.skip("AGENT_URL not set; skipping A2A agent contract tests")
    return url.rstrip("/")


@pytest.fixture(scope="session")
def session() -> requests.Session:
    return requests.Session()


@pytest.mark.contract_a2a
def test_a2a_openwebui_config_available(openwebui_url, session):
    """
    Contract: Open WebUI exposes /api/config and returns a JSON object
    with at least a 'version' field.
    """
    resp = session.get(f"{openwebui_url}/api/config", timeout=10)
    assert resp.status_code == 200

    data = resp.json()
    assert isinstance(data, dict)
    assert "version" in data


@pytest.mark.contract_a2a
def test_a2a_config_api_available(openwebui_url, api_key, session):
    """
    Contract: A2A agents config API is reachable with a valid API key:
      GET /api/v1/configs/a2a_agents
    """
    headers = {"Authorization": f"Bearer {api_key}"}
    resp = session.get(
        f"{openwebui_url}/api/v1/configs/a2a_agents",
        headers=headers,
        timeout=10,
    )
    _assert_ok_or_skip_unauthorized(resp, "/api/v1/configs/a2a_agents (GET)")

    data = resp.json()
    # Basic shape checks
    assert isinstance(data, dict)
    assert "ENABLE_A2A_AGENTS" in data
    assert "A2A_AGENT_CONNECTIONS" in data


@pytest.fixture(scope="session")
def ensure_agent_registered(openwebui_url, api_key, agent_url, session):
    """
    Ensure that an A2A agent with AGENT_URL is registered via the A2A config API.

    Returns the full config after registration, so tests can inspect it.
    """
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }

    # 1) Get current config
    resp = session.get(
        f"{openwebui_url}/api/v1/configs/a2a_agents",
        headers=headers,
        timeout=10,
    )
    _assert_ok_or_skip_unauthorized(
        resp,
        "/api/v1/configs/a2a_agents (GET) in ensure_agent_registered",
    )

    config = resp.json()
    connections = config.get("A2A_AGENT_CONNECTIONS", [])

    # 2) Check if our agent is already registered
    for conn in connections:
        if conn.get("url") == agent_url:
            # Ensure A2A is enabled
            config["ENABLE_A2A_AGENTS"] = True
            return config

    # 3) Add our agent connection
    connections.append(
        {
            "url": agent_url,
            "name": "Contract A2A Agent",
            "config": {},
        }
    )

    payload = {
        "ENABLE_A2A_AGENTS": True,
        "A2A_AGENT_CONNECTIONS": connections,
    }

    # 4) Update config
    resp = session.post(
        f"{openwebui_url}/api/v1/configs/a2a_agents",
        headers=headers,
        json=payload,
        timeout=20,
    )
    _assert_ok_or_skip_unauthorized(
        resp,
        "/api/v1/configs/a2a_agents (POST) in ensure_agent_registered",
    )

    updated = resp.json()
    assert updated.get("ENABLE_A2A_AGENTS") is True
    return updated


@pytest.mark.contract_a2a
def test_a2a_agent_shows_in_models_list(
    openwebui_url,
    api_key,
    ensure_agent_registered,
    agent_url,
    session,
):
    """
    Contract: after an A2A agent is registered via config API,
    at least one model owned_by 'a2a-agent' appears in /api/models,
    and ideally one of them corresponds to our AGENT_URL.
    """
    headers = {"Authorization": f"Bearer {api_key}"}

    # Wait briefly in case there's async model cache refresh
    time.sleep(2)

    resp = session.get(
        f"{openwebui_url}/api/models", headers=headers, timeout=20
    )
    _assert_ok_or_skip_unauthorized(resp, "/api/models (GET)")

    data = resp.json()
    models = data.get("data", [])
    assert isinstance(models, list)

    agent_models = [m for m in models if m.get("owned_by") == "a2a-agent"]
    assert agent_models, "No A2A agent models found in /api/models"

    # Try to find one that matches our agent URL if it's present in the info
    matching = [
        m
        for m in agent_models
        if agent_url in str(
            m.get("info", {}).get("params", {}).get("url", "")
        )
    ]

    if matching:
        selected = matching[0]
    else:
        selected = agent_models[-1]  # fall back to last A2A agent model

    # Stash model id on pytest module so the next test can reuse it
    pytest.selected_a2a_model_id = selected["id"]


@pytest.mark.contract_a2a
def test_a2a_chat_completion_with_agent(openwebui_url, api_key, session):
    """
    Contract: we can send a non-streaming chat completion request
    to an A2A agent model and receive a textual response.

    NOTE: This test assumes that test_a2a_agent_shows_in_models_list
    has already selected pytest.selected_a2a_model_id.
    """
    model_id = getattr(pytest, "selected_a2a_model_id", None)
    if not model_id:
        pytest.skip(
            "No A2A model ID selected; previous test likely failed or did not run"
        )

    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }

    payload = {
        "model": model_id,
        "messages": [
            {
                "role": "user",
                "content": "Hello! This is an A2A contract test message.",
            }
        ],
        "stream": False,
    }

    resp = session.post(
        f"{openwebui_url}/api/chat/completions",
        headers=headers,
        json=payload,
        timeout=60,
    )
    _assert_ok_or_skip_unauthorized(
        resp, "/api/chat/completions (POST to A2A model)"
    )

    data = resp.json()
    assert "choices" in data
    assert isinstance(data["choices"], list)
    assert data["choices"], "No choices returned from chat completion"

    message = data["choices"][0].get("message", {})
    content = message.get("content", "")
    assert isinstance(content, str)
    assert content != ""
