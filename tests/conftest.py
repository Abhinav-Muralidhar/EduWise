import os
import pytest
from app import create_app
from app.extensions import db
from app.models.user import User
from app.config import Config
from werkzeug.security import generate_password_hash

class TestConfig(Config):
    TESTING = True
    SQLALCHEMY_DATABASE_URI = 'sqlite:///:memory:'
    WTF_CSRF_ENABLED = False
    SECRET_KEY = 'test-secret-key'
    RATELIMIT_ENABLED = False
    SCHEDULER_API_ENABLED = False
    JOBS = []

@pytest.fixture
def app():
    app = create_app(TestConfig)
    
    with app.app_context():
        db.create_all()
        yield app
        db.session.remove()
        db.drop_all()

@pytest.fixture
def client(app):
    return app.test_client()

@pytest.fixture
def test_user_id(app):
    with app.app_context():
        user = User(
            username="teststudent",
            email="student@example.com",
            password=generate_password_hash("password123")
        )
        db.session.add(user)
        db.session.commit()
        return user.id

@pytest.fixture
def auth_client(client, test_user_id):
    with client.session_transaction() as sess:
        sess['user_id'] = test_user_id
        sess['username'] = "teststudent"
    return client
