import os
from flask import Flask, render_template, redirect, url_for
from flask_login import LoginManager, current_user
from flask_wtf.csrf import CSRFProtect
from datetime import date, datetime

from config import Config
from models import db, User, Notification
from routes import register_blueprints

def create_app(config_class=Config):
    app = Flask(__name__)
    app.config.from_object(config_class)

    # Ensure instance directory exists
    instance_dir = os.path.join(app.root_path, 'instance')
    os.makedirs(instance_dir, exist_ok=True)

    # Initialize Database
    db.init_app(app)

    # Initialize CSRF Protection
    csrf = CSRFProtect(app)

    # Initialize Login Manager
    login_manager = LoginManager()
    login_manager.login_view = 'auth.login'
    login_manager.login_message = 'Please log in to access this page.'
    login_manager.login_message_category = 'warning'
    login_manager.init_app(app)

    @login_manager.user_loader
    def load_user(user_id):
        return db.session.get(User, int(user_id))

    # Context processors for all Jinja templates
    @app.context_processor
    def inject_global_vars():
        unread_notifications_count = 0
        recent_notifications = []
        if current_user.is_authenticated:
            unread_notifications_count = Notification.query.filter_by(
                user_id=current_user.id, is_read=False
            ).count()
            recent_notifications = Notification.query.filter_by(
                user_id=current_user.id
            ).order_by(Notification.created_at.desc()).limit(5).all()

        return {
            'now': datetime.utcnow(),
            'today': date.today(),
            'unread_notifications_count': unread_notifications_count,
            'recent_notifications': recent_notifications,
            'default_currency': app.config.get('DEFAULT_CURRENCY', '₹')
        }

    # Custom Jinja filters
    @app.template_filter('currency')
    def currency_filter(value):
        try:
            val = float(value or 0)
            curr = current_user.currency if current_user.is_authenticated else "₹"
            return f"{curr}{val:,.2f}"
        except (ValueError, TypeError):
            return f"₹{value}"

    @app.template_filter('badge_color')
    def badge_color_filter(category):
        palette = {
            'Salary': 'success',
            'Freelancing': 'info',
            'Business': 'primary',
            'Allowance': 'warning',
            'Investments': 'success',
            'Food': 'warning',
            'Rent': 'danger',
            'Transportation': 'primary',
            'Education': 'info',
            'Healthcare': 'danger',
            'Entertainment': 'secondary',
            'Shopping': 'warning',
            'Utilities': 'dark',
            'Groceries': 'success',
            'Subscriptions': 'info',
            'Travel': 'primary',
            'Other': 'secondary'
        }
        return palette.get(category, 'secondary')

    # Register all Blueprints
    register_blueprints(app)

    # Root route: Landing page or dashboard redirect
    @app.route('/')
    def index():
        if current_user.is_authenticated:
            return redirect(url_for('dashboard.index'))
        return render_template('index.html')

    # Error Handlers
    @app.errorhandler(404)
    def page_not_found(e):
        return render_template('404.html'), 404

    @app.errorhandler(500)
    def internal_server_error(e):
        return render_template('500.html'), 500

    # Auto-create tables
    with app.app_context():
        db.create_all()

    return app


app = create_app()

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='127.0.0.1', port=port, debug=True)
