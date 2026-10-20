"""Database helpers (Developer 2). Developer 1 imports these in app.py.

Tables:
  items(id, name, stock, price)
  orders(id, customer_name, total_price, status, created_at)
  order_items(id, order_id, item_id, item_name, quantity, unit_price)
"""
import os
import sqlite3

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, 'stall.db')
SCHEMA_PATH = os.path.join(BASE_DIR, 'schema.sql')
LOW_STOCK_THRESHOLD = 10


def get_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def init_db():
    """Create (or reset) all tables from schema.sql. WARNING: wipes data."""
    with open(SCHEMA_PATH, 'r', encoding='utf-8') as f:
        script = f.read()
    conn = sqlite3.connect(DB_PATH)
    try:
        conn.executescript(script)
        conn.commit()
    finally:
        conn.close()


def ensure_db():
    """Create missing tables without deleting existing data."""
    with open(SCHEMA_PATH, 'r', encoding='utf-8') as f:
        script = f.read()
    statements = []
    for statement in script.split(';'):
        statement = statement.strip()
        if not statement or statement.startswith('PRAGMA') or statement.startswith('DROP TABLE'):
            continue
        statement = statement.replace('CREATE TABLE ', 'CREATE TABLE IF NOT EXISTS ', 1)
        statement = statement.replace('CREATE INDEX ', 'CREATE INDEX IF NOT EXISTS ', 1)
        statements.append(statement)

    conn = sqlite3.connect(DB_PATH)
    try:
        conn.executescript(';\n'.join(statements))
        conn.commit()
    finally:
        conn.close()


def get_all_items():
    """Inventory list. Each dict has: id, name, stock, price, low_stock (bool)."""
    conn = get_connection()
    try:
        rows = conn.execute("SELECT id, name, stock, price FROM items ORDER BY name").fetchall()
    finally:
        conn.close()
    items = [dict(r) for r in rows]
    for it in items:
        it['low_stock'] = it['stock'] <= LOW_STOCK_THRESHOLD
    return items


def get_low_stock_count():
    conn = get_connection()
    try:
        row = conn.execute("SELECT COUNT(*) FROM items WHERE stock <= ?",
                           (LOW_STOCK_THRESHOLD,)).fetchone()
    finally:
        conn.close()
    return int(row[0])


def get_customer_balances():
    conn = get_connection()
    try:
        rows = conn.execute(
            "SELECT customer_name, balance, updated_at "
            "FROM customer_balances ORDER BY customer_name"
        ).fetchall()
    finally:
        conn.close()
    return [dict(row) for row in rows]


def add_customer_balance(customer_name, amount):
    customer = str(customer_name or '').strip()
    if not customer:
        return False, "Customer name is required."
    try:
        value = round(float(amount), 2)
    except (TypeError, ValueError):
        return False, "Amount must be a valid number."
    if value <= 0:
        return False, "Amount must be greater than RM 0.00."

    conn = get_connection()
    try:
        with conn:
            conn.execute(
                "INSERT INTO customer_balances (customer_name, balance) VALUES (?, ?) "
                "ON CONFLICT(customer_name) DO UPDATE SET "
                "balance = balance + excluded.balance, "
                "updated_at = datetime('now', 'localtime')",
                (customer, value),
            )
        return True, f"RM {value:.2f} added to {customer}'s balance."
    except sqlite3.Error as error:
        return False, f"Database error: {error}"
    finally:
        conn.close()


def mark_order_paid(order_id):
    try:
        order_id = int(order_id)
    except (TypeError, ValueError):
        return False, "Order ID is not valid."

    conn = get_connection()
    try:
        with conn:
            order = conn.execute(
                "SELECT status FROM orders WHERE id = ?", (order_id,)
            ).fetchone()
            if order is None:
                return False, "Order not found."
            if order['status'] == 'Paid':
                return False, "Order is already paid."
            conn.execute("UPDATE orders SET status = 'Paid' WHERE id = ?", (order_id,))
        return True, f"Order #{order_id} marked as paid."
    except sqlite3.Error as error:
        return False, f"Database error: {error}"
    finally:
        conn.close()


