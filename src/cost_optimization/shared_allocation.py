"""
Shared Cost Allocation Engine
Allocate shared costs (networking, security, platform services) across business owners
"""

from typing import List, Dict, Any, Optional, Callable
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
import json


class AllocationMethod(Enum):
    FIXED_PERCENTAGE = "fixed_percentage"
    EQUAL_SPLIT = "equal_split"
    USAGE_BASED = "usage_based"
    TEMPLATE_BASED = "template_based"
    CUSTOM = "custom"


@dataclass
class SharedCostPool:
    id: str
    name: str
    description: str
    total_cost: float
    currency: str = "USD"
    created_at: datetime = field(default_factory=datetime.now)
    is_active: bool = True


@dataclass
class AllocationRule:
    id: str
    pool_id: str
    method: AllocationMethod
    targets: List[Dict[str, Any]]  # [{"dimension": "tag", "value": "Engineering", "percentage": 40}]
    created_at: datetime = field(default_factory=datetime.now)
    is_active: bool = True


@dataclass
class AllocationResult:
    allocation_id: str
    pool_id: str
    target: str
    allocated_cost: float
    original_cost: float
    allocation_percentage: float
    allocation_method: str
    allocated_at: datetime = field(default_factory=datetime.now)


@dataclass
class AllocationPreview:
    pool_id: str
    pool_name: str
    total_cost: float
    allocations: List[Dict[str, Any]]
    unallocated: float
    is_valid: bool
    warnings: List[str] = field(default_factory=list)


