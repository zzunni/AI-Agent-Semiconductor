"""
Track B Cost Charts
비용 관련 시각화
"""

from typing import Dict, List, Optional
from pathlib import Path
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import matplotlib
matplotlib.use('Agg')  # Non-interactive backend
import logging

logger = logging.getLogger(__name__)

# 한글 폰트 설정 (있으면 사용, 없으면 기본)
try:
    plt.rcParams['font.family'] = 'AppleGothic'
except:
    pass
plt.rcParams['axes.unicode_minus'] = False


def plot_cost_comparison(
    comparison_df: pd.DataFrame,
    output_path: Optional[Path] = None,
    figsize: tuple = (10, 6)
) -> plt.Figure:
    """
    방법별 비용 비교 바 차트
    
    Args:
        comparison_df: 비교 데이터프레임 (method, total_cost 컬럼)
        output_path: 저장 경로
        figsize: 그림 크기
    
    Returns:
        Figure 객체
    """
    fig, ax = plt.subplots(figsize=figsize)
    
    methods = comparison_df['method'].tolist()
    costs = comparison_df['total_cost'].tolist()
    
    # 색상
    colors = ['#e74c3c', '#f39c12', '#27ae60'][:len(methods)]
    
    bars = ax.bar(methods, costs, color=colors, edgecolor='black', linewidth=1.2)
    
    # 값 표시
    for bar, cost in zip(bars, costs):
        height = bar.get_height()
        ax.annotate(
            f'${cost:,.0f}',
            xy=(bar.get_x() + bar.get_width() / 2, height),
            xytext=(0, 3),
            textcoords='offset points',
            ha='center', va='bottom',
            fontsize=12, fontweight='bold'
        )
    
    ax.set_xlabel('Method', fontsize=12)
    ax.set_ylabel('Total Cost ($)', fontsize=12)
    ax.set_title('Cost Comparison by Method', fontsize=14, fontweight='bold')
    
    # 그리드
    ax.yaxis.grid(True, linestyle='--', alpha=0.7)
    ax.set_axisbelow(True)
    
    plt.tight_layout()
    
    if output_path:
        fig.savefig(output_path, dpi=300, bbox_inches='tight')
        logger.info(f"비용 비교 차트 저장: {output_path}")
    
    return fig


def plot_cost_breakdown(
    metrics: Dict[str, Dict],
    output_path: Optional[Path] = None,
    figsize: tuple = (12, 5)
) -> plt.Figure:
    """
    비용 분해 차트 (inline vs SEM)
    
    Args:
        metrics: 방법별 메트릭 딕셔너리
        output_path: 저장 경로
        figsize: 그림 크기
    
    Returns:
        Figure 객체
    """
    fig, axes = plt.subplots(1, 2, figsize=figsize)
    
    methods = list(metrics.keys())
    
    # 왼쪽: 비용 스택 바
    ax1 = axes[0]
    
    inline_costs = [m.get('inline_cost', m.get('total_cost', 0)) for m in metrics.values()]
    sem_costs = [m.get('sem_cost', 0) for m in metrics.values()]
    
    x = np.arange(len(methods))
    width = 0.6
    
    ax1.bar(x, inline_costs, width, label='Inline', color='#3498db')
    ax1.bar(x, sem_costs, width, bottom=inline_costs, label='SEM', color='#9b59b6')
    
    ax1.set_xlabel('Method')
    ax1.set_ylabel('Cost ($)')
    ax1.set_title('Cost Breakdown')
    ax1.set_xticks(x)
    ax1.set_xticklabels(methods)
    ax1.legend()
    ax1.yaxis.grid(True, linestyle='--', alpha=0.7)
    
    # 오른쪽: 검출당 비용
    ax2 = axes[1]
    
    cost_per_catch = [m.get('cost_per_catch', 0) for m in metrics.values()]
    # 무한대 값 처리
    cost_per_catch = [c if c != float('inf') else 0 for c in cost_per_catch]
    
    colors = ['#e74c3c', '#f39c12', '#27ae60'][:len(methods)]
    bars = ax2.bar(methods, cost_per_catch, color=colors, edgecolor='black')
    
    for bar, cost in zip(bars, cost_per_catch):
        if cost > 0:
            ax2.annotate(
                f'${cost:,.0f}',
                xy=(bar.get_x() + bar.get_width() / 2, bar.get_height()),
                xytext=(0, 3),
                textcoords='offset points',
                ha='center', va='bottom',
                fontsize=10
            )
    
    ax2.set_xlabel('Method')
    ax2.set_ylabel('Cost per Catch ($)')
    ax2.set_title('Cost Efficiency')
    ax2.yaxis.grid(True, linestyle='--', alpha=0.7)
    
    plt.tight_layout()
    
    if output_path:
        fig.savefig(output_path, dpi=300, bbox_inches='tight')
        logger.info(f"비용 분해 차트 저장: {output_path}")
    
    return fig


def plot_cost_vs_recall(
    comparison_df: pd.DataFrame,
    output_path: Optional[Path] = None,
    figsize: tuple = (8, 6)
) -> plt.Figure:
    """
    비용 vs 재현율 트레이드오프 플롯
    """
    fig, ax = plt.subplots(figsize=figsize)
    
    methods = comparison_df['method'].tolist()
    costs = comparison_df['total_cost'].tolist()
    recalls = comparison_df['high_risk_recall'].tolist()
    
    colors = ['#e74c3c', '#f39c12', '#27ae60'][:len(methods)]
    
    for method, cost, recall, color in zip(methods, costs, recalls, colors):
        ax.scatter(cost, recall * 100, s=200, c=color, label=method, 
                   edgecolor='black', linewidth=1.5, zorder=5)
    
    ax.set_xlabel('Total Cost ($)', fontsize=12)
    ax.set_ylabel('High-Risk Recall (%)', fontsize=12)
    ax.set_title('Cost vs Detection Performance', fontsize=14, fontweight='bold')
    ax.legend(loc='lower right')
    ax.grid(True, linestyle='--', alpha=0.7)
    
    # 이상적인 방향 화살표
    ax.annotate(
        'Better',
        xy=(min(costs) * 0.9, max(recalls) * 100 * 1.02),
        xytext=(min(costs) * 1.1, max(recalls) * 100 * 0.9),
        arrowprops=dict(arrowstyle='->', color='gray'),
        fontsize=10, color='gray'
    )
    
    plt.tight_layout()
    
    if output_path:
        fig.savefig(output_path, dpi=300, bbox_inches='tight')
        logger.info(f"비용 vs 재현율 플롯 저장: {output_path}")
    
    return fig
