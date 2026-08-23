import sqlite3
import os
from typing import Dict, Any

# hd_data.sqlite is reference data shipped with the repository. Resolve it against
# the project root rather than the process working directory, so the repository
# works regardless of where uvicorn or pytest was started from.
# HD_DATA_PATH overrides the location.
_PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
DEFAULT_DB_PATH = os.environ.get("HD_DATA_PATH") or os.path.join(_PROJECT_ROOT, "hd_data.sqlite")


class SQLiteRepository:
    _instance = None
    _db_path = DEFAULT_DB_PATH

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(SQLiteRepository, cls).__new__(cls)
            cls._instance.connection = None
        return cls._instance

    def connect(self):
        if self.connection is None:
            if not os.path.exists(self._db_path):
                raise FileNotFoundError(f"Database file not found: {self._db_path}")
            self.connection = sqlite3.connect(self._db_path, check_same_thread=False)
            self.connection.row_factory = sqlite3.Row
        return self.connection

    def get_gate_label(self, gate_number: int) -> Dict[str, Any]:
        conn = self.connect()
        cursor = conn.cursor()
        cursor.execute("SELECT name, summary FROM public_gates WHERE gate_number = ?", (gate_number,))
        row = cursor.fetchone()
        if row:
            return dict(row)
        return {"name": f"Gate {gate_number}", "summary": ""}

    def get_line_label(self, gate_number: int, line_number: int) -> Dict[str, Any]:
        conn = self.connect()
        cursor = conn.cursor()
        cursor.execute("SELECT name, description FROM public_gate_lines WHERE gate_number = ? AND line_number = ?", 
                       (gate_number, line_number))
        row = cursor.fetchone()
        if row:
            return dict(row)
        return {"name": f"Line {line_number}", "description": ""}

    def get_channel(self, gate_a: int, gate_b: int) -> Dict[str, Any]:
        """Channel reference row. `channel_id` is stored in one gate order only,
        so both are tried."""
        conn = self.connect()
        cursor = conn.cursor()
        for key in (f"{gate_a}-{gate_b}", f"{gate_b}-{gate_a}"):
            cursor.execute(
                "SELECT channel_id, name, type, description, design_purpose "
                "FROM public_channels WHERE channel_id = ?", (key,)
            )
            row = cursor.fetchone()
            if row:
                return dict(row)
        return {}

    def get_channel_gifts(self, channel_id: str) -> Dict[int, str]:
        """{gate_number: gift} for one channel."""
        conn = self.connect()
        cursor = conn.cursor()
        cursor.execute(
            "SELECT gate_number, gift FROM public_channel_gates WHERE channel_id = ?",
            (channel_id,)
        )
        return {int(r["gate_number"]): r["gift"] for r in cursor.fetchall()}

    def get_gate_reference(self, gate_number: int) -> Dict[str, Any]:
        """Fuller gate row than `get_gate_label` — used by the relational engines."""
        conn = self.connect()
        cursor = conn.cursor()
        cursor.execute(
            "SELECT gate_number, name, summary, circuit, quarter, notes "
            "FROM public_gates WHERE gate_number = ?", (gate_number,)
        )
        row = cursor.fetchone()
        return dict(row) if row else {"gate_number": gate_number, "name": f"Gate {gate_number}"}

    def get_planet_info(self, planet_name: str) -> Dict[str, Any]:
        conn = self.connect()
        cursor = conn.cursor()
        cursor.execute("SELECT name, description, role, archetype FROM public_planets WHERE name = ?", (planet_name,))
        row = cursor.fetchone()
        if row:
            return dict(row)
        return {"name": planet_name, "description": ""}

    # More methods for colors, tones, etc. can be added here as needed.
