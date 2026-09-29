from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_required, current_user
from datetime import date
from decimal import Decimal
from sqlalchemy import extract, func

from models import db, Income
from forms import IncomeForm
from services.analytics_service import AnalyticsService

income_bp = Blueprint('income', __name__)

@income_bp.route('/income', methods=['GET'])
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

    query = Income.query.filter_by(user_id=current_user.id)

    if selected_month:
        query = query.filter(extract('month', Income.date) == selected_month)
    if selected_year:
        query = query.filter(extract('year', Income.date) == selected_year)
    if selected_category:
        query = query.filter(Income.category == selected_category)

    incomes = query.order_by(Income.date.desc(), Income.id.desc()).all()

    # Calculate month total
    total_income = sum(float(i.amount) for i in incomes)

    # Category breakdown for selected month
    breakdown = AnalyticsService.get_income_category_breakdown(current_user.id, selected_month, selected_year)

    form = IncomeForm()

    return render_template(
        'income.html',
        incomes=incomes,
        total_income=round(total_income, 2),
        breakdown=breakdown,
        selected_month=selected_month,
        selected_year=selected_year,
        selected_category=selected_category,
        form=form
    )


@income_bp.route('/income/add', methods=['POST'])
@login_required
def add():
    form = IncomeForm()
    if form.validate_on_submit():
        income = Income(
            user_id=current_user.id,
            amount=form.amount.data,
            category=form.category.data,
            description=form.description.data.strip() if form.description.data else '',
            date=form.date.data,
            is_recurring=form.is_recurring.data
        )
        db.session.add(income)
        db.session.commit()
        flash(f'Income of {current_user.currency}{income.amount:,.2f} added successfully!', 'success')
    else:
        for field, errors in form.errors.items():
            for error in errors:
                flash(f"{field.capitalize()}: {error}", 'danger')

    return redirect(url_for('income.index'))


@income_bp.route('/income/edit/<int:id>', methods=['GET', 'POST'])
@login_required
def edit(id):
    income = Income.query.filter_by(id=id, user_id=current_user.id).first_or_404()
    form = IncomeForm(obj=income)

    if form.validate_on_submit():
        income.amount = form.amount.data
        income.category = form.category.data
        income.description = form.description.data.strip() if form.description.data else ''
        income.date = form.date.data
        income.is_recurring = form.is_recurring.data
        db.session.commit()
        flash('Income entry updated successfully.', 'success')
        return redirect(url_for('income.index'))

    return render_template('income_edit.html', form=form, income=income)


@income_bp.route('/income/delete/<int:id>', methods=['POST'])
@login_required
def delete(id):
    income = Income.query.filter_by(id=id, user_id=current_user.id).first_or_404()
    db.session.delete(income)
    db.session.commit()
    flash('Income record deleted successfully.', 'info')
    return redirect(url_for('income.index'))
