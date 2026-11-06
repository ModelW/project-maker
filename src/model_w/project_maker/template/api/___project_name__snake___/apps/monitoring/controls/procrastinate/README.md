Checks that Procrastinate is correctly wired to its database and that both the
default Django app and the worker app can connect.

This relies on Procrastinate's own built-in health checks to verify:

1. **Database connection** — the system can connect to the database.
2. **Migration status** — all required Procrastinate migrations are applied.
3. **Default Django Procrastinate app** — the default app can connect.
4. **Worker app** — the worker app can establish a connection.

## Troubleshooting

A failure usually indicates:

1. **Database connectivity issues** (network problems, credentials, server down).
2. **Missing migrations** — run `python manage.py migrate procrastinate`.
3. **Configuration issues** with the default app or the worker app.

Check the database server status and network connectivity, verify the
credentials and permissions, and review the logs for the underlying error.
