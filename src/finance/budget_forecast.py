"""
Financial Planning Engine
Budget management, forecasting, and variance analysis
"""

from typing import List, Dict, Any, Optional
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
import json
from abc import ABC, abstractmethod


class BudgetPeriod(Enum):
    MONTHLY = "monthly"
    QUARTERLY = "quarterly"
    ANNUAL = "annual"


class ForecastModel(Enum):
    SIMPLE_TREND = "simple_trend"
    SEASONAL = "seasonal"
    HISTORICAL_AVERAGE = "historical_average"
    EXPONENTIAL_SMOOTHING = "exponential_smoothing"
    SCENARIO = "scenario"


@dataclass
class Budget:
    id: str
    name: str
    period: BudgetPeriod
    amount: float
    currency: str = "USD"
    allocated_to: Dict[str, float] = field(default_factory=dict)
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)
    is_active: bool = True
    owner_id: str = ""
    description: str = ""


@dataclass
class Forecast:
    id: str
    budget_id: str
    model: ForecastModel
    predictions: List[Dict[str, Any]]
    confidence_interval: float = 0.90
    model_version: int = 1
    created_at: datetime = field(default_factory=datetime.now)


@dataclass
class VarianceRecord:
    period: str
    budget_amount: float
    actual_amount: float
    variance: float
    variance_percent: float
    explanation: str


@dataclass
class Scenario:
    id: str
    name: str
    description: str
    changes: List[Dict[str, Any]]
    created_at: datetime = field(default_factory=datetime.now)


class ForecastAlgorithm(ABC):
    """Abstract base class for forecasting algorithms"""

    @abstractmethod
    def forecast(self, historical_data: List[Dict[str, Any]],
                 periods_ahead: int) -> Dict[str, Any]:
        """Generate forecast from historical data"""
        pass


class SimpleTrendForecaster(ForecastAlgorithm):
    """Simple trend-based forecasting using linear regression concepts"""

    def forecast(self, historical_data: List[Dict[str, Any]],
                 periods_ahead: int = 3) -> Dict[str, Any]:
        if len(historical_data) < 2:
            return {"predictions": [], "confidence": 0}

        # Calculate trend
        values = [d.get('amount', 0) for d in historical_data[-12:]]
        dates = [d.get('date') for d in historical_data[-12:]]

        if not values:
            return {"predictions": [], "confidence": 0}

        baseline = sum(values) / len(values)
        trend = 0

        if len(values) >= 2:
            # Simple linear trend
            x = list(range(len(values)))
            n = len(values)
            sum_x = sum(x)
            sum_y = sum(values)
            sum_xy = sum(xi * yi for xi, yi in zip(x, values))
            sum_x2 = sum(xi * xi for xi in x)

            denominator = n * sum_x2 - sum_x * sum_x
            if denominator != 0:
                slope = (n * sum_xy - sum_x * sum_y) / denominator
                trend = slope

        predictions = []
        last_date = datetime.strptime(dates[-1], "%Y-%m-%d") if dates else datetime.now()

        for i in range(1, periods_ahead + 1):
            future_date = last_date + timedelta(days=30 * i)
            prediction = baseline + trend * i
            predictions.append({
                "period": future_date.strftime("%Y-%m-%d"),
                "predicted_amount": max(0, prediction),
                "confidence": min(0.85, 0.5 + 0.3 * min(len(values) / 12, 1))
            })

        return {
            "predictions": predictions,
            "confidence": 0.55 if len(values) < 3 else 0.70,
            "model": "simple_trend",
            "baseline": baseline,
            "trend": trend
        }


class SeasonalForecaster(ForecastAlgorithm):
    """Seasonal forecasting with monthly/quarterly patterns"""

    def forecast(self, historical_data: List[Dict[str, Any]],
                 periods_ahead: int = 3) -> Dict[str, Any]:
        if not historical_data:
            return {"predictions": [], "confidence": 0}

        values = [d.get('amount', 0) for d in historical_data]
        dates = [d.get('date') for d in historical_data]

        avg = sum(values) / len(values) if values else 0

        # Calculate monthly factors
        monthly_totals = {}
        monthly_counts = {}
        for d in historical_data:
            month = datetime.strptime(d['date'], "%Y-%m-%d").month
            monthly_totals[month] = monthly_totals.get(month, 0) + d.get('amount', 0)
            monthly_counts[month] = monthly_counts.get(month, 0) + 1

        monthly_factors = {}
        for month in monthly_totals:
            monthly_avg = monthly_totals[month] / monthly_counts[month]
            monthly_factors[month] = monthly_avg / avg if avg > 0 else 1.0

        predictions = []
        last_date = datetime.strptime(dates[-1], "%Y-%m-%d") if dates else datetime.now()

        for i in range(1, periods_ahead + 1):
            future_date = last_date + timedelta(days=30 * i)
            month = future_date.month
            factor = monthly_factors.get(month, 1.0)
            prediction = avg * factor
            predictions.append({
                "period": future_date.strftime("%Y-%m-%d"),
                "predicted_amount": max(0, prediction),
                "confidence": 0.75 * min(len(values) / 6, 1),
                "seasonal_factor": factor
            })

        return {
            "predictions": predictions,
            "confidence": 0.75 if len(values) >= 6 else 0.55,
            "model": "seasonal",
            "average": avg
        }


