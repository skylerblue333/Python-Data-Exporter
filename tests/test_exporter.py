import csv
import json
import sqlite3

import pytest

from src.exporter import DataExporter, ExportError


@pytest.fixture
def database(tmp_path):
    path = tmp_path / "records.db"
    with sqlite3.connect(path) as connection:
        connection.execute("CREATE TABLE users (id INTEGER, name TEXT, active INTEGER)")
        connection.executemany(
            "INSERT INTO users VALUES (?, ?, ?)",
            [(1, "Alice", 1), (2, "Bob", 0), (3, "Chen", 1)],
        )
    return path


def test_parameterized_read_only_fetch(database) -> None:
    exporter = DataExporter(database)
    rows = exporter.fetch("SELECT id, name FROM users WHERE active = ? ORDER BY id", [1])
    assert rows == [{"id": 1, "name": "Alice"}, {"id": 3, "name": "Chen"}]


def test_json_and_csv_exports(database, tmp_path) -> None:
    exporter = DataExporter(database)
    json_path = tmp_path / "users.json"
    csv_path = tmp_path / "users.csv"

    json_result = exporter.to_json("SELECT id, name FROM users ORDER BY id", json_path)
    assert json_result["rows"] == 3
    assert json.loads(json_path.read_text(encoding="utf-8"))[1]["name"] == "Bob"

    csv_result = exporter.to_csv("SELECT id, name FROM users ORDER BY id", csv_path)
    assert csv_result["columns"] == 2
    with csv_path.open(encoding="utf-8", newline="") as handle:
        rows = list(csv.DictReader(handle))
    assert rows[2] == {"id": "3", "name": "Chen"}


def test_rejects_write_and_multiple_statements(database) -> None:
    exporter = DataExporter(database)
    with pytest.raises(ExportError, match="only SELECT or WITH"):
        exporter.fetch("DELETE FROM users")
    with pytest.raises(ExportError, match="multiple SQL statements"):
        exporter.fetch("SELECT 1; SELECT 2")


def test_row_limit_is_enforced(database) -> None:
    exporter = DataExporter(database, max_rows=2)
    with pytest.raises(ExportError, match="exceeds 2 rows"):
        exporter.fetch("SELECT * FROM users")


def test_output_requires_explicit_overwrite(database, tmp_path) -> None:
    output = tmp_path / "users.json"
    output.write_text("keep", encoding="utf-8")
    exporter = DataExporter(database)
    with pytest.raises(ExportError, match="already exists"):
        exporter.to_json("SELECT * FROM users", output)
    exporter.to_json("SELECT * FROM users", output, force=True)
    assert json.loads(output.read_text(encoding="utf-8"))[0]["name"] == "Alice"
