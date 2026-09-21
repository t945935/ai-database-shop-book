from datetime import date, datetime, timezone
import re

import pytest

from ai_tools import execute_tool


def seed_ledger(db):
    import psycopg

    with psycopg.connect(db) as conn:
        conn.execute(
            """
            INSERT INTO balance(sku, physical, reserved, value)
            VALUES ('COFFEE-250', 10, 2, 3200.000000)
            """
        )
        conn.execute(
            """
            INSERT INTO ledger(
                event, kind, sku, payload, physical_delta, reserved_delta,
                value_delta, created_at
            )
            VALUES
              ('evt-1', 'receive', 'COFFEE-250', '{"internal_note":"do not expose"}',
               10, 0, 3200.000000, '2026-09-01 10:00:00+00'),
              ('evt-2', 'reserve', 'COFFEE-250', '{}',
               0, 2, 0, '2026-09-02 10:00:00+00')
            """
        )


def test_inventory_snapshot_is_bounded_and_has_audit_metadata(db):
    seed_ledger(db)

    result = execute_tool(
        db,
        "inventory_snapshot",
        {"start_date": date(2026, 9, 1), "end_date": date(2026, 9, 2)},
    )

    assert result["query_name"] == "inventory_snapshot"
    assert re.fullmatch(r"inventory_snapshot:[0-9a-f]{32}", result["query_id"])
    assert result["data_as_of"] == datetime(2026, 9, 2, 10, tzinfo=timezone.utc)
    assert result["rows"] == [
        {"sku": "COFFEE-250", "physical": 10, "reserved": 2, "available": 8}
    ]
    assert "payload" not in result["rows"][0]


def test_unknown_tool_is_rejected_without_sql(db):
    with pytest.raises(ValueError, match="unknown query name"):
        execute_tool(db, "arbitrary_sql", {})


def test_date_types_and_order_are_validated(db):
    with pytest.raises(TypeError, match="date"):
        execute_tool(db, "inventory_snapshot", {"start_date": "2026-09-01", "end_date": date(2026, 9, 2)})
    with pytest.raises(ValueError, match="start_date"):
        execute_tool(db, "inventory_snapshot", {"start_date": date(2026, 9, 3), "end_date": date(2026, 9, 2)})


def test_result_limit_is_enforced(db):
    with pytest.raises(ValueError, match="max_rows"):
        execute_tool(
            db,
            "inventory_snapshot",
            {"start_date": date(2026, 9, 1), "end_date": date(2026, 9, 2), "max_rows": 101},
        )


def test_write_like_query_name_is_not_allowed(db):
    with pytest.raises(ValueError, match="unknown query name"):
        execute_tool(db, "delete_ledger", {})
