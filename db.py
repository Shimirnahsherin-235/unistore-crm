import sqlite3

def init_db():
    conn = sqlite3.connect("crm.db")
    conn.execute("""
        CREATE TABLE IF NOT EXISTS stores (
            store_id INTEGER PRIMARY KEY AUTOINCREMENT,
            store_name TEXT NOT NULL,
            city TEXT
        )
    """)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS customers (
            customer_id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            phone TEXT NOT NULL UNIQUE,
            email TEXT
        )
    """)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS products (
            product_id INTEGER PRIMARY KEY AUTOINCREMENT,
            product_name TEXT NOT NULL,
            price REAL NOT NULL
        )
    """)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS orders (
            order_id INTEGER PRIMARY KEY AUTOINCREMENT,
            customer_id INTEGER NOT NULL,
            store_id INTEGER NOT NULL,
            order_date TEXT DEFAULT CURRENT_TIMESTAMP,
            total REAL NOT NULL,
            FOREIGN KEY (customer_id) REFERENCES customers(customer_id),
            FOREIGN KEY (store_id) REFERENCES stores(store_id)
        )
    """)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS order_items (
            item_id INTEGER PRIMARY KEY AUTOINCREMENT,
            order_id INTEGER NOT NULL,
            product_id INTEGER NOT NULL,
            quantity INTEGER NOT NULL,
            unit_price REAL NOT NULL,
            FOREIGN KEY (order_id) REFERENCES orders(order_id),
            FOREIGN KEY (product_id) REFERENCES products(product_id)
        )
    """)
    conn.commit()
    conn.close()
    
def add_store(name, city):
    conn = sqlite3.connect("crm.db")
    conn.execute("INSERT INTO stores (store_name, city) VALUES (?, ?)", (name, city))
    conn.commit()
    conn.close()

def get_stores():
    conn = sqlite3.connect("crm.db")
    rows = conn.execute("SELECT store_id, store_name, city FROM stores").fetchall()
    conn.close()
    return rows

def add_customer(name, phone, email):
    conn = sqlite3.connect("crm.db")
    try:
        conn.execute("INSERT INTO customers (name, phone, email) VALUES (?, ?, ?)", (name, phone, email))
        conn.commit()
        return True
    except sqlite3.IntegrityError:
        return False
    finally:
        conn.close()

def search_customers(text):
    conn = sqlite3.connect("crm.db")
    rows = conn.execute(
        "SELECT customer_id, name, phone, email FROM customers WHERE name LIKE ? OR phone LIKE ?",
        (f"%{text}%", f"%{text}%")).fetchall()
    conn.close()
    return rows
def count_rows(table):
    if table not in ("stores", "customers", "products", "orders"):
        raise ValueError("Unknown table")
    conn = sqlite3.connect("crm.db")
    n = conn.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0]
    conn.close()
    return n

def add_product(name, price):
    conn = sqlite3.connect("crm.db")
    conn.execute("INSERT INTO products (product_name, price) VALUES (?, ?)", (name, price))
    conn.commit()
    conn.close()

def get_products():
    conn = sqlite3.connect("crm.db")
    rows = conn.execute("SELECT product_id, product_name, price FROM products").fetchall()
    conn.close()
    return rows

def get_customers():
    conn = sqlite3.connect("crm.db")
    rows = conn.execute("SELECT customer_id, name, phone FROM customers").fetchall()
    conn.close()
    return rows

def save_order(customer_id, store_id, items):
    total = sum(qty * price for _, qty, price in items)
    conn = sqlite3.connect("crm.db")
    try:
        cur = conn.execute("INSERT INTO orders (customer_id, store_id, total) VALUES (?, ?, ?)",
                           (customer_id, store_id, total))
        order_id = cur.lastrowid
        for product_id, qty, price in items:
            conn.execute("INSERT INTO order_items (order_id, product_id, quantity, unit_price) VALUES (?, ?, ?, ?)",
                         (order_id, product_id, qty, price))
        conn.commit()
        return order_id
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()

def get_orders():
    conn = sqlite3.connect("crm.db")
    rows = conn.execute("""
        SELECT o.order_id, o.order_date, c.name, s.store_name, o.total
        FROM orders o
        JOIN customers c ON o.customer_id = c.customer_id
        JOIN stores s ON o.store_id = s.store_id
        ORDER BY o.order_id DESC
    """).fetchall()
    conn.close()
    return rows

def sales_by_store():
    conn = sqlite3.connect("crm.db")
    rows = conn.execute("""
        SELECT s.store_name, COUNT(o.order_id), COALESCE(SUM(o.total), 0)
        FROM stores s
        LEFT JOIN orders o ON o.store_id = s.store_id
        GROUP BY s.store_id
    """).fetchall()
    conn.close()
    return rows

