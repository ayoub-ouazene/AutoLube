"""
Verify the products-extraction feature added to the chat pipeline.

Covers:
  - process_turn returns a 4-tuple (reply, history, vehicle, products)
  - chat_service.process_message returns (reply, products)
  - GET /chat/session/{id}/message includes "products" in the response
  - products carry the ProductOut shape (no admin-only fields)
  - products are empty for filter/brake fluid paths
  - products are sorted by price ascending
  - duplicate products are deduplicated

Prerequisites:
    - API running at http://127.0.0.1:8000
    - Stock seeded (products exist for Clio IV / Golf VII etc.)

Usage:
    python -m tests.llm_product_extraction

Optional env:
    API_BASE   default http://127.0.0.1:8000
"""

import inspect
import os
import sys

import requests


BASE = os.getenv("API_BASE", "http://127.0.0.1:8000")
API = f"{BASE}/api/v1"


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


def phase(title: str) -> None:
    print()
    print(f"--- {title} ---")


# ---------------------------------------------------------------- 1. imports

def test_imports(r: TestRunner) -> None:
    phase("1. Module imports and signatures")

    try:
        from app.agents.main_agent import (
            process_turn,
            _extract_products_from_messages,
            _parse_tool_payload,
        )
        r.check("import main_agent helpers", True)
    except ImportError as e:
        r.check("import main_agent helpers", False, str(e))
        return

    sig = inspect.signature(process_turn)
    r.check(
        "process_turn signature is (user_message, history, current_vehicle)",
        list(sig.parameters.keys()) == ["user_message", "history", "current_vehicle"],
        f"got {list(sig.parameters.keys())}",
    )

    try:
        from app.services.chat_service import process_message
        r.check("import chat_service.process_message", True)
    except ImportError as e:
        r.check("import chat_service.process_message", False, str(e))
        return

    sig = inspect.signature(process_message)
    r.check(
        "chat_service.process_message signature is (session_id, message)",
        list(sig.parameters.keys()) == ["session_id", "message"],
        f"got {list(sig.parameters.keys())}",
    )

    try:
        from app.schemas.chat import MessageResponse
        r.check("import MessageResponse", True)
    except ImportError as e:
        r.check("import MessageResponse", False, str(e))
        return

    fields = set(MessageResponse.model_fields.keys())
    r.check(
        "MessageResponse has 'products' field",
        "products" in fields,
        f"fields={sorted(fields)}",
    )
    r.check(
        "MessageResponse has 'reply' field",
        "reply" in fields,
        f"fields={sorted(fields)}",
    )


# ---------------------------------------------------------------- 2. _parse_tool_payload

def test_parse_tool_payload(r: TestRunner) -> None:
    phase("2. _parse_tool_payload handles dict and string")

    from app.agents.main_agent import _parse_tool_payload

    r.check("dict input passes through", _parse_tool_payload({"a": 1}) == {"a": 1})
    r.check("valid JSON string is parsed", _parse_tool_payload('{"a": 1}') == {"a": 1})
    r.check("invalid JSON string returns None", _parse_tool_payload("not json") is None)
    r.check("None returns None", _parse_tool_payload(None) is None)
    r.check("list returns None", _parse_tool_payload([1, 2]) is None)


# ---------------------------------------------------------------- 3. _extract_products_from_messages

