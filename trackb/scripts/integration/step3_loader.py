"""
Track B Step 3 Loader
STEP 3 (SEM + Operational) 아티팩트 로더
"""

from typing import Dict, Any, Optional
from pathlib import Path
import pandas as pd
import json
import logging

logger = logging.getLogger(__name__)


class Step3Loader:
    """
    STEP 3 아티팩트 로더
    SEM 분류 및 운영 결과 로드
    """
    
    def __init__(self, step3_dir: Path):
        """
        Args:
            step3_dir: STEP 3 아티팩트 디렉토리 (data/step3/)
        """
        self.step3_dir = Path(step3_dir)
        if not self.step3_dir.exists():
            raise FileNotFoundError(f"STEP 3 디렉토리가 존재하지 않습니다: {step3_dir}")
        
        logger.info(f"Step3Loader 초기화: {step3_dir}")
    
    def load_results(self, version: str = 'final') -> pd.DataFrame:
        """
        Stage 3 결과 로드
        
        Args:
            version: 'final' 또는 '' (기본)
        """
        if version == 'final':
            file_path = self.step3_dir / 'stage3_results_final.csv'
        else:
            file_path = self.step3_dir / 'stage3_results.csv'
        
        if not file_path.exists():
            raise FileNotFoundError(f"파일 없음: {file_path}")
        
        df = pd.read_csv(file_path)
        logger.info(f"Stage 3 결과 로드 ({version}): {len(df)} 행")
        return df
    
    def load_efficiency_summary(self) -> Dict[str, Any]:
        """효율 요약 로드"""
        file_path = self.step3_dir / 'efficiency_summary.json'
        
        if not file_path.exists():
            raise FileNotFoundError(f"파일 없음: {file_path}")
        
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        logger.info("효율 요약 로드 완료")
        return data
    
    def load_efficiency_table(self) -> pd.DataFrame:
        """효율 테이블 로드"""
        file_path = self.step3_dir / 'efficiency_table.csv'
        
        if not file_path.exists():
            raise FileNotFoundError(f"파일 없음: {file_path}")
        
        df = pd.read_csv(file_path)
        logger.info(f"효율 테이블 로드: {len(df)} 행")
        return df
    
    def load_engineer_decisions(self) -> pd.DataFrame:
        """엔지니어 결정 로드"""
        file_path = self.step3_dir / 'engineer_decisions.csv'
        
        if not file_path.exists():
            raise FileNotFoundError(f"파일 없음: {file_path}")
        
        df = pd.read_csv(file_path)
        logger.info(f"엔지니어 결정 로드: {len(df)} 행")
        return df
    
    def load_defect_to_action_mapping(self, version: str = 'default') -> Dict[str, Any]:
        """
        결함 → 조치 매핑 로드
        
        Args:
            version: 'default' 또는 'data_driven'
        """
        if version == 'data_driven':
            file_path = self.step3_dir / 'defect_to_action_mapping_data_driven.json'
        else:
            file_path = self.step3_dir / 'defect_to_action_mapping.json'
        
        if not file_path.exists():
            logger.warning(f"매핑 파일 없음: {file_path}")
            return {}
        
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        return data
    
    def load_config(self) -> Dict[str, Any]:
        """Stage 3 설정 로드"""
        file_path = self.step3_dir / 'stage3_config.json'
        
        if not file_path.exists():
            return {}
        
        with open(file_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    
    def get_operational_metrics(self) -> Dict[str, Any]:
        """운영 메트릭 종합"""
        metrics = {}
        
        # 효율 요약
        try:
            efficiency = self.load_efficiency_summary()
            metrics['efficiency'] = efficiency
        except FileNotFoundError:
            logger.warning("효율 요약 없음")
        
        # 결과 분석
        try:
            results_df = self.load_results('final')
            
            # Triage 분포
            if 'triage' in results_df.columns:
                triage_dist = results_df['triage'].value_counts().to_dict()
                metrics['triage_distribution'] = triage_dist
            
            # 결정 분포
            if 'engineer_decision' in results_df.columns:
                decision_dist = results_df['engineer_decision'].value_counts().to_dict()
                metrics['decision_distribution'] = decision_dist
            
            metrics['total_cases'] = len(results_df)
        except FileNotFoundError:
            logger.warning("결과 없음")
        
        return metrics
    
    def get_summary(self) -> Dict[str, Any]:
        """로드된 데이터 요약"""
        summary = {
            'step3_dir': str(self.step3_dir),
            'operational_metrics': self.get_operational_metrics(),
            'available_files': []
        }
        
        # 사용 가능한 파일 목록
        for f in self.step3_dir.iterdir():
            if f.is_file():
                summary['available_files'].append(f.name)
        
        return summary


def load_step3_artifacts(step3_dir: str) -> Dict[str, Any]:
    """
    Step 3 아티팩트 로드 헬퍼 함수
    
    Args:
        step3_dir: STEP 3 디렉토리 경로
    
    Returns:
        아티팩트 딕셔너리
    """
    loader = Step3Loader(Path(step3_dir))
    
    artifacts = {
        'loader': loader,
        'results': None,
        'results_final': None,
        'efficiency_summary': None,
        'efficiency_table': None,
        'engineer_decisions': None,
        'defect_mapping': None,
        'operational_metrics': None
    }
    
    try:
        artifacts['results'] = loader.load_results('')
    except FileNotFoundError:
        pass
    
    try:
        artifacts['results_final'] = loader.load_results('final')
    except FileNotFoundError:
        logger.warning("최종 결과 없음")
    
    try:
        artifacts['efficiency_summary'] = loader.load_efficiency_summary()
    except FileNotFoundError:
        logger.warning("효율 요약 없음")
    
    try:
        artifacts['efficiency_table'] = loader.load_efficiency_table()
    except FileNotFoundError:
        logger.warning("효율 테이블 없음")
    
    try:
        artifacts['engineer_decisions'] = loader.load_engineer_decisions()
    except FileNotFoundError:
        logger.warning("엔지니어 결정 없음")
    
    artifacts['defect_mapping'] = loader.load_defect_to_action_mapping()
    artifacts['operational_metrics'] = loader.get_operational_metrics()
    
    return artifacts
