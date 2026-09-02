from __future__ import annotations

import argparse
import os
import time
from urllib.error import HTTPError, URLError
from urllib.request import urlopen


def qdrant_is_ready(url: str, timeout_seconds: float) -> bool:
    endpoint = f"{url.rstrip('/')}/collections"

    try:
        with urlopen(endpoint, timeout=timeout_seconds) as response:
            return 200 <= response.status < 300
    except (HTTPError, URLError, OSError):
        return False


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Wait until a Qdrant HTTP endpoint is available."
    )
    parser.add_argument(
        "--url",
        default=os.getenv("QDRANT_URL", "http://localhost:6333"),
    )
    parser.add_argument(
        "--timeout-seconds",
        type=float,
        default=60.0,
    )
    parser.add_argument(
        "--interval-seconds",
        type=float,
        default=1.0,
    )
    args = parser.parse_args()

    if args.timeout_seconds <= 0:
        parser.error("--timeout-seconds must be positive")
    if args.interval_seconds <= 0:
        parser.error("--interval-seconds must be positive")

    deadline = time.monotonic() + args.timeout_seconds

    while time.monotonic() < deadline:
        if qdrant_is_ready(args.url, args.interval_seconds):
            print(f"Qdrant is ready at {args.url}")
            return

        time.sleep(args.interval_seconds)

    parser.exit(
        1,
        f"Qdrant did not become ready within {args.timeout_seconds:.0f} seconds: "
        f"{args.url}\n",
    )


if __name__ == "__main__":
    main()