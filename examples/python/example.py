import os
import sys
import time

from superserve import SuperserveApi
from superserve.environment import SuperserveApiEnvironment

api_key = os.environ.get("SUPERSERVE_API_KEY")
if not api_key:
    print("Set SUPERSERVE_API_KEY environment variable")
    sys.exit(1)

api_url = os.environ.get("SUPERSERVE_API_URL")

client = SuperserveApi(
    api_key=api_key,
    **({"base_url": api_url} if api_url else {"environment": SuperserveApiEnvironment.PRODUCTION}),
)


def main():
    # 1. Health check
    print("--- Health Check ---")
    health = client.system.health()
    print(f"Status: {health.status} | Version: {health.version}")

    # 2. Create a sandbox
    print("\n--- Creating Sandbox ---")
    sandbox = client.sandboxes.create_sandbox(
        name="example-sandbox",
        metadata={"purpose": "sdk-example"},
    )
    sandbox_id = sandbox.id
    print(f"Created: {sandbox_id} | Status: {sandbox.status}")

    # 3. Poll until active
    print("\n--- Waiting for sandbox to become active ---")
    status = sandbox.status
    while status != "active":
        time.sleep(1)
        current = client.sandboxes.get_sandbox(sandbox_id=sandbox_id)
        status = current.status
        print(f"  Status: {status}")

    # 4. Execute a command
    print("\n--- Executing Command ---")
    result = client.exec.command(
        sandbox_id=sandbox_id,
        command="echo Hello from Superserve && uname -a",
    )
    print(f"Exit code: {result.exit_code}")
    print(f"Stdout: {result.stdout.strip() if result.stdout else ''}")
    if result.stderr:
        print(f"Stderr: {result.stderr.strip()}")

    # 5. Clean up
    print("\n--- Deleting Sandbox ---")
    client.sandboxes.delete_sandbox(sandbox_id=sandbox_id)
    print(f"Deleted: {sandbox_id}")


if __name__ == "__main__":
    main()
