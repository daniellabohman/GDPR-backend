from flask import Blueprint, Response
from app.models import BlogPost

sitemap_bp = Blueprint("sitemap", __name__)

@sitemap_bp.route("/sitemap.xml", methods=["GET"])
def sitemap():
    posts = BlogPost.query.filter_by(published=True).all()
    base_url = "https://nexpertia.dk"

    urls = [
        f"<url><loc>{base_url}/</loc></url>",
        f"<url><loc>{base_url}/blog</loc></url>"
    ] + [
        f"<url><loc>{base_url}/blog/{post.slug}</loc></url>"
        for post in posts
    ]

    xml = f"""<?xml version="1.0" encoding="UTF-8"?>
<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">
  {''.join(urls)}
</urlset>
"""
    return Response(xml, mimetype="application/xml")
