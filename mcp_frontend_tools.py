#!/usr/bin/env python3
"""
MCP Server for Frontend Development Tools
Provides persistent state management and verification tools for Claude
"""

import json
import os
import subprocess
import hashlib
from pathlib import Path
from typing import Dict, List, Any, Optional
from datetime import datetime

class FrontendStateManager:
    """Manages frontend configuration state persistently"""

    def __init__(self, project_root: str = "/Users/erik/Desktop/claude-multiagent-system"):
        self.project_root = Path(project_root)
        self.state_file = self.project_root / ".mcp_frontend_state.json"
        self.config_checksums = {}
        self.load_state()

    def load_state(self):
        """Load persistent state"""
        if self.state_file.exists():
            with open(self.state_file) as f:
                self.state = json.load(f)
        else:
            self.state = {
                "components": {},
                "api_endpoints": {},
                "port_mappings": {},
                "verified_connections": {},
                "last_known_good": None
            }

    def save_state(self):
        """Save state to disk"""
        with open(self.state_file, 'w') as f:
            json.dump(self.state, f, indent=2)

    def track_component(self, component_name: str, file_path: str, config: Dict):
        """Track a React component configuration"""
        file_hash = self._get_file_hash(file_path)
        self.state["components"][component_name] = {
            "file": file_path,
            "hash": file_hash,
            "config": config,
            "last_modified": datetime.now().isoformat()
        }
        self.save_state()
        return file_hash

    def verify_component(self, component_name: str) -> Dict:
        """Verify if component has been modified"""
        if component_name not in self.state["components"]:
            return {"status": "not_tracked"}

        comp = self.state["components"][component_name]
        current_hash = self._get_file_hash(comp["file"])

        return {
            "status": "unchanged" if current_hash == comp["hash"] else "modified",
            "tracked_hash": comp["hash"],
            "current_hash": current_hash,
            "config": comp["config"]
        }

    def track_api_endpoint(self, name: str, url: str, expected_response: Dict):
        """Track API endpoint configuration"""
        self.state["api_endpoints"][name] = {
            "url": url,
            "expected_response_keys": list(expected_response.keys()),
            "last_verified": None
        }
        self.save_state()

    def verify_api_endpoint(self, name: str) -> Dict:
        """Verify API endpoint is responding correctly"""
        import requests

        if name not in self.state["api_endpoints"]:
            return {"status": "not_tracked"}

        endpoint = self.state["api_endpoints"][name]
        try:
            response = requests.get(endpoint["url"], timeout=5)
            data = response.json()

            missing_keys = [k for k in endpoint["expected_response_keys"]
                          if k not in data]

            result = {
                "status": "working" if not missing_keys else "incomplete",
                "status_code": response.status_code,
                "missing_keys": missing_keys,
                "response_sample": str(data)[:200]
            }

            self.state["api_endpoints"][name]["last_verified"] = datetime.now().isoformat()
            self.save_state()

            return result

        except Exception as e:
            return {
                "status": "error",
                "error": str(e)
            }

    def _get_file_hash(self, file_path: str) -> str:
        """Get hash of file contents"""
        path = Path(file_path)
        if not path.exists():
            return "file_not_found"

        with open(path, 'rb') as f:
            return hashlib.md5(f.read()).hexdigest()

    def snapshot_good_state(self, name: str):
        """Save current state as known good configuration"""
        self.state["last_known_good"] = {
            "name": name,
            "timestamp": datetime.now().isoformat(),
            "components": self.state["components"].copy(),
            "api_endpoints": self.state["api_endpoints"].copy()
        }
        self.save_state()
        return "Snapshot saved"

    def restore_good_state(self) -> Dict:
        """Get last known good configuration"""
        if not self.state.get("last_known_good"):
            return {"status": "no_snapshot"}
        return self.state["last_known_good"]

    def verify_all_connections(self) -> Dict:
        """Comprehensive verification of all tracked components"""
        results = {
            "components": {},
            "api_endpoints": {},
            "overall_status": "healthy"
        }

        # Check components
        for comp_name in self.state["components"]:
            results["components"][comp_name] = self.verify_component(comp_name)
            if results["components"][comp_name]["status"] == "modified":
                results["overall_status"] = "components_modified"

        # Check APIs
        for api_name in self.state["api_endpoints"]:
            results["api_endpoints"][api_name] = self.verify_api_endpoint(api_name)
            if results["api_endpoints"][api_name]["status"] != "working":
                results["overall_status"] = "api_issues"

        return results

