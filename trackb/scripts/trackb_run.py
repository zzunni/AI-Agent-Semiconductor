#!/usr/bin/env python3
"""
Track B Main Execution Script
Track B 메인 실행 스크립트

Usage:
    python scripts/trackb_run.py --mode from_artifacts
    python scripts/trackb_run.py --mode quick --skip_figures
    python scripts/trackb_run.py --help
"""

import argparse
import sys
import json
import logging
from pathlib import Path
from datetime import datetime
from typing import Optional

# 경로 설정
SCRIPT_DIR = Path(__file__).parent
TRACKB_ROOT = SCRIPT_DIR.parent
sys.path.insert(0, str(SCRIPT_DIR))

from common.io import PathResolver, save_json_safe, save_csv_safe
from common.report import ReportGenerator
from integration.pipeline import TrackBPipeline
from integration.step1_loader import Step1Loader
from integration.step2_loader import Step2Loader
from integration.step3_loader import Step3Loader
from validation.ground_truth_validator import GroundTruthValidator
from validation.statistical_validator import run_full_validation, format_validation_report
import json
from visualization.cost_charts import plot_cost_comparison, plot_cost_breakdown
from visualization.performance_charts import plot_detection_performance, plot_confusion_matrices
from visualization.agent_charts import create_all_agent_charts

# 로깅 설정
def setup_logging(verbose: bool = False) -> None:
    """로깅 설정"""
    level = logging.DEBUG if verbose else logging.INFO
    
    # Run ID가 있으면 해당 디렉토리 사용, 없으면 임시 경로
    log_file = TRACKB_ROOT / 'outputs' / 'trackb_run.log'
    
    logging.basicConfig(
        level=level,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler(sys.stdout),
            logging.FileHandler(log_file, encoding='utf-8')
        ]
    )

logger = logging.getLogger(__name__)


def load_config(config_path: Path) -> dict:
    """설정 로드. 출력 경로를 trackb 루트 기준으로 고정하여 검증기와 일치시킨다."""
    with open(config_path, 'r', encoding='utf-8') as f:
        config = json.load(f)
    # 출력은 항상 trackb/outputs/ 에 두어 verify_outputs.py와 동일한 기준 사용
    config.setdefault('paths', {})['trackb_outputs'] = str(TRACKB_ROOT / 'outputs')
    return config


