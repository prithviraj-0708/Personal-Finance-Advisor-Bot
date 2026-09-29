from flask import Blueprint, render_template, redirect, url_for, flash, request, jsonify
from flask_login import login_user, logout_user, login_required, current_user
from datetime import date, datetime, timedelta
from decimal import Decimal
import random

from models import db, User, Income, Expense, Budget, SavingsGoal, SavingsContribution, Notification
from forms import LoginForm, RegisterForm, ProfileSettingsForm, PasswordChangeForm

auth_bp = Blueprint('auth', __name__)

@auth_bp.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard.index'))

    form = RegisterForm()
    if form.validate_on_submit():
        user = User(
            name=form.name.data.strip(),
            email=form.email.data.strip().lower(),
            financial_mode=form.financial_mode.data,
            currency=form.currency.data
        )
        user.set_password(form.password.data)
        db.session.add(user)
        db.session.commit()

        # Add welcome notification
        welcome_note = Notification(
            user_id=user.id,
            title="Welcome to Personal Finance Advisor!",
            message=f"Account initialized in {user.financial_mode.title()} Mode. Start by adding your income and expenses.",
            type="success"
        )
        db.session.add(welcome_note)
        db.session.commit()

        flash('Your account has been created! Please log in to continue.', 'success')
        return redirect(url_for('auth.login'))

    return render_template('register.html', form=form)


@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard.index'))

    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data.strip().lower()).first()
        if user and user.check_password(form.password.data):
            login_user(user, remember=form.remember.data)
            flash(f"Welcome back, {user.name}!", "success")
            next_page = request.args.get('next')
            return redirect(next_page if next_page else url_for('dashboard.index'))
        else:
            flash('Invalid email or password. Please check your credentials.', 'danger')

    return render_template('login.html', form=form)


@auth_bp.route('/logout')
@login_required
def logout():
    logout_user()
    flash('You have been safely signed out.', 'info')
    return redirect(url_for('auth.login'))


@auth_bp.route('/profile', methods=['GET', 'POST'])
@login_required
def profile():
    profile_form = ProfileSettingsForm(obj=current_user)
    password_form = PasswordChangeForm()

    if request.method == 'GET':
        profile_form.financial_mode.data = current_user.financial_mode
        profile_form.currency.data = current_user.currency
        profile_form.monthly_allowance.data = current_user.monthly_allowance

    if 'profile_submit' in request.form and profile_form.validate_on_submit():
        current_user.name = profile_form.name.data.strip()
        current_user.currency = profile_form.currency.data
        current_user.financial_mode = profile_form.financial_mode.data
        current_user.monthly_allowance = profile_form.monthly_allowance.data or 0.0
        db.session.commit()
        flash('Profile settings updated successfully.', 'success')
        return redirect(url_for('auth.profile'))

    if 'password_submit' in request.form and password_form.validate_on_submit():
        if current_user.check_password(password_form.current_password.data):
            current_user.set_password(password_form.new_password.data)
            db.session.commit()
            flash('Password changed successfully!', 'success')
            return redirect(url_for('auth.profile'))
        else:
            flash('Incorrect current password.', 'danger')

    return render_template('profile.html', profile_form=profile_form, password_form=password_form)


@auth_bp.route('/settings', methods=['GET', 'POST'])
@login_required
def settings():
    return render_template('settings.html')


