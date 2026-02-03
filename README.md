# AI 기반 반도체 품질 관리 시스템

반도체 웨이퍼 품질 관리를 위한 다단계 검사 파이프라인과 경제적 최적화를 제공합니다. **Track A**는 운영용 웹 UI와 Human-in-the-Loop 워크플로우를, **Track B**는 과학적 검증과 보고서 생성을 담당합니다.

## 개요

본 프로젝트는 반도체 제조 현장에서 머신러닝 모델과 대규모 언어 모델(LLM)을 결합해, **비용을 고려한 검사 라우팅**을 수행하는 AI 품질 관리 시스템을 구현합니다. **5단계 파이프라인**(Stage 0 → 1 → 2A → 2B → 3)으로 웨이퍼 결함을 단계적으로 분석하며, 각 단계에서 지능형 의사결정을 통해 검사 비용을 최적화합니다.

**이원화 아키텍처**

- **Track A (운영 워크플로우):** 웹 데모, LOT 모니터링, 의사결정 큐, 예산 추적. 엔지니어가 AI 권고와 어떻게 상호작용하는지 시연합니다. [streamlit_app/](streamlit_app/) 참고.
- **Track B (주장 경계):** 배치 검증 파이프라인, 동일 웨이퍼 기반 실험, 자동 보고서 생성. 검증된 Core(Step1)와 Proxy 벤치마크(Step2/3)를 구분합니다. [trackb/](trackb/README.md) 참고.

![이원화 거버넌스 아키텍처](Two-layer_Governance_Architecture.svg)

## 기술 스택

- **Python**: 3.9+
- **AI/LLM**: Anthropic Claude (claude-sonnet-4-20250514)
- **웹 인터페이스**: Streamlit 1.30.0
- **머신러닝**: scikit-learn 1.3.2, XGBoost 2.0.1
- **데이터 처리**: pandas 2.0.3, numpy 1.24.3
- **시각화**: plotly 5.18.0

## 프로젝트 구조

```
ai-agent-semiconductor/
├── README.md                           # 프로젝트 문서
├── Two-layer_Governance_Architecture.svg  # Track A vs Track B 아키텍처 다이어그램
├── requirements.txt                    # Python 의존성
├── config.yaml                         # 설정 (예산, 모델, LLM 등)
├── .env.example                        # 환경 변수 템플릿
├── .gitignore
├── data/                               # 데이터 디렉터리
│   ├── inputs/                         # 입력 (웨이퍼 이미지, 검사 데이터)
│   ├── outputs/                        # 출력 (분석 결과, 보고서)
│   ├── step1/                          # Stage 0/1/2A 산출물 (리스크 점수, 모델)
│   ├── step2/                          # Stage 2B 산출물 (웨이퍼맵, WM-811K)
│   └── step3/                          # Stage 3 산출물 (SEM, 결함 매핑)
├── models/                             # 학습된 ML 모델
├── logs/                               # 애플리케이션 로그
├── src/                                # 소스 코드
│   ├── agents/                         # Stage 0~3 에이전트, discovery, learning
│   ├── pipeline/                      # 파이프라인 컨트롤러
│   ├── llm/                            # LLM 연동 (Claude)
│   └── utils/                          # 데이터 로더, 로거, 메트릭
├── streamlit_app/                      # Track A: 웹 UI (Human-AI 협업)
│   ├── app.py                          # 대시보드 홈
│   ├── pages/                          # 생산 모니터, 의사결정 큐, AI 인사이트
│   └── utils/                          # 웨이퍼 처리, 스테이지 실행, UI 컴포넌트
├── trackb/                             # Track B: 과학적 검증 파이프라인
│   ├── scripts/                        # trackb_run.py, compile, static_check, verify
│   ├── configs/                        # trackb_config.json
│   ├── outputs/run_*/reports/          # 마크다운/JSON 보고서 (Core, Proxy, PAPER_AGENT_INPUT_GUIDE)
│   └── README.md                       # Track B 빠른 시작 및 검증 상태
├── notebooks/
└── scripts/                            # 테스트 스크립트, 목 데이터 생성
```

## 주요 기능

### 5단계 검사 파이프라인

각 단계별 전용 모델로 점진적 검사를 수행합니다.

**Phase 1 (인라인, 리워크 가능)**

1. **Stage 0: 이상 탐지** (Isolation Forest)
   - 웨이퍼 센서 데이터(etch_rate, pressure, temperature 등) 초기 스크리닝
   - 위험도 분류(고/중/저)
   - 결정: INLINE(인라인 검사 진행) 또는 SKIP(웨이퍼 완료)

