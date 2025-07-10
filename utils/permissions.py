
from flask_jwt_extended import get_jwt_identity
from app.models import User
from flask import abort

def require_admin_user():
    email = get_jwt_identity()
    user = User.query.filter_by(email=email).first()
    if not user or user.role != "admin":
        abort(403, "Adgang nægtet – kun for admin")
    return user
