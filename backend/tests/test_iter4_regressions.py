# Iteration 4 regressions: dev plan update unknown id, distributor-limit message for max=1
import os
import pytest
import requests

BASE = os.environ["CONVEX_SITE_URL"].rstrip("/") + "/api"
DEV = {"Authorization": "Bearer test_token_dev"}
OWNER = {"Authorization": "Bearer test_token_owner"}
BASELINE = {"plan_tier": "PRO", "modules": ["reports", "targets", "routes", "tracking", "daily_sms", "debt_sms"],
            "max_distributors": None, "max_employees": 15}


# Dev plans: PUT unknown id must be an error (not 200 ok)
def test_put_unknown_plan_returns_error():
    r = requests.put(f"{BASE}/dev/plans/unknown-id", json={"name": "TEST_x", "price": 1}, headers=DEV, timeout=30)
    print(r.status_code, r.text[:200])
    assert r.status_code >= 400
    assert "الخطة غير موجودة" in r.text


# Distributor limit: when max_distributors == 1 message reads singular form
def test_distributor_limit_message_singular():
    r = requests.patch(f"{BASE}/dev/orgs/org_test_1", json={"max_distributors": 1}, headers=DEV, timeout=30)
    assert r.status_code == 200, r.text
    try:
        inv = requests.post(f"{BASE}/employees/invite", json={"name": "TEST_limit", "employee_type": "FIELD_AGENT"},
                            headers=OWNER, timeout=30)
        print(inv.status_code, inv.text[:300])
        assert inv.status_code >= 400
        assert "خطتك تسمح بموزع واحد فقط" in inv.text
    finally:
        requests.patch(f"{BASE}/dev/orgs/org_test_1", json=BASELINE, headers=DEV, timeout=30)


# Dev orgs list: orgs without owner email have null owner_email (UI shows 'بدون مالك')
def test_dev_orgs_list_owner_email_null_or_str():
    r = requests.get(f"{BASE}/dev/orgs", headers=DEV, timeout=30)
    assert r.status_code == 200
    data = r.json()
    items = data if isinstance(data, list) else data.get("items", data.get("orgs", []))
    assert len(items) > 0
    vals = [o.get("owner_email") for o in items]
    print("owner_email values:", vals[:10])
    assert all(v is None or isinstance(v, str) for v in vals)
