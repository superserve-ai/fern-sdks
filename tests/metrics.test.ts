import { expect, test } from "bun:test";
import { SuperserveApi, SuperserveApiClient } from "../sdks/typescript/index";

const sandboxId = "sb-use-123e4567-e89b-12d3-a456-426614174000";
const observation: SuperserveApi.SandboxMetrics = {
  id: sandboxId,
  status: "active",
  cpu: {
    configured_vcpus: 1, effective_vcpus: 2, limit_vcpus: 4,
    usage: { used_vcpus: 1.25, sampled_at: "2026-11-19T16:00:10Z", window_seconds: 1.75, source: "live" },
  },
  memory: {
    configured_bytes: 67108864, effective_bytes: 134217728, limit_bytes: 268435456,
    usage: { used_bytes: 1048576, sampled_at: "2026-11-19T16:00:00Z", source: "last_known" },
  },
  disk: { configured_bytes: 1073741824, effective_bytes: null, limit_bytes: 1073741824, usage: null },
};

function clientFor(body: unknown, status = 200) {
  const requests: Request[] = [];
  const client = new SuperserveApiClient({
    apiKey: "test-key", environment: "https://example.test", maxRetries: 0,
    fetch: async (input, init) => {
      requests.push(new Request(input, init));
      return new Response(JSON.stringify(body), { status, headers: { "Content-Type": "application/json" } });
    },
  });
  return { client, requests };
}

test("metrics preserve raw observations, independent timestamps and null disk", async () => {
  const { client, requests } = clientFor(observation);
  const result = await client.sandboxes.getSandboxMetrics({ sandbox_id: sandboxId });
  expect(requests).toHaveLength(1);
  expect(requests[0].method).toBe("GET");
  expect(new URL(requests[0].url).pathname).toBe(`/sandboxes/${sandboxId}/metrics`);
  expect(requests[0].headers.get("X-API-Key")).toBe("test-key");
  expect(result).toEqual(observation);
});

test("paused allocations remain available with no observations", async () => {
  const payload: SuperserveApi.SandboxMetrics = {
    ...observation, status: "paused",
    cpu: { ...observation.cpu, effective_vcpus: null, usage: null },
    memory: { ...observation.memory, effective_bytes: null, usage: null },
  };
  const { client } = clientFor(payload);
  expect(await client.sandboxes.getSandboxMetrics({ sandbox_id: sandboxId })).toEqual(payload);
});

test("metrics preserve ordinary not-found errors", async () => {
  const { client, requests } = clientFor({ error: { code: "not_found", message: "Sandbox not found" } }, 404);
  await expect(Promise.resolve(client.sandboxes.getSandboxMetrics({ sandbox_id: sandboxId }))).rejects.toBeInstanceOf(SuperserveApi.NotFoundError);
  expect(requests).toHaveLength(1);
});

test("regeneration preserves existing create and list request parameters", async () => {
  const { client, requests } = clientFor({ id: sandboxId });
  await client.sandboxes.createSandbox({ name: "example", allow_internet_access: false, timeout_seconds: 60, metadata: { env: "test" } });
  expect(await requests[0].json()).toMatchObject({ name: "example", allow_internet_access: false, timeout_seconds: 60, metadata: { env: "test" } });
  await client.sandboxes.listSandboxes({ "metadata.{key}": "test" });
  expect(new URL(requests[1].url).searchParams.get("metadata.{key}")).toBe("test");
});
