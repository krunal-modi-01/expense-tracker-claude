import os
import tempfile
import pytest
from app import app as flask_app
from database.db import get_db, init_db


@pytest.fixture
def app():
    db_fd, db_path = tempfile.mkstemp(suffix=".db")
    flask_app.config["TESTING"] = True
    flask_app.config["DATABASE"] = db_path

    # Patch DB_PATH so get_db() uses the temp DB for each test run
    import database.db as db_module
    original_path = db_module.DB_PATH
    db_module.DB_PATH = db_path

    with flask_app.app_context():
        init_db()

    yield flask_app

    db_module.DB_PATH = original_path
    os.close(db_fd)
    os.unlink(db_path)


@pytest.fixture
def client(app):
    return app.test_client()
