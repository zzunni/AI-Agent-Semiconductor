# AI-Driven Semiconductor QC - Streamlit Dashboard

Interactive web interface for the multi-stage wafer inspection pipeline.

## 🚀 Quick Start

### Launch Dashboard

```bash
streamlit run streamlit_app/app.py
```

The dashboard will open automatically in your browser at `http://localhost:8501`

### Alternative: Custom Port

```bash
streamlit run streamlit_app/app.py --server.port 8502
```

## 📊 Dashboard Features

### 🏠 Dashboard (Home)

**Overview page with key metrics and visualizations**

- **Metrics Display:**
  - Total Inspections
  - Total Cost
  - AI-Engineer Agreement Rate
  - Average Confidence

- **Charts:**
  - AI Recommendation Distribution (Pie Chart)
  - Cost by Stage (Bar Chart)
  - Recent Decisions Table

**Use Case:** Quick overview of system performance and recent activity

---

### 🔍 Wafer Inspection

**Interactive wafer-by-wafer inspection interface**

**Features:**
1. **Wafer Selection**
   - Dropdown with all available wafers
   - Wafer information display (lot, chamber, recipe, sensors)

2. **Pipeline Execution**
   - Click "🚀 Run Pipeline" button
   - Real-time progress bar
   - Stage-by-stage results

3. **Results Display**
   - **Stage 0:** Anomaly Detection
     - Risk level, anomaly score
     - Outlier sensor alerts
   - **Stage 1:** Yield Prediction
     - Predicted yield with confidence interval
     - Interactive gauge chart
     - Economic value calculation
   - **Stage 2B:** Pattern Classification (if triggered)
     - Pattern type, severity
     - Defect density
   - **Stage 3:** Defect Analysis (if SEM performed)
     - Defect type and count
     - LLM root cause analysis (Korean)

4. **Cost Summary**
   - Total cost for inspection
   - Final decision
   - Budget utilization

**Use Case:** Execute inspection on specific wafers and review detailed multi-stage results

**Example Workflow:**
1. Select wafer "W0001" from dropdown
2. Click "Run Pipeline"
3. Review Stage 0: Risk assessment
4. Review Stage 1: Yield prediction (60.6%)
5. Check if SEM was triggered (Stage 2B decision)
6. View final recommendation and total cost

---

### 📊 Pattern Discovery

**Statistical pattern analysis with LLM insights**

**Features:**
1. **Pattern Discovery Engine**
   - Click "🔍 Discover Patterns"
   - Analyzes entire wafer dataset
   - Statistical significance testing (p < 0.01)

2. **Pattern Types Detected:**
   - **Sensor-Pattern Correlations**
     - T-test results (p-value, correlation)
     - Mean comparisons
     - Example: "etch_rate correlates with Edge-Ring pattern"

   - **Chamber Effects**
     - ANOVA results (F-statistic)
     - Chamber-by-chamber statistics
     - Edge-ring rate comparison

   - **Recipe Effects**
     - ANOVA results
     - Recipe-specific severity levels

3. **LLM Analysis** (Korean)
   - Root cause interpretation
   - Recommended actions
   - Process insights

**Use Case:** Identify systemic issues and process optimization opportunities

**Example Insights:**
- "Chamber B3 shows 20% higher defect rate"
- "High etch_rate correlates with Edge-Ring patterns (p=0.00001)"
- "Recipe R2 consistently produces lower severity defects"

---

### 📚 Learning Insights

**Engineer feedback analysis and continuous learning**

**Features:**
1. **Analysis Period Selection**
   - Slider: 7-90 days lookback
   - Default: 30 days

2. **Metrics Overview**
   - Total decisions analyzed
   - AI-Engineer approval rate
   - Agreement/disagreement counts
   - Analysis date range

3. **Rejection Analysis**
   - **Categories:**
     - Cost-related (비용 관련)
     - Risk-related (리스크 관련)
     - Confidence-related (신뢰도 관련)
     - Other (기타)

   - **Bar Chart:** Rejection distribution
   - **Detailed Reasons:** Expandable list

4. **Decision Patterns**
   - **Cost Sensitivity:**
     - High cost (>$500) vs Low cost (≤$500) approval rates
     - Example: "44% vs 68% approval"

   - **Confidence Threshold:**
     - High confidence (>0.8) vs Low confidence (≤0.8)
     - Trust patterns

   - **Stage-Specific Approval:**
     - Approval rate by stage (0, 1, 2B, 3)
     - Bar chart visualization

