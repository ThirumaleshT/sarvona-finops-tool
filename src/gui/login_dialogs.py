"""
Cloud Credential Login Dialogs
Interactive forms for AWS and Azure authentication in the GUI
"""

import tkinter as tk
from tkinter import ttk, messagebox
import os


class AWSLoginDialog:
    """AWS Credential Login Dialog"""

    def __init__(self, parent):
        self.parent = parent
        self.result = None
        self.access_key = None
        self.secret_key = None
        self.region = None
        self.session_token = None

    def show(self):
        """Show the login dialog and return credentials"""
        dialog = tk.Toplevel(self.parent)
        dialog.title("🔐 AWS Login")
        dialog.geometry("400x350")
        dialog.resizable(False, False)
        dialog.transient(self.parent)
        dialog.grab_set()

        # Center dialog
        dialog.update_idletasks()
        x = (dialog.winfo_screenwidth() // 2) - (dialog.winfo_reqwidth() // 2)
        y = (dialog.winfo_screenheight() // 2) - (dialog.winfo_reqheight() // 2)
        dialog.geometry(f"+{x}+{y}")

        # Form title
        tk.Label(dialog, text="AWS Credential Login", font=("Helvetica", 16, "bold")).pack(pady=15)

        # Access Key ID
        key_frame = tk.Frame(dialog)
        key_frame.pack(fill="x", padx=20, pady=5)
        tk.Label(key_frame, text="Access Key ID:", width=15, anchor="w").pack(side="left")
        self.access_entry = tk.Entry(key_frame, width=30)
        self.access_entry.pack(side="left")

        # Secret Access Key
        secret_frame = tk.Frame(dialog)
        secret_frame.pack(fill="x", padx=20, pady=5)
        tk.Label(secret_frame, text="Secret Key:", width=15, anchor="w").pack(side="left")
        self.secret_entry = tk.Entry(secret_frame, width=30, show="*")
        self.secret_entry.pack(side="left")

        # Session Token (optional)
        session_frame = tk.Frame(dialog)
        session_frame.pack(fill="x", padx=20, pady=5)
        tk.Label(session_frame, text="Session Token:", width=15, anchor="w").pack(side="left")
        self.session_entry = tk.Entry(session_frame, width=30)
        self.session_entry.pack(side="left")

        # Region
        region_frame = tk.Frame(dialog)
        region_frame.pack(fill="x", padx=20, pady=5)
        tk.Label(region_frame, text="Region:", width=15, anchor="w").pack(side="left")
        self.region_var = tk.StringVar(value="us-east-1")
        region_combo = ttk.Combobox(region_frame, textvariable=self.region_var, width=27,
                                    values=["us-east-1", "us-east-2", "us-west-1", "us-west-2",
                                         "eu-west-1", "eu-west-2", "eu-west-3", "eu-central-1",
                                         "ap-southeast-1", "ap-southeast-2", "ap-northeast-1", "sa-east-1"])
        region_combo.pack(side="left")

        # Buttons
        btn_frame = tk.Frame(dialog)
        btn_frame.pack(fill="x", pady=20)

        def on_connect():
            access = self.access_entry.get().strip()
            secret = self.secret_entry.get().strip()
            token = self.session_entry.get().strip()
            region = self.region_var.get()

            if not access or not secret:
                messagebox.showerror("Error", "Access Key ID and Secret Key are required")
                return

            # Store credentials
            self.access_key = access
            self.secret_key = secret
            self.region = region
            self.session_token = token if token else None

            dialog.destroy()

        def on_cancel():
            dialog.destroy()

        tk.Button(btn_frame, text="Connect", command=on_connect, bg="#4ade80", width=10).pack(side="left", padx=20)
        tk.Button(btn_frame, text="Cancel", command=on_cancel, bg="#f87171", width=10).pack(side="right", padx=20)

        dialog.wait_window()
        return self.result is not None if hasattr(self, 'result') else self.access_key is not None


class AzureLoginDialog:
    """Azure Authentication Dialog with Interactive Browser Login"""

    def __init__(self, parent):
        self.parent = parent
        self.auth_method = None
        self.subscription_id = None

    def show(self):
        """Show the simplified Azure login dialog"""
        dialog = tk.Toplevel(self.parent)
        dialog.title("🔐 Azure Login")
        dialog.geometry("450x250")
        dialog.resizable(False, False)
        dialog.transient(self.parent)
        dialog.grab_set()

        # Center dialog
        dialog.update_idletasks()
        x = (dialog.winfo_screenwidth() // 2) - (dialog.winfo_reqwidth() // 2)
        y = (dialog.winfo_screenheight() // 2) - (dialog.winfo_reqheight() // 2)
        dialog.geometry(f"+{x}+{y}")

        # Title
        tk.Label(dialog, text="Azure Authentication", font=("Helvetica", 16, "bold")).pack(pady=15)

        tk.Label(dialog, text="Enter your Subscription ID and click Login.\nA browser window will open for secure authentication.",
                 font=("Helvetica", 10), justify="center").pack(pady=5)

        # Subscription ID
        sub_frame = tk.Frame(dialog)
        sub_frame.pack(fill="x", padx=20, pady=10)
        tk.Label(sub_frame, text="Subscription ID:", width=15, anchor="w").pack(side="left")
        self.sub_entry = tk.Entry(sub_frame, width=35)
        self.sub_entry.pack(side="left")

        # Buttons
        btn_frame = tk.Frame(dialog)
        btn_frame.pack(fill="x", pady=20)

        def on_login():
            sub = self.sub_entry.get().strip()
            if not sub:
                messagebox.showerror("Error", "Subscription ID is required")
                return

            self.auth_method = "interactive"
            self.subscription_id = sub
            dialog.destroy()

        def on_cancel():
            dialog.destroy()

        tk.Button(btn_frame, text="Login via Browser", command=on_login, bg="#4ade80", width=15).pack(side="left", padx=50)
        tk.Button(btn_frame, text="Cancel", command=on_cancel, bg="#f87171", width=10).pack(side="right", padx=50)

        dialog.wait_window()
        return self.auth_method is not None


def show_aws_login(parent):
    """Show AWS login dialog and return credentials"""
    dialog = AWSLoginDialog(parent)
    success = dialog.show()

    if success:
        # Set environment variables
        os.environ['AWS_ACCESS_KEY_ID'] = dialog.access_key
        os.environ['AWS_SECRET_ACCESS_KEY'] = dialog.secret_key
        if dialog.session_token:
            os.environ['AWS_SESSION_TOKEN'] = dialog.session_token

        return {
            'access_key': dialog.access_key,
            'secret_key': dialog.secret_key,
            'region': dialog.region,
            'session_token': dialog.session_token
        }
    return None


def show_azure_login(parent):
    """Show Azure login dialog and return credentials"""
    dialog = AzureLoginDialog(parent)
    success = dialog.show()

    if success:
        return {
            'auth_method': 'interactive',
            'subscription_id': dialog.subscription_id
        }
    return None