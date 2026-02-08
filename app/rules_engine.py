# app/rules_engine.py
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from decimal import Decimal, InvalidOperation
from typing import Any, Dict, Iterable, List, Optional


@dataclass(frozen=True)
class RuleHit:
    rule_id: str
    score: int
    reason: str
    severity: str = "medium"

    def as_dict(self) -> Dict[str, Any]:
        return {
            "rule_id": self.rule_id,
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
    """
    Accepts ISO-8601 strings like '2026-02-07T10:00:00+02:00'
    Returns aware datetime or None if parsing fails.
    """
    if not value:
        return None
    if isinstance(value, datetime):
        # ensure tz-aware
        return value if value.tzinfo else value.replace(tzinfo=timezone.utc)
    try:
        # Python 3.11+ supports fromisoformat with offsets
        dt = datetime.fromisoformat(str(value))
        return dt if dt.tzinfo else dt.replace(tzinfo=timezone.utc)
    except Exception:
        return None


def _csv_set(value: str) -> set[str]:
    return {v.strip().upper() for v in value.split(",") if v.strip()}



DEFAULT_BLACKLISTED_COUNTRIES = {"NG", "IR", "KP"}  # adjust freely
DEFAULT_HIGH_AMOUNT_THRESHOLD = Decimal("10000")    # 10k+
DEFAULT_SCORE_BLACKLISTED_COUNTRY = 25
DEFAULT_SCORE_HIGH_AMOUNT = 50
DEFAULT_SCORE_WEB_CHANNEL = 10


def apply_rules(payload: Dict[str, Any], rules: Optional[Iterable[Any]] = None) -> List[Dict[str, Any]]:
    
    hits: List[RuleHit] = []

    amount = _to_decimal(payload.get("amount"))
    country = _to_upper(payload.get("country"))
    channel = _to_upper(payload.get("channel"))
    category = _to_upper(payload.get("category"))
    merchant = _to_str(payload.get("merchant"))
    merchant_id = _to_upper(payload.get("merchant_id") or payload.get("merchantId"))
    event_time = _parse_iso_datetime(payload.get("event_time") or payload.get("occurred_at"))


    if rules:
        for rule in rules:
            rule_id = getattr(rule, "rule_id", None) or getattr(rule, "code", None) or "unknown_rule"
            rule_type = (
                getattr(rule, "rule_type", None)
                or getattr(rule, "type", None)
                or getattr(rule, "kind", None)
                or ""
            )
            cfg = getattr(rule, "config", None) or {}

            rtype = str(rule_type).lower()

            if rtype == "blacklisted_country":
                countries = _csv_set(_to_str(cfg.get("countries", ""))) or DEFAULT_BLACKLISTED_COUNTRIES
                score = int(cfg.get("score", DEFAULT_SCORE_BLACKLISTED_COUNTRY))
                if country in countries:
                    hits.append(
                        RuleHit(
                            rule_id=str(rule_id),
                            score=score,
                            reason=f"Country {country} is blacklisted",
                            severity="high",
                        )
                    )

          
            elif rtype == "high_amount":
                threshold = _to_decimal(cfg.get("threshold", DEFAULT_HIGH_AMOUNT_THRESHOLD))
                score = int(cfg.get("score", DEFAULT_SCORE_HIGH_AMOUNT))
                if amount >= threshold:
                    hits.append(
                        RuleHit(
                            rule_id=str(rule_id),
                            score=score,
                            reason=f"Amount {amount} >= threshold {threshold}",
                            severity="high",
                        )
                    )


            elif rtype == "web_channel":
                score = int(cfg.get("score", DEFAULT_SCORE_WEB_CHANNEL))
                if channel == "WEB":
                    hits.append(
                        RuleHit(
                            rule_id=str(rule_id),
                            score=score,
                            reason="Transaction channel is WEB",
                            severity="medium",
                        )
                    )

   
            elif rtype == "risky_category":
                risky = _csv_set(_to_str(cfg.get("merchant_categories", ""))) or {"GAMBLING", "CRYPTO"}
                score = int(cfg.get("score", 20))
                if _to_upper(payload.get("merchant_category")) in risky:
                    hits.append(
                        RuleHit(
                            rule_id=str(rule_id),
                            score=score,
                            reason=f"Merchant category {_to_upper(payload.get('merchant_category'))} is risky",
                            severity="medium",
                        )
                    )

           
        #return [h.as_dict() for h in hits]



    # Blacklisted country
    if country in DEFAULT_BLACKLISTED_COUNTRIES:
        hits.append(
            RuleHit(
                rule_id="blacklisted_country",
                score=DEFAULT_SCORE_BLACKLISTED_COUNTRY,
                reason=f"Country {country} is blacklisted",
                severity="high",
            )
        )

    # High amount
    if amount >= DEFAULT_HIGH_AMOUNT_THRESHOLD:
        hits.append(
            RuleHit(
                rule_id="high_amount",
                score=DEFAULT_SCORE_HIGH_AMOUNT,
                reason=f"Amount {amount} >= {DEFAULT_HIGH_AMOUNT_THRESHOLD}",
                severity="high",
            )
        )


    if channel == "WEB":
        hits.append(
            RuleHit(
                rule_id="web_channel",
                score=DEFAULT_SCORE_WEB_CHANNEL,
                reason="Transaction channel is WEB",
                severity="medium",
            )
        )

 
    if merchant and len(merchant.strip()) <= 2:
        hits.append(
            RuleHit(
                rule_id="suspicious_merchant_name",
                score=10,
                reason="Merchant name looks suspiciously short",
                severity="low",
            )
        )


    if event_time is None and (payload.get("event_time") or payload.get("occurred_at")):
        hits.append(
            RuleHit(
                rule_id="invalid_timestamp",
                score=5,
                reason="Transaction timestamp could not be parsed",
                severity="low",
            )
        )

    return [h.as_dict() for h in hits]
