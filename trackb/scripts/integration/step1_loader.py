"""
Track B Step 1 Loader
STEP 1 (Stage 0-2A) 아티팩트 로더
"""

from typing import Dict, Any, Optional, Tuple, List
from pathlib import Path
import pandas as pd
import numpy as np
import json
import glob
import logging

logger = logging.getLogger(__name__)

# Canonical column name mappings
RISK_COLUMN_ALIASES = {
    'riskscore': ['riskscore', 'risk_score', 'stage0_risk', 'pred_proba', 'score', 'probability', 'y_pred'],
    'yield_true': ['yield_true', 'true_yield', 'actual_yield', 'ground_truth'],
    'wafer_id': ['wafer_id', 'WaferID', 'wafer'],
    'lot_id': ['lot_id', 'LotID', 'lot']
}


def find_column(df: pd.DataFrame, canonical_name: str) -> Optional[str]:
    """Find actual column name from aliases"""
    aliases = RISK_COLUMN_ALIASES.get(canonical_name, [canonical_name])
    for alias in aliases:
        if alias in df.columns:
            return alias
    return None


def map_to_canonical(df: pd.DataFrame) -> pd.DataFrame:
    """Map columns to canonical names"""
    df = df.copy()
    for canonical, aliases in RISK_COLUMN_ALIASES.items():
        actual = find_column(df, canonical)
        if actual and actual != canonical:
            df[canonical] = df[actual]
            logger.debug(f"Mapped '{actual}' -> '{canonical}'")
    return df


