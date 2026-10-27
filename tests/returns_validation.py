"""Returns validation + idempotency + isolation checks against the live Convex API."""
import json, urllib.request, uuid, concurrent.futures as cf
S = "https://fearless-ostrich-878.eu-west-1.convex.site/api"
AG, OW, AC = "test_token_agent", "test_token_owner", "test_token_acct"

def call(m, p, t, b=None):
    r = urllib.request.Request(S + p, method=m, data=json.dumps(b).encode() if b is not None else None, headers={"Content-Type": "application/json", "Authorization": f"Bearer {t}"})
    try:
        with urllib.request.urlopen(r) as x: return x.status, json.loads(x.read() or b"null")
    except urllib.error.HTTPError as e: return e.code, json.loads(e.read() or b"null")

ok = lambda c, msg: print(("PASS " if c else "FAIL ") + msg)
inv = call("GET", "/my/inventory", AG)[1]
prod = next(i for i in inv if i["quantity"] >= 3)["product_id"]
st, cust = call("POST", "/customers", AG, {"id": "RT_" + uuid.uuid4().hex[:8], "name": "RT customer " + uuid.uuid4().hex[:4], "phone": "+963911" + str(uuid.uuid4().int)[:6], "address": "Damascus test", "location": "test", "lat": 33.5, "lng": 36.3})
cid = cust["id"]
bal0 = cust.get("balance", 0)
# 1. return without any sale -> rejected
st, r = call("POST", "/sales-returns", AG, {"id": uuid.uuid4().hex, "customer_id": cid, "items": [{"product_id": prod, "quantity": 1}]})
ok(st == 400, f"return of unsold product rejected ({r})")
# 2. sell 2 pieces
sid = uuid.uuid4().hex
st, sale = call("POST", "/sales", AG, {"id": sid, "customer_id": cid, "items": [{"product_id": prod, "quantity": 2, "unit": "PIECE"}], "paid_amount": 0})
ok(st == 200, f"sale created {st} {str(sale)[:80] if st != 200 else ''}")
st2, sale2 = call("POST", "/sales", AG, {"id": sid, "customer_id": cid, "items": [{"product_id": prod, "quantity": 2, "unit": "PIECE"}], "paid_amount": 0})
ok(st2 == 200 and sale2.get("id") == sid, "sale replay with same id is idempotent")
ok(len([s for s in call("GET", "/sales", AG)[1] if s["id"] == sid]) == 1, "no duplicate sale stored")
# 3. over-limit return rejected
st, r = call("POST", "/sales-returns", AG, {"id": uuid.uuid4().hex, "customer_id": cid, "items": [{"product_id": prod, "quantity": 3}]})
ok(st == 400, f"return 3 > sold 2 rejected ({r.get('detail')})")
st, r = call("POST", "/sales-returns", AG, {"id": uuid.uuid4().hex, "customer_id": cid, "items": [{"product_id": prod, "quantity": -1}]})
ok(st == 400, "negative quantity rejected")
# 4. concurrent returns of 2 x 2 pieces: only one may succeed
ids = [uuid.uuid4().hex for _ in range(4)]
with cf.ThreadPoolExecutor(4) as ex:
    res = list(ex.map(lambda i: call("POST", "/sales-returns", AG, {"id": i, "customer_id": cid, "items": [{"product_id": prod, "quantity": 2}]}), ids))
okc = [r for r in res if r[0] == 200]
ok(len(okc) == 1, f"concurrent over-limit returns: {len(okc)} accepted of 4")
# 5. replay accepted return id -> same doc, no extra effect
rid = okc[0][1]["id"] if okc else ids[0]
st, r = call("POST", "/sales-returns", AG, {"id": rid, "customer_id": cid, "items": [{"product_id": prod, "quantity": 2}]})
ok(st == 200 and r["id"] == rid, "return replay idempotent")
ok(len([x for x in call("GET", "/sales-returns", AG)[1] if x["customer_id"] == cid]) == 1, "only one return stored")
c = next(x for x in call("GET", "/customers", AG)[1] if x["id"] == cid)
ok(abs(c["balance"] - bal0) < 0.01, f"customer balance back to start after sale+full return ({bal0} -> {c['balance']})")
# 6. isolation: accountant cannot create returns; other-org/unknown customer rejected
ok(call("POST", "/sales-returns", AC, {"id": uuid.uuid4().hex, "customer_id": cid, "items": [{"product_id": prod, "quantity": 1}]})[0] in (401, 403), "accountant cannot create returns")
ok(call("POST", "/sales-returns", AG, {"id": uuid.uuid4().hex, "customer_id": "nope_" + uuid.uuid4().hex, "items": [{"product_id": prod, "quantity": 1}]})[0] in (400, 404), "unknown customer rejected")
ok(call("GET", f"/customers/{cid}/statement", AC)[0] == 200, "accountant (staff) can read statements")
