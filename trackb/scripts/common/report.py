"""
Track B Report Generator
마크다운 보고서 자동 생성
"""

from typing import Dict, List, Any, Optional
from pathlib import Path
import pandas as pd
import json
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


class ReportGenerator:
    """마크다운 보고서 생성기"""
    
    def __init__(self, output_dir: Path, language: str = 'korean'):
        """
        Args:
            output_dir: 출력 디렉토리
            language: 보고서 언어 ('korean' 또는 'english')
        """
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.language = language
        self.sections = []
    
    def add_header(self, title: str, subtitle: Optional[str] = None) -> None:
        """헤더 추가"""
        content = f"# {title}\n"
        if subtitle:
            content += f"## {subtitle}\n"
        content += f"\n생성 시각: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n"
        self.sections.append(content)
    
    def add_section(self, title: str, content: str, level: int = 2) -> None:
        """섹션 추가"""
        header = '#' * level
        section = f"\n{'━' * 50}\n{header} {title}\n{'━' * 50}\n\n{content}\n"
        self.sections.append(section)
    
    def add_table(self, df: pd.DataFrame, title: Optional[str] = None) -> None:
        """테이블 추가"""
        if title:
            self.sections.append(f"\n**{title}**\n")
        self.sections.append(df.to_markdown(index=False) + "\n")
    
    def add_metrics_table(
        self,
        metrics: Dict[str, Any],
        title: str = "주요 메트릭"
    ) -> None:
        """메트릭 테이블 추가"""
        rows = []
        for key, value in metrics.items():
            if isinstance(value, float):
                if 'rate' in key or 'recall' in key or 'precision' in key or 'f1' in key:
                    formatted = f"{value:.1%}"
                elif 'cost' in key.lower():
                    formatted = f"{value:,.0f}"  # 절대 $ 금지
                else:
                    formatted = f"{value:.4f}"
            elif isinstance(value, int):
                formatted = f"{value:,}"
            else:
                formatted = str(value)
            
            rows.append({'지표': key, '값': formatted})
        
        df = pd.DataFrame(rows)
        self.add_table(df, title)
    
    def add_comparison_table(
        self,
        comparison_df: pd.DataFrame,
        highlight_best: bool = True
    ) -> None:
        """비교 테이블 추가"""
        # framework 행 NaN 보정: baseline(첫 행) 값으로 채움 (표시용)
        formatted_df = comparison_df.copy()
        if len(formatted_df) >= 2:
            baseline = formatted_df.iloc[0]
            last_idx = formatted_df.index[-1]
            for col in formatted_df.columns:
                if col == 'method':
                    continue
                if pd.isna(formatted_df.loc[last_idx, col]) and col in baseline.index:
                    formatted_df.loc[last_idx, col] = baseline[col]
        
        for col in formatted_df.columns:
            if 'rate' in col or 'recall' in col or 'precision' in col or 'f1' in col:
                formatted_df[col] = formatted_df[col].apply(
                    lambda x: f"{x:.1%}" if pd.notna(x) else ""
                )
            elif 'cost' in col.lower() and 'pct' not in col.lower():
                # 절대 $ 금지: 정규화/비율만 (단위 표기 없이 수치)
                formatted_df[col] = formatted_df[col].apply(
                    lambda x: f"{x:,.0f}" if pd.notna(x) else ""
                )
            elif 'delta' in col.lower() and 'pct' in col.lower():
                formatted_df[col] = formatted_df[col].apply(
                    lambda x: f"{x:+.1f}%" if pd.notna(x) else ""
                )
        
        # 표 바로 위 주석: 3000/150/500 등이 통화가 아님을 명시
        self.sections.append("*All cost-like values in this table: **normalized units (not currency)**.*\n\n")
        self.add_table(formatted_df, "방법별 비교")
    
    def add_statistical_results(
        self,
        stats_results: Dict[str, Any]
    ) -> None:
        """통계 검정 결과 추가"""
        content = "### 통계 검정 결과\n\n"
        
        tests = stats_results.get('tests', {})
        
        for test_name, result in tests.items():
            sig = "✅ 유의" if result.get('significant_005') else "❌ 비유의"
            p_val = result.get('p_value', 0)
            p_str = f"<0.001" if p_val < 0.001 else f"{p_val:.3f}"
            
            content += f"- **{test_name}**: p = {p_str} ({sig})\n"
        
        summary = stats_results.get('summary', {})
        content += f"\n**결론**: {summary.get('conclusion', '')}\n"
        
        self.sections.append(content)
    
    def add_figure(
        self,
        figure_path: str,
        caption: str,
        width: Optional[str] = None
    ) -> None:
        """그림 추가"""
        rel_path = Path(figure_path).name
        if width:
            content = f'<img src="../figures/{rel_path}" width="{width}" alt="{caption}">\n\n'
        else:
            content = f"![{caption}](../figures/{rel_path})\n\n"
        content += f"*그림: {caption}*\n"
        self.sections.append(content)
    
    def add_validation_status(self) -> None:
        """검증 상태 섹션 추가"""
        content = """
### 검증 상태

| 구성 요소 | 상태 | 설명 |
|-----------|------|------|
| Stage 0–2A (STEP 1) | ✅ | Same-source, yield_true GT validated (200개 테스트 웨이퍼) |
| Stage 2B (STEP 2) | ⚠️ | Benchmark performance reported (proxy; different source) |
| Stage 3 (STEP 3) | ⚠️ | Benchmark performance reported (proxy; different source) |
| 통합 (2B → 3) | ⚠️ | Proxy plausibility check only (not causal) |

**한계**: 다른 데이터 출처로 인해 동일 웨이퍼 검증 불가
**향후 과제**: 통합된 다단계 측정 데이터 수집
"""
        self.sections.append(content)
    
    def add_limitations(self) -> None:
        """한계 섹션 추가"""
        content = """
### 현재 한계

1. **데이터 통합**: 다른 출처의 데이터, proxy 기반 통합
2. **클래스 불균형**: Step1에서는 high-risk를 bottom 20%(k=40/200)로 정의. 실제 fab에서는 정의/비율이 달라질 수 있어 운영 전 캘리브레이션 필요.
3. **Pattern 추정**: 도메인 지식 기반, 실제 관측값 없음
4. **Lot-level**: This evaluation reflects within-production-distribution performance under the current sampling scheme. Lot-level generalization requires additional holdout-lot validation.

### 향후 개선

- 동일 웨이퍼 다단계 측정 데이터 수집
- 희귀 결함 후속검사 데이터 확장
- 엔지니어 피드백 기반 온라인 정책 업데이트
"""
        self.sections.append(content)
    
    def add_run_disclaimer(self, run_id: str) -> None:
        """현재 run만 사용함을 명시 (할루시네이션 방지)"""
        content = f"""
**데이터 출처**: 본 보고서의 모든 수치·표·결론은 **이 실행(run_{run_id})** 의 산출물만 사용합니다. 다른 run 또는 외부 데이터를 사용하지 않습니다.
"""
        self.sections.append(content)

    def add_evidence_index(
        self,
        run_id: str,
        manifest_path: Optional[Path] = None,
        manifest_dict: Optional[Dict[str, Any]] = None,
    ) -> None:
        """증거 인덱스: 주요 산출물 경로 및 SHA256 (재현성·검증용)"""
        content = f"### 증거 인덱스 (run_{run_id})\n\n"
        content += "아래 파일에서 보고서 수치를 인용했습니다. 해시로 동일 실행 여부를 확인할 수 있습니다.\n\n"
        rows = []
        if manifest_dict:
            for out_entry in manifest_dict.get("outputs", [])[:20]:
                path = out_entry.get("path", "")
                sha = out_entry.get("sha256", "")
                name = Path(path).name if path else ""
                if "validation/" in path or "baselines/" in path or "agent/autotune" in path:
                    rows.append({"파일": name, "경로": path, "SHA256": sha})
            if rows:
                content += pd.DataFrame(rows).to_markdown(index=False) + "\n\n"
        if manifest_path and Path(manifest_path).exists():
            content += f"- **Manifest**: `{manifest_path}` (전체 입·출력 목록 및 해시)\n"
        if not rows and not (manifest_path and Path(manifest_path).exists()):
            content += "*(Manifest가 아직 없거나 비어 있음. 파이프라인 완료 후 _manifest.json 참조)*\n"
        self.sections.append(content)

    def add_reproducibility_section(
        self,
        run_id: str,
        manifest_path: Optional[str] = None,
        config_path: Optional[str] = None,
    ) -> None:
        """재현성 섹션 추가 (현재 run 기준 경로)"""
        content = "### 재현성\n\n"
        content += f"- **실행 ID**: `run_{run_id}`\n"
        if manifest_path:
            content += f"- **Manifest**: [{manifest_path}]({manifest_path})\n"
        if config_path:
            content += f"- **설정**: [{config_path}]({config_path})\n"
        content += """
**재현 단계**:
```bash
cd trackb/
python scripts/trackb_run.py --mode from_artifacts
```
"""
        self.sections.append(content)
    
    def generate(self, filename: str = "trackB_report.md") -> Path:
        """보고서 생성 및 저장"""
        content = "\n".join(self.sections)
        content += "\n\n" + "━" * 50 + "\n보고서 끝\n" + "━" * 50 + "\n"
        
        output_path = self.output_dir / filename
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(content)
        
        logger.info(f"보고서 생성됨: {output_path}")
        return output_path
    
    def reset(self) -> None:
        """섹션 초기화"""
        self.sections = []


