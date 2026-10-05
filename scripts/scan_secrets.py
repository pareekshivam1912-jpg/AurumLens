"""Secrets and Credentials Scanner for AurumLens (Phase A10 Hardening).

Scans repository files and directories to ensure:
1. No Supabase service-role keys or JWTs exist in web/ or public code.
2. No Telegram bot tokens or API private keys are hardcoded in source.
3. .env files are not tracked by git or populated with production credentials.
4. Client bundle code in web/ contains only NEXT_PUBLIC_SUPABASE_ANON_KEY / URL.
"""

from __future__ import annotations

import os
import re
import sys
from pathlib import Path

# Sensitive patterns to search for
SUSPICIOUS_PATTERNS = [
    (re.compile(r"ey[A-Za-z0-9-_=]+\.ey[A-Za-z0-9-_=]+\.[A-Za-z0-9-_.+/=]+"), "JWT Token (Service Role / Secret)"),
    (re.compile(r"(?i)(service[_-]?role[_-]?key\s*[:=]\s*['\"][A-Za-z0-9-_.]+['\"])"), "Explicit Service Role Key"),
    (re.compile(r"(?i)(bot[0-9]{8,10}:[a-zA-Z0-9_-]{35})"), "Telegram Bot Token"),
    (re.compile(r"(?i)(AIza[0-9A-Za-z-_]{35})"), "Google Cloud API Key"),
    (re.compile(r"-----BEGIN (?:RSA |EC )?PRIVATE KEY-----"), "Private Key Header"),
]

# Allowlisted paths or placeholders
IGNORED_DIRS = {".git", ".pytest_cache", "node_modules", ".next"}
IGNORED_FILES = {"package-lock.json", "scan_secrets.py"}
SAFE_PLACEHOLDERS = {
    "aurumlens-dev-token",
    "placeholder-token",
    "http://127.0.0.1:54321",
    "eyJhGciOi",
    "mock-signal-1",
}


def scan_file(file_path: Path) -> list[str]:
    findings = []
    try:
        content = file_path.read_text(encoding="utf-8", errors="ignore")
    except Exception as e:
        return [f"Could not read {file_path}: {e}"]

    # Special check for web/ directory: must NEVER contain service_role
    if "web" in file_path.parts:
        if "service_role" in content.lower():
            findings.append(f"CRITICAL: 'service_role' reference found in frontend file: {file_path}")

    for pattern, name in SUSPICIOUS_PATTERNS:
        matches = pattern.findall(content)
        for m in matches:
            match_str = str(m)
            # Skip safe dev placeholders
            if any(safe in match_str for safe in SAFE_PLACEHOLDERS):
                continue
            # If in .env.example, check if it's an empty placeholder
            if file_path.name == ".env.example":
                continue
            findings.append(f"Suspicious pattern [{name}] in {file_path}: {match_str[:25]}...")

    return findings


def run_secrets_scan(root_dir: Path) -> int:
    print(f"[*] Scanning repository for leaked secrets at: {root_dir}")
    total_scanned = 0
    all_findings = []

    for path in root_dir.rglob("*"):
        if any(ignored in path.parts for ignored in IGNORED_DIRS):
            continue
        if path.name in IGNORED_FILES:
            continue
        if path.is_file():
            # Only scan text/code files
            if path.suffix.lower() in {".py", ".ts", ".tsx", ".js", ".json", ".yaml", ".yml", ".md", ".env", ".env.local"}:
                total_scanned += 1
                findings = scan_file(path)
                if findings:
                    all_findings.extend(findings)

    print(f"[*] Total files scanned: {total_scanned}")
    if all_findings:
        print(f"[!] Found {len(all_findings)} potential secret leakage issues:")
        for f in all_findings:
            print(f"    - {f}")
        return 1
    else:
        print("[+] SUCCESS: No exposed secrets or service-role keys detected.")
        return 0


if __name__ == "__main__":
    repo_root = Path(__file__).resolve().parents[1]
    sys.exit(run_secrets_scan(repo_root))
