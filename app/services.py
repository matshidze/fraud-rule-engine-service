from decimal import Decimal
from .extensions import db
from .models import Transaction, RuleHit, FraudRule
from .rules_engine import apply_rules
from flask import current_app

def ensure_seed_rules():
    # seed only if empty
    if FraudRule.query.count() > 0:
        return
    seeds = [
        FraudRule(code="AMT_10K", name="Amount >= 10000", enabled=True, category=None, min_amount=Decimal("10000"), score=40),
        FraudRule(code="BLOCK_COUNTRY", name="Blocked countries", enabled=True, category=None, country_blocklist="NG,RU", score=60),
    ]
    db.session.add_all(seeds)
    db.session.commit()

def process_transaction(payload: dict) -> dict:
    rules = FraudRule.query.filter_by(enabled=True).all()
    hits = apply_rules(payload, rules)
    total_score = sum(h["score"] for h in hits)
    threshold = int(current_app.config["FRAUD_SCORE_THRESHOLD"])
    flagged = total_score >= threshold

    tx = Transaction(
        id=payload["id"],
        customer_id=payload["customer_id"],
        category=payload["category"],
        amount=payload["amount"],
        currency=payload["currency"],
        merchant=payload.get("merchant"),
        country=(payload.get("country") or None),
        channel=payload.get("channel"),
        device_id=payload.get("device_id"),
        ip_address=payload.get("ip_address"),
        event_time=payload["event_time"],
        fraud_score=total_score,
        is_flagged=flagged
    )

    db.session.merge(tx)  # idempotent upsert by pk
    db.session.flush()

    # remove old hits for same tx (if re-sent)
    RuleHit.query.filter_by(transaction_id=tx.id).delete()
    for h in hits:
        db.session.add(RuleHit(
            transaction_id=tx.id,
            rule_code=h["rule_code"],
            rule_name=h["rule_name"],
            score=h["score"],
            reason=h["reason"]
        ))

    db.session.commit()
    return {"transaction_id": tx.id, "fraud_score": total_score, "is_flagged": flagged, "hits": hits}
