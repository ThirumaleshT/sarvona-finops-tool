"""
Governance and RBAC Engine
Role-based access control and governance compliance
"""

from typing import List, Dict, Any, Optional
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
import json


class ResourceType(Enum):
    VM = "vm"
    INSTANCE = "ec2"
    DATABASE = "database"
    STORAGE = "storage"
    CONTAINER = "container"
    NETWORK = "network"
    FUNCTION = "function"
    UNKNOWN = "unknown"


class ComplianceStatus(Enum):
    COMPLIANT = "compliant"
    NON_COMPLIANT = "non_compliant"
    WARNING = "warning"
    UNKNOWN = "unknown"


@dataclass
class UserRole:
    id: str
    name: str
    description: str
    permissions: List[str] = field(default_factory=list)
    is_admin: bool = False
    created_at: datetime = field(default_factory=datetime.now)


@dataclass
class User:
    id: str
    name: str
    email: str
    role_id: str
    tenant_id: str = ""
    is_active: bool = True
    created_at: datetime = field(default_factory=datetime.now)


@dataclass
class GovernanceRule:
    id: str
    name: str
    description: str
    resource_type: str
    condition: str
    action: str
    severity: str  # low, medium, high, critical
    enabled: bool = True
    created_at: datetime = field(default_factory=datetime.now)


@dataclass
class ComplianceReport:
    resource_id: str
    resource_name: str
    resource_type: str
    rule_id: str
    status: ComplianceStatus
    compliance_score: float
    violations: List[Dict[str, Any]]
    recommendations: List[str]
    assessed_at: datetime = field(default_factory=datetime.now)


class RBACEngine:
    """Role-based access control engine"""

    def __init__(self):
        self.users: List[User] = []
        self.roles: List[UserRole] = []
        self._setup_default_roles()

    def _setup_default_roles(self):
        """Initialize default RBAC roles"""
        self.roles = [
            UserRole(
                id="role_admin",
                name="Administrator",
                description="Full access to all features and settings",
                permissions=["read", "write", "delete", "admin", "approve", "export"],
                is_admin=True
            ),
            UserRole(
                id="role_finance",
                name="Finance",
                description="Budgets, forecasts, and financial reporting access",
                permissions=["read", "write_budgets", "read_forecasts", "export_reports"]
            ),
            UserRole(
                id="role_eng_lead",
                name="Engineering Lead",
                description="Team cost views and optimization recommendations",
                permissions=["read", "read_recommendations", "approve_optimizations"]
            ),
            UserRole(
                id="role_eng_member",
                name="Engineering Member",
                description="Personal cost views and recommendations",
                permissions=["read", "read_own_costs", "read_recommendations"]
            ),
            UserRole(
                id="role_viewer",
                name="Viewer",
                description="Read-only access to dashboards and reports",
                permissions=["read"]
            )
        ]

    def create_role(self, name: str, description: str,
                    permissions: List[str], is_admin: bool = False) -> UserRole:
        """Create a new custom role"""
        role_id = f"role_{len(self.roles) + 1}_{int(datetime.now().timestamp())}"
        role = UserRole(
            id=role_id,
            name=name,
            description=description,
            permissions=permissions,
            is_admin=is_admin
        )
        self.roles.append(role)
        return role

    def create_user(self, name: str, email: str, role_id: str,
                    tenant_id: str = "") -> User:
        """Create a new user"""
        user_id = f"user_{len(self.users) + 1}_{int(datetime.now().timestamp())}"
        user = User(
            id=user_id,
            name=name,
            email=email,
            role_id=role_id,
            tenant_id=tenant_id
        )
        self.users.append(user)
        return user

    def has_permission(self, user_id: str, permission: str) -> bool:
        """Check if user has a specific permission"""
        user = next((u for u in self.users if u.id == user_id), None)
        if not user:
            return False

        role = next((r for r in self.roles if r.id == user.role_id), None)
        if not role:
            return False

        return permission in role.permissions

    def get_user_permissions(self, user_id: str) -> List[str]:
        """Get all permissions for a user"""
        user = next((u for u in self.users if u.id == user_id), None)
        if not user:
            return []

        role = next((r for r in self.roles if r.id == user.role_id), None)
        return role.permissions if role else []

    def can_access(self, user_id: str, resource_type: str) -> bool:
        """Check if user can access a resource type"""
        return self.has_permission(user_id, "read")