def run_from_artifacts(config: dict, skip_figures: bool = False) -> dict:
    """
    아티팩트에서 파이프라인 실행
    
    Args:
        config: 설정 딕셔너리
        skip_figures: True면 그림 생성 스킵
    
    Returns:
        결과 딕셔너리
    """
    logger.info("=" * 60)
    logger.info("Track B 파이프라인 시작 (mode: from_artifacts)")
    logger.info("=" * 60)
    
    start_time = datetime.now()
    
    # Run ID 생성 (타임스탬프 기반)
    run_id = start_time.strftime("%Y%m%d_%H%M%S")
    logger.info(f"Run ID: {run_id}")
    
    # Run ID를 config에 추가
    config['run_id'] = run_id
    config['run_timestamp'] = start_time.isoformat()
    
    # 파이프라인 초기화
    pipeline = TrackBPipeline(config)
    
    # 실행
    results = pipeline.run()
    
    # 그림 생성
    if not skip_figures:
        logger.info("시각화 생성 중...")
        figures_dir = Path(config['paths']['trackb_outputs']) / 'figures'
        figures_dir = TRACKB_ROOT / figures_dir
        figures_dir.mkdir(parents=True, exist_ok=True)
        
        try:
            # 비용 비교
            if 'validation' in results and 'comparison' in results['validation']:
                comparison_df = results['validation']['comparison']
                plot_cost_comparison(
                    comparison_df,
                    figures_dir / 'cost_comparison.png'
                )
                plot_detection_performance(
                    comparison_df,
                    figures_dir / 'detection_performance.png'
                )
            
            # Agent 차트
            if 'agent' in results:
                agent_results = results['agent']
                
                optimizer_history = None
                best_config = {'tau0': 0.6, 'tau1': 0.6, 'tau2a': 0.6}
                
                if agent_results.get('optimizer'):
                    optimizer_history = agent_results['optimizer'].get('history_df')
                    if 'summary' in agent_results['optimizer']:
                        best_config = agent_results['optimizer']['summary'].get(
                            'best_config', best_config
                        )
                
                scheduler_log = None
                if agent_results.get('scheduler'):
                    scheduler_log = agent_results['scheduler'].get('log_df')
                
                explainer_trace = None
                if agent_results.get('explainer'):
                    explainer_trace = agent_results['explainer'].get('trace_df')
                
                if optimizer_history is not None or scheduler_log is not None:
                    create_all_agent_charts(
                        optimizer_history,
                        best_config,
                        scheduler_log,
                        explainer_trace,
                        figures_dir
                    )
            
            logger.info(f"✅ 시각화 생성 완료: {figures_dir}")
        except Exception as e:
            logger.warning(f"시각화 생성 중 오류: {e}")
    
    # Run-isolated paths
    run_id = config.get('run_id', 'unknown')
    results['run_id'] = run_id
    run_output_dir = TRACKB_ROOT / 'outputs' / f'run_{run_id}'
    reports_dir = run_output_dir / 'reports'
    reports_dir.mkdir(parents=True, exist_ok=True)
    
    # Lot leakage 진단 + Random seed sweep (paper_reports / final_validation에서 사용)
    try:
        from lot_leakage_diagnostics import compute_lot_diagnostics
        raw = config.get('paths', {}).get('step1_artifacts', '')
        step1_dir = (TRACKB_ROOT / raw).resolve() if raw else TRACKB_ROOT.parent / 'data' / 'step1'
        step1_dir = step1_dir if step1_dir.exists() else None
        diag = compute_lot_diagnostics(run_output_dir, step1_dir=step1_dir)
        out_path = run_output_dir / 'validation' / 'lot_leakage_diagnostics.json'
        out_path.parent.mkdir(parents=True, exist_ok=True)
        with open(out_path, 'w', encoding='utf-8') as f:
            json.dump(diag, f, indent=2, ensure_ascii=False)
        logger.info(f"✅ Lot leakage diagnostics: {out_path}")
    except Exception as e:
        logger.warning(f"Lot leakage diagnostics 오류: {e}")
    try:
        from random_seed_sweep import run_sweep
        sweep_df, sweep_summary = run_sweep(run_output_dir, n_seeds=50)
        val_dir = run_output_dir / 'validation'
        val_dir.mkdir(parents=True, exist_ok=True)
        sweep_df.to_csv(val_dir / 'random_seed_sweep.csv', index=False)
        with open(val_dir / 'random_seed_sweep_summary.json', 'w', encoding='utf-8') as f:
            json.dump(sweep_summary, f, indent=2, ensure_ascii=False)
        logger.info("✅ Random seed sweep: validation/random_seed_sweep.csv, random_seed_sweep_summary.json")
    except Exception as e:
        logger.warning(f"Random seed sweep 오류: {e}")
    
    # 매니페스트 먼저 생성 (보고서에서 SHA256·증거 인덱스 참조)
    logger.info("매니페스트 생성 중...")
    try:
        manifest = pipeline.generate_manifest()
        results['manifest'] = manifest
    except Exception as e:
        logger.warning(f"매니페스트 생성 중 오류: {e}")
    
    # 보고서 생성 (현재 run 데이터만 사용, SHA256 포함)
    logger.info("보고서 생성 중...")
    try:
        generate_master_report(results, config, reports_dir, run_id=run_id, run_output_dir=run_output_dir)
    except Exception as e:
        logger.warning(f"보고서 생성 중 오류: {e}")
    
    # Paper Input Bundle: paper_bundle.json + Core/Appendix/TrackA/PAPER_IO_TRACE
    logger.info("Paper bundle 생성 중...")
    try:
        from paper_bundle import write_paper_bundle
        from paper_reports import write_paper_reports
        write_paper_bundle(run_output_dir, config, run_id)
        write_paper_reports(run_output_dir, run_id, config)
    except Exception as e:
        logger.warning(f"Paper bundle/reports 오류: {e}")

    # 궁극 목표 종합 검증: FINAL_VALIDATION.md (Q1~Q6, 판정) — 산출물 기반만 사용
    logger.info("Final validation 생성 중...")
    try:
        from final_validation import write_final_validation
        write_final_validation(run_output_dir, run_id)
    except Exception as e:
        logger.warning(f"Final validation 오류: {e}")

    # 완료
    end_time = datetime.now()
    duration = (end_time - start_time).total_seconds()
    
    logger.info("=" * 60)
    logger.info(f"Track B 파이프라인 완료")
    logger.info(f"소요 시간: {duration:.1f}초")
    logger.info("=" * 60)
    
    # 결과 요약 출력
    print_summary(results)
    
    return results


