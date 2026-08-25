from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path
from typing import Any

MAX_INPUT_BYTES = 16 * 1024 * 1024
MAX_ROWS = 100_000
MAX_COLUMNS = 200


class ExportError(ValueError):
    pass


def require_input(path: Path) -> Path:
    target = path.expanduser().resolve()
    if not target.is_file():
        raise ExportError("input must be an existing file")
    if target.stat().st_size > MAX_INPUT_BYTES:
        raise ExportError("input exceeds 16 MiB limit")
    return target


def require_output(path: Path, input_path: Path, force: bool) -> Path:
    target = path.expanduser().resolve()
    if target == input_path:
        raise ExportError("output must differ from input")
    if target.exists() and not force:
        raise ExportError("output already exists; pass --force to replace it")
    target.parent.mkdir(parents=True, exist_ok=True)
    return target


def json_to_csv(input_path: Path, output_path: Path, force: bool = False) -> dict[str, Any]:
    source = require_input(input_path)
    destination = require_output(output_path, source, force)
    try:
        value = json.loads(source.read_text(encoding="utf-8"))
    except UnicodeDecodeError as exc:
        raise ExportError("JSON input must be UTF-8") from exc
    except json.JSONDecodeError as exc:
        raise ExportError(f"invalid JSON at line {exc.lineno} column {exc.colno}") from exc

    if not isinstance(value, list):
        raise ExportError("JSON input must be an array of objects")
    if len(value) > MAX_ROWS:
        raise ExportError(f"row count exceeds {MAX_ROWS}")
    if any(not isinstance(row, dict) for row in value):
        raise ExportError("every JSON array item must be an object")

    columns = sorted({str(key) for row in value for key in row})
    if len(columns) > MAX_COLUMNS:
        raise ExportError(f"column count exceeds {MAX_COLUMNS}")

    with destination.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=columns, extrasaction="ignore")
        writer.writeheader()
        for row in value:
            normalized: dict[str, str] = {}
            for key in columns:
                item = row.get(key)
                if item is None:
                    normalized[key] = ""
                elif isinstance(item, (dict, list)):
                    normalized[key] = json.dumps(item, separators=(",", ":"), ensure_ascii=False)
                else:
                    normalized[key] = str(item)
            writer.writerow(normalized)

    return {"format": "csv", "rows": len(value), "columns": len(columns), "output": str(destination)}


def csv_to_json(input_path: Path, output_path: Path, force: bool = False) -> dict[str, Any]:
    source = require_input(input_path)
    destination = require_output(output_path, source, force)
    try:
        handle = source.open("r", encoding="utf-8", newline="")
    except UnicodeDecodeError as exc:
        raise ExportError("CSV input must be UTF-8") from exc

    with handle:
        reader = csv.DictReader(handle)
        if reader.fieldnames is None:
            raise ExportError("CSV input must include a header row")
        if len(reader.fieldnames) > MAX_COLUMNS:
            raise ExportError(f"column count exceeds {MAX_COLUMNS}")
        if len(set(reader.fieldnames)) != len(reader.fieldnames):
            raise ExportError("CSV header names must be unique")
        rows: list[dict[str, str]] = []
        for row_number, row in enumerate(reader, start=1):
            if row_number > MAX_ROWS:
                raise ExportError(f"row count exceeds {MAX_ROWS}")
            if None in row:
                raise ExportError("CSV row contains more values than the header")
            rows.append({key: value or "" for key, value in row.items()})

    destination.write_text(json.dumps(rows, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    return {"format": "json", "rows": len(rows), "columns": len(reader.fieldnames), "output": str(destination)}


def parser() -> argparse.ArgumentParser:
    root = argparse.ArgumentParser(prog="sky-data-exporter", description="Bounded local JSON/CSV exporter")
    commands = root.add_subparsers(dest="command", required=True)
    for name in ("json-to-csv", "csv-to-json"):
        command = commands.add_parser(name)
        command.add_argument("input", type=Path)
        command.add_argument("output", type=Path)
        command.add_argument("--force", action="store_true")
    return root


def main() -> int:
    args = parser().parse_args()
    try:
        if args.command == "json-to-csv":
            result = json_to_csv(args.input, args.output, args.force)
        else:
            result = csv_to_json(args.input, args.output, args.force)
    except ExportError as exc:
        print(json.dumps({"error": str(exc)}, separators=(",", ":")))
        return 1
    print(json.dumps(result, separators=(",", ":")))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
