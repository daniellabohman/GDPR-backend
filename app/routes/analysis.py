from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from app.models import User, Analysis
from app.extensions import db
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from bs4 import BeautifulSoup
from urllib.parse import urlparse
from datetime import datetime
import time

analysis_bp = Blueprint("analysis", __name__)

def analyze_website(url):
    if not url.startswith("http"):
        url = "https://" + url

    options = Options()
    options.headless = True
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--disable-blink-features=AutomationControlled")

    service = Service(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service, options=options)

    try:
        driver.get(url)
        time.sleep(5)

        html = driver.page_source.lower()
        soup = BeautifulSoup(html, "html.parser")

        scripts = soup.find_all("script")
        script_sources = [s.get("src") for s in scripts if s.get("src")]
        hostname = urlparse(url).hostname or ""
        third_party = [src for src in script_sources if hostname not in src]

        cookie_keywords = ["cookie", "accept", "afvis", "privacy", "samtykke"]
        has_cookie_banner = any(kw in html for kw in cookie_keywords)

        cookie_texts = soup.find_all(string=True)
        cookie_text_combined = " ".join([t.strip().lower() for t in cookie_texts if t.strip()])
        banner_keywords = ["nødvendige", "statistik", "marketing", "valg", "indstillinger"]
        banner_advanced_ok = any(word in cookie_text_combined for word in banner_keywords)

        known_frameworks = {
            "Cookiebot": "cookiebot.com",
            "Klaro": "klaro.js",
            "Osano": "osano.com"
        }
        found_frameworks = []
        for src in script_sources:
            for name, signature in known_frameworks.items():
                if signature in src:
                    found_frameworks.append(name)

        links = [a.text.lower() for a in soup.find_all("a")]
        has_privacy = any("privat" in text or "policy" in text for text in links)

        cookies = driver.get_cookies()
        early_cookies = [c["name"] for c in cookies if "consent" not in c["name"].lower()]

        forms = soup.find_all("form")
        consent_near_form = any(
            any(word in form.get_text().lower() for word in ["samtykke", "gdpr", "privatliv"])
            for form in forms
        )

        overlay_found = False
        try:
            banners = driver.find_elements("xpath", "//*[contains(@style,'position:fixed') or contains(@class,'cookie')]")
            for banner in banners:
                size = banner.size
                if size["height"] > 40 and size["width"] > 100:
                    overlay_found = True
                    break
        except:
            pass

        missing = []
        suggestions = []

        if not has_cookie_banner:
            missing.append("Cookie-banner")
            suggestions.append("Tilføj synligt cookie-banner med valgmuligheder")
        elif not banner_advanced_ok:
            suggestions.append("Cookie-banner mangler kategorier (nødvendige/statistik/marketing) og valg-muligheder")

        if not overlay_found:
            suggestions.append("Cookie-banner skal være visuelt synligt som overlay")

        if not has_privacy:
            missing.append("Privatlivspolitik")
            suggestions.append("Tilføj link til privatlivspolitik (fx i footer)")

        if early_cookies:
            suggestions.append(f"Siden sætter cookies tidligt: {', '.join(early_cookies[:5])}… (kræver samtykke først)")

        if not consent_near_form and forms:
            suggestions.append("Formularer mangler samtykketekst i nærheden")

        if not third_party:
            suggestions.append("Ingen 3rd-party scripts fundet – overvej fx Analytics hvis relevant")

        if found_frameworks:
            suggestions.append(f"Samtykkestyring fundet via: {', '.join(found_frameworks)}")
        else:
            suggestions.append("Ingen kendt samtykkeplatform fundet – overvej Cookiebot eller Klaro for korrekt håndtering")

        score = max(0, 100 - len(missing) * 20 - len([s for s in suggestions if "samtykke" in s.lower()]) * 5)

        return {
            "score": score,
            "missing": missing,
            "suggestions": suggestions,
            "scripts": third_party,
            "cookies": early_cookies
        }

    except Exception as e:
        return {"error": str(e)}
    finally:
        driver.quit()


@analysis_bp.route("/gdpr/analyze", methods=["POST"])
@jwt_required(optional=True)
def analyze_and_save():
    user_email = get_jwt_identity()
    user = User.query.filter_by(email=user_email).first() if user_email else None

    data = request.json
    url = data.get("url")
    if not url:
        return jsonify({"msg": "URL is required"}), 400

    result = analyze_website(url)
    if "error" in result:
        return jsonify({"msg": result["error"]}), 500

    analysis = Analysis(
        user_id=user.id if user else None,
        url=url,
        score=result["score"],
        missing=result["missing"],
        suggestions=result["suggestions"],
        created_at=datetime.utcnow()
    )

    db.session.add(analysis)
    db.session.commit()

    return jsonify({
        "id": analysis.id,
        "url": url,
        **result,
        "created_at": analysis.created_at.isoformat()
    }), 200

from flask_cors import cross_origin

@analysis_bp.route("/gdpr/analyze-demo", methods=["POST", "OPTIONS"])
def analyze_demo():

    try:
        data = request.get_json()
        url = data.get("url", "").strip()
        if not url:
            return jsonify({"error": "URL mangler"}), 400

        result = analyze_website(url)

        return jsonify({
            "score": result["score"],
            "missing": result["missing"],
            "suggestions": result["suggestions"]
        })
    except Exception as e:
        return jsonify({"error": "Noget gik galt", "details": str(e)}), 500


@analysis_bp.route("/me/average-score", methods=["GET"])
@jwt_required()
def average_score():
    user_email = get_jwt_identity()
    user = User.query.filter_by(email=user_email).first()
    if not user:
        return jsonify({"msg": "User not found"}), 404

    analyses = user.analyses
    if not analyses:
        return jsonify({"average_score": None})

    scores = [a.score for a in analyses if a.score is not None]
    if not scores:
        return jsonify({"average_score": None})

    avg = round(sum(scores) / len(scores), 1)
    return jsonify({"average_score": avg})


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
