import random
import sqlite3
from datetime import datetime, timedelta

import pandas as pd
from faker import Faker

from db import init_db, count_rows, get_stores, get_customers, get_products, save_order

fake = Faker("en_IN")
Faker.seed(1)
random.seed(1)

init_db()
if count_rows("customers") > 0:
    print("Sample data already exists. Delete crm.db to start again.")
    raise SystemExit

conn = sqlite3.connect("crm.db")

stores = pd.DataFrame({
    "store_name": ["UniStore Chennai", "UniStore Coimbatore", "UniStore Madurai"],
    "city": ["Chennai", "Coimbatore", "Madurai"],
})
stores.to_sql("stores", conn, if_exists="append", index=False)

phones = random.sample(range(6000000000, 9999999999), 30)
customers = pd.DataFrame({
    "name": [fake.name() for _ in range(30)],
    "phone": [str(p) for p in phones],
    "email": [fake.email() for _ in range(30)],
})
customers.to_sql("customers", conn, if_exists="append", index=False)

products = pd.DataFrame({
    "product_name": ["Shirt", "Jeans", "Belt", "Saree", "Dupatta", "T-shirt",
                     "Rice 5kg", "Cooking oil 1L", "Soap", "Biscuits", "Notebook", "Pen"],
    "price": [500, 900, 300, 1200, 400, 400, 350, 140, 40, 30, 60, 10],
})
products.to_sql("products", conn, if_exists="append", index=False)
conn.close()

store_ids = [s[0] for s in get_stores()]
customer_ids = [c[0] for c in get_customers()]
product_rows = get_products()

conn = sqlite3.connect("crm.db")
for _ in range(60):
    chosen = random.sample(product_rows, random.randint(1, 4))
    items = [(p[0], random.randint(1, 3), p[2]) for p in chosen]
    order_id = save_order(random.choice(customer_ids), random.choice(store_ids), items)
    day = datetime.now() - timedelta(days=random.randint(0, 60))
    conn.execute("UPDATE orders SET order_date = ? WHERE order_id = ?",
                 (day.strftime("%Y-%m-%d %H:%M:%S"), order_id))
    conn.commit()
conn.commit()
conn.close()

print("Done: sample data created.")