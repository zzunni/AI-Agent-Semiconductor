"""
Track B Step 2 Loader
STEP 2 (Stage 2B - Wafermap Pattern) 아티팩트 로더
"""

from typing import Dict, Any, Optional
from pathlib import Path
import pandas as pd
import json
import logging

logger = logging.getLogger(__name__)


class Step2Loader:
    """
    STEP 2 아티팩트 로더
    Wafermap 패턴 분류 모델 및 결과 로드
    """
    
    def __init__(self, step2_dir: Path):
        """
        Args:
            step2_dir: STEP 2 아티팩트 디렉토리 (data/step2/)
        """
        self.step2_dir = Path(step2_dir)
        if not self.step2_dir.exists():
            raise FileNotFoundError(f"STEP 2 디렉토리가 존재하지 않습니다: {step2_dir}")
        
        logger.info(f"Step2Loader 초기화: {step2_dir}")
    
    def load_test_accuracy_summary(self) -> Dict[str, Any]:
        """테스트 정확도 요약 로드"""
        file_path = self.step2_dir / 'test_accuracy_summary.json'
        
        if not file_path.exists():
            raise FileNotFoundError(f"파일 없음: {file_path}")
        
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        logger.info(f"테스트 정확도 로드: accuracy={data.get('test_accuracy', 'N/A')}")
        return data
    
    def load_test_classification_report(self) -> pd.DataFrame:
        """테스트 분류 리포트 로드"""
        file_path = self.step2_dir / 'test_classification_report.csv'
        
        if not file_path.exists():
            raise FileNotFoundError(f"파일 없음: {file_path}")
        
        df = pd.read_csv(file_path)
        logger.info(f"분류 리포트 로드: {len(df)} 행")
        return df
    
    def load_test_confusion_matrix(self) -> pd.DataFrame:
        """테스트 혼동 행렬 로드"""
        file_path = self.step2_dir / 'test_confusion_matrix.csv'
        
        if not file_path.exists():
            raise FileNotFoundError(f"파일 없음: {file_path}")
        
        df = pd.read_csv(file_path)
        logger.info(f"혼동 행렬 로드: {df.shape}")
        return df
    
    def load_stage2b_results(self) -> pd.DataFrame:
        """Stage 2B 결과 로드"""
        file_path = self.step2_dir / 'stage2b_results.csv'
        
        if not file_path.exists():
            raise FileNotFoundError(f"파일 없음: {file_path}")
        
        df = pd.read_csv(file_path)
        logger.info(f"Stage 2B 결과 로드: {len(df)} 행")
        return df
    
    def load_severity_scores(self, subset: str = 'all') -> pd.DataFrame:
        """
        Severity scores 로드
        
        Args:
            subset: 'all' 또는 'test'
        """
        file_name = f'severity_scores_{subset}.csv'
        file_path = self.step2_dir / file_name
        
        if not file_path.exists():
            raise FileNotFoundError(f"파일 없음: {file_path}")
        
        df = pd.read_csv(file_path)
        logger.info(f"Severity scores 로드 ({subset}): {len(df)} 행")
        return df
    
    def load_sem_candidates(self, top_p: str = '10pct') -> pd.DataFrame:
        """SEM 후보 로드"""
        file_name = f'sem_candidates_top{top_p}.csv'
        file_path = self.step2_dir / file_name
        
        if not file_path.exists():
            # 대안 시도
            file_name = f'sem_send_top{top_p}.csv'
            file_path = self.step2_dir / file_name
            
            if not file_path.exists():
                raise FileNotFoundError(f"SEM 후보 파일 없음")
        
        df = pd.read_csv(file_path)
        logger.info(f"SEM 후보 로드 ({top_p}): {len(df)} 행")
        return df
    
    def load_classes(self) -> Dict[str, Any]:
        """클래스 정의 로드"""
        file_path = self.step2_dir / 'classes.json'
        
        if not file_path.exists():
            logger.warning(f"클래스 파일 없음: {file_path}")
            return {}
        
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        return data
    
    def load_pattern_to_process_mapping(self) -> Dict[str, Any]:
        """패턴 → 프로세스 매핑 로드"""
        file_path = self.step2_dir / 'pattern_to_process_mapping.json'
        
        if not file_path.exists():
            logger.warning(f"매핑 파일 없음: {file_path}")
            return {}
        
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        return data
    
    def load_config(self) -> Dict[str, Any]:
        """Stage 2B 설정 로드"""
        file_path = self.step2_dir / 'stage2b_config.json'
        
        if not file_path.exists():
            return {}
        
        with open(file_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    
    def get_test_metrics(self) -> Dict[str, Any]:
        """테스트 메트릭 종합"""
        metrics = {}
        
        # 정확도 요약
        try:
            accuracy_summary = self.load_test_accuracy_summary()
            metrics['accuracy'] = accuracy_summary.get('test_accuracy')
            metrics['num_test_samples'] = accuracy_summary.get('num_test_samples')
            metrics['num_classes'] = accuracy_summary.get('num_classes')
        except FileNotFoundError:
            logger.warning("정확도 요약 없음")
        
        # 분류 리포트에서 macro F1
        try:
            report_df = self.load_test_classification_report()
            if 'f1-score' in report_df.columns:
                # 마지막 행이 보통 macro avg
                metrics['macro_f1'] = report_df['f1-score'].iloc[-1]
        except FileNotFoundError:
            logger.warning("분류 리포트 없음")
        
        return metrics
    
    def get_summary(self) -> Dict[str, Any]:
        """로드된 데이터 요약"""
        summary = {
            'step2_dir': str(self.step2_dir),
            'test_metrics': self.get_test_metrics(),
            'available_files': []
        }
        
        # 사용 가능한 파일 목록
        for f in self.step2_dir.iterdir():
            if f.is_file():
                summary['available_files'].append(f.name)
        
        return summary


def load_step2_artifacts(step2_dir: str) -> Dict[str, Any]:
    """
    Step 2 아티팩트 로드 헬퍼 함수
    
    Args:
        step2_dir: STEP 2 디렉토리 경로
    
    Returns:
        아티팩트 딕셔너리
    """
    loader = Step2Loader(Path(step2_dir))
    
    artifacts = {
        'loader': loader,
        'test_accuracy_summary': None,
        'test_classification_report': None,
        'test_confusion_matrix': None,
        'stage2b_results': None,
        'severity_scores': None,
        'classes': None,
        'pattern_mapping': None,
        'test_metrics': None
    }
    
    try:
        artifacts['test_accuracy_summary'] = loader.load_test_accuracy_summary()
    except FileNotFoundError:
        logger.warning("테스트 정확도 요약 없음")
    
    try:
        artifacts['test_classification_report'] = loader.load_test_classification_report()
    except FileNotFoundError:
        logger.warning("분류 리포트 없음")
    
    try:
        artifacts['test_confusion_matrix'] = loader.load_test_confusion_matrix()
    except FileNotFoundError:
        logger.warning("혼동 행렬 없음")
    
    try:
        artifacts['stage2b_results'] = loader.load_stage2b_results()
    except FileNotFoundError:
        logger.warning("Stage 2B 결과 없음")
    
    try:
        artifacts['severity_scores'] = loader.load_severity_scores('all')
    except FileNotFoundError:
        logger.warning("Severity scores 없음")
    
    artifacts['classes'] = loader.load_classes()
    artifacts['pattern_mapping'] = loader.load_pattern_to_process_mapping()
    artifacts['test_metrics'] = loader.get_test_metrics()
    
    return artifacts
