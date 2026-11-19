import streamlit as st
import pandas as pd
from db import get_customer_summary, get_customer_orders, inactive_customers, recommend_products
from db import (init_db, add_store, get_stores, add_customer, search_customers,
                count_rows, add_product, get_products, get_customers,
                save_order, get_orders, sales_by_store, top_customers,
                import_customers)
from db import import_stores, import_products, import_bills
from db import delete_store, delete_product, delete_customer, delete_order
from db import clear_all_data

st.set_page_config(page_title="UniStore CRM", page_icon="🛍️", layout="wide")
init_db()

st.sidebar.title("UniStore CRM")
page = st.sidebar.radio("Menu", ["Dashboard", "Stores", "Customers", "Products", "Bills", "Customer Insights", "Import Data"])

if page == "Dashboard":
    st.title("Dashboard")
    c1, c2, c3 = st.columns(3)
    c1.metric("Stores", count_rows("stores"))
    c2.metric("Customers", count_rows("customers"))
    c3.metric("Bills", count_rows("orders"))

    st.subheader("Sales by store")
    sales = pd.DataFrame(sales_by_store(), columns=["Store", "Bills", "Sales (Rs)"])
    st.bar_chart(sales.set_index("Store")["Sales (Rs)"])
    st.dataframe(sales, hide_index=True)

    st.subheader("Top 5 customers")
    top = pd.DataFrame(top_customers(), columns=["Name", "Phone", "Bills", "Total spent (Rs)"])
    st.dataframe(top, hide_index=True)

elif page == "Stores":
    st.title("Stores")
    left, right = st.columns(2)
    with left:
        st.subheader("Add a store")
        name = st.text_input("Store name")
        city = st.text_input("City")
        if st.button("Save store"):
            if name.strip() == "":
                st.error("Store name is required.")
            else:
                add_store(name.strip(), city.strip())
                st.success("Store saved.")
    with right:
        st.subheader("All stores")
        st.dataframe(pd.DataFrame(get_stores(), columns=["ID", "Store name", "City"]), hide_index=True)
        
    st.divider()
    st.subheader("Delete a store")
    if st.session_state.get("flash_store"):
        st.success(st.session_state.pop("flash_store"))
    store_list = get_stores()
    if store_list:
        del_store = st.selectbox("Choose a store to delete", store_list,
                                 format_func=lambda s: f"{s[1]} ({s[2]})", key="del_store")
        sure = st.checkbox("I am sure", key="sure_store")
        if st.button("Delete store"):
            if not sure:
                st.error("Tick 'I am sure' first.")
            else:
                ok, msg = delete_store(del_store[0])
                if ok:
                    st.session_state["flash_store"] = msg
                    st.rerun()
                else:
                    st.error(msg)

elif page == "Customers":
    st.title("Customers")
    left, right = st.columns(2)
    with left:
        st.subheader("Add a customer")
        c_name = st.text_input("Customer name")
        c_phone = st.text_input("Phone (10 digits)")
        c_email = st.text_input("Email (optional)")
        if st.button("Save customer"):
            if c_name.strip() == "" or not (c_phone.isdigit() and len(c_phone) == 10):
                st.error("Enter a name and a 10-digit phone number.")
            elif add_customer(c_name.strip(), c_phone, c_email.strip()):
                st.success("Customer saved.")
            else:
                st.error("This phone number already exists.")
    with right:
        st.subheader("Search customers")
        q = st.text_input("Search by name or phone")
        st.dataframe(pd.DataFrame(search_customers(q), columns=["ID", "Name", "Phone", "Email"]), hide_index=True)
    st.divider()
    st.subheader("Delete a customer")
    if st.session_state.get("flash_cust"):
        st.success(st.session_state.pop("flash_cust"))
    cust_list = get_customers()
    if cust_list:
        del_cust = st.selectbox("Choose a customer to delete", cust_list,
                                format_func=lambda c: f"{c[1]} ({c[2]})", key="del_cust")
        sure = st.checkbox("I am sure", key="sure_cust")
        if st.button("Delete customer"):
            if not sure:
                st.error("Tick 'I am sure' first.")
            else:
                ok, msg = delete_customer(del_cust[0])
                if ok:
                    st.session_state["flash_cust"] = msg
                    st.rerun()
                else:
                    st.error(msg)
    
