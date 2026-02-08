from datetime import datetime, timezone
from .extensions import db

class Transaction(db.Model):
    __tablename__ = "transactions"

    id = db.Column(db.String(64), primary_key=True)  # external transaction id
    customer_id = db.Column(db.String(64), nullable=False, index=True)
    category = db.Column(db.String(32), nullable=False, index=True)  # CARD/ACH/ATM/...
    amount = db.Column(db.Numeric(12, 2), nullable=False)
    currency = db.Column(db.String(8), nullable=False, default="ZAR")

    merchant = db.Column(db.String(128))
    country = db.Column(db.String(2))  # ISO-3166
    channel = db.Column(db.String(32)) # WEB/POS/MOBILE/ATM
    device_id = db.Column(db.String(128))
    ip_address = db.Column(db.String(64))

    event_time = db.Column(db.DateTime(timezone=True), nullable=False)
    created_at = db.Column(db.DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc))

    fraud_score = db.Column(db.Integer, nullable=False, default=0)
    is_flagged = db.Column(db.Boolean, nullable=False, default=False)

class RuleHit(db.Model):
    __tablename__ = "rule_hits"

    id = db.Column(db.Integer, primary_key=True)
    transaction_id = db.Column(db.String(64), db.ForeignKey("transactions.id"), nullable=False, index=True)
    rule_code = db.Column(db.String(64), nullable=False)
    rule_name = db.Column(db.String(128), nullable=False)
    score = db.Column(db.Integer, nullable=False)
    reason = db.Column(db.String(256), nullable=False)

    created_at = db.Column(db.DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc))

class FraudRule(db.Model):
    """
    Simple configurable rules table for thresholds.
    You can extend this later into a full DSL engine.
    """
    __tablename__ = "fraud_rules"

    code = db.Column(db.String(64), primary_key=True)
    name = db.Column(db.String(128), nullable=False)
    enabled = db.Column(db.Boolean, nullable=False, default=True)
    category = db.Column(db.String(32), nullable=True)  # apply to category or all if null
    min_amount = db.Column(db.Numeric(12, 2), nullable=True)
    country_blocklist = db.Column(db.String(512), nullable=True)  # comma-separated: "NG,RU,..."
    score = db.Column(db.Integer, nullable=False, default=30)
