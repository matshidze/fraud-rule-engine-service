from marshmallow import Schema, fields, validate

class TransactionInSchema(Schema):
    id = fields.Str(required=True)
    customer_id = fields.Str(required=True)
    category = fields.Str(required=True, validate=validate.OneOf(["CARD", "ACH", "ATM", "EFT", "PAYPAL", "OTHER"]))
    amount = fields.Decimal(required=True, as_string=True)
    currency = fields.Str(required=True, validate=validate.Length(min=3, max=8))

    merchant = fields.Str(required=False, allow_none=True)
    country = fields.Str(required=False, allow_none=True, validate=validate.Length(equal=2))
    channel = fields.Str(required=False, allow_none=True)
    device_id = fields.Str(required=False, allow_none=True)
    ip_address = fields.Str(required=False, allow_none=True)

    event_time = fields.DateTime(required=True)  # ISO-8601

class TransactionOutSchema(Schema):
    id = fields.Str()
    customer_id = fields.Str()
    category = fields.Str()
    amount = fields.Str()
    currency = fields.Str()
    event_time = fields.DateTime()

    fraud_score = fields.Int()
    is_flagged = fields.Bool()

class RuleHitSchema(Schema):
    rule_code = fields.Str()
    rule_name = fields.Str()
    score = fields.Int()
    reason = fields.Str()
