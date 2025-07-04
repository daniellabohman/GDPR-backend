from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from app.models import User, Analysis
from app.extensions import db

analysis_bp = Blueprint("analysis", __name__)

@analysis_bp.route("/gdpr/history", methods=["GET"])
@jwt_required()
def get_history():
    user_email = get_jwt_identity()
    user = User.query.filter_by(email=user_email).first()
    if not user:
        return jsonify({"msg": "User not found"}), 404

    history = Analysis.query.filter_by(user_id=user.id).order_by(Analysis.created_at.desc()).all()
    return jsonify([
        {
            "id": a.id,
            "url": a.url,
            "score": a.score,
            "missing": a.missing,
            "suggestions": a.suggestions,
            "created_at": a.created_at.isoformat()
        }
        for a in history
    ])
@analysis_bp.route("/gdpr/submit", methods=["POST"])
@jwt_required()
def submit_analysis():
    user_email = get_jwt_identity()
    user = User.query.filter_by(email=user_email).first()
    if not user:
        return jsonify({"msg": "User not found"}), 404

    data = request.json
    url = data.get("url")
    score = data.get("score")
    missing = data.get("missing", {})
    suggestions = data.get("suggestions", {})

    if not url or not score:
        return jsonify({"msg": "URL and score are required"}), 400

    analysis = Analysis(
        user_id=user.id,
        url=url,
        score=score,
        missing=missing,
        suggestions=suggestions
    )
    
    db.session.add(analysis)
    db.session.commit()

    return jsonify({"msg": "Analysis submitted successfully", "id": analysis.id}), 201