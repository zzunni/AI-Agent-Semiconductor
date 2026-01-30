#!/usr/bin/env python3
"""
Track B Report Generator
보고서 자동 생성 스크립트
"""

import sys
import json
import logging
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, Optional
import pandas as pd

# 경로 설정
SCRIPT_DIR = Path(__file__).parent
TRACKB_ROOT = SCRIPT_DIR.parent
sys.path.insert(0, str(SCRIPT_DIR))

from common.io import load_csv_safe, load_json_safe
from common.report import ReportGenerator, generate_executive_summary, generate_methodology_section

logger = logging.getLogger(__name__)


def generate_trackb_report(
    outputs_dir: Path,
    config: Dict[str, Any],
    output_path: Optional[Path] = None
) -> str:
    """
    Track B 마스터 보고서 생성
    
    Args:
        outputs_dir: outputs 디렉토리 경로
        config: 설정 딕셔너리
        output_path: 출력 경로 (None이면 기본 경로)
    
    Returns:
        생성된 보고서 내용
    """
    outputs_dir = Path(outputs_dir)
    
    if output_path is None:
        output_path = outputs_dir / 'reports' / 'trackB_report.md'
    
    # 보고서 시작
    report = f"""# Track B 검증 보고서
## AI 기반 모듈러 프레임워크 - 과학적 검증

생성 시각: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
설정 파일: configs/trackb_config.json

"""
    
    # ━━━━━ 요약 ━━━━━
    report += "\n" + "━" * 50 + "\n"
    report += "## 요약\n"
    report += "━" * 50 + "\n\n"
    
    # 비교 결과 로드
    try:
        comparison_path = outputs_dir / 'validation' / 'framework_results.csv'
        comparison_df = load_csv_safe(comparison_path)
        
        if len(comparison_df) >= 3:
            random = comparison_df.iloc[0]
            rulebased = comparison_df.iloc[1]
            framework = comparison_df.iloc[2]
            
            report += """### 주요 기여 (Ground Truth 검증)
- 데이터: 200개 실제 웨이퍼 (yield_true 있음)
- 방법: 자율 최적화 Agent
- Baseline: Random (10%) + Rule-based (top 10%)

### 핵심 결과
| 지표 | Random | Rule-based | Framework | 개선 |
|------|--------|------------|-----------|------|
"""
            
            metrics = [
                ('비용 (units)', 'total_cost', '{:,.0f}'),
                ('선택 수', 'n_selected', '{:.0f}'),
                ('고위험 Recall (%)', 'high_risk_recall', '{:.1%}'),
                ('고위험 Precision (%)', 'high_risk_precision', '{:.1%}'),
                ('고위험 F1 (%)', 'high_risk_f1', '{:.1%}'),
                ('검출당 비용 (units)', 'cost_per_catch', '{:,.0f}'),
                ('누락 고위험', 'missed_high_risk', '{:.0f}'),
            ]
            
            for label, col, fmt in metrics:
                if col in comparison_df.columns:
                    r_val = random.get(col, 0)
                    rb_val = rulebased.get(col, 0)
                    f_val = framework.get(col, 0)
                    
                    if col in ['total_cost', 'cost_per_catch', 'missed_high_risk']:
                        delta = r_val - f_val
                        delta_str = f"-{abs(delta):.0f}" if delta > 0 else f"+{abs(delta):.0f}"
                    else:
                        delta = f_val - r_val
                        if col in ['high_risk_recall', 'high_risk_precision', 'high_risk_f1']:
                            delta_str = f"+{delta:.1%}" if delta > 0 else f"{delta:.1%}"
                        else:
                            delta_str = f"+{delta:.0f}" if delta > 0 else f"{delta:.0f}"
                    
                    r_str = fmt.format(r_val) if r_val else 'N/A'
                    rb_str = fmt.format(rb_val) if rb_val else 'N/A'
                    f_str = fmt.format(f_val) if f_val else 'N/A'
                    
                    report += f"| {label} | {r_str} | {rb_str} | {f_str} | {delta_str} |\n"
    except Exception as e:
        logger.warning(f"비교 결과 로드 실패: {e}")
        report += "비교 결과를 로드할 수 없습니다.\n"
    
    # ━━━━━ 통계 검증 ━━━━━
    report += "\n### 통계 검증\n"
    
    try:
        stats_path = outputs_dir / 'validation' / 'statistical_tests.json'
        if stats_path.exists():
            stats = load_json_safe(stats_path)
            
            tests = stats.get('tests', {})
            for test_name, result in tests.items():
                p_val = result.get('p_value', 0)
                sig = "✅ 유의" if result.get('significant_005') else "❌ 비유의"
                p_str = "<0.001" if p_val < 0.001 else f"{p_val:.4f}"
                report += f"- **{test_name}**: p = {p_str} ({sig})\n"
    except Exception as e:
        logger.warning(f"통계 결과 로드 실패: {e}")
    
    # ━━━━━ 검증 상태 ━━━━━
    report += """
### 검증 상태
| 구성 요소 | 상태 | 설명 |
|-----------|------|------|
| Stage 0–2A (STEP 1) | ✅ | Same-source, yield_true GT validated (200개 테스트 웨이퍼) |
| Stage 2B (STEP 2) | ⚠️ | Benchmark performance reported (proxy; different source) |
| Stage 3 (STEP 3) | ⚠️ | Benchmark performance reported (proxy; different source) |
| 통합 (2B → 3) | ⚠️ | Proxy plausibility check only (not causal) |

"""
    
    # ━━━━━ 방법론 ━━━━━
    report += "\n" + "━" * 50 + "\n"
    report += "## 1. 실험 설정\n"
    report += "━" * 50 + "\n\n"
    report += generate_methodology_section()
    
    # ━━━━━ Agent 결과 ━━━━━
    report += "\n" + "━" * 50 + "\n"
    report += "## 2. Agent 구성 요소\n"
    report += "━" * 50 + "\n\n"
    
    try:
        autotune_path = outputs_dir / 'agent' / 'autotune_summary.json'
        if autotune_path.exists():
            autotune = load_json_safe(autotune_path)
            
            report += "### 2.1 Threshold Optimizer\n"
            report += f"- 방법: Grid Search\n"
            report += f"- 탐색 공간: {autotune.get('search_space', {})}\n"
            report += f"- 예산 제약 (units): {autotune.get('budget_constraint', 0):,.0f}\n"
            report += f"- 최적 설정: {autotune.get('best_config', {})}\n"
            report += f"- 최적 점수: {autotune.get('best_score', 0):.4f}\n"
            report += f"- 평가 반복: {autotune.get('iterations_evaluated', 0)}회\n\n"
    except Exception as e:
        logger.warning(f"Agent 결과 로드 실패: {e}")
    
    # ━━━━━ 한계 및 향후 과제 ━━━━━
    report += "\n" + "━" * 50 + "\n"
    report += "## 3. 한계 및 향후 과제\n"
    report += "━" * 50 + "\n\n"
    
    report += """### 3.1 현재 한계
1. **데이터 통합**: 다른 출처의 데이터, proxy 기반 통합
2. **클래스 불균형**: Step1에서는 high-risk를 bottom 20%(k=40/200)로 정의. 실제 fab에서는 정의/비율이 달라질 수 있어 운영 전 캘리브레이션 필요.
3. **Pattern 추정**: 도메인 지식 기반, 실제 관측값 없음

### 3.2 향후 개선
- 동일 웨이퍼 다단계 측정 데이터 수집
- 희귀 결함 SEM 데이터 확장
- 엔지니어 피드백 기반 온라인 정책 업데이트

"""
    
    # ━━━━━ 재현성 ━━━━━
    report += "\n" + "━" * 50 + "\n"
    report += "## 4. 재현성\n"
    report += "━" * 50 + "\n\n"
    
    report += """### 4.1 재현 단계
```bash
cd trackb/
python scripts/trackb_run.py --mode from_artifacts
```

### 4.2 파일 참조
- Manifest: [_manifest.json](../_manifest.json)
- 설정: [trackb_config.json](../../configs/trackb_config.json)

"""
    
    # 마무리
    report += "\n" + "━" * 50 + "\n"
    report += "보고서 끝\n"
    report += "━" * 50 + "\n"
    
    # 저장
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(report)
    
    logger.info(f"보고서 저장: {output_path}")
    
    return report


