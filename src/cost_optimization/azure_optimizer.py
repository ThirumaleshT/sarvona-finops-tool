"""
Azure Cost Optimization Module
Provides cost analysis and optimization recommendations for Azure resources
"""

from azure.identity import InteractiveBrowserCredential
from azure.mgmt.costmanagement import CostManagementClient
from azure.mgmt.compute import ComputeManagementClient
from azure.mgmt.resource.resources import ResourceManagementClient
from typing import List, Dict, Any, Optional
from dataclasses import dataclass
from enum import Enum
import datetime


class AzureRecommendationType(Enum):
    RIGHTSIZING = "rightsizing"
    TERMINATION = "termination"
    RESERVATION = "reservation"
    STORAGE_OPTIMIZATION = "storage_optimization"
    SPOT_VM = "spot_vm"
    IDLE_RESOURCE = "idle_resource"
    AZURE_HYBRID_BENEFIT = "azure_hybrid_benefit"


@dataclass
class AzureRecommendation:
    resource_id: str
    resource_name: str
    resource_type: str
    recommendation_type: AzureRecommendationType
    current_cost: float
    recommended_cost: float
    potential_savings: float
    confidence: float
    action: str
    implementation_cost: float = 0
    payback_period_months: float = 0


class AzureCostOptimizer:
    """Azure Cost Optimization engine"""

    def __init__(self, subscription_id: str, region: str = "eastus"):
        self.subscription_id = subscription_id
        self.region = region
        # Use InteractiveBrowserCredential for GUI-based interactive logins
        self.credential = InteractiveBrowserCredential()
        self.compute_client = ComputeManagementClient(
            self.credential, subscription_id
        )
        self.cost_client = CostManagementClient(
            self.credential, subscription_id
        )
        self.resource_client = ResourceManagementClient(
            self.credential, subscription_id
        )

    def test_connection(self):
        """Test connection by listing resource groups"""
        list(self.resource_client.resource_groups.list())

    def get_cost_data(self, months: int = 3) -> Dict[str, Any]:
        """Get Azure cost data for the specified period"""
        end_date = datetime.date.today()
        start_date = end_date - datetime.timedelta(days=30 * months)

        scope = f"/subscriptions/{self.subscription_id}"

        query = {
            "type": "Usage",
            "timeframe": "Custom",
            "timePeriod": {
                "start": str(start_date),
                "end": str(end_date),
            },
            "dataset": {
                "granularity": "Monthly",
                "aggregation": {
                    "TotalCost": {
                        "name": "Cost",
                        "function": "Sum"
                    }
                },
                "grouping": [
                    {"type": "Dimension", "name": "ResourceProvider"},
                    {"type": "Dimension", "name": "ServiceName"},
                    {"type": "Dimension", "name": "ResourceLocation"},
                    {"type": "Dimension", "name": "ResourceType"},
                ],
            },
        }

        try:
            response = self.cost_client.query.usage(scope, parameters=query)
            return response
        except Exception as e:
            print(f"Error getting Azure costs: {e}")
            return {}

    def get_vms(self) -> List[Dict]:
        """Get all VMs in the subscription"""
        vms = []
        try:
            for vm in self.compute_client.virtual_machines.list_all():
                vms.append({
                    "id": vm.id,
                    "name": vm.name,
                    "location": vm.location,
                    "vm_size": vm.hardware_profile.vm_size,
                    "power_state": self._get_vm_power_state(vm),
                    "tags": vm.tags or {},
                })
        except Exception as e:
            print(f"Error listing VMs: {e}")
        return vms

    def _get_vm_power_state(self, vm) -> str:
        """Get VM power state using instance view"""
        try:
            instance_view = self.compute_client.virtual_machines.instance_view(
                self.subscription_id,
                vm.resource_group,
                vm.name
            )
            for status in instance_view.statuses:
                if "PowerState" in status.code:
                    return status.code.split("/")[-1]
        except Exception:
            pass
        return "Unknown"

    def get_vm_utilization(self, resource_group: str, vm_name: str) -> Optional[Dict]:
        """Get VM performance data from Azure Monitor"""
        # Note: Requires Azure Monitor Metrics client
        # This is a simplified placeholder
        return {
            "avg_cpu": 15.0,  # Placeholder - use Azure Metrics API in production
            "avg_memory": 30.0,
            "data_points": 168,  # 7 days worth
        }

    def _get_vm_hourly_price(self, vm_size: str) -> float:
        """Get hourly price for a VM size (East US, Pay-as-you-go)"""
        # Simplified pricing - use Azure Retail Prices API in production
        pricing = {
            "Standard_B1s": 0.0384,
            "Standard_B1ms": 0.04224,
            "Standard_B2s": 0.0416,
            "Standard_B2ms": 0.0832,
            "Standard_B4ms": 0.1664,
            "Standard_D2s_v3": 0.096,
            "Standard_D4s_v3": 0.192,
            "Standard_D8s_v3": 0.384,
            "Standard_D16s_v3": 0.768,
            "Standard_D32s_v3": 1.536,
            "Standard_E2s_v3": 0.096,
            "Standard_E4s_v3": 0.192,
            "Standard_E8s_v3": 0.384,
        }
        return pricing.get(vm_size, 0.1)

    def identify_idle_vms(self, cpu_threshold: float = 15.0) -> List[AzureRecommendation]:
        """Identify VMs with consistently low utilization"""
        recommendations = []
        vms = self.get_vms()

        for vm in vms:
            if vm["power_state"] != "running":
                continue

            # Check for dev/test environment
            env = vm["tags"].get("Environment", "").lower()
            if env not in ["dev", "test", "staging", "development"]:
                continue

            utilization = self.get_vm_utilization(
                vm["id"].split("/")[-2],
                vm["name"]
            )

            if not utilization:
                continue

            avg_cpu = utilization.get("avg_cpu", 0)
            if avg_cpu < cpu_threshold:
                hourly_price = self._get_vm_hourly_price(vm["vm_size"])
                monthly_cost = hourly_price * 24 * 30

                recommendations.append(AzureRecommendation(
                    resource_id=vm["id"],
                    resource_name=vm["name"],
                    resource_type="VirtualMachine",
                    recommendation_type=AzureRecommendationType.IDLE_RESOURCE,
                    current_cost=monthly_cost,
                    recommended_cost=0,
                    potential_savings=monthly_cost * 0.9,  # Save 90% by stopping
                    confidence=0.80,
                    action=f"Stop idle VM {vm['name']} in {vm['location']}. Avg CPU: {avg_cpu:.1f}%, Monthly Cost: ${monthly_cost:.2f}",
                ))

        return recommendations

    def get_orphaned_disks(self) -> List[AzureRecommendation]:
        """Find unattached managed disks"""
        recommendations = []

        try:
            for disk in self.compute_client.disks.list():
                if disk.managed_by is None and disk.disk_state == "Unattached":
                    size_gb = disk.disk_size_gb
                    hourly_price = size_gb * 0.000112  # Azure managed disk pricing

                    recommendations.append(AzureRecommendation(
                        resource_id=disk.id,
                        resource_name=disk.name,
                        resource_type="ManagedDisk",
                        recommendation_type=AzureRecommendationType.TERMINATION,
                        current_cost=hourly_price * 24 * 30,
                        recommended_cost=0,
                        potential_savings=hourly_price * 24 * 30,
                        confidence=0.95,
                        action=f"Delete unattached disk {disk.name} ({size_gb} GB)",
                    ))
        except Exception as e:
            print(f"Error getting disk info: {e}")

        return recommendations

    def get_storage_optimization(self) -> List[AzureRecommendation]:
        """Identify storage accounts that could use cooler tiers"""
        recommendations = []

        try:
            for storage_account in self.resource_client.resources.list_by_resource_group(self.subscription_id):
                if storage_account.type == "Microsoft.Storage/storageAccounts":
                    # In production, check blob access patterns
                    recommendations.append(AzureRecommendation(
                        resource_id=storage_account.id,
                        resource_name=storage_account.name,
                        resource_type="StorageAccount",
                        recommendation_type=AzureRecommendationType.STORAGE_OPTIMIZATION,
                        current_cost=500.0,  # Placeholder
                        recommended_cost=250.0,
                        potential_savings=250.0,
                        confidence=0.70,
                        action=f"Enable Storage Blob Intelligence Tiering for {storage_account.name}",
                    ))
        except Exception as e:
            print(f"Error getting storage accounts: {e}")

        return recommendations

    def get_reserved_instance_recommendations(self) -> List[AzureRecommendation]:
        """Get Azure reserved instance recommendations"""
        recommendations = []

        scope = f"/subscriptions/{self.subscription_id}"

        try:
            # Get reservation recommendations
            for rec in self.cost_client.reservation_recommendations.list_for_azure_scope(scope):
                if rec.reservation_scope == "Single" and rec.term == "P1Y":
                    recommendations.append(AzureRecommendation(
                        resource_id=rec.resource_id,
                        resource_name=rec.resource_name,
                        resource_type="ReservedVM",
                        recommendation_type=AzureRecommendationType.RESERVATION,
                        current_cost=0,
                        recommended_cost=rec.savings_per_month or 0,
                        potential_savings=rec.total_cost_to_save or 0,
                        confidence=rec.recommended_quantity or 0.5,
                        action=f"Purchase 1-year reservation for {rec.resource_name}",
                        implementation_cost=rec.total_cost_if_bought_up_front or 0,
                    ))
        except Exception as e:
            print(f"Error getting RI recommendations: {e}")

        return recommendations

    def get_azure_hybrid_benefit_recommendations(self) -> List[AzureRecommendation]:
        """Identify Windows VMs eligible for Azure Hybrid Benefit"""
        recommendations = []
        vms = self.get_vms()

        for vm in vms:
            # Check if it's a Windows VM with eligible licensing
            # In production, check marketplace image reference
            if "Windows" in vm.get("vm_size", "") or vm.get("tags", {}).get("OS") == "Windows":
                vm_size = vm["vm_size"]
                linux_price = self._get_vm_hourly_price(vm_size.replace("Standard_", ""))
                windows_price = linux_price * 1.3  # Approx 30% premium for Windows

                savings = (windows_price - linux_price) * 24 * 30

                recommendations.append(AzureRecommendation(
                    resource_id=vm["id"],
                    resource_name=vm["name"],
                    resource_type="VirtualMachine",
                    recommendation_type=AzureRecommendationType.AZURE_HYBRID_BENEFIT,
                    current_cost=windows_price * 24 * 30,
                    recommended_cost=linux_price * 24 * 30,
                    potential_savings=savings,
                    confidence=0.90,
                    action=f"Apply Azure Hybrid Benefit for {vm['name']} (save {(windows_price - linux_price) / windows_price * 100:.1f}%)",
                ))

        return recommendations

    def get_spot_vm_opportunities(self) -> List[AzureRecommendation]:
        """Identify VMs that could use Low-Priority VMs (Azure Spot)"""
        recommendations = []
        vms = self.get_vms()

        for vm in vms:
            if vm["power_state"] != "running":
                continue

            # Check for batch/dev/test workloads
            workload = vm["tags"].get("Workload", "").lower()
            env = vm["tags"].get("Environment", "").lower()

            if workload in ["batch", "analytics", "ci-cd"] or env in ["dev", "test"]:
                vm_size = vm["vm_size"]
                current_price = self._get_vm_hourly_price(vm_size)

                # Spot typically 60-90% discount
                spot_price = current_price * 0.30

                recommendations.append(AzureRecommendation(
                    resource_id=vm["id"],
                    resource_name=vm["name"],
                    resource_type="VirtualMachine",
                    recommendation_type=AzureRecommendationType.SPOT_VM,
                    current_cost=current_price * 24 * 30,
                    recommended_cost=spot_price * 24 * 30,
                    potential_savings=(current_price - spot_price) * 24 * 30,
                    confidence=0.75,
                    action=f"Convert {vm['name']} to Spot VM for up to 70% savings",
                ))

        return recommendations

    def optimize_all(self) -> Dict[str, Any]:
        """Run all optimizations and return consolidated report"""
        all_recommendations = []

        all_recommendations.extend(self.identify_idle_vms())
        all_recommendations.extend(self.get_orphaned_disks())
        all_recommendations.extend(self.get_storage_optimization())
        all_recommendations.extend(self.get_reserved_instance_recommendations())
        all_recommendations.extend(self.get_azure_hybrid_benefit_recommendations())
        all_recommendations.extend(self.get_spot_vm_opportunities())

        all_recommendations.sort(key=lambda x: x.potential_savings, reverse=True)

        total_savings = sum(r.potential_savings for r in all_recommendations)
        by_type = {}
        for r in all_recommendations:
            by_type[r.recommendation_type.value] = by_type.get(r.recommendation_type.value, 0) + r.potential_savings

        return {
            "recommendations": all_recommendations,
            "total_potential_savings": total_savings,
            "summary_by_type": by_type,
            "timestamp": datetime.datetime.now().isoformat()
        }