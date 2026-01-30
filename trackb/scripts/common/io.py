"""
Track B I/O Utilities
파일 경로 해석 및 파일 발견 유틸리티
"""

from pathlib import Path
import json
import glob
import hashlib
import pandas as pd
import logging
from typing import Optional, List, Dict, Any, Union

logger = logging.getLogger(__name__)


class PathResolver:
    """설정 기반 경로 해석기"""
    
    def __init__(self, config_path: Optional[str] = None):
        """
        Args:
            config_path: 설정 파일 경로 (None이면 기본 경로 사용)
        """
        if config_path is None:
            # trackb/scripts/common에서 실행될 때 기준
            base_dir = Path(__file__).parent.parent.parent
            config_path = base_dir / 'configs' / 'trackb_config.json'
        
        config_path = Path(config_path)
        if not config_path.exists():
            raise FileNotFoundError(f"설정 파일을 찾을 수 없습니다: {config_path}")
        
        with open(config_path, encoding='utf-8') as f:
            self.config = json.load(f)
        
        self.paths = self.config.get('paths', {})
        self.base_dir = config_path.parent.parent  # trackb/ 디렉토리
    
    def resolve(self, key: str) -> Path:
        """
        설정에서 경로 해석
        
        Args:
            key: 경로 키 (예: 'step1_artifacts')
        
        Returns:
            해석된 Path 객체
        
        Raises:
            FileNotFoundError: 경로를 찾을 수 없을 때
        """
        path_str = self.paths.get(key)
        if path_str:
            # 상대 경로 처리
            p = Path(path_str)
            if not p.is_absolute():
                p = self.base_dir / p
            
            if p.exists():
                return p.resolve()
        
        # 자동 탐색 시도
        return self._auto_discover(key)
    
    def _auto_discover(self, key: str) -> Path:
        """경로 자동 탐색"""
        search_map = {
            'step1_artifacts': [
                'data/step1/', '../data/step1/',
                'step1/', '../step1/'
            ],
            'step2_artifacts': [
                'data/step2/', '../data/step2/',
                'step2/', '../step2/'
            ],
            'step3_artifacts': [
                'data/step3/', '../data/step3/',
                'step3/', '../step3/'
            ],
            'trackb_outputs': [
                'outputs/', './outputs/'
            ]
        }
        
        candidates = search_map.get(key, [])
        
        for candidate in candidates:
            p = self.base_dir / candidate
            if p.exists():
                logger.warning(f"⚠️ 자동 탐색으로 {key} 발견: {p}")
                return p.resolve()
        
        raise FileNotFoundError(
            f"{key}를 찾을 수 없습니다. "
            f"검색 위치: {candidates}"
        )
    
    def get_config(self, *keys: str) -> Any:
        """
        중첩된 설정 값 가져오기
        
        Args:
            keys: 설정 키 경로 (예: 'agent', 'budget_total')
        
        Returns:
            설정 값
        """
        result = self.config
        for key in keys:
            if isinstance(result, dict):
                result = result.get(key)
            else:
                return None
        return result


def find_file(pattern: str, base_dir: Optional[Path] = None, 
              raise_if_missing: bool = True) -> Optional[Path]:
    """
    패턴에 맞는 파일 찾기 (한글 파일명 지원)
    
    Args:
        pattern: glob 패턴
        base_dir: 기준 디렉토리 (None이면 현재)
        raise_if_missing: True면 파일 없을 때 예외 발생
    
    Returns:
        가장 최근 수정된 파일 경로
    
    Raises:
        FileNotFoundError: 파일이 없고 raise_if_missing=True일 때
    """
    if base_dir:
        full_pattern = str(base_dir / pattern)
    else:
        full_pattern = pattern
    
    files = glob.glob(full_pattern)
    
    if not files:
        if raise_if_missing:
            raise FileNotFoundError(f"파일을 찾을 수 없습니다: {full_pattern}")
        return None
    
    # 가장 최근 수정된 파일 반환
    latest = max(files, key=lambda x: Path(x).stat().st_mtime)
    return Path(latest)


def find_files(pattern: str, base_dir: Optional[Path] = None) -> List[Path]:
    """
    패턴에 맞는 모든 파일 찾기
    
    Args:
        pattern: glob 패턴
        base_dir: 기준 디렉토리
    
    Returns:
        파일 경로 리스트 (수정 시간 역순 정렬)
    """
    if base_dir:
        full_pattern = str(base_dir / pattern)
    else:
        full_pattern = pattern
    
    files = glob.glob(full_pattern)
    
    # 수정 시간 역순 정렬
    files = sorted(files, key=lambda x: Path(x).stat().st_mtime, reverse=True)
    return [Path(f) for f in files]


