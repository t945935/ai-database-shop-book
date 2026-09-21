from datetime import date
from decimal import Decimal as D
from pathlib import Path

import psycopg


SETUP = Path("lessons/ch10_setup.sql")
REPORT = Path("lessons/ch10_reports.sql")


def ch10_db(db):
    with psycopg.connect(db) as c:
        c.execute(SETUP.read_text())
        c.execute(REPORT.read_text())
    return db


def test_ch10_report_separates_sales_refunds_cogs_and_gross_profit(db):
    ch10 = ch10_db(db)
    with psycopg.connect(ch10) as c:
        rows = c.execute(
            """
            SELECT sku_code, units, gross_sales, refunds, cogs, gross_profit
            FROM ch10_monthly_operations
            WHERE period_start = DATE '2026-09-01'
            ORDER BY sku_code
            """
        ).fetchall()
    assert rows == [
        ("BEANS-250", 5, D("1850"), D("300"), D("560"), D("990")),
        ("EMPTY-100", 0, D("0"), D("0"), D("0"), D("0")),
        ("FILTER-100", 2, D("240"), D("0"), D("80"), D("160")),
    ]


def test_ch10_zero_sales_is_kept_and_out_of_period_events_are_excluded(db):
    ch10 = ch10_db(db)
    with psycopg.connect(ch10) as c:
        assert c.execute(
            """
            SELECT sku_code, units, gross_sales, refunds, cogs, gross_profit
            FROM ch10_monthly_operations
            WHERE period_start = DATE '2026-10-01'
            ORDER BY sku_code
            """
        ).fetchall() == [
            ("BEANS-250", 1, D("370"), D("0"), D("120"), D("250")),
            ("EMPTY-100", 0, D("0"), D("0"), D("0"), D("0")),
            ("FILTER-100", 0, D("0"), D("0"), D("0"), D("0")),
        ]


def test_ch10_refund_is_not_counted_as_sales_and_cost_uses_shipment_snapshot(db):
    ch10 = ch10_db(db)
    with psycopg.connect(ch10) as c:
        assert c.execute(
            """
            SELECT units, gross_sales, refunds, cogs, gross_profit
            FROM ch10_monthly_operations
            WHERE sku_code = 'BEANS-250' AND period_start = DATE '2026-09-01'
            """
        ).fetchone() == (5, D("1850"), D("300"), D("560"), D("990"))
        assert c.execute(
            "SELECT unit_cost_snapshot FROM ch10_shipment ORDER BY shipped_on, id"
        ).fetchall() == [(D("100"),), (D("40"),), (D("120"),), (D("120"),), (D("120"),)]


def test_ch10_window_rank_orders_profit_within_period(db):
    ch10 = ch10_db(db)
    with psycopg.connect(ch10) as c:
        rows=c.execute(Path('lessons/ch10_rank.sql').read_text()).fetchall()
    assert rows == [
        ('BEANS-250',date(2026,9,1),D('990'),1),
        ('FILTER-100',date(2026,9,1),D('160'),2),
        ('EMPTY-100',date(2026,9,1),D('0'),3),
    ]