elif page == "Products":
    st.title("Products")
    left, right = st.columns(2)
    with left:
        st.subheader("Add a product")
        p_name = st.text_input("Product name")
        p_price = st.number_input("Price (Rs)", min_value=0.0, step=1.0)
        if st.button("Save product"):
            if p_name.strip() == "" or p_price <= 0:
                st.error("Enter a product name and a price above 0.")
            else:
                add_product(p_name.strip(), p_price)
                st.success("Product saved.")
    with right:
        st.subheader("All products")
        st.dataframe(pd.DataFrame(get_products(), columns=["ID", "Product", "Price"]), hide_index=True)
    st.divider()
    st.subheader("Delete a product")
    if st.session_state.get("flash_prod"):
        st.success(st.session_state.pop("flash_prod"))
    prod_list = get_products()
    if prod_list:
        del_prod = st.selectbox("Choose a product to delete", prod_list,
                                format_func=lambda p: f"{p[1]} (Rs {p[2]})", key="del_prod")
        sure = st.checkbox("I am sure", key="sure_prod")
        if st.button("Delete product"):
            if not sure:
                st.error("Tick 'I am sure' first.")
            else:
                ok, msg = delete_product(del_prod[0])
                if ok:
                    st.session_state["flash_prod"] = msg
                    st.rerun()
                else:
                    st.error(msg)


elif page == "Bills":
    st.title("New bill")
    stores = get_stores()
    customers = get_customers()
    products = get_products()
    if not stores or not customers or not products:
        st.warning("Add at least one store, one customer and one product first.")
    else:
        store_choice = st.selectbox("Store", stores, format_func=lambda s: s[1])
        cust_choice = st.selectbox("Customer", customers, format_func=lambda c: f"{c[1]} ({c[2]})")
        st.subheader("Quantities")
        items = []
        for pid, pname, price in products:
            qty = st.number_input(f"{pname} (Rs {price})", min_value=0, step=1, key=f"qty_{pid}")
            if qty > 0:
                items.append((pid, qty, price))
        if st.button("Save bill"):
            if not items:
                st.error("Choose at least one product.")
            else:
                oid = save_order(cust_choice[0], store_choice[0], items)
                st.success(f"Bill {oid} saved.")
    st.subheader("Recent bills")
    st.dataframe(pd.DataFrame(get_orders(), columns=["Bill", "Date", "Customer", "Store", "Total"]), hide_index=True)
    
    st.divider()
    st.subheader("Delete a bill")
    if st.session_state.get("flash_bill"):
        st.success(st.session_state.pop("flash_bill"))
    bill_list = get_orders()
    if bill_list:
        del_bill = st.selectbox("Choose a bill to delete", bill_list,
                                format_func=lambda b: f"Bill {b[0]} | {str(b[1])[:10]} | {b[2]} | Rs {b[4]}",
                                key="del_bill")
        sure = st.checkbox("I am sure", key="sure_bill")
        if st.button("Delete bill"):
            if not sure:
                st.error("Tick 'I am sure' first.")
            else:
                ok, msg = delete_order(del_bill[0])
                st.session_state["flash_bill"] = msg
                st.rerun()  
    
    
elif page == "Customer Insights":
    st.title("Customer Insights")
    tab1, tab2, tab3 = st.tabs(["Customer profile", "Inactive customers", "Next product"])
    
    with tab1:
        customers = get_customers()
        if not customers:
            st.info("No customers yet.")
        else:
            choice = st.selectbox("Select a customer", customers,
                                  format_func=lambda c: f"{c[1]} ({c[2]})")
            bills, spent, last = get_customer_summary(choice[0])
            m1, m2, m3 = st.columns(3)
            m1.metric("Total bills", bills)
            m2.metric("Total spent (Rs)", f"{spent:,.2f}")
            m3.metric("Last purchase", str(last)[:10] if last else "Never")
            st.subheader("Bill history")
            st.dataframe(pd.DataFrame(get_customer_orders(choice[0]),
                         columns=["Bill", "Date", "Store", "Total"]), hide_index=True)

    with tab2:
        days = st.number_input("No purchase in the last (days)", min_value=1, value=30, step=1)
        inactive = pd.DataFrame(inactive_customers(days),
                   columns=["Name", "Phone", "Email", "Last purchase", "Bills", "Total spent (Rs)"])
        st.write(f"{len(inactive)} customers to follow up with")
        st.dataframe(inactive, hide_index=True)
        
        
    with tab3:
        all_customers = get_customers()
        if not all_customers:
            st.info("No customers yet.")
        else:
            pick = st.selectbox("Select a customer", all_customers,
                                format_func=lambda c: f"{c[1]} ({c[2]})",
                                key="reco_customer")
            recs = recommend_products(pick[0])
            if not recs:
                st.info("Not enough purchase history for this customer yet.")
            else:
                st.write("Products often bought together with this customer's past purchases:")
                reco = pd.DataFrame(recs, columns=["Product", "Likelihood score"])
                reco["Likelihood score"] = (reco["Likelihood score"] * 100).round(1).astype(str) + " %"
                st.dataframe(reco, hide_index=True)
                
                
