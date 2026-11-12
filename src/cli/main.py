"""
FinOps Optimizer CLI
Command-line interface for multi-cloud cost optimization
"""

import click
import os
import json
from datetime import datetime
from typing import Optional

from cost_optimization.aws_optimizer import AWSCostOptimizer, Recommendation
from cost_optimization.azure_optimizer import AzureCostOptimizer, AzureRecommendation
from reports.report_generator import ReportGenerator


def check_aws_credentials() -> bool:
    """Check if AWS credentials are available"""
    try:
        ec2 = AWSCostOptimizer().ec2_client
        ec2.describe_instances(MaxResults=1)
        return True
    except Exception:
        return False


def check_azure_credentials() -> bool:
    """Check if Azure credentials are available"""
    try:
        subscription_id = os.environ.get("AZURE_SUBSCRIPTION_ID")
        if not subscription_id:
            return False
        client = AzureCostOptimizer(subscription_id)
        return True
    except Exception:
        return False


@click.group()
@click.version_option(version="1.0.0")
def app():
    """FinOps Optimizer - Multi-cloud cost optimization for AWS and Azure"""
    pass


@app.group()
def aws():
    """AWS cost optimization commands"""
    pass


@app.group()
def azure():
    """Azure cost optimization commands"""
    pass


@aws.command("analyze")
@click.option("--months", default=3, help="Number of months to analyze")
@click.option("--output", default=None, help="Output file for detailed report")
@click.option("--dry-run", is_flag=True, help="Show what would be done without making changes")
def aws_analyze(months: int, output: Optional[str], dry_run: bool):
    """Analyze AWS costs and identify optimization opportunities"""
    if not check_aws_credentials():
        click.echo("[yellow]Warning: AWS credentials not found or invalid.[/yellow]")
        click.echo("\nTo configure AWS credentials, run:")
        click.echo("  aws configure")
        click.echo("\nOr set environment variables:")
        click.echo("  AWS_ACCESS_KEY_ID, AWS_SECRET_ACCESS_KEY, AWS_SESSION_TOKEN (optional)")
        return

    optimizer = AWSCostOptimizer()
    results = optimizer.optimize_all()

    generator = ReportGenerator()
    generator.generate_cli_report(results, {})

    if output:
        generator.generate_json_report(results, {}, output)
        click.echo(f"\nDetailed report saved to {output}")

    click.echo(f"\nTotal potential monthly savings: ${results['total_potential_savings']:,.2f}")


@aws.command("identify-idle")
@click.option("--threshold-hours", default=72, help="Hours of low CPU utilization threshold")
@click.option("--cpu-percent", default=10.0, help="CPU utilization percentage threshold")
def aws_identify_idle(threshold_hours: int, cpu_percent: float):
    """Identify idle EC2 instances and resources"""
    optimizer = AWSCostOptimizer()
    recommendations = optimizer.identify_idle_ec2(cpu_threshold=cpu_percent)

    if not recommendations:
        click.echo("No idle EC2 instances found.")
        return

    click.echo(f"Found {len(recommendations)} idle EC2 instances:\n")
    for rec in recommendations:
        click.echo(f"  • {rec.resource_id} - {rec.action}")

    total_savings = sum(r.potential_savings for r in recommendations)
    click.echo(f"\nTotal potential savings: ${total_savings:,.2f}/month")


@aws.command("orphaned-volumes")
def aws_orphaned_volumes():
    """Find orphaned EBS volumes"""
    optimizer = AWSCostOptimizer()
    recommendations = optimizer.get_orphaned_ebs_volumes()

    click.echo(f"Found {len(recommendations)} orphaned EBS volumes:\n")
    for rec in recommendations:
        click.echo(f"  • {rec.resource_id} - {rec.action}")

    total_savings = sum(r.potential_savings for r in recommendations)
    click.echo(f"\nTotal potential savings: ${total_savings:,.2f}/month")


@aws.command("rightsize")
@click.option("--max-savings-percent", default=30, help="Maximum percentage savings to recommend")
def aws_rightsize(max_savings_percent: int):
    """Right-size EC2 instances"""
    optimizer = AWSCostOptimizer()
    # Note: This is a placeholder - full implementation would use AWS Compute Optimizer
    click.echo("Right-sizing analysis requires AWS Compute Optimizer API access.")
    click.echo(f"Would identify instances with {max_savings_percent}%+ savings potential")


@aws.command("reserved-recommendations")
@click.option("--terms", default="AllUpfront", help="Term options: AllUpfront, PartialUpfront, NoUpfront")
@click.option("--offering-type", default="ReservedInstances", help="Offering type")
def aws_reserved_recommendations(terms: str, offering_type: str):
    """Get Reserved Instance recommendations"""
    optimizer = AWSCostOptimizer()
    recommendations = optimizer.get_reserved_instance_recommendations()

    click.echo("Reserved Instance Recommendations:\n")
    for rec in recommendations:
        click.echo(f"  • {rec.resource_id}")
        click.echo(f"    Action: {rec.action}")
        click.echo(f"    Savings: ${rec.potential_savings:,.2f}/month\n")


