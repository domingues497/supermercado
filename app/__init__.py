import os
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_wtf import CSRFProtect
from flask_login import LoginManager
from dotenv import load_dotenv

# Load environment variables from .env
load_dotenv()

db = SQLAlchemy()
migrate = Migrate()
csrf = CSRFProtect()
login_manager = LoginManager()
login_manager.login_view = 'admin.login'

from app.models import AdminUser
@login_manager.user_loader
def load_user(user_id):
    return AdminUser.query.get(int(user_id))



def create_app():
    app = Flask(__name__)
    app.config.from_object('app.config.Config')

    # Inicializa extensões
    db.init_app(app)
    migrate.init_app(app, db)
    csrf.init_app(app)
    login_manager.init_app(app)

    # Importa e registra Blueprints
    from app.routes_admin import bp as admin_bp
    from app.routes_cliente import bp as cliente_bp
    from app.routes_api import bp as api_bp
    from app.routes_publico import bp as publico_bp
    
        
    app.register_blueprint(publico_bp)
    app.register_blueprint(admin_bp, url_prefix='/admin')
    app.register_blueprint(cliente_bp, url_prefix='/cliente')
    app.register_blueprint(api_bp, url_prefix='/api')
   
    from flask_wtf.csrf import generate_csrf

    @app.context_processor
    def inject_csrf_token():
        return dict(csrf_token=generate_csrf)

    return app
