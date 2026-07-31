"""Idempotent development seed script for CBO.

Usage:
    python scripts/seed.py

Requires the API to be running at http://localhost:8000.
Records that already exist are skipped, so the script is safe to run repeatedly.
"""

import json
import urllib.error
import urllib.request

API_BASE = "http://localhost:8000"

ADMIN_EMAIL = "admin@cbo.local"
ADMIN_PASSWORD = "password123"
ADMIN_NAME = "Store Owner"

CATEGORIES = ["Grains", "Beverages", "Dairy", "Oils & Ghee", "Household", "Snacks"]

PRODUCTS = [
    {"name": "Super Basmati Rice 5kg", "sku": "GRN-RICE-05", "category": "Grains", "unit": "Pack", "purchase_price": 1250, "selling_price": 1600, "stock_quantity": 45, "minimum_stock": 10},
    {"name": "Coca Cola 1.5L Bottle", "sku": "BEV-COKE-15", "category": "Beverages", "unit": "Piece", "purchase_price": 120, "selling_price": 180, "stock_quantity": 120, "minimum_stock": 25},
    {"name": "Full Cream Milk 1L", "sku": "DRY-MILK-01", "category": "Dairy", "unit": "Litre", "purchase_price": 110, "selling_price": 150, "stock_quantity": 8, "minimum_stock": 15},
    {"name": "Whole Wheat Flour 10kg", "sku": "GRN-FLOU-10", "category": "Grains", "unit": "Pack", "purchase_price": 800, "selling_price": 1120, "stock_quantity": 30, "minimum_stock": 10},
    {"name": "Refined Cooking Oil 3L", "sku": "OIL-COOK-03", "category": "Oils & Ghee", "unit": "Litre", "purchase_price": 650, "selling_price": 900, "stock_quantity": 5, "minimum_stock": 12},
    {"name": "Lipton Yellow Label Tea 500g", "sku": "BEV-TEA-500", "category": "Beverages", "unit": "Pack", "purchase_price": 420, "selling_price": 600, "stock_quantity": 60, "minimum_stock": 15},
    {"name": "White Refined Sugar 5kg", "sku": "GRN-SUGA-05", "category": "Grains", "unit": "Pack", "purchase_price": 480, "selling_price": 650, "stock_quantity": 85, "minimum_stock": 20},
    {"name": "Unsalted Butter 200g", "sku": "DRY-BUTT-20", "category": "Dairy", "unit": "Piece", "purchase_price": 200, "selling_price": 280, "stock_quantity": 18, "minimum_stock": 10},
    {"name": "Dishwashing Liquid 750ml", "sku": "HSH-DISH-75", "category": "Household", "unit": "Bottle", "purchase_price": 250, "selling_price": 370, "stock_quantity": 4, "minimum_stock": 8},
    {"name": "Potato Chips Salted 150g", "sku": "SNK-CHIP-15", "category": "Snacks", "unit": "Pack", "purchase_price": 80, "selling_price": 140, "stock_quantity": 110, "minimum_stock": 30},
]

CUSTOMERS = [
    {"name": "Ali Hassan", "phone": "+92 300 1234567", "address": "12 Top Commercial Area, Gulberg, Lahore"},
    {"name": "Fatima Zahra", "phone": "+92 321 9876543", "address": "House 45, Sector F-7, Islamabad"},
    {"name": "Muhammad Usman", "phone": "+92 333 4567890", "address": "78 Clifton Block 5, Karachi"},
    {"name": "Ayesha Khan", "phone": "+92 301 5551234", "address": "Plot 12B, Model Town, Multan"},
    {"name": "Tariq Mahmood", "phone": "+92 345 6789012", "address": "University Road, Peshawar"},
    {"name": "Zainab Malik", "phone": "+92 312 3456789", "address": "DHA Phase 6, Karachi"},
    {"name": "Bilal Ahmed", "phone": "+92 302 8887766", "address": "Satellite Town, Rawalpindi"},
    {"name": "Sana Iqbal", "phone": "+92 323 1122334", "address": "Jinnah Colony, Faisalabad"},
    {"name": "Hamza Raza", "phone": "+92 334 9988776", "address": "Cantonment Area, Quetta"},
    {"name": "Maryam Nawaz", "phone": "+92 305 4433221", "address": "Johar Town Phase 2, Lahore"},
]

