from __future__ import annotations

from decimal import Decimal
from typing import Any, Dict, List

from flask import current_app

from .extensions import db
from .models import FraudRule, RuleHit, Transaction
from .rules_engine import apply_rules


def ensure_seed_rules() -> None:
    """Seed a minimal rule set if no rules exist (idempotent)."""
    if FraudRule.query.count() > 0:
        return

    seeds = [
        FraudRule(
            code="AMT_10K",
            name="Amount >= 10000",
            enabled=True,
            category=None,
            min_amount=Decimal("10000"),
            score=50,
        ),
        FraudRule(
            code="BLOCK_COUNTRY",
            name="Blocked countries",
            enabled=True,
            category=None,
            country_blocklist="NG,RU",
            score=25,
        ),
    ]


    db.session.add_all(seeds)
    db.session.commit()


def _hit_code(hit: Dict[str, Any]) -> str:
    """Support multiple hit shapes coming from rules_engine."""
    return str(hit.get("rule_code") or hit.get("rule_id") or hit.get("code") or "UNKNOWN_RULE")


def _hit_name(hit: Dict[str, Any]) -> str:
    return str(hit.get("rule_name") or hit.get("name") or hit.get("rule_id") or _hit_code(hit))


def process_transaction(payload: dict) -> dict:
    """
    Process a transaction:
      - ensure rules exist
      - apply rules
      - store transaction + rule hits
      - return summary for API
    """
    ensure_seed_rules()

    rules = FraudRule.query.filter_by(enabled=True).all()
    hits: List[Dict[str, Any]] = apply_rules(payload, rules)

    total_score = int(sum(int(h.get("score", 0)) for h in hits))
    threshold = int(current_app.config.get("FRAUD_SCORE_THRESHOLD", 60))
    flagged = total_score >= threshold

    # Build Transaction row (idempotent)
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
        is_flagged=flagged,
    )

    db.session.merge(tx)  # upsert by primary key
    db.session.flush()

    # Remove old hits for same tx (if re-sent)
    RuleHit.query.filter_by(transaction_id=tx.id).delete()

    for h in hits:
        db.session.add(
            RuleHit(
                transaction_id=tx.id,
                rule_code=_hit_code(h),
                rule_name=_hit_name(h),
                score=int(h.get("score", 0)),
                reason=str(h.get("reason", "")),
            )
        )

    db.session.commit()

    # API response (keep both keys for clients)
    return {
        "transaction_id": tx.id,
        "fraud_score": total_score,
        "is_flagged": flagged,
        "rule_hits": hits,
        "hits": hits,  # backward compatible
    }
