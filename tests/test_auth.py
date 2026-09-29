from models import User

def test_register_user(client, app):
    response = client.post('/register', data={
        'name': 'Priya Sharma',
        'email': 'priya@example.com',
        'password': 'securepassword',
        'confirm_password': 'securepassword',
        'financial_mode': 'student',
        'currency': '₹'
    }, follow_redirects=True)
    assert response.status_code == 200
    assert b'Your account has been created' in response.data

    with app.app_context():
        user = User.query.filter_by(email='priya@example.com').first()
        assert user is not None
        assert user.name == 'Priya Sharma'
        assert user.financial_mode == 'student'
        assert user.check_password('securepassword') is True
        assert user.check_password('wrongpass') is False

def test_login_success(client, auth_user):
    response = client.post('/login', data={
        'email': 'test@example.com',
        'password': 'password123'
    }, follow_redirects=True)
    assert response.status_code == 200
    assert b'Welcome back, Test User' in response.data

def test_login_failure(client, auth_user):
    response = client.post('/login', data={
        'email': 'test@example.com',
        'password': 'incorrect_password'
    }, follow_redirects=True)
    assert response.status_code == 200
    assert b'Invalid email or password' in response.data

def test_protected_routes_redirect_unauthenticated(client):
    response = client.get('/dashboard', follow_redirects=False)
    assert response.status_code == 302
    assert '/login' in response.headers['Location']

def test_logout(auth_client):
    response = auth_client.get('/logout', follow_redirects=True)
    assert response.status_code == 200
    assert b'You have been safely signed out' in response.data
