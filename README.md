# AI-Driven Semiconductor Quality Control System

Multi-stage inspection pipeline with economic optimization for semiconductor wafer quality control.

## Overview

This project implements an AI-powered quality control system for semiconductor manufacturing that combines machine learning models with large language models for cost-aware inspection routing. The system uses a 4-stage pipeline to progressively analyze wafer defects while optimizing inspection costs through intelligent decision-making at each stage.

## Tech Stack

- **Python**: 3.9+
- **AI/LLM**: Anthropic Claude (claude-sonnet-4-20250514)
- **Web Interface**: Streamlit 1.30.0
- **Machine Learning**: scikit-learn 1.3.2, XGBoost 2.0.1
- **Data Processing**: pandas 2.0.3, numpy 1.24.3
- **Visualization**: plotly 5.18.0

## Project Structure

```
ai-agent-semiconductor/
├── README.md                    # Project documentation
├── requirements.txt             # Python dependencies
├── config.yaml                  # Configuration settings
├── .env.example                 # Environment variables template
├── .gitignore                   # Git ignore rules
├── data/                        # Data directory
│   ├── inputs/                  # Input data (wafer images, inspection data)
│   ├── outputs/                 # Output data (analysis results, reports)
│   ├── step1/                   # Step1 artifacts (Stage 0-2A)
│   ├── step2/                   # Step2 artifacts (WM-811K benchmark)
│   └── step3/                   # Step3 artifacts (Carinthia benchmark)
├── models/                      # Trained ML models
├── logs/                        # Application logs
│   ├── pattern_discovery/       # Pattern discovery logs
│   ├── root_cause_analysis/     # Root cause analysis logs
│   └── learning_feedback/       # Learning feedback logs
├── src/                         # Source code
│   ├── agents/                  # AI agent implementations
│   ├── pipeline/                # Processing pipeline
│   ├── llm/                     # LLM integration
│   └── utils/                   # Utility functions
├── streamlit_app/               # Streamlit web application (Track A)
│   ├── app.py                   # Main application entry point
│   ├── pages/                   # Multi-page app pages
│   └── utils/                   # UI components
├── trackb/                      # Track B: Scientific validation pipeline
│   ├── scripts/                 # Validation scripts
│   ├── outputs/                 # Run-isolated outputs
│   ├── configs/                 # Pipeline configuration
│   └── docs/                    # Documentation
├── notebooks/                   # Jupyter notebooks for exploration
└── scripts/                     # Utility scripts
```

## Repository Structure

이 저장소는 두 개의 주요 트랙으로 구성됩니다:

- **Track A (streamlit_app/)**: 운영용 웹 인터페이스 및 실시간 모니터링
- **Track B (trackb/)**: 과학적 검증 파이프라인 및 논문 생성용 보고서

### Track B: Scientific Validation Pipeline

Track B는 AI 기반 반도체 검사 프레임워크의 과학적 검증을 위한 자동화된 파이프라인입니다.

**주요 특징**:
- ✅ **Core/Appendix 분리**: Step1 (yield_true GT validated) vs Step2/3 (proxy benchmark-only)
- ✅ **정규화 비용 단위**: 절대 금액 사용 금지, normalized units만 사용
- ✅ **Run isolation**: 각 실행마다 독립된 출력 디렉토리 (SHA256 manifest 포함)
- ✅ **증거 게이트**: Proxy validation FAILED 시 Core 승격 차단
- ✅ **자동 검증**: compileall → static_check → pipeline → verify → adversarial tests

**빠른 시작**:
```bash
cd trackb/scripts
python run_full_e2e.py  # Full E2E: compileall → static → run → verify → adversarial
```

**주요 산출물** (`trackb/outputs/run_YYYYMMDD_HHMMSS/reports/`):
- `trackB_report_core_validated.md`: Step1 Core 결과 (yield_true GT 기반)
- `trackB_report_appendix_proxy.md`: Step2/3 Proxy 결과 (benchmark-only)
- `FINAL_VALIDATION.md`: Q1–Q6 종합 검증 + verdict
- `paper_bundle.json`: 논문 생성 AI Agent용 입력 번들

