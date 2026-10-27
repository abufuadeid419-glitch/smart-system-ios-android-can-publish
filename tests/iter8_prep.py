# Prep data for iteration-8 UI offline-ordering tests: prints JSON with ids + queue payloads
import json, uuid, requests
S = "https://fearless-ostrich-878.eu-west-1.convex.site/api"
H = {"Authorization": "Bearer test_token_agent"}
prod = next(i for i in requests.get(S + "/my/inventory", headers=H).json() if i["quantity"] >= 6)["product_id"]
# debtor customer for the collection (online/offline event) test
cb = {"id": "TEST_UIB_" + uuid.uuid4().hex[:6], "name": "TEST_UIB " + uuid.uuid4().hex[:4], "phone": "+963944" + str(uuid.uuid4().int)[:6], "address": "t", "location": "t", "lat": 33.5, "lng": 36.3}
assert requests.post(S + "/customers", headers=H, json=cb).status_code == 200
assert requests.post(S + "/sales", headers=H, json={"id": uuid.uuid4().hex, "customer_id": cb["id"], "items": [{"product_id": prod, "quantity": 1, "unit": "PIECE"}], "paid_amount": 0}).status_code == 200
now = "2026-01-01T00:00:00.000Z"
cid, sid, rid, colid, badrid = "TEST_UIA_" + uuid.uuid4().hex[:6], uuid.uuid4().hex, uuid.uuid4().hex, uuid.uuid4().hex, uuid.uuid4().hex
cust = {"id": cid, "name": "TEST_UIA " + cid[-4:], "phone": "+963955" + str(uuid.uuid4().int)[:6], "address": "t", "location": "t", "lat": 33.5, "lng": 36.3}
qa = [
    {"id": rid, "path": "/sales-returns", "body": {"id": rid, "customer_id": cid, "items": [{"product_id": prod, "quantity": 1}]}, "label": "مرتجع · TEST", "attempts": 0, "created_at": now},
    {"id": sid, "path": "/sales", "body": {"id": sid, "customer_id": cid, "items": [{"product_id": prod, "quantity": 2, "unit": "PIECE"}], "paid_amount": 0}, "label": "فاتورة · TEST", "attempts": 0, "created_at": now},
    {"id": badrid, "path": "/sales-returns", "body": {"id": badrid, "customer_id": cid, "items": [{"product_id": prod, "quantity": 999}]}, "label": "مرتجع زائد · TEST", "attempts": 0, "created_at": now},
    {"id": cid, "path": "/customers", "body": cust, "label": "عميل جديد · TEST", "attempts": 1, "next_attempt_at": "__FUTURE__", "created_at": now},
]
qb = [{"id": colid, "path": "/collections", "body": {"id": colid, "customer_id": cb["id"], "amount": 1}, "label": "تحصيل · TEST", "attempts": 0, "created_at": now}]
print(json.dumps({"prod": prod, "cid": cid, "sid": sid, "rid": rid, "badrid": badrid, "cb": cb["id"], "colid": colid, "qa": qa, "qb": qb}, ensure_ascii=False))
