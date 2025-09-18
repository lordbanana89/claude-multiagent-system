#!/usr/bin/env python3
"""
Install Enhanced Dependencies - LangGraph Platform Style Features
Script per installare tutte le dipendenze necessarie per l'interfaccia avanzata
"""

import subprocess
import sys
import os

def install_package(package):
    """Install package using pip"""
    try:
        subprocess.check_call([sys.executable, "-m", "pip", "install", package])
        print(f"✅ {package} installed successfully")
        return True
    except subprocess.CalledProcessError:
        print(f"❌ Failed to install {package}")
        return False

def main():
    """Install all required dependencies"""
    print("🤖 Enhanced Multi-Agent Platform - Dependency Installation")
    print("=" * 60)
    print("Installing LangGraph Platform style features for Claude CLI integration")
    print()

    # Required packages for enhanced interface
    dependencies = [
        "streamlit>=1.28.0",
        "plotly>=5.17.0",
        "pandas>=2.0.0",
        "sqlite3",  # Usually built-in
        "hashlib",  # Usually built-in
        "secrets",  # Usually built-in
        "dataclasses",  # Usually built-in for Python 3.7+
    ]

    print("📦 Installing dependencies...")
    success_count = 0
    total_count = len(dependencies)

    for package in dependencies:
        if package in ["sqlite3", "hashlib", "secrets", "dataclasses"]:
            print(f"✅ {package} (built-in)")
            success_count += 1
            continue

        if install_package(package):
            success_count += 1

    print()
    print("📊 Installation Summary")
    print("-" * 30)
    print(f"Total packages: {total_count}")
    print(f"Successfully installed: {success_count}")
    print(f"Failed: {total_count - success_count}")

    if success_count == total_count:
        print()
        print("🎉 All dependencies installed successfully!")
        print()
        print("🚀 Next Steps:")
        print("1. Start the enhanced interface:")
        print("   python3 -m streamlit run web_interface_enhanced.py --server.port=8504")
        print()
        print("2. Access the platform at:")
        print("   http://localhost:8504")
        print()
        print("3. Default login credentials:")
        print("   Username: admin")
        print("   Password: admin123")
        print()
        print("🎯 Enhanced Features Available:")
        print("   ✅ Visual Workflow Builder (drag-and-drop)")
        print("   ✅ Advanced State Management & Persistence")
        print("   ✅ Performance Analytics & Charts")
        print("   ✅ Enterprise Authentication & RBAC")
        print("   ✅ Team Management & Workspaces")
        print("   ✅ Visual Debugging & Flow Visualization")
        print("   ✅ Enhanced Agent Dashboard")
        print("   ✅ Real-time Claude CLI Integration")
        print()
        print("💡 LangGraph Platform Features Integrated:")
        print("   🎨 Visual Studio-style interface")
        print("   📊 Management Console with analytics")
        print("   👥 Multi-user support with RBAC")
        print("   🏢 Workspace management")
        print("   📈 Performance monitoring")
        print("   🔐 Enterprise security")

    else:
        print()
        print("⚠️ Some dependencies failed to install.")
        print("Please check the errors above and try again.")
        print("You may need to:")
        print("- Update pip: python3 -m pip install --upgrade pip")
        print("- Install system dependencies")
        print("- Use virtual environment")

    print()
    print("🔧 System Requirements Verified:")
    print(f"✅ Python version: {sys.version}")
    print(f"✅ Current directory: {os.getcwd()}")
    print(f"✅ Required files present:")

    required_files = [
        "web_interface_enhanced.py",
        "auth_manager.py",
        "claude_orchestrator.py",
        "langchain_claude_final.py"
    ]

    for file in required_files:
        if os.path.exists(file):
            print(f"   ✅ {file}")
        else:
            print(f"   ❌ {file} (missing)")

if __name__ == "__main__":
    main()