PURCHASES = [
    {"product_name": "Super Basmati Rice 5kg", "supplier_name": "Punjab Agro Mills", "quantity": 50, "purchase_price": 1250, "total_amount": 62500, "purchase_date": "2026-07-20T09:00:00Z", "notes": "Bulk seasonal restock"},
    {"product_name": "Coca Cola 1.5L Bottle", "supplier_name": "Beverage Traders Ltd", "quantity": 150, "purchase_price": 120, "total_amount": 18000, "purchase_date": "2026-07-21T11:30:00Z", "notes": "Weekly beverage shipment"},
    {"product_name": "Full Cream Milk 1L", "supplier_name": "Fresh Dairy Farms", "quantity": 60, "purchase_price": 110, "total_amount": 6600, "purchase_date": "2026-07-22T07:30:00Z", "notes": "Fresh stock shipment"},
    {"product_name": "Whole Wheat Flour 10kg", "supplier_name": "Al-Barkat Flour Mills", "quantity": 40, "purchase_price": 800, "total_amount": 32000, "purchase_date": "2026-07-23T14:00:00Z", "notes": "Grain inventory order"},
    {"product_name": "Refined Cooking Oil 3L", "supplier_name": "Habib Oil Industries", "quantity": 25, "purchase_price": 650, "total_amount": 16250, "purchase_date": "2026-07-24T10:20:00Z", "notes": "Oil drum replenishment"},
    {"product_name": "Lipton Yellow Label Tea 500g", "supplier_name": "Unilever Wholesale", "quantity": 80, "purchase_price": 420, "total_amount": 33600, "purchase_date": "2026-07-25T13:15:00Z", "notes": "Tea crates restock"},
    {"product_name": "White Refined Sugar 5kg", "supplier_name": "Chiniot Sugar Mills", "quantity": 100, "purchase_price": 480, "total_amount": 48000, "purchase_date": "2026-07-26T09:45:00Z", "notes": "Sugar bags lot"},
    {"product_name": "Unsalted Butter 200g", "supplier_name": "Fresh Dairy Farms", "quantity": 30, "purchase_price": 200, "total_amount": 6000, "purchase_date": "2026-07-27T08:10:00Z", "notes": "Cold storage dairy stock"},
    {"product_name": "Dishwashing Liquid 750ml", "supplier_name": "Consumer Goods Co", "quantity": 20, "purchase_price": 250, "total_amount": 5000, "purchase_date": "2026-07-28T12:00:00Z", "notes": "Hygiene supplies"},
    {"product_name": "Potato Chips Salted 150g", "supplier_name": "Lays Snack Distribution", "quantity": 120, "purchase_price": 80, "total_amount": 9600, "purchase_date": "2026-07-29T10:00:00Z", "notes": "Confectionery carton box"},
]

