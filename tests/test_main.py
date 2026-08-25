import json
import sqlite3
import subprocess
import sys


def test_cli_exports_json(tmp_path) -> None:
    database = tmp_path / "records.db"
    output = tmp_path / "records.json"
    with sqlite3.connect(database) as connection:
        connection.execute("CREATE TABLE records (id INTEGER, value TEXT)")
        connection.executemany("INSERT INTO records VALUES (?, ?)", [(1, "a"), (2, "b")])

    result = subprocess.run(
        [
            sys.executable,
            "main.py",
            "json",
            str(database),
            str(output),
            "SELECT * FROM records ORDER BY id",
        ],
        check=False,
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, result.stderr or result.stdout
    assert json.loads(result.stdout)["rows"] == 2
    assert json.loads(output.read_text(encoding="utf-8"))[1]["value"] == "b"
