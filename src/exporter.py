import csv
import json
import sqlite3
from pathlib import Path
from typing import List, Dict

class DataExporter:
    def __init__(self, db_path: str):
        self.db_path = db_path

    def _fetch_data(self, query: str) -> List[Dict]:
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            cursor.execute(query)
            return [dict(row) for row in cursor.fetchall()]

    def to_csv(self, query: str, output_path: str):
        data = self._fetch_data(query)
        if not data:
            return
        
        with open(output_path, 'w', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=data[0].keys())
            writer.writeheader()
            writer.writerows(data)

    def to_json(self, query: str, output_path: str):
        data = self._fetch_data(query)
        with open(output_path, 'w') as f:
            json.dump(data, f, indent=2)