def compute_file_hash(file_path: Path) -> str:
    """파일 SHA256 해시 계산"""
    sha256 = hashlib.sha256()
    with open(file_path, 'rb') as f:
        for chunk in iter(lambda: f.read(8192), b''):
            sha256.update(chunk)
    return sha256.hexdigest()


def compute_manifest(
    input_files: List[Union[str, Path]],
    output_files: List[Union[str, Path]],
    config: Optional[Dict] = None
) -> Dict[str, Any]:
    """
    재현성 매니페스트 생성
    
    Args:
        input_files: 입력 파일 경로 리스트
        output_files: 출력 파일 경로 리스트
        config: 설정 정보 (선택)
    
    Returns:
        매니페스트 딕셔너리
    """
    manifest = {
        'version': '1.0',
        'timestamp': pd.Timestamp.now().isoformat(),
        'inputs': [],
        'outputs': [],
        'config_snapshot': config
    }
    
    # 입력 파일 처리
    for f in input_files:
        p = Path(f)
        if p.exists():
            file_info = {
                'path': str(p),
                'sha256': compute_file_hash(p),
                'size_bytes': p.stat().st_size,
                'mtime': pd.Timestamp.fromtimestamp(p.stat().st_mtime).isoformat()
            }
            manifest['inputs'].append(file_info)
        else:
            logger.warning(f"입력 파일이 존재하지 않습니다: {p}")
    
    # 출력 파일 처리
    for f in output_files:
        p = Path(f)
        if p.exists():
            file_info = {
                'path': str(p),
                'sha256': compute_file_hash(p),
                'size_bytes': p.stat().st_size,
                'mtime': pd.Timestamp.fromtimestamp(p.stat().st_mtime).isoformat()
            }
            
            # CSV 파일이면 행 수 추가
            if str(p).endswith('.csv'):
                try:
                    df = pd.read_csv(p)
                    file_info['row_count'] = len(df)
                    file_info['columns'] = list(df.columns)
                except Exception as e:
                    logger.warning(f"CSV 읽기 실패: {p}, {e}")
            
            manifest['outputs'].append(file_info)
        else:
            logger.warning(f"출력 파일이 존재하지 않습니다: {p}")
    
    return manifest


def save_manifest(manifest: Dict, output_path: Path) -> None:
    """매니페스트 JSON 저장"""
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(manifest, f, ensure_ascii=False, indent=2)
    logger.info(f"매니페스트 저장됨: {output_path}")


def load_csv_safe(file_path: Union[str, Path], **kwargs) -> pd.DataFrame:
    """
    CSV 안전하게 로드 (한글 파일명 지원)
    
    Args:
        file_path: 파일 경로
        **kwargs: pd.read_csv에 전달할 인자
    
    Returns:
        DataFrame
    """
    file_path = Path(file_path)
    
    # 인코딩 시도 순서
    encodings = ['utf-8', 'cp949', 'euc-kr', 'utf-8-sig']
    
    for encoding in encodings:
        try:
            df = pd.read_csv(file_path, encoding=encoding, **kwargs)
            logger.debug(f"CSV 로드 성공 ({encoding}): {file_path}")
            return df
        except UnicodeDecodeError:
            continue
        except Exception as e:
            raise
    
    raise ValueError(f"CSV 파일을 읽을 수 없습니다: {file_path}")


def save_csv_safe(df: pd.DataFrame, file_path: Union[str, Path], 
                  index: bool = False) -> None:
    """CSV 안전하게 저장"""
    file_path = Path(file_path)
    file_path.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(file_path, index=index, encoding='utf-8-sig')
    logger.info(f"CSV 저장됨: {file_path} ({len(df)} 행)")


def load_json_safe(file_path: Union[str, Path]) -> Dict:
    """JSON 안전하게 로드"""
    file_path = Path(file_path)
    with open(file_path, 'r', encoding='utf-8') as f:
        return json.load(f)


class NumpyEncoder(json.JSONEncoder):
    """Numpy 타입 JSON 인코더"""
    def default(self, obj):
        import numpy as np
        if isinstance(obj, np.integer):
            return int(obj)
        elif isinstance(obj, np.floating):
            return float(obj)
        elif isinstance(obj, np.ndarray):
            return obj.tolist()
        elif isinstance(obj, np.bool_):
            return bool(obj)
        return super().default(obj)


def save_json_safe(data: Dict, file_path: Union[str, Path]) -> None:
    """JSON 안전하게 저장 (numpy 타입 지원)"""
    file_path = Path(file_path)
    file_path.parent.mkdir(parents=True, exist_ok=True)
    with open(file_path, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2, cls=NumpyEncoder)
    logger.info(f"JSON 저장됨: {file_path}")
