"""
Track B Performance Charts
검출 성능 관련 시각화
"""

from typing import Dict, List, Optional
from pathlib import Path
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import matplotlib
matplotlib.use('Agg')
from sklearn.metrics import roc_curve, auc, confusion_matrix
import logging

logger = logging.getLogger(__name__)

plt.rcParams['axes.unicode_minus'] = False


def plot_detection_performance(
    comparison_df: pd.DataFrame,
    output_path: Optional[Path] = None,
    figsize: tuple = (12, 5)
) -> plt.Figure:
    """
    검출 성능 메트릭 비교 차트
    """
    fig, axes = plt.subplots(1, 3, figsize=figsize)
    
    methods = comparison_df['method'].tolist()
    colors = ['#e74c3c', '#f39c12', '#27ae60'][:len(methods)]
    
    # Recall
    ax1 = axes[0]
    recalls = comparison_df['high_risk_recall'].tolist()
    bars = ax1.bar(methods, [r * 100 for r in recalls], color=colors, edgecolor='black')
    ax1.set_ylabel('Recall (%)')
    ax1.set_title('High-Risk Recall')
    ax1.set_ylim(0, 100)
    for bar, val in zip(bars, recalls):
        ax1.annotate(f'{val:.1%}', xy=(bar.get_x() + bar.get_width()/2, bar.get_height()),
                     xytext=(0, 3), textcoords='offset points', ha='center', fontsize=10)
    
    # Precision
    ax2 = axes[1]
    precisions = comparison_df['high_risk_precision'].tolist()
    bars = ax2.bar(methods, [p * 100 for p in precisions], color=colors, edgecolor='black')
    ax2.set_ylabel('Precision (%)')
    ax2.set_title('High-Risk Precision')
    ax2.set_ylim(0, 100)
    for bar, val in zip(bars, precisions):
        ax2.annotate(f'{val:.1%}', xy=(bar.get_x() + bar.get_width()/2, bar.get_height()),
                     xytext=(0, 3), textcoords='offset points', ha='center', fontsize=10)
    
    # F1
    ax3 = axes[2]
    f1s = comparison_df['high_risk_f1'].tolist()
    bars = ax3.bar(methods, [f * 100 for f in f1s], color=colors, edgecolor='black')
    ax3.set_ylabel('F1 Score (%)')
    ax3.set_title('High-Risk F1')
    ax3.set_ylim(0, 100)
    for bar, val in zip(bars, f1s):
        ax3.annotate(f'{val:.1%}', xy=(bar.get_x() + bar.get_width()/2, bar.get_height()),
                     xytext=(0, 3), textcoords='offset points', ha='center', fontsize=10)
    
    for ax in axes:
        ax.yaxis.grid(True, linestyle='--', alpha=0.7)
        ax.set_axisbelow(True)
    
    plt.tight_layout()
    
    if output_path:
        fig.savefig(output_path, dpi=300, bbox_inches='tight')
        logger.info(f"검출 성능 차트 저장: {output_path}")
    
    return fig


def plot_roc_curves(
    results: Dict[str, pd.DataFrame],
    yield_col: str = 'yield_true',
    risk_col: str = 'riskscore',
    high_risk_threshold: float = 0.6,
    output_path: Optional[Path] = None,
    figsize: tuple = (8, 8)
) -> plt.Figure:
    """
    ROC 곡선 플롯
    """
    fig, ax = plt.subplots(figsize=figsize)
    
    colors = ['#e74c3c', '#f39c12', '#27ae60']
    linestyles = ['-', '--', '-.']
    
    for i, (method, df) in enumerate(results.items()):
        if risk_col not in df.columns:
            continue
        
        # Ground truth: high risk = 1
        y_true = (df[yield_col] < high_risk_threshold).astype(int)
        y_score = df[risk_col]
        
        fpr, tpr, _ = roc_curve(y_true, y_score)
        roc_auc = auc(fpr, tpr)
        
        ax.plot(
            fpr, tpr,
            color=colors[i % len(colors)],
            linestyle=linestyles[i % len(linestyles)],
            linewidth=2,
            label=f'{method} (AUC = {roc_auc:.3f})'
        )
    
    # 대각선 (무작위)
    ax.plot([0, 1], [0, 1], 'k--', linewidth=1, label='Random (AUC = 0.500)')
    
    ax.set_xlabel('False Positive Rate', fontsize=12)
    ax.set_ylabel('True Positive Rate', fontsize=12)
    ax.set_title('ROC Curves for High-Risk Detection', fontsize=14, fontweight='bold')
    ax.legend(loc='lower right')
    ax.grid(True, linestyle='--', alpha=0.7)
    ax.set_xlim([0, 1])
    ax.set_ylim([0, 1])
    
    plt.tight_layout()
    
    if output_path:
        fig.savefig(output_path, dpi=300, bbox_inches='tight')
        logger.info(f"ROC 곡선 저장: {output_path}")
    
    return fig