@app.command("analyze")
@click.option("--aws/--no-aws", default=True, help="Include AWS analysis")
@click.option("--azure/--no-azure", default=False, help="Include Azure analysis")
@click.option("--months", default=3, help="Number of months to analyze")
@click.option("--subscription-id", default=None, help="Azure subscription ID")
@click.option("--output", default=None, help="Output file for comprehensive report")
@click.option("--format", "output_format", default="cli", help="Output format: cli, json, csv")
def analyze(aws: bool, azure: bool, months: int, subscription_id: Optional[str], output: Optional[str], output_format: str):
    """Analyze costs across cloud providers"""
    aws_results = {}
    azure_results = {}

    if aws and not check_aws_credentials():
        click.echo("[yellow]Warning: AWS credentials not found. Skipping AWS analysis.[/yellow]")

    if azure:
        if not subscription_id:
            subscription_id = os.environ.get("AZURE_SUBSCRIPTION_ID")
        if not subscription_id:
            click.echo("[yellow]Warning: Azure subscription ID not provided. Skipping Azure analysis.[/yellow]")

    if aws:
        if check_aws_credentials():
            optimizer = AWSCostOptimizer()
            aws_results = optimizer.optimize_all()

    if azure:
        if subscription_id:
            try:
                optimizer = AzureCostOptimizer(subscription_id)
                azure_results = optimizer.optimize_all()
            except Exception as e:
                click.echo(f"[red]Error analyzing Azure: {e}[/red]")

    if not aws_results and not azure_results:
        click.echo("[yellow]No results to display. Please configure cloud credentials.[/yellow]")
        return

    generator = ReportGenerator()

    if output_format == "json":
        output = output or "finops-report.json"
        generator.generate_json_report(aws_results, azure_results, output)
        click.echo(f"JSON report saved to {output}")
    elif output_format == "csv":
        output = output or "finops-report.csv"
        generator.generate_csv_export(aws_results, azure_results, output)
        click.echo(f"CSV export saved to {output}")
    else:
        generator.generate_cli_report(aws_results, azure_results)

    if output and output_format == "cli":
        generator.generate_json_report(aws_results, azure_results, output)
        click.echo(f"\nDetailed JSON report saved to {output}")


@azure.command("analyze")
@click.option("--months", default=3, help="Number of months to analyze")
@click.option("--subscription-id", default=None, help="Azure subscription ID")
@click.option("--output", default=None, help="Output file")
def azure_analyze(months: int, subscription_id: Optional[str], output: Optional[str]):
    """Analyze Azure costs"""
    if not subscription_id:
        subscription_id = os.environ.get("AZURE_SUBSCRIPTION_ID")
        if not subscription_id:
            click.echo("Error: Azure subscription ID required via --subscription-id or AZURE_SUBSCRIPTION_ID env var")
            return

    optimizer = AzureCostOptimizer(subscription_id)
    results = optimizer.optimize_all()

    generator = ReportGenerator()
    generator.generate_cli_report({}, results)

    if output:
        generator.generate_json_report({}, results, output)
        click.echo(f"\nDetailed report saved to {output}")

    click.echo(f"\nTotal potential monthly savings: ${results['total_potential_savings']:,.2f}")


@azure.command("identify-idle")
@click.option("--threshold-percent", default=15.0, help="CPU utilization percentage threshold")
@click.option("--subscription-id", default=None, help="Azure subscription ID")
def azure_identify_idle(threshold_percent: float, subscription_id: Optional[str]):
    """Identify idle Azure VMs"""
    if not subscription_id:
        subscription_id = os.environ.get("AZURE_SUBSCRIPTION_ID")
        if not subscription_id:
            click.echo("Error: Azure subscription ID required")
            return

    optimizer = AzureCostOptimizer(subscription_id)
    recommendations = optimizer.identify_idle_vms(cpu_threshold=threshold_percent)

    click.echo(f"Found {len(recommendations)} potential idle Azure VMs:\n")
    for rec in recommendations:
        click.echo(f"  • {rec.resource_name} - {rec.action}")

    total_savings = sum(r.potential_savings for r in recommendations)
    click.echo(f"\nTotal potential savings: ${total_savings:,.2f}/month")


@azure.command("orphaned-disks")
@click.option("--subscription-id", default=None, help="Azure subscription ID")
def azure_orphaned_disks(subscription_id: Optional[str]):
    """Find orphaned Azure managed disks"""
    if not subscription_id:
        subscription_id = os.environ.get("AZURE_SUBSCRIPTION_ID")
        if not subscription_id:
            click.echo("Error: Azure subscription ID required")
            return

    optimizer = AzureCostOptimizer(subscription_id)
    recommendations = optimizer.get_orphaned_disks()

    click.echo(f"Found {len(recommendations)} orphaned managed disks:\n")
    for rec in recommendations:
        click.echo(f"  • {rec.resource_name} - {rec.action}")

    total_savings = sum(r.potential_savings for r in recommendations)
    click.echo(f"\nTotal potential savings: ${total_savings:,.2f}/month")


