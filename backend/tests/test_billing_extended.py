# Billing / subscription extended regression tests (Convex HTTP API)
import base64, os, struct, uuid, zlib
import pytest
import requests

S = "https://fearless-ostrich-878.eu-west-1.convex.site/api"
D, O, A, G = "test_token_dev", "test_token_owner", "test_token_acct", "test_token_agent"
STATE = {}


def call(method, path, token=None, body=None):
    h = {"Content-Type": "application/json"}
    if token:
        h["Authorization"] = f"Bearer {token}"
    r = requests.request(method, S + path, json=body, headers=h, timeout=60)
    try:
        return r.status_code, r.json()
    except Exception:
        return r.status_code, None


def png():
    raw = b"".join(b"\x00" + os.urandom(60) for _ in range(20))
    def chunk(t, d): return struct.pack(">I", len(d)) + t + d + struct.pack(">I", zlib.crc32(t + d) & 0xffffffff)
    return b"\x89PNG\r\n\x1a\n" + chunk(b"IHDR", struct.pack(">IIBBBBB", 20, 20, 8, 2, 0, 0, 0)) + chunk(b"IDAT", zlib.compress(raw)) + chunk(b"IEND", b"")


def pdf(js=False):
    extra = b"/OpenAction << /S /JavaScript /JS (app.alert(1)) >>" if js else b""
    return (b"%PDF-1.4\n1 0 obj << /Type /Catalog /Pages 2 0 R " + extra + b" >> endobj\n"
            b"2 0 obj << /Type /Pages /Kids [3 0 R] /Count 1 >> endobj\n"
            b"3 0 obj << /Type /Page /Parent 2 0 R /MediaBox [0 0 200 200] >> endobj\n"
            b"trailer << /Root 1 0 R >>\n%%EOF\n")


b64 = lambda b: base64.b64encode(b).decode()


def submit(receipt):
    body = {"plan_id": STATE["pid"], "billing": "monthly", "method_id": STATE["mid"], "amount": 10,
            "payment_ref": "TX-EXT", "idem_key": str(uuid.uuid4()), "receipt": b64(receipt)}
    return call("POST", "/upgrade-requests", O, body)


def owner_req(rid):
    st, lst = call("GET", "/upgrade-requests", O)
    return next((x for x in lst if x["id"] == rid), None)


@pytest.fixture(scope="module", autouse=True)
def setup_plan():
    # cancel any leftover open owner request
    st, lst = call("GET", "/upgrade-requests", O)
    for x in lst or []:
        if x.get("status") in ("PENDING", "UNDER_REVIEW", "NEEDS_INFO"):
            call("POST", f"/upgrade-requests/{x['id']}/cancel", O)
    st, p = call("POST", "/dev/plans", D, {"name": "TEST_EXT Pro", "tier": "PRO", "price": 10, "currency": "USD", "days": 30,
                                           "grace_days": 3, "max_employees": 10, "modules": ["reports"]})
    assert st == 200, p
    STATE["pid"] = p["id"]
    assert call("POST", f"/dev/plans/{p['id']}/publish", D)[0] == 200
    st, m = call("POST", "/dev/payment-methods", D, {"name": "TEST_EXT Bank", "kind": "bank", "currency": "USD",
                                                     "account": "IBAN-EXT", "plan_ids": [p["id"]]})
    assert st == 200, m
    STATE["mid"] = m["id"]
    yield
    call("POST", f"/dev/plans/{STATE['pid']}/archive", D, {})
    call("DELETE", f"/dev/payment-methods/{STATE['mid']}", D)
    call("PATCH", "/dev/orgs/org_test_1", D, {"status": "ACTIVE", "modules": ["reports", "targets", "routes", "tracking", "daily_sms", "debt_sms"],
                                               "max_employees": 10, "max_distributors": None, "max_customers": None})


# --- receipts: PDF validation
def test_pdf_with_javascript_rejected():
    st, r = submit(pdf(js=True))
    assert st == 400 and "PDF" in r["detail"], r


def test_clean_pdf_accepted():
    st, r = submit(pdf())
    assert st == 200 and r["status"] == "PENDING", r
    STATE["rid"] = r["id"]
    st, rc = call("GET", f"/upgrade-requests/{r['id']}/receipt", O)
    assert st == 200 and rc["data_uri"].startswith("data:application/pdf"), rc


# --- NEEDS_INFO -> owner resubmit -> PENDING
def test_needs_info_requires_note():
    st, r = call("PATCH", f"/dev/upgrade-requests/{STATE['rid']}", D, {"action": "needs_info"})
    assert st == 400


def test_needs_info_then_resubmit():
    st, r = call("PATCH", f"/dev/upgrade-requests/{STATE['rid']}", D, {"action": "needs_info", "note": "TEST unclear receipt"})
    assert st == 200 and r.get("status") == "NEEDS_INFO", r
    assert owner_req(STATE["rid"])["status"] == "NEEDS_INFO"
    st, r = call("POST", f"/upgrade-requests/{STATE['rid']}/receipt", O, {"receipt": b64(png()), "payment_ref": "TX-EXT-2"})
    assert st == 200, r
    assert owner_req(STATE["rid"])["status"] == "PENDING"


