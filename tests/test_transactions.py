def test_ingest_and_fetch(client):
    payload = {
        "id": "tx_001",
        "customer_id": "c_001",
        "category": "WEB".replace("WEB","CARD"),  # ensure allowed category
        "amount": "12000.00",
        "currency": "ZAR",
        "merchant": "Some Shop",
        "country": "NG",
        "channel": "WEB",
        "event_time": "2026-02-07T10:00:00+02:00"
    }

    r = client.post("/api/v1/transactions", json=payload)
    assert r.status_code == 201
    data = r.get_json()
    assert data["transaction_id"] == "tx_001"
    assert data["fraud_score"] >= 60
    assert data["is_flagged"] is True

    r2 = client.get("/api/v1/transactions/tx_001")
    assert r2.status_code == 200
    out = r2.get_json()
    assert out["transaction"]["id"] == "tx_001"
    assert len(out["hits"]) >= 1
