from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required
from utils.text_analysis import analyze_policy_text  

enhancer_bp = Blueprint("enhancer")

@enhancer_bp.post("/analyze-text")
@jwt_required()
def analyze_policy():
    try:
        data = request.get_json()
        policy_text = data.get("text", "").strip()

        if not policy_text:
            return jsonify({"error": "Ingen tekst modtaget"}), 400

        analysis_result = analyze_policy_text(policy_text)

        return jsonify({"recommendations": analysis_result}), 200
    except Exception as e:
        return jsonify({"error": "Noget gik galt", "details": str(e)}), 500
