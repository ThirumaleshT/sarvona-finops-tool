"""
FinOps Optimizer GUI - Local Testing Interface
A local GUI for testing the FinOps Optimizer before connecting to cloud providers
"""

import tkinter as tk
from tkinter import ttk, messagebox
import customtkinter as ctk
import json
import os
from datetime import datetime


class FinOpsGUI:
    """GUI for FinOps Optimizer - Local testing mode"""

    def __init__(self):
        self.root = ctk.CTk()
        ctk.set_appearance_mode("dark")
        ctk.set_default_color_theme("blue")

        self.root.title("FinOps Optimizer - Local Test Mode")
        self.root.geometry("900x600")

        self.aws_connected = False
        self.azure_connected = False

        self.total_savings = 0.0

        self.setup_ui()

    def setup_ui(self):
        """Setup the main UI components"""

        # Main container
        main_frame = ctk.CTkFrame(self.root)
        main_frame.pack(fill="both", expand=True, padx=10, pady=10)

        # Header
        header = ctk.CTkLabel(
            main_frame,
            text="FinOps Optimizer",
            font=ctk.CTkFont(size=24, weight="bold")
        )
        header.pack(pady=10)

        # Status indicators
        status_frame = ctk.CTkFrame(main_frame)
        status_frame.pack(fill="x", pady=(0, 10))

        self.aws_status = ctk.CTkLabel(status_frame, text="AWS: Not Connected")
        self.aws_status.pack(side="left", padx=10)

        ctk.CTkLabel(status_frame, text=" | ").pack(side="left")

        self.azure_status = ctk.CTkLabel(status_frame, text="Azure: Not Connected")
        self.azure_status.pack(side="left")

        # Tab view
        self.tabview = ctk.CTkTabview(main_frame)
        self.tabview.pack(fill="both", expand=True)

        self.tabview.add("Dashboard")
        self.tabview.add("AWS")
        self.tabview.add("Azure")

        self.setup_dashboard_tab()
        self.setup_aws_tab()
        self.setup_azure_tab()

    def setup_dashboard_tab(self):
        """Setup dashboard tab with cost savings actions"""

        frame = self.tabview.tab("Dashboard")

        title = ctk.CTkLabel(
            frame, text="Cost Optimization Actions",
            font=ctk.CTkFont(size=18, weight="bold")
        )
        title.pack(pady=10)

        # Summary
        self.summary = ctk.CTkLabel(
            frame, text="Total Potential Savings: $0.00/month",
            font=ctk.CTkFont(size=16, weight="bold")
        )
        self.summary.pack(pady=10)

        # Action cards as frames
        actions = [
            ("🖥️ EC2/VM Optimization", "Stop idle instances, right-size based on utilization", "$500-5000/mo"),
            ("💾 Storage Optimization", "Delete orphaned disks, enable intelligent tiering", "$100-2000/mo"),
            ("📦 Reserved Instances", "Purchase RIs for consistent workloads", "20-60% savings"),
            ("⚡ Spot/Low-Priority VMs", "Convert fault-tolerant workloads to spot", "60-90% savings"),
            ("🔄 Azure Hybrid Benefit", "Apply AHUB for Windows VMs", "40-50% savings")
        ]

        for name, desc, benefit in actions:
            card = ctk.CTkFrame(frame, corner_radius=8)
            card.pack(fill="x", padx=20, pady=5)

            ctk.CTkLabel(card, text=name, font=ctk.CTkFont(weight="bold")).pack(anchor="w", padx=10, pady=5)
            ctk.CTkLabel(card, text=desc, text_color="gray").pack(anchor="w", padx=15)
            ctk.CTkLabel(card, text=benefit, text_color="#4ade80").pack(anchor="w", padx=15, pady=(0, 5))

        # Export button
        export_btn = ctk.CTkButton(
            frame, text="Export Recommendations",
            command=self.export_recommendations
        )
        export_btn.pack(pady=15)

    def setup_aws_tab(self):
        """Setup AWS analysis tab"""

        frame = self.tabview.tab("AWS")

        # Connection
        conn_frame = ctk.CTkFrame(frame)
        conn_frame.pack(fill="x", pady=5)

        ctk.CTkLabel(conn_frame, text="AWS Connection:").pack(side="left", padx=5)
        self.aws_connect_btn = ctk.CTkButton(
            conn_frame, text="Connect (Simulated)",
            command=self.simulate_aws_connection
        )
        self.aws_connect_btn.pack(side="left", padx=5)

        # Options
        ctk.CTkLabel(frame, text="Analysis Options:").pack(anchor="w", padx=10, pady=10)

        self.ec2_var = tk.BooleanVar()
        ctk.CTkCheckBox(frame, text="Check idle EC2 instances", variable=self.ec2_var).pack(anchor="w", padx=20)

        self.ebs_var = tk.BooleanVar()
        ctk.CTkCheckBox(frame, text="Find orphaned EBS volumes", variable=self.ebs_var).pack(anchor="w", padx=20)

        self.s3_var = tk.BooleanVar()
        ctk.CTkCheckBox(frame, text="Check S3 storage optimization", variable=self.s3_var).pack(anchor="w", padx=20)

        self.ri_var = tk.BooleanVar()
        ctk.CTkCheckBox(frame, text="Get RI recommendations", variable=self.ri_var).pack(anchor="w", padx=20)

        # Run button
        ctk.CTkButton(frame, text="Run AWS Analysis", command=self.run_aws_simulation).pack(pady=10)

        # Results
        self.aws_results = ctk.CTkTextbox(frame, height=150)
        self.aws_results.pack(fill="both", expand=True, pady=(10, 0))

        # Savings
        self.aws_savings = ctk.CTkLabel(frame, text="Estimated Savings: $0.00")
        self.aws_savings.pack(pady=5)

    def setup_azure_tab(self):
        """Setup Azure analysis tab"""

        frame = self.tabview.tab("Azure")

        # Connection
        conn_frame = ctk.CTkFrame(frame)
        conn_frame.pack(fill="x", pady=5)

        ctk.CTkLabel(conn_frame, text="Azure Connection:").pack(side="left", padx=5)
        self.azure_connect_btn = ctk.CTkButton(
            conn_frame, text="Connect (Simulated)",
            command=self.simulate_azure_connection
        )
        self.azure_connect_btn.pack(side="left", padx=5)

        # Options
        ctk.CTkLabel(frame, text="Analysis Options:").pack(anchor="w", padx=10, pady=10)

        self.vm_var = tk.BooleanVar()
        ctk.CTkCheckBox(frame, text="Check idle VMs", variable=self.vm_var).pack(anchor="w", padx=20)

        self.disk_var = tk.BooleanVar()
        ctk.CTkCheckBox(frame, text="Find orphaned disks", variable=self.disk_var).pack(anchor="w", padx=20)

        self.storage_var = tk.BooleanVar()
        ctk.CTkCheckBox(frame, text="Check storage optimization", variable=self.storage_var).pack(anchor="w", padx=20)

        self.reservation_var = tk.BooleanVar()
        ctk.CTkCheckBox(frame, text="Get reservation recommendations", variable=self.reservation_var).pack(anchor="w", padx=20)

        # Run button
        ctk.CTkButton(frame, text="Run Azure Analysis", command=self.run_azure_simulation).pack(pady=10)

        # Results
        self.azure_results = ctk.CTkTextbox(frame, height=150)
        self.azure_results.pack(fill="both", expand=True, pady=(10, 0))

        # Savings
        self.azure_savings = ctk.CTkLabel(frame, text="Estimated Savings: $0.00")
        self.azure_savings.pack(pady=5)

    def simulate_aws_connection(self):
        """Simulate AWS connection"""
        self.aws_connected = True
        self.aws_status.configure(text="✅ AWS: Connected (Simulated)")
        self.aws_connect_btn.configure(state="disabled")

    def simulate_azure_connection(self):
        """Simulate Azure connection"""
        self.azure_connected = True
        self.azure_status.configure(text="✅ Azure: Connected (Simulated)")
        self.azure_connect_btn.configure(state="disabled")

    def run_aws_simulation(self):
        """Run simulated AWS analysis"""
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

        # Update total
        self.update_total_savings()

    def run_azure_simulation(self):
        """Run simulated Azure analysis"""
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

        self.update_total_savings()

    def update_total_savings(self):
        """Update total savings display"""
        aws_text = self.aws_savings.cget("text")
        azure_text = self.azure_savings.cget("text")

        aws_val = float(aws_text.split("$")[1].replace(",", "")) if "$" in aws_text else 0
        azure_val = float(azure_text.split("$")[1].replace(",", "")) if "$" in azure_text else 0

        self.total_savings = aws_val + azure_val
        self.summary.configure(text=f"Total Potential Savings: ${self.total_savings:,.2f}/month")

    def export_recommendations(self):
        """Export recommendations to JSON file"""
        data = {
            "generated_at": datetime.now().isoformat(),
            "aws": {
                "connected": self.aws_connected,
                "recommendations": []
            },
            "azure": {
                "connected": self.azure_connected,
                "recommendations": []
            },
            "total_potential_savings": self.total_savings
        }

        filepath = os.path.join(
            os.path.expanduser("~"),
            "Desktop",
            "finops-recommendations.json"
        )
        with open(filepath, 'w') as f:
            json.dump(data, f, indent=2)

        messagebox.showinfo("Export Complete", f"Recommendations exported to:\n{filepath}")

    def run(self):
        """Start the GUI application"""
        self.root.mainloop()


def main():
    """Main entry point for GUI mode"""
    app = FinOpsGUI()
    app.run()


if __name__ == "__main__":
    main()