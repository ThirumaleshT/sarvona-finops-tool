"""
Report Generation Module
Creates detailed cost optimization reports in multiple formats
"""

from typing import Dict, Any, List
from datetime import datetime
from dataclasses import asdict
import json
from tabulate import tabulate
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.rule import Rule


class ReportGenerator:
    """Generates cost optimization reports in multiple formats"""

    def __init__(self):
        self.console = Console()

    def generate_cli_report(self, aws_results: Dict, azure_results: Dict) -> None:
        """Generate a formatted CLI report"""
        self.console.print(Panel.fit(
            "[bold cyan]FinOps Optimization Report[/bold cyan]",
            subtitle=f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
        ))

        # AWS Summary
        if aws_results:
            self.console.print(Rule("[bold yellow]AWS Cost Optimization[/bold yellow]"))
            aws_table = Table(title="AWS Recommendations")
            aws_table.add_column("ID", style="dim", width=20)
            aws_table.add_column("Type", width=15)
            aws_table.add_column("Savings", justify="right", width=15)
            aws_table.add_column("Confidence", width=12)
            aws_table.add_column("Action", width=55)

            for rec in aws_results.get("recommendations", [])[:10]:
                aws_table.add_row(
                    rec.resource_id[:20],
                    rec.recommendation_type.value,
                    f"${rec.potential_savings:,.2f}/mo",
                    f"{rec.confidence*100:.0f}%",
                    rec.action[:55] + "..." if len(rec.action) > 55 else rec.action
                )

            self.console.print(aws_table)

            # AWS Summary
            aws_savings = aws_results.get("total_potential_savings", 0)
            self.console.print(f"\n[bold green]AWS Total Potential Savings: ${aws_savings:,.2f}/month[/bold green]")

        # Azure Summary
        if azure_results:
            self.console.print(Rule("[bold blue]Azure Cost Optimization[/bold blue]"))
            azure_table = Table(title="Azure Recommendations")
            azure_table.add_column("Name", style="dim", width=25)
            azure_table.add_column("Type", width=15)
            azure_table.add_column("Savings", justify="right", width=15)
            azure_table.add_column("Confidence", width=12)
            azure_table.add_column("Action", width=50)

            for rec in azure_results.get("recommendations", [])[:10]:
                azure_table.add_row(
                    rec.resource_name[:25],
                    rec.recommendation_type.value,
                    f"${rec.potential_savings:,.2f}/mo",
                    f"{rec.confidence*100:.0f}%",
                    rec.action[:50] + "..." if len(rec.action) > 50 else rec.action
                )

            self.console.print(azure_table)

            azure_savings = azure_results.get("total_potential_savings", 0)
            self.console.print(f"\n[bold green]Azure Total Potential Savings: ${azure_savings:,.2f}/month[/bold green]")

        # Combined Summary
        total_savings = aws_savings + azure_savings
        self.console.print(Rule())
        self.console.print(Panel(
            f"[bold magenta]Total Potential Monthly Savings: ${total_savings:,.2f}[/bold magenta]",
            border_style="magenta",
            expand=True
        ))

        self._print_detailed_summary(aws_results, azure_results)

    def _print_detailed_summary(self, aws_results: Dict, azure_results: Dict) -> None:
        """Print detailed breakdown by category"""
        if not aws_results and not azure_results:
            return

        self.console.print("\n[bold]Breakdown by Category:[/bold]")

        if aws_results:
            self.console.print("\n[yellow]AWS:[/yellow]")
            for category, savings in aws_results.get("summary_by_type", {}).items():
                self.console.print(f"  • {category.replace('_', ' ').title()}: ${savings:,.2f}")

        if azure_results:
            self.console.print("\n[blue]Azure:[/blue]")
            for category, savings in azure_results.get("summary_by_type", {}).items():
                self.console.print(f"  • {category.replace('_', ' ').title()}: ${savings:,.2f}")

    def generate_json_report(self, aws_results: Dict, azure_results: Dict, filepath: str) -> None:
        """Generate JSON format report"""
        report = {
            "generated_at": datetime.now().isoformat(),
            "aws": {
                "total_savings": aws_results.get("total_potential_savings", 0),
                "recommendations": [asdict(r) for r in aws_results.get("recommendations", [])],
                "summary_by_type": aws_results.get("summary_by_type", {})
            },
            "azure": {
                "total_savings": azure_results.get("total_potential_savings", 0),
                "recommendations": [asdict(r) for r in azure_results.get("recommendations", [])],
                "summary_by_type": azure_results.get("summary_by_type", {})
            },
            "total_savings": (
                aws_results.get("total_potential_savings", 0) +
                azure_results.get("total_potential_savings", 0)
            )
        }

        with open(filepath, 'w') as f:
            json.dump(report, f, indent=2, default=str)

    def generate_csv_export(self, aws_results: Dict, azure_results: Dict, filepath: str) -> None:
        """Generate CSV export for BI tools"""
        import csv

        with open(filepath, 'w', newline='') as f:
            writer = csv.writer(f)
            writer.writerow([
                "Cloud", "Resource ID", "Resource Name", "Type", "Recommendation Type",
                "Current Cost", "Recommended Cost", "Potential Savings", "Confidence",
                "Action", "Implementation Cost", "Payback Period", "Timestamp"
            ])

            for rec in aws_results.get("recommendations", []):
                writer.writerow([
                    "AWS",
                    rec.resource_id,
                    "",
                    rec.resource_type,
                    rec.recommendation_type.value,
                    rec.current_cost,
                    rec.recommended_cost,
                    rec.potential_savings,
                    rec.confidence,
                    rec.action,
                    rec.implementation_cost,
                    rec.payback_period_months,
                    rec.timestamp if hasattr(rec, 'timestamp') else datetime.now().isoformat()
                ])

            for rec in azure_results.get("recommendations", []):
                writer.writerow([
                    "Azure",
                    rec.resource_id,
                    rec.resource_name,
                    rec.resource_type,
                    rec.recommendation_type.value,
                    rec.current_cost,
                    rec.recommended_cost,
                    rec.potential_savings,
                    rec.confidence,
                    rec.action,
                    rec.implementation_cost,
                    rec.payback_period_months,
                    datetime.now().isoformat()
                ])

    def generate_action_plan(self, aws_results: Dict, azure_results: Dict, filepath: str) -> None:
        """Generate prioritized action plan with implementation steps"""
        all_recommendations = []
        all_recommendations.extend(aws_results.get("recommendations", []))
        all_recommendations.extend(azure_results.get("recommendations", []))

        # Sort by savings and priority
        priority_order = {
            "termination": 1,
            "idle_resource": 2,
            "storage_optimization": 3,
            "spot_vm": 4,
            "rightsizing": 5,
            "reserved_instance": 6,
            "reservation": 7,
            "azure_hybrid_benefit": 8
        }

        all_recommendations.sort(key=lambda x: (
            priority_order.get(x.recommendation_type.value if hasattr(x, 'recommendation_type') else x.recommendation_type.value, 99),
            -x.potential_savings
        ))

        with open(filepath, 'w') as f:
            f.write("# FinOps Action Plan\n\n")
            f.write(f"## Overview\n")
            f.write(f"- Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write(f"- Total Recommendations: {len(all_recommendations)}\n")
            f.write(f"- Total Potential Savings: ${sum(r.potential_savings for r in all_recommendations):,.2f}/month\n\n")

            f.write("## Priority Order\n\n")

            for i, rec in enumerate(all_recommendations, 1):
                f.write(f"### {i}. {rec.action}\n")
                f.write(f"- **Cloud**: {'AWS' if hasattr(rec, 'resource_id') and not hasattr(rec, 'resource_name') else 'Azure'}\n")
                f.write(f"- **Resource**: {rec.resource_id if hasattr(rec, 'resource_id') else rec.resource_name}\n")
                f.write(f"- **Type**: {rec.resource_type}\n")
                f.write(f"- **Recommendation**: {rec.recommendation_type.value if hasattr(rec, 'recommendation_type') else rec.recommendation_type.value}\n")
                f.write(f"- **Potential Savings**: ${rec.potential_savings:,.2f}/month\n")
                f.write(f"- **Confidence**: {rec.confidence*100:.0f}%\n")
                f.write(f"  \n")

                if rec.recommendation_type.value in ["termination", "idle_resource"]:
                    f.write("**Implementation**:\n")
                    f.write("1. Review the recommendation\n")
                    f.write("2. Verify the resource is not required\n")
                    f.write("3. Execute the termination action\n")
                elif "storage" in rec.recommendation_type.value:
                    f.write("**Implementation**:\n")
                    f.write("1. Review current access patterns\n")
                    f.write("2. Move data to appropriate storage tier\n")
                    f.write("3. Set lifecycle policies for future optimization\n")

                f.write("  \n---\n\n")

    def generate_executive_summary(self, aws_results: Dict, azure_results: Dict) -> str:
        """Generate executive summary text"""
        total_savings = (
            aws_results.get("total_potential_savings", 0) +
            azure_results.get("total_potential_savings", 0)
        )

        summary = f"""
Executive Summary - FinOps Cost Optimization

OVERVIEW:
Our analysis identified significant cost optimization opportunities across your AWS and Azure environments.

KEY FINDINGS:
• Total Monthly Savings Potential: ${total_savings:,.2f}
• Total Annual Savings Potential: ${total_savings * 12:,.2f}

AWS Recommendations:
• {len(aws_results.get('recommendations', []))} opportunities identified
• Monthly Savings: ${aws_results.get('total_potential_savings', 0):,.2f}

Azure Recommendations:
• {len(azure_results.get('recommendations', []))} opportunities identified
• Monthly Savings: ${azure_results.get('total_potential_savings', 0):,.2f}

PRIORITY ACTIONS:
1. Terminate idle/stopped resources immediately
2. Implement storage lifecycle policies
3. Purchase reserved instances for steady-state workloads
4. Convert dev/test workloads to spot/low-priority instances

RISK ASSESSMENT:
All recommendations have been categorized by risk level:
• Low Risk: Termination, storage optimization
• Medium Risk: Rightsizing, spot instances
• High Risk: Reserved instances (commitment required)

Next Steps:
1. Review this report with your cloud team
2. Prioritize recommendations based on business impact
3. Create a 90-day cost optimization roadmap
4. Set up monthly cost monitoring and alerting
"""
        return summary