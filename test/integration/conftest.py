"""
Fixtures para tests de integración contra PostgreSQL real.

Requieren TEST_DATABASE_URL: una base cuyo nombre termine en `_test`, construida sólo con
`dbmate up` (igual que en CI). Sin esa variable, los tests que usan `db_session` se omiten.

Cada test corre dentro de una transacción que se revierte al terminar: los `commit()` del código
de la app caen en un SAVEPOINT, así que la base queda igual que antes del test.

`db.session` se reemplaza por un `scoped_session` de SQLAlchemy atado a esa conexión porque
Flask-SQLAlchemy 3.1 ignora el `bind` de la sesión en `get_bind`: con
`db.session.configure(bind=connection)` las filas se escriben por otra conexión y sobreviven
al rollback (verificado).
"""
import os
import uuid

import pytest
from flask import Flask
from sqlalchemy.engine import make_url
from sqlalchemy.orm import scoped_session, sessionmaker

from database import KineticSample, User, db

TEST_DATABASE_URL = os.getenv("TEST_DATABASE_URL")

# Adsorbatos y adsorbentes que ya siembran las migraciones.
SEEDED_ADSORBATE_ID = 1
SEEDED_ADSORBENT_ID = 1


@pytest.fixture(scope="session")
def integration_app():
    if not TEST_DATABASE_URL:
        pytest.skip("TEST_DATABASE_URL no definido: se omiten los tests de integración")
    database_name = make_url(TEST_DATABASE_URL).database or ""
    if not database_name.endswith("_test"):
        pytest.exit(
            f"TEST_DATABASE_URL apunta a '{database_name}': sólo se aceptan bases '*_test'",
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
            "title": "muestra de integración",
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
