from datetime import date
from models import Budget, User
from services.budget_service import BudgetService

def test_add_budget(auth_client, app, auth_user):
    today = date.today()
    response = auth_client.post('/budgets/add', data={
        'category': 'Food',
        'monthly_limit': '5000',
        'month': today.month,
        'year': today.year
    }, follow_redirects=True)
    assert response.status_code == 200

    with app.app_context():
        budget = Budget.query.filter_by(user_id=auth_user, category='Food').first()
        assert budget is not None
        assert float(budget.monthly_limit) == 5000.0

def test_smart_budget_generation(app, auth_user):
    with app.app_context():
        from models import db
        user = db.session.get(User, auth_user)
        # Test standard mode budget generation
        rec = BudgetService.generate_smart_budget(user, custom_income=50000.0)
        assert rec['mode'] == 'standard'
        assert rec['effective_income'] == 50000.0
        assert rec['target_savings'] == 10000.0  # 20%
        assert rec['total_spendable_budget'] == 40000.0
        assert len(rec['budgets']) > 0

        # Test student mode budget generation
        user.financial_mode = 'student'
        user.monthly_allowance = 6000.0
        rec_student = BudgetService.generate_smart_budget(user)
        assert rec_student['mode'] == 'student'
        assert rec_student['weekly_allowance'] == 1500.0  # 6000 / 4

def test_apply_recommendations(auth_client, app, auth_user):
    today = date.today()
    response = auth_client.post('/budgets/apply-recommendations', data={
        'month': today.month,
        'year': today.year
    }, follow_redirects=True)
    assert response.status_code == 200

    with app.app_context():
        budgets = Budget.query.filter_by(user_id=auth_user, month=today.month, year=today.year).all()
        assert len(budgets) > 0
