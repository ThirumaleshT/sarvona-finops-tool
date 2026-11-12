"""
AI-Enhanced FinOps Engine
Combines CloudCheckr-style features with AI-powered optimization
"""

import boto3
import json
import re
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from collections import defaultdict


class AICapability(Enum):
    """AI-powered optimization capabilities"""
    AUTOMATED_RIGHTSIZING = "automated_rightsizing"
    DEMAND_FORECASTING = "demand_forecasting"
    ANOMALY_DETECTION = "anomaly_detection"
    ANOMALY_RECOMMENDATIONS = "anomaly_recommendations"
    BUDGET_PREDICTION = "budget_prediction"
    RESERVATION_OPTIMIZATION = "reservation_optimization"
    COMMITMENT_STRATEGY = "commitment_strategy"
    NETWORK_OPTIMIZATION = "network_optimization"
    SERVERLESS_ANALYSIS = "serverless_analysis"


@dataclass
class AIPrediction:
    """AI-generated cost prediction or recommendation"""
    category: str
    current_cost: float
    predicted_cost: float
    recommended_action: str
    confidence: float
    effort: str  # low, medium, high
    roi_months: float
    implementation_steps: List[str] = field(default_factory=list)


@dataclass
class ForecastData:
    """Cost forecasting data"""
    period: str  # daily, weekly, monthly
    predictions: List[Dict[str, Any]]
    confidence_range: Tuple[float, float]
    variance_percent: float


