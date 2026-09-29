from datetime import date
from decimal import Decimal
from sqlalchemy import func, extract
from models import db, Income, Expense, Budget

ESSENTIAL_CATEGORIES = {'Food', 'Rent', 'Transportation', 'Education', 'Healthcare', 'Utilities', 'Groceries'}
DISCRETIONARY_CATEGORIES = {'Entertainment', 'Shopping', 'Subscriptions', 'Travel', 'Other'}

class BudgetService:

    @staticmethod
    def generate_smart_budget(user, month=None, year=None, custom_income=None):
        """Generates a personalized budget recommendation based on user mode, income, and spending history."""
        today = date.today()
        month = month or today.month
        year = year or today.year

        # 1. Determine effective income
        if custom_income and float(custom_income) > 0:
            effective_income = float(custom_income)
        else:
            # Check current month income
            inc = float(db.session.query(func.coalesce(func.sum(Income.amount), 0)).filter(
                Income.user_id == user.id,
                extract('month', Income.date) == month,
                extract('year', Income.date) == year
            ).scalar())

            if inc > 0:
                effective_income = inc
            elif user.financial_mode == 'student' and user.monthly_allowance and float(user.monthly_allowance) > 0:
                effective_income = float(user.monthly_allowance)
            else:
                # Average of last 3 months
                avg_inc = float(db.session.query(func.coalesce(func.avg(Income.amount), 0)).filter(
                    Income.user_id == user.id
                ).scalar())
                effective_income = avg_inc if avg_inc > 0 else 25000.0  # default starter baseline if totally empty

        # 2. Analyze historical category proportions if user has past expenses
        past_expenses = db.session.query(
            Expense.category,
            func.sum(Expense.amount).label('total')
        ).filter(
            Expense.user_id == user.id
        ).group_by(Expense.category).all()

        total_historical_spent = sum(float(r.total) for r in past_expenses)
        historical_weights = {}
        if total_historical_spent > 0:
            for r in past_expenses:
                historical_weights[r.category] = float(r.total) / total_historical_spent

        # 3. Determine allocation template based on mode
        mode = user.financial_mode or 'standard'

        if mode == 'student':
            # Target 15% savings, 85% expenses focused on college life
            savings_target = effective_income * 0.15
            spendable = effective_income * 0.85
            base_proportions = {
                'Food': 0.35,
                'Transportation': 0.20,
                'Education': 0.15,
                'Entertainment': 0.10,
                'Shopping': 0.08,
                'Subscriptions': 0.05,
                'Other': 0.07
            }
        elif mode == 'freelancer':
            # Target 25% savings/tax buffer due to income volatility
            savings_target = effective_income * 0.25
            spendable = effective_income * 0.75
            base_proportions = {
                'Rent': 0.25,
                'Groceries': 0.18,
                'Food': 0.12,
                'Utilities': 0.10,
                'Transportation': 0.10,
                'Healthcare': 0.08,
                'Education': 0.07,
                'Other': 0.10
            }
        elif mode == 'household':
            # Target 20% savings, emphasis on groceries, utilities, rent, healthcare
            savings_target = effective_income * 0.20
            spendable = effective_income * 0.80
            base_proportions = {
                'Groceries': 0.24,
                'Rent': 0.24,
                'Utilities': 0.12,
                'Healthcare': 0.10,
                'Education': 0.10,
                'Food': 0.08,
                'Transportation': 0.08,
                'Other': 0.04
            }
        else:
            # Standard mode (50/30/20 guideline)
            savings_target = effective_income * 0.20
            spendable = effective_income * 0.80
            base_proportions = {
                'Rent': 0.26,
                'Groceries': 0.18,
                'Food': 0.12,
                'Transportation': 0.10,
                'Utilities': 0.08,
                'Healthcare': 0.06,
                'Entertainment': 0.08,
                'Shopping': 0.06,
                'Subscriptions': 0.03,
                'Other': 0.03
            }

        # 4. Blend historical spending habits (40%) with optimal guideline (60%) if historical data exists
        final_categories = {}
        all_categories = set(base_proportions.keys()) | set(historical_weights.keys())

        for cat in all_categories:
            base_p = base_proportions.get(cat, 0.02)
            hist_p = historical_weights.get(cat, base_p)
            blended_p = (0.60 * base_p) + (0.40 * hist_p)
            final_categories[cat] = blended_p

        # Normalize proportions so sum == 1.0
        sum_p = sum(final_categories.values())
        if sum_p > 0:
            final_categories = {k: v / sum_p for k, v in final_categories.items()}

        recommended_budgets = []
        for cat, prop in sorted(final_categories.items(), key=lambda x: x[1], reverse=True):
            limit_amount = round(spendable * prop, 0)
            if limit_amount >= 50:  # ignore tiny negligible amounts
                recommended_budgets.append({
                    'category': cat,
                    'monthly_limit': limit_amount,
                    'is_essential': cat in ESSENTIAL_CATEGORIES,
                    'share_percentage': round(prop * 100, 1)
                })

        return {
            'mode': mode,
            'effective_income': round(effective_income, 2),
            'target_savings': round(savings_target, 2),
            'total_spendable_budget': round(spendable, 2),
            'weekly_allowance': round(effective_income / 4, 2) if mode == 'student' else None,
            'budgets': recommended_budgets,
            'month': month,
            'year': year
        }

    @staticmethod
    def apply_generated_budgets(user_id, budget_list, month, year):
        """Applies or updates generated budgets in the database for the given month/year."""
        applied_count = 0
        for item in budget_list:
            cat = item.get('category')
            limit = Decimal(str(item.get('monthly_limit', 0)))
            if limit <= 0:
                continue

            existing = Budget.query.filter_by(
                user_id=user_id,
                category=cat,
                month=month,
                year=year
            ).first()

            if existing:
                existing.monthly_limit = limit
            else:
                new_budget = Budget(
                    user_id=user_id,
                    category=cat,
                    monthly_limit=limit,
                    month=month,
                    year=year
                )
                db.session.add(new_budget)
            applied_count += 1

        db.session.commit()
        return applied_count
