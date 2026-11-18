import streamlit as st
import sys
import os
import pandas as pd
import plotly.express as px
from datetime import datetime, timedelta
import json

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), 'src')))

from cost_optimization.aws_optimizer import AWSCostOptimizer
from cost_optimization.azure_optimizer import AzureCostOptimizer
from cost_optimization.gcp_optimizer import GCPOptimizer
from cost_optimization.virtual_tags import VirtualTagsEngine, VirtualTagType, create_default_rules_engine
from cost_optimization.shared_allocation import SharedCostAllocator, create_networking_pool, NETWORKING_ALLOCATION_TEMPLATE
from finance.budget_forecast import FinancialPlanningEngine, BudgetPeriod, ForecastModel, create_sample_period_data
from analytics.anomaly_detection import AnomalyDetectionEngine, AnomalySeverity, AnomalyStatus
from analytics.data_explorer import DataExplorer, VirtualCostDataSource
from governance.rbac import RBACEngine, GovernanceEngine
from cloud_checkr_style.core import CloudCheckrStyleEngine, ResourceType, CloudProvider

st.set_page_config(page_title="AI FinOps Optimizer", page_icon="🧠", layout="wide")

st.markdown("""
    <style>
    .main { background-color: #0e1117; }
    .stMetric { background-color: #16213e; padding: 15px; border-radius: 10px; border: 1px solid #0f3460; }
    .stMetric [data-testid="stMetricLabel"], .stMetric [data-testid="stMetricLabel"] * { color: #c9d4e5 !important; }
    .stMetric [data-testid="stMetricValue"], .stMetric [data-testid="stMetricValue"] * { color: #ffffff !important; }
    .stTabs [data-baseweb="tab-list"] { gap: 24px; }
    .stTabs [data-baseweb="tab"] { padding: 12px 24px; }
    </style>
    """, unsafe_allow_html=True)

st.title("🧠 AI FinOps Optimizer - Multi-Cloud Governance")
st.markdown("---")

if 'connected' not in st.session_state:
    st.session_state.connected = False
if 'resources' not in st.session_state:
    st.session_state.resources = []
if 'budgets' not in st.session_state:
    st.session_state.budgets = []
if 'anomalies' not in st.session_state:
    st.session_state.anomalies = []
if 'allocations' not in st.session_state:
    st.session_state.allocations = []
if 'governance_engine' not in st.session_state:
    st.session_state.governance_engine = GovernanceEngine()
if 'rbac_engine' not in st.session_state:
    st.session_state.rbac_engine = RBACEngine()
if 'data_explorer' not in st.session_state:
    st.session_state.data_explorer = None

