from datetime import date
from models import Income

def test_add_income(auth_client, app, auth_user):
    response = auth_client.post('/income/add', data={
        'amount': '45000.00',
        'category': 'Salary',
        'description': 'Tech Corp Monthly Salary',
        'date': date.today().strftime('%Y-%m-%d'),
        'is_recurring': True
    }, follow_redirects=True)
    assert response.status_code == 200

    with app.app_context():
        income = Income.query.filter_by(user_id=auth_user).first()
        assert income is not None
        assert float(income.amount) == 45000.00
        assert income.category == 'Salary'
        assert income.is_recurring is True

def test_edit_income(auth_client, app, auth_user):
    # Add income first
    with app.app_context():
        inc = Income(user_id=auth_user, amount=10000, category='Freelancing', description='UI Project', date=date.today())
        from models import db
        db.session.add(inc)
        db.session.commit()
        inc_id = inc.id

    response = auth_client.post(f'/income/edit/{inc_id}', data={
        'amount': '15000.00',
        'category': 'Freelancing',
        'description': 'UI Project + Retainer',
        'date': date.today().strftime('%Y-%m-%d'),
        'is_recurring': False
    }, follow_redirects=True)
    assert response.status_code == 200

    with app.app_context():
        from models import db
        updated = db.session.get(Income, inc_id)
        assert float(updated.amount) == 15000.00
        assert updated.description == 'UI Project + Retainer'

def test_delete_income(auth_client, app, auth_user):
    with app.app_context():
        inc = Income(user_id=auth_user, amount=5000, category='Allowance', date=date.today())
        from models import db
        db.session.add(inc)
        db.session.commit()
        inc_id = inc.id

    response = auth_client.post(f'/income/delete/{inc_id}', follow_redirects=True)
    assert response.status_code == 200

    with app.app_context():
        from models import db
        deleted = db.session.get(Income, inc_id)
        assert deleted is None
