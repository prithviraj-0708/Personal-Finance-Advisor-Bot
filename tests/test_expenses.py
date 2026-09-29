from datetime import date
from models import Expense

def test_add_expense(auth_client, app, auth_user):
    response = auth_client.post('/expenses/add', data={
        'amount': '1250.50',
        'category': 'Food',
        'description': 'Team Dinner at Bistro',
        'payment_method': 'UPI',
        'date': date.today().strftime('%Y-%m-%d'),
        'notes': 'Casual dinner with colleagues',
        'is_work_related': False
    }, follow_redirects=True)
    assert response.status_code == 200

    with app.app_context():
        expense = Expense.query.filter_by(user_id=auth_user).first()
        assert expense is not None
        assert float(expense.amount) == 1250.50
        assert expense.category == 'Food'
        assert expense.payment_method == 'UPI'

def test_edit_expense(auth_client, app, auth_user):
    with app.app_context():
        exp = Expense(
            user_id=auth_user,
            amount=800,
            category='Transportation',
            description='Metro Card',
            payment_method='UPI',
            date=date.today()
        )
        from models import db
        db.session.add(exp)
        db.session.commit()
        exp_id = exp.id

    response = auth_client.post(f'/expenses/edit/{exp_id}', data={
        'amount': '1000.00',
        'category': 'Transportation',
        'description': 'Metro Card + Cab Ride',
        'payment_method': 'Credit Card',
        'date': date.today().strftime('%Y-%m-%d'),
        'notes': 'Airport cab',
        'is_work_related': True
    }, follow_redirects=True)
    assert response.status_code == 200

    with app.app_context():
        from models import db
        updated = db.session.get(Expense, exp_id)
        assert float(updated.amount) == 1000.00
        assert updated.payment_method == 'Credit Card'
        assert updated.is_work_related is True

def test_transactions_page_filter(auth_client, app, auth_user):
    with app.app_context():
        from models import db, Income
        db.session.add(Income(user_id=auth_user, amount=20000, category='Salary', description='Paycheck', date=date.today()))
        db.session.add(Expense(user_id=auth_user, amount=1500, category='Groceries', description='Weekly veggies', date=date.today()))
        db.session.commit()

    # Search for veggies
    res = auth_client.get('/transactions?q=veggies')
    assert res.status_code == 200
    assert b'Weekly veggies' in res.data
    assert b'Paycheck' not in res.data
