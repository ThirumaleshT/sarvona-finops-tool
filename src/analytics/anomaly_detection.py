"""
Anomaly Detection Engine
Detect unusual cost patterns, spend spikes, and financial anomalies
"""

from typing import List, Dict, Any, Optional, Callable
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
import json
import math
from abc import ABC, abstractmethod


class AnomalyType(Enum):
    COST_SPIKE = "cost_spike"
    COST_DROP = "cost_drop"
    NEW_SERVICE = "new_service"
    UNUSUAL_REGION = "unusual_region"
    UNEXPECTED_ACCOUNT = "unexpected_account"
    PRICE_CHANGE = "price_change"
    USAGE_ANOMALY = "usage_anomaly"
    TAG_ANOMALY = "tag_anomaly"


class AnomalySeverity(Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class AnomalyStatus(Enum):
    DETECTED = "detected"
    INVESTIGATING = "investigating"
    ACKNOWLEDGED = "acknowledged"
    RESOLVED = "resolved"
    FALSE_POSITIVE = "false_positive"


@dataclass
class Anomaly:
    id: str
    anomaly_type: AnomalyType
    severity: AnomalySeverity
    resource_id: str
    resource_name: str
    provider: str
    period: str
    actual_value: float
    expected_value: float
    deviation_percent: float
    confidence: float
    detected_at: datetime
    explanation: str
    suggested_actions: List[str] = field(default_factory=list)
    related_anomalies: List[str] = field(default_factory=list)
    status: AnomalyStatus = AnomalyStatus.DETECTED
    assigned_to: str = ""
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)


class DetectionAlgorithm(ABC):
    """Abstract base class for anomaly detection algorithms"""

    @abstractmethod
    def detect(self, data: List[Dict[str, Any]],
               context: Dict[str, Any]) -> List[Anomaly]:
        """Detect anomalies in the provided data"""
        pass

    @abstractmethod
    def get_name(self) -> str:
        """Return algorithm name"""
        pass


class ThresholdAnomalyDetector(DetectionAlgorithm):
    """Simple threshold-based anomaly detection"""

    def __init__(self, threshold_percent: float = 30.0):
        self.threshold_percent = threshold_percent

    def detect(self, data: List[Dict[str, Any]],
               context: Dict[str, Any]) -> List[Anomaly]:
        anomalies = []
        baseline = context.get('baseline_cost', 0)

        if baseline <= 0:
            return anomalies

        for item in data:
            actual = item.get('amount', 0)
            deviation = ((actual - baseline) / baseline * 100) if baseline > 0 else 0

            if abs(deviation) > self.threshold_percent:
                severity = AnomalySeverity.CRITICAL if abs(deviation) > 50 else \
                          AnomalySeverity.HIGH if abs(deviation) > 40 else \
                          AnomalySeverity.MEDIUM

                anomaly = Anomaly(
                    id=f"thr_{abs(int(deviation))}_{int(datetime.now().timestamp())}",
                    anomaly_type=AnomalyType.COST_SPIKE if deviation > 0 else AnomalyType.COST_DROP,
                    severity=severity,
                    resource_id=item.get('resource_id', item.get('id', 'unknown')),
                    resource_name=item.get('name', item.get('resource_name', 'Unknown')),
                    provider=item.get('provider', 'unknown'),
                    period=item.get('period', 'current'),
                    actual_value=actual,
                    expected_value=baseline,
                    deviation_percent=deviation,
                    confidence=min(0.95, 0.7 + abs(deviation) / 100),
                    detected_at=datetime.now(),
                    explanation=f"Cost deviates {deviation:.1f}% from baseline",
                    suggested_actions=self._get_suggestions(item, deviation)
                )
                anomalies.append(anomaly)

        return anomalies

    def get_name(self) -> str:
        return "threshold"

    def _get_suggestions(self, item: Dict[str, Any], deviation: float) -> List[str]:
        suggestions = []
        if deviation > 0:
            suggestions.append("Investigate recent deployments or usage increases")
            suggestions.append("Check for new services or resources")
        else:
            suggestions.append("Verify billing data completeness")
            suggestions.append("Check for service disruptions or deletions")
        suggestions.append("Review tags and resource ownership")
        return suggestions


