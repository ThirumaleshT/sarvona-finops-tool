"""
GCP Cost Optimization Module
Provides cost analysis and optimization recommendations for Google Cloud resources
"""

from typing import List, Dict, Any, Optional
from dataclasses import dataclass
from enum import Enum
from datetime import datetime, timedelta
import json


class GCPRecommendationType(Enum):
    RIGHTSIZING = "rightsizing"
    TERMINATION = "termination"
    COMMITMENT = "commitment"
    STORAGE_OPTIMIZATION = "storage_optimization"
    PREEMPTIBLE_VM = "preemptible_vm"
    IDLE_RESOURCE = "idle_resource"


@dataclass
class GCPRecommendation:
    resource_id: str
    resource_name: str
    resource_type: str
    recommendation_type: GCPRecommendationType
    current_cost: float
    recommended_cost: float
    potential_savings: float
    confidence: float
    action: str
    implementation_cost: float = 0
    payback_period_months: float = 0


class GCPOptimizer:
    """GCP Cost Optimization engine (simulated - requires Google Cloud API)"""

    def __init__(self, project_id: str, credentials_path: Optional[str] = None):
        self.project_id = project_id
        self.credentials_path = credentials_path
        self._sample_data = self._generate_sample_data()

    def _generate_sample_data(self) -> List[Dict]:
        """Generate sample GCP resources for demonstration"""
        return [
            {
                "id": "projects/p-001/zones/us-central1-a/instances/gke-cluster",
                "name": "GKE-Production-Cluster",
                "type": "GKECluster",
                "provider": "GCP",
                "project": self.project_id,
                "zone": "us-central1-a",
                "monthly_cost": 320.0,
                "tags": {"Environment": "prod", "Team": "Engineering"},
                "region": "us-central1"
            },
            {
                "id": "projects/p-001/zones/us-east1-b/disks/logs-disk",
                "name": "Logs-Persistent-Disk",
                "type": "PersistentDisk",
                "provider": "GCP",
                "project": self.project_id,
                "zone": "us-east1-b",
                "monthly_cost": 150.0,
                "tags": {"Environment": "prod"},
                "region": "us-east1"
            },
            {
                "id": "projects/p-001/buckets/prod-backups",
                "name": "Production-Backups",
                "type": "CloudStorage",
                "provider": "GCP",
                "monthly_cost": 85.0,
                "tags": {"Environment": "prod", "Team": "Platform"},
                "region": "us-central1"
            }
        ]

    def get_billing_data(self, months: int = 3) -> Dict[str, Any]:
        """Get billing data from Cloud Billing API"""
        # Placeholder for actual Google Cloud Billing API integration
        return {
            "project_id": self.project_id,
            "billing_period": f"Last {months} months",
            "total_cost": sum(r.get("monthly_cost", 0) for r in self._sample_data),
            "services": self._sample_data
        }

    def get_compute_instances(self) -> List[Dict]:
        """Get all Compute Engine instances"""
        return [r for r in self._sample_data if "instance" in r["type"].lower()]

    def get_cloud_storage_buckets(self) -> List[Dict]:
        """Get all Cloud Storage buckets"""
        return [r for r in self._sample_data if "storage" in r["type"].lower() or "bucket" in r["type"].lower()]

    def get_persistent_disks(self) -> List[Dict]:
        """Get all persistent disks"""
        return [r for r in self._sample_data if "disk" in r["type"].lower()]

    def identify_idle_compute(self, cpu_threshold: float = 15.0) -> List[GCPRecommendation]:
        """Identify Compute instances with consistently low utilization"""
        recommendations = []
        instances = self.get_compute_instances()

        for instance in instances:
            # Simulated idle detection - in production, use Monitoring API
            instance_type = instance.get("type", "")
            if "dev" in instance.get("tags", {}).get("Environment", "").lower():
                hourly_cost = instance.get("monthly_cost", 0) / 720
                recommendations.append(GCPRecommendation(
                    resource_id=instance["id"],
                    resource_name=instance["name"],
                    resource_type="Compute Instance",
                    recommendation_type=GCPRecommendationType.IDLE_RESOURCE,
                    current_cost=instance.get("monthly_cost", 0),
                    recommended_cost=0,
                    potential_savings=instance.get("monthly_cost", 0) * 0.7,
                    confidence=0.85,
                    action=f"Stop idle instance {instance['name']}. Dev environment not running."
                ))

        return recommendations

    def get_storage_optimization(self) -> List[GCPRecommendation]:
        """Identify storage optimization opportunities"""
        recommendations = []

        for bucket in self.get_cloud_storage_buckets():
            # Check if bucket could benefit from Nearline/Coldline
            cost = bucket.get("monthly_cost", 0)
            if "prod" in bucket.get("tags", {}).get("Environment", ""):
                recommendations.append(GCPRecommendation(
                    resource_id=bucket["id"],
                    resource_name=bucket["name"],
                    resource_type="Cloud Storage",
                    recommendation_type=GCPRecommendationType.STORAGE_OPTIMIZATION,
                    current_cost=cost,
                    recommended_cost=cost * 0.6,
                    potential_savings=cost * 0.4,
                    confidence=0.75,
                    action=f"Enable Storage Class Transition for {bucket['name']} to Nearline"
                ))

        for disk in self.get_persistent_disks():
            size_gb = disk.get("tags", {}).get("SizeGB", 100)
            if size_gb < 1000:
                recommendations.append(GCPRecommendation(
                    resource_id=disk["id"],
                    resource_name=disk["name"],
                    resource_type="Persistent Disk",
                    recommendation_type=GCPRecommendationType.TERMINATION,
                    current_cost=disk.get("monthly_cost", 0),
                    recommended_cost=0,
                    potential_savings=disk.get("monthly_cost", 0),
                    confidence=0.90,
                    action=f"Delete orphaned disk {disk['name']}"
                ))

        return recommendations

    def get_committed_use_recommendations(self) -> List[GCPRecommendation]:
        """Recommend Committed Use Discounts for predictable workloads"""
        recommendations = []

        compute_total = sum(i.get("monthly_cost", 0) for i in self.get_compute_instances())

        if compute_total > 500:
            recommendations.append(GCPRecommendation(
                resource_id=f"committed-{self.project_id}",
                resource_name="Committed Use Discount",
                resource_type="CommittedUse",
                recommendation_type=GCPRecommendationType.COMMITMENT,
                current_cost=0,
                recommended_cost=compute_total * 0.3,
                potential_savings=compute_total * 0.3,
                confidence=0.80,
                action=f"Purchase 1-year CUD for {self.project_id} - estimated 30-60% savings"
            ))

        return recommendations

    def get_preemptible_vm_opportunities(self) -> List[GCPRecommendation]:
        """Identify VMs that could use Preemptible instances"""
        recommendations = []

        for instance in self.get_compute_instances():
            workload = instance.get("tags", {}).get("Workload", "")
            env = instance.get("tags", {}).get("Environment", "")

            if workload in ["batch", "analytics", "ci-cd"] or env in ["dev", "test"]:
                current_cost = instance.get("monthly_cost", 0)
                recommendations.append(GCPRecommendation(
                    resource_id=instance["id"],
                    resource_name=instance["name"],
                    resource_type="Compute Instance",
                    recommendation_type=GCPRecommendationType.PREEMPTIBLE_VM,
                    current_cost=current_cost,
                    recommended_cost=current_cost * 0.2,
                    potential_savings=(current_cost - current_cost * 0.2) * 0.8,
                    confidence=0.75,
                    action=f"Convert {instance['name']} to Preemptible VM for up to 80% savings"
                ))

        return recommendations

    def optimize_all(self) -> Dict[str, Any]:
        """Run all optimizations and return consolidated report"""
        all_recommendations = []

        all_recommendations.extend(self.identify_idle_compute())
        all_recommendations.extend(self.get_storage_optimization())
        all_recommendations.extend(self.get_committed_use_recommendations())
        all_recommendations.extend(self.get_preemptible_vm_opportunities())

        all_recommendations.sort(key=lambda r: r.potential_savings, reverse=True)

        total_savings = sum(r.potential_savings for r in all_recommendations)
        by_type = {}
        for r in all_recommendations:
            by_type[r.recommendation_type.value] = by_type.get(r.recommendation_type.value, 0) + r.potential_savings

        return {
            "project_id": self.project_id,
            "recommendations": [
                {
                    "resource_id": r.resource_id,
                    "resource_name": r.resource_name,
                    "resource_type": r.resource_type,
                    "recommendation_type": r.recommendation_type.value,
                    "current_cost": r.current_cost,
                    "recommended_cost": r.recommended_cost,
                    "potential_savings": r.potential_savings,
                    "confidence": r.confidence,
                    "action": r.action,
                    "payback_period_months": r.payback_period_months
                }
                for r in all_recommendations
            ],
            "total_potential_savings": total_savings,
            "summary_by_type": by_type,
            "timestamp": datetime.now().isoformat()
        }


# Factory function
def create_gcp_optimizer(project_id: str) -> GCPOptimizer:
    """Create a GCP optimizer instance"""
    return GCPOptimizer(project_id=project_id)