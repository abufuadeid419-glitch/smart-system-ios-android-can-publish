# Extra billing edge cases (exploratory): assign plan, amount mismatch, oversize/foreign receipt, refund effect
import sys, json, uuid, base64
sys.path.insert(0, "/app/backend/tests")
from test_billing_extended import call, png, pdf, D, O, A, G

s = json.load(open("/tmp/ui_billing.json")); pid, mid = s["pid"], s["mid"]
b64 = lambda b: base64.b64encode(b).decode()
print("me ok", call("GET", "/auth/me", O)[0])
# assign plan manually
st, r = call("POST", "/dev/orgs/org_test_1/assign-plan", D, {"plan_id": pid, "days": 30, "note": "TEST assign"})
print("assign", st, str(r)[:200])
st, me = call("GET", "/auth/me", O); o = me["org"]; print("org after assign", o.get("plan_name"), o.get("expires_at"))
print("assign bad days", call("POST", "/dev/orgs/org_test_1/assign-plan", D, {"plan_id": pid, "days": -5}))
print("assign archived/unknown plan", call("POST", "/dev/orgs/org_test_1/assign-plan", D, {"plan_id": "nope", "days": 30}))
# amount lower than price
body = {"plan_id": pid, "billing": "monthly", "method_id": mid, "amount": 1, "payment_ref": "TX-LOW", "idem_key": str(uuid.uuid4()), "receipt": b64(png())}
st, r = call("POST", "/upgrade-requests", O, body); print("underpay submit", st, r.get("status") if isinstance(r, dict) else r, r.get("detail") if isinstance(r, dict) else "")
if st == 200:
    print("cancel", call("POST", f"/upgrade-requests/{r['id']}/cancel", O)[0])
# oversize receipt
big = png() + b"\x00" * (5 * 1024 * 1024)
body.update({"amount": 17, "idem_key": str(uuid.uuid4()), "receipt": b64(big)})
print("oversize", call("POST", "/upgrade-requests", O, body))
# yearly billing price
body.update({"billing": "yearly", "amount": 150, "idem_key": str(uuid.uuid4()), "receipt": b64(png())})
st, r = call("POST", "/upgrade-requests", O, body); print("yearly", st, r.get("price") if isinstance(r, dict) else r, r.get("days") if isinstance(r, dict) else "")
if st == 200:
    # agent / accountant cannot cancel owner request; agent cannot submit
    print("acct cancel", call("POST", f"/upgrade-requests/{r['id']}/cancel", A)[0])
    print("agent list requests", call("GET", "/upgrade-requests", G)[0])
    print("dev under_review", call("PATCH", f"/dev/upgrade-requests/{r['id']}", D, {"action": "under_review"})[1].get("status"))
    print("owner cancel UNDER_REVIEW", call("POST", f"/upgrade-requests/{r['id']}/cancel", O))
print("agent submit", call("POST", "/upgrade-requests", G, {**body, "idem_key": str(uuid.uuid4())})[0])
print("unknown action", call("PATCH", "/dev/upgrade-requests/xyz", D, {"action": "foo"}))
print("free plan publish dup check / restore bad version", call("POST", f"/dev/plans/{pid}/restore", D, {"version": 999}))