class StatisticalAnomalyDetector(DetectionAlgorithm):
    """Statistical anomaly detection using standard deviation"""

    def __init__(self, std_threshold: float = 2.0):
        self.std_threshold = std_threshold

    def detect(self, data: List[Dict[str, Any]],
               context: Dict[str, Any]) -> List[Anomaly]:
        anomalies = []

        if not data:
            return anomalies

        amounts = [d.get('amount', 0) for d in data]
        n = len(amounts)

        if n < 3:
            return anomalies

        mean = sum(amounts) / n
        variance = sum((x - mean) ** 2 for x in amounts) / n
        std = math.sqrt(variance)

        if std == 0:
            return anomalies

        for item in data:
            amount = item.get('amount', 0)
            z_score = (amount - mean) / std if std > 0 else 0

            if abs(z_score) > self.std_threshold:
                severity = AnomalySeverity.CRITICAL if abs(z_score) > 3 else \
                          AnomalySeverity.HIGH if abs(z_score) > 2.5 else \
                          AnomalySeverity.MEDIUM

                deviation = ((amount - mean) / mean * 100) if mean > 0 else 0

                anomaly = Anomaly(
                    id=f"stat_{abs(int(z_score))}_{int(datetime.now().timestamp())}",
                    anomaly_type=AnomalyType.USAGE_ANOMALY,
                    severity=severity,
                    resource_id=item.get('resource_id', item.get('id', 'unknown')),
                    resource_name=item.get('name', item.get('resource_name', 'Unknown')),
                    provider=item.get('provider', 'unknown'),
                    period=item.get('period', 'current'),
                    actual_value=amount,
                    expected_value=mean,
                    deviation_percent=deviation,
                    confidence=min(0.90, 0.6 + abs(z_score) / 5),
                    detected_at=datetime.now(),
                    explanation=f"Statistical outlier (z-score: {z_score:.2f})",
                    suggested_actions=[
                        "Compare with similar time periods",
                        "Check for seasonal patterns",
                        "Review resource utilization metrics"
                    ]
                )
                anomalies.append(anomaly)

        return anomalies

    def get_name(self) -> str:
        return "statistical"


class MovingAverageAnomalyDetector(DetectionAlgorithm):
    """Moving average-based anomaly detection for time series"""

    def __init__(self, window: int = 7, threshold: float = 2.0):
        self.window = window
        self.threshold = threshold

    def detect(self, data: List[Dict[str, Any]],
               context: Dict[str, Any]) -> List[Anomaly]:
        anomalies = []

        if len(data) < self.window + 1:
            return anomalies

        # Sort by date
        sorted_data = sorted(data, key=lambda x: x.get('date', ''))

        for i in range(self.window, len(sorted_data)):
            current = sorted_data[i]
            window_data = sorted_data[i - self.window:i]

            window_amounts = [d.get('amount', 0) for d in window_data]
            avg = sum(window_amounts) / len(window_amounts) if window_amounts else 0
            std = math.sqrt(sum((x - avg) ** 2 for x in window_amounts) / len(window_amounts)) if window_amounts else 0

            current_amount = current.get('amount', 0)
            if std > 0:
                deviation = (current_amount - avg) / std
                if abs(deviation) > self.threshold:
                    anomaly = Anomaly(
                        id=f"ma_{abs(int(deviation))}_{int(datetime.now().timestamp())}",
                        anomaly_type=AnomalyType.COST_SPIKE if deviation > 0 else AnomalyType.COST_DROP,
                        severity=AnomalySeverity.MEDIUM if abs(deviation) < 3 else AnomalySeverity.HIGH,
                        resource_id=current.get('resource_id', current.get('id', 'unknown')),
                        resource_name=current.get('name', current.get('resource_name', 'Unknown')),
                        provider=current.get('provider', 'unknown'),
                        period=current.get('date', 'current'),
                        actual_value=current_amount,
                        expected_value=avg,
                        deviation_percent=((current_amount - avg) / avg * 100) if avg > 0 else 0,
                        confidence=min(0.95, 0.7 + abs(deviation) / 10),
                        detected_at=datetime.now(),
                        explanation=f"Moving average deviation exceeded {self.threshold}σ",
                        suggested_actions=[
                            "Compare with same day last week",
                            "Check for unusual activity patterns",
                            "Review scheduled maintenance or deployments"
                        ]
                    )
                    anomalies.append(anomaly)

        return anomalies

    def get_name(self) -> str:
        return "moving_average"