with st.sidebar:
    st.header("☁️ Sample environment")
    st.info(
        "This tool runs on sample data. No cloud account is connected and no keys or "
        "passwords are needed. Never enter real credentials here. Connecting real accounts "
        "will use read-only access that you approve and can revoke."
    )
    providers = st.multiselect("Select Providers", ["AWS", "Azure", "GCP"], default=["AWS", "Azure"])
    aws_region = st.selectbox("Sample AWS region", ["us-east-1", "eu-west-1", "ap-south-1"])

    st.markdown("---")
    st.header("📊 Financial Planning")
    budget_amount = st.number_input("Monthly Budget ($)", value=5000.0, min_value=0.0, step=100.0)

    if st.button("🚀 Analyse sample data", use_container_width=True):
        with st.spinner("Loading sample data and running the analysis..."):
            import time
            time.sleep(1)

            sample_resources = [
                {"id": "web-prod-ec2-001", "name": "Web-Prod-EC2", "provider": "AWS", "type": "Compute",
                 "monthly_cost": 250.0, "hourly_cost": 8.33, "tags": {"Environment": "prod", "Team": "Engineering", "CostCenter": "CC-001"}, "region": aws_region},
                {"id": "db-main-vm-001", "name": "DB-Main-VM", "provider": "Azure", "type": "Compute",
                 "monthly_cost": 420.0, "hourly_cost": 14.0, "tags": {"Environment": "prod", "Team": "Data", "CostCenter": "CC-002"}, "region": "eastus"},
                {"id": "logs-s3-bucket", "name": "Logs-S3", "provider": "AWS", "type": "Storage",
                 "monthly_cost": 150.0, "hourly_cost": 5.0, "tags": {"Environment": "prod", "Team": "Platform"}, "region": aws_region},
                {"id": "backup-disk-001", "name": "Backup-Disk", "provider": "Azure", "type": "Storage",
                 "monthly_cost": 85.0, "hourly_cost": 2.83, "tags": {"Environment": "prod", "Team": "Platform"}, "region": "eastus"},
                {"id": "app-gke-cluster", "name": "App-GKE", "provider": "GCP", "type": "Kubernetes",
                 "monthly_cost": 320.0, "hourly_cost": 10.67, "tags": {"Environment": "prod", "Team": "Engineering"}, "region": "us-central1"},
                {"id": "network-nat-001", "name": "NAT-Gateway", "provider": "AWS", "type": "Networking",
                 "monthly_cost": 45.0, "hourly_cost": 1.5, "tags": {"Environment": "prod"}, "region": aws_region},
                {"id": "monitoring-az-001", "name": "Azure-Monitoring", "provider": "Azure", "type": "Monitoring",
                 "monthly_cost": 120.0, "hourly_cost": 4.0, "tags": {"Environment": "prod", "Team": "Platform"}, "region": "eastus"},
            ]

            shared_costs = [
                {"id": "shared-net-001", "name": "Load Balancer & NAT Costs", "monthly_cost": 120.0,
                 "type": "Networking", "provider": "Multi-cloud"},
                {"id": "shared-srv-001", "name": "Shared Monitoring & Logging", "monthly_cost": 95.0,
                 "type": "Platform", "provider": "Multi-cloud"}
            ]

            st.session_state.resources = sample_resources
            st.session_state.shared_costs = shared_costs
            st.session_state.connected = True

            fp_engine = FinancialPlanningEngine()
            fp_engine.create_budget(
                name="Monthly Cloud Budget",
                period=BudgetPeriod.MONTHLY,
                amount=budget_amount,
                owner_id="admin"
            )

            st.session_state.fp_engine = fp_engine
            st.session_state.vtags_engine = create_default_rules_engine()
            st.session_state.vtags_engine.assign_tags_to_resources(sample_resources)

            st.session_state.anomaly_detector = AnomalyDetectionEngine()
            st.session_state.allocation_engine = SharedCostAllocator()

            st.session_state.allocation_engine.create_pool(
                "Networking Pool", "Shared networking costs (LB, NAT, VPN)", 120.0
            )
            st.session_state.allocation_engine.create_pool(
                "Platform Services", "Monitoring, logging, security tools", 95.0
            )

            from analytics.data_explorer import create_explorer
            st.session_state.data_explorer = create_explorer(sample_resources)

            st.session_state.governance_engine = GovernanceEngine()
            st.session_state.rbac_engine = RBACEngine()

            st.session_state.gcp_optimizer = GCPOptimizer(
                project_id="sarvona-demo-project",
                credentials_path=None
            )

            st.success("Sample environment loaded. All figures below are sample data.")

