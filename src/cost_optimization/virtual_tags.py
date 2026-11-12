"""
Virtual Tags Engine
Rule-based cost allocation system for multi-cloud billing attribution
"""

from typing import List, Dict, Any, Optional
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
import json
import re
import copy


class VirtualTagType(Enum):
    BUSINESS_UNIT = "business_unit"
    PRODUCT = "product"
    TEAM = "team"
    ENVIRONMENT = "environment"
    CUSTOMER = "customer"
    COST_CENTER = "cost_center"


@dataclass
class VirtualTagRule:
    id: str
    name: str
    tag_type: VirtualTagType
    description: str
    priority: int
    conditions: List[Dict[str, Any]]
    output_value: str
    created_at: datetime
    updated_at: datetime
    is_active: bool = True
    version: int = 1


@dataclass
class VirtualTagAssignment:
    resource_id: str
    resource_name: str
    provider: str
    resource_type: str
    assigned_tag: str
    tag_type: str
    rule_id: str
    confidence: float
    matched_condition: str


@dataclass
class UnallocatedCost:
    provider: str
    resource_type: str
    estimated_cost: float
    count: int
    reason: str


class VirtualTagsEngine:
    """Virtual tags engine for multi-cloud cost allocation"""

    def __init__(self):
        self.rules: List[VirtualTagRule] = []
        self.assignments: List[VirtualTagAssignment] = []
        self.unallocated_history: List[Dict[str, Any]] = []

    def create_rule(self, name: str, tag_type: VirtualTagType,
                    conditions: List[Dict[str, Any]], output_value: str,
                    priority: int = 100) -> VirtualTagRule:
        """Create a new virtual tag rule"""
        rule_id = f"rule_{len(self.rules) + 1}_{int(datetime.now().timestamp())}"
        rule = VirtualTagRule(
            id=rule_id,
            name=name,
            tag_type=tag_type,
            description=f"Auto-generated rule for {tag_type.value}",
            priority=priority,
            conditions=conditions,
            output_value=output_value,
            created_at=datetime.now(),
            updated_at=datetime.now()
        )
        self.rules.append(rule)
        return rule

    def delete_rule(self, rule_id: str) -> bool:
        """Delete a virtual tag rule"""
        for i, rule in enumerate(self.rules):
            if rule.id == rule_id:
                self.rules.pop(i)
                return True
        return False

    def update_rule(self, rule_id: str, **kwargs) -> Optional[VirtualTagRule]:
        """Update an existing rule"""
        for rule in self.rules:
            if rule.id == rule_id:
                for key, value in kwargs.items():
                    if hasattr(rule, key):
                        setattr(rule, key, value)
                rule.updated_at = datetime.now()
                rule.version += 1
                return rule
        return None

    def _evaluate_condition(self, resource: Dict[str, Any], condition: Dict[str, Any]) -> bool:
        """Evaluate if a resource matches a condition"""
        match_type = condition.get('match', 'exact')
        key = condition.get('key', '')
        value = condition.get('value', '')
        pattern = condition.get('pattern', '')

        # Get resource value for the key
        resource_value = resource.get(key, '') or resource.get('tags', {}).get(key, '')
        if not resource_value:
            return False

        resource_str = str(resource_value).lower()
        value_str = str(value).lower()

        if match_type == 'exact':
            return resource_str == value_str
        elif match_type == 'contains':
            return value_str in resource_str
        elif match_type == 'regex':
            try:
                return bool(re.search(pattern or value, resource_str, re.IGNORECASE))
            except re.error:
                return False
        elif match_type == 'startswith':
            return resource_str.startswith(value_str)
        elif match_type == 'endswith':
            return resource_str.endswith(value_str)
        elif match_type == 'greater_than':
            try:
                return float(resource_value) > float(value)
            except (ValueError, TypeError):
                return False
        elif match_type == 'less_than':
            try:
                return float(resource_value) < float(value)
            except (ValueError, TypeError):
                return False

        return False

    def _evaluate_conditions(self, resource: Dict[str, Any],
                             conditions: List[Dict[str, Any]]) -> tuple[bool, str]:
        """Evaluate all conditions for a resource (AND logic within, OR across conditions)"""
        for condition in conditions:
            logic = condition.get('logic', 'AND')
            if logic == 'AND':
                if not all(self._evaluate_condition(resource, c) for c in condition.get('conditions', [])):
                    continue
                return True, json.dumps(condition)
            elif logic == 'OR':
                if any(self._evaluate_condition(resource, c) for c in condition.get('conditions', [])):
                    return True, json.dumps(condition)
        return False, ''

    def assign_tags_to_resources(self, resources: List[Dict[str, Any]]) -> List[VirtualTagAssignment]:
        """Assign virtual tags to resources based on rules"""
        self.assignments = []

        # Sort rules by priority (lower number = higher priority)
        sorted_rules = sorted(self.rules, key=lambda r: r.priority)

        for resource in resources:
            resource_id = resource.get('id') or resource.get('resource_id') or resource.get('Name', '')
            resource_name = resource.get('name') or resource.get('resource_name') or resource.get('Name', '')
            resource_type = resource.get('type') or resource.get('resource_type') or 'unknown'
            provider = resource.get('provider') or 'unknown'

            assigned = False
            for rule in sorted_rules:
                if not rule.is_active:
                    continue

                matches, matched_condition = self._evaluate_conditions(resource, rule.conditions)
                if matches:
                    assignment = VirtualTagAssignment(
                        resource_id=resource_id,
                        resource_name=resource_name,
                        provider=provider,
                        resource_type=resource_type,
                        assigned_tag=rule.output_value,
                        tag_type=rule.tag_type.value,
                        rule_id=rule.id,
                        confidence=0.95 if rule.priority < 100 else 0.85,
                        matched_condition=matched_condition
                    )
                    self.assignments.append(assignment)
                    assigned = True
                    break

            if not assigned:
                # Track unallocated for reporting
                self._track_unallocated(resource, provider, resource_type)

        return self.assignments

    def _track_unallocated(self, resource: Dict[str, Any], provider: str, resource_type: str):
        """Track unallocated resources and costs"""
        monthly_cost = resource.get('monthly_cost', resource.get('cost', 0))
        timestamp = datetime.now()

        entry = {
            "timestamp": timestamp,
            "provider": provider,
            "resource_type": resource_type,
            "estimated_cost": monthly_cost,
            "resource_count": 1,
            "sample_resource": str(resource)[:500]
        }

        self.unallocated_history.append(entry)

        # Keep last 30 days
        cutoff = timestamp - timedelta(days=30)
        self.unallocated_history = [
            e for e in self.unallocated_history
            if e["timestamp"] > cutoff
        ]

    def get_allocation_summary(self) -> Dict[str, Any]:
        """Get summary of tag allocation"""
        summary = {
            "total_resources": len(set(a.resource_id for a in self.assignments)),
            "by_tag": {},
            "by_type": {},
            "by_provider": {},
            "unallocated_count": len(self.unallocated_history),
            "total_unallocated_estimate": sum(e["estimated_cost"] for e in self.unallocated_history)
        }

        for assignment in self.assignments:
            tag = assignment.assigned_tag
            tag_type = assignment.tag_type
            provider = assignment.provider

            summary["by_tag"][tag] = summary["by_tag"].get(tag, 0) + 1
            if tag_type not in summary["by_type"]:
                summary["by_type"][tag_type] = {"count": 0, "tags": {}}
            summary["by_type"][tag_type]["count"] += 1
            summary["by_type"][tag_type]["tags"][tag] = \
                summary["by_type"][tag_type]["tags"].get(tag, 0) + 1

            if provider not in summary["by_provider"]:
                summary["by_provider"][provider] = 0
            summary["by_provider"][provider] += 1

        return summary

    def get_rule_preview(self, resources: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Preview how rules will assign tags before applying"""
        preview = {
            "total_resources": len(resources),
            "by_rule": {},
            "unallocated": [],
            "sample_mismatches": []
        }

        for rule in self.rules:
            matches = 0
            for resource in resources[:100]:  # Sample for preview
                match, _ = self._evaluate_conditions(resource, rule.conditions)
                if match:
                    matches += 1

            preview["by_rule"][rule.name] = {
                "rule_id": rule.id,
                "matches": matches,
                "estimated_percentage": (matches / min(len(resources), 100)) * 100 if resources else 0
            }

        return preview

    def get_cost_by_tag(self, resources: List[Dict[str, Any]],
                        assignments: List[VirtualTagAssignment]) -> Dict[str, float]:
        """Calculate cost distribution by virtual tag"""
        cost_by_tag = {}

        # Create lookup for assigned costs
        resource_to_cost = {}
        for r in resources:
            resource_id = r.get('id') or r.get('resource_id') or r.get('Name', '')
            cost = r.get('monthly_cost', r.get('cost', 0))
            resource_to_cost[resource_id] = cost

        for assignment in assignments:
            tag = assignment.assigned_tag
            resource_id = assignment.resource_id
            cost = resource_to_cost.get(resource_id, 0)
            cost_by_tag[tag] = cost_by_tag.get(tag, 0) + cost

        return cost_by_tag

    def export_rules(self) -> str:
        """Export rules to JSON for versioning/backup"""
        rules_data = []
        for rule in self.rules:
            rules_data.append({
                "id": rule.id,
                "name": rule.name,
                "tag_type": rule.tag_type.value,
                "description": rule.description,
                "priority": rule.priority,
                "conditions": rule.conditions,
                "output_value": rule.output_value,
                "is_active": rule.is_active,
                "version": rule.version,
                "created_at": rule.created_at.isoformat(),
                "updated_at": rule.updated_at.isoformat()
            })

        return json.dumps({
            "version": "1.0",
            "exported_at": datetime.now().isoformat(),
            "rules": rules_data
        }, indent=2)

    def import_rules(self, json_data: str) -> int:
        """Import rules from JSON"""
        try:
            data = json.loads(json_data)
            imported = 0

            for rule_data in data.get('rules', []):
                rule = VirtualTagRule(
                    id=rule_data['id'],
                    name=rule_data['name'],
                    tag_type=VirtualTagType(rule_data['tag_type']),
                    description=rule_data.get('description', ''),
                    priority=rule_data.get('priority', 100),
                    conditions=rule_data.get('conditions', []),
                    output_value=rule_data.get('output_value', ''),
                    created_at=datetime.fromisoformat(rule_data.get('created_at', datetime.now().isoformat())),
                    updated_at=datetime.fromisoformat(rule_data.get('updated_at', datetime.now().isoformat())),
                    is_active=rule_data.get('is_active', True),
                    version=rule_data.get('version', 1)
                )
                self.rules.append(rule)
                imported += 1

            return imported
        except (json.JSONDecodeError, KeyError, ValueError) as e:
            return -1

    def cleanup_rules(self) -> int:
        """Remove inactive rules older than 90 days"""
        cutoff = datetime.now() - timedelta(days=90)
        initial_count = len(self.rules)

        self.rules = [
            r for r in self.rules
            if r.is_active or r.updated_at > cutoff
        ]

        return initial_count - len(self.rules)


# Standard business mapping rules for common use cases
DEFAULT_RULES = [
    {
        "name": "Production Environment",
        "tag_type": "environment",
        "conditions": [{"key": "tags.Environment", "value": "prod", "match": "contains"}],
        "output_value": "Production",
        "priority": 10
    },
    {
        "name": "Development Environment",
        "tag_type": "environment",
        "conditions": [{"key": "tags.Environment", "value": "dev", "match": "contains"}],
        "output_value": "Development",
        "priority": 20
    },
    {
        "name": "Staging Environment",
        "tag_type": "environment",
        "conditions": [{"key": "tags.Environment", "value": "staging", "match": "contains"}],
        "output_value": "Staging",
        "priority": 20
    },
    {
        "name": "Cost Center - Engineering",
        "tag_type": "cost_center",
        "conditions": [{"key": "tags.Project", "value": "eng", "match": "contains"}],
        "output_value": "Engineering",
        "priority": 50
    },
    {
        "name": "Team - Platform",
        "tag_type": "team",
        "conditions": [{"key": "tags.Team", "value": "platform", "match": "contains"}],
        "output_value": "Platform Team",
        "priority": 50
    }
]


def create_default_rules_engine() -> VirtualTagsEngine:
    """Create an engine pre-populated with common business rules"""
    engine = VirtualTagsEngine()
    for rule_data in DEFAULT_RULES:
        engine.create_rule(
            name=rule_data["name"],
            tag_type=VirtualTagType(rule_data["tag_type"]),
            conditions=rule_data["conditions"],
            output_value=rule_data["output_value"],
            priority=rule_data["priority"]
        )
    return engine