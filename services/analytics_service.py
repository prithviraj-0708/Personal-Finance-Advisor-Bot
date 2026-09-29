from datetime import date, datetime, timedelta
from decimal import Decimal
from sqlalchemy import func, extract
from models import db, Income, Expense, Budget, SavingsGoal, Notification

class AnalyticsService:

    @staticmethod
    def get_monthly_metrics(user_id, target_date=None):
        """Calculates total income, total expense, net savings, and savings rate for a given month."""
        if not target_date:
            target_date = date.today()
            
        month = target_date.month
        year = target_date.year

        # Total monthly income
        income_query = db.session.query(func.coalesce(func.sum(Income.amount), 0)).filter(
            Income.user_id == user_id,
            extract('month', Income.date) == month,
            extract('year', Income.date) == year
        )
        total_income = float(income_query.scalar())

        # Total monthly expenses
        expense_query = db.session.query(func.coalesce(func.sum(Expense.amount), 0)).filter(
            Expense.user_id == user_id,
            extract('month', Expense.date) == month,
            extract('year', Expense.date) == year
        )
        total_expenses = float(expense_query.scalar())

        net_savings = total_income - total_expenses
        savings_rate = round((net_savings / total_income * 100), 1) if total_income > 0 else 0.0

        # Total monthly budget limit
        budget_query = db.session.query(func.coalesce(func.sum(Budget.monthly_limit), 0)).filter(
            Budget.user_id == user_id,
            Budget.month == month,
            Budget.year == year
        )
        total_budget = float(budget_query.scalar())
        remaining_budget = total_budget - total_expenses if total_budget > 0 else (total_income - total_expenses)
        budget_utilization = round((total_expenses / total_budget * 100), 1) if total_budget > 0 else 0.0

        return {
            'month': month,
            'year': year,
            'month_name': target_date.strftime('%B %Y'),
            'total_income': round(total_income, 2),
            'total_expenses': round(total_expenses, 2),
            'net_savings': round(net_savings, 2),
            'savings_rate': savings_rate,
            'total_budget': round(total_budget, 2),
            'remaining_budget': round(remaining_budget, 2),
            'budget_utilization': budget_utilization
        }

    @staticmethod
    def get_category_breakdown(user_id, month=None, year=None):
        """Returns expense breakdown by category with amounts and percentages."""
        if not month or not year:
            today = date.today()
            month = today.month
            year = today.year

        expenses = db.session.query(
            Expense.category,
            func.sum(Expense.amount).label('total'),
            func.count(Expense.id).label('count')
        ).filter(
            Expense.user_id == user_id,
            extract('month', Expense.date) == month,
            extract('year', Expense.date) == year
        ).group_by(Expense.category).order_by(func.sum(Expense.amount).desc()).all()

        total_sum = sum(float(item.total) for item in expenses)
        
        breakdown = []
        for item in expenses:
            amt = float(item.total)
            pct = round((amt / total_sum * 100), 1) if total_sum > 0 else 0.0
            breakdown.append({
                'category': item.category,
                'amount': round(amt, 2),
                'percentage': pct,
                'count': item.count
            })

        return breakdown

    @staticmethod
    def get_income_category_breakdown(user_id, month=None, year=None):
        """Returns income breakdown by source category."""
        if not month or not year:
            today = date.today()
            month = today.month
            year = today.year

        incomes = db.session.query(
            Income.category,
            func.sum(Income.amount).label('total')
        ).filter(
            Income.user_id == user_id,
            extract('month', Income.date) == month,
            extract('year', Income.date) == year
        ).group_by(Income.category).order_by(func.sum(Income.amount).desc()).all()

        total_sum = sum(float(item.total) for item in incomes)
        breakdown = []
        for item in incomes:
            amt = float(item.total)
            pct = round((amt / total_sum * 100), 1) if total_sum > 0 else 0.0
            breakdown.append({
                'category': item.category,
                'amount': round(amt, 2),
                'percentage': pct
            })
        return breakdown

    @staticmethod
    def get_budget_utilization_details(user_id, month=None, year=None):
        """Compares budget limits against actual spending per category."""
        if not month or not year:
            today = date.today()
            month = today.month
            year = today.year

        budgets = Budget.query.filter_by(user_id=user_id, month=month, year=year).all()
        
        # Actual spending in this month per category
        spending_records = db.session.query(
            Expense.category,
            func.sum(Expense.amount).label('spent')
        ).filter(
            Expense.user_id == user_id,
            extract('month', Expense.date) == month,
            extract('year', Expense.date) == year
        ).group_by(Expense.category).all()
        
        spending_map = {r.category: float(r.spent) for r in spending_records}

        result = []
        for b in budgets:
            limit = float(b.monthly_limit)
            spent = spending_map.get(b.category, 0.0)
            remaining = limit - spent
            pct = round((spent / limit * 100), 1) if limit > 0 else 0.0
            status = 'safe'
            if pct >= 100:
                status = 'over'
            elif pct >= 80:
                status = 'warning'

            result.append({
                'id': b.id,
                'category': b.category,
                'limit': round(limit, 2),
                'spent': round(spent, 2),
                'remaining': round(remaining, 2),
                'percentage': pct,
                'status': status
            })

        # Also add unbudgeted categories where expenses occurred
        budgeted_categories = {b.category for b in budgets}
        for cat, spent in spending_map.items():
            if cat not in budgeted_categories:
                result.append({
                    'id': None,
                    'category': cat,
                    'limit': 0.0,
                    'spent': round(spent, 2),
                    'remaining': round(-spent, 2),
                    'percentage': 100.0,
                    'status': 'unbudgeted'
                })

        return result

    @staticmethod
    def get_six_months_history(user_id):
        """Returns 6-month historical trend of income vs expenses."""
        today = date.today()
        months_data = []

        for i in range(5, -1, -1):
            # Calculate target month and year
            year = today.year
            month = today.month - i
            while month <= 0:
                month += 12
                year -= 1

            inc = float(db.session.query(func.coalesce(func.sum(Income.amount), 0)).filter(
                Income.user_id == user_id,
                extract('month', Income.date) == month,
                extract('year', Income.date) == year
            ).scalar())

            exp = float(db.session.query(func.coalesce(func.sum(Expense.amount), 0)).filter(
                Expense.user_id == user_id,
                extract('month', Expense.date) == month,
                extract('year', Expense.date) == year
            ).scalar())

            m_name = date(year, month, 1).strftime('%b %y')
            months_data.append({
                'label': m_name,
                'month': month,
                'year': year,
                'income': round(inc, 2),
                'expense': round(exp, 2),
                'savings': round(inc - exp, 2)
            })

        return months_data

    @staticmethod
    def check_and_generate_notifications(user):
        """Generates smart notifications based on spending thresholds and goals."""
        today = date.today()
        user_id = user.id

        # 1. Check budget overruns
        budget_details = AnalyticsService.get_budget_utilization_details(user_id, today.month, today.year)
        for b in budget_details:
            if b['status'] == 'over':
                msg = f"You exceeded your monthly limit for {b['category']} by {user.currency}{abs(b['remaining']):,.2f}!"
                _create_unique_notification(user_id, f"Budget Alert: {b['category']}", msg, "danger")
            elif b['status'] == 'warning':
                msg = f"You have used {b['percentage']}% of your {b['category']} budget ({user.currency}{b['spent']:,.2f} / {user.currency}{b['limit']:,.2f})."
                _create_unique_notification(user_id, f"Budget Warning: {b['category']}", msg, "warning")

        # 2. Check previous month comparison
        prev_month_date = today.replace(day=1) - timedelta(days=1)
        cur_metrics = AnalyticsService.get_monthly_metrics(user_id, today)
        prev_metrics = AnalyticsService.get_monthly_metrics(user_id, prev_month_date)

        if prev_metrics['total_expenses'] > 0 and cur_metrics['total_expenses'] > prev_metrics['total_expenses']:
            diff = cur_metrics['total_expenses'] - prev_metrics['total_expenses']
            pct_inc = round((diff / prev_metrics['total_expenses']) * 100, 1)
            msg = f"Your monthly spending is {pct_inc}% higher than last month (+{user.currency}{diff:,.2f})."
            _create_unique_notification(user_id, "Spending Increase Alert", msg, "info")

        # 3. Check savings goals
        goals = SavingsGoal.query.filter_by(user_id=user_id).all()
        for g in goals:
            if g.progress_percentage >= 100:
                msg = f"Congratulations! You reached 100% of your savings goal for '{g.name}'!"
                _create_unique_notification(user_id, f"Goal Achieved: {g.name}", msg, "success")
            elif g.progress_percentage >= 80:
                msg = f"You are close! '{g.name}' is {g.progress_percentage}% complete ({user.currency}{float(g.current_amount):,.2f} of {user.currency}{float(g.target_amount):,.2f})."
                _create_unique_notification(user_id, f"Goal Milestone: {g.name}", msg, "info")

        # 4. Mode-specific alerts
        if user.financial_mode == 'freelancer':
            # Check if this month's income is lower than last 3-month average
            history = AnalyticsService.get_six_months_history(user_id)
            past_incomes = [h['income'] for h in history[:-1] if h['income'] > 0]
            if len(past_incomes) >= 2:
                avg_income = sum(past_incomes) / len(past_incomes)
                if cur_metrics['total_income'] < (avg_income * 0.75):
                    msg = f"Your income this month ({user.currency}{cur_metrics['total_income']:,.2f}) is over 25% below your average ({user.currency}{round(avg_income, 2):,.2f}). Consider tightening discretionary expenses."
                    _create_unique_notification(user_id, "Freelancer Variable Income Alert", msg, "warning")


def _create_unique_notification(user_id, title, message, notif_type):
    """Ensures notifications aren't duplicated today."""
    today_start = datetime.combine(date.today(), datetime.min.time())
    existing = Notification.query.filter(
        Notification.user_id == user_id,
        Notification.title == title,
        Notification.created_at >= today_start
    ).first()
    if not existing:
        notif = Notification(user_id=user_id, title=title, message=message, type=notif_type)
        db.session.add(notif)
        try:
            db.session.commit()
        except Exception:
            db.session.rollback()
