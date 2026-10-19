"""Pandas analytics (Developer 2). Only counts PAID orders as revenue."""
import sqlite3
import pandas as pd
from db import DB_PATH


def _read(query, params=()):
    conn = sqlite3.connect(DB_PATH)
    try:
        return pd.read_sql_query(query, conn, params=params)
    finally:
        conn.close()


def get_total_revenue_today():
    """Total RM from Paid orders created today. Returns a float."""
    df = _read("SELECT total_price FROM orders "
               "WHERE status = 'Paid' AND date(created_at) = date('now', 'localtime')")
    if df.empty:
        return 0.0
    return round(float(df['total_price'].sum()), 2)


def get_todays_order_count():
    df = _read("SELECT COUNT(*) AS n FROM orders WHERE date(created_at) = date('now', 'localtime')")
    return int(df['n'].iloc[0])


def get_unpaid_total():
    df = _read("SELECT COALESCE(SUM(total_price), 0) AS t FROM orders WHERE status = 'Unpaid'")
    return round(float(df['t'].iloc[0]), 2)


def get_best_selling_items(limit=5):
    """List of {'item_name': str, 'quantity': int}, best first. Paid orders only."""
    df = _read("SELECT oi.item_name, oi.quantity FROM order_items oi "
               "JOIN orders o ON o.id = oi.order_id WHERE o.status = 'Paid'")
    if df.empty:
        return []
    grouped = (df.groupby('item_name', as_index=False)['quantity'].sum()
                 .sort_values(by=['quantity', 'item_name'], ascending=[False, True])
                 .head(limit))
    grouped['quantity'] = grouped['quantity'].astype(int)
    return grouped.to_dict(orient='records')


def get_weekly_trend():
    """Last 7 days (including today), missing days filled with 0.
    Returns {'dates': ['2026-10-13', ...], 'revenues': [12.5, 0.0, ...]} for Chart.js."""
    days = pd.date_range(end=pd.Timestamp.now().normalize(), periods=7)
    start = days[0].strftime('%Y-%m-%d')
    df = _read("SELECT date(created_at) AS day, SUM(total_price) AS revenue FROM orders "
               "WHERE status = 'Paid' AND date(created_at) >= ? GROUP BY date(created_at)",
               (start,))
    by_day = {}
    if not df.empty:
        by_day = dict(zip(df['day'], df['revenue']))
    dates = [d.strftime('%Y-%m-%d') for d in days]
    revenues = [round(float(by_day.get(d, 0.0)), 2) for d in dates]
    return {'dates': dates, 'revenues': revenues}