elif page == "Import Data":
    st.title("Import Data")
    st.write("Import in this order: Stores, Products, Customers, then Bills.")

    def read_csv(file):
        df = pd.read_csv(file, dtype=str).fillna("")
        df.columns = [c.strip().lower() for c in df.columns]
        return df

    t1, t2, t3, t4 = st.tabs(["Stores", "Products", "Customers", "Bills"])

    with t1:
        st.caption("Columns: store_name, city")
        f = st.file_uploader("Stores CSV", type="csv", key="imp_stores")
        if f is not None:
            df = read_csv(f).rename(columns={"name": "store_name", "store": "store_name", "branch": "store_name"})
            st.dataframe(df.head(10), hide_index=True)
            if "store_name" not in df.columns:
                st.error("The file needs a store_name column.")
            elif st.button("Import stores"):
                if "city" not in df.columns:
                    df["city"] = ""
                added, skipped = import_stores(df)
                st.success(f"Added {added}, skipped {skipped}.")

    with t2:
        st.caption("Columns: product_name, price")
        f = st.file_uploader("Products CSV", type="csv", key="imp_products")
        if f is not None:
            df = read_csv(f).rename(columns={"name": "product_name", "product": "product_name",
                                             "item": "product_name", "rate": "price", "mrp": "price"})
            st.dataframe(df.head(10), hide_index=True)
            if "product_name" not in df.columns or "price" not in df.columns:
                st.error("The file needs the columns: product_name, price")
            elif st.button("Import products"):
                added, skipped = import_products(df)
                st.success(f"Added {added}, skipped {skipped}.")

    with t3:
        st.caption("Columns: name, phone, email (optional)")
        f = st.file_uploader("Customers CSV", type="csv", key="imp_customers")
        if f is not None:
            df = read_csv(f).rename(columns={"mail": "email", "e-mail": "email", "email id": "email",
                                             "mobile": "phone", "phone number": "phone",
                                             "customer name": "name"})
            st.dataframe(df.head(10), hide_index=True)
            if "name" not in df.columns or "phone" not in df.columns:
                st.error("The file needs the columns: name, phone")
            elif st.button("Import customers"):
                if "email" not in df.columns:
                    df["email"] = ""
                added, skipped = import_customers(df)
                st.success(f"Added {added}, skipped {skipped}.")

    with t4:
        st.caption("Columns: bill_ref, phone, store_name, order_date (optional), product_name, quantity. "
                   "One row per item. Rows with the same bill_ref form one bill.")
        f = st.file_uploader("Bills CSV", type="csv", key="imp_bills")
        if f is not None:
            df = read_csv(f).rename(columns={"bill": "bill_ref", "bill no": "bill_ref", "invoice": "bill_ref",
                                             "mobile": "phone", "store": "store_name", "date": "order_date",
                                             "product": "product_name", "item": "product_name",
                                             "qty": "quantity"})
            st.dataframe(df.head(10), hide_index=True)
            needed = ["bill_ref", "phone", "store_name", "product_name", "quantity"]
            missing = [c for c in needed if c not in df.columns]
            if missing:
                st.error("Missing columns: " + ", ".join(missing))
            elif st.button("Import bills"):
                if "order_date" not in df.columns:
                    df["order_date"] = ""
                added, skipped, errors = import_bills(df)
                st.success(f"Added {added} bills, skipped {skipped}.")
                if errors:
                    with st.expander("Why some bills were skipped"):
                        for e in errors[:20]:
                            st.write(e)
                            
            st.divider()
    st.subheader("Start fresh")
    st.warning("This deletes ALL stores, customers, products and bills. It cannot be undone.")
    confirm = st.text_input("Type DELETE to confirm", key="clear_confirm")
    if st.button("Clear all data"):
        if confirm == "DELETE":
            clear_all_data()
            st.success("All data cleared. You can now import your own files.")
        else:
            st.error("Type DELETE exactly to confirm.")