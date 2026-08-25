# Security Policy

Sky Data Exporter is an engineering-beta read-only export utility, not an authorization boundary.

The SQLite connection is opened in read-only mode and enables `PRAGMA query_only`. Queries are limited to one `SELECT` or `WITH` statement, result size and width are bounded, outputs are written atomically, and existing files require explicit overwrite authorization from the CLI/library caller. The container runs as a non-root user.

Read-only access does not determine whether a caller is entitled to see the selected rows or columns. Integrators must separately enforce database-file permissions, identity, authorization, tenant isolation, field redaction, output encryption, retention, and secure transfer. Do not export credentials, private keys, regulated data, or other sensitive material unless those controls are in place.

Report vulnerabilities privately through GitHub security reporting when available. Do not publish private datasets, database files, credentials, or working exploit details in public issues.
