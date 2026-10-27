"""Void-after-return guard (iteration 7 HIGH bug)."""
import json, urllib.request, uuid
S = "https://fearless-ostrich-878.eu-west-1.convex.site/api"
AG, OW = "test_token_agent", "test_token_owner"

def call(m, p, t, b=None):
    r = urllib.request.Request(S + p, method=m, data=json.dumps(b).encode() if b is not None else None, headers={"Content-Type": "application/json", "Authorization": f"Bearer {t}"})
    try:
        with urllib.request.urlopen(r) as x: return x.status, json.loads(x.read() or b"null")
    except urllib.error.HTTPError as e: return e.code, json.loads(e.read() or b"null")

ok = lambda c, msg: print(("PASS " if c else "FAIL ") + msg)
prod = next(i for i in call("GET", "/my/inventory", AG)[1] if i["quantity"] >= 2)["product_id"]
cust = call("POST", "/customers", AG, {"id": "VT_" + uuid.uuid4().hex[:8], "name": "VT " + uuid.uuid4().hex[:4], "phone": "+963922" + str(uuid.uuid4().int)[:6], "address": "test", "location": "test", "lat": 33.5, "lng": 36.3})[1]
sid = uuid.uuid4().hex
ok(call("POST", "/sales", AG, {"id": sid, "customer_id": cust["id"], "items": [{"product_id": prod, "quantity": 2, "unit": "PIECE"}], "paid_amount": 0})[0] == 200, "sale")
ok(call("POST", "/sales-returns", AG, {"id": uuid.uuid4().hex, "customer_id": cust["id"], "items": [{"product_id": prod, "quantity": 2}]})[0] == 200, "return")
routes = [l for l in open("/app/frontend/convex/http.ts").read().splitlines() if "voidSale" in l]
path = routes[0].split('"')[3].replace(":id", sid) if routes else f"/sales/{sid}/void"
method = routes[0].split('"')[1] if routes else "POST"
st, r = call(method, path, OW, {"reason": "test"})
ok(st == 400, f"void blocked when returns exist ({st} {r})")
# a sale without returns can still be voided
sid2 = uuid.uuid4().hex
call("POST", "/sales", AG, {"id": sid2, "customer_id": cust["id"], "items": [{"product_id": prod, "quantity": 1, "unit": "PIECE"}], "paid_amount": 0})
st, r = call(method, path.replace(sid, sid2), OW, {"reason": "test"})
ok(st == 200, f"void allowed without returns ({st})")
c = next(x for x in call("GET", "/customers", AG)[1] if x["id"] == cust["id"])
ok(abs(c["balance"]) < 0.01, f"balance consistent ({c['balance']})")
