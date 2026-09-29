from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_required, current_user
from datetime import date, timedelta
from decimal import Decimal
from sqlalchemy import extract, func, or_

from models import db, Expense, Income
from forms import ExpenseForm
from services.analytics_service import AnalyticsService

expenses_bp = Blueprint('expenses', __name__)

@expenses_bp.route('/expenses', methods=['GET'])
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

    query = Expense.query.filter_by(user_id=current_user.id)

    if selected_month:
        query = query.filter(extract('month', Expense.date) == selected_month)
    if selected_year:
        query = query.filter(extract('year', Expense.date) == selected_year)
    if selected_category:
        query = query.filter(Expense.category == selected_category)

    expenses = query.order_by(Expense.date.desc(), Expense.id.desc()).all()

    # Calculate summaries: daily (today), weekly (last 7 days), monthly (selected month)
    today_total = float(db.session.query(func.coalesce(func.sum(Expense.amount), 0)).filter(
        Expense.user_id == current_user.id,
        Expense.date == today
    ).scalar())

    seven_days_ago = today - timedelta(days=7)
    weekly_total = float(db.session.query(func.coalesce(func.sum(Expense.amount), 0)).filter(
        Expense.user_id == current_user.id,
        Expense.date >= seven_days_ago,
        Expense.date <= today
    ).scalar())

    monthly_total = sum(float(e.amount) for e in expenses)

    # Category breakdown for selected month
    breakdown = AnalyticsService.get_category_breakdown(current_user.id, selected_month, selected_year)

    form = ExpenseForm()

    return render_template(
        'expenses.html',
        expenses=expenses,
        today_total=round(today_total, 2),
        weekly_total=round(weekly_total, 2),
        monthly_total=round(monthly_total, 2),
        breakdown=breakdown,
        selected_month=selected_month,
        selected_year=selected_year,
        selected_category=selected_category,
        form=form
    )


@expenses_bp.route('/expenses/add', methods=['POST'])
@login_required
def add():
    form = ExpenseForm()
    if form.validate_on_submit():
        expense = Expense(
            user_id=current_user.id,
            amount=form.amount.data,
            category=form.category.data,
            description=form.description.data.strip(),
            payment_method=form.payment_method.data,
            date=form.date.data,
            notes=form.notes.data.strip() if form.notes.data else '',
            is_work_related=form.is_work_related.data
        )
        db.session.add(expense)
        db.session.commit()
        flash(f'Expense of {current_user.currency}{expense.amount:,.2f} recorded!', 'success')
    else:
        for field, errors in form.errors.items():
            for error in errors:
                flash(f"{field.capitalize()}: {error}", 'danger')

    return redirect(request.referrer or url_for('expenses.index'))


@expenses_bp.route('/expenses/edit/<int:id>', methods=['GET', 'POST'])
@login_required
def edit(id):
    expense = Expense.query.filter_by(id=id, user_id=current_user.id).first_or_404()
    form = ExpenseForm(obj=expense)

    if form.validate_on_submit():
        expense.amount = form.amount.data
        expense.category = form.category.data
        expense.description = form.description.data.strip()
        expense.payment_method = form.payment_method.data
        expense.date = form.date.data
        expense.notes = form.notes.data.strip() if form.notes.data else ''
        expense.is_work_related = form.is_work_related.data
        db.session.commit()
        flash('Expense record updated successfully.', 'success')
        return redirect(url_for('expenses.index'))

    return render_template('expenses_edit.html', form=form, expense=expense)


@expenses_bp.route('/expenses/delete/<int:id>', methods=['POST'])
@login_required
def delete(id):
    expense = Expense.query.filter_by(id=id, user_id=current_user.id).first_or_404()
    db.session.delete(expense)
    db.session.commit()
    flash('Expense entry deleted.', 'info')
    return redirect(request.referrer or url_for('expenses.index'))


@expenses_bp.route('/transactions', methods=['GET'])
@login_required
def transactions():
    """Unified transaction ledger with search, category filtering, date range, and sorting."""
    search_query = request.args.get('q', '').strip()
    category = request.args.get('category', '').strip()
    txn_type = request.args.get('type', '').strip()  # all, income, expense
    sort_by = request.args.get('sort', 'date_desc')  # date_desc, date_asc, amount_desc, amount_asc
    start_date_str = request.args.get('start_date', '')
    end_date_str = request.args.get('end_date', '')

    incomes_query = Income.query.filter_by(user_id=current_user.id)
    expenses_query = Expense.query.filter_by(user_id=current_user.id)

    # Date range filters
    if start_date_str:
        try:
            s_date = date.fromisoformat(start_date_str)
            incomes_query = incomes_query.filter(Income.date >= s_date)
            expenses_query = expenses_query.filter(Expense.date >= s_date)
        except ValueError:
            pass

    if end_date_str:
        try:
            e_date = date.fromisoformat(end_date_str)
            incomes_query = incomes_query.filter(Income.date <= e_date)
            expenses_query = expenses_query.filter(Expense.date <= e_date)
        except ValueError:
            pass

    # Category filter
    if category:
        incomes_query = incomes_query.filter(Income.category == category)
        expenses_query = expenses_query.filter(Expense.category == category)

    # Search query
    if search_query:
        incomes_query = incomes_query.filter(
            or_(
                Income.description.ilike(f"%{search_query}%"),
                Income.category.ilike(f"%{search_query}%")
            )
        )
        expenses_query = expenses_query.filter(
            or_(
                Expense.description.ilike(f"%{search_query}%"),
                Expense.category.ilike(f"%{search_query}%"),
                Expense.notes.ilike(f"%{search_query}%")
            )
        )

    all_txns = []

    if txn_type != 'expense':
        for inc in incomes_query.all():
            all_txns.append({
                'type': 'income',
                'id': inc.id,
                'category': inc.category,
                'description': inc.description or 'Income deposit',
                'payment_method': 'Bank Transfer / Cash',
                'amount': float(inc.amount),
                'date': inc.date,
                'notes': 'Recurring' if inc.is_recurring else ''
            })

    if txn_type != 'income':
        for exp in expenses_query.all():
            all_txns.append({
                'type': 'expense',
                'id': exp.id,
                'category': exp.category,
                'description': exp.description,
                'payment_method': exp.payment_method,
                'amount': float(exp.amount),
                'date': exp.date,
                'notes': exp.notes or ''
            })

    # Sorting
    if sort_by == 'date_asc':
        all_txns.sort(key=lambda x: x['date'])
    elif sort_by == 'amount_desc':
        all_txns.sort(key=lambda x: x['amount'], reverse=True)
    elif sort_by == 'amount_asc':
        all_txns.sort(key=lambda x: x['amount'])
    else:  # default date_desc
        all_txns.sort(key=lambda x: x['date'], reverse=True)

    # Totals in filtered view
    total_inc = sum(t['amount'] for t in all_txns if t['type'] == 'income')
    total_exp = sum(t['amount'] for t in all_txns if t['type'] == 'expense')
    net_flow = total_inc - total_exp

    return render_template(
        'transactions.html',
        transactions=all_txns,
        total_inc=round(total_inc, 2),
        total_exp=round(total_exp, 2),
        net_flow=round(net_flow, 2),
        search_query=search_query,
        category=category,
        txn_type=txn_type,
        sort_by=sort_by,
        start_date=start_date_str,
        end_date=end_date_str
    )