class FinOpsAIEngine:
    """AI-Enhanced FinOps optimization engine"""

    def __init__(self):
        self.predictions: List[AIPrediction] = []
        self.forecasts: Dict[str, ForecastData] = {}
        self.recommendations: List[Dict] = []

        # AI rule definitions
        self.ai_rules = self._define_ai_rules()

    def _define_ai_rules(self) -> Dict:
        """Define AI-powered optimization rules"""
        return {
            "rightsizing": {
                "description": "Analyze usage patterns and recommend optimal instance sizes",
                "algorithm": "statistical_analysis",
                "confidence_threshold": 0.7,
                "savings_range": "20-60%"
            },
            "anomaly_detection": {
                "description": "Detect unusual spending patterns using ML algorithms",
                "algorithm": "unsupervised_learning",
                "sensitivity": "medium",
                "alert_types": ["spike", "drop", "gradual_increase"]
            },
            "reservation_optimization": {
                "description": "Optimize committed usage discounts",
                "algorithm": "linear_programming",
                "lookback_period": 60,
                "horizon": 12
            },
            "demand_forecasting": {
                "description": "Predict future spending with ML models",
                "algorithm": "time_series",
                "horizon_months": 3,
                "confidence_level": 0.95
            }
        }

    def ai_rightsizing_analysis(self, resources: List[Dict]) -> List[AIPrediction]:
        """AI-powered rightsizing recommendations"""
        predictions = []

        for resource in resources:
            name = resource.get('name', 'unknown')
            current_instance = resource.get('instance_type', '')
            avg_cpu = resource.get('avg_cpu', 0)
            avg_mem = resource.get('avg_memory', 0)
            hour_cost = resource.get('hourly_cost', 0)

            # AI logic for rightsizing
            if avg_cpu < 30 and avg_mem < 40:
                # Suggest downsizing
                smaller_instance = self._suggest_smaller_instance(current_instance)
                savings = hour_cost * 0.5  # Estimate 50% savings
                roi = hour_cost / (hour_cost * 0.5) * 720  # Rough months
                confidence = min(avg_cpu * 5, 1.0)  # Higher CPU variance = higher confidence

                predictions.append(AIPrediction(
                    category="rightsizing",
                    current_cost=hour_cost * 720,
                    predicted_cost=hour_cost * 720 - savings * 720,
                    recommended_action=f"Downsize {current_instance} → {smaller_instance}",
                    confidence=confidence,
                    effort="low",
                    roi_months=roi,
                    implementation_steps=[
                        "Review resource dependencies",
                        "Schedule maintenance window",
                        f"Change instance type to {smaller_instance}",
                        "Monitor post-change performance"
                    ]
                ))

            elif avg_cpu > 80 and avg_mem > 80:
                # Suggest upsizing
                larger_instance = self._suggest_larger_instance(current_instance)
                if larger_instance:
                    predictions.append(AIPrediction(
                        category="rightsizing",
                        current_cost=hour_cost * 720,
                        predicted_cost=hour_cost * 720,
                        recommended_action=f"Consider {larger_instance} for better performance",
                        confidence=0.6,
                        effort="medium",
                        roi_months=12,
                        implementation_steps=[
                            "Validate performance needs",
                            "Plan instance migration",
                            f"Configure {larger_instance}",
                            "Test application performance"
                        ]
                    ))

        return predictions

    def _suggest_smaller_instance(self, instance_type: str) -> str:
        """Suggest a smaller instance type"""
        size_map = {
            'large': 'medium',
            'xlarge': 'large',
            '2xlarge': 'xlarge',
            '4xlarge': '2xlarge',
            '8xlarge': '4xlarge'
        }

        # Extract size from instance type
        match = re.match(r'\w+\.(\w+)', instance_type.lower())
        if match:
            size = match.group(1)
            if size in size_map:
                prefix = instance_type.split('.')[0]
                return f"{prefix}.{size_map[size]}"

        return instance_type

    def _suggest_larger_instance(self, instance_type: str) -> str:
        """Suggest a larger instance type"""
        # Simplified - would be more sophisticated in production
        return instance_type.replace('.medium', '.large').replace('.large', '.xlarge')

    def ai_anomaly_detection(self, cost_data: List[Dict]) -> List[AIPrediction]:
        """Detect spending anomalies using statistical methods"""
        predictions = []

        # Group by resource
        by_resource = defaultdict(list)
        for item in cost_data:
            by_resource[item.get('resource_id', 'unknown')].append(item.get('cost', 0))

        for resource_id, costs in by_resource.items():
            if len(costs) < 3:
                continue

            avg = sum(costs) / len(costs)
            std_dev = (sum((c - avg) ** 2 for c in costs) / len(costs)) ** 0.5

            # Check for anomalies
            for cost in costs[-7:]:  # Last 7 days
                variance = abs(cost - avg) / avg if avg > 0 else 0

                if variance > 0.5:  # 50% variance threshold
                    predictions.append(AIPrediction(
                        category="anomaly",
                        current_cost=cost,
                        predicted_cost=avg,
                        recommended_action=f"Investigate unusual spike in {resource_id} (${cost:.2f} vs avg ${avg:.2f})",
                        confidence=min(variance, 1.0),
                        effort="low",
                        roi_months=0,
                        implementation_steps=[
                            "Review resource usage history",
                            "Check for new deployments",
                            "Verify billing accuracy"
                        ]
                    ))

        return predictions

    def ai_demand_forecasting(self, historical_costs: List[Dict], months: int = 3) -> ForecastData:
        """Predict future costs using trend analysis"""
        # Simple linear regression for demonstration
        # In production, would use ARIMA, Prophet, or Neural Networks

        costs = [c['cost'] for c in historical_costs[-30:]]  # Last 30 days

        if len(costs) < 5:
            return ForecastData(
                period="monthly",
                predictions=[],
                confidence_range=(0, 0),
                variance_percent=0
            )

        # Calculate trend
        n = len(costs)
        x_avg = (n + 1) / 2
        y_avg = sum(costs) / n

        numerator = sum((i + 1) * costs[i] for i in range(n)) - n * x_avg * y_avg
        denominator = sum((i + 1) ** 2 for i in range(n)) - n * x_avg ** 2

        slope = numerator / denominator if denominator != 0 else 0
        intercept = y_avg - slope * x_avg

        # Predict next 'months' months
        predictions = []
        base_cost = sum(costs[-30:]) / 30  # Average of last 30 days

        for m in range(1, months + 1):
            predicted = intercept + slope * (n + m)
            # Add seasonality factor (simplified)
            seasonal_factor = 1 + 0.1 * (1 + (-1) ** m)  # Rough seasonality
            final_prediction = predicted * seasonal_factor

            predictions.append({
                "month": datetime.now().replace(day=1) + timedelta(days=30 * m),
                "predicted_cost": max(final_prediction, base_cost * 0.5),  # Floor at 50% of base
                "lower_bound": final_prediction * 0.8,
                "upper_bound": final_prediction * 1.2
            })

        avg_confidence = sum(costs) / len(costs) if costs else 0
        variance = slope * months

        return ForecastData(
            period="monthly",
            predictions=predictions,
            confidence_range=(avg_confidence * 0.8, avg_confidence * 1.2),
            variance_percent=abs(variance) / avg_confidence * 100 if avg_confidence > 0 else 0
        )

    def ai_reservation_optimization(self, usage_data: List[Dict]) -> List[AIPrediction]:
        """AI-powered reservation/Commitment recommendations"""
        predictions = []

        # Aggregate usage by family
        by_family = defaultdict(lambda: {'total_hours': 0, 'avg_util': 0, 'count': 0})

        for item in usage_data:
            family = item.get('instance_family', 'unknown')
            hours = item.get('hours_used', 0)
            util = item.get('utilization', 0)

            by_family[family]['total_hours'] += hours
            by_family[family]['avg_util'] += util
            by_family[family]['count'] += 1

        for family, data in by_family.items():
            if data['count'] == 0:
                continue

            avg_util = data['avg_util'] / data['count']

            if avg_util > 0.65:  # 65%+ utilization
                # Recommend purchase
                purchase_options = [
                    {"term": "1-year", "savings": 0.4, "upfront": 0.5},
                    {"term": "3-year", "savings": 0.6, "upfront": 1.0}
                ]

                for option in purchase_options:
                    predictions.append(AIPrediction(
                        category="reservation",
                        current_cost=1000,  # Placeholder - would use actual costs
                        predicted_cost=1000 * (1 - option['savings']),
                        recommended_action=f"Purchase 1-year {family} RI for {option['savings']*100}% savings",
                        confidence=0.85,
                        effort="medium",
                        roi_months=option['upfront'] * 12,
                        implementation_steps=[
                            f"Purchase {family} {option['term']} RI",
                            "Apply to consistent workload",
                            "Monitor for optimal usage"
                        ]
                    ))

        return predictions

    def ai_commitment_strategy(self, spend_data: Dict[str, float]) -> List[AIPrediction]:
        """Recommend optimal commitment strategy"""
        predictions = []

        total_monthly = sum(spend_data.values())

        # Analyze spend patterns
        if total_monthly > 10000:
            # Large spender - recommend aggressive commitments
            predictions.append(AIPrediction(
                category="commitment",
                current_cost=total_monthly,
                predicted_cost=total_monthly * 0.7,  # 30% savings estimate
                recommended_action="Adopt Enterprise Discount Program (EDP) with 3-year term",
                confidence=0.9,
                effort="high",
                roi_months=36,
                implementation_steps=[
                    "Negotiate EDP terms with cloud provider",
                    "Commit to minimum annual spend",
                    "Optimize reserved capacity allocation"
                ]
            ))
        elif total_monthly > 1000:
            predictions.append(AIPrediction(
                category="commitment",
                current_cost=total_monthly,
                predicted_cost=total_monthly * 0.75,
                recommended_action="Purchase 1-year RIs for consistent workloads",
                confidence=0.8,
                effort="medium",
                roi_months=12,
                implementation_steps=[
                    "Identify steady-state workloads",
                    "Purchase 1-year reserved instances",
                    "Monitor utilization monthly"
                ]
            ))

        return predictions

    def generate_ai_report(self) -> Dict[str, Any]:
        """Generate comprehensive AI-powered report"""
        return {
            "ai_insights": {
                "rightsizing_recommendations": len([p for p in self.predictions if p.category == "rightsizing"]),
                "anomaly_detections": len([p for p in self.predictions if p.category == "anomaly"]),
                "reservation_optimizations": len([p for p in self.predictions if p.category == "reservation"]),
                "commitment_strategies": len([p for p in self.predictions if p.category == "commitment"])
            },
            "forecast": {
                "next_3_months": [p.__dict__ for p in self.predictions[:5]],
                "total_savings": sum(p.predicted_cost for p in self.predictions) - sum(p.current_cost for p in self.predictions)
            },
            "top_recommendations": sorted(
                self.predictions,
                key=lambda x: x.current_cost - x.predicted_cost,
                reverse=True
            )[:10],
            "implementation_score": len([p for p in self.predictions if p.effort == "low"]) / len(self.predictions) * 100 if self.predictions else 0
        }