def generate_step_reports(outputs_dir: Path) -> None:
    """각 단계별 보고서 생성"""
    outputs_dir = Path(outputs_dir)
    reports_dir = outputs_dir / 'reports'
    reports_dir.mkdir(parents=True, exist_ok=True)
    
    # Step 1 보고서
    step1_report = """# Step 1 보고서
## Stage 0-2A: 센서 기반 리스크 스코어링

### 데이터
- 총 웨이퍼: 1,252개
- 테스트 셋: 200개 (독립)
- Ground truth: yield_true

### 모델
- Stage 0: XGBoost
- Stage 1: XGBoost (추가 피처)
- Stage 2A: XGBoost (추가 피처)

### 검증 상태
✅ Ground truth 기반 완전 검증
"""
    
    with open(reports_dir / 'step1_report.md', 'w', encoding='utf-8') as f:
        f.write(step1_report)
    
    # Step 2 보고서
    step2_report = """# Step 2 보고서
## Stage 2B: Wafermap 패턴 분류

### 데이터
- 출처: WM-811K 벤치마크
- 학습 데이터: ~170,000 웨이퍼
- 테스트 데이터: ~17,000 웨이퍼

### 모델
- 아키텍처: SmallCNN
- 파일: wm_cnn_best.pt

### 검증 상태
⚠️ WM-811K 벤치마크에서 독립 검증
(Step 1과 다른 데이터 출처)
"""
    
    with open(reports_dir / 'step2_report.md', 'w', encoding='utf-8') as f:
        f.write(step2_report)
    
    # Step 3 보고서
    step3_report = """# Step 3 보고서
## SEM + 운영 계층

### 데이터
- 출처: Carinthia 데이터셋
- 결함 클래스: 9개

### 검증 상태
⚠️ Carinthia 데이터셋에서 독립 검증
(Step 1, 2와 다른 데이터 출처)

### 통합 방법
- Proxy 기반 매핑
- Plausibility-checked (인과 증명 아님)
"""
    
    with open(reports_dir / 'step3_report.md', 'w', encoding='utf-8') as f:
        f.write(step3_report)
    
    logger.info(f"단계별 보고서 생성 완료: {reports_dir}")


if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO)
    
    # 설정 로드
    config_path = TRACKB_ROOT / 'configs' / 'trackb_config.json'
    with open(config_path, 'r', encoding='utf-8') as f:
        config = json.load(f)
    
    outputs_dir = TRACKB_ROOT / config['paths']['trackb_outputs']
    
    # 보고서 생성
    generate_trackb_report(outputs_dir, config)
    generate_step_reports(outputs_dir)
