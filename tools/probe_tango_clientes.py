#!/usr/bin/env python3
"""
Probe the Tango API to discover the process number for customers (GVA14).

Tries a curated list of likely process IDs first, then an optional full scan.
For each process that returns data, prints the field names of the first record
so you can identify which one contains customer data (NOMBRE, CUIT, etc.).

Usage:
    # Use env vars:
    TANGO_TOKEN=<token> python tools/probe_tango_clientes.py

    # Or pass args:
    python tools/probe_tango_clientes.py --base-url http://server-t:17000 --token <token> --company 25

    # Full scan (slow, tries 1-300):
    TANGO_TOKEN=<token> python tools/probe_tango_clientes.py --full-scan
"""

import argparse
import json
import os
import sys
import time
import urllib.error
import urllib.parse
import urllib.request

BASE_URL_DEFAULT = "http://server-t:17000"
COMPANY_DEFAULT = "25"
PAGE_SIZE = 1  # Only need 1 record to inspect field names

# Likely process IDs for GVA14 (clientes) based on Tango Gestión conventions.
# 87 = artículos (confirmed). Customers typically nearby.
CURATED_CANDIDATES = [
    88, 89, 90, 91, 92, 93, 94, 95, 96, 97, 98, 99, 100,
    101, 102, 103, 104, 105, 110, 115, 120, 130, 140, 150,
    60, 61, 62, 63, 64, 65, 70, 75, 80, 85, 86,
]

# Fields that strongly suggest this is the customer (GVA14) process
CUSTOMER_FIELD_HINTS = {"CUIT", "RAZON_SOCIAL", "NOMBRE", "COD_GVA14", "ID_GVA14", "CONDICION_IVA"}


def build_url(base_url: str, process: int, page_size: int = PAGE_SIZE, page_index: int = 0) -> str:
    params = urllib.parse.urlencode({
        "process": process,
        "pageSize": page_size,
        "pageIndex": page_index,
    })
    return f"{base_url.rstrip('/')}/Api/Get?{params}"


def fetch_process(base_url: str, token: str, company: str, process: int) -> dict | None:
    url = build_url(base_url, process)
    req = urllib.request.Request(url)
    req.add_header("ApiAuthorization", token)
    req.add_header("Company", company)
    try:
        with urllib.request.urlopen(req, timeout=5) as resp:
            raw = resp.read().decode("utf-8", errors="replace")
            return json.loads(raw)
    except urllib.error.HTTPError as e:
        if e.code in (400, 404, 500):
            return None  # Process does not exist or no data
        print(f"  HTTP {e.code} for process {process}", file=sys.stderr)
        return None
    except (urllib.error.URLError, json.JSONDecodeError, TimeoutError):
        return None


def extract_fields(response: dict) -> list[str]:
    """Extract field names from the first record in a Tango API response."""
    # Tango responses vary: sometimes {"data": [...]} or {"items": [...]} or bare list
    for key in ("data", "items", "Data", "Items", "result", "Result"):
        if key in response and isinstance(response[key], list) and response[key]:
            return list(response[key][0].keys())
    if isinstance(response, list) and response:
        return list(response[0].keys())
    # Try any list value in the response
    for v in response.values():
        if isinstance(v, list) and v and isinstance(v[0], dict):
            return list(v[0].keys())
    return []


def score_customer_match(fields: set[str]) -> int:
    return len(fields & CUSTOMER_FIELD_HINTS)


def probe_processes(
    base_url: str,
    token: str,
    company: str,
    candidates: list[int],
    delay: float = 0.2,
) -> None:
    print(f"\nProbing {len(candidates)} process IDs against {base_url} (Company={company})\n")
    print(f"{'Process':>8}  {'Records?':>8}  {'Customer match':>14}  Fields")
    print("-" * 90)

    best_match: tuple[int, list[str]] | None = None
    best_score = 0

    for process in candidates:
        time.sleep(delay)
        response = fetch_process(base_url, token, company, process)
        if response is None:
            continue

        fields = extract_fields(response)
        if not fields:
            continue

        fset = {f.upper() for f in fields}
        score = score_customer_match(fset)
        hint = "*** LIKELY CUSTOMER ***" if score >= 2 else ("possible" if score == 1 else "")
        print(f"{process:>8}  {'yes':>8}  {score:>14}  {', '.join(fields[:8])}{'...' if len(fields) > 8 else ''}  {hint}")

        if score > best_score:
            best_score = score
            best_match = (process, fields)

    print("-" * 90)
    if best_match:
        proc, fields = best_match
        print(f"\nBest candidate: process={proc} (score={best_score})")
        print(f"All fields: {fields}\n")
        print(f"Suggested env var: TANGO_PROCESS_CLIENTES={proc}")
    else:
        print("\nNo customer process found in this range. Try --full-scan.")


def main() -> None:
    parser = argparse.ArgumentParser(description="Probe Tango API for customer process (GVA14)")
    parser.add_argument("--base-url", default=os.environ.get("TANGO_BASE_URL", BASE_URL_DEFAULT))
    parser.add_argument("--token", default=os.environ.get("TANGO_TOKEN", ""))
    parser.add_argument("--company", default=os.environ.get("TANGO_COMPANY", COMPANY_DEFAULT))
    parser.add_argument("--full-scan", action="store_true", help="Scan all process IDs 1-300 (slow)")
    parser.add_argument("--range", help="Custom range, e.g. '50-150'")
    parser.add_argument("--delay", type=float, default=0.15, help="Delay between requests in seconds")
    args = parser.parse_args()

    if not args.token:
        print("ERROR: TANGO_TOKEN env var or --token required", file=sys.stderr)
        sys.exit(1)

    if args.full_scan:
        candidates = list(range(1, 301))
    elif args.range:
        start, end = args.range.split("-")
        candidates = list(range(int(start), int(end) + 1))
    else:
        candidates = CURATED_CANDIDATES

    probe_processes(args.base_url, args.token, args.company, candidates, delay=args.delay)


if __name__ == "__main__":
    main()
