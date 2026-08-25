from __future__ import annotations

import csv
import json
import os
import sqlite3
import tempfile
from collections.abc import Sequence
from pathlib import Path
from typing import Any

MAX_DATABASE_BYTES = 512 * 1024 * 1024
MAX_QUERY_CHARS = 20_000
MAX_ROWS = 100_000
MAX_COLUMNS = 200


class ExportError(ValueError):
    """Raised when an export request violates the product boundary."""


class DataExporter:
    """Bounded, read-only SQLite query exporter for JSON and CSV artifacts."""

    def __init__(self, db_path: str | Path, *, max_rows: int = MAX_ROWS) -> None:
        path = Path(db_path).expanduser().resolve()
        if not path.is_file():
            raise ExportError("database path must reference an existing file")
        if path.stat().st_size > MAX_DATABASE_BYTES:
            raise ExportError("database exceeds 512 MiB limit")
        if not 1 <= max_rows <= MAX_ROWS:
            raise ExportError(f"max_rows must be between 1 and {MAX_ROWS}")
        self.db_path = path
        self.max_rows = max_rows

    @staticmethod
    def _validate_query(query: str) -> str:
        query = query.strip()
        if not query or len(query) > MAX_QUERY_CHARS:
            raise ExportError("query must contain 1-20000 characters")
        first = query.split(None, 1)[0].upper()
        if first not in {"SELECT", "WITH"}:
            raise ExportError("only SELECT or WITH queries are allowed")
        if ";" in query.rstrip(";"):
            raise ExportError("multiple SQL statements are not allowed")
        return query.rstrip(";")

    def fetch(self, query: str, parameters: Sequence[Any] = ()) -> list[dict[str, Any]]:
        safe_query = self._validate_query(query)
        uri = f"file:{self.db_path.as_posix()}?mode=ro"
        try:
            with sqlite3.connect(uri, uri=True, timeout=5) as connection:
                connection.execute("PRAGMA query_only = ON")
                connection.row_factory = sqlite3.Row
                cursor = connection.execute(safe_query, tuple(parameters))
                if cursor.description is None:
                    raise ExportError("query did not produce a result set")
                if len(cursor.description) > MAX_COLUMNS:
                    raise ExportError(f"result exceeds {MAX_COLUMNS} columns")
                rows = cursor.fetchmany(self.max_rows + 1)
        except sqlite3.Error as exc:
            raise ExportError(f"SQLite query failed: {exc}") from exc
        if len(rows) > self.max_rows:
            raise ExportError(f"result exceeds {self.max_rows} rows")
        return [dict(row) for row in rows]

    @staticmethod
    def _destination(output_path: str | Path, force: bool) -> Path:
        path = Path(output_path).expanduser().resolve()
        if path.exists() and not force:
            raise ExportError("output already exists; pass force=True to replace it")
        path.parent.mkdir(parents=True, exist_ok=True)
        return path

    @staticmethod
    def _atomic_write(path: Path, write) -> None:
        descriptor, temporary_name = tempfile.mkstemp(prefix=f".{path.name}.", dir=path.parent)
        os.close(descriptor)
        temporary = Path(temporary_name)
        try:
            write(temporary)
            os.replace(temporary, path)
        finally:
            temporary.unlink(missing_ok=True)

    def to_json(
        self,
        query: str,
        output_path: str | Path,
        parameters: Sequence[Any] = (),
        *,
        force: bool = False,
    ) -> dict[str, Any]:
        rows = self.fetch(query, parameters)
        destination = self._destination(output_path, force)

        def write(path: Path) -> None:
            path.write_text(json.dumps(rows, indent=2, ensure_ascii=False, default=str) + "\n", encoding="utf-8")

        self._atomic_write(destination, write)
        return {"format": "json", "rows": len(rows), "output": str(destination)}

    def to_csv(
        self,
        query: str,
        output_path: str | Path,
        parameters: Sequence[Any] = (),
        *,
        force: bool = False,
    ) -> dict[str, Any]:
        rows = self.fetch(query, parameters)
        destination = self._destination(output_path, force)
        columns = list(rows[0].keys()) if rows else []

        def write(path: Path) -> None:
            with path.open("w", newline="", encoding="utf-8") as handle:
                writer = csv.DictWriter(handle, fieldnames=columns)
                if columns:
                    writer.writeheader()
                    writer.writerows(rows)

        self._atomic_write(destination, write)
        return {"format": "csv", "rows": len(rows), "columns": len(columns), "output": str(destination)}