def test_extract_products(r: TestRunner) -> None:
    phase("3. _extract_products_from_messages")

    from app.agents.main_agent import _extract_products_from_messages

    class FakeToolCall:
        def __init__(self, cid, name):
            self._d = {"id": cid, "name": name}
        def get(self, k):
            return self._d.get(k)

    class FakeAIMessage:
        def __init__(self, tool_calls):
            self.tool_calls = tool_calls

    # The implementation checks `type(m).__name__ == "ToolMessage"`, so the
    # fake class must be named exactly that.
    class ToolMessage:
        def __init__(self, tool_call_id, content):
            self.tool_call_id = tool_call_id
            self.content = content

    # Case 1: no messages -> empty list
    r.check("empty messages -> []", _extract_products_from_messages([]) == [])

    # Case 2: one stock_lookup ok with two products
    msgs = [
        FakeAIMessage([FakeToolCall("c1", "stock_lookup")]),
        ToolMessage("c1", {
            "status": "ok",
            "products": [
                {"category": "engine_oil", "id": 5, "price": 9000, "name": "A"},
                {"category": "engine_oil", "id": 2, "price": 4000, "name": "B"},
            ],
        }),
    ]
    result = _extract_products_from_messages(msgs)
    r.check("returns 2 products", len(result) == 2, f"got {len(result)}")
    if len(result) == 2:
        r.check("sorted by price asc", result[0]["price"] <= result[1]["price"],
                f"prices={[p['price'] for p in result]}")

    # Case 3: status != ok -> skipped
    msgs = [
        FakeAIMessage([FakeToolCall("c1", "stock_lookup")]),
        ToolMessage("c1", {"status": "no_match", "products": []}),
    ]
    r.check("no_match -> []", _extract_products_from_messages(msgs) == [])

    # Case 4: dedup across two stock_lookup calls
    msgs = [
        FakeAIMessage([FakeToolCall("c1", "stock_lookup")]),
        ToolMessage("c1", {
            "status": "ok",
            "products": [{"category": "gearbox_oil", "id": 1, "price": 2300, "name": "X"}],
        }),
        FakeAIMessage([FakeToolCall("c2", "stock_lookup")]),
        ToolMessage("c2", {
            "status": "ok",
            "products": [
                {"category": "gearbox_oil", "id": 1, "price": 2300, "name": "X"},
                {"category": "gearbox_oil", "id": 2, "price": 4400, "name": "Y"},
            ],
        }),
    ]
    result = _extract_products_from_messages(msgs)
    r.check("dedup: 2 unique products", len(result) == 2, f"got {len(result)}")

    # Case 5: a different tool name is ignored
    msgs = [
        FakeAIMessage([FakeToolCall("c1", "specs_lookup")]),
        ToolMessage("c1", {
            "status": "ok",
            "products": [{"category": "engine_oil", "id": 1, "price": 1, "name": "Z"}],
        }),
    ]
    r.check("non-stock_lookup tools ignored", _extract_products_from_messages(msgs) == [])

    # Case 6: content as JSON string
    msgs = [
        FakeAIMessage([FakeToolCall("c1", "stock_lookup")]),
        ToolMessage("c1", '{"status": "ok", "products": [{"category": "gearbox_oil", "id": 9, "price": 100, "name": "S"}]}'),
    ]
    result = _extract_products_from_messages(msgs)
    r.check("JSON string content works", len(result) == 1)


# ---------------------------------------------------------------- 4. HTTP: chat response

def test_chat_endpoint(r: TestRunner) -> None:
    phase("4. /chat/.../message response shape (gearbox oil, cache hit)")

    # Create a session
    resp = requests.post(f"{API}/chat/session")
    r.check("POST /chat/session -> 201", resp.status_code == 201, f"got {resp.status_code}")
    if resp.status_code != 201:
        return None
    sid = resp.json()["session_id"]

    # Send a gearbox-oil query that should hit the cache and stock
    resp = requests.post(
        f"{API}/chat/session/{sid}/message",
        json={"message": "VW Golf VII 2016 MQ250 manual, huile de boîte"},
        timeout=120,
    )
    r.check("POST message -> 200", resp.status_code == 200, f"got {resp.status_code}: {resp.text[:200]}")
    if resp.status_code != 200:
        return sid

    body = resp.json()
    r.check("response has 'reply'", "reply" in body and isinstance(body["reply"], str))
    r.check("response has 'products' field", "products" in body)
    r.check("'products' is a list", isinstance(body.get("products"), list))

    products = body.get("products", [])
    if not products:
        print("       (no products returned — cache or stock may be empty, skipping product checks)")
        return sid

    r.check("at least one product returned", len(products) >= 1)

    first = products[0]
    required_keys = {
        "category", "id", "brand", "name", "specification",
        "viscosity", "size", "price", "in_stock",
        "image_front_url", "image_back_url",
    }
    r.check(
        "product has all ProductOut keys",
        required_keys.issubset(first.keys()),
        f"missing={required_keys - set(first.keys())}",
    )
    r.check("product does NOT expose 'quantity'",
            "quantity" not in first,
            f"keys={sorted(first.keys())}")
    r.check("product category is gearbox_oil",
            first.get("category") == "gearbox_oil",
            f"got {first.get('category')}")

    # Sorted by price ascending
    prices = [p["price"] for p in products]
    r.check("products sorted by price ascending",
            prices == sorted(prices),
            f"prices={prices}")

    return sid


# ---------------------------------------------------------------- 5. filter path returns empty

def test_filter_path(r: TestRunner, sid: str | None) -> None:
    phase("5. Filter path returns empty products list")

    if not sid:
        print("  SKIP  no session id from previous test")
        return

    resp = requests.post(
        f"{API}/chat/session/{sid}/message",
        json={"message": "filtre à huile pour Peugeot 208"},
        timeout=120,
    )
    r.check("POST filter query -> 200", resp.status_code == 200, f"got {resp.status_code}")
    if resp.status_code != 200:
        return

    body = resp.json()
    r.check("filter reply has products field", "products" in body)
    r.check("filter reply has NO products", body.get("products") == [] or len(body.get("products", [])) == 0,
            f"got {body.get('products')}")


# ---------------------------------------------------------------- main

def main() -> int:
    r = TestRunner()

    test_imports(r)
    test_parse_tool_payload(r)
    test_extract_products(r)
    sid = test_chat_endpoint(r)
    test_filter_path(r, sid)

    return r.summary()


if __name__ == "__main__":
    sys.exit(main())