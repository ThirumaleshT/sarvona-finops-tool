"""
Simple FinOps GUI - Local Testing Interface
Simplified version that should work reliably
"""

import tkinter as tk
from tkinter import messagebox, ttk
import json
import os
from datetime import datetime
from typing import Optional, Dict, Any

try:
    from gui.login_dialogs import show_aws_login, show_azure_login
except ImportError:
    from src.gui.login_dialogs import show_aws_login, show_azure_login


class FinOpsSimpleGUI:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("FinOps Optimizer - Local Test Mode")
        self.root.geometry("800x500")

        # Configure style
        self.style = ttk.Style()
        self.style.theme_use('clam')

        self.aws_connected = False
        self.azure_connected = False
        self.total_savings = 0.0
        self.aws_credentials = None
        self.azure_credentials = None

        self.setup_ui()

    def setup_ui(self):
        # Title
        title = tk.Label(self.root, text="FinOps Optimizer", font=("Helvetica", 20, "bold"))
        title.pack(pady=10)

        # Status bar
        status_frame = tk.Frame(self.root, bg="#2d2d2d", height=30)
        status_frame.pack(fill="x", padx=10, pady=5)
        status_frame.pack_propagate(False)

        self.aws_status = tk.Label(status_frame, text="AWS: Not Connected", fg="red", font=("Arial", 10))
        self.aws_status.pack(side="left", padx=10)

        tk.Label(status_frame, text=" | ", fg="white").pack(side="left")

        self.azure_status = tk.Label(status_frame, text="Azure: Not Connected", fg="red", font=("Arial", 10))
        self.azure_status.pack(side="left")

        # Tabs
        self.notebook = ttk.Notebook(self.root)
        self.notebook.pack(fill="both", expand=True, padx=10, pady=5)

        self.dashboard_tab = tk.Frame(self.notebook)
        self.aws_tab = tk.Frame(self.notebook)
        self.azure_tab = tk.Frame(self.notebook)

        self.notebook.add(self.dashboard_tab, text="Dashboard")
        self.notebook.add(self.aws_tab, text="AWS")
        self.notebook.add(self.azure_tab, text="Azure")

        self.setup_dashboard()
        self.setup_aws()
        self.setup_azure()

    def setup_dashboard(self):
        frame = self.dashboard_tab

        tk.Label(frame, text="Cost Optimization Actions", font=("Helvetica", 16, "bold")).pack(pady=10)

        self.summary = tk.Label(frame, text="Total Potential Savings: $0.00/month", font=("Helvetica", 14, "bold"))
        self.summary.pack(pady=10)

        # Action list
        actions = [
            ("EC2/VM Optimization", "Stop idle instances, right-size based on utilization", "$500-5000/mo"),
            ("Storage Optimization", "Delete orphaned disks, enable intelligent tiering", "$100-2000/mo"),
            ("Reserved Instances", "Purchase RIs for consistent workloads", "20-60% savings"),
            ("Spot VMs", "Convert fault-tolerant workloads to spot", "60-90% savings"),
            ("Azure Hybrid Benefit", "Apply AHUB for Windows VMs", "40-50% savings")
        ]

        for name, desc, benefit in actions:
            card = tk.Frame(frame, bd=1, relief="solid", bg="#2a2a2a")
            card.pack(fill="x", padx=20, pady=3)

            tk.Label(card, text=name, font=("Arial", 11, "bold"), bg="#2a2a2a", fg="white").pack(anchor="w", padx=10, pady=3)
            tk.Label(card, text=desc, font=("Arial", 9), bg="#2a2a2a", fg="#cccccc").pack(anchor="w", padx=15)
            tk.Label(card, text=benefit, font=("Arial", 9, "italic"), bg="#2a2a2a", fg="#4ade80").pack(anchor="w", padx=15, pady=(0, 3))

        # Export button
        export_btn = tk.Button(frame, text="Export Recommendations", command=self.export_recommendations, bg="#4a90d9", fg="white")
        export_btn.pack(pady=15)

    def setup_aws(self):
        frame = self.aws_tab

        conn_frame = tk.Frame(frame)
        conn_frame.pack(fill="x", padx=10, pady=5)

        tk.Button(conn_frame, text="Connect AWS", command=self.connect_aws, bg="#4a90d9", fg="white").pack(side="left", padx=5)

        # Options
        opt_frame = tk.LabelFrame(frame, text="Analysis Options", padx=10, pady=10)
        opt_frame.pack(fill="x", padx=10, pady=5)

        self.ec2_var = tk.BooleanVar()
        tk.Checkbutton(opt_frame, text="Check idle EC2 instances", variable=self.ec2_var).pack(anchor="w")

        self.ebs_var = tk.BooleanVar()
        tk.Checkbutton(opt_frame, text="Find orphaned EBS volumes", variable=self.ebs_var).pack(anchor="w")

        self.s3_var = tk.BooleanVar()
        tk.Checkbutton(opt_frame, text="Check S3 storage optimization", variable=self.s3_var).pack(anchor="w")

        self.ri_var = tk.BooleanVar()
        tk.Checkbutton(opt_frame, text="Get RI recommendations", variable=self.ri_var).pack(anchor="w")

        # Run button
        tk.Button(frame, text="Run AWS Analysis", command=self.run_aws_analysis, bg="#4a90d9", fg="white").pack(pady=10)

        # Results
        self.aws_results = tk.Text(frame, height=8)
        self.aws_results.pack(fill="both", expand=True, padx=10, pady=5)

        self.aws_savings = tk.Label(frame, text="Estimated Savings: $0.00")
        self.aws_savings.pack()

    def setup_azure(self):
        frame = self.azure_tab

        conn_frame = tk.Frame(frame)
        conn_frame.pack(fill="x", padx=10, pady=5)

        tk.Button(conn_frame, text="Connect Azure", command=self.connect_azure, bg="#4a90d9", fg="white").pack(side="left", padx=5)

        # Options
        opt_frame = tk.LabelFrame(frame, text="Analysis Options", padx=10, pady=10)
        opt_frame.pack(fill="x", padx=10, pady=5)

        self.vm_var = tk.BooleanVar()
        tk.Checkbutton(opt_frame, text="Check idle VMs", variable=self.vm_var).pack(anchor="w")

        self.disk_var = tk.BooleanVar()
        tk.Checkbutton(opt_frame, text="Find orphaned disks", variable=self.disk_var).pack(anchor="w")

        self.storage_var = tk.BooleanVar()
        tk.Checkbutton(opt_frame, text="Check storage optimization", variable=self.storage_var).pack(anchor="w")

        self.reservation_var = tk.BooleanVar()
        tk.Checkbutton(opt_frame, text="Get reservation recommendations", variable=self.reservation_var).pack(anchor="w")

        # Run button
        tk.Button(frame, text="Run Azure Analysis", command=self.run_azure_analysis, bg="#4a90d9", fg="white").pack(pady=10)

        # Results
        self.azure_results = tk.Text(frame, height=8)
        self.azure_results.pack(fill="both", expand=True, padx=10, pady=5)

        self.azure_savings = tk.Label(frame, text="Estimated Savings: $0.00")
        self.azure_savings.pack()

    def connect_aws(self):
        """Connect to AWS with user credentials"""
        cred = show_aws_login(self.root)
        if cred is None:
            return

        try:
            from cost_optimization.aws_optimizer import AWSCostOptimizer
            opt = AWSCostOptimizer(cred['region'])
            opt.ec2_client.describe_instances(MaxResults=1)
            self.aws_credentials = cred
            self.aws_connected = True
            self.aws_status.configure(text=f"✅ AWS: Connected ({cred['region']})", fg="green")
        except ImportError:
            self.aws_credentials = cred
            self.aws_connected = True
            self.aws_status.configure(text=f"✅ AWS: Connected (simulated)", fg="green")
        except Exception as e:
            messagebox.showerror("AWS Connection Error", f"Failed to connect: {e}")

    def connect_azure(self):
        """Connect to Azure with user credentials"""
        cred = show_azure_login(self.root)
        if cred is None:
            return

        try:
            from cost_optimization.azure_optimizer import AzureCostOptimizer
            opt = AzureCostOptimizer(cred['subscription_id'])
            # InteractiveBrowserCredential will open a browser window for login
            list(opt.compute_client.virtual_machines.list_all())
            self.azure_credentials = cred
            self.azure_connected = True
            self.azure_status.configure(text=f"✅ Azure: Connected ({cred['subscription_id'][:8]}...)", fg="green")
        except ImportError:
            self.azure_credentials = cred
            self.azure_connected = True
            self.azure_status.configure(text=f"✅ Azure: Connected (simulated)", fg="green")
        except Exception as e:
            messagebox.showerror("Azure Connection Error", f"Failed to connect: {e}\n\nNote: A browser window will open for authentication. Please complete the login in your browser.")

    def connect_aws_real(self):
        """Connect to AWS and run real analysis"""
        try:
            from cost_optimization.aws_optimizer import AWSCostOptimizer
            opt = AWSCostOptimizer(self.aws_credentials['region'])

            results = []
            total = 0.0

            if self.ec2_var.get():
                recs = opt.identify_idle_ec2()
                for r in recs:
                    results.append(f"EC2: {r.action}")
                    total += r.potential_savings

            if self.ebs_var.get():
                recs = opt.get_orphaned_ebs_volumes()
                for r in recs:
                    results.append(f"EBS: {r.action}")
                    total += r.potential_savings

            if self.ri_var.get():
                recs = opt.get_reserved_instance_recommendations()
                for r in recs:
                    results.append(f"RI: {r.action}")
                    total += r.potential_savings

            self.aws_results.delete("1.0", tk.END)
            self.aws_results.insert("1.0", "\n".join(results) if results else "No savings found")
            self.aws_savings.configure(text=f"Estimated Savings: ${total:,.2f}")

            self.update_total()

        except ImportError:
            self.run_aws_simulation()
        except Exception as e:
            messagebox.showerror("Error", f"AWS analysis failed: {e}")

    def connect_azure_real(self):
        """Connect to Azure and run real analysis"""
        try:
            from cost_optimization.azure_optimizer import AzureCostOptimizer
            opt = AzureCostOptimizer(self.azure_credentials['subscription_id'])

            results = []
            total = 0.0

            if self.vm_var.get():
                recs = opt.identify_idle_vms()
                for r in recs:
                    results.append(f"VM: {r.action}")
                    total += r.potential_savings

            if self.disk_var.get():
                recs = opt.get_orphaned_disks()
                for r in recs:
                    results.append(f"Disk: {r.action}")
                    total += r.potential_savings

            if self.reservation_var.get():
                recs = opt.get_reserved_instance_recommendations()
                for r in recs:
                    results.append(f"Reservation: {r.action}")
                    total += r.potential_savings

            self.azure_results.delete("1.0", tk.END)
            self.azure_results.insert("1.0", "\n".join(results) if results else "No savings found")
            self.azure_savings.configure(text=f"Estimated Savings: ${total:,.2f}")

            self.update_total()

        except ImportError:
            self.run_azure_simulation()
        except Exception as e:
            messagebox.showerror("Error", f"Azure analysis failed: {e}")

    def run_aws_analysis(self):
        """Run AWS analysis - either real or simulated"""
        if not self.aws_connected:
            messagebox.showwarning("AWS", "Please connect to AWS first")
            return

        if self.aws_credentials and any([self.ec2_var.get(), self.ebs_var.get(), self.ri_var.get()]):
            self.connect_aws_real()
        else:
            self.run_aws_simulation()

    def run_azure_analysis(self):
        """Run Azure analysis - either real or simulated"""
        if not self.azure_connected:
            messagebox.showwarning("Azure", "Please connect to Azure first")
            return

        if self.azure_credentials and any([self.vm_var.get(), self.disk_var.get(), self.reservation_var.get()]):
            self.connect_azure_real()
        else:
            self.run_azure_simulation()

    def run_aws_simulation(self):
        if not self.aws_connected:
            messagebox.showwarning("AWS", "Please connect to AWS first")
            return

        lines = []
        total = 0.0

        if self.ec2_var.get():
            lines.append("EC2 Instances:")
            lines.append("  - i-1234567890abcdef0: Idle (CPU < 5%), Save $45.00/month")
            lines.append("  - i-0987654321fedcba0: Under-utilized, Save $120.00/month")
            total += 165

        if self.ebs_var.get():
            lines.append("\nEBS Volumes:")
            lines.append("  - vol-1234567890: 50GB unattached, Save $5.60/month")
            lines.append("  - vol-0987654321: 200GB in gp2, Convert to gp3 Save $13.44/month")
            total += 19.04

        if self.s3_var.get():
            lines.append("\nS3 Buckets:")
            lines.append("  - company-data-bucket: 80% cold data, Enable Intelligent-Tiering Save $150.00/month")
            total += 150

        if self.ri_var.get():
            lines.append("\nReserved Instance Recommendations:")
            lines.append("  - m5.large: 30-month usage, 40% savings, Save $280.00/month")
            lines.append("  - r5.xlarge: 15-month usage, 35% savings, Save $420.00/month")
            total += 700

        self.aws_results.delete("1.0", tk.END)
        self.aws_results.insert("1.0", "\n".join(lines) if lines else "No results")
        self.aws_savings.configure(text=f"Estimated Savings: ${total:,.2f}")

        self.update_total()

    def run_azure_simulation(self):
        if not self.azure_connected:
            messagebox.showwarning("Azure", "Please connect to Azure first")
            return

        lines = []
        total = 0.0

        if self.vm_var.get():
            lines.append("Virtual Machines:")
            lines.append("  - dev-web-vm: Stopped outside hours, Save $180.00/month")
            lines.append("  - test-db-vm: <15% CPU, Stop or resize, Save $95.00/month")
            total += 275

        if self.disk_var.get():
            lines.append("\nManaged Disks:")
            lines.append("  - test-disk-01: 128GB unattached, Save $6.40/month")
            lines.append("  - backup-osdisk: 64GB unattached, Save $3.20/month")
            total += 9.60

        if self.storage_var.get():
            lines.append("\nStorage Accounts:")
            lines.append("  - company-blob: 70% cold data, Move to Archive, Save $250.00/month")
            total += 250

        if self.reservation_var.get():
            lines.append("\nReservation Recommendations:")
            lines.append("  - Standard_D4s_v3: 1-year term, 38% savings, Save $156.00/month")
            lines.append("  - Standard_E8s_v3: 3-year term, 45% savings, Save $378.00/month")
            total += 534

        self.azure_results.delete("1.0", tk.END)
        self.azure_results.insert("1.0", "\n".join(lines) if lines else "No results")
        self.azure_savings.configure(text=f"Estimated Savings: ${total:,.2f}")

        self.update_total()

    def update_total(self):
        # Parse savings from labels
        aws_text = self.aws_savings.cget("text")
        azure_text = self.azure_savings.cget("text")

        try:
            aws_val = float(aws_text.split("$")[1].replace(",", "")) if "$" in aws_text else 0
        except:
            aws_val = 0

        try:
            azure_val = float(azure_text.split("$")[1].replace(",", "")) if "$" in azure_text else 0
        except:
            azure_val = 0

        self.total_savings = aws_val + azure_val
        self.summary.configure(text=f"Total Potential Savings: ${self.total_savings:,.2f}/month")

    def export_recommendations(self):
        data = {
            "generated_at": datetime.now().isoformat(),
            "aws": {"connected": self.aws_connected},
            "azure": {"connected": self.azure_connected},
            "total_potential_savings": self.total_savings
        }

        filepath = os.path.join(os.path.expanduser("~"), "Desktop", "finops-recommendations.json")
        with open(filepath, 'w') as f:
            json.dump(data, f, indent=2)

        messagebox.showinfo("Export Complete", f"Recommendations saved to:\n{filepath}")

    def run(self):
        self.root.mainloop()


def main():
    app = FinOpsSimpleGUI()
    app.run()


if __name__ == "__main__":
    main()