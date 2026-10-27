# Setup/teardown helper for billing UI tests: python3 ui_billing_setup.py setup|teardown
import sys, json, base64
sys.path.insert(0, "/app/backend/tests")
from test_billing_extended import call, png, D, O

if sys.argv[1] == "setup":
    print(call("PUT", "/dev/billing/settings", D, {"allow_resubmit": True, "max_receipt_mb": 4, "max_requests_per_day": 50, "reminder_days": 7}))
    st, lst = call("GET", "/upgrade-requests", O)
    for x in lst or []:
        if x.get("status") in ("PENDING", "UNDER_REVIEW", "NEEDS_INFO"):
            call("POST", f"/upgrade-requests/{x['id']}/cancel", O)
    st, p = call("POST", "/dev/plans", D, {"name": "TEST_UI Pro", "tier": "PRO", "price": 15, "yearly_price": 150, "currency": "USD", "days": 30, "max_employees": 10, "modules": ["reports"]})
    call("POST", f"/dev/plans/{p['id']}/publish", D)
    st, m = call("POST", "/dev/payment-methods", D, {"name": "TEST_UI Bank", "kind": "bank", "currency": "USD", "account": "IBAN-UI-123", "instructions": "حوّل المبلغ", "plan_ids": [p["id"]]})
    call("POST", f"/dev/payment-methods/{m['id']}/qr", D, {"data": base64.b64encode(png()).decode()})
    json.dump({"pid": p["id"], "mid": m["id"]}, open("/tmp/ui_billing.json", "w"))
    print("setup", p["id"], m["id"])
else:
    s = json.load(open("/tmp/ui_billing.json"))
    st, lst = call("GET", "/upgrade-requests", O)
    for x in lst or []:
        if x.get("status") in ("PENDING", "UNDER_REVIEW", "NEEDS_INFO"):
            print("cancel", x["id"], call("POST", f"/upgrade-requests/{x['id']}/cancel", O)[0])
    print(call("POST", f"/dev/plans/{s['pid']}/archive", D, {})[0], call("DELETE", f"/dev/payment-methods/{s['mid']}", D)[0])
    for pl in call("GET", "/plans", D)[1]:
        if pl["name"].startswith("TEST_") and pl.get("status") != "archived":
            print("archive leftover", pl["name"], call("POST", f"/dev/plans/{pl['id']}/archive", D, {})[0])
    print(call("PUT", "/dev/billing/settings", D, {"allow_resubmit": True, "max_receipt_mb": 4, "max_requests_per_day": 5, "reminder_days": 7}))
    print(call("PATCH", "/dev/orgs/org_test_1", D, {"status": "ACTIVE", "modules": ["reports", "targets", "routes", "tracking", "daily_sms", "debt_sms"], "max_employees": 10, "max_distributors": None, "max_customers": None}))
