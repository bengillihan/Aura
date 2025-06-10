import os
import logging
from flask import Flask, render_template, redirect, url_for, flash, request, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, login_required, current_user
from flask_socketio import SocketIO, emit
from sqlalchemy.orm import DeclarativeBase
from werkzeug.middleware.proxy_fix import ProxyFix

# Configure logging
logging.basicConfig(level=logging.DEBUG)

class Base(DeclarativeBase):
    pass

db = SQLAlchemy(model_class=Base)

# Create the app
app = Flask(__name__)
app.secret_key = os.environ.get("SESSION_SECRET", "dev-secret-key-change-in-production")
app.wsgi_app = ProxyFix(app.wsgi_app, x_proto=1, x_host=1)

# Configure the database
app.config["SQLALCHEMY_DATABASE_URI"] = os.environ.get("DATABASE_URL", "sqlite:///aura.db")
app.config["SQLALCHEMY_ENGINE_OPTIONS"] = {
    "pool_recycle": 300,
    "pool_pre_ping": True,
}

# Initialize extensions
db.init_app(app)
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'
socketio = SocketIO(app, cors_allowed_origins="*")

# Import configuration
from config import MANAGED_SERVICES, ALLOWED_EMAIL

with app.app_context():
    # Import models
    import models
    db.create_all()

# Import blueprints and managers
from google_auth import google_auth
from service_manager import ServiceManager
from resource_monitor import ResourceMonitor
from deployment_manager import DeploymentManager
from terminal_handler import TerminalHandler

# Register blueprints
app.register_blueprint(google_auth)

# Initialize managers
service_manager = ServiceManager()
resource_monitor = ResourceMonitor()
deployment_manager = DeploymentManager()
terminal_handler = TerminalHandler(socketio)

@login_manager.user_loader
def load_user(user_id):
    from models import User
    return User.query.get(int(user_id))

def check_authorization():
    """Check if current user is authorized"""
    if not current_user.is_authenticated:
        return False
    return current_user.email == ALLOWED_EMAIL

@app.route('/')
def index():
    if not current_user.is_authenticated:
        return render_template('login.html')
    
    if not check_authorization():
        flash('Access denied. You are not authorized to use this application.', 'danger')
        return redirect(url_for('google_auth.logout'))
    
    return render_template('index.html', services=MANAGED_SERVICES)

@app.route('/login')
def login():
    return render_template('login.html')

@app.route('/services')
@login_required
def services():
    if not check_authorization():
        flash('Access denied.', 'danger')
        return redirect(url_for('index'))
    
    # Get status for all services
    service_status = {}
    for service_name in MANAGED_SERVICES.keys():
        service_status[service_name] = service_manager.get_service_status(service_name)
    
    return render_template('services.html', services=MANAGED_SERVICES, status=service_status)

@app.route('/service/<action>/<service_name>')
@login_required
def service_action(action, service_name):
    if not check_authorization():
        return jsonify({'error': 'Access denied'}), 403
    
    if service_name not in MANAGED_SERVICES:
        return jsonify({'error': 'Service not found'}), 404
    
    if action == 'start':
        result = service_manager.start_service(service_name)
    elif action == 'stop':
        result = service_manager.stop_service(service_name)
    elif action == 'restart':
        result = service_manager.restart_service(service_name)
    elif action == 'status':
        result = service_manager.get_service_status(service_name)
    else:
        return jsonify({'error': 'Invalid action'}), 400
    
    return jsonify(result)

@app.route('/deploy')
@login_required
def deploy():
    if not check_authorization():
        flash('Access denied.', 'danger')
        return redirect(url_for('index'))
    
    return render_template('deploy.html', services=MANAGED_SERVICES)

@app.route('/deploy/<service_name>')
@login_required
def deploy_service(service_name):
    if not check_authorization():
        return jsonify({'error': 'Access denied'}), 403
    
    if service_name not in MANAGED_SERVICES:
        return jsonify({'error': 'Service not found'}), 404
    
    # Start deployment in background and return immediate response
    result = deployment_manager.deploy_service(service_name)
    return jsonify(result)

@app.route('/monitoring')
@login_required
def monitoring():
    if not check_authorization():
        flash('Access denied.', 'danger')
        return redirect(url_for('index'))
    
    return render_template('monitoring.html', services=MANAGED_SERVICES)

@app.route('/api/resource_usage')
@login_required
def api_resource_usage():
    if not check_authorization():
        return jsonify({'error': 'Access denied'}), 403
    
    usage_data = resource_monitor.get_system_usage()
    service_usage = {}
    
    for service_name in MANAGED_SERVICES.keys():
        service_usage[service_name] = resource_monitor.get_service_usage(service_name)
    
    return jsonify({
        'system': usage_data,
        'services': service_usage
    })

@app.route('/terminal')
@login_required
def terminal():
    if not check_authorization():
        flash('Access denied.', 'danger')
        return redirect(url_for('index'))
    
    return render_template('terminal.html')

@app.route('/service_config/<service_name>')
@login_required
def service_config(service_name):
    if not check_authorization():
        return jsonify({'error': 'Access denied'}), 403
    
    if service_name not in MANAGED_SERVICES:
        return jsonify({'error': 'Service not found'}), 404
    
    config = service_manager.get_service_config(service_name)
    return jsonify(config)

@app.route('/service_config/<service_name>', methods=['POST'])
@login_required
def update_service_config(service_name):
    if not check_authorization():
        return jsonify({'error': 'Access denied'}), 403
    
    if service_name not in MANAGED_SERVICES:
        return jsonify({'error': 'Service not found'}), 404
    
    cpu_quota = request.json.get('cpu_quota')
    memory_max = request.json.get('memory_max')
    
    result = service_manager.update_service_limits(service_name, cpu_quota, memory_max)
    return jsonify(result)

# Socket.IO events for terminal
@socketio.on('connect')
def handle_connect():
    if not current_user.is_authenticated or not check_authorization():
        return False
    terminal_handler.handle_connect(current_user.id)

@socketio.on('disconnect')
def handle_disconnect():
    if current_user.is_authenticated:
        terminal_handler.handle_disconnect(current_user.id)

@socketio.on('terminal_input')
def handle_terminal_input(data):
    if not current_user.is_authenticated or not check_authorization():
        return
    terminal_handler.handle_input(current_user.id, data)

@socketio.on('terminal_resize')
def handle_terminal_resize(data):
    if not current_user.is_authenticated or not check_authorization():
        return
    terminal_handler.handle_resize(current_user.id, data)

if __name__ == '__main__':
    socketio.run(app, host='0.0.0.0', port=5000, debug=True)