class SharedCostAllocator:
    """Engine for allocating shared costs across resources and owners"""

    def __init__(self):
        self.pools: List[SharedCostPool] = []
        self.rules: List[AllocationRule] = []
        self.allocations: List[AllocationResult] = []

    def create_pool(self, name: str, description: str,
                    total_cost: float, currency: str = "USD") -> SharedCostPool:
        """Create a new shared cost pool"""
        pool_id = f"pool_{len(self.pools) + 1}_{int(datetime.now().timestamp())}"
        pool = SharedCostPool(
            id=pool_id,
            name=name,
            description=description,
            total_cost=total_cost,
            currency=currency
        )
        self.pools.append(pool)
        return pool

    def create_rule(self, pool_id: str, method: AllocationMethod,
                    targets: List[Dict[str, Any]]) -> AllocationRule:
        """Create an allocation rule for a pool"""

        # Validate percentages sum to 100
        total_pct = sum(t.get('percentage', 0) for t in targets)
        if total_pct > 100:
            raise ValueError("Allocation percentages cannot exceed 100%")

        rule_id = f"rule_{len(self.rules) + 1}_{int(datetime.now().timestamp())}"
        rule = AllocationRule(
            id=rule_id,
            pool_id=pool_id,
            method=method,
            targets=targets
        )
        self.rules.append(rule)
        return rule

    def preview_allocation(self, pool_id: str,
                          metrics: Optional[Dict[str, List[float]]] = None,
                          resources: Optional[List[Dict[str, Any]]] = None) -> AllocationPreview:
        """Preview allocation without making changes"""
        pool = next((p for p in self.pools if p.id == pool_id), None)
        if not pool:
            return AllocationPreview(
                pool_id=pool_id,
                pool_name="",
                total_cost=0,
                allocations=[],
                unallocated=0,
                is_valid=False,
                warnings=["Pool not found"]
            )

        rule = next((r for r in self.rules if r.pool_id == pool_id and r.is_active), None)
        if not rule:
            return AllocationPreview(
                pool_id=pool_id,
                pool_name=pool.name,
                total_cost=pool.total_cost,
                allocations=[],
                unallocated=pool.total_cost,
                is_valid=False,
                warnings=["No active allocation rule found"]
            )

        preview_result = self._apply_allocation(pool, rule, metrics, resources)

        return AllocationPreview(
            pool_id=pool_id,
            pool_name=pool.name,
            total_cost=pool.total_cost,
            allocations=preview_result['allocations'],
            unallocated=preview_result['unallocated'],
            is_valid=True,
            warnings=preview_result.get('warnings', [])
        )

    def _apply_allocation(self, pool: SharedCostPool, rule: AllocationRule,
                          metrics: Optional[Dict[str, List[float]]],
                          resources: Optional[List[Dict[str, Any]]]) -> Dict[str, Any]:
        """Apply allocation logic and return results"""
        allocations = []
        unallocated = pool.total_cost
        warnings = []

        if rule.method == AllocationMethod.FIXED_PERCENTAGE:
            allocated_pct = 0
            for target in rule.targets:
                pct = target.get('percentage', 0)
                allocated_pct += pct
                allocated_cost = pool.total_cost * (pct / 100)

                allocations.append({
                    "target": target.get('value', 'Unknown'),
                    "allocated_cost": allocated_cost,
                    "allocation_percentage": pct,
                    "method": "fixed_percentage"
                })

            unallocated = pool.total_cost * (1 - allocated_pct / 100)
            if unallocated > 0:
                warnings.append(f"{unallocated:.2f} unallocated ({allocated_pct}% distributed)")

        elif rule.method == AllocationMethod.EQUAL_SPLIT:
            num_targets = len(rule.targets)
            if num_targets > 0:
                per_target = pool.total_cost / num_targets
                pct = 100 / num_targets

                for target in rule.targets:
                    allocations.append({
                        "target": target.get('value', 'Unknown'),
                        "allocated_cost": per_target,
                        "allocation_percentage": pct,
                        "method": "equal_split"
                    })
                    unallocated -= per_target

        elif rule.method == AllocationMethod.USAGE_BASED and metrics:
            total_metric = sum(sum(m.values) for m in metrics.values() if isinstance(m, (list, tuple)))
            if total_metric > 0:
                for target in rule.targets:
                    dimension = target.get('dimension', 'service')
                    target_metric = sum(metrics.get(dimension, {}).get(target.get('value', ''), 0))
                    pct = (target_metric / total_metric) * 100 if total_metric > 0 else 0
                    allocated = pool.total_cost * (pct / 100)

                    allocations.append({
                        "target": target.get('value', 'Unknown'),
                        "allocated_cost": allocated,
                        "allocation_percentage": pct,
                        "method": "usage_based"
                    })
                    unallocated -= allocated

        elif rule.method == AllocationMethod.TEMPLATE_BASED and resources:
            # Template-based allocation using resource attributes
            resource_mapping = self._build_resource_map(resources)

            allocated_total = 0
            for target in rule.targets:
                dimension = target.get('dimension')
                template_value = target.get('value')
                matched_resources = resource_mapping.get(f"{dimension}:{template_value}", [])

                if matched_resources:
                    # Allocate proportionally to matched resource costs
                    matched_cost = sum(r.get('monthly_cost', r.get('cost', 0)) for r in matched_resources)
                    pct = (matched_cost / pool.total_cost * 100) if pool.total_cost > 0 else 0
                    allocated = pool.total_cost * (pct / 100)

                    allocations.append({
                        "target": f"{template_value} ({len(matched_resources)} resources)",
                        "allocated_cost": allocated,
                        "allocation_percentage": pct,
                        "method": "template_based",
                        "resource_count": len(matched_resources)
                    })
                    allocated_total += allocated

            unallocated = pool.total_cost - allocated_total

        return {
            "allocations": allocations,
            "unallocated": max(0, unallocated),
            "warnings": warnings
        }

    def _build_resource_map(self, resources: List[Dict[str, Any]]) -> Dict[str, List[Dict]]:
        """Build a mapping of resource attributes for allocation"""
        resource_map = {}

        for resource in resources:
            # Map by common dimensions
            tags = resource.get('tags', {})

            for key, value in tags.items():
                map_key = f"tag:{key}:{value}"
                if map_key not in resource_map:
                    resource_map[map_key] = []
                resource_map[map_key].append(resource)

            # Provider and type mapping
            provider = resource.get('provider', '')
            res_type = resource.get('type', resource.get('resource_type', ''))
            if provider:
                map_key = f"provider:{provider}"
                if map_key not in resource_map:
                    resource_map[map_key] = []
                resource_map[map_key].append(resource)

            if provider and res_type:
                map_key = f"provider:{provider}:type:{res_type}"
                if map_key not in resource_map:
                    resource_map[map_key] = []
                resource_map[map_key].append(resource)

        return resource_map

    def allocate(self, pool_id: str,
                 metrics: Optional[Dict[str, List[float]]] = None,
                 resources: Optional[List[Dict[str, Any]]] = None,
                 override_allocations: Optional[List[Dict[str, Any]]] = None) -> List[AllocationResult]:
        """Execute allocation and save results"""
        pool = next((p for p in self.pools if p.id == pool_id), None)
        if not pool:
            return []

        rule = next((r for r in self.rules if r.pool_id == pool_id and r.is_active), None)
        if not rule:
            return []

        # Use override if provided
        preview_data = override_allocations if override_allocations else self._apply_allocation(
            pool, rule, metrics, resources
        )

        self.allocations = []
        timestamp = datetime.now()

        for alloc in preview_data.get('allocations', []):
            result = AllocationResult(
                allocation_id=f"alloc_{int(timestamp.timestamp())}_{len(self.allocations)}",
                pool_id=pool_id,
                target=alloc['target'],
                allocated_cost=alloc['allocated_cost'],
                original_cost=pool.total_cost,
                allocation_percentage=alloc['allocation_percentage'],
                allocation_method=alloc['method']
            )
            self.allocations.append(result)

        return self.allocations

    def reconcile_allocation(self, pool_id: str) -> Dict[str, Any]:
        """Verify allocation totals match pool cost"""
        pool = next((p for p in self.pools if p.id == pool_id), None)
        if not pool:
            return {"valid": False, "error": "Pool not found"}

        allocations = [a for a in self.allocations if a.pool_id == pool_id]
        total_allocated = sum(a.allocated_cost for a in allocations)

        tolerance = 0.01  # 1 cent tolerance

        is_valid = abs(pool.total_cost - total_allocated) <= tolerance

        return {
            "valid": is_valid,
            "pool_total": pool.total_cost,
            "allocated_total": total_allocated,
            "difference": pool.total_cost - total_allocated,
            "allocation_count": len(allocations)
        }

    def get_allocation_summary(self, pool_id: Optional[str] = None) -> Dict[str, Any]:
        """Get summary of all or specific allocations"""
        allocations = [a for a in self.allocations if a.pool_id == pool_id] if pool_id else self.allocations

        by_target = {}
        by_method = {}

        for alloc in allocations:
            by_target[alloc.target] = by_target.get(alloc.target, 0) + alloc.allocated_cost
            by_method[alloc.allocation_method] = by_method.get(alloc.allocation_method, 0) + alloc.allocated_cost

        pools = [a for a in allocations]
        unique_pools = len(set(a.pool_id for a in pools)) if pools else 0

        return {
            "total_pools": unique_pools,
            "total_allocations": len(allocations),
            "total_allocated_cost": sum(a.allocated_cost for a in allocations),
            "by_target": by_target,
            "by_method": by_method,
            "last_allocated": max(a.allocated_at for a in allocations).isoformat() if allocations else None
        }

    def export_allocations(self) -> str:
        """Export allocation results to JSON"""
        return json.dumps({
            "exported_at": datetime.now().isoformat(),
            "allocations": [{
                "allocation_id": a.allocation_id,
                "pool_id": a.pool_id,
                "target": a.target,
                "allocated_cost": a.allocated_cost,
                "original_cost": a.original_cost,
                "allocation_percentage": a.allocation_percentage,
                "allocation_method": a.allocation_method,
                "allocated_at": a.allocated_at.isoformat()
            } for a in self.allocations]
        }, indent=2)


