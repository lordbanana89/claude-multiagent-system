"""
Intelligent Agent with Real Capabilities and Learning
"""

import os
import json
import time
import subprocess
import requests
import sqlite3
import hashlib
import re
from typing import Dict, List, Any, Optional, Callable
from dataclasses import dataclass, field
from enum import Enum
import logging
import numpy as np
from collections import defaultdict
import pickle

logger = logging.getLogger(__name__)


class SkillType(Enum):
    """Types of agent skills"""
    DATA_PROCESSING = "data_processing"
    API_INTEGRATION = "api_integration"
    DATABASE_OPERATION = "database_operation"
    FILE_MANAGEMENT = "file_management"
    COMPUTATION = "computation"
    COMMUNICATION = "communication"
    MONITORING = "monitoring"
    SECURITY = "security"


@dataclass
class SkillResult:
    """Result from skill execution"""
    success: bool
    output: Any
    error: Optional[str] = None
    execution_time: float = 0
    metadata: Dict = field(default_factory=dict)


class AgentSkill:
    """Base class for agent skills"""

    def __init__(self, name: str, description: str, skill_type: SkillType):
        self.name = name
        self.description = description
        self.skill_type = skill_type
        self.execution_count = 0
        self.success_count = 0
        self.avg_execution_time = 0
        self.last_error = None

    def execute(self, params: Dict[str, Any]) -> SkillResult:
        """Execute the skill"""
        start_time = time.time()
        try:
            result = self._perform(params)
            execution_time = time.time() - start_time

            # Update metrics
            self.execution_count += 1
            if result.success:
                self.success_count += 1
            self.avg_execution_time = (
                (self.avg_execution_time * (self.execution_count - 1) + execution_time) /
                self.execution_count
            )

            result.execution_time = execution_time
            return result

        except Exception as e:
            self.last_error = str(e)
            return SkillResult(
                success=False,
                output=None,
                error=str(e),
                execution_time=time.time() - start_time
            )

    def _perform(self, params: Dict[str, Any]) -> SkillResult:
        """Override in subclasses"""
        raise NotImplementedError

    def get_success_rate(self) -> float:
        """Get skill success rate"""
        if self.execution_count == 0:
            return 0
        return self.success_count / self.execution_count


# Concrete Skill Implementations

class DataProcessingSkill(AgentSkill):
    """Process and transform data"""

    def __init__(self):
        super().__init__(
            "data_processing",
            "Process and transform data in various formats",
            SkillType.DATA_PROCESSING
        )

    def _perform(self, params: Dict[str, Any]) -> SkillResult:
        operation = params.get("operation", "transform")
        data = params.get("data", [])

        if operation == "aggregate":
            result = self._aggregate(data, params.get("method", "sum"))
        elif operation == "filter":
            result = self._filter(data, params.get("condition", {}))
        elif operation == "transform":
            result = self._transform(data, params.get("transformation", {}))
        elif operation == "sort":
            result = self._sort(data, params.get("key", None), params.get("reverse", False))
        else:
            return SkillResult(False, None, f"Unknown operation: {operation}")

        return SkillResult(True, result)

    def _aggregate(self, data: List, method: str) -> Any:
        if method == "sum":
            return sum(data) if all(isinstance(x, (int, float)) for x in data) else None
        elif method == "mean":
            return np.mean(data) if data else None
        elif method == "count":
            return len(data)
        elif method == "unique":
            return list(set(data))
        return None

    def _filter(self, data: List, condition: Dict) -> List:
        field = condition.get("field")
        operator = condition.get("operator", "==")
        value = condition.get("value")

        if not field:
            return data

        filtered = []
        for item in data:
            if isinstance(item, dict):
                item_value = item.get(field)
                if self._check_condition(item_value, operator, value):
                    filtered.append(item)
            elif operator == "==" and item == value:
                filtered.append(item)

        return filtered

    def _check_condition(self, item_value, operator: str, value) -> bool:
        if operator == "==":
            return item_value == value
        elif operator == "!=":
            return item_value != value
        elif operator == ">":
            return item_value > value
        elif operator == "<":
            return item_value < value
        elif operator == ">=":
            return item_value >= value
        elif operator == "<=":
            return item_value <= value
        elif operator == "contains":
            return value in str(item_value)
        return False

    def _transform(self, data: List, transformation: Dict) -> List:
        transform_type = transformation.get("type", "map")

        if transform_type == "map":
            func_str = transformation.get("function", "x")
            try:
                # Safe evaluation with limited scope
                return [eval(func_str, {"__builtins__": {}}, {"x": item}) for item in data]
            except:
                return data

        elif transform_type == "flatten":
            flat = []
            for item in data:
                if isinstance(item, list):
                    flat.extend(item)
                else:
                    flat.append(item)
            return flat

        return data

    def _sort(self, data: List, key: Optional[str], reverse: bool) -> List:
        if key and all(isinstance(item, dict) for item in data):
            return sorted(data, key=lambda x: x.get(key, 0), reverse=reverse)
        return sorted(data, reverse=reverse)


