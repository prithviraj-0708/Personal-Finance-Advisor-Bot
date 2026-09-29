from flask import Blueprint, render_template, redirect, url_for, flash, request, jsonify
from flask_login import login_required, current_user
from datetime import date
from decimal import Decimal

from models import db, Budget, Expense, Income
from forms import BudgetForm
from services.analytics_service import AnalyticsService
from services.budget_service import BudgetService

budgets_bp = Blueprint('budgets', __name__)

@budgets_bp.route('/budgets', methods=['GET'])
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

    # Utilization details for selected month
    utilization_details = AnalyticsService.get_budget_utilization_details(
        current_user.id, selected_month, selected_year
    )

    # Monthly metrics
    metrics = AnalyticsService.get_monthly_metrics(
        current_user.id, date(selected_year, selected_month, 1)
    )

    form = BudgetForm()
    form.month.data = selected_month
    form.year.data = selected_year

    # Generate a fresh smart budget recommendation preview
    recommendation = BudgetService.generate_smart_budget(current_user, selected_month, selected_year)

    return render_template(
        'budgets.html',
        utilization_details=utilization_details,
        metrics=metrics,
        recommendation=recommendation,
        selected_month=selected_month,
        selected_year=selected_year,
        form=form
    )


@budgets_bp.route('/budgets/add', methods=['POST'])
@login_required
def add():
    form = BudgetForm()
    if form.validate_on_submit():
        category = form.category.data
        limit = form.monthly_limit.data
        month = form.month.data
        year = form.year.data

        existing = Budget.query.filter_by(
            user_id=current_user.id,
            category=category,
            month=month,
            year=year
        ).first()

        if existing:
            existing.monthly_limit = limit
            flash(f"Updated budget for {category} to {current_user.currency}{limit:,.2f}.", "info")
        else:
            budget = Budget(
                user_id=current_user.id,
                category=category,
                monthly_limit=limit,
                month=month,
                year=year
            )
            db.session.add(budget)
            flash(f"Budget for {category} set to {current_user.currency}{limit:,.2f}.", "success")

        db.session.commit()
    else:
        for field, errors in form.errors.items():
            for error in errors:
                flash(f"{field.capitalize()}: {error}", 'danger')

    return redirect(url_for('budgets.index', month=form.month.data, year=form.year.data))


@budgets_bp.route('/budgets/edit/<int:id>', methods=['POST'])
@login_required
def edit(id):
    budget = Budget.query.filter_by(id=id, user_id=current_user.id).first_or_404()
    new_limit = request.form.get('monthly_limit')
    try:
        limit_val = Decimal(new_limit)
        if limit_val > 0:
            budget.monthly_limit = limit_val
            db.session.commit()
            flash(f"Updated {budget.category} budget limit to {current_user.currency}{limit_val:,.2f}.", "success")
        else:
            flash("Budget limit must be greater than zero.", "danger")
    except Exception:
        flash("Invalid limit value provided.", "danger")

    return redirect(url_for('budgets.index', month=budget.month, year=budget.year))


@budgets_bp.route('/budgets/delete/<int:id>', methods=['POST'])
@login_required
def delete(id):
    budget = Budget.query.filter_by(id=id, user_id=current_user.id).first_or_404()
    month, year = budget.month, budget.year
    db.session.delete(budget)
    db.session.commit()
    flash(f"Budget for {budget.category} removed.", "info")
    return redirect(url_for('budgets.index', month=month, year=year))


@budgets_bp.route('/budgets/apply-recommendations', methods=['POST'])
@login_required
def apply_recommendations():
    """Applies smart budget generated allocations into the database."""
    month = int(request.form.get('month', date.today().month))
    year = int(request.form.get('year', date.today().year))
    custom_income = request.form.get('custom_income', None)

    rec = BudgetService.generate_smart_budget(current_user, month, year, custom_income)
    applied = BudgetService.apply_generated_budgets(current_user.id, rec['budgets'], month, year)

    flash(f"Successfully applied {applied} smart budget allocations for {date(year, month, 1).strftime('%B %Y')}!", "success")
    return redirect(url_for('budgets.index', month=month, year=year))
