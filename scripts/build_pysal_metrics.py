#!/usr/bin/env python3
from __future__ import annotations

import json
import os
import random
import sys
import time
from dataclasses import dataclass, asdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import requests

PYPISTATS_BASE = "https://pypistats.org/api/packages"
GITHUB_API_BASE = "https://api.github.com"
ANACONDA_API_BASE = "https://api.anaconda.org/package"
DEFAULT_OUTPUT_DIR = Path("data")
REQUEST_TIMEOUT = 30
GITHUB_TOKEN = os.environ.get("GITHUB_TOKEN")

MODULES: List[Dict[str, str]] = [
    {"module": "access", "pypi": "access", "owner": "pysal", "repo": "access", "conda_channel": "conda-forge", "conda_package": "access"},
    {"module": "esda", "pypi": "esda", "owner": "pysal", "repo": "esda", "conda_channel": "conda-forge", "conda_package": "esda"},
    {"module": "giddy", "pypi": "giddy", "owner": "pysal", "repo": "giddy", "conda_channel": "conda-forge", "conda_package": "giddy"},
    {"module": "inequality", "pypi": "inequality", "owner": "pysal", "repo": "inequality", "conda_channel": "conda-forge", "conda_package": "inequality"},
    {"module": "libpysal", "pypi": "libpysal", "owner": "pysal", "repo": "libpysal", "conda_channel": "conda-forge", "conda_package": "libpysal"},
    {"module": "mapclassify", "pypi": "mapclassify", "owner": "pysal", "repo": "mapclassify", "conda_channel": "conda-forge", "conda_package": "mapclassify"},
    {"module": "mgwr", "pypi": "mgwr", "owner": "pysal", "repo": "mgwr", "conda_channel": "conda-forge", "conda_package": "mgwr"},
    {"module": "pointpats", "pypi": "pointpats", "owner": "pysal", "repo": "pointpats", "conda_channel": "conda-forge", "conda_package": "pointpats"},
    {"module": "pysal", "pypi": "pysal", "owner": "pysal", "repo": "pysal", "conda_channel": "conda-forge", "conda_package": "pysal"},
    {"module": "segregation", "pypi": "segregation", "owner": "pysal", "repo": "segregation", "conda_channel": "conda-forge", "conda_package": "segregation"},
    {"module": "splot", "pypi": "splot", "owner": "pysal", "repo": "splot", "conda_channel": "conda-forge", "conda_package": "splot"},
    {"module": "spopt", "pypi": "spopt", "owner": "pysal", "repo": "spopt", "conda_channel": "conda-forge", "conda_package": "spopt"},
    {"module": "spreg", "pypi": "spreg", "owner": "pysal", "repo": "spreg", "conda_channel": "conda-forge", "conda_package": "spreg"},
    {"module": "spaghetti", "pypi": "spaghetti", "owner": "pysal", "repo": "spaghetti", "conda_channel": "conda-forge", "conda_package": "spaghetti"},
    {"module": "spglm", "pypi": "spglm", "owner": "pysal", "repo": "spglm", "conda_channel": "conda-forge", "conda_package": "spglm"},
]

MODULE_COLORS = {
    "access": "#1f77b4",
    "esda": "#aec7e8",
    "giddy": "#ff7f0e",
    "inequality": "#ffbb78",
    "libpysal": "#2ca02c",
    "mapclassify": "#98df8a",
    "mgwr": "#d62728",
    "pointpats": "#ff9896",
    "pysal": "#9467bd",
    "segregation": "#c5b0d5",
    "splot": "#8c564b",
    "spopt": "#c49c94",
    "spreg": "#e377c2",
    "spaghetti": "#f7b6d2",
    "spglm": "#7f7f7f",
}

@dataclass
class ModuleMetrics:
    module: str
    pypi: str
    owner: str
    repo: str
    conda_channel: str
    conda_package: str
    pypi_last_week: int
    pypi_last_month: int
    conda_total_downloads: int
    stars: int
    forks: int
    age_years: float
    contributors: int
    color: str
    visible: bool
    repo_url: str
    pypi_url: str
    conda_url: str

def build_session() -> requests.Session:
    session = requests.Session()
    session.headers.update({
        "User-Agent": "pysal-quarto-builder/1.0",
        "Accept": "application/json",
    })
    if GITHUB_TOKEN:
        session.headers["Authorization"] = f"Bearer {GITHUB_TOKEN}"
        session.headers["X-GitHub-Api-Version"] = "2022-11-28"
    return session