def generate_master_report(
    results: dict,
    config: dict,
    reports_dir: Path,
    run_id: str = 'unknown',
    run_output_dir: Optional[Path] = None,
) -> Path:
    """마스터 보고서 생성. 현재 run 데이터만 사용하며, SHA256·증거 인덱스 포함."""
    if run_output_dir is None:
        run_output_dir = reports_dir.parent
    report_gen = ReportGenerator(reports_dir, language='korean')
    
    # 헤더
    report_gen.add_header(
        "Track B 검증 보고서",
        "AI 기반 모듈러 프레임워크 - 과학적 검증"
    )
    # 현재 run만 사용 명시 (할루시네이션 방지)
    report_gen.add_run_disclaimer(run_id)
    
    # 요약
    if 'validation' in results and 'comparison' in results['validation']:
        comparison_df = results['validation']['comparison']
        
        summary_content = """
### 주요 기여 (Ground Truth 검증)
- 데이터: 200개 실제 웨이퍼 (yield_true 있음)
- 방법: 자율 최적화 Agent
- Baseline: Random (10%) + Rule-based (top 10%)

"""
        report_gen.add_section("요약", summary_content)
        # 정책 방어: Primary만 결론, 나머지 exploratory
        report_gen.sections.append("""**Primary conclusions use only**: Recall@10% and normalized cost reduction (%) with bootstrap 95% CI.
**All other tests** (t-test, chi-square, McNemar) are exploratory and not used for final claims.

""")
        # 비용 = 정규화 단위 명시 (돈처럼 오해 방지)
        report_gen.sections.append("Cost values are reported in **normalized units (unitless)**. No currency or absolute money is used.\n")
        report_gen.sections.append("Numbers like 3000/150/500 in tables are **normalized units (not currency)**.\n\n")
        # 표 컬럼명: 보고서에서만 _norm 접미사로 라벨링 (절대 비용 오해 방지)
        display_df = comparison_df.rename(columns={
            'n_sem': 'n_followup',
            'sem_cost': 'followup_cost_norm',
            'cost_sem_unit': 'followup_unit_norm',
            'inline_cost': 'inline_cost_norm',
            'total_cost': 'total_cost_norm',
            'cost_per_catch': 'cost_per_catch_norm',
            'cost_inline_unit': 'cost_unit_inline_norm',
        }, errors='ignore')
        report_gen.add_comparison_table(display_df)
    
    # 검증 상태
    report_gen.add_validation_status()
    
    # 통계 검증 (현재 run의 statistical_tests.json에서 직접 읽기)
    stats_json_path = reports_dir.parent / 'validation' / 'statistical_tests.json'
    if stats_json_path.exists():
        try:
            with open(stats_json_path, 'r', encoding='utf-8') as f:
                stats_data = json.load(f)
            stats_section = format_statistical_tests_from_json(stats_data)
            report_gen.sections.append(stats_section)
        except Exception as e:
            logger.warning(f"통계 검증 결과 로드 실패: {e}")
            report_gen.add_section("통계 검증 결과", f"⚠️ 통계 검증 결과 로드 실패: {e}")
    elif 'validation' in results:
        stats_section = format_validation_report(results['validation'])
        report_gen.sections.append(stats_section)
    
    # 한계
    report_gen.add_limitations()
    
    # 증거 인덱스 (SHA256·경로)
    manifest_path = run_output_dir / '_manifest.json'
    manifest_dict = None
    if manifest_path.exists():
        try:
            with open(manifest_path, 'r', encoding='utf-8') as f:
                manifest_dict = json.load(f)
        except Exception as e:
            logger.warning(f"Manifest 로드 실패: {e}")
    report_gen.add_evidence_index(run_id, manifest_path=manifest_path, manifest_dict=manifest_dict)
    
    # 재현성 (현재 run 기준 경로)
    report_gen.add_reproducibility_section(
        run_id=run_id,
        manifest_path='../_manifest.json',
        config_path='../../configs/trackb_config.json'
    )
    
    # 저장
    output_path = report_gen.generate("trackB_report.md")
    
    logger.info(f"✅ 마스터 보고서 생성: {output_path}")
    
    return output_path


