"""Per-IP sliding-window limit on the authentication routes (SEC-7).

In memory, so it holds per instance; with several instances behind a load balancer each one
enforces its own window. X-Forwarded-For is only trusted when TRUSTED_PROXY_HOPS says how many
proxies of ours sit in front: the client can forge everything to the left of what they append.
"""

import os
import time
from collections import defaultdict, deque

LIMIT_PER_MINUTE = int(os.getenv("AUTH_RATE_LIMIT_PER_MINUTE", "20"))
TRUSTED_PROXY_HOPS = int(os.getenv("TRUSTED_PROXY_HOPS", "0"))
WINDOW_SECONDS = 60
LIMITED_PATHS = (
    "/api/v1/auth/login", "/api/v1/auth/register", "/api/v1/auth/forgot-password",
    "/api/v1/auth/reset-password", "/api/v1/auth/refresh",
)

_hits: dict[str, deque] = defaultdict(deque)


def resolve_client_ip(request) -> str | None:
    direct = request.client.host if request.client else None
    forwarded = request.headers.get("x-forwarded-for")
    if TRUSTED_PROXY_HOPS > 0 and forwarded:
        chain = [ip.strip() for ip in forwarded.split(",") if ip.strip()]
        if len(chain) >= TRUSTED_PROXY_HOPS:
            return chain[-TRUSTED_PROXY_HOPS]
    return direct


def is_limited(path: str, method: str) -> bool:
    return method == "POST" and path.rstrip("/").startswith(LIMITED_PATHS)


def check(ip: str | None) -> int | None:
    """Registers a hit; returns the seconds to wait when over the limit, else None."""
    key = ip or "desconhecido"
    now = time.monotonic()
    hits = _hits[key]
    while hits and now - hits[0] > WINDOW_SECONDS:
        hits.popleft()
    if len(hits) >= LIMIT_PER_MINUTE:
        return max(1, int(WINDOW_SECONDS - (now - hits[0])) + 1)
    hits.append(now)
    return None


def reset() -> None:
    _hits.clear()
