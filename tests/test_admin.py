"""
End-to-end test for the admin API.

Prerequisites:
    - API running at http://127.0.0.1:8000 (uvicorn app.main:app --reload)
    - At least one product in the stock (run the seed scripts if needed)

Usage:
    ADMIN_PASSWORD=yourpassword python -m scripts.test_admin

Optional env vars:
    API_BASE          default http://127.0.0.1:8000
    ADMIN_USERNAME    default "admin"
    ADMIN_PASSWORD    required
"""

import os
import sys

import requests


BASE = os.getenv("API_BASE", "http://127.0.0.1:8000")
API = f"{BASE}/api/v1"
USERNAME = os.getenv("ADMIN_USERNAME", "admin")
PASSWORD = os.getenv("ADMIN_PASSWORD", "")


# ---------------------------------------------------------------- helpers

class TestRunner:
    def __init__(self):
        self.passed = 0
        self.failed = 0
        self.failures: list[str] = []

    def check(self, name: str, ok: bool, detail: str = "") -> None:
        if ok:
            self.passed += 1
            print(f"  PASS  {name}")
        else:
            self.failed += 1
            self.failures.append(name)
            print(f"  FAIL  {name}")
            if detail:
                print(f"        {detail}")

    def summary(self) -> int:
        print()
        print(f"=== {self.passed} passed, {self.failed} failed ===")
        if self.failures:
            print("\nFailures:")
            for f in self.failures:
                print(f"  - {f}")
            return 1
        return 0


def auth(token: str) -> dict:
    return {"Authorization": f"Bearer {token}"}


def phase(title: str) -> None:
    print()
    print(f"--- {title} ---")


# ---------------------------------------------------------------- tests

