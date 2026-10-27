import base64, json, urllib.request, uuid, struct, zlib
S = "https://fearless-ostrich-878.eu-west-1.convex.site/api"

def call(method, path, token=None, body=None):
    req = urllib.request.Request(S + path, method=method, data=json.dumps(body).encode() if body is not None else None, headers={"Content-Type": "application/json", **({"Authorization": f"Bearer {token}"} if token else {})})
    try:
        with urllib.request.urlopen(req) as r:
            return r.status, json.loads(r.read() or b"null")
    except urllib.error.HTTPError as e:
        return e.code, json.loads(e.read() or b"null")

def png():
    import os; raw = b"".join(b"\x00" + os.urandom(60) for _ in range(20))
    def chunk(t, d): return struct.pack(">I", len(d)) + t + d + struct.pack(">I", zlib.crc32(t + d) & 0xffffffff)
    return b"\x89PNG\r\n\x1a\n" + chunk(b"IHDR", struct.pack(">IIBBBBB", 20, 20, 8, 2, 0, 0, 0)) + chunk(b"IDAT", zlib.compress(raw)) + chunk(b"IEND", b"")

D, O, A = "test_token_dev", "test_token_owner", "test_token_acct"
st, p = call("POST", "/dev/plans", D, {"name": "SMOKE Pro", "tier": "PRO", "price": 10, "yearly_price": 100, "currency": "USD", "days": 30, "grace_days": 3, "max_employees": 8, "max_distributors": 4, "modules": ["reports"]}); print("create plan", st, p.get("status"))
pid = p["id"]
st, lst = call("GET", "/plans", O); print("owner sees draft?", any(x["id"] == pid for x in lst))
print("publish", call("POST", f"/dev/plans/{pid}/publish", D))
st, lst = call("GET", "/plans", O); print("owner sees published?", any(x["id"] == pid for x in lst))
print("owner create plan forbidden", call("POST", "/dev/plans", O, {"name": "x", "price": 1})[0])
st, m = call("POST", "/dev/payment-methods", D, {"name": "SMOKE Bank", "kind": "bank", "currency": "USD", "account": "IBAN-TEST", "instructions": "transfer", "plan_ids": [pid]}); print("method", st)
mid = m["id"]
print("qr upload", call("POST", f"/dev/payment-methods/{mid}/qr", D, {"data": base64.b64encode(png()).decode()}))
print("qr bad file", call("POST", f"/dev/payment-methods/{mid}/qr", D, {"data": base64.b64encode(b"<html>" * 50).decode()}))
st, ms = call("GET", "/payment-methods", O); print("owner methods qr_url", [bool(x.get("qr_url")) for x in ms if x["id"] == mid], "no storage leak", all("qr_storage" not in x for x in ms))
key = str(uuid.uuid4())
body = {"plan_id": pid, "billing": "monthly", "method_id": mid, "amount": 10, "payment_ref": "TX123", "idem_key": key}
print("no receipt", call("POST", "/upgrade-requests", O, body))
body["receipt"] = base64.b64encode(png()).decode()
st, r = call("POST", "/upgrade-requests", O, body); print("submit", st, r.get("status"), r.get("ref_code"), r.get("price"))
st, r2 = call("POST", "/upgrade-requests", O, body); print("dup same key", st, r2.get("id") == r.get("id"), r2.get("duplicate"))
body["idem_key"] = str(uuid.uuid4())
print("second open request", call("POST", "/upgrade-requests", O, body))
rid = r["id"]
print("acct receipt forbidden", call("GET", f"/upgrade-requests/{rid}/receipt", A)[0])
st, rc = call("GET", f"/upgrade-requests/{rid}/receipt", O); print("owner receipt", st, (rc.get("data_uri") or "")[:22])
st, me = call("GET", "/auth/me", O); print("org before approve", me["org"].get("plan"), me["org"].get("plan_name"))
print("price change", call("PUT", f"/dev/plans/{pid}", D, {"name": "SMOKE Pro", "tier": "PRO", "price": 99, "currency": "USD"})[0])
print("reject no reason", call("PATCH", f"/dev/upgrade-requests/{rid}", D, {"action": "reject"}))
st, ap = call("PATCH", f"/dev/upgrade-requests/{rid}", D, {"action": "approve"}); print("approve", st, ap.get("status"), ap.get("price"))
print("approve again", call("PATCH", f"/dev/upgrade-requests/{rid}", D, {"action": "approve"}))
st, me = call("GET", "/auth/me", O); o = me["org"]; print("org after", o.get("plan"), o.get("plan_name"), o.get("max_employees"), o.get("max_distributors"), o.get("expires_at"), o.get("grace_until"))
st, au = call("GET", "/dev/audit", D); print("audit", st, [x["action"] for x in au[:6]])
print("stats", call("GET", "/dev/billing/stats", D))
print("org detail", call("GET", "/dev/orgs/org_test_1", D)[1].get("usage"))
print("archive plan", call("POST", f"/dev/plans/{pid}/archive", D, {})[0], "archive method", call("DELETE", f"/dev/payment-methods/{mid}", D)[0])
