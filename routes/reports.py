from flask import Blueprint, render_template, request, Response, redirect, url_for, flash
from flask_login import login_required, current_user
from datetime import date, timedelta
from decimal import Decimal
from sqlalchemy import extract, func

from models import db, Income, Expense, Budget, SavingsGoal
from services.analytics_service import AnalyticsService
from services.report_service import ReportService

reports_bp = Blueprint('reports', __name__)

@reports_bp.route('/reports', methods=['GET'])
@login_required
def index():
    today = date.today()
    try:
        selected_month = int(request.args.get('month') or today.month)
        if not (1 <= selected_month <= 12):
            selected_month = today.month
    except (ValueError, TypeError):
        selected_month = today.month

    try:
        selected_year = int(request.args.get('year') or today.year)
        if selected_year < 2000 or selected_year > 2100:
            selected_year = today.year
    except (ValueError, TypeError):
        selected_year = today.year

    selected_category = request.args.get('category', '').strip()

    target_date = date(selected_year, selected_month, 1)

    # Core monthly metrics
    metrics = AnalyticsService.get_monthly_metrics(current_user.id, target_date)

    # Category breakdowns
    category_breakdown = AnalyticsService.get_category_breakdown(current_user.id, selected_month, selected_year)
    income_breakdown = AnalyticsService.get_income_category_breakdown(current_user.id, selected_month, selected_year)

    # Budget utilization details
    budget_details = AnalyticsService.get_budget_utilization_details(current_user.id, selected_month, selected_year)

    # 6-Month history
    history = AnalyticsService.get_six_months_history(current_user.id)

    # Savings goals
    savings_goals = SavingsGoal.query.filter_by(user_id=current_user.id).all()

    # Daily expenses for this month
    daily_records = db.session.query(
        Expense.date,
        func.sum(Expense.amount).label('total'),
        func.count(Expense.id).label('count')
    ).filter(
        Expense.user_id == current_user.id,
        extract('month', Expense.date) == selected_month,
        extract('year', Expense.date) == selected_year
    ).group_by(Expense.date).order_by(Expense.date.desc()).all()

    daily_report = [{'date': r.date.strftime('%Y-%m-%d'), 'amount': float(r.total), 'count': r.count} for r in daily_records]

    return render_template(
        'reports.html',
        metrics=metrics,
        category_breakdown=category_breakdown,
        income_breakdown=income_breakdown,
        budget_details=budget_details,
        history=history,
        savings_goals=savings_goals,
        daily_report=daily_report,
        selected_month=selected_month,
        selected_year=selected_year,
        selected_category=selected_category
    )


@reports_bp.route('/reports/printable-summary', methods=['GET'])
@login_required
def printable_summary():
    today = date.today()
    try:
        selected_month = int(request.args.get('month') or today.month)
        if not (1 <= selected_month <= 12):
            selected_month = today.month
    except (ValueError, TypeError):
        selected_month = today.month

    try:
        selected_year = int(request.args.get('year') or today.year)
        if selected_year < 2000 or selected_year > 2100:
            selected_year = today.year
    except (ValueError, TypeError):
        selected_year = today.year

    target_date = date(selected_year, selected_month, 1)

    metrics = AnalyticsService.get_monthly_metrics(current_user.id, target_date)
    category_breakdown = AnalyticsService.get_category_breakdown(current_user.id, selected_month, selected_year)
    budget_details = AnalyticsService.get_budget_utilization_details(current_user.id, selected_month, selected_year)
    savings_goals = SavingsGoal.query.filter_by(user_id=current_user.id).all()

    return render_template(
        'printable_summary.html',
        metrics=metrics,
        category_breakdown=category_breakdown,
        budget_details=budget_details,
        savings_goals=savings_goals,
        month_name=target_date.strftime('%B %Y')
    )


@reports_bp.route('/reports/export/transactions', methods=['GET'])
@login_required
def export_transactions():
    csv_data = ReportService.export_transactions_csv(current_user.id)
    return Response(
        csv_data,
        mimetype="text/csv",
        headers={"Content-Disposition": f"attachment;filename=transactions_{date.today().strftime('%Y%m%d')}.csv"}
    )


@reports_bp.route('/reports/export/budgets', methods=['GET'])
@login_required
def export_budgets():
    month = request.args.get('month', type=int)
    year = request.args.get('year', type=int)
    csv_data = ReportService.export_budgets_csv(current_user.id, month, year)
    return Response(
        csv_data,
        mimetype="text/csv",
        headers={"Content-Disposition": f"attachment;filename=budgets_{date.today().strftime('%Y%m%d')}.csv"}
    )


@reports_bp.route('/reports/export/savings', methods=['GET'])
@login_required
def export_savings():
    csv_data = ReportService.export_savings_csv(current_user.id)
    return Response(
        csv_data,
        mimetype="text/csv",
        headers={"Content-Disposition": f"attachment;filename=savings_goals_{date.today().strftime('%Y%m%d')}.csv"}
    )