class APIIntegrationSkill(AgentSkill):
    """Integrate with external APIs"""

    def __init__(self):
        super().__init__(
            "api_integration",
            "Make HTTP requests to external APIs",
            SkillType.API_INTEGRATION
        )

    def _perform(self, params: Dict[str, Any]) -> SkillResult:
        method = params.get("method", "GET").upper()
        url = params.get("url")
        headers = params.get("headers", {})
        data = params.get("data", {})
        timeout = params.get("timeout", 30)

        if not url:
            return SkillResult(False, None, "URL is required")

        try:
            response = requests.request(
                method=method,
                url=url,
                headers=headers,
                json=data if method in ["POST", "PUT", "PATCH"] else None,
                params=data if method == "GET" else None,
                timeout=timeout
            )

            result = {
                "status_code": response.status_code,
                "headers": dict(response.headers),
                "body": response.json() if response.headers.get("content-type", "").startswith("application/json") else response.text
            }

            return SkillResult(
                success=response.status_code < 400,
                output=result
            )

        except requests.exceptions.RequestException as e:
            return SkillResult(False, None, str(e))


class DatabaseSkill(AgentSkill):
    """Database operations"""

    def __init__(self, db_path: str = "data/agent_data.db"):
        super().__init__(
            "database",
            "Execute database operations",
            SkillType.DATABASE_OPERATION
        )
        self.db_path = db_path

    def _perform(self, params: Dict[str, Any]) -> SkillResult:
        operation = params.get("operation")

        if operation == "query":
            return self._query(params.get("sql"), params.get("params", []))
        elif operation == "insert":
            return self._insert(params.get("table"), params.get("data"))
        elif operation == "update":
            return self._update(params.get("table"), params.get("data"), params.get("condition"))
        elif operation == "delete":
            return self._delete(params.get("table"), params.get("condition"))
        elif operation == "create_table":
            return self._create_table(params.get("table"), params.get("schema"))
        else:
            return SkillResult(False, None, f"Unknown operation: {operation}")

    def _query(self, sql: str, params: List) -> SkillResult:
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                cursor.execute(sql, params)
                rows = cursor.fetchall()
                return SkillResult(True, [dict(row) for row in rows])
        except Exception as e:
            return SkillResult(False, None, str(e))

    def _insert(self, table: str, data: Dict) -> SkillResult:
        try:
            with sqlite3.connect(self.db_path) as conn:
                columns = ", ".join(data.keys())
                placeholders = ", ".join(["?" for _ in data])
                sql = f"INSERT INTO {table} ({columns}) VALUES ({placeholders})"
                conn.execute(sql, list(data.values()))
                conn.commit()
                return SkillResult(True, {"inserted": conn.total_changes})
        except Exception as e:
            return SkillResult(False, None, str(e))

    def _update(self, table: str, data: Dict, condition: Dict) -> SkillResult:
        try:
            with sqlite3.connect(self.db_path) as conn:
                set_clause = ", ".join([f"{k} = ?" for k in data.keys()])
                where_clause = " AND ".join([f"{k} = ?" for k in condition.keys()])
                sql = f"UPDATE {table} SET {set_clause} WHERE {where_clause}"
                conn.execute(sql, list(data.values()) + list(condition.values()))
                conn.commit()
                return SkillResult(True, {"updated": conn.total_changes})
        except Exception as e:
            return SkillResult(False, None, str(e))

    def _delete(self, table: str, condition: Dict) -> SkillResult:
        try:
            with sqlite3.connect(self.db_path) as conn:
                where_clause = " AND ".join([f"{k} = ?" for k in condition.keys()])
                sql = f"DELETE FROM {table} WHERE {where_clause}"
                conn.execute(sql, list(condition.values()))
                conn.commit()
                return SkillResult(True, {"deleted": conn.total_changes})
        except Exception as e:
            return SkillResult(False, None, str(e))

    def _create_table(self, table: str, schema: Dict) -> SkillResult:
        try:
            with sqlite3.connect(self.db_path) as conn:
                columns = []
                for col_name, col_type in schema.items():
                    columns.append(f"{col_name} {col_type}")
                sql = f"CREATE TABLE IF NOT EXISTS {table} ({', '.join(columns)})"
                conn.execute(sql)
                conn.commit()
                return SkillResult(True, {"created": table})
        except Exception as e:
            return SkillResult(False, None, str(e))