def run_ai_optimization(cloud_resources: List[Dict], cost_data: List[Dict]) -> Dict:
    """Run complete AI optimization analysis"""
    engine = FinOpsAIEngine()

    # Rightsizing
    rightsizing_results = engine.ai_rightsizing_analysis(cloud_resources)

    # Anomaly detection
    anomaly_results = engine.ai_anomaly_detection(cost_data)

    # Combine all predictions
    all_predictions = rightsizing_results + anomaly_results
    engine.predictions = all_predictions

    # Generate report
    return engine.generate_ai_report()


def main():
    # Test with sample data
    sample_resources = [
        {
            "name": "web-server-1",
            "instance_type": "t3.large",
            "avg_cpu": 15,
            "avg_memory": 30,
            "hourly_cost": 0.0832
        },
        {
            "name": "db-server-1",
            "instance_type": "m5.xlarge",
            "avg_cpu": 85,
            "avg_memory": 75,
            "hourly_cost": 0.192
        }
    ]

    sample_cost_data = [
        {"resource_id": "r1", "cost": 100},
        {"resource_id": "r1", "cost": 105},
        {"resource_id": "r1", "cost": 500},  # Anomaly
        {"resource_id": "r2", "cost": 200},
        {"resource_id": "r2", "cost": 210},
    ]

    report = run_ai_optimization(sample_resources, sample_cost_data)

    print(json.dumps(report, indent=2, default=str))


if __name__ == "__main__":
    main()