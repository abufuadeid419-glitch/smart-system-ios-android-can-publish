"""Sales quantity validation + returns strictness (live Convex HTTP API)."""
import uuid
import pytest
import requests

S = "https://fearless-ostrich-878.eu-west-1.convex.site/api"
AG = {"Authorization": "Bearer test_token_agent", "Content-Type": "application/json"}


@pytest.fixture(scope="module")
def ctx():
    inv = requests.get(f"{S}/my/inventory", headers=AG, timeout=30).json()
    prod = next(i for i in inv if i["quantity"] >= 3)["product_id"]
    r = requests.post(f"{S}/customers", headers=AG, timeout=30, json={
        "id": "TEST_" + uuid.uuid4().hex[:8], "name": "TEST_qty " + uuid.uuid4().hex[:4],
        "phone": "+963912" + str(uuid.uuid4().int)[:6], "address": "Damascus test", "location": "test",
        "lat": 33.5, "lng": 36.3})
    assert r.status_code == 200, r.text
    return {"prod": prod, "cid": r.json()["id"]}


# Sales: quantity <= 0 / invalid must be rejected
@pytest.mark.parametrize("qty", [0, -1, -0.5])
def test_sale_nonpositive_qty_rejected(ctx, qty):
    sid = uuid.uuid4().hex
    r = requests.post(f"{S}/sales", headers=AG, timeout=30, json={
        "id": sid, "customer_id": ctx["cid"], "items": [{"product_id": ctx["prod"], "quantity": qty, "unit": "PIECE"}], "paid_amount": 0})
    assert r.status_code == 400, f"qty={qty} -> {r.status_code} {r.text[:200]}"
    sales = requests.get(f"{S}/sales", headers=AG, timeout=30).json()
    assert not any(s["id"] == sid for s in sales)


def test_sale_empty_items_rejected(ctx):
    r = requests.post(f"{S}/sales", headers=AG, timeout=30, json={
        "id": uuid.uuid4().hex, "customer_id": ctx["cid"], "items": [], "paid_amount": 0})
    assert r.status_code == 400, r.text


def test_sale_mixed_valid_and_zero_rejected(ctx):
    r = requests.post(f"{S}/sales", headers=AG, timeout=30, json={
        "id": uuid.uuid4().hex, "customer_id": ctx["cid"],
        "items": [{"product_id": ctx["prod"], "quantity": 1, "unit": "PIECE"}, {"product_id": ctx["prod"], "quantity": 0, "unit": "PIECE"}],
        "paid_amount": 0})
    assert r.status_code == 400, r.text


def test_return_zero_qty_rejected(ctx):
    r = requests.post(f"{S}/sales-returns", headers=AG, timeout=30, json={
        "id": uuid.uuid4().hex, "customer_id": ctx["cid"], "items": [{"product_id": ctx["prod"], "quantity": 0}]})
    assert r.status_code == 400