def plot_confusion_matrices(
    results: Dict[str, pd.DataFrame],
    yield_col: str = 'yield_true',
    selected_col: str = 'selected',
    high_risk_threshold: float = 0.6,
    output_path: Optional[Path] = None,
    figsize: tuple = (15, 4)
) -> plt.Figure:
    """
    혼동 행렬 히트맵
    """
    n_methods = len(results)
    fig, axes = plt.subplots(1, n_methods, figsize=figsize)
    
    if n_methods == 1:
        axes = [axes]
    
    for ax, (method, df) in zip(axes, results.items()):
        # Ground truth
        y_true = (df[yield_col] < high_risk_threshold).astype(int)
        y_pred = df[selected_col].astype(int)
        
        cm = confusion_matrix(y_true, y_pred)
        
        # 히트맵
        im = ax.imshow(cm, cmap='Blues')
        
        # 값 표시
        for i in range(2):
            for j in range(2):
                text = ax.text(j, i, cm[i, j],
                              ha='center', va='center',
                              fontsize=14, fontweight='bold')
        
        ax.set_xticks([0, 1])
        ax.set_yticks([0, 1])
        ax.set_xticklabels(['Not Selected', 'Selected'])
        ax.set_yticklabels(['Low Risk', 'High Risk'])
        ax.set_xlabel('Predicted')
        ax.set_ylabel('Actual')
        ax.set_title(f'{method}')
    
    plt.suptitle('Confusion Matrices', fontsize=14, fontweight='bold', y=1.02)
    plt.tight_layout()
    
    if output_path:
        fig.savefig(output_path, dpi=300, bbox_inches='tight')
        logger.info(f"혼동 행렬 저장: {output_path}")
    
    return fig


def plot_stage_funnel(
    stage_counts: Dict[str, int],
    output_path: Optional[Path] = None,
    figsize: tuple = (10, 6)
) -> plt.Figure:
    """
    스테이지별 필터링 퍼널 차트
    """
    fig, ax = plt.subplots(figsize=figsize)
    
    stages = list(stage_counts.keys())
    counts = list(stage_counts.values())
    
    # 퍼널 모양 바
    colors = plt.cm.Blues(np.linspace(0.3, 0.9, len(stages)))
    
    y_positions = np.arange(len(stages))[::-1]
    
    for i, (stage, count, y) in enumerate(zip(stages, counts, y_positions)):
        width = count / max(counts)
        ax.barh(y, width, height=0.6, left=(1-width)/2, 
               color=colors[i], edgecolor='black', linewidth=1)
        ax.text(0.5, y, f'{stage}\n{count:,}', 
               ha='center', va='center', fontsize=11, fontweight='bold')
    
    ax.set_xlim(0, 1)
    ax.set_ylim(-0.5, len(stages) - 0.5)
    ax.axis('off')
    ax.set_title('Stage Filtering Funnel', fontsize=14, fontweight='bold')
    
    plt.tight_layout()
    
    if output_path:
        fig.savefig(output_path, dpi=300, bbox_inches='tight')
        logger.info(f"스테이지 퍼널 저장: {output_path}")
    
    return fig