def main() -> int:
    if not PASSWORD:
        print("ERROR: set ADMIN_PASSWORD env var before running.", file=sys.stderr)
        print("  ADMIN_PASSWORD=yourpassword python -m scripts.test_admin", file=sys.stderr)
        return 1

    r = TestRunner()
    token = None

    # ============================================================ 1. LOGIN
    phase("1. Login")

    # 1a. empty body
    resp = requests.post(f"{API}/admin/login", json={})
    r.check("login with empty body -> 422", resp.status_code == 422, f"got {resp.status_code}")

    # 1b. empty username
    resp = requests.post(f"{API}/admin/login",
                         json={"username": "", "password": PASSWORD})
    r.check("login with empty username -> 422", resp.status_code == 422, f"got {resp.status_code}")

    # 1c. wrong password
    resp = requests.post(f"{API}/admin/login",
                         json={"username": USERNAME, "password": "definitely-wrong"})
    r.check("login wrong password -> 401", resp.status_code == 401, f"got {resp.status_code}")

    # 1d. wrong username
    resp = requests.post(f"{API}/admin/login",
                         json={"username": "not-admin", "password": PASSWORD})
    r.check("login wrong username -> 401", resp.status_code == 401, f"got {resp.status_code}")

    # 1e. correct
    resp = requests.post(f"{API}/admin/login",
                         json={"username": USERNAME, "password": PASSWORD})
    r.check("login correct -> 200", resp.status_code == 200, f"got {resp.status_code}")
    if resp.status_code == 200:
        body = resp.json()
        token = body.get("access_token")
        r.check("response has access_token", bool(token))
        r.check("response has token_type=bearer", body.get("token_type") == "bearer")
        r.check("response has expires_in", isinstance(body.get("expires_in"), int))

    if not token:
        print("\nCannot continue without a token.")
        return r.summary()

    # ==================================================== 2. AUTH GUARD
    phase("2. Auth protection")

    resp = requests.get(f"{API}/admin/orders")
    r.check("GET /admin/orders no token -> 401", resp.status_code == 401, f"got {resp.status_code}")

    resp = requests.get(f"{API}/admin/orders",
                        headers={"Authorization": "Bearer not-a-real-token"})
    r.check("GET /admin/orders bad token -> 401", resp.status_code == 401, f"got {resp.status_code}")

    resp = requests.get(f"{API}/admin/orders", headers=auth(token))
    r.check("GET /admin/orders good token -> 200", resp.status_code == 200, f"got {resp.status_code}")

    # ==================================================== 3. GET PRODUCT
    phase("3. Fetch a product to use in orders")

    resp = requests.get(f"{API}/products?page_size=1")
    r.check("GET /products -> 200", resp.status_code == 200, f"got {resp.status_code}")
    if resp.status_code != 200 or not resp.json().get("items"):
        print("\nNo products in stock. Seed the DB first.")
        return r.summary()

    product = resp.json()["items"][0]
    cat = product["category"]
    pid = product["id"]
    print(f"       using product: category={cat} id={pid} name={product['name']}")

    # ==================================================== 4. CREATE ORDER
    phase("4. Create test order (public)")

    order_payload = {
        "customer": {
            "full_name": "TEST SCRIPT — DELETE ME",
            "phone": "+213555000000",
            "email": "test@example.com",
            "wilaya": "Alger",
            "city": "Alger",
            "notes": "auto-generated by test_admin.py",
        },
        "items": [{"category": cat, "id": pid, "quantity": 1}],
    }
    resp = requests.post(f"{API}/orders", json=order_payload)
    r.check("POST /orders valid -> 201", resp.status_code == 201, f"got {resp.status_code}")
    order_id = resp.json().get("order_id") if resp.status_code == 201 else None
    r.check("order has whatsapp_url",
            resp.status_code == 201 and resp.json().get("whatsapp_url", "").startswith("https://wa.me/"))

    # 4b. out of stock — pick quantity above current stock but within the 50 cap
    stock_items = requests.get(
        f"{API}/admin/stock?category={cat}&page_size=100",
        headers=auth(token),
    ).json()["items"]
    current_qty = next((s["quantity"] for s in stock_items if s["id"] == pid), 0)

    if current_qty < 50:
        over = current_qty + 1
        bad = dict(order_payload)
        bad["items"] = [{"category": cat, "id": pid, "quantity": over}]
        resp = requests.post(f"{API}/orders", json=bad)
        r.check(
            f"POST /orders out of stock (asked {over}, have {current_qty}) -> 400",
            resp.status_code == 400,
            f"got {resp.status_code}",
        )
    else:
        print(f"  SKIP  POST /orders out of stock (stock {current_qty} >= 50 cap)")

    # 4c. unknown product
    bad = dict(order_payload)
    bad["items"] = [{"category": cat, "id": 9999999, "quantity": 1}]
    resp = requests.post(f"{API}/orders", json=bad)
    r.check("POST /orders unknown product -> 400", resp.status_code == 400, f"got {resp.status_code}")

    # 4d. empty items
    bad = dict(order_payload)
    bad["items"] = []
    resp = requests.post(f"{API}/orders", json=bad)
    r.check("POST /orders empty items -> 422", resp.status_code == 422, f"got {resp.status_code}")

    # ==================================================== 5. ADMIN LIST
    phase("5. Admin - list orders")

    resp = requests.get(f"{API}/admin/orders", headers=auth(token))
    r.check("GET /admin/orders -> 200", resp.status_code == 200, f"got {resp.status_code}")
    body = resp.json() if resp.status_code == 200 else {}
    r.check("response has items/total/page/page_size/has_next",
            all(k in body for k in ("items", "total", "page", "page_size", "has_next")))
    r.check("our order is in the list",
            order_id is not None and any(o["id"] == order_id for o in body.get("items", [])))

    resp = requests.get(f"{API}/admin/orders?status=pending", headers=auth(token))
    r.check("GET /admin/orders?status=pending -> 200", resp.status_code == 200, f"got {resp.status_code}")

    resp = requests.get(f"{API}/admin/orders?status=bogus", headers=auth(token))
    r.check("GET /admin/orders?status=bogus -> 422", resp.status_code == 422, f"got {resp.status_code}")

    resp = requests.get(f"{API}/admin/orders?page_size=500", headers=auth(token))
    r.check("GET /admin/orders?page_size=500 -> 422 (max 100)", resp.status_code == 422, f"got {resp.status_code}")

    # ==================================================== 6. ADMIN DETAIL
    phase("6. Admin - order detail")

    if order_id:
        resp = requests.get(f"{API}/admin/orders/{order_id}", headers=auth(token))
        r.check(f"GET /admin/orders/{order_id} -> 200", resp.status_code == 200, f"got {resp.status_code}")
        body = resp.json() if resp.status_code == 200 else {}
        r.check("detail has customer_name", bool(body.get("customer_name")))
        r.check("detail has items list", isinstance(body.get("items"), list) and len(body["items"]) > 0)
        r.check("item has snapshots",
                body.get("items") and all(k in body["items"][0]
                    for k in ("brand", "name", "specification", "unit_price", "quantity", "line_total")))

    resp = requests.get(f"{API}/admin/orders/9999999", headers=auth(token))
    r.check("GET /admin/orders/9999999 -> 404", resp.status_code == 404, f"got {resp.status_code}")

    # ==================================================== 7. CONFIRM
    phase("7. Admin - confirm order (with stock check)")

    if order_id and cat != "additional":
        stock_before = requests.get(
            f"{API}/admin/stock?category={cat}&page_size=100", headers=auth(token)
        ).json()["items"]
        qty_before = next((s["quantity"] for s in stock_before if s["id"] == pid), None)

        resp = requests.post(f"{API}/admin/orders/{order_id}/confirm", headers=auth(token))
        r.check(f"POST /admin/orders/{order_id}/confirm -> 200", resp.status_code == 200, f"got {resp.status_code}")
        if resp.status_code == 200:
            r.check("confirm returns status=confirmed",
                    resp.json().get("status") == "confirmed")

        stock_after = requests.get(
            f"{API}/admin/stock?category={cat}&page_size=100", headers=auth(token)
        ).json()["items"]
        qty_after = next((s["quantity"] for s in stock_after if s["id"] == pid), None)

        r.check("stock decremented by 1",
                qty_before is not None and qty_after is not None and qty_after == qty_before - 1,
                f"before={qty_before} after={qty_after}")

        # confirm again should fail
        resp = requests.post(f"{API}/admin/orders/{order_id}/confirm", headers=auth(token))
        r.check("confirm twice -> 400", resp.status_code == 400, f"got {resp.status_code}")

    # ==================================================== 8. CANCEL
    phase("8. Admin - cancel a fresh order")

    resp = requests.post(f"{API}/orders", json=order_payload)
    cancel_id = resp.json().get("order_id") if resp.status_code == 201 else None

    if cancel_id:
        resp = requests.post(f"{API}/admin/orders/{cancel_id}/cancel", headers=auth(token))
        r.check("cancel pending order -> 200", resp.status_code == 200, f"got {resp.status_code}")
        if resp.status_code == 200:
            r.check("cancel returns status=cancelled",
                    resp.json().get("status") == "cancelled")

        resp = requests.post(f"{API}/admin/orders/{cancel_id}/cancel", headers=auth(token))
        r.check("cancel twice -> 400", resp.status_code == 400, f"got {resp.status_code}")

    # ==================================================== 9. STOCK LIST
    phase("9. Admin - stock list")

    resp = requests.get(f"{API}/admin/stock", headers=auth(token))
    r.check("GET /admin/stock -> 200", resp.status_code == 200, f"got {resp.status_code}")
    body = resp.json() if resp.status_code == 200 else {}
    r.check("items include quantity", body.get("items") and "quantity" in body["items"][0])

    resp = requests.get(f"{API}/admin/stock?category=engine_oil", headers=auth(token))
    r.check("GET /admin/stock?category=engine_oil -> 200", resp.status_code == 200, f"got {resp.status_code}")
    if resp.status_code == 200:
        r.check("all items are engine_oil",
                all(i["category"] == "engine_oil" for i in resp.json()["items"]))

    resp = requests.get(f"{API}/admin/stock?category=bogus", headers=auth(token))
    r.check("invalid category -> 422", resp.status_code == 422, f"got {resp.status_code}")

    # ==================================================== 10. STOCK UPDATE
    phase("10. Admin - stock update")

    # 10a. change price
    resp = requests.patch(
        f"{API}/admin/stock/{cat}/{pid}",
        headers=auth(token),
        json={"price": 99999.99},
    )
    r.check("PATCH price -> 200", resp.status_code == 200, f"got {resp.status_code}")
    if resp.status_code == 200:
        r.check("price updated", resp.json().get("price") == 99999.99)

    # revert
    requests.patch(f"{API}/admin/stock/{cat}/{pid}", headers=auth(token),
                   json={"price": product["price"]})

    # 10b. change quantity
    resp = requests.patch(
        f"{API}/admin/stock/{cat}/{pid}",
        headers=auth(token),
        json={"quantity": 777},
    )
    r.check("PATCH quantity -> 200", resp.status_code == 200, f"got {resp.status_code}")
    if resp.status_code == 200:
        r.check("quantity updated", resp.json().get("quantity") == 777)
    requests.patch(f"{API}/admin/stock/{cat}/{pid}", headers=auth(token),
                   json={"quantity": 12})  # restore

    # 10c. non-existent product
    resp = requests.patch(
        f"{API}/admin/stock/{cat}/9999999",
        headers=auth(token),
        json={"price": 100},
    )
    r.check("PATCH unknown product -> 404", resp.status_code == 404, f"got {resp.status_code}")

    # ==================================================== 11. STOCK CREATE
    phase("11. Admin - stock create")

    created_items: list[tuple[str, int]] = []

    # 11a. engine_oil
    resp = requests.post(
        f"{API}/admin/stock",
        headers=auth(token),
        json={
            "category": "engine_oil",
            "brand": "TEST-BRAND",
            "specification": "test spec 12345",
            "viscosity": "0w-20",
            "size": "1L",
            "price": 100,
            "quantity": 5,
        },
    )
    r.check("POST engine_oil -> 201", resp.status_code == 201, f"got {resp.status_code}")
    if resp.status_code == 201:
        created_items.append(("engine_oil", resp.json()["id"]))

    # 11b. oil_filter
    resp = requests.post(
        f"{API}/admin/stock",
        headers=auth(token),
        json={
            "category": "oil_filter",
            "brand": "TEST-BRAND",
            "specification": "TESTFILTER123",
            "price": 50,
            "quantity": 10,
        },
    )
    r.check("POST oil_filter -> 201", resp.status_code == 201, f"got {resp.status_code}")
    if resp.status_code == 201:
        created_items.append(("oil_filter", resp.json()["id"]))

    # 11c. additional WITHOUT category_type -> must fail
    resp = requests.post(
        f"{API}/admin/stock",
        headers=auth(token),
        json={
            "category": "additional",
            "brand": "TEST-BRAND",
            "specification": "some addon",
            "price": 200,
            "quantity": 1,
        },
    )
    r.check("POST additional without category_type -> 400",
            resp.status_code == 400, f"got {resp.status_code}")

    # 11d. additional WITH category_type
    resp = requests.post(
        f"{API}/admin/stock",
        headers=auth(token),
        json={
            "category": "additional",
            "brand": "TEST-BRAND",
            "specification": "DOT 4 brake fluid",
            "size": "1L",
            "price": 200,
            "quantity": 3,
            "category_type": "liquide de frein",
        },
    )
    r.check("POST additional with category_type -> 201",
            resp.status_code == 201, f"got {resp.status_code}")
    if resp.status_code == 201:
        created_items.append(("additional", resp.json()["id"]))

    # 11e. invalid category
    resp = requests.post(
        f"{API}/admin/stock",
        headers=auth(token),
        json={"category": "bogus", "brand": "X", "specification": "Y", "price": 1},
    )
    r.check("POST invalid category -> 422", resp.status_code == 422, f"got {resp.status_code}")

    # ==================================================== 12. DELETE
    phase("12. Admin - stock delete (cleanup)")

    for category, item_id in created_items:
        resp = requests.delete(f"{API}/admin/stock/{category}/{item_id}", headers=auth(token))
        r.check(f"DELETE {category}/{item_id} -> 204", resp.status_code == 204, f"got {resp.status_code}")

    # delete again -> 404
    if created_items:
        cat_del, id_del = created_items[0]
        resp = requests.delete(f"{API}/admin/stock/{cat_del}/{id_del}", headers=auth(token))
        r.check(f"DELETE {cat_del}/{id_del} twice -> 404", resp.status_code == 404, f"got {resp.status_code}")

    # ==================================================== 13. HEALTH
    phase("13. Health check")

    resp = requests.get(f"{BASE}/health")
    r.check("GET /health -> 200", resp.status_code == 200, f"got {resp.status_code}")

    return r.summary()


if __name__ == "__main__":
    sys.exit(main())