class FileManagementSkill(AgentSkill):
    """File system operations"""

    def __init__(self, base_path: str = "/tmp/agent_workspace"):
        super().__init__(
            "file_management",
            "Manage files and directories",
            SkillType.FILE_MANAGEMENT
        )
        self.base_path = base_path
        os.makedirs(base_path, exist_ok=True)

    def _perform(self, params: Dict[str, Any]) -> SkillResult:
        operation = params.get("operation")

        if operation == "read":
            return self._read_file(params.get("path"))
        elif operation == "write":
            return self._write_file(params.get("path"), params.get("content"))
        elif operation == "list":
            return self._list_directory(params.get("path", "."))
        elif operation == "delete":
            return self._delete(params.get("path"))
        elif operation == "copy":
            return self._copy(params.get("source"), params.get("destination"))
        elif operation == "move":
            return self._move(params.get("source"), params.get("destination"))
        else:
            return SkillResult(False, None, f"Unknown operation: {operation}")

    def _safe_path(self, path: str) -> str:
        """Ensure path is within base directory"""
        full_path = os.path.join(self.base_path, path.lstrip("/"))
        # Prevent directory traversal
        if not full_path.startswith(self.base_path):
            raise ValueError("Invalid path")
        return full_path

    def _read_file(self, path: str) -> SkillResult:
        try:
            safe_path = self._safe_path(path)
            with open(safe_path, "r") as f:
                content = f.read()
            return SkillResult(True, content)
        except Exception as e:
            return SkillResult(False, None, str(e))

    def _write_file(self, path: str, content: str) -> SkillResult:
        try:
            safe_path = self._safe_path(path)
            os.makedirs(os.path.dirname(safe_path), exist_ok=True)
            with open(safe_path, "w") as f:
                f.write(content)
            return SkillResult(True, {"path": path, "size": len(content)})
        except Exception as e:
            return SkillResult(False, None, str(e))

    def _list_directory(self, path: str) -> SkillResult:
        try:
            safe_path = self._safe_path(path)
            items = []
            for item in os.listdir(safe_path):
                item_path = os.path.join(safe_path, item)
                items.append({
                    "name": item,
                    "type": "directory" if os.path.isdir(item_path) else "file",
                    "size": os.path.getsize(item_path) if os.path.isfile(item_path) else 0
                })
            return SkillResult(True, items)
        except Exception as e:
            return SkillResult(False, None, str(e))

    def _delete(self, path: str) -> SkillResult:
        try:
            safe_path = self._safe_path(path)
            if os.path.isfile(safe_path):
                os.remove(safe_path)
            elif os.path.isdir(safe_path):
                import shutil
                shutil.rmtree(safe_path)
            return SkillResult(True, {"deleted": path})
        except Exception as e:
            return SkillResult(False, None, str(e))

    def _copy(self, source: str, destination: str) -> SkillResult:
        try:
            import shutil
            safe_source = self._safe_path(source)
            safe_dest = self._safe_path(destination)
            shutil.copy2(safe_source, safe_dest)
            return SkillResult(True, {"copied": source, "to": destination})
        except Exception as e:
            return SkillResult(False, None, str(e))

    def _move(self, source: str, destination: str) -> SkillResult:
        try:
            import shutil
            safe_source = self._safe_path(source)
            safe_dest = self._safe_path(destination)
            shutil.move(safe_source, safe_dest)
            return SkillResult(True, {"moved": source, "to": destination})
        except Exception as e:
            return SkillResult(False, None, str(e))


