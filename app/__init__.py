from flask import Flask
from flask_cors import CORS
from .extensions import db, jwt, migrate, limiter
from .routes.auth import auth_bp
from .routes.analysis import analysis_bp
from .routes.policy import policy_bp

def create_app():
    from .config import Config

    app = Flask(__name__)
    app.config.from_object(Config)

    CORS(app,
     resources={r"/*": {"origins": "http://localhost:3000"}},
     supports_credentials=True,
     allow_headers=["Content-Type", "Authorization"],
     methods=["GET", "POST", "OPTIONS", "PUT", "DELETE"]
)

    db.init_app(app)
    jwt.init_app(app)
    migrate.init_app(app, db)
    limiter.init_app(app)

    app.register_blueprint(auth_bp, url_prefix="/api/auth")
    app.register_blueprint(analysis_bp, url_prefix="/api")
    app.register_blueprint(policy_bp, url_prefix="/api/gdpr")

    return app
