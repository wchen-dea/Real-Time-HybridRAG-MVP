#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import os
import re
import urllib.error
import urllib.request
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
TEMPLATES_DIR = ROOT / "resources" / "connectors" / "templates"
DEFAULT_OUTPUT_DIR = ROOT / "resources" / "connectors" / "generated"
DEFAULT_CONNECT_URL = "http://localhost:8083"


def load_dotenv(path: Path) -> dict[str, str]:
    values: dict[str, str] = {}
    if not path.exists():
        return values
    for line in path.read_text(encoding="utf-8").splitlines():
        stripped = line.strip()
        if not stripped or stripped.startswith("#") or "=" not in stripped:
            continue
        key, value = stripped.split("=", 1)
        values[key.strip()] = value.strip()
    return values


def resolve_env() -> dict[str, str]:
    env = load_dotenv(ROOT / ".env.example")
    env.update(load_dotenv(ROOT / ".env"))
    env.update(os.environ)
    return {k: str(v) for k, v in env.items()}


def ensure_defaults(env: dict[str, str]) -> dict[str, str]:
    resolved = dict(env)
    host = resolved.get("DATABRICKS_HOST", "")
    if host.startswith("https://"):
        host = host[len("https://") :]
    elif host.startswith("http://"):
        host = host[len("http://") :]
    if "/" in host:
        host = host.split("/", 1)[0]
    resolved["DATABRICKS_CONNECT_HOST"] = resolved.get("DATABRICKS_CONNECT_HOST", host)
    return resolved


def render_template(content: str, env: dict[str, str]) -> str:
    pattern = re.compile(r"\$\{([A-Z0-9_]+)\}")

    def _replace(match: re.Match[str]) -> str:
        key = match.group(1)
        return env.get(key, "")

    return pattern.sub(_replace, content)


def render_templates(output_dir: Path) -> list[Path]:
    env = ensure_defaults(resolve_env())
    output_dir.mkdir(parents=True, exist_ok=True)
    generated: list[Path] = []

    for template_path in sorted(TEMPLATES_DIR.glob("*.tmpl.json")):
        rendered = render_template(template_path.read_text(encoding="utf-8"), env)
        parsed = json.loads(rendered)
        out_name = template_path.name.replace(".tmpl", "")
        out_path = output_dir / out_name
        out_path.write_text(json.dumps(parsed, indent=2) + "\n", encoding="utf-8")
        generated.append(out_path)
        print(f"rendered {out_path.relative_to(ROOT)}")
    return generated


def http_json(
    url: str, method: str, payload: dict[str, Any] | None = None
) -> dict[str, Any]:
    data = None
    headers = {"Content-Type": "application/json"}
    if payload is not None:
        data = json.dumps(payload).encode("utf-8")
    request = urllib.request.Request(url=url, data=data, method=method, headers=headers)
    with urllib.request.urlopen(request, timeout=20) as response:
        body = response.read().decode("utf-8")
        return json.loads(body) if body else {}


def register_connector(connect_url: str, connector_path: Path) -> None:
    payload = json.loads(connector_path.read_text(encoding="utf-8"))
    name = payload["name"]
    config = payload["config"]
    base = connect_url.rstrip("/")
    connector_url = f"{base}/connectors/{name}"
    try:
        http_json(connector_url, "GET")
        http_json(f"{connector_url}/config", "PUT", config)
        print(f"updated {name}")
    except urllib.error.HTTPError as exc:
        if exc.code != 404:
            raise
        http_json(f"{base}/connectors", "POST", payload)
        print(f"created {name}")


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Render Kafka Connect connector configs and optionally register them."
    )
    parser.add_argument(
        "--output-dir",
        default=os.getenv("CONNECTORS_OUTPUT_DIR")
        or str(DEFAULT_OUTPUT_DIR.relative_to(ROOT)),
        help="Relative output directory for rendered connector configs.",
    )
    parser.add_argument(
        "--register",
        action="store_true",
        help="Register connectors against Kafka Connect REST API after rendering.",
    )
    parser.add_argument(
        "--connect-url",
        default=os.getenv("KAFKA_CONNECT_URL", DEFAULT_CONNECT_URL),
        help="Kafka Connect base URL.",
    )
    args = parser.parse_args()

    output_dir = (ROOT / args.output_dir).resolve()
    generated = render_templates(output_dir)

    if args.register:
        for connector_file in generated:
            register_connector(args.connect_url, connector_file)


if __name__ == "__main__":
    main()
