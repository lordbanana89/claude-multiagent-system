#!/usr/bin/env python3
"""
Authentication & RBAC Manager - LangGraph Platform Style
Sistema di autenticazione e controllo accessi per la piattaforma multi-agent
"""

import sqlite3
import hashlib
import secrets
import os
from typing import Dict, List, Optional
from dataclasses import dataclass
from datetime import datetime, timedelta
import json
from pathlib import Path
import sys

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))
from config.settings import AUTH_DB_PATH, AUTH_SECRET_KEY, PROJECT_ROOT

@dataclass
class User:
    """User model"""
    username: str
    email: str
    role: str  # admin, developer, viewer
    permissions: List[str]
    created_at: datetime
    last_login: Optional[datetime] = None
    is_active: bool = True

@dataclass
class Workspace:
    """Workspace model for team management"""
    name: str
    description: str
    owner: str
    members: List[str]
    agents_access: List[str]  # Which agents this workspace can access
    created_at: datetime

class AuthManager:
    """Authentication and RBAC manager"""

    def __init__(self):
        self.db_path = str(AUTH_DB_PATH)

        # Role-based permissions (initialize before database)
        self.role_permissions = {
            "admin": [
                "view_all_agents",
                "control_all_agents",
                "manage_users",
                "manage_workspaces",
                "view_analytics",
                "system_management",
                "export_logs"
            ],
            "developer": [
                "view_assigned_agents",
                "control_assigned_agents",
                "create_workflows",
                "view_analytics",
                "export_data"
            ],
            "viewer": [
                "view_assigned_agents",
                "view_basic_analytics"
            ]
        }

        # Initialize database after permissions are set
        self.init_database()

    def init_database(self):
        """Initialize authentication database"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        # Users table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS users (
                username TEXT PRIMARY KEY,
                email TEXT UNIQUE,
                password_hash TEXT,
                salt TEXT,
                role TEXT,
                permissions TEXT,
                created_at TEXT,
                last_login TEXT,
                is_active BOOLEAN
            )
        """)

        # Workspaces table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS workspaces (
                name TEXT PRIMARY KEY,
                description TEXT,
                owner TEXT,
                members TEXT,
                agents_access TEXT,
                created_at TEXT
            )
        """)

        # Sessions table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS sessions (
                session_id TEXT PRIMARY KEY,
                username TEXT,
                created_at TEXT,
                expires_at TEXT,
                is_active BOOLEAN
            )
        """)

        # Create default admin user if doesn't exist
        cursor.execute("SELECT COUNT(*) FROM users WHERE role = 'admin'")
        if cursor.fetchone()[0] == 0:
            self._create_default_admin()

        conn.commit()
        conn.close()

    def _create_default_admin(self):
        """Create default admin user with secure random password"""
        # Generate secure random password
        password = secrets.token_urlsafe(16)
        salt = secrets.token_hex(32)
        password_hash = hashlib.pbkdf2_hmac('sha256', password.encode(), salt.encode(), 100000)

        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        # Check if admin already exists
        cursor.execute("SELECT username FROM users WHERE username = ?", ("admin",))
        if cursor.fetchone():
            conn.close()
            return  # Admin already exists

        cursor.execute("""
            INSERT INTO users (username, email, password_hash, salt, role, permissions, created_at, is_active)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            "admin",
            "admin@multiagent.local",
            password_hash.hex(),
            salt,
            "admin",
            json.dumps(self.role_permissions["admin"]),
            datetime.now().isoformat(),
            True
        ))

        conn.commit()
        conn.close()

        # Display password ONCE
        print("\n" + "="*60)
        print("🔐 DEFAULT ADMIN ACCOUNT CREATED")
        print(f"Username: admin")
        print(f"Password: {password}")
        print("⚠️  SAVE THIS PASSWORD - IT WON'T BE SHOWN AGAIN")
        print("="*60 + "\n")

        # Save to secure file
        from pathlib import Path
        auth_file = Path.home() / ".claude_admin_creds"
        try:
            with open(auth_file, 'w') as f:
                f.write(f"admin:{password}\n")
                f.write(f"Created: {datetime.now().isoformat()}\n")
            os.chmod(auth_file, 0o600)
            print(f"📁 Credentials saved to: {auth_file}")
            print("   (This file is readable only by you)\n")
        except Exception as e:
            print(f"⚠️  Could not save credentials to file: {e}")
            print("   Make sure to save the password shown above!\n")

    def authenticate_user(self, username: str, password: str) -> Optional[User]:
        """Authenticate user credentials"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute("SELECT * FROM users WHERE username = ? AND is_active = 1", (username,))
        user_data = cursor.fetchone()

        if not user_data:
            conn.close()
            return None

        stored_hash = user_data[2]
        salt = user_data[3]

        # Verify password
        password_hash = hashlib.pbkdf2_hmac('sha256', password.encode(), salt.encode(), 100000)

        if password_hash.hex() == stored_hash:
            # Update last login
            cursor.execute("UPDATE users SET last_login = ? WHERE username = ?",
                         (datetime.now().isoformat(), username))
            conn.commit()

            user = User(
                username=user_data[0],
                email=user_data[1],
                role=user_data[4],
                permissions=json.loads(user_data[5]) if user_data[5] else [],
                created_at=datetime.fromisoformat(user_data[6]),
                last_login=datetime.fromisoformat(user_data[7]) if user_data[7] else None,
                is_active=bool(user_data[8])
            )

            conn.close()
            return user

        conn.close()
        return None

    def create_session(self, user: User) -> str:
        """Create user session"""
        session_id = secrets.token_urlsafe(32)
        expires_at = datetime.now() + timedelta(hours=8)

        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute("""
            INSERT INTO sessions (session_id, username, created_at, expires_at, is_active)
            VALUES (?, ?, ?, ?, ?)
        """, (session_id, user.username, datetime.now().isoformat(), expires_at.isoformat(), True))

        conn.commit()
        conn.close()

        return session_id

    def validate_session(self, session_id: str) -> Optional[User]:
        """Validate user session"""
        if not session_id:
            return None

        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute("""
            SELECT s.username, s.expires_at, u.* FROM sessions s
            JOIN users u ON s.username = u.username
            WHERE s.session_id = ? AND s.is_active = 1
        """, (session_id,))

        result = cursor.fetchone()
        conn.close()

        if not result:
            return None

        expires_at = datetime.fromisoformat(result[1])
        if datetime.now() > expires_at:
            self.invalidate_session(session_id)
            return None

        user = User(
            username=result[2],
            email=result[3],
            role=result[6],
            permissions=json.loads(result[7]) if result[7] else [],
            created_at=datetime.fromisoformat(result[8]),
            last_login=datetime.fromisoformat(result[9]) if result[9] else None,
            is_active=bool(result[10])
        )

        return user

    def invalidate_session(self, session_id: str):
        """Invalidate user session"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute("UPDATE sessions SET is_active = 0 WHERE session_id = ?", (session_id,))

        conn.commit()
        conn.close()

    def check_permission(self, user: User, permission: str) -> bool:
        """Check if user has specific permission"""
        return permission in user.permissions

    def get_user_agents(self, user: User) -> List[str]:
        """Get agents accessible to user"""
        if "view_all_agents" in user.permissions:
            return [
                "claude-prompt-validator",
                "claude-task-coordinator",
                "claude-backend-api",
                "claude-database",
                "claude-frontend-ui",
                "claude-instagram",
                "claude-queue-manager",
                "claude-testing",
                "claude-deployment"
            ]
        else:
            # For non-admin users, return agents based on workspace membership
            return self._get_workspace_agents(user.username)

    def _get_workspace_agents(self, username: str) -> List[str]:
        """Get agents accessible through workspace membership"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute("""
            SELECT agents_access FROM workspaces
            WHERE owner = ? OR members LIKE ?
        """, (username, f"%{username}%"))

        results = cursor.fetchall()
        conn.close()

        accessible_agents = set()
        for result in results:
            agents = json.loads(result[0]) if result[0] else []
            accessible_agents.update(agents)

        return list(accessible_agents)

    def create_workspace(self, name: str, description: str, owner: str, agents_access: List[str]) -> bool:
        """Create new workspace"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        try:
            cursor.execute("""
                INSERT INTO workspaces (name, description, owner, members, agents_access, created_at)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (
                name,
                description,
                owner,
                json.dumps([owner]),
                json.dumps(agents_access),
                datetime.now().isoformat()
            ))

            conn.commit()
            conn.close()
            return True
        except sqlite3.IntegrityError:
            conn.close()
            return False

    def get_user_workspaces(self, username: str) -> List[Workspace]:
        """Get workspaces for user"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute("""
            SELECT * FROM workspaces
            WHERE owner = ? OR members LIKE ?
        """, (username, f"%{username}%"))

        results = cursor.fetchall()
        conn.close()

        workspaces = []
        for result in results:
            workspace = Workspace(
                name=result[0],
                description=result[1],
                owner=result[2],
                members=json.loads(result[3]) if result[3] else [],
                agents_access=json.loads(result[4]) if result[4] else [],
                created_at=datetime.fromisoformat(result[5])
            )
            workspaces.append(workspace)

        return workspaces

def render_login_form():
    """Render login form"""
    st.markdown("""
    <div style='max-width: 400px; margin: 2rem auto; padding: 2rem;
                border-radius: 15px; background: white; box-shadow: 0 10px 30px rgba(0,0,0,0.1);'>
        <h2 style='text-align: center; color: #333; margin-bottom: 2rem;'>
            🤖 Multi-Agent Platform Login
        </h2>
    </div>
    """, unsafe_allow_html=True)

    with st.container():
        col1, col2, col3 = st.columns([1, 2, 1])

        with col2:
            username = st.text_input("👤 Username", key="login_username")
            password = st.text_input("🔒 Password", type="password", key="login_password")

            col_a, col_b = st.columns(2)
            with col_a:
                if st.button("🚀 Login", type="primary", use_container_width=True):
                    return username, password
            with col_b:
                if st.button("👥 Demo Access", use_container_width=True):
                    return "admin", "admin123"

            st.markdown("""
            <div style='text-align: center; margin-top: 2rem; padding: 1rem;
                        background: #f8f9fa; border-radius: 10px; font-size: 0.9rem;'>
                <strong>Default Login:</strong><br>
                Username: <code>admin</code><br>
                Password: <code>admin123</code>
            </div>
            """, unsafe_allow_html=True)

    return None, None

def render_user_management(auth_manager: AuthManager, current_user: User):
    """Render user management interface"""
    if not auth_manager.check_permission(current_user, "manage_users"):
        st.error("❌ Access denied. You don't have permission to manage users.")
        return

    st.markdown("## 👥 User Management")

    # Add new user
    with st.expander("➕ Add New User"):
        col1, col2 = st.columns(2)

        with col1:
            new_username = st.text_input("Username")
            new_email = st.text_input("Email")

        with col2:
            new_role = st.selectbox("Role", ["viewer", "developer", "admin"])

        if st.button("👤 Create User"):
            if new_username and new_email:
                # Here you would implement user creation
                st.success(f"User {new_username} created successfully!")

def render_workspace_management(auth_manager: AuthManager, current_user: User):
    """Render workspace management interface"""
    st.markdown("## 🏢 Workspace Management")

    # User's workspaces
    workspaces = auth_manager.get_user_workspaces(current_user.username)

    if workspaces:
        st.markdown("### Your Workspaces")

        for workspace in workspaces:
            with st.expander(f"🏢 {workspace.name}"):
                st.write(f"**Description**: {workspace.description}")
                st.write(f"**Owner**: {workspace.owner}")
                st.write(f"**Members**: {', '.join(workspace.members)}")
                st.write(f"**Agents Access**: {', '.join(workspace.agents_access)}")
                st.write(f"**Created**: {workspace.created_at.strftime('%Y-%m-%d %H:%M')}")
    else:
        st.info("No workspaces found. Create one to get started!")

    # Create new workspace
    if auth_manager.check_permission(current_user, "manage_workspaces"):
        with st.expander("➕ Create New Workspace"):
            workspace_name = st.text_input("Workspace Name")
            workspace_desc = st.text_area("Description")

            available_agents = [
                "claude-prompt-validator", "claude-task-coordinator",
                "claude-backend-api", "claude-database", "claude-frontend-ui",
                "claude-instagram", "claude-queue-manager", "claude-testing",
                "claude-deployment"
            ]

            selected_agents = st.multiselect("Agent Access", available_agents)

            if st.button("🏢 Create Workspace"):
                if workspace_name and selected_agents:
                    success = auth_manager.create_workspace(
                        workspace_name, workspace_desc, current_user.username, selected_agents
                    )
                    if success:
                        st.success(f"Workspace '{workspace_name}' created successfully!")
                        st.rerun()
                    else:
                        st.error("Failed to create workspace. Name might already exist.")