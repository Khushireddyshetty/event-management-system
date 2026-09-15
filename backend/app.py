"""
Intelligent Event Management Platform — Flask Backend
Entry point: python app.py
"""

import os
from flask import Flask
from flask_cors import CORS
from dotenv import load_dotenv

from database import init_db
from email_service import init_mail
from routes.attendees import attendees_bp
from routes.analytics import analytics_bp
from routes.importexport import importexport_bp
from routes.ai_insights import ai_bp
from routes.operations import operations_bp
from routes.milestone3 import m3_bp
from routes.intelligence import intelligence_bp

load_dotenv()

app = Flask(__name__)
allowed_origins = [origin.strip() for origin in os.environ.get("CORS_ORIGINS", "http://localhost:3000,http://127.0.0.1:3000").split(",") if origin.strip()]
CORS(app, origins=allowed_origins or "*")

# Flask secret key (needed for session / some extensions)
app.config["SECRET_KEY"] = os.environ.get("SECRET_KEY", "change-me-in-production")

# Initialize Flask-Mail
init_mail(app)

# Register blueprints
app.register_blueprint(attendees_bp)
app.register_blueprint(analytics_bp)
app.register_blueprint(importexport_bp)
app.register_blueprint(ai_bp)
app.register_blueprint(operations_bp)
app.register_blueprint(m3_bp)
app.register_blueprint(intelligence_bp)
init_db()


@app.route("/", methods=["GET"])
def health():
    return {"status": "ok", "message": "Intelligent Event Management Platform API"}, 200


if __name__ == "__main__":
    init_db()
    port = int(os.environ.get("PORT", 5000))
    debug = os.environ.get("FLASK_DEBUG", "true").lower() == "true"
    print(f"\n🚀 Backend running at http://localhost:{port}\n")
    app.run(host="0.0.0.0", port=port, debug=debug)
