from __future__ import annotations

import argparse
import json
from pathlib import Path

from src.exporter import DataExporter, ExportError


def parser() -> argparse.ArgumentParser:
    root = argparse.ArgumentParser(
        prog="sky-data-exporter",
        description="Bounded read-only SQLite query exporter",
    )
    root.add_argument("format", choices=("json", "csv"))
    root.add_argument("database", type=Path)
    root.add_argument("output", type=Path)
    root.add_argument("query", help="single SELECT or WITH query")
    root.add_argument("--max-rows", type=int, default=100_000)
    root.add_argument("--force", action="store_true")
    return root


def main() -> int:
    args = parser().parse_args()
    try:
        exporter = DataExporter(args.database, max_rows=args.max_rows)
        if args.format == "json":
            result = exporter.to_json(args.query, args.output, force=args.force)
        else:
            result = exporter.to_csv(args.query, args.output, force=args.force)
    except ExportError as exc:
        print(json.dumps({"error": str(exc)}, separators=(",", ":")))
        return 1
    print(json.dumps(result, separators=(",", ":")))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
