import pytest
import sqlite3
import json
from pathlib import Path
from src.exporter import DataExporter

@pytest.fixture
def setup_db(tmp_path):
    db_file = tmp_path / "test.db"
    conn = sqlite3.connect(db_file)
    conn.execute("CREATE TABLE users (id INT, name TEXT)")
    conn.execute("INSERT INTO users VALUES (1, 'Alice'), (2, 'Bob')")
    conn.commit()
    conn.close()
    return str(db_file)

def test_json_export(setup_db, tmp_path):
    out_file = tmp_path / "out.json"
    exporter = DataExporter(setup_db)
    exporter.to_json("SELECT * FROM users", str(out_file))
    
    with open(out_file) as f:
        data = json.load(f)
    assert len(data) == 2
    assert data[0]["name"] == "Alice"
