# Iteration 3: change-password, developer-controlled plans (Pro/VIP), org limits, distributor cap, feature gating
# Live Convex HTTP API. Run serially: pytest -p no:xdist
import os
import pytest
import requests


def _site_url():
    url = os.environ.get("EXPO_PUBLIC_CONVEX_SITE_URL")
    if not url:
        for line in open("/app/frontend/.env"):
            if line.startswith("EXPO_PUBLIC_CONVEX_SITE_URL="):
                url = line.split("=", 1)[1].strip().strip('"')
    return url.rstrip("/")


BASE = _site_url() + "/api"
ALL = ["reports", "targets", "routes", "tracking", "daily_sms", "debt_sms"]
H = lambda t: {"Authorization": f"Bearer {t}", "Content-Type": "application/json"}
DEV, OWNER, AGENT = H("test_token_dev"), H("test_token_owner"), H("test_token_agent")
ORG = "org_test_1"


def patch_org(body):
    return requests.patch(f"{BASE}/dev/orgs/{ORG}", headers=DEV, json=body)


@pytest.fixture(scope="module", autouse=True)
def restore_org():
    me = requests.get(f"{BASE}/auth/me", headers=OWNER).json()
    orig_max = (me.get("org") or {}).get("max_employees") or 10
    yield
    patch_org({"modules": ALL, "max_distributors": None, "max_employees": orig_max, "status": "ACTIVE"})


# --- change password (agent)
class TestChangePassword:
    def test_wrong_current_shows_remaining(self):
        r = requests.post(f"{BASE}/auth/password/change", headers=AGENT, json={"current": "Wrong9999", "password": "NewPass123"})
        assert r.status_code == 400
        assert "متبقي" in r.json()["detail"]

    def test_weak_new_password_rejected(self):
        r = requests.post(f"{BASE}/auth/password/change", headers=AGENT, json={"current": "Agent12345", "password": "short"})
        assert r.status_code == 400

    def test_same_password_rejected(self):
        r = requests.post(f"{BASE}/auth/password/change", headers=AGENT, json={"current": "Agent12345", "password": "Agent12345"})
        assert r.status_code == 400

    def test_change_and_back_and_login(self):
        r = requests.post(f"{BASE}/auth/password/change", headers=AGENT, json={"current": "Agent12345", "password": "NewPass123"})
        assert r.status_code == 200 and r.json().get("ok") is True, r.text
        # token still valid
        assert requests.get(f"{BASE}/auth/me", headers=AGENT).status_code == 200
        r = requests.post(f"{BASE}/auth/password/change", headers=AGENT, json={"current": "NewPass123", "password": "Agent12345"})
        assert r.status_code == 200, r.text

    def test_no_auth(self):
        r = requests.post(f"{BASE}/auth/password/change", json={"current": "x", "password": "NewPass123"})
        assert r.status_code in (400, 401, 403)


# --- developer plans
class TestDevPlans:
    plan_id = None

    def test_owner_forbidden(self):
        r = requests.post(f"{BASE}/dev/plans", headers=OWNER, json={"name": "TEST_x", "price": 1})
        assert r.status_code in (400, 401, 403)

    def test_invalid_module(self):
        r = requests.post(f"{BASE}/dev/plans", headers=DEV, json={"name": "TEST_bad", "price": 1, "modules": ["reports", "foo"]})
        assert r.status_code == 400

    def test_invalid_tier(self):
        r = requests.post(f"{BASE}/dev/plans", headers=DEV, json={"name": "TEST_bad", "price": 1, "tier": "GOLD"})
        assert r.status_code == 400

    def test_create_vip(self):
        r = requests.post(f"{BASE}/dev/plans", headers=DEV, json={"name": "TEST_VIP", "price": 50, "days": 30, "tier": "VIP",
                                                                  "max_employees": 8, "max_distributors": 3, "modules": ["reports", "routes"]})
        assert r.status_code == 200, r.text
        d = r.json()
        assert d["tier"] == "VIP" and d["max_employees"] == 8 and d["max_distributors"] == 3
        assert sorted(d["modules"]) == ["reports", "routes"]
        TestDevPlans.plan_id = d["id"]

    def test_update_plan(self):
        pid = TestDevPlans.plan_id or pytest.skip("no plan")
        r = requests.put(f"{BASE}/dev/plans/{pid}", headers=DEV, json={"name": "TEST_VIP2", "price": 60, "tier": "PRO",
                                                                       "max_employees": 4, "max_distributors": 9, "modules": ["targets"]})
        assert r.status_code == 200, r.text
        d = r.json()
        assert d["name"] == "TEST_VIP2" and d["tier"] == "PRO" and d["modules"] == ["targets"]
        assert d["max_distributors"] == 4  # clamped to max_employees

    def test_delete_plan(self):
        pid = TestDevPlans.plan_id or pytest.skip("no plan")
        r = requests.delete(f"{BASE}/dev/plans/{pid}", headers=DEV)
        assert r.status_code == 200, r.text


# --- org overrides, distributor cap, gating
class TestOrgControls:
    def test_patch_org_and_me(self):
        r = patch_org({"plan_tier": "VIP", "modules": ["targets", "routes"], "max_employees": 12, "max_distributors": 5})
        assert r.status_code == 200, r.text
        o = requests.get(f"{BASE}/auth/me", headers=OWNER).json()["org"]
        assert o["plan_tier"] == "VIP" and sorted(o["modules"]) == ["routes", "targets"]
        assert o["max_employees"] == 12 and o["max_distributors"] == 5

    def test_patch_org_invalid(self):
        assert patch_org({"modules": ["nope"]}).status_code == 400
        assert patch_org({"plan_tier": "GOLD"}).status_code == 400
        assert requests.patch(f"{BASE}/dev/orgs/{ORG}", headers=OWNER, json={"max_employees": 99}).status_code in (400, 401, 403)

    def test_reports_locked(self):
        r = requests.get(f"{BASE}/stats/reports?period=week", headers=OWNER)
        assert r.status_code == 200 and r.json().get("locked") is True, r.text
        r = requests.get(f"{BASE}/stats/reports?period=day", headers=OWNER)
        assert r.status_code == 200 and not r.json().get("locked")

    def test_debt_sms_locked(self):
        r = requests.put(f"{BASE}/org/debt-sms", headers=OWNER, json={"enabled": True, "days": 14})
        assert r.status_code == 400, r.text

    def test_distributor_cap(self):
        emps = requests.get(f"{BASE}/employees", headers=OWNER).json()
        agents = len([e for e in emps["employees"] if e.get("employee_type") == "FIELD_AGENT"])
        agents += len([i for i in emps["invitations"] if not i.get("used") and i.get("employee_type") == "FIELD_AGENT"])
        assert patch_org({"max_distributors": agents, "max_employees": 15}).status_code == 200
        r = requests.post(f"{BASE}/employees/invite", headers=OWNER, json={"name": "TEST_agent", "employee_type": "FIELD_AGENT"})
        assert r.status_code == 400 and "موزع" in r.json()["detail"], r.text
        r = requests.post(f"{BASE}/employees/invite", headers=OWNER, json={"name": "TEST_acct", "employee_type": "ACCOUNTANT"})
        assert r.status_code == 200, r.text
        assert requests.delete(f"{BASE}/employees/invite/{r.json()['id']}", headers=OWNER).status_code == 200

    def test_restore_all_modules_unlocks(self):
        assert patch_org({"modules": ALL, "max_distributors": None}).status_code == 200
        r = requests.get(f"{BASE}/stats/reports?period=week", headers=OWNER)
        assert not r.json().get("locked")