SALES = [
    {"customer_name": "Ali Hassan", "product_name": "Super Basmati Rice 5kg", "quantity": 3, "unit_price": 1600, "total_amount": 4800, "sale_date": "2026-07-28T16:20:00Z", "notes": "Paid in cash"},
    {"customer_name": "Fatima Zahra", "product_name": "Coca Cola 1.5L Bottle", "quantity": 12, "unit_price": 180, "total_amount": 2160, "sale_date": "2026-07-28T17:45:00Z", "notes": "Party order via WhatsApp"},
    {"customer_name": "Muhammad Usman", "product_name": "Whole Wheat Flour 10kg", "quantity": 2, "unit_price": 1120, "total_amount": 2240, "sale_date": "2026-07-28T18:10:00Z", "notes": "Card payment"},
    {"customer_name": "Ayesha Khan", "product_name": "Lipton Yellow Label Tea 500g", "quantity": 4, "unit_price": 600, "total_amount": 2400, "sale_date": "2026-07-29T09:30:00Z", "notes": "Regular grocery pickup"},
    {"customer_name": "Tariq Mahmood", "product_name": "Refined Cooking Oil 3L", "quantity": 2, "unit_price": 900, "total_amount": 1800, "sale_date": "2026-07-29T10:15:00Z", "notes": "Home delivery"},
    {"customer_name": "Zainab Malik", "product_name": "White Refined Sugar 5kg", "quantity": 5, "unit_price": 650, "total_amount": 3250, "sale_date": "2026-07-29T11:00:00Z", "notes": "Bakery batch purchase"},
    {"customer_name": "Bilal Ahmed", "product_name": "Potato Chips Salted 150g", "quantity": 10, "unit_price": 140, "total_amount": 1400, "sale_date": "2026-07-29T12:20:00Z", "notes": "Snacks restock"},
    {"customer_name": "Sana Iqbal", "product_name": "Full Cream Milk 1L", "quantity": 6, "unit_price": 150, "total_amount": 900, "sale_date": "2026-07-29T13:00:00Z", "notes": "Daily morning order"},
    {"customer_name": "Hamza Raza", "product_name": "Unsalted Butter 200g", "quantity": 3, "unit_price": 280, "total_amount": 840, "sale_date": "2026-07-29T14:15:00Z", "notes": "Counter purchase"},
    {"customer_name": "Maryam Nawaz", "product_name": "Dishwashing Liquid 750ml", "quantity": 2, "unit_price": 370, "total_amount": 740, "sale_date": "2026-07-29T15:00:00Z", "notes": "Household cleaning supplies"},
]

EXPENSES = [
    {"title": "July Store Electricity Bill", "category": "Electricity", "amount": 24500, "expense_date": "2026-07-25T08:00:00Z", "notes": "LESCO bill payment online"},
    {"title": "High-Speed Fiber Internet", "category": "Internet", "amount": 4500, "expense_date": "2026-07-26T09:30:00Z", "notes": "Monthly broadband subscription"},
    {"title": "Goods Delivery Transport Fare", "category": "Transport", "amount": 6500, "expense_date": "2026-07-26T14:15:00Z", "notes": "Rickshaw cargo transport from wholesale market"},
    {"title": "Store Assistant Weekly Salary", "category": "Salary", "amount": 18000, "expense_date": "2026-07-27T17:00:00Z", "notes": "Helper wage for July Week 4"},
    {"title": "Packaging Tape & Plastic Bags", "category": "Miscellaneous", "amount": 2500, "expense_date": "2026-07-28T10:00:00Z", "notes": "Store counter packing items"},
    {"title": "Water Cooler Maintenance", "category": "Miscellaneous", "amount": 3500, "expense_date": "2026-07-28T12:45:00Z", "notes": "Filter change for customer drinking water"},
    {"title": "Fuel for Delivery Scooter", "category": "Transport", "amount": 3000, "expense_date": "2026-07-28T16:20:00Z", "notes": "Home delivery fuel allowance"},
    {"title": "Generator Backup Diesel", "category": "Electricity", "amount": 8500, "expense_date": "2026-07-29T08:15:00Z", "notes": "Emergency power backup during outage"},
    {"title": "Printing Paper & Receipts", "category": "Miscellaneous", "amount": 1850, "expense_date": "2026-07-29T11:00:00Z", "notes": "POS thermal receipt paper rolls"},
    {"title": "Part-Time Stocker Salary", "category": "Salary", "amount": 12000, "expense_date": "2026-07-29T15:30:00Z", "notes": "Night shift stocking payout"},
]


class SeedError(Exception):
    pass