class GovernanceEngine:
    """Governance compliance engine"""

    def __init__(self):
        self.rules: List[GovernanceRule] = []
        self.reports: List[ComplianceReport] = []
        self._setup_default_rules()

    def _setup_default_rules(self):
        """Initialize default governance rules"""
        self.rules = [
            GovernanceRule(
                id="rule_disks",
                name="Unattached Disks",
                description="EBS volumes and managed disks not attached to any VM",
                resource_type="disk",
                condition="attachment_count = 0",
                action="Delete disk after backup verification",
                severity="high"
            ),
            GovernanceRule(
                id="rule_tags",
                name="Owner Tag Required",
                description="All resources must have an Owner tag",
                resource_type="all",
                condition="tags.Owner IS NOT NULL",
                action="Add Owner tag or escalate",
                severity="low"
            ),
            GovernanceRule(
                id="rule_idle_vm",
                name="Idle VM/Instance",
                description="VMs or EC2 instances idle for more than 168 hours",
                resource_type="vm,instance",
                condition="avg_cpu < 10% AND runtime > 168h",
                action="Stop or terminate after owner approval",
                severity="high"
            ),
            GovernanceRule(
                id="rule_env_tag",
                name="Environment Tag Compliance",
                description="Resources must have Environment tag (prod/staging/dev)",
                resource_type="all",
                condition="tags.Environment IN [prod,staging,dev,qa]",
                action="Add correct Environment tag",
                severity="medium"
            ),
            GovernanceRule(
                id="rule_public_ip",
                name="Public IP Monitoring",
                description="Track and report on public IP assignments",
                resource_type="network",
                condition="public_ip IS NOT NULL",
                action="Review necessity and implement approved patterns",
                severity="medium"
            ),
            GovernanceRule(
                id="rule_retention",
                name="Data Retention Policy",
                description="Ensure storage resources follow retention policies",
                resource_type="storage",
                condition="age < retention_policy OR backup_exists = true",
                action="Verify retention configuration",
                severity="medium"
            )
        ]

    def create_rule(self, name: str, description: str,
                    resource_type: str, condition: str,
                    action: str, severity: str = "medium") -> GovernanceRule:
        """Create a new governance rule"""
        rule_id = f"rule_{len(self.rules) + 1}_{int(datetime.now().timestamp())}"
        rule = GovernanceRule(
            id=rule_id,
            name=name,
            description=description,
            resource_type=resource_type,
            condition=condition,
            action=action,
            severity=severity
        )
        self.rules.append(rule)
        return rule

    def assess_resource(self, resource: Dict[str, Any]) -> ComplianceReport:
        """Assess a resource against all applicable rules"""
        resource_id = resource.get('id', resource.get('resource_id', 'unknown'))
        resource_name = resource.get('name', resource.get('resource_name', 'Unknown'))
        resource_type = resource.get('type', resource.get('resource_type', 'unknown'))

        violations = []
        recommendations = []

        for rule in self.rules:
            if not rule.enabled:
                continue
            if rule.resource_type != "all" and rule.resource_type not in resource_type:
                continue

            is_compliant, violation = self._check_rule(resource, rule)
            if not is_compliant:
                violations.append({
                    "rule_id": rule.id,
                    "rule_name": rule.name,
                    "violation": violation
                })
                recommendations.append(rule.action)

        # Calculate compliance score (0-100)
        applicable_rules = [r for r in self.rules if r.enabled and
                           (r.resource_type == "all" or r.resource_type in resource_type)]
        compliance_count = len(applicable_rules) - len(violations)
        score = (compliance_count / len(applicable_rules) * 100) if applicable_rules else 100

        status = ComplianceStatus.COMPLIANT if score >= 95 else \
                ComplianceStatus.WARNING if score >= 80 else \
                ComplianceStatus.NON_COMPLIANT

        report = ComplianceReport(
            resource_id=resource_id,
            resource_name=resource_name,
            resource_type=resource_type,
            rule_id=f"composite_{len(violations)}",
            status=status,
            compliance_score=score,
            violations=violations,
            recommendations=list(set(recommendations))
        )

        self.reports.append(report)
        return report

    def _check_rule(self, resource: Dict[str, Any],
                    rule: GovernanceRule) -> tuple:
        """Check if a resource violates a specific rule"""
        violations = []

        if "Owner tag" in rule.name and "Owner" not in resource.get('tags', {}):
            violations.append("Missing Owner tag")

        if "Unattached" in rule.name:
            attachments = resource.get('attachments', [])
            if not attachments:
                violations.append("No attachments found")

        if "Idle" in rule.name:
            avg_cpu = resource.get('metrics', {}).get('avg_cpu', 100)
            runtime = resource.get('runtime_hours', 0)
            if avg_cpu >= 10 or runtime < 168:
                violations.append(f"Not idle (CPU: {avg_cpu}%, Runtime: {runtime}h)")

        if "Environment" in rule.name and "Environment" not in resource.get('tags', {}):
            violations.append("Missing Environment tag")

        is_compliant = len(violations) == 0
        return is_compliant, "; ".join(violations) if violations else "Compliant"

    def get_governance_summary(self) -> Dict[str, Any]:
        """Get overall governance compliance summary"""
        if not self.reports:
            return {"total_resources": 0, "compliance_rate": 100}

        total = len(self.reports)
        compliant = len([r for r in self.reports if r.status == ComplianceStatus.COMPLIANT])
        non_compliant = len([r for r in self.reports if r.status == ComplianceStatus.NON_COMPLIANT])
        warnings = len([r for r in self.reports if r.status == ComplianceStatus.WARNING])

        return {
            "total_resources": total,
            "compliant_count": compliant,
            "warning_count": warnings,
            "non_compliant_count": non_compliant,
            "compliance_rate": (compliant / total * 100) if total > 0 else 100,
            "violations_count": sum(len(r.violations) for r in self.reports)
        }

    def export_compliance_report(self) -> str:
        """Export compliance reports to JSON"""
        return json.dumps({
            "exported_at": datetime.now().isoformat(),
            "summary": self.get_governance_summary(),
            "rules": [{
                "id": r.id,
                "name": r.name,
                "description": r.description,
                "severity": r.severity,
                "enabled": r.enabled
            } for r in self.rules],
            "reports": [{
                "resource_id": r.resource_id,
                "resource_name": r.resource_name,
                "resource_type": r.resource_type,
                "status": r.status.value,
                "compliance_score": r.compliance_score,
                "violations": r.violations,
                "recommendations": r.recommendations
            } for r in self.reports]
        }, indent=2)


def get_standard_governance_rules() -> List[Dict[str, Any]]:
    """Return standard governance rules for quick setup"""
    return [
        {
            "name": "Unattached Disks",
            "description": "Identify and manage unattached storage volumes",
            "resource_type": "disk,volume",
            "condition": "attachment_count = 0",
            "action": "Delete after backup verification",
            "severity": "high"
        },
        {
            "name": "Instance Tagging",
            "description": "Ensure all instances have proper tagging",
            "resource_type": "instance,vm",
            "condition": "tags.Owner IS NOT NULL AND tags.Environment IS NOT NULL",
            "action": "Apply missing tags",
            "severity": "medium"
        },
        {
            "name": "S3 Bucket Access",
            "description": "Check S3 buckets are not publicly accessible",
            "resource_type": "s3",
            "condition": "public_access_block_enabled = true",
            "action": "Enable public access block",
            "severity": "high"
        }
    ]