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
│   └── outputs/                 # Output data (analysis results, reports)
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
├── streamlit_app/               # Streamlit web application
│   ├── app.py                   # Main application entry point
│   ├── pages/                   # Multi-page app pages
│   └── components/              # Reusable UI components
├── notebooks/                   # Jupyter notebooks for exploration
└── scripts/                     # Utility scripts
```

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

## Git Workflow (Commit & Push)

한글 커밋 메시지가 GitHub에서 깨지지 않도록 인코딩을 설정한 뒤, 커밋·푸시하면 됩니다.

### 1. 인코딩 설정 (한글 깨짐 방지)

최초 한 번만 설정하면 됩니다.

```bash
# 커밋 메시지를 UTF-8로 저장
git config --global i18n.commitEncoding utf-8

# 로그 출력을 UTF-8로 표시
git config --global i18n.logOutputEncoding utf-8

# Windows: 한글 파일명/경로 깨짐 방지
git config --global core.quotepath false
```

### 2. 일반적인 커밋 & 푸시

```bash
# 변경 파일 스테이징
git add .

# 또는 특정 파일만
git add README.md streamlit_app/app.py

# 커밋 (한글 메시지 사용 가능)
git commit -m "feat: Paper Agent 입력 가이드 추가"

# 원격 저장소로 푸시
git push origin main
```

### 3. 방금 한 커밋 메시지 수정 후 푸시

이미 `git commit` 했는데 메시지를 바꾸고 싶을 때:

```bash
# 가장 최근 커밋 메시지 수정 (에디터 열림)
git commit --amend

# 또는 한 줄로 메시지 지정
git commit --amend -m "feat: Paper Agent 입력 가이드 추가"

# 이미 push 했다면 강제 푸시 (main 브랜치 히스토리 변경됨)
git push --force origin main
```

**주의:** `git push --force`는 원격 브랜치 히스토리를 덮어씁니다. 다른 사람과 같은 브랜치를 쓰면 사전에 합의하는 것이 좋습니다.

### 4. 인코딩 설정 후 이미 깨진 커밋 고치기

과거 커밋 메시지가 한글 깨짐으로 저장된 경우:

1. 위 **1번**대로 인코딩 설정
2. **3번**대로 `git commit --amend -m "올바른 한글 메시지"` 로 수정
3. `git push --force origin main` 으로 푸시

### 5. 상태 확인

```bash
# 변경/스테이징 상태 확인
git status

# 최근 커밋 로그 (한글이 제대로 보이는지 확인)
git log -1 --oneline
```

---

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