class ScenarioForecaster(ForecastAlgorithm):
    """Scenario-based forecasting for what-if analysis"""

    def forecast(self, historical_data: List[Dict[str, Any]],
                 periods_ahead: int = 3) -> Dict[str, Any]:
        values = [d.get('amount', 0) for d in historical_data]
        avg = sum(values) / len(values) if values else 0

        # Default scenarios
        scenarios = {
            "baseline": {"multiplier": 1.0, "description": "Current trend continuation"},
            "optimistic": {"multiplier": 0.85, "description": "Successful cost optimization"},
            "conservative": {"multiplier": 1.15, "description": "Increased usage/growth"},
            "aggressive_growth": {"multiplier": 1.30, "description": "Rapid business growth"}
        }

        predictions = {}
        for scenario_name, scenario_config in scenarios.items():
            pred_values = []
            for i in range(1, periods_ahead + 1):
                pred_values.append(avg * scenario_config["multiplier"])
            predictions[scenario_name] = {
                "predicted_amounts": pred_values,
                "description": scenario_config["description"]
            }

        return {
            "predictions": predictions,
            "confidence": 0.60,
            "model": "scenario",
            "average": avg,
            "scenarios": list(scenarios.keys())
        }


class FinancialPlanningEngine:
    """Main financial planning engine for budgets and forecasts"""

    def __init__(self):
        self.budgets: List[Budget] = []
        self.forecasts: Dict[str, Forecast] = {}
        self.variance_history: List[VarianceRecord] = []
        self.scenarios: Dict[str, Scenario] = {}
        self._forecasters = {
            ForecastModel.SIMPLE_TREND: SimpleTrendForecaster(),
            ForecastModel.SEASONAL: SeasonalForecaster(),
            ForecastModel.SCENARIO: ScenarioForecaster()
        }

    def create_budget(self, name: str, period: BudgetPeriod,
                      amount: float, owner_id: str = "",
                      currency: str = "USD",
                      allocated_to: Optional[Dict[str, float]] = None) -> Budget:
        """Create a new budget"""
        budget_id = f"bgt_{len(self.budgets) + 1}_{int(datetime.now().timestamp())}"
        budget = Budget(
            id=budget_id,
            name=name,
            period=period,
            amount=amount,
            currency=currency,
            allocated_to=allocated_to or {},
            owner_id=owner_id
        )
        self.budgets.append(budget)
        return budget

    def create_forecast(self, budget_id: str, model: ForecastModel,
                        historical_data: List[Dict[str, Any]],
                        periods_ahead: int = 3) -> Forecast:
        """Generate a forecast for a budget"""
        forecaster = self._forecasters.get(model)
        if not forecaster:
            raise ValueError(f"Unknown forecast model: {model}")

        result = forecaster.forecast(historical_data, periods_ahead)

        forecast_id = f"fcast_{len(self.forecasts) + 1}_{int(datetime.now().timestamp())}"
        forecast = Forecast(
            id=forecast_id,
            budget_id=budget_id,
            model=model,
            predictions=result["predictions"],
            confidence_interval=result.get("confidence", 0.90)
        )

        self.forecasts[budget_id] = forecast
        return forecast

    def calculate_variance(self, actual_spend: float, budget_amount: float,
                           period: str, explanation: str = "") -> VarianceRecord:
        """Calculate variance between actual and budget"""
        variance = actual_spend - budget_amount
        variance_percent = (variance / budget_amount * 100) if budget_amount > 0 else 0

        record = VarianceRecord(
            period=period,
            budget_amount=budget_amount,
            actual_amount=actual_spend,
            variance=variance,
            variance_percent=variance_percent,
            explanation=explanation
        )

        self.variance_history.append(record)
        return record

    def create_scenario(self, name: str, description: str,
                        changes: List[Dict[str, Any]]) -> Scenario:
        """Create a what-if scenario"""
        scenario_id = f"scn_{len(self.scenarios) + 1}_{int(datetime.now().timestamp())}"
        scenario = Scenario(
            id=scenario_id,
            name=name,
            description=description,
            changes=changes
        )
        self.scenarios[scenario_id] = scenario
        return scenario

    def run_scenario_simulation(self, scenario: Scenario,
                                baseline_data: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Run a scenario simulation on baseline cost data"""
        results = []

        for item in baseline_data:
            simulated = dict(item)
            for change in scenario.changes:
                if change.get("field") == "cost":
                    multiplier = change.get("multiplier", 1.0)
                    simulated["amount"] = item.get("amount", 0) * multiplier
                elif change.get("field") == "growth_rate":
                    growth = change.get("value", 0.01)
                    simulated["amount"] = item.get("amount", 0) * (1 + growth)
            results.append(simulated)

        return results

    def allocate_budget(self, budget_id: str, allocation: Dict[str, float]) -> bool:
        """Allocate budget across dimensions"""
        budget = next((b for b in self.budgets if b.id == budget_id), None)
        if not budget:
            return False

        total_allocated = sum(allocation.values())
        if total_allocated > budget.amount * 1.05:  # Allow 5% buffer
            return False

        budget.allocated_to.update(allocation)
        return True

    def get_budget_status(self, budget_id: str,
                          actual_spent: float) -> Dict[str, Any]:
        """Get comprehensive budget status"""
        budget = next((b for b in self.budgets if b.id == budget_id), None)
        forecast = self.forecasts.get(budget_id)

        if not budget:
            return {"error": "Budget not found"}

        remaining = budget.amount - actual_spent
        variance = actual_spent - budget.amount
        utilization = (actual_spent / budget.amount * 100) if budget.amount > 0 else 0

        alerts = []
        if utilization >= 120:
            alerts.append({"level": "CRITICAL", "message": "Budget exceeded by 20%"})
        elif utilization >= 100:
            alerts.append({"level": "WARNING", "message": "Budget exceeded"})
        elif utilization >= 80:
            alerts.append({"level": "INFO", "message": "80% of budget consumed"})

        return {
            "budget_id": budget.id,
            "name": budget.name,
            "budget_amount": budget.amount,
            "actual_spent": actual_spent,
            "remaining": remaining,
            "variance": variance,
            "utilization_percent": utilization,
            "alerts": alerts,
            "forecast": forecast.predictions if forecast else [],
            "confidence": forecast.confidence_interval if forecast else 0
        }

    def get_financial_summary(self) -> Dict[str, Any]:
        """Get overall financial summary"""
        if not self.budgets:
            return {"total_budgets": 0, "total_allocated": 0}

        total_budgeted = sum(b.amount for b in self.budgets if b.is_active)
        total_spent = sum(v.actual_amount for v in self.variance_history)
        avg_variance = sum(v.variance_percent for v in self.variance_history)
        avg_variance = avg_variance / len(self.variance_history) if self.variance_history else 0

        budgets_by_period = {}
        for b in self.budgets:
            period = b.period.value
            budgets_by_period[period] = budgets_by_period.get(period, 0) + b.amount

        return {
            "total_budgets": len(self.budgets),
            "total_budgeted": total_budgeted,
            "total_spent": total_spent,
            "average_variance_percent": avg_variance,
            "budgets_by_period": budgets_by_period,
            "recent_variances": sorted(self.variance_history,
                                       key=lambda x: x.period, reverse=True)[:5]
        }

    def export_budget_data(self) -> str:
        """Export budget and forecast data to JSON"""
        data = {
            "exported_at": datetime.now().isoformat(),
            "budgets": [{
                "id": b.id,
                "name": b.name,
                "period": b.period.value,
                "amount": b.amount,
                "currency": b.currency,
                "allocated_to": b.allocated_to,
                "is_active": b.is_active,
                "owner_id": b.owner_id,
                "description": b.description
            } for b in self.budgets],
            "forecasts": {
                budget_id: [
                    {
                        "period": p["period"],
                        "predicted_amount": p.get("predicted_amount", p.get("amount", 0)),
                        "confidence": p.get("confidence", 1.0)
                    }
                    for p in f.predictions
                ]
                for budget_id, f in self.forecasts.items()
            }
        }
        return json.dumps(data, indent=2, default=str)


def create_sample_period_data(start_date: datetime, months: int = 12) -> List[Dict[str, Any]]:
    """Generate sample historical period data for forecasting"""
    import random

    data = []
    base_amount = 10000

    for i in range(months):
        date = start_date - timedelta(days=30 * (months - i - 1))
        # Add some trend and seasonality
        trend_factor = 1 + (i * 0.01)
        seasonal_factor = 1 + 0.1 * (i % 3 - 1)  # Quarterly variation
        noise = random.uniform(-0.05, 0.05)

        amount = base_amount * trend_factor * seasonal_factor * (1 + noise)
        data.append({
            "date": date.strftime("%Y-%m-%d"),
            "amount": round(amount, 2),
            "provider": ["AWS", "Azure", "GCP"][i % 3]
        })

    return data