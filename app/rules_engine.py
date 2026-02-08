from decimal import Decimal
from .models import FraudRule

def apply_rules(tx_payload: dict, rules: list[FraudRule]) -> list[dict]:
    """
    Returns a list of hits: {rule_code, rule_name, score, reason}
    """
    hits = []
    amount = Decimal(str(tx_payload["amount"]))
    category = tx_payload.get("category")
    country = (tx_payload.get("country") or "").upper()

    for r in rules:
        if not r.enabled:
            continue
        if r.category and r.category != category:
            continue

        # Rule: min_amount
        if r.min_amount is not None and amount >= Decimal(str(r.min_amount)):
            hits.append({
                "rule_code": r.code,
                "rule_name": r.name,
                "score": int(r.score),
                "reason": f"Amount {amount} >= min_amount {r.min_amount}"
            })

        # Rule: country blocklist
        if r.country_blocklist:
            blocked = {c.strip().upper() for c in r.country_blocklist.split(",") if c.strip()}
            if country and country in blocked:
                hits.append({
                    "rule_code": r.code,
                    "rule_name": r.name,
                    "score": int(r.score),
                    "reason": f"Country {country} is blocked"
                })

    # Built-in baseline heuristics (example)
    if tx_payload.get("channel") == "WEB" and amount >= Decimal("5000"):
        hits.append({
            "rule_code": "HEUR_WEB_HIGH",
            "rule_name": "High-value web transaction",
            "score": 25,
            "reason": "WEB channel with amount >= 5000"
        })

    if tx_payload.get("category") == "ATM" and amount >= Decimal("3000"):
        hits.append({
            "rule_code": "HEUR_ATM_HIGH",
            "rule_name": "High ATM withdrawal",
            "score": 25,
            "reason": "ATM category with amount >= 3000"
        })

    return hits