@auth_bp.route('/settings/seed-demo-data', methods=['POST'])
@login_required
def seed_demo_data():
    """Seeds realistic sample income, expenses, budgets, and savings goals for instant demonstration."""
    user_id = current_user.id
    today = date.today()

    # 1. Add Realistic Incomes
    if current_user.financial_mode == 'student':
        incomes = [
            Income(user_id=user_id, amount=Decimal('6000.00'), category='Allowance', description='Monthly Parents Allowance', date=today.replace(day=1), is_recurring=True),
            Income(user_id=user_id, amount=Decimal('2500.00'), category='Freelancing', description='Campus Tutoring & Project Assistance', date=today.replace(day=12), is_recurring=False),
        ]
    elif current_user.financial_mode == 'freelancer':
        incomes = [
            Income(user_id=user_id, amount=Decimal('35000.00'), category='Freelancing', description='UI/UX Web Design Client Milestone', date=today.replace(day=3), is_recurring=False),
            Income(user_id=user_id, amount=Decimal('22000.00'), category='Freelancing', description='Mobile App Consultation Retainer', date=today.replace(day=15), is_recurring=True),
            Income(user_id=user_id, amount=Decimal('8000.00'), category='Investments', description='Mutual Fund Dividends', date=today.replace(day=18), is_recurring=False),
        ]
    elif current_user.financial_mode == 'household':
        incomes = [
            Income(user_id=user_id, amount=Decimal('55000.00'), category='Salary', description='Primary Salary Deposit', date=today.replace(day=1), is_recurring=True),
            Income(user_id=user_id, amount=Decimal('30000.00'), category='Salary', description='Partner / Household Contribution', date=today.replace(day=5), is_recurring=True),
            Income(user_id=user_id, amount=Decimal('5000.00'), category='Investments', description='Rental & FD Interest', date=today.replace(day=10), is_recurring=False),
        ]
    else:
        # Standard mode
        incomes = [
            Income(user_id=user_id, amount=Decimal('45000.00'), category='Salary', description='Tech Corp Monthly Salary', date=today.replace(day=1), is_recurring=True),
            Income(user_id=user_id, amount=Decimal('12000.00'), category='Freelancing', description='Weekend Consulting Retainer', date=today.replace(day=14), is_recurring=False),
        ]

    for inc in incomes:
        db.session.add(inc)

    # 2. Add Realistic Expenses
    sample_expenses = [
        ('Rent', 12000 if current_user.financial_mode != 'student' else 2000, 'Apartment Monthly Rent', 'Net Banking', 2),
        ('Groceries', 4500 if current_user.financial_mode != 'student' else 1200, 'Supermarket Monthly Essentials & Veggies', 'UPI', 4),
        ('Food', 1800, 'Dinner Outing with College Peers', 'UPI', 6),
        ('Transportation', 1400, 'Metro Card Recharge & Fuel', 'Credit Card', 8),
        ('Utilities', 2200 if current_user.financial_mode != 'student' else 400, 'Electricity & Broadband Bill', 'UPI', 10),
        ('Entertainment', 950, 'Weekend Cinema & Snacks', 'UPI', 11),
        ('Subscriptions', 499, 'Spotify & Cloud Storage', 'Credit Card', 13),
        ('Healthcare', 800, 'Pharmacy & Health Vitamins', 'Cash', 16),
        ('Shopping', 2400, 'Office Work Apparel', 'Credit Card', 19),
        ('Education', 1500, 'Online Certification & Book', 'UPI', 22),
    ]

    for cat, amt, desc, pay_method, day_offset in sample_expenses:
        exp_date = today.replace(day=min(day_offset, 28))
        exp = Expense(
            user_id=user_id,
            amount=Decimal(str(amt)),
            category=cat,
            description=desc,
            payment_method=pay_method,
            date=exp_date,
            is_work_related=(cat in ['Education', 'Subscriptions'] and current_user.financial_mode == 'freelancer')
        )
        db.session.add(exp)

    # 3. Add Realistic Budgets
    sample_budgets = [
        ('Rent', 12000 if current_user.financial_mode != 'student' else 2500),
        ('Groceries', 5000 if current_user.financial_mode != 'student' else 1500),
        ('Food', 2500),
        ('Transportation', 2000),
        ('Utilities', 2500),
        ('Entertainment', 1200),
        ('Shopping', 3000),
        ('Healthcare', 1500),
    ]

    for cat, limit in sample_budgets:
        existing = Budget.query.filter_by(user_id=user_id, category=cat, month=today.month, year=today.year).first()
        if not existing:
            b = Budget(user_id=user_id, category=cat, monthly_limit=Decimal(str(limit)), month=today.month, year=today.year)
            db.session.add(b)

    # 4. Add Realistic Savings Goals
    existing_goals = SavingsGoal.query.filter_by(user_id=user_id).count()
    if existing_goals == 0:
        g1 = SavingsGoal(
            user_id=user_id,
            name="Emergency Rainy Day Fund",
            target_amount=Decimal('50000.00'),
            current_amount=Decimal('28000.00'),
            target_date=today + timedelta(days=120),
            description="3 months of essential fixed living expenses"
        )
        g2 = SavingsGoal(
            user_id=user_id,
            name="New Work Laptop & Monitor",
            target_amount=Decimal('65000.00'),
            current_amount=Decimal('42000.00'),
            target_date=today + timedelta(days=90),
            description="Upgrading workstation for productivity"
        )
        db.session.add_all([g1, g2])
        db.session.flush()

        # Add contribution records
        c1 = SavingsContribution(goal_id=g1.id, amount=Decimal('5000.00'), date=today - timedelta(days=15), description="Monthly bonus deposit")
        c2 = SavingsContribution(goal_id=g2.id, amount=Decimal('7000.00'), date=today - timedelta(days=5), description="Project payout savings")
        db.session.add_all([c1, c2])

    db.session.commit()
    flash("Realistic sample demo data loaded successfully! Explore your Dashboard, Charts, and AI Advisor.", "success")
    return redirect(url_for('dashboard.index'))


@auth_bp.route('/settings/clear-demo-data', methods=['POST'])
@login_required
def clear_demo_data():
    """Clears all financial data for current user to reset fresh."""
    user_id = current_user.id
    Expense.query.filter_by(user_id=user_id).delete()
    Income.query.filter_by(user_id=user_id).delete()
    Budget.query.filter_by(user_id=user_id).delete()
    
    # Cascade will clean contributions
    SavingsGoal.query.filter_by(user_id=user_id).delete()
    Notification.query.filter_by(user_id=user_id).delete()
    db.session.commit()

    flash("All user transactions, budgets, and savings goals have been cleared.", "info")
    return redirect(url_for('dashboard.index'))
