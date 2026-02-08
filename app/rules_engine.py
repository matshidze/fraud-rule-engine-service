# app/rules_engine.py
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from decimal import Decimal, InvalidOperation
from typing import Any, Dict, Iterable, List, Optional


@dataclass(frozen=True)
class RuleHit:
    rule_code: str
    rule_name: str
    score: int
    reason: str
    severity: str = "medium"

    def as_dict(self) -> Dict[str, Any]:
        return {
            "rule_code": self.rule_code,
            "rule_name": self.rule_name,
            "score": self.score,
            "reason": self.reason,
            "severity": self.severity,
        }


def _to_decimal(value: Any) -> Decimal:
    if isinstance(value, Decimal):
        return value
    if value is None:
        return Decimal("0")
    try:
        return Decimal(str(value))
    except (InvalidOperation, ValueError, TypeError):
        return Decimal("0")


def _to_str(value: Any) -> str:
    return "" if value is None else str(value)


def _to_upper(value: Any) -> str:
    return _to_str(value).strip().upper()


def _parse_iso_datetime(value: Any) -> Optional[datetime]:
    if not value:
        return None
    if isinstance(value, datetime):
        return value if value.tzinfo else value.replace(tzinfo=timezone.utc)
    try:
        dt = datetime.fromisoformat(str(value))
        return dt if dt.tzinfo else dt.replace(tzinfo=timezone.utc)
    except Exception:
        return None


def _csv_set(value: str) -> set[str]:
    return {v.strip().upper() for v in value.split(",") if v.strip()}


DEFAULT_SCORE_WEB_CHANNEL = 10


def apply_rules(payload: Dict[str, Any], rules: Optional[Iterable[Any]] = None) -> List[Dict[str, Any]]:
    hits: List[RuleHit] = []

    amount = _to_decimal(payload.get("amount"))
    country = _to_upper(payload.get("country"))
    channel = _to_upper(payload.get("channel"))
    merchant = _to_str(payload.get("merchant"))
    event_time = _parse_iso_datetime(payload.get("event_time") or payload.get("occurred_at"))


    rules_list = list(rules) if rules is not None else []
    for rule in rules_list:
        code = _to_str(getattr(rule, "code", "UNKNOWN_RULE")) or "UNKNOWN_RULE"
        name = _to_str(getattr(rule, "name", code)) or code
        score = int(getattr(rule, "score", 0) or 0)

        min_amount = getattr(rule, "min_amount", None)
        if min_amount is not None:
            try:
                min_amount_dec = _to_decimal(min_amount)
                if amount >= min_amount_dec and score > 0:
                    hits.append(
                        RuleHit(
                            rule_code=code,
                            rule_name=name,
                            score=score,
                            reason=f"Amount {amount} >= {min_amount_dec}",
                            severity="high",
                        )
                    )
            except Exception:
                pass

    
        blocklist = _to_str(getattr(rule, "country_blocklist", "") or "")
        if blocklist:
            countries = _csv_set(blocklist)
            if country in countries and score > 0:
                hits.append(
                    RuleHit(
                        rule_code=code,
                        rule_name=name,
                        score=score,
                        reason=f"Country {country} is in blocklist",
                        severity="high",
                    )
                )

 
    if channel == "WEB":
        hits.append(
            RuleHit(
                rule_code="WEB_CHANNEL",
                rule_name="WEB channel",
                score=DEFAULT_SCORE_WEB_CHANNEL,
                reason="Transaction channel is WEB",
                severity="medium",
            )
        )

    if merchant and len(merchant.strip()) <= 2:
        hits.append(
            RuleHit(
                rule_code="SUSPICIOUS_MERCHANT_NAME",
                rule_name="Suspicious merchant name",
                score=10,
                reason="Merchant name looks suspiciously short",
                severity="low",
            )
        )

    if event_time is None and (payload.get("event_time") or payload.get("occurred_at")):
        hits.append(
            RuleHit(
                rule_code="INVALID_TIMESTAMP",
                rule_name="Invalid timestamp",
                score=5,
                reason="Transaction timestamp could not be parsed",
                severity="low",
            )
        )

    return [h.as_dict() for h in hits]