class AnomalyDetectionEngine:
    """Main anomaly detection engine"""

    def __init__(self):
        self.anomalies: List[Anomaly] = []
        self.detectors: Dict[str, DetectionAlgorithm] = {
            "threshold": ThresholdAnomalyDetector(threshold_percent=30.0),
            "statistical": StatisticalAnomalyDetector(std_threshold=2.0),
            "moving_average": MovingAverageAnomalyDetector(window=7, threshold=2.0)
        }
        self._detection_results = {}

    def add_detector(self, name: str, detector: DetectionAlgorithm):
        """Add a custom detection algorithm"""
        self.detectors[name] = detector

    def detect_anomalies(self, data: List[Dict[str, Any]],
                         detectors: Optional[List[str]] = None,
                         context: Optional[Dict[str, Any]] = None) -> List[Anomaly]:
        """Run anomaly detection with specified algorithms"""
        self.anomalies = []
        context = context or {}

        if detectors is None:
            detectors = list(self.detectors.keys())

        all_anomalies = []
        for detector_name in detectors:
            detector = self.detectors.get(detector_name)
            if detector:
                detected = detector.detect(data, context)
                detector.anomalies = detected
                self._detection_results[detector_name] = detected
                all_anomalies.extend(detected)

        # Deduplicate and merge similar anomalies
        self.anomalies = self._deduplicate_anomalies(all_anomalies)
        return self.anomalies

    def _deduplicate_anomalies(self, anomalies: List[Anomaly]) -> List[Anomaly]:
        """Merge duplicates and group related anomalies"""
        deduped = []
        seen = {}

        for anomaly in anomalies:
            key = f"{anomaly.resource_id}_{anomaly.anomaly_type.value}_{anomaly.period}"
            if key not in seen:
                seen[key] = anomaly
                deduped.append(anomaly)

        return deduped

    def acknowledge_anomaly(self, anomaly_id: str, analyst: str = "") -> bool:
        """Mark anomaly as acknowledged"""
        for anomaly in self.anomalies:
            if anomaly.id == anomaly_id:
                anomaly.status = AnomalyStatus.ACKNOWLEDGED
                anomaly.assigned_to = analyst
                anomaly.updated_at = datetime.now()
                return True
        return False

    def resolve_anomaly(self, anomaly_id: str, notes: str = "") -> bool:
        """Mark anomaly as resolved"""
        for anomaly in self.anomalies:
            if anomaly.id == anomaly_id:
                anomaly.status = AnomalyStatus.RESOLVED
                anomaly.explanation = notes
                anomaly.updated_at = datetime.now()
                return True
        return False

    def get_anomalies_by_severity(self,
                                  severity: AnomalySeverity) -> List[Anomaly]:
        """Filter anomalies by severity"""
        return [a for a in self.anomalies if a.severity == severity]

    def get_anomalies_by_status(self,
                                status: AnomalyStatus) -> List[Anomaly]:
        """Filter anomalies by status"""
        return [a for a in self.anomalies if a.status == status]

    def get_anomalies_by_type(self,
                              anomaly_type: AnomalyType) -> List[Anomaly]:
        """Filter anomalies by type"""
        return [a for a in self.anomalies if a.anomaly_type == anomaly_type]

    def create_incident(self, anomalies: List[Anomaly],
                        title: str) -> Dict[str, Any]:
        """Group related anomalies into an incident"""
        incident_id = f"inc_{int(datetime.now().timestamp())}"

        affected_resources = list(set(a.resource_id for a in anomalies))
        total_impact = sum(a.actual_value - a.expected_value for a in anomalies if a.actual_value > a.expected_value)

        incident = {
            "id": incident_id,
            "title": title,
            "created_at": datetime.now().isoformat(),
            "anomaly_ids": [a.id for a in anomalies],
            "affected_resources": affected_resources,
            "total_impact": total_impact,
            "severity": max((a.severity for a in anomalies), key=lambda s: list(AnomalySeverity).index(s)),
            "status": AnomalyStatus.DETECTED.value
        }

        return incident

    def export_anomalies(self) -> str:
        """Export anomalies to JSON"""
        data = {
            "exported_at": datetime.now().isoformat(),
            "total_anomalies": len(self.anomalies),
            "by_severity": {
                s.value: len([a for a in self.anomalies if a.severity == s])
                for s in AnomalySeverity
            },
            "anomalies": [{
                "id": a.id,
                "type": a.anomaly_type.value,
                "severity": a.severity.value,
                "resource_id": a.resource_id,
                "resource_name": a.resource_name,
                "provider": a.provider,
                "period": a.period,
                "actual_value": a.actual_value,
                "expected_value": a.expected_value,
                "deviation_percent": a.deviation_percent,
                "confidence": a.confidence,
                "detected_at": a.detected_at.isoformat(),
                "explanation": a.explanation,
                "status": a.status.value,
                "suggested_actions": a.suggested_actions
            } for a in self.anomalies]
        }
        return json.dumps(data, indent=2)

    def get_detection_summary(self) -> Dict[str, Any]:
        """Get summary of detection results by algorithm"""
        summary = {
            "total_anomalies": len(self.anomalies),
            "by_detector": {},
            "by_severity": {},
            "resolved_count": len([a for a in self.anomalies if a.status == AnomalyStatus.RESOLVED])
        }

        for name, anomalies in self._detection_results.items():
            summary["by_detector"][name] = len(anomalies)

        for severity in AnomalySeverity:
            summary["by_severity"][severity.value] = len(
                [a for a in self.anomalies if a.severity == severity]
            )

        return summary


