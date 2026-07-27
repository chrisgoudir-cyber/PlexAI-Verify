from __future__ import annotations

import argparse
import json

from plexai_verify.app.application_api import app_api


def main() -> int:
    parser = argparse.ArgumentParser(prog="plexai-verify-cli")
    parser.add_argument("command", choices=["stats", "issues"])
    args = parser.parse_args()

    if args.command == "stats":
        payload = app_api.dashboard()
    else:
        payload = app_api.issues()

    print(json.dumps(payload, ensure_ascii=False, indent=2, default=str))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
