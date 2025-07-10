from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required
from app.models import BlogPost, db
from utils.permissions import require_admin_user


blog_bp = Blueprint("blog", __name__)


@blog_bp.post("/")
@jwt_required()
def create_blog():
    user = require_admin_user()
    data = request.get_json()
    post = BlogPost(
        title=data["title"],
        slug=data["slug"],
        content=data["content"],
        author_id=user.id,
        published=data.get("published", True)
    )
    db.session.add(post)
    db.session.commit()
    return jsonify({"message": "Blogindlæg oprettet", "id": post.id}), 201

@blog_bp.get("/")
def list_blogs():
    posts = BlogPost.query.filter_by(published=True).order_by(BlogPost.created_at.desc()).all()
    return jsonify([
        {
            "id": p.id,
            "title": p.title,
            "slug": p.slug,
            "created_at": p.created_at.isoformat()
        }
        for p in posts
    ])

@blog_bp.get("/<slug>")
def get_blog(slug):
    post = BlogPost.query.filter_by(slug=slug, published=True).first_or_404()
    return jsonify({
        "id": post.id,
        "title": post.title,
        "content": post.content,
        "created_at": post.created_at.isoformat(),
        "author": post.author.email
    })

@blog_bp.put("/<int:id>")
@jwt_required()
def update_blog(id):
    user = require_admin_user()
    data = request.get_json()

    post = BlogPost.query.get_or_404(id)
    post.title = data.get("title", post.title)
    post.slug = data.get("slug", post.slug)
    post.content = data.get("content", post.content)
    post.published = data.get("published", post.published)

    db.session.commit()
    return jsonify({"message": "Blogindlæg opdateret"}), 200

@blog_bp.delete("/<int:id>")
@jwt_required()
def delete_blog(id):
    user = require_admin_user()
    post = BlogPost.query.get_or_404(id)

    db.session.delete(post)
    db.session.commit()
    return jsonify({"message": "Blogindlæg slettet"}), 200
