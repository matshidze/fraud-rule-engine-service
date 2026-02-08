import pytest
from app import create_app
from app.extensions import db

@pytest.fixture()
def client():
    app = create_app()
    app.config["TESTING"] = True
    # SQLite for tests (fast, isolated)
    app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite://"
    with app.app_context():
        db.drop_all()
        db.create_all()
    with app.test_client() as c:
        yield c
