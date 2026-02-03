# AI-Driven Semiconductor Quality Control System

Multi-stage inspection pipeline with economic optimization for semiconductor wafer quality control. **Track A** provides the operational web UI and Human-in-the-Loop workflow; **Track B** provides scientific validation and report generation.

## Overview

This project implements an AI-powered quality control system for semiconductor manufacturing that combines machine learning models with large language models for cost-aware inspection routing. The system uses a **5-stage pipeline** (Stage 0 → 1 → 2A → 2B → 3) to progressively analyze wafer defects while optimizing inspection costs through intelligent decision-making at each stage.

**Two-layer architecture:**
- **Track A (Operational Workflow):** Web demo, LOT monitoring, decision queue, budget tracking. Demonstrates how engineers interact with AI recommendations. See [streamlit_app/](streamlit_app/).
- **Track B (Claim Boundary):** Batch validation pipeline, same-wafer ground-truth experiments, automated reports. Validated Core (Step1) + Proxy benchmarks (Step2/3). See [trackb/](trackb/README.md).

![Two-layer Governance Architecture](Two-layer_Governance_Architecture.svg)

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
├── README.md                           # Project documentation
├── Two-layer_Governance_Architecture.svg  # Track A vs Track B architecture diagram
├── requirements.txt                    # Python dependencies
├── config.yaml                         # Configuration settings
├── .env.example                        # Environment variables template
├── .gitignore                          # Git ignore rules
├── data/                               # Data directory
│   ├── inputs/                         # Input data (wafer images, inspection data)
│   ├── outputs/                        # Output data (analysis results, reports)
│   ├── step1/                          # Stage 0/1/2A artifacts (risk scores, models)
│   ├── step2/                          # Stage 2B artifacts (wafermap, WM-811K)
│   └── step3/                          # Stage 3 artifacts (SEM, defect mapping)
├── models/                             # Trained ML models
├── logs/                               # Application logs
├── src/                                # Source code (agents, pipeline, LLM, utils)
│   ├── agents/                         # Stage 0–3 agents, discovery, learning
│   ├── pipeline/                       # Pipeline controller
│   ├── llm/                            # LLM integration (Claude)
│   └── utils/                          # Data loader, logger, metrics
├── streamlit_app/                      # Track A: Web UI (Human-AI collaboration)
│   ├── app.py                          # Dashboard home
│   ├── pages/                          # Production Monitor, Decision Queue, AI Insights
│   └── utils/                          # Wafer processor, stage executors, UI components
├── trackb/                             # Track B: Scientific validation pipeline
│   ├── scripts/                        # trackb_run.py, compile, static_check, verify
│   ├── configs/                        # trackb_config.json
│   ├── outputs/run_*/reports/          # Markdown/JSON reports (Core, Proxy, PAPER_AGENT_INPUT_GUIDE)
│   └── README.md                       # Track B quick start and validation status
├── notebooks/                          # Jupyter notebooks
└── scripts/                            # Test scripts, mock data generators
```

## Features

### 5-Stage Inspection Pipeline

The system uses a progressive inspection approach with specialized models at each stage.

**Phase 1 (In-line, rework possible)**

1. **Stage 0: Anomaly Detection** (Isolation Forest)
   - Initial screening of wafer sensor data (etch_rate, pressure, temperature, etc.)
   - Risk-based classification (high, medium, low risk)
   - Decision: INLINE (proceed to inline) or SKIP (complete wafer)

2. **Stage 1: Yield Prediction & Inline Inspection** (XGBoost)
   - Inline measurements (CD uniformity, film thickness, line width, edge bead)
   - Economic decision: SKIP / PROCEED / REWORK (new sensor data) / SCRAP
   - Rework logic: 70% improvement probability; cost tracked in normalized units

**Phase 2 (Post-fab, no rework)**

3. **Stage 2A: WAT (Wafer Acceptance Test)**
   - Electrical test data (electrical uniformity, contact resistance, leakage, breakdown)
   - Decision: SKIP or PROCEED to pattern analysis

4. **Stage 2B: Wafermap Pattern Analysis** (CNN)
   - Defect maps (pattern type, severity). Benchmarks: WM-811K (proxy).
   - Decision: SKIP or PROCEED to root cause (SEM)

5. **Stage 3: Root Cause Analysis** (SEM + LLM)
   - SEM imaging (destructive; wafer scrapped). LLM root cause reports (Korean).
   - Benchmarks: Carinthia (proxy). Decision: COMPLETE or INVESTIGATE

### Track A: Operational Workflow (Web UI)

- **Production Monitor:** LOT progress (25 wafers/LOT), sensor stream, alerts, wafer status (Queued / Processing / Waiting / Completed / Scrapped), rework badges, yield summary
- **Decision Queue:** AI recommendations per stage, explainability (reasoning, economics, wafermap/SEM viz), one-click actions (INLINE, SKIP, REWORK, PROCEED, SCRAP, COMPLETE), audit trail
- **AI Insights:** Pattern discovery (sensor–pattern correlation, p<0.01), root cause repository (Stage 3), learning from engineer feedback (agreement rate, cost/confidence patterns)
- **Budget Monitor:** Inline / SEM / rework cost tracking (normalized units), progress bars, caps

### Track B: Scientific Validation

- **Step1 Core (Validated):** Same-wafer ground truth, N=200, selection_rate=10%, high-risk=bottom 20%. Bootstrap 95% CI (Recall@10%, normalized cost). Primary results only.
- **Step2/3 Proxy (Benchmarks):** WM-811K (wafermap), Carinthia (SEM). Reported as capability benchmarks; no shared wafer_id. Appendix-only.
- **Outputs:** `trackb/outputs/run_*/reports/` — `trackB_report_core_validated.md`, `trackB_report_appendix_proxy.md`, `PAPER_AGENT_INPUT_GUIDE.md`, `paper_bundle.json`, etc.

### Economic Optimization

- **Budget Management:** Tracks inline/SEM/rework costs (normalized units; no currency in claims)
- **Cost-Aware Routing:** Routes wafers by cost-benefit at each stage
- **Evidence Gate:** Core-only metrics in main results; Proxy benchmarks in appendix only

### Intelligence & Learning

- **Pattern Discovery:** Statistical analysis (14-day lookback), LLM interpretation (Korean)
- **Continuous Learning:** Engineer feedback logging, agreement/disagreement patterns
- **LLM Integration:** Claude for root cause analysis and recommendations (Korean)

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

### Track A: Web Dashboard (Operational Workflow)

```bash
streamlit run streamlit_app/app.py
```

The application is available at `http://localhost:8501`.

