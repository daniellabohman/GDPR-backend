# Blueprint: /api/gdpr
from flask import Blueprint, request, jsonify, send_file
from flask_jwt_extended import jwt_required, get_jwt_identity
from app.models import User, PrivacyPolicy, PolicyLog
from app.extensions import db
from datetime import datetime
from weasyprint import HTML
from flask_cors import cross_origin
import io

policy_bp = Blueprint("policy", __name__)


# --- Preflight routes (CORS) ---
@policy_bp.route("/policy/generate", methods=["OPTIONS"])
@policy_bp.route("/policy/<int:policy_id>", methods=["OPTIONS"])
@policy_bp.route("/policy/<int:policy_id>/pdf", methods=["OPTIONS"])
@policy_bp.route("/policy/history", methods=["OPTIONS"])
@cross_origin(origins="http://localhost:3000", supports_credentials=True)
def preflight_ok(**kwargs):
    return '', 200


# --- Generer politik ---
@policy_bp.route("/policy/generate", methods=["POST"])
@cross_origin(origins="http://localhost:3000", supports_credentials=True)
@jwt_required()
def generate_policy():
    user_email = get_jwt_identity()
    user = User.query.filter_by(email=user_email).first()
    if not user:
        return jsonify({"msg": "User not found"}), 404

    data = request.get_json()
    if not data:
        return jsonify({"msg": "No data provided"}), 400

    prompt = build_privacy_policy_prompt(data)
    html = call_ai_model(prompt)

    policy = PrivacyPolicy(
        user_id=user.id,
        data=data,
        html_output=html,
        created_at=datetime.utcnow()
    )

    db.session.add(policy)
    db.session.commit()

    log = PolicyLog(
        user_id=user.id,
        input_data=data,
        output_html=html
    )

    db.session.add(log)
    db.session.commit()

    return jsonify({ "html": html, "id": policy.id }), 200


# --- Hent politik som HTML ---
@policy_bp.route("/policy/<int:policy_id>", methods=["GET"])
@cross_origin(origins="http://localhost:3000", supports_credentials=True)
@jwt_required()
def get_policy(policy_id):
    user_email = get_jwt_identity()
    user = User.query.filter_by(email=user_email).first()
    policy = PrivacyPolicy.query.filter_by(id=policy_id, user_id=user.id).first()
    if not policy:
        return jsonify({"msg": "Policy not found"}), 404
    return jsonify({ "html_output": policy.html_output })


# --- Hent som PDF ---
@policy_bp.route("/policy/<int:policy_id>/pdf", methods=["GET"])
@cross_origin(origins="http://localhost:3000", supports_credentials=True)
@jwt_required()
def download_policy_pdf(policy_id):
    user_email = get_jwt_identity()
    user = User.query.filter_by(email=user_email).first()
    policy = PrivacyPolicy.query.filter_by(id=policy_id, user_id=user.id).first()
    if not policy:
        return jsonify({"msg": "Policy not found"}), 404

    pdf_io = io.BytesIO()
    HTML(string=policy.html_output).write_pdf(pdf_io)
    pdf_io.seek(0)

    return send_file(pdf_io, mimetype="application/pdf", download_name=f"privatlivspolitik_{policy_id}.pdf", as_attachment=True)


# --- Historik ---
@policy_bp.route("/policy/history", methods=["GET"])
@cross_origin(origins="http://localhost:3000", supports_credentials=True)
@jwt_required()
def policy_history():
    user_email = get_jwt_identity()
    user = User.query.filter_by(email=user_email).first()
    policies = PrivacyPolicy.query.filter_by(user_id=user.id).order_by(PrivacyPolicy.created_at.desc()).all()

    return jsonify([
        {
            "id": p.id,
            "created_at": p.created_at.isoformat(),
            "virksomhed_navn": p.data.get("virksomhed_navn", "Ukendt"),
        } for p in policies
    ])


# --- Prompt builder og dummy AI ---
def build_privacy_policy_prompt(data):
    return f"""
Du er juridisk ekspert i GDPR og dansk persondatalovgivning.

Generér en privatlivspolitik i HTML baseret på:

Virksomhedsnavn: {data['virksomhed_navn']}
E-mail: {data['email']}
Lokation: {data.get('lokation', '')}
Branche: {data.get('branche', '')}
Målgruppe: {data.get('brugertyper', '')}
Kontaktformular: {data.get('kontaktformular')}
Nyhedsbrev: {data.get('nyhedsbrev')}
Webshop: {data.get('webshop')}
Cookies: {data.get('cookies')}
""".strip()


def call_ai_model(prompt):
    return """
<h1>Privatlivspolitik</h1>
<h2>1. Hvem er vi?</h2>
<p>Vi er Eksempelfirmaet – kontakt os på demo@example.com.</p>
<h2>2. Hvilke oplysninger indsamles?</h2>
<p>Navn, e-mail, IP-adresse og browserdata.</p>
<h2>3. Brug af data</h2>
<p>Vi bruger dine data til support og forbedring af siden.</p>
<h2>4. Cookies</h2>
<p>Vi anvender cookies til statistik og funktionalitet.</p>
<h2>5. Dine rettigheder</h2>
<p>Du har ret til indsigt og sletning. Kontakt os ved spørgsmål.</p>
"""
