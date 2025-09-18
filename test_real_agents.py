#!/usr/bin/env python3
"""
Test della comunicazione reale MCP -> Agenti
Verifica se gli agenti possono ricevere e processare comandi
"""

import json
import requests
import subprocess
import time
import asyncio

class RealAgentTester:
    def __init__(self):
        self.mcp_server = "http://localhost:8099"
        self.agents = {
            'backend-api': 'claude-backend-api',
            'supervisor': 'claude-supervisor',
            'database': 'claude-database',
            'frontend-ui': 'claude-frontend-ui'
        }

    def send_mcp_command(self, tool, agent, task=None):
        """Invia un comando MCP al server"""
        payload = {
            "jsonrpc": "2.0",
            "method": "tools/call",
            "params": {
                "name": tool,
                "arguments": {
                    "agent": agent,
                    "status": "active",
                    "activity": task or f"Testing {agent}",
                    "category": "task"
                }
            },
            "id": 1
        }

        response = requests.post(
            f"{self.mcp_server}/jsonrpc",
            json=payload,
            headers={"Content-Type": "application/json"}
        )
        return response.json()

    def send_to_tmux_agent(self, agent_session, command):
        """Invia comando diretto all'agente nel terminale tmux - IN DUE FASI"""
        try:
            print(f"      Invio comando a {agent_session}...")

            # FASE 1: Invia il comando (senza Enter)
            subprocess.run([
                'tmux', 'send-keys', '-t', agent_session, command
            ], check=True)

            time.sleep(1)  # Pausa tra comando e Enter

            # FASE 2: Invia Enter per eseguire
            subprocess.run([
                'tmux', 'send-keys', '-t', agent_session, 'Enter'
            ], check=True)

            print(f"      Attendendo elaborazione (40 secondi)...")
            time.sleep(40)  # ASPETTA 40 SECONDI PER L'ELABORAZIONE DELL'AGENTE

            # Cattura l'output
            result = subprocess.run([
                'tmux', 'capture-pane', '-t', agent_session, '-p'
            ], capture_output=True, text=True)

            return result.stdout
        except Exception as e:
            return f"Error: {e}"

    def test_agent_delegation(self):
        """Test delegazione task da Supervisor a Backend"""
        print("=== TEST DELEGAZIONE TASK ===\n")

        # 1. Registra richiesta in MCP
        print("1. Registrando richiesta collaborazione in MCP...")
        mcp_result = requests.post(
            f"{self.mcp_server}/jsonrpc",
            json={
                "jsonrpc": "2.0",
                "method": "tools/call",
                "params": {
                    "name": "request_collaboration",
                    "arguments": {
                        "from_agent": "supervisor",
                        "to_agent": "backend-api",
                        "task": "Implementare endpoint REST per autenticazione",
                        "priority": "high"
                    }
                },
                "id": 100
            },
            headers={"Content-Type": "application/json"}
        )

        result = mcp_result.json()
        if 'result' in result:
            request_id = result['result'].get('request_id')
            print(f"   ✅ Richiesta registrata: ID {request_id}\n")
        else:
            print(f"   ❌ Errore: {result}\n")
            return

        # 2. Notifica al Supervisor via tmux
        print("2. Notificando Supervisor del task...")
        supervisor_cmd = f"Task {request_id}: Delega implementazione auth a backend-api"
        output = self.send_to_tmux_agent('claude-supervisor', supervisor_cmd)
        print(f"   Risposta Supervisor: {output[-200:]}\n")  # Ultimi 200 caratteri

        # 3. Notifica Backend-API
        print("3. Notificando Backend-API del task assegnato...")
        backend_cmd = f"Task {request_id}: Implementare endpoint REST autenticazione (priorità: high)"
        output = self.send_to_tmux_agent('claude-backend-api', backend_cmd)
        print(f"   Risposta Backend: {output[-200:]}\n")

        # 4. Aggiorna stato in MCP
        print("4. Aggiornando stato in MCP...")
        status_result = requests.post(
            f"{self.mcp_server}/jsonrpc",
            json={
                "jsonrpc": "2.0",
                "method": "tools/call",
                "params": {
                    "name": "update_status",
                    "arguments": {
                        "agent": "backend-api",
                        "status": "busy",
                        "current_task": f"Working on task {request_id}"
                    }
                },
                "id": 101
            },
            headers={"Content-Type": "application/json"}
        )

        if 'result' in status_result.json():
            print("   ✅ Stato aggiornato: backend-api -> busy\n")

        return request_id

    def test_real_workflow(self):
        """Test workflow completo"""
        print("\n" + "="*60)
        print("TEST WORKFLOW COMPLETO MCP + AGENTI REALI")
        print("="*60 + "\n")

        # Test delegazione
        request_id = self.test_agent_delegation()

        if request_id:
            print("="*60)
            print("RISULTATO FINALE:")
            print(f"✅ Task {request_id} delegato con successo")
            print("✅ MCP ha registrato la richiesta")
            print("✅ Agenti notificati via tmux")
            print("✅ Stati aggiornati nel sistema")
            print("\n🎯 Il sistema è PARZIALMENTE funzionante:")
            print("   - MCP orchestra correttamente")
            print("   - I terminali tmux ricevono comandi")
            print("   - Manca: AI reale che risponde nei terminali")
            print("   - Manca: Esecuzione automatica dei task")

if __name__ == "__main__":
    tester = RealAgentTester()
    tester.test_real_workflow()