def detect_new_service_usage(previous_data: List[Dict[str, Any]],
                             current_data: List[Dict[str, Any]]) -> List[Anomaly]:
    """Detect newly appearing services"""
    previous_services = set(d.get('service') for d in previous_data)
    current_services = set(d.get('service') for d in current_data)

    new_services = current_services - previous_services
    anomalies = []

    for service in new_services:
        service_data = next((d for d in current_data if d.get('service') == service), None)
        if service_data:
            anomaly = Anomaly(
                id=f"new_svc_{service}_{int(datetime.now().timestamp())}",
                anomaly_type=AnomalyType.NEW_SERVICE,
                severity=AnomalySeverity.MEDIUM,
                resource_id=service,
                resource_name=service,
                provider=service_data.get('provider', 'unknown'),
                period=service_data.get('period', 'current'),
                actual_value=service_data.get('amount', 0),
                expected_value=0,
                deviation_percent=100,
                confidence=0.85,
                detected_at=datetime.now(),
                explanation=f"New service detected: {service}",
                suggested_actions=[
                    "Verify service deployment",
                    "Assign appropriate tags",
                    "Set baseline for monitoring"
                ]
            )
            anomalies.append(anomaly)

    return anomalies


def detect_tag_anomalies(resources: List[Dict[str, Any]]) -> List[Anomaly]:
    """Detect resources with missing or suspicious tags"""
    anomalies = []
    expected_tags = {'Environment', 'Project', 'Owner', 'CostCenter'}

    for resource in resources:
        resource_tags = set(resource.get('tags', {}).keys())
        missing_tags = expected_tags - resource_tags

        if missing_tags:
            anomaly = Anomaly(
                id=f"tag_miss_{resource.get('id', 'unknown')}_{int(datetime.now().timestamp())}",
                anomaly_type=AnomalyType.TAG_ANOMALY,
                severity=AnomalySeverity.LOW,
                resource_id=resource.get('id', 'unknown'),
                resource_name=resource.get('name', 'Unknown'),
                provider=resource.get('provider', 'unknown'),
                period='current',
                actual_value=0,
                expected_value=0,
                deviation_percent=0,
                confidence=0.90,
                detected_at=datetime.now(),
                explanation=f"Missing tags: {', '.join(missing_tags)}",
                suggested_actions=[f"Add missing tags: {', '.join(missing_tags)}"]
            )
            anomalies.append(anomaly)

    return anomalies