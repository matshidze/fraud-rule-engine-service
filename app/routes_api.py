from flask import Blueprint, jsonify, request
from .extensions import db
from .models import Transaction, RuleHit
from .schemas import TransactionInSchema, TransactionOutSchema, RuleHitSchema
from .services import process_transaction

api = Blueprint("api", __name__, url_prefix="/api/v1")

tx_in = TransactionInSchema()
tx_out = TransactionOutSchema()
hit_out = RuleHitSchema(many=True)

@api.get("/health")
def health():
    return jsonify({"status": "ok"})

@api.post("/transactions")
def ingest_transaction():
    payload = tx_in.load(request.get_json(force=True))
    result = process_transaction(payload)
    return jsonify(result), 201

@api.get("/transactions")
def list_transactions():
    limit = min(int(request.args.get("limit", 50)), 200)
    rows = Transaction.query.order_by(Transaction.created_at.desc()).limit(limit).all()
    return jsonify(tx_out.dump(rows, many=True))

@api.get("/transactions/<tx_id>")
def get_transaction(tx_id: str):
    tx = Transaction.query.get_or_404(tx_id)
    hits = RuleHit.query.filter_by(transaction_id=tx_id).all()
    return jsonify({
        "transaction": tx_out.dump(tx),
        "hits": hit_out.dump(hits),
    })

@api.get("/fraud/alerts")
def fraud_alerts():
    limit = min(int(request.args.get("limit", 50)), 200)
    rows = Transaction.query.filter_by(is_flagged=True).order_by(Transaction.created_at.desc()).limit(limit).all()
    return jsonify(tx_out.dump(rows, many=True))