if st.session_state.connected:
    st.warning("Sample data: these results are examples, not an analysis of your cloud account.")
    col1, col2, col3, col4 = st.columns(4)
    total_cost = sum(r.get("monthly_cost", r.get("cost", 0)) for r in st.session_state.resources)
    total_savings = sum(r.get("PotentialSavings", 0) for r in st.session_state.resources)
    total_shared = sum(s.get("monthly_cost", 0) for s in st.session_state.get("shared_costs", []))

    col1.metric("Total Monthly Spend", f"${total_cost + total_shared:,.2f}")
    col2.metric("Shared Costs", f"${total_shared:,.2f}")
    col3.metric("Savings Opportunity", f"${total_savings:,.2f}", delta_color="inverse")
    col4.metric("Resource Count", len(st.session_state.resources))

    tabs = st.tabs([
        "📊 Dashboard",
        "🏷️ Virtual Tags",
        "💰 Financial Planning",
        "🤝 Shared Costs",
        "🚨 Anomalies",
        "⚙️ Governance"
    ])

    with tabs[0]:
        st.subheader("Cost Breakdown")
        df = pd.DataFrame(st.session_state.resources)

        c1, c2 = st.columns(2)
        with c1:
            fig_pie = px.pie(df, values='monthly_cost', names='provider', title='Spend by Provider',
                           hole=.4, color_discrete_sequence=['#2563eb', '#0078d4', '#4285f4'])
            st.plotly_chart(fig_pie, use_container_width=True)

        with c2:
            fig_bar = px.bar(df, x='type', y='monthly_cost', color='provider',
                           title='Cost by Resource Category', text='monthly_cost',
                           color_discrete_sequence=['#2563eb', '#0078d4', '#4285f4'])
            fig_bar.update_traces(texttemplate='$%{y}', textposition='outside')
            st.plotly_chart(fig_bar, use_container_width=True)

        st.markdown("### Detailed Resource View")
        display_df = df.copy()
        display_df['monthly_cost'] = display_df['monthly_cost'].apply(lambda x: f"${x:,.2f}")
        st.dataframe(display_df, use_container_width=True)

        if st.session_state.get("shared_costs"):
            st.markdown("### Shared Cost Pools")
            shared_df = pd.DataFrame(st.session_state.shared_costs)
            shared_fig = px.treemap(shared_df, path=['name'], values='monthly_cost',
                                  title='Shared Cost Distribution',
                                  color_discrete_sequence=['#f59e0b', '#8b5cf6'])
            st.plotly_chart(shared_fig, use_container_width=True)

    with tabs[1]:
        st.subheader("🏷️ Virtual Tags - Business Attribution")
        vtags = st.session_state.vtags_engine

        allocation_summary = vtags.get_allocation_summary()

        col1, col2 = st.columns(2)
        with col1:
            st.metric("Allocated Resources", allocation_summary.get('total_resources', 0))
            st.write(f"Unallocated: {allocation_summary.get('unallocated_count', 0)} resources")

        with col2:
            unallocated_cost = allocation_summary.get('total_unallocated_estimate', 0)
            st.metric("Unallocated Cost", f"${unallocated_cost:,.2f}")

        st.markdown("---")
        st.markdown("### Cost by Virtual Tag")

        costs_by_tag = vtags.get_cost_by_tag(st.session_state.resources, vtags.assignments)
        if costs_by_tag:
            tag_df = pd.DataFrame([
                {"Tag": k, "Monthly Cost": v, "Percentage": v / total_cost * 100 if total_cost > 0 else 0}
                for k, v in costs_by_tag.items()
            ]).sort_values('Monthly Cost', ascending=False)
            tag_df['Monthly Cost'] = tag_df['Monthly Cost'].apply(lambda x: f"${x:,.2f}")
            tag_df['Percentage'] = tag_df['Percentage'].apply(lambda x: f"{x:.1f}%")
            st.table(tag_df)

        st.markdown("---")
        st.markdown("### Unallocated Resources")
        if allocation_summary.get('by_type'):
            for tag_type, data in allocation_summary['by_type'].items():
                st.write(f"**{tag_type.replace('_', ' ').title()}:** {data['count']} resources")
                for tag, count in data['tags'].items():
                    st.write(f"  - {tag}: {count} resources")

    with tabs[2]:
        st.subheader("💰 Financial Planning & Budgeting")
        fp_engine = st.session_state.get('fp_engine')

        if not fp_engine:
            fp_engine = FinancialPlanningEngine()
            st.session_state.fp_engine = fp_engine

        budget_status = fp_engine.get_budget_status(
            budget_id="bgt_1",
            actual_spent=total_cost
        )

        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Budget Amount", f"${budget_status.get('budget_amount', 0):,.2f}")
        with col2:
            st.metric("Actual Spend", f"${budget_status.get('actual_spent', 0):,.2f}")
        with col3:
            utilization = budget_status.get('utilization_percent', 0)
            st.metric("Utilization", f"{utilization:.1f}%")

        if budget_status.get('alerts'):
            st.markdown("---")
            st.markdown("### Budget Alerts")
            for alert in budget_status['alerts']:
                icon = "🔴" if alert['level'] == 'CRITICAL' else "🟡" if alert['level'] == 'WARNING' else "🔵"
                st.warning(f"{icon} {alert['message']}")

        st.markdown("---")
        st.markdown("### Forecasting")

        historical_data = create_sample_period_data(datetime.now() - timedelta(days=90), months=6)
        forecast_result = fp_engine.create_forecast(
            budget_id="bgt_1",
            model=ForecastModel.SEASONAL,
            historical_data=historical_data,
            periods_ahead=3
        )

        if forecast_result.predictions:
            forecast_df = pd.DataFrame(forecast_result.predictions)
            fig_forecast = px.line(forecast_df, x='period', y='predicted_amount',
                                 title='3-Month Cost Forecast with Seasonal Adjustment',
                                 markers=True)
            fig_forecast.update_traces(line_color='#10b981')
            st.plotly_chart(fig_forecast, use_container_width=True)

        st.markdown("---")
        st.markdown("### Scenario Planning")

        scenario = fp_engine.create_scenario(
            name="Optimization Scenario",
            description="20% cost reduction through rightsizing and reserved instances",
            changes=[{"field": "cost", "multiplier": 0.80}]
        )

        scenario_results = fp_engine.run_scenario_simulation(scenario, historical_data)
        scenario_df = pd.DataFrame(scenario_results)
        if not scenario_df.empty:
            st.write(f"**{scenario.name}** - {scenario.description}")
            st.write(f"Baseline: ${sum(x['amount'] for x in historical_data[-3:]):,.2f}")
            st.write(f"Projected: ${sum(x['amount'] for x in scenario_results[-3:]):,.2f}")

    with tabs[3]:
        st.subheader("🤝 Shared Cost Allocation")
        allocator = st.session_state.allocation_engine

        st.markdown("#### Current Shared Cost Pools")
        if allocator.pools:
            for pool in allocator.pools:
                if pool.is_active:
                    st.write(f"**{pool.name}**: ${pool.total_cost:,.2f}/month - {pool.description}")

        st.markdown("---")

        st.markdown("#### Networking Pool Allocation Preview")
        networking_pool = next((p for p in allocator.pools if "Network" in p.name), None)
        if networking_pool:
            preview = allocator.preview_allocation(
                pool_id=networking_pool.id
            )

            if preview.allocations:
                alloc_df = pd.DataFrame([{
                    "Target": a['target'],
                    "Allocated Cost": f"${a['allocated_cost']:,.2f}",
                    "Allocation %": f"{a['allocation_percentage']:.1f}%"
                } for a in preview.allocations])
                st.table(alloc_df)

                st.write(f"**Unallocated:** ${preview.unallocated:,.2f}")

                if st.button("📊 Execute Network Allocation"):
                    allocator.allocate(pool_id=networking_pool.id)
                    st.success("Allocation executed successfully!")

        st.markdown("---")
        st.markdown("#### Allocation Summary")

        summary = allocator.get_allocation_summary()
        st.write(f"**Total Allocated:** ${summary['total_allocated_cost']:,.2f}")
        st.write(f"**Active Pools:** {summary['total_pools']}")

    with tabs[4]:
        st.subheader("🚨 Anomaly Detection")
        detector = st.session_state.anomaly_detector

        with st.expander("Run Anomaly Detection", expanded=True):
            if st.session_state.resources:
                data = [{
                    'date': (datetime.now() - timedelta(days=i)).strftime('%Y-%m-%d'),
                    'amount': r.get('monthly_cost', 0) * (30 / 30),
                    'resource_id': r.get('id', r.get('Name', 'unknown')),
                    'name': r.get('name', r.get('Name', 'Unknown')),
                    'provider': r.get('provider', 'unknown'),
                    'service': r.get('type', 'unknown')
                } for r in st.session_state.resources for i in range(1, 4)]

                anomalies = detector.detect_anomalies(data)
                st.session_state.anomalies = anomalies

        if detector.anomalies:
            st.markdown("---")
            st.markdown("### Detected Anomalies")

            critical = [a for a in detector.anomalies if a.severity == AnomalySeverity.CRITICAL]
            high = [a for a in detector.anomalies if a.severity == AnomalySeverity.HIGH]
            medium = [a for a in detector.anomalies if a.severity == AnomalySeverity.MEDIUM]

            if critical:
                st.error(f"🔴 {len(critical)} Critical anomalies detected")
            if high:
                st.warning(f"🟡 {len(high)} High severity anomalies")
            if medium:
                st.info(f"🔵 {len(medium)} Medium severity anomalies")

            for anomaly in detector.anomalies[:10]:
                anomaly_type_display = anomaly.anomaly_type.value.replace('_', ' ').title()
                with st.expander(f"{anomaly.severity.value.title()}: {anomaly_type_display} - {anomaly.resource_name}"):
                    st.write(f"**Provider:** {anomaly.provider}")
                    st.write(f"**Period:** {anomaly.period}")
                    st.write(f"**Actual:** ${anomaly.actual_value:,.2f}")
                    st.write(f"**Expected:** ${anomaly.expected_value:,.2f}")
                    st.write(f"**Deviation:** {anomaly.deviation_percent:+.1f}%")
                    st.write(f"**Confidence:** {anomaly.confidence * 100:.0f}%")
                    st.write(f"**Explanation:** {anomaly.explanation}")
                    st.write(f"**Suggested Actions:**")
                    for action in anomaly.suggested_actions:
                        st.write(f"  - {action}")
        else:
            st.info("No anomalies detected yet. Run detection with sample data.")

    with tabs[5]:
        st.subheader("🛡️ Governance & Compliance")
        governance_engine = st.session_state.governance_engine

        with st.expander("Assess Resources Against Governance Rules", expanded=True):
            if st.session_state.resources:
                reports = []
                for resource in st.session_state.resources[:20]:
                    report = governance_engine.assess_resource(resource)
                    reports.append({
                        "Resource": resource.get('name', resource.get('resource_name', 'Unknown')),
                        "Type": resource.get('type', 'Unknown'),
                        "Status": report.status.value,
                        "Score": f"{report.compliance_score:.0f}%",
                        "Violations": len(report.violations)
                    })

                if reports:
                    report_df = pd.DataFrame(reports)
                    st.dataframe(report_df, use_container_width=True)

                    st.markdown("---")
                    summary = governance_engine.get_governance_summary()
                    col1, col2, col3 = st.columns(3)
                    with col1:
                        st.metric("Compliance Rate", f"{summary['compliance_rate']:.1f}%")
                    with col2:
                        st.metric("Non-Compliant", summary['non_compliant_count'])
                    with col3:
                        st.metric("Violations", summary['violations_count'])

        st.markdown("---")
        st.markdown("### Governance Rules")

        rules_data = []
        for rule in governance_engine.rules:
            violated_count = sum(1 for r in [governance_engine.assess_resource(res) for res in st.session_state.resources]
                               if any(v.get('rule_id') == rule.id for v in r.violations))
            status = "Violating" if violated_count > 0 else "Compliant"
            rules_data.append({
                "Rule": rule.name,
                "Description": rule.description[:50] + "...",
                "Status": status,
                "Severity": rule.severity,
                "Violations": violated_count
            })

        if rules_data:
            rules_df = pd.DataFrame(rules_data)
            st.table(rules_df)

        if st.button("🔄 Reassess Governance"):
            governance_engine.reports = []
            for resource in st.session_state.resources:
                governance_engine.assess_resource(resource)
            st.success("Governance assessment complete!")