class ReactComponentAnalyzer:
    """Analyzes React components for MCP connectivity"""

    @staticmethod
    def find_mcp_references(file_path: str) -> Dict:
        """Find all MCP-related code in a component"""
        with open(file_path) as f:
            content = f.read()

        results = {
            "imports": [],
            "api_calls": [],
            "state_vars": [],
            "mcp_logic": []
        }

        lines = content.split('\n')
        for i, line in enumerate(lines, 1):
            # Find imports
            if 'import' in line and 'mcp' in line.lower():
                results["imports"].append({"line": i, "code": line.strip()})

            # Find API calls
            if 'fetch(' in line and ('mcp' in line.lower() or '5001' in line):
                results["api_calls"].append({"line": i, "code": line.strip()})

            # Find state variables
            if 'useState' in line and 'mcp' in line.lower():
                results["state_vars"].append({"line": i, "code": line.strip()})

            # Find MCP logic
            if 'mcpStatus' in line or 'agentMCPStatus' in line:
                results["mcp_logic"].append({"line": i, "code": line.strip()})

        return results

    @staticmethod
    def generate_test_code(component_name: str, api_endpoint: str) -> str:
        """Generate test code for a component"""
        return f'''
// Test code for {component_name}
// Paste this in browser console:

(async function testMCPConnection() {{
    console.log("🧪 Testing MCP for {component_name}");

    try {{
        const response = await fetch('{api_endpoint}');
        const data = await response.json();

        console.log("✅ API Response:", data);

        // Check expected structure
        const hasAgentStates = data.agent_states && Array.isArray(data.agent_states);
        const hasServerRunning = typeof data.server_running === 'boolean';

        console.log("Agent States:", hasAgentStates ? "✅" : "❌");
        console.log("Server Running:", hasServerRunning ? "✅" : "❌");

        if (data.agent_states) {{
            console.log("Agents:", data.agent_states.map(a => `${{a.agent}}: ${{a.status}}`));
        }}

        // Check React component
        const reactRoot = document.querySelector('#root')._reactRootContainer;
        console.log("React Root:", reactRoot ? "✅" : "❌");

    }} catch (error) {{
        console.error("❌ Test failed:", error);
    }}
}})();
'''

# MCP Tool Functions
def initialize_frontend_tracking(project_root: str = None) -> str:
    """Initialize frontend state tracking"""
    manager = FrontendStateManager(project_root or os.getcwd())

    # Track MultiTerminal component
    terminal_path = manager.project_root / "claude-ui/src/components/terminal/MultiTerminal.tsx"
    if terminal_path.exists():
        manager.track_component("MultiTerminal", str(terminal_path), {
            "fetch_url": "http://localhost:5001/api/mcp/status",
            "polling_interval": 10000,
            "expected_props": ["agents", "mcpStatus"]
        })

    # Track MCP API endpoint
    manager.track_api_endpoint("mcp_status", "http://localhost:5001/api/mcp/status", {
        "server_running": bool,
        "agent_states": list,
        "stats": dict
    })

    return "Frontend tracking initialized"

def verify_mcp_connection() -> Dict:
    """Verify all MCP connections"""
    manager = FrontendStateManager()
    return manager.verify_all_connections()

def analyze_component(component_path: str) -> Dict:
    """Analyze a React component for MCP integration"""
    analyzer = ReactComponentAnalyzer()
    return analyzer.find_mcp_references(component_path)

def generate_debug_dashboard() -> str:
    """Generate a debug dashboard HTML"""
    manager = FrontendStateManager()
    status = manager.verify_all_connections()

    html = f'''<!DOCTYPE html>
<html>
<head>
    <title>MCP Debug Dashboard</title>
    <style>
        body {{ font-family: monospace; padding: 20px; background: #1a1a1a; color: #fff; }}
        .status-ok {{ color: #4ade80; }}
        .status-error {{ color: #f87171; }}
        .section {{ margin: 20px 0; padding: 15px; border: 1px solid #374151; }}
        pre {{ background: #111; padding: 10px; overflow-x: auto; }}
    </style>
</head>
<body>
    <h1>🔧 MCP Frontend Debug Dashboard</h1>
    <div class="section">
        <h2>Overall Status: <span class="status-{('ok' if status['overall_status'] == 'healthy' else 'error')}">{status['overall_status']}</span></h2>
    </div>

    <div class="section">
        <h2>API Endpoints</h2>
        <pre>{json.dumps(status.get('api_endpoints', {}), indent=2)}</pre>
    </div>

    <div class="section">
        <h2>Components</h2>
        <pre>{json.dumps(status.get('components', {}), indent=2)}</pre>
    </div>

    <div class="section">
        <h2>Live Test</h2>
        <button onclick="testAPI()">Test API Connection</button>
        <div id="test-result"></div>
    </div>

    <script>
        async function testAPI() {{
            const result = document.getElementById('test-result');
            try {{
                const response = await fetch('http://localhost:5001/api/mcp/status');
                const data = await response.json();
                result.innerHTML = '<pre class="status-ok">' + JSON.stringify(data, null, 2) + '</pre>';
            }} catch (error) {{
                result.innerHTML = '<pre class="status-error">Error: ' + error + '</pre>';
            }}
        }}

        // Auto-refresh every 5 seconds
        setInterval(testAPI, 5000);
        testAPI();
    </script>
</body>
</html>'''

    dashboard_path = manager.project_root / "mcp_debug_dashboard.html"
    with open(dashboard_path, 'w') as f:
        f.write(html)

    return str(dashboard_path)

if __name__ == "__main__":
    # Initialize tracking
    print(initialize_frontend_tracking())

    # Verify connections
    status = verify_mcp_connection()
    print(json.dumps(status, indent=2))

    # Generate dashboard
    dashboard = generate_debug_dashboard()
    print(f"Dashboard created: {dashboard}")
    print(f"Open: open {dashboard}")