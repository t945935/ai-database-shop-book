"""Model-independent, allowlisted read-only database tools."""
from __future__ import annotations

from datetime import date, datetime, timedelta, timezone
from uuid import uuid4

import psycopg


MAX_ROWS = 100
_ALLOWED_QUERIES = frozenset({"inventory_snapshot"})


def _validate_arguments(arguments: dict) -> tuple[date, date, int]:
    if type(arguments) is not dict:
        raise TypeError("arguments must be a dict")
    required = {"start_date", "end_date"}
    if not required.issubset(arguments):
        raise ValueError("start_date and end_date are required")
    start_date = arguments["start_date"]
    end_date = arguments["end_date"]
    if type(start_date) is not date or type(end_date) is not date:
        raise TypeError("start_date and end_date must be date")
    if start_date > end_date:
        raise ValueError("start_date must be on or before end_date")
    max_rows = arguments.get("max_rows", MAX_ROWS)
    if type(max_rows) is not int or not 1 <= max_rows <= MAX_ROWS:
        raise ValueError("max_rows must be an integer from 1 to 100")
    unexpected = set(arguments) - {"start_date", "end_date", "max_rows"}
    if unexpected:
        raise ValueError("unsupported arguments")
    return start_date, end_date, max_rows


def execute_tool(db: str, query_name: str, arguments: dict) -> dict:
    """Execute one fixed, bounded, read-only operational query.

    The function deliberately accepts a query name, not SQL. The returned rows
    contain only operational fields; ledger payloads and other sensitive data
    never cross this boundary.
    """
    if query_name not in _ALLOWED_QUERIES:
        raise ValueError("unknown query name")
    start_date, end_date, max_rows = _validate_arguments(arguments)
    end_exclusive = end_date + timedelta(days=1)

    with psycopg.connect(db) as conn:
        with conn.transaction():
            conn.execute("SET TRANSACTION READ ONLY")
            latest_event_at_in_range = conn.execute(
                """
                SELECT max(created_at)
                FROM ledger
                WHERE created_at >= %s AND created_at < %s
                """,
                (start_date, end_exclusive),
            ).fetchone()[0]
            rows = conn.execute(
                """
                SELECT sku, physical, reserved, physical - reserved AS available
                FROM balance
                WHERE sku IN (
                    SELECT DISTINCT sku
                    FROM ledger
                    WHERE created_at >= %s AND created_at < %s
                )
                ORDER BY sku
                LIMIT %s
                """,
                (start_date, end_exclusive, max_rows),
            ).fetchall()

    return {
        "query_name": query_name,
        "query_id": f"{query_name}:{uuid4().hex}",
        "latest_event_at_in_range": latest_event_at_in_range,
        "rows": [
            {
                "sku": sku,
                "physical": physical,
                "reserved": reserved,
                "available": available,
            }
            for sku, physical, reserved, available in rows
        ],
    }
