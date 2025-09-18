#!/usr/bin/env python3
"""
Agent Creator System - Backend Logic for Dynamic Agent Creation
Sistema per la creazione dinamica di agenti Claude Code
"""

import json
import os
import time
import subprocess
from typing import Dict, List, Optional, Tuple
from datetime import datetime
from pathlib import Path
import uuid
import shutil

class PortManager:
    """Gestisce assegnazione e tracking delle porte per agenti"""

    def __init__(self, start_port: int = 8095, end_port: int = 8200):
        self.start_port = start_port
        self.end_port = end_port
        self.used_ports = set()
        self._load_existing_ports()

    def _load_existing_ports(self):
        """Carica porte già in uso dal sistema"""
        try:
            # Check existing agents in shared_state.json
            state_file = Path(__file__).parent / "shared_state.json"
            if state_file.exists():
                with open(state_file, 'r') as f:
                    state = json.load(f)

                agents = state.get('agents', {})
                for agent_id, agent_data in agents.items():
                    if 'port' in agent_data:
                        self.used_ports.add(agent_data['port'])

        except Exception as e:
            print(f"Warning: Could not load existing ports: {e}")

    def get_next_available_port(self) -> int:
        """Trova prossima porta disponibile"""
        for port in range(self.start_port, self.end_port + 1):
            if port not in self.used_ports and self._is_port_free(port):
                return port
        raise Exception(f"No available ports in range {self.start_port}-{self.end_port}")

    def _is_port_free(self, port: int) -> bool:
        """Verifica se porta è libera nel sistema"""
        try:
            result = subprocess.run(
                ["lsof", "-i", f":{port}"],
                capture_output=True,
                text=True,
                timeout=5
            )
            return result.returncode != 0  # Port is free if lsof returns non-zero
        except:
            return True  # Assume free if can't check

    def reserve_port(self, port: int) -> bool:
        """Riserva porta specifica"""
        if port in self.used_ports:
            return False
        if not self._is_port_free(port):
            return False

        self.used_ports.add(port)
        return True

    def release_port(self, port: int):
        """Rilascia porta"""
        self.used_ports.discard(port)


class AgentTemplate:
    """Rappresenta un template per la creazione di agenti"""

    def __init__(self, template_id: str, config: Dict):
        self.template_id = template_id
        self.name = config.get('name', 'Unnamed Template')
        self.description = config.get('description', '')
        self.icon = config.get('icon', '🤖')
        self.category = config.get('category', 'General')
        self.capabilities = config.get('capabilities', [])
        self.instruction_template = config.get('instruction_template', '')
        self.initial_commands = config.get('initial_commands', [])
        self.default_config = config.get('default_config', {})

    def generate_instructions(self, agent_config: Dict) -> str:
        """Genera file istruzioni personalizzato basato su template"""
        instructions = self.instruction_template

        # Replace placeholders with actual values
        replacements = {
            '{AGENT_NAME}': agent_config.get('name', 'Agent'),
            '{AGENT_DESCRIPTION}': agent_config.get('description', ''),
            '{AGENT_CAPABILITIES}': '\n'.join([f"- {cap}" for cap in agent_config.get('capabilities', [])]),
            '{CREATION_DATE}': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            '{AGENT_ID}': agent_config.get('agent_id', ''),
            '{PORT}': str(agent_config.get('port', 'N/A')),
            '{SESSION}': agent_config.get('session', 'N/A')
        }

        for placeholder, value in replacements.items():
            instructions = instructions.replace(placeholder, value)

        return instructions

    def validate_config(self, agent_config: Dict) -> Tuple[bool, List[str]]:
        """Valida configurazione agente contro template"""
        errors = []

        # Check required fields (agent_id is optional as it can be auto-generated)
        required_fields = ['name', 'description']
        for field in required_fields:
            if not agent_config.get(field):
                errors.append(f"Missing required field: {field}")

        # Validate agent name format
        name = agent_config.get('name', '')
        if name and not name.replace(' ', '').replace('-', '').replace('_', '').isalnum():
            errors.append("Agent name can only contain letters, numbers, spaces, hyphens, and underscores")

        # Validate capabilities
        capabilities = agent_config.get('capabilities', [])
        if not isinstance(capabilities, list):
            errors.append("Capabilities must be a list")

        return len(errors) == 0, errors