def format_statistical_tests_from_json(stats_data: dict) -> str:
    """statistical_tests.json에서 직접 통계 검증 결과 포맷팅"""
    report = """
## 통계 검증 결과

### 검정 요약

"""
    
    tests = stats_data.get('tests', {})
    summary = stats_data.get('summary', {})
    
    # T-test
    if 't_test_yields' in tests:
        t_test = tests['t_test_yields']
        t_sig = "✅ 유의" if t_test.get('significant_005') else "❌ 비유의"
        t_p = t_test.get('p_value', 0)
        t_p_str = "<0.001" if t_p < 0.001 else f"{t_p:.4f}"
        report += f"- **T-test (yield 비교)**: t={t_test.get('t_statistic', 'N/A'):.3f}, p={t_p_str} ({t_sig})\n"
        report += f"  - 비교 집단: 선택된 웨이퍼의 yield_true 분포 (baseline vs framework)\n"
        report += f"  - Baseline mean: {t_test.get('baseline_mean', 0):.4f}, Framework mean: {t_test.get('framework_mean', 0):.4f}\n"
        report += f"  - Sample sizes: n_baseline={t_test.get('n_baseline', 0)}, n_framework={t_test.get('n_framework', 0)}\n"
    
    # Chi-square
    if 'chi_square_detection' in tests:
        chi_sq = tests['chi_square_detection']
        chi_sig = "✅ 유의" if chi_sq.get('significant_005') else "❌ 비유의"
        chi_p = chi_sq.get('p_value', 0)
        chi_p_str = "<0.001" if chi_p < 0.001 else f"{chi_p:.4f}"
        report += f"- **Chi-square (검출률)**: χ²={chi_sq.get('chi2_statistic', 'N/A'):.3f}, p={chi_p_str} ({chi_sig})\n"
        contingency = chi_sq.get('contingency_table', [])
        if contingency:
            report += f"  - Contingency table: Baseline [TP={contingency[0][0]}, FN={contingency[0][1]}], Framework [TP={contingency[1][0]}, FN={contingency[1][1]}]\n"
    
    # Bootstrap: policy — % CI only, no absolute cost CI
    if 'bootstrap_cost' in tests:
        bootstrap = tests['bootstrap_cost']
        pct_low = bootstrap.get('delta_cost_pct_ci_lower')
        pct_high = bootstrap.get('delta_cost_pct_ci_upper')
        if pct_low is not None and pct_high is not None:
            report += f"- **Bootstrap (normalized cost reduction %, 95% CI)**: [{pct_low:.1f}%, {pct_high:.1f}%] (percentage only; no absolute money units)\n"
        else:
            report += f"- **Bootstrap (normalized cost reduction %)**: observed {bootstrap.get('percent_reduction', 0):.1f}% (CI in percentage only)\n"
        report += f"  - n_bootstrap: {bootstrap.get('n_bootstrap', 0)}\n"
    
    # McNemar
    if 'mcnemar' in tests:
        mcnemar = tests['mcnemar']
        mcn_sig = "✅ 유의" if mcnemar.get('significant_005') else "❌ 비유의"
        mcn_p = mcnemar.get('p_value', 0)
        mcn_p_str = "<0.001" if mcn_p < 0.001 else f"{mcn_p:.4f}"
        report += f"- **McNemar**: statistic={mcnemar.get('statistic', 'N/A'):.3f}, p={mcn_p_str} ({mcn_sig})\n"
    
    # High-risk count 확인
    hr_count = stats_data.get('high_risk_count', None)
    if hr_count is not None:
        report += f"\n**High-risk count**: {hr_count} (하위 20% 정의 기준)\n"
    
    # 결론
    report += f"""
### 전체 결론

{summary.get('conclusion', '')}

- 총 검정 수: {summary.get('total_tests', 0)}
- 유의한 검정 수: {summary.get('significant_count', 0)}
- 유의한 검정: {', '.join(summary.get('significant_tests', []))}
"""
    
    return report