class ComputationSkill(AgentSkill):
    """Complex computations and algorithms"""

    def __init__(self):
        super().__init__(
            "computation",
            "Perform complex calculations and algorithms",
            SkillType.COMPUTATION
        )

    def _perform(self, params: Dict[str, Any]) -> SkillResult:
        operation = params.get("operation")

        if operation == "statistics":
            return self._statistics(params.get("data", []))
        elif operation == "linear_regression":
            return self._linear_regression(params.get("x", []), params.get("y", []))
        elif operation == "clustering":
            return self._clustering(params.get("data", []), params.get("n_clusters", 3))
        elif operation == "hash":
            return self._hash(params.get("data", ""), params.get("algorithm", "sha256"))
        elif operation == "encrypt":
            return self._encrypt(params.get("data", ""), params.get("key", ""))
        else:
            return SkillResult(False, None, f"Unknown operation: {operation}")

    def _statistics(self, data: List[float]) -> SkillResult:
        if not data:
            return SkillResult(False, None, "No data provided")

        try:
            import numpy as np
            from scipy import stats

            result = {
                "mean": np.mean(data),
                "median": np.median(data),
                "std": np.std(data),
                "var": np.var(data),
                "min": np.min(data),
                "max": np.max(data),
                "q1": np.percentile(data, 25),
                "q3": np.percentile(data, 75),
                "skewness": stats.skew(data),
                "kurtosis": stats.kurtosis(data)
            }
            return SkillResult(True, result)
        except Exception as e:
            return SkillResult(False, None, str(e))

    def _linear_regression(self, x: List[float], y: List[float]) -> SkillResult:
        if len(x) != len(y) or len(x) < 2:
            return SkillResult(False, None, "Invalid data for regression")

        try:
            import numpy as np
            from sklearn.linear_model import LinearRegression

            X = np.array(x).reshape(-1, 1)
            y = np.array(y)

            model = LinearRegression()
            model.fit(X, y)

            result = {
                "coefficient": float(model.coef_[0]),
                "intercept": float(model.intercept_),
                "r_squared": float(model.score(X, y)),
                "predictions": model.predict(X).tolist()
            }
            return SkillResult(True, result)
        except Exception as e:
            return SkillResult(False, None, str(e))

    def _clustering(self, data: List[List[float]], n_clusters: int) -> SkillResult:
        if not data or n_clusters < 1:
            return SkillResult(False, None, "Invalid data for clustering")

        try:
            import numpy as np
            from sklearn.cluster import KMeans

            X = np.array(data)
            kmeans = KMeans(n_clusters=n_clusters, random_state=42)
            labels = kmeans.fit_predict(X)

            result = {
                "labels": labels.tolist(),
                "centers": kmeans.cluster_centers_.tolist(),
                "inertia": float(kmeans.inertia_)
            }
            return SkillResult(True, result)
        except Exception as e:
            return SkillResult(False, None, str(e))

    def _hash(self, data: str, algorithm: str) -> SkillResult:
        try:
            if algorithm == "md5":
                h = hashlib.md5(data.encode()).hexdigest()
            elif algorithm == "sha1":
                h = hashlib.sha1(data.encode()).hexdigest()
            elif algorithm == "sha256":
                h = hashlib.sha256(data.encode()).hexdigest()
            elif algorithm == "sha512":
                h = hashlib.sha512(data.encode()).hexdigest()
            else:
                return SkillResult(False, None, f"Unknown algorithm: {algorithm}")

            return SkillResult(True, {"algorithm": algorithm, "hash": h})
        except Exception as e:
            return SkillResult(False, None, str(e))

    def _encrypt(self, data: str, key: str) -> SkillResult:
        # Simple XOR encryption for demonstration
        if not key:
            return SkillResult(False, None, "Encryption key required")

        try:
            encrypted = []
            for i, char in enumerate(data):
                key_char = key[i % len(key)]
                encrypted.append(chr(ord(char) ^ ord(key_char)))

            return SkillResult(True, {
                "encrypted": "".join(encrypted),
                "algorithm": "xor"
            })
        except Exception as e:
            return SkillResult(False, None, str(e))


