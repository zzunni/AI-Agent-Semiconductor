#!/usr/bin/env python3
"""
정적 점검: compileall + 보고서 생성 로직에서 $ 포맷 전수 스캔.
"""

import subprocess
import sys
from pathlib import Path

TRACKB_ROOT = Path(__file__).parent.parent
SCRIPTS_DIR = Path(__file__).parent


def main():
    errors = []
    # 1) compileall
    r = subprocess.run(
        [sys.executable, "-m", "compileall", str(SCRIPTS_DIR), "-q"],
        cwd=str(TRACKB_ROOT),
        capture_output=True,
        text=True,
    )
    if r.returncode != 0:
        errors.append("compileall failed")

    # 2) $ in report-related Python (금지)
    report_files = [
        "common/report.py",
        "report_generator.py",
        "paper_reports.py",
        "integration/pipeline.py",
        "final_validation.py",
    ]
    for rel in report_files:
        p = SCRIPTS_DIR / rel
        if p.exists():
            text = p.read_text(encoding="utf-8")
            # $ in string that would be written to report (e.g. f"${...}" or '${')
            if '"$' in text or "'$" in text or 'f"${' in text or "f'${" in text:
                errors.append(f"Cost policy: '$' found in {rel}")

    if errors:
        print("Static check FAILED:")
        for e in errors:
            print(f"  - {e}")
        sys.exit(1)
    print("Static check OK: compileall passed, no $ in report generators.")
    sys.exit(0)


if __name__ == "__main__":
    main()
