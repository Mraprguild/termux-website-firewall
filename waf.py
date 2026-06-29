#!/usr/bin/env python3
"""
Mraprguild Termux Website Firewall
Defensive WAF reverse proxy for websites/apps you own.

Run:
  python waf.py --config config.yml
"""

from __future__ import annotations

import argparse
import collections
import datetime as dt
import ipaddress
import logging
import os
import re
import sys
import time
from typing import Any, Dict, Iterable, List, Tuple
from urllib.parse import urljoin

import requests
import yaml
from colorama import Fore, Style, init as colorama_init
from flask import Flask, Response, jsonify, request

colorama_init(autoreset=True)

APP_NAME = "Mraprguild Termux Website Firewall"
LOG_DIR = "logs"
BLOCK_LOG = os.path.join(LOG_DIR, "blocked.log")

app = Flask(__name__)
CONFIG: Dict[str, Any] = {}
RATE_BUCKETS: Dict[str, collections.deque] = collections.defaultdict(collections.deque)

DEFAULT_RULES = {
    "sql_injection": [
        r"(?i)\bunion\b.{0,80}\bselect\b",
        r"(?i)\bselect\b.{0,80}\bfrom\b",
        r"(?i)\binformation_schema\b",
        r"(?i)\bor\s+1\s*=\s*1\b",
        r"(?i)\band\s+1\s*=\s*1\b",
        r"(?i)\bdrop\s+table\b",
        r"(?i)\binsert\s+into\b",
        r"(?i)\bdelete\s+from\b",
        r"(?i)\bsleep\s*\(",
        r"(?i)\bbenchmark\s*\(",
        r"(?i)'\s*or\s*'",
        r"(?i)\"\s*or\s*\"",
    ],
    "xss": [
        r"(?i)<\s*script",
        r"(?i)javascript\s*:",
        r"(?i)onerror\s*=",
        r"(?i)onload\s*=",
        r"(?i)document\.cookie",
        r"(?i)<\s*iframe",
        r"(?i)<\s*svg",
    ],
    "path_traversal": [
        r"(?i)\.\./",
        r"(?i)\.\.\\",
        r"(?i)/etc/passwd",
        r"(?i)/proc/self/environ",
        r"(?i)php://",
        r"(?i)data:text/html",
        r"(?i)file://",
    ],
    "command_injection": [
        r"(?i);\s*(cat|id|whoami|uname|wget|curl|bash|sh)\b",
        r"(?i)&&\s*(cat|id|whoami|uname|wget|curl|bash|sh)\b",
        r"(?i)\|\s*(cat|id|whoami|uname|wget|curl|bash|sh)\b",
        r"(?i)`[^`]+`",
        r"(?i)\$\([^)]*\)",
    ],
}


def now_iso() -> str:
    return dt.datetime.now(dt.timezone.utc).astimezone().isoformat(timespec="seconds")


def load_config(path: str) -> Dict[str, Any]:
    if not os.path.exists(path):
        print(Fore.RED + f"Config not found: {path}")
        sys.exit(1)
    with open(path, "r", encoding="utf-8") as f:
        cfg = yaml.safe_load(f) or {}
    cfg.setdefault("upstream", "http://127.0.0.1:8000")
    cfg.setdefault("listen_host", "0.0.0.0")
    cfg.setdefault("listen_port", 8080)
    cfg.setdefault("max_body_bytes", 2 * 1024 * 1024)
    cfg.setdefault("rate_limit_requests", 80)
    cfg.setdefault("rate_limit_seconds", 60)
    cfg.setdefault("proxy_timeout_seconds", 20)
    cfg.setdefault("modules", {})
    cfg.setdefault("blocked_paths", [])
    cfg.setdefault("custom_block_regex", [])
    return cfg


def read_lines(path: str) -> List[str]:
    if not os.path.exists(path):
        return []
    out = []
    with open(path, "r", encoding="utf-8", errors="ignore") as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith("#"):
                out.append(line)
    return out


