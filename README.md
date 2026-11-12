# AI FinOps Optimizer

A comprehensive AI-powered multi-cloud cost optimization tool combining CloudCheckr and Economize features.

## Quick Start

### GUI Launchers (Recommended)

**Simple GUI**: Double-click `run-gui.bat`
**AI Dashboard**: Double-click `run-ai-dashboard.bat`
**CloudCheckr Style**: Double-click `run-cloudcheckr-gui.bat`

### CLI Commands
```bash
pip install -e .
finops --help
```

## Key Features

### AI-Powered Intelligence
- **Automated Rightsizing**: ML-driven instance size recommendations
- **Anomaly Detection**: Statistical anomaly detection with confidence scoring
- **Demand Forecasting**: 3-month cost forecasting with uncertainty ranges
- **Reservation Optimization**: AI-powered committed usage recommendations
- **Commitment Strategy**: Enterprise discount program optimization

### CloudCheckr-Style Features
- **Cost Overview Dashboard**: Monthly spend, trends, and alerts
- **Resource Breakdown**: Detailed cost by service, region, and tags
- **Governance Rules**: 7+ compliance and cost control rules
- **Budget Monitoring**: Real-time budget alerts and variance tracking
- **Multi-cloud Support**: AWS + Azure with unified view

### Economize-Style Features
- **AI Recommendations**: Actionable savings with ROI calculations
- **Implementation Plans**: Step-by-step optimization guides
- **Confidence Scoring**: Risk-adjusted savings predictions
- **Effort Estimation**: Low/Medium/High implementation effort ratings

## GUI Dashboard Features

### AI Overview Tab
- Total monthly spend with trend indicator
- Savings potential cards (idle resources, storage, reservations)
- AI recommendation count and confidence score
- Cost breakdown by service

### AI Insights Tab
- Top 10 AI-powered recommendations
- Confidence scores and expected savings
- Implementation effort ratings

### Forecasting Tab
- 3-month cost predictions
- Confidence intervals (80-95%)
- Seasonal adjustment factors
- Alert thresholds

### Actions Tab
- Prioritized action list
- Effort-based categorization
- Export to JSON/CSV
- Mark as planned/implemented

## Cost Saving Categories

### Tier 1: Immediate Savings (Low Risk)
1. **Idle Resources**: Stop/terminate unused EC2/VMs
   - Savings: $500-5000/month per resource
   - Effort: Low, ROI: <1 month

2. **Orphaned Volumes**: Delete unattached disks
   - Savings: $5-50/month per volume
   - Effort: Low, ROI: Immediate

### Tier 2: Medium Risk Actions
3. **Storage Optimization**: Tier cold data to archive
   - Savings: 50-80% reduction on cold storage
   - Effort: Medium, ROI: 1-3 months

4. **Reserved Instances**: Commit to steady workloads
   - Savings: 20-60% off on-demand rates
   - Effort: Medium, ROI: 6-12 months

### Tier 3: Strategic Commitments
5. **Spot/Low-Priority VMs**: For fault-tolerant workloads
   - Savings: 60-90% off spot prices
   - Effort: Medium-High, ROI: Immediate

6. **Enterprise Discount Program**: For large spenders
   - Savings: Additional 10-20% over RIs
   - Effort: High, ROI: 12-24 months

7. **Azure Hybrid Benefit**: Leverage existing Windows licenses
   - Savings: 40-50% on Windows VMs
   - Effort: Low, ROI: Immediate

## AI Algorithms Used

| Algorithm | Purpose | Confidence |
|-----------|---------|------------|
| Statistical Analysis | Rightsizing decisions | 80-95% |
| Time Series (Linear Regression) | Cost forecasting | 70-85% |
| Unsupervised Learning | Anomaly detection | 85-90% |
| Linear Programming | Reservation optimization | 90-95% |
| Rule-based Engine | Recommendation prioritization | 95% |

## Project Structure

```
finops-tool/
├── pyproject.toml          # Package configuration
├── requirements.txt        # Dependencies
├── README.md              # This file
├── run-gui.bat           # Simple GUI launcher
├── run-ai-dashboard.bat  # Advanced AI dashboard
├── run-cloudcheckr-gui.bat # Enterprise dashboard
├── gui_launcher.py       # Simple GUI entry
├── simple_gui_launcher.py # Simple GUI
├── test_installation.py  # Validation script
├── src/
│   ├── cli/               # CLI commands
│   ├── cost_optimization/ # Core AWS/Azure optimizers
│   ├── cloud_checkr_style/ # CloudCheckr-style features
│   ├── ai_enhanced/       # AI engine and algorithms
│   ├── reports/           # Report generation
│   ├── gui/               # GUI interfaces
│   └── finops_optimizer/  # Main package
└── examples/              # Integration examples
```

## Installation

```bash
pip install -r requirements.txt
pip install -e .
```

## Cloud Authentication

### AWS
```bash
aws configure
# Or set: AWS_ACCESS_KEY_ID, AWS_SECRET_ACCESS_KEY
```

### Azure
```bash
az login
# Or set: AZURE_CLIENT_ID, AZURE_CLIENT_SECRET, AZURE_TENANT_ID, AZURE_SUBSCRIPTION_ID
```

## Output Files

The tool generates:
- `finops-report.json` - Full JSON report with all recommendations
- `finops-export.csv` - CSV for BI tools
- `finops-ai-recommendations.json` - AI-specific recommendations
- `action-plan.md` - Prioritized implementation guide

## Next Steps

1. Run the AI Dashboard: `run-ai-dashboard.bat`
2. Connect your cloud accounts
3. Review AI-powered insights
4. Export action plan
5. Implement optimization actions
6. Monitor savings monthly

## About

This tool combines features from:
- **CloudCheckr**: Governance, budgets, reservations, multi-cloud
- **Economize**: AI recommendations, forecasting, ROI calculations

Designed for FinOps teams to identify and implement cost optimizations across AWS and Azure environments.