# Superserve SDK

Official TypeScript and Python SDKs for the [Superserve API](https://api.superserve.ai) — sandbox infrastructure to run AI Agents in the cloud, powered by Firecracker MicroVMs.

## Sandbox Lifecycle

```
starting --> active <--> idle --> deleted
```

Each sandbox runs **Ubuntu 24.04** with 1 vCPU, 1 GB RAM, 4 GB disk.
Pre-installed: Python 3.12, Node.js 22, npm, git, curl, build-essential.

## Installation

### TypeScript

```bash
npm install @superserve/sdk
# or
bun add @superserve/sdk
```

### Python

```bash
pip install superserve
```

## Quick Start

### TypeScript

```typescript
import { SuperserveApiClient } from "@superserve/sdk";

const client = new SuperserveApiClient({
  apiKey: process.env.SUPERSERVE_API_KEY,
  environment: "https://api.superserve.ai",
});

// Create a sandbox
const sandbox = await client.sandboxes.createSandbox({ name: "my-sandbox" });

// Poll until active
let status = sandbox.status;
while (status !== "active") {
  await new Promise((r) => setTimeout(r, 1000));
  const current = await client.sandboxes.getSandbox({ sandbox_id: sandbox.id! });
  status = current.status;
}

// Run a command
const result = await client.exec.command({
  sandbox_id: sandbox.id!,
  body: { command: "echo Hello from Superserve" },
});
console.log(result.stdout);

// Clean up
await client.sandboxes.deleteSandbox({ sandbox_id: sandbox.id! });
```

### Python

```python
from superserve import SuperserveApi
from superserve.environment import SuperserveApiEnvironment

client = SuperserveApi(
    api_key="YOUR_API_KEY",
    environment=SuperserveApiEnvironment.PRODUCTION,
)

# Create a sandbox
sandbox = client.sandboxes.create_sandbox(name="my-sandbox")

# Poll until active
import time
while sandbox.status != "active":
    time.sleep(1)
    sandbox = client.sandboxes.get_sandbox(sandbox_id=sandbox.id)

# Run a command
result = client.exec.command(
    sandbox_id=sandbox.id,
    command="echo Hello from Superserve",
)
print(result.stdout)

# Clean up
client.sandboxes.delete_sandbox(sandbox_id=sandbox.id)
```

## API Reference

| Resource | Description |
|----------|-------------|
| **Sandboxes** | Create, list, get, patch, pause, resume, delete sandboxes |
| **Exec** | Run commands (sync or SSE streaming) inside a sandbox |
| **Files** | Upload and download files to/from a sandbox |
| **System** | Health check |

Authentication is via the `X-API-Key` header, passed as `apiKey` when creating the client.

### Environments

| Environment | URL |
|-------------|-----|
| Production | `https://api.superserve.ai` |
| Staging | `https://api-staging.superserve.ai` |
| Local | `http://localhost:8080` |

## Running Locally

To test against a local Superserve API server running on `http://localhost:8080`:

### TypeScript

```typescript
const client = new SuperserveApiClient({
  apiKey: process.env.SUPERSERVE_API_KEY,
  environment: "http://localhost:8080",
});
```

### Python

```python
client = SuperserveApi(
    api_key="YOUR_API_KEY",
    base_url="http://localhost:8080",
)
```

### Running the examples with a custom environment

Both examples support `SUPERSERVE_API_KEY` and `SUPERSERVE_API_URL` environment variables. By default they point to production.

```bash
# TypeScript — against staging
cd examples/typescript && bun install
SUPERSERVE_API_KEY=<key> SUPERSERVE_API_URL=https://api-staging.superserve.ai bun run start

# Python — against staging
cd examples/python && python3 -m venv .venv && .venv/bin/pip install -e ../../sdks/python
SUPERSERVE_API_KEY=<key> SUPERSERVE_API_URL=https://api-staging.superserve.ai .venv/bin/python example.py

# Against local
SUPERSERVE_API_KEY=<key> SUPERSERVE_API_URL=http://localhost:8080 bun run start
```

## Examples

Working examples are in the [`examples/`](./examples) directory:

- **[TypeScript](./examples/typescript)** — `cd examples/typescript && bun install && SUPERSERVE_API_KEY=<key> bun run start`
- **[Python](./examples/python)** — `cd examples/python && python3 -m venv .venv && .venv/bin/pip install -e ../../sdks/python && SUPERSERVE_API_KEY=<key> .venv/bin/python example.py`

## Development

SDKs are auto-generated from `openapi.yaml` using [Fern](https://buildwithfern.com). Do not edit files under `sdks/` directly.

```bash
# Regenerate TypeScript SDK
cd fern && fern generate --group local

# Regenerate Python SDK
cd fern && fern generate --group python-sdk

# Preview API docs locally
cd fern && fern docs dev
```

## License

Proprietary
