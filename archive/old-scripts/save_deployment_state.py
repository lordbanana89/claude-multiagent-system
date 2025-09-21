#!/usr/bin/env python3
import sqlite3
import json
import shutil
from datetime import datetime
import hashlib
import os

def create_deployment_backup():
    """Create comprehensive backup for deployment"""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    # Create deployment directory
    deploy_dir = f"deployment_{timestamp}"
    os.makedirs(deploy_dir, exist_ok=True)
    
    backups = []
    
    # Backup all databases
    databases = [
        'mcp_system.db',
        'langgraph-test/shared_inbox.db',
        'langgraph-test/dramatiq_queue.db'
    ]
    
    for db_path in databases:
        if os.path.exists(db_path):
            backup_name = os.path.basename(db_path).replace('.db', f'_{timestamp}.db')
            backup_path = os.path.join(deploy_dir, backup_name)
            shutil.copy2(db_path, backup_path)
            
            # Calculate checksum
            with open(backup_path, 'rb') as f:
                checksum = hashlib.sha256(f.read()).hexdigest()
            
            backups.append({
                "original": db_path,
                "backup": backup_path,
                "checksum": checksum,
                "size": os.path.getsize(backup_path)
            })
            
            print(f"✅ Backed up: {db_path} -> {backup_path}")
    
    return deploy_dir, backups

def save_system_state():
    """Save current system state to database"""
    conn = sqlite3.connect('mcp_system.db')
    cursor = conn.cursor()
    
    # Ensure schema_migrations table exists
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS schema_migrations (
            migration_id INTEGER PRIMARY KEY AUTOINCREMENT,
            version TEXT UNIQUE NOT NULL,
            name TEXT NOT NULL,
            applied_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            checksum TEXT,
            execution_time_ms INTEGER,
            rollback_sql TEXT
        )
    """)
    
    # Get current state
    state_data = {
        "timestamp": datetime.now().isoformat(),
        "deployment_phase": "pre-rollout",
        "databases": {},
        "agents": [],
        "active_tasks": []
    }
    
    # Get table counts
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
    tables = cursor.fetchall()
    
    for table in tables:
        table_name = table[0]
        cursor.execute(f"SELECT COUNT(*) FROM {table_name}")
        count = cursor.fetchone()[0]
        state_data["databases"][table_name] = count
    
    # Get agent states
    cursor.execute("SELECT id, status, current_task FROM agents")
    agents = cursor.fetchall()
    for agent in agents:
        state_data["agents"].append({
            "id": agent[0],
            "status": agent[1],
            "task": agent[2]
        })
    
    # Get active tasks
    cursor.execute("SELECT task_id, task_type, status FROM tasks WHERE status != 'completed'")
    tasks = cursor.fetchall()
    for task in tasks:
        state_data["active_tasks"].append({
            "id": task[0],
            "type": task[1],
            "status": task[2]
        })
    
    # Save checkpoint
    cursor.execute("""
        INSERT INTO mcp_checkpoints (checkpoint_name, checkpoint_type, system_state, created_by, description)
        VALUES (?, ?, ?, ?, ?)
    """, (
        f"pre_deployment_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
        'auto',
        json.dumps(state_data),
        'database',
        'Pre-deployment checkpoint for rollout'
    ))
    
    checkpoint_id = cursor.lastrowid
    
    conn.commit()
    conn.close()
    
    return state_data, checkpoint_id

def create_rollout_manifest(deploy_dir, backups, state_data):
    """Create deployment manifest"""
    manifest = {
        "deployment_id": deploy_dir,
        "created_at": datetime.now().isoformat(),
        "created_by": "database",
        "backups": backups,
        "system_state": state_data,
        "rollout_status": "ready",
        "verification": {
            "databases_backed_up": len(backups),
            "total_tables": len(state_data["databases"]),
            "active_agents": len([a for a in state_data["agents"] if a["status"] != 'offline']),
            "pending_tasks": len(state_data["active_tasks"])
        }
    }
    
    manifest_path = os.path.join(deploy_dir, "manifest.json")
    with open(manifest_path, 'w') as f:
        json.dump(manifest, f, indent=2)
    
    print(f"📋 Manifest created: {manifest_path}")
    return manifest

def main():
    print("🚀 DEPLOYMENT PREPARATION - DATABASE AGENT")
    print("=" * 50)
    
    # Step 1: Create backups
    print("\n📦 Creating deployment backups...")
    deploy_dir, backups = create_deployment_backup()
    
    # Step 2: Save system state
    print("\n💾 Saving system state...")
    state_data, checkpoint_id = save_system_state()
    print(f"✅ Checkpoint created: ID {checkpoint_id}")
    
    # Step 3: Create manifest
    print("\n📝 Creating deployment manifest...")
    manifest = create_rollout_manifest(deploy_dir, backups, state_data)
    
    # Step 4: Summary
    print("\n" + "=" * 50)
    print("✅ DEPLOYMENT PREPARATION COMPLETE")
    print(f"📁 Deployment directory: {deploy_dir}")
    print(f"💾 Databases backed up: {len(backups)}")
    print(f"📊 Total tables: {len(state_data['databases'])}")
    print(f"👥 Active agents: {len([a for a in state_data['agents'] if a['status'] != 'offline'])}")
    print(f"📋 Pending tasks: {len(state_data['active_tasks'])}")
    print("\n🟢 Database ready for deployment rollout")

if __name__ == "__main__":
    main()
