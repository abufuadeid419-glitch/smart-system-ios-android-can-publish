# Auth password flow tests against the live Convex HTTP API (fearless-ostrich-878)
# NOTE: never call /auth/start for numbers without a password (sends real SMS)
import os
import json
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
AGENT_PHONE = "+963900000004"
AGENT_PW = "Agent12345"


@pytest.fixture(scope="module")
def s():
    x = requests.Session()
    x.headers.update({"Content-Type": "application/json"})
    return x


def _no_secrets(obj):
    txt = json.dumps(obj).lower()
    return '"hash"' not in txt and '"salt"' not in txt and "code_hash" not in txt


# --- /auth/me
class TestMe:
    def test_me_owner_has_password_field_no_secrets(self, s):
        r = s.get(f"{BASE}/auth/me", headers={"Authorization": "Bearer test_token_owner"})
        assert r.status_code == 200, r.text
        d = r.json()
        assert "has_password" in d and isinstance(d["has_password"], bool)
        assert d.get("phone") == "+963900000002"
        assert _no_secrets(d)

    def test_me_no_token_401(self, s):
        r = s.get(f"{BASE}/auth/me")
        assert r.status_code in (401, 400), r.text


# --- /auth/start
class TestStart:
    def test_start_password_user(self, s):
        r = s.post(f"{BASE}/auth/start", json={"phone": AGENT_PHONE})
        assert r.status_code == 200, r.text
        assert r.json() == {"method": "password"}

    def test_start_invalid_phone(self, s):
        r = s.post(f"{BASE}/auth/start", json={"phone": "12"})
        assert r.status_code == 400
        assert "detail" in r.json()


# --- POST /auth/password (set)
class TestSetPassword:
    def test_too_short_password(self, s):
        r = s.post(f"{BASE}/auth/password", json={"password": "ab1"}, headers={"Authorization": "Bearer test_token_owner"})
        assert r.status_code == 400, r.text
        assert "8" in r.json()["detail"]

    def test_letters_only_password(self, s):
        r = s.post(f"{BASE}/auth/password", json={"password": "abcdefghij"}, headers={"Authorization": "Bearer test_token_owner"})
        assert r.status_code == 400, r.text

    def test_refused_when_password_exists(self, s):
        r = s.post(f"{BASE}/auth/password", json={"password": "NewPass123"}, headers={"Authorization": "Bearer test_token_agent"})
        assert r.status_code == 400, r.text
        assert "SMS" in r.json()["detail"]

    def test_no_token(self, s):
        r = s.post(f"{BASE}/auth/password", json={"password": "NewPass123"})
        assert r.status_code in (400, 401), r.text


# --- POST /auth/password/login
class TestPasswordLogin:
    def test_unknown_phone_generic(self, s):
        r = s.post(f"{BASE}/auth/password/login", json={"phone": "+963900000099", "password": "Whatever123"})
        assert r.status_code == 400, r.text
        assert r.json()["detail"] == "رقم الهاتف أو كلمة المرور غير صحيحة"

    def test_wrong_password_remaining(self, s):
        r = s.post(f"{BASE}/auth/password/login", json={"phone": AGENT_PHONE, "password": "Wrong12345"})
        assert r.status_code == 400, r.text
        assert "متبقي" in r.json()["detail"]

    def test_no_force_conflict(self, s):
        r = s.post(f"{BASE}/auth/password/login", json={"phone": AGENT_PHONE, "password": AGENT_PW})
        assert r.status_code == 400, r.text
        assert r.json()["detail"] == "DEVICE_CONFLICT"

    def test_correct_password_force(self, s):
        r = s.post(f"{BASE}/auth/password/login", json={"phone": AGENT_PHONE, "password": AGENT_PW, "force": True})
        assert r.status_code == 200, r.text
        d = r.json()
        assert isinstance(d.get("session_token"), str) and len(d["session_token"]) >= 32
        assert d["user"]["has_password"] is True
        assert _no_secrets(d)
        me = s.get(f"{BASE}/auth/me", headers={"Authorization": f"Bearer {d['session_token']}"})
        assert me.status_code == 200 and me.json()["phone"] == AGENT_PHONE
        assert _no_secrets(me.json())
        # old seeded token must be revoked by force takeover
        old = s.get(f"{BASE}/auth/me", headers={"Authorization": "Bearer test_token_agent"})
        assert old.status_code == 401, old.text
