from flask import Blueprint, render_template, request, jsonify, redirect, url_for, flash
from flask_login import login_required, current_user
from datetime import date

from models import db, AIConversation, SavingsGoal
from services.analytics_service import AnalyticsService
from services.gemini_service import GeminiService

ai_bp = Blueprint('ai_advisor', __name__)

@ai_bp.route('/ai-advisor', methods=['GET'])
@login_required
def index():
    today = date.today()
    user_id = current_user.id

    metrics = AnalyticsService.get_monthly_metrics(user_id, today)
    category_breakdown = AnalyticsService.get_category_breakdown(user_id, today.month, today.year)
    budget_details = AnalyticsService.get_budget_utilization_details(user_id, today.month, today.year)
    goals = SavingsGoal.query.filter_by(user_id=user_id).all()

    # Pre-generate insights
    budget_advice = GeminiService.get_budget_advice(current_user, metrics, category_breakdown, budget_details)
    spending_analysis = GeminiService.analyze_spending(current_user, metrics, category_breakdown, budget_details)
    savings_advice = GeminiService.get_savings_advice(current_user, metrics, goals)
    health_summary = GeminiService.get_financial_health_summary(current_user, metrics, category_breakdown, budget_details, goals)

    # Chat history
    chat_history = AIConversation.query.filter_by(user_id=user_id).order_by(AIConversation.created_at.asc()).all()

    is_api_connected = GeminiService.is_api_configured()

    return render_template(
        'ai_advisor.html',
        metrics=metrics,
        budget_advice=budget_advice,
        spending_analysis=spending_analysis,
        savings_advice=savings_advice,
        health_summary=health_summary,
        chat_history=chat_history,
        is_api_connected=is_api_connected
    )


@ai_bp.route('/api/ai/chat', methods=['POST'])
@login_required
def chat_api():
    data = request.get_json() or {}
    user_message = data.get('message', '').strip()
    if not user_message:
        return jsonify({'error': 'Message cannot be empty.'}), 400

    today = date.today()
    user_id = current_user.id

    metrics = AnalyticsService.get_monthly_metrics(user_id, today)
    category_breakdown = AnalyticsService.get_category_breakdown(user_id, today.month, today.year)
    budget_details = AnalyticsService.get_budget_utilization_details(user_id, today.month, today.year)
    goals = SavingsGoal.query.filter_by(user_id=user_id).all()
    history = AIConversation.query.filter_by(user_id=user_id).order_by(AIConversation.created_at.asc()).limit(6).all()

    # Get response via Gemini or rule-based fallback
    ai_result = GeminiService.chat_response(
        user_message, current_user, metrics, category_breakdown, budget_details, goals, history
    )

    # Save to database
    conv = AIConversation(
        user_id=user_id,
        message=user_message,
        response=ai_result['text'],
        is_fallback=ai_result['is_fallback']
    )
    db.session.add(conv)
    db.session.commit()

    return jsonify({
        'id': conv.id,
        'message': conv.message,
        'response': conv.response,
        'is_fallback': conv.is_fallback,
        'created_at': conv.created_at.strftime('%H:%M')
    })


@ai_bp.route('/api/ai/clear-history', methods=['POST'])
@login_required
def clear_history():
    AIConversation.query.filter_by(user_id=current_user.id).delete()
    db.session.commit()
    flash("AI conversation history cleared.", "info")
    return redirect(url_for('ai_advisor.index'))