def pay_order_from_balance(order_id):
    try:
        order_id = int(order_id)
    except (TypeError, ValueError):
        return False, "Order ID is not valid."

    conn = get_connection()
    try:
        with conn:
            order = conn.execute(
                "SELECT customer_name, total_price, status FROM orders WHERE id = ?",
                (order_id,),
            ).fetchone()
            if order is None:
                return False, "Order not found."
            if order['status'] == 'Paid':
                return False, "Order is already paid."

            balance = conn.execute(
                "SELECT id, balance FROM customer_balances "
                "WHERE lower(customer_name) = lower(?)",
                (order['customer_name'],),
            ).fetchone()
            if balance is None:
                return False, f"No balance found for {order['customer_name']}."
            if balance['balance'] < order['total_price']:
                return False, (
                    f"{order['customer_name']} has RM {balance['balance']:.2f}; "
                    f"the order costs RM {order['total_price']:.2f}."
                )

            conn.execute(
                "UPDATE customer_balances SET balance = balance - ?, "
                "updated_at = datetime('now', 'localtime') WHERE id = ?",
                (order['total_price'], balance['id']),
            )
            conn.execute("UPDATE orders SET status = 'Paid' WHERE id = ?", (order_id,))
        return True, f"Order #{order_id} paid from {order['customer_name']}'s balance."
    except sqlite3.Error as error:
        return False, f"Database error: {error}"
    finally:
        conn.close()


def get_recent_orders(limit=20):
    """Latest orders, each with an 'items' list of {name, quantity, unit_price}."""
    conn = get_connection()
    try:
        orders = [dict(r) for r in conn.execute(
            "SELECT id, customer_name, total_price, status, created_at "
            "FROM orders ORDER BY created_at DESC, id DESC LIMIT ?", (limit,)).fetchall()]
        for o in orders:
            rows = conn.execute(
                "SELECT item_name AS name, quantity, unit_price "
                "FROM order_items WHERE order_id = ?", (o['id'],)).fetchall()
            o['items'] = [dict(r) for r in rows]
            o['items_text'] = ", ".join(f"{r['quantity']}x {r['name']}" for r in rows)
    finally:
        conn.close()
    return orders


def _find_item(conn, name):
    """Case-insensitive match; falls back to partial match ('nasi lemak' -> 'Nasi Lemak Special')."""
    name = (name or '').strip()
    if not name:
        return None
    row = conn.execute("SELECT * FROM items WHERE lower(name) = lower(?)", (name,)).fetchone()
    if row:
        return row
    rows = conn.execute("SELECT * FROM items WHERE lower(name) LIKE ?",
                        (f"%{name.lower()}%",)).fetchall()
    return rows[0] if len(rows) == 1 else None


def save_order(parsed):
    """Save a parsed order. Returns (success: bool, message: str).

    Expected input (from parser.py):
      {
        "customer_name": "Ali",
        "items": [{"name": "Teh Tarik", "quantity": 2}, ...],
        "payment_status": "Paid"          # or "Unpaid"
      }
    Total price is calculated from the items table, never trusted from the AI.
    Everything happens in one transaction: if anything fails, nothing is saved.
    """
    if not isinstance(parsed, dict):
        return False, "Parsed order is not valid data."

    customer = str(parsed.get('customer_name') or 'Walk-in').strip() or 'Walk-in'
    status = str(parsed.get('payment_status') or parsed.get('status') or 'Unpaid').strip().capitalize()
    if status not in ('Paid', 'Unpaid'):
        status = 'Unpaid'

    raw_items = parsed.get('items')
    if not isinstance(raw_items, list) or not raw_items:
        return False, "No items found in the order."

    conn = get_connection()
    try:
        lines, total = [], 0.0
        for entry in raw_items:
            if not isinstance(entry, dict):
                return False, "An item in the order is not valid."
            try:
                qty = int(entry.get('quantity', 1))
            except (TypeError, ValueError):
                return False, f"Invalid quantity for '{entry.get('name')}'."
            if qty <= 0:
                return False, f"Quantity must be at least 1 for '{entry.get('name')}'."
            item = _find_item(conn, entry.get('name'))
            if item is None:
                return False, f"Item not found on the menu: '{entry.get('name')}'."
            if item['stock'] < qty:
                return False, f"Not enough stock for {item['name']} (have {item['stock']}, need {qty})."
            lines.append((item, qty))
            total += item['price'] * qty

        # Merge duplicates of the same item so stock checks stay correct
        need = {}
        for item, qty in lines:
            need[item['id']] = need.get(item['id'], 0) + qty
        for item, _ in lines:
            if item['stock'] < need[item['id']]:
                return False, f"Not enough stock for {item['name']}."

        with conn:  # commits on success, rolls back on error
            cur = conn.execute(
                "INSERT INTO orders (customer_name, total_price, status) VALUES (?, ?, ?)",
                (customer, round(total, 2), status))
            order_id = cur.lastrowid
            for item, qty in lines:
                conn.execute(
                    "INSERT INTO order_items (order_id, item_id, item_name, quantity, unit_price) "
                    "VALUES (?, ?, ?, ?, ?)",
                    (order_id, item['id'], item['name'], qty, item['price']))
                conn.execute("UPDATE items SET stock = stock - ? WHERE id = ?", (qty, item['id']))
        return True, f"Order #{order_id} saved for {customer} (RM {total:.2f}, {status})."
    except sqlite3.Error as e:
        return False, f"Database error: {e}"
    finally:
        conn.close()
