#!/usr/bin/env python3
"""
Quick validation script to test FinOps optimizer installation
Run this after pip installing the package
"""

import sys


def test_imports():
    print("Testing FinOps Optimizer installation...\n")

    errors = []

    # Test core imports
    try:
        from cost_optimization.aws_optimizer import AWSCostOptimizer
        print("✓ AWSCostOptimizer imported successfully")
    except ImportError as e:
        errors.append(f"AWS optimizer: {e}")
        print(f"✗ AWS optimizer import failed: {e}")

    try:
        from cost_optimization.azure_optimizer import AzureCostOptimizer
        print("✓ AzureCostOptimizer imported successfully")
    except ImportError as e:
        errors.append(f"Azure optimizer: {e}")
        print(f"✗ Azure optimizer import failed: {e}")

    try:
        from reports.report_generator import ReportGenerator
        print("✓ ReportGenerator imported successfully")
    except ImportError as e:
        errors.append(f"Report generator: {e}")
        print(f"✗ Report generator import failed: {e}")

    try:
        import click
        print("✓ Click CLI framework available")
    except ImportError as e:
        errors.append(f"Click: {e}")
        print(f"✗ Click CLI framework missing: {e}")

    print("\n" + "=" * 50)

    if errors:
        print(f"\n❌ {len(errors)} issues found:")
        for err in errors:
            print(f"  - {err}")
        print("\n🔧 Fix with: pip install -e .")
        return 1
    else:
        print("\n✅ All imports successful!")
        print("\nUsage:")
        print("  finops aws analyze                    # AWS cost analysis")
        print("  finops azure analyze                  # Azure cost analysis")
        print("  finops analyze --aws --azure          # Combined analysis")
        return 0


if __name__ == "__main__":
    sys.exit(test_imports())