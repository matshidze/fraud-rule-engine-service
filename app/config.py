import os

class Config:
    ENV = os.getenv("FLASK_ENV", "production")
    SECRET_KEY = os.getenv("SECRET_KEY", "change-me")

    SQLALCHEMY_DATABASE_URI = os.getenv(
        "DATABASE_URL",
        "postgresql+psycopg2://fraud:fraud@localhost:5432/fraud_db"
    )
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # Fraud decision threshold: if total score >= threshold => flagged
    FRAUD_SCORE_THRESHOLD = int(os.getenv("FRAUD_SCORE_THRESHOLD", "60"))