def top_customers(limit=5):
    conn = sqlite3.connect("crm.db")
    rows = conn.execute("""
        SELECT c.name, c.phone, COUNT(o.order_id), SUM(o.total)
        FROM customers c
        JOIN orders o ON o.customer_id = c.customer_id
        GROUP BY c.customer_id
        ORDER BY SUM(o.total) DESC
        LIMIT ?
    """, (limit,)).fetchall()
    conn.close()
    return rows

def import_customers(df):
    added = 0
    skipped = 0
    conn = sqlite3.connect("crm.db")
    for _, r in df.iterrows():
        name = str(r["name"]).strip()
        phone = str(r["phone"]).strip()
        email = str(r.get("email", "")).strip()
        if name == "" or not (phone.isdigit() and len(phone) == 10):
            skipped += 1
            continue
        try:
            conn.execute("INSERT INTO customers (name, phone, email) VALUES (?, ?, ?)", (name, phone, email))
            added += 1
        except sqlite3.IntegrityError:
            skipped += 1
    conn.commit()
    conn.close()
    return added, skipped


def get_customer_summary(customer_id):
    conn = sqlite3.connect("crm.db")
    row = conn.execute("""
        SELECT COUNT(order_id), COALESCE(SUM(total), 0), MAX(order_date)
        FROM orders WHERE customer_id = ?
    """, (customer_id,)).fetchone()
    conn.close()
    return row

def get_customer_orders(customer_id):
    conn = sqlite3.connect("crm.db")
    rows = conn.execute("""
        SELECT o.order_id, o.order_date, s.store_name, o.total
        FROM orders o
        JOIN stores s ON o.store_id = s.store_id
        WHERE o.customer_id = ?
        ORDER BY o.order_id DESC
    """, (customer_id,)).fetchall()
    conn.close()
    return rows

def inactive_customers(days=30):
    conn = sqlite3.connect("crm.db")
    rows = conn.execute("""
        SELECT c.name, c.phone, c.email, MAX(o.order_date) AS last_purchase,
               COUNT(o.order_id), COALESCE(SUM(o.total), 0)
        FROM customers c
        LEFT JOIN orders o ON o.customer_id = c.customer_id
        GROUP BY c.customer_id
        HAVING last_purchase IS NULL OR date(last_purchase) < date('now', ?)
        ORDER BY last_purchase
    """, (f"-{int(days)} days",)).fetchall()
    conn.close()
    return rows

def recommend_products(customer_id, limit=5):
    conn = sqlite3.connect("crm.db")
    rows = conn.execute("""
        WITH mine AS (
            SELECT DISTINCT oi.product_id
            FROM order_items oi
            JOIN orders o ON o.order_id = oi.order_id
            WHERE o.customer_id = ?
        ),
        related AS (
            SELECT DISTINCT order_id FROM order_items
            WHERE product_id IN (SELECT product_id FROM mine)
        )
        SELECT p.product_name,
               COUNT(DISTINCT oi.order_id) * 1.0 / (SELECT COUNT(*) FROM related)
        FROM order_items oi
        JOIN products p ON p.product_id = oi.product_id
        WHERE oi.order_id IN (SELECT order_id FROM related)
          AND oi.product_id NOT IN (SELECT product_id FROM mine)
        GROUP BY oi.product_id
        ORDER BY 2 DESC
        LIMIT ?
    """, (customer_id, limit)).fetchall()
    conn.close()
    return rows

def import_stores(df):
    added = 0
    skipped = 0
    conn = sqlite3.connect("crm.db")
    existing = {r[0].strip().lower() for r in conn.execute("SELECT store_name FROM stores")}
    for _, r in df.iterrows():
        name = str(r["store_name"]).strip()
        city = str(r["city"]).strip()
        if name == "" or name.lower() in existing:
            skipped += 1
            continue
        conn.execute("INSERT INTO stores (store_name, city) VALUES (?, ?)", (name, city))
        existing.add(name.lower())
        added += 1
    conn.commit()
    conn.close()
    return added, skipped


def import_products(df):
    added = 0
    skipped = 0
    conn = sqlite3.connect("crm.db")
    existing = {r[0].strip().lower() for r in conn.execute("SELECT product_name FROM products")}
    for _, r in df.iterrows():
        name = str(r["product_name"]).strip()
        try:
            price = float(str(r["price"]).strip())
        except ValueError:
            price = 0
        if name == "" or price <= 0 or name.lower() in existing:
            skipped += 1
            continue
        conn.execute("INSERT INTO products (product_name, price) VALUES (?, ?)", (name, price))
        existing.add(name.lower())
        added += 1
    conn.commit()
    conn.close()
    return added, skipped