def client_ip() -> str:
    # Only trust X-Forwarded-For if you placed this firewall behind a trusted proxy.
    forwarded = request.headers.get("X-Forwarded-For", "").split(",")[0].strip()
    return forwarded or request.remote_addr or "unknown"


def ip_in_list(ip: str, values: Iterable[str]) -> bool:
    if ip == "unknown":
        return False
    try:
        ip_obj = ipaddress.ip_address(ip)
    except ValueError:
        return False
    for item in values:
        try:
            if "/" in item:
                if ip_obj in ipaddress.ip_network(item, strict=False):
                    return True
            elif ip_obj == ipaddress.ip_address(item):
                return True
        except ValueError:
            continue
    return False


def request_text_for_rules() -> str:
    parts = [
        request.path or "",
        request.query_string.decode("utf-8", "ignore"),
        request.headers.get("User-Agent", ""),
        request.headers.get("Referer", ""),
        request.headers.get("Content-Type", ""),
    ]
    body = request.get_data(cache=True, as_text=True) if request.content_length and request.content_length < 120_000 else ""
    if body:
        parts.append(body)
    return "\n".join(parts)


def module_enabled(name: str) -> bool:
    return bool(CONFIG.get("modules", {}).get(name, True))


def check_rate_limit(ip: str) -> Tuple[bool, str]:
    if not module_enabled("rate_limit"):
        return True, ""
    limit = int(CONFIG.get("rate_limit_requests", 80))
    window = int(CONFIG.get("rate_limit_seconds", 60))
    q = RATE_BUCKETS[ip]
    current = time.time()

    while q and q[0] < current - window:
        q.popleft()

    if len(q) >= limit:
        return False, f"Rate limit exceeded: {limit}/{window}s"

    q.append(current)
    return True, ""


def check_request() -> Tuple[bool, str, int]:
    ip = client_ip()
    allowed = read_lines("rules/allowed_ips.txt")
    blocked = read_lines("rules/blocked_ips.txt")

    if ip_in_list(ip, allowed):
        return True, "", 200

    if ip_in_list(ip, blocked):
        return False, "Blocked IP", 403

    content_length = request.content_length or 0
    max_body = int(CONFIG.get("max_body_bytes", 2 * 1024 * 1024))
    if content_length > max_body:
        return False, f"Body too large: {content_length} > {max_body}", 413

    ok, reason = check_rate_limit(ip)
    if not ok:
        return False, reason, 429

    if module_enabled("block_sensitive_paths"):
        low_path = (request.path or "").lower()
        for p in CONFIG.get("blocked_paths", []):
            if low_path.startswith(str(p).lower()):
                return False, f"Sensitive path blocked: {p}", 403

    if module_enabled("bad_bots"):
        ua = request.headers.get("User-Agent", "")
        for bad in read_lines("rules/bad_bots.txt"):
            if bad.lower() in ua.lower():
                return False, f"Bad bot User-Agent: {bad}", 403

    text = request_text_for_rules()

    checks = [
        ("sql_injection", DEFAULT_RULES["sql_injection"]),
        ("xss", DEFAULT_RULES["xss"]),
        ("path_traversal", DEFAULT_RULES["path_traversal"]),
        ("command_injection", DEFAULT_RULES["command_injection"]),
    ]

    for module, patterns in checks:
        if not module_enabled(module):
            continue
        for pattern in patterns:
            if re.search(pattern, text):
                return False, f"{module} rule matched: {pattern}", 403

    for pattern in CONFIG.get("custom_block_regex", []):
        try:
            if re.search(pattern, text):
                return False, f"Custom rule matched: {pattern}", 403
        except re.error as exc:
            print(Fore.YELLOW + f"Invalid custom regex skipped: {pattern} ({exc})")

    return True, "", 200


def log_block(reason: str, status: int) -> None:
    os.makedirs(LOG_DIR, exist_ok=True)
    line = {
        "time": now_iso(),
        "ip": client_ip(),
        "method": request.method,
        "path": request.full_path,
        "status": status,
        "reason": reason,
        "user_agent": request.headers.get("User-Agent", ""),
    }
    with open(BLOCK_LOG, "a", encoding="utf-8") as f:
        f.write(json_line(line) + "\n")
    print(Fore.RED + f"[BLOCK] {line['ip']} {request.method} {request.full_path} -> {status} {reason}")


