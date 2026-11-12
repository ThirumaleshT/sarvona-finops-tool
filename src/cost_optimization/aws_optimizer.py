"""
AWS Cost Optimization Module
Provides cost analysis and optimization recommendations for AWS resources
"""

import boto3
import datetime
from typing import List, Dict, Any, Optional
from dataclasses import dataclass
from enum import Enum


class RecommendationType(Enum):
    RIGHTSIZING = "rightsizing"
    TERMINATION = "termination"
    RESERVED_INSTANCE = "reserved_instance"
    STORAGE_OPTIMIZATION = "storage_optimization"
    SPOT_INSTANCE = "spot_instance"
    IDLE_RESOURCE = "idle_resource"


@dataclass
class Recommendation:
    resource_id: str
    resource_type: str
    recommendation_type: RecommendationType
    current_cost: float
    recommended_cost: float
    potential_savings: float
    confidence: float
    action: str
    implementation_cost: float = 0
    payback_period_months: float = 0


class AWSCostOptimizer:
    """AWS Cost Optimization engine"""

    def __init__(self, region: str = "us-east-1"):
        self.region = region
        self.ec2_client = boto3.client("ec2", region_name=region)
        self.ce_client = boto3.client("ce", region_name=region)
        self.s3_client = boto3.client("s3", region_name=region)
        self.rds_client = boto3.client("rds", region_name=region)

    def get_cost_and_usage(self, months: int = 3) -> Dict[str, Any]:
        """Get cost and usage data for the specified period"""
        end_date = datetime.date.today()
        start_date = end_date - datetime.timedelta(days=30 * months)

        response = self.ce_client.get_cost_and_usage(
            TimePeriod={
                "Start": str(start_date),
                "End": str(end_date),
            },
            Granularity="MONTHLY",
            Metrics=["UnblendedCost", "UsageQuantity"],
            GroupBy=[
                {"Type": "DIMENSION", "Key": "SERVICE"},
                {"Type": "DIMENSION", "Key": "USAGE_TYPE"},
            ],
        )
        return response

    def get_ec2_instances(self) -> List[Dict]:
        """Get all EC2 instances with their metadata"""
        response = self.ec2_client.describe_instances()
        instances = []
        for reservation in response["Reservations"]:
            for instance in reservation["Instances"]:
                instance["ReservationId"] = reservation["ReservationId"]
                instances.append(instance)
        return instances

    def get_ec2_utilization(self, instance_id: str) -> Optional[Dict]:
        """Get CloudWatch metrics for EC2 instance utilization"""
        try:
            cloudwatch = boto3.client("cloudwatch", region_name=self.region)
            end_time = datetime.datetime.utcnow()
            start_time = end_time - datetime.timedelta(days=7)

            # CPU utilization
            cpu_response = cloudwatch.get_metric_statistics(
                Namespace="AWS/EC2",
                MetricName="CPUUtilization",
                Dimensions=[{"Name": "InstanceId", "Value": instance_id}],
                StartTime=start_time,
                End_time=end_time,
                Period=86400,
                Statistics=["Average"],
            )

            # Network utilization
            network_response = cloudwatch.get_metric_statistics(
                Namespace="AWS/EC2",
                MetricName="NetworkIn",
                Dimensions=[{"Name": "InstanceId", "Value": instance_id}],
                StartTime=start_time,
                EndTime=end_time,
                Period=86400,
                Statistics=["Average"],
            )

            cpu_values = [d["Average"] for d in cpu_response.get("Datapoints", [])]
            net_values = [d["Average"] for d in network_response.get("Datapoints", [])]

            return {
                "avg_cpu": sum(cpu_values) / len(cpu_values) if cpu_values else 0,
                "max_cpu": max(cpu_values) if cpu_values else 0,
                "avg_network_in": sum(net_values) / len(net_values) if net_values else 0,
                "network_points": len(net_values),
            }
        except Exception:
            return None

    def identify_idle_ec2(self, cpu_threshold: float = 10.0, days_threshold: int = 7) -> List[Recommendation]:
        """Identify EC2 instances with low CPU utilization"""
        recommendations = []
        instances = self.get_ec2_instances()

        for instance in instances:
            instance_id = instance["InstanceId"]
            state = instance["State"]["Name"]

            if state != "running":
                continue

            utilization = self.get_ec2_utilization(instance_id)
            if not utilization:
                continue

            avg_cpu = utilization.get("avg_cpu", 0)
            if avg_cpu < cpu_threshold and utilization.get("network_points", 0) >= days_threshold:
                instance_type = instance["InstanceType"]
                hourly_price = self._get_instance_hourly_price(instance_type)

                recommendations.append(Recommendation(
                    resource_id=instance_id,
                    resource_type="EC2",
                    recommendation_type=RecommendationType.IDLE_RESOURCE,
                    current_cost=hourly_price * 24 * 30,
                    recommended_cost=0,
                    potential_savings=hourly_price * 24 * 30,
                    confidence=0.85,
                    action=f"Stop idle instance {instance_id}. Average CPU: {avg_cpu:.2f}%",
                ))

        return recommendations

    def _get_instance_hourly_price(self, instance_type: str) -> float:
        """Get hourly price for an instance type (on-demand, us-east-1)"""
        # Simplified pricing - in production, use AWS Price List API
        pricing = {
            "t3.micro": 0.0104,
            "t3.small": 0.0208,
            "t3.medium": 0.0416,
            "t3.large": 0.0832,
            "t3.xlarge": 0.1664,
            "t3.2xlarge": 0.3328,
            "m5.large": 0.096,
            "m5.xlarge": 0.192,
            "m5.2xlarge": 0.384,
            "m5.4xlarge": 0.768,
            "c5.large": 0.085,
            "c5.xlarge": 0.17,
            "c5.2xlarge": 0.34,
            "r5.large": 0.126,
            "r5.xlarge": 0.252,
            "r5.2xlarge": 0.504,
        }
        return pricing.get(instance_type, 0.1)

    def get_orphaned_ebs_volumes(self) -> List[Recommendation]:
        """Find EBS volumes not attached to any instance"""
        recommendations = []

        response = self.ec2_client.describe_volumes()
        for volume in response.get("Volumes", []):
            if not volume.get("Attachments"):
                vol_id = volume["VolumeId"]
                size_gb = volume["Size"]
                hourly_price = size_gb * 0.000112  # EBS gp2 pricing per GB

                savings = hourly_price * 24 * 30

                recommendations.append(Recommendation(
                    resource_id=vol_id,
                    resource_type="EBS Volume",
                    recommendation_type=RecommendationType.TERMINATION,
                    current_cost=hourly_price * 24 * 30,
                    recommended_cost=0,
                    potential_savings=savings,
                    confidence=0.95,
                    action=f"Delete orphaned EBS volume {vol_id} ({size_gb} GB)",
                ))

        return recommendations

    def get_s3_storage_optimization(self) -> List[Recommendation]:
        """Identify S3 buckets that could benefit from Intelligent-Tiering"""
        recommendations = []

        buckets = self.s3_client.list_buckets()

        for bucket in buckets.get("Buckets", []):
            bucket_name = bucket["Name"]
            try:
                # Get bucket policy and storage class
                size_response = self.s3_client.list_objects_v2(
                    Bucket=bucket_name,
                    MaxKeys=1
                )

                if size_response.get("KeyCount", 0) > 0:
                    # Check if bucket uses Standard storage
                    # In production, analyze access patterns
                    recommendations.append(Recommendation(
                        resource_id=bucket_name,
                        resource_type="S3 Bucket",
                        recommendation_type=RecommendationType.STORAGE_OPTIMIZATION,
                        current_cost=10.0,  # Placeholder
                        recommended_cost=5.0,
                        potential_savings=5.0,
                        confidence=0.70,
                        action=f"Enable S3 Intelligent-Tiering for bucket {bucket_name}",
                    ))
            except Exception:
                continue

        return recommendations

    def get_reserved_instance_recommendations(self) -> List[Recommendation]:
        """Get RI recommendations from AWS Cost Explorer"""
        recommendations = []

        try:
            response = self.ce_client.get_reservation_recommendation(
                Service="AmazonEC2",
                AccountScope="PAYER"
            )

            for rec in response.get("Recommendations", []):
                ri_type = rec["ReservationRecommendation"]
                instance_type = ri_type["Recommendation"]

                recommendations.append(Recommendation(
                    resource_id=f"RI-{instance_type}",
                    resource_type="ReservedInstance",
                    recommendation_type=RecommendationType.RESERVED_INSTANCE,
                    current_cost=0,
                    recommended_cost=rec["TotalPotentialSavings"].get("MonthlySavings", 0),
                    potential_savings=rec["TotalSavings"].get("AnnualSavings", 0),
                    confidence=rec.get("RecommendationScore", 0),
                    action=f"Purchase {rec['UtilizationScore']}% RI for {instance_type}",
                ))

        except Exception as e:
            print(f"Error getting RI recommendations: {e}")

        return recommendations

    def get_spot_instance_opportunities(self) -> List[Recommendation]:
        """Identify instances that could use spot instances"""
        recommendations = []
        instances = self.get_ec2_instances()

        for instance in instances:
            instance_id = instance["InstanceId"]
            state = instance["State"]["Name"]

            if state != "running":
                continue

            utilization = self.get_ec2_utilization(instance_id)
            if not utilization:
                continue

            # Check for fault-tolerant workloads (dev/test environments)
            tags = instance.get("Tags", [])
            env_tag = next((t for t in tags if t["Key"] == "Environment"), None)

            if env_tag and env_tag["Value"].lower() in ["dev", "test", "staging"]:
                instance_type = instance["InstanceType"]
                current_cost = self._get_instance_hourly_price(instance_type)

                # Spot typically 70% discount
                spot_cost = current_cost * 0.30

                recommendations.append(Recommendation(
                    resource_id=instance_id,
                    resource_type="EC2",
                    recommendation_type=RecommendationType.SPOT_INSTANCE,
                    current_cost=current_cost * 24 * 30,
                    recommended_cost=spot_cost * 24 * 30,
                    potential_savings=(current_cost - spot_cost) * 24 * 30,
                    confidence=0.80,
                    action=f"Convert {instance_id} to Spot instance for 70% savings",
                ))

        return recommendations

    def optimize_all(self) -> Dict[str, Any]:
        """Run all optimizations and return consolidated report"""
        all_recommendations = []

        # Run all checks
        all_recommendations.extend(self.identify_idle_ec2())
        all_recommendations.extend(self.get_orphaned_ebs_volumes())
        all_recommendations.extend(self.get_s3_storage_optimization())
        all_recommendations.extend(self.get_reserved_instance_recommendations())
        all_recommendations.extend(self.get_spot_instance_opportunities())

        # Sort by potential savings
        all_recommendations.sort(key=lambda x: x.potential_savings, reverse=True)

        # Calculate summary
        total_potential_savings = sum(r.potential_savings for r in all_recommendations)
        by_type = {}
        for r in all_recommendations:
            by_type[r.recommendation_type.value] = by_type.get(r.recommendation_type.value, 0) + r.potential_savings

        return {
            "recommendations": all_recommendations,
            "total_potential_savings": total_potential_savings,
            "summary_by_type": by_type,
            "timestamp": datetime.datetime.now().isoformat()
        }