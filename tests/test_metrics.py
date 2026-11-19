import asyncio
import datetime as dt
import json

import httpx
import pytest
from superserve import AsyncSuperserveApi, SuperserveApi
from superserve.errors.not_found_error import NotFoundError


SANDBOX_ID = "sb-use-123e4567-e89b-12d3-a456-426614174000"
OBSERVATION = {
    "id": SANDBOX_ID,
    "status": "active",
    "cpu": {"configured_vcpus": 1, "effective_vcpus": 2, "limit_vcpus": 4,
            "usage": {"used_vcpus": 1.25, "sampled_at": "2026-11-19T16:00:10Z", "window_seconds": 1.75, "source": "live"}},
    "memory": {"configured_bytes": 67108864, "effective_bytes": 134217728, "limit_bytes": 268435456,
               "usage": {"used_bytes": 1048576, "sampled_at": "2026-11-19T16:00:00Z", "source": "last_known"}},
    "disk": {"configured_bytes": 1073741824, "effective_bytes": None, "limit_bytes": 1073741824, "usage": None},
}


def assert_observation(result):
    assert result.id == SANDBOX_ID
    assert result.cpu.usage.used_vcpus == 1.25
    assert result.cpu.usage.window_seconds == 1.75
    assert result.cpu.usage.sampled_at == dt.datetime(2026, 11, 19, 16, 0, 10, tzinfo=dt.timezone.utc)
    assert result.memory.usage.used_bytes == 1048576
    assert result.memory.usage.sampled_at == dt.datetime(2026, 11, 19, 16, 0, tzinfo=dt.timezone.utc)
    assert result.disk.usage is None
    assert result.disk.effective_bytes is None


def test_metrics_request_and_nullable_observations():
    requests = []

    def respond(request):
        requests.append(request)
        return httpx.Response(200, json=OBSERVATION)

    with httpx.Client(transport=httpx.MockTransport(respond)) as transport:
        client = SuperserveApi(api_key="test-key", base_url="https://example.test", httpx_client=transport)
        assert_observation(client.sandboxes.get_sandbox_metrics(sandbox_id=SANDBOX_ID))
    assert len(requests) == 1
    assert requests[0].method == "GET"
    assert requests[0].url.path == f"/sandboxes/{SANDBOX_ID}/metrics"
    assert requests[0].headers["X-API-Key"] == "test-key"


def test_async_metrics_supports_same_response_contract():
    async def run():
        async with httpx.AsyncClient(transport=httpx.MockTransport(lambda request: httpx.Response(200, json=OBSERVATION))) as transport:
            client = AsyncSuperserveApi(api_key="test-key", base_url="https://example.test", httpx_client=transport)
            assert_observation(await client.sandboxes.get_sandbox_metrics(sandbox_id=SANDBOX_ID))

    asyncio.run(run())


def test_paused_null_usage_preserves_current_allocations():
    payload = {**OBSERVATION, "status": "paused", "cpu": {**OBSERVATION["cpu"], "effective_vcpus": None, "usage": None},
               "memory": {**OBSERVATION["memory"], "effective_bytes": None, "usage": None}}
    with httpx.Client(transport=httpx.MockTransport(lambda request: httpx.Response(200, json=payload))) as transport:
        client = SuperserveApi(api_key="test-key", base_url="https://example.test", httpx_client=transport)
        result = client.sandboxes.get_sandbox_metrics(sandbox_id=SANDBOX_ID)
    assert result.cpu.usage is None and result.memory.usage is None and result.disk.usage is None
    assert result.cpu.configured_vcpus == 1 and result.memory.limit_bytes == 268435456


def test_metrics_preserves_not_found_error():
    with httpx.Client(transport=httpx.MockTransport(lambda request: httpx.Response(404, json={"error": {"code": "not_found", "message": "Sandbox not found"}}))) as transport:
        client = SuperserveApi(api_key="test-key", base_url="https://example.test", httpx_client=transport)
        with pytest.raises(NotFoundError):
            client.sandboxes.get_sandbox_metrics(sandbox_id=SANDBOX_ID)


def test_regeneration_preserves_existing_create_and_list_parameters():
    requests = []

    def respond(request):
        requests.append(request)
        return httpx.Response(200, json=[] if request.method == "GET" else {"id": SANDBOX_ID})

    with httpx.Client(transport=httpx.MockTransport(respond)) as transport:
        client = SuperserveApi(api_key="test-key", base_url="https://example.test", httpx_client=transport)
        client.sandboxes.create_sandbox(name="example", allow_internet_access=False, timeout_seconds=60, metadata={"env": "test"})
        client.sandboxes.list_sandboxes(metadata_key="test")
    assert json.loads(requests[0].content)["metadata"] == {"env": "test"}
    assert json.loads(requests[0].content)["allow_internet_access"] is False
    assert json.loads(requests[0].content)["timeout_seconds"] == 60
    assert requests[1].url.params["metadata.{key}"] == "test"