def json_line(obj: Dict[str, Any]) -> str:
    import json
    return json.dumps(obj, ensure_ascii=False, separators=(",", ":"))


@app.before_request
def firewall_gate():
    ok, reason, status = check_request()
    if not ok:
        log_block(reason, status)
        return jsonify({
            "blocked": True,
            "status": status,
            "firewall": APP_NAME,
            "reason": reason,
        }), status
    return None


@app.route("/", defaults={"path": ""}, methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS", "HEAD"])
@app.route("/<path:path>", methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS", "HEAD"])
def proxy(path: str):
    upstream = str(CONFIG.get("upstream", "http://127.0.0.1:8000")).rstrip("/") + "/"
    target_url = urljoin(upstream, path)

    excluded_req_headers = {"host", "content-length", "transfer-encoding", "connection", "accept-encoding"}
    headers = {k: v for k, v in request.headers.items() if k.lower() not in excluded_req_headers}
    headers["X-Forwarded-For"] = client_ip()
    headers["X-Forwarded-Proto"] = request.scheme
    headers["X-Mraprguild-WAF"] = "enabled"

    try:
        upstream_response = requests.request(
            method=request.method,
            url=target_url,
            params=request.args,
            data=request.get_data(),
            headers=headers,
            cookies=request.cookies,
            allow_redirects=False,
            timeout=int(CONFIG.get("proxy_timeout_seconds", 20)),
            stream=True,
        )
    except requests.RequestException as exc:
        print(Fore.YELLOW + f"[UPSTREAM ERROR] {exc}")
        return jsonify({
            "error": "Upstream connection failed",
            "details": str(exc),
            "upstream": upstream,
        }), 502

    excluded_resp_headers = {"content-encoding", "content-length", "transfer-encoding", "connection"}
    response_headers = [(k, v) for k, v in upstream_response.headers.items() if k.lower() not in excluded_resp_headers]
    response_headers.append(("X-Protected-By", APP_NAME))

    return Response(
        upstream_response.content,
        status=upstream_response.status_code,
        headers=response_headers,
    )


@app.route("/__waf_status", methods=["GET"])
def waf_status():
    return jsonify({
        "firewall": APP_NAME,
        "status": "running",
        "time": now_iso(),
        "upstream": CONFIG.get("upstream"),
        "rate_limit_requests": CONFIG.get("rate_limit_requests"),
        "rate_limit_seconds": CONFIG.get("rate_limit_seconds"),
    })


def banner() -> None:
    print(Fore.CYAN + "================================================")
    print(Fore.CYAN + f" {APP_NAME}")
    print(Fore.CYAN + "================================================")
    print(Fore.GREEN + f" Upstream: {CONFIG.get('upstream')}")
    print(Fore.GREEN + f" Listen:   http://{CONFIG.get('listen_host')}:{CONFIG.get('listen_port')}")
    print(Fore.GREEN + " Status:   /__waf_status")
    print(Fore.CYAN + "================================================" + Style.RESET_ALL)


def main() -> None:
    parser = argparse.ArgumentParser(description=APP_NAME)
    parser.add_argument("--config", default="config.yml", help="Path to config.yml")
    args = parser.parse_args()

    global CONFIG
    CONFIG = load_config(args.config)

    os.makedirs(LOG_DIR, exist_ok=True)
    os.makedirs("rules", exist_ok=True)
    for p in ["rules/blocked_ips.txt", "rules/allowed_ips.txt", "rules/bad_bots.txt"]:
        if not os.path.exists(p):
            open(p, "a", encoding="utf-8").close()

    logging.getLogger("werkzeug").setLevel(logging.WARNING)
    banner()

    app.run(
        host=str(CONFIG.get("listen_host", "0.0.0.0")),
        port=int(CONFIG.get("listen_port", 8080)),
        debug=False,
        threaded=True,
    )


if __name__ == "__main__":
    main()
