import os
from flask import current_app
from datetime import date

# Try importing the official google-genai SDK
try:
    from google import genai
    from google.genai import types
    GENAI_AVAILABLE = True
except ImportError:
    GENAI_AVAILABLE = False


class GeminiService:

    @classmethod
    def get_client(cls):
        api_key = current_app.config.get("GEMINI_API_KEY") or os.getenv("GEMINI_API_KEY")
        if not api_key or not GENAI_AVAILABLE:
            return None
        try:
            return genai.Client(api_key=api_key)
        except Exception:
            return None

    @classmethod
    def is_api_configured(cls):
        api_key = current_app.config.get("GEMINI_API_KEY") or os.getenv("GEMINI_API_KEY")
        return bool(api_key and len(api_key.strip()) > 5)

    @classmethod
    def generate_content(cls, prompt, system_instruction=None):
        """Calls Gemini API if available, else returns None to signal fallback."""
        client = cls.get_client()
        if not client:
            return None

        model_name = current_app.config.get("GEMINI_MODEL", "gemini-2.5-flash")
        try:
            config = None
            if system_instruction:
                config = types.GenerateContentConfig(
                    system_instruction=system_instruction,
                    temperature=0.4
                )
            
            response = client.models.generate_content(
                model=model_name,
                contents=prompt,
                config=config
            )
            return response.text
        except Exception as e:
            current_app.logger.warning(f"Gemini API call failed: {e}. Falling back to rule-based engine.")
            return None

    # ==========================================
    # Feature A: Personalized Budget Recommendations
    # ==========================================
    @classmethod
    def get_budget_advice(cls, user, metrics, category_breakdown, budget_details):
        currency = user.currency
        mode = user.financial_mode

        system_instruction = (
            "You are an empathetic, certified personal finance advisor. "
            "Provide realistic, grounded, actionable budget advice based strictly on user financial numbers. "
            "Never invent fictional balances or transactions. Format in concise bullet points with markdown bolding."
        )

        prompt = f"""
        User Financial Profile:
        - Mode: {mode.title()}
        - Monthly Income: {currency}{metrics['total_income']:,.2f}
        - Monthly Expenses: {currency}{metrics['total_expenses']:,.2f}
        - Net Savings: {currency}{metrics['net_savings']:,.2f} (Savings Rate: {metrics['savings_rate']}%)
        - Total Budget Limit: {currency}{metrics['total_budget']:,.2f}
        - Top Expense Categories: {', '.join([f"{c['category']}: {currency}{c['amount']:,.2f} ({c['percentage']}%)" for c in category_breakdown[:4]]) or 'None recorded yet'}
        - Budget Overruns/Warnings: {', '.join([f"{b['category']} ({b['percentage']}%)" for b in budget_details if b['percentage'] >= 80]) or 'None'}

        Please generate:
        1. 3 specific budget adjustments tailored to {mode} lifestyle.
        2. Where to reallocate funds to reach at least a 20% savings rate.
        3. Recommended spending limits for top 3 categories.
        Keep it direct, professional, and within 250 words.
        """

        ai_res = cls.generate_content(prompt, system_instruction)
        if ai_res:
            return {'text': ai_res, 'is_fallback': False}

        # Rule-based fallback
        return {
            'text': cls._fallback_budget_advice(user, metrics, category_breakdown, budget_details),
            'is_fallback': True
        }

    # ==========================================
    # Feature B: Spending Analysis & Anomaly Detection
    # ==========================================
    @classmethod
    def analyze_spending(cls, user, metrics, category_breakdown, budget_details):
        currency = user.currency
        system_instruction = (
            "You are a financial forensics and spending analyst. "
            "Identify spending leaks, high-risk categories, and behavioral patterns from user transactions."
        )

        prompt = f"""
        Analyze current spending for {user.name}:
        - Monthly Income: {currency}{metrics['total_income']:,.2f}
        - Total Expenses: {currency}{metrics['total_expenses']:,.2f}
        - Category Breakdown: {', '.join([f"{c['category']}: {currency}{c['amount']:,.2f} ({c['percentage']}%)" for c in category_breakdown])}
        - Overspending Categories: {', '.join([f"{b['category']} ({b['percentage']}% utilized)" for b in budget_details if b['percentage'] >= 100]) or 'None'}

        Highlight:
        1. Primary money drain categories.
        2. Discretionary vs Essential spend ratio evaluation.
        3. Actionable quick-win cuts for this upcoming week.
        Keep it concise, friendly, and practical.
        """

        ai_res = cls.generate_content(prompt, system_instruction)
        if ai_res:
            return {'text': ai_res, 'is_fallback': False}

        return {
            'text': cls._fallback_spending_analysis(user, metrics, category_breakdown, budget_details),
            'is_fallback': True
        }

    # ==========================================
    # Feature C: Savings Recommendations & Goals
    # ==========================================
    @classmethod
    def get_savings_advice(cls, user, metrics, goals):
        currency = user.currency
        system_instruction = (
            "You are a wealth-building coach. Suggest realistic ways to increase monthly savings consistency, "
            "manage irregular cash flow, and fund savings goals without extreme austerity."
        )

        goals_summary = ', '.join([
            f"{g.name} (Target: {currency}{float(g.target_amount):,.2f}, Saved: {currency}{float(g.current_amount):,.2f}, {g.progress_percentage}%)"
            for g in goals
        ]) or "No active savings goals set."

        prompt = f"""
        User Financial Position:
        - Monthly Income: {currency}{metrics['total_income']:,.2f}
        - Monthly Expenses: {currency}{metrics['total_expenses']:,.2f}
        - Current Monthly Net Savings: {currency}{metrics['net_savings']:,.2f}
        - Savings Rate: {metrics['savings_rate']}%
        - Active Goals: {goals_summary}

        Provide:
        1. Milestone pacing: Are current contributions sufficient for target dates?
        2. The 10% trim tactic: Two specific habits to shave expenses safely.
        3. Emergency fund guideline suitable for their {user.financial_mode} status.
        """

        ai_res = cls.generate_content(prompt, system_instruction)
        if ai_res:
            return {'text': ai_res, 'is_fallback': False}

        return {
            'text': cls._fallback_savings_advice(user, metrics, goals),
            'is_fallback': True
        }

    # ==========================================
    # Feature D: Financial Chatbot
    # ==========================================
    @classmethod
    def chat_response(cls, user_message, user, metrics, category_breakdown, budget_details, goals, history=None):
        currency = user.currency
        system_instruction = f"""
        You are the Personal Finance Advisor Bot assistant for {user.name}.
        You have direct access to their authenticated financial ledger:
        - Currency: {currency}
        - Mode: {user.financial_mode}
        - Total Monthly Income: {currency}{metrics['total_income']:,.2f}
        - Total Monthly Expenses: {currency}{metrics['total_expenses']:,.2f}
        - Current Net Savings: {currency}{metrics['net_savings']:,.2f} (Savings Rate: {metrics['savings_rate']}%)
        - Monthly Budget Limit: {currency}{metrics['total_budget']:,.2f} (Remaining: {currency}{metrics['remaining_budget']:,.2f})
        - Spending Categories: {', '.join([f"{c['category']}={currency}{c['amount']:,.2f} ({c['percentage']}%)" for c in category_breakdown]) or 'No expenses yet'}
        - Active Savings Goals: {', '.join([f"{g.name}: {currency}{float(g.current_amount):,.2f}/{currency}{float(g.target_amount):,.2f}" for g in goals]) or 'None'}

        RULES:
        1. Always answer user questions using their REAL financial numbers above.
        2. Never invent imaginary expenses or accounts.
        3. Do not give direct investment stock picks or guaranteed returns. Focus on budgeting, saving, and debt prudence.
        4. Keep answers concise, clear, and structured with markdown.
        """

        # Build context prompt
        conv_context = ""
        if history:
            conv_context = "\n".join([f"User: {h.message}\nAssistant: {h.response}" for h in history[-4:]]) + "\n"

        full_prompt = f"{conv_context}User: {user_message}\nAssistant:"
        ai_res = cls.generate_content(full_prompt, system_instruction)
        if ai_res:
            return {'text': ai_res, 'is_fallback': False}

        # Rule-based fallback chatbot handler
        return {
            'text': cls._fallback_chat(user_message, user, metrics, category_breakdown, budget_details, goals),
            'is_fallback': True
        }

    # ==========================================
    # Feature E: Monthly Financial Health Summary
    # ==========================================
    @classmethod
    def get_financial_health_summary(cls, user, metrics, category_breakdown, budget_details, goals):
        currency = user.currency
        system_instruction = (
            "You are a senior financial analyst writing a monthly executive financial health report card."
        )

        prompt = f"""
        Generate a comprehensive Financial Health Summary for {user.name} ({metrics['month_name']}):
        - Total Income: {currency}{metrics['total_income']:,.2f}
        - Total Expenses: {currency}{metrics['total_expenses']:,.2f}
        - Net Savings: {currency}{metrics['net_savings']:,.2f}
        - Savings Rate: {metrics['savings_rate']}%
        - Top Expense Category: {category_breakdown[0]['category'] if category_breakdown else 'N/A'} ({currency}{category_breakdown[0]['amount']:,.2f} if category_breakdown else 0)
        - Budget Performance: {metrics['budget_utilization']}% utilization against {currency}{metrics['total_budget']:,.2f} limit

        Structure with:
        1. Overall Financial Health Grade (A/B/C/D) with brief rationale.
        2. Top Spending Highlights & Key Patterns.
        3. Budget Discipline Score.
        4. 3 Actionable Directives for Next Month.
        """

        ai_res = cls.generate_content(prompt, system_instruction)
        if ai_res:
            return {'text': ai_res, 'is_fallback': False}

        return {
            'text': cls._fallback_financial_summary(user, metrics, category_breakdown, budget_details, goals),
            'is_fallback': True
        }

    # =========================================================================
    # FALLBACK RULE-BASED ENGINE (Operates seamlessly without API Key)
    # =========================================================================

    @classmethod
    def _fallback_budget_advice(cls, user, metrics, category_breakdown, budget_details):
        c = user.currency
        income = metrics['total_income']
        expenses = metrics['total_expenses']
        savings_rate = metrics['savings_rate']

        points = []
        if income == 0:
            return (
                f"### 📋 Rule-Based Budget Recommendations\n\n"
                f"• **Add Income Records:** You have not logged any income for this month yet. Start by logging your salary, allowance, or freelance invoices on the **Income** tab.\n"
                f"• **Starter Budget Rule:** Aim for the standard 50/30/20 guideline (50% essentials like rent/groceries, 30% lifestyle, 20% savings).\n"
                f"• **Category Caps:** Create proactive budget limits in the **Budget Planner** before expenses occur."
            )

        if savings_rate < 15:
            points.append(f"• **Boost Savings Rate:** Your current savings rate is **{savings_rate}%** ({c}{metrics['net_savings']:,.2f}). To build resilience, aim to preserve at least **20%** ({c}{round(income * 0.20, 2):,.2f}).")
        else:
            points.append(f"• **Healthy Savings Velocity:** Excellent discipline! You are retaining **{savings_rate}%** of your income this month.")

        over_cats = [b for b in budget_details if b['percentage'] >= 100]
        if over_cats:
            over_names = ", ".join([f"**{b['category']}** ({b['percentage']}%)" for b in over_cats[:3]])
            points.append(f"• **Budget Overruns Detected:** You have exceeded spending limits in: {over_names}. Pause discretionary shopping in these areas until next month.")

        if category_breakdown:
            top = category_breakdown[0]
            points.append(f"• **Top Expense Driver:** **{top['category']}** accounts for **{top['percentage']}%** ({c}{top['amount']:,.2f}) of your spending. Re-evaluating this category yields the highest impact.")

        if user.financial_mode == 'student':
            points.append(f"• **Student Tip:** Track food and campus travel closely. Using weekly allowance buckets prevents running dry before the month ends.")
        elif user.financial_mode == 'freelancer':
            points.append(f"• **Freelancer Tip:** Set aside 25% of all client payouts immediately into a separate buffer account for tax and lean months.")

        return "### 📋 Rule-Based Budget Strategy\n\n" + "\n\n".join(points)

    @classmethod
    def _fallback_spending_analysis(cls, user, metrics, category_breakdown, budget_details):
        c = user.currency
        if not category_breakdown:
            return "No expense records found for this period. Add expenses to generate real-time spending insights."

        top_cats = category_breakdown[:3]
        lines = [
            f"### 🔍 Rule-Based Spending Pattern Analysis\n",
            f"• **Highest Expenditure:** **{top_cats[0]['category']}** makes up **{top_cats[0]['percentage']}%** of all expenses ({c}{top_cats[0]['amount']:,.2f})."
        ]

        if len(top_cats) > 1:
            lines.append(f"• **Secondary Spending:** **{top_cats[1]['category']}** ({c}{top_cats[1]['amount']:,.2f}) and **{top_cats[2]['category'] if len(top_cats) > 2 else ''}** ({c}{top_cats[2]['amount']:,.2f} if len(top_cats) > 2 else '') constitute significant portions of outflow.")

        # Check for discretionary leaks
        discretionary = {'Entertainment', 'Shopping', 'Subscriptions', 'Travel'}
        disc_spent = sum(c_item['amount'] for c_item in category_breakdown if c_item['category'] in discretionary)
        if metrics['total_expenses'] > 0:
            disc_pct = round((disc_spent / metrics['total_expenses']) * 100, 1)
            lines.append(f"• **Discretionary Spending Ratio:** Discretionary lifestyle categories comprise **{disc_pct}%** ({c}{disc_spent:,.2f}) of your total outflow. A benchmark below 30% is ideal.")

        lines.append(f"• **Recommended Action:** Review recurrent subscriptions and meal delivery expenses over the last 14 days to recover instant cash.")
        return "\n\n".join(lines)

    @classmethod
    def _fallback_savings_advice(cls, user, metrics, goals):
        c = user.currency
        lines = ["### 💰 Rule-Based Savings Recommendations\n"]
        
        if metrics['net_savings'] <= 0:
            lines.append(f"• **Zero/Negative Cashflow Alert:** Currently, expenses ({c}{metrics['total_expenses']:,.2f}) match or exceed income ({c}{metrics['total_income']:,.2f}). Implement a 7-day 'needs-only' freeze to restore positive cash flow.")
        else:
            lines.append(f"• **Active Surplus:** You have generated **{c}{metrics['net_savings']:,.2f}** in surplus this month. Immediately allocate 50% of this towards your active savings goals.")

        if goals:
            active_goal = goals[0]
            lines.append(f"• **Priority Goal Progress:** '{active_goal.name}' is currently at **{active_goal.progress_percentage}%** ({c}{float(active_goal.current_amount):,.2f} / {c}{float(active_goal.target_amount):,.2f}). Target completion requires approx **{c}{active_goal.monthly_required:,.2f}/month**.")
        else:
            lines.append(f"• **Set an Emergency Fund Goal:** You do not have an active savings goal. We strongly advise creating a **3-Month Emergency Fund** goal on the Savings Goals page.")

        lines.append("• **Micro-Savings Rule:** Round up each transaction to the nearest 100 and stash the difference into savings.")
        return "\n\n".join(lines)

    @classmethod
    def _fallback_chat(cls, query, user, metrics, category_breakdown, budget_details, goals):
        q = query.lower()
        c = user.currency

        if "how much did i spend" in q or "spent" in q or "total expense" in q:
            return (
                f"📊 **Monthly Spending Summary:**\n\n"
                f"You have spent **{c}{metrics['total_expenses']:,.2f}** this month across {len(category_breakdown)} categories.\n\n"
                f"Your total monthly income is **{c}{metrics['total_income']:,.2f}**, leaving a net balance of **{c}{metrics['net_savings']:,.2f}**."
            )

        if "where" in q and ("money" in q or "going" in q or "category" in q):
            if not category_breakdown:
                return "You have not logged any expenses for this month yet!"
            top = category_breakdown[:3]
            top_str = "\n".join([f"• **{item['category']}**: {c}{item['amount']:,.2f} ({item['percentage']}%)" for item in top])
            return (
                f"💸 **Where Your Money Is Going:**\n\n"
                f"Your top expenditure categories this month are:\n{top_str}\n\n"
                f"Your single largest outflow is **{top[0]['category']}** at **{top[0]['percentage']}%** of all spending."
            )

        if "save" in q or "saving" in q:
            rem = metrics['net_savings']
            rate = metrics['savings_rate']
            return (
                f"💡 **Savings Status:**\n\n"
                f"• Current Net Savings this month: **{c}{rem:,.2f}**\n"
                f"• Current Savings Rate: **{rate}%**\n\n"
                f"To save more, inspect discretionary categories like Dining, Shopping, and Subscriptions. Putting aside just 10% on payday before spending is the easiest way to hit your target!"
            )

        if "food" in q:
            food_exp = next((x for x in category_breakdown if x['category'] == 'Food'), None)
            if food_exp:
                return f"🍔 **Food & Dining Spending:** You have spent **{c}{food_exp['amount']:,.2f}** on Food this month ({food_exp['percentage']}% of your total expenses)."
            return f"You haven't logged any food expenses yet for this month."

        if "budget" in q:
            return (
                f"📋 **Budget Overview:**\n\n"
                f"• Total Budget Limit: **{c}{metrics['total_budget']:,.2f}**\n"
                f"• Total Spent: **{c}{metrics['total_expenses']:,.2f}**\n"
                f"• Remaining: **{c}{metrics['remaining_budget']:,.2f}** ({metrics['budget_utilization']}% utilized)"
            )

        # General response with live metrics
        return (
            f"Hello {user.name}! Here is a quick snapshot of your finances for {metrics['month_name']}:\n\n"
            f"• **Income:** {c}{metrics['total_income']:,.2f}\n"
            f"• **Expenses:** {c}{metrics['total_expenses']:,.2f}\n"
            f"• **Net Balance:** {c}{metrics['net_savings']:,.2f} (Savings Rate: {metrics['savings_rate']}%)\n\n"
            f"You can ask me questions like:\n"
            f"- *How much did I spend this month?*\n"
            f"- *Where is most of my money going?*\n"
            f"- *How much did I spend on food?*\n"
            f"- *What is my budget status?*"
        )

    @classmethod
    def _fallback_financial_summary(cls, user, metrics, category_breakdown, budget_details, goals):
        c = user.currency
        inc = metrics['total_income']
        exp = metrics['total_expenses']
        sav = metrics['net_savings']
        rate = metrics['savings_rate']

        grade = "A" if rate >= 25 else ("B" if rate >= 15 else ("C" if rate > 0 else "D"))

        top_cat_str = f"**{category_breakdown[0]['category']}** ({c}{category_breakdown[0]['amount']:,.2f})" if category_breakdown else "N/A"

        return f"""### 📊 Monthly Financial Health Report Card ({metrics['month_name']})

**Overall Grade:** `{grade}` (Savings Rate: **{rate}%**)

#### 1. Executive Summary
- **Total Inflow (Income):** {c}{inc:,.2f}
- **Total Outflow (Expenses):** {c}{exp:,.2f}
- **Net Retained Savings:** {c}{sav:,.2f}
- **Budget Utilization:** {metrics['budget_utilization']}% of {c}{metrics['total_budget']:,.2f}

#### 2. Key Observations
- Top spending pressure point: {top_cat_str}.
- Active savings goals in progress: **{len(goals)}**.
- Financial Mode configured: **{user.financial_mode.title()} Mode**.

#### 3. Recommended Directives for Next Month
1. Maintain essential fixed living expenses below 50% of net monthly income.
2. Automate transfers to your top savings goal on the day income is credited.
3. Review and adjust any category limits that exceeded 100% utilization.
"""
