from flask import Blueprint, render_template
from .models import Transaction

ui = Blueprint("ui", __name__)

@ui.get("/")
def dashboard():
    total = Transaction.query.count()
    flagged = Transaction.query.filter_by(is_flagged=True).count()
    latest = Transaction.query.order_by(Transaction.created_at.desc()).limit(10).all()
    return render_template("dashboard.html", total=total, flagged=flagged, latest=latest)

@ui.get("/transactions")
def transactions():
    rows = Transaction.query.order_by(Transaction.created_at.desc()).limit(200).all()
    return render_template("transactions.html", rows=rows)

@ui.get("/alerts")
def alerts():
    rows = Transaction.query.filter_by(is_flagged=True).order_by(Transaction.created_at.desc()).limit(200).all()
    return render_template("alerts.html", rows=rows)