def import_bills(df):
    import pandas as pd
    from datetime import datetime

    added = 0
    skipped = 0
    errors = []
    conn = sqlite3.connect("crm.db")
    try:
        customers = {r[1]: r[0] for r in conn.execute("SELECT customer_id, phone FROM customers")}
        stores = {r[1].strip().lower(): r[0] for r in conn.execute("SELECT store_id, store_name FROM stores")}
        products = {r[1].strip().lower(): (r[0], r[2])
                    for r in conn.execute("SELECT product_id, product_name, price FROM products")}

        for ref, group in df.groupby("bill_ref", sort=False):
            first = group.iloc[0]
            phone = str(first["phone"]).strip()
            store_name = str(first["store_name"]).strip().lower()

            if phone not in customers:
                skipped += 1
                errors.append(f"Bill {ref}: customer {phone} not found")
                continue
            if store_name not in stores:
                skipped += 1
                errors.append(f"Bill {ref}: store '{first['store_name']}' not found")
                continue

            raw_date = str(first["order_date"]).strip()
            if raw_date == "":
                date = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            else:
                try:
                    date = pd.to_datetime(raw_date).strftime("%Y-%m-%d %H:%M:%S")
                except Exception:
                    skipped += 1
                    errors.append(f"Bill {ref}: invalid date '{raw_date}'")
                    continue

            items = []
            ok = True
            for _, r in group.iterrows():
                pname = str(r["product_name"]).strip().lower()
                try:
                    qty = int(float(str(r["quantity"]).strip()))
                except ValueError:
                    qty = 0
                if pname not in products or qty <= 0:
                    ok = False
                    errors.append(f"Bill {ref}: bad product or quantity ('{r['product_name']}', '{r['quantity']}')")
                    break
                pid, price = products[pname]
                items.append((pid, qty, price))
            if not ok:
                skipped += 1
                continue

            cid = customers[phone]
            sid = stores[store_name]
            dup = conn.execute(
                "SELECT 1 FROM orders WHERE customer_id = ? AND store_id = ? AND order_date = ?",
                (cid, sid, date)).fetchone()
            if dup:
                skipped += 1
                errors.append(f"Bill {ref}: already exists")
                continue

            total = sum(q * p for _, q, p in items)
            cur = conn.execute(
                "INSERT INTO orders (customer_id, store_id, order_date, total) VALUES (?, ?, ?, ?)",
                (cid, sid, date, total))
            oid = cur.lastrowid
            for pid, qty, price in items:
                conn.execute(
                    "INSERT INTO order_items (order_id, product_id, quantity, unit_price) VALUES (?, ?, ?, ?)",
                    (oid, pid, qty, price))
            added += 1
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()
    return added, skipped, errors


def delete_store(store_id):
    conn = sqlite3.connect("crm.db")
    n = conn.execute("SELECT COUNT(*) FROM orders WHERE store_id = ?", (store_id,)).fetchone()[0]
    if n > 0:
        conn.close()
        return False, f"Cannot delete: this store has {n} bill(s). Delete those bills first."
    conn.execute("DELETE FROM stores WHERE store_id = ?", (store_id,))
    conn.commit()
    conn.close()
    return True, "Store deleted."


def delete_product(product_id):
    conn = sqlite3.connect("crm.db")
    n = conn.execute("SELECT COUNT(*) FROM order_items WHERE product_id = ?", (product_id,)).fetchone()[0]
    if n > 0:
        conn.close()
        return False, f"Cannot delete: this product is used in {n} bill item(s). Delete those bills first."
    conn.execute("DELETE FROM products WHERE product_id = ?", (product_id,))
    conn.commit()
    conn.close()
    return True, "Product deleted."


def delete_customer(customer_id):
    conn = sqlite3.connect("crm.db")
    n = conn.execute("SELECT COUNT(*) FROM orders WHERE customer_id = ?", (customer_id,)).fetchone()[0]
    if n > 0:
        conn.close()
        return False, f"Cannot delete: this customer has {n} bill(s). Delete those bills first."
    conn.execute("DELETE FROM customers WHERE customer_id = ?", (customer_id,))
    conn.commit()
    conn.close()
    return True, "Customer deleted."


def delete_order(order_id):
    conn = sqlite3.connect("crm.db")
    try:
        conn.execute("DELETE FROM order_items WHERE order_id = ?", (order_id,))
        conn.execute("DELETE FROM orders WHERE order_id = ?", (order_id,))
        conn.commit()
        return True, "Bill deleted."
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()