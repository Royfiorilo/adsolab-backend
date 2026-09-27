"""PostgreSQL integration fixtures: need TEST_DATABASE_URL (a `*_test` DB); each test is rolled back."""
import os
import uuid

import pytest
from flask import Flask
from sqlalchemy.engine import make_url
from sqlalchemy.orm import scoped_session, sessionmaker

from database import KineticSample, User, db

TEST_DATABASE_URL = os.getenv("TEST_DATABASE_URL")

# Seeded by the migrations.
SEEDED_ADSORBATE_ID = 1
SEEDED_ADSORBENT_ID = 1


@pytest.fixture(scope="session")
def integration_app():
    if not TEST_DATABASE_URL:
        pytest.skip("TEST_DATABASE_URL not set: skipping integration tests")
    database_name = make_url(TEST_DATABASE_URL).database or ""
    if not database_name.endswith("_test"):
        pytest.exit(
            f"TEST_DATABASE_URL points to '{database_name}': only '*_test' databases are allowed",
            returncode=2,
        )

    app = Flask("adsolab-integration-tests")
    app.config.update(
        SQLALCHEMY_DATABASE_URI=TEST_DATABASE_URL,
        SQLALCHEMY_TRACK_MODIFICATIONS=False,
        TESTING=True,
    )
    db.init_app(app)
    with app.app_context():
        yield app


@pytest.fixture
def db_session(integration_app):
    connection = db.engine.connect()
    transaction = connection.begin()
    original_session = db.session
    # Flask-SQLAlchemy 3.1 ignores the session bind, so rows would survive the rollback.
    db.session = scoped_session(
        sessionmaker(bind=connection, join_transaction_mode="create_savepoint")
    )
    try:
        yield db.session
    finally:
        db.session.remove()
        db.session = original_session
        transaction.rollback()
        connection.close()


@pytest.fixture
def make_user(db_session):
    def build(**overrides):
        fields = {
            "email": f"{uuid.uuid4().hex[:8]}@test.adsolab",
            "active": True,
            "fs_uniquifier": uuid.uuid4().hex,
        }
        fields.update(overrides)
        user = User(**fields)
        db_session.add(user)
        db_session.flush()
        return user
    return build


@pytest.fixture
def make_kinetic_sample(db_session, make_user):
    def build(**overrides):
        fields = {
            "time": [0.0, 5.0, 10.0, 20.0, 40.0],
            "qt": [0.0, 3.8, 5.0, 6.1, 6.4],
            "title": "integration sample",
            "adsorbate_id": SEEDED_ADSORBATE_ID,
            "adsorbent_id": SEEDED_ADSORBENT_ID,
        }
        fields.update(overrides)
        if "user_id" not in fields:
            fields["user_id"] = make_user().id
        sample = KineticSample(**fields)
        db_session.add(sample)
        db_session.flush()
        return sample
    return build
