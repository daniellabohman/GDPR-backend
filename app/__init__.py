from flask import Flask
from flask_cors import CORS
from .extensions import db, jwt, migrate, limiter
from .routes.auth import auth_bp

def create_app():
    from .config import Config

    app = Flask(__name__)
    app.config.from_object(Config)

    CORS(app, supports_credentials=True,
         origins=["http://localhost:3000"])
    db.init_app(app)
    jwt.init_app(app)
    migrate.init_app(app, db)
    limiter.init_app(app)

    app.register_blueprint(auth_bp, url_prefix="/api/auth")
    return app