class Step1Loader:
    """
    STEP 1 아티팩트 로더
    Stage 0-2A 데이터, 모델, 예측 결과 로드
    """
    
    def __init__(self, step1_dir: Path):
        """
        Args:
            step1_dir: STEP 1 아티팩트 디렉토리 (data/step1/)
        """
        self.step1_dir = Path(step1_dir)
        if not self.step1_dir.exists():
            raise FileNotFoundError(f"STEP 1 디렉토리가 존재하지 않습니다: {step1_dir}")
        
        logger.info(f"Step1Loader 초기화: {step1_dir}")
    
    def _find_file(self, pattern: str) -> Optional[Path]:
        """패턴에 맞는 파일 찾기 (한글 파일명 지원)"""
        files = list(self.step1_dir.glob(pattern))
        if not files:
            return None
        # 가장 최근 파일 반환
        return max(files, key=lambda x: x.stat().st_mtime)
    
    def load_test_data(self, stage: str = 'stage0') -> pd.DataFrame:
        """
        테스트 데이터 로드
        
        Args:
            stage: 스테이지 ('stage0', 'stage1', 'stage2a')
        
        Returns:
            테스트 데이터 DataFrame
        """
        pattern = f"_{stage}_test*.csv"
        file_path = self._find_file(pattern)
        
        if file_path is None:
            raise FileNotFoundError(f"테스트 파일을 찾을 수 없습니다: {pattern}")
        
        df = pd.read_csv(file_path)
        logger.info(f"테스트 데이터 로드: {file_path.name} ({len(df)} 행)")
        
        return df
    
    def load_train_data(self, stage: str = 'stage0') -> pd.DataFrame:
        """학습 데이터 로드"""
        pattern = f"_{stage}_train*.csv"
        file_path = self._find_file(pattern)
        
        if file_path is None:
            raise FileNotFoundError(f"학습 파일을 찾을 수 없습니다: {pattern}")
        
        df = pd.read_csv(file_path)
        logger.info(f"학습 데이터 로드: {file_path.name} ({len(df)} 행)")
        
        return df
    
    def load_predictions(self, stage: str = 'stage0') -> pd.DataFrame:
        """
        예측 결과 로드
        
        Args:
            stage: 스테이지
        
        Returns:
            예측 결과 DataFrame (yield_true, yield_pred 포함)
        """
        pattern = f"_{stage}_pred*.csv"
        file_path = self._find_file(pattern)
        
        if file_path is None:
            raise FileNotFoundError(f"예측 파일을 찾을 수 없습니다: {pattern}")
        
        df = pd.read_csv(file_path)
        logger.info(f"예측 데이터 로드: {file_path.name} ({len(df)} 행)")
        
        return df
    
    def load_risk_scores(self, stage: str = 'stage0') -> pd.DataFrame:
        """
        Risk scores 로드
        
        Args:
            stage: 스테이지
        
        Returns:
            Risk scores DataFrame (riskscore 포함)
        """
        pattern = f"_{stage}_risk_scores*.csv"
        file_path = self._find_file(pattern)
        
        if file_path is None:
            raise FileNotFoundError(f"Risk scores 파일을 찾을 수 없습니다: {pattern}")
        
        df = pd.read_csv(file_path)
        logger.info(f"Risk scores 로드: {file_path.name} ({len(df)} 행)")
        
        return df
    
    def load_top_features(self, stage: str = 'stage0') -> Dict[str, Any]:
        """상위 피처 로드"""
        pattern = f"_{stage}_top_features*.json"
        file_path = self._find_file(pattern)
        
        if file_path is None:
            logger.warning(f"Top features 파일을 찾을 수 없습니다: {pattern}")
            return {}
        
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        logger.info(f"Top features 로드: {file_path.name}")
        return data
    
    def load_all_stages_test(self) -> Dict[str, pd.DataFrame]:
        """모든 스테이지 테스트 데이터 로드"""
        stages = ['stage0', 'stage1', 'stage2a']
        result = {}
        
        for stage in stages:
            try:
                result[stage] = self.load_test_data(stage)
            except FileNotFoundError as e:
                logger.warning(f"{stage} 테스트 데이터 없음: {e}")
        
        return result
    
    def load_all_stages_predictions(self) -> Dict[str, pd.DataFrame]:
        """모든 스테이지 예측 결과 로드"""
        stages = ['stage0', 'stage1', 'stage2a']
        result = {}
        
        for stage in stages:
            try:
                result[stage] = self.load_predictions(stage)
            except FileNotFoundError as e:
                logger.warning(f"{stage} 예측 데이터 없음: {e}")
        
        return result
    
    def get_consolidated_test_data(self, use_multistage: bool = True) -> pd.DataFrame:
        """
        통합 테스트 데이터 생성 (200 wafers - SACRED TEST SET)
        
        CRITICAL: 이 데이터는 최종 평가에만 사용. Optimizer는 절대 사용 금지!
        
        Args:
            use_multistage: True면 multi-stage combined risk 사용 (Framework용)
                           False면 stage0 risk만 사용 (Rule-based용)
        
        Returns:
            통합 테스트 DataFrame
        """
        # Stage 0 predictions 기본 (canonical source)
        try:
            base_df = self.load_predictions('stage0')
        except FileNotFoundError:
            base_df = self.load_test_data('stage0')
        
        # Map to canonical columns
        base_df = map_to_canonical(base_df)
        
        # Stage 0 Risk scores 병합
        try:
            risk_df = self.load_risk_scores('stage0')
            risk_df = map_to_canonical(risk_df)
            
            merge_cols = ['lot_id', 'wafer_id']
            extra_cols = [c for c in risk_df.columns if c not in base_df.columns]
            if extra_cols:
                base_df = base_df.merge(
                    risk_df[merge_cols + extra_cols],
                    on=merge_cols,
                    how='left'
                )
            base_df = base_df.rename(columns={'riskscore': 'risk_stage0'})
            logger.info(f"Stage 0 risk scores 병합 완료")
        except FileNotFoundError:
            if 'yield_true' in base_df.columns:
                base_df['risk_stage0'] = 1 - base_df['yield_true']
            logger.warning("Stage 0 risk scores 없음, yield 기반 proxy 생성")
        
        if use_multistage:
            # Multi-stage risk scores 병합
            try:
                risk1_df = self.load_risk_scores('stage1')
                risk1_df = map_to_canonical(risk1_df)
                base_df = base_df.merge(
                    risk1_df[['lot_id', 'wafer_id', 'riskscore']].rename(columns={'riskscore': 'risk_stage1'}),
                    on=['lot_id', 'wafer_id'],
                    how='left'
                )
                logger.info("Stage 1 risk scores 병합 완료")
            except FileNotFoundError:
                base_df['risk_stage1'] = base_df['risk_stage0']  # fallback
                logger.warning("Stage 1 risk scores 없음, stage0 사용")
            
            try:
                risk2a_df = self.load_risk_scores('stage2a')
                risk2a_df = map_to_canonical(risk2a_df)
                base_df = base_df.merge(
                    risk2a_df[['lot_id', 'wafer_id', 'riskscore']].rename(columns={'riskscore': 'risk_stage2a'}),
                    on=['lot_id', 'wafer_id'],
                    how='left'
                )
                logger.info("Stage 2A risk scores 병합 완료")
            except FileNotFoundError:
                base_df['risk_stage2a'] = base_df['risk_stage0']  # fallback
                logger.warning("Stage 2A risk scores 없음, stage0 사용")
            
            # Combined risk score (weighted average)
            # Weights: stage0=0.4, stage1=0.35, stage2a=0.25
            base_df['riskscore'] = (
                0.4 * base_df['risk_stage0'] +
                0.35 * base_df['risk_stage1'] +
                0.25 * base_df['risk_stage2a']
            )
            logger.info(
                f"Multi-stage combined risk 계산 완료: "
                f"[{base_df['riskscore'].min():.3f}, {base_df['riskscore'].max():.3f}]"
            )
        else:
            # Single stage (rule-based baseline용)
            base_df['riskscore'] = base_df['risk_stage0']
        
        # Verify yield_true exists
        if 'yield_true' not in base_df.columns:
            if 'yield' in base_df.columns:
                base_df['yield_true'] = base_df['yield']
                logger.warning("yield_true 없음, yield를 사용")
            else:
                raise ValueError("yield_true 또는 yield 컬럼이 필요합니다")
        
        logger.info(
            f"통합 테스트 데이터: {len(base_df)} 행, "
            f"riskscore range: [{base_df['riskscore'].min():.3f}, {base_df['riskscore'].max():.3f}]"
        )
        
        return base_df
    
    def get_train_val_split(
        self,
        stage: str = 'stage0',
        val_ratio: float = 0.2,
        seed: int = 42
    ) -> Tuple[pd.DataFrame, pd.DataFrame]:
        """
        학습 데이터에서 train/val 분리
        CRITICAL: Optimizer는 반드시 validation set만 사용해야 함
        
        Args:
            stage: 스테이지
            val_ratio: Validation 비율
            seed: 랜덤 시드
        
        Returns:
            (train_inner_df, val_df)
        """
        train_df = self.load_train_data(stage)
        
        # Map to canonical columns
        train_df = map_to_canonical(train_df)
        
        # 셔플 후 분리
        train_df = train_df.sample(frac=1, random_state=seed).reset_index(drop=True)
        
        n_val = int(len(train_df) * val_ratio)
        val_df = train_df.iloc[:n_val].copy()
        train_inner_df = train_df.iloc[n_val:].copy()
        
        # Validation에 yield_true가 없으면 yield를 사용
        if 'yield_true' not in val_df.columns and 'yield' in val_df.columns:
            val_df['yield_true'] = val_df['yield']
            logger.warning("Using 'yield' as 'yield_true' for validation set")
        
        # riskscore 생성 (yield 기반 proxy)
        if 'riskscore' not in val_df.columns:
            if 'yield' in val_df.columns:
                val_df['riskscore'] = 1 - val_df['yield']
                logger.warning("Generated 'riskscore' from yield for validation")
        
        logger.info(f"Train/Val 분리: train_inner={len(train_inner_df)}, val={len(val_df)}")
        
        return train_inner_df, val_df
    
    def get_validation_set(
        self,
        stage: str = 'stage0',
        val_ratio: float = 0.2,
        seed: int = 42
    ) -> pd.DataFrame:
        """
        Validation set만 반환 (Optimizer용)
        CRITICAL: Test set (200 wafers)과 완전히 분리됨
        
        Args:
            stage: 스테이지
            val_ratio: Validation 비율 (from train)
            seed: 랜덤 시드
        
        Returns:
            val_df
        """
        _, val_df = self.get_train_val_split(stage, val_ratio, seed)
        return val_df
    
    def get_summary(self) -> Dict[str, Any]:
        """로드된 데이터 요약"""
        summary = {
            'step1_dir': str(self.step1_dir),
            'stages': {}
        }
        
        for stage in ['stage0', 'stage1', 'stage2a']:
            stage_info = {}
            
            try:
                test_df = self.load_test_data(stage)
                stage_info['test_rows'] = len(test_df)
            except:
                stage_info['test_rows'] = None
            
            try:
                pred_df = self.load_predictions(stage)
                stage_info['pred_rows'] = len(pred_df)
            except:
                stage_info['pred_rows'] = None
            
            summary['stages'][stage] = stage_info
        
        return summary


def load_step1_artifacts(
    step1_dir: str,
    stage: str = 'stage0'
) -> Dict[str, Any]:
    """
    Step 1 아티팩트 로드 헬퍼 함수
    
    Args:
        step1_dir: STEP 1 디렉토리 경로
        stage: 스테이지
    
    Returns:
        아티팩트 딕셔너리
    """
    loader = Step1Loader(Path(step1_dir))
    
    artifacts = {
        'loader': loader,
        'test_data': None,
        'predictions': None,
        'risk_scores': None,
        'consolidated': None
    }
    
    try:
        artifacts['test_data'] = loader.load_test_data(stage)
    except FileNotFoundError:
        logger.warning(f"테스트 데이터 없음 ({stage})")
    
    try:
        artifacts['predictions'] = loader.load_predictions(stage)
    except FileNotFoundError:
        logger.warning(f"예측 데이터 없음 ({stage})")
    
    try:
        artifacts['risk_scores'] = loader.load_risk_scores(stage)
    except FileNotFoundError:
        logger.warning(f"Risk scores 없음 ({stage})")
    
    try:
        artifacts['consolidated'] = loader.get_consolidated_test_data()
    except Exception as e:
        logger.warning(f"통합 데이터 생성 실패: {e}")
    
    return artifacts
