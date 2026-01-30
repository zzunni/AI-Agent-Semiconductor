"""
Track B Agent Charts
Agent 구성 요소 관련 시각화
"""

from typing import Dict, List, Optional
from pathlib import Path
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import matplotlib
matplotlib.use('Agg')
import logging

logger = logging.getLogger(__name__)

plt.rcParams['axes.unicode_minus'] = False


def plot_threshold_optimization(
    history_df: pd.DataFrame,
    best_config: Dict[str, float],
    output_path: Optional[Path] = None,
    figsize: tuple = (12, 5)
) -> plt.Figure:
    """
    임계값 최적화 히스토리 플롯
    """
    fig, axes = plt.subplots(1, 2, figsize=figsize)
    
    # 왼쪽: Recall vs Cost scatter
    ax1 = axes[0]
    
    within_budget = history_df['within_budget']
    
    scatter = ax1.scatter(
        history_df.loc[within_budget, 'cost'],
        history_df.loc[within_budget, 'recall'] * 100,
        c=history_df.loc[within_budget, 'f1'],
        cmap='viridis',
        s=50, alpha=0.7,
        edgecolor='black', linewidth=0.5
    )
    
    # 예산 초과 (회색)
    ax1.scatter(
        history_df.loc[~within_budget, 'cost'],
        history_df.loc[~within_budget, 'recall'] * 100,
        c='gray', s=30, alpha=0.3,
        label='Over budget'
    )
    
    # 최적 설정 표시
    best_mask = (
        (history_df['tau0'] == best_config['tau0']) &
        (history_df['tau1'] == best_config['tau1']) &
        (history_df['tau2a'] == best_config['tau2a'])
    )
    if best_mask.sum() > 0:
        best_row = history_df[best_mask].iloc[0]
        ax1.scatter(
            best_row['cost'],
            best_row['recall'] * 100,
            marker='*', s=300, c='red',
            edgecolor='black', linewidth=2,
            label=f'Best (τ0={best_config["tau0"]})'
        )
    
    ax1.set_xlabel('Cost ($)', fontsize=11)
    ax1.set_ylabel('Recall (%)', fontsize=11)
    ax1.set_title('Optimization Landscape', fontsize=12, fontweight='bold')
    ax1.legend(loc='lower right')
    ax1.grid(True, linestyle='--', alpha=0.7)
    
    cbar = plt.colorbar(scatter, ax=ax1)
    cbar.set_label('F1 Score')
    
    # 오른쪽: Threshold distribution
    ax2 = axes[1]
    
    # 예산 내 설정의 tau0 분포
    within_budget_df = history_df[history_df['within_budget']]
    
    tau0_recalls = within_budget_df.groupby('tau0')['recall'].mean()
    
    ax2.bar(
        [str(t) for t in tau0_recalls.index],
        tau0_recalls.values * 100,
        color='steelblue', edgecolor='black'
    )
    
    # 최적 표시
    best_tau0_str = str(best_config['tau0'])
    for i, tick in enumerate(ax2.get_xticklabels()):
        if tick.get_text() == best_tau0_str:
            ax2.patches[i].set_facecolor('red')
    
    ax2.set_xlabel('τ0 Threshold', fontsize=11)
    ax2.set_ylabel('Avg Recall (%)', fontsize=11)
    ax2.set_title('Recall by τ0', fontsize=12, fontweight='bold')
    ax2.yaxis.grid(True, linestyle='--', alpha=0.7)
    
    plt.tight_layout()
    
    if output_path:
        fig.savefig(output_path, dpi=300, bbox_inches='tight')
        logger.info(f"임계값 최적화 차트 저장: {output_path}")
    
    return fig


