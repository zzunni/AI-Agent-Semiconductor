# AI-Driven Semiconductor Quality Control System

Multi-stage decision support system using 6 AI models for real-time wafer inspection optimization.

## Overview

This project implements an advanced AI-powered quality control system for semiconductor manufacturing. It leverages multiple specialized AI models to analyze wafer defects, identify patterns, perform root cause analysis, and optimize inspection processes in real-time.

## Tech Stack

- **Python**: 3.9+
- **AI/LLM**: Anthropic Claude (Sonnet 4.5)
- **Web Interface**: Streamlit
- **Machine Learning**: scikit-learn, XGBoost
- **Data Processing**: pandas, numpy
- **Visualization**: matplotlib, seaborn, plotly

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

### 6 AI Models for Comprehensive Quality Control

1. **Pattern Discovery**: Identifies recurring defect patterns across wafer batches
2. **Root Cause Analysis**: Analyzes defects to determine underlying causes
3. **Defect Classification**: Categorizes defects by type and severity
4. **Predictive Maintenance**: Forecasts equipment issues before they occur
5. **Process Optimization**: Recommends process improvements
6. **Learning & Feedback**: Continuously improves from inspection results

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

Edit `config.yaml` to configure:
- Individual model parameters (temperature, max_tokens)
- Enable/disable specific models
- API settings and timeouts
- Pipeline batch size and thresholds

### Environment Variables

Key environment variables in `.env`:
- `ANTHROPIC_API_KEY`: Your Anthropic API key (required)
- `CLAUDE_MODEL`: Claude model version to use
- `LOG_LEVEL`: Logging verbosity (DEBUG, INFO, WARNING, ERROR)
- `ENABLE_REAL_TIME_PROCESSING`: Enable real-time processing mode

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