def print_summary(results: dict) -> None:
    """결과 요약 출력"""
    print("\n" + "=" * 60)
    print("결과 요약")
    print("=" * 60)
    
    # 베이스라인 결과
    if 'baselines' in results:
        print("\n📊 Baseline 결과:")
        for name, data in results['baselines'].items():
            if name == 'comparison':
                continue
            if isinstance(data, dict) and 'metrics' in data:
                metrics = data['metrics']
                print(f"  {name}:")
                print(f"    - Recall: {metrics.get('high_risk_recall', 0):.1%}")
                print(f"    - total_cost (normalized): {metrics.get('total_cost', 0):,.0f}")
    
    # Agent 결과
    if 'agent' in results:
        agent = results['agent']
        print("\n🤖 Agent 결과:")
        
        if agent.get('optimizer'):
            opt = agent['optimizer']
            print(f"  Optimizer: tau0={opt.get('best_tau0', 'N/A')}, score={opt.get('best_score', 0):.4f}")
        
        if agent.get('scheduler'):
            sched = agent['scheduler']['summary']
            print(f"  Scheduler: {sched.get('n_inspected', 0)}/{sched.get('total_wafers', 0)} 선택")
            print(f"  예산 사용: {sched.get('budget_utilization', 0):.1%}")
        
        if agent.get('framework_metrics'):
            fm = agent['framework_metrics']
            print(f"  Framework 성능:")
            print(f"    - Recall: {fm['detection'].get('high_risk_recall', 0):.1%}")
            print(f"    - Precision: {fm['detection'].get('high_risk_precision', 0):.1%}")
            print(f"    - total_cost (normalized): {fm['cost'].get('total_cost', 0):,.0f}")
    
    # 통계 검증
    if 'validation' in results:
        validation = results['validation']
        print("\n📈 통계 검증:")
        
        for comp_name, comp_data in validation.get('comparisons', {}).items():
            print(f"  {comp_name}:")
            
            chi_sq = comp_data.get('chi_square', {})
            if chi_sq.get('p_value') is not None:
                sig = "✅" if chi_sq.get('significant_005') else "❌"
                print(f"    - Chi-square: p={chi_sq['p_value']:.4f} {sig}")
            
            bootstrap = comp_data.get('bootstrap', {})
            if bootstrap.get('percent_reduction') is not None:
                print(f"    - 비용 절감: {bootstrap['percent_reduction']:.1f}%")
    
    run_id = results.get('run_id', 'unknown')
    report_path = f"trackb/outputs/run_{run_id}/reports/trackB_report.md"
    print("\n" + "=" * 60)
    print(f"상세 결과: {report_path}")
    print("=" * 60 + "\n")


def main():
    """메인 함수"""
    parser = argparse.ArgumentParser(
        description='Track B 과학적 검증 파이프라인',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
    # 아티팩트에서 전체 실행
    python scripts/trackb_run.py --mode from_artifacts
    
    # 빠른 테스트 (그림 스킵)
    python scripts/trackb_run.py --mode from_artifacts --skip_figures
    
    # 상세 로그
    python scripts/trackb_run.py --mode from_artifacts --verbose
        """
    )
    
    parser.add_argument(
        '--mode',
        choices=['from_artifacts', 'quick', 'full'],
        default='from_artifacts',
        help='실행 모드 (기본: from_artifacts)'
    )
    
    parser.add_argument(
        '--config',
        type=str,
        default='configs/trackb_config.json',
        help='설정 파일 경로'
    )
    
    parser.add_argument(
        '--skip_figures',
        action='store_true',
        help='그림 생성 스킵'
    )
    
    parser.add_argument(
        '--verbose', '-v',
        action='store_true',
        help='상세 로그 출력'
    )
    
    args = parser.parse_args()
    
    # 로깅 설정
    setup_logging(args.verbose)
    
    # 설정 로드
    config_path = TRACKB_ROOT / args.config
    if not config_path.exists():
        logger.error(f"설정 파일이 없습니다: {config_path}")
        sys.exit(1)
    
    config = load_config(config_path)
    
    # 모드별 실행
    if args.mode == 'from_artifacts':
        results = run_from_artifacts(config, skip_figures=args.skip_figures)
    elif args.mode == 'quick':
        results = run_from_artifacts(config, skip_figures=True)
    elif args.mode == 'full':
        results = run_from_artifacts(config, skip_figures=False)
    else:
        logger.error(f"알 수 없는 모드: {args.mode}")
        sys.exit(1)
    
    # 종료
    logger.info("Track B 파이프라인 종료")


if __name__ == '__main__':
    main()
