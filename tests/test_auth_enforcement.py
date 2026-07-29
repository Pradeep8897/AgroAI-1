import os
os.environ.setdefault("JWT_SECRET_KEY", "testsecret")

from backend.app import app as flask_app


def test_protected_endpoints_require_auth():
    client = flask_app.test_client()

    resp = client.post("/api/profit/optimize", json={})
    assert resp.status_code == 401

    resp = client.post("/api/crop/recommend", json={})
    assert resp.status_code == 401

    resp = client.post("/api/market/predict", json={})
    assert resp.status_code == 401

    resp = client.post("/api/equipment", json={})
    assert resp.status_code == 401


def test_public_auth_endpoints_allow_access_without_token():
    client = flask_app.test_client()

    resp = client.post("/api/auth/register", json={"username": "t", "email": "t@example.com", "password": "p"})
    assert resp.status_code != 401

    resp = client.post("/api/auth/login", json={"email": "noone@example.com", "password": "x"})
    assert resp.status_code != 401
