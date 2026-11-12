# FinOps Optimizer Tool

A comprehensive multi-cloud cost optimization tool for AWS and Azure.

## Project Structure

```
finops-tool/
├── pyproject.toml           # Project configuration
├── README.md                # Documentation
├── CLAUDE.md                # This file
├── src/
│   ├── finops_optimizer/   # Main package
│   │   └── __init__.py
│   ├── cost_optimization/
│   │   ├── aws_optimizer.py      # AWS cost analysis
│   │   └── azure_optimizer.py    # Azure cost analysis
│   ├── reports/
│   │   └── report_generator.py   # Report generation
│   └── cli/
│       └── main.py               # CLI entry point
└── examples/
```

## Usage

### AWS Commands
```bash
# Analyze AWS costs
finops aws analyze --months 6 --output aws-report.json

# Identify idle EC2 instances
finops aws identify-idle --cpu-percent 10 --threshold-hours 168

# Find orphaned EBS volumes
finops aws orphaned-volumes

# Get Reserved Instance recommendations
finops aws reserved-recommendations --terms AllUpfront
```

### Azure Commands
```bash
# Analyze Azure costs (requires AZURE_SUBSCRIPTION_ID env var)
finops azure analyze --months 6 --output azure-report.json

# Identify idle VMs
finops azure identify-idle --threshold-percent 15

# Find orphaned disks
finops azure orphaned-disks

# Get savings recommendations
finops azure savings-recommendations
```

### Combined Multi-cloud
```bash
# Full analysis
finops analyze --aws --azure --months 3 --output combined-report.json

# Export for BI tools
finops export --aws --azure --format json --output data-export.json
```

## AWS Cost Saving Actions

1. **EC2 Optimization**
   - Stop/terminate idle instances (CPU < 10%)
   - Right-size based on CloudWatch metrics
   - Convert On-Demand to Reserved Instances
   - Use Spot instances for fault-tolerant workloads

2. **Storage Optimization**
   - Delete orphaned EBS volumes
   - Enable S3 Intelligent-Tiering
   - Move cold data to Glacier
   - Convert gp2 → gp3 for better pricing

3. **Networking**
   - Release unused Elastic IPs
   - Use VPC endpoints to reduce data transfer costs

4. **Reserved Instances & Savings Plans**
   - Purchase Compute Savings Plans for consistent workloads
   - Convert high-utilization instances to RIs

## Azure Cost Saving Actions

1. **VM Optimization**
   - Stop dev/test VMs outside working hours
   - Right-size based on performance data
   - Use Spot VMs for batch workloads
   - Apply Azure Hybrid Benefit for Windows licenses

2. **Storage Optimization**
   - Move blob storage to Cool/Archive tiers
   - Clean up unattached disks
   - Enable Storage Blob Intelligence Tiering

3. **Networking**
   - Delete unused public IPs
   - Use Azure Virtual WAN for optimized routing

4. **Azure Reservations**
   - Purchase 1-year reservations for consistent workloads
   - Use reserved VM instances for savings

## Environment Variables

- `AZURE_SUBSCRIPTION_ID` - Azure subscription ID
- `AWS_PROFILE` - AWS CLI profile (optional)

## Dependencies

- boto3 >= 1.34.0 (AWS SDK)
- azure-identity >= 1.16.0 (Azure auth)
- azure-mgmt-costmanagement >= 2.0.1
- azure-mgmt-compute >= 35.0.0
- rich >= 13.0.0 (CLI formatting)
- tabulate >= 0.9.0 (table formatting)