"""Cost optimization package for FinOps Optimizer"""

from .aws_optimizer import AWSCostOptimizer, Recommendation, RecommendationType
from .azure_optimizer import AzureCostOptimizer, AzureRecommendation, AzureRecommendationType
from .virtual_tags import VirtualTagsEngine, VirtualTagType, VirtualTagRule, VirtualTagAssignment
from .shared_allocation import SharedCostAllocator, SharedCostPool, AllocationRule, AllocationResult

__all__ = [
    'AWSCostOptimizer', 'Recommendation', 'RecommendationType',
    'AzureCostOptimizer', 'AzureRecommendation', 'AzureRecommendationType',
    'VirtualTagsEngine', 'VirtualTagType', 'VirtualTagRule', 'VirtualTagAssignment',
    'SharedCostAllocator', 'SharedCostPool', 'AllocationRule', 'AllocationResult'
]