5. **LLM Insights** (Korean)
   - Comprehensive analysis of feedback patterns
   - Improvement recommendations
   - Engineer preference insights

**Use Case:** Understand how engineers interact with AI recommendations and improve the system

**Example Patterns:**
- "Engineers reject 75% of high-cost recommendations"
- "Stage 1 has 85% approval, Stage 3 has 60% approval"
- "Low confidence recommendations are rejected 65% of the time"

---

### 💰 Budget Monitor

**Real-time cost tracking and budget management**

**Features:**
1. **Inline Inspection Budget**
   - Total budget: $50,000/month
   - Current spending
   - Remaining budget
   - Utilization percentage
   - Progress bar visualization
   - Status indicators (OK, WARNING, EXCEEDED)

2. **SEM Inspection Budget**
   - Total budget: $30,000/month
   - Current spending
   - Remaining budget
   - Utilization percentage
   - Progress bar visualization
   - Status indicators

3. **Total Spending Overview**
   - Combined budget
   - Total spent across all categories
   - Total remaining
   - Spending breakdown pie chart (Inline, SEM, Rework)

4. **Alerts:**
   - ⚠️ Warning at >80% utilization
   - 🚨 Error when budget exceeded

**Use Case:** Monitor monthly inspection costs and prevent budget overruns

**Example Scenario:**
- Inline: $5,200 spent / $50,000 (10.4% utilization) ✅
- SEM: $23,400 spent / $30,000 (78% utilization) ⚠️
- Action: Reduce SEM inspections or adjust thresholds

---

## 🔧 Technical Details

### Architecture

```
streamlit_app/app.py
├── Configuration Loading (config.yaml)
├── Component Initialization
│   ├── PipelineController
│   ├── DataLoader
│   ├── DiscoveryAgent
│   ├── LearningAgent
│   └── MetricsCalculator
└── Page Rendering
    ├── Dashboard
    ├── Wafer Inspection
    ├── Pattern Discovery
    ├── Learning Insights
    └── Budget Monitor
```

### Data Flow

1. **Wafer Inspection:**
   ```
   User selects wafer
   → PipelineController.process_wafer()
   → Stage 0 → Stage 1 → Stage 2B → Stage 3 (conditional)
   → Results displayed with charts
   ```

2. **Pattern Discovery:**
   ```
   User clicks "Discover Patterns"
   → DiscoveryAgent.discover_patterns()
   → Statistical tests (t-test, ANOVA)
   → LLM analysis (optional)
   → Results displayed with expandable sections
   ```

3. **Learning Insights:**
   ```
   User sets lookback period
   → LearningAgent.analyze_feedback()
   → Load decisions_log.csv
   → Calculate approval rates, patterns
   → LLM analysis (optional)
   → Results displayed with charts
   ```

### Dependencies

- **streamlit** >= 1.53.0 - Web framework
- **plotly** >= 6.5.0 - Interactive charts
- **pandas** >= 2.3.0 - Data manipulation
- **pyyaml** - Configuration
- All src/ modules (pipeline, agents, utils)

### Caching

The app uses Streamlit's caching decorators for performance:

```python
@st.cache_resource  # Cache singleton resources
def init_pipeline():
    return PipelineController()

@st.cache_data  # Cache data operations
def load_wafer_data():
    return data_loader.load_step1_data()
```

**Cache Clearing:**
- Press `C` in the browser to clear cache
- Or: Streamlit menu → Clear cache

---

## 📱 User Interface

### Navigation

**Sidebar:**
- Radio buttons for page selection
- Pipeline architecture diagram
- System information footer

**Main Area:**
- Page title and description
- Interactive controls (buttons, dropdowns, sliders)
- Real-time results and visualizations
- Expandable sections for detailed info

### Visual Design

**Color Coding:**
- 🔵 **Blue** - Stage 0 (Anomaly Detection)
- 🟢 **Green** - Stage 1 (Yield Prediction)
- 🟡 **Yellow** - Stage 2B (Pattern Classification)
- 🔴 **Red** - Stage 3 (Defect Analysis)

**Status Indicators:**
- ✅ Success / OK
- ⚠️ Warning
- ❌ Error / Failure

---

## 🔄 Workflow Examples

### Example 1: Daily Wafer Inspection

**Goal:** Inspect today's wafer batch

