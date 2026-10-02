"""Run the existing real Auth/PostgREST suite against a verified fresh local stack."""
from __future__ import annotations

import argparse
import json
import os
import re
import subprocess
import sys
from pathlib import Path
from urllib.parse import urlsplit

import jwt


ROOT = Path(__file__).resolve().parents[2]


def command(args: list[str]) -> str:
    result = subprocess.run(args, check=True, capture_output=True, text=True)
    return result.stdout


def local_credentials(project_id: str, api_url: str) -> dict[str, str]:
    if not re.fullmatch(r"profit-radar-fresh-proof-[0-9a-f]{12}", project_id):
        raise ValueError("Unexpected fresh project id")
    parsed = urlsplit(api_url)
    if (parsed.scheme != "http" or parsed.hostname not in {"127.0.0.1", "localhost"}
            or parsed.username or parsed.password or parsed.path not in {"", "/"}
            or parsed.query or parsed.fragment or not parsed.port):
        raise ValueError("Fresh integration requires an exact loopback API URL")

    container = f"supabase_kong_{project_id}"
    info = json.loads(command(["docker", "inspect", container]))[0]
    if info["Config"]["Labels"].get("com.supabase.cli.project") != project_id:
        raise ValueError("Unexpected local Supabase gateway label")
    bindings = info["NetworkSettings"]["Ports"].get("8000/tcp") or []
    if not any(binding.get("HostIp") in {"0.0.0.0", "127.0.0.1", "::"}
               and int(binding.get("HostPort", "0")) == parsed.port for binding in bindings):
        raise ValueError("Fresh gateway port does not match the verified container")

    container_env = dict(item.split("=", 1) for item in info["Config"]["Env"])
    content = command(["docker", "exec", container, "cat", container_env["KONG_DECLARATIVE_CONFIG"]])
    keys: dict[str, str] = {}
    for candidate in re.findall(r"eyJ[A-Za-z0-9_-]+\.[A-Za-z0-9_-]+\.[A-Za-z0-9_-]+", content):
        role = jwt.decode(candidate, options={"verify_signature": False}).get("role")
        if role in {"anon", "service_role"}:
            keys[role] = candidate
    if set(keys) != {"anon", "service_role"}:
        raise ValueError("Fresh local gateway credentials unavailable")
    return keys


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--project-id", required=True)
    parser.add_argument("--api-url", required=True)
    parser.add_argument("--allow-fresh-fixtures", action="store_true")
    args = parser.parse_args()
    if not args.allow_fresh_fixtures:
        raise ValueError("Explicit fresh fixture approval is required")
    keys = local_credentials(args.project_id, args.api_url)
    port = urlsplit(args.api_url).port
    env = dict(
        os.environ,
        P0_SUPABASE_TEST_URL=args.api_url,
        P0_SUPABASE_EXPECTED_URL=args.api_url,
        P0_ALLOW_FIXTURE_WRITES="CREATE_DISPOSABLE_FIXTURES",
        P0_SUPABASE_TEST_ANON_KEY=keys["anon"],
        P0_SUPABASE_TEST_SERVICE_KEY=keys["service_role"],
        P0_FRESH_MIGRATION_TEST="ALLOW_FRESH_MIGRATION_FIXTURES",
        P0_FRESH_MIGRATION_PROJECT_ID=args.project_id,
        P0_FRESH_MIGRATION_API_PORT=str(port),
        FINAL_GATE_LOCAL_TEST="allow-disposable-fixtures",
        PR_AUTH_E2E_LOCAL_TEST="ALLOW_DISPOSABLE_LOCAL",
    )
    result = subprocess.run(
        [sys.executable, "-m", "pytest", "tests/integration", "-q", "-rs", "--tb=short"],
        cwd=ROOT / "backend",
        env=env,
    )
    return result.returncode


if __name__ == "__main__":
    raise SystemExit(main())