else:
    st.info("👋 Welcome! Press **Analyse sample data** in the sidebar to explore cost analysis, budgets, anomalies and governance on sample cloud resources.")

    c1, c2, c3 = st.columns(3)
    with c1:
        st.markdown("[![AWS](https://raw.githubusercontent.com/devicons/devicon/master/icons/amazonwebservices/amazonwebservices-original.svg)](https://aws.amazon.com/)")
        st.markdown("### AWS Support\nRight-sizing, RIs, Storage optimization")
    with c2:
        st.markdown("[![Azure](https://raw.githubusercontent.com/devicons/devicon/master/icons/azure/azure-original.svg)](https://azure.microsoft.com/)")
        st.markdown("### Azure Support\nVM optimization, Reservations, Hybrid Benefit")
    with c3:
        st.markdown("[![GCP](https://raw.githubusercontent.com/devicons/devicon/master/icons/google/google-original.svg)](https://cloud.google.com/)")
        st.markdown("### GCP Support\nCommitted use discounts, Rightsizing")

    st.markdown("---")

    features = [
        {"icon": "🎯", "title": "AI-Powered", "desc": "Machine learning identifies anomalies and optimization opportunities"},
        {"icon": "🏢", "title": "Multi-Cloud", "desc": "Unified view for AWS, Azure, and GCP"},
        {"icon": "🏷️", "title": "Virtual Tags", "desc": "Rule-based cost allocation to business owners"},
        {"icon": "💰", "title": "Budgeting", "desc": "Create budgets, forecasts, and track variance"},
        {"icon": "🤝", "title": "Shared Costs", "desc": "Allocate networking, security, and platform costs"},
        {"icon": "🚨", "title": "Anomaly Detection", "desc": "Proactive alerts for cost spikes and unusual patterns"},
        {"icon": "🛡️", "title": "Governance", "desc": "Compliance rules with quantified savings impact"}
    ]

    for i in range(0, len(features), 3):
        cols = st.columns(3)
        for j, feature in enumerate(features[i:i+3]):
            with cols[j]:
                st.markdown(f"### {feature['icon']} {feature['title']}")
                st.write(feature['desc'])

st.markdown("---")
st.caption("SARVONA • Sample data only • [Privacy Policy](https://sarvona.si/privacy-policy/) • Contact: info@sarvona.si")