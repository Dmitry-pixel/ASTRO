import sqlite3
import os
from typing import Dict, Any

class SQLiteRepository:
    _instance = None
    _db_path = "hd_data.sqlite"

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

    def get_planet_info(self, planet_name: str) -> Dict[str, Any]:
        conn = self.connect()
        cursor = conn.cursor()
        cursor.execute("SELECT name, description, role, archetype FROM public_planets WHERE name = ?", (planet_name,))
        row = cursor.fetchone()
        if row:
            return dict(row)
        return {"name": planet_name, "description": ""}

    # More methods for colors, tones, etc. can be added here as needed.