def plot_budget_tracking(
    scheduler_log: pd.DataFrame,
    output_path: Optional[Path] = None,
    figsize: tuple = (12, 6)
) -> plt.Figure:
    """
    예산 추적 차트
    """
    fig, axes = plt.subplots(2, 1, figsize=figsize, sharex=True)
    
    # 상단: 예산 잔액
    ax1 = axes[0]
    
    wafer_idx = range(len(scheduler_log))
    budget_remaining = scheduler_log['budget_remaining_after'].tolist()
    
    ax1.plot(wafer_idx, budget_remaining, 'b-', linewidth=1.5)
    ax1.fill_between(wafer_idx, 0, budget_remaining, alpha=0.3)
    
    # 위기/경고 선
    if 'wafers_remaining' in scheduler_log.columns:
        n_wafers = len(scheduler_log)
        ax1.axhline(y=80 * n_wafers * 0.5, color='red', linestyle='--', 
                   label='Critical', alpha=0.7)
        ax1.axhline(y=120 * n_wafers * 0.5, color='orange', linestyle='--',
                   label='Warning', alpha=0.7)
    
    ax1.set_ylabel('Budget Remaining ($)', fontsize=11)
    ax1.set_title('Budget Tracking', fontsize=12, fontweight='bold')
    ax1.legend(loc='upper right')
    ax1.grid(True, linestyle='--', alpha=0.7)
    
    # 하단: 조정된 임계값
    ax2 = axes[1]
    
    if 'tau_adjusted' in scheduler_log.columns:
        ax2.plot(wafer_idx, scheduler_log['tau_adjusted'], 'g-', linewidth=1.5)
        
        # 결정 표시
        if 'decision' in scheduler_log.columns:
            inspect_mask = scheduler_log['decision'] == 'inspect'
            ax2.scatter(
                [i for i, m in enumerate(inspect_mask) if m],
                scheduler_log.loc[inspect_mask, 'tau_adjusted'],
                c='red', s=20, label='Inspected', zorder=5
            )
    
    ax2.set_xlabel('Wafer Index', fontsize=11)
    ax2.set_ylabel('Adjusted Threshold', fontsize=11)
    ax2.set_title('Dynamic Threshold Adjustment', fontsize=12, fontweight='bold')
    ax2.legend(loc='upper right')
    ax2.grid(True, linestyle='--', alpha=0.7)
    
    plt.tight_layout()
    
    if output_path:
        fig.savefig(output_path, dpi=300, bbox_inches='tight')
        logger.info(f"예산 추적 차트 저장: {output_path}")
    
    return fig


def plot_decision_distribution(
    decision_trace: pd.DataFrame,
    output_path: Optional[Path] = None,
    figsize: tuple = (10, 5)
) -> plt.Figure:
    """
    결정 분포 차트
    """
    fig, axes = plt.subplots(1, 2, figsize=figsize)
    
    # 왼쪽: 결정 파이 차트
    ax1 = axes[0]
    
    if 'decision' in decision_trace.columns:
        decision_counts = decision_trace['decision'].value_counts()
        colors = ['#27ae60' if d == 'inspect' else '#95a5a6' 
                  for d in decision_counts.index]
        
        ax1.pie(
            decision_counts.values,
            labels=decision_counts.index,
            colors=colors,
            autopct='%1.1f%%',
            startangle=90,
            explode=[0.05 if d == 'inspect' else 0 for d in decision_counts.index]
        )
        ax1.set_title('Decision Distribution', fontsize=12, fontweight='bold')
    
    # 오른쪽: 스케줄러 이유 분포
    ax2 = axes[1]
    
    if 'scheduler_reason' in decision_trace.columns:
        reason_counts = decision_trace['scheduler_reason'].value_counts()
        
        colors_map = {
            'normal': '#3498db',
            'low_budget': '#f39c12',
            'critical_budget': '#e74c3c',
            'budget_surplus': '#27ae60'
        }
        colors = [colors_map.get(r, '#95a5a6') for r in reason_counts.index]
        
        ax2.bar(reason_counts.index, reason_counts.values, color=colors, edgecolor='black')
        ax2.set_xlabel('Scheduler Reason')
        ax2.set_ylabel('Count')
        ax2.set_title('Scheduler Adjustment Reasons', fontsize=12, fontweight='bold')
        ax2.tick_params(axis='x', rotation=45)
        ax2.yaxis.grid(True, linestyle='--', alpha=0.7)
    
    plt.tight_layout()
    
    if output_path:
        fig.savefig(output_path, dpi=300, bbox_inches='tight')
        logger.info(f"결정 분포 차트 저장: {output_path}")
    
    return fig


def create_all_agent_charts(
    optimizer_history: pd.DataFrame,
    best_config: Dict[str, float],
    scheduler_log: pd.DataFrame,
    decision_trace: pd.DataFrame,
    output_dir: Path
) -> Dict[str, Path]:
    """모든 Agent 관련 차트 생성"""
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    
    charts = {}
    
    # 임계값 최적화
    if optimizer_history is not None and not optimizer_history.empty:
        path = output_dir / 'threshold_optimization.png'
        plot_threshold_optimization(optimizer_history, best_config, path)
        charts['threshold_optimization'] = path
    
    # 예산 추적
    if scheduler_log is not None and not scheduler_log.empty:
        path = output_dir / 'budget_tracking.png'
        plot_budget_tracking(scheduler_log, path)
        charts['budget_tracking'] = path
    
    # 결정 분포
    if decision_trace is not None and not decision_trace.empty:
        path = output_dir / 'decision_distribution.png'
        plot_decision_distribution(decision_trace, path)
        charts['decision_distribution'] = path
    
    logger.info(f"Agent 차트 {len(charts)}개 생성 완료")
    
    return charts
