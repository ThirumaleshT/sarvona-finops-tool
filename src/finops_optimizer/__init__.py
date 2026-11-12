"""
FinOps Optimizer Package
Multi-cloud cost optimization for AWS and Azure
"""

__version__ = "1.0.0"
__author__ = "FinOps Team"

from cost_optimization.aws_optimizer import AWSCostOptimizer, Recommendation, RecommendationType
from cost_optimization.azure_optimizer import AzureCostOptimizer, AzureRecommendation, AzureRecommendationType
from reports.report_generator import ReportGenerator

__all__ = [
    "AWSCostOptimizer",
    "Recommendation",
    "RecommendationType",
    "AzureCostOptimizer",
    "AzureRecommendation",
    "AzureRecommendationType",
    "ReportGenerator",
]