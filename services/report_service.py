import csv
import io
from datetime import date
from models import Income, Expense, Budget, SavingsGoal

class ReportService:

    @staticmethod
    def export_transactions_csv(user_id):
        """Generates a CSV string containing all user incomes and expenses combined and sorted."""
        output = io.StringIO()
        writer = csv.writer(output)
        
        # Write headers
        writer.writerow(['Type', 'Date', 'Category', 'Description', 'Payment Method', 'Amount', 'Recurring/Notes'])

        incomes = Income.query.filter_by(user_id=user_id).order_by(Income.date.desc()).all()
        expenses = Expense.query.filter_by(user_id=user_id).order_by(Expense.date.desc()).all()

        all_records = []
        for inc in incomes:
            all_records.append({
                'type': 'Income',
                'date': inc.date,
                'category': inc.category,
                'description': inc.description or '',
                'payment_method': 'Bank/Deposit',
                'amount': float(inc.amount),
                'notes': 'Recurring' if inc.is_recurring else ''
            })

        for exp in expenses:
            all_records.append({
                'type': 'Expense',
                'date': exp.date,
                'category': exp.category,
                'description': exp.description,
                'payment_method': exp.payment_method,
                'amount': -float(exp.amount),
                'notes': exp.notes or ''
            })

        all_records.sort(key=lambda x: x['date'], reverse=True)

        for r in all_records:
            writer.writerow([
                r['type'],
                r['date'].strftime('%Y-%m-%d'),
                r['category'],
                r['description'],
                r['payment_method'],
                r['amount'],
                r['notes']
            ])

        return output.getvalue()

    @staticmethod
    def export_budgets_csv(user_id, month=None, year=None):
        """Generates a CSV string of budget allocations."""
        output = io.StringIO()
        writer = csv.writer(output)
        writer.writerow(['Month', 'Year', 'Category', 'Monthly Limit'])

        query = Budget.query.filter_by(user_id=user_id)
        if month and year:
            query = query.filter_by(month=month, year=year)

        budgets = query.order_by(Budget.year.desc(), Budget.month.desc()).all()
        for b in budgets:
            writer.writerow([b.month, b.year, b.category, float(b.monthly_limit)])

        return output.getvalue()

    @staticmethod
    def export_savings_csv(user_id):
        """Generates a CSV string of savings goals and progress."""
        output = io.StringIO()
        writer = csv.writer(output)
        writer.writerow(['Goal Name', 'Target Amount', 'Current Amount', 'Target Date', 'Progress %', 'Monthly Required'])

        goals = SavingsGoal.query.filter_by(user_id=user_id).all()
        for g in goals:
            writer.writerow([
                g.name,
                float(g.target_amount),
                float(g.current_amount),
                g.target_date.strftime('%Y-%m-%d'),
                f"{g.progress_percentage}%",
                g.monthly_required
            ])

        return output.getvalue()
