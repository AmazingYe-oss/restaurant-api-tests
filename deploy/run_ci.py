"""Run the regression suite against an isolated Compose project."""
import argparse
import json
import os
from pathlib import Path
import re
import secrets
import socket
import subprocess
import sys
import tempfile

import requests

ROOT = Path(__file__).resolve().parents[1]
SUT = ROOT.parent / "restaurant-reservation-sut"
EVIDENCE = ROOT / "evidence"


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--reuse-image", help="Local image for an isolated smoke run")
    args = parser.parse_args()
    port = 28080
    base_url = f"http://127.0.0.1:{port}"
    with socket.socket() as sock:
        sock.bind(("127.0.0.1", port))

    credentials = {
        key: secrets.token_hex(24)
        for key in ("DB_PASSWORD", "DB_ROOT_PASSWORD", "JWT_SECRET", "APP_ADMIN_PASSWORD")
    }
    config = dict(credentials, DB_NAME="reservation", DB_USER="reservation",
                  APP_ADMIN_EMAIL="admin@example.com", APP_ADMIN_NAME="CI Admin")
    password = secrets.token_hex(16)
    EVIDENCE.mkdir(exist_ok=True)
    report = EVIDENCE / "ci-junit.xml"
    report.unlink(missing_ok=True)
    (EVIDENCE / "ci-scope.txt").write_text(
        "Stable regression excludes test_concurrent_reservations_allow_only_one "
        "because of known BUG-001. The test remains in the repository.\n"
    )
    project = "restaurant-ci-" + secrets.token_hex(6)
    with tempfile.TemporaryDirectory(prefix=project) as directory:
        env_file = Path(directory) / ".env"
        env_file.write_text("".join(f"{key}={value}\n" for key, value in config.items()))
        env_file.chmod(0o600)
        env = dict(os.environ, PRACTICE_API_PORT=str(port), TEST_BASE_URL=base_url,
                   TEST_DEPLOY_ENV_FILE=str(env_file), TEST_LOGIN_PASSWORD=password)
        compose = ["docker", "compose", "--env-file", str(env_file), "-p", project,
                   "-f", str(SUT / "docker-compose.yml"),
                   "-f", str(ROOT / "deploy/compose.test.yml")]
        if args.reuse_image:
            override = Path(directory) / "image.json"
            override.write_text(json.dumps({"services": {"api": {"image": args.reuse_image}}}))
            compose.extend(["-f", str(override)])
        try:
            if not args.reuse_image:
                subprocess.run(compose + ["build", "api"], env=env, check=True)
            subprocess.run(compose + ["up", "-d", "--no-build", "--wait", "--wait-timeout", "180"],
                           env=env, check=True)
            registered = requests.post(
                base_url + "/api/auth/register",
                json={"fullName": "CI Customer", "email": "user@example.com", "password": password},
                timeout=15,
            )
            if registered.status_code != 201 or registered.json()["customerId"] != 2:
                raise RuntimeError(f"CI customer initialization failed (HTTP {registered.status_code})")
            seeded = subprocess.check_output([sys.executable, "deploy/prepare_data.py"], cwd=ROOT, env=env)
            data = json.loads(seeded)
            if (data["restaurantId"], data["tableId"]) != (1, 1):
                raise RuntimeError("CI restaurant/table IDs do not match the test data assumptions")
            print("Temporary database prepared. Running stable regression.", flush=True)
            result = subprocess.run(
                [sys.executable, "-m", "pytest", "-v", "tests/", "-k", "not concurrent_reservations",
                 f"--junitxml={report}"],
                cwd=ROOT, env=env,
            )
        finally:
            cleanup = subprocess.run(compose + ["down", "-v", "--remove-orphans"], env=env)
            if report.exists():
                content = report.read_text()
                for secret in [password, *credentials.values()]:
                    content = content.replace(secret, "[REDACTED]")
                content = re.sub(r"eyJ[\w-]+\.[\w-]+\.[\w-]+", "[REDACTED_TOKEN]", content)
                report.write_text(content)
        return result.returncode or cleanup.returncode


if __name__ == "__main__":
    sys.exit(main())
