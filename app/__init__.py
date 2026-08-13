from flask import Flask, session, g, send_from_directory
from pathlib import Path
import config
from app.db import close_db, query


def create_app():
    root = Path(__file__).resolve().parent.parent
    app = Flask(
        __name__,
        template_folder=str(root / "templates"),
        static_folder=str(root / "static"),
    )
    app.secret_key = config.SECRET_KEY
    app.config["MAX_CONTENT_LENGTH"] = 5 * 1024 * 1024

    config.RECEIPT_DIR.mkdir(parents=True, exist_ok=True)
    config.CERT_DIR.mkdir(parents=True, exist_ok=True)

    app.teardown_appcontext(close_db)

    @app.before_request
    def load_user():
        g.user = None
        uid = session.get("user_id")
        if uid:
            g.user = query("SELECT * FROM users WHERE id = %s", (uid,), fetch="one")

    @app.context_processor
    def inject():
        return {
            "current_user": g.get("user"),
            "fee_indigene": config.FEE_INDIGENE,
            "fee_non_indigene": config.FEE_NON_INDIGENE,
            "units": config.CLEARANCE_UNITS,
            "paystack_enabled": bool(config.PAYSTACK_SECRET_KEY),
        }

    @app.route("/uploads/receipts/<path:filename>")
    def uploaded_receipt(filename):
        if not g.user:
            return ("Login required", 401)
        return send_from_directory(config.RECEIPT_DIR, filename)

    @app.route("/uploads/certificates/<path:filename>")
    def uploaded_cert(filename):
        if not g.user:
            return ("Login required", 401)
        return send_from_directory(config.CERT_DIR, filename)

    from app.routes_auth import bp as auth_bp
    from app.routes_student import bp as student_bp
    from app.routes_admin import bp as admin_bp
    from app.routes_pay import bp as pay_bp

    app.register_blueprint(auth_bp)
    app.register_blueprint(student_bp)
    app.register_blueprint(admin_bp)
    app.register_blueprint(pay_bp)
    return app
