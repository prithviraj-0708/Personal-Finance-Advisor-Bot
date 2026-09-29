from datetime import datetime, date
from decimal import Decimal
from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash

db = SQLAlchemy()

class User(UserMixin, db.Model):
    __tablename__ = 'users'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(255), nullable=False)
    currency = db.Column(db.String(10), default="₹")
    financial_mode = db.Column(db.String(20), default="standard")  # standard, student, freelancer, household
    monthly_allowance = db.Column(db.Numeric(12, 2), default=0.00)  # for student mode
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # Relationships with cascade delete
    incomes = db.relationship('Income', backref='user', lazy='dynamic', cascade='all, delete-orphan')
    expenses = db.relationship('Expense', backref='user', lazy='dynamic', cascade='all, delete-orphan')
    budgets = db.relationship('Budget', backref='user', lazy='dynamic', cascade='all, delete-orphan')
    savings_goals = db.relationship('SavingsGoal', backref='user', lazy='dynamic', cascade='all, delete-orphan')
    ai_conversations = db.relationship('AIConversation', backref='user', lazy='dynamic', cascade='all, delete-orphan')
    notifications = db.relationship('Notification', backref='user', lazy='dynamic', cascade='all, delete-orphan')

    def set_password(self, password):
        self.password_hash = generate_password_hash(password, method='pbkdf2:sha256')

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    def __repr__(self):
        return f"<User {self.email}>"


class Income(db.Model):
    __tablename__ = 'incomes'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='CASCADE'), nullable=False, index=True)
    amount = db.Column(db.Numeric(12, 2), nullable=False)
    category = db.Column(db.String(50), nullable=False)  # Salary, Freelancing, Business, Allowance, Investments, Other
    description = db.Column(db.String(255), nullable=True)
    date = db.Column(db.Date, nullable=False, default=date.today)
    is_recurring = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def to_dict(self):
        return {
            'id': self.id,
            'amount': float(self.amount),
            'category': self.category,
            'description': self.description or '',
            'date': self.date.strftime('%Y-%m-%d'),
            'is_recurring': self.is_recurring,
            'created_at': self.created_at.strftime('%Y-%m-%d %H:%M:%S')
        }


class Expense(db.Model):
    __tablename__ = 'expenses'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='CASCADE'), nullable=False, index=True)
    amount = db.Column(db.Numeric(12, 2), nullable=False)
    category = db.Column(db.String(50), nullable=False)  # Food, Rent, Transportation, Education, Healthcare, Entertainment, Shopping, Utilities, Groceries, Subscriptions, Travel, Other
    description = db.Column(db.String(255), nullable=False)
    payment_method = db.Column(db.String(50), default="UPI/Cash")  # UPI, Cash, Credit Card, Debit Card, Net Banking
    date = db.Column(db.Date, nullable=False, default=date.today)
    notes = db.Column(db.Text, nullable=True)
    is_work_related = db.Column(db.Boolean, default=False)  # Helpful for Freelancer mode
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def to_dict(self):
        return {
            'id': self.id,
            'amount': float(self.amount),
            'category': self.category,
            'description': self.description,
            'payment_method': self.payment_method,
            'date': self.date.strftime('%Y-%m-%d'),
            'notes': self.notes or '',
            'is_work_related': self.is_work_related,
            'created_at': self.created_at.strftime('%Y-%m-%d %H:%M:%S')
        }


class Budget(db.Model):
    __tablename__ = 'budgets'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='CASCADE'), nullable=False, index=True)
    category = db.Column(db.String(50), nullable=False)
    monthly_limit = db.Column(db.Numeric(12, 2), nullable=False)
    month = db.Column(db.Integer, nullable=False)  # 1 - 12
    year = db.Column(db.Integer, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    __table_args__ = (
        db.UniqueConstraint('user_id', 'category', 'month', 'year', name='uq_user_category_month_year'),
    )

    def to_dict(self):
        return {
            'id': self.id,
            'category': self.category,
            'monthly_limit': float(self.monthly_limit),
            'month': self.month,
            'year': self.year
        }


class SavingsGoal(db.Model):
    __tablename__ = 'savings_goals'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='CASCADE'), nullable=False, index=True)
    name = db.Column(db.String(100), nullable=False)
    target_amount = db.Column(db.Numeric(12, 2), nullable=False)
    current_amount = db.Column(db.Numeric(12, 2), default=0.00)
    target_date = db.Column(db.Date, nullable=False)
    description = db.Column(db.String(255), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    contributions = db.relationship('SavingsContribution', backref='goal', lazy='dynamic', cascade='all, delete-orphan')

    @property
    def progress_percentage(self):
        if not self.target_amount or float(self.target_amount) == 0:
            return 0
        pct = (float(self.current_amount) / float(self.target_amount)) * 100
        return min(round(pct, 1), 100.0)

    @property
    def remaining_amount(self):
        rem = float(self.target_amount) - float(self.current_amount)
        return max(0.0, round(rem, 2))

    @property
    def months_remaining(self):
        today = date.today()
        if self.target_date <= today:
            return 0
        months = (self.target_date.year - today.year) * 12 + (self.target_date.month - today.month)
        return max(1, months)

    @property
    def monthly_required(self):
        months = self.months_remaining
        if months <= 0:
            return self.remaining_amount
        return round(self.remaining_amount / months, 2)

    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'target_amount': float(self.target_amount),
            'current_amount': float(self.current_amount),
            'target_date': self.target_date.strftime('%Y-%m-%d'),
            'description': self.description or '',
            'progress_percentage': self.progress_percentage,
            'remaining_amount': self.remaining_amount,
            'monthly_required': self.monthly_required,
            'months_remaining': self.months_remaining
        }


class SavingsContribution(db.Model):
    __tablename__ = 'savings_contributions'

    id = db.Column(db.Integer, primary_key=True)
    goal_id = db.Column(db.Integer, db.ForeignKey('savings_goals.id', ondelete='CASCADE'), nullable=False, index=True)
    amount = db.Column(db.Numeric(12, 2), nullable=False)
    date = db.Column(db.Date, nullable=False, default=date.today)
    description = db.Column(db.String(255), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def to_dict(self):
        return {
            'id': self.id,
            'goal_id': self.goal_id,
            'amount': float(self.amount),
            'date': self.date.strftime('%Y-%m-%d'),
            'description': self.description or '',
            'created_at': self.created_at.strftime('%Y-%m-%d %H:%M:%S')
        }


class AIConversation(db.Model):
    __tablename__ = 'ai_conversations'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='CASCADE'), nullable=False, index=True)
    message = db.Column(db.Text, nullable=False)
    response = db.Column(db.Text, nullable=False)
    is_fallback = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def to_dict(self):
        return {
            'id': self.id,
            'message': self.message,
            'response': self.response,
            'is_fallback': self.is_fallback,
            'created_at': self.created_at.strftime('%Y-%m-%d %H:%M:%S')
        }


class Notification(db.Model):
    __tablename__ = 'notifications'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='CASCADE'), nullable=False, index=True)
    title = db.Column(db.String(100), nullable=False)
    message = db.Column(db.String(255), nullable=False)
    type = db.Column(db.String(20), default="info")  # info, warning, danger, success
    is_read = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def to_dict(self):
        return {
            'id': self.id,
            'title': self.title,
            'message': self.message,
            'type': self.type,
            'is_read': self.is_read,
            'created_at': self.created_at.strftime('%Y-%m-%d %H:%M:%S')
        }