상세 문서: [trackb/README.md](trackb/README.md), [trackb/docs/runbook.md](trackb/docs/runbook.md)

---

## Features

### 4-Stage Inspection Pipeline

The system uses a progressive inspection approach with specialized models at each stage:

1. **Stage 0: Anomaly Detection** (Isolation Forest)
   - Initial screening of wafer data to identify potential anomalies
   - Risk-based classification (high, medium, low risk)
   - Determines which wafers need further inspection

2. **Stage 1: Risk Assessment** (XGBoost)
   - Economic decision-making: inline inspection vs. rework vs. pass
   - Cost-benefit analysis considering wafer value and rework costs
   - Routes high-risk wafers to detailed inspection

3. **Stage 2b: Severity Analysis** (CNN)
   - Deep learning-based defect severity assessment
   - Determines if expensive SEM inspection is justified
   - Optimizes use of limited SEM inspection budget

4. **Stage 3: Detailed Classification** (ResNet)
   - Fine-grained defect classification and root cause analysis
   - LLM-powered pattern discovery and recommendations
   - Generates actionable insights for process improvement

### Economic Optimization

- **Budget Management**: Tracks monthly inspection budgets for inline and SEM inspection
- **Cost-Aware Routing**: Routes wafers to appropriate inspection based on cost-benefit analysis
- **ROI Maximization**: Optimizes inspection decisions to maximize value within budget constraints

### Intelligence & Learning

- **Pattern Discovery**: Statistical analysis to identify recurring defect patterns (14-day lookback)
- **Continuous Learning**: Feedback-based model improvement (minimum 50 samples)
- **LLM Integration**: Claude for root cause analysis and recommendations

## Installation

### Prerequisites

- Python 3.9 or higher
- pip package manager
- Anthropic API key ([Get one here](https://console.anthropic.com/))

### Setup

1. Clone the repository:
```bash
git clone <repository-url>
cd ai-agent-semiconductor
```

2. Create a virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Configure environment variables:
```bash
cp .env.example .env
# Edit .env and add your ANTHROPIC_API_KEY
```

5. Review and customize configuration:
```bash
# Edit config.yaml to adjust model settings and pipeline parameters
```

## Usage

### Running the Streamlit Application

```bash
streamlit run streamlit_app/app.py
```

The application will be available at `http://localhost:8501`

### Using the Python API

```python
from src.agents import PatternDiscoveryAgent
from src.pipeline import QualityControlPipeline

# Initialize pipeline
pipeline = QualityControlPipeline()

# Process wafer inspection data
results = pipeline.process(input_data)
```

## Configuration

### Model Settings

Edit [config.yaml](config.yaml) to configure:
- **Budget**: Monthly budgets and per-wafer costs for inline/SEM inspection
- **Stage Models**: Paths and thresholds for each ML model (Isolation Forest, XGBoost, CNN, ResNet)
- **LLM Settings**: Claude model configuration (temperature, max_tokens)
- **Discovery**: Pattern discovery parameters (lookback days, significance threshold)
- **Learning**: Feedback-based learning settings (minimum samples)
- **Simulation**: Engineer approval rates for rough vs. detailed analysis

### Environment Variables

Key environment variables in [.env](.env):
- `ANTHROPIC_API_KEY`: Your Anthropic API key (required)

All other configuration is centralized in [config.yaml](config.yaml) for easier management.

## Development

### Adding New Features

1. Create new modules in appropriate `src/` subdirectories
2. Update configuration in `config.yaml` if needed
3. Add tests for new functionality
4. Update documentation

### Logging

Logs are organized by functionality:
- Pattern discovery: `logs/pattern_discovery/`
- Root cause analysis: `logs/root_cause_analysis/`
- Learning feedback: `logs/learning_feedback/`

## Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Acknowledgments

- Built with [Anthropic Claude](https://www.anthropic.com/claude)
- Powered by [Streamlit](https://streamlit.io/)

## Support

For questions or issues, please open an issue on the GitHub repository.