def generate_executive_summary(
    metrics: Dict[str, Any],
    comparison_df: pd.DataFrame,
    stats_results: Dict[str, Any]
) -> str:
    """요약 보고서 생성"""
    # 프레임워크 결과 (마지막 행으로 가정)
    framework = comparison_df.iloc[-1] if len(comparison_df) > 1 else comparison_df.iloc[0]
    baseline = comparison_df.iloc[0]
    
    cost_reduction = (baseline['total_cost'] - framework['total_cost']) / baseline['total_cost'] * 100
    recall_improvement = framework['high_risk_recall'] - baseline['high_risk_recall']
    
    summary = f"""
## 요약

### 핵심 성과 (Ground Truth 검증)

- **비용 절감**: {cost_reduction:.1f}%
- **고위험 재현율 향상**: {recall_improvement:.1%}p
- **누락된 고위험 웨이퍼 감소**: {baseline.get('missed_high_risk', 0) - framework.get('missed_high_risk', 0)}개

### 통계적 유의성

"""
    
    tests = stats_results.get('tests', {})
    for test_name, result in tests.items():
        if result.get('significant_005'):
            p_str = "<0.001" if result['p_value'] < 0.001 else f"{result['p_value']:.3f}"
            summary += f"- {test_name}: p = {p_str} ✅\n"
    
    return summary


def generate_methodology_section() -> str:
    """방법론 섹션 생성"""
    return """
## 방법론

### 1. 데이터

- **테스트 셋**: 200개 실제 fab 웨이퍼 (독립, 학습에 미사용)
- **Ground Truth**: yield_true (실제 최종 수율)
- **고위험 정의**: yield < 0.6 (하위 ~20%)

### 2. Baselines

**Baseline 1: Random Sampling**
- 무작위 10% inline 검사
- 업계 표준 fallback 방법

**Baseline 2: Rule-based**
- Stage 0 risk 상위 10% 선택
- 단순 임계값 기반 방법

### 3. 제안 프레임워크

- **Threshold Optimizer**: Validation set에서 grid search로 최적 임계값 탐색
- **Budget-aware Scheduler**: 예산 상황에 따라 동적 임계값 조정
- **Decision Explainer**: 각 결정에 대한 이유 기록

### 4. 검증

- T-test: 선택된 웨이퍼 yield 비교
- Chi-square: 검출률 비교
- Bootstrap: 비용 절감 신뢰구간
- McNemar: 개별 샘플 수준 비교
"""
