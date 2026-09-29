from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_required, current_user
from datetime import date
from decimal import Decimal

from models import db, SavingsGoal, SavingsContribution
from forms import SavingsGoalForm, SavingsContributionForm

savings_bp = Blueprint('savings', __name__)

@savings_bp.route('/savings', methods=['GET'])
@login_required
def index():
    goals = SavingsGoal.query.filter_by(user_id=current_user.id).order_by(SavingsGoal.target_date.asc()).all()

    total_target = sum(float(g.target_amount) for g in goals)
    total_saved = sum(float(g.current_amount) for g in goals)
    total_progress = round((total_saved / total_target * 100), 1) if total_target > 0 else 0.0

    goal_form = SavingsGoalForm()
    contrib_form = SavingsContributionForm()

    return render_template(
        'savings.html',
        goals=goals,
        total_target=round(total_target, 2),
        total_saved=round(total_saved, 2),
        total_progress=total_progress,
        goal_form=goal_form,
        contrib_form=contrib_form
    )


@savings_bp.route('/savings/add', methods=['POST'])
@login_required
def add():
    form = SavingsGoalForm()
    if form.validate_on_submit():
        goal = SavingsGoal(
            user_id=current_user.id,
            name=form.name.data.strip(),
            target_amount=form.target_amount.data,
            current_amount=form.current_amount.data or 0.0,
            target_date=form.target_date.data,
            description=form.description.data.strip() if form.description.data else ''
        )
        db.session.add(goal)
        db.session.commit()
        flash(f"Savings goal '{goal.name}' created successfully!", "success")
    else:
        for field, errors in form.errors.items():
            for error in errors:
                flash(f"{field.capitalize()}: {error}", 'danger')

    return redirect(url_for('savings.index'))


@savings_bp.route('/savings/edit/<int:id>', methods=['GET', 'POST'])
@login_required
def edit(id):
    goal = SavingsGoal.query.filter_by(id=id, user_id=current_user.id).first_or_404()
    form = SavingsGoalForm(obj=goal)

    if form.validate_on_submit():
        goal.name = form.name.data.strip()
        goal.target_amount = form.target_amount.data
        goal.current_amount = form.current_amount.data or 0.0
        goal.target_date = form.target_date.data
        goal.description = form.description.data.strip() if form.description.data else ''
        db.session.commit()
        flash(f"Goal '{goal.name}' updated.", "success")
        return redirect(url_for('savings.index'))

    return render_template('savings_edit.html', form=form, goal=goal)


@savings_bp.route('/savings/delete/<int:id>', methods=['POST'])
@login_required
def delete(id):
    goal = SavingsGoal.query.filter_by(id=id, user_id=current_user.id).first_or_404()
    db.session.delete(goal)
    db.session.commit()
    flash(f"Goal '{goal.name}' deleted.", "info")
    return redirect(url_for('savings.index'))


@savings_bp.route('/savings/<int:id>/contribute', methods=['POST'])
@login_required
def contribute(id):
    goal = SavingsGoal.query.filter_by(id=id, user_id=current_user.id).first_or_404()
    form = SavingsContributionForm()

    if form.validate_on_submit():
        amount = form.amount.data
        contrib = SavingsContribution(
            goal_id=goal.id,
            amount=amount,
            date=form.date.data,
            description=form.description.data.strip() if form.description.data else 'Savings Deposit'
        )
        goal.current_amount = float(goal.current_amount) + float(amount)
        db.session.add(contrib)
        db.session.commit()

        flash(f"Deposited {current_user.currency}{amount:,.2f} into '{goal.name}'!", "success")
    else:
        for field, errors in form.errors.items():
            for error in errors:
                flash(f"{field.capitalize()}: {error}", 'danger')

    return redirect(url_for('savings.index'))