# --- owner cancel
def test_owner_cancel():
    st, r = call("POST", f"/upgrade-requests/{STATE['rid']}/cancel", O)
    assert st == 200, r
    assert owner_req(STATE["rid"])["status"] == "CANCELLED"
    assert call("POST", f"/upgrade-requests/{STATE['rid']}/cancel", O)[0] == 400


def test_refund_not_allowed_from_cancelled():
    st, r = call("PATCH", f"/dev/upgrade-requests/{STATE['rid']}", D, {"action": "refund", "note": "x"})
    assert st == 400


# --- refund only from APPROVED, needs note
def test_approve_then_refund():
    st, r = submit(png())
    assert st == 200, r
    rid = r["id"]
    assert call("PATCH", f"/dev/upgrade-requests/{rid}", D, {"action": "approve"})[0] == 200
    assert call("PATCH", f"/dev/upgrade-requests/{rid}", D, {"action": "refund"})[0] == 400
    st, r = call("PATCH", f"/dev/upgrade-requests/{rid}", D, {"action": "refund", "note": "TEST refund"})
    assert st == 200 and r.get("status") == "REFUNDED", r
    assert owner_req(rid)["status"] == "REFUNDED"
    STATE["refunded"] = rid


# --- plan versions + restore
def test_plan_versions_and_restore():
    pid = STATE["pid"]
    assert call("PUT", f"/dev/plans/{pid}", D, {"name": "TEST_EXT Pro v2", "tier": "PRO", "price": 20, "currency": "USD"})[0] == 200
    assert call("POST", f"/dev/plans/{pid}/publish", D)[0] == 200
    st, vs = call("GET", f"/dev/plans/{pid}/versions", D)
    assert st == 200 and len(vs) >= 2, vs
    STATE["versions"] = vs
    st, r = call("POST", f"/dev/plans/{pid}/restore", D, {"version": 1})
    assert st == 200, r
    st, lst = call("GET", "/dev/plans", D) if False else call("GET", "/plans", D)
    p = next((x for x in lst if x["id"] == pid), None)
    STATE["after_restore"] = p
    assert p is not None


# --- resource limits enforced on backend
def test_customer_limit():
    st, o = call("GET", "/dev/orgs/org_test_1", D)
    n = o["usage"]["customers"]
    assert call("PATCH", "/dev/orgs/org_test_1", D, {"max_customers": n})[0] == 200
    st, r = call("POST", "/customers", G, {"name": "TEST_limit cust", "phone": "+963911111199"})
    call("PATCH", "/dev/orgs/org_test_1", D, {"max_customers": None})
    assert st == 400 and "عميل" in (r or {}).get("detail", ""), (st, r)


def test_distributor_limit():
    st, o = call("GET", "/dev/orgs/org_test_1", D)
    n = o["usage"]["distributors"]
    assert call("PATCH", "/dev/orgs/org_test_1", D, {"max_distributors": n})[0] == 200
    st, r = call("POST", "/employees/invite", O, {"name": "TEST_limit agent", "employee_type": "FIELD_AGENT"})
    call("PATCH", "/dev/orgs/org_test_1", D, {"max_distributors": None})
    if st == 200 and r and r.get("id"):
        call("DELETE", f"/employees/invite/{r['id']}", O)
    assert st == 400 and "موزع" in (r or {}).get("detail", ""), (st, r)


# --- RBAC: non-developer tokens get 403 on /dev/* billing endpoints
DEV_EPS = [("POST", "/dev/plans", {"name": "x", "price": 1}), ("PUT", "/dev/plans/PID", {"name": "x", "price": 1}),
           ("POST", "/dev/plans/PID/publish", {}), ("POST", "/dev/plans/PID/archive", {}),
           ("GET", "/dev/plans/PID/versions", None), ("POST", "/dev/plans/PID/restore", {"version": 1}),
           ("POST", "/dev/payment-methods", {"name": "x"}), ("DELETE", "/dev/payment-methods/MID", None),
           ("POST", "/dev/payment-methods/MID/qr", {"data": ""}), ("PUT", "/dev/billing/settings", {}),
           ("GET", "/dev/billing/stats", None), ("GET", "/dev/audit", None), ("GET", "/dev/orgs/org_test_1", None),
           ("POST", "/dev/orgs/org_test_1/assign-plan", {"plan_id": "PID", "days": 30}),
           ("PATCH", "/dev/upgrade-requests/RID", {"action": "approve"}), ("PATCH", "/dev/orgs/org_test_1", {"status": "ACTIVE"}),
           ("GET", "/dev/orgs", None)]


@pytest.mark.parametrize("tok", [O, A, G])
def test_non_dev_forbidden(tok):
    bad = []
    for m, p, b in DEV_EPS:
        p = p.replace("PID", STATE["pid"]).replace("MID", STATE["mid"]).replace("RID", STATE.get("refunded", "x"))
        st, _ = call(m, p, tok, b)
        if st != 403:
            bad.append((m, p, st))
    assert not bad, bad
