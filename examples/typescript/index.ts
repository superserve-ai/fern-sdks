import { SuperserveApiClient } from "@superserve/sdk";

const SUPERSERVE_API_KEY = process.env.SUPERSERVE_API_KEY;
if (!SUPERSERVE_API_KEY) {
  console.error("Set SUPERSERVE_API_KEY environment variable");
  process.exit(1);
}

const client = new SuperserveApiClient({
  apiKey: SUPERSERVE_API_KEY,
  environment: process.env.SUPERSERVE_API_URL || "https://api.superserve.ai",
});

async function main() {
  // 1. Health check
  console.log("--- Health Check ---");
  const health = await client.system.health();
  console.log("Status:", health.status, "| Version:", health.version);

  // 2. Create a sandbox
  console.log("\n--- Creating Sandbox ---");
  const sandbox = await client.sandboxes.createSandbox({
    name: "example-sandbox",
    metadata: { purpose: "sdk-example" },
  });
  const sandboxId = sandbox.id!;
  console.log("Created:", sandboxId, "| Status:", sandbox.status);

  // 3. Poll until active
  console.log("\n--- Waiting for sandbox to become active ---");
  let status = sandbox.status;
  while (status !== "active") {
    await new Promise((r) => setTimeout(r, 1000));
    const current = await client.sandboxes.getSandbox({ sandbox_id: sandboxId });
    status = current.status;
    console.log("  Status:", status);
  }

  // 4. Execute a command
  console.log("\n--- Executing Command ---");
  const result = await client.exec.command({
    sandbox_id: sandboxId,
    body: { command: "echo Hello from Superserve && uname -a" },
  });
  console.log("Exit code:", result.exit_code);
  console.log("Stdout:", result.stdout?.trim());
  if (result.stderr) console.log("Stderr:", result.stderr.trim());

  // 5. Clean up
  console.log("\n--- Deleting Sandbox ---");
  await client.sandboxes.deleteSandbox({ sandbox_id: sandboxId });
  console.log("Deleted:", sandboxId);
}

main().catch((err) => {
  console.error("Error:", err);
  process.exit(1);
});