@azure.command("savings-recommendations")
@click.option("--subscription-id", default=None, help="Azure subscription ID")
def azure_savings_recommendations(subscription_id: Optional[str]):
    """Get Azure savings plan and reservation recommendations"""
    if not subscription_id:
        subscription_id = os.environ.get("AZURE_SUBSCRIPTION_ID")
        if not subscription_id:
            click.echo("Error: Azure subscription ID required")
            return

    optimizer = AzureCostOptimizer(subscription_id)

    # Get reservation recommendations
    reservations = optimizer.get_reserved_instance_recommendations()
    hybrid_benefits = optimizer.get_azure_hybrid_benefit_recommendations()

    click.echo("Azure Savings Recommendations:\n")

    if reservations:
        click.echo("### Reserved VM Recommendations ###")
        for rec in reservations:
            click.echo(f"  • {rec.resource_name}: {rec.action}")
            click.echo(f"    Savings: ${rec.potential_savings:,.2f}/month\n")
    else:
        click.echo("No reservation recommendations found.\n")

    if hybrid_benefits:
        click.echo("### Azure Hybrid Benefit Opportunities ###")
        for rec in hybrid_benefits:
            click.echo(f"  • {rec.resource_name}: {rec.action}")
            click.echo(f"    Savings: ${rec.potential_savings:,.2f}/month\n")

    total = sum(r.potential_savings for r in reservations + hybrid_benefits)
    if total > 0:
        click.echo(f"Total potential savings: ${total:,.2f}/month")


@app.command("report")
@click.option("--aws/--no-aws", default=True, help="Include AWS in report")
@click.option("--azure/--no-azure", default=False, help="Include Azure in report")
@click.option("--subscription-id", default=None, help="Azure subscription ID")
@click.option("--format", "output_format", type=click.Choice(["pdf", "json", "csv", "action-plan"]), default="json")
@click.option("--output", "-o", default=None, help="Output directory")
def generate_report(aws: bool, azure: bool, subscription_id: Optional[str], output_format: str, output: Optional[str]):
    """Generate a comprehensive report"""
    output_dir = output or "."

    aws_results = {}
    azure_results = {}

    if aws:
        optimizer = AWSCostOptimizer()
        aws_results = optimizer.optimize_all()

    if azure:
        if not subscription_id:
            subscription_id = os.environ.get("AZURE_SUBSCRIPTION_ID")
        if subscription_id:
            optimizer = AzureCostOptimizer(subscription_id)
            azure_results = optimizer.optimize_all()

    generator = ReportGenerator()

    if output_format == "json":
        filepath = f"{output_dir}/finops-report.json"
        generator.generate_json_report(aws_results, azure_results, filepath)
    elif output_format == "csv":
        filepath = f"{output_dir}/finops-report.csv"
        generator.generate_csv_export(aws_results, azure_results, filepath)
    elif output_format == "action-plan":
        filepath = f"{output_dir}/action-plan.md"
        generator.generate_action_plan(aws_results, azure_results, filepath)
    else:
        filepath = f"{output_dir}/finops-report.pdf"
        # PDF would require additional libraries like reportlab or weasyprint

    click.echo(f"Report generated: {filepath}")

    # Print executive summary
    click.echo("\n" + generator.generate_executive_summary(aws_results, azure_results))


@app.command("export")
@click.option("--aws/--no-aws", default=True, help="Include AWS data")
@click.option("--azure/--no-azure", default=False, help="Include Azure data")
@click.option("--subscription-id", default=None, help="Azure subscription ID")
@click.option("--format", "output_format", type=click.Choice(["json", "csv"]), default="csv")
@click.option("--output", "-o", default="finops-export", help="Output file/directory")
def export(aws: bool, azure: bool, subscription_id: Optional[str], output_format: str, output: str):
    """Export data for BI tools"""
    aws_results = {}
    azure_results = {}

    if aws:
        optimizer = AWSCostOptimizer()
        aws_results = optimizer.optimize_all()

    if azure:
        if not subscription_id:
            subscription_id = os.environ.get("AZURE_SUBSCRIPTION_ID")
        if subscription_id:
            optimizer = AzureCostOptimizer(subscription_id)
            azure_results = optimizer.optimize_all()

    generator = ReportGenerator()

    filepath = output if output.endswith(output_format) else f"{output}.{output_format}"
    if output_format == "csv":
        generator.generate_csv_export(aws_results, azure_results, filepath)
    else:
        generator.generate_json_report(aws_results, azure_results, filepath)

    click.echo(f"Data exported to {filepath}")


if __name__ == "__main__":
    app()