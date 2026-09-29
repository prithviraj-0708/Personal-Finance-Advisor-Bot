from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, BooleanField, SubmitField, DecimalField, SelectField, DateField, TextAreaField
from wtforms.validators import DataRequired, Email, EqualTo, Length, Optional, NumberRange, ValidationError
from datetime import date
from models import User

INCOME_CATEGORIES = [
    ('Salary', 'Salary'),
    ('Freelancing', 'Freelancing / Gigs'),
    ('Business', 'Business Income'),
    ('Allowance', 'Allowance / Pocket Money'),
    ('Investments', 'Investments / Dividends'),
    ('Other', 'Other Income')
]

EXPENSE_CATEGORIES = [
    ('Food', 'Food & Dining'),
    ('Rent', 'Rent & Housing'),
    ('Transportation', 'Transportation & Fuel'),
    ('Education', 'Education & Books'),
    ('Healthcare', 'Healthcare & Medical'),
    ('Entertainment', 'Entertainment & Outings'),
    ('Shopping', 'Shopping & Clothing'),
    ('Utilities', 'Utilities & Bills'),
    ('Groceries', 'Groceries & Household'),
    ('Subscriptions', 'Subscriptions & Memberships'),
    ('Travel', 'Travel & Vacation'),
    ('Other', 'Other Expenses')
]

PAYMENT_METHODS = [
    ('UPI', 'UPI (Google Pay, PhonePe, Paytm)'),
    ('Cash', 'Cash'),
    ('Credit Card', 'Credit Card'),
    ('Debit Card', 'Debit Card'),
    ('Net Banking', 'Net Banking / Bank Transfer'),
    ('Other', 'Other')
]

FINANCIAL_MODES = [
    ('standard', 'Standard Mode (General Personal Finance)'),
    ('student', 'College Student Mode (Allowance & Campus Life)'),
    ('freelancer', 'Freelancer Mode (Variable Income & Work Expenses)'),
    ('household', 'Household Mode (Family Budget & Bills)')
]

CURRENCIES = [
    ('₹', '₹ (Indian Rupee)'),
    ('$', '$ (US Dollar)'),
    ('€', '€ (Euro)'),
    ('£', '£ (British Pound)'),
    ('C$', 'C$ (Canadian Dollar)'),
    ('A$', 'A$ (Australian Dollar)')
]


class LoginForm(FlaskForm):
    email = StringField('Email Address', validators=[DataRequired(), Email()])
    password = PasswordField('Password', validators=[DataRequired()])
    remember = BooleanField('Remember Me')
    submit = SubmitField('Sign In')


class RegisterForm(FlaskForm):
    name = StringField('Full Name', validators=[DataRequired(), Length(min=2, max=100)])
    email = StringField('Email Address', validators=[DataRequired(), Email()])
    password = PasswordField('Password', validators=[DataRequired(), Length(min=6, message="Password must be at least 6 characters.")])
    confirm_password = PasswordField('Confirm Password', validators=[DataRequired(), EqualTo('password', message="Passwords must match.")])
    financial_mode = SelectField('Preferred Financial Mode', choices=FINANCIAL_MODES, default='standard')
    currency = SelectField('Currency Symbol', choices=CURRENCIES, default='₹')
    submit = SubmitField('Create Account')

    def validate_email(self, email):
        user = User.query.filter_by(email=email.data.strip().lower()).first()
        if user:
            raise ValidationError('That email is already registered. Please sign in or use another email.')


class IncomeForm(FlaskForm):
    amount = DecimalField('Amount', places=2, validators=[DataRequired(), NumberRange(min=0.01, message="Amount must be greater than zero.")])
    category = SelectField('Income Category', choices=INCOME_CATEGORIES, validators=[DataRequired()])
    description = StringField('Source / Description', validators=[Optional(), Length(max=255)])
    date = DateField('Date', default=date.today, validators=[DataRequired()])
    is_recurring = BooleanField('Recurring Monthly Income')
    submit = SubmitField('Save Income')


class ExpenseForm(FlaskForm):
    amount = DecimalField('Amount', places=2, validators=[DataRequired(), NumberRange(min=0.01, message="Amount must be greater than zero.")])
    category = SelectField('Category', choices=EXPENSE_CATEGORIES, validators=[DataRequired()])
    description = StringField('Description / Merchant', validators=[DataRequired(), Length(max=255)])
    payment_method = SelectField('Payment Method', choices=PAYMENT_METHODS, default='UPI')
    date = DateField('Date', default=date.today, validators=[DataRequired()])
    notes = TextAreaField('Optional Notes', validators=[Optional(), Length(max=500)])
    is_work_related = BooleanField('Work / Business Related (for Freelancers)')
    submit = SubmitField('Save Expense')


class BudgetForm(FlaskForm):
    category = SelectField('Category', choices=EXPENSE_CATEGORIES, validators=[DataRequired()])
    monthly_limit = DecimalField('Monthly Spending Limit', places=2, validators=[DataRequired(), NumberRange(min=1, message="Limit must be positive.")])
    month = SelectField('Month', coerce=int, choices=[(i, date(2000, i, 1).strftime('%B')) for i in range(1, 13)], default=date.today().month)
    year = SelectField('Year', coerce=int, choices=[(y, str(y)) for y in range(date.today().year - 1, date.today().year + 3)], default=date.today().year)
    submit = SubmitField('Save Budget Limit')


class SavingsGoalForm(FlaskForm):
    name = StringField('Goal Name (e.g., Emergency Fund, New Laptop)', validators=[DataRequired(), Length(min=2, max=100)])
    target_amount = DecimalField('Target Amount', places=2, validators=[DataRequired(), NumberRange(min=1)])
    current_amount = DecimalField('Initial Saved Amount', places=2, default=0.0, validators=[Optional(), NumberRange(min=0)])
    target_date = DateField('Target Target Date', validators=[DataRequired()])
    description = TextAreaField('Goal Purpose / Notes', validators=[Optional(), Length(max=255)])
    submit = SubmitField('Save Savings Goal')


class SavingsContributionForm(FlaskForm):
    amount = DecimalField('Deposit Amount', places=2, validators=[DataRequired(), NumberRange(min=0.01)])
    date = DateField('Contribution Date', default=date.today, validators=[DataRequired()])
    description = StringField('Note / Source', validators=[Optional(), Length(max=255)])
    submit = SubmitField('Add Deposit')


class ProfileSettingsForm(FlaskForm):
    name = StringField('Full Name', validators=[DataRequired(), Length(min=2, max=100)])
    email = StringField('Email Address', render_kw={'readonly': True})
    currency = SelectField('Preferred Currency Symbol', choices=CURRENCIES)
    financial_mode = SelectField('Financial Management Mode', choices=FINANCIAL_MODES)
    monthly_allowance = DecimalField('Monthly Allowance (Student Mode)', places=2, default=0.0, validators=[Optional(), NumberRange(min=0)])
    submit = SubmitField('Update Profile')


class PasswordChangeForm(FlaskForm):
    current_password = PasswordField('Current Password', validators=[DataRequired()])
    new_password = PasswordField('New Password', validators=[DataRequired(), Length(min=6)])
    confirm_new_password = PasswordField('Confirm New Password', validators=[DataRequired(), EqualTo('new_password', message="New passwords must match.")])
    submit = SubmitField('Change Password')
