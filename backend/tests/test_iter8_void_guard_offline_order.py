# Iteration 8: voidSale guard vs returns, stock restoration on void, server-side ordering deps, sale+collection regression
import uuid
import pytest
import requests

S = "https://fearless-ostrich-878.eu-west-1.convex.site/api"
AG, OW = "test_token_agent", "test_token_owner"


def call(m, p, t, b=None):
    r = requests.request(m, S + p, json=b, headers={"Authorization": f"Bearer {t}"}, timeout=30)
    try:
        return r.status_code, r.json()
    except Exception:
        return r.status_code, None


def inv_qty(pid):
    return next(i["quantity"] for i in call("GET", "/my/inventory", AG)[1] if i["product_id"] == pid)


def cust_balance(cid):
    return next(x for x in call("GET", "/customers", AG)[1] if x["id"] == cid)["balance"]


@pytest.fixture(scope="module")
def prod():
    items = [i for i in call("GET", "/my/inventory", AG)[1] if i["quantity"] >= 6]
    if not items:
        pytest.skip("no distributor stock >= 6")
    return items[0]["product_id"]


def new_customer():
    st, c = call("POST", "/customers", AG, {"id": "TEST_VT_" + uuid.uuid4().hex[:8], "name": "TEST_VT " + uuid.uuid4().hex[:4],
                                           "phone": "+963933" + str(uuid.uuid4().int)[:6], "address": "t", "location": "t", "lat": 33.5, "lng": 36.3})
    assert st == 200, c
    return c


def sale(cid, pid, q, paid=0):
    sid = uuid.uuid4().hex
    st, r = call("POST", "/sales", AG, {"id": sid, "customer_id": cid, "items": [{"product_id": pid, "quantity": q, "unit": "PIECE"}], "paid_amount": paid})
    assert st == 200, r
    return sid, r


def ret(cid, pid, q):
    return call("POST", "/sales-returns", AG, {"id": uuid.uuid4().hex, "customer_id": cid, "items": [{"product_id": pid, "quantity": q}]})


# voidSale: sale with no returns voids and restores distributor stock + balance
def test_void_restores_stock_and_balance(prod):
    c = new_customer()
    before = inv_qty(prod)
    sid, _ = sale(c["id"], prod, 2)
    assert abs(inv_qty(prod) - (before - 2)) < 1e-6
    st, r = call("POST", f"/sales/{sid}/void", OW, {"reason": "TEST"})
    assert st == 200 and r["voided"] is True and r["total"] == 0
    assert abs(inv_qty(prod) - before) < 1e-6
    assert abs(cust_balance(c["id"])) < 0.01
    # double void refused
    assert call("POST", f"/sales/{sid}/void", OW, {"reason": "TEST"})[0] in (400, 404)


# voidSale: partial return still blocks the void
def test_void_blocked_with_partial_return(prod):
    c = new_customer()
    sid, _ = sale(c["id"], prod, 2)
    assert ret(c["id"], prod, 1)[0] == 200
    before = inv_qty(prod)
    st, r = call("POST", f"/sales/{sid}/void", OW, {"reason": "TEST"})
    assert st == 400 and "مرتجعات" in r["detail"]
    assert abs(inv_qty(prod) - before) < 1e-6  # no stock changed on refusal


# voidSale: returns covered by ANOTHER sale don't block voiding this one
def test_void_allowed_when_other_sale_covers_returns(prod):
    c = new_customer()
    sid_a, _ = sale(c["id"], prod, 2)
    sale(c["id"], prod, 2)
    assert ret(c["id"], prod, 2)[0] == 200
    st, r = call("POST", f"/sales/{sid_a}/void", OW, {"reason": "TEST"})
    assert st == 200, r
    # now remaining sale is fully returned -> further return rejected
    assert ret(c["id"], prod, 1)[0] == 400


# server deps: return before its sale (what an un-ordered flush would do) is rejected; after the sale it succeeds
def test_return_requires_prior_sale(prod):
    c = new_customer()
    st, r = ret(c["id"], prod, 1)
    assert st == 400
    sale(c["id"], prod, 1)
    assert ret(c["id"], prod, 1)[0] == 200


# regression: online sale + collection
def test_sale_and_collection_online(prod):
    c = new_customer()
    sid, s = sale(c["id"], prod, 1, paid=0)
    bal = cust_balance(c["id"])
    assert bal > 0
    st, col = call("POST", "/collections", AG, {"id": uuid.uuid4().hex, "customer_id": c["id"], "amount": round(bal / 2, 2)})
    assert st == 200, col
    assert abs(cust_balance(c["id"]) - (bal - round(bal / 2, 2))) < 0.02
    # over-collection rejected
    assert call("POST", "/collections", AG, {"id": uuid.uuid4().hex, "customer_id": c["id"], "amount": bal * 10})[0] == 400
