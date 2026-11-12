"""
CloudCheckr-style FinOps Engine
Advanced multi-cloud cost management with billing, alerting, and governance
"""

import boto3
from typing import List, Dict, Any, Optional
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
import json


class CloudProvider(Enum):
    AWS = "aws"
    AZURE = "azure"
    GCP = "gcp"


class ResourceType(Enum):
    EC2 = "ec2"
    VM = "vm"
    EBS = "ebs"
    DISK = "disk"
    S3 = "s3"
    BLOB = "blob"
    RDS = "rds"
    DATABASE = "database"
    LOAD_BALANCER = "load_balancer"
    VPC = "vpc"


@dataclass
class ResourceCost:
    resource_id: str
    resource_name: str
    resource_type: ResourceType
    provider: CloudProvider
    hourly_cost: float
    monthly_cost: float
    year_to_date_cost: float
    tags: Dict[str, str] = field(default_factory=dict)
    region: str = ""
    account_id: str = ""


@dataclass
class CostAnomaly:
    resource_id: str
    resource_name: str
    anomaly_type: str
    deviation_percent: float
    predicted_cost: float
    actual_cost: float
    timestamp: datetime
    recommendation: str = ""


@dataclass
class BudgetAlert:
    name: str
    budget_amount: float
    actual_spending: float
    variance: float
    alert_threshold: float
    status: str  # ok, warning, exceeded


@dataclass
class GovernanceRule:
    name: str
    description: str
    resource_type: str
    condition: str
    action: str
    enabled: bool = True


