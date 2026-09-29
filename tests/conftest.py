import pytest
from app import create_app
from config import TestConfig
from models import db, User

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
def auth_user(app):
    with app.app_context():
        user = User(
            name="Test User",
            email="test@example.com",
            currency="₹",
            financial_mode="standard"
        )
        user.set_password("password123")
        db.session.add(user)
        db.session.commit()
        return user.id

@pytest.fixture
def auth_client(client, auth_user):
    client.post('/login', data={
        'email': 'test@example.com',
        'password': 'password123'
    }, follow_redirects=True)
    return client