- **Production Monitor:** Start a new LOT (25 wafers), watch sequential processing, view wafer status and yield.
- **Decision Queue:** Review AI recommendations (Stage 0–3), see reasoning and economics, approve/rework/scrap with one click.
- **AI Insights:** Run pattern discovery, view root cause reports (Korean), analyze engineer feedback.

### Track B: Validation Pipeline (Reports & Evidence)

```bash
cd trackb
python scripts/run_full_e2e.py   # compile → static_check → trackb_run → verify_outputs → adversarial
# or
python scripts/trackb_run.py --mode from_artifacts
```

Reports are written to `trackb/outputs/run_YYYYMMDD_HHMMSS/reports/`:

- **Core (validated):** `trackB_report_core_validated.md` — Step1 recall, normalized cost, bootstrap CI
- **Proxy (benchmarks):** `trackB_report_appendix_proxy.md` — Step2/3 WM-811K, Carinthia
- **Paper input:** `PAPER_AGENT_INPUT_GUIDE.md`, `paper_bundle.json` — for paper-generating AI

See [trackb/README.md](trackb/README.md) for validation status and quick start.

### Using the Python API

```python
from src.pipeline.controller import PipelineController
from src.utils.data_loader import DataLoader

controller = PipelineController()
# Process wafer inspection data; use streamlit_app for full UI workflow
```

## Key Outputs & Reports

| Output | Location | Description |
|--------|----------|-------------|
| Track A demo | `streamlit_app/` | Web UI: Production Monitor, Decision Queue, AI Insights |
| Track B run reports | `trackb/outputs/run_*/reports/` | Core validated report, Proxy appendix, PAPER_AGENT_INPUT_GUIDE |
| Architecture diagram | `Two-layer_Governance_Architecture.svg` | Track A vs Track B, Evidence Gate, Performance table |
| Paper bundle | `trackb/outputs/run_*/reports/paper_bundle.json` | Structured metadata for paper-generating AI |

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

1. **Track A (UI):** Add or modify pages in `streamlit_app/pages/`, logic in `streamlit_app/utils/` (wafer_processor, stage_executors, ui_components).
2. **Track B (validation):** Add scripts under `trackb/scripts/`, update `trackb/configs/` and report templates.
3. **Pipeline/agents:** Create or update modules in `src/agents/`, `src/pipeline/`, `src/llm/`.
4. Update `config.yaml` or `trackb/configs/` as needed; add tests under `scripts/` or `tests/`.

### Logging

- Application logs: `logs/` (Agent-stage*.log, PipelineController.log, llm_client.log)
- Track B run logs: under `trackb/outputs/run_*/` (if configured)
- Engineer feedback: `logs/engineer_feedbacks_*.jsonl` (from Decision Queue)

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
