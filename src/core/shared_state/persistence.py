"""
Persistence layer for SharedState system
"""

import json
import sqlite3
import threading
from pathlib import Path
from typing import Optional, Dict, Any
from datetime import datetime

from .models import SharedState


class JSONPersistence:
    """Persiste stato su file JSON"""

    def __init__(self, file_path: str = "shared_state.json"):
        self.file_path = Path(file_path)
        self.lock = threading.Lock()

        # Crea directory se non esiste
        self.file_path.parent.mkdir(parents=True, exist_ok=True)

    def save(self, state: SharedState) -> bool:
        """Salva stato su file JSON"""
        try:
            with self.lock:
                state_dict = state.to_dict()

                # Backup existing file
                if self.file_path.exists():
                    backup_path = self.file_path.with_suffix('.json.backup')
                    self.file_path.replace(backup_path)

                # Save new state
                with open(self.file_path, 'w', encoding='utf-8') as f:
                    json.dump(state_dict, f, indent=2, ensure_ascii=False)

                return True

        except Exception as e:
            print(f"Error saving state to JSON: {e}")
            return False

    def load(self) -> Optional[SharedState]:
        """Carica stato da file JSON"""
        try:
            with self.lock:
                if not self.file_path.exists():
                    return None

                with open(self.file_path, 'r', encoding='utf-8') as f:
                    state_dict = json.load(f)

                return SharedState.from_dict(state_dict)

        except Exception as e:
            print(f"Error loading state from JSON: {e}")

            # Try to load backup
            backup_path = self.file_path.with_suffix('.json.backup')
            if backup_path.exists():
                try:
                    with open(backup_path, 'r', encoding='utf-8') as f:
                        state_dict = json.load(f)
                    return SharedState.from_dict(state_dict)
                except Exception as backup_e:
                    print(f"Error loading backup: {backup_e}")

            return None


class SQLitePersistence:
    """Persiste stato su database SQLite (per future implementazioni avanzate)"""

    def __init__(self, db_path: str = "shared_state.db"):
        self.db_path = Path(db_path)
        self.lock = threading.Lock()
        self._init_database()

    def _init_database(self):
        """Inizializza database e tabelle"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                # Create tables
                conn.executescript('''
                    CREATE TABLE IF NOT EXISTS shared_state (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        state_data TEXT NOT NULL,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    );

                    CREATE TABLE IF NOT EXISTS state_history (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        state_data TEXT NOT NULL,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    );

                    -- Trigger for updating timestamp
                    CREATE TRIGGER IF NOT EXISTS update_shared_state_timestamp
                    AFTER UPDATE ON shared_state
                    FOR EACH ROW
                    BEGIN
                        UPDATE shared_state SET updated_at = CURRENT_TIMESTAMP
                        WHERE id = NEW.id;
                    END;
                ''')
                conn.commit()

        except Exception as e:
            print(f"Error initializing database: {e}")

    def save(self, state: SharedState) -> bool:
        """Salva stato su database SQLite"""
        try:
            with self.lock:
                state_json = json.dumps(state.to_dict(), ensure_ascii=False)

                with sqlite3.connect(self.db_path) as conn:
                    cursor = conn.cursor()

                    # Check if state exists
                    cursor.execute("SELECT id FROM shared_state LIMIT 1")
                    existing = cursor.fetchone()

                    if existing:
                        # Update existing
                        cursor.execute(
                            "UPDATE shared_state SET state_data = ? WHERE id = ?",
                            (state_json, existing[0])
                        )
                    else:
                        # Insert new
                        cursor.execute(
                            "INSERT INTO shared_state (state_data) VALUES (?)",
                            (state_json,)
                        )

                    # Save to history
                    cursor.execute(
                        "INSERT INTO state_history (state_data) VALUES (?)",
                        (state_json,)
                    )

                    conn.commit()
                    return True

        except Exception as e:
            print(f"Error saving state to SQLite: {e}")
            return False

    def load(self) -> Optional[SharedState]:
        """Carica ultimo stato da database SQLite"""
        try:
            with self.lock:
                with sqlite3.connect(self.db_path) as conn:
                    cursor = conn.cursor()

                    cursor.execute(
                        "SELECT state_data FROM shared_state ORDER BY updated_at DESC LIMIT 1"
                    )
                    result = cursor.fetchone()

                    if result:
                        state_dict = json.loads(result[0])
                        return SharedState.from_dict(state_dict)

                    return None

        except Exception as e:
            print(f"Error loading state from SQLite: {e}")
            return None

    def get_history(self, limit: int = 10) -> list:
        """Ottieni storico stati precedenti"""
        try:
            with self.lock:
                with sqlite3.connect(self.db_path) as conn:
                    cursor = conn.cursor()

                    cursor.execute(
                        "SELECT state_data, created_at FROM state_history "
                        "ORDER BY created_at DESC LIMIT ?",
                        (limit,)
                    )

                    results = []
                    for row in cursor.fetchall():
                        state_dict = json.loads(row[0])
                        results.append({
                            'state': SharedState.from_dict(state_dict),
                            'timestamp': row[1]
                        })

                    return results

        except Exception as e:
            print(f"Error getting history from SQLite: {e}")
            return []


class PersistenceManager:
    """Manager per diversi tipi di persistenza"""

    def __init__(self,
                 persistence_type: str = "json",
                 file_path: str = None,
                 db_path: str = None):

        if persistence_type == "json":
            self.persistence = JSONPersistence(
                file_path or "shared_state.json"
            )
        elif persistence_type == "sqlite":
            self.persistence = SQLitePersistence(
                db_path or "shared_state.db"
            )
        else:
            raise ValueError(f"Unknown persistence type: {persistence_type}")

    def save(self, state: SharedState) -> bool:
        """Salva stato"""
        return self.persistence.save(state)

    def load(self) -> Optional[SharedState]:
        """Carica stato"""
        return self.persistence.load()

    def get_history(self, limit: int = 10) -> list:
        """Ottieni storico (se supportato)"""
        if hasattr(self.persistence, 'get_history'):
            return self.persistence.get_history(limit)
        return []