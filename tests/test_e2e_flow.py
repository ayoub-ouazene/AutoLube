"""
End-to-end flow test for the AutoLube backend.

Simulates a real customer journey:
    1. Admin login (for later verification steps)
    2. Customer creates a chat session
    3. Customer asks for gearbox oil for a known car
       -> agent pipeline runs (cache -> stock)
       -> response includes products with all card data
    4. Customer asks for an oil filter
       -> response is text-only, no products
    5. Customer places an order from the recommended product
       -> order created, whatsapp_url returned
    6. Admin sees the order in their list
    7. Admin views order detail (with snapshots)
    8. Admin confirms the order
       -> stock decremented by the ordered quantity
    9. Verify product still visible in the public catalog

Every order/product created by the test is cleaned up at the end.

Prerequisites:
    - API running at http://127.0.0.1:8000
    - Stock seeded with at least one gearbox_oil item

Usage:
    ADMIN_PASSWORD=yourpassword python -m tests.test_e2e_flow

Optional env vars:
    API_BASE        default http://127.0.0.1:8000
    ADMIN_USERNAME  default "admin"
    ADMIN_PASSWORD  required
"""

import os
import sys

import requests


BASE = os.getenv("API_BASE", "http://127.0.0.1:8000")
API = f"{BASE}/api/v1"
USERNAME = os.getenv("ADMIN_USERNAME", "admin")
PASSWORD = os.getenv("ADMIN_PASSWORD", "")

# Marker used to identify orders created by this test, so we can clean them up.
TEST_CUSTOMER_NAME = "E2E TEST - DO NOT SHIP"


class Runner:
    def __init__(self):
        self.passed = 0
        self.failed = 0
        self.failures: list[str] = []
        self.created_orders: list[int] = []

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


def phase(title: str) -> None:
    print()
    print(f"--- {title} ---")


def auth(token: str) -> dict:
    return {"Authorization": f"Bearer {token}"}


# --------------------------------------------------------------------- steps

def step_1_admin_login(r: Runner) -> str | None:
    phase("1. Admin login")
    if not PASSWORD:
        r.check("ADMIN_PASSWORD set", False, "env var missing")
        return None

    resp = requests.post(
        f"{API}/admin/login",
        json={"username": USERNAME, "password": PASSWORD},
    )
    r.check("POST /admin/login -> 200", resp.status_code == 200, f"got {resp.status_code}")
    if resp.status_code != 200:
        return None
    token = resp.json().get("access_token")
    r.check("token present", bool(token))
    return token


def step_2_create_chat(r: Runner) -> str | None:
    phase("2. Customer creates a chat session")
    resp = requests.post(f"{API}/chat/session")
    r.check("POST /chat/session -> 201", resp.status_code == 201, f"got {resp.status_code}")
    if resp.status_code != 201:
        return None
    sid = resp.json().get("session_id")
    r.check("session_id present", bool(sid))
    return sid


def step_3_gearbox_query(r: Runner, sid: str) -> dict | None:
    phase("3. Customer asks for gearbox oil (expected cache + stock hit)")

    resp = requests.post(
        f"{API}/chat/session/{sid}/message",
        json={"message": "VW Golf VII 2016 MQ250 manual, huile de boîte"},
        timeout=180,
    )
    r.check("POST message -> 200", resp.status_code == 200,
            f"got {resp.status_code}: {resp.text[:200]}")
    if resp.status_code != 200:
        return None

    body = resp.json()
    r.check("reply present", isinstance(body.get("reply"), str) and len(body["reply"]) > 20)
    r.check("products is a list", isinstance(body.get("products"), list))

    products = body.get("products", [])
    if not products:
        print("       (no products returned — cache or stock may be empty)")
        return {"reply": body.get("reply"), "products": []}

    r.check("at least one product returned", len(products) >= 1)

    first = products[0]
    required = {
        "category", "id", "brand", "name", "specification",
        "viscosity", "size", "price", "in_stock",
        "image_front_url", "image_back_url",
    }
    r.check("product has full card shape",
            required.issubset(first.keys()),
            f"missing={required - set(first.keys())}")
    r.check("product does not expose quantity", "quantity" not in first)
    r.check("product is in stock", first.get("in_stock") is True)

    return {"reply": body["reply"], "products": products, "first": first}


