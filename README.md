# Sky Data Exporter

**Status: engineering beta.** A bounded, read-only SQLite query exporter for producing local JSON and CSV artifacts.

## Implemented behavior

- opens SQLite databases in read-only URI mode and enables `PRAGMA query_only`
- accepts a single `SELECT` or `WITH` statement only
- supports parameterized query values through the Python library API
- caps database size at 512 MiB, query length at 20,000 characters, result width at 200 columns, and rows at 100,000
- writes JSON and CSV through an atomic temporary-file replacement
- refuses to overwrite an existing destination unless explicitly requested
- CLI emits machine-readable JSON results/errors
- deterministic tests cover parameterized reads, JSON/CSV output, write-query rejection, multi-statement rejection, row caps, overwrite controls, and CLI execution
- CI verifies compile, Ruff, pytest, dependency audit, CLI smoke behavior, Docker packaging, and non-root execution

## Library example

```python
from src.exporter import DataExporter

exporter = DataExporter("analytics.db", max_rows=5000)
exporter.to_json(
    "SELECT id, name FROM users WHERE active = ? ORDER BY id",
    "users.json",
    [1],
)
```

## CLI

```bash
python main.py json analytics.db users.json \
  'SELECT id, name FROM users ORDER BY id'

python main.py csv analytics.db users.csv \
  'SELECT id, name FROM users ORDER BY id'
```

Use `--force` only when replacing an existing output is intentional.

## Container

```bash
docker build -t sky-data-exporter .
docker run --rm -v "$PWD:/data" sky-data-exporter \
  json /data/analytics.db /data/users.json 'SELECT * FROM users'
```

The image runs as an unprivileged UID and has no web server.

## SKYCOIN4444 integration

This product can provide controlled report/export boundaries for local SQLite-backed development tools, analytics jobs, migrations, or test fixtures. Production systems using PostgreSQL, MySQL, warehouses, object stores, or regulated data should use dedicated read-only adapters and authorization controls rather than routing those databases through SQLite.

## Explicit limitations

This is not a database administration tool, SQL proxy, BI platform, warehouse connector, backup system, streaming exporter, or distributed reporting service. It does not authenticate users, authorize table/column access, redact sensitive fields, encrypt output, schedule jobs, upload artifacts, or prove production deployment. Read-only SQL prevents writes through this connection but does not decide whether a caller is entitled to read the selected data.

See `SECURITY.md` and `CHANGELOG.md` for boundaries and productization history.
