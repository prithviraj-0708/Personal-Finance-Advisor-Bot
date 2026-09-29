from datetime import date, timedelta
from models import SavingsGoal, SavingsContribution
from services.gemini_service import GeminiService
from services.analytics_service import AnalyticsService

def test_savings_goal_and_contributions(auth_client, app, auth_user):
    today = date.today()
    # 1. Create a savings goal
    response = auth_client.post('/savings/add', data={
        'name': 'Emergency Fund',
        'target_amount': '60000.00',
        'current_amount': '20000.00',
        'target_date': (today + timedelta(days=120)).strftime('%Y-%m-%d'),
        'description': '3 months emergency buffer'
    }, follow_redirects=True)
    assert response.status_code == 200

    with app.app_context():
        goal = SavingsGoal.query.filter_by(user_id=auth_user, name='Emergency Fund').first()
        assert goal is not None
        assert goal.progress_percentage == 33.3
        assert goal.remaining_amount == 40000.00
        assert goal.months_remaining > 0
        goal_id = goal.id

    # 2. Add contribution deposit
    res_contrib = auth_client.post(f'/savings/{goal_id}/contribute', data={
        'amount': '10000.00',
        'date': today.strftime('%Y-%m-%d'),
        'description': 'Monthly bonus deposit'
    }, follow_redirects=True)
    assert res_contrib.status_code == 200

    with app.app_context():
        from models import db
        updated_goal = db.session.get(SavingsGoal, goal_id)
        assert float(updated_goal.current_amount) == 30000.00
        assert updated_goal.progress_percentage == 50.0

def test_ai_fallback_chat_api(auth_client, app, auth_user):
    # Test chat API endpoint returns valid response even when Gemini key is empty
    res = auth_client.post('/api/ai/chat', json={
        'message': 'How much did I spend this month?'
    })
    assert res.status_code == 200
    data = res.get_json()
    assert 'response' in data
    assert 'is_fallback' in data
    assert data['is_fallback'] is True
    assert 'Monthly Spending Summary' in data['response'] or 'spent' in data['response'].lower()