def api(method, path, token=None, body=None):
    url = f"{API_BASE}{path}"
    headers = {"Content-Type": "application/json"}
    if token:
        headers["Authorization"] = f"Bearer {token}"
    data = json.dumps(body).encode() if body is not None else None
    req = urllib.request.Request(url, data=data, headers=headers, method=method)
    try:
        with urllib.request.urlopen(req) as resp:
            if resp.status == 204:
                return None
            return json.loads(resp.read().decode())
    except urllib.error.HTTPError as exc:
        raise SeedError(f"{method} {path} -> {exc.code}: {exc.read().decode()}") from exc
    except urllib.error.URLError as exc:
        raise SeedError(
            f"API not reachable at {API_BASE} ({exc.reason}). Start the backend first."
        ) from exc


def login_or_register() -> str:
    try:
        token = api("POST", "/auth/login", body={"email": ADMIN_EMAIL, "password": ADMIN_PASSWORD})["access_token"]
    except SeedError:
        api("POST", "/auth/register", body={"email": ADMIN_EMAIL, "password": ADMIN_PASSWORD, "name": ADMIN_NAME})
        token = api("POST", "/auth/login", body={"email": ADMIN_EMAIL, "password": ADMIN_PASSWORD})["access_token"]
    return token


def seed_categories(token):
    existing = {c["name"] for c in api("GET", "/categories", token=token)}
    for name in CATEGORIES:
        if name in existing:
            print(f"  skip category: {name}")
            continue
        api("POST", "/categories", token=token, body={"name": name})
        print(f"  created category: {name}")


def seed_products(token):
    existing = {p["sku"] for p in api("GET", "/products", token=token)}
    for product in PRODUCTS:
        if product["sku"] in existing:
            print(f"  skip product: {product['name']}")
            continue
        api("POST", "/products", token=token, body=product)
        print(f"  created product: {product['name']}")


def seed_customers(token):
    existing = {c["phone"] for c in api("GET", "/customers", token=token)}
    for customer in CUSTOMERS:
        if customer["phone"] in existing:
            print(f"  skip customer: {customer['name']}")
            continue
        api("POST", "/customers", token=token, body=customer)
        print(f"  created customer: {customer['name']}")


def id_by_name(items, name):
    try:
        return items[name]
    except KeyError as exc:
        raise SeedError(f"Missing seed record: {name}. Run the full seed script in order.") from exc


def seed_purchases(token, products):
    if api("GET", "/purchases", token=token):
        print("  skip purchases: records already exist")
        return
    for p in PURCHASES:
        body = {k: v for k, v in p.items() if k != "product_name"}
        body["product_id"] = id_by_name(products, p["product_name"])
        api("POST", "/purchases", token=token, body=body)
        print(f"  created purchase: {p['supplier_name']}")


def seed_sales(token, products, customers):
    if api("GET", "/sales", token=token):
        print("  skip sales: records already exist")
        return
    for s in SALES:
        body = {k: v for k, v in s.items() if k not in ("product_name", "customer_name")}
        body["product_id"] = id_by_name(products, s["product_name"])
        if s.get("customer_name"):
            body["customer_id"] = id_by_name(customers, s["customer_name"])
        api("POST", "/sales", token=token, body=body)
        print(f"  created sale: {s['customer_name']} -> {s['product_name']}")


def seed_expenses(token):
    if api("GET", "/expenses", token=token):
        print("  skip expenses: records already exist")
        return
    for e in EXPENSES:
        api("POST", "/expenses", token=token, body=e)
        print(f"  created expense: {e['title']}")


def get_product_ids(token):
    return {p["name"]: p["id"] for p in api("GET", "/products", token=token)}


def get_customer_ids(token):
    return {c["name"]: c["id"] for c in api("GET", "/customers", token=token)}


def main():
    try:
        token = login_or_register()
    except SeedError as exc:
        print(f"ERROR: {exc}")
        return

    print("Seeding categories...")
    seed_categories(token)
    print("Seeding products...")
    seed_products(token)
    print("Seeding customers...")
    seed_customers(token)

    products = get_product_ids(token)
    customers = get_customer_ids(token)

    print("Seeding purchases...")
    seed_purchases(token, products)
    print("Seeding sales...")
    seed_sales(token, products, customers)
    print("Seeding expenses...")
    seed_expenses(token)

    print("\nDone!")


if __name__ == "__main__":
    main()
