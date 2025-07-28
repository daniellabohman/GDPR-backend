import os
from flask import Flask, send_from_directory
from flask_cors import CORS
from .extensions import db, jwt, migrate, limiter
from .routes.auth import auth_bp
from .routes.analysis import analysis_bp
from .routes.policy import policy_bp
from .routes.sitemap import sitemap_bp
from .routes.blog import blog_bp
from .routes.enhancer import enhancer_bp

def create_app():
    from .config import Config

    app = Flask(__name__)
    app.config.from_object(Config)

    CORS(
        app,
        supports_credentials=True,
        origins=["http://localhost:3000"],
        methods=["GET", "POST", "OPTIONS", "PUT", "DELETE"],
        allow_headers=["Content-Type", "Authorization"],
        expose_headers=["Content-Type", "Authorization"]
    )

    db.init_app(app)
    jwt.init_app(app)
    migrate.init_app(app, db)
    limiter.init_app(app)

    app.register_blueprint(auth_bp, url_prefix="/api/auth")
    app.register_blueprint(analysis_bp, url_prefix="/api")
    app.register_blueprint(policy_bp, url_prefix="/api/gdpr")
    app.register_blueprint(sitemap_bp)
    app.register_blueprint(blog_bp, url_prefix="/api/blog")
    app.register_blueprint(enhancer_bp, url_prefix="/api/enhancer")

    @app.route("/", defaults={"path": ""})
    @app.route("/<path:path>")
    def serve_react(path):
        if path.startswith("api/"):
            return "Not Found", 404

        static_dir = os.path.join(os.path.dirname(__file__), "frontend", "build")
        requested_path = os.path.join(static_dir, path)

        if os.path.exists(requested_path) and not os.path.isdir(requested_path):
            return send_from_directory(static_dir, path)
        else:
            return send_from_directory(static_dir, "index.html")

    return app