2. **Stage 1: 수율 예측 및 인라인 검사** (XGBoost)
   - 인라인 측정값(CD 균일도, 막 두께, 라인 폭, 에지 비드 등)
   - 경제적 결정: SKIP / PROCEED / REWORK(새 센서 데이터) / SCRAP
   - 리워크: 약 70% 개선 확률; 비용은 정규화 단위로 추적

**Phase 2 (포스트팹, 리워크 불가)**

3. **Stage 2A: WAT(웨이퍼 수용 테스트)**
   - 전기 테스트 데이터(전기 균일도, 접촉 저항, 누설 전류, 항복 전압 등)
   - 결정: SKIP 또는 패턴 분석으로 PROCEED

4. **Stage 2B: 웨이퍼맵 패턴 분석** (CNN)
   - 결함 맵(패턴 유형, 심각도). 벤치마크: WM-811K(프록시).
   - 결정: SKIP 또는 근본 원인(SEM) 분석으로 PROCEED

5. **Stage 3: 근본 원인 분석** (SEM + LLM)
   - SEM 촬영(파괴 검사 → 웨이퍼 스크랩). LLM 근본 원인 보고서(한국어).
   - 벤치마크: Carinthia(프록시). 결정: COMPLETE 또는 INVESTIGATE

### Track A: 운영 워크플로우 (웹 UI)

- **생산 모니터:** LOT 진행(25장/LOT), 센서 스트림, 알림, 웨이퍼 상태(대기/처리 중/결정 대기/완료/스크랩), 리워크 뱃지, 수율 요약
- **의사결정 큐:** 단계별 AI 권고, 설명(근거·경제성·웨이퍼맵/SEM 시각화), 원클릭 액션(INLINE, SKIP, REWORK, PROCEED, SCRAP, COMPLETE), 감사 추적
- **AI 인사이트:** 패턴 발견(센서–패턴 상관, p<0.01), Stage 3 근본 원인 저장소, 엔지니어 피드백 학습(동의율, 비용/신뢰도 패턴)
- **예산 모니터:** 인라인/SEM/리워크 비용 추적(정규화 단위), 진행률, 상한

### Track B: 과학적 검증

- **Step1 Core(검증됨):** 동일 웨이퍼 ground truth, N=200, selection_rate=10%, high-risk=하위 20%. Bootstrap 95% CI(Recall@10%, 정규화 비용). 메인 결과만 사용.
- **Step2/3 Proxy(벤치마크):** WM-811K(웨이퍼맵), Carinthia(SEM). 능력 벤치마크로 보고; wafer_id 공유 없음. 부록 전용.
- **산출물:** `trackb/outputs/run_*/reports/` — `trackB_report_core_validated.md`, `trackB_report_appendix_proxy.md`, `PAPER_AGENT_INPUT_GUIDE.md`, `paper_bundle.json` 등

### 경제적 최적화

- **예산 관리:** 인라인/SEM/리워크 비용을 정규화 단위로 추적(통화 단위 주장 없음)
- **비용 인식 라우팅:** 단계별 비용·효익에 따라 웨이퍼 라우팅
- **Evidence Gate:** 메인 결과에는 Core 지표만; Proxy 벤치마크는 부록만

### 지능 및 학습

- **패턴 발견:** 통계 분석(14일 lookback), LLM 해석(한국어)
- **지속 학습:** 엔지니어 피드백 로깅, 동의/불일치 패턴
- **LLM 연동:** Claude를 이용한 근본 원인 분석 및 권고(한국어)

## 설치

### 요구 사항