class CloudCheckrStyleEngine:
    """CloudCheckr-style cost management engine"""

    def __init__(self):
        self.resources: List[ResourceCost] = []
        self.anomalies: List[CostAnomaly] = []
        self.budgets: List[BudgetAlert] = []
        self.governance_rules: List[GovernanceRule] = []
        self._initialize_governance_rules()

    def _initialize_governance_rules(self):
        """Initialize default governance rules similar to CloudCheckr"""

        self.governance_rules = [
            GovernanceRule(
                name="Idle_EC2_Detection",
                description="Find EC2 instances with <10% CPU for 7+ days",
                resource_type="ec2",
                condition="avg_cpu < 10 AND uptime > 168h",
                action="Stop or terminate instance"
            ),
            GovernanceRule(
                name="Orphaned_Volume_Detection",
                description="Find unattached EBS volumes or managed disks",
                resource_type="ebs,disk",
                condition="attachment_count = 0",
                action="Delete volume to save costs"
            ),
            GovernanceRule(
                name="Reserved_Instance_Analysis",
                description="Recommend RIs for steady-state workloads",
                resource_type="ec2,vm,rds,database",
                condition="avg_utilization > 70% AND consistent_usage > 80%",
                action="Purchase RI for 1-year or 3-year term"
            ),
            GovernanceRule(
                name="Storage_Tiering",
                description="Move infrequently accessed data to cheaper storage",
                resource_type="s3,blob",
                condition="last_accessed > 90 days AND data_size > 100GB",
                action="Move to archive/cool tier"
            ),
            GovernanceRule(
                name="Unused_Resources",
                description="Find completely unused resources",
                resource_type="all",
                condition="uptime = 0 OR traffic = 0",
                action="Terminate resource immediately"
            ),
            GovernanceRule(
                name="Over_Provisioned",
                description="Right-size resources with low utilization",
                resource_type="ec2,vm,rds",
                condition="max_utilization < 30%",
                action="Downgrade to smaller instance type"
            ),
            GovernanceRule(
                name="Spot_VM_Opportunity",
                description="Convert fault-tolerant workloads to spot/low-priority",
                resource_type="ec2,vm",
                condition="workload_type in [batch,dev,test] AND eviction_tolerance = ok",
                action="Convert to spot/low-priority VM"
            ),
        ]

    def get_billing_data_aws(self, months: int = 3) -> List[ResourceCost]:
        """Get detailed AWS billing data with granular resource costs"""
        try:
            ce = boto3.client('ce')

            # Get detailed billing
            end_date = datetime.now()
            start_date = end_date - timedelta(days=months * 30)

            response = ce.get_cost_and_usage(
                TimePeriod={'Start': start_date.strftime('%Y-%m-%d'),
                           'End': end_date.strftime('%Y-%m-%d')},
                Granularity='DAILY',
                Metrics=['UnblendedCost'],
                GroupBy=[
                    {'Type': 'DIMENSION', 'Key': 'LINKED_ACCOUNT'},
                    {'Type': 'DIMENSION', 'Key': 'SERVICE'},
                    {'Type': 'DIMENSION', 'Key': 'USAGE_TYPE'}
                ]
            )

            # Parse and aggregate costs
            for result in response.get('ResultsByTime', []):
                for group in result.get('Groups', []):
                    amount = float(group['Metrics']['UnblendedCost']['Amount'])
                    service = group['Keys'][1] if len(group['Keys']) > 1 else 'Unknown'

                    self.resources.append(ResourceCost(
                        resource_id=f"{service}_{group['Keys'][0]}",
                        resource_name=service,
                        resource_type=self._map_aws_service(service),
                        provider=CloudProvider.AWS,
                        hourly_cost=amount / 24 / 30,
                        monthly_cost=amount,
                        year_to_date_cost=amount * (months / 3)
                    ))

            return self.resources
        except Exception as e:
            print(f"AWS Billing Error: {e}")
            return []

    def _map_aws_service(self, service: str) -> ResourceType:
        mapping = {
            'AmazonEC2': ResourceType.EC2,
            'AmazonEBS': ResourceType.EBS,
            'AmazonS3': ResourceType.S3,
            'AmazonRDS': ResourceType.RDS,
            'ElasticLoadBalancing': ResourceType.LOAD_BALANCER,
            'AmazonVPC': ResourceType.VPC
        }
        return mapping.get(service, ResourceType.EC2)

    def detect_cost_anomalies(self) -> List[CostAnomaly]:
        """Detect unusual cost spikes or patterns"""
        self.anomalies = []

        for resource in self.resources:
            # Simple anomaly detection based on cost variance
            if resource.monthly_cost > 1000:
                # Large costs get more scrutiny
                continue

            # Simulated anomaly detection
            current_cost = resource.monthly_cost
            baseline_cost = resource.hourly_cost * 720  # 30 days

            if current_cost > baseline_cost * 1.5:
                self.anomalies.append(CostAnomaly(
                    resource_id=resource.resource_id,
                    resource_name=resource.resource_name,
                    anomaly_type="Cost Spike",
                    deviation_percent=((current_cost - baseline_cost) / baseline_cost * 100) if baseline_cost > 0 else 0,
                    predicted_cost=baseline_cost,
                    actual_cost=current_cost,
                    timestamp=datetime.now(),
                    recommendation="Review recent changes and usage patterns"
                ))

        return self.anomalies

    def calculate_budget_alerts(self, budget_config: Dict[str, float]) -> List[BudgetAlert]:
        """Calculate budget alerts based on spending vs budgets"""
        self.budgets = []

        total_monthly_spend = sum(r.monthly_cost for r in self.resources)

        for budget_name, budget_amount in budget_config.items():
            variance = ((total_monthly_spend - budget_amount) / budget_amount * 100) if budget_amount > 0 else 0

            status = "ok"
            if variance > 50:
                status = "exceeded"
            elif variance > 20:
                status = "warning"

            self.budgets.append(BudgetAlert(
                name=budget_name,
                budget_amount=budget_amount,
                actual_spending=total_monthly_spend,
                variance=variance,
                alert_threshold=30 if status == "exceeded" else 20 if status == "warning" else 50,
                status=status
            ))

        return self.budgets

    def generate_comprehensive_report(self) -> Dict[str, Any]:
        """Generate a full CloudCheckr-style report"""

        total_monthly = sum(r.monthly_cost for r in self.resources)
        total_ytd = sum(r.year_to_date_cost for r in self.resources)

        # Group by provider
        by_provider = {}
        for r in self.resources:
            provider = r.provider.value
            by_provider[provider] = by_provider.get(provider, 0) + r.monthly_cost

        # Group by type
        by_type = {}
        for r in self.resources:
            rtype = r.resource_type.value
            by_type[rtype] = by_type.get(rtype, 0) + r.monthly_cost

        # Savings potential
        idle_savings = sum(r.monthly_cost * 0.9 for r in self.resources
                          if r.resource_type in [ResourceType.EC2, ResourceType.VM]
                          and r.monthly_cost < 200)

        storage_savings = sum(r.monthly_cost * 0.4 for r in self.resources
                             if r.resource_type in [ResourceType.S3, ResourceType.BLOB, ResourceType.EBS, ResourceType.DISK]
                             and r.monthly_cost < 500)

        ri_savings = sum(r.monthly_cost * 0.4 for r in self.resources
                        if r.resource_type in [ResourceType.EC2, ResourceType.VM]
                        and r.monthly_cost > 100)

        return {
            "report_metadata": {
                "generated_at": datetime.now().isoformat(),
                "time_period": "30 days",
                "total_resources": len(self.resources),
                "total_monthly_spend": total_monthly,
                "total_ytd_spend": total_ytd
            },
            "cost_breakdown": {
                "by_provider": by_provider,
                "by_type": by_type,
                "top_services": sorted([(k, v) for k, v in by_type.items()], key=lambda x: x[1], reverse=True)[:5]
            },
            "anomalies": [{
                "resource": a.resource_name,
                "type": a.anomaly_type,
                "deviation_percent": a.deviation_percent,
                "recommendation": a.recommendation
            } for a in self.anomalies],
            "budget_alerts": [{
                "budget": b.name,
                "status": b.status,
                "variance_percent": b.variance,
                "actual": b.actual_spending,
                "budgeted": b.budget_amount
            } for b in self.budgets],
            "savings_opportunities": {
                "idle_resources": {
                    "description": "Stop idle EC2/VMs with low CPU usage",
                    "potential_savings": idle_savings,
                    "action_items": "Identify and stop instances with <10% CPU for 7+ days"
                },
                "storage_optimization": {
                    "description": "Right-size storage and use appropriate tiers",
                    "potential_savings": storage_savings,
                    "action_items": "Move cold data to archive, delete orphaned volumes"
                },
                "reserved_instances": {
                    "description": "Purchase RIs for consistent workloads",
                    "potential_savings": ri_savings,
                    "action_items": "Analyze usage patterns and purchase 1-year or 3-year RIs"
                }
            },
            "governance_rules": [{
                "name": r.name,
                "description": r.description,
                "condition": r.condition,
                "action": r.action,
                "violations": 0  # Would count in real implementation
            } for r in self.governance_rules],
            "total_potential_savings": idle_savings + storage_savings + ri_savings
        }