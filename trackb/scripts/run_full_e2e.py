#!/usr/bin/env python3
"""
Track B End-to-End 실행: compileall → static_check → trackb_run → verify_outputs → adversarial → 산출물 요약.
항상 이 순서로 실행하여 정책·검증·반증 테스트까지 통과시키는 스크립트.
"""

import subprocess
import sys
from pathlib import Path

TRACKB_ROOT = Path(__file__).resolve().parent.parent
REPO_ROOT = TRACKB_ROOT.parent
SCRIPTS_DIR = Path(__file__).resolve().parent
OUTPUTS_DIR = TRACKB_ROOT / "outputs"

REQUIRED_ARTIFACTS = [
    "reports/trackB_report_core_validated.md",
    "reports/trackB_report_appendix_proxy.md",
    "reports/trackA_report.md",
    "reports/FINAL_VALIDATION.md",
    "reports/final_validation_report.json",
    "reports/paper_bundle.json",
    "reports/PAPER_IO_TRACE.md",
    "_manifest.json",
]


def run(cmd: list, cwd: Path, desc: str) -> tuple[int, str]:
    p = subprocess.run(cmd, cwd=str(cwd), capture_output=True, text=True, timeout=300)
    out = (p.stdout or "") + (p.stderr or "")
    return p.returncode, out


def main() -> int:
    print("=" * 60)
    print("Track B Full E2E: compileall → static_check → trackb_run → verify → adversarial → summary")
    print("=" * 60)

    # 1) compileall
    print("\n[1] compileall trackb ...")
    code, out = run([sys.executable, "-m", "compileall", str(TRACKB_ROOT), "-q"], REPO_ROOT, "compileall")
    if code != 0:
        print(out)
        print("FAIL: compileall")
        return 1
    print("  OK")

    # 2) static_check
    print("\n[2] static_check.py ...")
    code, out = run([sys.executable, str(SCRIPTS_DIR / "static_check.py")], TRACKB_ROOT, "static_check")
    if code != 0:
        print(out)
        print("FAIL: static_check")
        return 1
    print("  OK")

    # 3) trackb_run
    print("\n[3] trackb_run.py --mode from_artifacts --skip_figures ...")
    code, out = run(
        [sys.executable, str(SCRIPTS_DIR / "trackb_run.py"), "--mode", "from_artifacts", "--skip_figures"],
        SCRIPTS_DIR,
        "trackb_run",
    )
    if code != 0:
        print(out)
        print("FAIL: trackb_run")
        return 1
    # Parse run_id from log (last run_YYYYMMDD_HHMMSS)
    run_id = None
    for line in out.splitlines():
        if "Run ID:" in line:
            run_id = line.split("Run ID:")[-1].strip()
            break
    if not run_id:
        dirs = sorted([d.name for d in OUTPUTS_DIR.iterdir() if d.is_dir() and d.name.startswith("run_")], reverse=True)
        run_id = dirs[0].replace("run_", "") if dirs else None
    if not run_id:
        print("Could not determine run_id")
        return 1
    print(f"  OK run_id={run_id}")

    run_dir = OUTPUTS_DIR / f"run_{run_id}"

    # 4) verify_outputs
    print("\n[4] verify_outputs.py --run_id", run_id, "...")
    code, out = run(
        [sys.executable, str(SCRIPTS_DIR / "verify_outputs.py"), "--run_id", run_id],
        SCRIPTS_DIR,
        "verify",
    )
    if code != 0:
        print(out)
        print("FAIL: verify_outputs")
        return 1
    print("  OK")

    # 5) adversarial tests
    print("\n[5] run_adversarial_tests.py --run_id", run_id, "...")
    code, out = run(
        [sys.executable, str(SCRIPTS_DIR / "run_adversarial_tests.py"), "--run_id", run_id],
        SCRIPTS_DIR,
        "adversarial",
    )
    if code != 0:
        print(out)
        print("FAIL: adversarial tests")
        return 1
    print("  OK")

    # 6) 산출물 요약
    print("\n" + "=" * 60)
    print("최종 산출물 경로 (run_{})".format(run_id))
    print("=" * 60)
    for rel in REQUIRED_ARTIFACTS:
        full = run_dir / rel
        status = "OK" if full.exists() else "MISSING"
        print(f"  [{status}] {rel}")
    print("  base_dir:", run_dir)
    print("=" * 60)
    print("E2E 완료: 모든 규칙 통과 (verify + FINAL_VALIDATION verdict)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