# Common shared cost pools
def create_networking_pool(total_monthly_cost: float) -> SharedCostPool:
    """Create typical networking shared cost pool"""
    return SharedCostPool(
        name="Networking - Shared",
        description="Load balancers, NAT gateways, VPN, ExpressRoute, peering costs",
        total_cost=total_monthly_cost,
        currency="USD"
    )


def create_security_pool(total_monthly_cost: float) -> SharedCostPool:
    """Create typical security/shared services cost pool"""
    return SharedCostPool(
        name="Platform Security & Observability",
        description="Monitoring, logging, security tools, support charges",
        total_cost=total_monthly_cost,
        currency="USD"
    )


# Predefined allocation templates
NETWORKING_ALLOCATION_TEMPLATE = [
    {"dimension": "tag", "value": "Production", "percentage": 50},
    {"dimension": "tag", "value": "Staging", "percentage": 20},
    {"dimension": "tag", "value": "Development", "percentage": 15},
    {"dimension": "tag", "value": "Unknown", "percentage": 15}
]

SECURITY_ALLOCATION_TEMPLATE = [
    {"dimension": "tag", "value": "Engineering", "percentage": 40},
    {"dimension": "tag", "value": "Data", "percentage": 25},
    {"dimension": "tag", "value": "Platform", "percentage": 20},
    {"dimension": "tag", "value": "Security", "percentage": 10},
    {"dimension": "tag", "value": "Unknown", "percentage": 5}
]