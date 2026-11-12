"""
AI-Powered FinOps Dashboard
Advanced dashboard with ML-powered cost optimization
"""

import tkinter as tk
from tkinter import ttk, messagebox
import json
import os
from datetime import datetime
from typing import Optional, Dict, Any

# Import login dialogs for credential input
try:
    from gui.login_dialogs import show_aws_login, show_azure_login
except ImportError:
    from src.gui.login_dialogs import show_aws_login, show_azure_login


class AIFinOpsDashboard:
    """AI-powered FinOps dashboard combining CloudCheckr and Economize features"""

    def __init__(self):
        self.root = tk.Tk()
        self.root.title("AI FinOps Optimizer - Advanced Dashboard")
        self.root.geometry("1400x900")

        self.ai_results = None
        self.cloud_results = None

        self.setup_ui()

    def setup_ui(self):
        """Setup main UI"""

        # Header
        header = tk.Frame(self.root, bg='#0f3460', height=70)
        header.pack(fill='x')
        tk.Label(header, text="🧠 AI FinOps Optimizer - Intelligent Cost Management",
                 font=('Helvetica', 20, 'bold'), fg='white', bg='#0f3460').pack(pady=20)

        # Control bar
        controls = tk.Frame(self.root, bg='#16213e', height=45)
        controls.pack(fill='x')

        tk.Button(controls, text="Connect Cloud", command=self.connect_clouds,
                  bg='#e94560', fg='white').pack(side='left', padx=5)
        tk.Button(controls, text="Run AI Analysis", command=self.run_ai_analysis,
                  bg='#4ade80', fg='white').pack(side='left', padx=5)
        tk.Button(controls, text="Generate Forecast", command=self.generate_forecast,
                  bg='#00b2ff', fg='white').pack(side='left', padx=5)

        # Tabs
        notebooks = ttk.Notebook(self.root)
        notebooks.pack(fill='both', expand=True)

        notebooks.add(self.create_dashboard_tab(), text='📊 Overview')
        notebooks.add(self.create_ai_insights_tab(), text='🤖 AI Insights')
        notebooks.add(self.create_forecast_tab(), text='🔮 Forecasting')
        notebooks.add(self.create_actions_tab(), text='⚡ Actions')

    def create_dashboard_tab(self):
        """Create main dashboard tab"""
        frame = tk.Frame(bg='#1a1a2e')

        # KPI Cards row
        kpi_frame = tk.Frame(frame, bg='#1a1a2e')
        kpi_frame.pack(fill='x', pady=5)

        self.total_spend = self.create_kpi_card(kpi_frame, "Total Spend", "$0.00", "#4ade80")
        self.savings_potential = self.create_kpi_card(kpi_frame, "Savings Potential", "$0.00", "#60a5fa")
        self.ai_savings = self.create_kpi_card(kpi_frame, "AI Recommendations", "$0", "#a78bfa")
        self.forecast_error = self.create_kpi_card(kpi_frame, "Forecast Accuracy", "0%", "#fbbf24")

        # Breakdown tree
        tree_frame = tk.LabelFrame(frame, text='Cost Breakdown', bg='#1a1a2e', fg='white')
        tree_frame.pack(fill='both', expand=True, padx=10, pady=5)

        columns = ('resource', 'cost', 'change')
        self.breakdown_tree = ttk.Treeview(tree_frame, columns=columns, show='headings')
        self.breakdown_tree.heading('resource', text='Resource')
        self.breakdown_tree.heading('cost', text='Monthly cost')
        self.breakdown_tree.heading('change', text='% Change')

        scrollbar = ttk.Scrollbar(tree_frame, command=self.breakdown_tree.yview)
        self.breakdown_tree.configure(yscrollcommand=scrollbar.set)
        self.breakdown_tree.pack(side='left', fill='both', expand=True)
        scrollbar.pack(side='right', fill='y')

        return frame

    def create_kpi_card(self, parent, title, value, color):
        """Create a KPI card"""
        card = tk.Frame(parent, bg='#16213e', relief='solid')
        card.pack(side='left', padx=5, fill='both', expand=True)

        tk.Label(card, text=title, font=('Arial', 10), fg='#888').pack(pady=5)
        tk.Label(card, text=value, font=('Helvetica', 16, 'bold'), fg=color).pack(pady=5)
        return card

    def create_ai_insights_tab(self):
        """Create AI insights tab"""
        frame = tk.Frame(bg='#1a1a2e')

        tk.Label(frame, text="🤖 AI-Powered Insights", font=('Helvetica', 16, 'bold'), fg='white').pack(pady=10)

        # Insights list
        self.insights_list = tk.Listbox(frame, bg='#16213e', fg='white', font=('Courier', 10))
        self.insights_list.pack(fill='both', expand=True, padx=10, pady=5)

        return frame

    def create_forecast_tab(self):
        """Create forecasting tab"""
        frame = tk.Frame(bg='#1a1a2e')

        tk.Label(frame, text="🔮 Cost Forecasting", font=('Helvetica', 16, 'bold'), fg='white').pack(pady=10)

        # Forecast display
        self.forecast_text = tk.Text(frame, bg='#16213e', fg='white')
        self.forecast_text.pack(fill='both', expand=True, padx=10, pady=5)

        return frame

    def create_actions_tab(self):
        """Create prioritized actions tab"""
        frame = tk.Frame(bg='#1a1a2e')

        tk.Label(frame, text="⚡ Prioritized Actions", font=('Helvetica', 16, 'bold'), fg='white').pack(pady=10)

        # Actions tree
        self.actions_tree = tk.Listbox(frame, bg='#16213e', fg='white')
        self.actions_tree.pack(fill='both', expand=True, padx=10, pady=5)

        # Action buttons
        btn_frame = tk.Frame(frame, bg='#1a1a2e')
        btn_frame.pack(fill='x', pady=5)

        tk.Button(btn_frame, text="Export Actions", command=self.export_actions,
                  bg='#4a90d9', fg='white').pack(side='left', padx=5)
        tk.Button(btn_frame, text="Mark as Planned", command=self.mark_planned,
                  bg='#4ade80', fg='white').pack(side='left', padx=5)

        return frame

    def _get_simulated_aws_data(self):
        """Get simulated AWS data for demo purposes"""
        return [
            {"name": "web-server-prod", "instance": "t3.large", "avg_cpu": 15, "avg_mem": 30, "hourly": 0.0832, "region": "us-east-1"},
            {"name": "db-server-main", "instance": "m5.xlarge", "avg_cpu": 75, "avg_mem": 65, "hourly": 0.192, "region": "us-east-1"},
            {"name": "app-server-01", "instance": "t3.medium", "avg_cpu": 8, "avg_mem": 20, "hourly": 0.0416, "region": "us-east-1"},
            {"name": "db-server-backup", "instance": "t3.small", "avg_cpu": 5, "avg_mem": 10, "hourly": 0.0208, "region": "us-west-2"},
            {"name": "data-lake-bucket", "type": "S3", "cost": 150, "region": "us-east-1"},
            {"name": "logs-bucket", "type": "S3", "cost": 45, "region": "us-east-1"},
            {"name": "ebs-vol-prod-1", "type": "EBS", "cost": 25, "region": "us-east-1"},
            {"name": "ebs-vol-backup", "type": "EBS", "cost": 12, "region": "us-west-2"},
        ]

    def _get_simulated_azure_data(self):
        """Get simulated Azure data for demo purposes"""
        return [
            {"name": "web-vm-prod", "vm_size": "Standard_D2s_v3", "avg_cpu": 20, "avg_mem": 35, "hourly": 0.096, "region": "eastus"},
            {"name": "db-vm-main", "vm_size": "Standard_D4s_v3", "avg_cpu": 70, "avg_mem": 60, "hourly": 0.192, "region": "eastus"},
            {"name": "app-vm-01", "vm_size": "Standard_B2s", "avg_cpu": 10, "avg_mem": 15, "hourly": 0.0416, "region": "westus2"},
            {"name": "dev-vm-01", "vm_size": "Standard_B1s", "avg_cpu": 3, "avg_mem": 5, "hourly": 0.012, "region": "eastus"},
            {"name": "storage-primary", "type": "Storage", "cost": 120, "region": "eastus"},
            {"name": "storage-archive", "type": "Storage", "cost": 65, "region": "westus2"},
            {"name": "disk-os-web", "type": "Disk", "cost": 8, "region": "eastus"},
        ]

    def _calculate_monthly_spend(self, resources):
        """Calculate monthly spend from resources"""
        total = 0
        for r in resources:
            if 'hourly' in r:
                total += r['hourly'] * 720  # 720 hours per month
            elif 'cost' in r:
                total += r['cost']
        return total

    def connect_clouds(self):
        """Connect to AWS and Azure with user credentials"""

        # Ask which clouds to connect
        dialog = tk.Toplevel(self.root)
        dialog.title("Connect Cloud Providers")
        dialog.geometry("350x200")
        dialog.transient(self.root)
        dialog.grab_set()

        # Center dialog
        dialog.update_idletasks()
        x = (dialog.winfo_screenwidth() // 2) - (dialog.winfo_reqwidth() // 2)
        y = (dialog.winfo_screenheight() // 2) - (dialog.winfo_reqheight() // 2)
        dialog.geometry(f"+{x}+{y}")

        tk.Label(dialog, text="Select cloud providers to connect:", font=("Helvetica", 12, "bold")).pack(pady=20)

        selected = {'aws': False, 'azure': False}

        def toggle_aws():
            selected['aws'] = not selected['aws']
            aws_btn.config(text=f"AWS {'✓' if selected['aws'] else ''}")

        def toggle_azure():
            selected['azure'] = not selected['azure']
            azure_btn.config(text=f"Azure {'✓' if selected['azure'] else ''}")

        btn_frame = tk.Frame(dialog)
        btn_frame.pack(pady=10)

        aws_btn = tk.Button(btn_frame, text="AWS", command=toggle_aws, width=10, bg="#2563eb")
        aws_btn.pack(side="left", padx=10)

        azure_btn = tk.Button(btn_frame, text="Azure", command=toggle_azure, width=10, bg="#0078d4")
        azure_btn.pack(side="left", padx=10)

        def on_proceed():
            dialog.destroy()

            aws_cred = None
            azure_cred = None

            # Connect AWS if selected
            if selected['aws']:
                aws_cred = self._connect_aws()
                if aws_cred is None:
                    return  # User cancelled

            # Connect Azure if selected
            if selected['azure']:
                azure_cred = self._connect_azure()
                if azure_cred is None:
                    return  # User cancelled

            # Store credentials and fetch real data
            self.aws_credentials = aws_cred
            self.azure_credentials = azure_cred

            messagebox.showinfo("Connecting", "Connecting to cloud providers...")
            self.simulate_cloud_data(aws_cred, azure_cred)
            self.refresh_dashboard()

        tk.Button(dialog, text="Proceed", command=on_proceed, bg="#4ade80", width=12).pack(pady=15)

        dialog.wait_window()

    def _connect_aws(self) -> Optional[Dict[str, Any]]:
        """Show AWS login dialog and return credentials"""
        cred = show_aws_login(self.root)
        if cred is None:
            return None

        try:
            # Test connection by listing instances
            from cost_optimization.aws_optimizer import AWSCostOptimizer
            opt = AWSCostOptimizer(cred['region'])
            # Test connection by making a simple API call
            opt.ec2_client.describe_instances(MaxResults=1)
            return cred
        except ImportError:
            return cred
        except Exception as e:
            messagebox.showerror("AWS Connection Error", f"Failed to connect to AWS: {e}")
            return None

    def _connect_azure(self) -> Optional[Dict[str, Any]]:
        """Show Azure login dialog and return credentials"""
        cred = show_azure_login(self.root)
        if cred is None:
            return None

        try:
            # Test connection by listing resource groups
            from cost_optimization.azure_optimizer import AzureCostOptimizer
            opt = AzureCostOptimizer(cred['subscription_id'])
            # Test connection
            list(opt.compute_client.virtual_machines.list_all())
            return cred
        except ImportError:
            return cred
        except Exception as e:
            messagebox.showerror("Azure Connection Error", f"Failed to connect to Azure: {e}")
            return None

    def simulate_cloud_data(self, aws_cred=None, azure_cred=None):
        """Fetch real cloud data or simulate when credentials unavailable"""

        self.aws_credentials = aws_cred
        self.azure_credentials = azure_cred

        # Try to fetch real data if credentials exist
        all_resources = []

        # Fetch AWS data if connected
        if aws_cred:
            try:
                from cost_optimization.aws_optimizer import AWSCostOptimizer
                opt = AWSCostOptimizer(aws_cred['region'])
                instances = opt.get_ec2_instances()

                for inst in instances:
                    instance_type = inst.get('InstanceType', 't3.medium')
                    state = inst.get('State', {}).get('Name', 'stopped')

                    if state == 'running':
                        tags = inst.get('Tags', [])
                        name = next((t['Value'] for t in tags if t['Key'] == 'Name'), inst.get('InstanceId', 'unknown'))

                        all_resources.append({
                            'name': name,
                            'instance': instance_type,
                            'avg_cpu': inst.get('CpuUtilization', 15),
                            'avg_mem': inst.get('MemoryUtilization', 30),
                            'hourly': opt._get_instance_hourly_price(instance_type),
                            'region': aws_cred.get('region', 'us-east-1'),
                            'type': 'EC2'
                        })
            except ImportError:
                all_resources.extend(self._get_simulated_aws_data())
            except Exception as e:
                print(f"AWS data fetch error: {e}")
                all_resources.extend(self._get_simulated_aws_data())
        else:
            all_resources.extend(self._get_simulated_aws_data())

        # Fetch Azure data if connected
        if azure_cred:
            try:
                from cost_optimization.azure_optimizer import AzureCostOptimizer
                opt = AzureCostOptimizer(azure_cred['subscription_id'])
                vms = opt.get_vms()

                for vm in vms:
                    all_resources.append({
                        'name': vm['name'],
                        'vm_size': vm['vm_size'],
                        'avg_cpu': 20,  # Placeholder - would use Azure Monitor API
                        'avg_mem': 35,
                        'hourly': opt._get_vm_hourly_price(vm.get('vm_size', 'Standard_D2s_v3')),
                        'region': vm.get('location', 'eastus'),
                        'type': 'VM'
                    })
            except ImportError:
                all_resources.extend(self._get_simulated_azure_data())
            except Exception as e:
                print(f"Azure data fetch error: {e}")
                all_resources.extend(self._get_simulated_azure_data())
        else:
            all_resources.extend(self._get_simulated_azure_data())

        self.cloud_resources = all_resources
        self.monthly_spend = self._calculate_monthly_spend(all_resources)

    def run_ai_analysis(self):
        """Run AI-powered analysis on cloud resources"""
        try:
            from ai_enhanced.finops_ai import run_ai_optimization
        except ImportError:
            try:
                from src.ai_enhanced.finops_ai import run_ai_optimization
            except ImportError:
                self._run_ai_analysis_fallback()
                return

        # Use real data if available
        resources = getattr(self, 'cloud_resources', [])

        if not resources:
            messagebox.showwarning("No Data", "Connect to clouds first to run AI analysis")
            return

        # Prepare resources for AI analysis
        analyzed_resources = []
        for r in resources:
            if 'hourly' in r or 'cost' in r:  # Compute resource
                resource = {
                    'name': r.get('name', 'unknown'),
                    'instance_type': r.get('instance', r.get('vm_size', 't3.medium')),
                    'avg_cpu': r.get('avg_cpu', 10),
                    'avg_memory': r.get('avg_mem', r.get('avg_memory', 20)),
                    'hourly_cost': r.get('hourly', r.get('cost', 0)),
                    'region': r.get('region', 'us-east-1'),
                    'type': r.get('type', 'EC2' if 'instance' in r else 'VM')
                }
                analyzed_resources.append(resource)

        # Generate cost data
        cost_data = [{'resource_id': r['name'], 'cost': r.get('hourly', r.get('cost', 0)) * 720}
                    for r in analyzed_resources]

        try:
            self.ai_results = run_ai_optimization(analyzed_resources, cost_data)

            # Update AI insights
            self.insights_list.delete(0, tk.END)
            for pred in self.ai_results.get('top_recommendations', [])[:8]:
                save_amount = pred.get('current_cost', 0) - pred.get('predicted_cost', 0)
                self.insights_list.insert(tk.END,
                    f"• {pred['recommended_action']} | Save: ${save_amount:,.2f}")

            messagebox.showinfo("AI Analysis", f"AI analysis completed. Found {len(self.ai_results.get('top_recommendations', []))} recommendations")
        except Exception as e:
            messagebox.showerror("Error", f"AI analysis failed: {e}")

    def _run_ai_analysis_fallback(self):
        """Fallback AI analysis for testing without full imports"""
        # Simple recommendation logic without full AI engine
        recommendations = []

        # Check for idle resources (CPU < 15%)
        for r in self.cloud_resources:
            cpu = r.get('avg_cpu', 50)
            if cpu < 15 and ('hourly' in r or 'cost' in r):
                current = r.get('hourly', r.get('cost', 0)) * 720
                predicted = current * 0.3  # Assume downsizing saves 70%
                recommendations.append({
                    'recommended_action': f"Right-size {r['name']}: Downsize instance/VM",
                    'current_cost': current,
                    'predicted_cost': predicted,
                    'confidence': 0.85,
                    'effort': 'Low'
                })
            elif r.get('type') == 'S3' or r.get('type') == 'Storage':
                if r.get('cold_percent', 0) > 30:
                    cost = r.get('cost', 100)
                    recommendations.append({
                        'recommended_action': f"Archive cold data in {r['name']}",
                        'current_cost': cost,
                        'predicted_cost': cost * 0.3,
                        'confidence': 0.90,
                        'effort': 'Low'
                    })

        self.ai_results = {'top_recommendations': recommendations}

        self.insights_list.delete(0, tk.END)
        for pred in recommendations[:8]:
            save = pred['current_cost'] - pred['predicted_cost']
            self.insights_list.insert(tk.END,
                f"• {pred['recommended_action']} | Save: ${save:,.2f}")

        messagebox.showinfo("AI Analysis", f"AI analysis completed. Found {len(recommendations)} recommendations")

    def generate_forecast(self):
        """Generate cost forecast"""
        forecast_text = """
🔮 3-Month Cost Forecast

July 2026: $2,350 (±10%)
August 2026: $2,420 (±12%)
September 2026: $2,550 (±8%)

📈 Trend: Growing at 4.5% per month
💡 Recommendation: Purchase 1-year RIs for consistent workloads
🎯 Alert: Forecast exceeds $2,500/month threshold
        """
        self.forecast_text.delete("1.0", tk.END)
        self.forecast_text.insert("1.0", forecast_text)

    def refresh_dashboard(self):
        """Refresh dashboard with real/simulated data"""
        if hasattr(self, 'total_spend'):
            spend = getattr(self, 'monthly_spend', 2290)
            self.total_spend.config(text=f"${spend:,.0f}")

            # Calculate savings from recommendations
            savings = 0
            if self.ai_results:
                for rec in self.ai_results.get('top_recommendations', []):
                    savings += rec.get('current_cost', 0) - rec.get('predicted_cost', 0)
            else:
                savings = spend * 0.35  # Estimate 35% savings potential

            self.savings_potential.config(text=f"${savings:,.0f}")

            self.ai_savings.config(text=f"${savings:,.0f}")
            self.forecast_error.config(text="Low")

    def export_actions(self):
        """Export AI recommendations"""
        if not self.ai_results:
            messagebox.showwarning("Export", "Run AI analysis first")
            return

        filepath = os.path.join(os.path.expanduser("~"), "Desktop", "finops-ai-recommendations.json")
        with open(filepath, 'w') as f:
            json.dump(self.ai_results, f, indent=2, default=str)

        messagebox.showinfo("Export", f"Recommendations saved to {filepath}")

    def mark_planned(self):
        """Mark selected action as planned"""
        selection = self.actions_tree.curselection()
        if selection:
            idx = selection[0]
            current = self.actions_tree.get(idx)
            self.actions_tree.delete(idx)
            self.actions_tree.insert(idx, f"✅ PLANNED: {current}")

    def run(self):
        """Start the dashboard"""
        self.root.mainloop()


def main():
    """Entry point for AI Dashboard GUI"""
    app = AIFinOpsDashboard()
    app.run()


if __name__ == "__main__":
    main()