1. Navigate to **🔍 Wafer Inspection**
2. Select first wafer (e.g., W1200)
3. Click **Run Pipeline**
4. Review results:
   - Stage 0: SKIP (low risk)
   - Stage 1: PROCEED (yield 62%)
   - Cost: $0
5. Repeat for other wafers
6. Check **💰 Budget Monitor** after batch

### Example 2: Weekly Pattern Review

**Goal:** Identify systematic issues

1. Navigate to **📊 Pattern Discovery**
2. Click **Discover Patterns**
3. Review top 3 patterns:
   - Chamber B2 high defects
   - Pressure-Edge correlation
4. Read LLM analysis for root cause
5. Report findings to process team

### Example 3: Monthly Performance Review

**Goal:** Analyze AI performance with engineers

1. Navigate to **📚 Learning Insights**
2. Set lookback: 30 days
3. Click **Analyze Feedback**
4. Review:
   - Approval rate: 68%
   - Top rejection: "Cost too high"
   - Pattern: Low approval for >$500
5. Read LLM insights for recommendations
6. Adjust cost thresholds if needed

### Example 4: Budget Planning

**Goal:** Monthly budget review

1. Navigate to **💰 Budget Monitor**
2. Check utilization:
   - Inline: 15%
   - SEM: 78%
3. Review spending breakdown
4. Plan next month:
   - Increase SEM budget?
   - Optimize thresholds to reduce SEM?

---

## ⚙️ Configuration

### Customization

Edit `config.yaml` to adjust:

```yaml
budget:
  monthly:
    inline: 50000   # Adjust inline budget
    sem: 30000      # Adjust SEM budget
  costs:
    inline_per_wafer: 150
    sem_per_wafer: 800
    rework: 200

models:
  stage0:
    confidence_threshold: 0.7  # Lower = more INLINE
  stage1:
    wafer_value: 1000
    rework_cost: 200
  stage2b:
    severity_threshold: 0.7    # Lower = more SEM
  stage3:
    confidence_threshold: 0.8

learning:
  minimum_feedbacks: 50  # Min decisions for analysis

discovery:
  significance_threshold: 0.01  # p-value threshold
```

### Environment Variables

Create `.env` file:

```bash
ANTHROPIC_API_KEY=your-api-key-here
```

**Note:** LLM features (Korean root cause analysis) require API key

---

## 🐛 Troubleshooting

### Common Issues

**1. Dashboard won't start**
```bash
# Check if port is in use
lsof -i :8501

# Kill existing process
kill -9 <PID>

# Start on different port
streamlit run streamlit_app/app.py --server.port 8502
```

**2. "No decision history found"**
- Run some wafer inspections first
- System needs data in `data/outputs/decisions_log.csv`

**3. Pattern Discovery finds no patterns**
- Need sufficient data variety
- Check if p-value threshold is too strict
- Try with more wafers processed

**4. Learning Insights shows "Insufficient data"**
- Requires minimum 50 decisions (configurable)
- Process more wafers first

**5. LLM analysis shows "API key not found"**
- Add `ANTHROPIC_API_KEY` to `.env` file
- Restart Streamlit

---

## 📈 Performance Tips

1. **Batch Processing:**
   - Use batch mode for multiple wafers
   - Then view results in Dashboard

2. **Cache Management:**
   - Clear cache if data updates aren't showing
   - Press `C` or use menu

3. **Pattern Discovery:**
   - Run periodically (weekly), not on every wafer
   - Computationally expensive on large datasets

4. **Learning Insights:**
   - Start with 7-day lookback for quick analysis
   - Increase to 30-90 days for trends

---

## 🔐 Security Notes

- Dashboard runs locally (localhost:8501)
- No external data transmission (except LLM API if enabled)
- API key stored securely in `.env`
- Decision logs stored locally in `data/outputs/`

---

## 📚 Additional Resources

- **Main README:** [../README.md](../README.md)
- **Configuration:** [../config.yaml](../config.yaml)
- **Test Scripts:** [../scripts/](../scripts/)
- **Documentation:** Project repository

---

## 🎯 Next Steps

After using the dashboard:

1. **Production Deployment:**
   - Configure for production server
   - Set up authentication (Streamlit secrets)
   - Connect to fab data systems

2. **Model Integration:**
   - Replace mock models with real STEP team models
   - Retrain on actual fab data

3. **Customization:**
   - Add company branding
   - Customize thresholds for your process
   - Add facility-specific metrics

---

**Last Updated:** 2026-01-29
**Version:** 1.0
**Author:** AI-Driven Semiconductor QC System
