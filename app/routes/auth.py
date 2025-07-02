from flask import Blueprint, request, jsonify, make_response
from flask_jwt_extended import (
    create_access_token, create_refresh_token,
    jwt_required, get_jwt_identity, get_jwt
)
from app.models import User
from app.extensions import limiter, db
import re

auth_bp = Blueprint("auth", __name__)
EMAIL_REGEX = r"[^@]+@[^@]+\.[^@]+"

def is_valid_email(email):
    return re.match(EMAIL_REGEX, email)

# ✅ REGISTRERING
@auth_bp.route("/register", methods=["POST"])
def register():
    data = request.get_json()
    company_name = data.get("company_name", "").strip()
    email = data.get("email", "").strip().lower()
    password = data.get("password", "")
    website_url = data.get("website_url", "").strip()

    if not all([company_name, email, password]):
        return jsonify({"msg": "Missing required fields"}), 400
    if not is_valid_email(email):
        return jsonify({"msg": "Invalid email format"}), 400
    if len(password) < 8:
        return jsonify({"msg": "Password must be at least 8 characters"}), 400
    if User.query.filter_by(email=email).first():
        return jsonify({"msg": "User already exists"}), 409

    user = User(
        company_name=company_name,
        email=email,
        website_url=website_url
    )
    user.set_password(password)
    db.session.add(user)
    db.session.commit()

    return jsonify({"msg": "User registered successfully"}), 201

# ✅ LOGIN – access token + refresh token (httpOnly-cookie)
@auth_bp.route("/login", methods=["POST"])
@limiter.limit("5 per minute")
def login():
    data = request.get_json()
    email = data.get("email", "").strip().lower()
    password = data.get("password", "")

    user = User.query.filter_by(email=email).first()
    if not user or not user.check_password(password):
        return jsonify({"msg": "Invalid credentials"}), 401

    access_token = create_access_token(
        identity=user.email,
        additional_claims={"role": user.role, "company": user.company_name}
    )
    refresh_token = create_refresh_token(identity=user.email)

    response = make_response(jsonify(access_token=access_token))
    response.set_cookie(
        "refresh_token", refresh_token,
        httponly=True,
        secure=False,  # True i produktion med HTTPS!
        samesite="Strict",
        max_age=7 * 24 * 60 * 60
    )
    return response

# ✅ REFRESH (henter ny access token)
@auth_bp.route("/refresh", methods=["POST"])
@jwt_required(refresh=True)
def refresh():
    identity = get_jwt_identity()
    claims = get_jwt()

    new_access_token = create_access_token(
        identity=identity,
        additional_claims={
            "role": claims.get("role"),
            "company": claims.get("company")
        }
    )
    return jsonify(access_token=new_access_token), 200

# ✅ LOGOUT – sletter refresh cookie
@auth_bp.route("/logout", methods=["POST"])
def logout():
    response = jsonify({"msg": "Logged out"})
    response.set_cookie("refresh_token", "", max_age=0)
    return response

# ✅ BESKYTTET /me ENDPOINT
@auth_bp.route("/me", methods=["GET"])
@jwt_required()
def get_me():
    identity = get_jwt_identity()
    claims = get_jwt()
    return jsonify({
        "email": identity,
        "role": claims.get("role"),
        "company": claims.get("company")
    })

# ✅ KUN ADMIN
@auth_bp.route("/admin/only", methods=["GET"])
@jwt_required()
def admin_route():
    identity = get_jwt_identity()
    claims = get_jwt()
    if claims.get("role") != "admin":
        return jsonify({"msg": "Admins only"}), 403
    return jsonify({
        "msg": f"Welcome, admin from {claims.get('company')}",
        "email": identity
    }), 200
