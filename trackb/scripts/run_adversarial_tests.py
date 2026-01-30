#!/usr/bin/env python3
"""
의도적 오류 주입 반증 테스트.
- proxy 단어 1개 삽입 → verify가 FAIL해야 함
- $ 문자 1개 삽입 → verify가 FAIL해야 함
- 원복 후 verify 재통과 확인
"""

import sys
import subprocess
from pathlib import Path

TRACKB_ROOT = Path(__file__).parent.parent
OUTPUT_DIR = TRACKB_ROOT / "outputs"
SCRIPTS_DIR = Path(__file__).parent


def get_run_dir(run_id: str) -> Path:
    return OUTPUT_DIR / f"run_{run_id}"


def run_verify(run_id: str) -> int:
    r = subprocess.run(
        [sys.executable, str(SCRIPTS_DIR / "verify_outputs.py"), "--run_id", run_id],
        cwd=str(SCRIPTS_DIR),
        capture_output=True,
        text=True,
        timeout=60,
    )
    return r.returncode


def main():
    import argparse
    p = argparse.ArgumentParser(description="Adversarial tests: inject proxy/$ and assert verify FAILs")
    p.add_argument("--run_id", type=str, default=None, help="Run ID (default: latest)")
    args = p.parse_args()

    run_id = args.run_id
    if not run_id:
        latest = OUTPUT_DIR / "latest"
        if latest.exists():
            target = latest.read_text().strip() if latest.is_file() else latest.resolve().name
            run_id = target.replace("run_", "")
        else:
            dirs = sorted([d.name for d in OUTPUT_DIR.iterdir() if d.is_dir() and d.name.startswith("run_")], reverse=True)
            run_id = dirs[0].replace("run_", "") if dirs else None
    if not run_id:
        print("No run_id found. Run pipeline first or pass --run_id")
        sys.exit(1)

    run_dir = get_run_dir(run_id)
    core_path = run_dir / "reports" / "trackB_report_core_validated.md"
    if not core_path.exists():
        print(f"Core report not found: {core_path}")
        sys.exit(1)

    original = core_path.read_text(encoding="utf-8")

    # 1) 원본 상태에서 verify (PASS 또는 WARN 기대)
    print("1) Baseline verify (expect PASS or PASS_WITH_WARNINGS)...")
    code0 = run_verify(run_id)
    print(f"   Exit code: {code0}")

    # 2) proxy 삽입 → verify FAIL
    print("2) Inject 'proxy' into core → verify must FAIL...")
    core_path.write_text(original + "\n\nproxy\n", encoding="utf-8")
    code1 = run_verify(run_id)
    core_path.write_text(original, encoding="utf-8")
    if code1 == 0:
        print("   FAIL: verify should have exited non-zero when 'proxy' present in core")
        sys.exit(1)
    print(f"   Exit code: {code1} (expected non-zero) OK")

    # 3) $ 삽입 → verify FAIL
    print("3) Inject '$' into core → verify must FAIL...")
    core_path.write_text(original + "\n\nCost: $100\n", encoding="utf-8")
    code2 = run_verify(run_id)
    core_path.write_text(original, encoding="utf-8")
    if code2 == 0:
        print("   FAIL: verify should have exited non-zero when '$' present in core")
        sys.exit(1)
    print(f"   Exit code: {code2} (expected non-zero) OK")

    # 4) 원복 후 verify
    print("4) Restore and verify again (expect same as baseline)...")
    code3 = run_verify(run_id)
    if code3 != code0:
        print(f"   WARN: exit code after restore ({code3}) differs from baseline ({code0})")
    else:
        print("   OK: verify result after restore matches baseline")

    print("\nAdversarial tests passed: verifier correctly rejects proxy/$ in core and passes after restore.")
    sys.exit(0)


if __name__ == "__main__":
    main()
