"""
AWS Integration Example: Detailed cost analysis script
"""

import boto3
from cost_optimization.aws_optimizer import AWSCostOptimizer


def aws_detailed_analysis():
    """Run comprehensive AWS cost analysis"""
    optimizer = AWSCostOptimizer(region="us-east-1")

    # 1. Get cost and usage data
    print("Fetching cost data...")
    cost_data = optimizer.get_cost_and_usage(months=3)

    # 2. Identify idle EC2 instances
    print("Checking for idle EC2 instances...")
    idle_instances = optimizer.identify_idle_ec2(cpu_threshold=10.0)

    # 3. Find orphaned EBS volumes
    print("Checking for orphaned EBS volumes...")
    orphaned_volumes = optimizer.get_orphaned_ebs_volumes()

    # 4. Get storage optimization recommendations
    print("Checking S3 storage optimization opportunities...")
    s3_recommendations = optimizer.get_s3_storage_optimization()

    # 5. Get RI recommendations
    print("Fetching Reserved Instance recommendations...")
    ri_recommendations = optimizer.get_reserved_instance_recommendations()

    # 6. Get spot instance opportunities
    print("Checking for Spot instance opportunities...")
    spot_opportunities = optimizer.get_spot_vm_opportunities()

    # Compile report
    all_recommendations = (
        idle_instances +
        orphaned_volumes +
        s3_recommendations +
        ri_recommendations +
        spot_opportunities
    )

    all_recommendations.sort(key=lambda x: x.potential_savings, reverse=True)

    print("\n" + "=" * 60)
    print("AWS COST OPTIMIZATION REPORT")
    print("=" * 60)

    print(f"\nTotal recommendations: {len(all_recommendations)}")
    print(f"Total potential savings: ${sum(r.potential_savings for r in all_recommendations):,.2f}/month")

    print("\nTop 10 Recommendations:")
    for i, rec in enumerate(all_recommendations[:10], 1):
        print(f"  {i}. {rec.action}")
        print(f"     Savings: ${rec.potential_savings:,.2f}/month | Confidence: {rec.confidence*100:.0f}%")

    return all_recommendations


if __name__ == "__main__":
    aws_detailed_analysis()