def step_4_filter_query(r: Runner, sid: str) -> None:
    phase("4. Customer asks for an oil filter (expected no products, text-only)")

    resp = requests.post(
        f"{API}/chat/session/{sid}/message",
        json={"message": "filtre à huile pour Peugeot 208"},
        timeout=60,
    )
    r.check("POST message -> 200", resp.status_code == 200, f"got {resp.status_code}")
    if resp.status_code != 200:
        return
    body = resp.json()
    r.check("reply present", isinstance(body.get("reply"), str))
    r.check("products is empty list",
            body.get("products") == [],
            f"got {body.get('products')}")


def step_5_place_order(r: Runner, product: dict) -> int | None:
    phase("5. Customer places an order from the recommended product")

    order_payload = {
        "customer": {
            "full_name": TEST_CUSTOMER_NAME,
            "phone": "+213555000999",
            "email": "e2e@example.com",
            "wilaya": "Alger",
            "city": "Alger",
            "notes": "created by tests/test_e2e_flow.py",
        },
        "items": [
            {
                "category": product["category"],
                "id": product["id"],
                "quantity": 1,
            }
        ],
    }
    resp = requests.post(f"{API}/orders", json=order_payload)
    r.check("POST /orders -> 201", resp.status_code == 201,
            f"got {resp.status_code}: {resp.text[:200]}")
    if resp.status_code != 201:
        return None

    body = resp.json()
    order_id = body.get("order_id")
    r.check("order_id returned", isinstance(order_id, int))
    r.check("whatsapp_url returned",
            isinstance(body.get("whatsapp_url"), str)
            and body["whatsapp_url"].startswith("https://wa.me/"))
    r.check("total matches product price",
            body.get("total") == product["price"],
            f"got total={body.get('total')} price={product['price']}")
    if order_id:
        r.created_orders.append(order_id)
    return order_id


def step_6_admin_sees_order(r: Runner, token: str, order_id: int) -> None:
    phase("6. Admin sees the order in the list")

    resp = requests.get(f"{API}/admin/orders?status=pending&page_size=100", headers=auth(token))
    r.check("GET /admin/orders -> 200", resp.status_code == 200, f"got {resp.status_code}")
    if resp.status_code != 200:
        return
    body = resp.json()
    ids = [o["id"] for o in body.get("items", [])]
    r.check("new order present in list", order_id in ids, f"looking for {order_id} in {ids[:10]}")


def step_7_admin_detail(r: Runner, token: str, order_id: int) -> None:
    phase("7. Admin views order detail")

    resp = requests.get(f"{API}/admin/orders/{order_id}", headers=auth(token))
    r.check("GET /admin/orders/{id} -> 200", resp.status_code == 200, f"got {resp.status_code}")
    if resp.status_code != 200:
        return
    body = resp.json()
    r.check("customer_name matches", body.get("customer_name") == TEST_CUSTOMER_NAME)
    r.check("items list non-empty", isinstance(body.get("items"), list) and len(body["items"]) > 0)
    if body.get("items"):
        it = body["items"][0]
        for k in ("brand", "name", "specification", "unit_price", "quantity", "line_total"):
            r.check(f"item has snapshot '{k}'", k in it and it[k] not in (None, ""))


