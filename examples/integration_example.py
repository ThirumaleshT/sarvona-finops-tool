"""
Example: Using FinOps Optimizer as a Python library
"""

from cost_optimization.aws_optimizer import AWSCostOptimizer
from cost_optimization.azure_optimizer import AzureCostOptimizer
from reports.report_generator import ReportGenerator


def main():
    # Initialize optimizers
    aws_optimizer = AWSCostOptimizer(region="us-east-1")
    azure_optimizer = AzureCostOptimizer(
        subscription_id="your-subscription-id",
        region="eastus"
    )

    # Run full optimization
    print("Analyzing AWS environment...")
    aws_results = aws_optimizer.optimize_all()

    print("Analyzing Azure environment...")
    azure_results = azure_optimizer.optimize_all()

    # Generate reports
    generator = ReportGenerator()

    # Generate CLI report
    generator.generate_cli_report(aws_results, azure_results)

    # Generate JSON report
    generator.generate_json_report(aws_results, azure_results, "finops-report.json")

    # Generate CSV export
    generator.generate_csv_export(aws_results, azure_results, "finops-export.csv")

    # Generate action plan
    generator.generate_action_plan(aws_results, azure_results, "action-plan.md")

    # Print executive summary
    print(generator.generate_executive_summary(aws_results, azure_results))


if __name__ == "__main__":
    main()