def request_json_with_retry(
    session: requests.Session,
    url: str,
    *,
    headers: Optional[Dict[str, str]] = None,
    params: Optional[Dict[str, Any]] = None,
    max_retries: int = 6,
    base_sleep: float = 2.0,
    retry_on: Tuple[int, ...] = (429, 500, 502, 503, 504),
) -> Any:
    for attempt in range(max_retries + 1):
        try:
            response = session.get(url, headers=headers, params=params, timeout=REQUEST_TIMEOUT)
            if response.status_code in retry_on:
                if attempt == max_retries:
                    response.raise_for_status()
                retry_after = response.headers.get("Retry-After")
                sleep_seconds = float(retry_after) if retry_after is not None else base_sleep * (2 ** attempt) + random.uniform(0, 0.5)
                time.sleep(sleep_seconds)
                continue
            response.raise_for_status()
            return response.json()
        except requests.RequestException:
            if attempt == max_retries:
                raise
            sleep_seconds = base_sleep * (2 ** attempt) + random.uniform(0, 0.5)
            time.sleep(sleep_seconds)
    raise RuntimeError(f"Request failed unexpectedly: {url}")

def fetch_pypi_recent_downloads(session: requests.Session, package: str) -> Tuple[int, int]:
    url = f"{PYPISTATS_BASE}/{package}/recent"
    payload = request_json_with_retry(session, url, headers={"Accept": "application/json"}, max_retries=7, base_sleep=3.0)
    recent = payload.get("data", {})
    time.sleep(2.2)
    return int(recent.get("last_week", 0) or 0), int(recent.get("last_month", 0) or 0)

def fetch_github_repo_metadata(session: requests.Session, owner: str, repo: str) -> Dict[str, Any]:
    url = f"{GITHUB_API_BASE}/repos/{owner}/{repo}"
    return request_json_with_retry(session, url, headers={"Accept": "application/vnd.github+json"}, max_retries=4, base_sleep=1.5, retry_on=(403, 429, 500, 502, 503, 504))

def count_github_contributors(session: requests.Session, owner: str, repo: str) -> int:
    url = f"{GITHUB_API_BASE}/repos/{owner}/{repo}/contributors"
    contributors = 0
    page = 1
    while True:
      batch = request_json_with_retry(
          session,
          url,
          headers={"Accept": "application/vnd.github+json"},
          params={"per_page": 100, "anon": 1, "page": page},
          max_retries=4,
          base_sleep=1.5,
          retry_on=(403, 429, 500, 502, 503, 504),
      )
      if not isinstance(batch, list) or not batch:
          break
      contributors += len(batch)
      if len(batch) < 100:
          break
      page += 1
      time.sleep(0.3)
    return contributors

def compute_age_years(created_at_iso: str) -> float:
    created = datetime.fromisoformat(created_at_iso.replace("Z", "+00:00"))
    now = datetime.now(timezone.utc)
    return round(((now - created).total_seconds() / 86400.0) / 365.25, 1)

def parse_conda_total_downloads(payload: Dict[str, Any]) -> int:
    for key in ("ndownloads", "download_count", "total_downloads", "downloads"):
        value = payload.get(key)
        if isinstance(value, (int, float)):
            return int(value)

    files = payload.get("files", [])
    if isinstance(files, list) and files:
        total = 0
        seen_any = False
        for file_obj in files:
            if not isinstance(file_obj, dict):
                continue
            for key in ("ndownloads", "download_count", "downloads"):
                value = file_obj.get(key)
                if isinstance(value, (int, float)):
                    total += int(value)
                    seen_any = True
                    break
        if seen_any:
            return total
    raise ValueError("Could not parse conda total downloads.")

def fetch_conda_total_downloads(session: requests.Session, channel: str, package: str) -> int:
    url = f"{ANACONDA_API_BASE}/{channel}/{package}"
    payload = request_json_with_retry(session, url, headers={"Accept": "application/json"}, max_retries=5, base_sleep=2.0, retry_on=(403, 429, 500, 502, 503, 504))
    time.sleep(0.8)
    return parse_conda_total_downloads(payload)