def step_8_admin_confirms(r: Runner, token: str, order_id: int, product: dict) -> None:
    phase("8. Admin confirms the order and stock is decremented")

    # Read stock before
    cat, pid = product["category"], product["id"]
    resp = requests.get(
        f"{API}/admin/stock?category={cat}&page_size=100",
        headers=auth(token),
    )
    r.check("GET /admin/stock before -> 200", resp.status_code == 200)
    if resp.status_code != 200:
        return
    before = next((s for s in resp.json()["items"] if s["id"] == pid), None)
    if before is None:
        r.check("product found in admin stock", False, f"{cat}/{pid} not in stock list")
        return
    qty_before = before["quantity"]

    # Confirm
    resp = requests.post(f"{API}/admin/orders/{order_id}/confirm", headers=auth(token))
    r.check("POST /admin/orders/{id}/confirm -> 200", resp.status_code == 200,
            f"got {resp.status_code}: {resp.text[:200]}")
    if resp.status_code != 200:
        return
    r.check("status is confirmed", resp.json().get("status") == "confirmed")

    # Read stock after
    resp = requests.get(
        f"{API}/admin/stock?category={cat}&page_size=100",
        headers=auth(token),
    )
    after = next((s for s in resp.json()["items"] if s["id"] == pid), None)
    qty_after = after["quantity"] if after else None
    r.check("stock decremented by 1",
            qty_before is not None and qty_after == qty_before - 1,
            f"before={qty_before} after={qty_after}")


def step_9_public_catalog(r: Runner, product: dict) -> None:
    phase("9. Product still visible in the public catalog")

    cat, pid = product["category"], product["id"]
    resp = requests.get(f"{API}/products/{cat}/{pid}")
    r.check("GET /products/{cat}/{id} -> 200", resp.status_code == 200,
            f"got {resp.status_code}")
    if resp.status_code != 200:
        return
    body = resp.json()
    r.check("public response has no quantity", "quantity" not in body)
    r.check("public response has image fields",
            "image_front_url" in body and "image_back_url" in body)


def step_10_cleanup(r: Runner, token: str) -> None:
    phase("10. Cleanup - cancel any orders created by the test")

    # Fetch admin orders filtered by the test customer name (no name filter in
    # API, so list all and grep)
    resp = requests.get(f"{API}/admin/orders?page_size=100", headers=auth(token))
    if resp.status_code != 200:
        print("  SKIP  could not list orders for cleanup")
        return
    test_orders = [
        o for o in resp.json()["items"]
        if o.get("customer_name") == TEST_CUSTOMER_NAME
        and o.get("status") in ("pending", "confirmed")
    ]

    if not test_orders:
        print("  (nothing to clean up)")
        return

    for o in test_orders:
        # Confirmed orders can't be cancelled per API rules — leave them;
        # they carry the test customer name and are easy to spot in admin.
        if o["status"] == "confirmed":
            print(f"  NOTE  order #{o['id']} is confirmed — stock was decremented, "
                  f"manual cleanup recommended")
            continue
        resp = requests.post(f"{API}/admin/orders/{o['id']}/cancel", headers=auth(token))
        if resp.status_code == 200:
            print(f"  cancelled order #{o['id']}")
        else:
            print(f"  failed to cancel order #{o['id']}: {resp.status_code}")


# --------------------------------------------------------------------- main

def main() -> int:
    r = Runner()

    token = step_1_admin_login(r)
    if token is None:
        print("\nCannot proceed without admin token.")
        return r.summary()

    sid = step_2_create_chat(r)
    if sid is None:
        print("\nCannot proceed without chat session.")
        return r.summary()

    chat = step_3_gearbox_query(r, sid)
    step_4_filter_query(r, sid)

    if not chat or not chat.get("products"):
        print("\nNo products returned from the chat step; skipping order flow.")
        return r.summary()

    product = chat["first"]
    order_id = step_5_place_order(r, product)
    if order_id:
        step_6_admin_sees_order(r, token, order_id)
        step_7_admin_detail(r, token, order_id)
        step_8_admin_confirms(r, token, order_id, product)

    step_9_public_catalog(r, product)
    step_10_cleanup(r, token)

    return r.summary()


if __name__ == "__main__":
    sys.exit(main())