from flask import Blueprint, render_template, redirect, url_for, flash, request, jsonify
from flask_login import login_required, current_user
from datetime import date
from decimal import Decimal

from models import db, Income, Expense, Budget, SavingsGoal, Notification
from services.analytics_service import AnalyticsService
from services.gemini_service import GeminiService

dashboard_bp = Blueprint('dashboard', __name__)

@dashboard_bp.route('/dashboard')
@login_required
def index():
    today = date.today()
    user_id = current_user.id

    # Check and generate real-time alerts
    AnalyticsService.check_and_generate_notifications(current_user)

    # Core Monthly Metrics
    metrics = AnalyticsService.get_monthly_metrics(user_id, today)

    # Expense category breakdown
    category_breakdown = AnalyticsService.get_category_breakdown(user_id, today.month, today.year)

    # Budget utilization details
    budget_details = AnalyticsService.get_budget_utilization_details(user_id, today.month, today.year)

    # 6-Month historical trend for charts
    history = AnalyticsService.get_six_months_history(user_id)

    # Recent transactions (combined incomes and expenses)
    recent_incomes = Income.query.filter_by(user_id=user_id).order_by(Income.date.desc(), Income.id.desc()).limit(5).all()
    recent_expenses = Expense.query.filter_by(user_id=user_id).order_by(Expense.date.desc(), Expense.id.desc()).limit(8).all()

    recent_transactions = []
    for inc in recent_incomes:
        recent_transactions.append({
            'type': 'income',
            'id': inc.id,
            'category': inc.category,
            'description': inc.description or 'Income deposit',
            'amount': float(inc.amount),
            'date': inc.date,
            'payment_method': 'Deposit'
        })
    for exp in recent_expenses:
        recent_transactions.append({
            'type': 'expense',
            'id': exp.id,
            'category': exp.category,
            'description': exp.description,
            'amount': float(exp.amount),
            'date': exp.date,
            'payment_method': exp.payment_method
        })

    recent_transactions.sort(key=lambda x: x['date'], reverse=True)
    recent_transactions = recent_transactions[:8]

    # Active savings goals
    savings_goals = SavingsGoal.query.filter_by(user_id=user_id).order_by(SavingsGoal.created_at.desc()).limit(3).all()

    # In-app notifications
    notifications = Notification.query.filter_by(user_id=user_id).order_by(Notification.created_at.desc()).limit(6).all()
    unread_count = Notification.query.filter_by(user_id=user_id, is_read=False).count()

    # Quick AI insight for the dashboard
    quick_insight = GeminiService.analyze_spending(current_user, metrics, category_breakdown, budget_details)

    # Mode-specific context calculations
    student_context = {}
    if current_user.financial_mode == 'student':
        allowance = float(current_user.monthly_allowance or 0)
        # If no explicit allowance set in settings, fallback to allowance category income
        if allowance == 0:
            allowance = metrics['total_income']
        remaining_allowance = max(0.0, allowance - metrics['total_expenses'])
        weekly_allowance = round(allowance / 4, 2)
        student_context = {
            'monthly_allowance': round(allowance, 2),
            'remaining_allowance': round(remaining_allowance, 2),
            'weekly_allowance': weekly_allowance,
            'days_left_in_month': (date(today.year, today.month % 12 + 1, 1) - today).days if today.month < 12 else 31 - today.day
        }

    freelancer_context = {}
    if current_user.financial_mode == 'freelancer':
        work_expenses = [e for e in Expense.query.filter_by(user_id=user_id, is_work_related=True).all() if e.date.month == today.month and e.date.year == today.year]
        work_total = sum(float(e.amount) for e in work_expenses)
        freelancer_context = {
            'work_expenses_total': round(work_total, 2),
            'net_operating_income': round(metrics['total_income'] - work_total, 2),
            'tax_buffer_recommended': round(metrics['total_income'] * 0.20, 2)
        }

    household_context = {}
    if current_user.financial_mode == 'household':
        household_essentials = {'Groceries', 'Rent', 'Utilities', 'Healthcare', 'Education'}
        hh_spent = sum(c['amount'] for c in category_breakdown if c['category'] in household_essentials)
        household_context = {
            'household_essentials_spent': round(hh_spent, 2),
            'discretionary_spent': round(metrics['total_expenses'] - hh_spent, 2),
            'essential_share_pct': round((hh_spent / metrics['total_expenses'] * 100), 1) if metrics['total_expenses'] > 0 else 0.0
        }

    return render_template(
        'dashboard.html',
        metrics=metrics,
        category_breakdown=category_breakdown,
        budget_details=budget_details,
        history=history,
        recent_transactions=recent_transactions,
        savings_goals=savings_goals,
        notifications=notifications,
        unread_count=unread_count,
        quick_insight=quick_insight,
        student_context=student_context,
        freelancer_context=freelancer_context,
        household_context=household_context
    )


@dashboard_bp.route('/dashboard/switch-mode/<mode>', methods=['POST'])
@login_required
def switch_mode(mode):
    if mode in ['standard', 'student', 'freelancer', 'household']:
        current_user.financial_mode = mode
        db.session.commit()
        flash(f"Switched to {mode.title()} Mode.", "info")
    return redirect(url_for('dashboard.index'))


@dashboard_bp.route('/notifications/read/<int:id>', methods=['POST'])
@login_required
def mark_notification_read(id):
    notif = Notification.query.filter_by(id=id, user_id=current_user.id).first_or_404()
    notif.is_read = True
    db.session.commit()
    return jsonify({'status': 'success'})


@dashboard_bp.route('/notifications/clear-all', methods=['POST'])
@login_required
def clear_all_notifications():
    Notification.query.filter_by(user_id=current_user.id).delete()
    db.session.commit()
    flash("All notifications cleared.", "info")
    return redirect(request.referrer or url_for('dashboard.index'))