class IntelligentAgent:
    """
    Intelligent agent with real capabilities and learning
    """

    def __init__(self, agent_id: str, role: str):
        self.agent_id = agent_id
        self.role = role
        self.skills: Dict[str, AgentSkill] = {}
        self.knowledge_base: Dict[str, Any] = {}
        self.experience: List[Dict] = []
        self.performance_metrics = defaultdict(float)

        # Initialize skills based on role
        self._initialize_skills()

        # Learning parameters
        self.learning_rate = 0.1
        self.exploration_rate = 0.2

        logger.info(f"IntelligentAgent {agent_id} initialized with role {role}")

    def _initialize_skills(self):
        """Initialize agent skills based on role"""
        if self.role == "backend-api":
            self.skills["api"] = APIIntegrationSkill()
            self.skills["data"] = DataProcessingSkill()
            self.skills["computation"] = ComputationSkill()

        elif self.role == "database":
            self.skills["database"] = DatabaseSkill()
            self.skills["data"] = DataProcessingSkill()

        elif self.role == "frontend-ui":
            self.skills["file"] = FileManagementSkill()
            self.skills["data"] = DataProcessingSkill()

        elif self.role == "testing":
            self.skills["api"] = APIIntegrationSkill()
            self.skills["computation"] = ComputationSkill()

        else:  # supervisor, master, etc.
            # Supervisors get all skills
            self.skills["api"] = APIIntegrationSkill()
            self.skills["database"] = DatabaseSkill()
            self.skills["file"] = FileManagementSkill()
            self.skills["data"] = DataProcessingSkill()
            self.skills["computation"] = ComputationSkill()

    def process_task(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """Process a task using appropriate skills"""
        task_type = task.get("type", "generic")
        params = task.get("params", {})

        # Determine which skill to use
        skill = self._select_skill(task_type, params)

        if not skill:
            return {
                "success": False,
                "error": f"No skill available for task type: {task_type}"
            }

        # Execute skill
        result = skill.execute(params)

        # Learn from experience
        self._update_knowledge(task, result)

        # Update performance metrics
        self._update_metrics(skill, result)

        return {
            "success": result.success,
            "output": result.output,
            "error": result.error,
            "execution_time": result.execution_time,
            "skill_used": skill.name,
            "agent": self.agent_id
        }

    def _select_skill(self, task_type: str, params: Dict) -> Optional[AgentSkill]:
        """Select appropriate skill for task"""
        # Map task types to skills
        skill_map = {
            "api_call": "api",
            "data_processing": "data",
            "database_query": "database",
            "file_operation": "file",
            "computation": "computation"
        }

        skill_name = skill_map.get(task_type)
        if skill_name and skill_name in self.skills:
            return self.skills[skill_name]

        # Try to infer from parameters
        if "url" in params:
            return self.skills.get("api")
        elif "sql" in params or "table" in params:
            return self.skills.get("database")
        elif "path" in params:
            return self.skills.get("file")
        elif "data" in params:
            return self.skills.get("data")

        # Use computation as fallback
        return self.skills.get("computation")

    def _update_knowledge(self, task: Dict, result: SkillResult):
        """Update knowledge base from experience"""
        experience_entry = {
            "timestamp": time.time(),
            "task": task,
            "result": {
                "success": result.success,
                "execution_time": result.execution_time,
                "error": result.error
            }
        }
        self.experience.append(experience_entry)

        # Keep only recent experience
        if len(self.experience) > 1000:
            self.experience = self.experience[-1000:]

        # Update knowledge patterns
        task_pattern = f"{task.get('type')}_{result.success}"
        self.knowledge_base[task_pattern] = self.knowledge_base.get(task_pattern, 0) + 1

    def _update_metrics(self, skill: AgentSkill, result: SkillResult):
        """Update performance metrics"""
        self.performance_metrics["total_tasks"] += 1
        if result.success:
            self.performance_metrics["successful_tasks"] += 1

        self.performance_metrics["avg_execution_time"] = (
            (self.performance_metrics["avg_execution_time"] *
             (self.performance_metrics["total_tasks"] - 1) +
             result.execution_time) /
            self.performance_metrics["total_tasks"]
        )

        # Skill-specific metrics
        skill_key = f"skill_{skill.name}_success_rate"
        self.performance_metrics[skill_key] = skill.get_success_rate()

    def get_capabilities(self) -> Dict[str, List[str]]:
        """Get agent capabilities"""
        capabilities = {}
        for skill_name, skill in self.skills.items():
            capabilities[skill_name] = {
                "description": skill.description,
                "type": skill.skill_type.value,
                "success_rate": skill.get_success_rate(),
                "avg_time": skill.avg_execution_time
            }
        return capabilities

    def get_performance_report(self) -> Dict:
        """Get performance report"""
        return {
            "agent_id": self.agent_id,
            "role": self.role,
            "metrics": dict(self.performance_metrics),
            "skills": {
                name: {
                    "executions": skill.execution_count,
                    "success_rate": skill.get_success_rate(),
                    "avg_time": skill.avg_execution_time
                }
                for name, skill in self.skills.items()
            },
            "knowledge_patterns": self.knowledge_base,
            "experience_count": len(self.experience)
        }

    def save_state(self, path: str):
        """Save agent state to file"""
        state = {
            "agent_id": self.agent_id,
            "role": self.role,
            "knowledge_base": self.knowledge_base,
            "experience": self.experience[-100:],  # Save last 100 experiences
            "performance_metrics": dict(self.performance_metrics)
        }

        with open(path, "wb") as f:
            pickle.dump(state, f)

    def load_state(self, path: str):
        """Load agent state from file"""
        if os.path.exists(path):
            with open(path, "rb") as f:
                state = pickle.load(f)
                self.knowledge_base = state.get("knowledge_base", {})
                self.experience = state.get("experience", [])
                self.performance_metrics = defaultdict(float, state.get("performance_metrics", {}))


# Example usage
if __name__ == "__main__":
    # Create intelligent agent
    agent = IntelligentAgent("backend-api", "backend-api")

    # Test API skill
    api_task = {
        "type": "api_call",
        "params": {
            "method": "GET",
            "url": "https://api.github.com/users/github"
        }
    }
    result = agent.process_task(api_task)
    print(f"API Task Result: {result['success']}")

    # Test data processing
    data_task = {
        "type": "data_processing",
        "params": {
            "operation": "aggregate",
            "data": [1, 2, 3, 4, 5],
            "method": "sum"
        }
    }
    result = agent.process_task(data_task)
    print(f"Data Task Result: {result['output']}")

    # Get performance report
    print("\nPerformance Report:")
    print(json.dumps(agent.get_performance_report(), indent=2))