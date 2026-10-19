"""Fills stall.db with menu items + 18 fake orders over the last 7 days.
Run:  python seed_data.py     (WARNING: resets the database)"""
import random
from datetime import datetime, timedelta
import db

ITEMS = [
    ('Nasi Lemak Special', 60, 8.50),
    ('Teh Tarik', 120, 3.00),
    ('Chicken Chop', 40, 15.00),
    ('Mee Goreng', 50, 7.00),
    ('Sirap Bandung', 80, 2.50),
    ('Roti Canai', 70, 2.00),
]
CUSTOMERS = ['Ahmad', 'Siti', 'John', 'Ravi', 'Mei Ling', 'Farah', 'Kumar', 'Aisyah', 'Daniel']


def main():
    random.seed(42)  # same fake data every run
    db.init_db()
    conn = db.get_connection()
    try:
        with conn:
            conn.executemany("INSERT INTO items (name, stock, price) VALUES (?, ?, ?)", ITEMS)
            menu = conn.execute("SELECT id, name, price FROM items").fetchall()
            now = datetime.now()
            for i in range(18):
                day_offset = min(6, i // 3)  # 3 orders per day, today gets the last ones
                when = (now - timedelta(days=6 - day_offset)).replace(
                    hour=random.randint(8, 20), minute=random.randint(0, 59), second=0, microsecond=0)
                if when > now:
                    when = now - timedelta(minutes=random.randint(1, 30))
                status = 'Unpaid' if random.random() < 0.2 else 'Paid'
                picks = random.sample(menu, random.randint(1, 3))
                lines = [(m, random.randint(1, 3)) for m in picks]
                total = round(sum(m['price'] * q for m, q in lines), 2)
                cur = conn.execute(
                    "INSERT INTO orders (customer_name, total_price, status, created_at) VALUES (?, ?, ?, ?)",
                    (random.choice(CUSTOMERS), total, status, when.strftime('%Y-%m-%d %H:%M:%S')))
                for m, q in lines:
                    conn.execute(
                        "INSERT INTO order_items (order_id, item_id, item_name, quantity, unit_price) "
                        "VALUES (?, ?, ?, ?, ?)", (cur.lastrowid, m['id'], m['name'], q, m['price']))
                    conn.execute("UPDATE items SET stock = stock - ? WHERE id = ?", (q, m['id']))
            # make one item low on stock so the red badge shows up in the UI
            conn.execute("UPDATE items SET stock = 6 WHERE name = 'Chicken Chop'")
    finally:
        conn.close()
    print("DONE! Tables created and 18 sample orders added.")


if __name__ == '__main__':
    main()