- Python 3.9 이상
- pip
- Anthropic API 키 ([발급](https://console.anthropic.com/))

### 설정

1. 저장소 클론:
```bash
git clone <repository-url>
cd ai-agent-semiconductor
```

2. 가상 환경 생성 및 활성화:
```bash
python -m venv venv
source venv/bin/activate   # Windows: venv\Scripts\activate
```

3. 의존성 설치:
```bash
pip install -r requirements.txt
```

4. 환경 변수 설정:
```bash
cp .env.example .env
# .env에 ANTHROPIC_API_KEY 입력
```

5. [config.yaml](config.yaml)에서 예산·모델·LLM 등 필요 시 수정

## 사용 방법

### Track A: 웹 대시보드 (운영 워크플로우)

```bash
streamlit run streamlit_app/app.py
```

브라우저에서 `http://localhost:8501` 접속.

- **생산 모니터:** 새 LOT(25장) 시작, 순차 처리 확인, 웨이퍼 상태·수율 확인
- **의사결정 큐:** Stage 0~3 AI 권고 확인, 근거·경제성 확인 후 승인/리워크/스크랩 등 원클릭
- **AI 인사이트:** 패턴 발견 실행, 근본 원인 보고서(한국어) 확인, 엔지니어 피드백 분석

### Track B: 검증 파이프라인 (보고서·증거)

```bash
cd trackb
python scripts/run_full_e2e.py   # compile → static_check → trackb_run → verify_outputs → adversarial
# 또는
python scripts/trackb_run.py --mode from_artifacts
```

보고서는 `trackb/outputs/run_YYYYMMDD_HHMMSS/reports/`에 생성됩니다.

- **Core(검증):** `trackB_report_core_validated.md` — Step1 recall, 정규화 비용, bootstrap CI
- **Proxy(벤치마크):** `trackB_report_appendix_proxy.md` — Step2/3 WM-811K, Carinthia
- **논문 입력용:** `PAPER_AGENT_INPUT_GUIDE.md`, `paper_bundle.json` — 논문 생성 AI용

검증 상태 및 빠른 시작은 [trackb/README.md](trackb/README.md) 참고.

### Python API 사용

```python
from src.pipeline.controller import PipelineController
from src.utils.data_loader import DataLoader

controller = PipelineController()
# 풀 UI 워크플로우는 streamlit_app 사용
```

## 주요 산출물 및 보고서

| 산출물 | 위치 | 설명 |
|--------|------|------|
| Track A 데모 | `streamlit_app/` | 웹 UI: 생산 모니터, 의사결정 큐, AI 인사이트 |
| Track B 실행 보고서 | `trackb/outputs/run_*/reports/` | Core 검증 보고서, Proxy 부록, PAPER_AGENT_INPUT_GUIDE |
| 아키텍처 다이어그램 | `Two-layer_Governance_Architecture.svg` | Track A vs Track B, Evidence Gate, 성능 테이블 |
| 논문 번들 | `trackb/outputs/run_*/reports/paper_bundle.json` | 논문 생성 AI용 구조화 메타데이터 |

## 설정

### 모델·예산 설정

[config.yaml](config.yaml)에서 다음을 설정할 수 있습니다.

- **예산:** 인라인/SEM 검사 월 예산 및 웨이퍼당 비용
- **스테이지 모델:** Isolation Forest, XGBoost, CNN, ResNet 경로·임계값
- **LLM:** Claude 모델 설정(temperature, max_tokens)
- **Discovery:** 패턴 발견 lookback 일수, 유의 수준
- **Learning:** 피드백 학습 최소 샘플 수
- **Simulation:** 엔지니어 승인률(대략/상세 분석)

### 환경 변수

[.env](.env)에서 사용하는 주요 변수:

- `ANTHROPIC_API_KEY`: Anthropic API 키(필수)

그 외 설정은 [config.yaml](config.yaml)에서 통합 관리합니다.

## 개발

### 기능 추가 시 참고

1. **Track A(UI):** `streamlit_app/pages/`에 페이지 추가·수정, `streamlit_app/utils/`(wafer_processor, stage_executors, ui_components)에서 로직 수정
2. **Track B(검증):** `trackb/scripts/` 하위 스크립트 추가, `trackb/configs/` 및 보고서 템플릿 수정
3. **파이프라인/에이전트:** `src/agents/`, `src/pipeline/`, `src/llm/` 모듈 추가·수정
4. 필요 시 `config.yaml` 또는 `trackb/configs/` 수정; 테스트는 `scripts/` 또는 `tests/`에 추가

### 로그

- 애플리케이션 로그: `logs/` (Agent-stage*.log, PipelineController.log, llm_client.log)
- Track B 실행 로그: `trackb/outputs/run_*/` (설정에 따라)
- 엔지니어 피드백: `logs/engineer_feedbacks_*.jsonl` (의사결정 큐에서 기록)

## 기여

1. 저장소 Fork
2. 기능 브랜치 생성 (`git checkout -b feature/기능명`)
3. 변경 사항 커밋 (`git commit -m '기능 설명'`)
4. 브랜치 푸시 (`git push origin feature/기능명`)
5. Pull Request 생성

## 라이선스

MIT License. 자세한 내용은 LICENSE 파일을 참고하세요.

## 감사의 말

- [Anthropic Claude](https://www.anthropic.com/claude) 기반
- [Streamlit](https://streamlit.io/) 사용

## 문의

질문이나 이슈는 GitHub 저장소에 이슈를 등록해 주세요.
