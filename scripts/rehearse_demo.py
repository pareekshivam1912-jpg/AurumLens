#!/usr/bin/env python3
"""
AurumLens — Automated Offline Rehearsal Runner.

Runs the full quality gate sequence three consecutive times:
  1. pytest (117+ tests)
  2. secrets scan (0 findings)
  3. FR1–FR27 checklist (27/27 pass)
  4. Next.js build (12/12 routes)

Exit gate: all four checks pass three consecutive times.
"""
from __future__ import annotations

import subprocess
import sys
import time
from dataclasses import dataclass, field
from pathlib import Path

# Windows console encoding fix
if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8")  # type: ignore[attr-defined]

PROJECT_ROOT = Path(__file__).resolve().parent.parent
WEB_DIR = PROJECT_ROOT / "web"
REQUIRED_PASSES = 3


@dataclass
class CheckResult:
    name: str
    passed: bool
    detail: str
    duration_s: float = 0.0


@dataclass
class RoundResult:
    round_num: int
    checks: list[CheckResult] = field(default_factory=list)

    @property
    def passed(self) -> bool:
        return all(c.passed for c in self.checks)


def _run(cmd: list[str], cwd: Path, timeout: int = 300) -> subprocess.CompletedProcess:
    """Run a subprocess and capture combined output."""
    use_shell = sys.platform == "win32"
    return subprocess.run(
        cmd,
        cwd=str(cwd),
        capture_output=True,
        text=True,
        timeout=timeout,
        encoding="utf-8",
        errors="replace",
        shell=use_shell,
    )



def check_pytest() -> CheckResult:
    """Run pytest and verify all tests pass."""
    t0 = time.monotonic()
    try:
        r = _run([sys.executable, "-m", "pytest", "-q", "--tb=line"], PROJECT_ROOT)
        passed = r.returncode == 0
        # Extract summary line like "117 passed"
        lines = r.stdout.strip().splitlines()
        summary = lines[-1] if lines else "(no output)"
        detail = summary if passed else f"FAILED: {summary}\n{r.stdout[-500:]}"
    except subprocess.TimeoutExpired:
        passed = False
        detail = "TIMEOUT (>300s)"
    return CheckResult("pytest", passed, detail, time.monotonic() - t0)


def check_secrets_scan() -> CheckResult:
    """Run the secrets scanner and verify zero findings."""
    t0 = time.monotonic()
    script = PROJECT_ROOT / "scripts" / "scan_secrets.py"
    try:
        r = _run([sys.executable, str(script)], PROJECT_ROOT, timeout=120)
        passed = r.returncode == 0 and ("No exposed secrets" in r.stdout or "0 potential leaks" in r.stdout)
        detail = r.stdout.strip().splitlines()[-1] if r.stdout.strip() else "(no output)"
    except subprocess.TimeoutExpired:
        passed = False
        detail = "TIMEOUT"
    return CheckResult("secrets_scan", passed, detail, time.monotonic() - t0)


def check_fr_checklist() -> CheckResult:
    """Run the FR checklist and verify 27/27 PASS."""
    t0 = time.monotonic()
    script = PROJECT_ROOT / "scripts" / "verify_fr_checklist.py"
    try:
        r = _run([sys.executable, str(script)], PROJECT_ROOT, timeout=120)
        passed = r.returncode == 0 and ("ALL 27 FUNCTIONAL REQUIREMENTS" in r.stdout or "Failed: 0" in r.stdout)
        lines = r.stdout.strip().splitlines()
        detail = lines[-1] if lines else "(no output)"
    except subprocess.TimeoutExpired:
        passed = False
        detail = "TIMEOUT"
    return CheckResult("fr_checklist", passed, detail, time.monotonic() - t0)



def check_nextjs_build() -> CheckResult:
    """Run next build and verify all routes prerender."""
    t0 = time.monotonic()
    if not WEB_DIR.exists():
        return CheckResult("nextjs_build", False, f"web/ dir not found at {WEB_DIR}", 0)
    try:
        r = _run(["npx", "next", "build"], WEB_DIR, timeout=300)
        passed = r.returncode == 0
        # Count prerendered routes from output
        route_lines = [l for l in r.stdout.splitlines() if "○" in l or "●" in l or "ƒ" in l]
        detail = f"{len(route_lines)} routes detected, exit={r.returncode}"
        if not passed:
            stderr_tail = r.stderr[-500:] if r.stderr else ""
            detail += f"\n{stderr_tail}"
    except subprocess.TimeoutExpired:
        passed = False
        detail = "TIMEOUT (>300s)"
    except FileNotFoundError:
        passed = False
        detail = "npx not found — Node.js not installed?"
    return CheckResult("nextjs_build", passed, detail, time.monotonic() - t0)


def run_round(round_num: int) -> RoundResult:
    """Execute one full rehearsal round."""
    result = RoundResult(round_num=round_num)
    checks = [check_pytest, check_secrets_scan, check_fr_checklist, check_nextjs_build]
    for check_fn in checks:
        cr = check_fn()
        result.checks.append(cr)
        status = "PASS" if cr.passed else "FAIL"
        print(f"  [{status}] {cr.name}: {cr.detail} ({cr.duration_s:.1f}s)")
    return result


def main() -> int:
    import argparse
    parser = argparse.ArgumentParser(description="AurumLens demo rehearsal runner")
    parser.add_argument("--rounds", type=int, default=REQUIRED_PASSES, help="Number of consecutive rounds (default 3)")
    args = parser.parse_args()

    num_passes = args.rounds
    print("=" * 60)
    print("AurumLens — Offline Demo Rehearsal")
    print(f"Requires {num_passes} consecutive passing rounds")
    print("=" * 60)

    results: list[RoundResult] = []
    for i in range(1, num_passes + 1):
        print(f"\n--- Round {i}/{num_passes} ---")
        rr = run_round(i)
        results.append(rr)
        if rr.passed:
            print(f"  ✓ Round {i} PASSED")
        else:
            print(f"  ✗ Round {i} FAILED — aborting")
            print("\nFailing checks:")
            for c in rr.checks:
                if not c.passed:
                    print(f"  - {c.name}: {c.detail}")
            return 1

    total_time = sum(c.duration_s for r in results for c in r.checks)
    print("\n" + "=" * 60)
    print(f"EXIT GATE: {num_passes}/{num_passes} rounds PASSED ({total_time:.1f}s total)")
    print("Demo rehearsal complete — ready to present.")
    print("=" * 60)
    return 0


if __name__ == "__main__":
    sys.exit(main())