def fetch_one_module(session: requests.Session, config: Dict[str, str]) -> ModuleMetrics:
    pypi_last_week, pypi_last_month = fetch_pypi_recent_downloads(session, config["pypi"])
    conda_total_downloads = fetch_conda_total_downloads(session, config["conda_channel"], config["conda_package"])
    repo_meta = fetch_github_repo_metadata(session, config["owner"], config["repo"])
    contributors = count_github_contributors(session, config["owner"], config["repo"])

    stars = int(repo_meta.get("stargazers_count", 0) or 0)
    forks = int(repo_meta.get("forks_count", 0) or 0)
    created_at = repo_meta.get("created_at")
    age_years = compute_age_years(created_at) if created_at else 0.0

    return ModuleMetrics(
        module=config["module"],
        pypi=config["pypi"],
        owner=config["owner"],
        repo=config["repo"],
        conda_channel=config["conda_channel"],
        conda_package=config["conda_package"],
        pypi_last_week=pypi_last_week,
        pypi_last_month=pypi_last_month,
        conda_total_downloads=conda_total_downloads,
        stars=stars,
        forks=forks,
        age_years=age_years,
        contributors=contributors,
        color=MODULE_COLORS[config["module"]],
        visible=(config["module"] == "pysal"),
        repo_url=f"https://github.com/{config['owner']}/{config['repo']}",
        pypi_url=f"https://pypi.org/project/{config['pypi']}/",
        conda_url=f"https://anaconda.org/{config['conda_channel']}/{config['conda_package']}",
    )

def build_summary(rows: List[ModuleMetrics]) -> Dict[str, Any]:
    top_pypi_month = max(rows, key=lambda x: x.pypi_last_month)
    top_conda = max(rows, key=lambda x: x.conda_total_downloads)
    most_starred = max(rows, key=lambda x: x.stars)
    oldest_module = max(rows, key=lambda x: x.age_years)
    return {
        "total_modules": len(rows),
        "top_pypi_month": top_pypi_month.module,
        "top_pypi_month_value": top_pypi_month.pypi_last_month,
        "top_conda_total": top_conda.module,
        "top_conda_total_value": top_conda.conda_total_downloads,
        "most_starred": most_starred.module,
        "most_starred_value": most_starred.stars,
        "oldest_module": oldest_module.module,
        "oldest_module_value": oldest_module.age_years,
    }

def build_payload(rows: List[ModuleMetrics]) -> Dict[str, Any]:
    total_pypi_last_month = sum(r.pypi_last_month for r in rows)
    total_conda_total = sum(r.conda_total_downloads for r in rows)

    sorted_pypi_month = sorted(rows, key=lambda x: x.pypi_last_month, reverse=True)
    sorted_conda_total = sorted(rows, key=lambda x: x.conda_total_downloads, reverse=True)

    pypi_ranks = {row.module: i + 1 for i, row in enumerate(sorted_pypi_month)}
    conda_ranks = {row.module: i + 1 for i, row in enumerate(sorted_conda_total)}

    max_stars = max((r.stars for r in rows), default=1)
    max_forks = max((r.forks for r in rows), default=1)
    max_age = max((r.age_years for r in rows), default=1)
    max_contributors = max((r.contributors for r in rows), default=1)

    enriched_rows = []
    for row in rows:
        normalized_values = [
            (row.pypi_last_month / total_pypi_last_month) if total_pypi_last_month else 0.0,
            (row.conda_total_downloads / total_conda_total) if total_conda_total else 0.0,
            (row.stars / max_stars) if max_stars else 0.0,
            (row.forks / max_forks) if max_forks else 0.0,
            (row.age_years / max_age) if max_age else 0.0,
            (row.contributors / max_contributors) if max_contributors else 0.0,
        ]
        item = asdict(row)
        item["values"] = normalized_values
        item["pypi_rank"] = pypi_ranks[row.module]
        item["conda_rank"] = conda_ranks[row.module]
        item["size"] = sum(normalized_values)
        enriched_rows.append(item)

    return {
        "generated_at_utc": datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC"),
        "feature_labels": [
            "PIP Install\n(Last month, %)",
            "Conda Install\n(Total, %)",
            "GitHub\nStars",
            "GitHub\nForks",
            "Age\n(Years)",
            "Contributors",
        ],
        "data": enriched_rows,
        "summary": build_summary(rows),
        "totals": {
            "pypi_last_month_total": total_pypi_last_month,
            "conda_total_downloads_total": total_conda_total,
        },
    }

def main() -> int:
    session = build_session()
    rows: List[ModuleMetrics] = []
    errors: List[str] = []

    for config in MODULES:
        try:
            rows.append(fetch_one_module(session, config))
        except Exception as exc:
            errors.append(f"{config['module']}: {exc}")

    if not rows:
        print("No module data fetched successfully.", file=sys.stderr)
        return 1

    rows.sort(key=lambda x: x.module.lower())
    DEFAULT_OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    output_path = DEFAULT_OUTPUT_DIR / "pysal_metrics_latest.json"
    output_path.write_text(json.dumps(build_payload(rows), indent=2), encoding="utf-8")

    print(f"Wrote JSON: {output_path}")

    if errors:
        print("Some modules failed:", file=sys.stderr)
        for err in errors:
            print(f"  - {err}", file=sys.stderr)

    return 0

if __name__ == "__main__":
    raise SystemExit(main())