class AgentCreator:
    """Sistema principale per creazione agenti dinamici"""

    def __init__(self, shared_state_file: str):
        self.shared_state_file = shared_state_file
        self.port_manager = PortManager()
        self.templates = self._load_templates()
        self.project_root = Path(__file__).parent

    def _load_templates(self) -> Dict[str, AgentTemplate]:
        """Carica template agenti disponibili"""
        templates = {}

        # Standard templates
        standard_templates = {
            "backend-api": {
                "name": "Backend API Agent",
                "icon": "🔧",
                "category": "Development",
                "description": "API development, server-side logic, microservices",
                "capabilities": [
                    "RESTful API development",
                    "Database integration",
                    "Authentication & authorization",
                    "Performance optimization",
                    "Error handling & logging"
                ],
                "instruction_template": """# 🔧 {AGENT_NAME} - Operational Instructions

## 🎯 PRIMARY ROLE
You are the **{AGENT_NAME}** specialized in backend development and API creation.

**Agent ID**: {AGENT_ID}
**Port**: {PORT}
**Session**: {SESSION}
**Created**: {CREATION_DATE}

## 💼 CORE CAPABILITIES
{AGENT_CAPABILITIES}

## 🔧 TOOLS AND COMMANDS

### Development Commands
```bash
# Start development server
npm run dev

# Run tests
npm test

# Build production
npm run build
```

## 📋 TASK TYPES

### ✅ API Development
- RESTful endpoint creation
- Database integration
- Authentication systems
- Performance optimization

## 🎯 EXAMPLE TASKS
- "Create user authentication API"
- "Design database schema"
- "Implement caching strategy"

---
**🚀 Ready to build amazing backend systems!**
""",
                "initial_commands": [
                    "echo '{AGENT_NAME} Ready! 🔧'",
                    "pwd",
                    "ls -la"
                ]
            },

            "frontend-ui": {
                "name": "Frontend UI Agent",
                "icon": "🎨",
                "category": "Development",
                "description": "User interface development, React, Vue, responsive design",
                "capabilities": [
                    "React/Vue development",
                    "Responsive design",
                    "Component architecture",
                    "State management",
                    "UI/UX optimization"
                ],
                "instruction_template": """# 🎨 {AGENT_NAME} - Operational Instructions

## 🎯 PRIMARY ROLE
You are the **{AGENT_NAME}** specialized in frontend development and user interface design.

**Agent ID**: {AGENT_ID}
**Port**: {PORT}
**Session**: {SESSION}
**Created**: {CREATION_DATE}

## 💼 CORE CAPABILITIES
{AGENT_CAPABILITIES}

## 🔧 TOOLS AND COMMANDS

### Frontend Commands
```bash
# Start development server
npm start

# Build production
npm run build

# Run tests
npm test
```

## 📋 TASK TYPES

### ✅ UI Development
- Component creation
- Responsive design
- State management
- Performance optimization

---
**🚀 Ready to create beautiful user interfaces!**
""",
                "initial_commands": [
                    "echo '{AGENT_NAME} Ready! 🎨'",
                    "npm --version",
                    "node --version"
                ]
            },

            "security-audit": {
                "name": "Security Audit Agent",
                "icon": "🛡️",
                "category": "Security",
                "description": "Security analysis, vulnerability assessment, compliance",
                "capabilities": [
                    "Vulnerability scanning",
                    "Code security review",
                    "Compliance checking",
                    "Penetration testing",
                    "Security documentation"
                ],
                "instruction_template": """# 🛡️ {AGENT_NAME} - Operational Instructions

## 🎯 PRIMARY ROLE
You are the **{AGENT_NAME}** specialized in security assessment and audit.

**Agent ID**: {AGENT_ID}
**Port**: {PORT}
**Session**: {SESSION}
**Created**: {CREATION_DATE}

## 💼 CORE CAPABILITIES
{AGENT_CAPABILITIES}

## 🔧 SECURITY TOOLS

### Vulnerability Assessment
```bash
# Network scanning
nmap -sV target_host

# Vulnerability scanning
nikto -h target_url

# SSL/TLS testing
testssl target_host
```

## 📋 SECURITY TASKS

### ✅ Security Assessment
- Vulnerability scanning
- Code review
- Compliance audit
- Risk assessment

---
**🚀 Ready to secure your systems!**
""",
                "initial_commands": [
                    "echo '{AGENT_NAME} Ready! 🛡️'",
                    "nmap --version",
                    "echo 'Security tools initialized'"
                ]
            },

            "devops-ci": {
                "name": "DevOps CI/CD Agent",
                "icon": "⚡",
                "category": "DevOps",
                "description": "CI/CD pipelines, infrastructure, deployment automation",
                "capabilities": [
                    "CI/CD pipeline design",
                    "Infrastructure as Code",
                    "Container orchestration",
                    "Monitoring & alerting",
                    "Deployment automation"
                ],
                "instruction_template": """# ⚡ {AGENT_NAME} - Operational Instructions

## 🎯 PRIMARY ROLE
You are the **{AGENT_NAME}** specialized in DevOps and CI/CD automation.

**Agent ID**: {AGENT_ID}
**Port**: {PORT}
**Session**: {SESSION}
**Created**: {CREATION_DATE}

## 💼 CORE CAPABILITIES
{AGENT_CAPABILITIES}

## 🔧 DEVOPS TOOLS

### CI/CD Commands
```bash
# Docker operations
docker build -t app:latest .
docker run -p 8080:8080 app:latest

# Kubernetes
kubectl apply -f deployment.yaml
kubectl get pods
```

## 📋 DEVOPS TASKS

### ✅ Infrastructure
- Pipeline creation
- Container management
- Infrastructure provisioning
- Monitoring setup

---
**🚀 Ready to automate your deployments!**
""",
                "initial_commands": [
                    "echo '{AGENT_NAME} Ready! ⚡'",
                    "docker --version",
                    "kubectl version --client"
                ]
            },

            "custom": {
                "name": "Custom Agent",
                "icon": "🎯",
                "category": "Custom",
                "description": "Blank template for custom agent creation",
                "capabilities": [],
                "instruction_template": """# 🎯 {AGENT_NAME} - Operational Instructions

## 🎯 PRIMARY ROLE
You are the **{AGENT_NAME}** - a custom agent created for specific tasks.

**Agent ID**: {AGENT_ID}
**Port**: {PORT}
**Session**: {SESSION}
**Created**: {CREATION_DATE}

## 💼 CORE CAPABILITIES
{AGENT_CAPABILITIES}

## 🔧 TOOLS AND COMMANDS
Add your custom tools and commands here.

## 📋 TASK TYPES
Define your specific task types here.

---
**🚀 Ready for custom tasks!**
""",
                "initial_commands": [
                    "echo '{AGENT_NAME} Ready! 🎯'",
                    "pwd"
                ]
            }
        }

        # Convert to AgentTemplate objects
        for template_id, config in standard_templates.items():
            templates[template_id] = AgentTemplate(template_id, config)

        return templates

    def get_available_templates(self) -> Dict[str, Dict]:
        """Ottieni template disponibili"""
        return {
            template_id: {
                "name": template.name,
                "description": template.description,
                "icon": template.icon,
                "category": template.category,
                "capabilities": template.capabilities
            }
            for template_id, template in self.templates.items()
        }

    def validate_agent_config(self, agent_config: Dict) -> Tuple[bool, List[str]]:
        """Valida configurazione agente completa"""
        errors = []

        # Check agent name uniqueness
        if self._agent_name_exists(agent_config.get('name', '')):
            errors.append("Agent name already exists")

        # Check agent ID uniqueness (only if provided)
        agent_id = agent_config.get('agent_id')
        if agent_id and self._agent_id_exists(agent_id):
            errors.append("Agent ID already exists")

        # Check session name uniqueness (only if provided)
        session = agent_config.get('session')
        if session and self._session_exists(session):
            errors.append("Session name already exists")

        # Validate port (only if provided)
        port = agent_config.get('port')
        if port:
            # Don't reserve port during validation, just check availability
            if not self.port_manager._is_port_free(port):
                errors.append(f"Port {port} is not available")

        # Template-specific validation
        template_id = agent_config.get('template')
        if template_id and template_id in self.templates:
            template = self.templates[template_id]
            is_valid, template_errors = template.validate_config(agent_config)
            errors.extend(template_errors)

        return len(errors) == 0, errors

    def create_agent(self, agent_config: Dict) -> Dict:
        """Crea nuovo agente dinamicamente"""
        try:
            # Validate configuration
            is_valid, errors = self.validate_agent_config(agent_config)
            if not is_valid:
                return {
                    "success": False,
                    "error": f"Validation failed: {'; '.join(errors)}",
                    "agent_id": None
                }

            # Generate unique agent ID if not provided
            if not agent_config.get('agent_id'):
                agent_config['agent_id'] = self._generate_agent_id(agent_config['name'])

            # Assign port if not provided
            if not agent_config.get('port'):
                agent_config['port'] = self.port_manager.get_next_available_port()

            # Generate session name if not provided
            if not agent_config.get('session'):
                agent_config['session'] = f"claude-{agent_config['agent_id']}"

            # Create instruction file
            instruction_file = self._create_instruction_file(agent_config)

            # Register agent in shared state
            self._register_agent_in_state(agent_config, instruction_file)

            # Create tmux session
            self._create_tmux_session(agent_config)

            # Log creation
            self._log_creation(agent_config)

            return {
                "success": True,
                "agent_id": agent_config['agent_id'],
                "port": agent_config['port'],
                "session": agent_config['session'],
                "instruction_file": instruction_file
            }

        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "agent_id": agent_config.get('agent_id')
            }

    def _generate_agent_id(self, name: str) -> str:
        """Genera ID agente unico"""
        base_id = name.lower().replace(' ', '-').replace('_', '-')
        base_id = ''.join(c for c in base_id if c.isalnum() or c == '-')

        # Ensure uniqueness
        counter = 1
        agent_id = base_id
        while self._agent_id_exists(agent_id):
            agent_id = f"{base_id}-{counter}"
            counter += 1

        return agent_id

    def _create_instruction_file(self, agent_config: Dict) -> str:
        """Crea file istruzioni per agente"""
        template_id = agent_config.get('template', 'custom')
        template = self.templates.get(template_id, self.templates['custom'])

        # Generate instructions
        instructions = template.generate_instructions(agent_config)

        # Save to file
        filename = f"{agent_config['agent_id'].upper()}_INSTRUCTIONS.md"
        file_path = self.project_root / filename

        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(instructions)

        return str(file_path)

    def _register_agent_in_state(self, agent_config: Dict, instruction_file: str):
        """Registra agente nel sistema di stato condiviso"""
        # Load current state
        with open(self.shared_state_file, 'r') as f:
            state = json.load(f)

        # Add new agent
        agent_data = {
            "agent_id": agent_config['agent_id'],
            "name": agent_config['name'],
            "status": "idle",
            "current_task": None,
            "last_activity": datetime.now().isoformat(),
            "session_id": agent_config['session'],
            "port": agent_config['port'],
            "capabilities": agent_config.get('capabilities', []),
            "error_message": None,
            "is_dynamic": True,
            "created_at": datetime.now().isoformat(),
            "created_by": "user",
            "template": agent_config.get('template', 'custom'),
            "instruction_file": instruction_file,
            "auto_start": agent_config.get('auto_start', False),
            "creation_config": {
                "original_config": agent_config,
                "template_used": agent_config.get('template', 'custom')
            }
        }

        state['agents'][agent_config['agent_id']] = agent_data
        state['last_updated'] = datetime.now().isoformat()

        # Save updated state
        with open(self.shared_state_file, 'w') as f:
            json.dump(state, f, indent=2)

    def _create_tmux_session(self, agent_config: Dict):
        """Crea sessione tmux per agente"""
        session_name = agent_config['session']

        try:
            # Create tmux session
            subprocess.run([
                "/opt/homebrew/bin/tmux", "new-session", "-d", "-s", session_name
            ], check=True)

            # Send welcome message
            welcome_msg = f"echo '{agent_config['name']} Ready! {self.templates[agent_config.get('template', 'custom')].icon}'"
            subprocess.run([
                "/opt/homebrew/bin/tmux", "send-keys", "-t", session_name,
                welcome_msg
            ], check=True)

            # Wait for command to be processed, then send Enter
            import time
            time.sleep(0.1)  # Short delay to let command be processed
            subprocess.run([
                "/opt/homebrew/bin/tmux", "send-keys", "-t", session_name,
                "Enter"
            ], check=True)

            # Send initial commands if specified
            initial_commands = agent_config.get('initial_commands', [])
            if not initial_commands and agent_config.get('template') in self.templates:
                initial_commands = self.templates[agent_config['template']].initial_commands

            for command in initial_commands:
                # Replace placeholders in commands
                command = command.replace('{AGENT_NAME}', agent_config['name'])
                subprocess.run([
                    "/opt/homebrew/bin/tmux", "send-keys", "-t", session_name,
                    command
                ], check=True)

                # Wait for command to be processed, then send Enter
                time.sleep(0.1)  # Short delay to let command be processed
                subprocess.run([
                    "/opt/homebrew/bin/tmux", "send-keys", "-t", session_name,
                    "Enter"
                ], check=True)
                time.sleep(0.5)

        except Exception as e:
            print(f"Warning: Could not create tmux session: {e}")

    def _log_creation(self, agent_config: Dict):
        """Log creazione agente"""
        log_entry = {
            "creation_id": str(uuid.uuid4()),
            "agent_id": agent_config['agent_id'],
            "timestamp": datetime.now().isoformat(),
            "template": agent_config.get('template', 'custom'),
            "success": True,
            "error_message": None
        }

        # Load and update state with creation log
        with open(self.shared_state_file, 'r') as f:
            state = json.load(f)

        if 'creation_history' not in state:
            state['creation_history'] = []

        state['creation_history'].append(log_entry)

        # Keep only last 50 creation records
        state['creation_history'] = state['creation_history'][-50:]

        with open(self.shared_state_file, 'w') as f:
            json.dump(state, f, indent=2)

    def _agent_name_exists(self, name: str) -> bool:
        """Verifica se nome agente esiste già"""
        try:
            with open(self.shared_state_file, 'r') as f:
                state = json.load(f)

            agents = state.get('agents', {})
            return any(agent.get('name') == name for agent in agents.values())
        except:
            return False

    def _agent_id_exists(self, agent_id: str) -> bool:
        """Verifica se ID agente esiste già"""
        try:
            with open(self.shared_state_file, 'r') as f:
                state = json.load(f)

            return agent_id in state.get('agents', {})
        except:
            return False

    def _session_exists(self, session_name: str) -> bool:
        """Verifica se sessione tmux esiste già"""
        try:
            result = subprocess.run([
                "/opt/homebrew/bin/tmux", "list-sessions", "-F", "#{session_name}"
            ], capture_output=True, text=True, timeout=3)
            return session_name in result.stdout
        except:
            return False

    def remove_agent(self, agent_id: str) -> Dict:
        """Rimuove agente dinamico"""
        try:
            # Load state
            with open(self.shared_state_file, 'r') as f:
                state = json.load(f)

            agents = state.get('agents', {})
            if agent_id not in agents:
                return {"success": False, "error": "Agent not found"}

            agent_data = agents[agent_id]

            # Only remove dynamic agents
            if not agent_data.get('is_dynamic', False):
                return {"success": False, "error": "Cannot remove static agent"}

            # Kill tmux session
            session_name = agent_data.get('session_id', '')
            if session_name:
                try:
                    subprocess.run([
                        "/opt/homebrew/bin/tmux", "kill-session", "-t", session_name
                    ], check=True)
                except:
                    pass  # Session might not exist

            # Release port
            port = agent_data.get('port')
            if port:
                self.port_manager.release_port(port)

            # Remove instruction file
            instruction_file = agent_data.get('instruction_file')
            if instruction_file and os.path.exists(instruction_file):
                os.remove(instruction_file)

            # Remove from state
            del agents[agent_id]
            state['last_updated'] = datetime.now().isoformat()

            # Save updated state
            with open(self.shared_state_file, 'w') as f:
                json.dump(state, f, indent=2)

            return {"success": True, "agent_id": agent_id}

        except Exception as e:
            return {"success": False, "error": str(e)}

    def get_dynamic_agents(self) -> Dict:
        """Ottieni solo agenti dinamici"""
        try:
            with open(self.shared_state_file, 'r') as f:
                state = json.load(f)

            agents = state.get('agents', {})
            dynamic_agents = {
                agent_id: agent_data
                for agent_id, agent_data in agents.items()
                if agent_data.get('is_dynamic', False)
            }

            return dynamic_agents
        except:
            return {}


# Factory function for easy access
def create_agent_creator(shared_state_file: str = None) -> AgentCreator:
    """Factory per creare AgentCreator"""
    if shared_state_file is None:
        shared_state_file = str(Path(__file__).parent / "shared_state.json")

    return AgentCreator(shared_state_file)


if __name__ == "__main__":
    # Test creation system
    creator = create_agent_creator()

    # Test configuration
    test_config = {
        "name": "Test Security Agent",
        "description": "A test security agent for demonstration",
        "template": "security-audit",
        "capabilities": ["Vulnerability scanning", "Security analysis"],
        "auto_start": True
    }

    print("Testing agent creation...")
    result = creator.create_agent(test_config)
    print(f"Creation result: {result}")

    if result["success"]:
        print(f"Agent created with ID: {result['agent_id']}")
        print(f"Port: {result['port']}")
        print(f"Session: {result['session']}")